"""
BaseModelTool — 统一模型基类
"""
from __future__ import annotations
import math
import uuid
import time
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field, asdict

from .errors import STANDARD_ERROR_CODES


# ── 数据类 ──

@dataclass
class BoundaryWarning:
    field: str
    message: str
    level: str = "warning"         # warning / error
    min_allowed: Optional[float] = None
    max_allowed: Optional[float] = None


@dataclass
class BoundaryCheck:
    passed: bool = True
    warnings: List[BoundaryWarning] = field(default_factory=list)


@dataclass
class Provenance:
    """数据来源追踪"""
    dataset_id: str
    name: str
    version: Optional[str] = None
    url: Optional[str] = None
    table: Optional[str] = None
    record_id: Optional[str] = None
    source_ref: Optional[str] = None
    checksum: Optional[str] = None
    applicable_domain: Optional[Dict[str, Any]] = None


@dataclass
class ModelResult:
    """模型调用统一返回格式"""
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    confidence: Optional[float] = None
    boundary_check: BoundaryCheck = field(default_factory=BoundaryCheck)
    provenance: List[Provenance] = field(default_factory=list)
    runtime_ms: float = 0.0
    trace_id: str = ""


@dataclass
class InvocationContext:
    """调用上下文"""
    user_or_agent: str = "system"
    trace_id: str = ""
    validate_boundary: bool = True
    return_provenance: bool = True


# ── Schema 构建辅助 ──

class InputField:
    """描述一个输入参数"""
    def __init__(
        self,
        name: str,
        label: str,
        type: str = "number",        # number / string / select / boolean
        required: bool = True,
        default: Any = None,
        unit: Optional[str] = None,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        enum: Optional[List[str]] = None,
        placeholder: Optional[str] = None,
        description: str = "",
        items: Optional[Dict[str, Any]] = None,
    ):
        self.name = name
        self.label = label
        # ``select`` was used by the legacy UI. JSON Schema represents it as
        # a string with enum; ui_type keeps the display hint backwards-compatible.
        self.ui_type = type
        self.type = "string" if type == "select" else type
        self.required = required
        self.default = default
        self.unit = unit
        self.min_value = min_value
        self.max_value = max_value
        self.enum = enum
        self.placeholder = placeholder
        self.description = description
        self.items = items

    def to_dict(self) -> dict:
        d = {
            "name": self.name,
            "label": self.label,
            "type": self.type,
            "required": self.required,
            "description": self.description,
            "ui_type": self.ui_type,
        }
        if self.default is not None:
            d["default"] = self.default
        if self.unit:
            d["unit"] = self.unit
        if self.min_value is not None:
            d["min_value"] = self.min_value
            d["minimum"] = self.min_value
        if self.max_value is not None:
            d["max_value"] = self.max_value
            d["maximum"] = self.max_value
        if self.enum:
            d["enum"] = self.enum
        if self.placeholder:
            d["placeholder"] = self.placeholder
        if self.items is not None:
            d["items"] = self.items
        return d


class OutputField:
    """描述一个输出字段"""
    def __init__(
        self,
        name: str,
        label: str,
        type: str = "number",
        unit: Optional[str] = None,
        description: str = "",
    ):
        self.name = name
        self.label = label
        self.type = type
        self.unit = unit
        self.description = description

    def to_dict(self) -> dict:
        d = {
            "name": self.name,
            "label": self.label,
            "type": self.type,
            "description": self.description,
        }
        if self.unit:
            d["unit"] = self.unit
        return d


# ── 模型基类 ──

class BaseModelTool:
    """所有小模型的基类"""

    # --- 元数据（子类重写）---
    model_id: str = ""
    name: str = ""
    scenario: str = ""
    model_type: str = "确定性公式/规则"
    version: str = "1.0.0"
    priority: str = "P2"
    applicable_boundary: str = ""
    api_name: str = ""
    tool_name: str = ""
    description: str = ""
    temperature_range: Optional[List[float]] = None
    pressure_range: Optional[List[float]] = None
    required_data: List[str] = []
    data_source: List[str] = []
    formula_reference: str = ""
    dependencies: List[str] = []
    status: str = "baseline"
    source_version: str = ""
    source_records: List[Dict[str, str]] = []
    failure_modes: List[str] = []
    independent_validation: List[str] = []
    relations: List[Dict[str, str]] = []
    qualification_status: str = "unqualified"
    count_eligible: bool = False
    qualification_cases: List[Dict[str, Any]] = []
    # 数据资格契约。静态JSON/Python表可以作为导入源或测试夹具，但数据必需型
    # 工具只有通过数据库Repository并执行数据准入样例后才具备最终资格。
    data_requirement: str = "FORMULA_ONLY"
    data_access_mode: str = "none"
    required_dataset_ids: List[str] = []
    database_tables: List[str] = []
    data_qualification_cases: List[Dict[str, Any]] = []
    # 目录身份与运行时身份分离。值由版本化crosswalk在注册发现时注入，
    # 避免为兼容旧model_code而复制或重命名真实工具。
    tool_uid: str = ""
    catalog_id: Optional[str] = None
    catalog_mapping_status: str = "unmapped"
    catalog_coverage: bool = False
    legacy_model_codes: List[str] = []
    related_catalog_ids: List[str] = []

    # --- Schema（子类重写）---
    input_fields: List[InputField] = []
    output_fields: List[OutputField] = []
    validation_rules: List[Dict] = []

    def __init_subclass__(cls, **kwargs):
        """自动设置兼容API名和面向大模型的稳定函数名。"""
        super().__init_subclass__(**kwargs)
        if not cls.api_name and cls.model_id:
            cls.api_name = f"model_{cls.model_id.lower()}"
        if not cls.tool_name and cls.model_id:
            cls.tool_name = f"metallurgy_{cls.model_id.lower()}"

    def get_input_schema(self) -> dict:
        return {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {f.name: f.to_dict() for f in self.input_fields},
            "required": [f.name for f in self.input_fields if f.required],
            "additionalProperties": False,
        }

    def get_output_schema(self) -> dict:
        return {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {f.name: f.to_dict() for f in self.output_fields},
            "required": [f.name for f in self.output_fields],
            "additionalProperties": False,
        }

    def get_llm_input_schema(self) -> dict:
        """返回只含标准JSON Schema关键字的function-tool参数契约。"""
        properties = {}
        for field_spec in self.input_fields:
            prop = {"type": field_spec.type}
            description = field_spec.description or field_spec.label
            if field_spec.unit:
                description = f"{description}；单位: {field_spec.unit}"
            prop["description"] = description
            if field_spec.default is not None:
                prop["default"] = field_spec.default
            if field_spec.min_value is not None:
                prop["minimum"] = field_spec.min_value
            if field_spec.max_value is not None:
                prop["maximum"] = field_spec.max_value
            if field_spec.enum:
                prop["enum"] = list(field_spec.enum)
            if field_spec.items is not None:
                prop["items"] = field_spec.items
            properties[field_spec.name] = prop
        return {
            "type": "object",
            "properties": properties,
            "required": [f.name for f in self.input_fields if f.required],
            "additionalProperties": False,
        }

    def get_tool_definition(self, eligibility: Optional[Dict[str, Any]] = None) -> dict:
        """构建可直接交给大模型function calling的稳定工具定义。"""
        return {
            "type": "function",
            "function": {
                "name": self.tool_name,
                "description": self.description or self.applicable_boundary,
                "parameters": self.get_llm_input_schema(),
            },
            "tool_uid": self.tool_uid,
            "catalog_id": self.catalog_id,
            "catalog_mapping_status": self.catalog_mapping_status,
            "legacy_model_codes": list(self.legacy_model_codes),
            "model_code": self.model_id,
            "model_version": self.version,
            "category": self.scenario,
            "data_requirement": self.data_requirement,
            "required_dataset_ids": list(self.required_dataset_ids),
            "fully_eligible": bool((eligibility or {}).get("fully_eligible", False)),
        }

    def get_registry_entry(self) -> dict:
        input_schema = self.get_input_schema()
        output_schema = self.get_output_schema()
        input_units = {
            f.name: f.unit for f in self.input_fields if f.unit
        }
        output_units = {
            f.name: f.unit for f in self.output_fields if f.unit
        }
        return {
            "tool_uid": self.tool_uid,
            "catalog_id": self.catalog_id,
            "catalog_mapping_status": self.catalog_mapping_status,
            "catalog_coverage": self.catalog_coverage,
            "legacy_model_codes": list(self.legacy_model_codes),
            "related_catalog_ids": list(self.related_catalog_ids),
            "model_id": self.model_id,
            "model_code": self.model_id,
            "name": self.name,
            "model_name": self.name,
            "scenario": self.scenario,
            "category": self.scenario,
            "description": self.description or self.applicable_boundary,
            "model_type": self.model_type,
            "api_name": self.api_name,
            "tool_name": self.tool_name,
            "version": self.version,
            "priority": self.priority,
            "applicable_boundary": self.applicable_boundary,
            "applicable_conditions": self.applicable_boundary,
            "temperature_range": self.temperature_range,
            "pressure_range": self.pressure_range,
            "required_data": self.required_data,
            "data_source": self.data_source,
            "formula_reference": self.formula_reference,
            "dependencies": self.dependencies,
            "status": self.status,
            "qualification_status": self.qualification_status,
            "count_eligible": self.count_eligible,
            "data_requirement": self.data_requirement,
            "data_access_mode": self.data_access_mode,
            "required_dataset_ids": list(self.required_dataset_ids),
            "database_tables": list(self.database_tables),
            "source_version": self.source_version,
            "source_records": self.source_records,
            "failure_modes": self.failure_modes,
            "independent_validation": self.independent_validation,
            "relations": self.relations,
            "input_schema_json": input_schema,
            "output_schema_json": output_schema,
            "input_schema": input_schema,
            "output_schema": output_schema,
            "input_units": input_units,
            "output_units": output_units,
            "validation_rules": self.validation_rules,
            "error_codes": list(STANDARD_ERROR_CODES),
        }

    def get_provenance(self) -> List[Provenance]:
        """Build standardized provenance records from the immutable tool card."""
        return [
            Provenance(
                dataset_id=record["source_id"],
                name=record["name"],
                version=record.get("version") or self.source_version or None,
                url=record.get("url"),
                table=record.get("table"),
                record_id=str(record["record_id"]) if record.get("record_id") is not None else None,
                source_ref=record.get("source_ref"),
                checksum=record.get("checksum"),
                applicable_domain=record.get("applicable_domain"),
            )
            for record in self.source_records
        ]

    # --- 核心方法 ---

    def invoke(self, params: dict, context: Optional[InvocationContext] = None) -> ModelResult:
        """
        执行模型计算。
        子类必须重写此方法。
        """
        raise NotImplementedError

    def validate_input(self, params: dict) -> List[str]:
        """输入校验，返回错误信息列表"""
        if not isinstance(params, dict):
            return ["输入必须是 JSON 对象"]

        errors = []
        for f in self.input_fields:
            value = params.get(f.name)
            is_empty = value is None or value == "" or value == {} or value == []
            if f.required and (f.name not in params or is_empty):
                errors.append(f"缺少必填参数: {f.name}")
                continue
            if f.name in params and f.type == "number":
                val = value
                if isinstance(val, bool):
                    errors.append(f"{f.name} 必须是数值")
                    continue
                try:
                    val = float(val)
                except (TypeError, ValueError):
                    errors.append(f"{f.name} 必须是数值")
                    continue
                if not math.isfinite(val):
                    errors.append(f"{f.name} 必须是有限数值")
                    continue
                if f.min_value is not None and val < f.min_value:
                    errors.append(f"{f.name} ({val}) 低于最小值 {f.min_value}")
                if f.max_value is not None and val > f.max_value:
                    errors.append(f"{f.name} ({val}) 超过最大值 {f.max_value}")
            if f.name in params and f.type == "string" \
                    and not isinstance(value, str):
                errors.append(f"{f.name} 必须是字符串")
            if f.name in params and f.type == "object" and not isinstance(value, dict):
                errors.append(f"{f.name} 必须是对象")
            if f.name in params and f.type == "array" and not isinstance(value, list):
                errors.append(f"{f.name} 必须是数组")
            if f.name in params and f.type == "boolean" and not isinstance(value, bool):
                errors.append(f"{f.name} 必须是布尔值")
            if f.name in params and f.enum and value not in f.enum:
                errors.append(f"{f.name} 必须是 {f.enum} 之一，收到 {value}")
        return errors

    def run_with_logging(self, params: dict, context: Optional[InvocationContext] = None) -> ModelResult:
        """带日志和计时的 invoke 包装"""
        if context is None:
            context = InvocationContext()
        if not context.trace_id:
            context.trace_id = f"TRACE-{uuid.uuid4().hex[:12].upper()}"

        ctx = context
        start = time.perf_counter()
        try:
            result = self.invoke(params, ctx)
        except Exception as e:
            result = ModelResult(
                success=False,
                error=str(e),
                error_code="INTERNAL_ERROR",
            )
        if ctx.return_provenance and not result.provenance:
            result.provenance = self.get_provenance()
        result.runtime_ms = round((time.perf_counter() - start) * 1000, 2)
        result.trace_id = ctx.trace_id
        return result


def make_boundary_check(**kwargs) -> BoundaryCheck:
    """方便构造 BoundaryCheck"""
    passed = kwargs.pop("passed", True)
    warnings = kwargs.pop("warnings", [])
    return BoundaryCheck(passed=passed, warnings=warnings)
