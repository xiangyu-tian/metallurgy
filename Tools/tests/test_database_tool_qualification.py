"""Database admission tests for the 14 data-required tools."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

import psycopg2


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "Tools"
sys.path.insert(0, str(TOOLS))

from models_core import ModelRegistry


class DatabaseToolQualificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = ModelRegistry()
        cls.registry.discover()

    @staticmethod
    def connection():
        config = {
            "database": os.getenv("METALLURGY_DB_NAME", "metallurgy"),
            "user": os.getenv("METALLURGY_DB_USER", "postgres"),
            "password": os.getenv("METALLURGY_DB_PASSWORD", ""),
        }
        if os.getenv("METALLURGY_DB_HOST"):
            config["host"] = os.environ["METALLURGY_DB_HOST"]
        if os.getenv("METALLURGY_DB_PORT"):
            config["port"] = int(os.environ["METALLURGY_DB_PORT"])
        return psycopg2.connect(**config)

    def test_additive_migration_contains_no_destructive_sql(self):
        sql = (ROOT / "database" / "migrations" / "006_tool_data_qualification.sql").read_text(encoding="utf-8").upper()
        for forbidden in ("DELETE FROM", "TRUNCATE", "DROP TABLE", "DROP SCHEMA"):
            self.assertNotIn(forbidden, sql)

    def test_imported_reference_record_counts(self):
        with self.connection() as connection, connection.cursor() as cur:
            queries = {
                "elements": "SELECT count(*) FROM metallurgy_v2.element_reference WHERE is_active",
                "nasa7": "SELECT count(*) FROM metallurgy_v2.thermodynamic_correlation WHERE equation_type='NASA7' AND is_active",
                "reaction_properties": "SELECT count(*) FROM metallurgy_v2.reaction_property",
                "process_parameters": "SELECT count(*) FROM metallurgy_v2.process_parameter_set WHERE is_active",
            }
            actual = {}
            for key, query in queries.items():
                cur.execute(query)
                actual[key] = cur.fetchone()[0]
        self.assertGreaterEqual(actual["elements"], 95)
        self.assertEqual(actual["nasa7"], 12)
        self.assertGreaterEqual(actual["reaction_properties"], 26)
        self.assertEqual(actual["process_parameters"], 8)

    def test_every_data_tool_executes_with_matching_record_provenance(self):
        for card in self.registry.list_models():
            if not card["eligibility"]["data_required"]:
                continue
            model = self.registry.get(card["model_code"])
            case = model.data_qualification_cases[0]
            with self.subTest(model_code=model.model_id):
                result = self.registry.invoke(model.model_id, case["input"])
                self.assertTrue(result.success, result.error)
                matching = [
                    record for record in result.provenance
                    if record.dataset_id in model.required_dataset_ids
                    and record.table in model.database_tables
                    and record.record_id
                ]
                self.assertTrue(matching)

    def test_repeat_import_dry_run_is_idempotent(self):
        completed = subprocess.run(
            [sys.executable, str(ROOT / "database" / "import_tool_reference_data.py")],
            cwd=ROOT, check=True, capture_output=True, text=True, encoding="utf-8",
        )
        report = json.loads(completed.stdout)
        self.assertEqual(report["mode"], "dry-run")
        self.assertEqual(report["inserted"], 0)
        self.assertEqual(report["unchanged"], 147)


if __name__ == "__main__":
    unittest.main()
