from __future__ import annotations

import hashlib
import io
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

from fastapi.testclient import TestClient


TOOLS = Path(__file__).resolve().parents[1]
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import models_server
from models_core import ModelRegistry
from models_core.artifacts import RECOMMENDED_ARTIFACT_TOOLS, ToolArtifactService
from models_core.services import InMemoryTraceStore, ModelExecutionService


def normal_case(registry: ModelRegistry, code: str, case_id: str | None = None) -> dict:
    cases = [case for case in registry.get(code).qualification_cases if case.get("kind") == "normal"]
    if case_id:
        return next(case["input"] for case in cases if case["id"] == case_id)
    return cases[0]["input"]


class ToolExecutionArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = ModelRegistry()
        cls.registry.discover()
        cls.client = TestClient(models_server.app)

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "tool_artifacts"
        self.store = InMemoryTraceStore()
        self.artifacts = ToolArtifactService(self.root)
        self.service = ModelExecutionService(self.registry, self.store, self.artifacts)

    def tearDown(self):
        self.temporary.cleanup()

    def test_capability_classifies_native_recommended_and_optional_outputs(self):
        native = self.artifacts.capability(self.registry.get("G005"))
        recommended = self.artifacts.capability(self.registry.get("G004"))
        optional = self.artifacts.capability(self.registry.get("T001"))
        self.assertEqual(native["delivery"], "native_case_bundle")
        self.assertEqual(native["request_location"], "arguments.artifact_mode")
        self.assertTrue(recommended["recommended"])
        self.assertIn("time_series", recommended["csv_output_fields"])
        self.assertFalse(optional["recommended"])
        self.assertEqual(optional["csv_output_fields"], [])
        self.assertEqual(len(RECOMMENDED_ARTIFACT_TOOLS), 30)

    def test_timeseries_execution_materializes_readable_directory_and_zip(self):
        result = self.service.execute(
            "G004",
            normal_case(self.registry, "G004", "G004-N1"),
            options={"artifact": {"mode": "directory_and_zip", "name": "reaction_ode_01"}},
        )
        self.assertEqual(result["status"], "success", result)
        artifact = result["artifact"]
        directory = Path(artifact["artifact_directory"])
        zip_path = Path(artifact["zip_path"])
        self.assertTrue(artifact["readback_verified"])
        self.assertFalse(artifact["artifact_reused"])
        self.assertEqual(directory.parent, (self.root / "g004").resolve())
        self.assertTrue((directory / "input.json").is_file())
        self.assertTrue((directory / "result.json").is_file())
        self.assertTrue((directory / "README.md").is_file())
        self.assertTrue((directory / "manifest.json").is_file())
        self.assertTrue((directory / "tables" / "time_series.csv").is_file())
        self.assertTrue(zip_path.is_file())
        self.assertEqual(hashlib.sha256(zip_path.read_bytes()).hexdigest(), artifact["zip_sha256"])
        self.assertEqual(
            json.loads((directory / "result.json").read_text(encoding="utf-8")),
            result["output"],
        )
        csv_text = (directory / "tables" / "time_series.csv").read_text(encoding="utf-8")
        self.assertIn("time_s", csv_text.splitlines()[0])
        with zipfile.ZipFile(zip_path) as archive:
            names = set(archive.namelist())
            self.assertIn("reaction_ode_01/result.json", names)
            self.assertIn("reaction_ode_01/tables/time_series.csv", names)

    def test_scalar_execution_gets_lossless_json_bundle_without_fake_csv(self):
        result = self.service.execute(
            "T001",
            normal_case(self.registry, "T001"),
            options={"artifact": {"mode": "directory", "name": "steady_wall_01"}},
        )
        self.assertEqual(result["status"], "success", result)
        artifact = result["artifact"]
        self.assertEqual(artifact["delivery_profile"], "optional")
        self.assertEqual(artifact["csv_files"], [])
        self.assertIsNone(artifact["zip_path"])
        self.assertEqual(
            json.loads(Path(artifact["artifact_directory"], "result.json").read_text(encoding="utf-8")),
            result["output"],
        )

    def test_existing_execution_export_is_idempotent_and_different_content_is_not_overwritten(self):
        first = self.service.execute("T001", normal_case(self.registry, "T001"))
        self.assertEqual(first["status"], "success")
        request = {"mode": "directory_and_zip", "name": "review_bundle_01"}
        created = self.service.materialize_execution_artifact(first["execution_id"], request)
        repeated = self.service.materialize_execution_artifact(first["execution_id"], request)
        self.assertFalse(created["artifact_reused"])
        self.assertTrue(repeated["artifact_reused"])
        self.assertEqual(created["zip_sha256"], repeated["zip_sha256"])
        before = Path(created["artifact_directory"], "result.json").read_bytes()

        changed_input = dict(normal_case(self.registry, "T001"))
        changed_input["hot_temperature"] += 10
        collision = self.service.execute(
            "T001",
            changed_input,
            options={"artifact": request},
        )
        self.assertEqual(collision["status"], "rejected")
        self.assertEqual(collision["error_code"], "MODEL_ARTIFACT_UNAVAILABLE")
        self.assertEqual(Path(created["artifact_directory"], "result.json").read_bytes(), before)

    def test_path_escape_and_generic_g005_export_are_rejected_before_calculation(self):
        bad_name = self.service.execute(
            "T001",
            normal_case(self.registry, "T001"),
            options={"artifact": {"mode": "directory", "name": "../escape"}},
        )
        self.assertEqual(bad_name["status"], "rejected")
        self.assertEqual(bad_name["error_code"], "INVALID_INPUT")
        self.assertFalse(self.root.exists())

        g005 = self.service.execute(
            "G005",
            normal_case(self.registry, "G005"),
            options={"artifact": {"mode": "directory"}},
        )
        self.assertEqual(g005["status"], "rejected")
        self.assertEqual(g005["error_code"], "INVALID_INPUT")
        self.assertIn("arguments.artifact_mode", g005["error"])

    def test_http_manifest_and_post_execution_export_contract(self):
        capabilities = self.client.get("/api/v1/artifacts/capabilities")
        self.assertEqual(capabilities.status_code, 200)
        body = capabilities.json()
        self.assertEqual(body["total"], 120)
        self.assertEqual(body["native_case_bundle_count"], 1)
        self.assertEqual(body["recommended_result_bundle_count"], 30)
        definitions = {item["model_code"]: item for item in self.client.get("/api/v1/tools").json()["tools"]}
        self.assertEqual(definitions["G005"]["artifact_capability"]["delivery"], "native_case_bundle")
        self.assertTrue(definitions["F005"]["artifact_capability"]["recommended"])

        old_service = models_server.execution_service.artifact_service
        try:
            models_server.execution_service.artifact_service = ToolArtifactService(self.root)
            called = self.client.post(
                f"/api/v1/tools/{definitions['T001']['function']['name']}/call",
                json={"arguments": normal_case(self.registry, "T001")},
            )
            self.assertEqual(called.status_code, 200, called.text)
            self.assertEqual(called.json()["status"], "success")
            exported = self.client.post(
                f"/api/v1/executions/{called.json()['execution_id']}/artifact",
                json={"mode": "directory_and_zip", "name": "http_export_01"},
            )
            self.assertEqual(exported.status_code, 200, exported.text)
            self.assertTrue(exported.json()["readback_verified"])
            self.assertTrue(Path(exported.json()["zip_path"]).is_file())

            direct = self.client.post(
                f"/api/v1/tools/{definitions['G004']['function']['name']}/call",
                json={
                    "arguments": normal_case(self.registry, "G004", "G004-N2"),
                    "options": {
                        "validate_boundary": True,
                        "return_provenance": True,
                        "artifact": {"mode": "directory", "name": "http_ode_01"},
                    },
                },
            )
            self.assertEqual(direct.status_code, 200, direct.text)
            self.assertEqual(direct.json()["status"], "success", direct.text)
            self.assertTrue(direct.json()["artifact"]["readback_verified"])
            self.assertIn("tables/time_series.csv", direct.json()["artifact"]["csv_files"])
        finally:
            models_server.execution_service.artifact_service = old_service

    def test_experiment_can_generate_and_download_verified_zip(self):
        old_service = models_server.execution_service.artifact_service
        try:
            models_server.execution_service.artifact_service = ToolArtifactService(self.root)
            response = self.client.post("/api/v1/experiments/run", json={
                "user_query": "强制计算稳态平板导热并生成可下载结果包",
                "mode": "forced",
                "model_code": "T001",
                "arguments": normal_case(self.registry, "T001"),
                "artifact": {"mode": "directory_and_zip", "name": "experiment_wall_01"},
            })
            self.assertEqual(response.status_code, 200, response.text)
            execution = response.json()["execution_result"]
            self.assertEqual(execution["status"], "success", response.text)
            self.assertTrue(execution["artifact"]["readback_verified"])

            download = self.client.get(
                f"/api/v1/executions/{execution['execution_id']}/artifact/download"
            )
            self.assertEqual(download.status_code, 200, download.text)
            self.assertEqual(download.headers["content-type"], "application/zip")
            self.assertEqual(
                hashlib.sha256(download.content).hexdigest(),
                download.headers["x-artifact-sha256"],
            )
            with zipfile.ZipFile(io.BytesIO(download.content)) as archive:
                self.assertIn("experiment_wall_01/result.json", archive.namelist())

            no_zip = self.client.post(
                f"/api/v1/tools/{self.registry.get('T001').tool_name}/call",
                json={
                    "arguments": normal_case(self.registry, "T001"),
                    "options": {"artifact": {"mode": "directory", "name": "directory_only_01"}},
                },
            ).json()
            rejected_download = self.client.get(
                f"/api/v1/executions/{no_zip['execution_id']}/artifact/download"
            )
            self.assertEqual(rejected_download.status_code, 400)
            self.assertEqual(
                rejected_download.json()["detail"]["error_code"],
                "MODEL_ARTIFACT_UNAVAILABLE",
            )
        finally:
            models_server.execution_service.artifact_service = old_service


if __name__ == "__main__":
    unittest.main()
