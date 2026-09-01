"""R0 contracts: data eligibility and LLM function-tool exposure."""

import os
import sys
import unittest


TOOLS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, TOOLS_DIR)

from models_core import ModelRegistry
from fastapi import HTTPException
from fastapi.testclient import TestClient
from models_server import ToolCallRequest, app, call_llm_tool, list_llm_tools


FORMULA_ONLY_IDS = {
    "A001", "A002", "A004", "A005", "A006",
    "A008", "A101",
    "B010", "B014", "B015", "B016", "B017", "B018", "B019",
    "C001", "C002", "C003", "C004", "C005", "C006", "C007", "C103", "T001", "T002",
    "D004", "D006", "D015", "D016", "D021",
    "E001", "E002", "E005", "E011",
    "F003", "F007",
    "G001", "G002",
    "C009", "C010", "E006", "E007", "E009", "E012", "E014",
    "A011", "C011", "T003", "T004", "D023", "E021",
    "B026", "B027", "C012", "D022", "H002", "H003",
    "A009", "A010", "B020", "B022", "B025",
    "D018", "D019", "D020",
}
DATA_REQUIRED_IDS = {
    "A003", "A007",
    "B001", "B002", "B003", "B004", "B005", "B006", "B007", "B008", "B009", "B011", "B012", "B013",
    "D001", "D002", "D005", "D007", "D010", "D011", "D012", "D013", "D014", "E003", "E004",
    "F001", "F002", "F004", "F005", "F006",
    "B023", "B024", "C008",
}


class R0DataEligibilityAndLlmToolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = ModelRegistry()
        cls.registry.discover()

    def test_four_dimensional_counts_are_dynamic(self):
        counts = self.registry.get_counts()
        self.assertEqual(counts["registered_count"], 97)
        self.assertEqual(counts["implementation_qualified_count"], 97)
        self.assertEqual(counts["qualified_executable_count"], 97)
        self.assertEqual(counts["data_required_count"], 33)
        self.assertEqual(counts["data_qualified_count"], 33)
        self.assertEqual(counts["interface_qualified_count"], 97)
        self.assertEqual(counts["fully_eligible_count"], 97)

    def test_data_required_tools_are_database_qualified(self):
        for model_code in sorted(DATA_REQUIRED_IDS):
            with self.subTest(model_code=model_code):
                report = self.registry.eligibility_report(model_code)
                self.assertTrue(report["implementation_qualified"])
                self.assertTrue(report["data_required"])
                self.assertTrue(report["data_qualified"], report["data_reasons"])
                self.assertTrue(report["fully_eligible"])
                self.assertEqual(report["data_reasons"], [])

    def test_formula_only_tools_are_fully_eligible(self):
        eligible = {
            card["model_code"]
            for card in self.registry.list_models(fully_eligible_only=True)
        }
        self.assertEqual(eligible, FORMULA_ONLY_IDS | DATA_REQUIRED_IDS)
        for model_code in sorted(FORMULA_ONLY_IDS):
            with self.subTest(model_code=model_code):
                report = self.registry.eligibility_report(model_code)
                self.assertFalse(report["data_required"])
                self.assertTrue(report["data_qualified"])
                self.assertTrue(report["interface_qualified"])
                self.assertTrue(report["scientific_validation_qualified"])
                self.assertTrue(report["fully_eligible"])

    def test_registry_cards_expose_data_contract_and_dynamic_count_flag(self):
        formula_card = next(x for x in self.registry.list_models() if x["model_code"] == "T001")
        data_card = next(x for x in self.registry.list_models() if x["model_code"] == "B002")
        for card in (formula_card, data_card):
            self.assertIn("data_requirement", card)
            self.assertIn("data_access_mode", card)
            self.assertIn("required_dataset_ids", card)
            self.assertIn("database_tables", card)
            self.assertIn("eligibility", card)
        self.assertTrue(formula_card["count_eligible"])
        self.assertTrue(data_card["count_eligible"])
        self.assertEqual(data_card["data_requirement"], "REFERENCE_DATA_REQUIRED")
        self.assertEqual(data_card["data_access_mode"], "database_repository")
        self.assertIn("metallurgy_v2.thermodynamic_correlation", data_card["database_tables"])

    def test_llm_function_definitions_are_schema_driven_and_stable(self):
        tools = self.registry.list_tool_definitions(fully_eligible_only=True)
        self.assertEqual(len(tools), 97)
        names = set()
        for tool in tools:
            function = tool["function"]
            names.add(function["name"])
            self.assertEqual(tool["type"], "function")
            self.assertTrue(function["name"].startswith("metallurgy_"))
            self.assertTrue(function["description"])
            self.assertEqual(function["parameters"]["type"], "object")
            self.assertFalse(function["parameters"]["additionalProperties"])
            self.assertTrue(tool["fully_eligible"])
        self.assertEqual(len(names), 97)
        t001 = next(x for x in tools if x["model_code"] == "T001")
        self.assertEqual(t001["function"]["name"], "metallurgy_t001")
        self.assertIn("thermal_conductivity", t001["function"]["parameters"]["required"])

    def test_tool_name_resolves_only_eligible_tools_by_default(self):
        self.assertEqual(self.registry.get_by_tool_name("metallurgy_t001").model_id, "T001")
        self.assertEqual(self.registry.get_by_tool_name("metallurgy_b002").model_id, "B002")

    def test_http_contract_lists_and_calls_only_fully_eligible_tools(self):
        manifest = list_llm_tools()
        self.assertEqual(manifest["total"], 97)
        self.assertEqual(manifest["fully_eligible_count"], 97)
        execution = call_llm_tool("metallurgy_t001", ToolCallRequest(arguments={
            "thermal_conductivity": 20,
            "thickness": 0.1,
            "area": 2,
            "hot_temperature": 1000,
            "cold_temperature": 500,
        }))
        self.assertEqual(execution["status"], "success")
        self.assertEqual(execution["model_code"], "T001")
        self.assertEqual(execution["output"]["heat_rate_w"], 200000)
        thermo = call_llm_tool("metallurgy_b002", ToolCallRequest(arguments={
            "species": "O2(g)", "temperature": 1000,
        }))
        self.assertEqual(thermo["status"], "success")
        self.assertEqual(thermo["model_code"], "B002")

    def test_all_eligible_tools_execute_through_real_http_routes(self):
        client = TestClient(app)
        response = client.get("/api/v1/tools")
        self.assertEqual(response.status_code, 200)
        manifest = response.json()
        self.assertEqual(manifest["total"], 97)
        for definition in manifest["tools"]:
            model_code = definition["model_code"]
            model = self.registry.get(model_code)
            normal_case = next(case for case in model.qualification_cases if case["kind"] == "normal")
            with self.subTest(model_code=model_code):
                execution = client.post(
                    f"/api/v1/tools/{definition['function']['name']}/call",
                    json={"arguments": normal_case["input"]},
                )
                self.assertEqual(execution.status_code, 200, execution.text)
                body = execution.json()
                self.assertEqual(body["status"], "success")
                self.assertEqual(body["model_code"], model_code)


if __name__ == "__main__":
    unittest.main()
