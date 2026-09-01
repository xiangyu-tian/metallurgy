"""Dry-run-first, insert-only importer for the P1-W13 C008 data asset."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import uuid
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable

import psycopg2
import psycopg2.extras


psycopg2.extras.register_uuid()

ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "Tools" / "models_core" / "data" / "melt_viscosity_correlations_w13_v1.json"
MIGRATION = ROOT / "database" / "migrations" / "011_melt_viscosity_correlations.sql"
LOCK_KEY = 1300820260901


class ImportConflict(RuntimeError):
    """Raised when an existing natural key has different scientific content."""


def db_config() -> dict[str, Any]:
    config: dict[str, Any] = {
        "database": os.getenv("METALLURGY_DB_NAME", "metallurgy"),
        "user": os.getenv("METALLURGY_DB_USER", "postgres"),
        "password": os.getenv("METALLURGY_DB_PASSWORD", ""),
        "connect_timeout": int(os.getenv("METALLURGY_DB_CONNECT_TIMEOUT", "5")),
    }
    if os.getenv("METALLURGY_DB_HOST"):
        config["host"] = os.environ["METALLURGY_DB_HOST"]
    if os.getenv("METALLURGY_DB_PORT"):
        config["port"] = int(os.environ["METALLURGY_DB_PORT"])
    return config


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_backup(path_text: str | None, apply: bool) -> dict[str, str] | None:
    if not path_text:
        if apply:
            raise ValueError("--apply requires --backup-file from a verified pre-import backup")
        return None
    path = Path(path_text).resolve()
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f"backup file is missing or empty: {path}")
    if path.read_bytes()[:5] != b"PGDMP":
        raise ValueError("backup is not a PostgreSQL custom-format archive")
    digest = sha256(path)
    sums = path.parent / "SHA256SUMS"
    if sums.exists() and digest not in sums.read_text(encoding="utf-8"):
        raise ValueError("backup SHA256 does not match SHA256SUMS")
    return {"path": str(path), "sha256": digest}


def equivalent(existing: Any, incoming: Any) -> bool:
    if isinstance(existing, psycopg2.extras.Json):
        existing = existing.adapted
    if isinstance(incoming, psycopg2.extras.Json):
        incoming = incoming.adapted
    if isinstance(existing, (int, float, Decimal)) and not isinstance(existing, bool) \
            and isinstance(incoming, (int, float, Decimal)) and not isinstance(incoming, bool):
        return Decimal(str(existing)) == Decimal(str(incoming))
    if isinstance(existing, dict) and isinstance(incoming, dict):
        return set(existing) == set(incoming) and all(
            equivalent(existing[key], incoming[key]) for key in existing
        )
    if isinstance(existing, (list, tuple)) and isinstance(incoming, (list, tuple)):
        return len(existing) == len(incoming) and all(
            equivalent(left, right) for left, right in zip(existing, incoming)
        )
    return existing == incoming


def insert_checked(
    cur,
    table: str,
    key_where: str,
    key_values: tuple,
    data: dict[str, Any],
    compare_fields: Iterable[str],
) -> str:
    cur.execute(f"SELECT * FROM {table} WHERE {key_where} FOR SHARE", key_values)
    existing = cur.fetchone()
    if existing:
        mismatches = {
            field: {"existing": existing[field], "incoming": data[field]}
            for field in compare_fields
            if not equivalent(existing[field], data[field])
        }
        if mismatches:
            raise ImportConflict(
                f"content conflict in {table} key={key_values}: "
                + json.dumps(mismatches, ensure_ascii=False, default=str, sort_keys=True)
            )
        return "unchanged"
    columns = list(data)
    placeholders = ",".join(["%s"] * len(columns))
    cur.execute(
        f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders})",
        tuple(
            psycopg2.extras.Json(data[column])
            if isinstance(data[column], (dict, list))
            else data[column]
            for column in columns
        ),
    )
    return "inserted"


def validate_asset(asset: dict[str, Any]) -> None:
    required_top = {
        "asset_id", "dataset_id", "name", "version", "provider",
        "license", "retrieved_at", "models",
    }
    if set(asset) != required_top:
        raise ValueError("viscosity asset top-level fields do not match the fixed schema")
    models = asset["models"]
    if not isinstance(models, list) or len(models) != 2:
        raise ValueError("viscosity asset must contain exactly two approved model definitions")
    ids = [model.get("model_id") for model in models]
    if ids != ["URBAIN_SLAG_1981", "HIRAI_LIQUID_ALLOY_1993"]:
        raise ValueError("unexpected or reordered viscosity model definitions")
    required_model = {
        "model_id", "material_kind", "equation_type", "temperature_min_k",
        "temperature_max_k", "parameters", "component_groups", "applicability",
        "source_version", "source_ref", "source_url", "is_approved",
    }
    for model in models:
        if set(model) != required_model:
            raise ValueError(f"model fields do not match fixed schema: {model.get('model_id')}")
        if model["temperature_min_k"] <= 0 or model["temperature_max_k"] <= model["temperature_min_k"]:
            raise ValueError(f"invalid model temperature range: {model['model_id']}")
        if model["is_approved"] is not True:
            raise ValueError(f"asset model is not approved: {model['model_id']}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="commit insert-only migration/import")
    parser.add_argument("--backup-file", help="verified PostgreSQL custom backup required for --apply")
    args = parser.parse_args()

    backup = verify_backup(args.backup_file, args.apply)
    asset = json.loads(ASSET.read_text(encoding="utf-8"))
    validate_asset(asset)
    checksum = "sha256:" + sha256(ASSET)
    run_id = uuid.uuid4()
    stats = {"inserted": 0, "unchanged": 0}

    conn = psycopg2.connect(**db_config())
    conn.autocommit = False
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SET LOCAL statement_timeout='60s'")
            cur.execute("SELECT pg_advisory_xact_lock(%s)", (LOCK_KEY,))
            cur.execute(MIGRATION.read_text(encoding="utf-8"))

            dataset = {
                "dataset_id": asset["dataset_id"],
                "name": asset["name"],
                "category": "动力学与传递",
                "provider": asset["provider"],
                "license": asset["license"],
                "access_url": "https://doi.org/10.1002/srin.198701513",
                "ingestion_mode": "versioned repository asset",
                "version": asset["version"],
                "retrieved_at": asset["retrieved_at"],
                "checksum": checksum,
                "owner": "metallurgy-tools",
                "security_level": "公开",
                "quality_grade": "B",
                "lineage_json": {
                    "asset_id": asset["asset_id"],
                    "import_source": str(ASSET.relative_to(ROOT)).replace("\\", "/"),
                    "model_ids": [model["model_id"] for model in asset["models"]],
                    "plant_control_approved": False,
                },
            }
            dataset_fields = [
                "name", "category", "provider", "license", "access_url",
                "ingestion_mode", "version", "checksum", "owner",
                "security_level", "quality_grade", "lineage_json",
            ]
            status = insert_checked(
                cur,
                "metallurgy_v2.dataset_registry",
                "dataset_id=%s",
                (dataset["dataset_id"],),
                dataset,
                dataset_fields,
            )
            stats[status] += 1

            model_fields = [
                "material_kind", "equation_type", "temperature_min_k",
                "temperature_max_k", "parameters", "component_groups",
                "applicability", "source_ref", "source_url", "is_approved",
            ]
            for model in asset["models"]:
                row = {"dataset_id": asset["dataset_id"], **model}
                status = insert_checked(
                    cur,
                    "metallurgy_v2.melt_viscosity_model_definition",
                    "dataset_id=%s AND model_id=%s AND source_version=%s",
                    (row["dataset_id"], row["model_id"], row["source_version"]),
                    row,
                    model_fields,
                )
                stats[status] += 1

            details = {
                "backup": backup,
                "asset_id": asset["asset_id"],
                "asset_sha256": checksum,
                "migration": str(MIGRATION.relative_to(ROOT)).replace("\\", "/"),
            }
            cur.execute(
                """INSERT INTO metallurgy_v2.dataset_import_run
                   (run_id,dataset_id,source_version,source_checksum,dry_run,status,
                    staged_count,inserted_count,unchanged_count,details,completed_at)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,CURRENT_TIMESTAMP)""",
                (
                    run_id, asset["dataset_id"], asset["version"], checksum,
                    not args.apply, "committed" if args.apply else "dry_run_passed",
                    stats["inserted"] + stats["unchanged"], stats["inserted"],
                    stats["unchanged"], psycopg2.extras.Json(details),
                ),
            )

        if args.apply:
            conn.commit()
        else:
            conn.rollback()
        print(json.dumps({
            "mode": "apply" if args.apply else "dry-run",
            "run_id": str(run_id),
            "dataset_id": asset["dataset_id"],
            "asset_sha256": checksum,
            **stats,
            "backup": backup,
        }, ensure_ascii=False, indent=2))
        return 0
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
