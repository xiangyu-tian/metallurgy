"""P1-W5C qualification tests for F006 configuration and benchmark data."""
from __future__ import annotations

import hashlib
import json
import math
import os
import sys
import unittest
from pathlib import Path

import psycopg2
import psycopg2.extras


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "Tools"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(TOOLS))

from database.import_casting_endpoint_data import import_rows, load_asset
from models_core import ModelRegistry
from models_core.repositories.casting_endpoint_repository import (
    approved_machine_configuration,
    endpoint_benchmark_cases,
)
from models_core.repositories.reference_repository import RepositoryError


ASSET = TOOLS / "models_core" / "data" / "casting_endpoint_reference_v1.json"
MIGRATION = ROOT / "database" / "migrations" / "009_casting_endpoint_configuration.sql"
LONG_MACHINE = "F006_BENCH_LONG_020M_V1"


def _event_time(curve: list[dict], threshold: float) -> float:
    if curve[0]["center_solid_fraction"] >= threshold:
        return float(curve[0]["time_s"])
    for left, right in zip(curve, curve[1:]):
        f0 = float(left["center_solid_fraction"])
        f1 = float(right["center_solid_fraction"])
        if f1 >= threshold:
            t0, t1 = float(left["time_s"]), float(right["time_s"])
            return t0 + (threshold - f0) * (t1 - t0) / (f1 - f0)
    raise AssertionError("qualification curve does not cross threshold")


def _curve_value(curve: list[dict], time_s: float) -> float:
    for left, right in zip(curve, curve[1:]):
        t0, t1 = float(left["time_s"]), float(right["time_s"])
        if t0 <= time_s <= t1:
            f0 = float(left["center_solid_fraction"])
            f1 = float(right["center_solid_fraction"])
            return f0 + (time_s - t0) * (f1 - f0) / (t1 - t0)
    raise AssertionError("qualification curve does not cover exit time")


class P1W5CCastingEndpointDataTests(unittest.TestCase):
    @staticmethod
    def connection():
        config = {
            "database": os.getenv("METALLURGY_DB_NAME", "metallurgy"),
            "user": os.getenv("METALLURGY_DB_USER", "postgres"),
            "password": os.getenv("METALLURGY_DB_PASSWORD", ""),
        }
        if os.getenv("METALLURGY_DB_HOST"):
            config["host"] = os.environ["METALLURGY_DB_HOST"]
        if os.getenv("METALLURGY_DB_PORT"):
            config["port"] = int(os.environ["METALLURGY_DB_PORT"])
        return psycopg2.connect(**config)

    def test_data_layer_integrates_with_f006_runtime_counts(self):
        registry = ModelRegistry()
        registry.discover()
        self.assertEqual(registry.get_counts(), {
            "registered_count": 93,
            "runtime_tool_count": 93,
            "catalog_coverage_count": 75,
            "qualified_executable_count": 93,
            "implementation_qualified_count": 93,
            "data_required_count": 32,
            "data_qualified_count": 32,
            "interface_qualified_count": 93,
            "fully_eligible_count": 93,
        })

    def test_asset_is_versioned_project_generated_and_excludes_ds042(self):
        payload, asset_sha = load_asset()
        self.assertEqual(asset_sha, hashlib.sha256(ASSET.read_bytes()).hexdigest())
        self.assertEqual(payload["asset_version"], "2026.09-v1")
        self.assertEqual(len(payload["machine_configurations"]), 2)
        self.assertEqual(len(payload["benchmark_cases"]), 3)
        serialized = json.dumps(payload, ensure_ascii=False)
        self.assertNotIn('"dataset_id": "DS042"', serialized)
        for row in payload["machine_configurations"]:
            self.assertEqual(row["usage_scope"], "MATHEMATICAL_BENCHMARK_ONLY")
            self.assertIs(row["metadata"]["is_real_equipment"], False)

    def test_migration_is_additive_only(self):
        sql = MIGRATION.read_text(encoding="utf-8").upper()
        for forbidden in (
            "DELETE FROM", "TRUNCATE", "DROP TABLE", "DROP SCHEMA", "ALTER TABLE", "UPDATE "
        ):
            self.assertNotIn(forbidden, sql)
        for table in (
            "CASTING_MACHINE_CONFIGURATION",
            "CASTING_ENDPOINT_BENCHMARK_CASE",
        ):
            self.assertIn(f"CREATE TABLE IF NOT EXISTS METALLURGY_V2.{table}", sql)

    def test_database_rows_repository_scope_and_provenance_are_exact(self):
        with self.connection() as connection, connection.cursor() as cur:
            cur.execute("SELECT count(*) FROM metallurgy_v2.casting_machine_configuration")
            self.assertEqual(cur.fetchone()[0], 2)
            cur.execute("SELECT count(*) FROM metallurgy_v2.casting_endpoint_benchmark_case")
            self.assertEqual(cur.fetchone()[0], 3)
        row, provenance = approved_machine_configuration(LONG_MACHINE)
        self.assertEqual(row["usage_scope"], "MATHEMATICAL_BENCHMARK_ONLY")
        self.assertEqual(float(row["effective_metallurgical_length_m"]), 0.2)
        self.assertEqual(
            provenance.table, "metallurgy_v2.casting_machine_configuration"
        )
        self.assertEqual(provenance.dataset_id, "DS_F006_ENDPOINT_BENCH_V1")
        self.assertEqual(
            provenance.applicable_domain["casting_speed_max_m_s"], 0.05
        )

    def test_benchmarks_recompute_from_independent_arithmetic(self):
        rows = endpoint_benchmark_cases()
        self.assertEqual(len(rows), 3)
        configs = {
            config_id: approved_machine_configuration(config_id)[0]
            for config_id in {row["machine_configuration_id"] for row in rows}
        }
        for row in rows:
            inputs = row["input_json"]
            expected = row["expected_json"]
            tolerance = row["tolerance_json"]
            curve = inputs["center_solid_fraction_curve"]
            speed = float(inputs["casting_speed_m_s"])
            event_time = _event_time(
                curve, float(inputs["endpoint_solid_fraction_threshold"])
            )
            position = speed * event_time
            machine_length = float(
                configs[row["machine_configuration_id"]][
                    "effective_metallurgical_length_m"
                ]
            )
            exit_fraction = _curve_value(curve, machine_length / speed)
            status = "inside_machine" if position < machine_length else (
                "at_machine_exit" if math.isclose(position, machine_length, abs_tol=1e-12)
                else "beyond_machine_exit"
            )
            self.assertAlmostEqual(
                event_time, float(expected["solidification_end_time_s"]),
                delta=float(tolerance["time_s"]),
            )
            self.assertAlmostEqual(
                position, float(expected["solidification_end_position_m"]),
                delta=float(tolerance["position_m"]),
            )
            self.assertAlmostEqual(
                exit_fraction, float(expected["exit_center_solid_fraction"]),
                delta=float(tolerance["solid_fraction"]),
            )
            self.assertEqual(status, expected["equipment_status"])

    def test_missing_configuration_fails_closed_without_file_fallback(self):
        with self.assertRaises(RepositoryError) as raised:
            approved_machine_configuration("DOES_NOT_EXIST")
        self.assertEqual(raised.exception.error_code, "MISSING_DATA")

    def test_import_is_idempotent_and_conflict_checked(self):
        payload, asset_sha = load_asset()
        stats = {"inserted": 0, "unchanged": 0}
        connection = self.connection()
        connection.autocommit = False
        try:
            with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                import_rows(cur, payload, asset_sha, stats)
            self.assertEqual(stats, {"inserted": 0, "unchanged": 6})
        finally:
            connection.rollback()
            connection.close()


if __name__ == "__main__":
    unittest.main()
