"""
A 系列模型：通用数据与校验
A001 单位换算 → 委托到 a001_unit_conversion
A002 化学式解析
A003 摩尔质量计算
A004 成分归一化
A005 元素质量守恒校验
"""
from __future__ import annotations
import math
import re
from typing import Dict, List, Optional, Tuple

from .base import (
    BaseModelTool, ModelResult, InputField, OutputField,
    BoundaryCheck, BoundaryWarning, InvocationContext, Provenance,
)
from .chemical_data import ELEMENT_ATOMIC_WEIGHTS


# ── A001 单位换算 ──

class A001_UnitConversion(BaseModelTool):
    model_id = "A001"
    name = "单位换算"
    scenario = "通用数据与校验"
    priority = "P0"
    version = "1.0.0"
    applicable_boundary = "支持线性换算和温度偏移换算；超界返回警告"

    input_fields = [
        InputField("value", "数值", type="number", required=True, description="待换算的数值"),
        InputField("source_unit", "源单位", type="string", required=True, placeholder="如 °C, kg, MPa"),
        InputField("target_unit", "目标单位", type="string", required=True, placeholder="如 K, g, psi"),
    ]

    output_fields = [
        OutputField("value", "换算值", type="number"),
        OutputField("source_unit", "源单位", type="string"),
        OutputField("target_unit", "目标单位", type="string"),
        OutputField("conversion_factor", "换算因子", type="number"),
        OutputField("category", "单位类别", type="string"),
    ]

    def invoke(self, params: dict, context: Optional[InvocationContext] = None) -> ModelResult:
        # 尝试委托到 a001_unit_conversion（如果已安装）
        try:
            from a001_unit_conversion import convert_units
            r = convert_units(
                params["value"], params["source_unit"],
                params["target_unit"], strict=False
            )
            warnings = []
            if hasattr(r, 'warnings') and r.warnings:
                for w in r.warnings:
                    warnings.append(BoundaryWarning(
                        field=getattr(w, 'field', 'value'),
                        message=getattr(w, 'message', str(w)),
                        level=getattr(w, 'level', 'warning'),
                    ))

            return ModelResult(
                success=True,
                result={
                    "value": r.value,
                    "source_unit": r.source_unit,
                    "target_unit": r.target_unit,
                    "conversion_factor": getattr(r, 'conversion_factor', r.value / params['value'] if params['value'] else 0),
                    "category": getattr(r, 'category', ''),
                },
                boundary_check=BoundaryCheck(
                    passed=len([w for w in warnings if w.level == 'error']) == 0,
                    warnings=warnings,
                ),
            )
        except ImportError:
            pass

        # 内置简易换算（作为 fallback）
        value = float(params["value"])
        src = params["source_unit"]
        tgt = params["target_unit"]

        # 温度专用
        temp_conversions = {
            ("°C", "K"): (lambda v: v + 273.15, 1),
            ("K", "°C"): (lambda v: v - 273.15, 1),
            ("°C", "°F"): (lambda v: v * 9/5 + 32, 9/5),
            ("°F", "°C"): (lambda v: (v - 32) * 5/9, 5/9),
        }
        if (src, tgt) in temp_conversions:
            fn, factor = temp_conversions[(src, tgt)]
            result = fn(value)
            return ModelResult(
                success=True,
                result={
                    "value": round(result, 6),
                    "source_unit": src,
                    "target_unit": tgt,
                    "conversion_factor": factor,
                    "category": "温度",
                },
            )

        # 常用单位映射到 SI base
        unit_to_si = {
            "kg": ("质量", 1), "g": ("质量", 0.001), "t": ("质量", 1000), "lb": ("质量", 0.453592),
            "m": ("长度", 1), "cm": ("长度", 0.01), "mm": ("长度", 0.001), "km": ("长度", 1000),
            "Pa": ("压强", 1), "kPa": ("压强", 1000), "MPa": ("压强", 1e6),
            "atm": ("压强", 101325), "bar": ("压强", 1e5), "psi": ("压强", 6894.76),
            "J": ("能量", 1), "kJ": ("能量", 1000), "cal": ("能量", 4.184),
            "W": ("功率", 1), "kW": ("功率", 1000), "MW": ("功率", 1e6),
            "s": ("时间", 1), "min": ("时间", 60), "h": ("时间", 3600),
        }

        if src in unit_to_si and tgt in unit_to_si:
            cat_src, factor_src = unit_to_si[src]
            cat_tgt, factor_tgt = unit_to_si[tgt]
            if cat_src != cat_tgt:
                return ModelResult(
                    success=False, error=f"量纲不匹配: {cat_src} vs {cat_tgt}",
                    error_code="DIMENSION_MISMATCH",
                )
            si_value = value * factor_src
            result = si_value / factor_tgt
            return ModelResult(
                success=True,
                result={
                    "value": round(result, 10),
                    "source_unit": src,
                    "target_unit": tgt,
                    "conversion_factor": round(factor_src / factor_tgt, 10),
                    "category": cat_src,
                },
            )

        return ModelResult(
            success=False, error=f"不支持的换算: {src} → {tgt}",
            error_code="UNSUPPORTED_CONVERSION",
        )


# ── 化学式解析辅助 ──

# 元素符号正则：大写字母开头，后跟可选小写字母
_ELEM_RE = re.compile(r'([A-Z][a-z]?)(\d*(?:\.\d+)?)')
_BRACKET_RE = re.compile(r'[\(\[{]')
_BRACKET_CLOSE = {'(': ')', '[': ']', '{': '}'}

def parse_formula(formula: str) -> Tuple[Optional[Dict[str, float]], Optional[str]]:
    """
    解析化学式，返回 {元素: 数量} 和错误信息。
    支持括号嵌套：Fe2(SO4)3, Mg(OH)2, [Cu(NH3)4]SO4
    """
    formula = formula.strip()
    if not formula:
        return None, "化学式为空"

    # 词法分析：括号 + 元素 + 数字
    # 先展开所有括号
    try:
        expanded = _expand_brackets(formula)
    except ValueError as e:
        return None, str(e)

    # 解析展开后的元素
    counts: Dict[str, float] = {}
    for elem, num_str in _ELEM_RE.findall(expanded):
        num = float(num_str) if num_str else 1
        counts[elem] = counts.get(elem, 0) + num

    # 验证元素存在
    for elem in counts:
        if elem not in ELEMENT_ATOMIC_WEIGHTS:
            return None, f"未知元素: {elem}"

    return counts, None


def _expand_brackets(s: str) -> str:
    """递归展开括号：Fe2(SO4)3 → Fe2S3O12"""
    # 找到最内层括号
    stack = []
    for i, ch in enumerate(s):
        if ch in _BRACKET_CLOSE:
            stack.append((i, ch))
        elif ch in ')]}':
            if not stack:
                raise ValueError(f"括号不匹配: 多余的 '{ch}'")
            start, open_ch = stack.pop()
            expected_close = _BRACKET_CLOSE[open_ch]
            if ch != expected_close:
                raise ValueError(f"括号不匹配: '{open_ch}' 期望 '{expected_close}' 但收到 '{ch}'")
            # 提取括号内容
            inner = s[start+1:i]
            # 提取括号后的数字
            j = i + 1
            while j < len(s) and (s[j].isdigit() or s[j] == '.'):
                j += 1
            multiplier = float(s[i+1:j]) if j > i + 1 else 1
            # 展开括号内每个元素
            expanded_inner = _multiply_elements(inner, multiplier)
            s = s[:start] + expanded_inner + s[j:]
            # 递归处理外层括号
            return _expand_brackets(s)

    if stack:
        raise ValueError("括号不匹配: 有未闭合的括号")

    return s


def _multiply_elements(s: str, multiplier: float) -> str:
    """将化学式中的每个元素数量乘以系数"""
    result = []
    for elem, num_str in _ELEM_RE.findall(s):
        num = float(num_str) if num_str else 1
        new_num = num * multiplier
        if new_num == int(new_num):
            result.append(f"{elem}{int(new_num)}")
        else:
            result.append(f"{elem}{new_num}")
    return ''.join(result)


def calc_molar_mass_from_elements(elements: Dict[str, float]) -> float:
    """根据元素组成计算摩尔质量"""
    return sum(count * ELEMENT_ATOMIC_WEIGHTS[elem] for elem, count in elements.items())


# ── A002 化学式解析 ──

class A002_ChemicalFormulaParser(BaseModelTool):
    model_id = "A002"
    name = "化学式解析"
    scenario = "通用数据与校验"
    priority = "P0"
    version = "1.0.0"
    applicable_boundary = "支持含括号的化学式；不支持同位素标记"

    input_fields = [
        InputField("formula", "化学式", type="string", required=True,
                    placeholder="如 Fe2(SO4)3, CaCO3, Mg(OH)2"),
    ]

    output_fields = [
        OutputField("elements", "元素组成", type="object"),
        OutputField("molar_mass", "摩尔质量 (g/mol)", type="number"),
        OutputField("formula_display", "显示格式", type="string"),
    ]

    def invoke(self, params: dict, context: Optional[InvocationContext] = None) -> ModelResult:
        formula = params["formula"]
        elements, error = parse_formula(formula)
        if error:
            return ModelResult(success=False, error=error, error_code="PARSE_ERROR")

        mm = calc_molar_mass_from_elements(elements)

        total_atoms = sum(elements.values())
        mass_fractions = {}
        for elem, count in elements.items():
            elem_mass = count * ELEMENT_ATOMIC_WEIGHTS[elem]
            mass_fractions[elem] = round(elem_mass / mm, 6)

        return ModelResult(
            success=True,
            result={
                "elements": {k: (v if v == int(v) else v) for k, v in elements.items()},
                "element_count": len(elements),
                "total_atoms": total_atoms,
                "molar_mass": round(mm, 4),
                "mass_fractions": mass_fractions,
                "formula_display": formula,
                "is_stoichiometric": all(v == int(v) for v in elements.values()),
            },
        )


# ── A003 摩尔质量计算 ──

class A003_MolarMassCalculator(BaseModelTool):
    model_id = "A003"
    name = "摩尔质量计算"
    scenario = "通用数据与校验"
    priority = "P0"
    version = "1.0.0"
    applicable_boundary = "基于 IUPAC 2021 原子量"

    input_fields = [
        InputField("formula", "化学式", type="string", required=True,
                    placeholder="如 Fe2O3, H2SO4, CaCO3"),
    ]

    output_fields = [
        OutputField("molar_mass", "摩尔质量 (g/mol)", type="number"),
        OutputField("formula", "化学式", type="string"),
    ]

    def invoke(self, params: dict, context: Optional[InvocationContext] = None) -> ModelResult:
        formula = params["formula"]
        elements, error = parse_formula(formula)
        if error:
            return ModelResult(success=False, error=error, error_code="PARSE_ERROR")

        mm = calc_molar_mass_from_elements(elements)
        return ModelResult(
            success=True,
            result={
                "molar_mass": round(mm, 4),
                "formula": formula,
                "unit": "g/mol",
            },
        )


# ── A004 成分归一化 ──

class A004_CompositionNormalizer(BaseModelTool):
    model_id = "A004"
    name = "成分归一化"
    scenario = "通用数据与校验"
    priority = "P0"
    version = "1.0.0"
    applicable_boundary = "输入各组分分数（质量或摩尔），总和可不等于1"

    input_fields = [
        InputField("compositions", "组成", type="object", required=True,
                    description='如 {"Fe": 0.94, "C": 0.005, "Si": 0.003}'),
        InputField("tolerance", "容差", type="number", required=False, default=0.001,
                    description="归一化偏差容差"),
    ]

    output_fields = [
        OutputField("normalized", "归一化组成", type="object"),
        OutputField("sum_before", "归一化前总和", type="number"),
        OutputField("deviation", "偏差", type="number"),
        OutputField("passed", "是否通过", type="boolean"),
    ]

    def invoke(self, params: dict, context: Optional[InvocationContext] = None) -> ModelResult:
        comps = params.get("compositions", {})
        tol = float(params.get("tolerance", 0.001))

        if not comps:
            return ModelResult(success=False, error="组成不能为空", error_code="INVALID_INPUT")

        values = [float(v) for v in comps.values()]
        total = sum(values)

        if total == 0:
            return ModelResult(success=False, error="组成总和为0", error_code="INVALID_INPUT")

        normalized = {k: round(float(v) / total, 6) for k, v in comps.items()}
        deviation = abs(total - 1.0)
        passed = deviation <= tol

        warnings = []
        if not passed:
            warnings.append(BoundaryWarning(
                field="compositions", level="warning",
                message=f"归一化前总和 {total:.6f}，偏差 {deviation:.6f} 超出容差 {tol}",
            ))

        return ModelResult(
            success=True,
            result={
                "normalized": normalized,
                "sum_before": round(total, 6),
                "sum_after": 1.0,
                "deviation": round(deviation, 6),
                "passed": passed,
            },
            boundary_check=BoundaryCheck(passed=passed, warnings=warnings),
        )


# ── A005 元素质量守恒校验 ──

class A005_MassBalanceChecker(BaseModelTool):
    model_id = "A005"
    name = "元素质量守恒校验"
    scenario = "通用数据与校验"
    priority = "P0"
    version = "1.0.0"
    applicable_boundary = "输入输出物料流中各元素质量分数"

    input_fields = [
        InputField("input_streams", "输入物流", type="object", required=True,
                    description='[{"name":"铁水","mass":100,"elements":{"Fe":0.94,"C":0.04}}, ...]'),
        InputField("output_streams", "输出物流", type="object", required=True,
                    description='[{"name":"钢水","mass":92,"elements":{"Fe":0.98,"C":0.001}}, ...]'),
        InputField("tolerance", "容差", type="number", required=False, default=0.001),
    ]

    output_fields = [
        OutputField("element_balances", "元素平衡", type="object"),
        OutputField("closure_rate", "闭合率", type="number"),
        OutputField("passed", "是否通过", type="boolean"),
    ]

    def invoke(self, params: dict, context: Optional[InvocationContext] = None) -> ModelResult:
        inputs = params.get("input_streams", [])
        outputs = params.get("output_streams", [])
        tol = float(params.get("tolerance", 0.001))

        if not inputs or not outputs:
            return ModelResult(success=False, error="输入和输出物流不能为空", error_code="INVALID_INPUT")

        # 计算各元素总输入和总输出质量
        input_masses: Dict[str, float] = {}
        output_masses: Dict[str, float] = {}

        total_in_mass = 0
        for stream in inputs:
            mass = float(stream.get("mass", 0))
            total_in_mass += mass
            for elem, frac in stream.get("elements", {}).items():
                input_masses[elem] = input_masses.get(elem, 0) + mass * float(frac)

        total_out_mass = 0
        for stream in outputs:
            mass = float(stream.get("mass", 0))
            total_out_mass += mass
            for elem, frac in stream.get("elements", {}).items():
                output_masses[elem] = output_masses.get(elem, 0) + mass * float(frac)

        # 逐个元素计算残差
        all_elements = set(input_masses.keys()) | set(output_masses.keys())
        balances = {}
        max_residual = 0
        for elem in sorted(all_elements):
            inp = input_masses.get(elem, 0)
            out = output_masses.get(elem, 0)
            residual = inp - out
            max_residual = max(max_residual, abs(residual))
            balances[elem] = {
                "input": round(inp, 4),
                "output": round(out, 4),
                "residual": round(residual, 4),
                "closure": round(1 - abs(residual) / (inp if inp else 1), 6),
            }

        mass_closure = 1 - abs(total_in_mass - total_out_mass) / (total_in_mass if total_in_mass else 1)
        passed = max_residual <= tol

        return ModelResult(
            success=True,
            result={
                "element_balances": balances,
                "total_input_mass": round(total_in_mass, 4),
                "total_output_mass": round(total_out_mass, 4),
                "mass_closure_rate": round(mass_closure, 6),
                "max_element_residual": round(max_residual, 6),
                "passed": passed,
            },
            boundary_check=BoundaryCheck(
                passed=passed,
                warnings=[] if passed else [
                    BoundaryWarning(field="mass_balance", level="warning",
                                    message=f"最大元素残差 {max_residual:.6f} 超出容差 {tol}")
                ],
            ),
        )
