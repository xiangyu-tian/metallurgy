"""P1-W14 complete blast-furnace material/energy-chain tools."""

from __future__ import annotations

import math
from typing import Any, Iterable

from .base import (
    BaseModelTool,
    BoundaryCheck,
    BoundaryWarning,
    InputField,
    ModelResult,
    OutputField,
    Provenance,
)
from .repositories.reference_repository import RepositoryError, nasa7


SCENARIO = "高炉低碳"


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
        parsed = float(value)
    except (TypeError, ValueError):
        return None, f"{label}必须是数值"
    if not math.isfinite(parsed):
        return None, f"{label}必须是有限数值"
    if minimum is not None and (parsed <= minimum if strict_minimum else parsed < minimum):
        return None, f"{label}必须{'大于' if strict_minimum else '不小于'}{minimum:g}"
    if maximum is not None and parsed > maximum:
        return None, f"{label}不能大于{maximum:g}"
    return parsed, None


def numeric_mapping(
    raw: Any,
    label: str,
    allowed: Iterable[str],
    *,
    required: Iterable[str] = (),
) -> tuple[dict[str, float] | None, str | None]:
    if not isinstance(raw, dict):
        return None, f"{label}必须是对象"
    allowed_set = set(allowed)
    unknown = sorted(set(raw) - allowed_set)
    if unknown:
        return None, f"{label}包含不支持的键: {', '.join(unknown)}"
    missing = sorted(set(required) - set(raw))
    if missing:
        return None, f"{label}缺少必填键: {', '.join(missing)}"
    result: dict[str, float] = {}
    for key in sorted(allowed_set):
        value, error = finite(raw.get(key, 0.0), f"{label}.{key}", minimum=0)
        if error:
            return None, error
        result[key] = float(value)
    return result, None


def point(raw: Any, label: str) -> tuple[dict[str, float] | None, str | None]:
    if not isinstance(raw, dict) or set(raw) != {"x", "y"}:
        return None, f"{label}必须且只能包含x、y"
    result = {}
    for key in ("x", "y"):
        value, error = finite(raw[key], f"{label}.{key}")
        if error:
            return None, error
        result[key] = float(value)
    return result, None


def unique_provenance(records: list[Provenance]) -> list[Provenance]:
    result: list[Provenance] = []
    seen: set[tuple[Any, ...]] = set()
    for record in records:
        key = (record.dataset_id, record.table, record.record_id)
        if key not in seen:
            seen.add(key)
            result.append(record)
    return result


class W14BFFormulaTool(BaseModelTool):
    scenario = SCENARIO
    priority = "P1"
    status = "qualified"
    qualification_status = "qualified"
    count_eligible = True
    data_requirement = "FORMULA_ONLY"
    data_access_mode = "none"


class E010_BFTopGasComposition(W14BFFormulaTool):
    model_id, name, version = "E010", "高炉理论炉顶煤气组成", "1.0.0"
    tool_name = "metallurgy_calculate_bf_top_gas_composition"
    description = "从风口CO/H2/N2、矿石还原氧及直接/间接还原分配，按C/O/H/N守恒计算湿基和干基理论炉顶煤气。"
    applicable_boundary = (
        "稳态同一统计基准；气相物种限定CO/CO2/H2/H2O/N2；直接还原按1 kmol O生成1 kmol CO，"
        "间接还原按等摩尔CO→CO2、H2→H2O；不含CH4、漏风、粉尘碳和未声明分解气。"
    )
    data_source = ["C/O/H/N atom conservation", "BF top-gas component balance"]
    source_version = "bf-top-gas-chon-balance-v1"
    formula_reference = (
        "n_CO,in=n_CO,bosh+n_O,direct; n_CO2=n_O,indirect,C+extra; "
        "n_H2O=n_O,indirect,H+extra; n_CO=n_CO,in-n_O,indirect,C"
    )
    source_records = [
        {
            "source_id": "ISIJ-BF-TOP-GAS-2023",
            "name": "Mathematical Modeling and Analyses of Integrated Process with Blast Furnace Iron Making and Co-gasification",
            "version": "ISIJ International 63(5), Eqs. 46-52",
            "url": "https://doi.org/10.2355/isijinternational.ISIJINT-2022-505",
        },
        {"source_id": "CHON-CONSERVATION", "name": "Conservation of C/O/H/N atoms", "version": "v1"},
    ]
    failure_modes = [
        "风口或外加气体包含未支持物种",
        "还原氧或分配分数越界",
        "CO或H2不足以承担声明的间接还原",
        "湿基或干基理论煤气总量为零",
        "把理论组成解释为在线分析仪实测值",
    ]
    independent_validation = [
        "C/O/H/N四元素输入输出残差逐项为零",
        "湿基和干基摩尔分数分别归一为1",
        "直接还原每增加1 kmol O使进入间接区的CO增加1 kmol",
        "所有kmol量同比缩放时组成与利用率不变",
    ]
    dependencies = ["E003", "E004", "E005", "E011", "E012"]
    relations = [
        rel("uses_output_of", "E012", "风口前CO/H2/N2可直接作为本工具bosh_gas_kmol"),
        rel("validated_by", "E003", "炉顶CO/CO2碳量可进入高炉碳平衡"),
        rel("validated_by", "E004", "矿石还原氧去向可进入高炉氧平衡"),
        rel("validated_by", "E005", "H2/H2O转换可进入高炉氢平衡"),
        rel("overlaps", "E011", "均报告CO/H2利用率，但本工具还计算完整炉顶气量和组成"),
    ]
    input_fields = [
        InputField("bosh_gas_kmol", "风口区气体量", "object", description="{CO,H2,N2}，单位kmol/$basis"),
        InputField("reduced_ore_oxygen_kmol", "被还原矿石氧", "number", unit="kmol O atoms/$basis", min_value=0),
        InputField("direct_reduction_fraction", "直接还原分数", "number", unit="1", min_value=0, max_value=1),
        InputField("hydrogen_share_of_indirect_reduction", "间接还原中H2分担率", "number", unit="1", min_value=0, max_value=1),
        InputField("additional_top_gas_kmol", "外加炉顶气体", "object", required=False, description="{CO2,H2O,N2}，单位kmol/$basis"),
        InputField("normal_molar_volume_nm3_kmol", "标况摩尔体积", "number", required=False, default=22.414, unit="Nm3/kmol", min_value=1e-12),
        InputField("atom_balance_tolerance_kmol", "原子平衡容差", "number", required=False, default=1e-9, unit="kmol atoms/$basis", min_value=0),
    ]
    output_fields = [
        OutputField("component_amounts_kmol", "炉顶气各组分量", "object"),
        OutputField("component_volumes_nm3", "炉顶气各组分标况体积", "object"),
        OutputField("wet_total_gas_kmol", "湿炉顶气总量", "number", "kmol/$basis"),
        OutputField("dry_total_gas_kmol", "干炉顶气总量", "number", "kmol/$basis"),
        OutputField("wet_total_gas_nm3", "湿炉顶气标况体积", "number", "Nm3/$basis"),
        OutputField("dry_total_gas_nm3", "干炉顶气标况体积", "number", "Nm3/$basis"),
        OutputField("wet_mole_fractions", "湿基摩尔组成", "object"),
        OutputField("dry_mole_fractions", "干基摩尔组成", "object"),
        OutputField("direct_reduction_oxygen_kmol", "直接还原氧", "number", "kmol O atoms/$basis"),
        OutputField("indirect_reduction_oxygen_kmol", "间接还原氧", "number", "kmol O atoms/$basis"),
        OutputField("co_reduction_oxygen_kmol", "CO承担间接还原氧", "number", "kmol O atoms/$basis"),
        OutputField("h2_reduction_oxygen_kmol", "H2承担间接还原氧", "number", "kmol O atoms/$basis"),
        OutputField("co_utilization_fraction", "CO利用率", "number", "1"),
        OutputField("h2_utilization_fraction", "H2利用率", "number", "1"),
        OutputField("atom_balance_residuals_kmol", "C/O/H/N原子残差", "object"),
        OutputField("normal_molar_volume_nm3_kmol", "所用标况摩尔体积", "number", "Nm3/kmol"),
        OutputField("passed", "元素守恒是否通过", "boolean"),
    ]
    validation_rules = [
        {"rule": "supported_nonnegative_gas_mappings"},
        {"rule": "fractions_within_zero_one"},
        {"rule": "sufficient_CO_and_H2_for_indirect_reduction"},
    ]
    _base_case = {
        "bosh_gas_kmol": {"CO": 2.0, "H2": 0.5, "N2": 3.0},
        "reduced_ore_oxygen_kmol": 1.5,
        "direct_reduction_fraction": 0.3,
        "hydrogen_share_of_indirect_reduction": 0.2,
        "additional_top_gas_kmol": {"CO2": 0.1, "H2O": 0.05, "N2": 0.2},
    }
    qualification_cases = [
        {"id": "E010-N1", "kind": "normal", "input": _base_case},
        {"id": "E010-N2", "kind": "normal", "input": {**_base_case, "direct_reduction_fraction": 0.5, "hydrogen_share_of_indirect_reduction": 0.0}},
        {"id": "E010-N3", "kind": "normal", "input": {**_base_case, "reduced_ore_oxygen_kmol": 1.0, "hydrogen_share_of_indirect_reduction": 0.4}},
        {"id": "E010-B1", "kind": "boundary", "input": {**_base_case, "direct_reduction_fraction": 1.0, "hydrogen_share_of_indirect_reduction": 0.0}},
        {"id": "E010-F1", "kind": "failure", "input": {**_base_case, "bosh_gas_kmol": {"CO": 0.1, "H2": 0.01, "N2": 3.0}, "direct_reduction_fraction": 0.0}},
    ]

    def invoke(self, params, context=None):
        bosh, error = numeric_mapping(params.get("bosh_gas_kmol"), "bosh_gas_kmol", ("CO", "H2", "N2"), required=("CO",))
        if error:
            return fail(error)
        extra, error = numeric_mapping(params.get("additional_top_gas_kmol", {}), "additional_top_gas_kmol", ("CO2", "H2O", "N2"))
        if error:
            return fail(error)
        parsed = {}
        for field in self.input_fields:
            if field.type != "number":
                continue
            value, error = finite(
                params.get(field.name, field.default),
                field.name,
                minimum=field.min_value,
                maximum=field.max_value,
            )
            if error:
                return fail(error)
            parsed[field.name] = float(value)

        reduced = parsed["reduced_ore_oxygen_kmol"]
        direct = reduced * parsed["direct_reduction_fraction"]
        indirect = reduced - direct
        h2_reduction = indirect * parsed["hydrogen_share_of_indirect_reduction"]
        co_reduction = indirect - h2_reduction
        co_available = bosh["CO"] + direct
        if co_reduction > co_available + 1e-12:
            return fail("可用CO不足以承担声明的间接还原氧", "MODEL_NOT_APPLICABLE")
        if h2_reduction > bosh["H2"] + 1e-12:
            return fail("可用H2不足以承担声明的间接还原氧", "MODEL_NOT_APPLICABLE")

        amounts = {
            "CO": max(0.0, co_available - co_reduction),
            "CO2": co_reduction + extra["CO2"],
            "H2": max(0.0, bosh["H2"] - h2_reduction),
            "H2O": h2_reduction + extra["H2O"],
            "N2": bosh["N2"] + extra["N2"],
        }
        wet_total = math.fsum(amounts.values())
        dry_total = wet_total - amounts["H2O"]
        if wet_total <= 0 or dry_total <= 0:
            return fail("湿基和干基炉顶气总量必须大于0", "DIVISION_BY_ZERO")

        atom_input = {
            "C": bosh["CO"] + direct + extra["CO2"],
            "O": bosh["CO"] + reduced + 2 * extra["CO2"] + extra["H2O"],
            "H": 2 * bosh["H2"] + 2 * extra["H2O"],
            "N": 2 * (bosh["N2"] + extra["N2"]),
        }
        atom_output = {
            "C": amounts["CO"] + amounts["CO2"],
            "O": amounts["CO"] + 2 * amounts["CO2"] + amounts["H2O"],
            "H": 2 * (amounts["H2"] + amounts["H2O"]),
            "N": 2 * amounts["N2"],
        }
        residuals = {symbol: atom_output[symbol] - atom_input[symbol] for symbol in atom_input}
        tolerance = parsed["atom_balance_tolerance_kmol"]
        passed = all(abs(value) <= tolerance for value in residuals.values())
        warnings = []
        if parsed["direct_reduction_fraction"] in {0.0, 1.0}:
            warnings.append(BoundaryWarning("direct_reduction_fraction", "直接还原分数位于声明边界"))
        if parsed["hydrogen_share_of_indirect_reduction"] in {0.0, 1.0}:
            warnings.append(BoundaryWarning("hydrogen_share_of_indirect_reduction", "H2分担率位于声明边界"))
        if not passed:
            warnings.append(BoundaryWarning("atom_balance", "C/O/H/N原子账未在声明容差内闭合"))
        vm = parsed["normal_molar_volume_nm3_kmol"]
        return ModelResult(True, result={
            "component_amounts_kmol": amounts,
            "component_volumes_nm3": {key: value * vm for key, value in amounts.items()},
            "wet_total_gas_kmol": wet_total,
            "dry_total_gas_kmol": dry_total,
            "wet_total_gas_nm3": wet_total * vm,
            "dry_total_gas_nm3": dry_total * vm,
            "wet_mole_fractions": {key: value / wet_total for key, value in amounts.items()},
            "dry_mole_fractions": {key: (0.0 if key == "H2O" else value / dry_total) for key, value in amounts.items()},
            "direct_reduction_oxygen_kmol": direct,
            "indirect_reduction_oxygen_kmol": indirect,
            "co_reduction_oxygen_kmol": co_reduction,
            "h2_reduction_oxygen_kmol": h2_reduction,
            "co_utilization_fraction": co_reduction / co_available if co_available > 0 else 0.0,
            "h2_utilization_fraction": h2_reduction / bosh["H2"] if bosh["H2"] > 0 else 0.0,
            "atom_balance_residuals_kmol": residuals,
            "normal_molar_volume_nm3_kmol": vm,
            "passed": passed,
        }, boundary_check=BoundaryCheck(passed and not warnings, warnings))


class E106_CompleteRistOperatingLine(W14BFFormulaTool):
    model_id, name, version = "E106", "完整物料型Rist操作线", "1.0.0"
    tool_name = "metallurgy_construct_complete_bf_rist_line"
    description = "用含氢炉顶气、能量固定点P和理想wüstite点W构造实际/理想Rist线，并求直接还原度和还原剂超额。"
    applicable_boundary = (
        "稳态同一Fe基准；Rist广义C-H-O坐标；P点和W点须由同一坐标与热化学口径给出；"
        "不自行求解全炉热平衡P点，不含上部未登记中途喷吹或碳酸盐分解气。"
    )
    data_source = ["Generalized Rist operating diagram", "C/H/O balance per mol Fe"]
    source_version = "generalized-material-rist-A-P-W-v1"
    formula_reference = (
        "X=(O+H/2)/(C+H/2); Y=O_reduced/Fe; Y=mu*X+Y_E; "
        "y_direct=mu+Y_E; actual=A-P; ideal=W-P"
    )
    source_records = [
        {
            "source_id": "RIST-MULTI-INJECTION-2023",
            "name": "Revisiting the Rist diagram for predicting operating conditions in blast furnaces with multiple injections",
            "version": "Scientific Reports 13 (2023)",
            "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC10445826/",
        }
    ]
    failure_modes = [
        "Fe基准非正或炉料氧小于铁水残余氧",
        "炉顶还原气总量为零",
        "A与P或W与P横坐标重合",
        "操作线斜率非正",
        "直接还原氧超出总被还原氧",
        "P/W点与炉顶气量不在同一Rist基准",
    ]
    independent_validation = [
        "实际线严格通过A和P、理想线严格通过W和P",
        "实际斜率由炉顶还原气总量/Fe独立复算",
        "直接还原氧满足y_d=mu+Y_E且直接加间接等于总还原氧",
        "所有绝对kmol量同比缩放时两条线及还原分数不变",
    ]
    dependencies = ["E001", "E002", "E003", "E004", "E005", "E007", "E011"]
    relations = [
        rel("overlaps", "E006", "E006只处理CO/CO2简化线，本工具增加H2/H2O、P/W点和直接还原分解"),
        rel("uses_output_of", "E007", "分区热平衡可为调用方确定或审核能量固定点P"),
        rel("uses_output_of", "E003", "炉顶碳量用于独立复算还原气斜率"),
        rel("uses_output_of", "E004", "炉料与铁水氧量确定Y轴和总还原氧"),
        rel("overlaps", "E011", "炉顶气氧化度与CO/H2利用率互相约束"),
    ]
    input_fields = [
        InputField("iron_basis_kmol", "Fe统计基准", "number", unit="kmol Fe/$basis", min_value=1e-12),
        InputField("burden_oxygen_atom_kmol", "炉料铁氧化物结合氧", "number", unit="kmol O atoms/$basis", min_value=0),
        InputField("hot_metal_oxygen_atom_kmol", "铁水残余氧", "number", required=False, default=0, unit="kmol O atoms/$basis", min_value=0),
        InputField("top_gas_kmol", "炉顶还原气组分", "object", description="{CO,CO2,H2,H2O}，单位kmol/$basis"),
        InputField("energy_balance_point", "能量固定点P", "object", description="{x,y}，Rist无量纲坐标"),
        InputField("ideal_wustite_point", "理想wüstite点W", "object", description="{x,y}，Rist无量纲坐标"),
        InputField("slope_closure_tolerance", "斜率闭合容差", "number", required=False, default=1e-8, unit="kmol reducing gas/kmol Fe", min_value=0),
    ]
    output_fields = [
        OutputField("top_point_a", "炉顶点A", "object"),
        OutputField("energy_balance_point_p", "能量固定点P", "object"),
        OutputField("ideal_wustite_point_w", "理想wüstite点W", "object"),
        OutputField("actual_slope_mu", "实际操作线斜率", "number", "kmol reducing gas/kmol Fe"),
        OutputField("actual_y_intercept", "实际Y截距", "number", "kmol O/kmol Fe"),
        OutputField("top_gas_rate_mu", "炉顶气独立复算斜率", "number", "kmol reducing gas/kmol Fe"),
        OutputField("slope_closure_residual", "斜率闭合残差", "number", "kmol reducing gas/kmol Fe"),
        OutputField("ideal_slope_mu", "理想操作线斜率", "number", "kmol reducing gas/kmol Fe"),
        OutputField("ideal_y_intercept", "理想Y截距", "number", "kmol O/kmol Fe"),
        OutputField("direct_reduction_oxygen_per_iron", "直接还原氧", "number", "kmol O/kmol Fe"),
        OutputField("indirect_reduction_oxygen_per_iron", "间接还原氧", "number", "kmol O/kmol Fe"),
        OutputField("direct_reduction_fraction", "直接还原分数", "number", "1"),
        OutputField("reducing_agent_excess_fraction", "实际相对理想还原剂超额", "number", "1"),
        OutputField("actual_line_points", "实际操作线端点", "array"),
        OutputField("ideal_line_points", "理想操作线端点", "array"),
        OutputField("passed", "实际线与炉顶气量是否闭合", "boolean"),
    ]
    validation_rules = [
        {"rule": "positive_iron_and_nonnegative_oxygen"},
        {"rule": "supported_top_gas_species"},
        {"rule": "distinct_characteristic_point_abscissae"},
        {"rule": "positive_actual_and_ideal_slopes"},
    ]
    _base_case = {
        "iron_basis_kmol": 1.0,
        "burden_oxygen_atom_kmol": 1.5,
        "hot_metal_oxygen_atom_kmol": 0.0,
        "top_gas_kmol": {"CO": 1.5, "CO2": 0.5, "H2": 0.0, "H2O": 0.0},
        "energy_balance_point": {"x": 0.5, "y": 0.0},
        "ideal_wustite_point": {"x": 1.1, "y": 1.0},
    }
    qualification_cases = [
        {"id": "E106-N1", "kind": "normal", "input": _base_case},
        {"id": "E106-N2", "kind": "normal", "input": {**_base_case, "top_gas_kmol": {"CO": 1.0, "CO2": 0.5, "H2": 0.4, "H2O": 0.1}, "energy_balance_point": {"x": 0.55, "y": 0.0}}},
        {"id": "E106-N3", "kind": "normal", "input": {**_base_case, "iron_basis_kmol": 2.0, "burden_oxygen_atom_kmol": 3.0, "top_gas_kmol": {"CO": 3.0, "CO2": 1.0, "H2": 0.0, "H2O": 0.0}}},
        {"id": "E106-B1", "kind": "boundary", "input": {**_base_case, "top_gas_kmol": {"CO": 0.5, "CO2": 1.5, "H2": 0.0, "H2O": 0.0}, "energy_balance_point": {"x": 0.5, "y": -1.0}}},
        {"id": "E106-F1", "kind": "failure", "input": {**_base_case, "energy_balance_point": {"x": 1.25, "y": 0.0}}},
    ]

    def invoke(self, params, context=None):
        parsed = {}
        for field in self.input_fields:
            if field.type != "number":
                continue
            value, error = finite(
                params.get(field.name, field.default), field.name,
                minimum=field.min_value, maximum=field.max_value,
                strict_minimum=field.name == "iron_basis_kmol",
            )
            if error:
                return fail(error)
            parsed[field.name] = float(value)
        gas, error = numeric_mapping(params.get("top_gas_kmol"), "top_gas_kmol", ("CO", "CO2", "H2", "H2O"))
        if error:
            return fail(error)
        p, error = point(params.get("energy_balance_point"), "energy_balance_point")
        if error:
            return fail(error)
        w, error = point(params.get("ideal_wustite_point"), "ideal_wustite_point")
        if error:
            return fail(error)
        if parsed["hot_metal_oxygen_atom_kmol"] > parsed["burden_oxygen_atom_kmol"]:
            return fail("hot_metal_oxygen_atom_kmol不能超过burden_oxygen_atom_kmol", "OUT_OF_DOMAIN")
        gas_total = math.fsum(gas.values())
        if gas_total <= 0:
            return fail("炉顶CO/CO2/H2/H2O总量必须大于0", "DIVISION_BY_ZERO")
        x_a = (gas["CO"] + 2 * gas["CO2"] + gas["H2"] + 2 * gas["H2O"]) / gas_total
        iron = parsed["iron_basis_kmol"]
        y_a = (parsed["burden_oxygen_atom_kmol"] - parsed["hot_metal_oxygen_atom_kmol"]) / iron
        if abs(x_a - p["x"]) <= 1e-12:
            return fail("炉顶点A与能量点P的x不能相同", "DIVISION_BY_ZERO")
        if abs(w["x"] - p["x"]) <= 1e-12:
            return fail("理想点W与能量点P的x不能相同", "DIVISION_BY_ZERO")
        actual_mu = (y_a - p["y"]) / (x_a - p["x"])
        ideal_mu = (w["y"] - p["y"]) / (w["x"] - p["x"])
        if actual_mu <= 0 or ideal_mu <= 0:
            return fail("实际与理想Rist操作线斜率必须为正", "MODEL_NOT_APPLICABLE")
        actual_intercept = y_a - actual_mu * x_a
        ideal_intercept = w["y"] - ideal_mu * w["x"]
        gas_mu = gas_total / iron
        residual = actual_mu - gas_mu
        direct = actual_mu + actual_intercept
        tolerance = parsed["slope_closure_tolerance"]
        if direct < -tolerance or direct > y_a + tolerance:
            return fail("由Rist线得到的直接还原氧超出总被还原氧", "MODEL_NOT_APPLICABLE")
        direct = min(max(direct, 0.0), y_a)
        indirect = y_a - direct
        direct_fraction = direct / y_a if y_a > 0 else 0.0
        passed = abs(residual) <= tolerance
        warnings = []
        if not passed:
            warnings.append(BoundaryWarning("slope_closure", "A-P直线斜率与炉顶气量/Fe独立复算不一致"))
        if direct <= tolerance or indirect <= tolerance:
            warnings.append(BoundaryWarning("reduction_split", "直接或间接还原位于零边界"))
        if actual_mu < ideal_mu:
            warnings.append(BoundaryWarning("ideal_comparison", "实际还原剂斜率低于所声明理想线，请复核P/W口径"))
        return ModelResult(True, result={
            "top_point_a": {"x": x_a, "y": y_a},
            "energy_balance_point_p": p,
            "ideal_wustite_point_w": w,
            "actual_slope_mu": actual_mu,
            "actual_y_intercept": actual_intercept,
            "top_gas_rate_mu": gas_mu,
            "slope_closure_residual": residual,
            "ideal_slope_mu": ideal_mu,
            "ideal_y_intercept": ideal_intercept,
            "direct_reduction_oxygen_per_iron": direct,
            "indirect_reduction_oxygen_per_iron": indirect,
            "direct_reduction_fraction": direct_fraction,
            "reducing_agent_excess_fraction": actual_mu / ideal_mu - 1,
            "actual_line_points": [p, {"x": x_a, "y": y_a}],
            "ideal_line_points": [p, w],
            "passed": passed,
        }, boundary_check=BoundaryCheck(passed and not warnings, warnings))


class E109_CompletePCIReplacement(W14BFFormulaTool):
    model_id, name, version = "E109", "完整喷煤等效置换与边际账", "1.0.0"
    tool_name = "metallurgy_calculate_complete_pci_replacement"
    description = "同时受固定碳、净有效能、最低结构焦比和增量灰分约束，计算PCI等效焦炭替代及边际总燃料变化。"
    applicable_boundary = (
        "静态单工况；煤焦工业分析、燃尽率、有效热利用率和工艺吸热由调用方按同一基准提供；"
        "输出是理论可行上限，不预测实际焦比、透气性或动态炉况。"
    )
    data_source = ["Fixed-carbon balance", "Net effective-energy balance", "Structural coke and ash constraints"]
    source_version = "pci-carbon-energy-structure-ash-v1"
    formula_reference = (
        "R=min(wC_coal*burnout/wC_coke, Qnet_coal/Qnet_coke, "
        "(m_coke0-m_coke,min)/m_coal); ash_net=m_coal*wash_coal-m_replaced*wash_coke"
    )
    source_records = [
        {
            "source_id": "PCI-MATERIAL-BALANCE-2017",
            "name": "Material Balance in a Blast Furnace, when Replacing Coke with Coal Dust",
            "version": "Metallurgy and Materials Science 40(4), 2017",
            "url": "https://www.gup.ugal.ro/ugaljournals/index.php/mms/article/view/1129",
        },
        {"source_id": "PCI-CARBON-ENERGY", "name": "Carbon and net effective-energy equivalence", "version": "v1"},
    ]
    failure_modes = [
        "基准焦比或喷煤量非正",
        "最低结构焦比高于基准焦比",
        "煤焦分析分数或有效系数越界",
        "焦炭净有效能非正",
        "选定理论替代量仍超过增量灰分预算",
        "把理论上限解释为现场经验置换率",
    ]
    independent_validation = [
        "替代后有效固定碳需求不超过煤有效固定碳",
        "替代后焦炭净有效能不超过煤净有效能",
        "替代后焦比不低于最低结构焦比",
        "增量灰分由煤带入灰减去被替焦炭灰独立复算",
        "喷煤量与焦比基准同比缩放时替代比不变且质量项同比缩放",
    ]
    dependencies = ["E003", "E005", "E007", "E009"]
    relations = [
        rel("overlaps", "E009", "均输出喷煤替代焦炭量；E109增加基准焦比、结构焦、工艺热和灰分可行性"),
        rel("validated_by", "E003", "固定碳裕量可进入全炉碳平衡"),
        rel("uses_output_of", "E007", "煤焦净有效能和工艺吸热应与高炉热平衡同基准"),
        rel("overlaps", "E005", "含氢燃料影响可通过有效LHV与工艺热显式反映"),
    ]
    input_fields = [
        InputField("coal_injection_kg", "喷煤量", "number", unit="kg/$basis", min_value=1e-12),
        InputField("baseline_coke_kg", "基准焦炭量", "number", unit="kg/$basis", min_value=1e-12),
        InputField("minimum_structural_coke_kg", "最低结构焦炭量", "number", unit="kg/$basis", min_value=0),
        InputField("coal_fixed_carbon_fraction", "煤固定碳分数", "number", unit="1", min_value=0, max_value=1),
        InputField("coal_burnout_fraction", "煤燃尽率", "number", unit="1", min_value=0, max_value=1),
        InputField("coal_ash_fraction", "煤灰分", "number", unit="1", min_value=0, max_value=1),
        InputField("coal_lhv_mj_kg", "煤低位热值", "number", unit="MJ/kg", min_value=0),
        InputField("coal_heat_utilization_fraction", "煤热利用率", "number", unit="1", min_value=0, max_value=1),
        InputField("coal_process_heat_demand_mj_kg", "煤工艺吸热", "number", unit="MJ/kg coal", min_value=0),
        InputField("coke_fixed_carbon_fraction", "焦炭固定碳分数", "number", unit="1", min_value=1e-12, max_value=1),
        InputField("coke_ash_fraction", "焦炭灰分", "number", unit="1", min_value=0, max_value=1),
        InputField("coke_lhv_mj_kg", "焦炭低位热值", "number", unit="MJ/kg", min_value=0),
        InputField("coke_heat_utilization_fraction", "焦炭热利用率", "number", unit="1", min_value=0, max_value=1),
        InputField("coke_process_heat_demand_mj_kg", "焦炭工艺吸热", "number", unit="MJ/kg coke", min_value=0),
        InputField("maximum_incremental_ash_kg", "允许增量灰分", "number", unit="kg ash/$basis", min_value=0),
    ]
    output_fields = [
        OutputField("fixed_carbon_replacement_limit", "固定碳替代上限", "number", "kg coke/kg coal"),
        OutputField("net_energy_replacement_limit", "净有效能替代上限", "number", "kg coke/kg coal"),
        OutputField("structural_coke_replacement_limit", "结构焦替代上限", "number", "kg coke/kg coal"),
        OutputField("selected_replacement_ratio", "选定理论替代比", "number", "kg coke/kg coal"),
        OutputField("controlling_constraint", "控制约束", "string"),
        OutputField("theoretical_coke_replaced_kg", "理论替代焦炭量", "number", "kg/$basis"),
        OutputField("resulting_coke_kg", "替代后焦炭量", "number", "kg/$basis"),
        OutputField("resulting_total_fuel_kg", "替代后煤焦总量", "number", "kg/$basis"),
        OutputField("marginal_total_fuel_change_kg", "相对基准总燃料变化", "number", "kg/$basis"),
        OutputField("effective_coal_carbon_kg", "煤有效固定碳", "number", "kg C/$basis"),
        OutputField("unburned_coal_carbon_kg", "煤未燃固定碳", "number", "kg C/$basis"),
        OutputField("fixed_carbon_margin_kg", "固定碳裕量", "number", "kg C/$basis"),
        OutputField("coal_net_effective_energy_mj", "煤净有效能", "number", "MJ/$basis"),
        OutputField("net_energy_margin_mj", "净有效能裕量", "number", "MJ/$basis"),
        OutputField("structural_coke_margin_kg", "结构焦裕量", "number", "kg/$basis"),
        OutputField("incremental_ash_kg", "增量灰分", "number", "kg ash/$basis"),
        OutputField("ash_budget_margin_kg", "灰分预算裕量", "number", "kg ash/$basis"),
        OutputField("feasible", "所有静态约束是否可行", "boolean"),
    ]
    validation_rules = [
        {"rule": "fractions_within_zero_one_and_nonnegative_energy_terms"},
        {"rule": "fixed_carbon_plus_ash_not_above_one"},
        {"rule": "minimum_structural_coke_not_above_baseline"},
        {"rule": "positive_coke_net_effective_energy"},
    ]
    _base_case = {
        "coal_injection_kg": 100.0,
        "baseline_coke_kg": 400.0,
        "minimum_structural_coke_kg": 200.0,
        "coal_fixed_carbon_fraction": 0.75,
        "coal_burnout_fraction": 0.9,
        "coal_ash_fraction": 0.10,
        "coal_lhv_mj_kg": 28.0,
        "coal_heat_utilization_fraction": 0.8,
        "coal_process_heat_demand_mj_kg": 2.0,
        "coke_fixed_carbon_fraction": 0.85,
        "coke_ash_fraction": 0.12,
        "coke_lhv_mj_kg": 29.0,
        "coke_heat_utilization_fraction": 0.9,
        "coke_process_heat_demand_mj_kg": 1.0,
        "maximum_incremental_ash_kg": 20.0,
    }
    qualification_cases = [
        {"id": "E109-N1", "kind": "normal", "input": _base_case},
        {"id": "E109-N2", "kind": "normal", "input": {**_base_case, "coal_fixed_carbon_fraction": 0.85, "coal_lhv_mj_kg": 24.0, "coal_heat_utilization_fraction": 0.7}},
        {"id": "E109-N3", "kind": "normal", "input": {**_base_case, "baseline_coke_kg": 300.0, "minimum_structural_coke_kg": 250.0, "coal_fixed_carbon_fraction": 0.9, "coal_lhv_mj_kg": 32.0}},
        {"id": "E109-B1", "kind": "boundary", "input": {**_base_case, "coal_lhv_mj_kg": 10.0, "coal_heat_utilization_fraction": 0.2, "coal_process_heat_demand_mj_kg": 2.0}},
        {"id": "E109-F1", "kind": "failure", "input": {**_base_case, "minimum_structural_coke_kg": 450.0}},
    ]

    def invoke(self, params, context=None):
        values = {}
        for field in self.input_fields:
            value, error = finite(
                params.get(field.name), field.name,
                minimum=field.min_value, maximum=field.max_value,
                strict_minimum=field.name in {"coal_injection_kg", "baseline_coke_kg"},
            )
            if error:
                return fail(error)
            values[field.name] = float(value)
        if values["minimum_structural_coke_kg"] > values["baseline_coke_kg"]:
            return fail("minimum_structural_coke_kg不能高于baseline_coke_kg", "OUT_OF_DOMAIN")
        if values["coal_fixed_carbon_fraction"] + values["coal_ash_fraction"] > 1 + 1e-12:
            return fail("煤固定碳与灰分之和不能大于1", "OUT_OF_DOMAIN")
        if values["coke_fixed_carbon_fraction"] + values["coke_ash_fraction"] > 1 + 1e-12:
            return fail("焦炭固定碳与灰分之和不能大于1", "OUT_OF_DOMAIN")
        coal_net_per_kg = (
            values["coal_lhv_mj_kg"] * values["coal_heat_utilization_fraction"]
            - values["coal_process_heat_demand_mj_kg"]
        )
        coke_net_per_kg = (
            values["coke_lhv_mj_kg"] * values["coke_heat_utilization_fraction"]
            - values["coke_process_heat_demand_mj_kg"]
        )
        if coal_net_per_kg < -1e-12:
            return fail("煤工艺吸热超过其有效LHV", "MODEL_NOT_APPLICABLE")
        coal_net_per_kg = max(0.0, coal_net_per_kg)
        if coke_net_per_kg <= 0:
            return fail("焦炭净有效能必须大于0", "DIVISION_BY_ZERO")
        carbon_limit = (
            values["coal_fixed_carbon_fraction"] * values["coal_burnout_fraction"]
            / values["coke_fixed_carbon_fraction"]
        )
        energy_limit = coal_net_per_kg / coke_net_per_kg
        structural_limit = (
            values["baseline_coke_kg"] - values["minimum_structural_coke_kg"]
        ) / values["coal_injection_kg"]
        limits = {
            "fixed_carbon": carbon_limit,
            "net_energy": energy_limit,
            "structural_coke": structural_limit,
        }
        controlling = min(limits, key=limits.get)
        selected = limits[controlling]
        coal_mass = values["coal_injection_kg"]
        replaced = coal_mass * selected
        resulting_coke = values["baseline_coke_kg"] - replaced
        effective_carbon = coal_mass * values["coal_fixed_carbon_fraction"] * values["coal_burnout_fraction"]
        unburned_carbon = coal_mass * values["coal_fixed_carbon_fraction"] * (1 - values["coal_burnout_fraction"])
        carbon_margin = effective_carbon - replaced * values["coke_fixed_carbon_fraction"]
        coal_net_energy = coal_mass * coal_net_per_kg
        energy_margin = coal_net_energy - replaced * coke_net_per_kg
        structural_margin = resulting_coke - values["minimum_structural_coke_kg"]
        incremental_ash = coal_mass * values["coal_ash_fraction"] - replaced * values["coke_ash_fraction"]
        ash_margin = values["maximum_incremental_ash_kg"] - incremental_ash
        if ash_margin < -1e-9:
            return fail("理论最大替代量仍使增量灰分超过预算", "MODEL_NOT_APPLICABLE")
        warnings = []
        if selected <= 1e-12:
            warnings.append(BoundaryWarning("selected_replacement_ratio", "理论替代比位于零边界"))
        if controlling == "structural_coke" or structural_margin <= 1e-9:
            warnings.append(BoundaryWarning("minimum_structural_coke_kg", "最低结构焦比约束处于激活边界"))
        if ash_margin <= 1e-9:
            warnings.append(BoundaryWarning("maximum_incremental_ash_kg", "增量灰分预算处于激活边界"))
        feasible = min(carbon_margin, energy_margin, structural_margin, ash_margin) >= -1e-8
        return ModelResult(True, result={
            "fixed_carbon_replacement_limit": carbon_limit,
            "net_energy_replacement_limit": energy_limit,
            "structural_coke_replacement_limit": structural_limit,
            "selected_replacement_ratio": selected,
            "controlling_constraint": controlling,
            "theoretical_coke_replaced_kg": replaced,
            "resulting_coke_kg": resulting_coke,
            "resulting_total_fuel_kg": resulting_coke + coal_mass,
            "marginal_total_fuel_change_kg": coal_mass - replaced,
            "effective_coal_carbon_kg": effective_carbon,
            "unburned_coal_carbon_kg": unburned_carbon,
            "fixed_carbon_margin_kg": carbon_margin,
            "coal_net_effective_energy_mj": coal_net_energy,
            "net_energy_margin_mj": energy_margin,
            "structural_coke_margin_kg": structural_margin,
            "incremental_ash_kg": incremental_ash,
            "ash_budget_margin_kg": ash_margin,
            "feasible": feasible,
        }, boundary_check=BoundaryCheck(feasible and not warnings, warnings))


class E013_RacewayAdiabaticFlameTemperature(BaseModelTool):
    model_id, name, version = "E013", "风口回旋区绝热火焰温度", "1.0.0"
    tool_name = "metallurgy_calculate_bf_raceway_raft"
    scenario = SCENARIO
    priority = "P1"
    status = "qualified"
    qualification_status = "qualified"
    count_eligible = True
    description = "按风口C/H/O/N守恒生成CO/H2/N2，并用数据库NASA7焓求解热风、富氧、湿分和有效燃料能共同决定的RAFT。"
    applicable_boundary = (
        "绝热定压、氧完全耗尽、参与反应的碳恰好生成CO；物种限定O2/N2/H2O/CO/H2，温区200-3500 K；"
        "燃料热解、灰分加热等须计入显式工艺吸热，不含解离化学平衡和现场热损。"
    )
    data_source = ["PostgreSQL DS_NASA7_GRI30 NASA7 thermodynamic correlations"]
    source_version = "bf-raceway-raft-nasa7-v1"
    formula_reference = (
        "sum(n_product*[h(Tad)-h(298)]) = LHV_effective - LHV_retained(CO,H2) "
        "+ H_sensible,reactants + H_sensible,fuel - Q_process"
    )
    required_dataset_ids = ["DS_NASA7_GRI30"]
    database_tables = ["metallurgy_v2.thermodynamic_correlation"]
    data_requirement = "THERMODYNAMIC_CORRELATIONS"
    data_access_mode = "database_repository"
    source_records = [
        {
            "source_id": "DS_NASA7_GRI30",
            "name": "GRI-Mech 3.0 NASA7 thermodynamic subset",
            "version": "NASA7-GRI30-SUBSET-V1",
            "url": "http://combustion.berkeley.edu/gri-mech/version30/text30.html",
        },
        {
            "source_id": "ISIJ-RAFT-2023",
            "name": "Theoretical combustion temperature in raceway zone",
            "version": "ISIJ International 63(5), Eq. 62",
            "url": "https://doi.org/10.2355/isijinternational.ISIJINT-2022-505",
        },
    ]
    required_data = ["O2/N2/H2O/CO/H2在298.15 K及求解温区的NASA7记录"]
    failure_modes = [
        "数据库不可用或NASA7记录缺失",
        "温度超200-3500 K批准域",
        "参与反应碳与完全耗氧所需碳不相等",
        "有效燃料能不足以覆盖CO/H2保留化学能与工艺吸热",
        "求根温区未括住能量零点",
        "把绝热理论温度解释为风口热电偶实测值",
    ]
    independent_validation = [
        "用NASA7焓在RAFT回代能量残差",
        "提高热风温度在其余输入不变时RAFT上升",
        "增加显式工艺吸热在其余输入不变时RAFT下降",
        "C/H/O/N原子账与E012同口径严格闭合",
        "数据库关闭时禁止常数兜底并显式失败",
    ]
    dependencies = ["B012", "E012"]
    relations = [
        rel("overlaps", "B012", "均求绝热温度；B012是单反应，本工具是BF风口多股物流与保留化学能专用模型"),
        rel("overlaps", "E012", "使用相同风口C/H/O/N完全耗氧边界，但独立加入数据库焓与能量求根"),
        rel("upstream_of", "E007", "RAFT热量分项可作为高温区热平衡审核输入"),
    ]
    input_fields = [
        InputField("dry_blast_nm3", "干鼓风标况体积", "number", unit="Nm3/$basis", min_value=0),
        InputField("dry_blast_oxygen_mole_fraction", "干风O2摩尔分数", "number", unit="1", min_value=0, max_value=1),
        InputField("blast_temperature_k", "热风温度", "number", unit="K", min_value=200, max_value=3500),
        InputField("supplemental_oxygen_nm3", "富氧标况体积", "number", unit="Nm3 O2/$basis", min_value=0),
        InputField("supplemental_oxygen_temperature_k", "富氧温度", "number", unit="K", min_value=200, max_value=3500),
        InputField("steam_kmol", "鼓风蒸汽", "number", unit="kmol H2O/$basis", min_value=0),
        InputField("steam_temperature_k", "蒸汽温度", "number", unit="K", min_value=200, max_value=3500),
        InputField("reacting_fuel_element_atoms_kmol", "参与反应燃料元素原子量", "object", description="{C,H,O,N}，单位kmol atoms/$basis"),
        InputField("effective_fuel_lhv_mj", "反应燃料有效完全氧化LHV", "number", unit="MJ/$basis", min_value=0),
        InputField("fuel_sensible_enthalpy_mj", "燃料相对298K显热", "number", required=False, default=0, unit="MJ/$basis"),
        InputField("fuel_process_heat_demand_mj", "热解灰分等工艺吸热", "number", required=False, default=0, unit="MJ/$basis", min_value=0),
        InputField("temperature_lower_k", "RAFT求根下界", "number", unit="K", min_value=200, max_value=3500),
        InputField("temperature_upper_k", "RAFT求根上界", "number", unit="K", min_value=200, max_value=3500),
        InputField("normal_molar_volume_nm3_kmol", "标况摩尔体积", "number", required=False, default=22.414, unit="Nm3/kmol", min_value=1e-12),
        InputField("carbon_closure_tolerance_kmol", "反应碳闭合容差", "number", required=False, default=1e-9, unit="kmol C/$basis", min_value=0),
    ]
    output_fields = [
        OutputField("raft_temperature_k", "回旋区绝热火焰温度", "number", "K"),
        OutputField("product_gas_amounts_kmol", "风口产物气体", "object"),
        OutputField("product_gas_mole_fractions", "风口产物气组成", "object"),
        OutputField("total_product_gas_kmol", "风口产物气总量", "number", "kmol/$basis"),
        OutputField("input_oxygen_atom_kmol", "输入氧原子总量", "number", "kmol O atoms/$basis"),
        OutputField("reacting_carbon_kmol", "参与反应碳", "number", "kmol C/$basis"),
        OutputField("effective_fuel_lhv_kj", "有效完全氧化LHV", "number", "kJ/$basis"),
        OutputField("co_retained_chemical_energy_kj", "CO保留化学能", "number", "kJ/$basis"),
        OutputField("h2_retained_chemical_energy_kj", "H2保留化学能", "number", "kJ/$basis"),
        OutputField("reactant_sensible_enthalpy_kj", "气态反应物显热", "number", "kJ/$basis"),
        OutputField("fuel_sensible_enthalpy_kj", "燃料显热", "number", "kJ/$basis"),
        OutputField("fuel_process_heat_demand_kj", "燃料工艺吸热", "number", "kJ/$basis"),
        OutputField("available_product_sensible_heat_kj", "可供产物升温热", "number", "kJ/$basis"),
        OutputField("product_sensible_enthalpy_kj", "RAFT产物显热", "number", "kJ/$basis"),
        OutputField("energy_balance_residual_kj", "能量闭合残差", "number", "kJ/$basis"),
        OutputField("atom_balance_residuals_kmol", "C/H/O/N原子残差", "object"),
        OutputField("solver_iterations", "二分求根迭代次数", "integer", "1"),
        OutputField("method", "计算方法", "string"),
    ]
    validation_rules = [
        {"rule": "temperatures_within_nasa7_domain_and_ordered_root_bounds"},
        {"rule": "reacting_carbon_equals_complete_CO_requirement"},
        {"rule": "positive_available_product_sensible_heat"},
        {"rule": "database_nasa7_only_no_static_fallback"},
    ]
    _base_case = {
        "dry_blast_nm3": 22.414,
        "dry_blast_oxygen_mole_fraction": 0.21,
        "blast_temperature_k": 1200.0,
        "supplemental_oxygen_nm3": 2.2414,
        "supplemental_oxygen_temperature_k": 298.15,
        "steam_kmol": 0.05,
        "steam_temperature_k": 500.0,
        "reacting_fuel_element_atoms_kmol": {"C": 0.67, "H": 0.10, "O": 0.0, "N": 0.0},
        "effective_fuel_lhv_mj": 300.0,
        "fuel_sensible_enthalpy_mj": 0.0,
        "fuel_process_heat_demand_mj": 5.0,
        "temperature_lower_k": 500.0,
        "temperature_upper_k": 3500.0,
    }
    qualification_cases = [
        {"id": "E013-N1", "kind": "normal", "input": _base_case},
        {"id": "E013-N2", "kind": "normal", "input": {**_base_case, "blast_temperature_k": 1400.0}},
        {"id": "E013-N3", "kind": "normal", "input": {**_base_case, "fuel_process_heat_demand_mj": 15.0}},
        {"id": "E013-B1", "kind": "boundary", "input": {**_base_case, "supplemental_oxygen_nm3": 0.0, "steam_kmol": 0.0, "reacting_fuel_element_atoms_kmol": {"C": 0.42, "H": 0.0, "O": 0.0, "N": 0.0}, "effective_fuel_lhv_mj": 165.3, "fuel_process_heat_demand_mj": 0.0}},
        {"id": "E013-F1", "kind": "failure", "input": {**_base_case, "reacting_fuel_element_atoms_kmol": {"C": 0.50, "H": 0.10, "O": 0.0, "N": 0.0}}},
    ]
    data_qualification_cases = [{"id": "E013-D1", "input": _base_case}]

    @staticmethod
    def _h(species: str, temperature: float, records: list[Provenance]) -> float:
        value, provenance = nasa7(species, temperature)
        records.extend(provenance)
        return float(value["H"])

    def invoke(self, params, context=None):
        values = {}
        for field in self.input_fields:
            if field.type != "number":
                continue
            value, error = finite(
                params.get(field.name, field.default), field.name,
                minimum=field.min_value, maximum=field.max_value,
            )
            if error:
                return fail(error)
            values[field.name] = float(value)
        if values["temperature_lower_k"] >= values["temperature_upper_k"]:
            return fail("temperature_lower_k必须小于temperature_upper_k")
        fuel, error = numeric_mapping(
            params.get("reacting_fuel_element_atoms_kmol"),
            "reacting_fuel_element_atoms_kmol", ("C", "H", "O", "N"), required=("C",),
        )
        if error:
            return fail(error)
        vm = values["normal_molar_volume_nm3_kmol"]
        dry_blast_kmol = values["dry_blast_nm3"] / vm
        blast_o2 = dry_blast_kmol * values["dry_blast_oxygen_mole_fraction"]
        blast_n2 = dry_blast_kmol - blast_o2
        supplemental_o2 = values["supplemental_oxygen_nm3"] / vm
        oxygen_atoms = 2 * (blast_o2 + supplemental_o2) + values["steam_kmol"] + fuel["O"]
        carbon_residual = fuel["C"] - oxygen_atoms
        if abs(carbon_residual) > values["carbon_closure_tolerance_kmol"]:
            return fail("reacting_fuel_element_atoms_kmol.C必须等于完全耗氧生成CO所需碳", "MODEL_NOT_APPLICABLE")
        products = {
            "CO": oxygen_atoms,
            "H2": (fuel["H"] + 2 * values["steam_kmol"]) / 2,
            "N2": blast_n2 + fuel["N"] / 2,
        }
        total_products = math.fsum(products.values())
        if oxygen_atoms <= 0 or total_products <= 0:
            return fail("输入氧与风口产物气总量必须大于0", "DIVISION_BY_ZERO")

        records: list[Provenance] = []
        cache: dict[tuple[str, float], float] = {}

        def h(species: str, temperature: float) -> float:
            key = (species, float(temperature))
            if key not in cache:
                cache[key] = self._h(species, temperature, records)
            return cache[key]

        reference = 298.15
        try:
            co_lhv_kj_mol = -(h("CO2(g)", reference) - h("CO(g)", reference) - 0.5 * h("O2(g)", reference))
            h2_lhv_kj_mol = -(h("H2O(g)", reference) - h("H2(g)", reference) - 0.5 * h("O2(g)", reference))
            reactant_sensible = 1000 * (
                blast_o2 * (h("O2(g)", values["blast_temperature_k"]) - h("O2(g)", reference))
                + blast_n2 * (h("N2(g)", values["blast_temperature_k"]) - h("N2(g)", reference))
                + supplemental_o2 * (h("O2(g)", values["supplemental_oxygen_temperature_k"]) - h("O2(g)", reference))
                + values["steam_kmol"] * (h("H2O(g)", values["steam_temperature_k"]) - h("H2O(g)", reference))
            )
        except RepositoryError as exc:
            return fail(str(exc), exc.error_code)
        co_retained = products["CO"] * co_lhv_kj_mol * 1000
        h2_retained = products["H2"] * h2_lhv_kj_mol * 1000
        effective_lhv = values["effective_fuel_lhv_mj"] * 1000
        fuel_sensible = values["fuel_sensible_enthalpy_mj"] * 1000
        process_heat = values["fuel_process_heat_demand_mj"] * 1000
        available = effective_lhv - co_retained - h2_retained + reactant_sensible + fuel_sensible - process_heat
        if available <= 0:
            return fail("有效燃料能、反应物显热不足以覆盖保留化学能和工艺吸热", "MODEL_NOT_APPLICABLE")

        def product_sensible(temperature: float) -> float:
            return 1000 * math.fsum(
                amount * (h(f"{species}(g)", temperature) - h(f"{species}(g)", reference))
                for species, amount in products.items()
            )

        lower, upper = values["temperature_lower_k"], values["temperature_upper_k"]
        try:
            f_lower = product_sensible(lower) - available
            f_upper = product_sensible(upper) - available
        except RepositoryError as exc:
            return fail(str(exc), exc.error_code)
        if f_lower > 0 or f_upper < 0:
            return fail("求根温区未括住RAFT能量零点", "MODEL_NOT_APPLICABLE")
        iterations = 0
        if abs(f_lower) <= 1e-8:
            root = lower
        elif abs(f_upper) <= 1e-8:
            root = upper
        else:
            lo, hi = lower, upper
            for iterations in range(1, 101):
                mid = (lo + hi) / 2
                try:
                    value = product_sensible(mid) - available
                except RepositoryError as exc:
                    return fail(str(exc), exc.error_code)
                if abs(value) <= max(1e-6, available * 1e-10) or hi - lo <= 1e-8:
                    lo = hi = mid
                    break
                if value < 0:
                    lo = mid
                else:
                    hi = mid
            root = (lo + hi) / 2
        try:
            product_heat = product_sensible(root)
        except RepositoryError as exc:
            return fail(str(exc), exc.error_code)
        residual = product_heat - available
        atom_input = {
            "C": fuel["C"],
            "H": fuel["H"] + 2 * values["steam_kmol"],
            "O": oxygen_atoms,
            "N": 2 * blast_n2 + fuel["N"],
        }
        atom_output = {"C": products["CO"], "H": 2 * products["H2"], "O": products["CO"], "N": 2 * products["N2"]}
        atom_residuals = {key: atom_output[key] - atom_input[key] for key in atom_input}
        warnings = []
        if values["supplemental_oxygen_nm3"] == 0:
            warnings.append(BoundaryWarning("supplemental_oxygen_nm3", "无富氧，位于该输入的零边界"))
        if values["steam_kmol"] == 0:
            warnings.append(BoundaryWarning("steam_kmol", "无鼓风湿分，位于该输入的零边界"))
        return ModelResult(True, result={
            "raft_temperature_k": root,
            "product_gas_amounts_kmol": products,
            "product_gas_mole_fractions": {key: value / total_products for key, value in products.items()},
            "total_product_gas_kmol": total_products,
            "input_oxygen_atom_kmol": oxygen_atoms,
            "reacting_carbon_kmol": fuel["C"],
            "effective_fuel_lhv_kj": effective_lhv,
            "co_retained_chemical_energy_kj": co_retained,
            "h2_retained_chemical_energy_kj": h2_retained,
            "reactant_sensible_enthalpy_kj": reactant_sensible,
            "fuel_sensible_enthalpy_kj": fuel_sensible,
            "fuel_process_heat_demand_kj": process_heat,
            "available_product_sensible_heat_kj": available,
            "product_sensible_enthalpy_kj": product_heat,
            "energy_balance_residual_kj": residual,
            "atom_balance_residuals_kmol": atom_residuals,
            "solver_iterations": iterations,
            "method": "BF raceway atom balance + PostgreSQL GRI-Mech NASA7 enthalpy + bisection",
        }, boundary_check=BoundaryCheck(not warnings, warnings), provenance=unique_provenance(records))
