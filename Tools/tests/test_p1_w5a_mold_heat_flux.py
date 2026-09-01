"""Focused P1-W5A admission tests for F007 mold water-side heat balance."""

from __future__ import annotations

import copy
import os
import sys
import unittest

from fastapi.testclient import TestClient


TOOLS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, TOOLS_DIR)

from models_core import ModelRegistry
from models_server import app


def single_circuit_payload(
    *,
    mass_flow=10.0,
    specific_heat=4200.0,
    inlet=293.15,
    outlet=298.15,
    area=2.0,
    steel_mass_flow=None,
):
    payload = {
        "cooling_circuits": [
            {
                "circuit_id": "whole-mold",
                "mass_flow_kg_s": mass_flow,
                "inlet_temperature_k": inlet,
                "outlet_temperature_k": outlet,
                "water_specific_heat_j_kg_k": specific_heat,
                "measurement_source": "calibrated_flowmeter_and_paired_rtd",
            }
        ],
        "effective_heat_transfer_area_m2": area,
        "area_definition": "whole_mold",
    }
    if steel_mass_flow is not None:
        payload["steel_mass_flow_kg_s"] = steel_mass_flow
    return payload


class P1W5AMoldHeatFluxTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = ModelRegistry()
        cls.registry.discover()
        cls.client = TestClient(app)

    def invoke_ok(self, payload):
        result = self.registry.invoke("F007", payload)
        self.assertTrue(result.success, result.error)
        self.assertTrue(result.provenance)
        return result

    def test_strict_gate_identity_and_dynamic_counts(self):
        report = self.registry.qualification_report("F007")
        self.assertTrue(report["qualified"], report["reasons"])
        self.assertEqual(report["normal_cases_passed"], 3)
        self.assertEqual(report["boundary_or_failure_cases_passed"], 3)
        eligibility = self.registry.eligibility_report("F007")
        self.assertTrue(eligibility["implementation_qualified"])
        self.assertFalse(eligibility["data_required"])
        self.assertTrue(eligibility["data_qualified"])
        self.assertTrue(eligibility["interface_qualified"])
        self.assertTrue(eligibility["scientific_validation_qualified"])
        self.assertTrue(eligibility["fully_eligible"])
        self.assertEqual(
            self.registry.get_counts(),
            {
                "registered_count": 86,
                "runtime_tool_count": 86,
                "catalog_coverage_count": 68,
                "qualified_executable_count": 86,
                "implementation_qualified_count": 86,
                "data_required_count": 30,
                "data_qualified_count": 30,
                "interface_qualified_count": 86,
                "fully_eligible_count": 86,
            },
        )
        model = self.registry.get("F007")
        self.assertEqual(model.catalog_id, "F007")
        self.assertEqual(model.tool_uid, "metallurgy.catalog.f007.mold_heat_flux.v1")
        self.assertEqual(model.tool_name, "metallurgy_calc_mold_heat_flux")

    def test_schema_units_formula_source_and_relationships_are_explicit(self):
        card = next(
            item for item in self.registry.list_models(fully_eligible_only=True)
            if item["model_code"] == "F007"
        )
        self.assertEqual(card["data_requirement"], "FORMULA_ONLY")
        self.assertEqual(card["data_access_mode"], "none")
        self.assertEqual(card["database_tables"], [])
        self.assertIn("Qdot_i", card["formula_reference"])
        self.assertTrue(card["source_records"])
        self.assertTrue(card["failure_modes"])
        self.assertGreaterEqual(len(card["independent_validation"]), 5)
        self.assertEqual({item["target"] for item in card["relations"]}, {"T001", "T002"})

        circuit_schema = card["input_schema"]["properties"]["cooling_circuits"]
        self.assertEqual(circuit_schema["type"], "array")
        self.assertEqual(circuit_schema["minItems"], 1)
        self.assertEqual(circuit_schema["maxItems"], 100)
        self.assertFalse(circuit_schema["items"]["additionalProperties"])
        self.assertEqual(
            set(circuit_schema["items"]["required"]),
            {
                "circuit_id",
                "mass_flow_kg_s",
                "inlet_temperature_k",
                "outlet_temperature_k",
                "water_specific_heat_j_kg_k",
                "measurement_source",
            },
        )
        self.assertEqual(card["input_units"]["effective_heat_transfer_area_m2"], "m^2")
        output_properties = card["output_schema"]["properties"]
        self.assertEqual(output_properties["steel_mass_flow_kg_s"]["type"], ["number", "null"])
        self.assertEqual(output_properties["heat_removed_j_kg_steel"]["type"], ["number", "null"])

    def test_three_normal_cases_match_independent_hand_calculations(self):
        single = self.invoke_ok(single_circuit_payload(steel_mass_flow=2.0)).result
        self.assertAlmostEqual(single["total_heat_rate_w"], 10 * 4200 * 5)
        self.assertAlmostEqual(single["mean_heat_flux_w_m2"], 105000.0)
        self.assertAlmostEqual(single["heat_removed_j_kg_steel"], 105000.0)
        self.assertEqual(single["steel_mass_flow_kg_s"], 2.0)

        multi = self.invoke_ok({
            "cooling_circuits": [
                {
                    "circuit_id": "wide-face",
                    "mass_flow_kg_s": 10,
                    "inlet_temperature_k": 293.15,
                    "outlet_temperature_k": 298.15,
                    "water_specific_heat_j_kg_k": 4200,
                    "measurement_source": "wide_face_instrumentation",
                },
                {
                    "circuit_id": "narrow-face",
                    "mass_flow_kg_s": 5,
                    "inlet_temperature_k": 294.15,
                    "outlet_temperature_k": 298.15,
                    "water_specific_heat_j_kg_k": 4200,
                    "measurement_source": "narrow_face_instrumentation",
                },
            ],
            "effective_heat_transfer_area_m2": 3,
            "area_definition": "whole_mold",
        }).result
        self.assertAlmostEqual(multi["total_heat_rate_w"], 210000 + 84000)
        self.assertAlmostEqual(multi["mean_heat_flux_w_m2"], 98000.0)
        self.assertAlmostEqual(
            sum(item["contribution_fraction"] for item in multi["circuit_results"]),
            1.0,
        )

        alternate_cp = self.invoke_ok(single_circuit_payload(
            mass_flow=12.5,
            specific_heat=4180,
            inlet=296.15,
            outlet=302.15,
            area=1.5,
        )).result
        self.assertAlmostEqual(alternate_cp["total_heat_rate_w"], 313500.0)
        self.assertAlmostEqual(alternate_cp["mean_heat_flux_w_m2"], 209000.0)
        self.assertIsNone(alternate_cp["steel_mass_flow_kg_s"])
        self.assertIsNone(alternate_cp["heat_removed_j_kg_steel"])

    def test_zero_rise_boundary_and_explicit_failures(self):
        zero = self.invoke_ok(single_circuit_payload(outlet=293.15))
        self.assertEqual(zero.result["total_heat_rate_w"], 0.0)
        self.assertEqual(zero.result["mean_heat_flux_w_m2"], 0.0)
        self.assertFalse(zero.boundary_check.passed)
        self.assertTrue(zero.boundary_check.warnings)

        reverse = self.registry.invoke(
            "F007",
            single_circuit_payload(inlet=300.15, outlet=299.15),
        )
        self.assertFalse(reverse.success)
        self.assertEqual(reverse.error_code, "OUT_OF_DOMAIN")

        invalid_area = self.registry.invoke("F007", single_circuit_payload(area=0))
        self.assertFalse(invalid_area.success)
        self.assertEqual(invalid_area.error_code, "OUT_OF_DOMAIN")

        missing_source_payload = single_circuit_payload()
        missing_source_payload["cooling_circuits"][0].pop("measurement_source")
        missing_source = self.registry.invoke("F007", missing_source_payload)
        self.assertFalse(missing_source.success)
        self.assertEqual(missing_source.error_code, "INVALID_INPUT")

        duplicate_payload = single_circuit_payload()
        duplicate_payload["cooling_circuits"].append(
            copy.deepcopy(duplicate_payload["cooling_circuits"][0])
        )
        duplicate = self.registry.invoke("F007", duplicate_payload)
        self.assertFalse(duplicate.success)
        self.assertEqual(duplicate.error_code, "INVALID_INPUT")

        critical_temperature = self.registry.invoke(
            "F007",
            single_circuit_payload(inlet=640.0, outlet=647.096),
        )
        self.assertFalse(critical_temperature.success)
        self.assertEqual(critical_temperature.error_code, "OUT_OF_DOMAIN")

    def test_linearity_additivity_area_scaling_and_energy_closure(self):
        base = self.invoke_ok(single_circuit_payload()).result
        doubled_flow = self.invoke_ok(single_circuit_payload(mass_flow=20)).result
        doubled_cp = self.invoke_ok(single_circuit_payload(specific_heat=8400)).result
        doubled_rise = self.invoke_ok(single_circuit_payload(outlet=303.15)).result
        doubled_area = self.invoke_ok(single_circuit_payload(area=4)).result
        self.assertAlmostEqual(doubled_flow["total_heat_rate_w"], 2 * base["total_heat_rate_w"])
        self.assertAlmostEqual(doubled_cp["total_heat_rate_w"], 2 * base["total_heat_rate_w"])
        self.assertAlmostEqual(doubled_rise["total_heat_rate_w"], 2 * base["total_heat_rate_w"])
        self.assertAlmostEqual(doubled_area["mean_heat_flux_w_m2"], base["mean_heat_flux_w_m2"] / 2)

        split_payload = single_circuit_payload()
        split_payload["cooling_circuits"] = [
            {
                **copy.deepcopy(split_payload["cooling_circuits"][0]),
                "circuit_id": circuit_id,
                "mass_flow_kg_s": 5,
            }
            for circuit_id in ("half-a", "half-b")
        ]
        split = self.invoke_ok(split_payload).result
        self.assertAlmostEqual(split["total_heat_rate_w"], base["total_heat_rate_w"])
        self.assertAlmostEqual(split["energy_sum_residual_w"], 0.0)
        self.assertAlmostEqual(
            split["mean_heat_flux_w_m2"],
            split["total_heat_rate_w"] / split["effective_heat_transfer_area_m2"],
        )

    def test_uniform_http_and_llm_function_route(self):
        manifest_response = self.client.get("/api/v1/tools")
        self.assertEqual(manifest_response.status_code, 200)
        manifest = manifest_response.json()
        self.assertEqual(manifest["total"], 86)
        definition = next(item for item in manifest["tools"] if item["model_code"] == "F007")
        self.assertEqual(definition["function"]["name"], "metallurgy_calc_mold_heat_flux")
        self.assertEqual(definition["catalog_id"], "F007")
        self.assertTrue(definition["fully_eligible"])
        nested = definition["function"]["parameters"]["properties"]["cooling_circuits"]
        self.assertEqual(nested["items"]["properties"]["mass_flow_kg_s"]["exclusiveMinimum"], 0)

        response = self.client.post(
            "/api/v1/tools/metallurgy_calc_mold_heat_flux/call",
            json={
                "arguments": single_circuit_payload(steel_mass_flow=2.0),
                "options": {"validate_boundary": True, "return_provenance": True},
            },
        )
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body["status"], "success")
        self.assertEqual(body["model_code"], "F007")
        self.assertEqual(body["catalog_id"], "F007")
        self.assertEqual(body["tool_uid"], "metallurgy.catalog.f007.mold_heat_flux.v1")
        self.assertTrue(body["execution_id"].startswith("EXEC-"))
        self.assertAlmostEqual(body["output"]["total_heat_rate_w"], 210000.0)
        self.assertEqual(body["actual_data_records"][0]["dataset_id"], "ISIJINT-2023-051")


if __name__ == "__main__":
    unittest.main()
