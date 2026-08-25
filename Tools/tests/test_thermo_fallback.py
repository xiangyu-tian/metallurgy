"""Data-required thermodynamic tools must use PostgreSQL without fallback."""

import os
import sys
import unittest


sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models_core import ModelRegistry


class ThermodynamicFallbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = ModelRegistry()
        cls.registry.discover()

    def test_shomate_uses_database_record_provenance(self):
        result = self.registry.invoke(
            "B001", {"species": "Fe(s)", "temperature": 1000}
        )

        self.assertTrue(result.success, result.error)
        self.assertAlmostEqual(result.result["Cp"], 35.47286, places=5)
        self.assertEqual(result.result["data_source"], "database_repository")
        self.assertTrue(any(p.table == "metallurgy_v2.thermodynamic_correlation" and p.record_id for p in result.provenance))

    def test_reaction_gibbs_uses_database_record(self):
        result = self.registry.invoke(
            "B008", {"reaction": "C + O₂ → CO₂", "temperature": 1000}
        )

        self.assertTrue(result.success, result.error)
        self.assertAlmostEqual(result.result["delta_G"], -396.4, places=1)
        self.assertTrue(any(p.table == "metallurgy_v2.reaction_property" and p.record_id for p in result.provenance))

    def test_database_failure_does_not_silently_fallback(self):
        previous = os.environ.get("METALLURGY_DB_NAME")
        os.environ["METALLURGY_DB_NAME"] = "metallurgy_database_that_does_not_exist"
        try:
            result = self.registry.invoke("B001", {"species": "Fe(s)", "temperature": 1000})
        finally:
            if previous is None:
                os.environ.pop("METALLURGY_DB_NAME", None)
            else:
                os.environ["METALLURGY_DB_NAME"] = previous
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, "DATA_BACKEND_UNAVAILABLE")


if __name__ == "__main__":
    unittest.main()
