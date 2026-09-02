"""P1-W13 admission, independent-property, database and forced-call tests."""

from __future__ import annotations

import hashlib
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
from models_core.repositories.reference_repository import _cursor
from models_server import app


W13_IDS = {"C008", "D018", "D019", "D020"}
DATA_IDS = {"C008"}
VISCOSITY_ASSET = TOOLS / "models_core" / "data" / "melt_viscosity_correlations_w13_v1.json"
VISCOSITY_SHA256 = "c57bff170f8f16eccc18ace52d25c2acc62638af58315841e7e5533f798a7048"


def case_payload(registry: ModelRegistry, code: str, case_id: str | None = None) -> dict:
    cases = registry.get(code).qualification_cases
    if case_id is None:
        return next(case["input"] for case in cases if case["kind"] == "normal")
    return next(case["input"] for case in cases if case["id"] == case_id)


class P1W13ViscosityBofOptimizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = ModelRegistry()
        cls.registry.discover()
        cls.client = TestClient(app)

    def ok(self, code: str, payload: dict):
        result = self.registry.invoke(code, payload)
        self.assertTrue(result.success, result.error)
        return result

    def test_four_tools_pass_all_gates_and_counts(self):
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
        for code in sorted(W13_IDS):
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

    def test_c008_urbain_equation_and_temperature_monotonicity(self):
        payload = case_payload(self.registry, "C008", "C008-N1")
        execution = self.ok("C008", payload)
        output = execution.result
        # Independent reconstruction uses the approved DS_IUPAC_AW_2021 values.
        aw = {"Si": 28.085, "O": 15.999, "Al": 26.982, "Ca": 40.078, "Mg": 24.305}
        molar_mass = {
            "SiO2": aw["Si"] + 2 * aw["O"],
            "Al2O3": 2 * aw["Al"] + 3 * aw["O"],
            "CaO": aw["Ca"] + aw["O"],
            "MgO": aw["Mg"] + aw["O"],
        }
        raw = {key: payload["composition_wt_pct"][key] / molar_mass[key] for key in molar_mass}
        total = sum(raw.values())
        x = {key: value / total for key, value in raw.items()}
        alpha = (x["CaO"] + x["MgO"]) / (x["CaO"] + x["MgO"] + x["Al2O3"])
        coefficients = [
            13.8 + 39.9355 * alpha - 44.049 * alpha**2,
            30.481 - 117.1505 * alpha + 129.9978 * alpha**2,
            -40.9429 + 234.0486 * alpha - 300.04 * alpha**2,
            60.7619 - 153.9276 * alpha + 211.1616 * alpha**2,
        ]
        b_value = sum(value * x["SiO2"]**power for power, value in enumerate(coefficients))
        ln_a = -11.57 - 0.29 * b_value
        temperature = payload["temperature_k"]
        expected = math.exp(ln_a) * temperature * math.exp(1000 * b_value / temperature)
        self.assertAlmostEqual(output["dynamic_viscosity_pa_s"], expected, places=12)
        self.assertAlmostEqual(sum(output["correlation_parameters"]["oxide_mole_fractions"].values()), 1, places=12)
        hotter = self.ok("C008", {**payload, "temperature_k": temperature + 100}).result
        self.assertLess(hotter["dynamic_viscosity_pa_s"], output["dynamic_viscosity_pa_s"])
        self.assertLess(output["d_ln_viscosity_d_temperature"], 0)

    def test_c008_hirai_melting_point_identity_and_arrhenius_ratio(self):
        payload = case_payload(self.registry, "C008", "C008-B1")
        at_melting = self.ok("C008", payload).result
        rho = payload["density_kg_m3"]
        tm = payload["liquidus_temperature_k"]
        molar_mass = payload["mean_molar_mass_kg_mol"]
        expected_tm = 1.7e-7 * rho ** (2 / 3) * tm**0.5 * molar_mass ** (-1 / 6)
        self.assertAlmostEqual(at_melting["dynamic_viscosity_pa_s"], expected_tm, places=14)
        t2 = 1.2 * tm
        at_t2 = self.ok("C008", {**payload, "temperature_k": t2}).result
        activation = 2.65 * tm**1.27
        expected_ratio = math.exp(activation / 8.3144 * (1 / t2 - 1 / tm))
        actual_ratio = at_t2["dynamic_viscosity_pa_s"] / at_melting["dynamic_viscosity_pa_s"]
        self.assertAlmostEqual(actual_ratio, expected_ratio, places=13)

    def test_c008_asset_database_and_record_provenance(self):
        self.assertEqual(hashlib.sha256(VISCOSITY_ASSET.read_bytes()).hexdigest(), VISCOSITY_SHA256)
        with _cursor() as cursor:
            cursor.execute(
                "SELECT model_id,is_approved FROM metallurgy_v2.melt_viscosity_model_definition "
                "WHERE dataset_id=%s ORDER BY model_id",
                ("DS_MELT_VISCOSITY_W13",),
            )
            rows = cursor.fetchall()
            cursor.execute(
                "SELECT status,dry_run,details FROM metallurgy_v2.dataset_import_run "
                "WHERE dataset_id=%s ORDER BY completed_at DESC LIMIT 1",
                ("DS_MELT_VISCOSITY_W13",),
            )
            import_run = cursor.fetchone()
        self.assertEqual([(row["model_id"], row["is_approved"]) for row in rows], [
            ("HIRAI_LIQUID_ALLOY_1993", True), ("URBAIN_SLAG_1981", True),
        ])
        self.assertEqual(import_run["status"], "committed")
        self.assertFalse(import_run["dry_run"])
        self.assertEqual(import_run["details"]["backup"]["sha256"],
                         "05bd3b9c930b3799d25b4dec2e04ab0e0d3e397737b54f3dc07cff815b7be5b5")
        execution = self.ok("C008", case_payload(self.registry, "C008", "C008-N1"))
        records = {(item.dataset_id, item.table) for item in execution.provenance}
        self.assertIn(("DS_MELT_VISCOSITY_W13", "metallurgy_v2.melt_viscosity_model_definition"), records)
        self.assertIn(("DS_IUPAC_AW_2021", "metallurgy_v2.element_reference"), records)
        self.assertTrue(all(item.record_id for item in execution.provenance))

    def test_d018_exact_target_closure_and_order_invariance(self):
        payload = case_payload(self.registry, "D018", "D018-N1")
        base = self.ok("D018", payload).result
        self.assertAlmostEqual(sum(stage["oxygen_volume_nm3"] for stage in base["stages"]), 120, places=12)
        self.assertAlmostEqual(base["weighted_l1_deviation_nm3"], 0, places=12)
        for stage in base["stages"]:
            self.assertAlmostEqual(stage["duration_min"] * stage["oxygen_flow_nm3_min"], stage["oxygen_volume_nm3"], places=12)
        reversed_result = self.ok("D018", {**payload, "stages": list(reversed(payload["stages"]))}).result
        volumes = {stage["name"]: stage["oxygen_volume_nm3"] for stage in base["stages"]}
        reversed_volumes = {stage["name"]: stage["oxygen_volume_nm3"] for stage in reversed_result["stages"]}
        self.assertEqual(volumes, reversed_volumes)
        self.assertAlmostEqual(base["useful_oxygen_nm3"] + base["oxygen_loss_nm3"], 120, places=12)

    def test_d019_closed_form_mass_balance_and_batch_integrality(self):
        payload = case_payload(self.registry, "D019", "D019-N1")
        output = self.ok("D019", payload).result
        expected = (0.01 * 1000 - 0.005 * 1000) / (0.8 * 0.9 - 0.01 * 1.0)
        self.assertAlmostEqual(output["total_addition_kg"], expected, places=12)
        self.assertAlmostEqual(output["final_composition_wt_pct"]["Mn"], 1.0, places=12)
        self.assertAlmostEqual(output["element_balances"][0]["mass_reconstruction_residual_kg"], 0, places=12)
        batch = self.ok("D019", case_payload(self.registry, "D019", "D019-N3")).result
        self.assertTrue(batch["integrality_used"])
        self.assertAlmostEqual(batch["additions"][0]["addition_kg"] % 5, 0, places=10)
        self.assertEqual(batch["additions"][0]["batch_count"], 2)

    def test_d020_energy_identity_minimum_cost_and_batch_integrality(self):
        payload = case_payload(self.registry, "D020", "D020-N1")
        output = self.ok("D020", payload).result
        expected_q_min = 100000 * 0.8 * (1900 - 1870) / 1000
        self.assertAlmostEqual(output["achieved_heat_removal_mj"], expected_q_min, places=10)
        self.assertAlmostEqual(output["predicted_final_temperature_k"], 1870, places=10)
        additions = {item["name"]: item["addition_kg"] for item in output["additions"]}
        self.assertEqual(additions["scrap"], 0)
        self.assertAlmostEqual(additions["ore"], expected_q_min / 2.0, places=10)
        self.assertAlmostEqual(output["energy_closure_residual_mj"], 0, places=12)
        batch = self.ok("D020", case_payload(self.registry, "D020", "D020-N2")).result
        self.assertTrue(batch["integrality_used"])
        for item in batch["additions"]:
            self.assertAlmostEqual(item["addition_kg"] % item["batch_size_kg"], 0, places=9)

    def test_schema_real_http_and_forced_route_for_each_new_tool(self):
        response = self.client.get("/api/v1/tools")
        self.assertEqual(response.status_code, 200)
        manifest = response.json()
        self.assertEqual(manifest["total"], 109)
        self.assertEqual(manifest["catalog_coverage_count"], 91)
        definitions = {item["model_code"]: item for item in manifest["tools"]}
        for code in sorted(W13_IDS):
            with self.subTest(code=code):
                payload = case_payload(self.registry, code)
                definition = definitions[code]
                schema = definition["function"]["parameters"]
                self.assertFalse(schema["additionalProperties"])
                self.assertEqual(set(schema["required"]), {field.name for field in self.registry.get(code).input_fields if field.required})
                called = self.client.post(
                    f"/api/v1/tools/{definition['function']['name']}/call",
                    json={"arguments": payload},
                )
                self.assertEqual(called.status_code, 200, called.text)
                self.assertEqual(called.json()["status"], "success")
                self.assertEqual(called.json()["model_code"], code)
                forced = self.client.post("/api/v1/experiments/run", json={
                    "user_query": f"强制调用{code}，不得使用其他工具。",
                    "mode": "forced",
                    "model_code": code,
                    "arguments": payload,
                    "llm_name": "isolated-http-contract-test",
                    "prompt_version": "p1-w13-v1",
                })
                self.assertEqual(forced.status_code, 200, forced.text)
                body = forced.json()
                self.assertEqual(body["selected_model"], code)
                self.assertEqual(body["execution_result"]["status"], "success")

    def test_provider_forced_case_manifest_has_one_case_per_tool(self):
        path = TOOLS / "benchmarks" / "llm_tool_call_cases_p1_w13.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual({case["model_code"] for case in payload["cases"]}, W13_IDS)
        self.assertEqual(len(payload["cases"]), 4)
        self.assertIn("not a research dataset", payload["purpose"])
        for case in payload["cases"]:
            self.assertTrue(case["force_tool_choice"])
            self.assertTrue(case["expected"])


if __name__ == "__main__":
    unittest.main()
