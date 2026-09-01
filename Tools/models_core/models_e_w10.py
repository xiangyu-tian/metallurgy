"""P1-W10 additive equilibrium-path tool; existing E-series implementations stay frozen."""

from __future__ import annotations

import math
from typing import Any, Optional

from .base import BaseModelTool, BoundaryCheck, BoundaryWarning, InputField, ModelResult, OutputField


R_J_MOL_K = 8.31446261815324
STANDARD_PRESSURE_PA = 100000.0
_QUALIFICATION_TEMPERATURE_K = 1000.0
_QUALIFICATION_DG_CO_KJ_MOL = -400.2
_QUALIFICATION_DG_CO2_KJ_MOL = -396.4
_QUALIFICATION_K = math.exp(-(
    _QUALIFICATION_DG_CO_KJ_MOL - _QUALIFICATION_DG_CO2_KJ_MOL
) * 1000 / (R_J_MOL_K * _QUALIFICATION_TEMPERATURE_K))
_QUALIFICATION_S = _QUALIFICATION_K
_QUALIFICATION_RATIO = (_QUALIFICATION_S + math.sqrt(_QUALIFICATION_S ** 2 + 4 * _QUALIFICATION_S)) / 2
_QUALIFICATION_Y_CO = _QUALIFICATION_RATIO / (1 + _QUALIFICATION_RATIO)
_QUALIFICATION_Y_CO2 = 1 / (1 + _QUALIFICATION_RATIO)


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


class E021_BoudouardEquilibriumDrivingForce(BaseModelTool):
    model_id, name, version = "E021", "Boudouard反应平衡驱动力", "1.0.0"
    scenario, priority = "高炉低碳", "P1"
    tool_name = "metallurgy_calculate_boudouard_equilibrium_driving_force"
    status = qualification_status = "qualified"
    count_eligible = True
    data_requirement = "FORMULA_ONLY"
    data_access_mode = "none"
    description = "组合两次B008标准反应Gibbs能执行结果，计算C+CO2→2CO的标准/实际驱动力、反应商和固定COx分压下的平衡CO/CO2比。"
    applicable_boundary = (
        "理想气体、气体逸度以分压近似、碳活度显式给定；温度及两项标准Gibbs能必须来自同一标准态和同一温度的B008执行。"
        "不校验外部执行记录内容，不处理非理想气体逸度系数或碳相转变。"
    )
    data_source = ["B008 execution outputs", "Boudouard equilibrium thermodynamic identity"]
    source_version = "boudouard-composed-gibbs-v1; R-CODATA-2018"
    formula_reference = (
        "DG°_B=DG°(2C+O2->2CO)-DG°(C+O2->CO2); K=exp(-DG°/RT); "
        "Q=(pCO/p°)^2/[aC(pCO2/p°)]; DG=DG°+RTlnQ; r_eq=[S+sqrt(S^2+4S)]/2, S=K*aC*p°/pCOx"
    )
    source_records = [
        {"source_id": "BOUDOUARD-THERMODYNAMIC-CYCLE", "name": "Hess-cycle construction and ideal-gas reaction quotient for C+CO2=2CO", "version": "v1"},
        {"source_id": "CODATA-R-2018", "name": "Molar gas constant", "version": "2018 SI"},
    ]
    failure_modes = [
        "温度、压力、摩尔分数或碳活度非正",
        "CO与CO2摩尔分数和大于1",
        "两项上游执行编号不是EXEC-格式",
        "标准Gibbs组合导致指数溢出或平衡比不能有限表示",
        "两项B008结果并非同温同标准态（调用方责任）",
    ]
    independent_validation = [
        "标准Boudouard Gibbs能按Hess定律由两个B008结果相减",
        "实际驱动力满足DG=RT*ln(Q/K)",
        "输出平衡CO/CO2比代回Q后等于K",
        "Q/K小于、等于、大于1时分别判为正向、平衡、逆向",
    ]
    dependencies = ["B008"]
    relations = [
        rel("depends_on", "B008", "必须显式传入同温度下两个B008执行结果及执行编号"),
        rel("overlaps", "B009", "都由标准Gibbs能计算K；E021进一步加入实际气相组成和碳活度"),
        rel("complements", "E011", "E011计算炉顶气利用率，本工具判断给定CO/CO2状态相对Boudouard平衡的位置"),
    ]
    input_fields = [
        InputField("temperature_k", "反应温度", "number", unit="K", min_value=1e-300),
        InputField("total_pressure_pa", "气相总压", "number", unit="Pa", min_value=1e-300),
        InputField("co_mole_fraction", "CO摩尔分数", "number", unit="1", min_value=1e-300, max_value=1),
        InputField("co2_mole_fraction", "CO2摩尔分数", "number", unit="1", min_value=1e-300, max_value=1),
        InputField("carbon_activity", "碳活度", "number", unit="1", min_value=1e-300),
        InputField("co_formation_reaction_gibbs_kj_mol", "2C+O2到2CO的标准反应Gibbs能", "number", unit="kJ/mol-reaction", description="同温度B008输出delta_G"),
        InputField("co2_formation_reaction_gibbs_kj_mol", "C+O2到CO2的标准反应Gibbs能", "number", unit="kJ/mol-reaction", description="同温度B008输出delta_G"),
        InputField("co_formation_execution_id", "CO生成反应B008执行编号", "string", description="必须以EXEC-开头"),
        InputField("co2_formation_execution_id", "CO2生成反应B008执行编号", "string", description="必须以EXEC-开头"),
        InputField("standard_pressure_pa", "标准压力", "number", required=False, default=STANDARD_PRESSURE_PA, unit="Pa", min_value=1e-300),
        InputField("equilibrium_relative_tolerance", "平衡判定相对容差", "number", required=False, default=1e-9, unit="1", min_value=0, max_value=0.1),
    ]
    output_fields = [
        OutputField("standard_reaction_gibbs_kj_mol", "Boudouard标准反应Gibbs能", "number", "kJ/mol-reaction"),
        OutputField("actual_reaction_gibbs_kj_mol", "给定状态实际反应Gibbs能", "number", "kJ/mol-reaction"),
        OutputField("equilibrium_constant", "无量纲平衡常数", "number", "1"),
        OutputField("reaction_quotient", "无量纲反应商", "number", "1"),
        OutputField("quotient_to_equilibrium_ratio", "Q/K", "number", "1"),
        OutputField("direction", "热力学自发方向", "string"),
        OutputField("actual_co_to_co2_ratio", "实际CO/CO2摩尔比", "number", "1"),
        OutputField("equilibrium_co_to_co2_ratio", "固定COx分压下平衡CO/CO2比", "number", "1"),
        OutputField("co_partial_pressure_pa", "CO分压", "number", "Pa"),
        OutputField("co2_partial_pressure_pa", "CO2分压", "number", "Pa"),
        OutputField("co_plus_co2_partial_pressure_pa", "CO与CO2分压和", "number", "Pa"),
        OutputField("co_formation_execution_id", "CO生成反应B008执行编号", "string"),
        OutputField("co2_formation_execution_id", "CO2生成反应B008执行编号", "string"),
        OutputField("model_version", "模型版本", "string"),
    ]
    validation_rules = [
        {"rule": "positive_temperature_pressure_composition_and_activity"},
        {"rule": "co_plus_co2_fraction_not_above_one"},
        {"rule": "two_explicit_B008_execution_ids"},
        {"rule": "hess_cycle_and_reaction_quotient_identity"},
    ]
    _base_case = {
        "temperature_k": _QUALIFICATION_TEMPERATURE_K,
        "total_pressure_pa": STANDARD_PRESSURE_PA,
        "carbon_activity": 1,
        "co_formation_reaction_gibbs_kj_mol": _QUALIFICATION_DG_CO_KJ_MOL,
        "co2_formation_reaction_gibbs_kj_mol": _QUALIFICATION_DG_CO2_KJ_MOL,
        "co_formation_execution_id": "EXEC-B008-CO-QUALIFICATION",
        "co2_formation_execution_id": "EXEC-B008-CO2-QUALIFICATION",
    }
    qualification_cases = [
        {"id": "E021-N1", "kind": "normal", "input": {**_base_case, "co_mole_fraction": 0.6, "co2_mole_fraction": 0.4}},
        {"id": "E021-N2", "kind": "normal", "input": {**_base_case, "co_mole_fraction": 0.8, "co2_mole_fraction": 0.2}},
        {"id": "E021-N3", "kind": "normal", "input": {**_base_case, "total_pressure_pa": 200000, "carbon_activity": 0.8, "co_mole_fraction": 0.4, "co2_mole_fraction": 0.1}},
        {"id": "E021-B1", "kind": "boundary", "input": {**_base_case, "co_mole_fraction": _QUALIFICATION_Y_CO, "co2_mole_fraction": _QUALIFICATION_Y_CO2}},
        {"id": "E021-F1", "kind": "failure", "input": {**_base_case, "co_mole_fraction": 0.8, "co2_mole_fraction": 0.4}},
        {"id": "E021-F2", "kind": "failure", "input": {**_base_case, "co_mole_fraction": 0.6, "co2_mole_fraction": 0.4, "co_formation_execution_id": "B008-NO-TRACE"}},
    ]

    def invoke(self, params: dict, context=None) -> ModelResult:
        specifications = (
            ("temperature_k", 0, None, True),
            ("total_pressure_pa", 0, None, True),
            ("co_mole_fraction", 0, 1, True),
            ("co2_mole_fraction", 0, 1, True),
            ("carbon_activity", 0, None, True),
            ("co_formation_reaction_gibbs_kj_mol", None, None, False),
            ("co2_formation_reaction_gibbs_kj_mol", None, None, False),
            ("standard_pressure_pa", 0, None, True),
            ("equilibrium_relative_tolerance", 0, 0.1, False),
        )
        defaults = {"standard_pressure_pa": STANDARD_PRESSURE_PA, "equilibrium_relative_tolerance": 1e-9}
        parsed = {}
        for key, minimum, maximum, strict in specifications:
            value, error = finite(params.get(key, defaults.get(key)), key, minimum=minimum, maximum=maximum, strict_minimum=strict)
            if error:
                return fail(error)
            parsed[key] = value
        if parsed["co_mole_fraction"] + parsed["co2_mole_fraction"] > 1 + 1e-12:
            return fail("co_mole_fraction与co2_mole_fraction之和不能大于1", "OUT_OF_DOMAIN")
        execution_ids = {}
        for key in ("co_formation_execution_id", "co2_formation_execution_id"):
            value = params.get(key)
            if not isinstance(value, str) or not value.startswith("EXEC-") or len(value) <= 5:
                return fail(f"{key}必须是以EXEC-开头的非空执行编号")
            execution_ids[key] = value

        standard_gibbs = (
            parsed["co_formation_reaction_gibbs_kj_mol"]
            - parsed["co2_formation_reaction_gibbs_kj_mol"]
        )
        exponent = -standard_gibbs * 1000 / (R_J_MOL_K * parsed["temperature_k"])
        if exponent < -700 or exponent > 700:
            return fail("平衡常数指数超出可稳定表示范围[-700,700]", "NUMERICAL_ERROR")
        equilibrium_constant = math.exp(exponent)
        co_pressure = parsed["total_pressure_pa"] * parsed["co_mole_fraction"]
        co2_pressure = parsed["total_pressure_pa"] * parsed["co2_mole_fraction"]
        cox_pressure = co_pressure + co2_pressure
        reaction_quotient = (
            (co_pressure / parsed["standard_pressure_pa"]) ** 2
            / (parsed["carbon_activity"] * (co2_pressure / parsed["standard_pressure_pa"]))
        )
        ratio_to_equilibrium = reaction_quotient / equilibrium_constant
        actual_gibbs = standard_gibbs + R_J_MOL_K * parsed["temperature_k"] * math.log(reaction_quotient) / 1000
        tolerance = parsed["equilibrium_relative_tolerance"]
        if ratio_to_equilibrium < 1 - tolerance:
            direction = "forward_to_CO"
        elif ratio_to_equilibrium > 1 + tolerance:
            direction = "reverse_to_C_and_CO2"
        else:
            direction = "equilibrium"

        equilibrium_s = (
            equilibrium_constant * parsed["carbon_activity"] * parsed["standard_pressure_pa"] / cox_pressure
        )
        if not math.isfinite(equilibrium_s):
            return fail("平衡CO/CO2比中间量不能有限表示", "NUMERICAL_ERROR")
        if equilibrium_s > 1e150:
            equilibrium_ratio = equilibrium_s + 1.0
        else:
            equilibrium_ratio = (equilibrium_s + math.sqrt(equilibrium_s ** 2 + 4 * equilibrium_s)) / 2
        warnings = []
        if direction == "equilibrium":
            warnings.append(BoundaryWarning("reaction_quotient", "Q在指定相对容差内等于K，处于平衡边界"))
        return ModelResult(True, result={
            "standard_reaction_gibbs_kj_mol": standard_gibbs,
            "actual_reaction_gibbs_kj_mol": actual_gibbs,
            "equilibrium_constant": equilibrium_constant,
            "reaction_quotient": reaction_quotient,
            "quotient_to_equilibrium_ratio": ratio_to_equilibrium,
            "direction": direction,
            "actual_co_to_co2_ratio": parsed["co_mole_fraction"] / parsed["co2_mole_fraction"],
            "equilibrium_co_to_co2_ratio": equilibrium_ratio,
            "co_partial_pressure_pa": co_pressure,
            "co2_partial_pressure_pa": co2_pressure,
            "co_plus_co2_partial_pressure_pa": cox_pressure,
            "co_formation_execution_id": execution_ids["co_formation_execution_id"],
            "co2_formation_execution_id": execution_ids["co2_formation_execution_id"],
            "model_version": "boudouard-composed-gibbs-v1",
        }, boundary_check=BoundaryCheck(not warnings, warnings))
