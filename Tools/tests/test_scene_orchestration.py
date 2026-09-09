"""Contract and vertical-slice tests for the five scene workbench APIs."""

from __future__ import annotations

import os
import sys
import unittest

from fastapi.testclient import TestClient


TOOLS = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

from models_server import app, registry


class SceneOrchestrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_five_scenes_reuse_exactly_the_existing_registry(self):
        response = self.client.get("/api/v1/scenes")
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body["scene_count"], 5)
        self.assertEqual(body["registered_count"], 120)
        self.assertEqual(body["qualified_executable_count"], 120)
        scenes = {item["scene_id"]: item for item in body["scenes"]}
        self.assertEqual(set(scenes), {"thermodynamics", "converter", "blastfurnace", "casting", "simulation"})
        self.assertEqual(scenes["simulation"]["applicable_tool_count"], 120)
        self.assertEqual(set(scenes["simulation"]["applicable_tool_ids"]), set(registry._models))
        self.assertTrue(all(item["applicable_tool_count"] <= 120 for item in scenes.values()))

    def test_reaction_recipe_executes_bound_chain_and_safety_gate(self):
        detail = self.client.get(
            "/api/v1/scenes/thermodynamics/recipes/reaction-thermodynamics-v1"
        ).json()
        response = self.client.post(
            "/api/v1/scenes/thermodynamics/recipes/reaction-thermodynamics-v1/execute",
            json=detail["sample_request"],
        )
        self.assertEqual(response.status_code, 200, response.text)
        run = response.json()
        self.assertEqual(run["status"], "success")
        self.assertEqual(run["successful_step_count"], 7)
        self.assertTrue(run["safety_gate_passed"])
        self.assertTrue(run["work_order_release_eligible"])
        by_step = {item["step_id"]: item for item in run["steps"]}
        reaction = by_step["balance"]["output"]["balanced_reaction"]
        self.assertEqual(by_step["balance_check"]["input"]["reaction"], reaction)
        self.assertEqual(by_step["gibbs"]["input"]["reaction"], reaction)
        self.assertEqual(len({item["trace_id"] for item in run["steps"]}), 1)

        work_order_response = self.client.post(
            "/api/v1/scenes/thermodynamics/work-orders",
            json={"run_id": run["run_id"], "operator_notes": "只用于离线技术复核"},
        )
        self.assertEqual(work_order_response.status_code, 200, work_order_response.text)
        work_order = work_order_response.json()
        self.assertEqual(work_order["status"], "ready_for_human_review")
        self.assertTrue(work_order["release_eligible"])
        self.assertFalse(work_order["dispatch_supported"])
        self.assertEqual(work_order["tool_count_effect"], 0)
        self.assertIn("人工复核", work_order["deterministic_markdown"])
        self.assertTrue(work_order["text_generation_policy"]["llm_assistance_optional"])
        self.assertFalse(work_order["text_generation_policy"]["llm_may_change_numeric_results"])
        self.assertNotIn("operator_notes", work_order["narrative_context"])
        narrative_json = str(work_order["narrative_context"]).lower()
        self.assertNotIn("zip_path", narrative_json)
        self.assertNotIn("file_contents", narrative_json)

        review_response = self.client.post(
            f"/api/v1/work-orders/{work_order['work_order_id']}/review",
            json={"action": "approve", "reviewer": "test-reviewer", "comment": "证据链完整"},
        )
        self.assertEqual(review_response.status_code, 200, review_response.text)
        reviewed = review_response.json()
        self.assertEqual(reviewed["status"], "approved_for_manual_execution")
        self.assertFalse(reviewed["dispatch_supported"])
        self.assertIn("审核人：test-reviewer", reviewed["deterministic_markdown"])
        self.assertNotIn("当前状态：等待人工审核", reviewed["deterministic_markdown"])

        repeated_review = self.client.post(
            f"/api/v1/work-orders/{work_order['work_order_id']}/review",
            json={"action": "reject", "reviewer": "second-reviewer"},
        )
        self.assertEqual(repeated_review.status_code, 409, repeated_review.text)
        self.assertEqual(repeated_review.json()["detail"]["error_code"], "WORK_ORDER_ALREADY_REVIEWED")

    def test_missing_dependency_and_evidence_fail_closed(self):
        missing_dependency = self.client.post(
            "/api/v1/scenes/thermodynamics/recipes/reaction-thermodynamics-v1/execute",
            json={"selected_steps": ["equilibrium"], "arguments_by_step": {"equilibrium": {"temperature": 1000}}},
        )
        self.assertEqual(missing_dependency.status_code, 409, missing_dependency.text)
        self.assertEqual(missing_dependency.json()["detail"]["error_code"], "SCENE_DEPENDENCY_MISSING")

        rejected_run = self.client.post(
            "/api/v1/scenes/thermodynamics/recipes/reaction-thermodynamics-v1/execute",
            json={"selected_steps": ["balance"], "arguments_by_step": {"balance": {}}},
        )
        self.assertEqual(rejected_run.status_code, 200, rejected_run.text)
        run = rejected_run.json()
        self.assertEqual(run["status"], "rejected")
        self.assertEqual(run["steps"][0]["status"], "rejected")
        no_evidence = self.client.post(
            "/api/v1/scenes/thermodynamics/work-orders",
            json={"run_id": run["run_id"]},
        )
        self.assertEqual(no_evidence.status_code, 400, no_evidence.text)
        self.assertEqual(no_evidence.json()["detail"]["error_code"], "WORK_ORDER_NO_EVIDENCE")

    def test_unverified_work_order_cannot_be_approved(self):
        detail = self.client.get(
            "/api/v1/scenes/thermodynamics/recipes/reaction-thermodynamics-v1"
        ).json()
        request = detail["sample_request"]
        request["selected_steps"] = ["balance"]
        request["arguments_by_step"] = {"balance": request["arguments_by_step"]["balance"]}
        request["options"]["artifact_steps"] = []
        run = self.client.post(
            "/api/v1/scenes/thermodynamics/recipes/reaction-thermodynamics-v1/execute",
            json=request,
        ).json()
        work_order = self.client.post(
            "/api/v1/scenes/thermodynamics/work-orders", json={"run_id": run["run_id"]}
        ).json()
        self.assertEqual(work_order["status"], "draft_unverified")
        response = self.client.post(
            f"/api/v1/work-orders/{work_order['work_order_id']}/review",
            json={"action": "approve", "reviewer": "test-reviewer"},
        )
        self.assertEqual(response.status_code, 409, response.text)
        self.assertEqual(response.json()["detail"]["error_code"], "WORK_ORDER_NOT_RELEASE_ELIGIBLE")


if __name__ == "__main__":
    unittest.main()
