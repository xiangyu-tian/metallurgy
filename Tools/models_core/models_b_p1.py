"""P1 workbook-catalog thermodynamics and solution tools.

Data-backed tools in this module read every thermochemical value through the
read-only PostgreSQL repository.  Formula tools require the caller to supply
parameter provenance; no alloy-specific constants are embedded here.
"""
from __future__ import annotations

import math
from typing import Any

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, brentq, minimize

from .base import BoundaryCheck, BoundaryWarning, InputField, ModelResult, OutputField, Provenance
from .models_a import normalize_composition, parse_formula
from .models_b import ThermoTool, _fail, rel
from .repositories.reference_repository import RepositoryError, nasa7, reaction_properties, shomate
from .thermo_assets import R_J_MOL_K


def _reaction_species_key(item: dict[str, Any]) -> str:
    phase = str(item.get("phase") or "").strip().lower()
    return f"{item['species']}({phase})" if phase else str(item["species"])


def _unique_provenance(records: list[Provenance]) -> list[Provenance]:
    unique: list[Provenance] = []
    seen: set[tuple[Any, ...]] = set()
    for record in records:
        key = (record.dataset_id, record.table, record.record_id, record.version)
        if key not in seen:
            seen.add(key)
            unique.append(record)
    return unique


def _finite_mapping(raw: Any, label: str, *, nonnegative: bool = True) -> tuple[dict[str, float] | None, str | None]:
    if not isinstance(raw, dict) or not raw:
        return None, f"{label}必须是非空对象"
    result: dict[str, float] = {}
    for key, value in raw.items():
        if not isinstance(key, str) or not key.strip():
            return None, f"{label}包含空物种名"
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None, f"{label}.{key}必须是数值"
        if not math.isfinite(number) or (nonnegative and number < 0):
            return None, f"{label}.{key}必须是{'非负' if nonnegative else ''}有限数值"
        result[key.strip()] = number
    return result, None


class B012_AdiabaticReactionTemperature(ThermoTool):
    model_id, name, version = "B012", "绝热反应温度", "1.0.0"
    tool_name = "metallurgy_calculate_adiabatic_reaction_temperature"
    priority = "P1"
    source_version = "2026.09-p1-w6b"
    description = "用数据库反应焓和Shomate显热，在指定反应进度下求解绝热定压终温及能量闭合。"
    applicable_boundary = (
        "单个数据库反应、固定压力、无外部热损；物种必须具有覆盖初温与终温的Shomate记录。"
        "首版至多处理一个由调用者提供来源的等温相变。"
    )
    formula_reference = (
        "xi*DeltaH_r,298 + sum(n_final*h_i(Tad)) - sum(n_initial*h_i(Tin)) + Q_phase = 0"
    )
    required_dataset_ids = ["DS002"]
    database_tables = [
        "metallurgy_v2.reaction_definition",
        "metallurgy_v2.reaction_property",
        "metallurgy_v2.thermodynamic_correlation",
    ]
    source_records = [{
        "source_id": "DS002",
        "name": "NIST-JANAF/Barin reaction and Shomate thermochemistry records",
        "version": "2026.08-v1",
        "url": "https://cantera.org/dev/examples/python/thermo/adiabatic.html",
    }]
    data_source = ["PostgreSQL DS002 reaction properties and Shomate correlations"]
    required_data = ["已登记反应计量", "298.15 K反应焓", "各物种Shomate显热"]
    failure_modes = [
        "反应或物种未登记", "反应进度导致负物质的量", "求根温区未括住能量零点",
        "热物性温区不覆盖", "相变参数不完整或与组成不匹配",
    ]
    independent_validation = [
        "能量方程回代残差", "零转化时终温等于初温", "增加惰性稀释降低放热反应终温",
        "相变平台以潜热分数闭合",
    ]
    dependencies = ["A006", "B003", "B006"]
    relations = [
        rel("requires_validation_by", "A006", "数据库反应仍应满足元素守恒"),
        rel("uses_output_of", "B006", "反应焓项与B006使用同一记录"),
        rel("uses_model_of", "B003", "各物种显热使用同一Shomate焓增量"),
        rel("overlaps", "D002", "都执行能量守恒，但本工具不含转炉装料和热损模型"),
    ]
    input_fields = [
        InputField("reaction", "数据库反应式", "string"),
        InputField("feed_moles", "反应前物种量", "object", unit="mol", description="物种键须含相态，如C(s)、O2(g)"),
        InputField("initial_temperature_k", "初始温度", "number", unit="K", min_value=1e-12),
        InputField("conversion_fraction", "限制反应物转化率", "number", unit="1", min_value=0, max_value=1),
        InputField("temperature_lower_k", "求根下界", "number", unit="K", min_value=1e-12),
        InputField("temperature_upper_k", "求根上界", "number", unit="K", min_value=1e-12),
        InputField("phase_transition_from_species", "相变前物种键", "string", required=False),
        InputField("phase_transition_to_species", "相变后物种键", "string", required=False),
        InputField("phase_transition_temperature_k", "相变温度", "number", required=False, unit="K", min_value=1e-12),
        InputField("phase_transition_latent_heat_kj_mol", "相变潜热", "number", required=False, unit="kJ/mol", min_value=0),
        InputField("phase_transition_source", "相变参数来源", "string", required=False),
        InputField("phase_transition_version", "相变参数版本", "string", required=False),
    ]
    output_fields = [
        OutputField("reaction", "规范反应式", "string"),
        OutputField("adiabatic_temperature_k", "绝热终温", "number", "K"),
        OutputField("conversion_fraction", "限制反应物转化率", "number", "1"),
        OutputField("reaction_extent_mol", "反应进度", "number", "mol-reaction"),
        OutputField("initial_moles", "初始物质的量", "object", "mol"),
        OutputField("final_moles", "终态物质的量", "object", "mol"),
        OutputField("reaction_enthalpy_term_kj", "298K反应焓项", "number", "kJ"),
        OutputField("initial_sensible_enthalpy_kj", "初态显热", "number", "kJ"),
        OutputField("final_sensible_enthalpy_kj", "终态显热", "number", "kJ"),
        OutputField("phase_transition_heat_kj", "相变潜热项", "number", "kJ"),
        OutputField("phase_transition_fraction", "相变完成分数", "number", "1"),
        OutputField("energy_balance_residual_kj", "能量闭合残差", "number", "kJ"),
        OutputField("solver_status", "求解状态", "string"),
        OutputField("method", "方法", "string"),
    ]
    validation_rules = [
        {"rule": "database_reaction", "field": "reaction"},
        {"rule": "nonnegative_mapping", "field": "feed_moles"},
        {"rule": "ordered_bounds", "fields": ["temperature_lower_k", "temperature_upper_k"]},
        {"rule": "all_or_none", "fields": [
            "phase_transition_from_species", "phase_transition_to_species",
            "phase_transition_temperature_k", "phase_transition_latent_heat_kj_mol",
            "phase_transition_source", "phase_transition_version",
        ]},
    ]
    _base_case = {
        "reaction": "C + O₂ → CO₂",
        "feed_moles": {"C(s)": 1, "O2(g)": 1, "N2(g)": 3.76},
        "initial_temperature_k": 298.15,
        "conversion_fraction": 1,
        "temperature_lower_k": 298.15,
        "temperature_upper_k": 3500,
    }
    qualification_cases = [
        {"id": "B012-N1", "kind": "normal", "input": _base_case},
        {"id": "B012-N2", "kind": "normal", "input": {**_base_case, "feed_moles": {"C(s)": 1, "O2(g)": 1, "N2(g)": 7.52}}},
        {"id": "B012-N3", "kind": "normal", "input": {**_base_case, "conversion_fraction": 0}},
        {"id": "B012-F1", "kind": "failure", "input": {**_base_case, "reaction": "Unknown -> X"}},
        {"id": "B012-F2", "kind": "failure", "input": {**_base_case, "temperature_upper_k": 400}},
    ]
    data_qualification_cases = [{"id": "B012-D1", "input": _base_case}]

    @staticmethod
    def _transition(params: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
        fields = {
            "from": params.get("phase_transition_from_species"),
            "to": params.get("phase_transition_to_species"),
            "temperature": params.get("phase_transition_temperature_k"),
            "latent": params.get("phase_transition_latent_heat_kj_mol"),
            "source": params.get("phase_transition_source"),
            "version": params.get("phase_transition_version"),
        }
        provided = [value is not None and value != "" for value in fields.values()]
        if not any(provided):
            return None, None
        if not all(provided):
            return None, "相变参数必须六项全部提供"
        if fields["from"] == fields["to"]:
            return None, "相变前后物种键不能相同"
        try:
            temperature = float(fields["temperature"])
            latent = float(fields["latent"])
        except (TypeError, ValueError):
            return None, "相变温度和潜热必须为数值"
        if not math.isfinite(temperature) or temperature <= 0 or not math.isfinite(latent) or latent < 0:
            return None, "相变温度必须为正有限值，潜热必须为非负有限值"
        fields["temperature"] = temperature
        fields["latent"] = latent
        return fields, None

    def invoke(self, params, context=None):
        feed, error = _finite_mapping(params.get("feed_moles"), "feed_moles")
        if error:
            return _fail(error)
        transition, error = self._transition(params)
        if error:
            return _fail(error, "MISSING_DATA")
        try:
            initial_temperature = float(params["initial_temperature_k"])
            conversion = float(params["conversion_fraction"])
            lower = float(params["temperature_lower_k"])
            upper = float(params["temperature_upper_k"])
        except (KeyError, TypeError, ValueError) as exc:
            return _fail(f"温度或转化率参数无效: {exc}")
        if lower >= upper:
            return _fail("求根温度下界必须小于上界")
        if not lower <= initial_temperature <= upper:
            return _fail("初始温度必须位于求根温区内", "OUT_OF_DOMAIN")
        try:
            reaction, provenance = reaction_properties(params["reaction"], "DS002")
        except RepositoryError as exc:
            return _fail(str(exc), exc.error_code)

        reactants = {_reaction_species_key(item): float(item["coeff"]) for item in reaction["reactants"]}
        products = {_reaction_species_key(item): float(item["coeff"]) for item in reaction["products"]}
        missing = [species for species in reactants if feed.get(species, 0.0) <= 0]
        if missing:
            return _fail(f"feed_moles缺少正量反应物: {', '.join(missing)}", "MISSING_DATA")
        maximum_extent = min(feed[species] / coefficient for species, coefficient in reactants.items())
        extent = maximum_extent * conversion
        final = dict(feed)
        for species, coefficient in reactants.items():
            final[species] = final.get(species, 0.0) - extent * coefficient
        for species, coefficient in products.items():
            final[species] = final.get(species, 0.0) + extent * coefficient
        tolerance = max(1e-12, maximum_extent * 1e-12)
        if any(value < -tolerance for value in final.values()):
            return _fail("反应进度导致终态物质的量为负")
        final = {species: max(0.0, value) for species, value in final.items()}
        if transition and final.get(str(transition["from"]), 0.0) <= 0:
            return _fail("相变前物种不在终态正量组成中", "MODEL_NOT_APPLICABLE")

        records = list(provenance)

        def sensible_for_species(species: str, temperature: float, phase_fraction: float = 1.0) -> float:
            if transition and species == transition["from"] and temperature >= transition["temperature"]:
                transition_temperature = float(transition["temperature"])
                h_from, source_from = shomate(species, transition_temperature)
                h_from_reference, source_from_reference = shomate(species, 298.15)
                h_to_at_transition, source_to_1 = shomate(str(transition["to"]), transition_temperature)
                h_to, source_to_2 = shomate(str(transition["to"]), temperature)
                records.extend(source_from + source_from_reference + source_to_1 + source_to_2)
                return (
                    h_from["H_minus_H298"]
                    - h_from_reference["H_minus_H298"]
                    + float(transition["latent"]) * phase_fraction
                    + h_to["H_minus_H298"]
                    - h_to_at_transition["H_minus_H298"]
                )
            properties, source = shomate(species, temperature)
            reference, reference_source = shomate(species, 298.15)
            records.extend(source + reference_source)
            return float(properties["H_minus_H298"] - reference["H_minus_H298"])

        try:
            initial_sensible = sum(
                moles * sensible_for_species(species, initial_temperature)
                for species, moles in feed.items() if moles > 0
            )
        except RepositoryError as exc:
            return _fail(str(exc), exc.error_code)
        reaction_term = extent * float(reaction["DELTA_H_STD"])

        def energy(temperature: float, phase_fraction: float = 1.0) -> tuple[float, float, float]:
            final_sensible = sum(
                moles * sensible_for_species(species, temperature, phase_fraction)
                for species, moles in final.items() if moles > 0
            )
            phase_heat = 0.0
            if transition and temperature >= transition["temperature"]:
                phase_heat = final[str(transition["from"])] * float(transition["latent"]) * phase_fraction
            return reaction_term + final_sensible - initial_sensible, final_sensible, phase_heat

        if extent <= tolerance:
            try:
                residual, final_sensible, phase_heat = energy(initial_temperature, 0.0)
            except RepositoryError as exc:
                return _fail(str(exc), exc.error_code)
            return ModelResult(True, result={
                "reaction": reaction["reaction"],
                "adiabatic_temperature_k": initial_temperature,
                "conversion_fraction": conversion,
                "reaction_extent_mol": extent,
                "initial_moles": feed,
                "final_moles": final,
                "reaction_enthalpy_term_kj": reaction_term,
                "initial_sensible_enthalpy_kj": initial_sensible,
                "final_sensible_enthalpy_kj": final_sensible,
                "phase_transition_heat_kj": phase_heat,
                "phase_transition_fraction": 0.0,
                "energy_balance_residual_kj": residual,
                "solver_status": "zero-conversion identity",
                "method": "adiabatic enthalpy balance / database Shomate",
            }, provenance=_unique_provenance(records))

        phase_fraction = 0.0
        solver_status = "brentq converged"
        try:
            if transition and lower <= transition["temperature"] <= upper:
                transition_temperature = float(transition["temperature"])
                below, _, _ = energy(transition_temperature, 0.0)
                above, _, _ = energy(transition_temperature, 1.0)
                if below <= 0 <= above and above > below:
                    root = transition_temperature
                    phase_fraction = -below / (above - below)
                    residual, final_sensible, phase_heat = energy(root, phase_fraction)
                    solver_status = "phase-transition plateau closure"
                else:
                    root = brentq(lambda value: energy(value)[0], lower, upper, xtol=1e-8, rtol=1e-12)
                    phase_fraction = 1.0 if root >= transition_temperature else 0.0
                    residual, final_sensible, phase_heat = energy(root, phase_fraction)
            else:
                root = brentq(lambda value: energy(value)[0], lower, upper, xtol=1e-8, rtol=1e-12)
                residual, final_sensible, phase_heat = energy(root)
        except RepositoryError as exc:
            return _fail(str(exc), exc.error_code)
        except ValueError as exc:
            return _fail(f"绝热温度求根失败（温区未括住能量零点或热物性不可用）: {exc}", "OUT_OF_DOMAIN")
        if abs(residual) > max(1e-7, abs(reaction_term) * 1e-9):
            return _fail(f"能量闭合残差{residual:.3e} kJ超过准入阈值", "NUMERICAL_ERROR")
        return ModelResult(True, result={
            "reaction": reaction["reaction"],
            "adiabatic_temperature_k": float(root),
            "conversion_fraction": conversion,
            "reaction_extent_mol": extent,
            "initial_moles": feed,
            "final_moles": final,
            "reaction_enthalpy_term_kj": reaction_term,
            "initial_sensible_enthalpy_kj": initial_sensible,
            "final_sensible_enthalpy_kj": final_sensible,
            "phase_transition_heat_kj": phase_heat,
            "phase_transition_fraction": phase_fraction,
            "energy_balance_residual_kj": residual,
            "solver_status": solver_status,
            "method": "adiabatic enthalpy balance / database Shomate / SciPy brentq",
        }, provenance=_unique_provenance(records))


class B013_IdealGasEquilibrium(ThermoTool):
    model_id, name, version = "B013", "理想气体混合平衡", "1.0.0"
    tool_name = "metallurgy_solve_ideal_gas_equilibrium"
    priority = "P1"
    source_version = "2026.09-p1-w6b"
    description = "由数据库NASA7标准Gibbs能最小化理想气体混合物总Gibbs能，返回元素守恒的平衡组成。"
    applicable_boundary = (
        "仅适用于数据库NASA7覆盖的中性理想气体，200–3500 K、正压力、最多12种物种和8种元素；"
        "不含凝聚相、离子、真实气体逸度或反应动力学。"
    )
    formula_reference = "min G/RT=sum n_i[g_i^0/RT+ln(y_i P/P^0)], subject to A*n=b and n_i>=0"
    required_dataset_ids = ["DS_NASA7_GRI30"]
    database_tables = ["metallurgy_v2.thermodynamic_correlation"]
    source_records = [{
        "source_id": "DS_NASA7_GRI30",
        "name": "GRI-Mech 3.0 NASA7 subset",
        "version": "NASA7-GRI30-SUBSET-V1",
        "url": "https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=959350",
    }]
    data_source = ["PostgreSQL DS_NASA7_GRI30 NASA7 correlations"]
    required_data = ["候选物种NASA7标准态热力学", "可解析的元素组成"]
    failure_modes = [
        "候选物种缺少NASA7", "初始物种不在候选集合", "温度超出数据库范围",
        "约束不可行或求解不收敛", "元素守恒或Gibbs下降闸门失败",
    ]
    independent_validation = [
        "逐元素初末守恒", "平衡总Gibbs能不高于初态", "水煤气变换Qp与NASA7 Kp一致",
        "无可行反应自由度时组成保持不变",
    ]
    dependencies = ["A002", "B002"]
    relations = [
        rel("uses_output_of", "A002", "候选物种元素矩阵采用相同化学式解析"),
        rel("uses_output_of", "B002", "标准态Gibbs能来自同一数据库NASA7记录"),
        rel("cross_validates", "B009", "单反应体系的平衡反应商应等于标准K"),
        rel("distinct_from", "B012", "本工具优化可变平衡组成；B012在给定反应进度下求绝热温度"),
    ]
    _candidate_item = {"type": "string", "description": "带(g)相态的NASA7物种键"}
    input_fields = [
        InputField("candidate_species", "候选气体物种", "array", items=_candidate_item, min_items=2, max_items=12),
        InputField("initial_moles", "初始物质的量", "object", unit="mol"),
        InputField("temperature_k", "温度", "number", unit="K", min_value=200, max_value=3500),
        InputField("pressure_pa", "总压力", "number", unit="Pa", min_value=1, max_value=1e8),
        InputField("max_iterations", "最大迭代次数", "number", required=False, default=1000, unit="1", min_value=20, max_value=10000),
        InputField("element_tolerance_mol", "元素守恒绝对容差", "number", required=False, default=1e-8, unit="mol", min_value=1e-12, max_value=1e-4),
    ]
    output_fields = [
        OutputField("equilibrium_moles", "平衡物质的量", "object", "mol"),
        OutputField("mole_fractions", "平衡摩尔分数", "object", "1"),
        OutputField("initial_element_totals_mol", "初始元素总量", "object", "mol-atom"),
        OutputField("final_element_totals_mol", "终态元素总量", "object", "mol-atom"),
        OutputField("element_balance_residuals_mol", "元素守恒残差", "object", "mol-atom"),
        OutputField("initial_total_gibbs_kj", "初态总Gibbs能", "number", "kJ"),
        OutputField("equilibrium_total_gibbs_kj", "平衡总Gibbs能", "number", "kJ"),
        OutputField("gibbs_decrease_kj", "Gibbs能下降量", "number", "kJ"),
        OutputField("temperature_k", "温度", "number", "K"),
        OutputField("pressure_pa", "总压力", "number", "Pa"),
        OutputField("standard_pressure_pa", "标准压力", "number", "Pa"),
        OutputField("iterations", "优化迭代次数", "number", "1"),
        OutputField("converged", "是否收敛", "boolean"),
        OutputField("solver_message", "求解器信息", "string"),
        OutputField("method", "方法", "string"),
    ]
    validation_rules = [
        {"rule": "unique_gas_species", "field": "candidate_species"},
        {"rule": "initial_species_subset", "fields": ["initial_moles", "candidate_species"]},
        {"rule": "database_temperature_range", "fields": ["candidate_species", "temperature_k"]},
        {"rule": "positive", "field": "pressure_pa"},
    ]
    _wgs_case = {
        "candidate_species": ["CO(g)", "H2O(g)", "CO2(g)", "H2(g)"],
        "initial_moles": {"CO(g)": 1, "H2O(g)": 1},
        "temperature_k": 1000,
        "pressure_pa": 100000,
    }
    qualification_cases = [
        {"id": "B013-N1", "kind": "normal", "input": _wgs_case},
        {"id": "B013-N2", "kind": "normal", "input": {
            "candidate_species": ["CO2(g)", "CO(g)", "O2(g)"],
            "initial_moles": {"CO2(g)": 1}, "temperature_k": 2500, "pressure_pa": 100000,
        }},
        {"id": "B013-N3", "kind": "normal", "input": {
            "candidate_species": ["O2(g)", "N2(g)"],
            "initial_moles": {"O2(g)": 1, "N2(g)": 3.76}, "temperature_k": 1000, "pressure_pa": 100000,
        }},
        {"id": "B013-F1", "kind": "failure", "input": {
            "candidate_species": ["CO2(g)", "O2(g)"],
            "initial_moles": {"CO(g)": 1}, "temperature_k": 1000, "pressure_pa": 100000,
        }},
        {"id": "B013-F2", "kind": "failure", "input": {
            "candidate_species": ["CH4(g)", "O2(g)"],
            "initial_moles": {"CH4(g)": 1, "O2(g)": 2}, "temperature_k": 1000, "pressure_pa": 100000,
        }},
    ]
    data_qualification_cases = [{"id": "B013-D1", "input": _wgs_case}]

    @staticmethod
    def _independent_rows(matrix: np.ndarray) -> list[int]:
        selected: list[int] = []
        rank = 0
        for index in range(matrix.shape[0]):
            candidate = matrix[selected + [index], :]
            candidate_rank = int(np.linalg.matrix_rank(candidate, tol=1e-12))
            if candidate_rank > rank:
                selected.append(index)
                rank = candidate_rank
        return selected

    def invoke(self, params, context=None):
        candidates = params.get("candidate_species")
        if not isinstance(candidates, list) or not 2 <= len(candidates) <= 12:
            return _fail("candidate_species必须包含2至12个物种")
        if any(not isinstance(item, str) or not item.strip() for item in candidates):
            return _fail("candidate_species必须是非空字符串数组")
        candidates = [item.strip() for item in candidates]
        if len(candidates) != len(set(candidates)):
            return _fail("candidate_species不得重复")
        if any(not species.lower().endswith("(g)") for species in candidates):
            return _fail("B013仅接受带(g)相态的气体物种", "MODEL_NOT_APPLICABLE")
        initial_mapping, error = _finite_mapping(params.get("initial_moles"), "initial_moles")
        if error:
            return _fail(error)
        extra = sorted(set(initial_mapping) - set(candidates))
        if extra:
            return _fail(f"初始物种未包含在候选集合: {', '.join(extra)}", "MISSING_DATA")
        initial = np.asarray([initial_mapping.get(species, 0.0) for species in candidates], dtype=float)
        if float(np.sum(initial)) <= 0:
            return _fail("初始总物质的量必须大于零")
        try:
            temperature = float(params["temperature_k"])
            pressure = float(params["pressure_pa"])
            max_iterations_number = float(params.get("max_iterations", 1000))
            tolerance = float(params.get("element_tolerance_mol", 1e-8))
        except (KeyError, TypeError, ValueError) as exc:
            return _fail(f"数值参数无效: {exc}")
        if not max_iterations_number.is_integer():
            return _fail("max_iterations必须是整数")
        max_iterations = int(max_iterations_number)

        compositions: list[dict[str, float]] = []
        elements: set[str] = set()
        standard_gibbs: list[float] = []
        provenance: list[Provenance] = []
        for species in candidates:
            composition, formula_error = parse_formula(species)
            if formula_error:
                return _fail(f"候选物种{species}无法解析: {formula_error}")
            compositions.append(composition)
            elements.update(composition)
            try:
                properties, records = nasa7(species, temperature)
            except RepositoryError as exc:
                return _fail(str(exc), exc.error_code)
            standard_gibbs.append(float(properties["G"]))
            provenance.extend(records)
        element_names = sorted(elements)
        if len(element_names) > 8:
            return _fail("候选物种涉及元素超过8种", "OUT_OF_DOMAIN")
        matrix = np.asarray([
            [composition.get(element, 0.0) for composition in compositions]
            for element in element_names
        ], dtype=float)
        initial_totals = matrix @ initial
        independent = self._independent_rows(matrix)
        constraint_matrix = matrix[independent, :]
        constraint_totals = initial_totals[independent]
        standard_gibbs_array = np.asarray(standard_gibbs, dtype=float)
        standard_pressure = 100000.0
        pressure_ratio = pressure / standard_pressure
        g_rt = standard_gibbs_array * 1000.0 / (R_J_MOL_K * temperature)

        def dimensionless_gibbs(moles: np.ndarray) -> float:
            total = float(np.sum(moles))
            if not math.isfinite(total) or total <= 0 or np.any(moles < 0):
                return 1e100
            fractions = np.maximum(moles / total, 1e-300)
            terms = np.where(
                moles > 0,
                moles * (g_rt + np.log(fractions * pressure_ratio)),
                0.0,
            )
            value = float(np.sum(terms))
            return value if math.isfinite(value) else 1e100

        def gradient(moles: np.ndarray) -> np.ndarray:
            total = max(float(np.sum(moles)), 1e-300)
            fractions = np.maximum(moles / total, 1e-300)
            return g_rt + np.log(fractions * pressure_ratio)

        initial_g_dimless = dimensionless_gibbs(initial)
        constraints = LinearConstraint(constraint_matrix, constraint_totals, constraint_totals)
        result = minimize(
            dimensionless_gibbs,
            initial,
            method="SLSQP",
            jac=gradient,
            bounds=Bounds(np.zeros(len(candidates)), np.full(len(candidates), np.inf)),
            constraints=constraints,
            options={"ftol": min(1e-12, tolerance * 0.01), "maxiter": max_iterations, "disp": False},
        )
        equilibrium = np.maximum(np.asarray(result.x, dtype=float), 0.0)
        final_totals = matrix @ equilibrium
        residuals = final_totals - initial_totals
        max_residual = float(np.max(np.abs(residuals))) if residuals.size else 0.0
        equilibrium_g_dimless = dimensionless_gibbs(equilibrium)
        if (
            not result.success
            or np.any(~np.isfinite(equilibrium))
            or max_residual > tolerance
            or equilibrium_g_dimless > initial_g_dimless + 1e-8
        ):
            return _fail(
                f"理想气体Gibbs最小化未通过收敛/守恒闸门: {result.message}; "
                f"max element residual={max_residual:.3e}",
                "NUMERICAL_ERROR",
            )
        total_moles = float(np.sum(equilibrium))
        fractions = equilibrium / total_moles
        scale = R_J_MOL_K * temperature / 1000.0
        initial_g = initial_g_dimless * scale
        equilibrium_g = equilibrium_g_dimless * scale
        return ModelResult(True, result={
            "equilibrium_moles": {species: float(value) for species, value in zip(candidates, equilibrium)},
            "mole_fractions": {species: float(value) for species, value in zip(candidates, fractions)},
            "initial_element_totals_mol": {element: float(value) for element, value in zip(element_names, initial_totals)},
            "final_element_totals_mol": {element: float(value) for element, value in zip(element_names, final_totals)},
            "element_balance_residuals_mol": {element: float(value) for element, value in zip(element_names, residuals)},
            "initial_total_gibbs_kj": initial_g,
            "equilibrium_total_gibbs_kj": equilibrium_g,
            "gibbs_decrease_kj": initial_g - equilibrium_g,
            "temperature_k": temperature,
            "pressure_pa": pressure,
            "standard_pressure_pa": standard_pressure,
            "iterations": int(result.nit),
            "converged": True,
            "solver_message": str(result.message),
            "method": "ideal-gas Gibbs minimization / database NASA7 / SciPy SLSQP",
        }, provenance=_unique_provenance(provenance))


class B016_RedlichKisterExcessGibbs(ThermoTool):
    data_requirement = "FORMULA_ONLY"
    data_access_mode = "none"
    required_dataset_ids: list[str] = []
    database_tables: list[str] = []
    model_id, name, version = "B016", "Redlich-Kister超额Gibbs", "1.0.0"
    tool_name = "metallurgy_calculate_redlich_kister_activity"
    priority = "P1"
    source_version = "2026.09-p1-w6b"
    description = "由调用者提供的二元Redlich-Kister系数计算超额Gibbs能、偏摩尔超额量、活度系数和活度。"
    applicable_boundary = (
        "仅二元、单相、给定温度下的摩尔基模型；L0…Ln必须属于该二元系和温度，"
        "本工具不拟合、外推或内置合金参数。"
    )
    formula_reference = "G^E=x1*x2*sum_k L_k(x1-x2)^k; ln(gamma_i)=mu_i^E/(RT)"
    source_records = [{
        "source_id": "REDLICH-KISTER-1948",
        "name": "Algebraic representation of thermodynamic properties and classification of solutions",
        "version": "Ind. Eng. Chem. 40 (1948) 345-348",
        "url": "https://doi.org/10.1021/ie50458a036",
    }]
    data_source = ["Redlich-Kister公开公式；相互作用参数由调用者显式提供并标明来源"]
    required_data = ["二元摩尔组成", "评价温度", "适用于该体系和温度的L0…Ln"]
    failure_modes = [
        "组成不是二元或含负值", "参数数组为空或含非有限值", "参数来源/版本为空", "活度系数指数溢出",
    ]
    independent_validation = [
        "仅L0时严格退化为B015", "全部Lk为零时退化为B014", "sum(x_i*mu_i^E)=G^E",
        "解析组成导数与中心差分一致",
    ]
    dependencies = ["A004", "B014", "B015"]
    relations = [
        rel("depends_on", "A004", "二元组成先按同一规则归一化"),
        rel("generalizes", "B015", "B015是只有L0的对称正则溶液特例"),
        rel("overlaps", "B014", "Lk全零时活度严格退化为理想溶液"),
        rel("upstream_of", "B017", "可将Raoult标准态活度系数交给标准态切换工具"),
    ]
    input_fields = [
        InputField("compositions", "二元摩尔组成", "object", unit="1", description="恰好两个组元的非负数值"),
        InputField("temperature_k", "温度", "number", unit="K", min_value=1e-12),
        InputField(
            "interaction_parameters_j_mol", "Redlich-Kister系数", "array", unit="J/mol",
            items={"type": "number"}, min_items=1, max_items=8, description="依次为L0,L1,...",
        ),
        InputField("parameter_source", "相互作用参数来源", "string"),
        InputField("parameter_version", "参数版本", "string"),
    ]
    output_fields = [
        OutputField("component_order", "组元顺序", "array"),
        OutputField("normalized_compositions", "归一化组成", "object", "1"),
        OutputField("interaction_parameters_j_mol", "相互作用系数", "array", "J/mol"),
        OutputField("excess_gibbs_j_mol", "超额Gibbs能", "number", "J/mol"),
        OutputField("partial_molar_excess_gibbs_j_mol", "偏摩尔超额Gibbs能", "object", "J/mol"),
        OutputField("activity_coefficients", "活度系数", "object", "1"),
        OutputField("activities", "Raoult标准态活度", "object", "1"),
        OutputField("gibbs_duhem_closure_residual_j_mol", "偏摩尔闭合残差", "number", "J/mol"),
        OutputField("polynomial_order", "多项式阶数", "number", "1"),
        OutputField("temperature_k", "温度", "number", "K"),
        OutputField("parameter_source", "参数来源", "string"),
        OutputField("parameter_version", "参数版本", "string"),
        OutputField("standard_state", "标准态", "string"),
        OutputField("method", "方法", "string"),
    ]
    validation_rules = [
        {"rule": "exact_component_count", "value": 2},
        {"rule": "finite_array", "field": "interaction_parameters_j_mol"},
        {"rule": "nonempty", "fields": ["parameter_source", "parameter_version"]},
    ]
    _regular_case = {
        "compositions": {"A": 0.3, "B": 0.7},
        "temperature_k": 1000,
        "interaction_parameters_j_mol": [10000],
        "parameter_source": "P1-W6B regular-solution identity",
        "parameter_version": "v1",
    }
    qualification_cases = [
        {"id": "B016-N1", "kind": "normal", "input": _regular_case},
        {"id": "B016-N2", "kind": "normal", "input": {
            **_regular_case, "compositions": {"A": 0.4, "B": 0.6},
            "interaction_parameters_j_mol": [8000, -2000, 500],
        }},
        {"id": "B016-N3", "kind": "normal", "input": {
            **_regular_case, "interaction_parameters_j_mol": [0, 0],
        }},
        {"id": "B016-B1", "kind": "boundary", "input": {
            **_regular_case, "compositions": {"A": 1, "B": 0},
        }},
        {"id": "B016-F1", "kind": "failure", "input": {
            **_regular_case, "compositions": {"A": 0.3, "B": 0.3, "C": 0.4},
        }},
    ]

    def invoke(self, params, context=None):
        parsed, error = normalize_composition(params.get("compositions"))
        if error:
            return _fail(error)
        composition = parsed["normalized"]
        if len(composition) != 2:
            return _fail("Redlich-Kister首版仅接受两个组元")
        raw_parameters = params.get("interaction_parameters_j_mol")
        if not isinstance(raw_parameters, list) or not 1 <= len(raw_parameters) <= 8:
            return _fail("interaction_parameters_j_mol必须包含1至8个系数")
        try:
            parameters = [float(value) for value in raw_parameters]
        except (TypeError, ValueError):
            return _fail("Redlich-Kister系数必须全部为数值")
        if any(not math.isfinite(value) for value in parameters):
            return _fail("Redlich-Kister系数必须全部为有限值")
        source = str(params.get("parameter_source") or "").strip()
        version = str(params.get("parameter_version") or "").strip()
        if not source or not version:
            return _fail("必须提供非空parameter_source和parameter_version", "MISSING_DATA")
        temperature = float(params["temperature_k"])
        names = list(composition)
        x1 = float(composition[names[0]])
        x2 = float(composition[names[1]])
        difference = x1 - x2
        polynomial = sum(value * difference**order for order, value in enumerate(parameters))
        derivative_polynomial = sum(
            order * value * difference ** (order - 1)
            for order, value in enumerate(parameters) if order
        )
        excess = x1 * x2 * polynomial
        derivative = (x2 - x1) * polynomial + 2.0 * x1 * x2 * derivative_polynomial
        partial_1 = excess + x2 * derivative
        partial_2 = excess - x1 * derivative
        try:
            gamma_1 = math.exp(partial_1 / (R_J_MOL_K * temperature))
            gamma_2 = math.exp(partial_2 / (R_J_MOL_K * temperature))
        except OverflowError:
            return _fail("活度系数指数溢出", "NUMERICAL_ERROR")
        if not all(math.isfinite(value) for value in (gamma_1, gamma_2)):
            return _fail("活度系数计算产生非有限值", "NUMERICAL_ERROR")
        partials = {names[0]: partial_1, names[1]: partial_2}
        gammas = {names[0]: gamma_1, names[1]: gamma_2}
        activities = {name: composition[name] * gammas[name] for name in names}
        closure = x1 * partial_1 + x2 * partial_2 - excess
        at_endpoint = x1 == 0.0 or x2 == 0.0
        warnings = [] if not at_endpoint else [BoundaryWarning(
            "compositions", "纯组元端点可计算，但缺失组元活度为零且其有限浓度性质不应外推"
        )]
        return ModelResult(True, result={
            "component_order": names,
            "normalized_compositions": composition,
            "interaction_parameters_j_mol": parameters,
            "excess_gibbs_j_mol": excess,
            "partial_molar_excess_gibbs_j_mol": partials,
            "activity_coefficients": gammas,
            "activities": activities,
            "gibbs_duhem_closure_residual_j_mol": closure,
            "polynomial_order": len(parameters) - 1,
            "temperature_k": temperature,
            "parameter_source": source,
            "parameter_version": version,
            "standard_state": "Raoult pure-component standard state",
            "method": "binary Redlich-Kister excess-Gibbs polynomial / analytical partial molar derivative",
        }, boundary_check=BoundaryCheck(not at_endpoint, warnings))


class B017_HenryRaoultStandardState(ThermoTool):
    data_requirement = "FORMULA_ONLY"
    data_access_mode = "none"
    required_dataset_ids: list[str] = []
    database_tables: list[str] = []
    model_id, name, version = "B017", "Henry/Raoult标准态切换", "1.0.0"
    tool_name = "metallurgy_convert_henry_raoult_standard_state"
    priority = "P1"
    source_version = "2026.09-p1-w6b"
    description = "在Raoult纯组元标准态与Henry无限稀释标准态之间转换稀溶质活度、活度系数和标准化学势。"
    applicable_boundary = (
        "转换因子必须由调用者以无限稀释Raoult活度系数或同单位H/f*提供并标明来源；"
        "Henry结果建议仅用于x<=0.1的稀溶质，工具不拟合Henry常数。"
    )
    formula_reference = (
        "gamma_inf=H/f*; a_H=a_R/gamma_inf; gamma_H=gamma_R/gamma_inf; "
        "mu_H^0-mu_R^0=RT*ln(gamma_inf)"
    )
    source_records = [{
        "source_id": "IUPAC-HENRY-LAW",
        "name": "IUPAC Gold Book definition of Henry's law",
        "version": "Gold Book H02783",
        "url": "https://doi.org/10.1351/goldbook.H02783",
    }]
    data_source = ["IUPAC标准态定义；转换参数由调用者显式提供并标明来源"]
    required_data = ["溶质摩尔分数", "Raoult活度系数", "gamma_inf或H与纯组元逸度"]
    failure_modes = [
        "转换模式与参数不匹配", "转换因子非正或非有限", "H与纯组元逸度单位/数值无效",
        "参数来源或版本为空", "两条同时提供的转换路径不一致",
    ]
    independent_validation = [
        "Raoult到Henry再换回严格往返", "直接gamma_inf与H/f*路径一致", "两标准态总化学势相等",
    ]
    dependencies = ["B014", "B015", "B016"]
    relations = [
        rel("accepts_output_of", "B014", "理想Raoult活度可作为输入"),
        rel("accepts_output_of", "B015", "正则溶液Raoult活度系数可作为输入"),
        rel("accepts_output_of", "B016", "Redlich-Kister Raoult活度系数可作为输入"),
        rel("distinct_from", "B016", "本工具只变换标准态，不计算或拟合超额Gibbs模型"),
    ]
    input_fields = [
        InputField("solute", "稀溶质名称", "string"),
        InputField("solute_mole_fraction", "溶质摩尔分数", "number", unit="1", min_value=0, max_value=1),
        InputField("temperature_k", "温度", "number", unit="K", min_value=1e-12),
        InputField("raoult_activity_coefficient", "Raoult标准态活度系数", "number", unit="1", min_value=1e-300),
        InputField(
            "conversion_mode", "转换因子模式", "select",
            enum=["gamma_infinite", "henry_over_pure_fugacity"],
        ),
        InputField("gamma_infinite", "无限稀释Raoult活度系数", "number", required=False, unit="1", min_value=1e-300),
        InputField("henry_constant_pa", "Henry常数", "number", required=False, unit="Pa", min_value=1e-300),
        InputField("pure_component_fugacity_pa", "纯组元标准态逸度", "number", required=False, unit="Pa", min_value=1e-300),
        InputField("parameter_source", "转换参数来源", "string"),
        InputField("parameter_version", "参数版本", "string"),
    ]
    output_fields = [
        OutputField("solute", "稀溶质名称", "string"),
        OutputField("solute_mole_fraction", "溶质摩尔分数", "number", "1"),
        OutputField("gamma_infinite", "标准态转换因子", "number", "1"),
        OutputField("raoult_activity_coefficient", "Raoult活度系数", "number", "1"),
        OutputField("henry_activity_coefficient", "Henry活度系数", "number", "1"),
        OutputField("raoult_activity", "Raoult标准态活度", "number", "1"),
        OutputField("henry_activity", "Henry标准态活度", "number", "1"),
        OutputField("standard_chemical_potential_shift_kj_mol", "muH0-muR0", "number", "kJ/mol"),
        OutputField("chemical_potential_from_raoult_kj_mol", "相对muR0的Raoult路径化学势", "number", "kJ/mol", nullable=True),
        OutputField("chemical_potential_from_henry_kj_mol", "换算到muR0后的Henry路径化学势", "number", "kJ/mol", nullable=True),
        OutputField("chemical_potential_invariance_residual_kj_mol", "化学势不变残差", "number", "kJ/mol", nullable=True),
        OutputField("conversion_mode", "转换模式", "string"),
        OutputField("parameter_source", "参数来源", "string"),
        OutputField("parameter_version", "参数版本", "string"),
        OutputField("recommended_dilute_domain", "建议稀释域", "string"),
        OutputField("method", "方法", "string"),
    ]
    validation_rules = [
        {"rule": "conditional_required", "field": "conversion_mode"},
        {"rule": "positive", "field": "raoult_activity_coefficient"},
        {"rule": "nonempty", "fields": ["parameter_source", "parameter_version"]},
    ]
    _direct_case = {
        "solute": "C in liquid Fe",
        "solute_mole_fraction": 0.01,
        "temperature_k": 1873,
        "raoult_activity_coefficient": 20,
        "conversion_mode": "gamma_infinite",
        "gamma_infinite": 25,
        "parameter_source": "P1-W6B algebraic identity",
        "parameter_version": "v1",
    }
    qualification_cases = [
        {"id": "B017-N1", "kind": "normal", "input": _direct_case},
        {"id": "B017-N2", "kind": "normal", "input": {
            **_direct_case, "conversion_mode": "henry_over_pure_fugacity",
            "henry_constant_pa": 5e6, "pure_component_fugacity_pa": 2e5,
        }},
        {"id": "B017-N3", "kind": "normal", "input": {
            **_direct_case, "raoult_activity_coefficient": 25,
        }},
        {"id": "B017-B1", "kind": "boundary", "input": {
            **_direct_case, "solute_mole_fraction": 0.2,
        }},
        {"id": "B017-F1", "kind": "failure", "input": {
            **_direct_case, "conversion_mode": "henry_over_pure_fugacity",
            "henry_constant_pa": 5e6,
        }},
    ]

    def invoke(self, params, context=None):
        source = str(params.get("parameter_source") or "").strip()
        version = str(params.get("parameter_version") or "").strip()
        if not source or not version:
            return _fail("必须提供非空parameter_source和parameter_version", "MISSING_DATA")
        mode = params.get("conversion_mode")
        direct = params.get("gamma_infinite")
        henry = params.get("henry_constant_pa")
        fugacity = params.get("pure_component_fugacity_pa")
        try:
            if mode == "gamma_infinite":
                if direct is None:
                    return _fail("gamma_infinite模式必须提供gamma_infinite", "MISSING_DATA")
                factor = float(direct)
                if (henry is None) != (fugacity is None):
                    return _fail("若同时提供H/f*交叉检查，henry_constant_pa与pure_component_fugacity_pa必须成对出现")
                if henry is not None:
                    ratio = float(henry) / float(fugacity)
                    if not math.isclose(factor, ratio, rel_tol=1e-10, abs_tol=0.0):
                        return _fail("gamma_infinite与H/f*不一致", "DATA_VALIDATION_ERROR")
            elif mode == "henry_over_pure_fugacity":
                if henry is None or fugacity is None:
                    return _fail("henry_over_pure_fugacity模式必须同时提供Henry常数和纯组元逸度", "MISSING_DATA")
                factor = float(henry) / float(fugacity)
                if direct is not None and not math.isclose(float(direct), factor, rel_tol=1e-10, abs_tol=0.0):
                    return _fail("gamma_infinite与H/f*不一致", "DATA_VALIDATION_ERROR")
            else:
                return _fail("未知conversion_mode")
            mole_fraction = float(params["solute_mole_fraction"])
            temperature = float(params["temperature_k"])
            gamma_raoult = float(params["raoult_activity_coefficient"])
        except (TypeError, ValueError, ZeroDivisionError) as exc:
            return _fail(f"标准态转换参数无效: {exc}")
        if not math.isfinite(factor) or factor <= 0:
            return _fail("标准态转换因子必须为正有限值")
        gamma_henry = gamma_raoult / factor
        activity_raoult = mole_fraction * gamma_raoult
        activity_henry = activity_raoult / factor
        shift = R_J_MOL_K * temperature * math.log(factor) / 1000.0
        if mole_fraction == 0:
            mu_raoult = mu_henry = residual = None
        else:
            mu_raoult = R_J_MOL_K * temperature * math.log(activity_raoult) / 1000.0
            mu_henry = shift + R_J_MOL_K * temperature * math.log(activity_henry) / 1000.0
            residual = mu_henry - mu_raoult
        warnings: list[BoundaryWarning] = []
        if mole_fraction > 0.1:
            warnings.append(BoundaryWarning(
                "solute_mole_fraction", "x>0.1超出本工具建议的Henry稀溶质使用域；转换恒等式仍返回"
            ))
        if mole_fraction == 0:
            warnings.append(BoundaryWarning(
                "solute_mole_fraction", "x=0时两标准态化学势均趋于负无穷，以null返回"
            ))
        return ModelResult(True, result={
            "solute": params["solute"],
            "solute_mole_fraction": mole_fraction,
            "gamma_infinite": factor,
            "raoult_activity_coefficient": gamma_raoult,
            "henry_activity_coefficient": gamma_henry,
            "raoult_activity": activity_raoult,
            "henry_activity": activity_henry,
            "standard_chemical_potential_shift_kj_mol": shift,
            "chemical_potential_from_raoult_kj_mol": mu_raoult,
            "chemical_potential_from_henry_kj_mol": mu_henry,
            "chemical_potential_invariance_residual_kj_mol": residual,
            "conversion_mode": mode,
            "parameter_source": source,
            "parameter_version": version,
            "recommended_dilute_domain": "solute mole fraction x <= 0.1",
            "method": "Henry/Raoult standard-state thermodynamic identity",
        }, boundary_check=BoundaryCheck(not warnings, warnings))
