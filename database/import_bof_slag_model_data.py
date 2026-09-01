"""Safely import P1-W7 public BOF slag/metal reference parameters.

The default run is a rolled-back dry run. ``--apply`` is insert-only and
requires a verified PostgreSQL backup. Runtime tools read only approved rows
from PostgreSQL; the JSON file is reviewed importer input, never a fallback.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import uuid
from decimal import Decimal
from pathlib import Path
from typing import Any

import psycopg2
import psycopg2.extras

try:
    from database.import_casting_thermal_data import (
        ImportConflict,
        db_config,
        equivalent,
        insert_checked,
        sha256,
        verify_backup,
    )
except ModuleNotFoundError as exc:
    if exc.name != "database":
        raise
    from import_casting_thermal_data import (  # type: ignore[no-redef]
        ImportConflict,
        db_config,
        equivalent,
        insert_checked,
        sha256,
        verify_backup,
    )


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "database" / "migrations" / "010_bof_slag_model_parameters.sql"
ASSET_PATH = ROOT / "Tools" / "models_core" / "data" / "bof_slag_model_parameters_v1.json"
LOCK_KEY = 4201020260901

EXPECTED_DATASETS = {
    "DS_BOF_P_PARTITION_ISIJ_2016",
    "DS_SLAG_S_CAPACITY_ISIJ_2013",
    "DS_S_DISTRIBUTION_ISIJ_2016",
    "DS_MN_EQUILIBRIUM_ISIJ_1963",
    "DS_SI_EQUILIBRIUM_ISIJ_2017",
}
EXPECTED_PARAMETER_CODES = {
    "D010_SPOONER_ISIJ_2016_V1": {
        "CAO_COEFF", "MGO_COEFF", "P2O5_COEFF", "AL2O3_COEFF",
        "SIO2_COEFF", "INV_T_COEFF", "INTERCEPT", "TFE_EXPONENT",
    },
    "D011_ZHANG_MA_ISIJ_V1": {
        "CS_INTERCEPT", "CS_INV_LAMBDA", "CS_INV_T", "CS_INV_LAMBDA_INV_T",
        "LOGK5_INV_T", "LOGK5_INTERCEPT", "OPTICAL_BASICITY_CAO",
        "OPTICAL_BASICITY_MGO", "OPTICAL_BASICITY_AL2O3", "OPTICAL_BASICITY_SIO2",
        "OPTICAL_BASICITY_FEO", "OPTICAL_BASICITY_MNO", "OPTICAL_BASICITY_TIO2",
        "OPTICAL_BASICITY_CAF2",
    },
    "D012_GUNJI_MATOBA_LIQUID_V1": {"LOGK_A", "LOGK_B"},
    "D013_DONG_ISIJ_2017_V1": {"LOGK_A", "LOGK_B"},
}


def _require_unique(items: list[dict[str, Any]], key: str) -> None:
    values = [item[key] for item in items]
    duplicates = sorted({value for value in values if values.count(value) > 1})
    if duplicates:
        raise ImportConflict(f"duplicate {key}: {duplicates}")


def load_asset() -> tuple[dict[str, Any], str]:
    payload = json.loads(ASSET_PATH.read_text(encoding="utf-8"))
    asset_sha = sha256(ASSET_PATH)
    for key in ("asset_id", "asset_version", "datasets", "parameter_sets"):
        if key not in payload:
            raise ImportConflict(f"asset missing {key}")
    if "DS042" in json.dumps(payload, ensure_ascii=False):
        raise ImportConflict("restricted DS042 data must not be imported")

    _require_unique(payload["datasets"], "dataset_id")
    _require_unique(payload["parameter_sets"], "parameter_set_id")
    dataset_ids = {row["dataset_id"] for row in payload["datasets"]}
    if dataset_ids != EXPECTED_DATASETS:
        raise ImportConflict(f"unexpected dataset set: {sorted(dataset_ids)}")
    parameter_sets = {row["parameter_set_id"]: row for row in payload["parameter_sets"]}
    if set(parameter_sets) != set(EXPECTED_PARAMETER_CODES):
        raise ImportConflict(f"unexpected parameter sets: {sorted(parameter_sets)}")

    seen_parameter_keys: set[tuple[str, str]] = set()
    for set_id, row in parameter_sets.items():
        if row["model_code"] not in {"D010", "D011", "D012", "D013"}:
            raise ImportConflict(f"unsupported model code in {set_id}")
        if row["dataset_id"] not in dataset_ids:
            raise ImportConflict(f"unknown default dataset in {set_id}")
        lower = float(row["temperature_min_k"])
        upper = float(row["temperature_max_k"])
        if not (math.isfinite(lower) and math.isfinite(upper) and 0 < lower < upper):
            raise ImportConflict(f"invalid temperature domain in {set_id}")
        if row["usage_scope"] not in {
            "REFERENCE_VALIDATION_ONLY", "ENGINEERING_SCREENING_ONLY"
        }:
            raise ImportConflict(f"invalid usage scope in {set_id}")
        if row["applicability"].get("plant_control_approved") is not False:
            raise ImportConflict(f"plant-control approval must remain false in {set_id}")

        codes = {parameter["parameter_code"] for parameter in row["parameters"]}
        if codes != EXPECTED_PARAMETER_CODES[set_id] or len(codes) != len(row["parameters"]):
            raise ImportConflict(f"parameter-code mismatch in {set_id}")
        for parameter in row["parameters"]:
            value = parameter["parameter_value"]
            if isinstance(value, bool) or not math.isfinite(float(value)):
                raise ImportConflict(f"non-finite parameter in {set_id}")
            parameter_dataset = parameter.get("dataset_id", row["dataset_id"])
            if parameter_dataset not in dataset_ids:
                raise ImportConflict(f"unknown parameter dataset in {set_id}")
            key = (set_id, parameter["parameter_code"])
            if key in seen_parameter_keys:
                raise ImportConflict(f"duplicate parameter key: {key}")
            seen_parameter_keys.add(key)

    d010 = {p["parameter_code"]: Decimal(str(p["parameter_value"]))
            for p in parameter_sets["D010_SPOONER_ISIJ_2016_V1"]["parameters"]}
    if d010["MGO_COEFF"] != d010["CAO_COEFF"] * Decimal("0.37") \
            or d010["P2O5_COEFF"] != d010["CAO_COEFF"] * Decimal("4.65") \
            or d010["AL2O3_COEFF"] != d010["CAO_COEFF"] * Decimal("-0.05") \
            or d010["SIO2_COEFF"] != d010["CAO_COEFF"] * Decimal("-0.2"):
        raise ImportConflict("D010 expanded coefficients do not reproduce source Eq.6")

    d011 = parameter_sets["D011_ZHANG_MA_ISIJ_V1"]
    optical = [p for p in d011["parameters"]
               if p["parameter_code"].startswith("OPTICAL_BASICITY_")]
    formulas = [p.get("metadata", {}).get("component_formula") for p in optical]
    if len(optical) != 8 or None in formulas or len(set(formulas)) != 8:
        raise ImportConflict("D011 optical-basicity component metadata is incomplete")
    if any(float(p["parameter_value"]) <= 0
           or float(p.get("metadata", {}).get("oxygen_equivalent", 0)) <= 0 for p in optical):
        raise ImportConflict("D011 optical-basicity values/oxygen equivalents must be positive")
    return payload, asset_sha


def _insert_parameter(cur, data: dict[str, Any]) -> str:
    key = (
        data["model_code"], data["parameter_set_id"],
        data["parameter_code"], data["source_version"],
    )
    cur.execute(
        """SELECT * FROM metallurgy_v2.bof_slag_model_parameter
           WHERE model_code=%s AND parameter_set_id=%s
             AND parameter_code=%s AND source_version=%s FOR SHARE""",
        key,
    )
    existing = cur.fetchone()
    if existing:
        mismatches = {
            field: {"existing": existing[field], "incoming": data[field]}
            for field in data if field != "created_at" and not equivalent(existing[field], data[field])
        }
        if mismatches:
            raise ImportConflict(
                "content conflict in metallurgy_v2.bof_slag_model_parameter: "
                + json.dumps(mismatches, ensure_ascii=False, default=str)
            )
        return "unchanged"
    columns = list(data)
    values = [psycopg2.extras.Json(data[column]) if isinstance(data[column], (dict, list))
              else data[column] for column in columns]
    cur.execute(
        f"INSERT INTO metallurgy_v2.bof_slag_model_parameter "
        f"({','.join(columns)}) VALUES ({','.join(['%s'] * len(columns))})",
        values,
    )
    return "inserted"


def import_rows(cur, payload: dict[str, Any], asset_sha: str,
                stats: dict[str, int]) -> None:
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

    for parameter_set in payload["parameter_sets"]:
        for parameter in parameter_set["parameters"]:
            data = {
                "dataset_id": parameter.get("dataset_id", parameter_set["dataset_id"]),
                "model_code": parameter_set["model_code"],
                "parameter_set_id": parameter_set["parameter_set_id"],
                "parameter_code": parameter["parameter_code"],
                "parameter_value": parameter["parameter_value"],
                "unit": parameter["unit"],
                "source_version": parameter.get(
                    "source_version", parameter_set["source_version"]
                ),
                "source_ref": parameter.get("source_ref", parameter_set["source_ref"]),
                "source_url": parameter.get("source_url", parameter_set["source_url"]),
                "temperature_min_k": parameter_set["temperature_min_k"],
                "temperature_max_k": parameter_set["temperature_max_k"],
                "usage_scope": parameter_set["usage_scope"],
                "applicability": parameter_set["applicability"],
                "metadata": parameter.get("metadata", {}),
                "is_approved": True,
            }
            stats[_insert_parameter(cur, data)] += 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--backup-file")
    parser.add_argument("--database")
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
            cur.execute("SELECT * FROM metallurgy_v2.dataset_registry WHERE dataset_id='DS042'")
            ds042_before = dict(cur.fetchone() or {})
            cur.execute(MIGRATION.read_text(encoding="utf-8"))
            import_rows(cur, payload, asset_sha, stats)
            cur.execute("SELECT * FROM metallurgy_v2.dataset_registry WHERE dataset_id='DS042'")
            ds042_after = dict(cur.fetchone() or {})
            if not equivalent(ds042_before, ds042_after):
                raise ImportConflict("DS042 metadata changed during public parameter import")
            details = {
                "backup": backup,
                "asset": str(ASSET_PATH.relative_to(ROOT)).replace("\\", "/"),
                "asset_sha256": asset_sha,
                "restricted_ds042_imported": False,
                "ds042_unchanged": True,
                "plant_control_approved": False,
            }
            cur.execute(
                """INSERT INTO metallurgy_v2.dataset_import_run
                   (run_id,dataset_id,source_version,source_checksum,dry_run,status,staged_count,
                    inserted_count,unchanged_count,details,completed_at)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,CURRENT_TIMESTAMP)""",
                (run_id, payload["asset_id"], payload["asset_version"], asset_sha,
                 not args.apply, "committed" if args.apply else "dry_run_passed",
                 stats["inserted"] + stats["unchanged"], stats["inserted"],
                 stats["unchanged"], psycopg2.extras.Json(details)),
            )
        connection.commit() if args.apply else connection.rollback()
        print(json.dumps({
            "mode": "apply" if args.apply else "dry-run",
            "database": args.database or os.getenv("METALLURGY_DB_NAME", "metallurgy"),
            "run_id": str(run_id),
            **stats,
            "asset_sha256": asset_sha,
            "backup": backup,
            "restricted_ds042_imported": False,
        }, ensure_ascii=False, indent=2))
        return 0
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
