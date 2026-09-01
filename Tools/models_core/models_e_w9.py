"""P1-W9 auditable blast-furnace operating, heat, fuel, gas and pressure tools."""

from __future__ import annotations

import math
from typing import Any, Optional

from .base import BaseModelTool, BoundaryCheck, BoundaryWarning, InputField, ModelResult, OutputField


SCENARIO = "高炉低碳"


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


class W9BFFormulaTool(BaseModelTool):
    scenario = SCENARIO
    priority = "P1"
    status = "qualified"
    qualification_status = "qualified"
    count_eligible = True
    data_requirement = "FORMULA_ONLY"
    data_access_mode = "none"


class E006_RistOperatingLine(W9BFFormulaTool):
    model_id, name, version = "E006", "简化C-O Rist操作线", "1.0.0"
    tool_name = "metallurgy_construct_bf_rist_operating_line"
    description = "按每kmol Fe的碳氧守恒重建简化高炉Rist操作线，并以炉顶CO/CO2状态点审计闭合。"
    applicable_boundary = "稳态简化C-O Rist图；不含H2注入、热约束、Si/Mn/P还原和直接还原分解。"
    data_source = ["Rist carbon-oxygen operating-line balance", "Blast-furnace top-gas carbon and oxygen balance"]
    source_version = "simplified-C-O-Rist-v1"
    formula_reference = "Y=n_C_g*X-n_O_B; X_g=(n_CO+2n_CO2)/(n_CO+n_CO2); Y_x=n_O_burden/n_Fe"
    source_records = [
        {"source_id": "RIST-CO-BALANCE", "name": "Modern Blast Furnace Ironmaking - Rist C/O balance appendix", "version": "4th edition", "url": "https://www.rexresearch1.com/IronSteelManufactureLibrary/ModernBlastFurnaceIronmakingIntroductionGeerdes.pdf"},
        {"source_id": "RIST-EXTENDED-2023", "name": "Revisiting the Rist diagram for predicting operating conditions in blast furnaces with multiple injections", "version": "2023", "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC10445826/"},
    ]
    failure_modes = ["Fe基准非正", "氧或炉顶气量为负", "CO与CO2总碳为零", "不同统计基准混用"]
    independent_validation = ["操作线斜率等于炉顶气碳量/Fe量", "炉顶气O/C由CO和CO2原子数直接复算", "状态点残差等于气体输出氧减鼓风和炉料输入氧", "所有kmol量同比缩放时操作线不变"]
    dependencies = ["E003", "E004"]
    relations = [
        rel("depends_on", "E003", "炉顶气碳量和Fe基准可由高炉碳平衡提供"),
        rel("depends_on", "E004", "鼓风及炉料氧量可由高炉氧平衡提供"),
        rel("upstream_of", "E007", "操作线可与分区热平衡组合形成热约束Rist分析"),
    ]
    input_fields = [
        InputField("iron_basis_kmol", "Fe统计基准", "number", unit="kmol Fe/$basis", min_value=1e-12),
        InputField("blast_oxygen_atom_kmol", "鼓风输入氧原子量", "number", unit="kmol O atoms/$basis", min_value=0),
        InputField("burden_oxygen_atom_kmol", "炉料Fe结合氧原子量", "number", unit="kmol O atoms/$basis", min_value=0),
        InputField("top_gas_co_kmol", "炉顶CO量", "number", unit="kmol CO/$basis", min_value=0),
        InputField("top_gas_co2_kmol", "炉顶CO2量", "number", unit="kmol CO2/$basis", min_value=0),
        InputField("closure_tolerance_o_per_fe", "状态点闭合容差", "number", required=False, default=1e-8, unit="kmol O/kmol Fe", min_value=0),
    ]
    output_fields = [
        OutputField("iron_basis_kmol", "Fe统计基准", "number", "kmol Fe/$basis"),
        OutputField("active_top_gas_carbon_per_iron", "操作线斜率", "number", "kmol C/kmol Fe"),
        OutputField("y_intercept", "操作线Y截距", "number", "kmol O/kmol Fe"),
        OutputField("top_gas_oxygen_per_carbon", "炉顶气O/C", "number", "kmol O/kmol C"),
        OutputField("burden_oxygen_per_iron", "炉料O/Fe", "number", "kmol O/kmol Fe"),
        OutputField("predicted_oxygen_per_iron", "操作线状态点Y", "number", "kmol O/kmol Fe"),
        OutputField("state_point_residual_o_per_fe", "状态点残差", "number", "kmol O/kmol Fe"),
        OutputField("line_points", "操作线端点", "array"),
        OutputField("passed", "C-O状态点是否闭合", "boolean"),
    ]
    validation_rules = [{"rule": "positive_iron_and_nonnegative_moles"}, {"rule": "nonzero_top_gas_carbon"}]
    qualification_cases = [
        {"id": "E006-N1", "kind": "normal", "input": {"iron_basis_kmol": 1, "blast_oxygen_atom_kmol": 1, "burden_oxygen_atom_kmol": 1.5, "top_gas_co_kmol": 1.5, "top_gas_co2_kmol": 0.5}},
        {"id": "E006-N2", "kind": "normal", "input": {"iron_basis_kmol": 2, "blast_oxygen_atom_kmol": 1, "burden_oxygen_atom_kmol": 3, "top_gas_co_kmol": 4, "top_gas_co2_kmol": 0}},
        {"id": "E006-N3", "kind": "normal", "input": {"iron_basis_kmol": 1, "blast_oxygen_atom_kmol": 0.5, "burden_oxygen_atom_kmol": 1.5, "top_gas_co_kmol": 1, "top_gas_co2_kmol": 0.5}},
        {"id": "E006-B1", "kind": "boundary", "input": {"iron_basis_kmol": 1, "blast_oxygen_atom_kmol": 1, "burden_oxygen_atom_kmol": 1.4, "top_gas_co_kmol": 1.5, "top_gas_co2_kmol": 0.5}},
        {"id": "E006-F1", "kind": "failure", "input": {"iron_basis_kmol": 1, "blast_oxygen_atom_kmol": 1, "burden_oxygen_atom_kmol": 1, "top_gas_co_kmol": 0, "top_gas_co2_kmol": 0}},
    ]

    def invoke(self, params, context=None):
        values = {}
        for name in ("iron_basis_kmol", "blast_oxygen_atom_kmol", "burden_oxygen_atom_kmol", "top_gas_co_kmol", "top_gas_co2_kmol"):
            value, error = finite(params.get(name), name, minimum=0, strict_minimum=name == "iron_basis_kmol")
            if error:
                return fail(error)
            values[name] = value
        carbon = values["top_gas_co_kmol"] + values["top_gas_co2_kmol"]
        if carbon <= 0:
            return fail("CO与CO2总碳量必须大于0", "DIVISION_BY_ZERO")
        iron = values["iron_basis_kmol"]
        slope = carbon / iron
        intercept = -values["blast_oxygen_atom_kmol"] / iron
        x_g = (values["top_gas_co_kmol"] + 2 * values["top_gas_co2_kmol"]) / carbon
        burden_y = values["burden_oxygen_atom_kmol"] / iron
        predicted_y = slope * x_g + intercept
        residual = predicted_y - burden_y
        tolerance = float(params.get("closure_tolerance_o_per_fe", 1e-8))
        passed = abs(residual) <= tolerance
        warnings = [] if passed else [BoundaryWarning("state_point", "炉顶气状态点不在声明的C-O操作线上")]
        return ModelResult(True, result={
            "iron_basis_kmol": iron,
            "active_top_gas_carbon_per_iron": slope,
            "y_intercept": intercept,
            "top_gas_oxygen_per_carbon": x_g,
            "burden_oxygen_per_iron": burden_y,
            "predicted_oxygen_per_iron": predicted_y,
            "state_point_residual_o_per_fe": residual,
            "line_points": [{"x_o_per_c": 0.0, "y_o_per_fe": intercept}, {"x_o_per_c": 2.0, "y_o_per_fe": 2 * slope + intercept}],
            "passed": passed,
        }, boundary_check=BoundaryCheck(passed, warnings))


class E007_BFZonalHeatBalance(W9BFFormulaTool):
    model_id, name, version = "E007", "高炉两区静态热平衡", "1.0.0"
    tool_name = "metallurgy_audit_bf_zonal_heat_balance"
    description = "对高炉高温区和低温区两个控制体执行显式热项与区间传热的静态能量闭合审计。"
    applicable_boundary = "同一稳态统计基准；各热项已由物性工具或实测值统一为kJ；区间热量正方向固定为高温区流向低温区。"
    data_source = ["First-law control-volume energy balance", "Blast-furnace zonal heat-balance method"]
    source_version = "two-zone-steady-control-volume-v1"
    formula_reference = "R_high=sum(Qin_high)-sum(Qout_high)-Q_interface; R_low=sum(Qin_low)+Q_interface-sum(Qout_low); R_total=R_high+R_low"
    source_records = [
        {"source_id": "FIRST-LAW-CONTROL-VOLUME", "name": "Steady-flow energy conservation", "version": "v1"},
        {"source_id": "BF-ZONAL-HEAT-BALANCE", "name": "Mathematical Model of a Blast Furnace in the Zone above the Tuyere Level", "version": "Journal of the Japan Institute of Metals and Materials", "url": "https://cir.nii.ac.jp/crid/1390282681459571584"},
    ]
    failure_modes = ["铁水基准非正", "热项为空、名称重复或能量为负", "容差无效", "统计基准或焓参考态混用"]
    independent_validation = ["区间传热在全炉总平衡中严格抵消", "两区残差之和等于全炉残差", "有用热效率等于非loss外部热输出/外部热输入", "所有热项同比缩放时闭合率和效率不变", "热项拆分合并不改变残差"]
    dependencies = ["B003", "B006", "T001", "T002"]
    relations = [
        rel("depends_on", "B003", "物流显热可由B003计算"),
        rel("depends_on", "B006", "反应热可由B006计算"),
        rel("depends_on", "T001", "炉壁导热损失可由T001提供"),
        rel("depends_on", "T002", "辐射损失可由T002提供"),
        rel("overlaps", "D002", "均执行热平衡，但D002针对BOF装料与终温，本工具针对BF两区控制体"),
        rel("overlaps", "E006", "两区热约束可与Rist物料操作线组合"),
    ]
    input_fields = [
        InputField("hot_metal_mass_kg", "铁水产量", "number", unit="kg/$basis", min_value=1e-12),
        InputField("high_zone_heat_inputs", "高温区外部热输入", "array", items={"type": "object"}, min_items=1, description="[{name,category,heat_kj}]"),
        InputField("high_zone_heat_outputs", "高温区外部热输出", "array", items={"type": "object"}, min_items=1, description="[{name,category,heat_kj}]"),
        InputField("low_zone_heat_inputs", "低温区外部热输入", "array", items={"type": "object"}, min_items=1, description="[{name,category,heat_kj}]"),
        InputField("low_zone_heat_outputs", "低温区外部热输出", "array", items={"type": "object"}, min_items=1, description="[{name,category,heat_kj}]"),
        InputField("high_to_low_interface_heat_kj", "高温区传向低温区热量", "number", unit="kJ/$basis", min_value=0),
        InputField("absolute_tolerance_kj", "绝对闭合容差", "number", required=False, default=1e-6, unit="kJ/$basis", min_value=0),
        InputField("relative_tolerance", "相对闭合容差", "number", required=False, default=1e-8, unit="1", min_value=0, max_value=1),
    ]
    output_fields = [
        OutputField("normalized_heat_terms", "规范化分区热项", "object"),
        OutputField("high_zone_heat_input_kj", "高温区总热输入", "number", "kJ/$basis"),
        OutputField("high_zone_heat_output_kj", "高温区总热输出含界面", "number", "kJ/$basis"),
        OutputField("high_zone_residual_kj", "高温区残差", "number", "kJ/$basis"),
        OutputField("low_zone_heat_input_kj", "低温区总热输入含界面", "number", "kJ/$basis"),
        OutputField("low_zone_heat_output_kj", "低温区总热输出", "number", "kJ/$basis"),
        OutputField("low_zone_residual_kj", "低温区残差", "number", "kJ/$basis"),
        OutputField("overall_external_heat_input_kj", "全炉外部热输入", "number", "kJ/$basis"),
        OutputField("overall_external_heat_output_kj", "全炉外部热输出", "number", "kJ/$basis"),
        OutputField("overall_residual_kj", "全炉热残差", "number", "kJ/$basis"),
        OutputField("overall_residual_kj_per_t_hot_metal", "吨铁热残差", "number", "kJ/t_hot_metal"),
        OutputField("overall_useful_heat_efficiency", "全炉有用热效率", "number", "1"),
        OutputField("high_zone_passed", "高温区是否闭合", "boolean"),
        OutputField("low_zone_passed", "低温区是否闭合", "boolean"),
        OutputField("overall_passed", "全炉是否闭合", "boolean"),
    ]
    validation_rules = [{"rule": "nonnegative_explicit_heat_terms"}, {"rule": "single_basis_and_reference_state"}]
    qualification_cases = [
        {"id": "E007-N1", "kind": "normal", "input": {"hot_metal_mass_kg": 1000, "high_zone_heat_inputs": [{"name": "combustion", "category": "reaction", "heat_kj": 100}], "high_zone_heat_outputs": [{"name": "hot_products", "category": "sensible", "heat_kj": 20}], "low_zone_heat_inputs": [{"name": "upper_reaction", "category": "reaction", "heat_kj": 10}], "low_zone_heat_outputs": [{"name": "top_gas", "category": "sensible", "heat_kj": 90}], "high_to_low_interface_heat_kj": 80}},
        {"id": "E007-N2", "kind": "normal", "input": {"hot_metal_mass_kg": 500, "high_zone_heat_inputs": [{"name": "blast", "category": "sensible", "heat_kj": 50}], "high_zone_heat_outputs": [{"name": "metal", "category": "sensible", "heat_kj": 50}], "low_zone_heat_inputs": [{"name": "burden", "category": "sensible", "heat_kj": 25}], "low_zone_heat_outputs": [{"name": "gas", "category": "sensible", "heat_kj": 25}], "high_to_low_interface_heat_kj": 0}},
        {"id": "E007-N3", "kind": "normal", "input": {"hot_metal_mass_kg": 2000, "high_zone_heat_inputs": [{"name": "raceway", "category": "reaction", "heat_kj": 300}, {"name": "hot_blast", "category": "sensible", "heat_kj": 100}], "high_zone_heat_outputs": [{"name": "reduction", "category": "reaction", "heat_kj": 250}], "low_zone_heat_inputs": [{"name": "upper_heat", "category": "reaction", "heat_kj": 20}], "low_zone_heat_outputs": [{"name": "burden_heating", "category": "sensible", "heat_kj": 170}], "high_to_low_interface_heat_kj": 150}},
        {"id": "E007-B1", "kind": "boundary", "input": {"hot_metal_mass_kg": 1000, "high_zone_heat_inputs": [{"name": "in", "category": "other", "heat_kj": 100}], "high_zone_heat_outputs": [{"name": "out", "category": "other", "heat_kj": 20}], "low_zone_heat_inputs": [{"name": "in2", "category": "other", "heat_kj": 0}], "low_zone_heat_outputs": [{"name": "out2", "category": "other", "heat_kj": 70}], "high_to_low_interface_heat_kj": 80}},
        {"id": "E007-F1", "kind": "failure", "input": {"hot_metal_mass_kg": 1000, "high_zone_heat_inputs": [{"name": "duplicate", "category": "other", "heat_kj": 100}, {"name": "duplicate", "category": "other", "heat_kj": 1}], "high_zone_heat_outputs": [{"name": "out", "category": "other", "heat_kj": 100}], "low_zone_heat_inputs": [{"name": "in", "category": "other", "heat_kj": 1}], "low_zone_heat_outputs": [{"name": "out", "category": "other", "heat_kj": 1}], "high_to_low_interface_heat_kj": 0}},
    ]
    _CATEGORIES = {"sensible", "reaction", "phase_change", "loss", "electrical", "other"}

    @classmethod
    def _heat_terms(cls, raw, label):
        if not isinstance(raw, list) or not raw:
            return None, f"{label}必须是非空数组"
        rows, names = [], set()
        for index, item in enumerate(raw):
            if not isinstance(item, dict):
                return None, f"{label}[{index}]必须是对象"
            name, category = item.get("name"), item.get("category")
            if not isinstance(name, str) or not name.strip():
                return None, f"{label}[{index}].name必须是唯一非空字符串"
            name = name.strip()
            if name in names:
                return None, f"{label}[{index}].name必须是唯一非空字符串"
            if category not in cls._CATEGORIES:
                return None, f"{label}[{index}].category不受支持"
            heat, error = finite(item.get("heat_kj"), f"{label}[{index}].heat_kj", minimum=0)
            if error:
                return None, error
            names.add(name)
            rows.append({"name": name, "category": category, "heat_kj": heat})
        return rows, None

    def invoke(self, params, context=None):
        hot_mass, error = finite(params.get("hot_metal_mass_kg"), "hot_metal_mass_kg", minimum=0, strict_minimum=True)
        if error:
            return fail(error)
        parsed = {}
        for key in ("high_zone_heat_inputs", "high_zone_heat_outputs", "low_zone_heat_inputs", "low_zone_heat_outputs"):
            rows, error = self._heat_terms(params.get(key), key)
            if error:
                return fail(error)
            parsed[key] = rows
        interface, error = finite(params.get("high_to_low_interface_heat_kj"), "high_to_low_interface_heat_kj", minimum=0)
        if error:
            return fail(error)
        high_external_in = math.fsum(x["heat_kj"] for x in parsed["high_zone_heat_inputs"])
        high_external_out = math.fsum(x["heat_kj"] for x in parsed["high_zone_heat_outputs"])
        low_external_in = math.fsum(x["heat_kj"] for x in parsed["low_zone_heat_inputs"])
        low_external_out = math.fsum(x["heat_kj"] for x in parsed["low_zone_heat_outputs"])
        high_in, high_out = high_external_in, high_external_out + interface
        low_in, low_out = low_external_in + interface, low_external_out
        high_residual, low_residual = high_in - high_out, low_in - low_out
        overall_in, overall_out = high_external_in + low_external_in, high_external_out + low_external_out
        if overall_in <= 0:
            return fail("全炉外部热输入必须大于0", "DIVISION_BY_ZERO")
        overall_residual = overall_in - overall_out
        useful_output = math.fsum(
            item["heat_kj"]
            for key in ("high_zone_heat_outputs", "low_zone_heat_outputs")
            for item in parsed[key]
            if item["category"] != "loss"
        )
        absolute = float(params.get("absolute_tolerance_kj", 1e-6))
        relative = float(params.get("relative_tolerance", 1e-8))

        def closed(residual, incoming, outgoing):
            return abs(residual) <= max(absolute, relative * max(incoming, outgoing, 1.0))

        high_passed = closed(high_residual, high_in, high_out)
        low_passed = closed(low_residual, low_in, low_out)
        overall_passed = closed(overall_residual, overall_in, overall_out)
        warnings = []
        if not high_passed:
            warnings.append(BoundaryWarning("high_zone", "高温区热量未闭合"))
        if not low_passed:
            warnings.append(BoundaryWarning("low_zone", "低温区热量未闭合"))
        if not overall_passed:
            warnings.append(BoundaryWarning("overall", "全炉外部热量未闭合"))
        return ModelResult(True, result={
            "normalized_heat_terms": parsed,
            "high_zone_heat_input_kj": high_in,
            "high_zone_heat_output_kj": high_out,
            "high_zone_residual_kj": high_residual,
            "low_zone_heat_input_kj": low_in,
            "low_zone_heat_output_kj": low_out,
            "low_zone_residual_kj": low_residual,
            "overall_external_heat_input_kj": overall_in,
            "overall_external_heat_output_kj": overall_out,
            "overall_residual_kj": overall_residual,
            "overall_residual_kj_per_t_hot_metal": overall_residual / hot_mass * 1000,
            "overall_useful_heat_efficiency": useful_output / overall_in,
            "high_zone_passed": high_passed,
            "low_zone_passed": low_passed,
            "overall_passed": overall_passed,
        }, boundary_check=BoundaryCheck(not warnings, warnings))


class E009_PCIEquivalentReplacement(W9BFFormulaTool):
    model_id, name, version = "E009", "喷煤理论等效替代", "1.0.0"
    tool_name = "metallurgy_calculate_pci_theoretical_replacement"
    description = "按固定碳、有效低位热值或双重限制计算喷煤的理论焦炭等效替代量，并显式报告未燃碳。"
    applicable_boundary = "静态理论当量，不预测实际焦比；煤/焦分析、燃尽率和有效热利用率必须显式提供。"
    data_source = ["Fixed-carbon conservation", "Effective lower-heating-value equivalence", "Published PCI replacement-ratio analysis"]
    source_version = "explicit-carbon-energy-equivalence-v1"
    formula_reference = "R_C=wC_coal*burnout/wC_coke; R_Q=LHV_coal*eta_coal/(LHV_coke*eta_coke); R_dual=min(R_C,R_Q)"
    source_records = [
        {"source_id": "PCI-REPLACEMENT-2017", "name": "New concept about replacement ratio between coke and coal", "version": "2017", "url": "https://doi.org/10.13228/j.boyuan.issn1001-0963.20160245"},
        {"source_id": "CARBON-ENERGY-CONSERVATION", "name": "Carbon and effective-energy equivalence", "version": "v1"},
    ]
    failure_modes = ["喷煤量或LHV无效", "质量分数、燃尽率或效率越界", "焦炭固定碳或有效热值为零", "把理论替代量解释为实测焦比变化"]
    independent_validation = ["碳基替代量的有效固定碳与被替焦炭固定碳严格相等", "热值基替代量的有效能量严格相等", "双重限制结果不大于任一单基准结果", "喷煤量同比缩放时替代比不变且替代量同比缩放"]
    dependencies = ["E003", "E007"]
    relations = [
        rel("overlaps", "E003", "固定碳替代遵循高炉碳平衡"),
        rel("overlaps", "E007", "有效热值替代可作为高炉热平衡方案项"),
        rel("upstream_of", "E001", "替代后的焦煤物流可进入总物料平衡"),
    ]
    input_fields = [
        InputField("coal_injection_kg", "喷煤量", "number", unit="kg/$basis", min_value=0),
        InputField("coal_fixed_carbon_fraction", "煤固定碳质量分数", "number", unit="1", min_value=0, max_value=1),
        InputField("coal_burnout_fraction", "煤燃尽率", "number", unit="1", min_value=0, max_value=1),
        InputField("coke_fixed_carbon_fraction", "焦炭固定碳质量分数", "number", unit="1", min_value=1e-12, max_value=1),
        InputField("coal_lhv_mj_kg", "煤低位热值", "number", unit="MJ/kg", min_value=1e-12),
        InputField("coke_lhv_mj_kg", "焦炭低位热值", "number", unit="MJ/kg", min_value=1e-12),
        InputField("coal_heat_utilization_fraction", "煤有效热利用率", "number", unit="1", min_value=0, max_value=1),
        InputField("coke_heat_utilization_fraction", "焦炭有效热利用率", "number", unit="1", min_value=1e-12, max_value=1),
        InputField("replacement_basis", "替代基准", "select", enum=["fixed_carbon", "effective_lhv", "dual_limit"]),
    ]
    output_fields = [
        OutputField("replacement_basis", "替代基准", "string"),
        OutputField("fixed_carbon_replacement_ratio", "碳基替代比", "number", "kg coke/kg coal"),
        OutputField("effective_lhv_replacement_ratio", "热值基替代比", "number", "kg coke/kg coal"),
        OutputField("selected_replacement_ratio", "所选理论替代比", "number", "kg coke/kg coal"),
        OutputField("theoretical_coke_replaced_kg", "理论替代焦炭量", "number", "kg/$basis"),
        OutputField("coal_effective_fixed_carbon_kg", "煤有效固定碳", "number", "kg C/$basis"),
        OutputField("coal_unburned_fixed_carbon_kg", "煤未燃固定碳", "number", "kg C/$basis"),
        OutputField("coal_effective_energy_mj", "煤有效热量", "number", "MJ/$basis"),
        OutputField("limiting_basis", "限制基准", "string"),
    ]
    validation_rules = [{"rule": "fractions_within_zero_one"}, {"rule": "positive_coke_denominators"}]
    qualification_cases = [
        {"id": "E009-N1", "kind": "normal", "input": {"coal_injection_kg": 100, "coal_fixed_carbon_fraction": 0.75, "coal_burnout_fraction": 0.9, "coke_fixed_carbon_fraction": 0.85, "coal_lhv_mj_kg": 28, "coke_lhv_mj_kg": 29, "coal_heat_utilization_fraction": 0.8, "coke_heat_utilization_fraction": 0.9, "replacement_basis": "fixed_carbon"}},
        {"id": "E009-N2", "kind": "normal", "input": {"coal_injection_kg": 150, "coal_fixed_carbon_fraction": 0.7, "coal_burnout_fraction": 0.85, "coke_fixed_carbon_fraction": 0.88, "coal_lhv_mj_kg": 30, "coke_lhv_mj_kg": 28, "coal_heat_utilization_fraction": 0.75, "coke_heat_utilization_fraction": 0.85, "replacement_basis": "effective_lhv"}},
        {"id": "E009-N3", "kind": "normal", "input": {"coal_injection_kg": 50, "coal_fixed_carbon_fraction": 0.8, "coal_burnout_fraction": 1, "coke_fixed_carbon_fraction": 0.9, "coal_lhv_mj_kg": 27, "coke_lhv_mj_kg": 30, "coal_heat_utilization_fraction": 0.9, "coke_heat_utilization_fraction": 0.9, "replacement_basis": "dual_limit"}},
        {"id": "E009-B1", "kind": "boundary", "input": {"coal_injection_kg": 100, "coal_fixed_carbon_fraction": 0.75, "coal_burnout_fraction": 0, "coke_fixed_carbon_fraction": 0.85, "coal_lhv_mj_kg": 28, "coke_lhv_mj_kg": 29, "coal_heat_utilization_fraction": 0, "coke_heat_utilization_fraction": 0.9, "replacement_basis": "dual_limit"}},
        {"id": "E009-F1", "kind": "failure", "input": {"coal_injection_kg": 100, "coal_fixed_carbon_fraction": 1.1, "coal_burnout_fraction": 0.9, "coke_fixed_carbon_fraction": 0.85, "coal_lhv_mj_kg": 28, "coke_lhv_mj_kg": 29, "coal_heat_utilization_fraction": 0.8, "coke_heat_utilization_fraction": 0.9, "replacement_basis": "fixed_carbon"}},
    ]

    def invoke(self, params, context=None):
        values = {}
        for field in self.input_fields:
            if field.type != "number":
                continue
            value, error = finite(params.get(field.name), field.name, minimum=field.min_value, maximum=field.max_value)
            if error:
                return fail(error)
            values[field.name] = value
        if values["coke_fixed_carbon_fraction"] <= 0 or values["coke_lhv_mj_kg"] * values["coke_heat_utilization_fraction"] <= 0:
            return fail("焦炭固定碳和有效热值必须大于0", "DIVISION_BY_ZERO")
        carbon_ratio = values["coal_fixed_carbon_fraction"] * values["coal_burnout_fraction"] / values["coke_fixed_carbon_fraction"]
        heat_ratio = values["coal_lhv_mj_kg"] * values["coal_heat_utilization_fraction"] / (values["coke_lhv_mj_kg"] * values["coke_heat_utilization_fraction"])
        basis = params["replacement_basis"]
        selected = carbon_ratio if basis == "fixed_carbon" else heat_ratio if basis == "effective_lhv" else min(carbon_ratio, heat_ratio)
        limiting = "fixed_carbon" if carbon_ratio <= heat_ratio else "effective_lhv"
        if basis != "dual_limit":
            limiting = basis
        coal_mass = values["coal_injection_kg"]
        effective_carbon = coal_mass * values["coal_fixed_carbon_fraction"] * values["coal_burnout_fraction"]
        unburned = coal_mass * values["coal_fixed_carbon_fraction"] * (1 - values["coal_burnout_fraction"])
        warnings = []
        if values["coal_burnout_fraction"] in {0.0, 1.0} or values["coal_heat_utilization_fraction"] in {0.0, 1.0}:
            warnings.append(BoundaryWarning("coal_performance", "燃尽率或热利用率位于声明边界"))
        return ModelResult(True, result={
            "replacement_basis": basis,
            "fixed_carbon_replacement_ratio": carbon_ratio,
            "effective_lhv_replacement_ratio": heat_ratio,
            "selected_replacement_ratio": selected,
            "theoretical_coke_replaced_kg": coal_mass * selected,
            "coal_effective_fixed_carbon_kg": effective_carbon,
            "coal_unburned_fixed_carbon_kg": unburned,
            "coal_effective_energy_mj": coal_mass * values["coal_lhv_mj_kg"] * values["coal_heat_utilization_fraction"],
            "limiting_basis": limiting,
        }, boundary_check=BoundaryCheck(not warnings, warnings))


class E012_TuyereTheoreticalGas(W9BFFormulaTool):
    model_id, name, version = "E012", "风口前理论煤气量", "1.0.0"
    tool_name = "metallurgy_calculate_bf_tuyere_theoretical_gas"
    description = "按干鼓风、富氧、水蒸气及燃料C/H/O/N原子守恒计算完全耗氧生成CO/H2/N2的理论风口煤气量。"
    applicable_boundary = "风口回旋区完全耗氧；气相产物限定为CO/H2/N2；不含CO2、CH4、硫物种、灰分气化、漏风和上升过程反应。"
    data_source = ["C/H/O/N atom conservation", "Ideal-gas normal molar-volume conversion", "Published blast-furnace belly-gas balance"]
    source_version = "tuyere-atom-balance-CO-H2-N2-v1"
    formula_reference = "n_CO=n_O,atoms; n_H2=(n_H,fuel+2n_H2O)/2; n_N2=n_N2,blast+n_N,fuel/2; V_N=n_total*V_m,N"
    source_records = [
        {"source_id": "BF-BELLY-GAS-2022", "name": "Numerical Analysis of Natural Gas Injection in Shougang Jingtang Blast Furnace", "version": "Metals 12 (2022) 2107", "url": "https://doi.org/10.3390/met12122107"},
        {"source_id": "ATOM-CONSERVATION", "name": "Conservation of C/H/O/N atoms", "version": "v1"},
    ]
    failure_modes = ["标况体积或组成无效", "燃料元素量为负或含未声明元素", "可用碳不足以将氧全部转为CO", "总理论煤气量为零"]
    independent_validation = ["C/H/O/N四个原子残差均为零", "干鼓风N2全部进入理论煤气N2", "标况摩尔体积只线性缩放体积而不改变kmol和组成", "所有物质量同比缩放时组成不变"]
    dependencies = ["A006", "A007", "E003", "E004", "E005"]
    relations = [
        rel("depends_on", "A006", "产物假设可由反应配平校验"),
        rel("depends_on", "A007", "完全耗氧的碳需求遵循氧当量"),
        rel("upstream_of", "E003", "CO与未反应碳可进入高炉碳平衡"),
        rel("upstream_of", "E004", "理论煤气氧去向可进入高炉氧平衡"),
        rel("upstream_of", "E005", "H2量可进入高炉氢平衡"),
    ]
    input_fields = [
        InputField("dry_blast_nm3", "干鼓风标况体积", "number", unit="Nm3/$basis", min_value=0),
        InputField("dry_blast_oxygen_mole_fraction", "干风O2摩尔分数", "number", unit="1", min_value=0, max_value=1),
        InputField("supplemental_oxygen_nm3", "富氧标况体积", "number", unit="Nm3 O2/$basis", min_value=0),
        InputField("steam_kmol", "鼓风水蒸气", "number", unit="kmol H2O/$basis", min_value=0),
        InputField("fuel_element_atoms_kmol", "燃料元素原子量", "object", description="{C,H,O,N}，单位均为kmol atoms/$basis，C必填"),
        InputField("normal_molar_volume_nm3_kmol", "标况摩尔体积", "number", required=False, default=22.414, unit="Nm3/kmol", min_value=1e-12),
    ]
    output_fields = [
        OutputField("component_amounts_kmol", "理论煤气分量", "object"),
        OutputField("component_volumes_nm3", "理论煤气分量体积", "object"),
        OutputField("total_theoretical_gas_kmol", "理论煤气总量", "number", "kmol/$basis"),
        OutputField("total_theoretical_gas_nm3", "理论煤气总体积", "number", "Nm3/$basis"),
        OutputField("gas_mole_fractions", "理论煤气摩尔组成", "object"),
        OutputField("carbon_required_kmol", "完全耗氧所需碳", "number", "kmol C/$basis"),
        OutputField("unreacted_carbon_kmol", "未反应碳", "number", "kmol C/$basis"),
        OutputField("input_oxygen_atom_kmol", "输入氧原子量", "number", "kmol O atoms/$basis"),
        OutputField("atom_balance_residuals_kmol", "C/H/O/N原子残差", "object"),
        OutputField("normal_molar_volume_nm3_kmol", "所用标况摩尔体积", "number", "Nm3/kmol"),
    ]
    validation_rules = [{"rule": "nonnegative_declared_CHON_atoms"}, {"rule": "enough_carbon_for_complete_oxygen_consumption"}]
    qualification_cases = [
        {"id": "E012-N1", "kind": "normal", "input": {"dry_blast_nm3": 22.414, "dry_blast_oxygen_mole_fraction": 0.21, "supplemental_oxygen_nm3": 0, "steam_kmol": 0, "fuel_element_atoms_kmol": {"C": 0.5, "H": 0, "O": 0, "N": 0}}},
        {"id": "E012-N2", "kind": "normal", "input": {"dry_blast_nm3": 22.414, "dry_blast_oxygen_mole_fraction": 0.21, "supplemental_oxygen_nm3": 0, "steam_kmol": 0.1, "fuel_element_atoms_kmol": {"C": 0.6, "H": 0.2, "O": 0, "N": 0}}},
        {"id": "E012-N3", "kind": "normal", "input": {"dry_blast_nm3": 0, "dry_blast_oxygen_mole_fraction": 0.21, "supplemental_oxygen_nm3": 11.207, "steam_kmol": 0, "fuel_element_atoms_kmol": {"C": 1.2, "H": 0.4, "O": 0, "N": 0.2}}},
        {"id": "E012-B1", "kind": "boundary", "input": {"dry_blast_nm3": 22.414, "dry_blast_oxygen_mole_fraction": 0.21, "supplemental_oxygen_nm3": 0, "steam_kmol": 0, "fuel_element_atoms_kmol": {"C": 0.42, "H": 0, "O": 0, "N": 0}}},
        {"id": "E012-F1", "kind": "failure", "input": {"dry_blast_nm3": 22.414, "dry_blast_oxygen_mole_fraction": 0.21, "supplemental_oxygen_nm3": 0, "steam_kmol": 0, "fuel_element_atoms_kmol": {"C": 0.2, "H": 0, "O": 0, "N": 0}}},
    ]

    def invoke(self, params, context=None):
        numeric = {}
        for field in self.input_fields:
            if field.type != "number":
                continue
            value, error = finite(params.get(field.name, field.default), field.name, minimum=field.min_value, maximum=field.max_value)
            if error:
                return fail(error)
            numeric[field.name] = value
        raw_elements = params.get("fuel_element_atoms_kmol")
        if not isinstance(raw_elements, dict) or "C" not in raw_elements:
            return fail("fuel_element_atoms_kmol必须是含C的对象")
        unknown = sorted(set(raw_elements) - {"C", "H", "O", "N"})
        if unknown:
            return fail(f"燃料元素暂不支持: {', '.join(unknown)}", "OUT_OF_DOMAIN")
        elements = {}
        for symbol in ("C", "H", "O", "N"):
            value, error = finite(raw_elements.get(symbol, 0), f"fuel_element_atoms_kmol.{symbol}", minimum=0)
            if error:
                return fail(error)
            elements[symbol] = value
        vm = numeric["normal_molar_volume_nm3_kmol"]
        blast_kmol = numeric["dry_blast_nm3"] / vm
        blast_o2 = blast_kmol * numeric["dry_blast_oxygen_mole_fraction"]
        blast_n2 = blast_kmol - blast_o2
        supplemental_o2 = numeric["supplemental_oxygen_nm3"] / vm
        oxygen_atoms = 2 * (blast_o2 + supplemental_o2) + numeric["steam_kmol"] + elements["O"]
        carbon_required = oxygen_atoms
        if elements["C"] + 1e-12 < carbon_required:
            return fail(f"燃料碳{elements['C']:g} kmol不足以消耗输入氧，至少需要{carbon_required:g} kmol", "OUT_OF_DOMAIN")
        co = carbon_required
        h2 = (elements["H"] + 2 * numeric["steam_kmol"]) / 2
        n2 = blast_n2 + elements["N"] / 2
        components = {"CO": co, "H2": h2, "N2": n2}
        total = math.fsum(components.values())
        if total <= 0:
            return fail("理论煤气总量为零", "DIVISION_BY_ZERO")
        unreacted = elements["C"] - co
        residuals = {
            "C": elements["C"] - co - unreacted,
            "H": elements["H"] + 2 * numeric["steam_kmol"] - 2 * h2,
            "O": oxygen_atoms - co,
            "N": 2 * blast_n2 + elements["N"] - 2 * n2,
        }
        warnings = []
        if abs(unreacted) <= 1e-12:
            warnings.append(BoundaryWarning("fuel_element_atoms_kmol.C", "燃料碳恰好等于完全耗氧的理论下限"))
        return ModelResult(True, result={
            "component_amounts_kmol": components,
            "component_volumes_nm3": {key: value * vm for key, value in components.items()},
            "total_theoretical_gas_kmol": total,
            "total_theoretical_gas_nm3": total * vm,
            "gas_mole_fractions": {key: value / total for key, value in components.items()},
            "carbon_required_kmol": carbon_required,
            "unreacted_carbon_kmol": unreacted,
            "input_oxygen_atom_kmol": oxygen_atoms,
            "atom_balance_residuals_kmol": residuals,
            "normal_molar_volume_nm3_kmol": vm,
        }, boundary_check=BoundaryCheck(not warnings, warnings))


class E014_ErgunPressureDrop(W9BFFormulaTool):
    model_id, name, version = "E014", "料柱Ergun压降", "1.0.0"
    tool_name = "metallurgy_calculate_bf_burden_ergun_pressure_drop"
    description = "按Ergun方程计算高炉料柱等效填充床的黏性压降、惯性压降和总压降。"
    applicable_boundary = "稳态单相填充床或以平均物性近似；不含软熔带收缩、粒径分布、非均匀布料、壁面效应和强可压缩性。"
    data_source = ["Ergun packed-column pressure-drop equation"]
    source_version = "Ergun-1952"
    formula_reference = "dP/L=150*mu*u*(1-eps)^2/(eps^3*d_eff^2)+1.75*rho*u^2*(1-eps)/(eps^3*d_eff); d_eff=phi*d_p"
    source_records = [
        {"source_id": "ERGUN-1952", "name": "Fluid Flow Through Packed Columns", "version": "Chemical Engineering Progress 48 (1952) 89-94", "url": "https://pubs.acs.org/doi/10.1021/ie50474a011"},
    ]
    failure_modes = ["粒径、速度、密度、黏度或床高非正", "孔隙率不在(0,1)", "球形度不在(0,1]", "把平均物性结果用于强可压缩长床层"]
    independent_validation = ["总压降等于黏性项与惯性项之和", "黏性项与速度一次方成正比且惯性项与速度平方成正比", "床层总压降与高度线性缩放", "颗粒Re等于rho*u*d_eff/mu"]
    dependencies = []
    relations = [
        rel("overlaps", "C010", "共用填充床粒径和流体物性，但E014计算动量损失而C010计算传质"),
        rel("upstream_of", "E001", "压降不改变E001质量平衡，但可作为同一稳态工况的可行性约束"),
    ]
    input_fields = [
        InputField("particle_diameter_m", "颗粒名义直径", "number", unit="m", min_value=1e-12),
        InputField("sphericity", "颗粒球形度", "number", unit="1", min_value=1e-12, max_value=1),
        InputField("void_fraction", "料柱孔隙率", "number", unit="1", min_value=1e-12, max_value=0.999999999999),
        InputField("superficial_velocity_m_s", "气体表观速度", "number", unit="m/s", min_value=1e-12),
        InputField("gas_density_kg_m3", "气体平均密度", "number", unit="kg/m3", min_value=1e-12),
        InputField("gas_dynamic_viscosity_pa_s", "气体动力黏度", "number", unit="Pa*s", min_value=1e-18),
        InputField("bed_height_m", "料柱高度", "number", unit="m", min_value=1e-12),
    ]
    output_fields = [
        OutputField("effective_particle_diameter_m", "球形度修正粒径", "number", "m"),
        OutputField("particle_reynolds_number", "颗粒Reynolds数", "number", "1"),
        OutputField("viscous_pressure_gradient_pa_m", "黏性压降梯度", "number", "Pa/m"),
        OutputField("inertial_pressure_gradient_pa_m", "惯性压降梯度", "number", "Pa/m"),
        OutputField("total_pressure_gradient_pa_m", "总压降梯度", "number", "Pa/m"),
        OutputField("viscous_pressure_drop_pa", "黏性压降", "number", "Pa"),
        OutputField("inertial_pressure_drop_pa", "惯性压降", "number", "Pa"),
        OutputField("total_pressure_drop_pa", "总压降", "number", "Pa"),
        OutputField("dominant_term", "主导项", "string"),
    ]
    validation_rules = [{"rule": "positive_packed_bed_properties"}, {"rule": "zero_less_void_fraction_and_sphericity_le_one"}]
    qualification_cases = [
        {"id": "E014-N1", "kind": "normal", "input": {"particle_diameter_m": 0.02, "sphericity": 1, "void_fraction": 0.4, "superficial_velocity_m_s": 1, "gas_density_kg_m3": 1.2, "gas_dynamic_viscosity_pa_s": 1.8e-5, "bed_height_m": 10}},
        {"id": "E014-N2", "kind": "normal", "input": {"particle_diameter_m": 0.04, "sphericity": 0.8, "void_fraction": 0.35, "superficial_velocity_m_s": 0.5, "gas_density_kg_m3": 0.8, "gas_dynamic_viscosity_pa_s": 2.5e-5, "bed_height_m": 20}},
        {"id": "E014-N3", "kind": "normal", "input": {"particle_diameter_m": 0.01, "sphericity": 0.9, "void_fraction": 0.5, "superficial_velocity_m_s": 2, "gas_density_kg_m3": 2, "gas_dynamic_viscosity_pa_s": 3e-5, "bed_height_m": 5}},
        {"id": "E014-B1", "kind": "boundary", "input": {"particle_diameter_m": 0.02, "sphericity": 1, "void_fraction": 0.05, "superficial_velocity_m_s": 1, "gas_density_kg_m3": 1.2, "gas_dynamic_viscosity_pa_s": 1.8e-5, "bed_height_m": 10}},
        {"id": "E014-F1", "kind": "failure", "input": {"particle_diameter_m": 0.02, "sphericity": 1, "void_fraction": 1, "superficial_velocity_m_s": 1, "gas_density_kg_m3": 1.2, "gas_dynamic_viscosity_pa_s": 1.8e-5, "bed_height_m": 10}},
    ]

    def invoke(self, params, context=None):
        values = {}
        for field in self.input_fields:
            value, error = finite(params.get(field.name), field.name, minimum=field.min_value, maximum=field.max_value)
            if error:
                return fail(error)
            values[field.name] = value
        eps = values["void_fraction"]
        if not 0 < eps < 1:
            return fail("void_fraction必须严格位于(0,1)", "OUT_OF_DOMAIN")
        effective_d = values["particle_diameter_m"] * values["sphericity"]
        u, rho, mu = values["superficial_velocity_m_s"], values["gas_density_kg_m3"], values["gas_dynamic_viscosity_pa_s"]
        viscous = 150 * mu * u * (1 - eps) ** 2 / (eps ** 3 * effective_d ** 2)
        inertial = 1.75 * rho * u ** 2 * (1 - eps) / (eps ** 3 * effective_d)
        total_gradient = viscous + inertial
        height = values["bed_height_m"]
        warnings = []
        if eps < 0.1 or eps > 0.8:
            warnings.append(BoundaryWarning("void_fraction", "孔隙率处于极端区间，应审查均匀填充床假设"))
        return ModelResult(True, result={
            "effective_particle_diameter_m": effective_d,
            "particle_reynolds_number": rho * u * effective_d / mu,
            "viscous_pressure_gradient_pa_m": viscous,
            "inertial_pressure_gradient_pa_m": inertial,
            "total_pressure_gradient_pa_m": total_gradient,
            "viscous_pressure_drop_pa": viscous * height,
            "inertial_pressure_drop_pa": inertial * height,
            "total_pressure_drop_pa": total_gradient * height,
            "dominant_term": "viscous" if viscous > inertial else "inertial" if inertial > viscous else "equal",
        }, boundary_check=BoundaryCheck(not warnings, warnings))
