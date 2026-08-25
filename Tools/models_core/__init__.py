"""
models_core — 冶金平台统一模型内核

架构：
  - 每个模型继承 BaseModelTool，实现 invoke() 方法
  - 通过 ModelRegistry 自动发现和注册
  - 通过统一的 input_schema / output_schema 驱动前端动态表单
  - 内置边界校验、版本追踪、调用日志

使用示例：
    from models_core import ModelRegistry
    registry = ModelRegistry()
    registry.discover()
    result = registry.invoke("A001", {"value": 100, "source_unit": "°C", "target_unit": "K"})
"""

from .base import BaseModelTool, ModelResult, BoundaryCheck, InvocationContext
from .registry import ModelRegistry
from .chemical_data import THERMOCHEMICAL_DB, ELEMENT_ATOMIC_WEIGHTS
from .errors import STANDARD_ERROR_CODES
from .services import ExperimentService, InMemoryTraceStore, ModelExecutionService

__version__ = "0.1.0"
