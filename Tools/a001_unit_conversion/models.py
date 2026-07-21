"""
Pydantic 模型 —— A001 单位换算的输入/输出定义及参数校验。
"""

from pydantic import BaseModel, Field, model_validator
from typing import List, Optional, Dict, Any, Union


class ConversionRequest(BaseModel):
    """单位换算请求参数"""
    value: float = Field(
        ..., description="待换算的数值",
    )
    source_unit: str = Field(
        ..., min_length=1, max_length=50,
        description="源单位符号或名称（如 'm', 'kg', '°C', 'MPa'）",
    )
    target_unit: str = Field(
        ..., min_length=1, max_length=50,
        description="目标单位符号或名称",
    )
    strict: bool = Field(
        default=False,
        description="严格模式：True=量纲不匹配时报错；False=仅在严格时返回警告",
    )

    @model_validator(mode='after')
    def validate_units_not_same(self) -> 'ConversionRequest':
        if self.source_unit.strip().lower() == self.target_unit.strip().lower():
            raise ValueError(f"源单位和目标单位相同: '{self.source_unit}'，无需换算")
        return self


class BoundaryWarning(BaseModel):
    """边界告警信息"""
    field: str = Field(..., description="触发告警的字段")
    message: str = Field(..., description="告警信息")
    level: str = Field(default="warning", description="告警级别: info/warning/error")
    si_value: Optional[float] = Field(None, description="SI 制下的数值")
    min_allowed: Optional[float] = Field(None, description="允许的最小值")
    max_allowed: Optional[float] = Field(None, description="允许的最大值")


class ConversionStep(BaseModel):
    """换算步骤记录"""
    step: str = Field(..., description="步骤描述")
    from_unit: str = Field(..., description="当前单位")
    to_unit: str = Field(..., description="目标单位")
    factor: float = Field(..., description="换算因子")


class ConversionResult(BaseModel):
    """单位换算结果"""
    success: bool = Field(default=True, description="是否成功")
    value: float = Field(..., description="换算后的数值")
    source_value: float = Field(..., description="原始数值")
    source_unit: str = Field(..., description="源单位")
    target_unit: str = Field(..., description="目标单位")
    conversion_factor: float = Field(..., description="从源到目标的换算因子")
    category: str = Field("", description="物理量类别（如 length, pressure, temperature 等）")
    dimension: str = Field("", description="量纲表示（如 L, M·T⁻²）")

    warnings: List[BoundaryWarning] = Field(
        default_factory=list, description="边界告警列表"
    )
    steps: List[ConversionStep] = Field(
        default_factory=list, description="换算步骤（仅供调试）"
    )

    error: Optional[str] = Field(None, description="错误信息（success=False 时）")


class UnitInfo(BaseModel):
    """单位信息（供 list_available_units 返回）"""
    name: str = Field(..., description="注册名称")
    symbol: str = Field(..., description="符号")
    category: str = Field(..., description="物理量类别")
    dimension: str = Field(..., description="量纲表示")
    aliases: List[str] = Field(default_factory=list, description="别名")
    description: str = Field("", description="说明")
