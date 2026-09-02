"""P1-W16 admission, scientific-property, HTTP and forced-call tests."""

from __future__ import annotations

import json
import math
import sys
import unittest
from pathlib import Path

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "Tools"
sys.path.insert(0, str(TOOLS))

from models_core import ModelRegistry
from models_server import app


W16_IDS = {"F009", "F011", "F014", "G003"}


def case_payload(registry: ModelRegistry, code: str, case_id: str | None = None) -> dict:
    cases = registry.get(code).qualification_cases
    if case_id is None:
        return next(case["input"] for case in cases if case["kind"] == "normal")
    return next(case["input"] for case in cases if case["id"] == case_id)


class P1W16CoolingSpeedStressHeatPDETests(unittest.TestCase):
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
            "registered_count": 113,
            "runtime_tool_count": 113,
            "catalog_coverage_count": 95,
            "qualified_executable_count": 113,
            "implementation_qualified_count": 113,
            "data_required_count": 35,
            "data_qualified_count": 35,
            "interface_qualified_count": 113,
            "fully_eligible_count": 113,
        })
        for code in sorted(W16_IDS):
            with self.subTest(code=code):
                admission = self.registry.qualification_report(code)
                eligibility = self.registry.eligibility_report(code)
                self.assertTrue(admission["qualified"], admission["reasons"])
                self.assertEqual(admission["normal_cases_passed"], 3)
                self.assertEqual(admission["boundary_or_failure_cases_passed"], 3)
                self.assertTrue(eligibility["fully_eligible"], eligibility)
                self.assertFalse(eligibility["data_required"])
                self.assertTrue(self.registry.get(code).catalog_coverage)

    def test_f009_bounded_proportional_projection_and_heat_balance(self):
        payload = case_payload(self.registry, "F009")
        output = self.ok("F009", payload).result
        flows = [row["water_flow_m3_h"] for row in output["zone_results"]]
        self.assertEqual(flows, [10.0, 20.0, 30.0])
        self.assertAlmostEqual(math.fsum(flows), payload["total_water_flow_m3_h"], places=12)
        expected_capacity = 60 * 998 / 3600 * 4.18 * 10
        self.assertAlmostEqual(output["total_heat_capacity_kw"], expected_capacity, places=12)
        capped = self.ok("F009", case_payload(self.registry, "F009", "F009-N2")).result
        self.assertAlmostEqual(capped["zone_results"][0]["water_flow_m3_h"], 10, places=12)
        self.assertAlmostEqual(capped["zone_results"][1]["water_flow_m3_h"], 40, places=12)
        self.assertTrue(capped["zone_results"][0]["at_maximum"])

    def test_f011_exact_constraint_intersection_and_monotonicity(self):
        payload = case_payload(self.registry, "F011")
        output = self.ok("F011", payload).result
        expected_cooling_limit = 2000 / (1 * 1.5 * 0.2 * 7400 * 50)
        self.assertAlmostEqual(output["recommended_casting_speed_m_s"], expected_cooling_limit, places=14)
        self.assertEqual(output["limiting_constraints"], ["cooling_power"])
        self.assertAlmostEqual(output["required_cooling_power_kw"], 2000, places=10)
        self.assertTrue(all(value >= -1e-9 for value in output["constraint_margins"].values()))
        wider = self.ok("F011", {
            **payload, "section_width_m": 3.0, "minimum_casting_speed_m_s": 0.005,
        }).result
        self.assertAlmostEqual(wider["speed_limits_m_s"]["cooling_power"], expected_cooling_limit / 2, places=14)
        longer = self.ok("F011", {**payload, "effective_machine_length_m": 60}).result
        self.assertAlmostEqual(longer["speed_limits_m_s"]["residence_time"], 2 * output["speed_limits_m_s"]["residence_time"], places=14)
        self.assertAlmostEqual(longer["speed_limits_m_s"]["shell_thickness"], 2 * output["speed_limits_m_s"]["shell_thickness"], places=14)

    def test_f014_thermoelastic_equilibrium_yield_and_strain_closure(self):
        output = self.ok("F014", case_payload(self.registry, "F014")).result
        self.assertAlmostEqual(output["common_total_strain"], 0.0025, places=14)
        self.assertAlmostEqual(output["equilibrium_residual_pa"], 0, delta=1e-6)
        self.assertAlmostEqual(output["maximum_tensile_stress_pa"], 500e6, delta=1e-3)
        self.assertAlmostEqual(output["maximum_compressive_stress_pa"], -500e6, delta=1e-3)
        for row in output["layer_results"]:
            self.assertLessEqual(abs(row["stress_pa"]), row["yield_strength_pa"] + 1e-6)
            self.assertAlmostEqual(
                row["common_total_strain"],
                row["thermal_strain"] + row["elastic_mechanical_strain"] + row["plastic_strain"],
                places=14,
            )
        yielded = self.ok("F014", case_payload(self.registry, "F014", "F014-N3")).result
        self.assertEqual(yielded["yielded_layer_count"], 1)
        self.assertAlmostEqual(yielded["layer_results"][0]["stress_pa"], -200e6, places=3)

    def test_g003_uniform_invariance_one_step_energy_and_symmetry(self):
        uniform = self.ok("G003", case_payload(self.registry, "G003")).result
        self.assertEqual([row["temperature_k"] for row in uniform["final_temperature_profile"]], [500.0] * 10)
        self.assertEqual(uniform["energy_closure_residual_j_m2"], 0)
        one_step = self.ok("G003", {
            "length_m": 1, "node_count": 4, "duration_s": 1, "time_step_s": 1,
            "density_kg_m3": 1000, "specific_heat_j_kg_k": 1000,
            "thermal_conductivity_w_m_k": 10, "initial_condition_mode": "uniform",
            "initial_temperature_k": 300, "left_boundary_type": "heat_flux",
            "left_heat_flux_into_domain_w_m2": 1000, "right_boundary_type": "heat_flux",
            "right_heat_flux_into_domain_w_m2": 0,
        }).result
        self.assertAlmostEqual(one_step["final_temperature_profile"][0]["temperature_k"], 300.004, places=12)
        self.assertAlmostEqual(one_step["stored_energy_change_j_m2"], 1000, places=6)
        self.assertAlmostEqual(one_step["cumulative_boundary_energy_in_j_m2"], 1000, places=12)
        self.assertLess(abs(one_step["energy_closure_relative"]), 1e-10)
        symmetric = self.ok("G003", {
            "length_m": 1, "node_count": 5, "duration_s": 2, "time_step_s": 0.1,
            "density_kg_m3": 1000, "specific_heat_j_kg_k": 1000,
            "thermal_conductivity_w_m_k": 10, "initial_condition_mode": "profile",
            "initial_temperature_profile_k": [300, 400, 500, 400, 300],
            "left_boundary_type": "heat_flux", "left_heat_flux_into_domain_w_m2": 0,
            "right_boundary_type": "heat_flux", "right_heat_flux_into_domain_w_m2": 0,
        }).result
        temperatures = [row["temperature_k"] for row in symmetric["final_temperature_profile"]]
        self.assertAlmostEqual(temperatures[0], temperatures[-1], places=12)
        self.assertAlmostEqual(temperatures[1], temperatures[-2], places=12)
        unstable = self.registry.invoke("G003", case_payload(self.registry, "G003", "G003-F1"))
        self.assertFalse(unstable.success)
        self.assertEqual(unstable.error_code, "OUT_OF_DOMAIN")

    def test_schema_real_http_and_forced_route_for_each_new_tool(self):
        response = self.client.get("/api/v1/tools")
        self.assertEqual(response.status_code, 200)
        manifest = response.json()
        self.assertEqual(manifest["total"], 113)
        self.assertEqual(manifest["catalog_coverage_count"], 95)
        definitions = {item["model_code"]: item for item in manifest["tools"]}
        for code in sorted(W16_IDS):
            with self.subTest(code=code):
                payload = case_payload(self.registry, code)
                definition = definitions[code]
                called = self.client.post(
                    f"/api/v1/tools/{definition['function']['name']}/call",
                    json={"arguments": payload},
                )
                self.assertEqual(called.status_code, 200, called.text)
                self.assertEqual(called.json()["status"], "success")
                self.assertEqual(called.json()["model_code"], code)
                forced = self.client.post("/api/v1/experiments/run", json={
                    "user_query": f"强制调用{code}，不得使用其他工具。",
                    "mode": "forced", "model_code": code, "arguments": payload,
                    "llm_name": "isolated-http-contract-test", "prompt_version": "p1-w16-v1",
                })
                self.assertEqual(forced.status_code, 200, forced.text)
                self.assertEqual(forced.json()["selected_model"], code)
                self.assertEqual(forced.json()["execution_result"]["status"], "success")

    def test_nested_schemas_and_provider_manifest_are_explicit(self):
        f009 = self.registry.get("F009").get_llm_input_schema()
        f014 = self.registry.get("F014").get_llm_input_schema()
        g003 = self.registry.get("G003").get_llm_input_schema()
        self.assertEqual(set(f009["properties"]["zones"]["items"]["required"]), {
            "name", "allocation_weight", "target_heat_removal_kw",
            "minimum_water_flow_m3_h", "maximum_water_flow_m3_h",
        })
        self.assertIn("yield_strength_pa", f014["properties"]["layers"]["items"]["required"])
        self.assertIn("left_boundary_type", g003["required"])
        self.assertIn("right_heat_transfer_coefficient_w_m2_k", g003["properties"])
        path = TOOLS / "benchmarks" / "llm_tool_call_cases_p1_w16.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual({case["model_code"] for case in payload["cases"]}, W16_IDS)
        self.assertEqual(len(payload["cases"]), 4)
        self.assertIn("not a research dataset", payload["purpose"])
        self.assertTrue(all(case["force_tool_choice"] and case["expected"] for case in payload["cases"]))


if __name__ == "__main__":
    unittest.main()
