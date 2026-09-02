"""P1-W17 admission, scientific-property, HTTP and forced-call tests."""

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
from models_core.thermo_assets import R_J_MOL_K
from models_server import app


W17_IDS = {"G004", "G008", "G009", "G010"}


def case_payload(registry: ModelRegistry, code: str, case_id: str | None = None) -> dict:
    cases = registry.get(code).qualification_cases
    if case_id is None:
        return next(case["input"] for case in cases if case["kind"] == "normal")
    return next(case["input"] for case in cases if case["id"] == case_id)


class P1W17ODELookupSensitivityUncertaintyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = ModelRegistry()
        cls.registry.discover()
        cls.client = TestClient(app)

    def ok(self, code: str, payload: dict):
        result = self.registry.invoke(code, payload)
        self.assertTrue(result.success, result.error)
        return result

    def test_four_tools_pass_all_gates_and_dynamic_counts(self):
        self.assertEqual(self.registry.get_counts(), {
            "registered_count": 113,
            "runtime_tool_count": 113,
            "catalog_coverage_count": 95,
            "qualified_executable_count": 113,
            "implementation_qualified_count": 113,
            "data_required_count": 35,
            "data_qualified_count": 35,
            "interface_qualified_count": 113,
            "fully_eligible_count": 113,
        })
        for code in sorted(W17_IDS):
            with self.subTest(code=code):
                admission = self.registry.qualification_report(code)
                eligibility = self.registry.eligibility_report(code)
                self.assertTrue(admission["qualified"], admission["reasons"])
                self.assertEqual(admission["normal_cases_passed"], 3)
                self.assertEqual(admission["boundary_or_failure_cases_passed"], 3)
                self.assertTrue(eligibility["fully_eligible"], eligibility)
                self.assertFalse(eligibility["data_required"])
                self.assertTrue(self.registry.get(code).catalog_coverage)

    def test_g004_matches_analytic_solutions_conservation_and_failures(self):
        irreversible = self.ok("G004", case_payload(self.registry, "G004", "G004-N1")).result
        expected_a = 10 * math.exp(-0.2 * 10)
        self.assertAlmostEqual(irreversible["final_concentrations_mol_m3"]["A"], expected_a, delta=2e-6)
        self.assertAlmostEqual(irreversible["final_concentrations_mol_m3"]["B"], 10 - expected_a, delta=2e-6)
        self.assertAlmostEqual(sum(irreversible["final_concentrations_mol_m3"].values()), 10, delta=1e-8)

        reversible = self.ok("G004", case_payload(self.registry, "G004", "G004-N2")).result
        expected_equilibrium_a = 2 + 8 * math.exp(-0.5 * 20)
        self.assertAlmostEqual(reversible["final_concentrations_mol_m3"]["A"], expected_equilibrium_a, delta=2e-5)
        self.assertAlmostEqual(sum(reversible["final_concentrations_mol_m3"].values()), 10, delta=1e-7)

        inert = self.ok("G004", case_payload(self.registry, "G004", "G004-N3")).result
        self.assertEqual([row["concentrations_mol_m3"]["inert"] for row in inert["time_series"]], [7.5] * 11)
        self.assertEqual(inert["final_reaction_rates_mol_m3_s"], {})
        for case_id in ("G004-F1", "G004-F2"):
            result = self.registry.invoke("G004", case_payload(self.registry, "G004", case_id))
            self.assertFalse(result.success)
            self.assertIsNotNone(result.error_code)

    def test_g008_affine_bilinear_nearest_and_boundary_policy(self):
        linear = self.ok("G008", case_payload(self.registry, "G008", "G008-N1")).result
        self.assertEqual(linear["interpolated_value"], 5)
        self.assertAlmostEqual(sum(row["weight"] for row in linear["corner_points"]), 1, places=15)

        bilinear = self.ok("G008", case_payload(self.registry, "G008", "G008-N2")).result
        self.assertEqual(bilinear["interpolated_value"], 1.25)
        self.assertAlmostEqual(sum(row["weight"] for row in bilinear["corner_points"]), 1, places=15)

        nearest = self.ok("G008", case_payload(self.registry, "G008", "G008-N3")).result
        self.assertEqual(nearest["interpolated_value"], 200)
        clamped = self.ok("G008", case_payload(self.registry, "G008", "G008-B1"))
        self.assertFalse(clamped.boundary_check.passed)
        self.assertEqual(clamped.result["interpolated_value"], 10)
        rejected = self.registry.invoke("G008", case_payload(self.registry, "G008", "G008-F1"))
        self.assertFalse(rejected.success)
        self.assertEqual(rejected.error_code, "OUT_OF_DOMAIN")

    def test_g009_recovers_analytic_derivatives_and_reports_local_limit(self):
        affine = self.ok("G009", case_payload(self.registry, "G009", "G009-N1")).result
        row = affine["parameter_results"][0]
        self.assertAlmostEqual(row["first_derivative"], 2, places=12)
        self.assertAlmostEqual(row["second_derivative"], 0, places=10)
        self.assertEqual(affine["evaluation_count"], 3)

        arrhenius_payload = case_payload(self.registry, "G009", "G009-N2")
        arrhenius = self.ok("G009", arrhenius_payload).result
        k = arrhenius["baseline_output_value"]
        expected = k * 80000 / (R_J_MOL_K * 1000**2)
        self.assertAlmostEqual(arrhenius["parameter_results"][0]["first_derivative"], expected, delta=expected * 2e-6)

        conduction = self.ok("G009", case_payload(self.registry, "G009", "G009-N3")).result
        by_path = {row["path"]: row for row in conduction["parameter_results"]}
        self.assertAlmostEqual(by_path["thermal_conductivity"]["first_derivative"], 10000, places=8)
        self.assertAlmostEqual(by_path["area"]["first_derivative"], 100000, places=7)
        boundary = self.ok("G009", case_payload(self.registry, "G009", "G009-B1"))
        self.assertFalse(boundary.boundary_check.passed)
        for case_id in ("G009-F1", "G009-F2"):
            self.assertFalse(self.registry.invoke("G009", case_payload(self.registry, "G009", case_id)).success)

    def test_g010_is_reproducible_and_matches_statistical_properties(self):
        payload = case_payload(self.registry, "G010", "G010-N1")
        first = self.ok("G010", payload).result
        second = self.ok("G010", payload).result
        self.assertEqual(first, second)
        stats = first["output_statistics"]
        self.assertAlmostEqual(stats["mean"], 2.0, delta=0.08)
        self.assertAlmostEqual(stats["sample_standard_deviation"], math.sqrt(1 / 3), delta=0.08)
        self.assertLessEqual(stats["minimum"], stats["p05"])
        self.assertLessEqual(stats["p05"], stats["p50"])
        self.assertLessEqual(stats["p50"], stats["p95"])
        self.assertLessEqual(stats["p95"], stats["maximum"])
        interval = first["failure_probability_wilson_95"]
        self.assertLessEqual(interval[0], first["estimated_failure_probability"])
        self.assertGreaterEqual(interval[1], first["estimated_failure_probability"])

        correlated = self.ok("G010", case_payload(self.registry, "G010", "G010-N2")).result
        realized = correlated["realized_correlation_matrix"][0][1]
        self.assertGreater(realized, 0.35)
        self.assertLess(realized, 0.65)
        constant = self.ok("G010", case_payload(self.registry, "G010", "G010-N3")).result
        self.assertEqual(constant["output_statistics"]["mean"], 5)
        self.assertEqual(constant["output_statistics"]["sample_standard_deviation"], 0)
        self.assertEqual(constant["failure_count"], 0)
        boundary = self.ok("G010", case_payload(self.registry, "G010", "G010-B1"))
        self.assertFalse(boundary.boundary_check.passed)
        for case_id in ("G010-F1", "G010-F2"):
            self.assertFalse(self.registry.invoke("G010", case_payload(self.registry, "G010", case_id)).success)

    def test_schema_http_and_local_forced_route_for_each_new_tool(self):
        response = self.client.get("/api/v1/tools")
        self.assertEqual(response.status_code, 200)
        manifest = response.json()
        self.assertEqual(manifest["total"], 113)
        self.assertEqual(manifest["catalog_coverage_count"], 95)
        definitions = {item["model_code"]: item for item in manifest["tools"]}
        for code in sorted(W17_IDS):
            with self.subTest(code=code):
                payload = case_payload(self.registry, code)
                definition = definitions[code]
                self.assertFalse(definition["function"]["parameters"]["additionalProperties"])
                called = self.client.post(
                    f"/api/v1/tools/{definition['function']['name']}/call",
                    json={"arguments": payload},
                )
                self.assertEqual(called.status_code, 200, called.text)
                self.assertEqual(called.json()["status"], "success")
                self.assertEqual(called.json()["model_code"], code)
                forced = self.client.post("/api/v1/experiments/run", json={
                    "user_query": f"强制调用{code}，不得使用其他工具。",
                    "mode": "forced", "model_code": code, "arguments": payload,
                    "llm_name": "isolated-http-contract-test", "prompt_version": "p1-w17-v1",
                })
                self.assertEqual(forced.status_code, 200, forced.text)
                self.assertEqual(forced.json()["selected_model"], code)
                self.assertEqual(forced.json()["execution_result"]["status"], "success")

    def test_nested_schemas_and_provider_manifest_are_explicit(self):
        g004 = self.registry.get("G004").get_llm_input_schema()
        g008 = self.registry.get("G008").get_llm_input_schema()
        g009 = self.registry.get("G009").get_llm_input_schema()
        g010 = self.registry.get("G010").get_llm_input_schema()
        self.assertEqual(set(g004["properties"]["reactions"]["items"]["required"]), {
            "name", "reactants", "products", "forward_rate_constant_per_s",
            "reverse_rate_constant_per_s", "reference_concentration_mol_m3",
        })
        self.assertIn("out_of_bounds_policy", g008["required"])
        self.assertTrue(g009["properties"]["parameter_steps"]["items"]["additionalProperties"] is False)
        self.assertTrue(g010["properties"]["uncertain_parameters"]["items"]["additionalProperties"] is False)
        path = TOOLS / "benchmarks" / "llm_tool_call_cases_p1_w17.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual({case["model_code"] for case in payload["cases"]}, W17_IDS)
        self.assertEqual(len(payload["cases"]), 4)
        self.assertIn("not a research dataset", payload["purpose"])
        self.assertTrue(all(case["force_tool_choice"] and case["expected"] for case in payload["cases"]))


if __name__ == "__main__":
    unittest.main()
