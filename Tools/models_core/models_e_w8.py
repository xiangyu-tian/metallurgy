"""P1-W8 blast-furnace hydrogen balance and reducing-gas utilization tools."""

from __future__ import annotations

import math
from typing import Optional

from .base import BaseModelTool, BoundaryCheck, BoundaryWarning, InputField, ModelResult, OutputField
from .models_a import parse_formula


SCENARIO = "高炉低碳"


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


HYDROGEN_STREAM_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "name": {"type": "string", "description": "流股唯一名称"},
        "species_kmol": {
            "type": "object",
            "additionalProperties": {"type": "number", "minimum": 0},
            "description": "中性化学式到物质量的映射；单位: kmol species/$basis",
        },
    },
    "required": ["name", "species_kmol"],
}


class E005_BFHydrogenBalance(BaseModelTool):
    model_id, name, version = "E005", "高炉氢平衡", "1.0.0"
    tool_name = "metallurgy_balance_bf_hydrogen"
    scenario, priority = SCENARIO, "P1"
    status = qualification_status = "qualified"
    count_eligible = True
    data_requirement, data_access_mode = "FORMULA_ONLY", "none"
    model_type = "确定性氢原子守恒"
    description = (
        "解析高炉输入/输出流股中的中性含氢物种，按氢原子kmol审计总平衡，"
        "并对指定炉顶气计算H2/H2O利用率。"
    )
    applicable_boundary = (
        "稳态统一统计基准；物种量必须为kmol，化学式限A002中性物种适用域。"
        "炉顶气利用率只使用指定输出流股的H2和H2O，不等同于全炉氢原子闭合率。"
    )
    formula_reference = (
        "n_H,stream=sum_j(n_j*nu_H,j); residual=sum(n_H,in)-sum(n_H,out); "
        "eta_H2=n_H2O/(n_H2+n_H2O)"
    )
    data_source = ["Conservation of hydrogen atoms", "IUPAC chemical-formula conventions", "ISIJ blast-furnace hydrogen utilization definition"]
    source_version = "bf-hydrogen-atom-balance-v1; A002-parser-2.0.0; ISIJINT-2021-574"
    source_records = [
        {"source_id": "H-ATOM-CONSERVATION", "name": "Conservation of hydrogen atoms", "version": "v1"},
        {"source_id": "IUPAC-RED-BOOK-2005", "name": "Nomenclature of Inorganic Chemistry", "version": "2005"},
        {"source_id": "ISIJINT-2021-574", "name": "Assessment of Blast Furnace Operational Constraints in the Presence of Hydrogen Injection", "version": "2022", "url": "https://doi.org/10.2355/isijinternational.ISIJINT-2021-574"},
    ]
    failure_modes = ["输入或输出流股为空、重名或结构非法", "化学式不能由A002解析", "物种kmol为负或非有限", "指定炉顶气不存在", "炉顶气H2与H2O分母为零"]
    independent_validation = ["H2/H2O/CH4分别含2/2/4个H原子", "输入输出逐物种H计量可独立复算", "流股拆分或合并不改变总残差", "炉顶气H2与H2O同比缩放不改变利用率"]
    dependencies = ["A002", "E001", "E003", "E004"]
    relations = [
        rel("depends_on", "A002", "复用唯一中性化学式解析器，不建立第二套物种语法"),
        rel("depends_on", "E001", "沿用高炉统一统计基准与物流边界"),
        rel("overlaps_with", "E003", "CH4等物种同时参与碳和氢平衡"),
        rel("overlaps_with", "E004", "H2O同时参与氧和氢平衡"),
        rel("overlaps_with", "E011", "两者均可给出H2/H2O利用率，但E005还要求全流程氢原子平衡"),
    ]
    input_fields = [
        InputField("basis", "统计基准", "select", enum=["per_hour", "per_day", "per_t_hot_metal"]),
        InputField("input_streams", "含氢输入流股", "array", items=HYDROGEN_STREAM_SCHEMA, min_items=1, max_items=200),
        InputField("output_streams", "含氢输出流股", "array", items=HYDROGEN_STREAM_SCHEMA, min_items=1, max_items=200),
        InputField("top_gas_stream_name", "炉顶气输出流股名称", "string"),
        InputField("absolute_tolerance_kmol_h", "氢原子绝对容差", "number", required=False, default=1e-9, unit="kmol H atoms/$basis", min_value=0),
        InputField("relative_tolerance", "相对容差", "number", required=False, default=1e-8, unit="1", min_value=0, max_value=1),
    ]
    output_fields = [
        OutputField("basis", "统计基准", "string"),
        OutputField("input_streams", "输入流股氢计量", "array", "species:kmol; hydrogen:kmol H atoms/$basis"),
        OutputField("output_streams", "输出流股氢计量", "array", "species:kmol; hydrogen:kmol H atoms/$basis"),
        OutputField("total_input_hydrogen_atom_kmol", "输入氢原子量", "number", "kmol H atoms/$basis"),
        OutputField("total_output_hydrogen_atom_kmol", "输出氢原子量", "number", "kmol H atoms/$basis"),
        OutputField("hydrogen_atom_residual_kmol", "氢原子残差", "number", "kmol H atoms/$basis"),
        OutputField("hydrogen_closure_rate", "氢闭合率", "number", "1"),
        OutputField("input_h2_equivalent_kmol", "输入H2当量", "number", "kmol H2-equivalent/$basis"),
        OutputField("output_h2_equivalent_kmol", "输出H2当量", "number", "kmol H2-equivalent/$basis"),
        OutputField("top_gas_h2_kmol", "炉顶气H2", "number", "kmol H2/$basis"),
        OutputField("top_gas_h2o_kmol", "炉顶气H2O", "number", "kmol H2O/$basis"),
        OutputField("top_gas_hydrogen_utilization_fraction", "炉顶气氢利用率", "number", "1"),
        OutputField("passed", "氢平衡是否闭合", "boolean"),
    ]
    validation_rules = [{"rule": "A002_parseable_neutral_species"}, {"rule": "common_kmol_and_time_basis"}, {"rule": "hydrogen_atom_conservation"}]
    qualification_cases = [
        {"id": "E005-N1", "kind": "normal", "input": {"basis": "per_hour", "input_streams": [{"name": "injection", "species_kmol": {"H2": 1}}], "output_streams": [{"name": "top_gas", "species_kmol": {"H2": 0.5, "H2O": 0.5}}], "top_gas_stream_name": "top_gas"}},
        {"id": "E005-N2", "kind": "normal", "input": {"basis": "per_day", "input_streams": [{"name": "fuel", "species_kmol": {"CH4": 1}}], "output_streams": [{"name": "top_gas", "species_kmol": {"H2": 2}}], "top_gas_stream_name": "top_gas"}},
        {"id": "E005-N3", "kind": "normal", "input": {"basis": "per_t_hot_metal", "input_streams": [{"name": "steam", "species_kmol": {"H2O": 1}}], "output_streams": [{"name": "top_gas", "species_kmol": {"H2O": 1}}], "top_gas_stream_name": "top_gas"}},
        {"id": "E005-B1", "kind": "boundary", "input": {"basis": "per_hour", "input_streams": [{"name": "injection", "species_kmol": {"H2": 1}}], "output_streams": [{"name": "top_gas", "species_kmol": {"H2": 0.5}}], "top_gas_stream_name": "top_gas"}},
        {"id": "E005-F1", "kind": "failure", "input": {"basis": "per_hour", "input_streams": [{"name": "bad", "species_kmol": {"XxH2": 1}}], "output_streams": [{"name": "top_gas", "species_kmol": {"H2": 1}}], "top_gas_stream_name": "top_gas"}},
    ]

    @staticmethod
    def _streams(raw, label):
        if not isinstance(raw, list) or not raw or len(raw) > 200:
            return None, f"{label}必须包含1到200条流股"
        parsed, names = [], set()
        for index, item in enumerate(raw):
            if not isinstance(item, dict) or set(item) != {"name", "species_kmol"}:
                return None, f"{label}[{index}]必须且只能包含name和species_kmol"
            name = item["name"]
            normalized_name = name.strip() if isinstance(name, str) else ""
            if not normalized_name or normalized_name in names:
                return None, f"{label}[{index}].name必须是唯一非空字符串"
            names.add(normalized_name)
            species = item["species_kmol"]
            if not isinstance(species, dict) or not species:
                return None, f"{label}[{index}].species_kmol必须是非空对象"
            species_result, stream_h = {}, 0.0
            for formula, raw_amount in species.items():
                if not isinstance(formula, str) or not formula.strip():
                    return None, f"{label}[{index}]物种名必须是非空化学式"
                elements, error = parse_formula(formula)
                if error:
                    return None, f"{label}[{index}].species_kmol.{formula}: {error}"
                h_count = float(elements.get("H", 0.0))
                if h_count <= 0:
                    return None, f"{label}[{index}].species_kmol.{formula}不是含氢物种"
                amount, error = finite(raw_amount, f"{label}[{index}].species_kmol.{formula}", minimum=0)
                if error:
                    return None, error
                hydrogen = amount * h_count
                species_result[formula] = {
                    "amount_kmol": amount, "hydrogen_atoms_per_molecule": h_count,
                    "hydrogen_atom_kmol": hydrogen,
                }
                stream_h += hydrogen
            parsed.append({"name": normalized_name, "species": species_result,
                           "hydrogen_atom_kmol": stream_h,
                           "h2_equivalent_kmol": stream_h / 2.0})
        return parsed, None

    def invoke(self, params, context=None):
        inputs, error = self._streams(params["input_streams"], "input_streams")
        if error: return fail(error)
        outputs, error = self._streams(params["output_streams"], "output_streams")
        if error: return fail(error)
        top_name = params["top_gas_stream_name"].strip()
        matches = [stream for stream in outputs if stream["name"] == top_name]
        if len(matches) != 1:
            return fail("top_gas_stream_name必须唯一匹配一条output_streams流股", "MISSING_DATA")
        top_species = matches[0]["species"]
        h2 = top_species.get("H2", {}).get("amount_kmol", 0.0)
        h2o = top_species.get("H2O", {}).get("amount_kmol", 0.0)
        if h2 + h2o <= 0:
            return fail("指定炉顶气流股的H2与H2O总量必须大于0", "DIVISION_BY_ZERO")
        total_in = math.fsum(stream["hydrogen_atom_kmol"] for stream in inputs)
        total_out = math.fsum(stream["hydrogen_atom_kmol"] for stream in outputs)
        residual = total_in - total_out
        absolute = float(params.get("absolute_tolerance_kmol_h", 1e-9))
        relative = float(params.get("relative_tolerance", 1e-8))
        tolerance = max(absolute, relative * max(total_in, total_out, 1.0))
        passed = abs(residual) <= tolerance
        closure = 1.0 - abs(residual) / max(total_in, total_out, 1.0)
        warnings = [] if passed else [BoundaryWarning("hydrogen_streams", "氢原子平衡未在声明容差内闭合")]
        return ModelResult(True, result={
            "basis": params["basis"], "input_streams": inputs, "output_streams": outputs,
            "total_input_hydrogen_atom_kmol": total_in,
            "total_output_hydrogen_atom_kmol": total_out,
            "hydrogen_atom_residual_kmol": residual, "hydrogen_closure_rate": closure,
            "input_h2_equivalent_kmol": total_in / 2.0,
            "output_h2_equivalent_kmol": total_out / 2.0,
            "top_gas_h2_kmol": h2, "top_gas_h2o_kmol": h2o,
            "top_gas_hydrogen_utilization_fraction": h2o / (h2 + h2o),
            "passed": passed,
        }, boundary_check=BoundaryCheck(passed, warnings))


GAS_SAMPLE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "time_s": {"type": "number", "minimum": 0, "description": "采样时间；单位: s"},
        "composition": {
            "type": "object",
            "additionalProperties": {"type": "number", "minimum": 0, "maximum": 1},
            "description": "CO/CO2/H2/H2O及可选N2/Ar/CH4/O2组成；单位: 1",
        },
    },
    "required": ["time_s", "composition"],
}


class E011_ReducingGasUtilization(BaseModelTool):
    model_id, name, version = "E011", "CO/CO2及H2/H2O利用率", "1.0.0"
    tool_name = "metallurgy_calculate_bf_reducing_gas_utilization"
    scenario, priority = SCENARIO, "P1"
    status = qualification_status = "qualified"
    count_eligible = True
    data_requirement, data_access_mode = "FORMULA_ONLY", "none"
    description = "由按时间递增的炉顶气摩尔/体积分数组成计算ηCO和ηH2，并返回首末变化与趋势。"
    applicable_boundary = "理想气体下摩尔分数与体积分数等价；样本必须采用同一干/湿基准，工具不执行干湿基换算或气体分析仪校准。"
    formula_reference = "eta_CO=x_CO2/(x_CO+x_CO2); eta_H2=x_H2O/(x_H2+x_H2O)"
    data_source = ["ISIJ blast-furnace reducing-gas utilization definitions"]
    source_version = "bf-reducing-gas-utilization-v1; ISIJINT-2021-574"
    source_records = [{"source_id": "ISIJINT-2021-574", "name": "Assessment of Blast Furnace Operational Constraints in the Presence of Hydrogen Injection", "version": "2022", "url": "https://doi.org/10.2355/isijinternational.ISIJINT-2021-574"}]
    failure_modes = ["样本为空、结构或组成非法", "时间不严格递增", "完整气体组成和不等于1", "所有样本的CO/CO2和H2/H2O分母均为零", "不同干湿基准混用"]
    independent_validation = ["ηCO和ηH2可逐样本手算", "相关气体组成同比缩放不改变利用率", "理想气体摩尔分数与体积分数得到相同结果", "首末变化等于最后值减第一有效值"]
    dependencies = ["E003", "E004", "E005"]
    relations = [
        rel("consumes_output_from", "E003", "E003炉顶气CO/CO2组成可作为E011样本"),
        rel("consumes_output_from", "E004", "E004炉顶气H2O组成可参与氢利用率"),
        rel("overlaps_with", "E005", "E011聚焦气体时序指标，E005聚焦全流程氢原子闭合"),
    ]
    input_fields = [
        InputField("composition_basis", "气体组成基准", "select", enum=["mole_fraction", "volume_fraction"]),
        InputField("composition_scope", "组成范围", "select", enum=["full_gas", "reactive_pair_subset"]),
        InputField("gas_samples", "炉顶气样本", "array", items=GAS_SAMPLE_SCHEMA, min_items=1, max_items=500),
        InputField("trend_tolerance", "趋势判定容差", "number", required=False, default=1e-6, unit="1", min_value=0, max_value=1),
    ]
    output_fields = [
        OutputField("composition_basis", "气体组成基准", "string"),
        OutputField("composition_scope", "组成范围", "string"),
        OutputField("sample_results", "逐样本利用率", "array", "time:s; utilization:1"),
        OutputField("latest_co_utilization_fraction", "最新CO利用率", "number", "1", nullable=True),
        OutputField("latest_h2_utilization_fraction", "最新H2利用率", "number", "1", nullable=True),
        OutputField("co_utilization_change", "CO利用率首末变化", "number", "1", nullable=True),
        OutputField("h2_utilization_change", "H2利用率首末变化", "number", "1", nullable=True),
        OutputField("co_trend", "CO利用率趋势", "string"),
        OutputField("h2_trend", "H2利用率趋势", "string"),
        OutputField("sample_count", "样本数", "number", "1"),
    ]
    validation_rules = [{"rule": "strictly_increasing_sample_time"}, {"rule": "common_dry_or_wet_basis"}, {"rule": "valid_reactive_pair_denominator"}]
    qualification_cases = [
        {"id": "E011-N1", "kind": "normal", "input": {"composition_basis": "mole_fraction", "composition_scope": "full_gas", "gas_samples": [{"time_s": 0, "composition": {"CO": 0.5, "CO2": 0.5}}]}},
        {"id": "E011-N2", "kind": "normal", "input": {"composition_basis": "volume_fraction", "composition_scope": "full_gas", "gas_samples": [{"time_s": 0, "composition": {"H2": 0.75, "H2O": 0.25}}]}},
        {"id": "E011-N3", "kind": "normal", "input": {"composition_basis": "mole_fraction", "composition_scope": "full_gas", "gas_samples": [{"time_s": 0, "composition": {"CO": 0.3, "CO2": 0.2, "H2": 0.1, "H2O": 0.1, "N2": 0.3}}, {"time_s": 60, "composition": {"CO": 0.2, "CO2": 0.3, "H2": 0.08, "H2O": 0.12, "N2": 0.3}}]}},
        {"id": "E011-B1", "kind": "boundary", "input": {"composition_basis": "mole_fraction", "composition_scope": "reactive_pair_subset", "gas_samples": [{"time_s": 0, "composition": {"CO": 0.2, "CO2": 0.1}}]}},
        {"id": "E011-F1", "kind": "failure", "input": {"composition_basis": "mole_fraction", "composition_scope": "full_gas", "gas_samples": [{"time_s": 1, "composition": {"CO": 0.5, "CO2": 0.5}}, {"time_s": 1, "composition": {"CO": 0.4, "CO2": 0.6}}]}},
    ]
    _ALLOWED_SPECIES = {"CO", "CO2", "H2", "H2O", "N2", "Ar", "CH4", "O2"}

    @staticmethod
    def _trend(values, tolerance):
        valid = [value for value in values if value is not None]
        if not valid: return None, "unavailable"
        if len(valid) == 1: return 0.0, "single_sample"
        change = valid[-1] - valid[0]
        if change > tolerance: return change, "increasing"
        if change < -tolerance: return change, "decreasing"
        return change, "steady"

    def invoke(self, params, context=None):
        raw = params["gas_samples"]
        if not isinstance(raw, list) or not raw or len(raw) > 500:
            return fail("gas_samples必须包含1到500个样本")
        scope = params["composition_scope"]
        results, previous_time, warnings = [], None, []
        any_metric = False
        for index, sample in enumerate(raw):
            if not isinstance(sample, dict) or set(sample) != {"time_s", "composition"}:
                return fail(f"gas_samples[{index}]必须且只能包含time_s和composition")
            time_s, error = finite(sample["time_s"], f"gas_samples[{index}].time_s", minimum=0)
            if error: return fail(error)
            if previous_time is not None and time_s <= previous_time:
                return fail("gas_samples.time_s必须严格递增")
            previous_time = time_s
            composition = sample["composition"]
            if not isinstance(composition, dict) or not composition:
                return fail(f"gas_samples[{index}].composition必须是非空对象")
            parsed = {}
            for species, raw_value in composition.items():
                if species not in self._ALLOWED_SPECIES:
                    return fail(f"gas_samples[{index}]包含未支持气体{species}", "MODEL_NOT_APPLICABLE")
                value, error = finite(raw_value, f"gas_samples[{index}].composition.{species}", minimum=0, maximum=1)
                if error: return fail(error)
                parsed[species] = value
            total = math.fsum(parsed.values())
            if scope == "full_gas" and not math.isclose(total, 1.0, rel_tol=0.0, abs_tol=1e-9):
                return fail(f"gas_samples[{index}]完整组成分数和必须为1")
            if scope == "reactive_pair_subset" and total > 1.0 + 1e-9:
                return fail(f"gas_samples[{index}]子集组成分数和不能超过1")
            co_den = parsed.get("CO", 0.0) + parsed.get("CO2", 0.0)
            h_den = parsed.get("H2", 0.0) + parsed.get("H2O", 0.0)
            eta_co = parsed.get("CO2", 0.0) / co_den if co_den > 0 else None
            eta_h = parsed.get("H2O", 0.0) / h_den if h_den > 0 else None
            any_metric = any_metric or eta_co is not None or eta_h is not None
            if eta_co is None or eta_h is None:
                warnings.append(BoundaryWarning("gas_samples", f"样本{index}至少一个反应气体对不可用"))
            results.append({"time_s": time_s, "composition": parsed, "composition_sum": total,
                            "co_utilization_fraction": eta_co,
                            "h2_utilization_fraction": eta_h})
        if not any_metric:
            return fail("所有样本的CO/CO2和H2/H2O分母均为零", "DIVISION_BY_ZERO")
        tolerance = float(params.get("trend_tolerance", 1e-6))
        co_values = [row["co_utilization_fraction"] for row in results]
        h_values = [row["h2_utilization_fraction"] for row in results]
        co_change, co_trend = self._trend(co_values, tolerance)
        h_change, h_trend = self._trend(h_values, tolerance)
        if len(results) == 1:
            warnings.append(BoundaryWarning("gas_samples", "单样本只能计算利用率，不能判断时序趋势"))
        latest_co = next((value for value in reversed(co_values) if value is not None), None)
        latest_h = next((value for value in reversed(h_values) if value is not None), None)
        return ModelResult(True, result={
            "composition_basis": params["composition_basis"], "composition_scope": scope,
            "sample_results": results, "latest_co_utilization_fraction": latest_co,
            "latest_h2_utilization_fraction": latest_h, "co_utilization_change": co_change,
            "h2_utilization_change": h_change, "co_trend": co_trend, "h2_trend": h_trend,
            "sample_count": len(results),
        }, boundary_check=BoundaryCheck(not warnings, warnings))
