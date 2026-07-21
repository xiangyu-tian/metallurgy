"""A001 - 单位换算 (Unit Conversion)

确定性公式/规则模型 —— 量纲分析与单位映射。
实现: Python 函数 + Pydantic 参数校验 + 边界告警。

API 函数: convert_units(value, source_unit, target_unit)
"""

from .converter import convert_units, list_available_units, UnitCategory
from .models import ConversionRequest, ConversionResult, UnitInfo

__all__ = [
    "convert_units",
    "list_available_units",
    "UnitCategory",
    "ConversionRequest",
    "ConversionResult",
    "UnitInfo",
]
