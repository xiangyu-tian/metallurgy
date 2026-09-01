"""P1-W8 admission and independent scientific tests for seven catalog tools."""

from __future__ import annotations

import math
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "Tools"
sys.path.insert(0, str(TOOLS))

from models_core import ModelRegistry
from models_server import app


W8_IDS = {"D007", "D015", "D016", "E005", "E011", "G001", "G002"}


def normal_payload(registry: ModelRegistry, code: str) -> dict:
    return next(
        case["input"] for case in registry.get(code).qualification_cases
        if case["kind"] == "normal"
    )


class P1W8ProcessHydrogenNumericsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = ModelRegistry()
        cls.registry.discover()
        cls.client = TestClient(app)

    def ok(self, code: str, payload: dict):
        result = self.registry.invoke(code, payload)
        self.assertTrue(result.success, result.error)
        return result

    def test_seven_tools_pass_all_gates_and_dynamic_counts(self):
        self.assertEqual(self.registry.get_counts(), {
            "registered_count": 97,
            "runtime_tool_count": 97,
            "catalog_coverage_count": 79,
            "qualified_executable_count": 97,
            "implementation_qualified_count": 97,
            "data_required_count": 33,
            "data_qualified_count": 33,
            "interface_qualified_count": 97,
            "fully_eligible_count": 97,
        })
        for code in W8_IDS:
            with self.subTest(code=code):
                admission = self.registry.qualification_report(code)
                eligibility = self.registry.eligibility_report(code)
                self.assertTrue(admission["qualified"], admission["reasons"])
                self.assertEqual(admission["normal_cases_passed"], 3)
                self.assertGreaterEqual(admission["boundary_or_failure_cases_passed"], 2)
                self.assertTrue(eligibility["fully_eligible"], eligibility)
                self.assertEqual(eligibility["data_required"], code == "D007")
                model = self.registry.get(code)
                self.assertEqual(model.catalog_id, code)
                self.assertTrue(model.catalog_coverage)
                self.assertTrue(model.source_records)
                self.assertTrue(model.independent_validation)
                self.assertTrue(model.failure_modes)
                self.assertTrue(model.relations)

    def test_d007_supply_and_kinetic_limits_and_conservation(self):
        common = {
            "initial_metal_mass_kg": 1000,
            "initial_carbon_mass_fraction": 0.04,
            "carbon_to_co2_fraction": 0,
            "parameter_source": "independent test fixture",
            "parameter_version": "v1",
        }
        supply = self.ok("D007", {**common, "segments": [{
            "name": "supply", "duration_s": 10, "oxygen_flow_kmol_s": 0.1,
            "decarburization_oxygen_efficiency": 1,
        }]}).result
        self.assertAlmostEqual(supply["total_carbon_removed_kg"], 24.022, places=10)
        self.assertAlmostEqual(supply["total_carbon_removed_kmol"], 2.0, places=12)
        self.assertAlmostEqual(supply["total_oxygen_consumed_by_decarburization_kmol"], 1.0, places=12)
        self.assertEqual(supply["time_history"][0]["controlling_mode"], "oxygen_supply")
        self.assertLess(abs(supply["carbon_mass_balance_residual_kg"]), 1e-12)
        self.assertLess(abs(supply["oxygen_allocation_residual_kmol"]), 1e-12)

        kinetic = self.ok("D007", {**common, "segments": [{
            "name": "kinetic", "duration_s": 10, "oxygen_flow_kmol_s": 0.1,
            "decarburization_oxygen_efficiency": 1, "kinetic_rate_limit_kg_s": 0.5,
        }]}).result
        self.assertAlmostEqual(kinetic["total_carbon_removed_kg"], 5.0, places=12)
        self.assertEqual(kinetic["time_history"][0]["controlling_mode"], "kinetic")
        self.assertAlmostEqual(
            kinetic["total_oxygen_consumed_by_decarburization_kmol"],
            0.5 * 5.0 / 12.011,
            places=12,
        )

    def test_d007_d015_d016_real_execution_chain_preserves_stoichiometry(self):
        d007 = self.ok("D007", {
            "initial_metal_mass_kg": 1000,
            "initial_carbon_mass_fraction": 0.04,
            "carbon_to_co2_fraction": 0.25,
            "parameter_source": "chain verification fixture",
            "parameter_version": "v1",
            "segments": [
                {"name": "s1", "duration_s": 5, "oxygen_flow_kmol_s": 0.08,
                 "decarburization_oxygen_efficiency": 0.8},
                {"name": "s2", "duration_s": 8, "oxygen_flow_kmol_s": 0.04,
                 "decarburization_oxygen_efficiency": 0.6,
                 "kinetic_rate_limit_kg_s": 0.3},
            ],
        }).result
        gas_segments = [{
            "name": row["name"], "duration_s": row["duration_s"],
            "carbon_removed_kmol": row["carbon_removed_kmol"],
            "carbon_to_co2_fraction": 0.25,
        } for row in d007["time_history"]]
        d015 = self.ok("D015", {
            "decarburization_segments": gas_segments,
            "gas_temperature_k": 1873.15,
            "gas_pressure_pa": 101325,
            "upstream_execution_id": "EXEC-CHAIN-D007",
        }).result
        self.assertAlmostEqual(d015["total_dry_gas_kmol"], d007["total_carbon_removed_kmol"], places=12)
        self.assertAlmostEqual(
            d015["total_oxygen_consumption_kmol"],
            d007["total_oxygen_consumed_by_decarburization_kmol"],
            places=12,
        )
        d016 = self.ok("D016", {
            "actual_oxygen_supply_kmol": d007["total_oxygen_supplied_kmol"],
            "useful_oxygen_components_kmol_o2": {
                "carbon": d015["total_oxygen_consumption_kmol"],
            },
            "source_execution_ids": {"carbon": "EXEC-CHAIN-D015"},
        }).result
        self.assertAlmostEqual(
            d016["oxygen_utilization_fraction"],
            d015["total_oxygen_consumption_kmol"] / d007["total_oxygen_supplied_kmol"],
            places=12,
        )
        self.assertLess(abs(d016["oxygen_closure_residual_kmol"]), 1e-12)

    def test_d015_ideal_gas_temperature_pressure_scaling(self):
        payload = {
            "decarburization_segments": [{
                "name": "gas", "duration_s": 10, "carbon_removed_kmol": 1,
                "carbon_to_co2_fraction": 0.4,
            }],
            "gas_temperature_k": 1000,
            "gas_pressure_pa": 200000,
        }
        base = self.ok("D015", payload).result
        double_t = self.ok("D015", {**payload, "gas_temperature_k": 2000}).result
        half_p = self.ok("D015", {**payload, "gas_pressure_pa": 100000}).result
        self.assertAlmostEqual(double_t["total_actual_volume_m3"], 2 * base["total_actual_volume_m3"], places=12)
        self.assertAlmostEqual(half_p["total_actual_volume_m3"], 2 * base["total_actual_volume_m3"], places=12)
        self.assertAlmostEqual(base["co_mole_fraction"], 0.6, places=12)
        self.assertAlmostEqual(base["co2_mole_fraction"], 0.4, places=12)

    def test_d016_scaling_invariance_and_overallocation_failure(self):
        payload = {
            "actual_oxygen_supply_kmol": 100,
            "useful_oxygen_components_kmol_o2": {"carbon": 60, "silicon": 20},
            "measured_loss_components_kmol_o2": {"offgas": 5},
        }
        base = self.ok("D016", payload).result
        scaled = self.ok("D016", {
            "actual_oxygen_supply_kmol": 300,
            "useful_oxygen_components_kmol_o2": {"carbon": 180, "silicon": 60},
            "measured_loss_components_kmol_o2": {"offgas": 15},
        }).result
        self.assertAlmostEqual(base["oxygen_utilization_fraction"], 0.8, places=12)
        self.assertAlmostEqual(scaled["oxygen_utilization_fraction"], 0.8, places=12)
        self.assertAlmostEqual(sum(base["useful_component_shares"].values()), 1.0, places=12)
        invalid = self.registry.invoke("D016", {
            "actual_oxygen_supply_kmol": 10,
            "useful_oxygen_components_kmol_o2": {"carbon": 9},
            "measured_loss_components_kmol_o2": {"offgas": 2},
        })
        self.assertFalse(invalid.success)
        self.assertEqual(invalid.error_code, "OUT_OF_DOMAIN")

    def test_e005_hydrogen_atom_counts_balance_and_split_invariance(self):
        methane = self.ok("E005", {
            "basis": "per_hour",
            "input_streams": [{"name": "fuel", "species_kmol": {"CH4": 1}}],
            "output_streams": [{"name": "top", "species_kmol": {"H2": 1, "H2O": 1}}],
            "top_gas_stream_name": "top",
        }).result
        self.assertAlmostEqual(methane["total_input_hydrogen_atom_kmol"], 4.0, places=12)
        self.assertAlmostEqual(methane["total_output_hydrogen_atom_kmol"], 4.0, places=12)
        self.assertAlmostEqual(methane["top_gas_hydrogen_utilization_fraction"], 0.5, places=12)
        self.assertTrue(methane["passed"])
        split = self.ok("E005", {
            "basis": "per_hour",
            "input_streams": [{"name": "fuel_a", "species_kmol": {"CH4": 0.4}},
                              {"name": "fuel_b", "species_kmol": {"CH4": 0.6}}],
            "output_streams": [{"name": "top", "species_kmol": {"H2": 1, "H2O": 1}}],
            "top_gas_stream_name": "top",
        }).result
        self.assertAlmostEqual(split["hydrogen_atom_residual_kmol"], methane["hydrogen_atom_residual_kmol"], places=12)

    def test_e011_manual_utilization_and_trends(self):
        result = self.ok("E011", {
            "composition_basis": "mole_fraction",
            "composition_scope": "full_gas",
            "gas_samples": [
                {"time_s": 0, "composition": {"CO": 0.3, "CO2": 0.2, "H2": 0.1, "H2O": 0.1, "N2": 0.3}},
                {"time_s": 60, "composition": {"CO": 0.2, "CO2": 0.3, "H2": 0.12, "H2O": 0.08, "N2": 0.3}},
            ],
        }).result
        self.assertAlmostEqual(result["sample_results"][0]["co_utilization_fraction"], 0.4, places=12)
        self.assertAlmostEqual(result["sample_results"][1]["co_utilization_fraction"], 0.6, places=12)
        self.assertAlmostEqual(result["sample_results"][0]["h2_utilization_fraction"], 0.5, places=12)
        self.assertAlmostEqual(result["sample_results"][1]["h2_utilization_fraction"], 0.4, places=12)
        self.assertEqual(result["co_trend"], "increasing")
        self.assertEqual(result["h2_trend"], "decreasing")

    def test_g001_mesh_rounding_and_second_order_gci(self):
        result = self.ok("G001", {
            "domain_lengths_m": {"x": 1.0, "y": 0.5},
            "resolution_drivers": [
                {"name": "thermal", "characteristic_length_m": 0.1, "minimum_cells": 10},
                {"name": "particle", "characteristic_length_m": 0.03, "minimum_cells": 6},
            ],
            "refinement_ratio": 2,
            "qoi_values_coarse_to_fine": [1.04, 1.01, 1.0025],
            "qoi_name": "synthetic_second_order",
        }).result
        self.assertEqual(result["limiting_driver"]["name"], "particle")
        self.assertAlmostEqual(result["recommended_cell_size_m"], 0.005, places=15)
        self.assertAlmostEqual(result["observed_order"], 2.0, places=12)
        self.assertAlmostEqual(result["richardson_extrapolated_qoi"], 1.0, places=12)
        self.assertEqual(result["mesh_plan"][1]["axis_cell_counts"], {"x": 200, "y": 100})
        for plan in result["mesh_plan"]:
            for actual in plan["axis_actual_cell_sizes_m"].values():
                self.assertLessEqual(actual, plan["nominal_cell_size_m"] + 1e-15)

    def test_g002_one_and_multi_dimensional_stability_identities(self):
        one = self.ok("G002", {
            "cell_sizes_m": [0.1], "time_step_s": 0.05,
            "advection_scheme": "explicit_first_order_upwind",
            "velocity_components_m_s": [1], "diffusion_scheme": "none",
        }).result
        self.assertAlmostEqual(one["total_advection_cfl"], 0.5, places=12)
        self.assertAlmostEqual(one["maximum_advection_time_step_s"], 0.1, places=12)
        self.assertTrue(one["stable"])
        multi = self.ok("G002", {
            "cell_sizes_m": [0.1, 0.2], "time_step_s": 0.02,
            "advection_scheme": "explicit_first_order_upwind",
            "velocity_components_m_s": [1, 2],
            "diffusion_scheme": "explicit_central",
            "diffusivity_components_m2_s": [0.001, 0.002],
        }).result
        self.assertAlmostEqual(multi["total_advection_cfl"], 0.4, places=12)
        self.assertAlmostEqual(multi["total_diffusion_fourier"], 0.003, places=12)
        self.assertEqual(multi["limiting_mechanism"], "advection_cfl")
        self.assertAlmostEqual(multi["maximum_stable_time_step_s"], 0.05, places=12)

    def test_nested_contracts_reject_blank_identity_and_normalized_duplicate_names(self):
        blank = self.registry.invoke("D007", {
            "initial_metal_mass_kg": 1000, "initial_carbon_mass_fraction": 0.04,
            "carbon_to_co2_fraction": 0, "parameter_source": "   ",
            "parameter_version": "v1", "segments": [{
                "name": "stage", "duration_s": 1, "oxygen_flow_kmol_s": 0.1,
                "decarburization_oxygen_efficiency": 1,
            }],
        })
        self.assertFalse(blank.success)
        self.assertEqual(blank.error_code, "INVALID_INPUT")
        duplicate = self.registry.invoke("G001", {
            "domain_lengths_m": {"x": 1},
            "resolution_drivers": [
                {"name": "layer", "characteristic_length_m": 0.1, "minimum_cells": 10},
                {"name": " layer ", "characteristic_length_m": 0.2, "minimum_cells": 10},
            ],
        })
        self.assertFalse(duplicate.success)
        self.assertEqual(duplicate.error_code, "INVALID_INPUT")

    def test_d007_database_path_fails_closed(self):
        with mock.patch.dict(os.environ, {
            "METALLURGY_DB_NAME": "metallurgy_p1_w8_missing_database",
            "METALLURGY_DB_CONNECT_TIMEOUT": "1",
        }):
            result = self.registry.invoke("D007", normal_payload(self.registry, "D007"))
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, "DATA_BACKEND_UNAVAILABLE")

    def test_schema_http_forced_routes_and_keyword_recall_for_each_tool(self):
        manifest = self.client.get("/api/v1/tools").json()
        self.assertEqual(manifest["total"], 97)
        self.assertEqual(manifest["catalog_coverage_count"], 79)
        definitions = {item["model_code"]: item for item in manifest["tools"]}
        queries = {
            "D007": "请计算分段脱碳速率", "D015": "请计算炉气生成量",
            "D016": "请计算氧利用率", "E005": "请计算高炉氢平衡",
            "E011": "请计算炉顶气利用率", "G001": "请计算网格尺度和GCI",
            "G002": "请计算CFL并校验时间步稳定性",
        }
        for code in sorted(W8_IDS):
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
                    "llm_name": "isolated-http-contract-test", "prompt_version": "p1-w8-v1",
                })
                self.assertEqual(forced.status_code, 200, forced.text)
                forced_body = forced.json()
                self.assertEqual(forced_body["selected_model"], code)
                self.assertEqual(forced_body["execution_result"]["status"], "success")
                autonomous = self.client.post("/api/v1/experiments/run", json={
                    "user_query": queries[code], "mode": "autonomous",
                    "arguments": payload, "llm_name": "deterministic-keyword-router",
                    "prompt_version": "p1-w8-v1",
                })
                self.assertEqual(autonomous.status_code, 200, autonomous.text)
                self.assertEqual(autonomous.json()["selected_model"], code)


if __name__ == "__main__":
    unittest.main()
