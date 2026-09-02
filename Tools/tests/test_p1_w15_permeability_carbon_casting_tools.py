"""P1-W15 admission, database, scientific-property, HTTP and forced-call tests."""

from __future__ import annotations

import hashlib
import json
import math
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "Tools"
sys.path.insert(0, str(TOOLS))

from models_core import ModelRegistry
from models_server import app


W15_IDS = {"E015", "E020", "F008", "F018"}
ASSET = TOOLS / "models_core" / "data" / "bf_emission_factors_w15_v1.json"
ASSET_SHA256 = "e242f3b1a5d44bebba2864dd8c9f18d67a7a3d7d7891135649e3d03a6badc090"


def case_payload(registry: ModelRegistry, code: str, case_id: str | None = None) -> dict:
    cases = registry.get(code).qualification_cases
    if case_id is None:
        return next(case["input"] for case in cases if case["kind"] == "normal")
    return next(case["input"] for case in cases if case["id"] == case_id)


class P1W15PermeabilityCarbonCastingTests(unittest.TestCase):
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
        for code in sorted(W15_IDS):
            with self.subTest(code=code):
                admission = self.registry.qualification_report(code)
                eligibility = self.registry.eligibility_report(code)
                self.assertTrue(admission["qualified"], admission["reasons"])
                self.assertEqual(admission["normal_cases_passed"], 3)
                self.assertGreaterEqual(admission["boundary_or_failure_cases_passed"], 2)
                self.assertTrue(eligibility["fully_eligible"], eligibility)
                self.assertEqual(eligibility["data_required"], code == "E020")
                self.assertTrue(self.registry.get(code).catalog_coverage)

    def test_e015_formula_flow_conversion_and_scaling_properties(self):
        payload = case_payload(self.registry, "E015")
        output = self.ok("E015", payload).result
        pressure_average = (payload["lower_bed_absolute_pressure_pa"] + payload["top_absolute_pressure_pa"]) / 2
        actual_flow = payload["gas_flow_normal_nm3_s"] * 1000 / 273.15 * 101325 / pressure_average
        velocity = actual_flow / payload["cross_section_area_m2"]
        expected = (150000 / 20) / (0.45 ** 0.7 * (4e-5) ** 0.3 * velocity ** 1.7)
        self.assertAlmostEqual(output["actual_gas_flow_m3_s"], actual_flow, places=12)
        self.assertAlmostEqual(output["permeability_resistance_index"], expected, places=9)
        doubled = self.ok("E015", {**payload, "gas_flow_normal_nm3_s": 100}).result
        self.assertAlmostEqual(doubled["permeability_resistance_index"] / expected, 2 ** -1.7, places=12)
        doubled_height = self.ok("E015", {
            **payload,
            "effective_bed_height_m": 40,
            "lower_bed_absolute_pressure_pa": 500000,
            "top_absolute_pressure_pa": 200000,
        }).result
        self.assertAlmostEqual(doubled_height["pressure_gradient_pa_m"], output["pressure_gradient_pa_m"], places=12)

    def test_e020_database_values_gwp_ledger_and_provenance(self):
        payload = case_payload(self.registry, "E020")
        execution = self.ok("E020", payload)
        output = execution.result
        expected_factor = 94600 + 10 * 27 + 1.5 * 273
        self.assertAlmostEqual(output["activity_results"][0]["co2e_factor_kg_per_unit"], expected_factor, places=12)
        self.assertAlmostEqual(output["gross_emissions_kg_co2e"], 10 * expected_factor, places=9)
        self.assertAlmostEqual(output["carbon_footprint_t_co2e_per_t_hm"], 0.952795, places=12)
        self.assertAlmostEqual(sum(output["scope_totals_kg_co2e"].values()), output["unallocated_net_kg_co2e"], places=9)
        self.assertAlmostEqual(output["ledger_closure_residual_kg_co2e"], 0, places=9)
        records = [item for item in execution.provenance if item.dataset_id == "DS_BF_GHG_FACTORS_W15"]
        self.assertTrue(records)
        self.assertTrue(all(item.table == "metallurgy_v2.emission_factor" and item.record_id and item.checksum for item in records))

    def test_e020_scale_allocation_units_and_no_static_fallback(self):
        payload = case_payload(self.registry, "E020")
        base = self.ok("E020", payload).result
        scaled = self.ok("E020", {
            **payload,
            "hot_metal_output_t": 5000,
            "activities": [{**payload["activities"][0], "quantity": 50}],
            "allocation_fraction": 0.4,
        }).result
        self.assertAlmostEqual(scaled["gross_emissions_kg_co2e"], base["gross_emissions_kg_co2e"] * 5, places=9)
        self.assertAlmostEqual(scaled["allocated_net_kg_co2e"], scaled["unallocated_net_kg_co2e"] * 0.4, places=9)
        self.assertAlmostEqual(scaled["carbon_footprint_t_co2e_per_t_hm"], base["carbon_footprint_t_co2e_per_t_hm"] * 0.4, places=12)
        self.assertEqual(self.registry.invoke("E020", case_payload(self.registry, "E020", "E020-F1")).error_code, "UNIT_MISMATCH")
        with patch.dict(os.environ, {"METALLURGY_DB_HOST": "127.0.0.1", "METALLURGY_DB_PORT": "1"}):
            result = self.registry.invoke("E020", payload)
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, "DATA_BACKEND_UNAVAILABLE")

    def test_e020_asset_checksum_and_fixed_record_count(self):
        self.assertEqual(hashlib.sha256(ASSET.read_bytes()).hexdigest(), ASSET_SHA256)
        asset = json.loads(ASSET.read_text(encoding="utf-8"))
        self.assertEqual(len(asset["factors"]), 16)
        self.assertEqual(len({row["factor_code"] for row in asset["factors"]}), 16)
        self.assertTrue(all(row["is_approved"] for row in asset["factors"]))

    def test_f008_mass_flow_heat_balance_and_mode_equivalence(self):
        payload = case_payload(self.registry, "F008")
        specific = self.ok("F008", payload).result
        expected_steel = 1 * 1.5 * 0.2 * 0.02 * 7400
        self.assertAlmostEqual(specific["steel_mass_flow_kg_s"], expected_steel, places=12)
        self.assertAlmostEqual(specific["total_water_mass_flow_kg_s"], expected_steel * 0.998, places=12)
        equivalent_heat = self.ok("F008", {
            "calculation_mode": "heat_balance", "strand_count": 1,
            "section_width_m": 1.5, "section_thickness_m": 0.2,
            "casting_speed_m_s": 0.02, "steel_density_kg_m3": 7400,
            "target_heat_removed_kj_kg": 41.7164,
            "water_inlet_temperature_k": 293.15, "water_outlet_temperature_k": 303.15,
        }).result
        self.assertAlmostEqual(equivalent_heat["total_water_mass_flow_kg_s"], specific["total_water_mass_flow_kg_s"], places=12)
        self.assertAlmostEqual(equivalent_heat["energy_closure_residual_kw"], 0, places=10)

    def test_f018_stokes_force_balance_distance_and_reverse_flow(self):
        payload = case_payload(self.registry, "F018")
        output = self.ok("F018", payload).result
        stokes = (7000 - 3900) * 9.80665 * (2e-5) ** 2 / (18 * 0.006)
        self.assertAlmostEqual(output["stokes_velocity_m_s"], stokes, places=15)
        self.assertLess(output["particle_reynolds_number"], 0.1)
        self.assertLess(abs(output["force_balance_relative_residual"]), 1e-7)
        farther = self.ok("F018", {**payload, "float_distance_m": 2}).result
        self.assertAlmostEqual(farther["float_time_s"], 2 * output["float_time_s"], places=8)
        reverse = self.ok("F018", case_payload(self.registry, "F018", "F018-B1"))
        self.assertFalse(reverse.boundary_check.passed)
        self.assertFalse(reverse.result["can_reach_surface"])
        self.assertIsNone(reverse.result["float_time_s"])
        self.assertEqual(reverse.result["residence_time_coverage_fraction"], 0)

    def test_schema_real_http_and_forced_route_for_each_new_tool(self):
        response = self.client.get("/api/v1/tools")
        self.assertEqual(response.status_code, 200)
        manifest = response.json()
        self.assertEqual(manifest["total"], 109)
        self.assertEqual(manifest["catalog_coverage_count"], 91)
        definitions = {item["model_code"]: item for item in manifest["tools"]}
        for code in sorted(W15_IDS):
            with self.subTest(code=code):
                payload = case_payload(self.registry, code)
                definition = definitions[code]
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
                    "llm_name": "isolated-http-contract-test", "prompt_version": "p1-w15-v1",
                })
                self.assertEqual(forced.status_code, 200, forced.text)
                self.assertEqual(forced.json()["selected_model"], code)
                self.assertEqual(forced.json()["execution_result"]["status"], "success")

    def test_provider_forced_case_manifest_has_one_case_per_tool(self):
        path = TOOLS / "benchmarks" / "llm_tool_call_cases_p1_w15.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual({case["model_code"] for case in payload["cases"]}, W15_IDS)
        self.assertEqual(len(payload["cases"]), 4)
        self.assertIn("not a research dataset", payload["purpose"])
        self.assertTrue(all(case["force_tool_choice"] and case["expected"] for case in payload["cases"]))


if __name__ == "__main__":
    unittest.main()
