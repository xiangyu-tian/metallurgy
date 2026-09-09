"""P1-W18 final-120 admission, science, data, HTTP, and forced-call tests."""
from __future__ import annotations

import inspect
import json
import math
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import psycopg2
from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "Tools"
sys.path.insert(0, str(TOOLS))

from models_core import ModelRegistry
import models_core.models_g_w18 as models_g_w18
from models_core.models_g_w18 import constrained_dominates
from models_core.repositories.reference_repository import R_J_MOL_K
from models_server import app
from database.import_nist_janaf_iron_reduction_w18 import (
    import_asset,
    load_and_validate_asset,
)


W18_IDS = {"G005", "G006", "G011", "G012", "G013", "E022", "H001"}
FORMULA_IDS = {"G005", "G006", "G011", "G012", "G013"}
DATA_IDS = {"E022", "H001"}


def case_payload(registry: ModelRegistry, code: str, case_id: str | None = None) -> dict:
    cases = registry.get(code).qualification_cases
    if case_id is None:
        return next(case["input"] for case in cases if case["kind"] == "normal")
    return next(case["input"] for case in cases if case["id"] == case_id)


class P1W18Final120ToolsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = ModelRegistry()
        cls.registry.discover()
        cls.client = TestClient(app)

    def ok(self, code: str, payload: dict):
        result = self.registry.invoke(code, payload)
        self.assertTrue(result.success, result.error)
        return result

    def test_seven_tools_pass_all_gates_and_close_dynamic_counts(self):
        self.assertEqual(self.registry.get_counts(), {
            "registered_count": 120,
            "runtime_tool_count": 120,
            "catalog_coverage_count": 100,
            "qualified_executable_count": 120,
            "implementation_qualified_count": 120,
            "data_required_count": 37,
            "data_qualified_count": 37,
            "interface_qualified_count": 120,
            "fully_eligible_count": 120,
        })
        for code in sorted(W18_IDS):
            with self.subTest(code=code):
                admission = self.registry.qualification_report(code)
                eligibility = self.registry.eligibility_report(code)
                self.assertTrue(admission["qualified"], admission["reasons"])
                self.assertEqual(admission["normal_cases_passed"], 3)
                self.assertGreaterEqual(admission["boundary_or_failure_cases_passed"], 2)
                self.assertTrue(eligibility["fully_eligible"], eligibility)
                self.assertEqual(eligibility["data_required"], code in DATA_IDS)
                self.assertEqual(self.registry.get(code).data_requirement == "FORMULA_ONLY", code in FORMULA_IDS)
                self.assertTrue(self.registry.get(code).source_records)
                self.assertTrue(self.registry.get(code).relations)
                self.assertTrue(self.registry.get(code).dependencies)

    def test_g005_case_structure_determinism_and_closed_path_policy(self):
        payload = case_payload(self.registry, "G005", "G005-N1")
        first = self.ok("G005", payload).result
        second = self.ok("G005", payload).result
        self.assertEqual(first, second)
        self.assertEqual(first["cell_count"], 20 * 4 * 2)
        self.assertEqual(set(first["files"]), {
            "0/T", "constant/transportProperties", "system/blockMeshDict",
            "system/controlDict", "system/fvSchemes", "system/fvSolution",
        })
        self.assertIn("hex (0 1 2 3 4 5 6 7)", first["files"]["system/blockMeshDict"])
        self.assertTrue(all("version 2.0;" in content for content in first["files"].values()))
        for boundary in ("left", "right", "insulated"):
            self.assertIn(boundary, first["files"]["0/T"])
            self.assertIn(boundary, first["files"]["system/blockMeshDict"])
        self.assertFalse(self.registry.invoke("G005", case_payload(self.registry, "G005", "G005-F1")).success)

    def test_g005_materializes_readable_case_zip_idempotently_and_rejects_conflict(self):
        payload = {
            **case_payload(self.registry, "G005", "G005-N1"),
            "artifact_mode": "directory_and_zip",
        }
        input_schema = self.registry.get("G005").get_llm_input_schema()
        self.assertEqual(
            input_schema["properties"]["artifact_mode"]["enum"],
            ["manifest_only", "directory", "directory_and_zip"],
        )
        self.assertNotIn("artifact_mode", input_schema["required"])
        with tempfile.TemporaryDirectory() as temporary_directory:
            artifact_root = Path(temporary_directory) / "openfoam_cases"
            with patch.object(models_g_w18, "OPENFOAM_CASE_ROOT", artifact_root):
                first = self.ok("G005", payload).result
                case_directory = Path(first["case_directory"])
                zip_path = Path(first["zip_path"])

                self.assertTrue(first["materialized"])
                self.assertTrue(first["readback_verified"])
                self.assertFalse(first["artifact_reused"])
                self.assertEqual(case_directory.parent.resolve(), artifact_root.resolve())
                self.assertTrue(case_directory.is_dir())
                self.assertTrue(zip_path.is_file())
                self.assertTrue(Path(first["case_manifest_path"]).is_file())
                self.assertTrue(first["structural_validation"]["verified"])

                for relative_path, expected_content in first["files"].items():
                    self.assertEqual(
                        (case_directory / relative_path).read_text(encoding="utf-8"),
                        expected_content,
                    )
                with zipfile.ZipFile(zip_path) as archive:
                    self.assertEqual(
                        set(archive.namelist()),
                        {f"{payload['case_name']}/{path}" for path in first["files"]}
                        | {f"{payload['case_name']}/case_manifest.json"},
                    )
                    self.assertEqual(
                        archive.read(f"{payload['case_name']}/0/T").decode("utf-8"),
                        first["files"]["0/T"],
                    )

                second = self.ok("G005", payload).result
                self.assertTrue(second["artifact_reused"])
                self.assertEqual(second["manifest_sha256"], first["manifest_sha256"])
                self.assertEqual(second["zip_sha256"], first["zip_sha256"])

                called = self.client.post(
                    "/api/v1/tools/metallurgy_generate_openfoam_laplacian_case/call",
                    json={"arguments": payload},
                )
                self.assertEqual(called.status_code, 200, called.text)
                self.assertEqual(called.json()["status"], "success")
                self.assertTrue(called.json()["output"]["materialized"])
                self.assertTrue(called.json()["output"]["readback_verified"])
                self.assertTrue(called.json()["output"]["artifact_reused"])

                conflict = dict(payload)
                conflict["left_temperature_k"] = payload["left_temperature_k"] + 1
                failed = self.registry.invoke("G005", conflict)
                self.assertFalse(failed.success)
                self.assertEqual(failed.error_code, "INVALID_INPUT")
                self.assertEqual(
                    (case_directory / "0/T").read_text(encoding="utf-8"),
                    first["files"]["0/T"],
                )

    def test_g006_cartesian_results_match_direct_registry_calls(self):
        result = self.ok("G006", case_payload(self.registry, "G006", "G006-N1")).result
        self.assertEqual(result["planned_runs"], math.prod(result["grid_shape"]))
        self.assertEqual(result["completed_runs"], result["successful_runs"] + result["failed_runs"])
        for run in result["runs"]:
            direct = self.ok("T001", {
                "thermal_conductivity": run["parameter_values"]["thermal_conductivity"],
                "thickness": 0.1, "area": 1, "hot_temperature": 1000, "cold_temperature": 500,
            }).result
            self.assertEqual(run["output"], direct)
        self.assertEqual(
            self.ok("G006", case_payload(self.registry, "G006", "G006-N1")).result["batch_sha256"],
            result["batch_sha256"],
        )

    def test_g011_reproducibility_ei_and_known_monotone_optimum(self):
        payload = case_payload(self.registry, "G011", "G011-N1")
        first = self.ok("G011", payload).result
        second = self.ok("G011", payload).result
        self.assertEqual(first, second)
        self.assertEqual(first["evaluation_count"], 9)
        self.assertEqual(first["best_parameters"]["thermal_conductivity"], 100.0)
        self.assertEqual(first["best_objective_value"], 500000.0)
        selected_ei = [row["expected_improvement_at_selection"] for row in first["history"] if row["expected_improvement_at_selection"] is not None]
        self.assertTrue(selected_ei)
        self.assertTrue(all(value >= 0 for value in selected_ei))

    def test_g012_reproducibility_nondominance_and_compromise_contract(self):
        payload = case_payload(self.registry, "G012", "G012-N1")
        first = self.ok("G012", payload).result
        second = self.ok("G012", payload).result
        self.assertEqual(first, second)
        self.assertEqual(first["evaluation_count"], 10 * (3 + 1))
        solutions = first["pareto_solutions"]
        self.assertGreaterEqual(len(solutions), 2)
        objectives = [
            {"feasible": True, "constraint_violation": 0.0,
             "minimized_objectives": [-row["objectives"]["heat"], -row["objectives"]["resistance"]]}
            for row in solutions
        ]
        for i, left in enumerate(objectives):
            for j, right in enumerate(objectives):
                if i != j:
                    self.assertFalse(constrained_dominates(left, right))
        self.assertIn(first["compromise_solution"], solutions)
        self.assertAlmostEqual(sum(first["algorithm_parameters"]["normalized_compromise_weights"]), 1.0, places=15)

    def test_g013_rules_are_safe_order_independent_and_count_closed(self):
        payload = {
            "rule_set_id": "closure", "rule_set_version": "1", "context": {"input": 100, "output": 99, "limit": 2},
            "rules": [
                {"id": "mass", "description": "质量闭合", "severity": "error", "assertion": {"op": "within", "args": [{"path": "input"}, {"path": "output"}, {"path": "limit"}]}, "recommendation": "复核物流"},
                {"id": "warning", "description": "提示阈值", "severity": "warning", "assertion": {"op": "less_than", "args": [{"path": "limit"}, {"constant": 1}]}, "recommendation": "降低阈值"},
            ],
        }
        first = self.ok("G013", payload)
        reordered = {**payload, "rules": list(reversed(payload["rules"]))}
        second = self.ok("G013", reordered)
        self.assertEqual(first.result["rules_sha256"], second.result["rules_sha256"])
        self.assertEqual(first.result["rule_count"], 2)
        self.assertEqual(first.result["error_count"] + first.result["warning_count"], len(first.result["violations"]))
        self.assertFalse(first.boundary_check.passed)
        malicious = case_payload(self.registry, "G013", "G013-F1")
        rejected = self.registry.invoke("G013", malicious)
        self.assertFalse(rejected.success)
        self.assertEqual(rejected.error_code, "INVALID_INPUT")

    def test_e022_database_gibbs_kp_stoichiometry_and_equilibrium_direction(self):
        payload = case_payload(self.registry, "E022", "E022-N1")
        result = self.ok("E022", payload)
        output = result.result
        independent_delta_g = math.fsum(
            row["stoichiometric_coefficient"] * row["standard_gibbs_kj_mol"]
            for row in output["species_standard_states"]
        )
        self.assertAlmostEqual(output["delta_g_standard_kj_mol_reaction"], independent_delta_g, places=12)
        expected_k = math.exp(-independent_delta_g * 1000 / (R_J_MOL_K * payload["temperature_k"]))
        self.assertAlmostEqual(output["equilibrium_constant_kp"], expected_k, delta=expected_k * 1e-13)
        self.assertAlmostEqual(output["q_over_k"], output["actual_oxidized_to_reducing_ratio"] / expected_k, places=15)
        atoms = {"Fe2O3": {"Fe": 2, "O": 3}, "Fe3O4": {"Fe": 3, "O": 4}, "CO": {"C": 1, "O": 1}, "CO2": {"C": 1, "O": 2}}
        states = {row["species"]: row["stoichiometric_coefficient"] for row in output["species_standard_states"]}
        for element in ("Fe", "C", "O"):
            residual = sum(coefficient * atoms[species].get(element, 0) for species, coefficient in states.items())
            self.assertEqual(residual, 0)
        ratio = output["equilibrium_constant_kp"]
        equilibrium_payload = {**payload, "reducing_gas_partial_pressure_bar": 1 / (1 + ratio), "oxidized_gas_partial_pressure_bar": ratio / (1 + ratio)}
        equilibrium = self.ok("E022", equilibrium_payload).result
        self.assertEqual(equilibrium["reaction_direction"], "equilibrium")
        self.assertAlmostEqual(equilibrium["q_over_k"], 1.0, places=12)
        self.assertTrue(all(record.dataset_id == "DS_NIST_JANAF_IRON_REDUCTION_W18" and record.record_id for record in result.provenance))

    def test_h001_equilibrium_activity_and_atomic_mass_closures(self):
        ideal = self.ok("H001", case_payload(self.registry, "H001", "H001-N1"))
        output = ideal.result
        self.assertEqual(output["activity_coefficient_deoxidizer"], 1.0)
        self.assertEqual(output["activity_coefficient_oxygen"], 1.0)
        self.assertAlmostEqual(output["standard_gibbs_j_mol_reaction"], -R_J_MOL_K * 1873 * math.log(1e12), places=8)
        self.assertAlmostEqual(output["reaction_quotient"], output["equilibrium_constant"], delta=output["equilibrium_constant"] * 2e-15)
        self.assertAlmostEqual(output["q_over_k"], 1.0, places=12)
        self.assertAlmostEqual(output["stoichiometric_oxide_kg_per_kg_oxygen"], output["stoichiometric_deoxidizer_kg_per_kg_oxygen"] + 1.0, places=14)
        self.assertEqual({record.dataset_id for record in ideal.provenance}, {"DS_IUPAC_AW_2021"})
        self.assertTrue(all(record.table == "metallurgy_v2.element_reference" and record.record_id for record in ideal.provenance))
        nonideal = self.ok("H001", case_payload(self.registry, "H001", "H001-N2")).result
        self.assertAlmostEqual(nonideal["log10_activity_coefficient_deoxidizer"], 0.002, places=15)
        self.assertAlmostEqual(nonideal["log10_activity_coefficient_oxygen"], -0.001, places=15)
        unknown = self.registry.invoke("H001", {
            **case_payload(self.registry, "H001", "H001-N1"),
            "interaction_terms": [{"target": "oxygen", "element": "Xx", "coefficient": 0.01, "mass_percent": 0.1}],
        })
        self.assertFalse(unknown.success)
        self.assertEqual(unknown.error_code, "MISSING_DATA")

    def test_data_asset_import_is_additive_idempotent_and_database_pinned(self):
        asset, checksum = load_and_validate_asset()
        self.assertEqual(len(asset["records"]), 14)
        self.assertEqual(checksum, "f2458b5414fbe6ed0c3dd4d9cefdb25900cad4b2399087f0c29fc4de62c9a85d")
        source = inspect.getsource(import_asset).upper()
        for forbidden in ("DELETE FROM", "TRUNCATE ", "DROP TABLE", "DROP SCHEMA", "UPDATE METALLURGY_V2"):
            self.assertNotIn(forbidden, source)
        completed = subprocess.run(
            [sys.executable, str(ROOT / "database" / "import_nist_janaf_iron_reduction_w18.py")],
            cwd=ROOT, check=True, capture_output=True, text=True, encoding="utf-8",
        )
        dry_run = json.loads(completed.stdout)
        self.assertEqual(dry_run["status"], "ok")
        self.assertEqual(dry_run["mode"], "dry_run")
        self.assertEqual(dry_run["dataset_inserted"], 0)
        self.assertEqual(dry_run["correlations_inserted"], 0)
        self.assertEqual(dry_run["unchanged"], 15)
        config = {"database": os.getenv("METALLURGY_DB_NAME", "metallurgy"), "user": os.getenv("METALLURGY_DB_USER", "postgres"), "password": os.getenv("METALLURGY_DB_PASSWORD", "")}
        if os.getenv("METALLURGY_DB_HOST"):
            config["host"] = os.environ["METALLURGY_DB_HOST"]
        if os.getenv("METALLURGY_DB_PORT"):
            config["port"] = int(os.environ["METALLURGY_DB_PORT"])
        with psycopg2.connect(**config) as connection, connection.cursor() as cursor:
            cursor.execute("SELECT checksum FROM metallurgy_v2.dataset_registry WHERE dataset_id=%s", (asset["dataset_id"],))
            self.assertEqual(cursor.fetchone()[0], checksum)
            cursor.execute("SELECT count(*) FROM metallurgy_v2.thermodynamic_correlation WHERE source_id=%s AND is_active", (asset["dataset_id"],))
            self.assertEqual(cursor.fetchone()[0], 14)

    def test_data_tools_fail_closed_when_postgresql_is_unavailable(self):
        with patch.dict(os.environ, {"METALLURGY_DB_NAME": "metallurgy_w18_missing_database"}):
            for code in sorted(DATA_IDS):
                with self.subTest(code=code):
                    result = self.registry.invoke(code, case_payload(self.registry, code))
                    self.assertFalse(result.success)
                    self.assertEqual(result.error_code, "DATA_BACKEND_UNAVAILABLE")

    def test_schema_http_and_local_forced_route_for_each_new_tool(self):
        response = self.client.get("/api/v1/tools")
        self.assertEqual(response.status_code, 200)
        manifest = response.json()
        self.assertEqual(manifest["total"], 120)
        self.assertEqual(manifest["catalog_coverage_count"], 100)
        definitions = {item["model_code"]: item for item in manifest["tools"]}
        for code in sorted(W18_IDS):
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
                    "llm_name": "isolated-http-contract-test", "prompt_version": "p1-w18-v1",
                })
                self.assertEqual(forced.status_code, 200, forced.text)
                self.assertEqual(forced.json()["selected_model"], code)
                self.assertEqual(forced.json()["execution_result"]["status"], "success")

    def test_nested_schemas_and_provider_manifest_are_explicit(self):
        for code, field in (("G006", "parameter_grid"), ("G011", "variables"), ("G012", "objectives"), ("G013", "rules"), ("H001", "interaction_terms")):
            schema = self.registry.get(code).get_llm_input_schema()
            self.assertFalse(schema["properties"][field]["items"]["additionalProperties"])
        path = TOOLS / "benchmarks" / "llm_tool_call_cases_p1_w18.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual({case["model_code"] for case in payload["cases"]}, W18_IDS)
        self.assertEqual(len(payload["cases"]), 7)
        self.assertIn("not a research dataset", payload["purpose"])
        self.assertTrue(all(case["force_tool_choice"] and case["expected"] for case in payload["cases"]))


if __name__ == "__main__":
    unittest.main()
