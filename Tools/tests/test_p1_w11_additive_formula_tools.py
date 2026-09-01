"""P1-W11 admission, mathematical-property and forced function-call tests."""

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


W11_IDS = {"B026", "B027", "C012", "D022", "H002", "H003"}
R_J_MOL_K = 8.31446261815324


def normal_payload(registry: ModelRegistry, code: str) -> dict:
    return next(case["input"] for case in registry.get(code).qualification_cases if case["kind"] == "normal")


class P1W11AdditiveFormulaToolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = ModelRegistry()
        cls.registry.discover()
        cls.client = TestClient(app)

    def ok(self, code: str, payload: dict):
        result = self.registry.invoke(code, payload)
        self.assertTrue(result.success, result.error)
        return result.result

    def test_six_tools_pass_all_gates_and_dynamic_counts(self):
        self.assertEqual(self.registry.get_counts(), {
            "registered_count": 86,
            "runtime_tool_count": 86,
            "catalog_coverage_count": 68,
            "qualified_executable_count": 86,
            "implementation_qualified_count": 86,
            "data_required_count": 30,
            "data_qualified_count": 30,
            "interface_qualified_count": 86,
            "fully_eligible_count": 86,
        })
        for code in W11_IDS:
            with self.subTest(code=code):
                admission = self.registry.qualification_report(code)
                eligibility = self.registry.eligibility_report(code)
                self.assertTrue(admission["qualified"], admission["reasons"])
                self.assertGreaterEqual(admission["normal_cases_passed"], 3)
                self.assertGreaterEqual(admission["boundary_or_failure_cases_passed"], 2)
                self.assertTrue(eligibility["fully_eligible"], eligibility)
                self.assertFalse(eligibility["data_required"])
                model = self.registry.get(code)
                self.assertIsNone(model.catalog_id)
                self.assertEqual(model.catalog_mapping_status, "extension")
                self.assertFalse(model.catalog_coverage)
                self.assertTrue(model.source_records)
                self.assertTrue(model.independent_validation)
                self.assertTrue(model.relations)
                self.assertTrue(model.tool_uid.startswith(f"metallurgy.extension.{code.lower()}."))

    def test_b026_cubic_eos_fugacity_and_phase_root_properties(self):
        payload = {
            "temperature_k": 280,
            "pressure_pa": 1e6,
            "critical_temperature_k": 304.1282,
            "critical_pressure_pa": 7.3773e6,
            "acentric_factor": 0.22394,
            "phase_root": "vapor",
        }
        vapor = self.ok("B026", payload)
        liquid = self.ok("B026", {**payload, "phase_root": "liquid"})
        stable = self.ok("B026", {**payload, "phase_root": "stable"})
        self.assertEqual(vapor["physical_root_count"], 3)
        self.assertEqual(vapor["compressibility_factor"], max(vapor["real_compressibility_roots"]))
        self.assertEqual(liquid["compressibility_factor"], min(liquid["real_compressibility_roots"]))
        self.assertIn(stable["compressibility_factor"], vapor["real_compressibility_roots"])
        self.assertAlmostEqual(vapor["fugacity_pa"], payload["pressure_pa"] * vapor["fugacity_coefficient"], places=8)
        self.assertLess(abs(vapor["selected_cubic_residual"]), 1e-10)
        self.assertLess(abs(vapor["pressure_residual_pa"]), payload["pressure_pa"] * 1e-8)
        low_pressure = self.registry.invoke("B026", {
            **payload, "temperature_k": 300, "pressure_pa": 1, "phase_root": "vapor",
        })
        self.assertTrue(low_pressure.success, low_pressure.error)
        self.assertFalse(low_pressure.boundary_check.passed)
        self.assertAlmostEqual(low_pressure.result["compressibility_factor"], 1, delta=1e-6)
        self.assertAlmostEqual(low_pressure.result["fugacity_coefficient"], 1, delta=1e-6)

    def test_b027_bubble_dew_closure_and_pressure_temperature_roundtrip(self):
        payload = normal_payload(self.registry, "B027")
        pressure_result = self.ok("B027", payload)
        temperature_result = self.ok("B027", {
            "mode": "bubble_temperature",
            "components": payload["components"],
            "pressure_kpa": pressure_result["equilibrium_pressure_kpa"],
        })
        self.assertAlmostEqual(temperature_result["equilibrium_temperature_k"], payload["temperature_k"], places=7)
        for result in (pressure_result, temperature_result):
            self.assertAlmostEqual(sum(result["feed_mole_fractions"].values()), 1, places=12)
            self.assertAlmostEqual(sum(result["equilibrium_mole_fractions"].values()), 1, places=12)
            self.assertLess(abs(result["phase_equilibrium_residual"]), 1e-8)
        expected_pressure = sum(
            pressure_result["feed_mole_fractions"][name] * pressure_result["saturation_pressures_kpa"][name]
            for name in pressure_result["feed_mole_fractions"]
        )
        self.assertAlmostEqual(pressure_result["equilibrium_pressure_kpa"], expected_pressure, places=12)

    def test_c011_to_c012_real_chain_and_ranz_marshall_scaling(self):
        dimensionless = self.ok("C011", {
            "density_kg_m3": 1.2,
            "velocity_m_s": 0.02,
            "characteristic_length_m": 0.1,
            "dynamic_viscosity_pa_s": 1.8e-5,
            "specific_heat_j_kg_k": 1005,
            "thermal_conductivity_w_m_k": 0.025,
            "diffusivity_m2_s": 2e-5,
        })
        transfer = self.ok("C012", {
            "reynolds_number": dimensionless["reynolds_number"],
            "characteristic_diameter_m": 0.1,
            "prandtl_number": dimensionless["prandtl_number"],
            "thermal_conductivity_w_m_k": 0.025,
            "schmidt_number": dimensionless["schmidt_number"],
            "mass_diffusivity_m2_s": 2e-5,
        })
        self.assertAlmostEqual(transfer["heat_transfer_coefficient_w_m2_k"], transfer["nusselt_number"] * 0.025 / 0.1, places=12)
        self.assertAlmostEqual(transfer["mass_transfer_coefficient_m_s"], transfer["sherwood_number"] * 2e-5 / 0.1, places=12)
        low = self.ok("C012", {"reynolds_number": 25, "characteristic_diameter_m": 0.01, "prandtl_number": 1, "thermal_conductivity_w_m_k": 0.1})
        high = self.ok("C012", {"reynolds_number": 100, "characteristic_diameter_m": 0.01, "prandtl_number": 1, "thermal_conductivity_w_m_k": 0.1})
        self.assertAlmostEqual(high["nusselt_number"] - 2, 2 * (low["nusselt_number"] - 2), places=12)

    def test_d022_element_closure_and_mass_scaling_invariance(self):
        payload = normal_payload(self.registry, "D022")
        result = self.ok("D022", payload)
        self.assertAlmostEqual(
            result["input_iron_mass_kg"],
            result["steel_iron_mass_kg"] + result["known_loss_iron_mass_kg"] + result["unaccounted_iron_mass_kg"],
            places=9,
        )
        self.assertAlmostEqual(
            result["iron_recovery_fraction"] + result["known_loss_fraction_of_input_iron"] + result["unaccounted_fraction_of_input_iron"],
            1,
            places=12,
        )
        scale = 3.5
        scaled = self.ok("D022", {
            **payload,
            "charge_streams": [{**item, "mass_kg": item["mass_kg"] * scale} for item in payload["charge_streams"]],
            "steel_mass_kg": payload["steel_mass_kg"] * scale,
            "loss_streams": [{**item, "mass_kg": item["mass_kg"] * scale} for item in payload["loss_streams"]],
        })
        for field in ("steel_mass_yield_fraction", "iron_recovery_fraction", "known_loss_fraction_of_input_iron", "unaccounted_fraction_of_input_iron"):
            self.assertAlmostEqual(scaled[field], result[field], places=12)

    def test_h002_sulfur_balance_partition_identity_and_monotonicity(self):
        payload = normal_payload(self.registry, "H002")
        result = self.ok("H002", payload)
        self.assertAlmostEqual(
            result["initial_total_sulfur_mass_kg"],
            result["final_steel_sulfur_mass_kg"] + result["final_slag_sulfur_mass_kg"],
            places=12,
        )
        self.assertAlmostEqual(
            result["equilibrium_slag_sulfur_mass_fraction"] / result["equilibrium_steel_sulfur_mass_fraction"],
            payload["sulfur_partition_ratio"],
            places=12,
        )
        higher_partition = self.ok("H002", {**payload, "sulfur_partition_ratio": 2 * payload["sulfur_partition_ratio"]})
        more_slag = self.ok("H002", {**payload, "slag_mass_kg": 2 * payload["slag_mass_kg"]})
        self.assertLess(higher_partition["equilibrium_steel_sulfur_mass_fraction"], result["equilibrium_steel_sulfur_mass_fraction"])
        self.assertLess(more_slag["equilibrium_steel_sulfur_mass_fraction"], result["equilibrium_steel_sulfur_mass_fraction"])

    def test_h003_power_formula_and_monotonic_mixing_time(self):
        payload = normal_payload(self.registry, "H003")
        result = self.ok("H003", payload)
        log_factor = math.log(1 + payload["injection_depth_m"] / (1.46e-5 * payload["surface_pressure_pa"]))
        expected_power = 6.18 * payload["argon_flow_nm3_min"] * payload["steel_temperature_k"] / payload["steel_mass_t"] * log_factor
        self.assertAlmostEqual(result["specific_stirring_power_w_t"], expected_power, places=12)
        self.assertAlmostEqual(result["mixing_time_s"], 800 * expected_power ** -0.4, places=12)
        more_flow = self.ok("H003", {**payload, "argon_flow_nm3_min": 2 * payload["argon_flow_nm3_min"]})
        more_mass = self.ok("H003", {**payload, "steel_mass_t": 2 * payload["steel_mass_t"]})
        self.assertLess(more_flow["mixing_time_s"], result["mixing_time_s"])
        self.assertGreater(more_mass["mixing_time_s"], result["mixing_time_s"])

    def test_schema_http_function_call_and_forced_route_for_each_new_tool(self):
        manifest = self.client.get("/api/v1/tools").json()
        self.assertEqual(manifest["total"], 86)
        self.assertEqual(manifest["catalog_coverage_count"], 68)
        definitions = {item["model_code"]: item for item in manifest["tools"]}
        for code in sorted(W11_IDS):
            with self.subTest(code=code):
                payload = normal_payload(self.registry, code)
                definition = definitions[code]
                self.assertTrue(definition["fully_eligible"])
                self.assertIsNone(definition["catalog_id"])
                self.assertFalse(definition["function"]["parameters"]["additionalProperties"])
                response = self.client.post(
                    f"/api/v1/tools/{definition['function']['name']}/call",
                    json={"arguments": payload},
                )
                self.assertEqual(response.status_code, 200, response.text)
                self.assertEqual(response.json()["model_code"], code)
                self.assertEqual(response.json()["status"], "success")
                forced = self.client.post("/api/v1/experiments/run", json={
                    "user_query": f"强制调用{code}，不得使用其他工具。",
                    "mode": "forced",
                    "model_code": code,
                    "arguments": payload,
                    "llm_name": "isolated-http-contract-test",
                    "prompt_version": "p1-w11-v1",
                })
                self.assertEqual(forced.status_code, 200, forced.text)
                self.assertEqual(forced.json()["selected_model"], code)
                self.assertEqual(forced.json()["execution_result"]["status"], "success")

    def test_provider_forced_case_manifest_has_one_case_per_tool(self):
        path = TOOLS / "benchmarks" / "llm_tool_call_cases_p1_w11.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual({case["model_code"] for case in payload["cases"]}, W11_IDS)
        self.assertEqual(len(payload["cases"]), 6)
        for case in payload["cases"]:
            self.assertTrue(case["force_tool_choice"])
            self.assertTrue(case["expected"])


if __name__ == "__main__":
    unittest.main()
