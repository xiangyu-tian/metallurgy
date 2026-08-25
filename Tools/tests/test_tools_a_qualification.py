"""Wave 0/1 qualification and scientific-property tests for A001--A007.

These are executable conformance tests, not research/evaluation cases.
"""

import math
import os
import sys
import unittest


TOOLS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, TOOLS_DIR)

from models_core import ModelRegistry
from models_core.chemical_data import ELEMENT_ATOMIC_WEIGHTS


class WaveOneQualificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = ModelRegistry()
        cls.registry.discover()

    def invoke_ok(self, model_code, payload):
        result = self.registry.invoke(model_code, payload)
        self.assertTrue(result.success, result.error)
        self.assertTrue(result.provenance, f"{model_code} 缺少来源信息")
        return result

    def invoke_fail(self, model_code, payload, error_code="INVALID_INPUT"):
        result = self.registry.invoke(model_code, payload)
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, error_code)
        self.assertTrue(result.provenance, f"{model_code} 失败结果缺少来源信息")
        return result

    def test_registry_reports_strict_counts_and_gate_details(self):
        counts = self.registry.get_counts()
        self.assertEqual(counts["registered_count"], 30)
        self.assertEqual(counts["qualified_executable_count"], 30)
        qualified = {
            card["model_code"]
            for card in self.registry.list_models(qualified_only=True)
        }
        self.assertEqual(len(qualified), 30)
        self.assertTrue({f"A{i:03d}" for i in range(1, 8)} <= qualified)
        for model_code in qualified:
            report = self.registry.qualification_report(model_code)
            self.assertTrue(report["qualified"], report["reasons"])
            self.assertGreaterEqual(report["normal_cases_passed"], 3)
            self.assertGreaterEqual(report["boundary_or_failure_cases_passed"], 2)

    def test_qualified_cards_have_contract_and_relationship_metadata(self):
        for card in self.registry.list_models(qualified_only=True):
            with self.subTest(model=card["model_code"]):
                self.assertEqual(card["qualification_status"], "qualified")
                self.assertTrue(card["source_version"])
                self.assertTrue(card["formula_reference"])
                self.assertTrue(card["failure_modes"])
                self.assertTrue(card["independent_validation"])
                self.assertTrue(card["relations"])
                self.assertEqual(card["input_schema"]["$schema"], "https://json-schema.org/draft/2020-12/schema")
                self.assertEqual(card["output_schema"]["$schema"], "https://json-schema.org/draft/2020-12/schema")

    def test_a001_three_normal_two_failure_and_round_trip(self):
        cases = [
            ({"value": 1, "source_unit": "kg", "target_unit": "g"}, 1000.0),
            ({"value": 100, "source_unit": "°C", "target_unit": "K"}, 373.15),
            ({"value": 1, "source_unit": "MPa", "target_unit": "Pa"}, 1_000_000.0),
        ]
        for payload, expected in cases:
            with self.subTest(payload=payload):
                actual = self.invoke_ok("A001", payload).result["value"]
                self.assertTrue(math.isclose(actual, expected, rel_tol=1e-10, abs_tol=1e-10))
        self.invoke_fail("A001", {"value": 1, "source_unit": "bogus", "target_unit": "kg"}, "UNIT_MISMATCH")
        self.invoke_fail("A001", {"value": 1, "source_unit": "kg", "target_unit": "m"}, "UNIT_MISMATCH")
        forward = self.invoke_ok("A001", {"value": 37.5, "source_unit": "°C", "target_unit": "°F"}).result["value"]
        backward = self.invoke_ok("A001", {"value": forward, "source_unit": "°F", "target_unit": "°C"}).result["value"]
        self.assertAlmostEqual(backward, 37.5, places=10)

    def test_a002_three_normal_two_failure_and_atom_count_identity(self):
        expected = [
            ("Fe2O3", {"Fe": 2.0, "O": 3.0}),
            ("Fe2(SO4)3", {"Fe": 2.0, "S": 3.0, "O": 12.0}),
            ("CuSO4·5H2O", {"Cu": 1.0, "S": 1.0, "O": 9.0, "H": 10.0}),
        ]
        for formula, elements in expected:
            with self.subTest(formula=formula):
                result = self.invoke_ok("A002", {"formula": formula}).result
                self.assertEqual(result["elements"], elements)
                self.assertAlmostEqual(result["total_atoms"], sum(elements.values()))
                self.assertNotIn("molar_mass", result)
        self.invoke_fail("A002", {"formula": "Fe2O3xyz"})
        self.invoke_fail("A002", {"formula": "Mg(OH]2"})

    def test_a003_three_normal_two_failure_and_weighted_sum(self):
        cases = [("H2O", 18.015), ("Fe2O3", 159.687), ("CaCO3", 100.086)]
        for formula, expected in cases:
            with self.subTest(formula=formula):
                result = self.invoke_ok("A003", {"formula": formula}).result
                self.assertAlmostEqual(result["molar_mass_g_per_mol"], expected, places=3)
                self.assertAlmostEqual(result["molar_mass_kg_per_kmol"], expected, places=3)
        self.invoke_fail("A003", {"formula": "Xx2O"})
        self.invoke_fail("A003", {"formula": "Fe2(O3"})
        weighted = 2 * ELEMENT_ATOMIC_WEIGHTS["Fe"] + 3 * ELEMENT_ATOMIC_WEIGHTS["O"]
        actual = self.invoke_ok("A003", {"formula": "Fe2O3"}).result["molar_mass_g_per_mol"]
        self.assertAlmostEqual(actual, weighted, places=6)

    def test_a004_three_normal_two_failure_and_scale_invariance(self):
        cases = [
            ({"compositions": {"Fe": 0.9, "C": 0.1}, "input_basis": "fraction"}, {"Fe": 0.9, "C": 0.1}),
            ({"compositions": {"Fe": 90, "C": 10}, "input_basis": "percent"}, {"Fe": 0.9, "C": 0.1}),
            ({"compositions": {"Fe": 900000, "C": 100000}, "input_basis": "ppm"}, {"Fe": 0.9, "C": 0.1}),
        ]
        for payload, expected in cases:
            with self.subTest(payload=payload):
                result = self.invoke_ok("A004", payload).result
                self.assertEqual(result["normalized"], expected)
                self.assertAlmostEqual(sum(result["normalized"].values()), 1.0, places=12)
        self.invoke_fail("A004", {"compositions": {"Fe": 1.1, "C": -0.1}})
        self.invoke_fail("A004", {"compositions": {"Fe": 0.0, "C": 0.0}})
        a = self.invoke_ok("A004", {"compositions": {"Fe": 9, "C": 1}}).result["normalized"]
        b = self.invoke_ok("A004", {"compositions": {"Fe": 900, "C": 100}}).result["normalized"]
        self.assertEqual(a, b)

    def test_a005_three_normal_two_boundary_failure_and_mass_identity(self):
        balanced_cases = [
            ({"input_streams": [{"name": "in", "mass": 10, "elements": {"Fe": 1}}],
              "output_streams": [{"name": "out", "mass": 10, "elements": {"Fe": 1}}]}, "Fe"),
            ({"input_streams": [{"name": "a", "mass": 6, "elements": {"Fe": 1}}, {"name": "b", "mass": 4, "elements": {"C": 1}}],
              "output_streams": [{"name": "c", "mass": 10, "elements": {"Fe": 0.6, "C": 0.4}}]}, "C"),
            ({"input_streams": [{"name": "in", "mass": 1000, "elements": {"Fe": 1}}],
              "output_streams": [{"name": "out", "mass": 999.9995, "elements": {"Fe": 1}}],
              "absolute_tolerance": 0.001}, "Fe"),
        ]
        for payload, element in balanced_cases:
            with self.subTest(payload=payload):
                result = self.invoke_ok("A005", payload).result
                self.assertTrue(result["passed"])
                balance = result["element_balances"][element]
                self.assertAlmostEqual(balance["residual"], balance["input_mass"] - balance["output_mass"], places=12)
        boundary = self.invoke_ok("A005", {
            "input_streams": [{"mass": 10, "elements": {"Fe": 1}}],
            "output_streams": [{"mass": 9, "elements": {"Fe": 1}}],
        })
        self.assertFalse(boundary.result["passed"])
        self.assertFalse(boundary.boundary_check.passed)
        self.invoke_fail("A005", {
            "input_streams": [{"mass": -10, "elements": {"Fe": 1}}],
            "output_streams": [{"mass": 10, "elements": {"Fe": 1}}],
        })
        self.invoke_fail("A005", {
            "input_streams": [{"mass": 10, "elements": {"Fe": 1.2}}],
            "output_streams": [{"mass": 10, "elements": {"Fe": 1}}],
        })

    def test_a006_three_normal_two_boundary_failure_and_zero_residual(self):
        equations = [
            "Fe2O3 + 3CO -> 2Fe + 3CO2",
            "CaCO3 -> CaO + CO2",
            "Fe2O3 + 2Al -> 2Fe + Al2O3",
        ]
        for equation in equations:
            with self.subTest(equation=equation):
                result = self.invoke_ok("A006", {"reaction": equation}).result
                self.assertTrue(result["balanced"])
                self.assertTrue(all(abs(v) < 1e-12 for v in result["element_residuals"].values()))
        boundary = self.invoke_ok("A006", {"reaction": "Fe2O3 + CO -> Fe + CO2"})
        self.assertFalse(boundary.result["balanced"])
        self.assertFalse(boundary.boundary_check.passed)
        self.invoke_fail("A006", {"reaction": "Fe2O3 + CO"})
        self.invoke_fail("A006", {"reaction": "Fe3+ + e- -> Fe2+"}, "MODEL_NOT_APPLICABLE")

    def test_a007_three_normal_two_failure_and_electron_equivalence(self):
        oxidation_cases = [
            ("C", 12.011, 4),
            ("Si", 28.085, 4),
            ("Al", 26.982, 3),
        ]
        for element, mass, target in oxidation_cases:
            with self.subTest(element=element):
                result = self.invoke_ok("A007", {
                    "composition": {element: 1.0}, "basis_mass_kg": mass,
                    "initial_valences": {element: 0}, "target_valences": {element: target},
                }).result
                self.assertEqual(result["mode"], "oxidation")
                self.assertAlmostEqual(result["electron_equivalents_kmol"], target, places=9)
                self.assertAlmostEqual(result["oxygen_required_kmol"], target / 4, places=9)
                self.assertAlmostEqual(result["electron_balance_residual_kmol"], 0.0, places=12)
        self.invoke_fail("A007", {
            "composition": {"Fe": 1}, "basis_mass_kg": 55.845,
            "initial_valences": {"Fe": 0}, "target_valences": {},
        })
        self.invoke_fail("A007", {
            "composition": {"Fe": 1}, "basis_mass_kg": 55.845,
            "initial_valences": {"Fe": 0}, "target_valences": {"Fe": 2},
            "oxygen_purity": 0,
        })
        reduction = self.invoke_ok("A007", {
            "composition": {"Fe": 1}, "basis_mass_kg": 55.845,
            "initial_valences": {"Fe": 2}, "target_valences": {"Fe": 0},
            "reductant_product": "CO",
        }).result
        self.assertEqual(reduction["mode"], "reduction")
        self.assertAlmostEqual(reduction["carbon_equivalent_kmol"], 1.0, places=9)


if __name__ == "__main__":
    unittest.main()
