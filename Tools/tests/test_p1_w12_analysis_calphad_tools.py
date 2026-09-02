"""P1-W12 admission, properties, database provenance and forced-call tests."""

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


W12_IDS = {"A009", "A010", "B020", "B022", "B023", "B024", "B025"}
DATA_IDS = {"B023", "B024"}
R_J_MOL_K = 8.31446261815324


def normal_payload(registry: ModelRegistry, code: str) -> dict:
    return next(case["input"] for case in registry.get(code).qualification_cases if case["kind"] == "normal")


class P1W12AnalysisCalphadToolTests(unittest.TestCase):
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
            "registered_count": 105,
            "runtime_tool_count": 105,
            "catalog_coverage_count": 87,
            "qualified_executable_count": 105,
            "implementation_qualified_count": 105,
            "data_required_count": 35,
            "data_qualified_count": 35,
            "interface_qualified_count": 105,
            "fully_eligible_count": 105,
        })
        for code in sorted(W12_IDS):
            with self.subTest(code=code):
                admission = self.registry.qualification_report(code)
                eligibility = self.registry.eligibility_report(code)
                self.assertTrue(admission["qualified"], admission["reasons"])
                self.assertGreaterEqual(admission["normal_cases_passed"], 3)
                self.assertGreaterEqual(admission["boundary_or_failure_cases_passed"], 2)
                self.assertTrue(eligibility["fully_eligible"], eligibility)
                self.assertEqual(eligibility["data_required"], code in DATA_IDS)
                model = self.registry.get(code)
                self.assertEqual(model.catalog_id, code)
                self.assertEqual(model.catalog_mapping_status, "same")
                self.assertTrue(model.catalog_coverage)
                self.assertTrue(model.source_records)
                self.assertTrue(model.independent_validation)
                self.assertTrue(model.relations)
                self.assertTrue(model.tool_uid.startswith(f"metallurgy.catalog.{code.lower()}."))

    def test_a009_iqr_and_affine_invariance(self):
        payload = {
            "values": [1, 2, 3, 4, 100],
            "labels": ["a", "b", "c", "d", "e"],
            "method": "iqr",
            "threshold": 1.5,
            "value_unit": "wt%",
        }
        base = self.ok("A009", payload).result
        shifted_scaled = self.ok("A009", {
            **payload,
            "values": [10 * value + 7 for value in payload["values"]],
            "value_unit": "scaled_wt%",
        }).result
        self.assertEqual(base["outlier_indices"], [4])
        self.assertEqual(base["outlier_labels"], ["e"])
        self.assertEqual(base["flags"], shifted_scaled["flags"])
        self.assertEqual(base["scores"], shifted_scaled["scores"])
        self.assertEqual(base["lower_fence"], -1)
        self.assertEqual(base["upper_fence"], 7)

    def test_a010_analytic_variance_and_fixed_seed_reproducibility(self):
        linear = self.ok("A010", normal_payload(self.registry, "A010")).result
        self.assertAlmostEqual(linear["output_estimate"], 35, places=10)
        self.assertAlmostEqual(linear["standard_uncertainty"], 0.5, places=8)
        self.assertAlmostEqual(linear["linearized_variance_closure_residual"], 0, places=12)
        monte_carlo_payload = next(
            case["input"] for case in self.registry.get("A010").qualification_cases
            if case["id"] == "A010-N3"
        )
        first = self.ok("A010", monte_carlo_payload).result
        second = self.ok("A010", monte_carlo_payload).result
        self.assertEqual(first, second)
        self.assertAlmostEqual(first["standard_uncertainty"], math.sqrt(5), delta=0.08)

    def test_b020_nodes_linear_identity_monotonicity_and_uncertainty(self):
        payload = normal_payload(self.registry, "B020")
        linear = self.ok("B020", payload).result
        pchip = self.ok("B020", {**payload, "method": "pchip"}).result
        self.assertEqual(linear["interpolated_value"], 1100)
        self.assertEqual(linear["first_derivative"], 400)
        self.assertAlmostEqual(linear["propagated_standard_uncertainty"], math.hypot(1, 1.5), places=12)
        self.assertEqual(pchip["interpolated_value"], linear["interpolated_value"])
        self.assertEqual(pchip["pchip_minus_linear"], 0)
        node = self.ok("B020", {**payload, "query_value": 0.5, "method": "pchip"}).result
        self.assertTrue(node["exact_knot"])
        self.assertEqual(node["interpolated_value"], 1200)

    def test_b022_element_closure_pure_phase_and_ideal_ratio(self):
        pure = self.ok("B022", normal_payload(self.registry, "B022")).result
        self.assertEqual(pure["species_amounts_mol"]["A_alpha"], 1)
        self.assertEqual(pure["species_amounts_mol"]["A_beta"], 0)
        self.assertEqual(pure["total_gibbs_energy_j"], 0)
        ideal_payload = next(
            case["input"] for case in self.registry.get("B022").qualification_cases
            if case["id"] == "B022-N3"
        )
        ideal = self.ok("B022", ideal_payload).result
        ratio = ideal["species_amounts_mol"]["A1"] / ideal["species_amounts_mol"]["A2"]
        self.assertAlmostEqual(ratio, math.exp(1000 / (R_J_MOL_K * 1000)), places=7)
        self.assertLessEqual(ideal["max_abs_element_residual_mol"], 1e-10)

    def test_b023_database_provenance_phase_and_composition_closure(self):
        execution = self.ok("B023", normal_payload(self.registry, "B023"))
        output = execution.result
        self.assertEqual(output["model_asset_id"], "MATCALC-MC_FE-2.059-PYCALPHAD")
        self.assertEqual(output["dataset_id"], "DS_MATCALC_MC_FE_2059")
        self.assertEqual(output["database_version"], "mc_fe_v2.059")
        self.assertLess(abs(output["phase_fraction_closure_residual"]), 1e-8)
        self.assertAlmostEqual(sum(item["phase_amount_fraction"] for item in output["stable_phases"]), 1, places=8)
        for phase in output["stable_phases"]:
            self.assertAlmostEqual(sum(phase["component_mole_fractions"].values()), 1, places=8)
        records = [item for item in execution.provenance if item.dataset_id == "DS_MATCALC_MC_FE_2059"]
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].table, "metallurgy_v2.solidification_model_definition")
        self.assertTrue(records[0].record_id)
        self.assertEqual(records[0].checksum, "sha256:a8628b6e0cb117f31d8278d87545e2d29fea78c9573694d0c51f1c72e50ac5e3")

    def test_b024_scheil_path_component_and_phase_closure(self):
        output = self.ok("B024", normal_payload(self.registry, "B024")).result
        self.assertTrue(output["converged"])
        self.assertLessEqual(output["path"][-1]["fraction_liquid"], output["residual_liquid_stop_fraction"])
        self.assertLess(output["max_abs_component_balance_residual"], 2e-5)
        self.assertLess(output["max_abs_phase_fraction_closure_residual"], 2e-8)
        self.assertGreater(output["maximum_liquid_enrichment_factors"]["C"], 1)
        self.assertTrue(any(point["new_solid_phase_mole_fractions"] for point in output["path"]))
        temperatures = [point["temperature_k"] for point in output["path"]]
        liquid = [point["fraction_liquid"] for point in output["path"]]
        self.assertTrue(all(a >= b for a, b in zip(temperatures, temperatures[1:])))
        self.assertTrue(all(a >= b for a, b in zip(liquid, liquid[1:])))

    def test_b025_reports_physical_violations_without_execution_failure(self):
        valid = self.ok("B025", normal_payload(self.registry, "B025")).result
        self.assertTrue(valid["passed"])
        violation_case = next(
            case["input"] for case in self.registry.get("B025").qualification_cases
            if case["id"] == "B025-B1"
        )
        execution = self.ok("B025", violation_case)
        self.assertFalse(execution.boundary_check.passed)
        self.assertFalse(execution.result["passed"])
        self.assertEqual(execution.result["violation_count"], 1)
        self.assertEqual(execution.result["violations"][0]["check"], "phase_rule")

    def test_schema_http_and_forced_route_for_each_new_tool(self):
        manifest = self.client.get("/api/v1/tools").json()
        self.assertEqual(manifest["total"], 105)
        self.assertEqual(manifest["catalog_coverage_count"], 87)
        definitions = {item["model_code"]: item for item in manifest["tools"]}
        for code in sorted(W12_IDS):
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
                self.assertEqual(response.json()["status"], "success")
                forced = self.client.post("/api/v1/experiments/run", json={
                    "user_query": f"强制调用{code}，不得使用其他工具。",
                    "mode": "forced",
                    "model_code": code,
                    "arguments": payload,
                    "llm_name": "isolated-http-contract-test",
                    "prompt_version": "p1-w12-v1",
                })
                self.assertEqual(forced.status_code, 200, forced.text)
                self.assertEqual(forced.json()["selected_model"], code)
                self.assertEqual(forced.json()["execution_result"]["status"], "success")

    def test_provider_forced_case_manifest_has_one_case_per_tool(self):
        path = TOOLS / "benchmarks" / "llm_tool_call_cases_p1_w12.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual({case["model_code"] for case in payload["cases"]}, W12_IDS)
        self.assertEqual(len(payload["cases"]), 7)
        self.assertIn("not a research dataset", payload["purpose"])
        for case in payload["cases"]:
            self.assertTrue(case["force_tool_choice"])
            self.assertTrue(case["expected"])


if __name__ == "__main__":
    unittest.main()
