"""Focused P1-W5B admission and scientific verification tests for F005."""

from __future__ import annotations

import json
import math
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[2]
TOOLS_DIR = ROOT / "Tools"
sys.path.insert(0, str(TOOLS_DIR))

from models_core import ModelRegistry
from models_server import app


ANALYTIC_SET = "F005_ANALYTIC_CONSTANT_V1"
NIST_SET = "NIST_SRM1155A_316L_2019_V1"


def analytic_payload(**overrides):
    payload = {
        "property_set_id": ANALYTIC_SET,
        "calculation_purpose": "validation",
        "half_thickness_m": 0.1,
        "initial_temperature_k": 800.0,
        "duration_s": 1.0,
        "casting_speed_m_s": 0.02,
        "grid_cells": 80,
        "time_step_s": 0.01,
        "shell_solid_fraction_threshold": 0.9,
        "boundary_mode": "constant_surface_temperature",
        "surface_temperature_k": 300.0,
        "boundary_source": "independent_analytical_verification",
        "picard_tolerance_k": 1e-8,
        "max_picard_iterations": 60,
        "output_points": 3,
    }
    payload.update(overrides)
    return {key: value for key, value in payload.items() if value is not None}


def nist_payload(**overrides):
    payload = {
        "property_set_id": NIST_SET,
        "calculation_purpose": "validation",
        "half_thickness_m": 0.05,
        "initial_temperature_k": 1750.0,
        "duration_s": 5.0,
        "casting_speed_m_s": 0.02,
        "grid_cells": 80,
        "time_step_s": 0.05,
        "shell_solid_fraction_threshold": 0.9,
        "boundary_mode": "constant_surface_temperature",
        "surface_temperature_k": 1500.0,
        "boundary_source": "published_reference_validation_boundary",
        "picard_tolerance_k": 1e-6,
        "max_picard_iterations": 60,
        "output_points": 11,
    }
    payload.update(overrides)
    return {key: value for key, value in payload.items() if value is not None}


class P1W5BShellGrowthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = ModelRegistry()
        cls.registry.discover()
        cls.client = TestClient(app)
        cls._result_cache = {}

    @classmethod
    def invoke(cls, payload):
        key = json.dumps(payload, sort_keys=True)
        if key not in cls._result_cache:
            cls._result_cache[key] = cls.registry.invoke("F005", payload)
        return cls._result_cache[key]

    def invoke_ok(self, payload):
        result = self.invoke(payload)
        self.assertTrue(result.success, result.error)
        self.assertTrue(result.provenance)
        return result

    @staticmethod
    def dirichlet_exact(x_m, time_s=1.0):
        alpha = 1e-4
        return 300.0 + 500.0 * math.erf(x_m / (2.0 * math.sqrt(alpha * time_s)))

    @staticmethod
    def neumann_exact(x_m, time_s=1.0):
        alpha, conductivity, heat_flux = 1e-4, 100.0, 100000.0
        eta = x_m / (2.0 * math.sqrt(alpha * time_s))
        return (
            800.0
            - 2.0 * heat_flux / conductivity * math.sqrt(alpha * time_s / math.pi)
            * math.exp(-eta * eta)
            + heat_flux * x_m / conductivity * math.erfc(eta)
        )

    def profile_rmse(self, output, exact):
        residuals = [
            row["temperature_k"] - exact(row["x_m"])
            for row in output["final_temperature_profile"]
        ]
        return math.sqrt(math.fsum(value * value for value in residuals) / len(residuals))

    def test_strict_gate_identity_and_dynamic_counts(self):
        report = self.registry.qualification_report("F005")
        self.assertTrue(report["qualified"], report["reasons"])
        self.assertEqual(report["normal_cases_passed"], 3)
        self.assertEqual(report["boundary_or_failure_cases_passed"], 3)
        eligibility = self.registry.eligibility_report("F005")
        self.assertTrue(eligibility["implementation_qualified"])
        self.assertTrue(eligibility["data_required"])
        self.assertTrue(eligibility["data_qualified"])
        self.assertTrue(eligibility["interface_qualified"])
        self.assertTrue(eligibility["scientific_validation_qualified"])
        self.assertTrue(eligibility["fully_eligible"])
        self.assertEqual(
            self.registry.get_counts(),
            {
                "registered_count": 97,
                "runtime_tool_count": 97,
                "catalog_coverage_count": 79,
                "qualified_executable_count": 97,
                "implementation_qualified_count": 97,
                "data_required_count": 33,
                "data_qualified_count": 33,
                "interface_qualified_count": 97,
                "fully_eligible_count": 97,
            },
        )
        model = self.registry.get("F005")
        self.assertEqual(model.catalog_id, "F005")
        self.assertEqual(model.tool_uid, "metallurgy.catalog.f005.one_dimensional_shell_growth.v1")
        self.assertEqual(model.tool_name, "metallurgy_solve_1d_shell_growth")

    def test_schema_units_sources_and_relationships_are_explicit(self):
        card = next(
            item for item in self.registry.list_models(fully_eligible_only=True)
            if item["model_code"] == "F005"
        )
        self.assertEqual(card["data_requirement"], "VERSIONED_DATABASE_REFERENCE")
        self.assertEqual(card["data_access_mode"], "database_repository")
        self.assertEqual(len(card["database_tables"]), 3)
        self.assertIn("rho(T)*dH(T)/dt", card["formula_reference"])
        self.assertEqual(
            set(card["required_dataset_ids"]),
            {"DS_NIST_SRM1155A_316L_2019", "DS_F005_ANALYTIC_BENCH_V1"},
        )
        self.assertEqual({item["target"] for item in card["relations"]}, {"F007", "T001"})
        self.assertGreaterEqual(len(card["independent_validation"]), 6)
        self.assertTrue(any(row["source_id"] == "SCIPY-LINALG-1.18.1"
                            for row in card["source_records"]))
        schema = card["input_schema"]["properties"]
        self.assertEqual(schema["grid_cells"]["type"], "integer")
        self.assertEqual(schema["half_thickness_m"]["minimum"], 0.001)
        self.assertEqual(schema["boundary_mode"]["enum"], [
            "database_profile", "constant_heat_flux", "constant_surface_temperature"
        ])
        requirements = (TOOLS_DIR / "requirements.txt").read_text(encoding="utf-8")
        self.assertIn("scipy==1.18.1", requirements)

    def test_missing_runtime_dependency_fails_closed_instead_of_hiding_models(self):
        import importlib

        original_import_module = importlib.import_module

        def fail_models_f(module_name):
            if module_name.endswith(".models_f"):
                raise ImportError("scipy unavailable for dependency-gate test")
            return original_import_module(module_name)

        with patch("models_core.registry.importlib.import_module", side_effect=fail_models_f):
            incomplete_registry = ModelRegistry()
            with self.assertRaisesRegex(
                RuntimeError,
                "models_f.*scipy unavailable for dependency-gate test",
            ):
                incomplete_registry.discover()

    def test_dirichlet_solution_matches_independent_erf_solution(self):
        output = self.invoke_ok(analytic_payload()).result
        rmse = self.profile_rmse(output, self.dirichlet_exact)
        maximum_error = max(
            abs(row["temperature_k"] - self.dirichlet_exact(row["x_m"]))
            for row in output["final_temperature_profile"]
        )
        self.assertLess(rmse, 0.5)
        self.assertLess(maximum_error, 1.1)
        self.assertEqual(output["final_surface_temperature_k"], 300.0)
        self.assertLess(output["energy_closure_relative"], 1e-9)

    def test_neumann_solution_matches_independent_constant_flux_solution(self):
        output = self.invoke_ok(analytic_payload(
            boundary_mode="constant_heat_flux",
            surface_heat_flux_w_m2=100000.0,
            surface_temperature_k=None,
        )).result
        exact_surface = self.neumann_exact(0.0)
        self.assertLess(abs(output["final_surface_temperature_k"] - exact_surface), 0.01)
        self.assertLess(self.profile_rmse(output, self.neumann_exact), 0.01)
        self.assertAlmostEqual(output["cumulative_removed_heat_j_m2"], 100000.0, places=8)
        self.assertLess(output["energy_closure_relative"], 1e-9)

    def test_nist_phase_change_grows_a_bounded_monotone_shell(self):
        result = self.invoke_ok(nist_payload())
        output = result.result
        self.assertEqual(output["shell_status"], "partial_shell")
        self.assertGreater(output["shell_thickness_m"], 0.004)
        self.assertLess(output["shell_thickness_m"], 0.005)
        history = [row["shell_thickness_m"] for row in output["time_history"]]
        self.assertTrue(all(left <= right + 1e-12 for left, right in zip(history, history[1:])))
        fractions = [row["solid_fraction"] for row in output["final_temperature_profile"]]
        self.assertTrue(all(0.0 <= value <= 1.0 for value in fractions))
        self.assertEqual(output["final_surface_temperature_k"], 1500.0)
        self.assertAlmostEqual(output["final_center_temperature_k"], 1750.0, places=6)
        self.assertLess(output["energy_closure_relative"], 1e-8)
        self.assertTrue(any(row.dataset_id == "DS_NIST_SRM1155A_316L_2019"
                            for row in result.provenance))

    def test_zero_flux_is_uniform_and_energy_conserving(self):
        output = self.invoke_ok(analytic_payload(
            duration_s=0.1,
            time_step_s=0.01,
            grid_cells=10,
            boundary_mode="database_profile",
            boundary_profile_id="F005_BENCH_ZERO_HEAT_FLUX_V1",
            surface_temperature_k=None,
            boundary_source="approved_database_benchmark",
        ))
        temperatures = [row["temperature_k"] for row in output.result["final_temperature_profile"]]
        self.assertTrue(all(abs(value - 800.0) < 1e-10 for value in temperatures))
        self.assertAlmostEqual(output.result["cumulative_removed_heat_j_m2"], 0.0, places=12)
        self.assertLess(abs(output.result["energy_closure_residual_j_m2"]), 1e-6)
        self.assertFalse(output.boundary_check.passed)

    def test_grid_and_time_refinement_converge(self):
        coarse = self.invoke_ok(analytic_payload(grid_cells=20, time_step_s=0.02)).result
        spatial = self.invoke_ok(analytic_payload(grid_cells=80, time_step_s=0.02)).result
        temporal = self.invoke_ok(analytic_payload(grid_cells=80, time_step_s=0.01)).result
        coarse_error = self.profile_rmse(coarse, self.dirichlet_exact)
        spatial_error = self.profile_rmse(spatial, self.dirichlet_exact)
        temporal_error = self.profile_rmse(temporal, self.dirichlet_exact)
        self.assertLess(spatial_error, 0.5 * coarse_error)
        self.assertLess(temporal_error, 0.7 * spatial_error)

        shell_40 = self.invoke_ok(nist_payload(grid_cells=40, time_step_s=0.05)).result
        shell_80 = self.invoke_ok(nist_payload(grid_cells=80, time_step_s=0.05)).result
        shell_dt = self.invoke_ok(nist_payload(grid_cells=80, time_step_s=0.025)).result
        self.assertLess(
            abs(shell_80["shell_thickness_m"] - shell_40["shell_thickness_m"])
            / shell_80["shell_thickness_m"],
            0.02,
        )
        self.assertLess(
            abs(shell_dt["shell_thickness_m"] - shell_80["shell_thickness_m"])
            / shell_dt["shell_thickness_m"],
            0.01,
        )

    def test_missing_out_of_domain_and_incompatible_inputs_fail_explicitly(self):
        cases = [
            (analytic_payload(property_set_id="DOES_NOT_EXIST"), "MISSING_DATA"),
            (nist_payload(calculation_purpose="engineering"), "MODEL_NOT_APPLICABLE"),
            (analytic_payload(
                boundary_mode="constant_heat_flux",
                surface_heat_flux_w_m2=100000.0,
                surface_temperature_k=None,
                boundary_source="F007",
            ), "MISSING_DATA"),
            (nist_payload(
                duration_s=0.1,
                time_step_s=0.01,
                boundary_mode="database_profile",
                boundary_profile_id="F005_BENCH_SURFACE_TEMP_300K_V1",
                surface_temperature_k=None,
            ), "MODEL_NOT_APPLICABLE"),
            (analytic_payload(initial_temperature_k=1300.0), "OUT_OF_DOMAIN"),
            (analytic_payload(duration_s=0.01, time_step_s=0.02), "INVALID_INPUT"),
        ]
        for payload, error_code in cases:
            with self.subTest(error_code=error_code):
                result = self.invoke(payload)
                self.assertFalse(result.success)
                self.assertEqual(result.error_code, error_code)

    def test_uniform_http_and_forced_experiment_routes(self):
        manifest_response = self.client.get("/api/v1/tools")
        self.assertEqual(manifest_response.status_code, 200)
        manifest = manifest_response.json()
        self.assertEqual(manifest["total"], 97)
        self.assertEqual(manifest["catalog_coverage_count"], 79)
        definition = next(item for item in manifest["tools"] if item["model_code"] == "F005")
        self.assertEqual(definition["function"]["name"], "metallurgy_solve_1d_shell_growth")
        self.assertEqual(definition["catalog_id"], "F005")
        self.assertTrue(definition["fully_eligible"])

        payload = analytic_payload(
            duration_s=0.1,
            time_step_s=0.01,
            grid_cells=20,
            boundary_mode="database_profile",
            boundary_profile_id="F005_BENCH_HEAT_FLUX_100KW_M2_V1",
            surface_temperature_k=None,
            boundary_source="approved_database_benchmark",
        )
        response = self.client.post(
            "/api/v1/tools/metallurgy_solve_1d_shell_growth/call",
            json={"arguments": payload, "options": {
                "validate_boundary": True, "return_provenance": True
            }},
        )
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body["status"], "success")
        self.assertEqual(body["model_code"], "F005")
        self.assertEqual(body["catalog_id"], "F005")
        self.assertEqual(body["tool_uid"], "metallurgy.catalog.f005.one_dimensional_shell_growth.v1")
        self.assertTrue(body["execution_id"].startswith("EXEC-"))
        self.assertAlmostEqual(body["output"]["cumulative_removed_heat_j_m2"], 10000.0)
        self.assertTrue(any(row["dataset_id"] == "DS_F005_ANALYTIC_BENCH_V1"
                            for row in body["actual_data_records"]))

        forced = self.client.post("/api/v1/experiments/run", json={
            "user_query": "使用指定的一维坯壳工具执行解析基准，不得自主改选工具。",
            "mode": "forced",
            "model_code": "F005",
            "arguments": payload,
            "llm_name": "isolated-http-contract-test",
            "prompt_version": "p1-w5b-v1",
        })
        self.assertEqual(forced.status_code, 200, forced.text)
        forced_body = forced.json()
        self.assertEqual(forced_body["selected_model"], "F005")
        self.assertEqual(forced_body["execution_result"]["status"], "success")
        self.assertEqual(forced_body["execution_result"]["model_code"], "F005")


if __name__ == "__main__":
    unittest.main()
