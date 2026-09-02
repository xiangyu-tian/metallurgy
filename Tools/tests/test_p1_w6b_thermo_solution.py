"""P1-W6B admission and independent scientific tests for B012/B013/B016/B017."""
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
from models_core.repositories.reference_repository import nasa7
from models_core.thermo_assets import R_J_MOL_K
from models_server import app


W6B_IDS = {"B012", "B013", "B016", "B017"}


def b012_payload(nitrogen_moles=3.76, conversion=1.0):
    return {
        "reaction": "C + O₂ → CO₂",
        "feed_moles": {"C(s)": 1, "O2(g)": 1, "N2(g)": nitrogen_moles},
        "initial_temperature_k": 298.15,
        "conversion_fraction": conversion,
        "temperature_lower_k": 298.15,
        "temperature_upper_k": 3500,
    }


def b013_payload():
    return {
        "candidate_species": ["CO(g)", "H2O(g)", "CO2(g)", "H2(g)"],
        "initial_moles": {"CO(g)": 1, "H2O(g)": 1},
        "temperature_k": 1000,
        "pressure_pa": 100000,
    }


def b016_payload(coefficients=None, compositions=None):
    return {
        "compositions": compositions or {"A": 0.3, "B": 0.7},
        "temperature_k": 1000,
        "interaction_parameters_j_mol": coefficients if coefficients is not None else [10000],
        "parameter_source": "P1-W6B independent algebraic test",
        "parameter_version": "v1",
    }


def b017_payload(mode="gamma_infinite"):
    payload = {
        "solute": "C in liquid Fe",
        "solute_mole_fraction": 0.01,
        "temperature_k": 1873,
        "raoult_activity_coefficient": 20,
        "conversion_mode": mode,
        "parameter_source": "P1-W6B independent algebraic test",
        "parameter_version": "v1",
    }
    if mode == "gamma_infinite":
        payload["gamma_infinite"] = 25
    else:
        payload["henry_constant_pa"] = 5e6
        payload["pure_component_fugacity_pa"] = 2e5
    return payload


class P1W6BThermoSolutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = ModelRegistry()
        cls.registry.discover()
        cls.client = TestClient(app)

    def ok(self, code, payload):
        result = self.registry.invoke(code, payload)
        self.assertTrue(result.success, result.error)
        return result

    def test_four_tools_pass_all_admission_gates_and_dynamic_counts(self):
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
        for code in W6B_IDS:
            with self.subTest(code=code):
                admission = self.registry.qualification_report(code)
                eligibility = self.registry.eligibility_report(code)
                self.assertTrue(admission["qualified"], admission["reasons"])
                self.assertGreaterEqual(admission["normal_cases_passed"], 3)
                self.assertGreaterEqual(admission["boundary_or_failure_cases_passed"], 2)
                self.assertTrue(eligibility["fully_eligible"])
                model = self.registry.get(code)
                self.assertEqual(model.catalog_id, code)
                self.assertTrue(model.source_records)
                self.assertTrue(model.independent_validation)
                self.assertTrue(model.failure_modes)
                self.assertTrue(model.relations)

    def test_b012_energy_closure_dilution_zero_conversion_and_provenance(self):
        base = self.ok("B012", b012_payload())
        diluted = self.ok("B012", b012_payload(nitrogen_moles=7.52))
        zero = self.ok("B012", b012_payload(conversion=0))
        self.assertLess(abs(base.result["energy_balance_residual_kj"]), 1e-7)
        self.assertAlmostEqual(base.result["initial_sensible_enthalpy_kj"], 0, places=12)
        self.assertGreater(base.result["adiabatic_temperature_k"], diluted.result["adiabatic_temperature_k"])
        self.assertAlmostEqual(zero.result["adiabatic_temperature_k"], 298.15, places=12)
        self.assertAlmostEqual(zero.result["reaction_extent_mol"], 0, places=15)
        species = set(zero.result["initial_moles"]) | set(zero.result["final_moles"])
        for name in species:
            self.assertAlmostEqual(
                zero.result["initial_moles"].get(name, 0.0),
                zero.result["final_moles"].get(name, 0.0),
                places=15,
            )
        tables = {record.table for record in base.provenance}
        self.assertIn("metallurgy_v2.reaction_property", tables)
        self.assertIn("metallurgy_v2.thermodynamic_correlation", tables)

    def test_b012_phase_transition_plateau_uses_partial_latent_heat(self):
        payload = b012_payload()
        payload["feed_moles"] = {**payload["feed_moles"], "Fe(s)": 2}
        payload.update({
            "phase_transition_from_species": "Fe(s)",
            "phase_transition_to_species": "Fe(l)",
            "phase_transition_temperature_k": 1812,
            "phase_transition_latent_heat_kj_mol": 13.81,
            "phase_transition_source": "NIST phase-change verification input",
            "phase_transition_version": "v1",
        })
        result = self.ok("B012", payload).result
        self.assertAlmostEqual(result["adiabatic_temperature_k"], 1812, places=10)
        self.assertGreater(result["phase_transition_fraction"], 0)
        self.assertLess(result["phase_transition_fraction"], 1)
        expected = 2 * 13.81 * result["phase_transition_fraction"]
        self.assertAlmostEqual(result["phase_transition_heat_kj"], expected, places=10)
        self.assertLess(abs(result["energy_balance_residual_kj"]), 1e-7)

    def test_b012_explicit_failures_close_instead_of_extrapolating(self):
        unknown = self.registry.invoke("B012", {**b012_payload(), "reaction": "Unknown -> X"})
        self.assertFalse(unknown.success)
        self.assertEqual(unknown.error_code, "MISSING_DATA")
        narrow = self.registry.invoke("B012", {**b012_payload(), "temperature_upper_k": 400})
        self.assertFalse(narrow.success)
        self.assertEqual(narrow.error_code, "OUT_OF_DOMAIN")

    def test_b013_wgs_matches_independent_nasa7_equilibrium_constant(self):
        result = self.ok("B013", b013_payload()).result
        y = result["mole_fractions"]
        reaction_quotient = y["CO2(g)"] * y["H2(g)"] / (y["CO(g)"] * y["H2O(g)"])
        properties = {
            species: nasa7(species, 1000)[0]
            for species in ("CO(g)", "H2O(g)", "CO2(g)", "H2(g)")
        }
        delta_g = (
            properties["CO2(g)"]["G"] + properties["H2(g)"]["G"]
            - properties["CO(g)"]["G"] - properties["H2O(g)"]["G"]
        )
        equilibrium_constant = math.exp(-delta_g * 1000 / (R_J_MOL_K * 1000))
        self.assertAlmostEqual(reaction_quotient / equilibrium_constant, 1, places=4)
        self.assertGreaterEqual(result["gibbs_decrease_kj"], 0)
        self.assertLess(max(abs(value) for value in result["element_balance_residuals_mol"].values()), 1e-10)

    def test_b013_inert_system_and_missing_data_failure(self):
        payload = {
            "candidate_species": ["O2(g)", "N2(g)"],
            "initial_moles": {"O2(g)": 1, "N2(g)": 3.76},
            "temperature_k": 1000,
            "pressure_pa": 100000,
        }
        result = self.ok("B013", payload).result
        self.assertAlmostEqual(result["equilibrium_moles"]["O2(g)"], 1, places=12)
        self.assertAlmostEqual(result["equilibrium_moles"]["N2(g)"], 3.76, places=12)
        missing = self.registry.invoke("B013", {
            "candidate_species": ["CH4(g)", "O2(g)"],
            "initial_moles": {"CH4(g)": 1, "O2(g)": 2},
            "temperature_k": 1000,
            "pressure_pa": 100000,
        })
        self.assertFalse(missing.success)
        self.assertEqual(missing.error_code, "MISSING_DATA")

    def test_data_tools_fail_closed_when_postgresql_is_unavailable(self):
        with mock.patch.dict(os.environ, {
            "METALLURGY_DB_NAME": "metallurgy_p1_w6b_missing_database",
            "METALLURGY_DB_CONNECT_TIMEOUT": "1",
        }):
            for code, payload in (("B012", b012_payload()), ("B013", b013_payload())):
                with self.subTest(code=code):
                    result = self.registry.invoke(code, payload)
                    self.assertFalse(result.success)
                    self.assertEqual(result.error_code, "DATA_BACKEND_UNAVAILABLE")

    def test_b016_regular_solution_limit_zero_limit_and_partial_molar_closure(self):
        redlich = self.ok("B016", b016_payload()).result
        regular = self.ok("B015", {
            "compositions": {"A": 0.3, "B": 0.7},
            "temperature": 1000,
            "omega_j_mol": 10000,
        }).result
        self.assertAlmostEqual(redlich["excess_gibbs_j_mol"], regular["excess_gibbs_j_mol"], places=12)
        for component in ("A", "B"):
            self.assertAlmostEqual(
                redlich["activity_coefficients"][component],
                regular["activity_coefficients"][component],
                places=12,
            )
        self.assertLess(abs(redlich["gibbs_duhem_closure_residual_j_mol"]), 1e-12)
        ideal_limit = self.ok("B016", b016_payload(coefficients=[0, 0, 0])).result
        self.assertAlmostEqual(ideal_limit["excess_gibbs_j_mol"], 0, places=15)
        self.assertEqual(ideal_limit["activity_coefficients"], {"A": 1.0, "B": 1.0})

    def test_b016_analytical_partial_molar_derivative_matches_finite_difference(self):
        coefficients = [8000, -2000, 500]
        x = 0.4
        result = self.ok("B016", b016_payload(coefficients, {"A": x, "B": 1-x})).result

        def excess(value):
            difference = 2 * value - 1
            polynomial = sum(coefficient * difference**order for order, coefficient in enumerate(coefficients))
            return value * (1-value) * polynomial

        step = 1e-6
        derivative = (excess(x + step) - excess(x - step)) / (2 * step)
        expected_a = excess(x) + (1-x) * derivative
        expected_b = excess(x) - x * derivative
        self.assertAlmostEqual(result["partial_molar_excess_gibbs_j_mol"]["A"], expected_a, places=5)
        self.assertAlmostEqual(result["partial_molar_excess_gibbs_j_mol"]["B"], expected_b, places=5)

    def test_b017_two_parameter_paths_round_trip_and_domain_warning(self):
        direct = self.ok("B017", b017_payload("gamma_infinite"))
        pressure = self.ok("B017", b017_payload("henry_over_pure_fugacity"))
        for key in (
            "gamma_infinite", "henry_activity_coefficient", "raoult_activity", "henry_activity",
            "standard_chemical_potential_shift_kj_mol",
        ):
            self.assertAlmostEqual(direct.result[key], pressure.result[key], places=12)
        self.assertLess(abs(direct.result["chemical_potential_invariance_residual_kj_mol"]), 1e-12)
        self.assertAlmostEqual(
            direct.result["henry_activity"] * direct.result["gamma_infinite"],
            direct.result["raoult_activity"], places=15,
        )
        outside_payload = b017_payload()
        outside_payload["solute_mole_fraction"] = 0.2
        outside = self.ok("B017", outside_payload)
        self.assertFalse(outside.boundary_check.passed)
        self.assertTrue(any("x>0.1" in warning.message for warning in outside.boundary_check.warnings))

    def test_schema_http_and_forced_routes_for_each_new_tool(self):
        payloads = {
            "B012": b012_payload(),
            "B013": b013_payload(),
            "B016": b016_payload(),
            "B017": b017_payload(),
        }
        manifest = self.client.get("/api/v1/tools").json()
        self.assertEqual(manifest["total"], 101)
        self.assertEqual(manifest["catalog_coverage_count"], 83)
        definitions = {item["model_code"]: item for item in manifest["tools"]}
        for code, payload in payloads.items():
            with self.subTest(code=code):
                definition = definitions[code]
                self.assertTrue(definition["fully_eligible"])
                self.assertEqual(definition["catalog_id"], code)
                self.assertFalse(definition["function"]["parameters"]["additionalProperties"])
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
                    "prompt_version": "p1-w6b-v1",
                })
                self.assertEqual(forced.status_code, 200, forced.text)
                forced_body = forced.json()
                self.assertEqual(forced_body["selected_model"], code)
                self.assertEqual(forced_body["execution_result"]["status"], "success")
                self.assertEqual(forced_body["execution_result"]["model_code"], code)


if __name__ == "__main__":
    unittest.main()
