"""Focused P0-W3 qualification tests for F003 only."""

from __future__ import annotations

import os
import sys
import unittest

from fastapi.testclient import TestClient


TOOLS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, TOOLS_DIR)

from models_core import ModelRegistry
from models_server import app


class P0W3SteelSuperheatTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = ModelRegistry()
        cls.registry.discover()

    def ok(self, payload):
        result = self.registry.invoke("F003", payload)
        self.assertTrue(result.success, result.error)
        self.assertTrue(result.provenance)
        return result

    def test_f003_strict_qualification_and_identity(self):
        report = self.registry.qualification_report("F003")
        self.assertTrue(report["qualified"], report["reasons"])
        self.assertEqual(report["normal_cases_passed"], 3)
        self.assertEqual(report["boundary_or_failure_cases_passed"], 2)
        eligibility = self.registry.eligibility_report("F003")
        self.assertTrue(eligibility["fully_eligible"])
        model = self.registry.get("F003")
        self.assertEqual(model.catalog_id, "F003")
        self.assertEqual(model.tool_uid, "metallurgy.catalog.f003.steel_superheat.v1")

    def test_temperature_difference_identity_and_unit_equivalence(self):
        kelvin = self.ok({
            "steel_temperature": 1873.15,
            "liquidus_temperature": 1823.15,
            "temperature_unit": "K",
            "liquidus_source": "reference",
        }).result
        celsius = self.ok({
            "steel_temperature": 1600,
            "liquidus_temperature": 1550,
            "temperature_unit": "degC",
            "liquidus_source": "reference",
        }).result
        self.assertAlmostEqual(kelvin["superheat_k"], 50, places=10)
        self.assertAlmostEqual(celsius["superheat_k"], 50, places=10)
        self.assertAlmostEqual(kelvin["superheat_degc"], celsius["superheat_degc"], places=10)

    def test_simultaneous_translation_invariance_and_limit_status(self):
        base = self.ok({
            "steel_temperature": 1800,
            "liquidus_temperature": 1760,
            "temperature_unit": "K",
            "liquidus_source": "reference",
            "evaluate_limits": True,
            "minimum_superheat_k": 20,
            "maximum_superheat_k": 60,
        }).result
        shifted = self.ok({
            "steel_temperature": 1900,
            "liquidus_temperature": 1860,
            "temperature_unit": "K",
            "liquidus_source": "reference",
            "evaluate_limits": True,
            "minimum_superheat_k": 20,
            "maximum_superheat_k": 60,
        }).result
        self.assertEqual(base["limit_status"], "within_range")
        self.assertAlmostEqual(base["superheat_k"], shifted["superheat_k"])

    def test_negative_superheat_is_boundary_not_silent_failure(self):
        result = self.ok({
            "steel_temperature": 1500,
            "liquidus_temperature": 1510,
            "temperature_unit": "degC",
            "liquidus_source": "reference",
        })
        self.assertAlmostEqual(result.result["superheat_k"], -10)
        self.assertFalse(result.boundary_check.passed)
        self.assertTrue(result.boundary_check.warnings)

    def test_invalid_absolute_temperature_and_incomplete_contract_fail(self):
        absolute = self.registry.invoke("F003", {
            "steel_temperature": -1,
            "liquidus_temperature": 100,
            "temperature_unit": "K",
            "liquidus_source": "reference",
        })
        self.assertFalse(absolute.success)
        self.assertEqual(absolute.error_code, "OUT_OF_DOMAIN")
        missing_limits = self.registry.invoke("F003", {
            "steel_temperature": 1800,
            "liquidus_temperature": 1750,
            "temperature_unit": "K",
            "liquidus_source": "reference",
            "evaluate_limits": True,
        })
        self.assertFalse(missing_limits.success)
        self.assertEqual(missing_limits.error_code, "MISSING_DATA")
        missing_upstream = self.registry.invoke("F003", {
            "steel_temperature": 1800,
            "liquidus_temperature": 1750,
            "temperature_unit": "K",
            "liquidus_source": "F001",
        })
        self.assertFalse(missing_upstream.success)
        self.assertEqual(missing_upstream.error_code, "MISSING_DATA")

    def test_f003_executes_through_uniform_http_route(self):
        client = TestClient(app)
        manifest = client.get("/api/v1/tools").json()
        self.assertEqual(manifest["total"], 43)
        model = self.registry.get("F003")
        response = client.post(
            f"/api/v1/tools/{model.tool_name}/call",
            json={"arguments": model.qualification_cases[0]["input"]},
        )
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body["status"], "success")
        self.assertEqual(body["model_code"], "F003")
        self.assertEqual(body["catalog_id"], "F003")
        self.assertAlmostEqual(body["output"]["superheat_k"], 50)


if __name__ == "__main__":
    unittest.main()
