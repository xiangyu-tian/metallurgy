"""P1-W6A admission and independent scientific tests for C103/C005/C006/C007."""
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


W6A_IDS = {"C103", "C005", "C006", "C007"}


def c103_uniform_payload():
    return {
        "domain_length_m": 0.01,
        "grid_cells": 10,
        "duration_s": 100,
        "time_step_s": 2,
        "initial_concentrations": [0.37] * 10,
        "diffusivity_profiles": [{"end_time_s": 100, "diffusivity_m2_s": 2e-8}],
        "left_boundary_type": "zero_flux",
        "right_boundary_type": "zero_flux",
        "concentration_unit": "mol/m3",
        "diffusivity_source": "P1-W6A uniform-property benchmark",
        "diffusivity_version": "v1",
    }


def c005_payload():
    return {
        "initial_grain_diameter_m": 10e-6,
        "growth_exponent": 2,
        "rate_prefactor_m_power_per_s": 2e-14,
        "activation_energy_j_mol": 0,
        "temperature_segments": [{"temperature_k": 900, "duration_s": 100}],
        "parameter_source": "P1-W6A algebraic benchmark",
        "parameter_version": "v1",
    }


def c006_payload():
    return {
        "particle_radius_m": 0.001,
        "solid_molar_density_mol_m3": 50000,
        "gas_concentration_mol_m3": 10,
        "solid_moles_per_gas_mole": 1,
        "time_s": 10,
        "film_mass_transfer_coefficient_m_s": 0.01,
        "parameter_source": "P1-W6A film-control benchmark",
        "parameter_version": "v1",
    }


def c007_payload():
    return {
        "temperature_k": 1200,
        "time_s": 3600,
        "parabolic_rate_constant_kg2_m4_s": 1e-10,
        "initial_mass_gain_kg_m2": 0,
        "oxide_density_kg_m3": 5000,
        "oxidant_mass_fraction_in_oxide": 0.25,
        "observed_regime": "protective_parabolic",
        "parameter_source": "P1-W6A parabolic-law benchmark",
        "parameter_version": "v1",
    }


class P1W6AKineticsDiffusionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = ModelRegistry()
        cls.registry.discover()
        cls.client = TestClient(app)

    def ok(self, code, payload):
        result = self.registry.invoke(code, payload)
        self.assertTrue(result.success, result.error)
        return result

    def test_four_tools_pass_all_admission_gates_and_counts(self):
        self.assertEqual(self.registry.get_counts(), {
            "registered_count": 101,
            "runtime_tool_count": 101,
            "catalog_coverage_count": 83,
            "qualified_executable_count": 101,
            "implementation_qualified_count": 101,
            "data_required_count": 34,
            "data_qualified_count": 34,
            "interface_qualified_count": 101,
            "fully_eligible_count": 101,
        })
        for code in W6A_IDS:
            with self.subTest(code=code):
                admission = self.registry.qualification_report(code)
                eligibility = self.registry.eligibility_report(code)
                self.assertTrue(admission["qualified"], admission["reasons"])
                self.assertGreaterEqual(admission["normal_cases_passed"], 3)
                self.assertGreaterEqual(admission["boundary_or_failure_cases_passed"], 2)
                self.assertFalse(eligibility["data_required"])
                self.assertTrue(eligibility["fully_eligible"])
                model = self.registry.get(code)
                self.assertTrue(model.source_records)
                self.assertTrue(model.independent_validation)
                self.assertTrue(model.failure_modes)
                self.assertTrue(model.relations)

    def test_catalog_identity_preserves_analytical_c003_and_covers_numerical_c003(self):
        analytical = self.registry.get("C003")
        numerical = self.registry.get("C103")
        self.assertFalse(analytical.catalog_coverage)
        self.assertEqual(numerical.catalog_id, "C003")
        self.assertTrue(numerical.catalog_coverage)
        self.assertEqual(self.registry.get_by_catalog_id("C003").model_id, "C103")
        self.assertNotEqual(analytical.tool_uid, numerical.tool_uid)
        self.assertNotEqual(analytical.tool_name, numerical.tool_name)

    def test_c103_uniform_zero_flux_solution_and_inventory_conservation(self):
        result = self.ok("C103", c103_uniform_payload()).result
        for concentration in result["final_concentrations"]:
            self.assertAlmostEqual(concentration, 0.37, places=13)
        self.assertAlmostEqual(result["initial_inventory"], result["final_inventory"], places=14)
        self.assertAlmostEqual(result["cumulative_net_boundary_transfer"], 0, places=14)
        self.assertLess(result["relative_mass_balance_error"], 1e-12)

    def test_c103_matches_semi_infinite_error_function_in_large_finite_domain(self):
        cells = 100
        length = 0.02
        duration = 100.0
        diffusion = 1e-7
        numerical = self.ok("C103", {
            "domain_length_m": length,
            "grid_cells": cells,
            "duration_s": duration,
            "time_step_s": 0.5,
            "initial_concentrations": [0.0] * cells,
            "diffusivity_profiles": [{"end_time_s": duration, "diffusivity_m2_s": diffusion}],
            "left_boundary_type": "fixed_concentration",
            "left_boundary_value": 1.0,
            "right_boundary_type": "fixed_concentration",
            "right_boundary_value": 0.0,
            "concentration_unit": "1",
            "diffusivity_source": "constant-D analytical comparison",
            "diffusivity_version": "v1",
            "snapshot_stride": 200,
        }).result
        positions = numerical["positions_m"]
        analytical = self.ok("C003", {
            "diffusion_coefficient": diffusion,
            "initial_concentration": 0,
            "surface_concentration": 1,
            "time_s": duration,
            "positions_m": positions[:60],
        }).result
        expected = [point["concentration"] for point in analytical["profile"]]
        actual = numerical["final_concentrations"][:60]
        self.assertLess(max(abs(a-b) for a, b in zip(actual, expected)), 0.012)
        self.assertLess(numerical["relative_mass_balance_error"], 1e-10)

    def test_c103_variable_diffusivity_still_closes_mass(self):
        payload = c103_uniform_payload()
        payload["initial_concentrations"] = [1, 0.8, 0.6, 0.4, 0.2, 0, 0.1, 0.3, 0.5, 0.7]
        payload["diffusivity_profiles"] = [
            {"end_time_s": 40, "cell_diffusivities_m2_s": [1e-9*(i+1) for i in range(10)]},
            {"end_time_s": 100, "cell_diffusivities_m2_s": [2e-8] * 10},
        ]
        result = self.ok("C103", payload).result
        self.assertAlmostEqual(result["initial_inventory"], result["final_inventory"], places=13)
        self.assertLess(result["relative_mass_balance_error"], 1e-11)

    def test_c005_closed_form_additivity_and_formula_residual(self):
        payload = c005_payload()
        result = self.ok("C005", payload).result
        expected = math.sqrt((10e-6) ** 2 + 2e-14 * 100)
        self.assertAlmostEqual(result["final_grain_diameter_m"], expected, places=15)
        self.assertAlmostEqual(result["integrated_growth_term_m_power"], 2e-12, places=22)
        self.assertAlmostEqual(result["formula_residual_m_power"], 0, places=22)
        split = dict(payload)
        split["temperature_segments"] = [
            {"temperature_k": 900, "duration_s": 40},
            {"temperature_k": 900, "duration_s": 60},
        ]
        self.assertAlmostEqual(
            self.ok("C005", split).result["final_grain_diameter_m"], expected, places=15
        )

    def test_c006_pure_control_limits_and_mixed_time_closure(self):
        film = self.ok("C006", c006_payload()).result
        tau_f = 50000 * 0.001 / (3 * 1 * 0.01 * 10)
        self.assertAlmostEqual(film["conversion_fraction"], 10 / tau_f, places=12)
        self.assertAlmostEqual(film["time_residual_s"], 0, places=10)

        reaction_payload = c006_payload()
        reaction_payload.pop("film_mass_transfer_coefficient_m_s")
        reaction_payload["surface_reaction_rate_constant_m_s"] = 0.02
        reaction_payload["time_s"] = 20
        reaction = self.ok("C006", reaction_payload).result
        tau_r = 50000 * 0.001 / (1 * 0.02 * 10)
        expected = 1 - (1 - 20 / tau_r) ** 3
        self.assertAlmostEqual(reaction["conversion_fraction"], expected, places=12)

        mixed = dict(reaction_payload)
        mixed["film_mass_transfer_coefficient_m_s"] = 0.01
        mixed["product_layer_diffusivity_m2_s"] = 1e-6
        mixed_result = self.ok("C006", mixed).result
        self.assertLess(abs(mixed_result["time_residual_s"]), 1e-9)
        self.assertGreaterEqual(mixed_result["conversion_fraction"], 0)
        self.assertLessEqual(mixed_result["conversion_fraction"], 1)

    def test_c007_parabolic_linearity_mass_thickness_and_nonapplicability(self):
        payload = c007_payload()
        result = self.ok("C007", payload).result
        expected_gain = math.sqrt(1e-10 * 3600)
        self.assertAlmostEqual(result["mass_gain_kg_m2"], expected_gain, places=15)
        self.assertAlmostEqual(result["parabolic_increment_kg2_m4"], 1e-10 * 3600, places=20)
        self.assertAlmostEqual(result["equivalent_oxide_thickness_m"], expected_gain / (5000 * 0.25), places=15)
        self.assertAlmostEqual(result["formula_residual_kg2_m4"], 0, places=20)
        invalid = dict(payload)
        invalid["observed_regime"] = "breakaway_or_spalling"
        rejected = self.registry.invoke("C007", invalid)
        self.assertFalse(rejected.success)
        self.assertEqual(rejected.error_code, "MODEL_NOT_APPLICABLE")

    def test_schema_units_failures_uniform_http_and_forced_routes(self):
        payloads = {
            "C103": c103_uniform_payload(),
            "C005": c005_payload(),
            "C006": c006_payload(),
            "C007": c007_payload(),
        }
        manifest = self.client.get("/api/v1/tools").json()
        self.assertEqual(manifest["total"], 101)
        self.assertEqual(manifest["catalog_coverage_count"], 83)
        definitions = {item["model_code"]: item for item in manifest["tools"]}
        for code, payload in payloads.items():
            with self.subTest(code=code):
                definition = definitions[code]
                self.assertTrue(definition["fully_eligible"])
                self.assertEqual(definition["catalog_id"], "C003" if code == "C103" else code)
                response = self.client.post(
                    f"/api/v1/tools/{definition['function']['name']}/call",
                    json={"arguments": payload},
                )
                self.assertEqual(response.status_code, 200, response.text)
                body = response.json()
                self.assertEqual(body["status"], "success")
                self.assertEqual(body["model_code"], code)
                self.assertTrue(body["execution_id"].startswith("EXEC-"))
                forced = self.client.post("/api/v1/experiments/run", json={
                    "user_query": f"强制调用{code}，不得选择其他工具。",
                    "mode": "forced",
                    "model_code": code,
                    "arguments": payload,
                    "llm_name": "isolated-http-contract-test",
                    "prompt_version": "p1-w6a-v1",
                })
                self.assertEqual(forced.status_code, 200, forced.text)
                forced_body = forced.json()
                self.assertEqual(forced_body["selected_model"], code)
                self.assertEqual(forced_body["execution_result"]["status"], "success")
                self.assertEqual(forced_body["execution_result"]["model_code"], code)


if __name__ == "__main__":
    unittest.main()
