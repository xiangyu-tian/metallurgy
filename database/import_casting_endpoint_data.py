"""Safely import P1-W5C casting endpoint configuration and benchmark data.

Default execution is a rolled-back dry run. ``--apply`` is insert-only and
requires a verified pre-import custom-format PostgreSQL backup. Runtime tools
never read the JSON asset; it is only the reviewed input to this importer.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import uuid
from pathlib import Path
from typing import Any

import psycopg2
import psycopg2.extras

try:
    from database.import_casting_thermal_data import (
        ImportConflict,
        db_config,
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
        insert_checked,
        sha256,
        verify_backup,
    )


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "database" / "migrations" / "009_casting_endpoint_configuration.sql"
ASSET_PATH = ROOT / "Tools" / "models_core" / "data" / "casting_endpoint_reference_v1.json"
LOCK_KEY = 4200620260901


def _require_unique(items: list[dict[str, Any]], key: str) -> None:
    values = [item[key] for item in items]
    duplicates = sorted({value for value in values if values.count(value) > 1})
    if duplicates:
        raise ImportConflict(f"duplicate {key}: {duplicates}")


def _curve_value(curve: list[dict[str, float]], time_s: float) -> float:
    if time_s < float(curve[0]["time_s"]) or time_s > float(curve[-1]["time_s"]):
        raise ImportConflict("benchmark curve does not cover machine exit time")
    for row in curve:
        if float(row["time_s"]) == time_s:
            return float(row["center_solid_fraction"])
    for left, right in zip(curve, curve[1:]):
        t0, t1 = float(left["time_s"]), float(right["time_s"])
        if t0 < time_s < t1:
            f0, f1 = float(left["center_solid_fraction"]), float(right["center_solid_fraction"])
            return f0 + (time_s - t0) * (f1 - f0) / (t1 - t0)
    raise ImportConflict("unable to interpolate benchmark curve")


def _event_time(curve: list[dict[str, float]], threshold: float) -> float:
    if float(curve[0]["center_solid_fraction"]) >= threshold:
        return float(curve[0]["time_s"])
    for left, right in zip(curve, curve[1:]):
        f0, f1 = float(left["center_solid_fraction"]), float(right["center_solid_fraction"])
        if f1 < threshold:
            continue
        t0, t1 = float(left["time_s"]), float(right["time_s"])
        if f1 == f0:
            return t1
        return t0 + (threshold - f0) * (t1 - t0) / (f1 - f0)
    raise ImportConflict("benchmark curve does not cross threshold")


def load_asset() -> tuple[dict[str, Any], str]:
    payload = json.loads(ASSET_PATH.read_text(encoding="utf-8"))
    asset_sha = sha256(ASSET_PATH)
    for required in ("asset_id", "asset_version", "datasets", "machine_configurations",
                     "benchmark_cases"):
        if required not in payload:
            raise ImportConflict(f"asset missing {required}")
    _require_unique(payload["datasets"], "dataset_id")
    _require_unique(payload["machine_configurations"], "machine_configuration_id")
    _require_unique(payload["benchmark_cases"], "benchmark_id")

    dataset_ids = {row["dataset_id"] for row in payload["datasets"]}
    if "DS042" in dataset_ids:
        raise ImportConflict("restricted DS042 data must not be imported")
    if dataset_ids != {"DS_F006_ENDPOINT_BENCH_V1"}:
        raise ImportConflict("W5C validation asset must contain only its benchmark dataset")
    configurations = {
        row["machine_configuration_id"]: row for row in payload["machine_configurations"]
    }
    for row in configurations.values():
        if row["dataset_id"] not in dataset_ids:
            raise ImportConflict(f"unknown dataset for {row['machine_configuration_id']}")
        positive = (
            "section_width_m", "section_thickness_m", "mold_length_m",
            "effective_metallurgical_length_m", "casting_speed_min_m_s",
            "casting_speed_max_m_s",
        )
        if not all(math.isfinite(float(row[key])) and float(row[key]) > 0 for key in positive):
            raise ImportConflict(f"invalid geometry/speed for {row['machine_configuration_id']}")
        if float(row["mold_length_m"]) > float(row["effective_metallurgical_length_m"]):
            raise ImportConflict(f"mold exceeds machine length: {row['machine_configuration_id']}")
        if float(row["casting_speed_min_m_s"]) >= float(row["casting_speed_max_m_s"]):
            raise ImportConflict(f"invalid speed interval: {row['machine_configuration_id']}")
        if row["usage_scope"] != "MATHEMATICAL_BENCHMARK_ONLY" \
                or row["metadata"].get("is_real_equipment") is not False:
            raise ImportConflict("project-generated equipment must remain benchmark-only and synthetic")

    for row in payload["benchmark_cases"]:
        if row["dataset_id"] not in dataset_ids or row["model_code"] != "F006":
            raise ImportConflict(f"invalid benchmark identity: {row['benchmark_id']}")
        config = configurations.get(row["machine_configuration_id"])
        if not config:
            raise ImportConflict(f"unknown benchmark machine: {row['benchmark_id']}")
        inputs = row["input_json"]
        curve = inputs["center_solid_fraction_curve"]
        if len(curve) < 2:
            raise ImportConflict(f"benchmark curve too short: {row['benchmark_id']}")
        times = [float(point["time_s"]) for point in curve]
        fractions = [float(point["center_solid_fraction"]) for point in curve]
        if times[0] < 0 or any(right <= left for left, right in zip(times, times[1:])):
            raise ImportConflict(f"benchmark times are not strictly increasing: {row['benchmark_id']}")
        if any(not math.isfinite(value) or not 0 <= value <= 1 for value in fractions) \
                or any(right < left for left, right in zip(fractions, fractions[1:])):
            raise ImportConflict(f"benchmark fractions are invalid/non-monotone: {row['benchmark_id']}")
        speed = float(inputs["casting_speed_m_s"])
        threshold = float(inputs["endpoint_solid_fraction_threshold"])
        event_time = _event_time(curve, threshold)
        event_position = speed * event_time
        machine_length = float(config["effective_metallurgical_length_m"])
        exit_fraction = _curve_value(curve, machine_length / speed)
        tolerance = row["tolerance_json"]
        expected = row["expected_json"]
        if not math.isclose(event_time, float(expected["solidification_end_time_s"]),
                            abs_tol=float(tolerance["time_s"]), rel_tol=0):
            raise ImportConflict(f"incorrect benchmark event time: {row['benchmark_id']}")
        if not math.isclose(event_position, float(expected["solidification_end_position_m"]),
                            abs_tol=float(tolerance["position_m"]), rel_tol=0):
            raise ImportConflict(f"incorrect benchmark event position: {row['benchmark_id']}")
        status = "inside_machine" if event_position < machine_length else (
            "at_machine_exit" if math.isclose(event_position, machine_length, abs_tol=1e-12) \
            else "beyond_machine_exit"
        )
        if status != expected["equipment_status"]:
            raise ImportConflict(f"incorrect benchmark equipment status: {row['benchmark_id']}")
        if not math.isclose(exit_fraction, float(expected["exit_center_solid_fraction"]),
                            abs_tol=float(tolerance["solid_fraction"]), rel_tol=0):
            raise ImportConflict(f"incorrect benchmark exit fraction: {row['benchmark_id']}")
    return payload, asset_sha


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

    for source in payload["machine_configurations"]:
        data = dict(source)
        stats[insert_checked(
            cur, "metallurgy_v2.casting_machine_configuration", "machine_configuration_id", data,
            [column for column in data if column != "machine_configuration_id"],
        )] += 1

    for source in payload["benchmark_cases"]:
        data = dict(source)
        stats[insert_checked(
            cur, "metallurgy_v2.casting_endpoint_benchmark_case", "benchmark_id", data,
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
                "real_equipment_imported": False,
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
