"""Metallurgy Platform v2.0 Baseline 自动回归测试。"""

import copy
import json
import math
import os
import sys
import unittest


TOOLS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, TOOLS_DIR)

from models_core import ModelRegistry
from models_core.errors import STANDARD_ERROR_CODES
from models_core.services import ExperimentService, InMemoryTraceStore, ModelExecutionService


def value_at_path(payload, path):
    value = payload
    for part in path.split("."):
        value = value[part]
    return value


class BaselineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = ModelRegistry()
        cls.registry.discover()
        benchmark_path = os.path.join(TOOLS_DIR, "benchmarks", "golden_cases.json")
        with open(benchmark_path, encoding="utf-8") as handle:
            cls.benchmark = json.load(handle)

    def test_approved_thirty_assets_plus_p0_w1_are_registered(self):
        self.assertEqual(self.registry.get_counts(), {
            "registered_count": 34,
            "runtime_tool_count": 34,
            "catalog_coverage_count": 30,
            "qualified_executable_count": 34,
            "implementation_qualified_count": 34,
            "data_required_count": 14,
            "data_qualified_count": 14,
            "interface_qualified_count": 34,
            "fully_eligible_count": 34,
        })

    def test_every_model_has_complete_protocol_card(self):
        required = {
            "model_code", "model_name", "category", "description",
            "input_schema", "output_schema", "input_units", "output_units",
            "applicable_conditions", "temperature_range", "pressure_range",
            "required_data", "data_source", "formula_reference", "dependencies",
            "version", "status", "error_codes",
        }
        for card in self.registry.list_models():
            with self.subTest(model=card["model_code"]):
                self.assertFalse(required - card.keys())
                self.assertTrue(set(card["error_codes"]) <= set(STANDARD_ERROR_CODES))

    def test_seventeen_nominal_golden_cases(self):
        covered = set()
        for case in self.benchmark["cases"]:
            with self.subTest(case=case["case_id"]):
                covered.add(case["model_code"])
                result = self.registry.invoke(case["model_code"], case["input"])
                self.assertTrue(result.success, result.error)
                actual = value_at_path(result.result, case["expected"]["path"])
                expected = case["expected"]["value"]
                tolerance = case.get("tolerance", {})
                self.assertTrue(math.isclose(
                    actual,
                    expected,
                    abs_tol=tolerance.get("abs", 0.0),
                    rel_tol=tolerance.get("rel", 0.0),
                ), f"{actual} != {expected}")
        self.assertEqual(covered, {case["model_code"] for case in self.benchmark["cases"]})

    def test_generated_input_robustness_matrix_exceeds_one_hundred_cases(self):
        seeds = {case["model_code"]: case["input"] for case in self.benchmark["cases"]}
        checked = 0
        for model_code in seeds:
            model = self.registry.get(model_code)
            for field in (f for f in model.input_fields if f.required):
                invalid_values = [None, "", {}, []]
                for invalid in invalid_values:
                    params = copy.deepcopy(seeds[model_code])
                    params[field.name] = invalid
                    validation = self.registry.validate(model_code, params)
                    self.assertFalse(validation["valid"], (model_code, field.name, invalid))
                    checked += 1

                params = copy.deepcopy(seeds[model_code])
                params.pop(field.name, None)
                validation = self.registry.validate(model_code, params)
                self.assertFalse(validation["valid"], (model_code, field.name, "missing"))
                checked += 1
        self.assertGreaterEqual(checked, 100)


class ExperimentTests(unittest.TestCase):
    def setUp(self):
        registry = ModelRegistry()
        registry.discover()
        self.store = InMemoryTraceStore()
        executor = ModelExecutionService(registry, self.store)
        self.experiments = ExperimentService(registry, executor, self.store)

    def test_direct_mode_never_calls_tool(self):
        record = self.experiments.run(
            user_query="计算 Fe2O3 的摩尔质量",
            mode="direct",
            baseline_answer="直接回答基线",
        )
        self.assertIsNone(record["selected_model"])
        self.assertIsNone(record["execution_result"])

    def test_forced_mode_calls_selected_tool_and_saves_trace(self):
        record = self.experiments.run(
            user_query="计算 Fe2O3 的摩尔质量",
            mode="forced",
            model_code="A003",
            arguments={"formula": "Fe2O3"},
        )
        self.assertEqual(record["execution_result"]["status"], "success")
        execution_id = record["execution_result"]["execution_id"]
        self.assertIsNotNone(self.store.get_execution(execution_id))

    def test_autonomous_mode_recalls_and_executes_tool(self):
        record = self.experiments.run(
            user_query="请计算 Fe2O3 的摩尔质量",
            mode="autonomous",
            arguments={"formula": "Fe2O3"},
        )
        self.assertEqual(record["selected_model"], "A003")
        self.assertEqual(record["execution_result"]["status"], "success")

    def test_autonomous_mode_skips_tool_for_concept_question(self):
        record = self.experiments.run(
            user_query="什么是摩尔质量？",
            mode="autonomous",
        )
        self.assertIsNone(record["selected_model"])


if __name__ == "__main__":
    unittest.main()
