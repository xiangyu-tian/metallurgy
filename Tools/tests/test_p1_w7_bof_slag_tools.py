"""P1-W7 admission and independent scientific tests for D005/D006/D010-D014."""
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


W7_IDS = {"D005", "D006", "D010", "D011", "D012", "D013", "D014"}


def normal_payload(registry: ModelRegistry, code: str) -> dict:
    model = registry.get(code)
    return next(case["input"] for case in model.qualification_cases if case["kind"] == "normal")


class P1W7BofSlagToolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = ModelRegistry()
        cls.registry.discover()
        cls.client = TestClient(app)

    def ok(self, code: str, payload: dict):
        result = self.registry.invoke(code, payload)
        self.assertTrue(result.success, result.error)
        return result

    def test_seven_tools_pass_all_gates_and_counts(self):
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
        for code in W7_IDS:
            with self.subTest(code=code):
                admission = self.registry.qualification_report(code)
                eligibility = self.registry.eligibility_report(code)
                self.assertTrue(admission["qualified"], admission["reasons"])
                self.assertEqual(admission["normal_cases_passed"], 3)
                self.assertEqual(admission["boundary_or_failure_cases_passed"], 2)
                self.assertTrue(eligibility["fully_eligible"], eligibility)
                self.assertEqual(eligibility["data_required"], code != "D006")
                model = self.registry.get(code)
                self.assertEqual(model.catalog_id, code)
                self.assertTrue(model.source_records)
                self.assertTrue(model.independent_validation)
                self.assertTrue(model.failure_modes)
                self.assertTrue(model.relations)

    def test_d005_stoichiometry_stream_closure_and_capture_linearity(self):
        base_payload = {
            "oxidized_element_masses_kg": {"Si": 28.085},
            "oxide_product_formulas": {"Si": "SiO2"},
        }
        base = self.ok("D005", base_payload)
        expected_sio2 = 28.085 + 2 * 15.999
        self.assertAlmostEqual(
            base.result["oxidation_product_masses_kg"]["SiO2"], expected_sio2, places=10
        )
        self.assertAlmostEqual(base.result["total_slag_mass_kg"], expected_sio2, places=10)
        self.assertLess(abs(base.result["mass_closure_residual_kg"]), 1e-12)
        half = self.ok("D005", {**base_payload, "oxide_capture_fractions": {"Si": 0.5}})
        self.assertAlmostEqual(
            half.result["oxidation_product_masses_kg"]["SiO2"], expected_sio2 / 2, places=10
        )
        streams = self.ok("D005", {
            **base_payload,
            "flux_streams": [{"name": "lime", "mass_kg": 10, "composition": {"CaO": 0.9, "SiO2": 0.1}}],
            "entrained_metal_mass_kg": 2,
        })
        self.assertAlmostEqual(streams.result["total_slag_mass_kg"], expected_sio2 + 12, places=10)
        self.assertAlmostEqual(sum(streams.result["component_mass_fractions"].values()), 1, places=12)
        invalid = self.registry.invoke("D005", {
            **base_payload,
            "flux_streams": [{"name": "bad", "mass_kg": 1, "composition": {"CaO": 0.8}}],
        })
        self.assertFalse(invalid.success)
        self.assertEqual(invalid.error_code, "INVALID_INPUT")
        not_an_oxide = self.registry.invoke("D005", {
            "oxidized_element_masses_kg": {"Si": 1},
            "oxide_product_formulas": {"Si": "Si"},
        })
        self.assertFalse(not_an_oxide.success)
        self.assertEqual(not_an_oxide.error_code, "MODEL_NOT_APPLICABLE")

    def test_d006_named_and_custom_ratios_are_scale_invariant(self):
        base = self.ok("D006", {
            "component_masses_kg": {"CaO": 40, "MgO": 10, "SiO2": 20, "Al2O3": 5},
            "definition": "R4_CaO_MgO_SiO2_Al2O3",
        }).result
        scaled = self.ok("D006", {
            "component_masses_kg": {"CaO": 120, "MgO": 30, "SiO2": 60, "Al2O3": 15},
            "definition": "R4_CaO_MgO_SiO2_Al2O3",
        }).result
        self.assertAlmostEqual(base["basicity"], 2.0, places=15)
        self.assertAlmostEqual(scaled["basicity"], base["basicity"], places=15)
        custom = self.ok("D006", {
            "component_masses_kg": {"CaO": 40, "MgO": 10, "SiO2": 20, "Al2O3": 5},
            "definition": "CUSTOM",
            "custom_numerator_components": ["CaO", "MgO"],
            "custom_denominator_components": ["SiO2", "Al2O3"],
        }).result
        self.assertAlmostEqual(custom["basicity"], 2.0, places=15)
        zero = self.registry.invoke("D006", {
            "component_masses_kg": {"CaO": 10, "SiO2": 0},
            "definition": "R2_CaO_SiO2",
        })
        self.assertFalse(zero.success)
        self.assertEqual(zero.error_code, "DIVISION_BY_ZERO")

    def test_d010_reproduces_published_equation_and_phosphorus_balance(self):
        payload = normal_payload(self.registry, "D010")
        result = self.ok("D010", payload)
        composition = payload["slag_composition_mass_percent"]
        expected_log_apparent = (
            0.06 * composition["CaO"] + 0.0222 * composition["MgO"]
            + 0.279 * composition["P2O5"] - 0.003 * composition["Al2O3"]
            - 0.012 * composition["SiO2"] + 11570 / payload["temperature_k"] - 10.52
        )
        expected_lp = 10 ** (expected_log_apparent + 2.5 * math.log10(payload["tfe_mass_percent"]))
        self.assertAlmostEqual(result.result["log10_apparent_partition"], expected_log_apparent, places=12)
        self.assertAlmostEqual(result.result["phosphorus_partition_ratio"], expected_lp, places=9)
        self.assertAlmostEqual(
            result.result["equilibrium_slag_p_mass_percent"]
            / result.result["equilibrium_metal_p_mass_percent"], expected_lp, places=9
        )
        reconstructed = (
            payload["metal_mass_kg"] * result.result["equilibrium_metal_p_mass_percent"] / 100
            + payload["slag_mass_kg"] * result.result["equilibrium_slag_p_mass_percent"] / 100
        )
        self.assertAlmostEqual(reconstructed, result.result["total_p_mass_kg"], places=12)
        self.assertEqual({record.dataset_id for record in result.provenance}, {"DS_BOF_P_PARTITION_ISIJ_2016"})

    def test_d011_reproduces_optical_basicity_capacity_partition_and_balance(self):
        payload = normal_payload(self.registry, "D011")
        result = self.ok("D011", payload)
        # Independent arithmetic uses the same reviewed 2021 snapshot precision,
        # copied here rather than calling the runtime repository implementation.
        molar_masses = {"CaO": 40.078 + 15.999, "SiO2": 28.085 + 2 * 15.999,
                        "Al2O3": 2 * 26.982 + 3 * 15.999, "MgO": 24.305 + 15.999}
        lambdas = {"CaO": 1.0, "SiO2": 0.48, "Al2O3": 0.61, "MgO": 0.78}
        oxygen_equivalent = {"CaO": 1, "SiO2": 2, "Al2O3": 3, "MgO": 1}
        weights = {
            component: payload["slag_component_masses_kg"][component] / molar_masses[component]
            * oxygen_equivalent[component]
            for component in payload["slag_component_masses_kg"]
        }
        optical = sum(weights[c] * lambdas[c] for c in weights) / sum(weights.values())
        expected_log_cs = -6.08 + 4.49 / optical + (15893 - 15864 / optical) / payload["temperature_k"]
        expected_log_ls = (
            expected_log_cs - math.log10(payload["oxygen_activity"])
            + math.log10(payload["sulfur_activity_coefficient"])
            - 420 / payload["temperature_k"] + 1.14
        )
        self.assertAlmostEqual(result.result["optical_basicity"], optical, places=8)
        self.assertAlmostEqual(result.result["log10_sulfide_capacity"], expected_log_cs, places=8)
        self.assertAlmostEqual(result.result["log10_sulfur_partition_ratio"], expected_log_ls, places=8)
        reconstructed = (
            payload["metal_mass_kg"] * result.result["equilibrium_metal_s_mass_percent"] / 100
            + payload["slag_mass_kg"] * result.result["equilibrium_slag_s_mass_percent"] / 100
        )
        self.assertAlmostEqual(reconstructed, result.result["total_s_mass_kg"], places=12)
        datasets = {record.dataset_id for record in result.provenance}
        self.assertTrue({"DS_SLAG_S_CAPACITY_ISIJ_2013", "DS_S_DISTRIBUTION_ISIJ_2016", "DS_IUPAC_AW_2021"}.issubset(datasets))

    def test_d012_and_d013_reproduce_mass_action_and_reject_zero_initial_activity(self):
        mn_payload = normal_payload(self.registry, "D012")
        mn = self.ok("D012", mn_payload).result
        expected_mn_logk = 6440 / mn_payload["temperature_k"] - 2.83
        expected_mn = mn_payload["mno_activity"] / (
            10 ** expected_mn_logk * mn_payload["feo_activity"]
            * mn_payload["mn_activity_coefficient"]
        )
        self.assertAlmostEqual(mn["log10_equilibrium_constant"], expected_mn_logk, places=12)
        self.assertAlmostEqual(mn["equilibrium_mn_mass_percent"], expected_mn, places=12)

        si_payload = normal_payload(self.registry, "D013")
        si = self.ok("D013", si_payload).result
        expected_si_logk = 18100 / si_payload["temperature_k"] - 6.372
        expected_si = si_payload["sio2_activity"] / (
            10 ** expected_si_logk * si_payload["feo_activity"] ** 2
            * si_payload["si_activity_coefficient"]
        )
        self.assertAlmostEqual(si["log10_equilibrium_constant"], expected_si_logk, places=12)
        self.assertAlmostEqual(si["equilibrium_si_mass_percent"], expected_si, places=12)
        for code, field in (("D012", "initial_mn_mass_percent"), ("D013", "initial_si_mass_percent")):
            invalid = self.registry.invoke(code, {**normal_payload(self.registry, code), field: 0})
            self.assertFalse(invalid.success)
            self.assertEqual(invalid.error_code, "INVALID_INPUT")

    def test_d014_species_stoichiometry_scaling_and_loss_identity(self):
        payload = {
            "slag_mass_kg": 100,
            "iron_species_mass_fractions": {"FeO": 0.1, "Fe2O3": 0.05, "Fe3O4": 0.03, "Fe": 0.01},
            "steel_tapped_mass_kg": 900,
            "iron_value_per_kg": 2.5,
        }
        result = self.ok("D014", payload).result
        fe, oxygen = 55.845, 15.999
        expected = {
            "FeO": 10 * fe / (fe + oxygen),
            "Fe2O3": 5 * (2 * fe) / (2 * fe + 3 * oxygen),
            "Fe3O4": 3 * (3 * fe) / (3 * fe + 4 * oxygen),
            "Fe": 1,
        }
        for species, value in expected.items():
            self.assertAlmostEqual(result["iron_breakdown_kg"][species], value, places=9)
        self.assertAlmostEqual(result["total_iron_loss_kg"], sum(expected.values()), places=9)
        self.assertAlmostEqual(result["economic_loss"], result["total_iron_loss_kg"] * 2.5, places=10)
        self.assertAlmostEqual(
            result["metal_recovery_fraction"], 900 / (900 + result["total_iron_loss_kg"]), places=12
        )

    def test_database_tools_fail_closed_when_postgresql_is_unavailable(self):
        with mock.patch.dict(os.environ, {
            "METALLURGY_DB_NAME": "metallurgy_p1_w7_missing_database",
            "METALLURGY_DB_CONNECT_TIMEOUT": "1",
        }):
            for code in ("D005", "D010", "D011", "D012", "D013", "D014"):
                with self.subTest(code=code):
                    result = self.registry.invoke(code, normal_payload(self.registry, code))
                    self.assertFalse(result.success)
                    self.assertEqual(result.error_code, "DATA_BACKEND_UNAVAILABLE")

    def test_schema_http_and_local_forced_routes_for_each_tool(self):
        manifest = self.client.get("/api/v1/tools").json()
        self.assertEqual(manifest["total"], 101)
        self.assertEqual(manifest["catalog_coverage_count"], 83)
        definitions = {item["model_code"]: item for item in manifest["tools"]}
        for code in sorted(W7_IDS):
            payload = normal_payload(self.registry, code)
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
                forced = self.client.post("/api/v1/experiments/run", json={
                    "user_query": f"强制调用{code}，不得选择其他工具。",
                    "mode": "forced",
                    "model_code": code,
                    "arguments": payload,
                    "llm_name": "isolated-http-contract-test",
                    "prompt_version": "p1-w7-v1",
                })
                self.assertEqual(forced.status_code, 200, forced.text)
                forced_body = forced.json()
                self.assertEqual(forced_body["selected_model"], code)
                self.assertEqual(forced_body["execution_result"]["status"], "success")
                self.assertEqual(forced_body["execution_result"]["model_code"], code)


if __name__ == "__main__":
    unittest.main()
