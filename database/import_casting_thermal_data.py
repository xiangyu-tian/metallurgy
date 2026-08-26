"""Safely import P1-W5B casting thermal reference data.

Default execution is a rolled-back dry run. ``--apply`` is insert-only and
requires a verified pre-import custom-format PostgreSQL backup. Runtime tools
never read the JSON asset; it is only the reviewed input to this importer.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import uuid
from decimal import Decimal
from pathlib import Path
from typing import Any

import psycopg2
import psycopg2.extras

psycopg2.extras.register_uuid()


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "database" / "migrations" / "008_casting_thermal_property_data.sql"
ASSET_PATH = ROOT / "Tools" / "models_core" / "data" / "casting_thermal_reference_v1.json"
LOCK_KEY = 4200520260826
KNOWN_EQUATIONS = {
    "CONSTANT",
    "POLYNOMIAL_T",
    "PIECEWISE_LINEAR_TABLE",
    "LINEAR_ENDPOINTS",
    "LINEAR_SOLID_FRACTION",
    "WIEDEMANN_FRANZ_FROM_RESISTIVITY_TABLE",
}


class ImportConflict(RuntimeError):
    """An immutable natural key already exists with different content."""


def db_config(database: str | None = None) -> dict[str, Any]:
    config: dict[str, Any] = {
        "database": database or os.getenv("METALLURGY_DB_NAME", "metallurgy"),
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


def _require_unique(items: list[dict[str, Any]], key: str) -> None:
    values = [item[key] for item in items]
    duplicates = sorted({value for value in values if values.count(value) > 1})
    if duplicates:
        raise ImportConflict(f"duplicate {key}: {duplicates}")


def _points(coefficients: dict[str, Any], equation_type: str) -> list[list[float]] | None:
    if equation_type == "PIECEWISE_LINEAR_TABLE":
        return coefficients.get("points")
    if equation_type == "WIEDEMANN_FRANZ_FROM_RESISTIVITY_TABLE":
        return coefficients.get("resistivity_points_microohm_m")
    return None


def load_asset() -> tuple[dict[str, Any], str]:
    payload = json.loads(ASSET_PATH.read_text(encoding="utf-8"))
    asset_sha = sha256(ASSET_PATH)
    for required in ("asset_id", "asset_version", "datasets", "property_sets", "correlations",
                     "boundary_profiles", "benchmark_cases"):
        if required not in payload:
            raise ImportConflict(f"asset missing {required}")
    _require_unique(payload["datasets"], "dataset_id")
    _require_unique(payload["property_sets"], "property_set_id")
    _require_unique(payload["correlations"], "correlation_id")
    _require_unique(payload["boundary_profiles"], "boundary_profile_id")
    _require_unique(payload["benchmark_cases"], "benchmark_id")

    dataset_ids = {row["dataset_id"] for row in payload["datasets"]}
    property_set_ids = {row["property_set_id"] for row in payload["property_sets"]}
    boundary_ids = {row["boundary_profile_id"] for row in payload["boundary_profiles"]}
    for row in payload["property_sets"]:
        if row["dataset_id"] not in dataset_ids:
            raise ImportConflict(f"unknown dataset for property set {row['property_set_id']}")
        if row["temperature_min_k"] <= 0 or row["temperature_max_k"] <= row["temperature_min_k"]:
            raise ImportConflict(f"invalid property-set range: {row['property_set_id']}")
    for row in payload["correlations"]:
        if row["property_set_id"] not in property_set_ids:
            raise ImportConflict(f"unknown property set for correlation {row['correlation_id']}")
        if row["equation_type"] not in KNOWN_EQUATIONS:
            raise ImportConflict(f"unsupported equation type: {row['equation_type']}")
        if row["temperature_min_k"] <= 0 or row["temperature_max_k"] <= row["temperature_min_k"]:
            raise ImportConflict(f"invalid correlation range: {row['correlation_id']}")
        points = _points(row["coefficients"], row["equation_type"])
        if points is not None:
            if len(points) < 2 or any(len(point) != 2 for point in points):
                raise ImportConflict(f"invalid point table: {row['correlation_id']}")
            temperatures = [float(point[0]) for point in points]
            values = [float(point[1]) for point in points]
            if temperatures != sorted(set(temperatures)) or not all(map(math.isfinite, temperatures + values)):
                raise ImportConflict(f"non-monotone/non-finite points: {row['correlation_id']}")
            if temperatures[0] != float(row["temperature_min_k"]) \
                    or temperatures[-1] != float(row["temperature_max_k"]):
                raise ImportConflict(f"point table does not cover declared range: {row['correlation_id']}")
    for row in payload["boundary_profiles"]:
        if row["dataset_id"] not in dataset_ids or row.get("property_set_id") not in property_set_ids:
            raise ImportConflict(f"invalid boundary references: {row['boundary_profile_id']}")
        if row["domain_max"] <= row["domain_min"]:
            raise ImportConflict(f"invalid boundary domain: {row['boundary_profile_id']}")
    for row in payload["benchmark_cases"]:
        if row["property_set_id"] not in property_set_ids:
            raise ImportConflict(f"invalid benchmark property set: {row['benchmark_id']}")
        if row.get("boundary_profile_id") not in boundary_ids:
            raise ImportConflict(f"invalid benchmark boundary: {row['benchmark_id']}")

    required_by_set = {
        "NIST_SRM1155A_316L_2019_V1": {
            "DENSITY", "ENTHALPY", "HEAT_CAPACITY", "THERMAL_CONDUCTIVITY",
            "LATENT_HEAT", "SOLID_FRACTION",
        },
        "F005_ANALYTIC_CONSTANT_V1": {"DENSITY", "ENTHALPY", "HEAT_CAPACITY", "THERMAL_CONDUCTIVITY"},
    }
    for set_id, required in required_by_set.items():
        available = {row["property_type"] for row in payload["correlations"]
                     if row["property_set_id"] == set_id}
        if missing := required - available:
            raise ImportConflict(f"{set_id} missing property types: {sorted(missing)}")

    nist = next(row for row in payload["datasets"]
                if row["dataset_id"] == "DS_NIST_SRM1155A_316L_2019")
    if nist["license"] != "CC BY 4.0" or not nist["checksum"].startswith("sha256:"):
        raise ImportConflict("NIST source license/checksum is incomplete")
    if any("DS042" in json.dumps(row, ensure_ascii=False) for row in payload.values() if isinstance(row, list)):
        raise ImportConflict("restricted DS042 data must not be present in the public reference asset")
    return payload, asset_sha


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
            raise ImportConflict(
                f"content conflict in {table}: {json.dumps(mismatches, ensure_ascii=False, default=str)}"
            )
        return "unchanged"
    columns = list(data)
    values = [psycopg2.extras.Json(data[column]) if isinstance(data[column], (dict, list))
              else data[column] for column in columns]
    cur.execute(
        f"INSERT INTO {table} ({','.join(columns)}) VALUES ({','.join(['%s'] * len(columns))})",
        values,
    )
    return "inserted"


def import_rows(cur, payload: dict[str, Any], asset_sha: str, stats: dict[str, int]) -> None:
    for source in payload["datasets"]:
        data = dict(source)
        if data["checksum"] is None:
            data["checksum"] = f"sha256:{asset_sha}"
        lineage = dict(data["lineage_json"])
        lineage.update({
            "import_asset": str(ASSET_PATH.relative_to(ROOT)).replace("\\", "/"),
            "import_asset_sha256": asset_sha,
        })
        data["lineage_json"] = lineage
        stats[insert_checked(
            cur, "metallurgy_v2.dataset_registry", "dataset_id", data,
            ["name", "provider", "license", "access_url", "version", "checksum", "lineage_json"],
        )] += 1

    for source in payload["property_sets"]:
        data = dict(source)
        stats[insert_checked(
            cur, "metallurgy_v2.casting_material_property_set", "property_set_id", data,
            [column for column in data if column != "property_set_id"],
        )] += 1

    property_set_urls = {row["property_set_id"]: row.get("source_url") for row in payload["property_sets"]}
    for source in payload["correlations"]:
        data = dict(source)
        data.setdefault("source_url", property_set_urls[data["property_set_id"]])
        data.setdefault("metadata", {})
        data.setdefault("is_active", True)
        stats[insert_checked(
            cur, "metallurgy_v2.casting_material_property_correlation", "correlation_id", data,
            [column for column in data if column != "correlation_id"],
        )] += 1

    for source in payload["boundary_profiles"]:
        data = dict(source)
        stats[insert_checked(
            cur, "metallurgy_v2.casting_boundary_profile", "boundary_profile_id", data,
            [column for column in data if column != "boundary_profile_id"],
        )] += 1

    for source in payload["benchmark_cases"]:
        data = dict(source)
        stats[insert_checked(
            cur, "metallurgy_v2.casting_model_benchmark_case", "benchmark_id", data,
            [column for column in data if column != "benchmark_id"],
        )] += 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--backup-file")
    parser.add_argument("--database", help="explicit target database; defaults to METALLURGY_DB_NAME/metallurgy")
    args = parser.parse_args()
    backup = verify_backup(args.backup_file, args.apply)
    payload, asset_sha = load_asset()
    stats = {"inserted": 0, "unchanged": 0}
    run_id = uuid.uuid4()
    connection = psycopg2.connect(**db_config(args.database))
    connection.autocommit = False
    try:
        with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SET LOCAL statement_timeout='120s'")
            cur.execute("SELECT pg_advisory_xact_lock(%s)", (LOCK_KEY,))
            cur.execute(MIGRATION.read_text(encoding="utf-8"))
            import_rows(cur, payload, asset_sha, stats)
            details = {
                "backup": backup,
                "asset": str(ASSET_PATH.relative_to(ROOT)).replace("\\", "/"),
                "asset_sha256": asset_sha,
                "restricted_ds042_imported": False,
            }
            cur.execute(
                """INSERT INTO metallurgy_v2.dataset_import_run
                   (run_id,dataset_id,source_version,source_checksum,dry_run,status,staged_count,
                    inserted_count,unchanged_count,details,completed_at)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,CURRENT_TIMESTAMP)""",
                (run_id, payload["asset_id"], payload["asset_version"], asset_sha,
                 not args.apply, "committed" if args.apply else "dry_run_passed",
                 stats["inserted"] + stats["unchanged"], stats["inserted"], stats["unchanged"],
                 psycopg2.extras.Json(details)),
            )
        connection.commit() if args.apply else connection.rollback()
        print(json.dumps({
            "mode": "apply" if args.apply else "dry-run",
            "database": args.database or os.getenv("METALLURGY_DB_NAME", "metallurgy"),
            "run_id": str(run_id),
            **stats,
            "asset_sha256": asset_sha,
            "backup": backup,
        }, ensure_ascii=False, indent=2))
        return 0
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
