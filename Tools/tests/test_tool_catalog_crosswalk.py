"""Contract tests for preserving 80 runtime assets while using the workbook as catalog."""

from __future__ import annotations

import os
import sys
import unittest


TOOLS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, TOOLS_DIR)

from models_core import ModelRegistry
from models_core.catalog import load_catalog_crosswalk


class ToolCatalogCrosswalkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.crosswalk = load_catalog_crosswalk()
        cls.registry = ModelRegistry()
        cls.registry.discover()

    def test_all_current_runtime_assets_are_preserved_once(self):
        mapped = [entry["runtime_model_code"] for entry in self.crosswalk["entries"]]
        registered = [entry["model_code"] for entry in self.registry.list_models()]
        self.assertEqual(len(mapped), 97)
        self.assertEqual(len(mapped), len(set(mapped)))
        self.assertEqual(set(mapped), set(registered))

    def test_mapping_summary_is_computed_not_assumed(self):
        entries = self.crosswalk["entries"]
        status_counts = {}
        for entry in entries:
            status = entry["mapping_status"]
            status_counts[status] = status_counts.get(status, 0) + 1

        summary = self.crosswalk["summary"]
        self.assertEqual(status_counts["same"], summary["same"])
        self.assertEqual(
            status_counts["catalog_equivalent_different_runtime_code"],
            summary["catalog_equivalent_different_runtime_code"],
        )
        self.assertEqual(status_counts["scope_variant"], summary["scope_variant"])
        self.assertEqual(status_counts["extension"], summary["extension"])

        covered = [entry["catalog_id"] for entry in entries if entry["catalog_coverage"]]
        self.assertEqual(len(covered), summary["catalog_entries_covered"])
        self.assertEqual(len(covered), len(set(covered)))
        self.assertNotIn(None, covered)

    def test_aliases_and_variants_do_not_inflate_tool_count(self):
        for entry in self.crosswalk["entries"]:
            if entry["mapping_status"] in {"extension", "scope_variant"}:
                self.assertFalse(entry["catalog_coverage"])
            for alias in entry.get("legacy_model_codes", []):
                self.assertEqual(alias, entry["runtime_model_code"])

        policy = self.crosswalk["counting_policy"]
        self.assertFalse(policy["compatibility_aliases_count"])
        self.assertFalse(policy["scope_variants_cover_catalog_entry"])

    def test_registry_exposes_dual_identity_and_dual_counts(self):
        counts = self.registry.get_counts()
        self.assertEqual(counts["runtime_tool_count"], 97)
        self.assertEqual(counts["catalog_coverage_count"], 79)

        oxygen = self.registry.get("A007")
        self.assertEqual(oxygen.catalog_id, "A006")
        self.assertEqual(
            oxygen.tool_uid,
            "metallurgy.catalog.a006.oxygen_reductant_equivalent.v1",
        )
        self.assertEqual(
            self.registry.get_by_catalog_id("A006", fully_eligible_only=False).model_id,
            "A007",
        )
        self.assertEqual(
            self.registry.get_by_tool_uid(
                oxygen.tool_uid, fully_eligible_only=False
            ).model_id,
            "A007",
        )

        variant = self.registry.get("C003")
        self.assertIsNone(variant.catalog_id)
        self.assertFalse(variant.catalog_coverage)
        numerical = self.registry.get_by_catalog_id("C003", fully_eligible_only=False)
        self.assertEqual(numerical.model_id, "C103")
        self.assertEqual(numerical.tool_uid, "metallurgy.catalog.c003.fick_1d_numerical.v1")

        charge = self.registry.get_by_catalog_id("A007", fully_eligible_only=False)
        self.assertEqual(charge.model_id, "A101")
        self.assertEqual(charge.tool_name, "metallurgy_check_charge_valence_balance")
        bof_balance = self.registry.get_by_catalog_id("D001", fully_eligible_only=False)
        self.assertEqual(bof_balance.model_id, "D021")
        self.assertEqual(bof_balance.tool_name, "metallurgy_balance_bof_charge")
        self.assertEqual(
            self.registry.get_by_catalog_id("E003", fully_eligible_only=False).model_id,
            "E003",
        )
        self.assertEqual(
            self.registry.get_by_catalog_id("F003", fully_eligible_only=False).model_id,
            "F003",
        )
        self.assertEqual(
            self.registry.get_by_catalog_id("F004", fully_eligible_only=False).model_id,
            "F004",
        )
        mold_heat_flux = self.registry.get_by_catalog_id(
            "F007", fully_eligible_only=False
        )
        self.assertEqual(mold_heat_flux.model_id, "F007")
        self.assertEqual(
            mold_heat_flux.tool_uid,
            "metallurgy.catalog.f007.mold_heat_flux.v1",
        )
        endpoint = self.registry.get_by_catalog_id("F006", fully_eligible_only=False)
        self.assertEqual(endpoint.model_id, "F006")
        self.assertEqual(
            endpoint.tool_uid,
            "metallurgy.catalog.f006.solidification_end_prediction.v1",
        )
        self.assertEqual(
            self.registry.get_by_catalog_id("B012", fully_eligible_only=False).model_id,
            "B012",
        )
        self.assertEqual(
            self.registry.get_by_catalog_id("B013", fully_eligible_only=False).model_id,
            "B013",
        )
        self.assertEqual(
            self.registry.get_by_catalog_id("B016", fully_eligible_only=False).model_id,
            "B016",
        )
        self.assertEqual(
            self.registry.get_by_catalog_id("B017", fully_eligible_only=False).model_id,
            "B017",
        )

    def test_llm_definition_contains_catalog_identity(self):
        definition = self.registry.get("A001").get_tool_definition(
            self.registry.eligibility_report("A001")
        )
        self.assertEqual(definition["tool_uid"], "metallurgy.catalog.a001.v1")
        self.assertEqual(definition["catalog_id"], "A001")
        self.assertEqual(definition["model_code"], "A001")
        self.assertEqual(definition["legacy_model_codes"], [])


if __name__ == "__main__":
    unittest.main()
