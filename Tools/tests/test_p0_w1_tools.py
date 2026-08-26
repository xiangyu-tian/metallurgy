"""Scientific and interface acceptance for catalog P0-W1 tools."""

from __future__ import annotations

import copy
import math
import os
import sys
import unittest


TOOLS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, TOOLS_DIR)

from fastapi.testclient import TestClient
from models_core import ModelRegistry
from models_server import app


W1_IDS = {"A101", "A008", "D021", "D004"}


class P0W1AcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = ModelRegistry()
        cls.registry.discover()
        cls.client = TestClient(app)

    def ok(self, code, payload):
        result = self.registry.invoke(code, payload)
        self.assertTrue(result.success, result.error)
        self.assertTrue(result.provenance)
        return result

    def fail(self, code, payload, error_code=None):
        result = self.registry.invoke(code, payload)
        self.assertFalse(result.success)
        if error_code:
            self.assertEqual(result.error_code, error_code)
        self.assertTrue(result.provenance)
        return result

    def test_all_four_pass_five_case_gate_and_catalog_identity(self):
        expected_catalog = {"A101": "A007", "A008": "A008", "D021": "D001", "D004": "D004"}
        for code in sorted(W1_IDS):
            with self.subTest(code=code):
                report = self.registry.eligibility_report(code)
                self.assertTrue(report["fully_eligible"], report)
                qualification = self.registry.qualification_report(code)
                self.assertEqual(qualification["normal_cases_passed"], 3)
                self.assertEqual(qualification["boundary_or_failure_cases_passed"], 2)
                model = self.registry.get(code)
                self.assertEqual(model.catalog_id, expected_catalog[code])
                self.assertTrue(model.catalog_coverage)

    def test_a101_charge_identity_mixed_valence_and_failures(self):
        magnetite = self.ok("A101", {
            "formula": "Fe3O4",
            "oxidation_states": {
                "Fe": [
                    {"oxidation_state": 3, "count": 2},
                    {"oxidation_state": 2, "count": 1},
                ],
                "O": -2,
            },
        }).result
        self.assertTrue(magnetite["balanced"])
        self.assertTrue(magnetite["mixed_valence"])
        self.assertAlmostEqual(
            magnetite["calculated_charge"],
            sum(magnetite["charge_contributions"].values()),
            places=12,
        )

        reordered = self.ok("A101", {
            "formula": "Fe3O4",
            "oxidation_states": {
                "Fe": [
                    {"oxidation_state": 2, "count": 1},
                    {"oxidation_state": 3, "count": 2},
                ],
                "O": -2,
            },
        }).result
        self.assertEqual(reordered["calculated_charge"], magnetite["calculated_charge"])

        unbalanced = self.ok("A101", {
            "formula": "FeO", "oxidation_states": {"Fe": 3, "O": -2}
        })
        self.assertFalse(unbalanced.result["balanced"])
        self.assertFalse(unbalanced.boundary_check.passed)
        self.fail("A101", {"formula": "FeO", "oxidation_states": {"Fe": 2}})
        self.fail("A101", {
            "formula": "Fe3O4",
            "oxidation_states": {"Fe": [{"oxidation_state": 2, "count": 1}], "O": -2},
        })

    def test_a008_preserves_observations_and_knn_is_permutation_invariant(self):
        payload = {
            "data": [[0, 0], [1, 1], [1.1, None], [10, 10]],
            "columns": ["x", "y"],
            "column_units": {"x": "1", "y": "1"},
            "method": "knn",
            "n_neighbors": 1,
        }
        result = self.ok("A008", payload).result
        self.assertAlmostEqual(result["imputed_data"][2][1], 1.0, places=12)
        for i, row in enumerate(payload["data"]):
            for j, value in enumerate(row):
                if value is not None:
                    self.assertEqual(result["imputed_data"][i][j], value)

        permutation = [3, 2, 0, 1]
        permuted = copy.deepcopy(payload)
        permuted["data"] = [payload["data"][index] for index in permutation]
        permuted_result = self.ok("A008", permuted).result
        target_row = permutation.index(2)
        self.assertAlmostEqual(permuted_result["imputed_data"][target_row][1], 1.0, places=12)

        mean = self.ok("A008", {
            "data": [[1], [None], [3]],
            "columns": ["x"], "column_units": {"x": "kg"}, "method": "mean",
        }).result
        self.assertEqual(mean["imputed_data"][1][0], 2.0)
        self.fail("A008", {
            "data": [[None, 1], [None, 2]],
            "columns": ["x", "y"], "column_units": {"x": "1", "y": "1"}, "method": "mean",
        }, "OUT_OF_DOMAIN")

    def test_d021_element_closure_scale_invariance_and_single_unknown(self):
        payload = {
            "basis": "per_heat",
            "input_streams": [{"name": "hot_metal", "category": "hot_metal", "mass_kg": 100, "composition": {"Fe": 0.96, "C": 0.04}}],
            "output_streams": [
                {"name": "steel", "category": "steel", "mass_kg": 96, "composition": {"Fe": 1}},
                {"name": "carbon", "category": "offgas", "mass_kg": 4, "composition": {"C": 1}},
            ],
        }
        base = self.ok("D021", payload).result
        self.assertTrue(base["passed"])
        self.assertAlmostEqual(base["steel_yield"], 0.96, places=12)
        self.assertTrue(all(abs(x["residual_kg"]) <= 1e-12 for x in base["element_balances"].values()))

        scaled = copy.deepcopy(payload)
        for stream in scaled["input_streams"] + scaled["output_streams"]:
            stream["mass_kg"] *= 10
        scaled_result = self.ok("D021", scaled).result
        self.assertAlmostEqual(scaled_result["mass_closure_rate"], base["mass_closure_rate"], places=12)
        self.assertAlmostEqual(scaled_result["steel_yield"], base["steel_yield"], places=12)

        solved = self.ok("D021", {
            "basis": "per_heat",
            "input_streams": [{"name": "iron", "category": "hot_metal", "mass_kg": 100, "composition": {"Fe": 1}}],
            "output_streams": [{"name": "steel", "category": "steel", "composition": {"Fe": 1}}],
            "solve_stream_name": "steel", "solve_element": "Fe",
        }).result
        self.assertEqual(solved["solved_stream"]["mass_kg"], 100.0)
        self.assertTrue(solved["passed"])

        boundary = self.ok("D021", {
            "basis": "per_heat",
            "input_streams": [{"name": "iron", "category": "hot_metal", "mass_kg": 100, "composition": {"Fe": 1}}],
            "output_streams": [{"name": "steel", "category": "steel", "mass_kg": 90, "composition": {"Fe": 1}}],
        })
        self.assertFalse(boundary.result["passed"])
        self.assertFalse(boundary.boundary_check.passed)

    def test_d004_substitution_scale_invariance_and_infeasible_failure(self):
        payload = {
            "existing_oxide_masses_kg": {"CaO": 10, "SiO2": 20, "MgO": 1, "Other": 9},
            "lime_assay": {"CaO": 0.9, "SiO2": 0.05, "MgO": 0.02, "Other": 0.03},
            "dolomite_assay": {"CaO": 0.55, "SiO2": 0.05, "MgO": 0.35, "Other": 0.05},
            "target_basicity": 1.0481927710843373,
            "target_mgo_fraction": 0.053636363636363635,
        }
        result = self.ok("D004", payload).result
        self.assertAlmostEqual(result["lime_addition_kg"], 10, places=10)
        self.assertAlmostEqual(result["dolomite_addition_kg"], 5, places=10)
        self.assertAlmostEqual(result["achieved_basicity"], payload["target_basicity"], places=12)
        self.assertAlmostEqual(result["achieved_mgo_fraction"], payload["target_mgo_fraction"], places=12)

        scaled = copy.deepcopy(payload)
        scaled["existing_oxide_masses_kg"] = {
            key: value * 7 for key, value in payload["existing_oxide_masses_kg"].items()
        }
        scaled_result = self.ok("D004", scaled).result
        self.assertAlmostEqual(scaled_result["lime_addition_kg"], 70, places=9)
        self.assertAlmostEqual(scaled_result["dolomite_addition_kg"], 35, places=9)
        self.assertAlmostEqual(scaled_result["achieved_basicity"], result["achieved_basicity"], places=12)

        self.fail("D004", {
            "existing_oxide_masses_kg": {"CaO": 10, "SiO2": 20, "MgO": 1, "Other": 9},
            "lime_assay": {"CaO": 0.8, "SiO2": 0.1, "MgO": 0.05, "Other": 0.05},
            "dolomite_assay": {"CaO": 0.8, "SiO2": 0.1, "MgO": 0.05, "Other": 0.05},
            "target_basicity": 2, "target_mgo_fraction": 0.08,
        }, "NUMERICAL_ERROR")

    def test_unknown_fields_are_rejected_as_schema_declares(self):
        self.fail("A101", {
            "formula": "Al2O3", "oxidation_states": {"Al": 3, "O": -2}, "hidden_default": 1,
        }, "INVALID_INPUT")

    def test_all_four_execute_through_uniform_http_tool_route(self):
        for code in sorted(W1_IDS):
            model = self.registry.get(code)
            definition = model.get_tool_definition(self.registry.eligibility_report(code))
            normal = next(case for case in model.qualification_cases if case["kind"] == "normal")
            with self.subTest(code=code):
                response = self.client.post(
                    f"/api/v1/tools/{definition['function']['name']}/call",
                    json={"arguments": normal["input"]},
                )
                self.assertEqual(response.status_code, 200, response.text)
                body = response.json()
                self.assertEqual(body["status"], "success")
                self.assertEqual(body["model_code"], code)
                self.assertEqual(body["catalog_id"], model.catalog_id)
                self.assertTrue(body["execution_id"])


if __name__ == "__main__":
    unittest.main()
