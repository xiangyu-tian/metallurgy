"""
A001 单位换算 —— 核心转换逻辑。

convert_units(value, source_unit, target_unit)
    主入口函数，执行单位换算并返回 ConversionResult。

支持：
  - 线性换算（大部分单位）
  - 偏移换算（温度：°C/°F ↔ K）
  - 量纲一致性校验
  - 边界检查与超界警告
  - 同类别宽松换算（如 % ↔ ppm 同属 dimensionless）
"""

import math
from typing import List, Optional, Dict, Any, Union

from .units import (
    resolve_unit, dimensions_match, get_category_for_dimension,
    dimension_symbol, UnitDef, UnitCategory,
)
from .models import (
    ConversionRequest, ConversionResult, BoundaryWarning, ConversionStep, UnitInfo,
)


def _convert_linear(value: float, source: UnitDef, target: UnitDef) -> float:
    """线性单位换算（无偏移）"""
    si_value = value * source.to_si_factor  + source.to_si_offset
    result = (si_value - target.to_si_offset) / target.to_si_factor
    return result


def _check_boundaries(
    value: float,
    si_value: float,
    source: UnitDef,
    target: UnitDef,
) -> List[BoundaryWarning]:
    """检查源单位和目标单位的合理值边界，返回告警列表"""
    warnings: List[BoundaryWarning] = []

    # 源值边界
    if source.min_value is not None and value < source.min_value:
        warnings.append(BoundaryWarning(
            field="source_value",
            message=f"源值 {value} {source.symbol} 低于合理下限 {source.min_value} "
                    f"{source.symbol}，结果可能不可靠",
            level="warning",
            si_value=si_value,
            min_allowed=source.min_value,
        ))
    if source.max_value is not None and value > source.max_value:
        warnings.append(BoundaryWarning(
            field="source_value",
            message=f"源值 {value} {source.symbol} 超过合理上限 {source.max_value} "
                    f"{source.symbol}，结果可能不可靠",
            level="warning",
            si_value=si_value,
            max_allowed=source.max_value,
        ))

    return warnings


def _is_offset_based(unit: UnitDef) -> bool:
    """判断是否偏移类单位（温度类且 to_si_offset != 0）"""
    return abs(unit.to_si_offset) > 1e-12


def convert_units(
    value: float,
    source_unit: str,
    target_unit: str,
    strict: bool = False,
) -> ConversionResult:
    """
    单位换算主函数。

    Args:
        value: 待换算的数值
        source_unit: 源单位符号或名称
        target_unit: 目标单位符号或名称
        strict: True=量纲不匹配时报错；False=返回告警但仍换算

    Returns:
        ConversionResult 对象

    Examples:
        >>> r = convert_units(100, "°C", "K")
        >>> print(r.value)  # 373.15

        >>> r = convert_units(1, "t", "kg")
        >>> print(r.value)  # 1000.0

        >>> r = convert_units(100, "MPa", "psi")
        >>> print(f"{r.value:.2f}")  # ~14503.77
    """
    # ── 解析单位 ──
    src = resolve_unit(source_unit)
    tgt = resolve_unit(target_unit)

    if src is None:
        return ConversionResult(
            success=False, value=0,
            source_value=value, source_unit=source_unit,
            target_unit=target_unit, conversion_factor=0,
            error=f"无法识别源单位: '{source_unit}'",
        )
    if tgt is None:
        return ConversionResult(
            success=False, value=0,
            source_value=value, source_unit=source_unit,
            target_unit=target_unit, conversion_factor=0,
            error=f"无法识别目标单位: '{target_unit}'",
        )

    # ── 量纲校验 ──
    if not dimensions_match(src.dimension, tgt.dimension):
        src_dim_str = dimension_symbol(src.dimension)
        tgt_dim_str = dimension_symbol(tgt.dimension)
        msg = (f"量纲不匹配: '{source_unit}' 的量纲为 [{src_dim_str}], "
               f"'{target_unit}' 的量纲为 [{tgt_dim_str}], "
               f"无法换算")
        if strict:
            return ConversionResult(
                success=False, value=0,
                source_value=value, source_unit=source_unit,
                target_unit=target_unit, conversion_factor=0,
                error=msg,
            )

    # ── 计算换算因子（用 1.0 做参考值） ──
    factor_ref = _convert_linear(1.0, src, tgt)

    # ── 执行换算 ──
    result_value = _convert_linear(value, src, tgt)

    # ── 量纲校验后的类别判断 ──
    cat = get_category_for_dimension(src.dimension)
    cat_str = cat.value if cat else "unknown"

    # ── 边界检查 ──
    si_value = value * src.to_si_factor + src.to_si_offset
    warnings = _check_boundaries(value, si_value, src, tgt)

    # ── 如果量纲不匹配，添加告警 ──
    if not dimensions_match(src.dimension, tgt.dimension):
        warnings.append(BoundaryWarning(
            field="dimension_mismatch",
            message=f"量纲不匹配: [{dimension_symbol(src.dimension)}] → "
                    f"[{dimension_symbol(tgt.dimension)}]，结果可能无物理意义",
            level="error",
        ))

    # ── 换算步骤（调试用） ──
    steps = [
        ConversionStep(step="源值 → SI", from_unit=src.symbol, to_unit="SI基值",
                       factor=src.to_si_factor),
        ConversionStep(step="SI → 目标", from_unit="SI基值", to_unit=tgt.symbol,
                       factor=1.0 / tgt.to_si_factor),
    ]

    # ── 修约处理 ──
    # 对于非常接近整数的结果，修约到合理精度
    if abs(result_value - round(result_value)) < 1e-12:
        result_value = float(round(result_value))
    elif abs(result_value - round(result_value, 10)) < 1e-12:
        # 修约到 10 位小数避免浮点噪声
        pass

    return ConversionResult(
        success=True,
        value=result_value,
        source_value=value,
        source_unit=src.symbol,
        target_unit=tgt.symbol,
        conversion_factor=factor_ref,
        category=cat_str,
        dimension=dimension_symbol(src.dimension),
        warnings=warnings,
        steps=steps,
    )


def list_available_units(category: Optional[str] = None) -> List[UnitInfo]:
    """
    列出所有可用的单位。

    Args:
        category: 按类别筛选（如 'length', 'pressure', 'temperature'）。
                  为 None 列出全部。

    Returns:
        UnitInfo 列表
    """
    from .units import _UNIT_REGISTRY

    results = []
    for u in _UNIT_REGISTRY.values():
        if category is None or u.category.value == category:
            results.append(UnitInfo(
                name=u.name,
                symbol=u.symbol,
                category=u.category.value,
                dimension=dimension_symbol(u.dimension),
                aliases=list(u.aliases),
                description=u.description,
            ))
    return results


# ── 便捷辅助函数 ───────────────────────────────

def convert_length(value: float, source: str, target: str) -> ConversionResult:
    """长度换算快捷函数"""
    return convert_units(value, source, target)


def convert_mass(value: float, source: str, target: str) -> ConversionResult:
    """质量换算快捷函数"""
    return convert_units(value, source, target)


def convert_temperature(value: float, source: str, target: str) -> ConversionResult:
    """温度换算快捷函数（含偏移量）"""
    return convert_units(value, source, target)


def convert_pressure(value: float, source: str, target: str) -> ConversionResult:
    """压力换算快捷函数"""
    return convert_units(value, source, target)


def convert_energy(value: float, source: str, target: str) -> ConversionResult:
    """能量换算快捷函数"""
    return convert_units(value, source, target)


def convert_flow(value: float, source: str, target: str) -> ConversionResult:
    """流量换算快捷函数"""
    return convert_units(value, source, target)


def convert_density(value: float, source: str, target: str) -> ConversionResult:
    """密度换算快捷函数"""
    return convert_units(value, source, target)


def convert_mass_flow(value: float, source: str, target: str) -> ConversionResult:
    """质量流量换算快捷函数"""
    return convert_units(value, source, target)
