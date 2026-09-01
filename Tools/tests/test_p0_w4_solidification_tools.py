"""Focused P0-W4 admission tests for F001, F002 and F004 only."""
from __future__ import annotations

import hashlib
import json
import os
import sys
import unittest
from pathlib import Path

import psycopg2
from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "Tools"
sys.path.insert(0, str(TOOLS))

from models_core import ModelRegistry
from models_core.repositories.solidification_repository import benchmark_cases
from models_server import app


W4_IDS = {"F001", "F002", "F004"}
ASSET = TOOLS / "models_core" / "data" / "calculation_assets" / "mc_fe_v2.059.pycalphad.tdb"
MANIFEST = ASSET.with_name("mc_fe_v2.059.manifest.json")


class P0W4SolidificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = ModelRegistry()
        cls.registry.discover()

    @staticmethod
    def connection():
        config = {"database": os.getenv("METALLURGY_DB_NAME", "metallurgy"),
                  "user": os.getenv("METALLURGY_DB_USER", "postgres"),
                  "password": os.getenv("METALLURGY_DB_PASSWORD", "")}
        if os.getenv("METALLURGY_DB_HOST"):
            config["host"] = os.environ["METALLURGY_DB_HOST"]
        if os.getenv("METALLURGY_DB_PORT"):
            config["port"] = int(os.environ["METALLURGY_DB_PORT"])
        return psycopg2.connect(**config)

    def invoke(self, code, payload):
        result = self.registry.invoke(code, payload)
        self.assertTrue(result.success, result.error)
        self.assertTrue(any(p.table == "metallurgy_v2.solidification_model_definition" for p in result.provenance))
        return result

    def test_w4_tools_remain_qualified_after_w5a(self):
        for code in W4_IDS:
            with self.subTest(code=code):
                report = self.registry.qualification_report(code)
                self.assertTrue(report["qualified"], report["reasons"])
                self.assertGreaterEqual(report["normal_cases_passed"], 3)
                self.assertGreaterEqual(report["boundary_or_failure_cases_passed"], 2)
                self.assertTrue(self.registry.eligibility_report(code)["fully_eligible"])
        self.assertEqual(self.registry.get_counts(), {
            "registered_count": 53, "runtime_tool_count": 53, "catalog_coverage_count": 49,
            "qualified_executable_count": 53, "implementation_qualified_count": 53,
            "data_required_count": 23, "data_qualified_count": 23,
            "interface_qualified_count": 53, "fully_eligible_count": 53,
        })

    def test_asset_hash_utf8_and_database_definition_are_identical(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertIn("mc_fe_v2.059", ASSET.read_text(encoding="utf-8")[:1000])
        self.assertEqual(hashlib.sha256(ASSET.read_bytes()).hexdigest(), manifest["asset_sha256"])
        with self.connection() as connection, connection.cursor() as cur:
            cur.execute("SELECT asset_sha256,is_approved FROM metallurgy_v2.solidification_model_definition WHERE model_asset_id=%s", (manifest["model_asset_id"],))
            row = cur.fetchone()
        self.assertEqual(row, (manifest["asset_sha256"], True))
        self.assertEqual(len(benchmark_cases(manifest["model_asset_id"])), 4)

    def test_migration_is_additive_only(self):
        sql = (ROOT / "database" / "migrations" / "007_solidification_model_data.sql").read_text(encoding="utf-8").upper()
        for forbidden in ("DELETE FROM", "TRUNCATE", "DROP TABLE", "DROP SCHEMA", "UPDATE "):
            self.assertNotIn(forbidden, sql)

    def test_f001_f002_endpoints_order_and_shared_calculation(self):
        payload = {"composition_wt_percent":{"C":0.1}, "temperature_min_k":1400,
                   "temperature_max_k":1900, "grid_step_k":5}
        liquidus = self.invoke("F001", payload).result
        solidus = self.invoke("F002", payload).result
        self.assertEqual(liquidus["liquidus_temperature_k"], solidus["liquidus_temperature_k"])
        self.assertEqual(liquidus["solidus_temperature_k"], solidus["solidus_temperature_k"])
        self.assertGreaterEqual(liquidus["liquidus_temperature_k"], liquidus["solidus_temperature_k"])
        self.assertEqual(liquidus["mushy_zone_width_k"], liquidus["liquidus_temperature_k"]-liquidus["solidus_temperature_k"])

    def test_f004_equilibrium_closure_monotonicity_and_endpoint_overlap(self):
        curve = self.invoke("F004", {"composition_wt_percent":{"C":0.1}, "model":"equilibrium",
                                      "start_temperature_k":1900,"end_temperature_k":1400,"step_k":5}).result
        for point in curve["curve"]:
            self.assertAlmostEqual(point["fraction_liquid"]+point["fraction_solid"], 1, places=10)
        ascending = list(reversed(curve["curve"]))
        self.assertTrue(all(left["fraction_liquid"] <= right["fraction_liquid"] + 1e-8
                            for left,right in zip(ascending,ascending[1:])))
        endpoint = self.invoke("F001", {"composition_wt_percent":{"C":0.1}, "temperature_min_k":1400,
                                         "temperature_max_k":1900,"grid_step_k":5}).result
        self.assertEqual(curve["liquidus_temperature_k"], endpoint["liquidus_temperature_k"])

    def test_f004_scheil_converges_and_phase_amounts_close(self):
        result = self.invoke("F004", {"composition_wt_percent":{"C":0.1}, "model":"scheil",
                                       "start_temperature_k":1900,"end_temperature_k":1400,"step_k":5}).result
        self.assertTrue(result["converged"])
        self.assertEqual(result["residual_liquid_stop_fraction"], 0.005)
        for point in result["curve"]:
            self.assertAlmostEqual(sum(point["phase_fractions"].values()), 1, places=8)

    def test_domain_failures_and_boundary_warning_are_explicit(self):
        unsupported = self.registry.invoke("F001", {"composition_wt_percent":{"P":0.001}})
        self.assertFalse(unsupported.success); self.assertEqual(unsupported.error_code,"OUT_OF_DOMAIN")
        range_error = self.registry.invoke("F004", {"composition_wt_percent":{"C":0.1},
                                                     "start_temperature_k":1500,"end_temperature_k":1900})
        self.assertFalse(range_error.success); self.assertEqual(range_error.error_code,"TEMPERATURE_RANGE_ERROR")
        boundary = self.invoke("F002", {"composition_wt_percent":{"Cr":23.0},"grid_step_k":10})
        self.assertFalse(boundary.boundary_check.passed)

    def test_all_three_execute_through_uniform_llm_tool_route(self):
        client = TestClient(app)
        manifest = client.get("/api/v1/tools").json()
        self.assertEqual(manifest["total"], 53)
        payloads = {
            "F001":{"composition_wt_percent":{"C":0.1},"grid_step_k":5},
            "F002":{"composition_wt_percent":{"C":0.1},"grid_step_k":5},
            "F004":{"composition_wt_percent":{"C":0.1},"model":"equilibrium","step_k":5},
        }
        for code,payload in payloads.items():
            model = self.registry.get(code)
            response = client.post(f"/api/v1/tools/{model.tool_name}/call", json={"arguments":payload})
            self.assertEqual(response.status_code,200,response.text)
            body=response.json(); self.assertEqual(body["status"],"success"); self.assertEqual(body["model_code"],code)


if __name__ == "__main__":
    unittest.main()
