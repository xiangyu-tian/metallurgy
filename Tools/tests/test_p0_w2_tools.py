"""P0-W2 scientific and HTTP qualification tests for E001--E004."""

from __future__ import annotations

import copy
import math
import os
import sys
import unittest

from fastapi.testclient import TestClient


TOOLS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, TOOLS_DIR)

from models_core import ModelRegistry
from models_server import app


W2_IDS = {"E001", "E002", "E003", "E004"}


class P0W2BlastFurnaceToolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = ModelRegistry()
        cls.registry.discover()

    def ok(self, code, payload):
        result = self.registry.invoke(code, payload)
        self.assertTrue(result.success, result.error)
        self.assertTrue(result.provenance)
        return result

    def test_every_w2_tool_has_three_normal_and_two_boundary_or_failure_cases(self):
        for code in sorted(W2_IDS):
            with self.subTest(code=code):
                report = self.registry.qualification_report(code)
                self.assertTrue(report["qualified"], report["reasons"])
                self.assertEqual(report["normal_cases_passed"], 3)
                self.assertEqual(report["boundary_or_failure_cases_passed"], 2)
                self.assertTrue(self.registry.eligibility_report(code)["fully_eligible"])

    def test_e001_mass_moisture_identity_and_scale_invariance(self):
        payload = {
            "basis": "per_hour",
            "input_streams": [
                {"name": "ore", "category": "ore", "mass_kg": 90, "moisture_fraction": 0.1},
                {"name": "coke", "category": "coke", "mass_kg": 10},
            ],
            "output_streams": [
                {"name": "iron", "category": "hot_metal", "mass_kg": 60},
                {"name": "slag", "category": "slag", "mass_kg": 30},
                {"name": "gas", "category": "top_gas", "mass_kg": 10},
            ],
        }
        result = self.ok("E001", payload).result
        self.assertAlmostEqual(result["total_input_mass_kg"], result["total_output_mass_kg"])
        self.assertAlmostEqual(
            result["total_input_dry_mass_kg"] + result["input_moisture_kg"],
            result["total_input_mass_kg"],
        )
        scaled = copy.deepcopy(payload)
        for stream in scaled["input_streams"] + scaled["output_streams"]:
            stream["mass_kg"] *= 7
        scaled_result = self.ok("E001", scaled).result
        self.assertAlmostEqual(result["mass_closure_rate"], scaled_result["mass_closure_rate"])
        self.assertAlmostEqual(result["burden_mass_kg_per_t_hot_metal"], scaled_result["burden_mass_kg_per_t_hot_metal"])

    def test_e002_iron_conservation_reduction_and_scale_invariance(self):
        payload = {
            "basis": "per_hour",
            "input_streams": [{"name": "ore", "category": "ore", "mass_kg": 100, "fe_mass_fraction": 0.7, "fe_oxidation_state": 3}],
            "output_streams": [
                {"name": "iron", "category": "hot_metal", "mass_kg": 68, "fe_mass_fraction": 1, "fe_oxidation_state": 0},
                {"name": "slag", "category": "slag", "mass_kg": 10, "fe_mass_fraction": 0.2, "fe_oxidation_state": 2},
            ],
        }
        result = self.ok("E002", payload).result
        self.assertAlmostEqual(result["fe_residual_kg"], 0)
        self.assertAlmostEqual(result["reduction_degree"], (210 - 4) / 210)
        scaled = copy.deepcopy(payload)
        for stream in scaled["input_streams"] + scaled["output_streams"]:
            stream["mass_kg"] *= 3
        scaled_result = self.ok("E002", scaled).result
        self.assertAlmostEqual(result["iron_yield"], scaled_result["iron_yield"])
        self.assertAlmostEqual(result["reduction_degree"], scaled_result["reduction_degree"])
        failure = self.registry.invoke("E002", self.registry.get("E002").qualification_cases[-1]["input"])
        self.assertFalse(failure.success)
        self.assertEqual(failure.error_code, "OUT_OF_DOMAIN")

    def test_e003_carbon_atom_count_scale_and_database_provenance(self):
        payload = {
            "basis": "per_hour",
            "material_inputs": [{"name": "coke", "category": "coke", "mass_kg": 12.011, "carbon_mass_fraction": 1}],
            "gas_outputs": [{"name": "gas", "amount_kmol": 1, "composition": {"CO": 0.25, "CO2": 0.25, "CH4": 0.5}}],
            "hot_metal_mass_kg": 1000,
        }
        result = self.ok("E003", payload)
        self.assertAlmostEqual(result.result["top_gas_carbon_kg"], 12.011, places=6)
        self.assertAlmostEqual(result.result["carbon_residual_kg"], 0, places=9)
        self.assertEqual(result.provenance[0].dataset_id, "DS_IUPAC_AW_2021")
        self.assertEqual(result.provenance[0].table, "metallurgy_v2.element_reference")
        scaled = copy.deepcopy(payload)
        scaled["material_inputs"][0]["mass_kg"] *= 2
        scaled["gas_outputs"][0]["amount_kmol"] *= 2
        scaled["hot_metal_mass_kg"] *= 2
        scaled_result = self.ok("E003", scaled).result
        self.assertAlmostEqual(result.result["carbon_closure_rate"], scaled_result["carbon_closure_rate"])
        self.assertAlmostEqual(result.result["carbon_input_kg_per_t_hot_metal"], scaled_result["carbon_input_kg_per_t_hot_metal"])

    def test_e004_oxygen_atom_count_allocation_and_database_provenance(self):
        payload = {
            "basis": "per_hour",
            "material_inputs": [
                {"name": "ore", "category": "ore", "mass_kg": 15.999, "oxygen_mass_fraction": 1},
                {"name": "blast", "category": "blast", "mass_kg": 15.999, "oxygen_mass_fraction": 1},
            ],
            "gas_outputs": [{"name": "gas", "amount_kmol": 1, "composition": {"CO2": 0.5, "H2O": 0.5}}],
            "reduced_ore_oxygen_kg": 15.999,
            "indirect_reduction_oxygen_kg": 10,
        }
        result = self.ok("E004", payload)
        self.assertAlmostEqual(result.result["total_output_oxygen_kg"], 1.5 * 15.999, places=6)
        self.assertAlmostEqual(
            result.result["direct_reduction_oxygen_kg"] + result.result["indirect_reduction_oxygen_kg"],
            result.result["reduced_ore_oxygen_kg"],
        )
        self.assertEqual(result.provenance[0].dataset_id, "DS_IUPAC_AW_2021")
        invalid = copy.deepcopy(payload)
        invalid["indirect_reduction_oxygen_kg"] = 20
        failed = self.registry.invoke("E004", invalid)
        self.assertFalse(failed.success)
        self.assertEqual(failed.error_code, "OUT_OF_DOMAIN")

    def test_w2_tools_execute_through_uniform_http_contract(self):
        client = TestClient(app)
        manifest = client.get("/api/v1/tools").json()
        self.assertEqual(manifest["total"], 67)
        for code in sorted(W2_IDS):
            model = self.registry.get(code)
            case = next(x for x in model.qualification_cases if x["kind"] == "normal")
            with self.subTest(code=code):
                response = client.post(f"/api/v1/tools/{model.tool_name}/call", json={"arguments": case["input"]})
                self.assertEqual(response.status_code, 200, response.text)
                body = response.json()
                self.assertEqual(body["status"], "success")
                self.assertEqual(body["model_code"], code)
                self.assertEqual(body["catalog_id"], code)
                self.assertEqual(body["tool_uid"], self.registry.get(code).tool_uid)


if __name__ == "__main__":
    unittest.main()
