"""Import the approved P0-W4 solidification model definition safely.

Default execution is a rolled-back dry run. ``--apply`` is insert-only and
requires a verified pre-import custom-format PostgreSQL backup.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import uuid
from decimal import Decimal
from pathlib import Path
from typing import Any

import psycopg2
import psycopg2.extras

psycopg2.extras.register_uuid()


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "database" / "migrations" / "007_solidification_model_data.sql"
ASSET_DIR = ROOT / "Tools" / "models_core" / "data" / "calculation_assets"
MANIFEST_PATH = ASSET_DIR / "mc_fe_v2.059.manifest.json"
LOCK_KEY = 4200420260826


class ImportConflict(RuntimeError):
    pass


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
            raise ValueError("--apply requires --backup-file from the verified pre-import backup")
        return None
    path = Path(path_text).resolve()
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f"backup file is missing or empty: {path}")
    return {"path": str(path), "sha256": sha256(path)}


def manifest() -> dict[str, Any]:
    payload = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    asset = ASSET_DIR / payload["asset_file"]
    actual = sha256(asset)
    if actual != payload["asset_sha256"]:
        raise ImportConflict(f"TDB SHA-256 mismatch: expected {payload['asset_sha256']}, got {actual}")
    header = asset.read_text(encoding="utf-8")[:5000]
    for marker in ("Open Database License", "Database Contents License", "mc_fe_v2.059"):
        if marker not in header:
            raise ImportConflict(f"TDB provenance marker missing: {marker}")
    return payload


def equivalent(left: Any, right: Any) -> bool:
    if isinstance(left, (int, float, Decimal)) and not isinstance(left, bool) \
            and isinstance(right, (int, float, Decimal)) and not isinstance(right, bool):
        return Decimal(str(left)) == Decimal(str(right))
    if isinstance(left, dict) and isinstance(right, dict):
        return set(left) == set(right) and all(equivalent(left[key], right[key]) for key in left)
    if isinstance(left, (list, tuple)) and isinstance(right, (list, tuple)):
        return len(left) == len(right) and all(equivalent(a, b) for a, b in zip(left, right))
    return left == right


def insert_checked(cur, table: str, key_field: str, data: dict[str, Any], compare: list[str]) -> str:
    cur.execute(f"SELECT * FROM {table} WHERE {key_field}=%s FOR SHARE", (data[key_field],))
    existing = cur.fetchone()
    if existing:
        mismatches = {
            field: {"existing": existing[field], "incoming": data[field]}
            for field in compare if not equivalent(existing[field], data[field])
        }
        if mismatches:
            raise ImportConflict(f"content conflict in {table}: {json.dumps(mismatches, default=str)}")
        return "unchanged"
    columns = list(data)
    values = [psycopg2.extras.Json(data[c]) if isinstance(data[c], (dict, list)) else data[c] for c in columns]
    cur.execute(
        f"INSERT INTO {table} ({','.join(columns)}) VALUES ({','.join(['%s'] * len(columns))})",
        values,
    )
    return "inserted"


def import_rows(cur, payload: dict[str, Any], stats: dict[str, int]) -> None:
    dataset = {
        "dataset_id": payload["dataset_id"],
        "name": "MatCalc mc_fe steel thermodynamic database v2.059",
        "category": "相平衡与凝固",
        "provider": "MatCalc / pyroll-project snapshot",
        "license": payload["license"],
        "ingestion_mode": "versioned repository asset",
        "retrieved_at": "2026-08-26 00:00:00",
        "version": payload["model_version"],
        "checksum": f"sha256:{payload['asset_sha256']}",
        "owner": "metallurgy-tools",
        "security_level": "公开",
        "quality_grade": "B",
        "lineage_json": {
            "source_url": payload["source_url"],
            "source_commit": payload["source_commit"],
            "manifest": str(MANIFEST_PATH.relative_to(ROOT)).replace("\\", "/"),
        },
    }
    stats[insert_checked(cur, "metallurgy_v2.dataset_registry", "dataset_id", dataset,
                         ["name", "provider", "license", "version", "checksum", "lineage_json"])] += 1

    definition = {
        "model_asset_id": payload["model_asset_id"],
        "dataset_id": payload["dataset_id"],
        "model_family": payload["model_family"],
        "model_version": payload["model_version"],
        "solver_name": payload["solver"]["name"],
        "solver_version": payload["solver"]["version"],
        "solidification_solver_name": payload["solidification_solver"]["name"],
        "solidification_solver_version": payload["solidification_solver"]["version"],
        "asset_uri": str((ASSET_DIR / payload["asset_file"]).relative_to(ROOT)).replace("\\", "/"),
        "asset_sha256": payload["asset_sha256"],
        "license": payload["license"],
        "source_url": payload["source_url"],
        "source_commit": payload["source_commit"],
        "temperature_min_k": payload["temperature_range_k"][0],
        "temperature_max_k": payload["temperature_range_k"][1],
        "composition_basis": payload["composition_basis"],
        "domain_json": {"component_max_wt_percent": payload["component_max_wt_percent"]},
        "supported_components": payload["supported_components"],
        "phase_set": payload["phase_set"],
        "metadata": {"scope_note": payload["scope_note"], "pressure_pa": 101325},
        "is_approved": True,
    }
    stats[insert_checked(cur, "metallurgy_v2.solidification_model_definition", "model_asset_id", definition,
                         [c for c in definition if c != "model_asset_id"])] += 1

    cases = [
        {
            "benchmark_id": "MCFE2059-PURE-FE-MELTING",
            "model_asset_id": payload["model_asset_id"], "composition_json": {},
            "reference_type": "fixed_point_interval",
            "expected_json": {"solidus_k": [1809, 1813], "liquidus_k": [1809, 1813]},
            "tolerance_json": {"grid_resolution_k": 2},
            "source_ref": "Accepted pure-iron melting point consistency check; CALPHAD asset self-consistency",
            "source_url": "https://physics.nist.gov/cgi-bin/cuu/Value?tk",
            "within_domain": True,
            "metadata": {"purpose": "independent fixed-point range; not a fitted benchmark"},
        },
        {
            "benchmark_id": "MCFE2059-FEC-LIQUID-MONOTONIC",
            "model_asset_id": payload["model_asset_id"], "composition_json": {"C": 0.1},
            "reference_type": "mathematical_property",
            "expected_json": {"property": "fraction_liquid nondecreasing with temperature"},
            "tolerance_json": {"absolute": 1e-8},
            "source_ref": "Equilibrium phase-fraction monotonicity across the Fe-0.1 wt% C solidification interval",
            "source_url": payload["source_url"], "within_domain": True,
            "metadata": {"validation": "property-based"},
        },
        {
            "benchmark_id": "MCFE2059-PURE-FE-NIST-1809K",
            "model_asset_id": payload["model_asset_id"], "composition_json": {},
            "reference_type": "external_fixed_point_interval",
            "expected_json": {"solidus_k": [1807, 1811], "liquidus_k": [1807, 1811]},
            "tolerance_json": {"grid_resolution_k": 2},
            "source_ref": "NIST Chemistry WebBook iron condensed-phase ranges meet at 1809 K (Chase, 1998)",
            "source_url": "https://webbook.nist.gov/cgi/cbook.cgi?ID=C7439896&Mask=24A",
            "within_domain": True,
            "metadata": {"purpose": "external fixed-point verification; not fitted by this project"},
        },
        {
            "benchmark_id": "MCFE2059-SCHEIL-CLOSURE",
            "model_asset_id": payload["model_asset_id"], "composition_json": {"C": 0.1},
            "reference_type": "mathematical_property",
            "expected_json": {"property": "fraction_liquid + fraction_solid = 1"},
            "tolerance_json": {"absolute": 1e-8},
            "source_ref": "Scheil-Gulliver phase-fraction closure",
            "source_url": "https://github.com/pycalphad/scheil", "within_domain": True,
            "metadata": {"validation": "conservation property"},
        },
    ]
    for case in cases:
        stats[insert_checked(cur, "metallurgy_v2.solidification_benchmark_case", "benchmark_id", case,
                             [c for c in case if c != "benchmark_id"])] += 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--backup-file")
    args = parser.parse_args()
    backup = verify_backup(args.backup_file, args.apply)
    payload = manifest()
    stats = {"inserted": 0, "unchanged": 0}
    run_id = uuid.uuid4()
    connection = psycopg2.connect(**db_config())
    connection.autocommit = False
    try:
        with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SET LOCAL statement_timeout='120s'")
            cur.execute("SELECT pg_advisory_xact_lock(%s)", (LOCK_KEY,))
            cur.execute(MIGRATION.read_text(encoding="utf-8"))
            import_rows(cur, payload, stats)
            details = {"backup": backup, "manifest": str(MANIFEST_PATH), "asset_sha256": payload["asset_sha256"]}
            cur.execute(
                """INSERT INTO metallurgy_v2.dataset_import_run
                   (run_id,dataset_id,source_version,source_checksum,dry_run,status,staged_count,
                    inserted_count,unchanged_count,details,completed_at)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,CURRENT_TIMESTAMP)""",
                (run_id, payload["dataset_id"], payload["model_version"], payload["asset_sha256"],
                 not args.apply, "committed" if args.apply else "dry_run_passed",
                 stats["inserted"] + stats["unchanged"], stats["inserted"], stats["unchanged"],
                 psycopg2.extras.Json(details)),
            )
        connection.commit() if args.apply else connection.rollback()
        print(json.dumps({"mode": "apply" if args.apply else "dry-run", "run_id": str(run_id),
                          **stats, "backup": backup}, ensure_ascii=False, indent=2))
        return 0
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
