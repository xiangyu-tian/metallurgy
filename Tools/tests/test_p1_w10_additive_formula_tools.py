"""P1-W10 admission, mathematical-property and function-call tests for six additive tools."""

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


W10_IDS = {"A011", "C011", "T003", "T004", "D023", "E021"}
R_J_MOL_K = 8.31446261815324


def normal_payload(registry: ModelRegistry, code: str) -> dict:
    return next(case["input"] for case in registry.get(code).qualification_cases if case["kind"] == "normal")


class P1W10AdditiveFormulaToolTests(unittest.TestCase):
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
        for code in W10_IDS:
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

    def test_a011_exact_coefficients_primitive_gcd_and_a006_independent_check(self):
        result = self.ok("A011", {
            "reactants": [{"formula": "KMnO4"}, {"formula": "HCl"}],
            "products": [{"formula": "KCl"}, {"formula": "MnCl2"}, {"formula": "H2O"}, {"formula": "Cl2"}],
        })
        self.assertEqual(result["reactant_coefficients"], [2, 16])
        self.assertEqual(result["product_coefficients"], [2, 2, 8, 5])
        self.assertTrue(result["gcd_is_one"])
        self.assertTrue(result["passed"])
        self.assertTrue(all(value == 0 for value in result["element_residuals"].values()))
        independent = self.registry.invoke("A006", {"reaction": result["balanced_reaction"]})
        self.assertTrue(independent.success, independent.error)
        self.assertTrue(independent.result["balanced"])
        self.assertTrue(all(abs(value) <= 1e-12 for value in independent.result["element_residuals"].values()))

    def test_c011_dimensionless_identities_and_velocity_scaling(self):
        payload = normal_payload(self.registry, "C011")
        result = self.ok("C011", payload)
        self.assertAlmostEqual(result["thermal_peclet_number"], result["reynolds_number"] * result["prandtl_number"], places=10)
        self.assertAlmostEqual(result["mass_peclet_number"], result["reynolds_number"] * result["schmidt_number"], places=10)
        self.assertAlmostEqual(result["lewis_number"], result["schmidt_number"] / result["prandtl_number"], places=10)
        doubled = self.ok("C011", {**payload, "velocity_m_s": 2 * payload["velocity_m_s"]})
        for key in ("reynolds_number", "thermal_peclet_number", "mass_peclet_number"):
            self.assertAlmostEqual(doubled[key], 2 * result[key], places=10)
        for key in ("prandtl_number", "schmidt_number", "lewis_number"):
            self.assertAlmostEqual(doubled[key], result[key], places=12)

    def test_t003_exponential_temperature_and_energy_identity(self):
        payload = normal_payload(self.registry, "T003")
        result = self.ok("T003", payload)
        expected_theta = math.exp(-payload["time_s"] / result["time_constant_s"])
        expected_temperature = payload["ambient_temperature_k"] + (
            payload["initial_temperature_k"] - payload["ambient_temperature_k"]
        ) * expected_theta
        expected_heat = (
            payload["density_kg_m3"] * payload["specific_heat_j_kg_k"] * payload["volume_m3"]
            * (payload["initial_temperature_k"] - expected_temperature)
        )
        self.assertLessEqual(result["biot_number"], 0.1)
        self.assertAlmostEqual(result["dimensionless_temperature"], expected_theta, places=12)
        self.assertAlmostEqual(result["temperature_k"], expected_temperature, places=12)
        self.assertAlmostEqual(result["heat_removed_j"], expected_heat, places=7)
        at_zero = self.registry.invoke("T003", {**payload, "time_s": 0})
        self.assertTrue(at_zero.success)
        self.assertFalse(at_zero.boundary_check.passed)
        self.assertEqual(at_zero.result["temperature_k"], payload["initial_temperature_k"])
        self.assertEqual(at_zero.result["heat_removed_j"], 0)

    def test_t004_single_layer_matches_t001_and_network_closes(self):
        payload = {
            "layers": [{"name": "steel", "thickness_m": 0.1, "conductivity_w_m_k": 20}],
            "area_m2": 2,
            "hot_boundary_temperature_k": 1000,
            "cold_boundary_temperature_k": 500,
        }
        multilayer = self.ok("T004", payload)
        plane = self.ok("T001", {
            "thermal_conductivity": 20,
            "thickness": 0.1,
            "area": 2,
            "hot_temperature": 1000,
            "cold_temperature": 500,
        })
        self.assertAlmostEqual(multilayer["total_thermal_resistance_k_w"], plane["thermal_resistance_k_per_w"], places=12)
        self.assertAlmostEqual(multilayer["heat_rate_w"], plane["heat_rate_w"], places=12)
        self.assertAlmostEqual(multilayer["heat_flux_w_m2"], plane["heat_flux_w_m2"], places=12)
        self.assertAlmostEqual(multilayer["closure_residual_k"], 0, places=12)
        self.assertAlmostEqual(
            sum(item["resistance_k_w"] for item in multilayer["resistance_breakdown"]),
            multilayer["total_thermal_resistance_k_w"], places=12,
        )

    def test_d023_two_mass_bases_close_to_target(self):
        base = {
            "bath_mass_kg": 100000,
            "initial_mass_fraction": 0.002,
            "target_mass_fraction": 0.005,
            "alloy_element_mass_fraction": 0.75,
            "element_recovery_fraction": 0.9,
        }
        fixed = self.ok("D023", {**base, "mass_basis": "fixed_initial_bath_mass"})
        final = self.ok("D023", {**base, "mass_basis": "addition_in_final_bath_mass"})
        self.assertAlmostEqual(fixed["alloy_addition_kg"], 100000 * 0.003 / (0.9 * 0.75), places=12)
        self.assertAlmostEqual(final["alloy_addition_kg"], 100000 * 0.003 / (0.9 * 0.75 - 0.005), places=12)
        for result in (fixed, final):
            self.assertAlmostEqual(result["predicted_mass_fraction"], base["target_mass_fraction"], places=12)
            self.assertAlmostEqual(result["mass_balance_residual_kg"], 0, places=9)
            self.assertAlmostEqual(
                result["initial_element_mass_kg"] + result["recovered_element_mass_kg"],
                result["final_element_mass_kg"], places=12,
            )

    def test_e021_real_b008_to_b008_to_e021_execution_chain_and_identity(self):
        definitions = {item["model_code"]: item for item in self.client.get("/api/v1/tools").json()["tools"]}
        b008_tool = definitions["B008"]["function"]["name"]
        upstream = []
        for reaction in ("2C + O₂ → 2CO", "C + O₂ → CO₂"):
            response = self.client.post(
                f"/api/v1/tools/{b008_tool}/call",
                json={"arguments": {"reaction": reaction, "temperature": 1000}},
            )
            self.assertEqual(response.status_code, 200, response.text)
            record = response.json()
            self.assertEqual(record["status"], "success")
            self.assertTrue(record["execution_id"].startswith("EXEC-"))
            upstream.append(record)

        e021_payload = {
            "temperature_k": 1000,
            "total_pressure_pa": 100000,
            "co_mole_fraction": 0.6,
            "co2_mole_fraction": 0.4,
            "carbon_activity": 1,
            "co_formation_reaction_gibbs_kj_mol": upstream[0]["output"]["delta_G"],
            "co2_formation_reaction_gibbs_kj_mol": upstream[1]["output"]["delta_G"],
            "co_formation_execution_id": upstream[0]["execution_id"],
            "co2_formation_execution_id": upstream[1]["execution_id"],
        }
        e021_tool = definitions["E021"]["function"]["name"]
        response = self.client.post(f"/api/v1/tools/{e021_tool}/call", json={"arguments": e021_payload})
        self.assertEqual(response.status_code, 200, response.text)
        record = response.json()
        self.assertEqual(record["status"], "success")
        output = record["output"]
        self.assertEqual(output["co_formation_execution_id"], upstream[0]["execution_id"])
        self.assertEqual(output["co2_formation_execution_id"], upstream[1]["execution_id"])
        self.assertAlmostEqual(
            output["standard_reaction_gibbs_kj_mol"],
            upstream[0]["output"]["delta_G"] - upstream[1]["output"]["delta_G"], places=12,
        )
        self.assertAlmostEqual(
            output["actual_reaction_gibbs_kj_mol"] * 1000 / (R_J_MOL_K * 1000),
            math.log(output["quotient_to_equilibrium_ratio"]), places=12,
        )
        ratio = output["equilibrium_co_to_co2_ratio"]
        reconstructed_q = ratio * ratio / (1 + ratio)
        self.assertAlmostEqual(reconstructed_q, output["equilibrium_constant"], places=12)

    def test_schema_http_forced_routes_and_keyword_recall_for_each_tool(self):
        manifest = self.client.get("/api/v1/tools").json()
        self.assertEqual(manifest["total"], 93)
        self.assertEqual(manifest["catalog_coverage_count"], 75)
        definitions = {item["model_code"]: item for item in manifest["tools"]}
        queries = {
            "A011": "请自动配平并求最小整数计量系数",
            "C011": "请计算Reynolds、Prandtl、Schmidt和Peclet无量纲数",
            "T003": "请用集总热容法计算瞬态温度和Biot数",
            "T004": "请计算复合壁多层热阻和温度剖面",
            "D023": "请按目标成分和元素收得率计算合金补加量",
            "E021": "请计算Boudouard反应CO/CO2平衡驱动力",
        }
        for code in sorted(W10_IDS):
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
                    "mode": "forced", "model_code": code, "arguments": payload,
                    "llm_name": "isolated-http-contract-test", "prompt_version": "p1-w10-v1",
                })
                self.assertEqual(forced.status_code, 200, forced.text)
                self.assertEqual(forced.json()["selected_model"], code)
                self.assertEqual(forced.json()["execution_result"]["status"], "success")
                autonomous = self.client.post("/api/v1/experiments/run", json={
                    "user_query": queries[code], "mode": "autonomous",
                    "arguments": payload, "llm_name": "deterministic-keyword-router",
                    "prompt_version": "p1-w10-v1",
                })
                self.assertEqual(autonomous.status_code, 200, autonomous.text)
                self.assertEqual(autonomous.json()["selected_model"], code)


if __name__ == "__main__":
    unittest.main()
