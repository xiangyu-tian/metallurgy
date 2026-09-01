"""Focused P1-W5C admission and scientific verification tests for F006."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "Tools"
sys.path.insert(0, str(TOOLS))

from models_core import ModelRegistry
from models_core.repositories.casting_endpoint_repository import endpoint_benchmark_cases
from models_server import app


LONG_MACHINE = "F006_BENCH_LONG_020M_V1"
SHORT_MACHINE = "F006_BENCH_SHORT_008M_V1"


def endpoint_payload(**overrides):
    payload = {
        "machine_configuration_id": LONG_MACHINE,
        "calculation_purpose": "validation",
        "upstream_execution_id": "EXEC-000000000000F005",
        "casting_speed_m_s": 0.02,
        "endpoint_solid_fraction_threshold": 0.8,
        "center_solid_fraction_curve": [
            {"time_s": 0.0, "center_solid_fraction": 0.0},
            {"time_s": 5.0, "center_solid_fraction": 0.5},
            {"time_s": 10.0, "center_solid_fraction": 1.0},
        ],
    }
    payload.update(overrides)
    return payload


def f005_chain_payload():
    return {
        "property_set_id": "NIST_SRM1155A_316L_2019_V1",
        "calculation_purpose": "validation",
        "half_thickness_m": 0.005,
        "initial_temperature_k": 1750.0,
        "duration_s": 10.0,
        "casting_speed_m_s": 0.02,
        "grid_cells": 30,
        "time_step_s": 0.05,
        "shell_solid_fraction_threshold": 0.9,
        "boundary_mode": "constant_surface_temperature",
        "surface_temperature_k": 1500.0,
        "boundary_source": "published_reference_validation_boundary",
        "picard_tolerance_k": 1e-6,
        "max_picard_iterations": 60,
        "output_points": 21,
    }


class P1W5CSolidificationEndpointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = ModelRegistry()
        cls.registry.discover()
        cls.client = TestClient(app)

    def invoke_ok(self, payload):
        result = self.registry.invoke("F006", payload)
        self.assertTrue(result.success, result.error)
        self.assertTrue(result.provenance)
        return result

    def test_strict_gate_identity_and_dynamic_counts(self):
        report = self.registry.qualification_report("F006")
        self.assertTrue(report["qualified"], report["reasons"])
        self.assertEqual(report["normal_cases_passed"], 3)
        self.assertGreaterEqual(report["boundary_or_failure_cases_passed"], 3)
        eligibility = self.registry.eligibility_report("F006")
        self.assertTrue(eligibility["implementation_qualified"])
        self.assertTrue(eligibility["data_required"])
        self.assertTrue(eligibility["data_qualified"])
        self.assertTrue(eligibility["interface_qualified"])
        self.assertTrue(eligibility["scientific_validation_qualified"])
        self.assertTrue(eligibility["fully_eligible"])
        self.assertEqual(self.registry.get_counts(), {
            "registered_count": 45,
            "runtime_tool_count": 45,
            "catalog_coverage_count": 41,
            "qualified_executable_count": 45,
            "implementation_qualified_count": 45,
            "data_required_count": 21,
            "data_qualified_count": 21,
            "interface_qualified_count": 45,
            "fully_eligible_count": 45,
        })
        model = self.registry.get("F006")
        self.assertEqual(model.catalog_id, "F006")
        self.assertEqual(
            model.tool_uid,
            "metallurgy.catalog.f006.solidification_end_prediction.v1",
        )

    def test_schema_sources_domains_and_relationships_are_explicit(self):
        card = next(
            item for item in self.registry.list_models(fully_eligible_only=True)
            if item["model_code"] == "F006"
        )
        self.assertEqual(card["data_requirement"], "VERSIONED_DATABASE_REFERENCE")
        self.assertEqual(card["data_access_mode"], "database_repository")
        self.assertEqual(card["required_dataset_ids"], ["DS_F006_ENDPOINT_BENCH_V1"])
        self.assertEqual(
            card["database_tables"], ["metallurgy_v2.casting_machine_configuration"]
        )
        self.assertEqual(card["dependencies"], ["F005"])
        self.assertEqual({row["target"] for row in card["relations"]}, {"F004", "F005"})
        self.assertIn("z*=v_cast*t*", card["formula_reference"])
        curve = card["input_schema"]["properties"]["center_solid_fraction_curve"]
        self.assertEqual(curve["minItems"], 2)
        self.assertEqual(curve["maxItems"], 2001)
        self.assertFalse(curve["items"]["additionalProperties"])

    def test_database_benchmarks_match_independent_expected_results(self):
        for case in endpoint_benchmark_cases():
            with self.subTest(case=case["benchmark_id"]):
                payload = {
                    **case["input_json"],
                    "machine_configuration_id": case["machine_configuration_id"],
                    "calculation_purpose": "validation",
                    "upstream_execution_id": "EXEC-000000000000F005",
                }
                output = self.invoke_ok(payload).result
                expected, tolerance = case["expected_json"], case["tolerance_json"]
                self.assertAlmostEqual(
                    output["solidification_end_time_s"],
                    float(expected["solidification_end_time_s"]),
                    delta=float(tolerance["time_s"]),
                )
                self.assertAlmostEqual(
                    output["solidification_end_position_m"],
                    float(expected["solidification_end_position_m"]),
                    delta=float(tolerance["position_m"]),
                )
                self.assertAlmostEqual(
                    output["exit_center_solid_fraction"],
                    float(expected["exit_center_solid_fraction"]),
                    delta=float(tolerance["solid_fraction"]),
                )
                self.assertEqual(output["equipment_status"], expected["equipment_status"])
                self.assertAlmostEqual(
                    output["solidification_end_position_m"],
                    output["solidification_end_time_s"] * payload["casting_speed_m_s"],
                    places=14,
                )

    def test_threshold_monotonicity_and_curve_refinement_invariance(self):
        low = self.invoke_ok(endpoint_payload(endpoint_solid_fraction_threshold=0.7)).result
        high = self.invoke_ok(endpoint_payload(endpoint_solid_fraction_threshold=0.9)).result
        self.assertLessEqual(
            low["solidification_end_time_s"], high["solidification_end_time_s"]
        )
        refined = self.invoke_ok(endpoint_payload(
            endpoint_solid_fraction_threshold=0.8,
            center_solid_fraction_curve=[
                {"time_s": 0.0, "center_solid_fraction": 0.0},
                {"time_s": 2.5, "center_solid_fraction": 0.25},
                {"time_s": 5.0, "center_solid_fraction": 0.5},
                {"time_s": 7.5, "center_solid_fraction": 0.75},
                {"time_s": 10.0, "center_solid_fraction": 1.0},
            ],
        )).result
        base = self.invoke_ok(endpoint_payload()).result
        self.assertAlmostEqual(
            refined["solidification_end_time_s"], base["solidification_end_time_s"],
            places=14,
        )
        self.assertAlmostEqual(
            refined["solidification_end_position_m"],
            base["solidification_end_position_m"],
            places=14,
        )

    def test_exact_point_boundary_and_explicit_failures(self):
        exact = self.invoke_ok(
            endpoint_payload(endpoint_solid_fraction_threshold=0.5)
        )
        self.assertFalse(exact.boundary_check.passed)
        self.assertEqual(exact.result["time_resolution_s"], 0.0)
        self.assertEqual(exact.result["position_resolution_m"], 0.0)

        failures = [
            (
                endpoint_payload(
                    endpoint_solid_fraction_threshold=0.95,
                    center_solid_fraction_curve=[
                        {"time_s": 0.0, "center_solid_fraction": 0.0},
                        {"time_s": 10.0, "center_solid_fraction": 0.8},
                    ],
                ),
                "MODEL_NOT_APPLICABLE",
            ),
            (
                endpoint_payload(center_solid_fraction_curve=[
                    {"time_s": 0.0, "center_solid_fraction": 0.0},
                    {"time_s": 5.0, "center_solid_fraction": 0.9},
                    {"time_s": 10.0, "center_solid_fraction": 0.8},
                ]),
                "INVALID_INPUT",
            ),
            (endpoint_payload(casting_speed_m_s=0.1), "OUT_OF_DOMAIN"),
            (endpoint_payload(upstream_execution_id=""), "INVALID_INPUT"),
            (endpoint_payload(calculation_purpose="engineering"), "MODEL_NOT_APPLICABLE"),
            (
                endpoint_payload(center_solid_fraction_curve=[
                    {"time_s": 0.0, "center_solid_fraction": 0.0},
                    {"time_s": 5.0, "center_solid_fraction": 1.0},
                ]),
                "MISSING_DATA",
            ),
        ]
        for payload, error_code in failures:
            with self.subTest(error_code=error_code):
                result = self.registry.invoke("F006", payload)
                self.assertFalse(result.success)
                self.assertEqual(result.error_code, error_code)

    def test_real_f005_to_f006_http_chain_preserves_ids_and_provenance(self):
        upstream = self.client.post(
            "/api/v1/tools/metallurgy_solve_1d_shell_growth/call",
            json={"arguments": f005_chain_payload()},
        )
        self.assertEqual(upstream.status_code, 200, upstream.text)
        upstream_body = upstream.json()
        self.assertEqual(upstream_body["status"], "success")
        history = upstream_body["output"]["time_history"]
        curve = [
            {
                "time_s": row["time_s"],
                "center_solid_fraction": row["center_solid_fraction"],
            }
            for row in history
        ]
        self.assertEqual(curve[0]["center_solid_fraction"], 0.0)
        self.assertEqual(curve[-1]["center_solid_fraction"], 1.0)

        downstream_payload = endpoint_payload(
            upstream_execution_id=upstream_body["execution_id"],
            endpoint_solid_fraction_threshold=0.9,
            center_solid_fraction_curve=curve,
        )
        downstream = self.client.post(
            "/api/v1/tools/metallurgy_predict_solidification_end/call",
            json={"arguments": downstream_payload},
        )
        self.assertEqual(downstream.status_code, 200, downstream.text)
        body = downstream.json()
        self.assertEqual(body["status"], "success")
        self.assertEqual(body["model_code"], "F006")
        self.assertEqual(body["catalog_id"], "F006")
        self.assertEqual(
            body["tool_uid"],
            "metallurgy.catalog.f006.solidification_end_prediction.v1",
        )
        self.assertNotEqual(body["execution_id"], upstream_body["execution_id"])
        self.assertEqual(
            body["output"]["upstream_execution_id"], upstream_body["execution_id"]
        )
        self.assertEqual(body["output"]["equipment_status"], "inside_machine")
        self.assertTrue(
            any(row["dataset_id"] == "DS_NIST_SRM1155A_316L_2019"
                for row in upstream_body["actual_data_records"])
        )
        self.assertEqual(
            body["actual_data_records"][0]["dataset_id"],
            "DS_F006_ENDPOINT_BENCH_V1",
        )

    def test_manifest_and_forced_experiment_route(self):
        manifest_response = self.client.get("/api/v1/tools")
        self.assertEqual(manifest_response.status_code, 200)
        manifest = manifest_response.json()
        self.assertEqual(manifest["total"], 45)
        self.assertEqual(manifest["catalog_coverage_count"], 41)
        definition = next(
            item for item in manifest["tools"] if item["model_code"] == "F006"
        )
        self.assertEqual(
            definition["function"]["name"],
            "metallurgy_predict_solidification_end",
        )
        self.assertTrue(definition["fully_eligible"])

        forced = self.client.post("/api/v1/experiments/run", json={
            "user_query": "强制调用F006凝固终点预测，不得选择其他工具。",
            "mode": "forced",
            "model_code": "F006",
            "arguments": endpoint_payload(),
            "llm_name": "isolated-http-contract-test",
            "prompt_version": "p1-w5c-v1",
        })
        self.assertEqual(forced.status_code, 200, forced.text)
        forced_body = forced.json()
        self.assertEqual(forced_body["selected_model"], "F006")
        self.assertEqual(forced_body["execution_result"]["status"], "success")
        self.assertEqual(forced_body["execution_result"]["model_code"], "F006")


if __name__ == "__main__":
    unittest.main()
