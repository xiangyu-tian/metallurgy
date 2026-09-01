"""P1-W5B thermal-data qualification tests in the current runtime baseline."""
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

from database.import_casting_thermal_data import import_rows, load_asset
from models_core import ModelRegistry
from models_core.repositories.casting_thermal_repository import (
    approved_property_set,
    benchmark_cases,
    boundary_profile,
    property_bundle,
    property_value,
)
from models_core.repositories.reference_repository import RepositoryError


ASSET = TOOLS / "models_core" / "data" / "casting_thermal_reference_v1.json"
MIGRATION = ROOT / "database" / "migrations" / "008_casting_thermal_property_data.sql"
NIST_SET = "NIST_SRM1155A_316L_2019_V1"
BENCH_SET = "F005_ANALYTIC_CONSTANT_V1"


class P1W5BCastingThermalDataTests(unittest.TestCase):
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

    def test_data_layer_integrates_with_current_runtime_counts(self):
        registry = ModelRegistry()
        registry.discover()
        self.assertEqual(registry.get_counts(), {
            "registered_count": 74,
            "runtime_tool_count": 74,
            "catalog_coverage_count": 68,
            "qualified_executable_count": 74,
            "implementation_qualified_count": 74,
            "data_required_count": 30,
            "data_qualified_count": 30,
            "interface_qualified_count": 74,
            "fully_eligible_count": 74,
        })

    def test_source_asset_is_versioned_licensed_and_excludes_restricted_ds042(self):
        payload, asset_sha = load_asset()
        self.assertEqual(asset_sha, hashlib.sha256(ASSET.read_bytes()).hexdigest())
        nist = next(row for row in payload["datasets"]
                    if row["dataset_id"] == "DS_NIST_SRM1155A_316L_2019")
        self.assertEqual(nist["license"], "CC BY 4.0")
        self.assertEqual(
            nist["checksum"],
            "sha256:ae90ec5c55b1e4145ad8f70f3b77d3656ec6cbcc83c0684bc33e4cfef57266ff",
        )
        self.assertNotIn("DS042", json.dumps(payload, ensure_ascii=False))

    def test_migration_is_additive_only(self):
        sql = MIGRATION.read_text(encoding="utf-8").upper()
        for forbidden in ("DELETE FROM", "TRUNCATE", "DROP TABLE", "DROP SCHEMA", "UPDATE "):
            self.assertNotIn(forbidden, sql)
        for table in (
            "CASTING_MATERIAL_PROPERTY_SET",
            "CASTING_MATERIAL_PROPERTY_CORRELATION",
            "CASTING_BOUNDARY_PROFILE",
            "CASTING_MODEL_BENCHMARK_CASE",
        ):
            self.assertIn(f"CREATE TABLE IF NOT EXISTS METALLURGY_V2.{table}", sql)

    def test_database_rows_and_approval_scopes_are_exact(self):
        with self.connection() as connection, connection.cursor() as cur:
            cur.execute("SELECT count(*) FROM metallurgy_v2.casting_material_property_set")
            self.assertEqual(cur.fetchone()[0], 2)
            cur.execute("SELECT count(*) FROM metallurgy_v2.casting_material_property_correlation")
            self.assertEqual(cur.fetchone()[0], 15)
            cur.execute("SELECT count(*) FROM metallurgy_v2.casting_boundary_profile")
            self.assertEqual(cur.fetchone()[0], 3)
            cur.execute("SELECT count(*) FROM metallurgy_v2.casting_model_benchmark_case")
            self.assertEqual(cur.fetchone()[0], 3)
        nist, provenance = approved_property_set(NIST_SET)
        self.assertEqual(nist["usage_scope"], "REFERENCE_VALIDATION_ONLY")
        self.assertEqual(float(nist["solidus_temperature_k"]), 1675.0)
        self.assertEqual(float(nist["liquidus_temperature_k"]), 1708.0)
        self.assertEqual(provenance.table, "metallurgy_v2.casting_material_property_set")
        bench, _ = approved_property_set(BENCH_SET)
        self.assertEqual(bench["usage_scope"], "MATHEMATICAL_BENCHMARK_ONLY")

    def test_nist_reported_values_and_si_conversions(self):
        density, provenance = property_value(NIST_SET, "DENSITY", 500.0)
        self.assertAlmostEqual(density["value"], 7770.0, places=9)
        self.assertEqual(density["unit"], "kg/m3")
        self.assertTrue(any(record.source_ref and "Table 3" in record.source_ref for record in provenance))

        enthalpy, _ = property_value(NIST_SET, "ENTHALPY", 1000.0)
        self.assertEqual(enthalpy["value"], 393000.0)
        self.assertEqual(enthalpy["unit"], "J/kg")

        cp, _ = property_value(NIST_SET, "HEAT_CAPACITY", 993.0)
        self.assertEqual(cp["value"], 605.0)
        self.assertEqual(cp["unit"], "J/(kg*K)")

        latent, _ = property_value(NIST_SET, "LATENT_HEAT", 1690.0)
        self.assertEqual(latent["value"], 290000.0)

    def test_derived_conductivity_is_transparent_and_independently_recomputed(self):
        result, provenance = property_value(NIST_SET, "THERMAL_CONDUCTIVITY", 1000.0)
        k_b = 1.380649e-23
        elementary_charge = 1.602176634e-19
        lorenz = math.pi ** 2 / 3 * (k_b / elementary_charge) ** 2
        expected = lorenz * 1000.0 / (1.223e-6)
        self.assertAlmostEqual(result["value"], expected, places=12)
        self.assertEqual(result["source_kind"], "DERIVED_MODEL_ESTIMATE")
        self.assertEqual(result["usage_scope"], "REFERENCE_VALIDATION_ONLY")
        self.assertTrue(any(record.source_ref and "not a direct" in record.source_ref
                            for record in provenance))

    def test_phase_fraction_boundaries_and_monotonicity(self):
        samples = [
            property_value(NIST_SET, "SOLID_FRACTION", temperature)[0]["value"]
            for temperature in (1600.0, 1675.0, 1691.5, 1708.0, 1800.0)
        ]
        self.assertEqual(samples, [1.0, 1.0, 0.5, 0.0, 0.0])
        self.assertTrue(all(left >= right for left, right in zip(samples, samples[1:])))

    def test_gaps_missing_properties_and_ranges_fail_without_fallback(self):
        for property_type, temperature, error_code in (
            ("DENSITY", 480.0, "OUT_OF_DOMAIN"),
            ("HEAT_CAPACITY", 1300.0, "OUT_OF_DOMAIN"),
            ("VISCOSITY", 1000.0, "MISSING_DATA"),
        ):
            with self.subTest(property_type=property_type, temperature=temperature):
                with self.assertRaises(RepositoryError) as raised:
                    property_value(NIST_SET, property_type, temperature)
                self.assertEqual(raised.exception.error_code, error_code)
        with self.assertRaises(RepositoryError) as raised:
            approved_property_set("DOES_NOT_EXIST")
        self.assertEqual(raised.exception.error_code, "MISSING_DATA")

    def test_analytic_property_bundle_and_boundary_profiles(self):
        bundle, provenance = property_bundle(
            BENCH_SET, 800.0, ("DENSITY", "HEAT_CAPACITY", "THERMAL_CONDUCTIVITY", "ENTHALPY")
        )
        alpha = (bundle["THERMAL_CONDUCTIVITY"]["value"]
                 / (bundle["DENSITY"]["value"] * bundle["HEAT_CAPACITY"]["value"]))
        self.assertEqual(alpha, 1e-4)
        self.assertEqual(bundle["ENTHALPY"]["value"], 500000.0)
        self.assertGreaterEqual(len(provenance), 5)

        profile, source = boundary_profile("F005_BENCH_HEAT_FLUX_100KW_M2_V1", 1.0)
        self.assertEqual(profile["value"], 100000.0)
        self.assertEqual(profile["sign_convention"], "outward_positive")
        self.assertEqual(profile["usage_scope"], "MATHEMATICAL_BENCHMARK_ONLY")
        self.assertEqual(source[0].table, "metallurgy_v2.casting_boundary_profile")
        with self.assertRaises(RepositoryError) as raised:
            boundary_profile("F005_BENCH_HEAT_FLUX_100KW_M2_V1", 11.0)
        self.assertEqual(raised.exception.error_code, "OUT_OF_DOMAIN")

    def test_benchmark_expected_values_recompute_from_independent_math(self):
        cases = {row["benchmark_id"]: row for row in benchmark_cases("F005")}
        self.assertEqual(len(cases), 3)
        dirichlet = cases["F005-ANALYTIC-DIRICHLET-SEMI-INFINITE-V1"]
        expected = 300.0 + (800.0 - 300.0) * math.erf(0.5)
        self.assertAlmostEqual(float(dirichlet["expected_json"]["temperature_at_sample_k"]),
                               expected, places=12)
        neumann = cases["F005-ANALYTIC-NEUMANN-SURFACE-V1"]
        expected_surface = 800.0 - 2 * 100000.0 * math.sqrt(1e-4) / (100.0 * math.sqrt(math.pi))
        self.assertAlmostEqual(float(neumann["expected_json"]["surface_temperature_k"]),
                               expected_surface, places=12)

    def test_import_is_idempotent_and_conflict_checked(self):
        payload, asset_sha = load_asset()
        stats = {"inserted": 0, "unchanged": 0}
        connection = self.connection()
        connection.autocommit = False
        try:
            with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                import_rows(cur, payload, asset_sha, stats)
            self.assertEqual(stats, {"inserted": 0, "unchanged": 25})
        finally:
            connection.rollback()
            connection.close()


if __name__ == "__main__":
    unittest.main()
