"""
ModelRegistry — 模型自动发现与注册
"""
from __future__ import annotations
import importlib
import inspect
import re
from typing import Dict, Optional, List, Type

from .base import BaseModelTool, ModelResult, InvocationContext
from .catalog import apply_catalog_metadata
from .errors import normalize_error_code


class ModelRegistry:
    """统一模型注册表，自动发现 models_core 包下的所有 BaseModelTool 子类"""

    def __init__(self):
        self._models: Dict[str, BaseModelTool] = {}
        self._initialized = False

    def discover(self, package_name: str = "models_core") -> int:
        """扫描当前包及子模块，注册所有 BaseModelTool 实例"""
        discovered: Dict[str, BaseModelTool] = {}
        package_prefix = __package__ or package_name
        # 手动导入已知模块确保被发现
        for module_name in [
            f"{package_prefix}.models_a",
            f"{package_prefix}.models_b",
            f"{package_prefix}.models_c",
            f"{package_prefix}.models_t",
            f"{package_prefix}.models_d",
            f"{package_prefix}.models_e",
        ]:
            try:
                importlib.import_module(module_name)
            except ImportError:
                continue

        # 扫描所有 BaseModelTool 子类
        for cls in self._find_subclasses(BaseModelTool):
            if cls.model_id:  # 只有设置了 model_id 的才注册
                if cls.model_id in discovered and type(discovered[cls.model_id]) is not cls:
                    raise ValueError(f"重复模型 ID: {cls.model_id}")
                instance = cls()
                apply_catalog_metadata(instance)
                discovered[cls.model_id] = instance

        self._models = discovered
        self._initialized = True
        return len(self._models)

    def _find_subclasses(self, base_cls: Type) -> List[Type]:
        """递归查找所有非抽象子类"""
        results = []
        for subclass in base_cls.__subclasses__():
            # 跳过基类自身（如果没设 model_id 就是抽象的）
            results.append(subclass)
            # 递归查找子类的子类
            results.extend(self._find_subclasses(subclass))
        return results

    def register(self, model: BaseModelTool) -> None:
        """手动注册一个模型实例"""
        if not model.model_id:
            raise ValueError("模型 ID 不能为空")
        if model.model_id in self._models:
            raise ValueError(f"重复模型 ID: {model.model_id}")
        self._models[model.model_id] = model

    def get(self, model_id: str) -> Optional[BaseModelTool]:
        """根据 model_id 获取模型实例"""
        if not self._initialized:
            self.discover()
        return self._models.get(model_id)

    def qualification_report(self, model_id: str) -> dict:
        """按可执行工具准入规则审查单个注册项，并执行其准入样例。"""
        model = self.get(model_id)
        if model is None:
            return {"qualified": False, "reasons": [f"未知模型 ID: {model_id}"],
                    "normal_cases_passed": 0, "boundary_or_failure_cases_passed": 0}

        reasons = []
        if not model.count_eligible:
            reasons.append("未声明可计数")
        if model.qualification_status != "qualified":
            reasons.append("未声明通过资格审查")
        for attr, label in (
            ("formula_reference", "公式/算法依据"),
            ("source_version", "来源版本"),
            ("source_records", "来源记录"),
            ("failure_modes", "失败条件"),
            ("independent_validation", "独立验证"),
            ("relations", "重叠/依赖关系"),
        ):
            if not getattr(model, attr, None):
                reasons.append(f"缺少{label}")

        if type(model).invoke is BaseModelTool.invoke:
            reasons.append("没有独立执行实现")

        input_names = [field.name for field in model.input_fields]
        output_names = [field.name for field in model.output_fields]
        if not input_names or len(input_names) != len(set(input_names)):
            reasons.append("输入 Schema 为空或字段重名")
        if not output_names or len(output_names) != len(set(output_names)):
            reasons.append("输出 Schema 为空或字段重名")
        for field in model.input_fields + model.output_fields:
            if field.type == "number" and not field.unit:
                reasons.append(f"数值字段缺少单位: {field.name}")

        for dependency in model.dependencies:
            if dependency not in self._models:
                reasons.append(f"依赖未注册: {dependency}")
        for relation in model.relations:
            if not isinstance(relation, dict) or not relation.get("type") \
                    or not relation.get("target") or not relation.get("description"):
                reasons.append("关系记录字段不完整")
                continue
            if relation["target"] not in self._models:
                reasons.append(f"关系目标未注册: {relation['target']}")

        normal_passed = 0
        nonnormal_passed = 0
        case_ids = set()
        cases = model.qualification_cases
        for case in cases:
            case_id = case.get("id")
            kind = case.get("kind")
            if not case_id or case_id in case_ids or kind not in {"normal", "boundary", "failure"}:
                reasons.append("准入样例 ID 重复或类型无效")
                continue
            case_ids.add(case_id)
            result = self.invoke(model_id, case.get("input", {}))
            expected_success = case.get("expect_success", kind != "failure")
            passed = result.success is expected_success
            if kind == "boundary" and passed:
                passed = result.boundary_check is not None and not result.boundary_check.passed
            if kind == "failure" and passed:
                passed = result.error_code is not None
            if passed and result.success:
                actual_fields = set((result.result or {}).keys())
                if actual_fields != set(output_names):
                    passed = False
                    reasons.append(
                        f"准入样例 {case_id} 输出字段与 Schema 不一致: "
                        f"{sorted(actual_fields ^ set(output_names))}"
                    )
            if not passed:
                reasons.append(f"准入样例未通过: {case_id}")
            elif kind == "normal":
                normal_passed += 1
            else:
                nonnormal_passed += 1

        if normal_passed < 3:
            reasons.append(f"正常准入样例不足3个: {normal_passed}")
        if nonnormal_passed < 2:
            reasons.append(f"边界/失败准入样例不足2个: {nonnormal_passed}")

        return {
            "qualified": not reasons,
            "reasons": reasons,
            "normal_cases_passed": normal_passed,
            "boundary_or_failure_cases_passed": nonnormal_passed,
        }

    def _interface_qualification(self, model: BaseModelTool) -> tuple[bool, List[str]]:
        """验证模型能否转换成稳定、唯一的大模型function-tool契约。"""
        reasons = []
        definition = model.get_tool_definition()
        function = definition.get("function", {})
        name = function.get("name", "")
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,63}", name):
            reasons.append("INVALID_TOOL_NAME")
        duplicates = [m.model_id for m in self._models.values() if m.tool_name == name]
        if len(duplicates) != 1:
            reasons.append("DUPLICATE_TOOL_NAME")
        parameters = function.get("parameters", {})
        if parameters.get("type") != "object" or parameters.get("additionalProperties") is not False:
            reasons.append("INVALID_TOOL_PARAMETERS_SCHEMA")
        if set(parameters.get("required", [])) - set(parameters.get("properties", {})):
            reasons.append("INVALID_TOOL_REQUIRED_FIELDS")
        if not function.get("description"):
            reasons.append("MISSING_TOOL_DESCRIPTION")
        return not reasons, reasons

    def _data_qualification(self, model: BaseModelTool) -> tuple[bool, bool, List[str]]:
        """验证数据型工具是否真正通过数据库Repository执行并返回记录级溯源。"""
        data_required = model.data_requirement != "FORMULA_ONLY"
        if not data_required:
            return False, True, []

        reasons = []
        if model.data_access_mode != "database_repository":
            reasons.append("STATIC_DATA_NOT_ALLOWED")
        if not model.required_dataset_ids:
            reasons.append("MISSING_DATASET_DECLARATION")
        if not model.database_tables:
            reasons.append("MISSING_DATABASE_TABLE_DECLARATION")
        if model.data_access_mode != "database_repository":
            return True, False, reasons
        if not model.data_qualification_cases:
            reasons.append("MISSING_DATA_QUALIFICATION_CASE")
            return True, False, reasons

        for case in model.data_qualification_cases:
            case_id = case.get("id")
            result = self.invoke(model.model_id, case.get("input", {}))
            if not case_id or not result.success:
                reasons.append(f"DATA_CASE_FAILED:{case_id or 'missing-id'}")
                continue
            matching_records = [
                record for record in result.provenance
                if record.dataset_id in model.required_dataset_ids
                and record.table in model.database_tables
                and record.record_id
            ]
            if not matching_records:
                reasons.append(f"MISSING_RECORD_PROVENANCE:{case_id}")
        return True, not reasons, reasons

    def eligibility_report(self, model_id: str) -> dict:
        """返回实现、数据、接口、科学验证四维资格和最终计数资格。"""
        model = self.get(model_id)
        if model is None:
            return {
                "implementation_qualified": False,
                "data_required": False,
                "data_qualified": False,
                "interface_qualified": False,
                "scientific_validation_qualified": False,
                "fully_eligible": False,
                "implementation_reasons": [f"未知模型 ID: {model_id}"],
                "data_reasons": [],
                "interface_reasons": [],
            }

        implementation = self.qualification_report(model_id)
        data_required, data_qualified, data_reasons = self._data_qualification(model)
        interface_qualified, interface_reasons = self._interface_qualification(model)
        scientific_qualified = (
            bool(model.independent_validation)
            and implementation["normal_cases_passed"] >= 3
            and implementation["boundary_or_failure_cases_passed"] >= 2
        )
        fully_eligible = (
            implementation["qualified"]
            and data_qualified
            and interface_qualified
            and scientific_qualified
        )
        return {
            "implementation_qualified": implementation["qualified"],
            "data_required": data_required,
            "data_qualified": data_qualified,
            "interface_qualified": interface_qualified,
            "scientific_validation_qualified": scientific_qualified,
            "fully_eligible": fully_eligible,
            "implementation_reasons": list(implementation["reasons"]),
            "data_reasons": data_reasons,
            "interface_reasons": interface_reasons,
        }

    def get_counts(self) -> dict:
        """分别报告注册项数量和通过严格资格闸门的真实工具数量。"""
        if not self._initialized:
            self.discover()
        reports = {model_id: self.eligibility_report(model_id) for model_id in self._models}
        implementation_qualified = sum(x["implementation_qualified"] for x in reports.values())
        data_required = sum(x["data_required"] for x in reports.values())
        data_qualified = sum(x["data_required"] and x["data_qualified"] for x in reports.values())
        interface_qualified = sum(x["interface_qualified"] for x in reports.values())
        fully_eligible = sum(x["fully_eligible"] for x in reports.values())
        covered_catalog_ids = {
            model.catalog_id
            for model in self._models.values()
            if model.catalog_coverage and model.catalog_id
        }
        return {
            "registered_count": len(self._models),
            "runtime_tool_count": implementation_qualified,
            "catalog_coverage_count": len(covered_catalog_ids),
            "qualified_executable_count": fully_eligible,
            "implementation_qualified_count": implementation_qualified,
            "data_required_count": data_required,
            "data_qualified_count": data_qualified,
            "interface_qualified_count": interface_qualified,
            "fully_eligible_count": fully_eligible,
        }

    def list_models(self, qualified_only: bool = False,
                    fully_eligible_only: bool = False) -> List[dict]:
        """返回所有注册模型的元数据列表"""
        if not self._initialized:
            self.discover()
        entries = []
        for model_id, model in self._models.items():
            report = self.qualification_report(model_id)
            if qualified_only and not report["qualified"]:
                continue
            eligibility = self.eligibility_report(model_id)
            if fully_eligible_only and not eligibility["fully_eligible"]:
                continue
            entry = model.get_registry_entry()
            entry["qualification_status"] = "qualified" if report["qualified"] else "unqualified"
            entry["qualification"] = report
            entry["eligibility"] = eligibility
            # 对外计数资格由四维闸门动态确定，不信任模型卡中的静态声明。
            entry["count_eligible"] = eligibility["fully_eligible"]
            entries.append(entry)
        return entries

    def list_by_scenario(self, scenario: str, qualified_only: bool = False,
                         fully_eligible_only: bool = False) -> List[dict]:
        """按场景筛选模型"""
        return [entry for entry in self.list_models(
                    qualified_only=qualified_only,
                    fully_eligible_only=fully_eligible_only)
                if entry["scenario"] == scenario]

    def list_tool_definitions(self, fully_eligible_only: bool = True,
                              scenario: Optional[str] = None) -> List[dict]:
        """返回可直接交给大模型function calling的工具定义。"""
        if not self._initialized:
            self.discover()
        definitions = []
        for model_id in sorted(self._models):
            model = self._models[model_id]
            eligibility = self.eligibility_report(model_id)
            if fully_eligible_only and not eligibility["fully_eligible"]:
                continue
            if scenario and model.scenario != scenario:
                continue
            definitions.append(model.get_tool_definition(eligibility))
        return definitions

    def get_by_tool_name(self, tool_name: str,
                         fully_eligible_only: bool = True) -> Optional[BaseModelTool]:
        """根据大模型函数名解析工具，默认拒绝未获最终资格的工具。"""
        if not self._initialized:
            self.discover()
        for model_id, model in self._models.items():
            if model.tool_name != tool_name:
                continue
            if fully_eligible_only and not self.eligibility_report(model_id)["fully_eligible"]:
                return None
            return model
        return None

    def get_by_tool_uid(self, tool_uid: str,
                        fully_eligible_only: bool = True) -> Optional[BaseModelTool]:
        """Resolve an immutable tool identity without treating aliases as tools."""
        if not self._initialized:
            self.discover()
        matches = [model for model in self._models.values() if model.tool_uid == tool_uid]
        if len(matches) != 1:
            return None
        model = matches[0]
        if fully_eligible_only and not self.eligibility_report(model.model_id)["fully_eligible"]:
            return None
        return model

    def get_by_catalog_id(self, catalog_id: str,
                          fully_eligible_only: bool = True) -> Optional[BaseModelTool]:
        """Resolve an implemented catalog capability; scope variants do not match."""
        if not self._initialized:
            self.discover()
        matches = [
            model for model in self._models.values()
            if model.catalog_id == catalog_id and model.catalog_coverage
        ]
        if len(matches) != 1:
            return None
        model = matches[0]
        if fully_eligible_only and not self.eligibility_report(model.model_id)["fully_eligible"]:
            return None
        return model

    def invoke(self, model_id: str, params: dict,
               context: Optional[InvocationContext] = None) -> ModelResult:
        """调用模型：校验 + 执行"""
        model = self.get(model_id)
        if model is None:
            return ModelResult(
                success=False,
                error=f"未知模型 ID: {model_id}",
                error_code="UNKNOWN_MODEL",
            )

        # 输入校验
        errors = model.validate_input(params)
        if errors:
            return ModelResult(
                success=False,
                error="; ".join(errors),
                error_code="INVALID_INPUT",
                provenance=model.get_provenance(),
            )

        # 执行
        result = model.run_with_logging(params, context)
        result.error_code = normalize_error_code(result.error_code)
        return result

    def validate(self, model_id: str, params: dict) -> dict:
        """只校验输入，不执行模型。"""
        model = self.get(model_id)
        if model is None:
            return {
                "valid": False,
                "errors": [{
                    "code": "UNKNOWN_MODEL",
                    "field": "model_code",
                    "message": f"未知模型 ID: {model_id}",
                }],
            }

        errors = model.validate_input(params)
        return {
            "valid": not errors,
            "model_code": model_id,
            "model_version": model.version,
            "errors": [
                {"code": "INVALID_INPUT", "field": None, "message": message}
                for message in errors
            ],
        }


# 全局单例
registry = ModelRegistry()
