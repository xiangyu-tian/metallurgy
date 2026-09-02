"""P1-W18 database-qualified iron-reduction and steel-deoxidation tools."""
from __future__ import annotations

import math
import re
from typing import Any

from .base import BaseModelTool, BoundaryCheck, BoundaryWarning, InputField, ModelResult, OutputField, Provenance
from .repositories.reference_repository import (
    R_J_MOL_K,
    RepositoryError,
    atomic_weights,
    shomate_standard_gibbs,
)


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


def unique_provenance(records: list[Provenance]) -> list[Provenance]:
    seen: set[tuple[Any, ...]] = set()
    result: list[Provenance] = []
    for record in records:
        identity = (record.dataset_id, record.table, record.record_id, record.version, record.checksum)
        if identity not in seen:
            seen.add(identity)
            result.append(record)
    return result


IRON_REDUCTION_DATASET = "DS_NIST_JANAF_IRON_REDUCTION_W18"

REDUCTION_STAGES: dict[str, dict[str, Any]] = {
    "hematite_to_magnetite": {
        "solids": {"Fe2O3": -3.0, "Fe3O4": 2.0},
        "equations": {
            "CO": "3Fe2O3(s) + CO(g) -> 2Fe3O4(s) + CO2(g)",
            "H2": "3Fe2O3(s) + H2(g) -> 2Fe3O4(s) + H2O(g)",
        },
    },
    "magnetite_to_wustite": {
        "solids": {"Fe3O4": -1.0, "FeO": 3.0},
        "equations": {
            "CO": "Fe3O4(s) + CO(g) -> 3FeO(s) + CO2(g)",
            "H2": "Fe3O4(s) + H2(g) -> 3FeO(s) + H2O(g)",
        },
    },
    "wustite_to_iron": {
        "solids": {"FeO": -1.0, "Fe": 1.0},
        "equations": {
            "CO": "FeO(s) + CO(g) -> Fe(s) + CO2(g)",
            "H2": "FeO(s) + H2(g) -> Fe(s) + H2O(g)",
        },
    },
}

PHASES = {
    "Fe": "solid_alpha_delta",
    "FeO": "solid",
    "Fe2O3": "solid",
    "Fe3O4": "solid",
    "CO": "gas",
    "CO2": "gas",
    "H2": "gas",
    "H2O": "gas",
}


class E022_IronOxideStepReductionEquilibrium(BaseModelTool):
    model_id, name, version = "E022", "铁氧化物逐级还原平衡", "1.0.0"
    tool_name = "metallurgy_calculate_iron_oxide_step_reduction_equilibrium"
    scenario = "高炉低碳"
    priority = "P1"
    status = "qualified"
    qualification_status = "qualified"
    count_eligible = True
    description = "由指定NIST/JANAF数据库分段计算铁氧化物三阶段CO或H2还原的标准Gibbs能、Kp、平衡气比及实际Q/K。"
    applicable_boundary = (
        "500至1100 K；纯Fe2O3/Fe3O4/FeO/Fe固相活度为1、气相理想且采用1 bar标准态；"
        "不覆盖非化学计量FeO、固溶体、相变区精细处理或动力学。"
    )
    formula_reference = "NIST Shomate equations; delta_r G standard state sum; Kp=exp(-delta_r G/(RT)); Q=p(oxidized gas)/p(reducing gas)"
    source_version = "nist-janaf-iron-reduction-w18-v1"
    data_source = ["PostgreSQL DS_NIST_JANAF_IRON_REDUCTION_W18", "NIST Chemistry WebBook SRD 69 / JANAF"]
    source_records = [
        {"source_id": IRON_REDUCTION_DATASET, "name": "NIST-JANAF iron-oxide reduction Shomate segments", "version": "2026.09-w18-v1", "url": "https://webbook.nist.gov/chemistry/"},
    ]
    required_data = ["Fe/FeO/Fe2O3/Fe3O4及CO/CO2/H2/H2O在调用温度的同版本Shomate记录"]
    failure_modes = ["数据库不可用", "指定数据集或物种分段缺失", "温度超500至1100 K", "气体分压非正或非有限", "标准Gibbs能、Kp或Q/K非有限"]
    independent_validation = ["三阶段反应逐元素守恒", "Kp由数据库逐物种Gibbs和exp(-deltaG/RT)独立复算", "平衡氧化气/还原气比等于Kp", "实际气比等于Kp时Q/K为1", "数据库关闭时不得常数兜底"]
    dependencies = ["A006", "B005", "B009"]
    relations = [
        rel("depends_on", "A006", "各阶段反应式可由A006独立核验元素守恒"),
        rel("depends_on", "B005", "逐物种标准态Gibbs沿用B005的参考态语义"),
        rel("overlaps", "B009", "均由标准Gibbs求平衡常数；E022限定铁氧化物逐级还原并返回气比"),
        rel("complements", "E002", "E002计算总铁物料账，E022计算还原阶段热力学方向"),
        rel("complements", "E011", "E011给出实际还原气利用率，E022给出平衡气比与驱动力"),
    ]
    data_requirement = "VERSIONED_DATABASE_CORRELATION"
    data_access_mode = "database_repository"
    required_dataset_ids = [IRON_REDUCTION_DATASET]
    database_tables = ["metallurgy_v2.thermodynamic_correlation"]
    input_fields = [
        InputField("reaction_stage", "逐级还原阶段", "select", enum=list(REDUCTION_STAGES)),
        InputField("reducing_gas", "还原气", "select", enum=["CO", "H2"]),
        InputField("temperature_k", "温度", "number", unit="K", min_value=500, max_value=1100),
        InputField("reducing_gas_partial_pressure_bar", "还原气分压", "number", unit="bar", min_value=1e-12),
        InputField("oxidized_gas_partial_pressure_bar", "氧化气分压", "number", unit="bar", min_value=1e-12),
    ]
    output_fields = [
        OutputField("reaction_stage", "逐级还原阶段", "string"),
        OutputField("reducing_gas", "还原气", "string"),
        OutputField("reaction_equation", "规范反应式", "string"),
        OutputField("temperature_k", "温度", "number", "K"),
        OutputField("reducing_gas_partial_pressure_bar", "还原气分压", "number", "bar"),
        OutputField("oxidized_gas_partial_pressure_bar", "氧化气分压", "number", "bar"),
        OutputField("delta_g_standard_kj_mol_reaction", "反应标准Gibbs能", "number", "kJ/mol-reaction"),
        OutputField("equilibrium_constant_kp", "无量纲平衡常数Kp", "number", "1"),
        OutputField("equilibrium_oxidized_to_reducing_ratio", "平衡氧化气/还原气比", "number", "1"),
        OutputField("actual_oxidized_to_reducing_ratio", "实际氧化气/还原气比", "number", "1"),
        OutputField("q_over_k", "反应商与平衡常数比", "number", "1"),
        OutputField("reaction_direction", "反应热力学方向", "string"),
        OutputField("species_standard_states", "逐物种标准态分项", "array"),
        OutputField("calculation_method", "计算方法", "string"),
        OutputField("data_version", "数据版本", "string"),
    ]
    validation_rules = [
        {"rule": "approved_three_stage_stoichiometry_and_reducing_gas"},
        {"rule": "temperature_500_to_1100_k_and_positive_partial_pressures"},
        {"rule": "database_pinned_shomate_records_only_no_constant_fallback"},
        {"rule": "kp_and_q_over_k_finite_and_positive"},
    ]
    qualification_cases = [
        {"id": "E022-N1", "kind": "normal", "input": {"reaction_stage": "hematite_to_magnetite", "reducing_gas": "CO", "temperature_k": 800, "reducing_gas_partial_pressure_bar": 0.7, "oxidized_gas_partial_pressure_bar": 0.3}},
        {"id": "E022-N2", "kind": "normal", "input": {"reaction_stage": "magnetite_to_wustite", "reducing_gas": "H2", "temperature_k": 900, "reducing_gas_partial_pressure_bar": 0.8, "oxidized_gas_partial_pressure_bar": 0.2}},
        {"id": "E022-N3", "kind": "normal", "input": {"reaction_stage": "wustite_to_iron", "reducing_gas": "CO", "temperature_k": 1000, "reducing_gas_partial_pressure_bar": 0.6, "oxidized_gas_partial_pressure_bar": 0.4}},
        {"id": "E022-B1", "kind": "boundary", "input": {"reaction_stage": "wustite_to_iron", "reducing_gas": "H2", "temperature_k": 500, "reducing_gas_partial_pressure_bar": 0.5, "oxidized_gas_partial_pressure_bar": 0.5}},
        {"id": "E022-F1", "kind": "failure", "input": {"reaction_stage": "hematite_to_magnetite", "reducing_gas": "CO", "temperature_k": 400, "reducing_gas_partial_pressure_bar": 0.7, "oxidized_gas_partial_pressure_bar": 0.3}},
        {"id": "E022-F2", "kind": "failure", "input": {"reaction_stage": "magnetite_to_wustite", "reducing_gas": "H2", "temperature_k": 900, "reducing_gas_partial_pressure_bar": 0.0, "oxidized_gas_partial_pressure_bar": 0.2}},
    ]
    data_qualification_cases = [{"id": "E022-D1", "input": qualification_cases[0]["input"]}]

    def invoke(self, params: dict, context=None) -> ModelResult:
        stage_name = params.get("reaction_stage")
        reducing_gas = params.get("reducing_gas")
        if stage_name not in REDUCTION_STAGES:
            return fail("reaction_stage不受支持", "MODEL_NOT_APPLICABLE")
        if reducing_gas not in {"CO", "H2"}:
            return fail("reducing_gas必须为CO或H2", "MODEL_NOT_APPLICABLE")
        temperature, error = finite(params.get("temperature_k"), "temperature_k", minimum=500, maximum=1100)
        if error:
            return fail(error, "OUT_OF_DOMAIN")
        reducing_pressure, error = finite(params.get("reducing_gas_partial_pressure_bar"), "reducing_gas_partial_pressure_bar", minimum=0, strict_minimum=True)
        if error:
            return fail(error, "OUT_OF_DOMAIN")
        oxidized_pressure, error = finite(params.get("oxidized_gas_partial_pressure_bar"), "oxidized_gas_partial_pressure_bar", minimum=0, strict_minimum=True)
        if error:
            return fail(error, "OUT_OF_DOMAIN")

        oxidized_gas = "CO2" if reducing_gas == "CO" else "H2O"
        stoichiometry = dict(REDUCTION_STAGES[stage_name]["solids"])
        stoichiometry[reducing_gas] = -1.0
        stoichiometry[oxidized_gas] = 1.0
        species_states = []
        provenance: list[Provenance] = []
        delta_g = 0.0
        try:
            for species, coefficient in stoichiometry.items():
                state, records = shomate_standard_gibbs(species, PHASES[species], temperature)
                provenance.extend(records)
                delta_g += coefficient * float(state["standard_gibbs_kj_mol"])
                species_states.append({
                    "species": species,
                    "phase": PHASES[species],
                    "stoichiometric_coefficient": coefficient,
                    "standard_gibbs_kj_mol": float(state["standard_gibbs_kj_mol"]),
                    "formation_enthalpy_298_kj_mol": float(state["formation_enthalpy_298_kj_mol"]),
                    "enthalpy_increment_kj_mol": float(state["enthalpy_increment_kj_mol"]),
                    "entropy_j_mol_k": float(state["entropy_j_mol_k"]),
                    "source_record_key": state["source_record_key"],
                })
        except RepositoryError as exc:
            return fail(str(exc), exc.error_code)
        log_k = -delta_g * 1000.0 / (R_J_MOL_K * temperature)
        if not math.isfinite(log_k) or abs(log_k) > 700:
            return fail("计算所得ln(Kp)超出有限数值范围", "NUMERICAL_ERROR")
        equilibrium_constant = math.exp(log_k)
        actual_ratio = oxidized_pressure / reducing_pressure
        q_over_k = actual_ratio / equilibrium_constant
        if not all(math.isfinite(value) and value > 0 for value in (equilibrium_constant, actual_ratio, q_over_k)):
            return fail("计算所得Kp、气比或Q/K不是有限正数", "NUMERICAL_ERROR")
        tolerance = 1e-9
        if abs(math.log(q_over_k)) <= tolerance:
            direction = "equilibrium"
        elif q_over_k < 1:
            direction = "forward_reduction"
        else:
            direction = "reverse_oxidation"
        provenance = unique_provenance(provenance)
        versions = sorted({record.version for record in provenance if record.version})
        warnings = []
        if temperature in {500.0, 1100.0}:
            warnings.append(BoundaryWarning("temperature_k", "温度位于批准数据域边界", min_allowed=500, max_allowed=1100))
        return ModelResult(True, result={
            "reaction_stage": stage_name,
            "reducing_gas": reducing_gas,
            "reaction_equation": REDUCTION_STAGES[stage_name]["equations"][reducing_gas],
            "temperature_k": temperature,
            "reducing_gas_partial_pressure_bar": reducing_pressure,
            "oxidized_gas_partial_pressure_bar": oxidized_pressure,
            "delta_g_standard_kj_mol_reaction": delta_g,
            "equilibrium_constant_kp": equilibrium_constant,
            "equilibrium_oxidized_to_reducing_ratio": equilibrium_constant,
            "actual_oxidized_to_reducing_ratio": actual_ratio,
            "q_over_k": q_over_k,
            "reaction_direction": direction,
            "species_standard_states": species_states,
            "calculation_method": "dataset-pinned Shomate standard-state Gibbs sum; ideal-gas Kp at 1 bar",
            "data_version": ",".join(versions),
        }, boundary_check=BoundaryCheck(not warnings, warnings), provenance=provenance)


INTERACTION_ITEM_SCHEMA = {
    "type": "object",
    "properties": {
        "target": {"type": "string", "enum": ["deoxidizer", "oxygen"]},
        "element": {"type": "string"},
        "coefficient": {"type": "number"},
        "mass_percent": {"type": "number", "minimum": 0},
    },
    "required": ["target", "element", "coefficient", "mass_percent"],
    "additionalProperties": False,
}

DEOXIDATION_REACTIONS = {
    "Al": {"m": 2.0, "n": 3.0, "oxide": "Al2O3", "equation": "2[Al] + 3[O] -> Al2O3(s)"},
    "Si": {"m": 1.0, "n": 2.0, "oxide": "SiO2", "equation": "[Si] + 2[O] -> SiO2(s)"},
    "Mn": {"m": 1.0, "n": 1.0, "oxide": "MnO", "equation": "[Mn] + [O] -> MnO(s)"},
}


class H001_SteelDeoxidationEquilibrium(BaseModelTool):
    model_id, name, version = "H001", "显式参数钢液脱氧平衡", "1.0.0"
    tool_name = "metallurgy_calculate_steel_deoxidation_equilibrium"
    scenario = "炉外精炼与洁净钢"
    priority = "P1"
    status = "qualified"
    qualification_status = "qualified"
    count_eligible = True
    description = "按1 wt% Henrian标准态，用调用者给定K或标准Gibbs能及显式Wagner一阶项求Al/Si/Mn脱氧平衡，并以数据库原子量核算计量质量。"
    applicable_boundary = (
        "1773至1973 K；Al/Si/Mn不超过5 wt%、O不超过0.2 wt%；纯或调用者显式给定活度的氧化物；"
        "交互参数和K不由工具臆造，不预测收得率、夹杂上浮或多氧化物固溶。"
    )
    formula_reference = "K=a_oxide/(a_M^m*a_O^n); deltaG_standard=-RT lnK; log10(f_i)=sum(e_i^j*[wt%j]) under the Wagner first-order convention"
    source_version = "explicit-wagner-deoxidation-w18-v1"
    data_source = ["Caller-supplied equilibrium and Wagner parameters", "PostgreSQL DS_IUPAC_AW_2021"]
    source_records = [
        {"source_id": "SIGWORTH-ELLIOTT-1974", "name": "The thermodynamics of liquid dilute iron alloys", "version": "Metal Science 8 (1974)", "url": "https://doi.org/10.1179/msc.1974.8.1.298"},
        {"source_id": "COSTA-E-SILVA-2016", "name": "Application limits of Wagner interaction parameters", "version": "JMMB 52B (2016)", "url": "https://doi.org/10.2298/JMMB150901001C"},
        {"source_id": "DS_IUPAC_AW_2021", "name": "IUPAC standard atomic weights", "version": "2021", "table": "metallurgy_v2.element_reference"},
    ]
    required_data = ["DS_IUPAC_AW_2021中Al/Si/Mn及O原子量", "调用者给定且标准态一致的K或deltaG标准值", "调用者需要时给定Wagner一阶交互项"]
    failure_modes = ["K与标准Gibbs能同时缺失或同时给定", "温度、浓度、氧化物活度或交互项非法", "计算模式所需已知浓度缺失", "结果非正或超稀溶液适用域", "数据库不可用或原子量记录缺失"]
    independent_validation = ["deltaG_standard=-RT lnK双向回代", "Wagner log10活度系数由显式项逐项求和", "求解后反应商Q回代等于K", "脱氧剂、氧及氧化物计量质量闭合", "空交互项时两活度系数严格为1", "数据库关闭时不得硬编码原子量"]
    dependencies = ["A003", "A007", "B009", "B014", "B015", "B016", "B017"]
    relations = [
        rel("depends_on", "A003", "氧化物摩尔质量可由A003和同一原子量数据独立复核"),
        rel("overlaps", "A007", "A007给通用氧/还原剂当量，H001进一步求钢液活度平衡"),
        rel("overlaps", "B009", "均执行deltaG与K换算；H001增加Henrian活度和反应计量"),
        rel("uses_convention_of", "B014", "空交互项退化为理想稀溶液活度"),
        rel("uses_convention_of", "B015", "显式非理想活度与B015同属相同输出不同模型的重叠"),
        rel("complements", "B016", "B016的活度系数可由调用者转写为已审查的显式活度输入"),
        rel("complements", "B017", "B017多组元活度框架可为H001提供更高阶外部参数"),
        rel("upstream_of", "H002", "脱氧后氧活度可作为钢包脱硫边界条件之一"),
        rel("complements", "H003", "H003给达到均匀状态的时间尺度，H001给平衡终态"),
    ]
    data_requirement = "VERSIONED_DATABASE_REFERENCE"
    data_access_mode = "database_repository"
    required_dataset_ids = ["DS_IUPAC_AW_2021"]
    database_tables = ["metallurgy_v2.element_reference"]
    input_fields = [
        InputField("deoxidizer", "脱氧剂", "select", enum=list(DEOXIDATION_REACTIONS)),
        InputField("temperature_k", "钢液温度", "number", unit="K", min_value=1773, max_value=1973),
        InputField("calculation_mode", "计算模式", "select", enum=["equilibrium_oxygen", "required_deoxidizer"]),
        InputField("equilibrium_constant", "平衡常数K", "number", required=False, unit="1", min_value=1e-300),
        InputField("standard_gibbs_j_mol", "反应标准Gibbs能", "number", required=False, unit="J/mol-reaction"),
        InputField("deoxidizer_mass_percent", "钢液中脱氧剂质量百分数", "number", required=False, unit="wt%", min_value=1e-12, max_value=5),
        InputField("oxygen_mass_percent", "钢液中溶解氧质量百分数", "number", required=False, unit="wt%", min_value=1e-12, max_value=0.2),
        InputField("oxide_activity", "氧化物活度", "number", unit="1", min_value=1e-12),
        InputField("interaction_terms", "显式Wagner一阶交互项", "array", required=False, default=[], items=INTERACTION_ITEM_SCHEMA, min_items=0, max_items=64),
        InputField("steel_mass_kg", "钢液质量", "number", unit="kg", min_value=1e-12),
    ]
    output_fields = [
        OutputField("deoxidizer", "脱氧剂", "string"),
        OutputField("oxide_formula", "脱氧产物", "string"),
        OutputField("reaction_equation", "规范脱氧反应", "string"),
        OutputField("calculation_mode", "计算模式", "string"),
        OutputField("temperature_k", "钢液温度", "number", "K"),
        OutputField("equilibrium_constant", "平衡常数K", "number", "1"),
        OutputField("standard_gibbs_j_mol_reaction", "反应标准Gibbs能", "number", "J/mol-reaction"),
        OutputField("log10_activity_coefficient_deoxidizer", "脱氧剂活度系数常用对数", "number", "1"),
        OutputField("log10_activity_coefficient_oxygen", "氧活度系数常用对数", "number", "1"),
        OutputField("activity_coefficient_deoxidizer", "脱氧剂活度系数", "number", "1"),
        OutputField("activity_coefficient_oxygen", "氧活度系数", "number", "1"),
        OutputField("deoxidizer_mass_percent", "平衡脱氧剂质量百分数", "number", "wt%"),
        OutputField("oxygen_mass_percent", "平衡溶解氧质量百分数", "number", "wt%"),
        OutputField("deoxidizer_activity", "脱氧剂Henrian活度", "number", "1"),
        OutputField("oxygen_activity", "氧Henrian活度", "number", "1"),
        OutputField("oxide_activity", "氧化物活度", "number", "1"),
        OutputField("reaction_quotient", "反应商Q", "number", "1"),
        OutputField("q_over_k", "Q/K", "number", "1"),
        OutputField("stoichiometric_deoxidizer_kg_per_kg_oxygen", "每kg氧计量脱氧剂", "number", "kg/kg O"),
        OutputField("stoichiometric_oxide_kg_per_kg_oxygen", "每kg氧计量氧化物", "number", "kg/kg O"),
        OutputField("dissolved_deoxidizer_mass_kg", "钢液中平衡脱氧剂质量", "number", "kg"),
        OutputField("dissolved_oxygen_mass_kg", "钢液中平衡溶解氧质量", "number", "kg"),
        OutputField("activity_standard_state", "活度标准态", "string"),
        OutputField("model_version", "模型版本", "string"),
    ]
    validation_rules = [
        {"rule": "exactly_one_of_equilibrium_constant_or_standard_gibbs"},
        {"rule": "mode_requires_exactly_one_known_concentration"},
        {"rule": "explicit_wagner_terms_with_allowlisted_targets_and_finite_values"},
        {"rule": "dilute_solution_domain_deoxidizer_at_most_5_wt_percent_and_oxygen_at_most_0_2_wt_percent"},
        {"rule": "database_atomic_weights_only_no_static_fallback"},
        {"rule": "reaction_quotient_closes_to_equilibrium_constant"},
    ]
    qualification_cases = [
        {"id": "H001-N1", "kind": "normal", "input": {"deoxidizer": "Al", "temperature_k": 1873, "calculation_mode": "equilibrium_oxygen", "equilibrium_constant": 1e12, "deoxidizer_mass_percent": 0.05, "oxide_activity": 1.0, "interaction_terms": [], "steel_mass_kg": 100000}},
        {"id": "H001-N2", "kind": "normal", "input": {"deoxidizer": "Si", "temperature_k": 1840, "calculation_mode": "equilibrium_oxygen", "standard_gibbs_j_mol": -280000, "deoxidizer_mass_percent": 0.3, "oxide_activity": 0.8, "interaction_terms": [{"target": "deoxidizer", "element": "C", "coefficient": 0.02, "mass_percent": 0.1}, {"target": "oxygen", "element": "C", "coefficient": -0.01, "mass_percent": 0.1}], "steel_mass_kg": 120000}},
        {"id": "H001-N3", "kind": "normal", "input": {"deoxidizer": "Mn", "temperature_k": 1900, "calculation_mode": "required_deoxidizer", "equilibrium_constant": 10000, "oxygen_mass_percent": 0.02, "oxide_activity": 1.0, "interaction_terms": [], "steel_mass_kg": 80000}},
        {"id": "H001-B1", "kind": "boundary", "input": {"deoxidizer": "Mn", "temperature_k": 1773, "calculation_mode": "required_deoxidizer", "equilibrium_constant": 10000, "oxygen_mass_percent": 0.02, "oxide_activity": 1.0, "interaction_terms": [], "steel_mass_kg": 1000}},
        {"id": "H001-F1", "kind": "failure", "input": {"deoxidizer": "Al", "temperature_k": 1873, "calculation_mode": "equilibrium_oxygen", "equilibrium_constant": 1e12, "standard_gibbs_j_mol": -400000, "deoxidizer_mass_percent": 0.05, "oxide_activity": 1.0, "interaction_terms": [], "steel_mass_kg": 100000}},
        {"id": "H001-F2", "kind": "failure", "input": {"deoxidizer": "Al", "temperature_k": 1873, "calculation_mode": "equilibrium_oxygen", "equilibrium_constant": 1.0, "deoxidizer_mass_percent": 0.0001, "oxide_activity": 1.0, "interaction_terms": [], "steel_mass_kg": 100000}},
    ]
    data_qualification_cases = [{"id": "H001-D1", "input": qualification_cases[0]["input"]}]

    @staticmethod
    def _interaction_logs(
        raw_terms: Any,
    ) -> tuple[float | None, float | None, set[str] | None, str | None]:
        if raw_terms is None:
            raw_terms = []
        if not isinstance(raw_terms, list) or len(raw_terms) > 64:
            return None, None, None, "interaction_terms必须是至多64项的数组"
        totals = {"deoxidizer": 0.0, "oxygen": 0.0}
        elements: set[str] = set()
        for index, item in enumerate(raw_terms):
            expected = {"target", "element", "coefficient", "mass_percent"}
            if not isinstance(item, dict) or set(item) != expected:
                return None, None, None, f"interaction_terms[{index}]字段必须恰为target/element/coefficient/mass_percent"
            target = item["target"]
            element = item["element"]
            if target not in totals:
                return None, None, None, f"interaction_terms[{index}].target不受支持"
            if not isinstance(element, str) or not re.fullmatch(r"[A-Z][a-z]?", element.strip()):
                return None, None, None, f"interaction_terms[{index}].element必须是规范元素符号"
            element = element.strip()
            elements.add(element)
            coefficient, error = finite(item["coefficient"], f"interaction_terms[{index}].coefficient")
            if error:
                return None, None, None, error
            mass_percent, error = finite(item["mass_percent"], f"interaction_terms[{index}].mass_percent", minimum=0, maximum=100)
            if error:
                return None, None, None, error
            totals[target] += coefficient * mass_percent
        if any(not math.isfinite(value) or abs(value) > 50 for value in totals.values()):
            return None, None, None, "Wagner活度系数对数超出安全数值域"
        return totals["deoxidizer"], totals["oxygen"], elements, None

    def invoke(self, params: dict, context=None) -> ModelResult:
        deoxidizer = params.get("deoxidizer")
        mode = params.get("calculation_mode")
        if deoxidizer not in DEOXIDATION_REACTIONS:
            return fail("deoxidizer必须为Al、Si或Mn", "MODEL_NOT_APPLICABLE")
        if mode not in {"equilibrium_oxygen", "required_deoxidizer"}:
            return fail("calculation_mode不受支持", "MODEL_NOT_APPLICABLE")
        temperature, error = finite(params.get("temperature_k"), "temperature_k", minimum=1773, maximum=1973)
        if error:
            return fail(error, "OUT_OF_DOMAIN")
        oxide_activity, error = finite(params.get("oxide_activity"), "oxide_activity", minimum=0, strict_minimum=True)
        if error:
            return fail(error, "OUT_OF_DOMAIN")
        steel_mass, error = finite(params.get("steel_mass_kg"), "steel_mass_kg", minimum=0, strict_minimum=True)
        if error:
            return fail(error, "OUT_OF_DOMAIN")

        has_k = params.get("equilibrium_constant") is not None
        has_g = params.get("standard_gibbs_j_mol") is not None
        if has_k == has_g:
            return fail("equilibrium_constant与standard_gibbs_j_mol必须且只能给定一项")
        if has_k:
            equilibrium_constant, error = finite(params.get("equilibrium_constant"), "equilibrium_constant", minimum=0, strict_minimum=True)
            if error:
                return fail(error, "OUT_OF_DOMAIN")
            standard_gibbs = -R_J_MOL_K * temperature * math.log(equilibrium_constant)
        else:
            standard_gibbs, error = finite(params.get("standard_gibbs_j_mol"), "standard_gibbs_j_mol")
            if error:
                return fail(error)
            log_k = -standard_gibbs / (R_J_MOL_K * temperature)
            if abs(log_k) > 700:
                return fail("由standard_gibbs_j_mol得到的ln(K)超出有限数值范围", "NUMERICAL_ERROR")
            equilibrium_constant = math.exp(log_k)
        if not math.isfinite(equilibrium_constant) or equilibrium_constant <= 0 or not math.isfinite(standard_gibbs):
            return fail("K或标准Gibbs能不是有限有效值", "NUMERICAL_ERROR")

        log_f_m, log_f_o, interaction_elements, error = self._interaction_logs(params.get("interaction_terms", []))
        if error:
            return fail(error)
        f_m = 10.0 ** log_f_m
        f_o = 10.0 ** log_f_o
        if not all(math.isfinite(value) and value > 0 for value in (f_m, f_o)):
            return fail("活度系数不是有限正数", "NUMERICAL_ERROR")
        known_m = params.get("deoxidizer_mass_percent")
        known_o = params.get("oxygen_mass_percent")
        if mode == "equilibrium_oxygen":
            if known_m is None or known_o is not None:
                return fail("equilibrium_oxygen模式必须只给deoxidizer_mass_percent")
            m_percent, error = finite(known_m, "deoxidizer_mass_percent", minimum=0, maximum=5, strict_minimum=True)
            if error:
                return fail(error, "OUT_OF_DOMAIN")
            reaction = DEOXIDATION_REACTIONS[deoxidizer]
            m_activity = f_m * m_percent
            o_activity = (oxide_activity / (equilibrium_constant * m_activity ** reaction["m"])) ** (1.0 / reaction["n"])
            o_percent = o_activity / f_o
        else:
            if known_o is None or known_m is not None:
                return fail("required_deoxidizer模式必须只给oxygen_mass_percent")
            o_percent, error = finite(known_o, "oxygen_mass_percent", minimum=0, maximum=0.2, strict_minimum=True)
            if error:
                return fail(error, "OUT_OF_DOMAIN")
            reaction = DEOXIDATION_REACTIONS[deoxidizer]
            o_activity = f_o * o_percent
            m_activity = (oxide_activity / (equilibrium_constant * o_activity ** reaction["n"])) ** (1.0 / reaction["m"])
            m_percent = m_activity / f_m
        if not math.isfinite(m_percent) or not math.isfinite(o_percent) or m_percent <= 0 or o_percent <= 0:
            return fail("平衡浓度不是有限正数", "NUMERICAL_ERROR")
        if m_percent > 5 or o_percent > 0.2:
            return fail("计算结果超出稀溶液适用域：脱氧剂<=5 wt%、氧<=0.2 wt%", "OUT_OF_DOMAIN")

        try:
            weights, provenance = atomic_weights([deoxidizer, "O", *interaction_elements])
        except RepositoryError as exc:
            return fail(str(exc), exc.error_code)
        m_coeff, o_coeff = reaction["m"], reaction["n"]
        deoxidizer_per_oxygen = m_coeff * weights[deoxidizer] / (o_coeff * weights["O"])
        oxide_per_oxygen = (m_coeff * weights[deoxidizer] + o_coeff * weights["O"]) / (o_coeff * weights["O"])
        m_activity = f_m * m_percent
        o_activity = f_o * o_percent
        quotient = oxide_activity / (m_activity ** m_coeff * o_activity ** o_coeff)
        q_over_k = quotient / equilibrium_constant
        values = (deoxidizer_per_oxygen, oxide_per_oxygen, m_activity, o_activity, quotient, q_over_k)
        if not all(math.isfinite(value) and value > 0 for value in values):
            return fail("计量或反应商结果不是有限正数", "NUMERICAL_ERROR")
        warnings = []
        if temperature in {1773.0, 1973.0}:
            warnings.append(BoundaryWarning("temperature_k", "温度位于批准稀溶液模型边界", min_allowed=1773, max_allowed=1973))
        return ModelResult(True, result={
            "deoxidizer": deoxidizer,
            "oxide_formula": reaction["oxide"],
            "reaction_equation": reaction["equation"],
            "calculation_mode": mode,
            "temperature_k": temperature,
            "equilibrium_constant": equilibrium_constant,
            "standard_gibbs_j_mol_reaction": standard_gibbs,
            "log10_activity_coefficient_deoxidizer": log_f_m,
            "log10_activity_coefficient_oxygen": log_f_o,
            "activity_coefficient_deoxidizer": f_m,
            "activity_coefficient_oxygen": f_o,
            "deoxidizer_mass_percent": m_percent,
            "oxygen_mass_percent": o_percent,
            "deoxidizer_activity": m_activity,
            "oxygen_activity": o_activity,
            "oxide_activity": oxide_activity,
            "reaction_quotient": quotient,
            "q_over_k": q_over_k,
            "stoichiometric_deoxidizer_kg_per_kg_oxygen": deoxidizer_per_oxygen,
            "stoichiometric_oxide_kg_per_kg_oxygen": oxide_per_oxygen,
            "dissolved_deoxidizer_mass_kg": steel_mass * m_percent / 100.0,
            "dissolved_oxygen_mass_kg": steel_mass * o_percent / 100.0,
            "activity_standard_state": "1 wt% Henrian dissolved-solute standard state; oxide activity explicit; gas standard state not used",
            "model_version": "explicit-wagner-deoxidation-w18-v1",
        }, boundary_check=BoundaryCheck(not warnings, warnings), provenance=unique_provenance(provenance))
