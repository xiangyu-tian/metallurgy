"""P1-W16 executable F009/F011/F014/G003 deterministic tools."""

from __future__ import annotations

import math
from typing import Any

from .base import BaseModelTool, BoundaryCheck, BoundaryWarning, InputField, ModelResult, OutputField


def rel(kind: str, target: str, description: str) -> dict[str, str]:
    return {"type": kind, "target": target, "description": description}


def fail(message: str, code: str = "INVALID_INPUT") -> ModelResult:
    return ModelResult(False, error=message, error_code=code)


def finite(
    value: Any,
    label: str,
    *,
    minimum: float | None = None,
    maximum: float | None = None,
    strict_minimum: bool = False,
) -> tuple[float | None, str | None]:
    if isinstance(value, bool):
        return None, f"{label}必须是数值"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None, f"{label}必须是数值"
    if not math.isfinite(number):
        return None, f"{label}必须是有限数值"
    if minimum is not None and (number <= minimum if strict_minimum else number < minimum):
        return None, f"{label}必须{'大于' if strict_minimum else '不小于'}{minimum:g}"
    if maximum is not None and number > maximum:
        return None, f"{label}不能大于{maximum:g}"
    return number, None


def integer(value: Any, label: str, minimum: int, maximum: int) -> tuple[int | None, str | None]:
    if isinstance(value, bool) or not isinstance(value, int):
        return None, f"{label}必须是整数"
    if not minimum <= value <= maximum:
        return None, f"{label}必须在{minimum}到{maximum}之间"
    return value, None


class W16FormulaTool(BaseModelTool):
    priority = "P1"
    status = qualification_status = "qualified"
    count_eligible = True
    data_requirement = "FORMULA_ONLY"
    data_access_mode = "none"


ZONE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "name": {"type": "string"},
        "allocation_weight": {"type": "number", "exclusiveMinimum": 0},
        "target_heat_removal_kw": {"type": "number", "minimum": 0},
        "minimum_water_flow_m3_h": {"type": "number", "minimum": 0},
        "maximum_water_flow_m3_h": {"type": "number", "minimum": 0},
    },
    "required": [
        "name",
        "allocation_weight",
        "target_heat_removal_kw",
        "minimum_water_flow_m3_h",
        "maximum_water_flow_m3_h",
    ],
}


class F009_SecondaryCoolingZoneAllocation(W16FormulaTool):
    model_id, name, version = "F009", "二冷分区水量分配", "1.0.0"
    tool_name = "metallurgy_allocate_secondary_cooling_water"
    scenario = "凝固与连铸"
    model_type = "确定性有界比例投影/水侧显热校核"
    description = "在各二冷区显式最小和最大水量约束下分配给定总水量，并用水侧显热计算分区热容量和需求覆盖。"
    applicable_boundary = (
        "稳态离线配水；调用方显式给出总水量、分区权重、热需求和设备水量上下限。"
        "不读取喷嘴、阀门、测温或历史浇次，不进行反馈控制，也不向PLC下发设定。"
    )
    data_source = ["Bounded proportional allocation", "Cooling-water sensible heat balance"]
    source_version = "bounded-secondary-cooling-allocation-v1"
    formula_reference = (
        "V_i=clip(lambda*w_i,Vmin_i,Vmax_i), solve sum(V_i)=Vtotal; "
        "Q_i=V_i*rho_w*cp_w*(Tout-Tin)/3600"
    )
    source_records = [
        {
            "source_id": "JISRI-DYNAMIC-WATER-2008",
            "name": "Dynamic Water Modeling and Application of Billet Continuous Casting",
            "version": "DOI 10.1016/S1006-706X(08)60023-0",
            "url": "https://doi.org/10.1016/S1006-706X(08)60023-0",
        },
        {
            "source_id": "BOUNDED-PROPORTIONAL-PROJECTION",
            "name": "Deterministic capped proportional allocation",
            "version": "project-algorithm-v1",
        },
    ]
    failure_modes = [
        "分区少于2个、名称重复、权重非正或字段不完整",
        "任一分区最小水量大于最大水量",
        "总水量低于分区最小值之和或高于最大值之和",
        "水物性非正、出水温度不高于进水温度或投影未闭合",
        "把离线分配结果解释为现场温度反馈或阀门控制指令",
    ]
    independent_validation = [
        "无上下限激活时分区水量严格按权重成比例",
        "每个分区结果均位于显式上下限内且分区和等于总水量",
        "各区热容量由水质量流量乘比热和温升独立复算",
        "总量等于上下限之和时所有分区分别落在对应边界",
    ]
    dependencies = ["F008"]
    relations = [
        rel("consumes_output_from", "F008", "F008计算二冷总水量，F009把该总量分配到显式分区约束"),
        rel("accepts_output_from", "F005", "F005移热结果可形成各区target_heat_removal_kw，但F009不求温度场"),
        rel("accepts_output_from", "F007", "F007水侧热量可作为分区热需求校核输入"),
        rel("upstream_of", "F011", "F009水侧总热容量可作为F011的可用二冷热功率"),
    ]
    input_fields = [
        InputField("total_water_flow_m3_h", "二冷总水量", "number", unit="m3/h", min_value=0),
        InputField("zones", "二冷分区", "array", items=ZONE_SCHEMA, min_items=2, max_items=50),
        InputField("water_inlet_temperature_k", "进水温度", "number", unit="K", min_value=1e-12),
        InputField("water_outlet_temperature_k", "出水温度", "number", unit="K", min_value=1e-12),
        InputField("water_density_kg_m3", "水密度", "number", required=False, default=998.0, unit="kg/m3", min_value=1e-12),
        InputField("water_specific_heat_kj_kg_k", "水比热", "number", required=False, default=4.18, unit="kJ/(kg*K)", min_value=1e-12),
    ]
    output_fields = [
        OutputField("zone_results", "逐区分配与热容量", "array", "flow:m3/h; heat:kW; coverage:1"),
        OutputField("total_water_flow_m3_h", "给定总水量", "number", "m3/h"),
        OutputField("allocated_water_flow_m3_h", "分配水量合计", "number", "m3/h"),
        OutputField("water_flow_closure_residual_m3_h", "水量闭合残差", "number", "m3/h"),
        OutputField("total_heat_capacity_kw", "水侧总热容量", "number", "kW"),
        OutputField("total_target_heat_removal_kw", "目标移热合计", "number", "kW"),
        OutputField("overall_heat_coverage_fraction", "总热需求覆盖率", "number", "1", nullable=True),
        OutputField("water_temperature_rise_k", "水温升", "number", "K"),
        OutputField("active_minimum_count", "触发最小水量分区数", "number", "1"),
        OutputField("active_maximum_count", "触发最大水量分区数", "number", "1"),
        OutputField("calculation_method", "计算方法", "string"),
    ]
    validation_rules = [
        {"rule": "two_to_fifty_unique_zones_with_positive_weights"},
        {"rule": "total_flow_within_sum_of_zone_bounds"},
        {"rule": "bounded_proportional_projection_closes_total_flow"},
        {"rule": "positive_water_properties_and_temperature_rise"},
    ]
    _BASE_ZONES = [
        {"name": "zone_1", "allocation_weight": 1, "target_heat_removal_kw": 1000, "minimum_water_flow_m3_h": 0, "maximum_water_flow_m3_h": 100},
        {"name": "zone_2", "allocation_weight": 2, "target_heat_removal_kw": 2000, "minimum_water_flow_m3_h": 0, "maximum_water_flow_m3_h": 100},
        {"name": "zone_3", "allocation_weight": 3, "target_heat_removal_kw": 3000, "minimum_water_flow_m3_h": 0, "maximum_water_flow_m3_h": 100},
    ]
    qualification_cases = [
        {"id": "F009-N1", "kind": "normal", "input": {"total_water_flow_m3_h": 60, "zones": _BASE_ZONES, "water_inlet_temperature_k": 293.15, "water_outlet_temperature_k": 303.15}},
        {"id": "F009-N2", "kind": "normal", "input": {"total_water_flow_m3_h": 50, "zones": [{"name": "mold_exit", "allocation_weight": 1, "target_heat_removal_kw": 500, "minimum_water_flow_m3_h": 0, "maximum_water_flow_m3_h": 10}, {"name": "spray", "allocation_weight": 3, "target_heat_removal_kw": 1500, "minimum_water_flow_m3_h": 0, "maximum_water_flow_m3_h": 100}], "water_inlet_temperature_k": 290, "water_outlet_temperature_k": 305}},
        {"id": "F009-N3", "kind": "normal", "input": {"total_water_flow_m3_h": 30, "zones": [{"name": "upper", "allocation_weight": 1, "target_heat_removal_kw": 700, "minimum_water_flow_m3_h": 20, "maximum_water_flow_m3_h": 50}, {"name": "lower", "allocation_weight": 1, "target_heat_removal_kw": 300, "minimum_water_flow_m3_h": 0, "maximum_water_flow_m3_h": 50}], "water_inlet_temperature_k": 295, "water_outlet_temperature_k": 310}},
        {"id": "F009-B1", "kind": "boundary", "input": {"total_water_flow_m3_h": 20, "zones": [{"name": "a", "allocation_weight": 1, "target_heat_removal_kw": 100, "minimum_water_flow_m3_h": 10, "maximum_water_flow_m3_h": 20}, {"name": "b", "allocation_weight": 1, "target_heat_removal_kw": 100, "minimum_water_flow_m3_h": 10, "maximum_water_flow_m3_h": 20}], "water_inlet_temperature_k": 293, "water_outlet_temperature_k": 303}},
        {"id": "F009-F1", "kind": "failure", "input": {"total_water_flow_m3_h": 10, "zones": [{"name": "a", "allocation_weight": 1, "target_heat_removal_kw": 100, "minimum_water_flow_m3_h": 8, "maximum_water_flow_m3_h": 20}, {"name": "b", "allocation_weight": 1, "target_heat_removal_kw": 100, "minimum_water_flow_m3_h": 8, "maximum_water_flow_m3_h": 20}], "water_inlet_temperature_k": 293, "water_outlet_temperature_k": 303}},
        {"id": "F009-F2", "kind": "failure", "input": {"total_water_flow_m3_h": 20, "zones": [{"name": "a", "allocation_weight": 1, "target_heat_removal_kw": 100, "minimum_water_flow_m3_h": 0, "maximum_water_flow_m3_h": 20}, {"name": "b", "allocation_weight": 1, "target_heat_removal_kw": 100, "minimum_water_flow_m3_h": 0, "maximum_water_flow_m3_h": 20}], "water_inlet_temperature_k": 300, "water_outlet_temperature_k": 300}},
    ]

    @staticmethod
    def _parse_zones(raw: Any) -> tuple[list[dict[str, float | str]] | None, str | None]:
        if not isinstance(raw, list) or not 2 <= len(raw) <= 50:
            return None, "zones必须包含2到50个分区"
        required = {"name", "allocation_weight", "target_heat_removal_kw", "minimum_water_flow_m3_h", "maximum_water_flow_m3_h"}
        parsed: list[dict[str, float | str]] = []
        names: set[str] = set()
        for index, item in enumerate(raw):
            if not isinstance(item, dict) or set(item) != required:
                return None, f"zones[{index}]字段必须且只能为{sorted(required)}"
            name = item.get("name")
            normalized = name.strip() if isinstance(name, str) else ""
            if not normalized or normalized in names:
                return None, f"zones[{index}].name必须唯一且非空"
            values: dict[str, float] = {}
            for key, strict in (("allocation_weight", True), ("target_heat_removal_kw", False), ("minimum_water_flow_m3_h", False), ("maximum_water_flow_m3_h", False)):
                value, error = finite(item.get(key), f"zones[{index}].{key}", minimum=0, strict_minimum=strict)
                if error:
                    return None, error
                values[key] = value
            if values["minimum_water_flow_m3_h"] > values["maximum_water_flow_m3_h"]:
                return None, f"zones[{index}]最小水量不能大于最大水量"
            names.add(normalized)
            parsed.append({"name": normalized, **values})
        return parsed, None

    def invoke(self, params, context=None):
        total, error = finite(params.get("total_water_flow_m3_h"), "total_water_flow_m3_h", minimum=0)
        if error:
            return fail(error, "OUT_OF_DOMAIN")
        inlet, error = finite(params.get("water_inlet_temperature_k"), "water_inlet_temperature_k", minimum=0, strict_minimum=True)
        if error:
            return fail(error, "OUT_OF_DOMAIN")
        outlet, error = finite(params.get("water_outlet_temperature_k"), "water_outlet_temperature_k", minimum=0, strict_minimum=True)
        if error:
            return fail(error, "OUT_OF_DOMAIN")
        if outlet <= inlet:
            return fail("water_outlet_temperature_k必须高于water_inlet_temperature_k", "OUT_OF_DOMAIN")
        density, error = finite(params.get("water_density_kg_m3", 998.0), "water_density_kg_m3", minimum=0, strict_minimum=True)
        if error:
            return fail(error, "OUT_OF_DOMAIN")
        cp, error = finite(params.get("water_specific_heat_kj_kg_k", 4.18), "water_specific_heat_kj_kg_k", minimum=0, strict_minimum=True)
        if error:
            return fail(error, "OUT_OF_DOMAIN")
        zones, error = self._parse_zones(params.get("zones"))
        if error:
            return fail(error)
        minimum_sum = math.fsum(float(row["minimum_water_flow_m3_h"]) for row in zones)
        maximum_sum = math.fsum(float(row["maximum_water_flow_m3_h"]) for row in zones)
        tolerance = 1e-10 * max(1.0, maximum_sum)
        if total < minimum_sum - tolerance or total > maximum_sum + tolerance:
            return fail(
                f"total_water_flow_m3_h={total:g}不在分区可行范围[{minimum_sum:g},{maximum_sum:g}]",
                "MODEL_NOT_APPLICABLE",
            )
        total = min(max(total, minimum_sum), maximum_sum)
        lower = 0.0
        upper = max(
            float(row["maximum_water_flow_m3_h"]) / float(row["allocation_weight"])
            for row in zones
        ) if maximum_sum > 0 else 0.0
        for _ in range(160):
            middle = (lower + upper) / 2
            projected = math.fsum(
                min(
                    float(row["maximum_water_flow_m3_h"]),
                    max(float(row["minimum_water_flow_m3_h"]), middle * float(row["allocation_weight"])),
                )
                for row in zones
            )
            if projected < total:
                lower = middle
            else:
                upper = middle
        scale = (lower + upper) / 2
        flows = [
            min(
                float(row["maximum_water_flow_m3_h"]),
                max(float(row["minimum_water_flow_m3_h"]), scale * float(row["allocation_weight"])),
            )
            for row in zones
        ]
        correction = total - math.fsum(flows)
        if correction:
            for index, (flow, row) in enumerate(zip(flows, zones)):
                low = float(row["minimum_water_flow_m3_h"])
                high = float(row["maximum_water_flow_m3_h"])
                if (correction > 0 and flow < high) or (correction < 0 and flow > low):
                    applied = min(correction, high - flow) if correction > 0 else max(correction, low - flow)
                    flows[index] += applied
                    correction -= applied
                    if abs(correction) <= tolerance:
                        break
        allocated = math.fsum(flows)
        residual = allocated - total
        if abs(residual) > tolerance:
            return fail("有界比例投影未达到水量闭合容差", "NUMERICAL_ERROR")
        delta_t = outlet - inlet
        results = []
        active_minimum = active_maximum = 0
        for row, flow in zip(zones, flows):
            low = float(row["minimum_water_flow_m3_h"])
            high = float(row["maximum_water_flow_m3_h"])
            at_minimum = math.isclose(flow, low, rel_tol=0, abs_tol=tolerance)
            at_maximum = math.isclose(flow, high, rel_tol=0, abs_tol=tolerance)
            active_minimum += int(at_minimum)
            active_maximum += int(at_maximum)
            heat_capacity = flow * density / 3600 * cp * delta_t
            demand = float(row["target_heat_removal_kw"])
            results.append({
                "name": row["name"],
                "allocation_weight": row["allocation_weight"],
                "water_flow_m3_h": flow,
                "minimum_water_flow_m3_h": low,
                "maximum_water_flow_m3_h": high,
                "water_mass_flow_kg_s": flow * density / 3600,
                "heat_capacity_kw": heat_capacity,
                "target_heat_removal_kw": demand,
                "heat_coverage_fraction": heat_capacity / demand if demand > 0 else None,
                "heat_capacity_margin_kw": heat_capacity - demand,
                "at_minimum": at_minimum,
                "at_maximum": at_maximum,
            })
        total_capacity = math.fsum(row["heat_capacity_kw"] for row in results)
        total_demand = math.fsum(float(row["target_heat_removal_kw"]) for row in zones)
        warnings = []
        if math.isclose(total, minimum_sum, rel_tol=0, abs_tol=tolerance):
            warnings.append(BoundaryWarning("total_water_flow_m3_h", "总水量等于分区最小水量之和"))
        elif math.isclose(total, maximum_sum, rel_tol=0, abs_tol=tolerance):
            warnings.append(BoundaryWarning("total_water_flow_m3_h", "总水量等于分区最大水量之和"))
        return ModelResult(True, result={
            "zone_results": results,
            "total_water_flow_m3_h": total,
            "allocated_water_flow_m3_h": allocated,
            "water_flow_closure_residual_m3_h": residual,
            "total_heat_capacity_kw": total_capacity,
            "total_target_heat_removal_kw": total_demand,
            "overall_heat_coverage_fraction": total_capacity / total_demand if total_demand > 0 else None,
            "water_temperature_rise_k": delta_t,
            "active_minimum_count": active_minimum,
            "active_maximum_count": active_maximum,
            "calculation_method": "bounded-proportional-water-allocation-v1",
        }, boundary_check=BoundaryCheck(not warnings, warnings))


class F011_MaximumFeasibleCastingSpeed(W16FormulaTool):
    model_id, name, version = "F011", "最大可行拉速", "1.0.0"
    tool_name = "metallurgy_optimize_casting_speed"
    scenario = "凝固与连铸"
    model_type = "确定性单调约束优化"
    description = "在设备、停留时间、平方根坯壳增长和二冷热功率约束下，解析求解最大可行连铸拉速及限制因素。"
    applicable_boundary = (
        "恒拉速、稳态断面质量流和显式参数的离线可行性设计；坯壳采用s=K*sqrt(t)简化关系。"
        "不预测缺陷概率、不读取历史质量标签、不做多目标学习，也不直接下发生产设定。"
    )
    data_source = ["Continuous-casting residence relation", "Square-root shell-growth law", "Steady cooling-power balance"]
    source_version = "maximum-feasible-casting-speed-v1"
    formula_reference = (
        "v<=L/t_req; v<=L*(K/s_min)^2; "
        "v<=Q_available/(n*A*rho*q_required); maximize v within equipment interval"
    )
    source_records = [
        {
            "source_id": "CC-HEAT-TRANSFER-1997",
            "name": "Simulation of the continuous casting process by a mathematical model",
            "version": "DOI 10.1016/0020-7403(96)00052-5",
            "url": "https://doi.org/10.1016/0020-7403(96)00052-5",
        },
        {"source_id": "STEFAN-SQRT-SHELL", "name": "Square-root solidification shell-growth approximation", "version": "analytic-scaling-v1"},
    ]
    failure_modes = [
        "流股、断面、密度、设备长度、停留时间、坯壳参数或冷却参数非正",
        "设备最低拉速高于最高拉速",
        "物理约束给出的综合上限低于设备最低拉速，因而无可行解",
        "把最大可行值解释为质量保证、闭环控制或多目标最优解",
    ]
    independent_validation = [
        "最优拉速等于设备、停留、坯壳和冷却四个上限的最小值",
        "推荐点的全部约束余量非负且至少一个上限被激活",
        "断面或单位移热需求增加时冷却拉速上限不增",
        "设备长度同比缩放时停留时间和坯壳上限同比缩放",
    ]
    dependencies = ["F006", "F008", "F009"]
    relations = [
        rel("accepts_output_from", "F006", "F006凝固终点时间可形成required_residence_time_s"),
        rel("accepts_output_from", "F008", "F008总热负荷可形成available_cooling_power_kw"),
        rel("accepts_output_from", "F009", "F009分区热容量合计可形成available_cooling_power_kw"),
        rel("differs_from", "G002", "G002校验数值时间步；F011求生产拉速的物理可行上限"),
    ]
    input_fields = [
        InputField("strand_count", "流股数", "integer", unit="1", min_value=1, max_value=16),
        InputField("section_width_m", "断面宽度", "number", unit="m", min_value=1e-12),
        InputField("section_thickness_m", "断面厚度", "number", unit="m", min_value=1e-12),
        InputField("steel_density_kg_m3", "钢密度", "number", unit="kg/m3", min_value=1e-12),
        InputField("effective_machine_length_m", "有效设备长度", "number", unit="m", min_value=1e-12),
        InputField("minimum_casting_speed_m_s", "设备最低拉速", "number", unit="m/s", min_value=1e-12),
        InputField("maximum_casting_speed_m_s", "设备最高拉速", "number", unit="m/s", min_value=1e-12),
        InputField("required_residence_time_s", "最低停留时间", "number", unit="s", min_value=1e-12),
        InputField("minimum_shell_thickness_m", "最低坯壳厚度", "number", unit="m", min_value=1e-12),
        InputField("shell_growth_coefficient_m_sqrt_s", "平方根坯壳增长系数", "number", unit="m/sqrt(s)", min_value=1e-12),
        InputField("available_cooling_power_kw", "可用二冷热功率", "number", unit="kW", min_value=1e-12),
        InputField("required_specific_heat_removal_kj_kg", "所需单位钢移热", "number", unit="kJ/kg", min_value=1e-12),
    ]
    output_fields = [
        OutputField("recommended_casting_speed_m_s", "最大可行拉速", "number", "m/s"),
        OutputField("recommended_casting_speed_m_min", "最大可行拉速", "number", "m/min"),
        OutputField("speed_limits_m_s", "各约束拉速上限", "object", "m/s"),
        OutputField("limiting_constraints", "限制约束", "array"),
        OutputField("residence_time_s", "设备内停留时间", "number", "s"),
        OutputField("predicted_shell_thickness_m", "平方根律预测坯壳厚度", "number", "m"),
        OutputField("steel_mass_flow_kg_s", "钢质量流量", "number", "kg/s"),
        OutputField("throughput_t_h", "产量", "number", "t/h"),
        OutputField("required_cooling_power_kw", "所需二冷热功率", "number", "kW"),
        OutputField("constraint_margins", "约束余量", "object"),
        OutputField("objective", "优化目标", "string"),
        OutputField("calculation_method", "计算方法", "string"),
    ]
    validation_rules = [
        {"rule": "strictly_positive_geometry_physics_and_cooling_inputs"},
        {"rule": "minimum_speed_not_greater_than_maximum_speed"},
        {"rule": "intersection_of_all_monotone_constraints_is_nonempty"},
    ]
    _BASE = {
        "strand_count": 1,
        "section_width_m": 1.5,
        "section_thickness_m": 0.2,
        "steel_density_kg_m3": 7400,
        "effective_machine_length_m": 30,
        "minimum_casting_speed_m_s": 0.01,
        "maximum_casting_speed_m_s": 0.05,
        "required_residence_time_s": 300,
        "minimum_shell_thickness_m": 0.02,
        "shell_growth_coefficient_m_sqrt_s": 0.002,
        "available_cooling_power_kw": 2000,
        "required_specific_heat_removal_kj_kg": 50,
    }
    qualification_cases = [
        {"id": "F011-N1", "kind": "normal", "input": _BASE},
        {"id": "F011-N2", "kind": "normal", "input": {**_BASE, "effective_machine_length_m": 10, "maximum_casting_speed_m_s": 0.1, "required_residence_time_s": 500, "available_cooling_power_kw": 20000}},
        {"id": "F011-N3", "kind": "normal", "input": {**_BASE, "effective_machine_length_m": 20, "maximum_casting_speed_m_s": 0.2, "required_residence_time_s": 100, "shell_growth_coefficient_m_sqrt_s": 0.001, "available_cooling_power_kw": 50000}},
        {"id": "F011-B1", "kind": "boundary", "input": {**_BASE, "minimum_casting_speed_m_s": 0.02, "maximum_casting_speed_m_s": 0.02, "available_cooling_power_kw": 100000}},
        {"id": "F011-F1", "kind": "failure", "input": {**_BASE, "minimum_casting_speed_m_s": 0.03}},
        {"id": "F011-F2", "kind": "failure", "input": {**_BASE, "minimum_casting_speed_m_s": 0.06, "maximum_casting_speed_m_s": 0.05}},
    ]

    def invoke(self, params, context=None):
        strands, error = integer(params.get("strand_count"), "strand_count", 1, 16)
        if error:
            return fail(error, "OUT_OF_DOMAIN")
        parsed: dict[str, float] = {}
        for field in self.input_fields[1:]:
            value, error = finite(params.get(field.name), field.name, minimum=0, strict_minimum=True)
            if error:
                return fail(error, "OUT_OF_DOMAIN")
            parsed[field.name] = value
        minimum_speed = parsed["minimum_casting_speed_m_s"]
        equipment_limit = parsed["maximum_casting_speed_m_s"]
        if minimum_speed > equipment_limit:
            return fail("minimum_casting_speed_m_s不能高于maximum_casting_speed_m_s", "OUT_OF_DOMAIN")
        length = parsed["effective_machine_length_m"]
        residence_limit = length / parsed["required_residence_time_s"]
        shell_limit = length * (
            parsed["shell_growth_coefficient_m_sqrt_s"] / parsed["minimum_shell_thickness_m"]
        ) ** 2
        area = parsed["section_width_m"] * parsed["section_thickness_m"]
        mass_flow_per_speed = strands * area * parsed["steel_density_kg_m3"]
        cooling_limit = parsed["available_cooling_power_kw"] / (
            mass_flow_per_speed * parsed["required_specific_heat_removal_kj_kg"]
        )
        limits = {
            "equipment": equipment_limit,
            "residence_time": residence_limit,
            "shell_thickness": shell_limit,
            "cooling_power": cooling_limit,
        }
        feasible_upper = min(limits.values())
        tolerance = 1e-12 * max(1.0, feasible_upper, minimum_speed)
        if feasible_upper < minimum_speed - tolerance:
            return fail(
                f"综合可行上限{feasible_upper:g} m/s低于设备最低拉速{minimum_speed:g} m/s",
                "MODEL_NOT_APPLICABLE",
            )
        speed = max(minimum_speed, feasible_upper)
        residence = length / speed
        shell = parsed["shell_growth_coefficient_m_sqrt_s"] * math.sqrt(residence)
        mass_flow = mass_flow_per_speed * speed
        required_power = mass_flow * parsed["required_specific_heat_removal_kj_kg"]
        limit_tolerance = 1e-10 * max(1.0, speed)
        limiting = sorted(name for name, limit in limits.items() if abs(limit - feasible_upper) <= limit_tolerance)
        margins = {
            "equipment_speed_margin_m_s": equipment_limit - speed,
            "residence_time_margin_s": residence - parsed["required_residence_time_s"],
            "shell_thickness_margin_m": shell - parsed["minimum_shell_thickness_m"],
            "cooling_power_margin_kw": parsed["available_cooling_power_kw"] - required_power,
            "minimum_speed_margin_m_s": speed - minimum_speed,
        }
        margin_tolerances = {
            "equipment_speed_margin_m_s": 1e-12 * max(1.0, equipment_limit),
            "residence_time_margin_s": 1e-10 * max(1.0, parsed["required_residence_time_s"]),
            "shell_thickness_margin_m": 1e-12 * max(1.0, parsed["minimum_shell_thickness_m"]),
            "cooling_power_margin_kw": 1e-10 * max(1.0, parsed["available_cooling_power_kw"]),
            "minimum_speed_margin_m_s": 1e-12 * max(1.0, minimum_speed),
        }
        if any(margins[key] < -margin_tolerances[key] for key in margins):
            return fail("推荐拉速未通过约束余量复核", "NUMERICAL_ERROR")
        warnings = []
        if math.isclose(feasible_upper, minimum_speed, rel_tol=0, abs_tol=tolerance):
            warnings.append(BoundaryWarning("minimum_casting_speed_m_s", "可行域退化为设备最低拉速单点"))
        return ModelResult(True, result={
            "recommended_casting_speed_m_s": speed,
            "recommended_casting_speed_m_min": speed * 60,
            "speed_limits_m_s": limits,
            "limiting_constraints": limiting,
            "residence_time_s": residence,
            "predicted_shell_thickness_m": shell,
            "steel_mass_flow_kg_s": mass_flow,
            "throughput_t_h": mass_flow * 3.6,
            "required_cooling_power_kw": required_power,
            "constraint_margins": margins,
            "objective": "maximize_casting_speed_subject_to_declared_constraints",
            "calculation_method": "analytic-monotone-constraint-intersection-v1",
        }, boundary_check=BoundaryCheck(not warnings, warnings))


THERMAL_LAYER_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "name": {"type": "string"},
        "temperature_k": {"type": "number", "exclusiveMinimum": 0},
        "weight_fraction": {"type": "number", "exclusiveMinimum": 0},
        "elastic_modulus_pa": {"type": "number", "exclusiveMinimum": 0},
        "thermal_expansion_1_k": {"type": "number", "minimum": 0},
        "yield_strength_pa": {"type": "number", "exclusiveMinimum": 0},
    },
    "required": [
        "name",
        "temperature_k",
        "weight_fraction",
        "elastic_modulus_pa",
        "thermal_expansion_1_k",
        "yield_strength_pa",
    ],
}


class F014_LayeredThermalStress(W16FormulaTool):
    model_id, name, version = "F014", "分层热应力与应变", "1.0.0"
    tool_name = "metallurgy_calculate_casting_thermal_stress"
    scenario = "凝固与连铸"
    model_type = "一维平面应力弹性—理想塑性后处理"
    description = "对显式分层温度和高温材料参数计算完全约束或无曲率自平衡膜状态下的热应力、弹塑性应变与屈服利用率。"
    applicable_boundary = (
        "一维层状、平面应力、小应变、弹性—理想塑性、各层参数常值；自平衡模式禁止截面弯曲且无外膜力。"
        "不包含蠕变、相变应变、损伤、裂纹、二维/三维应力集中或完整有限元。"
    )
    data_source = ["Linear thermoelastic strain decomposition", "Elastic-perfectly-plastic stress clipping", "Zero membrane-force equilibrium"]
    source_version = "layered-thermal-membrane-stress-v1"
    formula_reference = (
        "epsilon_th=alpha*(T-Tref); sigma=clip(E*(epsilon0-epsilon_th),+-yield); "
        "restrained: epsilon0=0; self_equilibrated: solve sum(w*sigma)=0"
    )
    source_records = [
        {
            "source_id": "NIST-TN-1907",
            "name": "Temperature-Dependent Material Modeling for Structural Steels",
            "version": "NIST Technical Note 1907 (2016)",
            "url": "https://nvlpubs.nist.gov/nistpubs/TechnicalNotes/NIST.TN.1907.pdf",
        },
        {"source_id": "THERMAL-STRESS-STRAIN-DECOMPOSITION", "name": "One-dimensional thermoelastic strain decomposition", "version": "formula-v1"},
    ]
    failure_modes = [
        "模式不支持、层数组为空或字段不完整",
        "层名重复、温度/权重/模量/屈服非正或热膨胀系数为负",
        "自平衡公共应变求根不收敛或膜力残差超限",
        "自平衡模式中全部层屈服而公共应变不唯一",
        "把一维膜结果解释为裂纹概率、弯曲应力或三维有限元结论",
    ]
    independent_validation = [
        "均匀温度和材料的自平衡截面应力严格为零",
        "单层完全约束结果与sigma=clip(-E*alpha*deltaT,+-yield)一致",
        "每层实际应力绝对值不超过显式屈服强度",
        "自平衡模式加权膜应力和接近零且应变分解闭合",
    ]
    dependencies = []
    relations = [
        rel("accepts_output_from", "F005", "F005温度剖面可转换为F014显式分层温度输入"),
        rel("accepts_output_from", "G003", "G003常物性温度剖面可转换为F014显式分层温度输入"),
        rel("accepts_output_from", "T003", "T003均温结果可形成F014均匀温度边界验证"),
        rel("differs_from", "A010", "A010传播输入不确定度；F014计算确定性热弹塑性响应"),
    ]
    input_fields = [
        InputField("constraint_mode", "约束模式", "select", enum=["fully_restrained", "self_equilibrated_membrane"]),
        InputField("reference_temperature_k", "无热应变参考温度", "number", unit="K", min_value=1e-12),
        InputField("layers", "分层温度与材料参数", "array", items=THERMAL_LAYER_SCHEMA, min_items=1, max_items=100),
    ]
    output_fields = [
        OutputField("constraint_mode", "约束模式", "string"),
        OutputField("reference_temperature_k", "参考温度", "number", "K"),
        OutputField("common_total_strain", "公共总应变", "number", "1"),
        OutputField("layer_results", "逐层应力应变", "array", "strain:1; stress:Pa"),
        OutputField("weighted_mean_stress_pa", "加权平均膜应力", "number", "Pa"),
        OutputField("equilibrium_residual_pa", "自平衡膜力残差", "number", "Pa", nullable=True),
        OutputField("maximum_tensile_stress_pa", "最大拉应力", "number", "Pa"),
        OutputField("maximum_compressive_stress_pa", "最大压应力", "number", "Pa"),
        OutputField("maximum_yield_utilization", "最大屈服利用率", "number", "1"),
        OutputField("critical_layer", "最大屈服利用率层", "string"),
        OutputField("yielded_layer_count", "屈服层数", "number", "1"),
        OutputField("calculation_method", "计算方法", "string"),
    ]
    validation_rules = [
        {"rule": "one_to_one_hundred_unique_positive_weight_layers"},
        {"rule": "positive_temperature_modulus_yield_and_nonnegative_expansion"},
        {"rule": "actual_stress_is_bounded_by_yield_strength"},
        {"rule": "self_equilibrated_mode_has_zero_weighted_membrane_stress"},
    ]
    _TWO_LAYER = [
        {"name": "hot", "temperature_k": 1000, "weight_fraction": 0.5, "elastic_modulus_pa": 200e9, "thermal_expansion_1_k": 1e-5, "yield_strength_pa": 1e9},
        {"name": "cold", "temperature_k": 500, "weight_fraction": 0.5, "elastic_modulus_pa": 200e9, "thermal_expansion_1_k": 1e-5, "yield_strength_pa": 1e9},
    ]
    qualification_cases = [
        {"id": "F014-N1", "kind": "normal", "input": {"constraint_mode": "self_equilibrated_membrane", "reference_temperature_k": 500, "layers": _TWO_LAYER}},
        {"id": "F014-N2", "kind": "normal", "input": {"constraint_mode": "fully_restrained", "reference_temperature_k": 300, "layers": [{"name": "surface", "temperature_k": 600, "weight_fraction": 1, "elastic_modulus_pa": 200e9, "thermal_expansion_1_k": 1e-5, "yield_strength_pa": 1e9}]}},
        {"id": "F014-N3", "kind": "normal", "input": {"constraint_mode": "fully_restrained", "reference_temperature_k": 300, "layers": [{"name": "yielded_hot_layer", "temperature_k": 1000, "weight_fraction": 1, "elastic_modulus_pa": 100e9, "thermal_expansion_1_k": 2e-5, "yield_strength_pa": 200e6}]}},
        {"id": "F014-B1", "kind": "boundary", "input": {"constraint_mode": "self_equilibrated_membrane", "reference_temperature_k": 300, "layers": [{"name": "a", "temperature_k": 500, "weight_fraction": 1, "elastic_modulus_pa": 200e9, "thermal_expansion_1_k": 1e-5, "yield_strength_pa": 500e6}, {"name": "b", "temperature_k": 500, "weight_fraction": 1, "elastic_modulus_pa": 200e9, "thermal_expansion_1_k": 1e-5, "yield_strength_pa": 500e6}]}},
        {"id": "F014-F1", "kind": "failure", "input": {"constraint_mode": "fully_restrained", "reference_temperature_k": 300, "layers": [{"name": "same", "temperature_k": 500, "weight_fraction": 1, "elastic_modulus_pa": 200e9, "thermal_expansion_1_k": 1e-5, "yield_strength_pa": 500e6}, {"name": "same", "temperature_k": 600, "weight_fraction": 1, "elastic_modulus_pa": 200e9, "thermal_expansion_1_k": 1e-5, "yield_strength_pa": 500e6}]}},
        {"id": "F014-F2", "kind": "failure", "input": {"constraint_mode": "fully_restrained", "reference_temperature_k": 300, "layers": [{"name": "bad", "temperature_k": 0, "weight_fraction": 1, "elastic_modulus_pa": 200e9, "thermal_expansion_1_k": 1e-5, "yield_strength_pa": 500e6}]}},
    ]

    @staticmethod
    def _parse_layers(raw: Any) -> tuple[list[dict[str, float | str]] | None, str | None]:
        if not isinstance(raw, list) or not 1 <= len(raw) <= 100:
            return None, "layers必须包含1到100层"
        required = {"name", "temperature_k", "weight_fraction", "elastic_modulus_pa", "thermal_expansion_1_k", "yield_strength_pa"}
        layers: list[dict[str, float | str]] = []
        names: set[str] = set()
        for index, item in enumerate(raw):
            if not isinstance(item, dict) or set(item) != required:
                return None, f"layers[{index}]字段必须且只能为{sorted(required)}"
            name = item.get("name")
            normalized = name.strip() if isinstance(name, str) else ""
            if not normalized or normalized in names:
                return None, f"layers[{index}].name必须唯一且非空"
            values = {}
            for key, strict in (("temperature_k", True), ("weight_fraction", True), ("elastic_modulus_pa", True), ("thermal_expansion_1_k", False), ("yield_strength_pa", True)):
                value, error = finite(item.get(key), f"layers[{index}].{key}", minimum=0, strict_minimum=strict)
                if error:
                    return None, error
                values[key] = value
            names.add(normalized)
            layers.append({"name": normalized, **values})
        return layers, None

    @staticmethod
    def _stress(layer: dict[str, float | str], common_strain: float, thermal_strain: float) -> tuple[float, float]:
        trial = float(layer["elastic_modulus_pa"]) * (common_strain - thermal_strain)
        yield_strength = float(layer["yield_strength_pa"])
        return trial, min(yield_strength, max(-yield_strength, trial))

    def invoke(self, params, context=None):
        mode = params.get("constraint_mode")
        if mode not in {"fully_restrained", "self_equilibrated_membrane"}:
            return fail("constraint_mode必须为fully_restrained或self_equilibrated_membrane")
        reference, error = finite(params.get("reference_temperature_k"), "reference_temperature_k", minimum=0, strict_minimum=True)
        if error:
            return fail(error, "OUT_OF_DOMAIN")
        layers, error = self._parse_layers(params.get("layers"))
        if error:
            return fail(error, "OUT_OF_DOMAIN")
        thermal = [
            float(row["thermal_expansion_1_k"]) * (float(row["temperature_k"]) - reference)
            for row in layers
        ]
        total_weight = math.fsum(float(row["weight_fraction"]) for row in layers)
        if mode == "fully_restrained":
            common = 0.0
        elif max(thermal) - min(thermal) <= 1e-18:
            common = thermal[0]
        else:
            strain_padding = max(float(row["yield_strength_pa"]) / float(row["elastic_modulus_pa"]) for row in layers) + 1.0
            lower = min(thermal) - strain_padding
            upper = max(thermal) + strain_padding

            def membrane(strain: float) -> float:
                return math.fsum(
                    float(row["weight_fraction"]) * self._stress(row, strain, eps_th)[1]
                    for row, eps_th in zip(layers, thermal)
                ) / total_weight

            if membrane(lower) > 0 or membrane(upper) < 0:
                return fail("自平衡公共应变未被数值区间括住", "NUMERICAL_ERROR")
            for _ in range(200):
                middle = (lower + upper) / 2
                if membrane(middle) < 0:
                    lower = middle
                else:
                    upper = middle
            common = (lower + upper) / 2
        results = []
        weighted_stress = 0.0
        yielded_count = 0
        for row, eps_th in zip(layers, thermal):
            trial, stress = self._stress(row, common, eps_th)
            elastic = stress / float(row["elastic_modulus_pa"])
            plastic = common - eps_th - elastic
            yield_strength = float(row["yield_strength_pa"])
            utilization = abs(stress) / yield_strength
            yielded = abs(trial) >= yield_strength * (1 - 1e-12)
            yielded_count += int(yielded)
            weighted_stress += float(row["weight_fraction"]) * stress
            results.append({
                "name": row["name"],
                "temperature_k": row["temperature_k"],
                "normalized_weight": float(row["weight_fraction"]) / total_weight,
                "thermal_strain": eps_th,
                "common_total_strain": common,
                "elastic_mechanical_strain": elastic,
                "plastic_strain": plastic,
                "trial_stress_pa": trial,
                "stress_pa": stress,
                "yield_strength_pa": yield_strength,
                "yield_utilization": utilization,
                "yielded": yielded,
            })
        weighted_mean = weighted_stress / total_weight
        equilibrium = weighted_mean if mode == "self_equilibrated_membrane" else None
        stress_scale = max(float(row["yield_strength_pa"]) for row in layers)
        if equilibrium is not None and abs(equilibrium) > 1e-10 * max(1.0, stress_scale):
            return fail("自平衡膜力残差超过容差", "NUMERICAL_ERROR")
        if mode == "self_equilibrated_membrane" and results and all(row["yielded"] for row in results):
            return fail("所有层均屈服，自平衡公共应变不唯一", "MODEL_NOT_APPLICABLE")
        critical = max(results, key=lambda row: row["yield_utilization"])
        warnings = []
        if mode == "self_equilibrated_membrane" and max(thermal) - min(thermal) <= 1e-18:
            warnings.append(BoundaryWarning("layers", "各层自由热应变相同，自平衡膜应力为零"))
        return ModelResult(True, result={
            "constraint_mode": mode,
            "reference_temperature_k": reference,
            "common_total_strain": common,
            "layer_results": results,
            "weighted_mean_stress_pa": weighted_mean,
            "equilibrium_residual_pa": equilibrium,
            "maximum_tensile_stress_pa": max(row["stress_pa"] for row in results),
            "maximum_compressive_stress_pa": min(row["stress_pa"] for row in results),
            "maximum_yield_utilization": critical["yield_utilization"],
            "critical_layer": critical["name"],
            "yielded_layer_count": yielded_count,
            "calculation_method": "layered-plane-stress-elastic-perfectly-plastic-v1",
        }, boundary_check=BoundaryCheck(not warnings, warnings))


class G003_OneDimensionalHeatPDE(W16FormulaTool):
    model_id, name, version = "G003", "一维瞬态导热PDE", "1.0.0"
    tool_name = "metallurgy_solve_heat_pde_1d"
    scenario = "数值方法与仿真"
    model_type = "确定性显式有限体积PDE"
    description = "用常物性单元中心显式有限体积法求解一维瞬态导热，支持定温、入域热流、对流边界和均匀体热源，并返回稳定性与能量闭合。"
    applicable_boundary = (
        "一维平板、常密度/比热/导热率、均匀网格、显式Euler；边界和体热源在计算期内恒定。"
        "不处理相变、温变物性、辐射非线性、移动边界、二维/三维几何或不稳定时间步。"
    )
    data_source = ["One-dimensional heat equation", "Cell-centred finite volume", "Explicit-Euler monotonicity stability"]
    source_version = "explicit-cell-centred-heat-fvm-v1"
    formula_reference = (
        "rho*cp*dT_i/dt=(q_left_in+q_right_in)/dx+qdot; internal q=k*(T_neighbor-T_i)/dx; "
        "require dt*max(discrete diagonal rate)<=1"
    )
    source_records = [
        {
            "source_id": "SANDIA-NETFLOW-1D-HEAT",
            "name": "NETFLOW one-dimensional transient wall heat-conduction model",
            "version": "SAND2016-0515R",
            "url": "https://www.osti.gov/servlets/purl/1236111",
        },
        {
            "source_id": "CFL-1928",
            "name": "On the Partial Difference Equations of Mathematical Physics",
            "version": "1928/English translation",
            "url": "https://galton.uchicago.edu/~lekheng/courses/302/classics/courant-friedrichs-lewy.pdf",
        },
    ]
    failure_modes = [
        "几何、节点、物性、时间配置或绝对温度非法",
        "初温模式字段冲突、逐节点初温长度不等于节点数",
        "边界类型不支持或边界字段不完整/不互斥",
        "显式稳定性系数大于1或时间步数超过200000",
        "积分产生非有限/非正绝对温度或能量闭合超限",
    ]
    independent_validation = [
        "绝热零源均匀初温在任意稳定步数后严格保持不变",
        "单步控制体更新与手算离散能量方程一致",
        "离散储能变化等于累计边界入热与体热源之和",
        "对称初边值保持温度场对称且不稳定时间步被拒绝",
    ]
    dependencies = ["G001", "G002"]
    relations = [
        rel("consumes_output_from", "G001", "G001推荐网格尺度可转换为G003节点数"),
        rel("verified_by", "G002", "G002可独立复算G003显式扩散Fourier稳定性"),
        rel("overlaps", "T001", "T001求常物性平板稳态解析热流；G003求瞬态空间温度场"),
        rel("overlaps", "T003", "T003是Bi小于等于0.1的零维均温瞬态；G003保留空间梯度"),
        rel("overlaps", "F005", "F005是温变物性和相变的一维隐式焓法；G003是常物性通用显式基准"),
    ]
    input_fields = [
        InputField("length_m", "一维域长度", "number", unit="m", min_value=1e-12),
        InputField("node_count", "控制体节点数", "integer", unit="1", min_value=3, max_value=501),
        InputField("duration_s", "计算时长", "number", unit="s", min_value=0),
        InputField("time_step_s", "名义时间步", "number", unit="s", min_value=1e-15),
        InputField("density_kg_m3", "密度", "number", unit="kg/m3", min_value=1e-12),
        InputField("specific_heat_j_kg_k", "比热", "number", unit="J/(kg*K)", min_value=1e-12),
        InputField("thermal_conductivity_w_m_k", "导热率", "number", unit="W/(m*K)", min_value=1e-12),
        InputField("initial_condition_mode", "初始条件模式", "select", enum=["uniform", "profile"]),
        InputField("initial_temperature_k", "均匀初温", "number", required=False, unit="K", min_value=1e-12),
        InputField("initial_temperature_profile_k", "逐节点初温", "array", required=False, items={"type": "number", "exclusiveMinimum": 0}, min_items=3, max_items=501, unit="K"),
        InputField("volumetric_heat_source_w_m3", "均匀体热源", "number", required=False, default=0.0, unit="W/m3"),
        InputField("left_boundary_type", "左边界类型", "select", enum=["dirichlet", "heat_flux", "convection"]),
        InputField("left_boundary_temperature_k", "左侧给定温度", "number", required=False, unit="K", min_value=1e-12),
        InputField("left_heat_flux_into_domain_w_m2", "左侧入域热流", "number", required=False, unit="W/m2"),
        InputField("left_ambient_temperature_k", "左侧对流环境温度", "number", required=False, unit="K", min_value=1e-12),
        InputField("left_heat_transfer_coefficient_w_m2_k", "左侧对流换热系数", "number", required=False, unit="W/(m2*K)", min_value=1e-12),
        InputField("right_boundary_type", "右边界类型", "select", enum=["dirichlet", "heat_flux", "convection"]),
        InputField("right_boundary_temperature_k", "右侧给定温度", "number", required=False, unit="K", min_value=1e-12),
        InputField("right_heat_flux_into_domain_w_m2", "右侧入域热流", "number", required=False, unit="W/m2"),
        InputField("right_ambient_temperature_k", "右侧对流环境温度", "number", required=False, unit="K", min_value=1e-12),
        InputField("right_heat_transfer_coefficient_w_m2_k", "右侧对流换热系数", "number", required=False, unit="W/(m2*K)", min_value=1e-12),
        InputField("snapshot_count", "输出快照数上限", "integer", required=False, default=5, unit="1", min_value=2, max_value=21),
    ]
    output_fields = [
        OutputField("positions_m", "控制体中心位置", "array", "m"),
        OutputField("final_temperature_profile", "最终温度剖面", "array", "position:m; temperature:K"),
        OutputField("snapshots", "有限温度场快照", "array", "time:s; temperature:K"),
        OutputField("minimum_temperature_k", "最终最低温度", "number", "K"),
        OutputField("maximum_temperature_k", "最终最高温度", "number", "K"),
        OutputField("mean_temperature_k", "最终算术平均温度", "number", "K"),
        OutputField("cell_size_m", "控制体宽度", "number", "m"),
        OutputField("thermal_diffusivity_m2_s", "热扩散率", "number", "m2/s"),
        OutputField("maximum_actual_time_step_s", "实际最大时间步", "number", "s"),
        OutputField("maximum_stable_time_step_s", "最大稳定时间步", "number", "s"),
        OutputField("fourier_number", "实际最大Fourier数", "number", "1"),
        OutputField("maximum_stability_coefficient", "最大离散稳定性系数", "number", "1"),
        OutputField("time_steps", "实际步数", "number", "1"),
        OutputField("final_left_heat_flux_into_domain_w_m2", "末态左边界入域热流", "number", "W/m2"),
        OutputField("final_right_heat_flux_into_domain_w_m2", "末态右边界入域热流", "number", "W/m2"),
        OutputField("stored_energy_change_j_m2", "单位面积储能变化", "number", "J/m2"),
        OutputField("cumulative_boundary_energy_in_j_m2", "累计边界入热", "number", "J/m2"),
        OutputField("cumulative_source_energy_in_j_m2", "累计体热源入热", "number", "J/m2"),
        OutputField("energy_closure_residual_j_m2", "能量闭合残差", "number", "J/m2"),
        OutputField("energy_closure_relative", "相对能量闭合残差", "number", "1"),
        OutputField("calculation_method", "计算方法", "string"),
    ]
    validation_rules = [
        {"rule": "constant_positive_properties_and_three_to_501_cells"},
        {"rule": "initial_condition_fields_are_complete_and_exclusive"},
        {"rule": "boundary_fields_are_complete_and_exclusive_for_declared_type"},
        {"rule": "maximum_explicit_diagonal_stability_coefficient_not_greater_than_one"},
        {"rule": "discrete_energy_balance_closes"},
    ]
    _BASE = {
        "length_m": 1.0,
        "node_count": 10,
        "duration_s": 10.0,
        "time_step_s": 0.1,
        "density_kg_m3": 1000,
        "specific_heat_j_kg_k": 1000,
        "thermal_conductivity_w_m_k": 10,
        "initial_condition_mode": "uniform",
        "initial_temperature_k": 500,
        "left_boundary_type": "heat_flux",
        "left_heat_flux_into_domain_w_m2": 0,
        "right_boundary_type": "heat_flux",
        "right_heat_flux_into_domain_w_m2": 0,
    }
    qualification_cases = [
        {"id": "G003-N1", "kind": "normal", "input": _BASE},
        {"id": "G003-N2", "kind": "normal", "input": {"length_m": 1, "node_count": 5, "duration_s": 5, "time_step_s": 0.5, "density_kg_m3": 1000, "specific_heat_j_kg_k": 1000, "thermal_conductivity_w_m_k": 10, "initial_condition_mode": "uniform", "initial_temperature_k": 350, "left_boundary_type": "dirichlet", "left_boundary_temperature_k": 400, "right_boundary_type": "dirichlet", "right_boundary_temperature_k": 300}},
        {"id": "G003-N3", "kind": "normal", "input": {"length_m": 1, "node_count": 10, "duration_s": 10, "time_step_s": 0.1, "density_kg_m3": 1000, "specific_heat_j_kg_k": 1000, "thermal_conductivity_w_m_k": 10, "initial_condition_mode": "uniform", "initial_temperature_k": 300, "volumetric_heat_source_w_m3": 1000, "left_boundary_type": "convection", "left_ambient_temperature_k": 500, "left_heat_transfer_coefficient_w_m2_k": 100, "right_boundary_type": "heat_flux", "right_heat_flux_into_domain_w_m2": 0}},
        {"id": "G003-B1", "kind": "boundary", "input": {**_BASE, "duration_s": 0}},
        {"id": "G003-F1", "kind": "failure", "input": {"length_m": 1, "node_count": 10, "duration_s": 1, "time_step_s": 0.01, "density_kg_m3": 1, "specific_heat_j_kg_k": 1, "thermal_conductivity_w_m_k": 1, "initial_condition_mode": "uniform", "initial_temperature_k": 300, "left_boundary_type": "heat_flux", "left_heat_flux_into_domain_w_m2": 0, "right_boundary_type": "heat_flux", "right_heat_flux_into_domain_w_m2": 0}},
        {"id": "G003-F2", "kind": "failure", "input": {**_BASE, "initial_condition_mode": "profile", "initial_temperature_k": None, "initial_temperature_profile_k": [300, 310, 320]}},
    ]

    @staticmethod
    def _boundary(params: dict, side: str) -> tuple[dict[str, float | str] | None, str | None]:
        boundary_type = params.get(f"{side}_boundary_type")
        field_map = {
            "dirichlet": {"temperature_k": f"{side}_boundary_temperature_k"},
            "heat_flux": {"heat_flux_into_domain_w_m2": f"{side}_heat_flux_into_domain_w_m2"},
            "convection": {
                "ambient_temperature_k": f"{side}_ambient_temperature_k",
                "heat_transfer_coefficient_w_m2_k": f"{side}_heat_transfer_coefficient_w_m2_k",
            },
        }
        required = field_map.get(boundary_type)
        if required is None:
            return None, f"{side}_boundary_type不受支持"
        all_optional = {
            f"{side}_boundary_temperature_k",
            f"{side}_heat_flux_into_domain_w_m2",
            f"{side}_ambient_temperature_k",
            f"{side}_heat_transfer_coefficient_w_m2_k",
        }
        supplied = {key for key in all_optional if params.get(key) is not None}
        expected = set(required.values())
        if supplied != expected:
            return None, f"{side}侧{boundary_type}边界必须且只能提供{sorted(expected)}"
        parsed: dict[str, float | str] = {"type": boundary_type}
        for normalized, key in required.items():
            strict = normalized in {"temperature_k", "ambient_temperature_k", "heat_transfer_coefficient_w_m2_k"}
            value, error = finite(params.get(key), key, minimum=0 if strict else None, strict_minimum=strict)
            if error:
                return None, error
            parsed[normalized] = value
        return parsed, None

    @staticmethod
    def _boundary_heat_flux(boundary: dict[str, float | str], temperature: float, conductivity: float, dx: float) -> float:
        if boundary["type"] == "dirichlet":
            return 2 * conductivity * (float(boundary["temperature_k"]) - temperature) / dx
        if boundary["type"] == "heat_flux":
            return float(boundary["heat_flux_into_domain_w_m2"])
        return float(boundary["heat_transfer_coefficient_w_m2_k"]) * (
            float(boundary["ambient_temperature_k"]) - temperature
        )

    def invoke(self, params, context=None):
        positive_fields = (
            "length_m", "time_step_s", "density_kg_m3", "specific_heat_j_kg_k", "thermal_conductivity_w_m_k"
        )
        values: dict[str, float] = {}
        for key in positive_fields:
            value, error = finite(params.get(key), key, minimum=0, strict_minimum=True)
            if error:
                return fail(error, "OUT_OF_DOMAIN")
            values[key] = value
        duration, error = finite(params.get("duration_s"), "duration_s", minimum=0)
        if error:
            return fail(error, "OUT_OF_DOMAIN")
        nodes, error = integer(params.get("node_count"), "node_count", 3, 501)
        if error:
            return fail(error, "OUT_OF_DOMAIN")
        snapshot_count, error = integer(params.get("snapshot_count", 5), "snapshot_count", 2, 21)
        if error:
            return fail(error, "OUT_OF_DOMAIN")
        mode = params.get("initial_condition_mode")
        uniform = params.get("initial_temperature_k")
        profile = params.get("initial_temperature_profile_k")
        if mode == "uniform":
            if profile is not None:
                return fail("uniform模式不得提供initial_temperature_profile_k")
            temperature, error = finite(uniform, "initial_temperature_k", minimum=0, strict_minimum=True)
            if error:
                return fail(error, "OUT_OF_DOMAIN")
            temperatures = [temperature] * nodes
        elif mode == "profile":
            if uniform is not None:
                return fail("profile模式不得提供initial_temperature_k")
            if not isinstance(profile, list) or len(profile) != nodes:
                return fail("initial_temperature_profile_k长度必须等于node_count")
            temperatures = []
            for index, raw in enumerate(profile):
                value, error = finite(raw, f"initial_temperature_profile_k[{index}]", minimum=0, strict_minimum=True)
                if error:
                    return fail(error, "OUT_OF_DOMAIN")
                temperatures.append(value)
        else:
            return fail("initial_condition_mode必须为uniform或profile")
        left, error = self._boundary(params, "left")
        if error:
            return fail(error)
        right, error = self._boundary(params, "right")
        if error:
            return fail(error)
        source, error = finite(params.get("volumetric_heat_source_w_m3", 0.0), "volumetric_heat_source_w_m3")
        if error:
            return fail(error)
        length = values["length_m"]
        nominal_dt = values["time_step_s"]
        density = values["density_kg_m3"]
        cp = values["specific_heat_j_kg_k"]
        conductivity = values["thermal_conductivity_w_m_k"]
        dx = length / nodes
        diffusivity = conductivity / (density * cp)
        step_count = int(math.ceil(duration / nominal_dt)) if duration > 0 else 0
        if step_count > 200000:
            return fail("显式积分步数超过200000，首版资源上限不适用", "MODEL_NOT_APPLICABLE")
        maximum_actual_dt = min(nominal_dt, duration) if duration > 0 else 0.0
        interior_rate = 2 * diffusivity / dx ** 2

        def boundary_rate(boundary: dict[str, float | str]) -> float:
            if boundary["type"] == "dirichlet":
                return 3 * diffusivity / dx ** 2
            if boundary["type"] == "convection":
                return diffusivity / dx ** 2 + float(boundary["heat_transfer_coefficient_w_m2_k"]) / (density * cp * dx)
            return diffusivity / dx ** 2

        maximum_rate = max(interior_rate, boundary_rate(left), boundary_rate(right))
        maximum_stable_dt = 1 / maximum_rate
        stability = maximum_actual_dt * maximum_rate
        fourier = diffusivity * maximum_actual_dt / dx ** 2
        if stability > 1 + 1e-12:
            return fail(
                f"最大离散稳定性系数{stability:g}超过1；time_step_s必须不大于{maximum_stable_dt:g}",
                "OUT_OF_DOMAIN",
            )
        positions = [(index + 0.5) * dx for index in range(nodes)]
        initial = list(temperatures)
        snapshot_indices = {0, step_count}
        if step_count > 0:
            snapshot_indices.update(round(i * step_count / (snapshot_count - 1)) for i in range(snapshot_count))
        snapshots = [{"time_s": 0.0, "temperatures_k": list(temperatures)}]
        boundary_energy = 0.0
        source_energy = 0.0
        elapsed = 0.0
        for step in range(1, step_count + 1):
            dt = min(nominal_dt, duration - elapsed)
            if dt <= 0:
                break
            left_flux = self._boundary_heat_flux(left, temperatures[0], conductivity, dx)
            right_flux = self._boundary_heat_flux(right, temperatures[-1], conductivity, dx)
            updated = []
            for index, current in enumerate(temperatures):
                incoming = 0.0
                if index == 0:
                    incoming += left_flux
                else:
                    incoming += conductivity * (temperatures[index - 1] - current) / dx
                if index == nodes - 1:
                    incoming += right_flux
                else:
                    incoming += conductivity * (temperatures[index + 1] - current) / dx
                new_temperature = current + dt * (incoming / dx + source) / (density * cp)
                if not math.isfinite(new_temperature) or new_temperature <= 0:
                    return fail("积分产生非有限或非正绝对温度", "NUMERICAL_ERROR")
                updated.append(new_temperature)
            boundary_energy += (left_flux + right_flux) * dt
            source_energy += source * length * dt
            temperatures = updated
            elapsed += dt
            if step in snapshot_indices:
                snapshots.append({"time_s": elapsed, "temperatures_k": list(temperatures)})
        stored = density * cp * dx * math.fsum(final - start for final, start in zip(temperatures, initial))
        residual = stored - boundary_energy - source_energy
        scale = max(1.0, abs(stored), abs(boundary_energy) + abs(source_energy))
        relative = residual / scale
        if abs(relative) > 1e-10:
            return fail("离散能量闭合相对残差超过1e-10", "NUMERICAL_ERROR")
        final_left_flux = self._boundary_heat_flux(left, temperatures[0], conductivity, dx)
        final_right_flux = self._boundary_heat_flux(right, temperatures[-1], conductivity, dx)
        warnings = []
        if duration == 0:
            warnings.append(BoundaryWarning("duration_s", "计算时长为0，返回初始状态边界"))
        elif math.isclose(stability, 1.0, rel_tol=0, abs_tol=1e-12):
            warnings.append(BoundaryWarning("time_step_s", "时间步恰位于显式单调稳定边界"))
        return ModelResult(True, result={
            "positions_m": positions,
            "final_temperature_profile": [
                {"position_m": position, "temperature_k": temperature}
                for position, temperature in zip(positions, temperatures)
            ],
            "snapshots": snapshots,
            "minimum_temperature_k": min(temperatures),
            "maximum_temperature_k": max(temperatures),
            "mean_temperature_k": math.fsum(temperatures) / nodes,
            "cell_size_m": dx,
            "thermal_diffusivity_m2_s": diffusivity,
            "maximum_actual_time_step_s": maximum_actual_dt,
            "maximum_stable_time_step_s": maximum_stable_dt,
            "fourier_number": fourier,
            "maximum_stability_coefficient": stability,
            "time_steps": step_count,
            "final_left_heat_flux_into_domain_w_m2": final_left_flux,
            "final_right_heat_flux_into_domain_w_m2": final_right_flux,
            "stored_energy_change_j_m2": stored,
            "cumulative_boundary_energy_in_j_m2": boundary_energy,
            "cumulative_source_energy_in_j_m2": source_energy,
            "energy_closure_residual_j_m2": residual,
            "energy_closure_relative": relative,
            "calculation_method": "explicit-cell-centred-heat-fvm-v1",
        }, boundary_check=BoundaryCheck(not warnings, warnings))
