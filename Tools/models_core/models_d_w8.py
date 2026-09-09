"""P1-W8 transparent BOF decarburization, furnace-gas and oxygen-audit tools."""

from __future__ import annotations

import math
from typing import Optional

from .base import BaseModelTool, BoundaryCheck, BoundaryWarning, InputField, ModelResult, OutputField
from .repositories.reference_repository import RepositoryError, atomic_weights


SCENARIO = "冶金工艺、物料与热平衡"
R_J_PER_KMOL_K = 8314.46261815324
NORMAL_TEMPERATURE_K = 273.15
NORMAL_PRESSURE_PA = 101325.0

OXYGEN_COMPONENT_MAP_SCHEMA = {
    "type": "object",
    "minProperties": 1,
    "propertyNames": {"type": "string", "minLength": 1},
    "additionalProperties": {"type": "number", "minimum": 0},
}

OPTIONAL_OXYGEN_COMPONENT_MAP_SCHEMA = {
    "type": "object",
    "propertyNames": {"type": "string", "minLength": 1},
    "additionalProperties": {"type": "number", "minimum": 0},
}

EXECUTION_ID_MAP_SCHEMA = {
    "type": "object",
    "propertyNames": {"type": "string", "minLength": 1},
    "additionalProperties": {"type": "string", "pattern": "^EXEC-"},
}


def rel(kind: str, target: str, description: str) -> dict:
    return {"type": kind, "target": target, "description": description}


def fail(message: str, code: str = "INVALID_INPUT") -> ModelResult:
    return ModelResult(False, error=message, error_code=code)


def finite(value, label: str, *, minimum: Optional[float] = None,
           maximum: Optional[float] = None):
    if isinstance(value, bool):
        return None, f"{label}必须是数值"
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None, f"{label}必须是数值"
    if not math.isfinite(parsed):
        return None, f"{label}必须是有限数值"
    if minimum is not None and parsed < minimum:
        return None, f"{label}不能小于{minimum:g}"
    if maximum is not None and parsed > maximum:
        return None, f"{label}不能大于{maximum:g}"
    return parsed, None


def nonnegative_mapping(raw, label: str, *, allow_empty: bool = False):
    if raw is None and allow_empty:
        return {}, None
    if not isinstance(raw, dict) or (not raw and not allow_empty):
        return None, f"{label}必须是{'对象' if allow_empty else '非空对象'}"
    parsed = {}
    for key, value in raw.items():
        if not isinstance(key, str) or not key.strip():
            return None, f"{label}的分项名称必须是非空字符串"
        number, error = finite(value, f"{label}.{key}", minimum=0)
        if error:
            return None, error
        parsed[key.strip()] = number
    return parsed, None


SEGMENT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "name": {"type": "string", "description": "唯一分段名称"},
        "duration_s": {"type": "number", "exclusiveMinimum": 0, "description": "分段时长；单位: s"},
        "oxygen_flow_kmol_s": {"type": "number", "minimum": 0, "description": "实供氧流量；单位: kmol O2/s"},
        "decarburization_oxygen_efficiency": {"type": "number", "minimum": 0, "maximum": 1, "description": "分配给脱碳的供氧比例；单位: 1"},
        "kinetic_rate_limit_kg_s": {"type": "number", "exclusiveMinimum": 0, "description": "可选动力学脱碳上限；单位: kg C/s"},
    },
    "required": ["name", "duration_s", "oxygen_flow_kmol_s", "decarburization_oxygen_efficiency"],
}


class D007_DecarburizationRate(BaseModelTool):
    model_id, name, version = "D007", "脱碳速率模型", "1.0.0"
    tool_name = "metallurgy_integrate_bof_decarburization_rate"
    scenario, priority = SCENARIO, "P1"
    status = qualification_status = "qualified"
    count_eligible = True
    model_type = "确定性分段约束积分"
    data_requirement = "REFERENCE_DATA_REQUIRED"
    data_access_mode = "database_repository"
    required_dataset_ids = ["DS_IUPAC_AW_2021"]
    database_tables = ["metallurgy_v2.element_reference"]
    description = (
        "按显式分段供氧、脱碳氧效率和可选动力学上限积分BOF碳量轨迹，"
        "逐段返回供氧控制/动力学控制状态；不内置工厂标定系数。"
    )
    applicable_boundary = (
        "零维完全混合、段内参数恒定且浴池仅因碳逸出而减重；CO/CO2去向比例全程恒定。"
        "枪位、乳化和炉气测量必须先由外部已验证模型转换为显式效率或速率上限。"
    )
    formula_reference = (
        "r_C,O2=F_O2*eta*M_C/[0.5(1-f_CO2)+f_CO2]；"
        "r_C=min(r_C,O2,r_C,kinetic,m_C_remaining/dt)；逐段显式质量守恒积分"
    )
    data_source = ["IUPAC atomic weights 2021", "ISIJ impact-zone decarburization control model"]
    source_version = "bof-decarburization-explicit-constraint-integrator-v1; IUPAC-2021"
    source_records = [
        {"source_id": "ISIJ-2011-51-1102", "name": "Comprehensive Model of Oxygen Steelmaking Part 3: Decarburization in Impact Zone", "version": "2011", "url": "https://doi.org/10.2355/isijinternational.51.1102"},
        {"source_id": "IUPAC-AW-2021", "name": "IUPAC standard atomic weights", "version": "2021 snapshot"},
    ]
    required_data = ["C原子量数据库记录", "显式分段供氧量与效率", "显式参数来源与版本"]
    failure_modes = ["分段为空、名称重复或结构错误", "分段时长/供氧/效率/动力学上限非法", "初始碳或金属质量非法", "C原子量数据库不可用", "碳去向比例越界"]
    independent_validation = ["纯C氧化计量独立复算", "每段实际速率等于供氧上限、动力学上限和剩余碳上限的最小值", "总碳移除量等于逐段积分和", "供氧分配等于脱碳耗氧与未利用分配氧之和"]
    dependencies = ["A003", "A007", "D001"]
    relations = [
        rel("uses_data_of", "A003", "复用同一IUPAC C原子量数据库记录"),
        rel("overlaps_with", "A007", "A007给出通用氧当量，D007增加时间分段和双上限积分"),
        rel("consumes_output_from", "D001", "D001供氧需求可用于检查D007分段供氧方案"),
        rel("upstream_of", "D015", "逐段carbon_removed_kmol可直接生成CO/CO2炉气"),
        rel("upstream_of", "D016", "逐段脱碳耗氧可作为有用耗氧分项"),
    ]
    input_fields = [
        InputField("initial_metal_mass_kg", "初始金属浴质量", "number", unit="kg", min_value=1e-12),
        InputField("initial_carbon_mass_fraction", "初始碳质量分数", "number", unit="1", min_value=0, max_value=0.1),
        InputField("segments", "脱碳分段", "array", items=SEGMENT_SCHEMA, min_items=1, max_items=200),
        InputField("carbon_to_co2_fraction", "碳最终生成CO2的摩尔比例", "number", unit="1", min_value=0, max_value=1),
        InputField("parameter_source", "分段参数来源", "string", description="炉次测量、文献拟合或批准模型的可审计来源"),
        InputField("parameter_version", "分段参数版本", "string", description="来源对应的固定版本/日期/配置号"),
    ]
    output_fields = [
        OutputField("time_history", "分段碳量轨迹", "array", "time:s; carbon:kg/kmol; oxygen:kmol O2; rate:kg C/s"),
        OutputField("initial_carbon_mass_kg", "初始碳质量", "number", "kg C"),
        OutputField("total_carbon_removed_kg", "总脱碳量", "number", "kg C"),
        OutputField("total_carbon_removed_kmol", "总脱碳量", "number", "kmol C"),
        OutputField("final_carbon_mass_kg", "终点碳质量", "number", "kg C"),
        OutputField("final_carbon_mass_fraction", "终点碳质量分数", "number", "1"),
        OutputField("final_metal_mass_kg", "终点金属浴质量", "number", "kg"),
        OutputField("total_oxygen_supplied_kmol", "总实供氧", "number", "kmol O2"),
        OutputField("total_oxygen_allocated_to_decarburization_kmol", "分配给脱碳的氧", "number", "kmol O2"),
        OutputField("total_oxygen_consumed_by_decarburization_kmol", "脱碳实际耗氧", "number", "kmol O2"),
        OutputField("unutilized_allocated_oxygen_kmol", "未用于脱碳的已分配氧", "number", "kmol O2"),
        OutputField("carbon_mass_balance_residual_kg", "碳质量守恒残差", "number", "kg C"),
        OutputField("oxygen_allocation_residual_kmol", "分配氧守恒残差", "number", "kmol O2"),
        OutputField("parameter_source", "参数来源", "string"),
        OutputField("parameter_version", "参数版本", "string"),
    ]
    validation_rules = [
        {"rule": "explicit_piecewise_constant_segments", "field": "segments"},
        {"rule": "no_hidden_calibration_parameters", "fields": ["parameter_source", "parameter_version"]},
        {"rule": "carbon_and_allocated_oxygen_conservation"},
    ]
    _COMMON = {
        "initial_metal_mass_kg": 1000,
        "initial_carbon_mass_fraction": 0.04,
        "carbon_to_co2_fraction": 0,
        "parameter_source": "qualification fixture based on explicit measured inputs",
        "parameter_version": "P1-W8-v1",
    }
    qualification_cases = [
        {"id": "D007-N1", "kind": "normal", "input": {**_COMMON, "segments": [{"name": "oxygen_limited", "duration_s": 10, "oxygen_flow_kmol_s": 0.1, "decarburization_oxygen_efficiency": 1}]}},
        {"id": "D007-N2", "kind": "normal", "input": {**_COMMON, "segments": [{"name": "kinetic_limited", "duration_s": 10, "oxygen_flow_kmol_s": 0.1, "decarburization_oxygen_efficiency": 1, "kinetic_rate_limit_kg_s": 0.5}]}},
        {"id": "D007-N3", "kind": "normal", "input": {**_COMMON, "carbon_to_co2_fraction": 0.25, "segments": [{"name": "stage_1", "duration_s": 5, "oxygen_flow_kmol_s": 0.08, "decarburization_oxygen_efficiency": 0.8}, {"name": "stage_2", "duration_s": 8, "oxygen_flow_kmol_s": 0.04, "decarburization_oxygen_efficiency": 0.6, "kinetic_rate_limit_kg_s": 0.3}]}},
        {"id": "D007-B1", "kind": "boundary", "input": {**_COMMON, "segments": [{"name": "zero_oxygen", "duration_s": 10, "oxygen_flow_kmol_s": 0, "decarburization_oxygen_efficiency": 0}]}},
        {"id": "D007-F1", "kind": "failure", "input": {**_COMMON, "segments": [{"name": "bad", "duration_s": 10, "oxygen_flow_kmol_s": 0.1, "decarburization_oxygen_efficiency": 1.1}]}},
    ]
    data_qualification_cases = [{"id": "D007-DATA-C", "input": qualification_cases[0]["input"]}]

    @staticmethod
    def _segments(raw):
        if not isinstance(raw, list) or not raw:
            return None, "segments必须是非空数组"
        if len(raw) > 200:
            return None, "segments不能超过200段"
        allowed = set(SEGMENT_SCHEMA["properties"])
        parsed, names = [], set()
        for index, item in enumerate(raw):
            if not isinstance(item, dict):
                return None, f"segments[{index}]必须是对象"
            unknown = set(item) - allowed
            if unknown:
                return None, f"segments[{index}]包含未声明字段: {', '.join(sorted(unknown))}"
            name = item.get("name")
            normalized_name = name.strip() if isinstance(name, str) else ""
            if not normalized_name or normalized_name in names:
                return None, f"segments[{index}].name必须是唯一非空字符串"
            names.add(normalized_name)
            duration, error = finite(item.get("duration_s"), f"segments[{index}].duration_s", minimum=1e-12)
            if error:
                return None, error
            oxygen, error = finite(item.get("oxygen_flow_kmol_s"), f"segments[{index}].oxygen_flow_kmol_s", minimum=0)
            if error:
                return None, error
            efficiency, error = finite(item.get("decarburization_oxygen_efficiency"), f"segments[{index}].decarburization_oxygen_efficiency", minimum=0, maximum=1)
            if error:
                return None, error
            cap = item.get("kinetic_rate_limit_kg_s")
            if cap is not None:
                cap, error = finite(cap, f"segments[{index}].kinetic_rate_limit_kg_s", minimum=1e-12)
                if error:
                    return None, error
            parsed.append({"name": normalized_name, "duration_s": duration, "oxygen_flow_kmol_s": oxygen,
                           "decarburization_oxygen_efficiency": efficiency,
                           "kinetic_rate_limit_kg_s": cap})
        return parsed, None

    def invoke(self, params, context=None):
        segments, error = self._segments(params["segments"])
        if error:
            return fail(error)
        parameter_source = params["parameter_source"].strip()
        parameter_version = params["parameter_version"].strip()
        if not parameter_source or not parameter_version:
            return fail("parameter_source与parameter_version必须是非空可审计字符串")
        try:
            weights, provenance = atomic_weights({"C"})
        except RepositoryError as exc:
            return fail(str(exc), exc.error_code)
        carbon_weight = weights["C"]
        initial_metal = float(params["initial_metal_mass_kg"])
        initial_fraction = float(params["initial_carbon_mass_fraction"])
        co2_fraction = float(params["carbon_to_co2_fraction"])
        oxygen_ratio = 0.5 * (1.0 - co2_fraction) + co2_fraction
        initial_carbon = initial_metal * initial_fraction
        remaining_carbon = initial_carbon
        remaining_metal = initial_metal
        time_s = 0.0
        supplied_total = allocated_total = consumed_total = 0.0
        history, warnings = [], []
        for segment in segments:
            duration = segment["duration_s"]
            supplied = segment["oxygen_flow_kmol_s"] * duration
            allocated = supplied * segment["decarburization_oxygen_efficiency"]
            oxygen_limited_rate = (
                segment["oxygen_flow_kmol_s"] * segment["decarburization_oxygen_efficiency"]
                * carbon_weight / oxygen_ratio
            )
            candidates = [("oxygen_supply", oxygen_limited_rate),
                          ("remaining_carbon", remaining_carbon / duration)]
            if segment["kinetic_rate_limit_kg_s"] is not None:
                candidates.append(("kinetic", segment["kinetic_rate_limit_kg_s"]))
            controlling_mode, actual_rate = min(candidates, key=lambda item: item[1])
            removed_kg = min(remaining_carbon, actual_rate * duration)
            removed_kmol = removed_kg / carbon_weight
            consumed = removed_kmol * oxygen_ratio
            if consumed > allocated + 1e-10:
                return fail("数值误差导致脱碳耗氧超过分配氧", "NUMERICAL_ERROR")
            start_carbon = remaining_carbon
            start_fraction = remaining_carbon / remaining_metal
            remaining_carbon -= removed_kg
            remaining_metal -= removed_kg
            if remaining_metal <= 0:
                return fail("脱碳后金属浴质量非正", "OUT_OF_DOMAIN")
            if removed_kg <= 1e-15:
                warnings.append(BoundaryWarning("segments", f"分段{segment['name']}没有发生脱碳"))
            if controlling_mode == "remaining_carbon" and removed_kg > 0:
                warnings.append(BoundaryWarning("segments", f"分段{segment['name']}达到碳耗尽边界"))
            history.append({
                "name": segment["name"], "start_time_s": time_s, "end_time_s": time_s + duration,
                "duration_s": duration, "start_carbon_mass_kg": start_carbon,
                "end_carbon_mass_kg": remaining_carbon, "start_carbon_mass_fraction": start_fraction,
                "end_carbon_mass_fraction": remaining_carbon / remaining_metal,
                "oxygen_supplied_kmol": supplied, "oxygen_allocated_to_decarburization_kmol": allocated,
                "oxygen_consumed_by_decarburization_kmol": consumed,
                "unutilized_allocated_oxygen_kmol": max(0.0, allocated - consumed),
                "oxygen_limited_rate_kg_s": oxygen_limited_rate,
                "kinetic_rate_limit_kg_s": segment["kinetic_rate_limit_kg_s"],
                "actual_decarburization_rate_kg_s": removed_kg / duration,
                "carbon_removed_kg": removed_kg, "carbon_removed_kmol": removed_kmol,
                "controlling_mode": controlling_mode,
            })
            time_s += duration
            supplied_total += supplied
            allocated_total += allocated
            consumed_total += consumed
        removed_total = initial_carbon - remaining_carbon
        unutilized = max(0.0, allocated_total - consumed_total)
        carbon_residual = initial_carbon - removed_total - remaining_carbon
        oxygen_residual = allocated_total - consumed_total - unutilized
        return ModelResult(True, result={
            "time_history": history,
            "initial_carbon_mass_kg": initial_carbon,
            "total_carbon_removed_kg": removed_total,
            "total_carbon_removed_kmol": removed_total / carbon_weight,
            "final_carbon_mass_kg": remaining_carbon,
            "final_carbon_mass_fraction": remaining_carbon / remaining_metal,
            "final_metal_mass_kg": remaining_metal,
            "total_oxygen_supplied_kmol": supplied_total,
            "total_oxygen_allocated_to_decarburization_kmol": allocated_total,
            "total_oxygen_consumed_by_decarburization_kmol": consumed_total,
            "unutilized_allocated_oxygen_kmol": unutilized,
            "carbon_mass_balance_residual_kg": carbon_residual,
            "oxygen_allocation_residual_kmol": oxygen_residual,
            "parameter_source": parameter_source,
            "parameter_version": parameter_version,
        }, boundary_check=BoundaryCheck(not warnings, warnings), provenance=provenance)


GAS_SEGMENT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "name": {"type": "string"},
        "duration_s": {"type": "number", "exclusiveMinimum": 0, "description": "单位: s"},
        "carbon_removed_kmol": {"type": "number", "minimum": 0, "description": "单位: kmol C"},
        "carbon_to_co2_fraction": {"type": "number", "minimum": 0, "maximum": 1, "description": "单位: 1"},
    },
    "required": ["name", "duration_s", "carbon_removed_kmol", "carbon_to_co2_fraction"],
}


class D015_FurnaceGasGeneration(BaseModelTool):
    model_id, name, version = "D015", "炉气生成量", "1.0.0"
    tool_name = "metallurgy_calculate_bof_furnace_gas"
    scenario, priority = SCENARIO, "P2"
    status = qualification_status = "qualified"
    count_eligible = True
    data_requirement, data_access_mode = "FORMULA_ONLY", "none"
    model_type = "确定性化学计量/理想气体"
    description = "把分段脱碳量及CO2比例换算为CO/CO2炉气量、实际/标准体积和平均流量曲线。"
    applicable_boundary = "只覆盖碳氧化产生的理想CO/CO2干气；不含喷溅、蒸汽、漏风、粉尘和二次燃烧区混入气体。"
    formula_reference = "n_CO=(1-f)n_C; n_CO2=f*n_C; n_O2=0.5*n_CO+n_CO2; V=nRT/P"
    data_source = ["Carbon oxidation stoichiometry", "SI ideal-gas law and CODATA molar gas constant"]
    source_version = "bof-carbon-gas-stoichiometry-v1; CODATA-2018-SI"
    source_records = [
        {"source_id": "C-OXIDATION-STOICHIOMETRY", "name": "Carbon-to-CO/CO2 stoichiometry", "version": "v1"},
        {"source_id": "CODATA-R-2018", "name": "CODATA molar gas constant", "version": "2018 SI", "url": "https://physics.nist.gov/cgi-bin/cuu/Value?r"},
    ]
    failure_modes = ["分段为空、重复或字段非法", "温度/压力非正", "碳量或CO2比例越界", "上游执行ID格式非法"]
    independent_validation = ["纯CO与纯CO2两个化学计量极限", "CO加CO2的碳kmol等于输入碳kmol", "体积与温度成正比且与压力成反比", "分段平均流量乘时长恢复分段体积"]
    dependencies = ["D007", "A007"]
    relations = [
        rel("consumes_output_from", "D007", "接收D007逐段carbon_removed_kmol并保留可选执行ID"),
        rel("overlaps_with", "A007", "采用相同C到O2当量，但增加炉气组成和体积曲线"),
        rel("upstream_of", "D016", "碳氧化耗氧可作为D016有用耗氧分项"),
    ]
    input_fields = [
        InputField("decarburization_segments", "脱碳分段", "array", items=GAS_SEGMENT_SCHEMA, min_items=1, max_items=200),
        InputField("gas_temperature_k", "炉气温度", "number", unit="K", min_value=1e-12),
        InputField("gas_pressure_pa", "炉气绝对压力", "number", unit="Pa", min_value=1e-12),
        InputField("upstream_execution_id", "D007上游执行ID", "string", required=False, description="可选；若提供必须为EXEC-开头"),
    ]
    output_fields = [
        OutputField("segment_gas_curve", "分段炉气曲线", "array", "time:s; amount:kmol; volume:m3/Nm3; flow:m3/s"),
        OutputField("total_co_kmol", "CO总量", "number", "kmol CO"),
        OutputField("total_co2_kmol", "CO2总量", "number", "kmol CO2"),
        OutputField("total_dry_gas_kmol", "CO+CO2总量", "number", "kmol gas"),
        OutputField("co_mole_fraction", "CO摩尔分数", "number", "1"),
        OutputField("co2_mole_fraction", "CO2摩尔分数", "number", "1"),
        OutputField("total_actual_volume_m3", "工况总体积", "number", "m³"),
        OutputField("total_normal_volume_m3", "标准总体积", "number", "Nm³"),
        OutputField("total_oxygen_consumption_kmol", "碳氧化耗氧", "number", "kmol O2"),
        OutputField("total_duration_s", "总时长", "number", "s"),
        OutputField("average_actual_flow_m3_s", "平均工况流量", "number", "m³/s"),
        OutputField("carbon_stoichiometry_residual_kmol", "碳计量残差", "number", "kmol C"),
        OutputField("upstream_execution_id", "D007上游执行ID", "string"),
    ]
    validation_rules = [{"rule": "carbon_to_co_co2_stoichiometry"}, {"rule": "ideal_gas_absolute_temperature_and_pressure"}]
    _COMMON = {"gas_temperature_k": 1873.15, "gas_pressure_pa": 101325}
    qualification_cases = [
        {"id": "D015-N1", "kind": "normal", "input": {**_COMMON, "decarburization_segments": [{"name": "co", "duration_s": 10, "carbon_removed_kmol": 1, "carbon_to_co2_fraction": 0}]}},
        {"id": "D015-N2", "kind": "normal", "input": {**_COMMON, "decarburization_segments": [{"name": "co2", "duration_s": 5, "carbon_removed_kmol": 2, "carbon_to_co2_fraction": 1}]}},
        {"id": "D015-N3", "kind": "normal", "input": {**_COMMON, "decarburization_segments": [{"name": "s1", "duration_s": 4, "carbon_removed_kmol": 1, "carbon_to_co2_fraction": 0.2}, {"name": "s2", "duration_s": 6, "carbon_removed_kmol": 3, "carbon_to_co2_fraction": 0.4}], "upstream_execution_id": "EXEC-000000000000D007"}},
        {"id": "D015-B1", "kind": "boundary", "input": {**_COMMON, "decarburization_segments": [{"name": "zero", "duration_s": 10, "carbon_removed_kmol": 0, "carbon_to_co2_fraction": 0}]}},
        {"id": "D015-F1", "kind": "failure", "input": {**_COMMON, "decarburization_segments": [{"name": "bad", "duration_s": 0, "carbon_removed_kmol": 1, "carbon_to_co2_fraction": 0}]}},
    ]

    def invoke(self, params, context=None):
        raw = params["decarburization_segments"]
        if not isinstance(raw, list) or not raw or len(raw) > 200:
            return fail("decarburization_segments必须包含1到200段")
        upstream = params.get("upstream_execution_id", "")
        if upstream and not upstream.startswith("EXEC-"):
            return fail("upstream_execution_id必须为D007返回的EXEC-执行编号")
        temperature = float(params["gas_temperature_k"])
        pressure = float(params["gas_pressure_pa"])
        actual_m3_per_kmol = R_J_PER_KMOL_K * temperature / pressure
        normal_m3_per_kmol = R_J_PER_KMOL_K * NORMAL_TEMPERATURE_K / NORMAL_PRESSURE_PA
        curve, names, warnings = [], set(), []
        time_s = total_c = total_co = total_co2 = total_o2 = 0.0
        allowed = set(GAS_SEGMENT_SCHEMA["properties"])
        for index, item in enumerate(raw):
            if not isinstance(item, dict) or set(item) - allowed:
                return fail(f"decarburization_segments[{index}]结构非法")
            name = item.get("name")
            normalized_name = name.strip() if isinstance(name, str) else ""
            if not normalized_name or normalized_name in names:
                return fail(f"decarburization_segments[{index}].name必须是唯一非空字符串")
            names.add(normalized_name)
            duration, error = finite(item.get("duration_s"), f"decarburization_segments[{index}].duration_s", minimum=1e-12)
            if error: return fail(error)
            carbon, error = finite(item.get("carbon_removed_kmol"), f"decarburization_segments[{index}].carbon_removed_kmol", minimum=0)
            if error: return fail(error)
            fraction, error = finite(item.get("carbon_to_co2_fraction"), f"decarburization_segments[{index}].carbon_to_co2_fraction", minimum=0, maximum=1)
            if error: return fail(error)
            co2 = carbon * fraction
            co = carbon - co2
            gas = co + co2
            oxygen = 0.5 * co + co2
            actual_volume = gas * actual_m3_per_kmol
            normal_volume = gas * normal_m3_per_kmol
            if carbon == 0:
                warnings.append(BoundaryWarning("decarburization_segments", f"分段{normalized_name}为零脱碳/零炉气边界"))
            curve.append({
                "name": normalized_name, "start_time_s": time_s, "end_time_s": time_s + duration,
                "duration_s": duration, "carbon_removed_kmol": carbon, "co_kmol": co,
                "co2_kmol": co2, "dry_gas_kmol": gas, "oxygen_consumption_kmol": oxygen,
                "actual_volume_m3": actual_volume, "normal_volume_m3": normal_volume,
                "average_actual_flow_m3_s": actual_volume / duration,
                "average_normal_flow_nm3_s": normal_volume / duration,
            })
            time_s += duration; total_c += carbon; total_co += co; total_co2 += co2; total_o2 += oxygen
        total_gas = total_co + total_co2
        actual_volume = total_gas * actual_m3_per_kmol
        normal_volume = total_gas * normal_m3_per_kmol
        return ModelResult(True, result={
            "segment_gas_curve": curve, "total_co_kmol": total_co, "total_co2_kmol": total_co2,
            "total_dry_gas_kmol": total_gas,
            "co_mole_fraction": total_co / total_gas if total_gas else 0.0,
            "co2_mole_fraction": total_co2 / total_gas if total_gas else 0.0,
            "total_actual_volume_m3": actual_volume, "total_normal_volume_m3": normal_volume,
            "total_oxygen_consumption_kmol": total_o2, "total_duration_s": time_s,
            "average_actual_flow_m3_s": actual_volume / time_s,
            "carbon_stoichiometry_residual_kmol": total_c - total_gas,
            "upstream_execution_id": upstream,
        }, boundary_check=BoundaryCheck(not warnings, warnings))


class D016_OxygenUtilization(BaseModelTool):
    model_id, name, version = "D016", "氧利用率计算", "1.0.0"
    tool_name = "metallurgy_audit_bof_oxygen_utilization"
    scenario, priority = SCENARIO, "P2"
    status = qualification_status = "qualified"
    count_eligible = True
    data_requirement, data_access_mode = "FORMULA_ONLY", "none"
    description = "按实供氧、有用耗氧分项和已测损失分项审计BOF氧利用率、未计量损失和氧量闭合。"
    applicable_boundary = "所有分项必须采用同一kmol O2基准；同一反应耗氧只能出现一次，工具不自动合并D001与D015的重复碳耗氧。"
    formula_reference = "eta_O2=sum(n_useful)/n_actual; n_unaccounted=n_actual-sum(n_useful)-sum(n_measured_loss)"
    data_source = ["Conservation of oxygen amount", "Explicit BOF oxygen accounting"]
    source_version = "bof-oxygen-utilization-audit-v1"
    source_records = [{"source_id": "O2-AMOUNT-CONSERVATION", "name": "Conservation of supplied oxygen amount", "version": "v1"}]
    failure_modes = ["实供氧非正", "分项对象为空、名称或数值非法", "有用耗氧超过实供氧", "有用耗氧与已测损失之和超过实供氧"]
    independent_validation = ["利用率等于有用耗氧分项和除以实供氧", "所有分项整体缩放时利用率不变", "实供氧等于有用耗氧、已测损失和未计量损失之和", "分项占比之和在有用耗氧非零时等于1"]
    dependencies = ["D001", "D007", "D015"]
    relations = [
        rel("consumes_output_from", "D001", "D001分元素理论耗氧可作为有用耗氧分项"),
        rel("consumes_output_from", "D007", "D007脱碳实际耗氧可作为carbon分项"),
        rel("consumes_output_from", "D015", "D015炉气碳氧化耗氧可作为carbon分项，但不得与D007同一耗氧重复"),
    ]
    input_fields = [
        InputField("actual_oxygen_supply_kmol", "实供氧量", "number", unit="kmol O2", min_value=1e-12),
        InputField("useful_oxygen_components_kmol_o2", "有用耗氧分项", "object", unit="kmol O2", description="非空的分项名到非负耗氧量映射；例如carbon、silicon、manganese、phosphorus、iron", json_schema=OXYGEN_COMPONENT_MAP_SCHEMA),
        InputField("measured_loss_components_kmol_o2", "已测损失分项", "object", required=False, unit="kmol O2", description="可选的分项名到非负损失氧映射；例如offgas_O2、leak_or_purge", json_schema=OPTIONAL_OXYGEN_COMPONENT_MAP_SCHEMA),
        InputField("source_execution_ids", "分项上游执行ID", "object", required=False, description="可选；键与耗氧分项对应，值必须以EXEC-开头", json_schema=EXECUTION_ID_MAP_SCHEMA),
    ]
    output_fields = [
        OutputField("useful_oxygen_components_kmol_o2", "规范化有用耗氧分项", "object", "kmol O2"),
        OutputField("useful_component_shares", "有用耗氧分项占比", "object", "1"),
        OutputField("measured_loss_components_kmol_o2", "规范化已测损失", "object", "kmol O2"),
        OutputField("actual_oxygen_supply_kmol", "实供氧量", "number", "kmol O2"),
        OutputField("total_useful_oxygen_kmol", "有用耗氧", "number", "kmol O2"),
        OutputField("oxygen_utilization_fraction", "氧利用率", "number", "1"),
        OutputField("oxygen_utilization_percent", "氧利用率", "number", "%"),
        OutputField("measured_loss_oxygen_kmol", "已测损失氧", "number", "kmol O2"),
        OutputField("unaccounted_oxygen_kmol", "未计量氧", "number", "kmol O2"),
        OutputField("total_loss_oxygen_kmol", "总损失氧", "number", "kmol O2"),
        OutputField("oxygen_closure_residual_kmol", "氧量闭合残差", "number", "kmol O2"),
        OutputField("source_execution_ids", "分项上游执行ID", "object"),
    ]
    validation_rules = [{"rule": "common_kmol_o2_basis"}, {"rule": "useful_plus_measured_loss_not_above_actual"}, {"rule": "no_duplicate_reaction_path"}]
    qualification_cases = [
        {"id": "D016-N1", "kind": "normal", "input": {"actual_oxygen_supply_kmol": 100, "useful_oxygen_components_kmol_o2": {"carbon": 60, "silicon": 20}}},
        {"id": "D016-N2", "kind": "normal", "input": {"actual_oxygen_supply_kmol": 100, "useful_oxygen_components_kmol_o2": {"carbon": 70}, "measured_loss_components_kmol_o2": {"offgas_O2": 10}}},
        {"id": "D016-N3", "kind": "normal", "input": {"actual_oxygen_supply_kmol": 50, "useful_oxygen_components_kmol_o2": {"carbon": 20, "iron": 10, "phosphorus": 5}, "source_execution_ids": {"carbon": "EXEC-000000000000D007", "iron": "EXEC-000000000000D001"}}},
        {"id": "D016-B1", "kind": "boundary", "input": {"actual_oxygen_supply_kmol": 10, "useful_oxygen_components_kmol_o2": {"carbon": 0}}},
        {"id": "D016-F1", "kind": "failure", "input": {"actual_oxygen_supply_kmol": 10, "useful_oxygen_components_kmol_o2": {"carbon": 11}}},
    ]

    def invoke(self, params, context=None):
        useful, error = nonnegative_mapping(params["useful_oxygen_components_kmol_o2"], "useful_oxygen_components_kmol_o2")
        if error: return fail(error)
        losses, error = nonnegative_mapping(params.get("measured_loss_components_kmol_o2"), "measured_loss_components_kmol_o2", allow_empty=True)
        if error: return fail(error)
        source_ids = params.get("source_execution_ids") or {}
        if not isinstance(source_ids, dict):
            return fail("source_execution_ids必须是对象")
        for key, value in source_ids.items():
            if key not in useful and key not in losses:
                return fail(f"source_execution_ids.{key}没有对应耗氧或损失分项")
            if not isinstance(value, str) or not value.startswith("EXEC-"):
                return fail(f"source_execution_ids.{key}必须为EXEC-执行ID")
        actual = float(params["actual_oxygen_supply_kmol"])
        total_useful = math.fsum(useful.values())
        measured_loss = math.fsum(losses.values())
        tolerance = 1e-10 * max(actual, 1.0)
        if total_useful > actual + tolerance:
            return fail("有用耗氧总量超过实供氧", "OUT_OF_DOMAIN")
        if total_useful + measured_loss > actual + tolerance:
            return fail("有用耗氧与已测损失之和超过实供氧", "OUT_OF_DOMAIN")
        unaccounted = max(0.0, actual - total_useful - measured_loss)
        total_loss = measured_loss + unaccounted
        residual = actual - total_useful - total_loss
        warnings = []
        if total_useful == 0:
            warnings.append(BoundaryWarning("useful_oxygen_components_kmol_o2", "有用耗氧为零，利用率位于零边界"))
        if unaccounted > 0.2 * actual:
            warnings.append(BoundaryWarning("unaccounted_oxygen_kmol", "未计量氧超过实供氧的20%，应复核边界与分项完整性"))
        shares = {key: value / total_useful if total_useful else 0.0 for key, value in useful.items()}
        return ModelResult(True, result={
            "useful_oxygen_components_kmol_o2": useful, "useful_component_shares": shares,
            "measured_loss_components_kmol_o2": losses, "actual_oxygen_supply_kmol": actual,
            "total_useful_oxygen_kmol": total_useful,
            "oxygen_utilization_fraction": total_useful / actual,
            "oxygen_utilization_percent": total_useful / actual * 100.0,
            "measured_loss_oxygen_kmol": measured_loss, "unaccounted_oxygen_kmol": unaccounted,
            "total_loss_oxygen_kmol": total_loss, "oxygen_closure_residual_kmol": residual,
            "source_execution_ids": dict(source_ids),
        }, boundary_check=BoundaryCheck(not warnings, warnings))
