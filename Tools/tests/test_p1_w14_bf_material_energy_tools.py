"""P1-W14 admission, scientific-property, database and forced-call tests."""

from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "Tools"
sys.path.insert(0, str(TOOLS))

from models_core import ModelRegistry
from models_server import app


W14_IDS = {"E010", "E013", "E106", "E109"}


def case_payload(registry: ModelRegistry, code: str, case_id: str | None = None) -> dict:
    cases = registry.get(code).qualification_cases
    if case_id is None:
        return next(case["input"] for case in cases if case["kind"] == "normal")
    return next(case["input"] for case in cases if case["id"] == case_id)


class P1W14BFMaterialEnergyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = ModelRegistry()
        cls.registry.discover()
        cls.client = TestClient(app)

    def ok(self, code: str, payload: dict):
        result = self.registry.invoke(code, payload)
        self.assertTrue(result.success, result.error)
        return result

    def test_four_tools_pass_all_gates_and_dynamic_counts(self):
        self.assertEqual(self.registry.get_counts(), {
            "registered_count": 120,
            "runtime_tool_count": 120,
            "catalog_coverage_count": 100,
            "qualified_executable_count": 120,
            "implementation_qualified_count": 120,
            "data_required_count": 37,
            "data_qualified_count": 37,
            "interface_qualified_count": 120,
            "fully_eligible_count": 120,
        })
        for code in sorted(W14_IDS):
            with self.subTest(code=code):
                admission = self.registry.qualification_report(code)
                eligibility = self.registry.eligibility_report(code)
                self.assertTrue(admission["qualified"], admission["reasons"])
                self.assertEqual(admission["normal_cases_passed"], 3)
                self.assertGreaterEqual(admission["boundary_or_failure_cases_passed"], 2)
                self.assertTrue(eligibility["fully_eligible"], eligibility)
                self.assertEqual(eligibility["data_required"], code == "E013")
                model = self.registry.get(code)
                self.assertTrue(model.source_records)
                self.assertTrue(model.independent_validation)
                self.assertTrue(model.relations)
                self.assertTrue(model.catalog_coverage)

    def test_catalog_identity_preserves_old_scope_variants(self):
        self.assertEqual(self.registry.get("E010").catalog_id, "E010")
        self.assertEqual(self.registry.get("E013").catalog_id, "E013")
        self.assertEqual(self.registry.get("E106").catalog_id, "E006")
        self.assertEqual(self.registry.get("E109").catalog_id, "E009")
        self.assertEqual(self.registry.get_by_catalog_id("E006", fully_eligible_only=False).model_id, "E106")
        self.assertEqual(self.registry.get_by_catalog_id("E009", fully_eligible_only=False).model_id, "E109")
        for old in ("E006", "E009"):
            self.assertTrue(self.registry.get(old).count_eligible)
            self.assertEqual(self.registry.get(old).catalog_mapping_status, "scope_variant")
            self.assertFalse(self.registry.get(old).catalog_coverage)

    def test_e010_four_atom_balance_compositions_and_scaling(self):
        payload = case_payload(self.registry, "E010")
        output = self.ok("E010", payload).result
        self.assertAlmostEqual(output["component_amounts_kmol"]["CO"], 1.61, places=12)
        self.assertAlmostEqual(output["component_amounts_kmol"]["CO2"], 0.94, places=12)
        self.assertAlmostEqual(output["co_reduction_oxygen_kmol"] + output["h2_reduction_oxygen_kmol"], output["indirect_reduction_oxygen_kmol"], places=12)
        self.assertAlmostEqual(sum(output["wet_mole_fractions"].values()), 1, places=12)
        self.assertAlmostEqual(sum(output["dry_mole_fractions"].values()), 1, places=12)
        for value in output["atom_balance_residuals_kmol"].values():
            self.assertAlmostEqual(value, 0, places=12)
        scaled = {
            **payload,
            "bosh_gas_kmol": {key: value * 4 for key, value in payload["bosh_gas_kmol"].items()},
            "reduced_ore_oxygen_kmol": payload["reduced_ore_oxygen_kmol"] * 4,
            "additional_top_gas_kmol": {key: value * 4 for key, value in payload["additional_top_gas_kmol"].items()},
        }
        scaled_output = self.ok("E010", scaled).result
        self.assertEqual(output["wet_mole_fractions"], scaled_output["wet_mole_fractions"])
        self.assertAlmostEqual(scaled_output["wet_total_gas_kmol"], output["wet_total_gas_kmol"] * 4, places=12)

    def test_e106_line_geometry_direct_reduction_and_scale_invariance(self):
        payload = case_payload(self.registry, "E106")
        output = self.ok("E106", payload).result
        self.assertAlmostEqual(output["actual_slope_mu"], 2.0, places=12)
        self.assertAlmostEqual(output["actual_y_intercept"], -1.0, places=12)
        self.assertAlmostEqual(output["top_gas_rate_mu"], 2.0, places=12)
        self.assertAlmostEqual(output["slope_closure_residual"], 0.0, places=12)
        self.assertAlmostEqual(output["direct_reduction_oxygen_per_iron"], output["actual_slope_mu"] + output["actual_y_intercept"], places=12)
        self.assertAlmostEqual(output["direct_reduction_oxygen_per_iron"] + output["indirect_reduction_oxygen_per_iron"], output["top_point_a"]["y"], places=12)
        p = output["energy_balance_point_p"]
        self.assertAlmostEqual(output["actual_slope_mu"] * p["x"] + output["actual_y_intercept"], p["y"], places=12)
        w = output["ideal_wustite_point_w"]
        self.assertAlmostEqual(output["ideal_slope_mu"] * w["x"] + output["ideal_y_intercept"], w["y"], places=12)
        scaled = {
            **payload,
            "iron_basis_kmol": payload["iron_basis_kmol"] * 7,
            "burden_oxygen_atom_kmol": payload["burden_oxygen_atom_kmol"] * 7,
            "hot_metal_oxygen_atom_kmol": payload["hot_metal_oxygen_atom_kmol"] * 7,
            "top_gas_kmol": {key: value * 7 for key, value in payload["top_gas_kmol"].items()},
        }
        scaled_output = self.ok("E106", scaled).result
        for key in ("actual_slope_mu", "actual_y_intercept", "top_gas_rate_mu", "direct_reduction_fraction"):
            self.assertAlmostEqual(output[key], scaled_output[key], places=12)

    def test_e109_three_limits_and_independent_constraint_back_calculation(self):
        payload = case_payload(self.registry, "E109")
        output = self.ok("E109", payload).result
        carbon_limit = payload["coal_fixed_carbon_fraction"] * payload["coal_burnout_fraction"] / payload["coke_fixed_carbon_fraction"]
        coal_net = payload["coal_lhv_mj_kg"] * payload["coal_heat_utilization_fraction"] - payload["coal_process_heat_demand_mj_kg"]
        coke_net = payload["coke_lhv_mj_kg"] * payload["coke_heat_utilization_fraction"] - payload["coke_process_heat_demand_mj_kg"]
        energy_limit = coal_net / coke_net
        structure_limit = (payload["baseline_coke_kg"] - payload["minimum_structural_coke_kg"]) / payload["coal_injection_kg"]
        self.assertAlmostEqual(output["fixed_carbon_replacement_limit"], carbon_limit, places=12)
        self.assertAlmostEqual(output["net_energy_replacement_limit"], energy_limit, places=12)
        self.assertAlmostEqual(output["structural_coke_replacement_limit"], structure_limit, places=12)
        self.assertAlmostEqual(output["selected_replacement_ratio"], min(carbon_limit, energy_limit, structure_limit), places=12)
        replaced = output["theoretical_coke_replaced_kg"]
        expected_ash = payload["coal_injection_kg"] * payload["coal_ash_fraction"] - replaced * payload["coke_ash_fraction"]
        self.assertAlmostEqual(output["incremental_ash_kg"], expected_ash, places=12)
        self.assertGreaterEqual(output["fixed_carbon_margin_kg"], -1e-12)
        self.assertGreaterEqual(output["net_energy_margin_mj"], -1e-12)
        self.assertGreaterEqual(output["structural_coke_margin_kg"], -1e-12)

    def test_e013_database_nasa7_energy_identity_and_monotonicity(self):
        payload = case_payload(self.registry, "E013")
        execution = self.ok("E013", payload)
        output = execution.result
        self.assertLess(abs(output["energy_balance_residual_kj"]), 1e-4)
        self.assertAlmostEqual(output["product_sensible_enthalpy_kj"], output["available_product_sensible_heat_kj"], places=4)
        self.assertAlmostEqual(sum(output["product_gas_mole_fractions"].values()), 1, places=12)
        for value in output["atom_balance_residuals_kmol"].values():
            self.assertAlmostEqual(value, 0, places=12)
        records = {(item.dataset_id, item.table) for item in execution.provenance}
        self.assertIn(("DS_NASA7_GRI30", "metallurgy_v2.thermodynamic_correlation"), records)
        self.assertTrue(all(item.record_id for item in execution.provenance))
        hotter = self.ok("E013", {**payload, "blast_temperature_k": payload["blast_temperature_k"] + 200}).result
        more_demand = self.ok("E013", {**payload, "fuel_process_heat_demand_mj": payload["fuel_process_heat_demand_mj"] + 10}).result
        self.assertGreater(hotter["raft_temperature_k"], output["raft_temperature_k"])
        self.assertLess(more_demand["raft_temperature_k"], output["raft_temperature_k"])

    def test_e013_database_unavailable_has_no_static_fallback(self):
        payload = case_payload(self.registry, "E013")
        with patch.dict(os.environ, {"METALLURGY_DB_HOST": "127.0.0.1", "METALLURGY_DB_PORT": "1"}):
            result = self.registry.invoke("E013", payload)
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, "DATA_BACKEND_UNAVAILABLE")

    def test_schema_real_http_and_forced_route_for_each_new_tool(self):
        response = self.client.get("/api/v1/tools")
        self.assertEqual(response.status_code, 200)
        manifest = response.json()
        self.assertEqual(manifest["total"], 120)
        self.assertEqual(manifest["catalog_coverage_count"], 100)
        definitions = {item["model_code"]: item for item in manifest["tools"]}
        for code in sorted(W14_IDS):
            with self.subTest(code=code):
                payload = case_payload(self.registry, code)
                definition = definitions[code]
                self.assertTrue(definition["fully_eligible"])
                self.assertFalse(definition["function"]["parameters"]["additionalProperties"])
                called = self.client.post(
                    f"/api/v1/tools/{definition['function']['name']}/call",
                    json={"arguments": payload},
                )
                self.assertEqual(called.status_code, 200, called.text)
                self.assertEqual(called.json()["status"], "success")
                self.assertEqual(called.json()["model_code"], code)
                forced = self.client.post("/api/v1/experiments/run", json={
                    "user_query": f"强制调用{code}，不得使用其他工具。",
                    "mode": "forced",
                    "model_code": code,
                    "arguments": payload,
                    "llm_name": "isolated-http-contract-test",
                    "prompt_version": "p1-w14-v1",
                })
                self.assertEqual(forced.status_code, 200, forced.text)
                body = forced.json()
                self.assertEqual(body["selected_model"], code)
                self.assertEqual(body["execution_result"]["status"], "success")

    def test_provider_forced_case_manifest_has_one_case_per_tool(self):
        path = TOOLS / "benchmarks" / "llm_tool_call_cases_p1_w14.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual({case["model_code"] for case in payload["cases"]}, W14_IDS)
        self.assertEqual(len(payload["cases"]), 4)
        self.assertIn("not a research dataset", payload["purpose"])
        for case in payload["cases"]:
            self.assertTrue(case["force_tool_choice"])
            self.assertTrue(case["expected"])


if __name__ == "__main__":
    unittest.main()
