"""P1-W15 additive E015/E020/F008/F018 executable tools."""

from __future__ import annotations

import math
from typing import Any

from .base import BaseModelTool, BoundaryCheck, BoundaryWarning, InputField, ModelResult, OutputField
from .repositories.reference_repository import RepositoryError, emission_factors


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


class W15FormulaTool(BaseModelTool):
    priority = "P1"
    status = qualification_status = "qualified"
    count_eligible = True
    data_requirement = "FORMULA_ONLY"
    data_access_mode = "none"


class E015_BFPermeabilityResistanceIndex(W15FormulaTool):
    model_id, name, version = "E015", "单工况高炉料柱透气阻力指数", "1.0.0"
    tool_name = "metallurgy_calculate_bf_permeability_resistance_index"
    scenario = "高炉低碳"
    description = "把单个稳态高炉工况的绝对压力、标况气量和平均气体物性归一化为料柱气体阻力指数，不进行趋势诊断。"
    applicable_boundary = (
        "稳态单快照、理想气体标况换算和料柱平均物性；下部绝压必须高于炉顶绝压。"
        "不处理连续时序、软熔带定位、仪表偏差、漏风、预警或闭环控制。"
    )
    data_source = ["Normalized gas-permeability resistance relation", "Ideal-gas flow conversion"]
    source_version = "bf-single-snapshot-resistance-index-v1"
    formula_reference = (
        "Q_actual=Q_N*(T/T_N)*(P_N/P_avg); u=Q_actual/A; "
        "K=(deltaP/H)/(rho^0.7*mu^0.3*u^1.7)"
    )
    source_records = [
        {
            "source_id": "EPO-EP4477762A1",
            "name": "Blast-furnace gas-permeability resistance expression",
            "version": "EP4477762A1 (2024)",
            "url": "https://data.epo.org/publication-server/rest/v1.2/patents/EP4477762NWA1/document.pdf",
        },
        {"source_id": "IDEAL-GAS-FLOW", "name": "Ideal-gas standard-to-actual volume conversion", "version": "formula-v1"},
    ]
    failure_modes = [
        "下部绝压不高于炉顶绝压或任一压力非正",
        "气量、温度、面积、密度、黏度或有效料柱高度非正",
        "输入并非同一稳态工况或平均物性不具代表性",
        "将归一化阻力指数解释成时序异常、预测或控制指令",
    ]
    independent_validation = [
        "直接代入公开归一化阻力公式复算",
        "相同压力梯度、物性和速度下指数与料柱高度无关",
        "其他量不变时标况气量翻倍使指数乘以2^-1.7",
        "标况—实际流量换算满足理想气体P-Q-T比例",
    ]
    dependencies = []
    relations = [
        rel("overlaps", "E014", "E014从粒径和孔隙率预测Ergun压降；E015从给定压差和流量归一化单工况阻力"),
        rel("context_for", "E001", "可作为同一稳态高炉物料衡算工况的独立透气性约束"),
    ]
    input_fields = [
        InputField("lower_bed_absolute_pressure_pa", "料柱下部绝压", "number", unit="Pa", min_value=1e-12),
        InputField("top_absolute_pressure_pa", "炉顶绝压", "number", unit="Pa", min_value=1e-12),
        InputField("gas_flow_normal_nm3_s", "标况气体体积流量", "number", unit="Nm3/s", min_value=1e-12),
        InputField("average_gas_temperature_k", "料柱平均气温", "number", unit="K", min_value=1e-12),
        InputField("cross_section_area_m2", "等效截面积", "number", unit="m2", min_value=1e-12),
        InputField("gas_density_kg_m3", "平均实际气体密度", "number", unit="kg/m3", min_value=1e-12),
        InputField("gas_dynamic_viscosity_pa_s", "平均气体动力黏度", "number", unit="Pa*s", min_value=1e-18),
        InputField("effective_bed_height_m", "有效料柱高度", "number", unit="m", min_value=1e-12),
        InputField("normal_temperature_k", "标况温度", "number", required=False, default=273.15, unit="K", min_value=1e-12),
        InputField("normal_pressure_pa", "标况压力", "number", required=False, default=101325.0, unit="Pa", min_value=1e-12),
    ]
    output_fields = [
        OutputField("pressure_drop_pa", "料柱压差", "number", "Pa"),
        OutputField("average_absolute_pressure_pa", "平均绝压", "number", "Pa"),
        OutputField("actual_gas_flow_m3_s", "平均状态实际气量", "number", "m3/s"),
        OutputField("superficial_velocity_m_s", "表观速度", "number", "m/s"),
        OutputField("pressure_gradient_pa_m", "压力梯度", "number", "Pa/m"),
        OutputField("permeability_resistance_index", "透气阻力指数", "number", "m^-1.3"),
        OutputField("inverse_resistance_index", "阻力指数倒数", "number", "m^1.3"),
        OutputField("raw_squared_pressure_index", "平方压力原始指数", "number", "Pa2*s^1.7/Nm5.1"),
        OutputField("calculation_method", "计算方法", "string"),
    ]
    validation_rules = [
        {"rule": "lower_absolute_pressure_strictly_greater_than_top"},
        {"rule": "positive_flow_geometry_and_average_properties"},
        {"rule": "single_snapshot_only"},
    ]
    qualification_cases = [
        {"id": "E015-N1", "kind": "normal", "input": {"lower_bed_absolute_pressure_pa": 350000, "top_absolute_pressure_pa": 200000, "gas_flow_normal_nm3_s": 50, "average_gas_temperature_k": 1000, "cross_section_area_m2": 80, "gas_density_kg_m3": 0.45, "gas_dynamic_viscosity_pa_s": 4e-5, "effective_bed_height_m": 20}},
        {"id": "E015-N2", "kind": "normal", "input": {"lower_bed_absolute_pressure_pa": 300000, "top_absolute_pressure_pa": 180000, "gas_flow_normal_nm3_s": 40, "average_gas_temperature_k": 900, "cross_section_area_m2": 60, "gas_density_kg_m3": 0.55, "gas_dynamic_viscosity_pa_s": 3.8e-5, "effective_bed_height_m": 18}},
        {"id": "E015-N3", "kind": "normal", "input": {"lower_bed_absolute_pressure_pa": 420000, "top_absolute_pressure_pa": 250000, "gas_flow_normal_nm3_s": 65, "average_gas_temperature_k": 1100, "cross_section_area_m2": 100, "gas_density_kg_m3": 0.4, "gas_dynamic_viscosity_pa_s": 4.3e-5, "effective_bed_height_m": 24, "normal_temperature_k": 288.15, "normal_pressure_pa": 101325}},
        {"id": "E015-B1", "kind": "boundary", "input": {"lower_bed_absolute_pressure_pa": 200010, "top_absolute_pressure_pa": 200000, "gas_flow_normal_nm3_s": 50, "average_gas_temperature_k": 1000, "cross_section_area_m2": 80, "gas_density_kg_m3": 0.45, "gas_dynamic_viscosity_pa_s": 4e-5, "effective_bed_height_m": 20}},
        {"id": "E015-F1", "kind": "failure", "input": {"lower_bed_absolute_pressure_pa": 180000, "top_absolute_pressure_pa": 200000, "gas_flow_normal_nm3_s": 50, "average_gas_temperature_k": 1000, "cross_section_area_m2": 80, "gas_density_kg_m3": 0.45, "gas_dynamic_viscosity_pa_s": 4e-5, "effective_bed_height_m": 20}},
        {"id": "E015-F2", "kind": "failure", "input": {"lower_bed_absolute_pressure_pa": 350000, "top_absolute_pressure_pa": 200000, "gas_flow_normal_nm3_s": 0, "average_gas_temperature_k": 1000, "cross_section_area_m2": 80, "gas_density_kg_m3": 0.45, "gas_dynamic_viscosity_pa_s": 4e-5, "effective_bed_height_m": 20}},
    ]

    def invoke(self, params, context=None):
        values: dict[str, float] = {}
        for field in self.input_fields:
            raw = params.get(field.name, field.default)
            value, error = finite(raw, field.name, minimum=0, strict_minimum=True)
            if error:
                return fail(error, "OUT_OF_DOMAIN")
            values[field.name] = value
        lower = values["lower_bed_absolute_pressure_pa"]
        top = values["top_absolute_pressure_pa"]
        if lower <= top:
            return fail("lower_bed_absolute_pressure_pa必须严格高于top_absolute_pressure_pa", "OUT_OF_DOMAIN")
        average_pressure = (lower + top) / 2
        actual_flow = values["gas_flow_normal_nm3_s"] * (
            values["average_gas_temperature_k"] / values["normal_temperature_k"]
        ) * (values["normal_pressure_pa"] / average_pressure)
        velocity = actual_flow / values["cross_section_area_m2"]
        pressure_drop = lower - top
        gradient = pressure_drop / values["effective_bed_height_m"]
        resistance = gradient / (
            values["gas_density_kg_m3"] ** 0.7
            * values["gas_dynamic_viscosity_pa_s"] ** 0.3
            * velocity ** 1.7
        )
        raw_index = (lower ** 2 - top ** 2) / values["gas_flow_normal_nm3_s"] ** 1.7
        warnings = []
        if pressure_drop / average_pressure < 1e-4:
            warnings.append(BoundaryWarning("lower_bed_absolute_pressure_pa", "压差低于平均绝压的0.01%，指数对测压分辨率高度敏感"))
        return ModelResult(True, result={
            "pressure_drop_pa": pressure_drop,
            "average_absolute_pressure_pa": average_pressure,
            "actual_gas_flow_m3_s": actual_flow,
            "superficial_velocity_m_s": velocity,
            "pressure_gradient_pa_m": gradient,
            "permeability_resistance_index": resistance,
            "inverse_resistance_index": 1 / resistance,
            "raw_squared_pressure_index": raw_index,
            "calculation_method": "single-snapshot-normalized-resistance-v1",
        }, boundary_check=BoundaryCheck(not warnings, warnings))


class E020_BFCarbonFootprint(BaseModelTool):
    model_id, name, version = "E020", "高炉活动数据碳足迹账本", "1.0.0"
    tool_name = "metallurgy_calculate_bf_carbon_footprint"
    scenario = "高炉低碳"
    priority = "P1"
    status = qualification_status = "qualified"
    count_eligible = True
    model_type = "版本化公开因子/确定性排放账本"
    description = "按声明工序边界读取批准的公开排放因子，对显式活动数据和直接排放逐项计算并汇总高炉碳足迹。"
    applicable_boundary = (
        "透明的活动数据×固定因子账本，不是认证LCA或企业自动盘查。燃料因子只适用于实际燃烧量的NCV能量，"
        "不得把总焦炭/煤装入量直接视作燃烧量；调用方负责边界、避免过程碳与副产煤气燃烧重复计数。"
    )
    data_source = ["IPCC 2006 stationary combustion defaults", "IPCC AR6 GWP100", "China MEE 2024 electricity carbon-footprint factors"]
    source_version = "BF-GHG-FACTORS-W15-2026.09-v1"
    formula_reference = "CO2e_i=q_i*(EF_CO2+EF_CH4*GWP_CH4+EF_N2O*GWP_N2O) or q_i*EF_CO2e; footprint=allocation*(emissions-credits)/hot_metal"
    source_records = [
        {"source_id": "IPCC-2006-V2-C2-T2.3", "name": "2006 IPCC stationary-combustion default factors", "version": "Volume 2 Chapter 2 Table 2.3", "url": "https://www.ipcc-nggip.iges.or.jp/public/2006gl/pdf/2_Volume2/V2_2_Ch2_Stationary_Combustion.pdf"},
        {"source_id": "IPCC-AR6-WGIII-ANNEX-II", "name": "IPCC AR6 GWP100 metric conventions", "version": "AR6 WGIII Annex II", "url": "https://www.ipcc.ch/report/ar6/wg3/downloads/report/IPCC_AR6_WGIII_Annex-II.pdf"},
        {"source_id": "MEE-CN-ELECTRICITY-CF-2024", "name": "生态环境部2024年全国电力碳足迹因子", "version": "2024", "url": "https://www.mee.gov.cn/xxgk2018/xxgk/xxgk01/202510/W020251024569470952545.pdf"},
    ]
    failure_modes = [
        "数据库不可用、因子集/因子代码缺失或记录未批准",
        "活动单位与数据库固定单位不一致",
        "活动或直接排放字段不完整、数值非法、scope或方向非法",
        "热金属产量非正或分配系数不在[0,1]",
        "把燃料总投入量当作燃烧能量，或过程碳与副产气燃烧重复计算",
    ]
    independent_validation = [
        "每项CO2e由数据库气体因子和GWP或直接CO2e因子独立复算",
        "分项之和等于scope汇总之和且排放、信用和净量严格闭合",
        "活动量同比缩放时总排放同比缩放，单位产品足迹保持不变",
        "分配系数只线性缩放净分配量和单位产品足迹",
    ]
    dependencies = ["E003", "E005"]
    relations = [
        rel("accepts_output_from", "E003", "E003碳平衡可形成有执行ID的直接过程CO2e输入；E020不重复求物料碳守恒"),
        rel("accepts_output_from", "E005", "E005氢平衡可辅助界定含氢燃料活动，但E020只计算声明活动的排放"),
        rel("complements", "E001", "E001闭合物料量，E020闭合声明边界内的温室气体账本"),
    ]
    data_requirement = "VERSIONED_DATABASE_REFERENCE"
    data_access_mode = "database_repository"
    required_dataset_ids = ["DS_BF_GHG_FACTORS_W15"]
    database_tables = ["metallurgy_v2.emission_factor"]
    _activity_items = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "factor_code": {"type": "string"},
            "quantity": {"type": "number", "minimum": 0},
            "unit": {"type": "string"},
            "direction": {"type": "string", "enum": ["emission", "credit"]},
        },
        "required": ["name", "factor_code", "quantity", "unit", "direction"],
        "additionalProperties": False,
    }
    _direct_items = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "co2e_kg": {"type": "number", "minimum": 0},
            "scope": {"type": "string", "enum": ["scope1", "scope2", "scope3"]},
            "direction": {"type": "string", "enum": ["emission", "credit"]},
            "source_execution_id": {"type": "string"},
        },
        "required": ["name", "co2e_kg", "scope", "direction", "source_execution_id"],
        "additionalProperties": False,
    }
    input_fields = [
        InputField("hot_metal_output_t", "热金属产量", "number", unit="tHM", min_value=1e-12),
        InputField("factor_set_id", "排放因子集", "select", default="BF_GHG_FACTORS_W15_V1", enum=["BF_GHG_FACTORS_W15_V1"]),
        InputField("boundary_name", "工序边界名称", "string", description="调用方声明的gate-to-gate边界，不得为空"),
        InputField("allocation_fraction", "归属于热金属的分配系数", "number", unit="1", min_value=0, max_value=1),
        InputField("activities", "活动数据", "array", items=_activity_items, min_items=1, description="每项单位必须与数据库因子完全一致"),
        InputField("direct_emissions", "显式直接排放", "array", required=False, items=_direct_items, description="无固定活动因子时由经审计上游执行提供的kgCO2e"),
    ]
    output_fields = [
        OutputField("factor_set_id", "因子集", "string"),
        OutputField("boundary_name", "工序边界", "string"),
        OutputField("allocation_fraction", "分配系数", "number", "1"),
        OutputField("activity_results", "活动分项结果", "array"),
        OutputField("direct_emission_results", "直接排放分项", "array"),
        OutputField("scope_totals_kg_co2e", "各scope净排放", "object", "kgCO2e"),
        OutputField("gross_emissions_kg_co2e", "总排放", "number", "kgCO2e"),
        OutputField("total_credits_kg_co2e", "总信用量", "number", "kgCO2e"),
        OutputField("unallocated_net_kg_co2e", "分配前净排放", "number", "kgCO2e"),
        OutputField("allocated_net_kg_co2e", "分配后净排放", "number", "kgCO2e"),
        OutputField("carbon_footprint_t_co2e_per_t_hm", "单位热金属碳足迹", "number", "tCO2e/tHM"),
        OutputField("hot_metal_output_t", "热金属产量", "number", "tHM"),
        OutputField("ledger_closure_residual_kg_co2e", "账本闭合残差", "number", "kgCO2e"),
        OutputField("factor_versions", "使用的因子版本", "array"),
        OutputField("calculation_method", "计算方法", "string"),
    ]
    validation_rules = [
        {"rule": "approved_database_factor_for_every_activity"},
        {"rule": "exact_activity_unit_match"},
        {"rule": "explicit_boundary_allocation_direction_and_scope"},
        {"rule": "direct_emission_requires_source_execution_id"},
    ]
    _base = {"hot_metal_output_t": 1000, "factor_set_id": "BF_GHG_FACTORS_W15_V1", "boundary_name": "blast-furnace-gate-to-gate", "allocation_fraction": 1.0}
    qualification_cases = [
        {"id": "E020-N1", "kind": "normal", "input": {**_base, "activities": [{"name": "coking coal combustion", "factor_code": "FUEL_COKING_COAL_COMBUSTION_TJ_NCV", "quantity": 10, "unit": "TJ_NCV", "direction": "emission"}]}},
        {"id": "E020-N2", "kind": "normal", "input": {**_base, "activities": [{"name": "purchased electricity", "factor_code": "ELECTRICITY_CN_NATIONAL_2024_KWH", "quantity": 100000, "unit": "kWh", "direction": "emission"}], "direct_emissions": [{"name": "process carbon", "co2e_kg": 200000, "scope": "scope1", "direction": "emission", "source_execution_id": "TRACE-E003-DEMO"}]}},
        {"id": "E020-N3", "kind": "normal", "input": {**_base, "allocation_fraction": 0.8, "activities": [{"name": "natural gas", "factor_code": "FUEL_NATURAL_GAS_COMBUSTION_TJ_NCV", "quantity": 2, "unit": "TJ_NCV", "direction": "emission"}, {"name": "exported electricity credit", "factor_code": "ELECTRICITY_CN_NATIONAL_2024_KWH", "quantity": 10000, "unit": "kWh", "direction": "credit"}]}},
        {"id": "E020-B1", "kind": "boundary", "input": {**_base, "allocation_fraction": 0, "activities": [{"name": "purchased electricity", "factor_code": "ELECTRICITY_CN_NATIONAL_2024_KWH", "quantity": 0, "unit": "kWh", "direction": "emission"}]}},
        {"id": "E020-F1", "kind": "failure", "input": {**_base, "activities": [{"name": "wrong unit", "factor_code": "ELECTRICITY_CN_NATIONAL_2024_KWH", "quantity": 1, "unit": "MWh", "direction": "emission"}]}},
        {"id": "E020-F2", "kind": "failure", "input": {**_base, "activities": [{"name": "unknown", "factor_code": "NOT_A_FACTOR", "quantity": 1, "unit": "kWh", "direction": "emission"}]}},
    ]
    data_qualification_cases = [
        {"id": "E020-D1", "input": qualification_cases[0]["input"]},
        {"id": "E020-D2", "input": qualification_cases[1]["input"]},
    ]

    @staticmethod
    def _validate_rows(raw: Any, direct: bool = False) -> tuple[list[dict[str, Any]] | None, str | None]:
        if raw is None and direct:
            return [], None
        if not isinstance(raw, list) or (not direct and not raw):
            return None, "activities必须是非空数组" if not direct else "direct_emissions必须是数组"
        required = {"name", "co2e_kg", "scope", "direction", "source_execution_id"} if direct else {"name", "factor_code", "quantity", "unit", "direction"}
        rows = []
        for index, item in enumerate(raw):
            if not isinstance(item, dict) or set(item) != required:
                return None, f"第{index + 1}项字段必须且只能为{sorted(required)}"
            if not all(isinstance(item[key], str) and item[key].strip() for key in required - ({"co2e_kg"} if direct else {"quantity"})):
                return None, f"第{index + 1}项字符串字段不得为空"
            if item["direction"] not in {"emission", "credit"}:
                return None, f"第{index + 1}项direction非法"
            if direct and item["scope"] not in {"scope1", "scope2", "scope3"}:
                return None, f"第{index + 1}项scope非法"
            numeric_key = "co2e_kg" if direct else "quantity"
            value, error = finite(item[numeric_key], f"第{index + 1}项{numeric_key}", minimum=0)
            if error:
                return None, error
            rows.append({**item, numeric_key: value})
        return rows, None

    def invoke(self, params, context=None):
        output_t, error = finite(params.get("hot_metal_output_t"), "hot_metal_output_t", minimum=0, strict_minimum=True)
        if error:
            return fail(error, "OUT_OF_DOMAIN")
        allocation, error = finite(params.get("allocation_fraction"), "allocation_fraction", minimum=0, maximum=1)
        if error:
            return fail(error, "OUT_OF_DOMAIN")
        factor_set = params.get("factor_set_id", "BF_GHG_FACTORS_W15_V1")
        if factor_set != "BF_GHG_FACTORS_W15_V1":
            return fail("factor_set_id不是批准版本", "MISSING_DATA")
        boundary = params.get("boundary_name")
        if not isinstance(boundary, str) or not boundary.strip():
            return fail("boundary_name不得为空")
        activities, error = self._validate_rows(params.get("activities"))
        if error:
            return fail(error)
        direct_rows, error = self._validate_rows(params.get("direct_emissions"), direct=True)
        if error:
            return fail(error)
        try:
            factors, provenance = emission_factors((row["factor_code"] for row in activities), factor_set)
        except RepositoryError as exc:
            return fail(str(exc), exc.error_code)
        activity_results = []
        direct_results = []
        scope_totals = {"scope1": 0.0, "scope2": 0.0, "scope3": 0.0}
        gross = 0.0
        credits = 0.0
        versions = set()
        for row in activities:
            factor = factors[row["factor_code"]]
            if row["unit"] != factor["activity_unit"]:
                return fail(f"{row['factor_code']}要求单位{factor['activity_unit']}，收到{row['unit']}", "UNIT_MISMATCH")
            co2_factor = float(factor["co2_kg_per_unit"] or 0)
            ch4_factor = float(factor["ch4_kg_per_unit"] or 0)
            n2o_factor = float(factor["n2o_kg_per_unit"] or 0)
            if factor["co2e_kg_per_unit"] is not None:
                co2e_factor = float(factor["co2e_kg_per_unit"])
                gwp_ch4 = gwp_n2o = None
            else:
                gwp_ch4 = float(factor["gwp_ch4"])
                gwp_n2o = float(factor["gwp_n2o"])
                co2e_factor = co2_factor + ch4_factor * gwp_ch4 + n2o_factor * gwp_n2o
            quantity = row["quantity"]
            co2, ch4, n2o = quantity * co2_factor, quantity * ch4_factor, quantity * n2o_factor
            co2e = quantity * co2e_factor
            sign = 1 if row["direction"] == "emission" else -1
            scope_totals[str(factor["scope"])] += sign * co2e
            if sign > 0:
                gross += co2e
            else:
                credits += co2e
            versions.add(str(factor["source_version"]))
            activity_results.append({
                "name": row["name"], "factor_code": row["factor_code"], "quantity": quantity,
                "unit": row["unit"], "direction": row["direction"], "scope": factor["scope"],
                "co2_kg": co2, "ch4_kg": ch4, "n2o_kg": n2o, "co2e_kg": co2e,
                "co2e_factor_kg_per_unit": co2e_factor, "gwp_ch4": gwp_ch4, "gwp_n2o": gwp_n2o,
                "source_version": factor["source_version"], "applicability": factor["applicability"],
            })
        for row in direct_rows:
            sign = 1 if row["direction"] == "emission" else -1
            scope_totals[row["scope"]] += sign * row["co2e_kg"]
            if sign > 0:
                gross += row["co2e_kg"]
            else:
                credits += row["co2e_kg"]
            direct_results.append(dict(row))
        unallocated = gross - credits
        allocated = unallocated * allocation
        scope_sum = math.fsum(scope_totals.values())
        warnings = []
        if allocation in {0.0, 1.0} or all(row["quantity"] == 0 for row in activities):
            warnings.append(BoundaryWarning("allocation_fraction", "分配系数或活动量位于零/全分配边界，请确认边界与分配声明"))
        return ModelResult(True, result={
            "factor_set_id": factor_set,
            "boundary_name": boundary.strip(),
            "allocation_fraction": allocation,
            "activity_results": activity_results,
            "direct_emission_results": direct_results,
            "scope_totals_kg_co2e": scope_totals,
            "gross_emissions_kg_co2e": gross,
            "total_credits_kg_co2e": credits,
            "unallocated_net_kg_co2e": unallocated,
            "allocated_net_kg_co2e": allocated,
            "carbon_footprint_t_co2e_per_t_hm": allocated / 1000 / output_t,
            "hot_metal_output_t": output_t,
            "ledger_closure_residual_kg_co2e": scope_sum - unallocated,
            "factor_versions": sorted(versions),
            "calculation_method": "versioned-activity-factor-ledger-v1",
        }, boundary_check=BoundaryCheck(not warnings, warnings), provenance=provenance)


class F008_TotalSecondaryCoolingWater(W15FormulaTool):
    model_id, name, version = "F008", "连铸二冷总水量", "1.0.0"
    tool_name = "metallurgy_calculate_total_secondary_cooling_water"
    scenario = "凝固与连铸"
    description = "按铸坯几何和拉速计算钢质量流量，再用比水量或水侧显热平衡求二冷总水量。"
    applicable_boundary = "稳态总量级设计；不分区、不模拟喷嘴、不拟合历史浇次、不预测表面温度，也不向阀门或PLC下发设定。"
    data_source = ["Steady mass flow", "Cooling-water sensible heat balance"]
    source_version = "secondary-cooling-total-water-v1"
    formula_reference = "m_steel=n*A*v*rho; Vw[m3/h]=specific_water[L/kg]*m_steel[kg/s]*3.6; mw=Vw*rho_w; heat mode: mw=m_steel*q_specific/(cp*deltaT)"
    source_records = [
        {"source_id": "MASS-FLOW-CONTINUITY", "name": "Steady strand mass-flow continuity", "version": "formula-v1"},
        {"source_id": "WATER-SENSIBLE-HEAT", "name": "Cooling-water sensible heat balance", "version": "formula-v1"},
    ]
    failure_modes = [
        "流股数、断面、拉速、钢密度或水物性非法",
        "比水量模式缺少比水量或混入热平衡专用字段",
        "热平衡模式缺少目标比移热/水温/水物性或水温升非正",
        "把总水量结果解释为分区配水、温度场或控制设定",
    ]
    independent_validation = [
        "钢质量流量由断面面积、拉速、密度和流股数独立复算",
        "specific_water模式的L/kg与m3/h单位换算独立复算",
        "构造相同水量的两种模式应返回相同总水量",
        "流股数或拉速同比缩放使钢流量和总水量同比缩放",
    ]
    dependencies = ["F003", "F005"]
    relations = [
        rel("accepts_output_from", "F005", "F005单位钢移热可作为heat_balance模式的目标比移热输入"),
        rel("complements", "F003", "F003计算凝固热状态；F008计算给定热负荷或比水量下的总水量"),
        rel("upstream_of", "F007", "F008总量可作为水路设计基准；F007从水路实测/显式流量反算移热"),
    ]
    input_fields = [
        InputField("calculation_mode", "计算模式", "select", enum=["specific_water", "heat_balance"]),
        InputField("strand_count", "流股数", "integer", unit="1", min_value=1, max_value=16),
        InputField("section_width_m", "铸坯宽度", "number", unit="m", min_value=1e-12),
        InputField("section_thickness_m", "铸坯厚度", "number", unit="m", min_value=1e-12),
        InputField("casting_speed_m_s", "拉速", "number", unit="m/s", min_value=1e-12),
        InputField("steel_density_kg_m3", "钢密度", "number", unit="kg/m3", min_value=1e-12),
        InputField("specific_water_l_kg", "比水量", "number", required=False, unit="L/kg_steel", min_value=0),
        InputField("target_heat_removed_kj_kg", "目标比移热", "number", required=False, unit="kJ/kg_steel", min_value=0),
        InputField("water_inlet_temperature_k", "进水温度", "number", required=False, unit="K", min_value=1e-12),
        InputField("water_outlet_temperature_k", "出水温度", "number", required=False, unit="K", min_value=1e-12),
        InputField("water_specific_heat_kj_kg_k", "水比热", "number", required=False, default=4.18, unit="kJ/(kg*K)", min_value=1e-12),
        InputField("water_density_kg_m3", "水密度", "number", required=False, default=998.0, unit="kg/m3", min_value=1e-12),
    ]
    output_fields = [
        OutputField("calculation_mode", "计算模式", "string"),
        OutputField("strand_count", "流股数", "number", "1"),
        OutputField("section_area_per_strand_m2", "单流股断面面积", "number", "m2"),
        OutputField("steel_mass_flow_kg_s", "总钢质量流量", "number", "kg/s"),
        OutputField("total_water_mass_flow_kg_s", "总水质量流量", "number", "kg/s"),
        OutputField("total_water_flow_m3_h", "总水体积流量", "number", "m3/h"),
        OutputField("water_flow_per_strand_m3_h", "单流股水量", "number", "m3/h"),
        OutputField("specific_water_l_kg", "比水量", "number", "L/kg_steel"),
        OutputField("specific_heat_removed_kj_kg", "比移热", "number", "kJ/kg_steel"),
        OutputField("total_heat_duty_kw", "总热负荷", "number", "kW"),
        OutputField("water_temperature_rise_k", "水温升", "number", "K", nullable=True),
        OutputField("energy_closure_residual_kw", "能量闭合残差", "number", "kW"),
        OutputField("calculation_method", "计算方法", "string"),
    ]
    validation_rules = [
        {"rule": "positive_geometry_speed_density_and_integer_strands"},
        {"rule": "mode_specific_fields_are_complete_and_exclusive"},
        {"rule": "heat_balance_requires_positive_water_temperature_rise"},
    ]
    qualification_cases = [
        {"id": "F008-N1", "kind": "normal", "input": {"calculation_mode": "specific_water", "strand_count": 1, "section_width_m": 1.5, "section_thickness_m": 0.2, "casting_speed_m_s": 0.02, "steel_density_kg_m3": 7400, "specific_water_l_kg": 1.0}},
        {"id": "F008-N2", "kind": "normal", "input": {"calculation_mode": "heat_balance", "strand_count": 2, "section_width_m": 0.15, "section_thickness_m": 0.15, "casting_speed_m_s": 0.04, "steel_density_kg_m3": 7400, "target_heat_removed_kj_kg": 100, "water_inlet_temperature_k": 293.15, "water_outlet_temperature_k": 303.15}},
        {"id": "F008-N3", "kind": "normal", "input": {"calculation_mode": "specific_water", "strand_count": 4, "section_width_m": 0.16, "section_thickness_m": 0.16, "casting_speed_m_s": 0.05, "steel_density_kg_m3": 7300, "specific_water_l_kg": 0.8, "water_density_kg_m3": 995}},
        {"id": "F008-B1", "kind": "boundary", "input": {"calculation_mode": "specific_water", "strand_count": 1, "section_width_m": 0.1, "section_thickness_m": 0.1, "casting_speed_m_s": 0.01, "steel_density_kg_m3": 7000, "specific_water_l_kg": 0}},
        {"id": "F008-F1", "kind": "failure", "input": {"calculation_mode": "heat_balance", "strand_count": 1, "section_width_m": 1.5, "section_thickness_m": 0.2, "casting_speed_m_s": 0.02, "steel_density_kg_m3": 7400, "target_heat_removed_kj_kg": 100, "water_inlet_temperature_k": 300, "water_outlet_temperature_k": 300}},
        {"id": "F008-F2", "kind": "failure", "input": {"calculation_mode": "specific_water", "strand_count": 1, "section_width_m": 1.5, "section_thickness_m": 0.2, "casting_speed_m_s": 0.02, "steel_density_kg_m3": 7400, "specific_water_l_kg": 1.0, "target_heat_removed_kj_kg": 100}},
    ]

    def invoke(self, params, context=None):
        mode = params.get("calculation_mode")
        if mode not in {"specific_water", "heat_balance"}:
            return fail("calculation_mode必须为specific_water或heat_balance")
        strands_raw = params.get("strand_count")
        if isinstance(strands_raw, bool):
            return fail("strand_count必须是整数")
        try:
            strands = int(strands_raw)
        except (TypeError, ValueError):
            return fail("strand_count必须是整数")
        if strands != strands_raw or not 1 <= strands <= 16:
            return fail("strand_count必须是1至16的整数", "OUT_OF_DOMAIN")
        values = {}
        for key in ("section_width_m", "section_thickness_m", "casting_speed_m_s", "steel_density_kg_m3"):
            value, error = finite(params.get(key), key, minimum=0, strict_minimum=True)
            if error:
                return fail(error, "OUT_OF_DOMAIN")
            values[key] = value
        water_density, error = finite(params.get("water_density_kg_m3", 998.0), "water_density_kg_m3", minimum=0, strict_minimum=True)
        if error:
            return fail(error, "OUT_OF_DOMAIN")
        area = values["section_width_m"] * values["section_thickness_m"]
        steel_flow = strands * area * values["casting_speed_m_s"] * values["steel_density_kg_m3"]
        warnings = []
        if mode == "specific_water":
            forbidden = {"target_heat_removed_kj_kg", "water_inlet_temperature_k", "water_outlet_temperature_k"} & set(params)
            if forbidden:
                return fail(f"specific_water模式不得提交: {', '.join(sorted(forbidden))}")
            specific, error = finite(params.get("specific_water_l_kg"), "specific_water_l_kg", minimum=0)
            if error:
                return fail(error)
            water_volume_flow_l_s = specific * steel_flow
            water_mass_flow = water_volume_flow_l_s * water_density / 1000
            cp, error = finite(params.get("water_specific_heat_kj_kg_k", 4.18), "water_specific_heat_kj_kg_k", minimum=0, strict_minimum=True)
            if error:
                return fail(error)
            delta_t = None
            heat_duty = 0.0
            specific_heat = 0.0
            method = "specified-specific-water-v1"
            if specific == 0:
                warnings.append(BoundaryWarning("specific_water_l_kg", "零比水量仅作为数学边界，不代表可行二冷工况"))
        else:
            if "specific_water_l_kg" in params:
                return fail("heat_balance模式不得提交specific_water_l_kg")
            target, error = finite(params.get("target_heat_removed_kj_kg"), "target_heat_removed_kj_kg", minimum=0)
            if error:
                return fail(error)
            inlet, error = finite(params.get("water_inlet_temperature_k"), "water_inlet_temperature_k", minimum=0, strict_minimum=True)
            if error:
                return fail(error)
            outlet, error = finite(params.get("water_outlet_temperature_k"), "water_outlet_temperature_k", minimum=0, strict_minimum=True)
            if error:
                return fail(error)
            cp, error = finite(params.get("water_specific_heat_kj_kg_k", 4.18), "water_specific_heat_kj_kg_k", minimum=0, strict_minimum=True)
            if error:
                return fail(error)
            delta_t = outlet - inlet
            if delta_t <= 0:
                return fail("water_outlet_temperature_k必须高于water_inlet_temperature_k", "OUT_OF_DOMAIN")
            heat_duty = steel_flow * target
            water_mass_flow = heat_duty / (cp * delta_t)
            specific = water_mass_flow / water_density * 1000 / steel_flow
            specific_heat = target
            method = "water-sensible-heat-balance-v1"
        water_flow_m3_h = water_mass_flow / water_density * 3600
        residual = heat_duty - water_mass_flow * cp * (delta_t or 0)
        return ModelResult(True, result={
            "calculation_mode": mode,
            "strand_count": strands,
            "section_area_per_strand_m2": area,
            "steel_mass_flow_kg_s": steel_flow,
            "total_water_mass_flow_kg_s": water_mass_flow,
            "total_water_flow_m3_h": water_flow_m3_h,
            "water_flow_per_strand_m3_h": water_flow_m3_h / strands,
            "specific_water_l_kg": specific,
            "specific_heat_removed_kj_kg": specific_heat,
            "total_heat_duty_kw": heat_duty,
            "water_temperature_rise_k": delta_t,
            "energy_closure_residual_kw": residual,
            "calculation_method": method,
        }, boundary_check=BoundaryCheck(not warnings, warnings))


class F018_InclusionFloatTime(W15FormulaTool):
    model_id, name, version = "F018", "球形夹杂物上浮时间", "1.0.0"
    tool_name = "metallurgy_calculate_inclusion_float_time"
    scenario = "凝固与连铸"
    description = "用Stokes初值和Schiller–Naumann阻力迭代求刚性球形轻质夹杂在牛顿钢液中的终端上浮速度与运动学到达时间。"
    applicable_boundary = "稀相刚性球、均匀牛顿流体、恒定物性与均匀竖直流；终端Re≤800。不输出经验捕获概率或质量标签预测。"
    data_source = ["Stokes terminal velocity", "Schiller-Naumann drag correlation"]
    source_version = "stokes-schiller-naumann-float-v1"
    formula_reference = "Re=rho*v*d/mu; Cd=24/Re*(1+0.15*Re^0.687); v=sqrt(4*g*d*(rho-rho_p)/(3*Cd*rho)); t=L/(v+u_bulk)"
    source_records = [
        {"source_id": "STOKES-1851", "name": "Stokes terminal velocity for a sphere", "version": "creeping-flow formula"},
        {"source_id": "SCHILLER-NAUMANN-1935", "name": "Schiller-Naumann drag relation", "version": "Cd=24/Re(1+0.15Re^0.687), restricted here to Re<=800", "url": "https://doi.org/10.1007/s00348-021-03274-9"},
    ]
    failure_modes = [
        "夹杂密度不小于钢液密度或任一物性/尺寸非正",
        "终端Re超过800或阻力迭代不收敛",
        "把稀相球形终端速度模型用于团聚、湍流弥散、界面反应或非牛顿钢液",
        "把停留时间覆盖分数解释为捕获概率",
    ]
    independent_validation = [
        "低Re极限与Stokes解析速度对照",
        "终端状态浮力与阻力相对残差接近零",
        "恒速条件下上浮距离翻倍使时间翻倍",
        "均匀竖直钢液速度只线性改变净速度而不改变滑移终端速度",
    ]
    dependencies = ["C008"]
    relations = [
        rel("accepts_output_from", "C008", "C008动力黏度可作为钢液黏度输入，调用方应保留来源执行ID"),
        rel("complements", "C002", "C002给出扩散系数；F018给出浮力—阻力控制的颗粒宏观迁移时间"),
        rel("complements", "C010", "C010处理填充床传质；F018处理单个球形夹杂终端运动"),
    ]
    input_fields = [
        InputField("inclusion_diameter_m", "夹杂直径", "number", unit="m", min_value=1e-12),
        InputField("inclusion_density_kg_m3", "夹杂密度", "number", unit="kg/m3", min_value=1e-12),
        InputField("liquid_steel_density_kg_m3", "钢液密度", "number", unit="kg/m3", min_value=1e-12),
        InputField("dynamic_viscosity_pa_s", "钢液动力黏度", "number", unit="Pa*s", min_value=1e-12),
        InputField("float_distance_m", "上浮距离", "number", unit="m", min_value=0),
        InputField("vertical_bulk_velocity_m_s", "钢液竖直速度", "number", required=False, default=0.0, unit="m/s", description="向上为正、向下为负"),
        InputField("available_residence_time_s", "可用停留时间", "number", required=False, unit="s", min_value=0),
    ]
    output_fields = [
        OutputField("terminal_slip_velocity_m_s", "终端滑移上浮速度", "number", "m/s"),
        OutputField("vertical_bulk_velocity_m_s", "钢液竖直速度", "number", "m/s"),
        OutputField("net_upward_velocity_m_s", "净上浮速度", "number", "m/s"),
        OutputField("particle_reynolds_number", "颗粒Reynolds数", "number", "1"),
        OutputField("drag_coefficient", "阻力系数", "number", "1"),
        OutputField("stokes_velocity_m_s", "Stokes解析速度", "number", "m/s"),
        OutputField("float_time_s", "到达时间", "number", "s", nullable=True),
        OutputField("can_reach_surface", "是否可到达", "boolean"),
        OutputField("residence_time_coverage_fraction", "停留时间运动学覆盖分数", "number", "1", nullable=True),
        OutputField("force_balance_relative_residual", "终端力平衡相对残差", "number", "1"),
        OutputField("iterations", "迭代次数", "number", "1"),
        OutputField("drag_regime", "阻力关联区间", "string"),
        OutputField("calculation_method", "计算方法", "string"),
    ]
    validation_rules = [
        {"rule": "light_rigid_sphere_in_newtonian_liquid"},
        {"rule": "terminal_reynolds_number_not_above_800"},
        {"rule": "nonpositive_net_velocity_is_valid_cannot_reach_result"},
    ]
    qualification_cases = [
        {"id": "F018-N1", "kind": "normal", "input": {"inclusion_diameter_m": 2e-5, "inclusion_density_kg_m3": 3900, "liquid_steel_density_kg_m3": 7000, "dynamic_viscosity_pa_s": 0.006, "float_distance_m": 1.0}},
        {"id": "F018-N2", "kind": "normal", "input": {"inclusion_diameter_m": 1e-4, "inclusion_density_kg_m3": 3000, "liquid_steel_density_kg_m3": 7000, "dynamic_viscosity_pa_s": 0.007, "float_distance_m": 0.8, "vertical_bulk_velocity_m_s": 0.001, "available_residence_time_s": 600}},
        {"id": "F018-N3", "kind": "normal", "input": {"inclusion_diameter_m": 5e-4, "inclusion_density_kg_m3": 2500, "liquid_steel_density_kg_m3": 6900, "dynamic_viscosity_pa_s": 0.005, "float_distance_m": 0.5, "available_residence_time_s": 30}},
        {"id": "F018-B1", "kind": "boundary", "input": {"inclusion_diameter_m": 1e-4, "inclusion_density_kg_m3": 3000, "liquid_steel_density_kg_m3": 7000, "dynamic_viscosity_pa_s": 0.007, "float_distance_m": 0.8, "vertical_bulk_velocity_m_s": -0.02, "available_residence_time_s": 600}},
        {"id": "F018-F1", "kind": "failure", "input": {"inclusion_diameter_m": 1e-4, "inclusion_density_kg_m3": 7500, "liquid_steel_density_kg_m3": 7000, "dynamic_viscosity_pa_s": 0.007, "float_distance_m": 0.8}},
        {"id": "F018-F2", "kind": "failure", "input": {"inclusion_diameter_m": 0.02, "inclusion_density_kg_m3": 1000, "liquid_steel_density_kg_m3": 7000, "dynamic_viscosity_pa_s": 0.001, "float_distance_m": 1.0}},
    ]

    def invoke(self, params, context=None):
        values = {}
        for key in ("inclusion_diameter_m", "inclusion_density_kg_m3", "liquid_steel_density_kg_m3", "dynamic_viscosity_pa_s"):
            value, error = finite(params.get(key), key, minimum=0, strict_minimum=True)
            if error:
                return fail(error, "OUT_OF_DOMAIN")
            values[key] = value
        distance, error = finite(params.get("float_distance_m"), "float_distance_m", minimum=0)
        if error:
            return fail(error, "OUT_OF_DOMAIN")
        bulk, error = finite(params.get("vertical_bulk_velocity_m_s", 0), "vertical_bulk_velocity_m_s")
        if error:
            return fail(error)
        residence = None
        if "available_residence_time_s" in params:
            residence, error = finite(params["available_residence_time_s"], "available_residence_time_s", minimum=0)
            if error:
                return fail(error, "OUT_OF_DOMAIN")
        rho_p, rho, mu, diameter = values["inclusion_density_kg_m3"], values["liquid_steel_density_kg_m3"], values["dynamic_viscosity_pa_s"], values["inclusion_diameter_m"]
        if rho_p >= rho:
            return fail("inclusion_density_kg_m3必须小于liquid_steel_density_kg_m3", "OUT_OF_DOMAIN")
        gravity = 9.80665
        delta_rho = rho - rho_p
        stokes = delta_rho * gravity * diameter ** 2 / (18 * mu)
        velocity = stokes
        converged = False
        iterations = 0
        for iterations in range(1, 101):
            reynolds = rho * velocity * diameter / mu
            if reynolds <= 0:
                return fail("终端Reynolds数非正", "NUMERICAL_ERROR")
            cd = 24 / reynolds * (1 + 0.15 * reynolds ** 0.687)
            updated = math.sqrt(4 * gravity * diameter * delta_rho / (3 * cd * rho))
            if abs(updated - velocity) <= 1e-12 * max(1.0, updated):
                velocity = updated
                converged = True
                break
            velocity = 0.5 * (velocity + updated)
        if not converged:
            return fail("Schiller-Naumann终端速度迭代未收敛", "NUMERICAL_ERROR")
        reynolds = rho * velocity * diameter / mu
        if reynolds > 800:
            return fail(f"终端Reynolds数{reynolds:g}超过首版上限800", "OUT_OF_DOMAIN")
        cd = 24 / reynolds * (1 + 0.15 * reynolds ** 0.687)
        buoyancy = math.pi / 6 * diameter ** 3 * delta_rho * gravity
        drag = 0.5 * cd * rho * math.pi / 4 * diameter ** 2 * velocity ** 2
        force_residual = (buoyancy - drag) / buoyancy
        net = velocity + bulk
        can_reach = distance == 0 or net > 0
        float_time = 0.0 if distance == 0 else distance / net if can_reach else None
        coverage = None
        if residence is not None:
            coverage = 1.0 if distance == 0 else min(1.0, max(0.0, residence * max(net, 0) / distance))
        warnings = []
        if not can_reach or distance == 0:
            warnings.append(BoundaryWarning("vertical_bulk_velocity_m_s", "净速度不向上或距离为零，返回运动学边界结果"))
        regime = "stokes_limit" if reynolds < 0.1 else "schiller_naumann"
        return ModelResult(True, result={
            "terminal_slip_velocity_m_s": velocity,
            "vertical_bulk_velocity_m_s": bulk,
            "net_upward_velocity_m_s": net,
            "particle_reynolds_number": reynolds,
            "drag_coefficient": cd,
            "stokes_velocity_m_s": stokes,
            "float_time_s": float_time,
            "can_reach_surface": can_reach,
            "residence_time_coverage_fraction": coverage,
            "force_balance_relative_residual": force_residual,
            "iterations": iterations,
            "drag_regime": regime,
            "calculation_method": "stokes-initialized-schiller-naumann-v1",
        }, boundary_check=BoundaryCheck(not warnings, warnings))
