"""Scientific integration tests preserving the 30-tool baseline through P0-W1."""

import math
import os
import sys
import unittest

TOOLS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, TOOLS_DIR)

from models_core import ModelRegistry


BASELINE_IDS = {
    "A001", "A002", "A003", "A004", "A005", "A006", "A007",
    "B001", "B002", "B003", "B004", "B005", "B006", "B007", "B008", "B009",
    "B010", "B011", "B014", "B015", "B018", "B019",
    "C001", "C002", "C003", "C004", "T001", "T002", "D001", "D002",
}
W1_IDS = {"A101", "A008", "D021", "D004"}
W2_IDS = {"E001", "E002", "E003", "E004"}
EXPECTED_IDS = BASELINE_IDS | W1_IDS | W2_IDS


class ThirtyToolBaselineAndW1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = ModelRegistry()
        cls.registry.discover()

    def ok(self, code, payload):
        result = self.registry.invoke(code, payload)
        self.assertTrue(result.success, result.error)
        self.assertTrue(result.provenance)
        return result

    def test_thirty_baseline_assets_and_four_w1_tools_are_qualified(self):
        self.assertEqual(self.registry.get_counts(), {
            "registered_count": 38,
            "runtime_tool_count": 38,
            "catalog_coverage_count": 34,
            "qualified_executable_count": 38,
            "implementation_qualified_count": 38,
            "data_required_count": 16,
            "data_qualified_count": 16,
            "interface_qualified_count": 38,
            "fully_eligible_count": 38,
        })
        registered = {x["model_code"] for x in self.registry.list_models(True)}
        self.assertEqual(registered, EXPECTED_IDS)
        self.assertTrue(BASELINE_IDS <= registered)

    def test_every_tool_executes_five_qualification_cases(self):
        for code in sorted(EXPECTED_IDS):
            with self.subTest(code=code):
                report = self.registry.qualification_report(code)
                self.assertTrue(report["qualified"], report["reasons"])
                self.assertGreaterEqual(report["normal_cases_passed"], 3)
                self.assertGreaterEqual(report["boundary_or_failure_cases_passed"], 2)

    def test_b001_shomate_internal_identity(self):
        result = self.ok("B001", {"species": "Fe(s)", "temperature": 1000}).result
        self.assertEqual(result["method"], "Shomate")
        self.assertAlmostEqual(result["Cp"], 35.47286, places=5)
        self.assertEqual(result["data_source"], "database_repository")

    def test_b002_is_true_nasa7_and_cp_matches_coefficients(self):
        result = self.ok("B002", {"species": "O2(g)", "temperature": 900}).result
        self.assertEqual(result["method"], "NASA7")
        a = result["coefficients"]
        expected = result["gas_constant"] * sum(a[i] * 900 ** i for i in range(5))
        self.assertAlmostEqual(result["Cp"], expected, places=10)

    def test_b003_molar_and_mass_bases_are_consistent(self):
        molar = self.ok("B003", {"species": "Fe(s)", "temperature_start": 298.15, "temperature_end": 1000, "amount": 1, "amount_basis": "mol"}).result
        mass = self.ok("B003", {"species": "Fe(s)", "temperature_start": 298.15, "temperature_end": 1000, "amount": 0.055845, "amount_basis": "kg"}).result
        self.assertAlmostEqual(molar["delta_H_total_kj"], mass["delta_H_total_kj"], places=9)

    def test_b004_entropy_is_state_function_difference(self):
        props_a = self.ok("B001", {"species": "Fe(s)", "temperature": 298.15}).result
        props_b = self.ok("B001", {"species": "Fe(s)", "temperature": 1000}).result
        entropy = self.ok("B004", {"species": "Fe(s)", "temperature_start": 298.15, "temperature_end": 1000}).result
        self.assertAlmostEqual(entropy["delta_S"], props_b["S"] - props_a["S"], places=9)

    def test_b005_reference_state_is_explicit_and_g_equals_h_minus_ts(self):
        result = self.ok("B005", {"species": "Fe(s)", "temperature": 1000}).result
        self.assertEqual(result["enthalpy_reference"], "H(298.15 K)=0 sensible reference")
        self.assertAlmostEqual(result["G"], result["H"] - 1000 * result["S"] / 1000, places=10)

    def test_b006_to_b009_thermodynamic_chain(self):
        payload = {"reaction": "C + O₂ → CO₂", "temperature": 1000}
        dh = self.ok("B006", payload).result["delta_H"]
        ds = self.ok("B007", payload).result["delta_S"]
        dg = self.ok("B008", payload).result["delta_G"]
        equilibrium = self.ok("B009", payload).result
        self.assertAlmostEqual(dg, dh - 1000 * ds / 1000, places=10)
        self.assertAlmostEqual(math.log(equilibrium["K"]), -dg * 1000 / (8.31446261815324 * 1000), places=10)

    def test_b010_vant_hoff_is_reversible(self):
        forward = self.ok("B010", {"K_reference": 10, "temperature_reference": 1000, "temperature_target": 1200, "delta_H_kj_mol": 100}).result["K_target"]
        backward = self.ok("B010", {"K_reference": forward, "temperature_reference": 1200, "temperature_target": 1000, "delta_H_kj_mol": 100}).result["K_target"]
        self.assertAlmostEqual(backward, 10, places=9)

    def test_b011_ellingham_line_has_expected_slope(self):
        result = self.ok("B011", {"reaction": "2Fe + O2 -> 2FeO", "temperatures": [800, 1000, 1200]}).result
        points = result["points"]
        slope = (points[2]["delta_G_kj_mol"] - points[0]["delta_G_kj_mol"]) / 400
        self.assertAlmostEqual(slope, -result["delta_S_j_mol_k"] / 1000, places=12)

    def test_b014_b015_overlap_at_zero_interaction(self):
        payload = {"compositions": {"Fe": 0.7, "C": 0.3}, "temperature": 1800}
        ideal = self.ok("B014", payload).result
        regular = self.ok("B015", {**payload, "omega_j_mol": 0}).result
        self.assertEqual(ideal["activities"], regular["activities"])
        self.assertTrue(all(v == 1 for v in ideal["activity_coefficients"].values()))

    def test_b018_phase_rule_and_b019_lever_conservation(self):
        phase_rule = self.ok("B018", {"components": 2, "phases": 2}).result
        self.assertEqual(phase_rule["degrees_of_freedom"], 2)
        lever = self.ok("B019", {"overall_composition": 0.4, "phase1_composition": 0.2, "phase2_composition": 0.8}).result
        self.assertAlmostEqual(lever["phase1_fraction"] + lever["phase2_fraction"], 1, places=12)
        self.assertAlmostEqual(lever["conservation_residual"], 0, places=12)

    def test_c001_arrhenius_and_c002_ev_conversion(self):
        rate = self.ok("C001", {"A": 1e7, "Ea": 80000, "temperature": 1000, "Ea_unit": "J/mol"}).result
        self.assertAlmostEqual(rate["k"], 1e7 * math.exp(-80000 / (8.31446261815324 * 1000)), places=10)
        ev = self.ok("C002", {"D0": 1e-4, "Q": 1, "temperature": 1000, "Q_unit": "eV/particle"}).result
        joule = self.ok("C002", {"D0": 1e-4, "Q": 96485.33212331001, "temperature": 1000, "Q_unit": "J/mol"}).result
        self.assertAlmostEqual(ev["D"], joule["D"], places=20)

    def test_c003_fick_boundary_and_c004_jmak_monotonicity(self):
        fick = self.ok("C003", {"diffusion_coefficient": 1e-10, "initial_concentration": 0, "surface_concentration": 1, "time_s": 3600, "positions_m": [0, 0.001]}).result
        self.assertEqual(fick["profile"][0]["concentration"], 1)
        self.assertLess(fick["profile"][1]["concentration"], 1)
        jmak = self.ok("C004", {"k": 0.01, "avrami_exponent": 2, "times_s": [0, 10, 20]}).result
        values = [x["fraction_transformed"] for x in jmak["curve"]]
        self.assertEqual(values[0], 0)
        self.assertLess(values[1], values[2])

    def test_t001_fourier_identity_and_t002_stefan_boltzmann_sign(self):
        conduction = self.ok("T001", {"thermal_conductivity": 20, "thickness": 0.1, "area": 2, "hot_temperature": 1000, "cold_temperature": 500}).result
        self.assertAlmostEqual(conduction["heat_rate_w"], conduction["temperature_difference_k"] / conduction["thermal_resistance_k_per_w"], places=10)
        hot = self.ok("T002", {"emitter_temperature": 1000, "surroundings_temperature": 500, "emissivity": 0.8, "area": 2, "view_factor": 1}).result["net_radiation_w"]
        cold = self.ok("T002", {"emitter_temperature": 500, "surroundings_temperature": 1000, "emissivity": 0.8, "area": 2, "view_factor": 1}).result["net_radiation_w"]
        self.assertAlmostEqual(hot, -cold, places=8)

    def test_d001_stoichiometric_oxygen_and_d002_energy_closure(self):
        oxygen = self.ok("D001", {
            "metal_inputs": [{"name": "carbon", "mass_kg": 12.011, "composition": {"C": 1}}],
            "target_steel_mass_kg": 0.000001,
            "target_composition": {"C": 0},
            "carbon_to_co2_fraction": 1,
        }).result
        self.assertAlmostEqual(oxygen["theoretical_oxygen_mass_kg"], 31.998, places=5)
        self.assertAlmostEqual(oxygen["theoretical_oxygen_normal_volume_m3"], 22.414, places=5)
        heat = self.ok("D002", {
            "hot_metal_mass_kg": 1000, "hot_metal_temperature_k": 1773,
            "scrap_mass_kg": 100, "scrap_temperature_k": 298.15,
            "reaction_heat_kj": 200000, "heat_loss_kj": 10000,
            "solve_for": "final_temperature",
        }).result
        self.assertAlmostEqual(heat["energy_closure_error_kj"], 0, places=6)


if __name__ == "__main__":
    unittest.main()
