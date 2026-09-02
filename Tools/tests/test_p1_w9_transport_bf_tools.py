"""P1-W9 admission, scientific-property and function-call tests for seven tools."""

from __future__ import annotations

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


W9_IDS = {"C009", "C010", "E006", "E007", "E009", "E012", "E014"}


def normal_payload(registry: ModelRegistry, code: str) -> dict:
    return next(case["input"] for case in registry.get(code).qualification_cases if case["kind"] == "normal")


class P1W9TransportBFTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = ModelRegistry()
        cls.registry.discover()
        cls.client = TestClient(app)

    def ok(self, code: str, payload: dict):
        result = self.registry.invoke(code, payload)
        self.assertTrue(result.success, result.error)
        return result.result

    def test_seven_tools_pass_all_gates_and_dynamic_counts(self):
        self.assertEqual(self.registry.get_counts(), {
            "registered_count": 109,
            "runtime_tool_count": 109,
            "catalog_coverage_count": 91,
            "qualified_executable_count": 109,
            "implementation_qualified_count": 109,
            "data_required_count": 35,
            "data_qualified_count": 35,
            "interface_qualified_count": 109,
            "fully_eligible_count": 109,
        })
        for code in W9_IDS:
            with self.subTest(code=code):
                admission = self.registry.qualification_report(code)
                eligibility = self.registry.eligibility_report(code)
                self.assertTrue(admission["qualified"], admission["reasons"])
                self.assertEqual(admission["normal_cases_passed"], 3)
                self.assertGreaterEqual(admission["boundary_or_failure_cases_passed"], 2)
                self.assertTrue(eligibility["fully_eligible"], eligibility)
                self.assertFalse(eligibility["data_required"])
                model = self.registry.get(code)
                self.assertEqual(model.catalog_id, code)
                if code in {"E006", "E009"}:
                    self.assertEqual(model.catalog_mapping_status, "scope_variant")
                    self.assertFalse(model.catalog_coverage)
                else:
                    self.assertEqual(model.catalog_mapping_status, "same")
                    self.assertTrue(model.catalog_coverage)
                self.assertTrue(model.source_records)
                self.assertTrue(model.independent_validation)
                self.assertTrue(model.relations)

    def test_c009_bounds_equal_phase_identity_and_maxwell_formula(self):
        identical = self.ok("C009", {
            "phases": [
                {"name": "a", "conductivity_w_m_k": 5, "volume_fraction": 0.25},
                {"name": "b", "conductivity_w_m_k": 5, "volume_fraction": 0.75},
            ],
            "method": "maxwell_eucken", "matrix_phase": "a",
        })
        self.assertAlmostEqual(identical["effective_conductivity_w_m_k"], 5.0, places=12)
        self.assertAlmostEqual(identical["series_bound_w_m_k"], 5.0, places=12)
        self.assertAlmostEqual(identical["parallel_bound_w_m_k"], 5.0, places=12)

        result = self.ok("C009", {
            "phases": [
                {"name": "matrix", "conductivity_w_m_k": 10, "volume_fraction": 0.8},
                {"name": "inclusion", "conductivity_w_m_k": 1, "volume_fraction": 0.2},
            ],
            "method": "maxwell_eucken", "matrix_phase": "matrix",
        })
        expected = 10 * (1 + 20 + 2 * 0.2 * (1 - 10)) / (1 + 20 - 0.2 * (1 - 10))
        self.assertAlmostEqual(result["effective_conductivity_w_m_k"], expected, places=12)
        self.assertLessEqual(result["series_bound_w_m_k"], result["effective_conductivity_w_m_k"])
        self.assertLessEqual(result["effective_conductivity_w_m_k"], result["parallel_bound_w_m_k"])

    def test_c010_wakao_definitions_and_dimensionless_identity(self):
        payload = {
            "superficial_velocity_m_s": 1,
            "particle_diameter_m": 0.01,
            "fluid_density_kg_m3": 1.2,
            "dynamic_viscosity_pa_s": 1.8e-5,
            "diffusivity_m2_s": 2e-5,
        }
        result = self.ok("C010", payload)
        re_expected = 1.2 * 1 * 0.01 / 1.8e-5
        sc_expected = 1.8e-5 / (1.2 * 2e-5)
        sh_expected = 2 + 1.1 * re_expected ** 0.6 * sc_expected ** (1 / 3)
        self.assertAlmostEqual(result["reynolds_number"], re_expected, places=12)
        self.assertAlmostEqual(result["schmidt_number"], sc_expected, places=12)
        self.assertAlmostEqual(result["sherwood_number"], sh_expected, places=12)
        self.assertAlmostEqual(
            result["mass_transfer_coefficient_m_s"] * payload["particle_diameter_m"] / payload["diffusivity_m2_s"],
            result["sherwood_number"], places=12,
        )

    def test_e006_rist_state_point_conservation_and_scaling(self):
        payload = {
            "iron_basis_kmol": 1, "blast_oxygen_atom_kmol": 1,
            "burden_oxygen_atom_kmol": 1.5,
            "top_gas_co_kmol": 1.5, "top_gas_co2_kmol": 0.5,
        }
        result = self.ok("E006", payload)
        self.assertAlmostEqual(result["active_top_gas_carbon_per_iron"], 2.0, places=12)
        self.assertAlmostEqual(result["y_intercept"], -1.0, places=12)
        self.assertAlmostEqual(result["top_gas_oxygen_per_carbon"], 1.25, places=12)
        self.assertAlmostEqual(result["state_point_residual_o_per_fe"], 0.0, places=12)
        scaled = self.ok("E006", {key: value * 7 for key, value in payload.items()})
        for key in ("active_top_gas_carbon_per_iron", "y_intercept", "top_gas_oxygen_per_carbon", "burden_oxygen_per_iron"):
            self.assertAlmostEqual(scaled[key], result[key], places=12)

    def test_e007_interface_cancels_and_zone_residuals_sum(self):
        payload = normal_payload(self.registry, "E007")
        result = self.ok("E007", payload)
        self.assertAlmostEqual(result["high_zone_residual_kj"] + result["low_zone_residual_kj"], result["overall_residual_kj"], places=12)
        self.assertEqual(result["overall_external_heat_input_kj"], 110)
        self.assertEqual(result["overall_external_heat_output_kj"], 110)
        self.assertAlmostEqual(result["overall_useful_heat_efficiency"], 1.0, places=12)
        changed = self.ok("E007", {**payload, "high_to_low_interface_heat_kj": 70})
        self.assertEqual(changed["overall_residual_kj"], result["overall_residual_kj"])
        self.assertAlmostEqual(changed["high_zone_residual_kj"], 10)
        self.assertAlmostEqual(changed["low_zone_residual_kj"], -10)

    def test_e009_carbon_energy_equivalence_and_dual_limit(self):
        payload = normal_payload(self.registry, "E009")
        carbon = self.ok("E009", payload)
        expected_carbon = 0.75 * 0.9 / 0.85
        self.assertAlmostEqual(carbon["fixed_carbon_replacement_ratio"], expected_carbon, places=12)
        self.assertAlmostEqual(carbon["theoretical_coke_replaced_kg"] * 0.85, carbon["coal_effective_fixed_carbon_kg"], places=12)
        dual = self.ok("E009", {**payload, "replacement_basis": "dual_limit"})
        self.assertAlmostEqual(dual["selected_replacement_ratio"], min(dual["fixed_carbon_replacement_ratio"], dual["effective_lhv_replacement_ratio"]), places=12)

    def test_e012_atom_balance_and_normal_volume_scaling(self):
        payload = {
            "dry_blast_nm3": 22.414,
            "dry_blast_oxygen_mole_fraction": 0.21,
            "supplemental_oxygen_nm3": 0,
            "steam_kmol": 0.1,
            "fuel_element_atoms_kmol": {"C": 0.6, "H": 0.2, "O": 0, "N": 0},
        }
        result = self.ok("E012", payload)
        self.assertAlmostEqual(result["component_amounts_kmol"]["CO"], 0.52, places=12)
        self.assertAlmostEqual(result["component_amounts_kmol"]["H2"], 0.2, places=12)
        for residual in result["atom_balance_residuals_kmol"].values():
            self.assertAlmostEqual(residual, 0.0, places=12)
        self.assertAlmostEqual(sum(result["gas_mole_fractions"].values()), 1.0, places=12)

    def test_e014_ergun_terms_and_height_velocity_scaling(self):
        payload = normal_payload(self.registry, "E014")
        result = self.ok("E014", payload)
        self.assertAlmostEqual(result["total_pressure_gradient_pa_m"], result["viscous_pressure_gradient_pa_m"] + result["inertial_pressure_gradient_pa_m"], places=12)
        self.assertAlmostEqual(result["total_pressure_drop_pa"], result["total_pressure_gradient_pa_m"] * payload["bed_height_m"], places=12)
        double_height = self.ok("E014", {**payload, "bed_height_m": 2 * payload["bed_height_m"]})
        self.assertAlmostEqual(double_height["total_pressure_drop_pa"], 2 * result["total_pressure_drop_pa"], places=8)
        double_velocity = self.ok("E014", {**payload, "superficial_velocity_m_s": 2 * payload["superficial_velocity_m_s"]})
        self.assertAlmostEqual(double_velocity["viscous_pressure_gradient_pa_m"], 2 * result["viscous_pressure_gradient_pa_m"], places=10)
        self.assertAlmostEqual(double_velocity["inertial_pressure_gradient_pa_m"], 4 * result["inertial_pressure_gradient_pa_m"], places=10)

    def test_schema_http_forced_routes_and_keyword_recall_for_each_tool(self):
        manifest = self.client.get("/api/v1/tools").json()
        self.assertEqual(manifest["total"], 109)
        self.assertEqual(manifest["catalog_coverage_count"], 91)
        definitions = {item["model_code"]: item for item in manifest["tools"]}
        queries = {
            "C009": "请计算有效导热系数混合规则",
            "C010": "请计算填充床传质系数和Sherwood数",
            "E006": "请计算高炉Rist操作线",
            "E007": "请计算高炉两区热平衡",
            "E009": "请计算喷煤焦炭替代比",
            "E012": "请计算风口前理论煤气量",
            "E014": "请用Ergun计算料柱压降",
        }
        for code in sorted(W9_IDS):
            with self.subTest(code=code):
                payload = normal_payload(self.registry, code)
                definition = definitions[code]
                self.assertTrue(definition["fully_eligible"])
                self.assertEqual(definition["catalog_id"], code)
                self.assertFalse(definition["function"]["parameters"]["additionalProperties"])
                response = self.client.post(
                    f"/api/v1/tools/{definition['function']['name']}/call",
                    json={"arguments": payload},
                )
                self.assertEqual(response.status_code, 200, response.text)
                self.assertEqual(response.json()["model_code"], code)
                forced = self.client.post("/api/v1/experiments/run", json={
                    "user_query": f"强制调用{code}，不得使用其他工具。",
                    "mode": "forced", "model_code": code, "arguments": payload,
                    "llm_name": "isolated-http-contract-test", "prompt_version": "p1-w9-v1",
                })
                self.assertEqual(forced.status_code, 200, forced.text)
                self.assertEqual(forced.json()["selected_model"], code)
                self.assertEqual(forced.json()["execution_result"]["status"], "success")
                autonomous = self.client.post("/api/v1/experiments/run", json={
                    "user_query": queries[code], "mode": "autonomous",
                    "arguments": payload, "llm_name": "deterministic-keyword-router",
                    "prompt_version": "p1-w9-v1",
                })
                self.assertEqual(autonomous.status_code, 200, autonomous.text)
                self.assertEqual(autonomous.json()["selected_model"], code)


if __name__ == "__main__":
    unittest.main()
