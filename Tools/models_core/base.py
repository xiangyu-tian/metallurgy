"""
BaseModelTool — 统一模型基类
"""
from __future__ import annotations
import uuid
import time
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field, asdict


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
    ):
        self.name = name
        self.label = label
        self.type = type
        self.required = required
        self.default = default
        self.unit = unit
        self.min_value = min_value
        self.max_value = max_value
        self.enum = enum
        self.placeholder = placeholder
        self.description = description

    def to_dict(self) -> dict:
        d = {
            "name": self.name,
            "label": self.label,
            "type": self.type,
            "required": self.required,
            "description": self.description,
        }
        if self.default is not None:
            d["default"] = self.default
        if self.unit:
            d["unit"] = self.unit
        if self.min_value is not None:
            d["min_value"] = self.min_value
        if self.max_value is not None:
            d["max_value"] = self.max_value
        if self.enum:
            d["enum"] = self.enum
        if self.placeholder:
            d["placeholder"] = self.placeholder
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

    # --- Schema（子类重写）---
    input_fields: List[InputField] = []
    output_fields: List[OutputField] = []
    validation_rules: List[Dict] = []

    def __init_subclass__(cls, **kwargs):
        """自动设置 api_name"""
        super().__init_subclass__(**kwargs)
        if not cls.api_name and cls.model_id:
            cls.api_name = f"model_{cls.model_id.lower()}"

    def get_input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {f.name: f.to_dict() for f in self.input_fields},
            "required": [f.name for f in self.input_fields if f.required],
        }

    def get_output_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {f.name: f.to_dict() for f in self.output_fields},
        }

    def get_registry_entry(self) -> dict:
        return {
            "model_id": self.model_id,
            "name": self.name,
            "scenario": self.scenario,
            "model_type": self.model_type,
            "api_name": self.api_name,
            "version": self.version,
            "priority": self.priority,
            "applicable_boundary": self.applicable_boundary,
            "input_schema_json": self.get_input_schema(),
            "output_schema_json": self.get_output_schema(),
            "validation_rules": self.validation_rules,
        }

    # --- 核心方法 ---

    def invoke(self, params: dict, context: Optional[InvocationContext] = None) -> ModelResult:
        """
        执行模型计算。
        子类必须重写此方法。
        """
        raise NotImplementedError

    def validate_input(self, params: dict) -> List[str]:
        """输入校验，返回错误信息列表"""
        errors = []
        for f in self.input_fields:
            if f.required and f.name not in params:
                errors.append(f"缺少必填参数: {f.name}")
            if f.name in params and f.type == "number":
                val = params[f.name]
                try:
                    val = float(val)
                except (TypeError, ValueError):
                    errors.append(f"{f.name} 必须是数值")
                    continue
                if f.min_value is not None and val < f.min_value:
                    errors.append(f"{f.name} ({val}) 低于最小值 {f.min_value}")
                if f.max_value is not None and val > f.max_value:
                    errors.append(f"{f.name} ({val}) 超过最大值 {f.max_value}")
            if f.name in params and f.enum and params[f.name] not in f.enum:
                errors.append(f"{f.name} 必须是 {f.enum} 之一，收到 {params[f.name]}")
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
        result.runtime_ms = round((time.perf_counter() - start) * 1000, 2)
        result.trace_id = ctx.trace_id
        return result


def make_boundary_check(**kwargs) -> BoundaryCheck:
    """方便构造 BoundaryCheck"""
    passed = kwargs.pop("passed", True)
    warnings = kwargs.pop("warnings", [])
    return BoundaryCheck(passed=passed, warnings=warnings)
