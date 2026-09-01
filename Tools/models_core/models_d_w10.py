"""P1-W10 additive process tool; existing D-series implementations stay frozen."""

from __future__ import annotations

import math
from typing import Any, Optional

from .base import BaseModelTool, BoundaryCheck, BoundaryWarning, InputField, ModelResult, OutputField


def rel(kind: str, target: str, description: str) -> dict[str, str]:
    return {"type": kind, "target": target, "description": description}


def fail(message: str, code: str = "INVALID_INPUT") -> ModelResult:
    return ModelResult(False, error=message, error_code=code)


def finite(value: Any, label: str, *, minimum: Optional[float] = None,
           maximum: Optional[float] = None, strict_minimum: bool = False):
    if isinstance(value, bool):
        return None, f"{label}必须是数值"
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None, f"{label}必须是数值"
    if not math.isfinite(parsed):
        return None, f"{label}必须是有限数值"
    if minimum is not None and (parsed <= minimum if strict_minimum else parsed < minimum):
        sign = "大于" if strict_minimum else "不小于"
        return None, f"{label}必须{sign}{minimum:g}"
    if maximum is not None and parsed > maximum:
        return None, f"{label}不能大于{maximum:g}"
    return parsed, None


class D023_SingleAlloyAddition(BaseModelTool):
    model_id, name, version = "D023", "单种合金补加量", "1.0.0"
    scenario, priority = "冶金工艺与物料衡算", "P1"
    tool_name = "metallurgy_calculate_single_alloy_addition"
    status = qualification_status = "qualified"
    count_eligible = True
    data_requirement = "FORMULA_ONLY"
    data_access_mode = "none"
    description = "按初始钢液量、元素初/目标质量分数、合金品位和元素收得率，计算单种合金理论补加量并复算元素闭合。"
    applicable_boundary = (
        "单一目标元素、单一合金、完全混合、品位与收得率显式给定且恒定；不处理多元素耦合、氧化损失机理、"
        "扒渣/出钢质量变化。可选择目标分数以初始钢液质量为基准或以加入合金后的最终钢液质量为基准。"
    )
    data_source = ["Single-solute alloy addition mass balance"]
    source_version = "single-alloy-mass-balance-v1"
    formula_reference = (
        "fixed_initial: m=M(xt-x0)/(eta*a); addition_in_final: "
        "m=M(xt-x0)/(eta*a-xt); element_residual=m_element,final-target_basis*xt"
    )
    source_records = [
        {"source_id": "ALLOY-ADDITION-BALANCE", "name": "Deterministic single-solute alloy addition mass balance", "version": "v1"},
    ]
    failure_modes = ["钢液质量、合金品位或收得率非正", "质量分数超出0到1", "目标低于初始值", "最终质量基准下eta*a不大于目标分数", "输入不是有限数值"]
    independent_validation = ["初始元素质量加回收元素质量等于最终元素质量", "按所选分母复算的最终分数等于目标分数", "目标等于初始值时补加量为0", "固定初始质量基准下补加量与品位和收得率乘积成反比"]
    dependencies = ["A004"]
    relations = [
        rel("depends_on", "A004", "合金品位和钢液成分应采用A004归一化后的质量分数"),
        rel("overlaps", "D021", "都进行装入物料衡算；D023只解单一合金补加，D021处理转炉装料总体平衡"),
        rel("complements", "D014", "D014量化铁损，本工具只处理给定元素收得率下的合金补加"),
    ]
    input_fields = [
        InputField("bath_mass_kg", "初始钢液质量", "number", unit="kg", min_value=1e-300),
        InputField("initial_mass_fraction", "初始元素质量分数", "number", unit="1", min_value=0, max_value=1),
        InputField("target_mass_fraction", "目标元素质量分数", "number", unit="1", min_value=0, max_value=1),
        InputField("alloy_element_mass_fraction", "合金中目标元素质量分数", "number", unit="1", min_value=1e-300, max_value=1),
        InputField("element_recovery_fraction", "目标元素收得率", "number", unit="1", min_value=1e-300, max_value=1),
        InputField("mass_basis", "目标分数质量基准", "select", required=False, default="addition_in_final_bath_mass", enum=["fixed_initial_bath_mass", "addition_in_final_bath_mass"], description="固定初始钢液质量，或计入合金加入量后的最终钢液质量"),
    ]
    output_fields = [
        OutputField("alloy_addition_kg", "理论合金补加量", "number", "kg"),
        OutputField("predicted_mass_fraction", "闭合复算元素质量分数", "number", "1"),
        OutputField("initial_element_mass_kg", "初始元素质量", "number", "kg"),
        OutputField("recovered_element_mass_kg", "由合金回收的元素质量", "number", "kg"),
        OutputField("final_element_mass_kg", "最终元素质量", "number", "kg"),
        OutputField("final_bath_mass_kg", "计入合金后的最终钢液质量", "number", "kg"),
        OutputField("mass_balance_residual_kg", "目标元素闭合残差", "number", "kg"),
        OutputField("mass_basis", "采用的质量基准", "string"),
        OutputField("formula_used", "采用的解析式", "string"),
        OutputField("model_version", "模型版本", "string"),
    ]
    validation_rules = [
        {"rule": "fractions_within_zero_and_one"},
        {"rule": "target_not_below_initial"},
        {"rule": "positive_denominator_for_selected_mass_basis"},
        {"rule": "element_mass_balance_closure"},
    ]
    qualification_cases = [
        {"id": "D023-N1", "kind": "normal", "input": {"bath_mass_kg": 100000, "initial_mass_fraction": 0.002, "target_mass_fraction": 0.005, "alloy_element_mass_fraction": 0.75, "element_recovery_fraction": 0.9, "mass_basis": "fixed_initial_bath_mass"}},
        {"id": "D023-N2", "kind": "normal", "input": {"bath_mass_kg": 100000, "initial_mass_fraction": 0.002, "target_mass_fraction": 0.005, "alloy_element_mass_fraction": 0.75, "element_recovery_fraction": 0.9, "mass_basis": "addition_in_final_bath_mass"}},
        {"id": "D023-N3", "kind": "normal", "input": {"bath_mass_kg": 150000, "initial_mass_fraction": 0.0005, "target_mass_fraction": 0.0012, "alloy_element_mass_fraction": 0.2, "element_recovery_fraction": 0.8}},
        {"id": "D023-B1", "kind": "boundary", "input": {"bath_mass_kg": 100000, "initial_mass_fraction": 0.005, "target_mass_fraction": 0.005, "alloy_element_mass_fraction": 0.75, "element_recovery_fraction": 0.9}},
        {"id": "D023-B2", "kind": "boundary", "input": {"bath_mass_kg": 100000, "initial_mass_fraction": 0.8, "target_mass_fraction": 0.8, "alloy_element_mass_fraction": 0.5, "element_recovery_fraction": 1, "mass_basis": "addition_in_final_bath_mass"}},
        {"id": "D023-F1", "kind": "failure", "input": {"bath_mass_kg": 100000, "initial_mass_fraction": 0.01, "target_mass_fraction": 0.005, "alloy_element_mass_fraction": 0.75, "element_recovery_fraction": 0.9}},
        {"id": "D023-F2", "kind": "failure", "input": {"bath_mass_kg": 100000, "initial_mass_fraction": 0.1, "target_mass_fraction": 0.6, "alloy_element_mass_fraction": 0.5, "element_recovery_fraction": 1, "mass_basis": "addition_in_final_bath_mass"}},
    ]

    def invoke(self, params: dict, context=None) -> ModelResult:
        specifications = (
            ("bath_mass_kg", 0, None, True),
            ("initial_mass_fraction", 0, 1, False),
            ("target_mass_fraction", 0, 1, False),
            ("alloy_element_mass_fraction", 0, 1, True),
            ("element_recovery_fraction", 0, 1, True),
        )
        parsed = {}
        for key, minimum, maximum, strict in specifications:
            value, error = finite(params.get(key), key, minimum=minimum, maximum=maximum, strict_minimum=strict)
            if error:
                return fail(error)
            parsed[key] = value
        mass_basis = params.get("mass_basis", "addition_in_final_bath_mass")
        if mass_basis not in {"fixed_initial_bath_mass", "addition_in_final_bath_mass"}:
            return fail("mass_basis必须是fixed_initial_bath_mass或addition_in_final_bath_mass")
        initial_fraction = parsed["initial_mass_fraction"]
        target_fraction = parsed["target_mass_fraction"]
        if target_fraction < initial_fraction:
            return fail("目标质量分数低于初始质量分数，本工具不处理稀释或脱除", "OUT_OF_DOMAIN")

        bath_mass = parsed["bath_mass_kg"]
        alloy_fraction = parsed["alloy_element_mass_fraction"]
        recovery = parsed["element_recovery_fraction"]
        numerator = bath_mass * (target_fraction - initial_fraction)
        if mass_basis == "fixed_initial_bath_mass":
            denominator = recovery * alloy_fraction
            formula_used = "m=M*(xt-x0)/(eta*a)"
        else:
            denominator = recovery * alloy_fraction - target_fraction
            formula_used = "m=M*(xt-x0)/(eta*a-xt)"
            if denominator <= 0 and numerator > 0:
                return fail("最终钢液质量基准要求element_recovery_fraction*alloy_element_mass_fraction大于target_mass_fraction", "OUT_OF_DOMAIN")
        addition = 0.0 if numerator == 0 else numerator / denominator
        initial_element = bath_mass * initial_fraction
        recovered_element = addition * alloy_fraction * recovery
        final_element = initial_element + recovered_element
        final_bath = bath_mass + addition
        target_basis_mass = bath_mass if mass_basis == "fixed_initial_bath_mass" else final_bath
        predicted_fraction = final_element / target_basis_mass
        residual = final_element - target_fraction * target_basis_mass
        if abs(residual) > 1e-9 * max(1.0, abs(final_element)):
            return fail("目标元素物料衡算未数值闭合", "NUMERICAL_ERROR")
        warnings = []
        if target_fraction == initial_fraction:
            warnings.append(BoundaryWarning("target_mass_fraction", "目标等于初始分数，理论补加量为0"))
        return ModelResult(True, result={
            "alloy_addition_kg": addition,
            "predicted_mass_fraction": predicted_fraction,
            "initial_element_mass_kg": initial_element,
            "recovered_element_mass_kg": recovered_element,
            "final_element_mass_kg": final_element,
            "final_bath_mass_kg": final_bath,
            "mass_balance_residual_kg": residual,
            "mass_basis": mass_basis,
            "formula_used": formula_used,
            "model_version": "single-alloy-mass-balance-v1",
        }, boundary_check=BoundaryCheck(not warnings, warnings))
