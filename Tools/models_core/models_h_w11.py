"""P1-W11 additive ladle-refining tools; all existing implementations stay frozen."""

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


class W11LadleTool(BaseModelTool):
    scenario = "炉外精炼与洁净钢"
    priority = "P1"
    status = "qualified"
    qualification_status = "qualified"
    count_eligible = True
    data_requirement = "FORMULA_ONLY"
    data_access_mode = "none"


class H002_LadleDesulfurizationEquilibrium(W11LadleTool):
    model_id, name, version = "H002", "钢包脱硫平衡与脱除量", "1.0.0"
    tool_name = "metallurgy_calculate_ladle_desulfurization_equilibrium"
    description = "在调用方显式给定有效硫分配比时，对封闭钢-渣两相做硫质量守恒，计算平衡硫含量、转移量和脱硫率。"
    applicable_boundary = (
        "封闭钢-渣两相、两相质量恒定、给定Ls=wS,slag/wS,metal；硫质量分数0到0.1。"
        "本工具不预测Ls，不处理动力学、气化、耐材吸硫、夹渣或连续加料。"
    )
    data_source = ["Caller-supplied sulfur partition ratio", "Closed two-phase sulfur mass balance"]
    source_version = "ladle-sulfur-partition-balance-v1"
    formula_reference = (
        "S_total=M_m*w_m0+M_s*w_s0; w_m_eq=S_total/(M_m+Ls*M_s); "
        "w_s_eq=Ls*w_m_eq; transferred=M_s*(w_s_eq-w_s0)"
    )
    source_records = [{
        "source_id": "STEEL-SLAG-SULFUR-BALANCE",
        "name": "Sulfur partition-ratio definition and closed steel-slag solute balance",
        "version": "deterministic mass-balance v1",
    }]
    failure_modes = [
        "钢水或渣质量非正", "初始硫分数超出0到0.1", "初始钢中硫为0导致脱硫率无定义",
        "硫分配比非正", "平衡硫分数超出物理/工具适用域", "硫质量或分配比回代不闭合",
    ]
    independent_validation = [
        "初末总硫质量守恒", "终态wS,slag/wS,metal回代等于Ls", "增大Ls不提高平衡钢中硫",
        "增大渣量不提高平衡钢中硫", "初始两相已满足Ls时硫净转移为0",
    ]
    dependencies = ["A005"]
    relations = [
        rel("depends_on", "A005", "钢水和渣的总硫物流可先由A005统一质量基准"),
        rel("overlaps", "D011", "D011筛选转炉渣硫分配；本工具消费显式Ls执行钢包两相质量衡算"),
        rel("complements", "H003", "H003估算宏观混合时间，本工具给混合充分后的两相平衡极限"),
    ]
    input_fields = [
        InputField("steel_mass_kg", "钢水质量", "number", unit="kg", min_value=1e-300),
        InputField("slag_mass_kg", "渣质量", "number", unit="kg", min_value=1e-300),
        InputField("initial_steel_sulfur_mass_fraction", "初始钢中硫质量分数", "number", unit="1", min_value=0, max_value=0.1),
        InputField("initial_slag_sulfur_mass_fraction", "初始渣中硫质量分数", "number", unit="1", min_value=0, max_value=0.1),
        InputField("sulfur_partition_ratio", "硫分配比Ls", "number", unit="1", min_value=1e-300),
    ]
    output_fields = [
        OutputField("equilibrium_steel_sulfur_mass_fraction", "平衡钢中硫质量分数", "number", "1"),
        OutputField("equilibrium_slag_sulfur_mass_fraction", "平衡渣中硫质量分数", "number", "1"),
        OutputField("initial_total_sulfur_mass_kg", "初始总硫质量", "number", "kg"),
        OutputField("final_steel_sulfur_mass_kg", "终态钢中硫质量", "number", "kg"),
        OutputField("final_slag_sulfur_mass_kg", "终态渣中硫质量", "number", "kg"),
        OutputField("sulfur_transferred_to_slag_kg", "由钢向渣净转移硫质量", "number", "kg"),
        OutputField("desulfurization_fraction", "钢水脱硫率", "number", "1"),
        OutputField("transfer_direction", "硫净转移方向", "string"),
        OutputField("total_sulfur_balance_residual_kg", "总硫衡算残差", "number", "kg"),
        OutputField("partition_ratio_residual", "分配比回代残差", "number", "1"),
        OutputField("model_version", "模型版本", "string"),
    ]
    validation_rules = [
        {"rule": "positive_phase_masses_and_partition_ratio"},
        {"rule": "sulfur_mass_fraction_between_zero_and_0.1"},
        {"rule": "closed_two_phase_sulfur_balance"},
        {"rule": "equilibrium_partition_ratio_identity"},
    ]
    qualification_cases = [
        {"id": "H002-N1", "kind": "normal", "input": {"steel_mass_kg": 100000, "slag_mass_kg": 1500, "initial_steel_sulfur_mass_fraction": 0.0002, "initial_slag_sulfur_mass_fraction": 0, "sulfur_partition_ratio": 100}},
        {"id": "H002-N2", "kind": "normal", "input": {"steel_mass_kg": 80000, "slag_mass_kg": 2000, "initial_steel_sulfur_mass_fraction": 0.0003, "initial_slag_sulfur_mass_fraction": 0.002, "sulfur_partition_ratio": 80}},
        {"id": "H002-N3", "kind": "normal", "input": {"steel_mass_kg": 120000, "slag_mass_kg": 1000, "initial_steel_sulfur_mass_fraction": 0.0001, "initial_slag_sulfur_mass_fraction": 0, "sulfur_partition_ratio": 200}},
        {"id": "H002-B1", "kind": "boundary", "input": {"steel_mass_kg": 100000, "slag_mass_kg": 1000, "initial_steel_sulfur_mass_fraction": 0.0002, "initial_slag_sulfur_mass_fraction": 0.002, "sulfur_partition_ratio": 10}},
        {"id": "H002-F1", "kind": "failure", "input": {"steel_mass_kg": 100000, "slag_mass_kg": 0, "initial_steel_sulfur_mass_fraction": 0.0002, "initial_slag_sulfur_mass_fraction": 0, "sulfur_partition_ratio": 100}},
        {"id": "H002-F2", "kind": "failure", "input": {"steel_mass_kg": 100000, "slag_mass_kg": 1000, "initial_steel_sulfur_mass_fraction": 0, "initial_slag_sulfur_mass_fraction": 0.002, "sulfur_partition_ratio": 10}},
    ]

    def invoke(self, params: dict, context=None) -> ModelResult:
        specifications = (
            ("steel_mass_kg", 0, None, True),
            ("slag_mass_kg", 0, None, True),
            ("initial_steel_sulfur_mass_fraction", 0, 0.1, False),
            ("initial_slag_sulfur_mass_fraction", 0, 0.1, False),
            ("sulfur_partition_ratio", 0, None, True),
        )
        parsed = {}
        for key, minimum, maximum, strict in specifications:
            value, error = finite(params.get(key), key, minimum=minimum, maximum=maximum, strict_minimum=strict)
            if error:
                return fail(error)
            parsed[key] = value
        initial_steel_fraction = parsed["initial_steel_sulfur_mass_fraction"]
        if initial_steel_fraction == 0:
            return fail("initial_steel_sulfur_mass_fraction必须大于0以定义脱硫率", "OUT_OF_DOMAIN")
        steel_mass = parsed["steel_mass_kg"]
        slag_mass = parsed["slag_mass_kg"]
        initial_slag_fraction = parsed["initial_slag_sulfur_mass_fraction"]
        partition_ratio = parsed["sulfur_partition_ratio"]
        initial_total = steel_mass * initial_steel_fraction + slag_mass * initial_slag_fraction
        equilibrium_steel_fraction = initial_total / (steel_mass + partition_ratio * slag_mass)
        equilibrium_slag_fraction = partition_ratio * equilibrium_steel_fraction
        if not 0 <= equilibrium_steel_fraction <= 0.1 or not 0 <= equilibrium_slag_fraction <= 0.1:
            return fail("计算的平衡硫质量分数超出[0,0.1]适用域", "OUT_OF_DOMAIN")
        final_steel_sulfur = steel_mass * equilibrium_steel_fraction
        final_slag_sulfur = slag_mass * equilibrium_slag_fraction
        transferred = final_slag_sulfur - slag_mass * initial_slag_fraction
        desulfurization = (steel_mass * initial_steel_fraction - final_steel_sulfur) / (steel_mass * initial_steel_fraction)
        total_residual = initial_total - final_steel_sulfur - final_slag_sulfur
        partition_residual = equilibrium_slag_fraction / equilibrium_steel_fraction - partition_ratio
        tolerance = 1e-12 * max(1.0, initial_total)
        if abs(total_residual) > tolerance or abs(partition_residual) > 1e-10 * max(1.0, partition_ratio):
            return fail("硫质量或分配比回代未数值闭合", "NUMERICAL_ERROR")
        transfer_tolerance = 1e-12 * max(1.0, initial_total)
        warnings = []
        if abs(transferred) <= transfer_tolerance:
            direction = "equilibrium_no_net_transfer"
            warnings.append(BoundaryWarning("sulfur_partition_ratio", "初始两相已满足给定分配比，净硫转移为0"))
        elif transferred > 0:
            direction = "metal_to_slag"
        else:
            direction = "slag_to_metal"
            warnings.append(BoundaryWarning("sulfur_partition_ratio", "给定分配比导致硫由渣返回钢水，结果不是脱硫"))
        return ModelResult(True, result={
            "equilibrium_steel_sulfur_mass_fraction": equilibrium_steel_fraction,
            "equilibrium_slag_sulfur_mass_fraction": equilibrium_slag_fraction,
            "initial_total_sulfur_mass_kg": initial_total,
            "final_steel_sulfur_mass_kg": final_steel_sulfur,
            "final_slag_sulfur_mass_kg": final_slag_sulfur,
            "sulfur_transferred_to_slag_kg": transferred,
            "desulfurization_fraction": desulfurization,
            "transfer_direction": direction,
            "total_sulfur_balance_residual_kg": total_residual,
            "partition_ratio_residual": partition_residual,
            "model_version": "ladle-sulfur-partition-balance-v1",
        }, boundary_check=BoundaryCheck(not warnings, warnings))


class H003_ArgonStirringMixingTime(W11LadleTool):
    model_id, name, version = "H003", "氩气搅拌均混时间", "1.0.0"
    tool_name = "metallurgy_calculate_ladle_argon_mixing_time"
    description = "由钢水量、温度、氩气标况流量、吹入深度和表面压力计算比搅拌功，并用Nakanishi关联式估算95%均混时间。"
    applicable_boundary = (
        "钢包底吹氩工程筛选：1500–2000 K、0.1–400 t、0.01–1000 Nm3/min、0.5–6 m、"
        "表面压力50–200 kPa、1–8个喷嘴，且计算比搅拌功1–2000 W/t。"
        "不代表CFD局部死区、厚渣层多相效应或在线控制设定。"
    )
    data_source = ["Nakanishi-Fujii mixing-time correlation", "Explicit gas expansion work expression"]
    source_version = "nakanishi-gas-stirring-v1"
    formula_reference = (
        "epsilon=(6.18*Qg*T/M)*ln[1+h/(1.46e-5*P0)] W/t; "
        "tau_single=800*epsilon^-0.4 s; tau=tau_single*N^(1/3)"
    )
    source_records = [
        {
            "source_id": "NAKANISHI-FUJII-MIXING",
            "name": "Nakanishi-Fujii complete-mixing correlation for metallurgical vessels",
            "version": "tau=800 epsilon^-0.4; epsilon in W/t",
            "url": "https://www.jstage.jst.go.jp/article/isijinternational/60/12/60_ISIJINT-2020-186/_pdf",
        },
        {
            "source_id": "GAS-STIRRING-POWER-EXPRESSION",
            "name": "Gas expansion stirring-power expression with SI input contract",
            "version": "6.18 coefficient, P0 in Pa",
            "url": "https://patents.google.com/patent/JP6628014B1/en",
        },
    ]
    failure_modes = [
        "温度、钢水量、流量、吹入深度或压力超输入域", "喷嘴数量不是1至8的整数",
        "对数功率项非法", "计算比搅拌功超出1至2000 W/t", "混合时间不是正有限值",
    ]
    independent_validation = [
        "比搅拌功按气体膨胀功公式直接复算", "混合时间按800*epsilon^-0.4回代",
        "流量或温度增大时混合时间降低", "钢水量或喷嘴数增大时混合时间增加",
    ]
    dependencies = []
    relations = [
        rel("complements", "C011", "C011给流动相似准则，本工具给钢包宏观均混时间尺度"),
        rel("complements", "H002", "本工具估算达到均混所需时间，H002给充分混合后的钢渣硫平衡极限"),
        rel("complements", "T003", "可将均混时间与T003热松弛时间比较，但本工具不求钢包温降"),
    ]
    input_fields = [
        InputField("steel_temperature_k", "钢水温度", "number", unit="K", min_value=1500, max_value=2000),
        InputField("steel_mass_t", "钢水质量", "number", unit="t", min_value=0.1, max_value=400),
        InputField("argon_flow_nm3_min", "氩气标况流量", "number", unit="Nm3/min", min_value=0.01, max_value=1000),
        InputField("injection_depth_m", "吹入深度", "number", unit="m", min_value=0.5, max_value=6),
        InputField("surface_pressure_pa", "钢液表面压力", "number", unit="Pa", min_value=50000, max_value=200000),
        InputField("plug_count", "喷嘴或透气砖数量", "number", unit="1", min_value=1, max_value=8),
    ]
    output_fields = [
        OutputField("specific_stirring_power_w_t", "比搅拌功", "number", "W/t"),
        OutputField("single_plug_mixing_time_s", "单喷嘴基础均混时间", "number", "s"),
        OutputField("plug_count_factor", "喷嘴数量修正系数", "number", "1"),
        OutputField("mixing_time_s", "95%均混时间", "number", "s"),
        OutputField("argon_flow_per_tonne_nm3_min_t", "吨钢氩气流量", "number", "Nm3/(min*t)"),
        OutputField("log_pressure_expansion_factor", "压力膨胀对数因子", "number", "1"),
        OutputField("model_version", "模型版本", "string"),
    ]
    validation_rules = [
        {"rule": "fixed_temperature_mass_flow_depth_pressure_ranges"},
        {"rule": "integer_plug_count_between_one_and_eight"},
        {"rule": "specific_stirring_power_between_one_and_2000_W_per_t"},
        {"rule": "mixing_time_formula_identity"},
    ]
    qualification_cases = [
        {"id": "H003-N1", "kind": "normal", "input": {"steel_temperature_k": 1873, "steel_mass_t": 100, "argon_flow_nm3_min": 1, "injection_depth_m": 3, "surface_pressure_pa": 101325, "plug_count": 1}},
        {"id": "H003-N2", "kind": "normal", "input": {"steel_temperature_k": 1800, "steel_mass_t": 150, "argon_flow_nm3_min": 2, "injection_depth_m": 3.5, "surface_pressure_pa": 101325, "plug_count": 1}},
        {"id": "H003-N3", "kind": "normal", "input": {"steel_temperature_k": 1900, "steel_mass_t": 80, "argon_flow_nm3_min": 0.8, "injection_depth_m": 2.5, "surface_pressure_pa": 100000, "plug_count": 1}},
        {"id": "H003-B1", "kind": "boundary", "input": {"steel_temperature_k": 1873, "steel_mass_t": 100, "argon_flow_nm3_min": 1, "injection_depth_m": 3, "surface_pressure_pa": 101325, "plug_count": 8}},
        {"id": "H003-F1", "kind": "failure", "input": {"steel_temperature_k": 1400, "steel_mass_t": 100, "argon_flow_nm3_min": 1, "injection_depth_m": 3, "surface_pressure_pa": 101325, "plug_count": 1}},
        {"id": "H003-F2", "kind": "failure", "input": {"steel_temperature_k": 1873, "steel_mass_t": 0.1, "argon_flow_nm3_min": 1000, "injection_depth_m": 6, "surface_pressure_pa": 50000, "plug_count": 1}},
    ]

    def invoke(self, params: dict, context=None) -> ModelResult:
        specifications = (
            ("steel_temperature_k", 1500, 2000),
            ("steel_mass_t", 0.1, 400),
            ("argon_flow_nm3_min", 0.01, 1000),
            ("injection_depth_m", 0.5, 6),
            ("surface_pressure_pa", 50000, 200000),
            ("plug_count", 1, 8),
        )
        parsed = {}
        for key, minimum, maximum in specifications:
            value, error = finite(params.get(key), key, minimum=minimum, maximum=maximum)
            if error:
                return fail(error, "OUT_OF_DOMAIN")
            parsed[key] = value
        if not parsed["plug_count"].is_integer():
            return fail("plug_count必须是1至8的整数")
        plug_count = int(parsed["plug_count"])
        pressure_factor_argument = 1.0 + parsed["injection_depth_m"] / (1.46e-5 * parsed["surface_pressure_pa"])
        if pressure_factor_argument <= 1.0:
            return fail("气体膨胀功对数参数必须大于1", "NUMERICAL_ERROR")
        log_factor = math.log(pressure_factor_argument)
        specific_power = (
            6.18 * parsed["argon_flow_nm3_min"] * parsed["steel_temperature_k"]
            / parsed["steel_mass_t"] * log_factor
        )
        if not 1.0 <= specific_power <= 2000.0:
            return fail(f"计算比搅拌功{specific_power:.6g} W/t超出[1,2000]适用域", "OUT_OF_DOMAIN")
        single_plug_time = 800.0 * specific_power ** -0.4
        plug_factor = plug_count ** (1.0 / 3.0)
        mixing_time = single_plug_time * plug_factor
        if not math.isfinite(mixing_time) or mixing_time <= 0:
            return fail("计算混合时间不是正有限值", "NUMERICAL_ERROR")
        warnings = []
        if plug_count > 1:
            warnings.append(BoundaryWarning("plug_count", "多喷嘴使用N^(1/3)经验修正，不解析喷嘴位置和流量分配"))
        if specific_power < 5 or specific_power > 1000:
            warnings.append(BoundaryWarning("specific_stirring_power_w_t", "比搅拌功接近工程筛选域边缘，结果不宜外推"))
        return ModelResult(True, result={
            "specific_stirring_power_w_t": specific_power,
            "single_plug_mixing_time_s": single_plug_time,
            "plug_count_factor": plug_factor,
            "mixing_time_s": mixing_time,
            "argon_flow_per_tonne_nm3_min_t": parsed["argon_flow_nm3_min"] / parsed["steel_mass_t"],
            "log_pressure_expansion_factor": log_factor,
            "model_version": "nakanishi-gas-stirring-v1",
        }, boundary_check=BoundaryCheck(not warnings, warnings))
