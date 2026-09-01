"""P1-W7 PostgreSQL import, lineage, and fail-closed repository tests."""
from __future__ import annotations

import hashlib
import json
import os
import sys
import unittest
from pathlib import Path

import psycopg2
import psycopg2.extras


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "Tools"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(TOOLS))

from database.import_bof_slag_model_data import ASSET_PATH, MIGRATION, import_rows, load_asset
from models_core.repositories.bof_slag_repository import approved_parameter_set
from models_core.repositories.reference_repository import RepositoryError


EXPECTED_DATASETS = {
    "DS_BOF_P_PARTITION_ISIJ_2016",
    "DS_SLAG_S_CAPACITY_ISIJ_2013",
    "DS_S_DISTRIBUTION_ISIJ_2016",
    "DS_MN_EQUILIBRIUM_ISIJ_1963",
    "DS_SI_EQUILIBRIUM_ISIJ_2017",
}
EXPECTED_PARAMETER_COUNTS = {"D010": 8, "D011": 14, "D012": 2, "D013": 2}


class P1W7BofSlagDataTests(unittest.TestCase):
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

    def test_asset_is_versioned_complete_and_excludes_restricted_ds042(self):
        payload, asset_sha = load_asset()
        self.assertEqual(asset_sha, hashlib.sha256(ASSET_PATH.read_bytes()).hexdigest())
        self.assertEqual(payload["asset_version"], "2026.09-v1")
        self.assertEqual({row["dataset_id"] for row in payload["datasets"]}, EXPECTED_DATASETS)
        self.assertEqual(len(payload["datasets"]), 5)
        self.assertEqual(len(payload["parameter_sets"]), 4)
        self.assertEqual(sum(len(row["parameters"]) for row in payload["parameter_sets"]), 26)
        serialized = json.dumps(payload, ensure_ascii=False)
        self.assertNotIn("DS042", serialized)
        for row in payload["parameter_sets"]:
            self.assertIs(row["applicability"]["plant_control_approved"], False)

    def test_migration_is_additive_only(self):
        sql = MIGRATION.read_text(encoding="utf-8").upper()
        for forbidden in ("DELETE FROM", "TRUNCATE", "DROP TABLE", "DROP SCHEMA", "ALTER TABLE", "UPDATE "):
            self.assertNotIn(forbidden, sql)
        self.assertIn("CREATE TABLE IF NOT EXISTS METALLURGY_V2.BOF_SLAG_MODEL_PARAMETER", sql)
        self.assertIn("UNIQUE (MODEL_CODE, PARAMETER_SET_ID, PARAMETER_CODE, SOURCE_VERSION)", sql)

    def test_database_rows_are_exact_approved_and_do_not_reference_ds042(self):
        with self.connection() as connection, connection.cursor() as cur:
            cur.execute(
                """SELECT model_code, count(*), bool_and(is_approved),
                          bool_and((applicability->>'plant_control_approved')::boolean = false)
                   FROM metallurgy_v2.bof_slag_model_parameter
                   GROUP BY model_code ORDER BY model_code"""
            )
            actual = {row[0]: (row[1], row[2], row[3]) for row in cur.fetchall()}
            self.assertEqual(actual, {code: (count, True, True) for code, count in EXPECTED_PARAMETER_COUNTS.items()})
            cur.execute(
                "SELECT count(*) FROM metallurgy_v2.bof_slag_model_parameter WHERE dataset_id='DS042'"
            )
            self.assertEqual(cur.fetchone()[0], 0)
            cur.execute(
                "SELECT count(*) FROM metallurgy_v2.dataset_registry WHERE dataset_id=ANY(%s)",
                (list(EXPECTED_DATASETS),),
            )
            self.assertEqual(cur.fetchone()[0], 5)
            cur.execute("SELECT count(*) FROM metallurgy_v2.dataset_registry WHERE dataset_id='DS042'")
            self.assertEqual(cur.fetchone()[0], 1)

    def test_repository_returns_exact_parameter_sets_and_record_provenance(self):
        cases = {
            "D010": ("D010_SPOONER_ISIJ_2016_V1", 1873, 8, {"DS_BOF_P_PARTITION_ISIJ_2016"}),
            "D011": ("D011_ZHANG_MA_ISIJ_V1", 1823, 14, {"DS_SLAG_S_CAPACITY_ISIJ_2013", "DS_S_DISTRIBUTION_ISIJ_2016"}),
            "D012": ("D012_GUNJI_MATOBA_LIQUID_V1", 1880, 2, {"DS_MN_EQUILIBRIUM_ISIJ_1963"}),
            "D013": ("D013_DONG_ISIJ_2017_V1", 1850, 2, {"DS_SI_EQUILIBRIUM_ISIJ_2017"}),
        }
        for code, (set_id, temperature, count, datasets) in cases.items():
            with self.subTest(code=code):
                model, provenance = approved_parameter_set(code, set_id, temperature)
                self.assertEqual(len(model["values"]), count)
                self.assertEqual(len(provenance), count)
                self.assertEqual({record.dataset_id for record in provenance}, datasets)
                self.assertTrue(all(record.table == "metallurgy_v2.bof_slag_model_parameter" for record in provenance))
                self.assertTrue(all(record.record_id for record in provenance))
                self.assertFalse(model["applicability"]["plant_control_approved"])

    def test_repository_missing_and_out_of_domain_fail_closed(self):
        with self.assertRaises(RepositoryError) as missing:
            approved_parameter_set("D010", "DOES_NOT_EXIST", 1873)
        self.assertEqual(missing.exception.error_code, "MISSING_DATA")
        with self.assertRaises(RepositoryError) as outside:
            approved_parameter_set("D012", "D012_GUNJI_MATOBA_LIQUID_V1", 1800)
        self.assertEqual(outside.exception.error_code, "OUT_OF_DOMAIN")

    def test_import_is_idempotent_and_conflict_checked_in_rolled_back_transaction(self):
        payload, asset_sha = load_asset()
        stats = {"inserted": 0, "unchanged": 0}
        connection = self.connection()
        connection.autocommit = False
        try:
            with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                import_rows(cur, payload, asset_sha, stats)
            self.assertEqual(stats, {"inserted": 0, "unchanged": 31})
        finally:
            connection.rollback()
            connection.close()

    def test_committed_import_audit_records_backup_and_safety_flags(self):
        with self.connection() as connection, connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """SELECT * FROM metallurgy_v2.dataset_import_run
                   WHERE dataset_id='P1-W7-BOF-SLAG-MODELS-2026.09-v1'
                     AND status='committed' ORDER BY completed_at DESC LIMIT 1"""
            )
            row = cur.fetchone()
        self.assertIsNotNone(row)
        details = dict(row["details"])
        self.assertTrue(details["ds042_unchanged"])
        self.assertFalse(details["restricted_ds042_imported"])
        self.assertFalse(details["plant_control_approved"])
        backup = Path(details["backup"]["path"])
        self.assertTrue(backup.is_file())
        self.assertEqual(hashlib.sha256(backup.read_bytes()).hexdigest(), details["backup"]["sha256"])
        self.assertEqual(row["inserted_count"], 31)


if __name__ == "__main__":
    unittest.main()
