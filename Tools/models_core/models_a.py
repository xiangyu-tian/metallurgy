"""A-series deterministic chemistry, stoichiometry and validation tools."""
from __future__ import annotations

import math
import re
from typing import Dict, List, Optional, Tuple

import numpy as np

from .base import BaseModelTool, BoundaryCheck, BoundaryWarning, InputField, InvocationContext, ModelResult, OutputField
from .chemical_data import ELEMENT_ATOMIC_WEIGHTS
from .repositories.reference_repository import RepositoryError, atomic_weights


SCENARIO = "通用数据与校验"


def _relation(relation_type: str, target: str, description: str) -> dict:
    return {"type": relation_type, "target": target, "description": description}


class A001_UnitConversion(BaseModelTool):
    model_id, name, scenario, priority = "A001", "单位换算", SCENARIO, "P0"
    version, status, qualification_status, count_eligible = "2.0.0", "qualified", "qualified", True
    description = "在相同物理量纲之间执行线性或带偏移的单位换算。"
    applicable_boundary = "仅支持内置单位表；严格模式拒绝未知单位和量纲不一致。"
    data_source = ["BIPM SI Brochure 9th edition", "NIST SP 811 (2008)"]
    source_version = "SI Brochure 9th ed. v3.01 (2025); NIST SP 811 (2008)"
    formula_reference = "x_SI = x*scale+offset; y = (x_SI-target_offset)/target_scale"
    source_records = [
        {"source_id": "BIPM-SI-9", "name": "BIPM SI Brochure", "version": "9th ed. v3.01"},
        {"source_id": "NIST-SP-811", "name": "Guide for the Use of the SI", "version": "2008"},
    ]
    failure_modes = ["源或目标单位未知", "量纲不一致", "输入不是有限数值"]
    independent_validation = ["往返换算恢复原值", "SI比例换算满足乘法传递性"]
    dependencies = []
    relations = [_relation("upstream_of", "A005", "为质量衡算提供质量单位契约"), _relation("complements", "A004", "分别处理量纲与无量纲比例")]
    input_fields = [
        InputField("value", "数值", "number", unit="$source_unit", description="有限的待换算数值"),
        InputField("source_unit", "源单位", "string", placeholder="如 °C, kg, MPa", description="内置单位符号或别名"),
        InputField("target_unit", "目标单位", "string", placeholder="如 K, g, psi", description="与源单位同量纲的单位"),
    ]
    output_fields = [
        OutputField("value", "换算值", "number", "$target_unit", "目标单位下的数值"),
        OutputField("source_unit", "规范化源单位", "string", description="解析后的源单位符号"),
        OutputField("target_unit", "规范化目标单位", "string", description="解析后的目标单位符号"),
        OutputField("conversion_factor", "比例换算因子", "number", "1", "不含偏移的scale比值"),
        OutputField("category", "物理量类别", "string", description="单位类别"),
        OutputField("dimension", "量纲", "string", description="SI基本量纲表示"),
    ]
    validation_rules = [{"rule": "finite", "field": "value"}, {"rule": "same_dimension", "fields": ["source_unit", "target_unit"]}]
    qualification_cases = [
        {"id": "A001-N1", "kind": "normal", "input": {"value": 1, "source_unit": "kg", "target_unit": "g"}},
        {"id": "A001-N2", "kind": "normal", "input": {"value": 100, "source_unit": "°C", "target_unit": "K"}},
        {"id": "A001-N3", "kind": "normal", "input": {"value": 1, "source_unit": "MPa", "target_unit": "Pa"}},
        {"id": "A001-F1", "kind": "failure", "input": {"value": 1, "source_unit": "unknown", "target_unit": "kg"}},
        {"id": "A001-F2", "kind": "failure", "input": {"value": 1, "source_unit": "kg", "target_unit": "m"}},
    ]

    def invoke(self, params: dict, context: Optional[InvocationContext] = None) -> ModelResult:
        try:
            from a001_unit_conversion import convert_units
        except ImportError:
            from ..a001_unit_conversion import convert_units
        converted = convert_units(float(params["value"]), params["source_unit"], params["target_unit"], strict=True)
        if not converted.success:
            return ModelResult(False, error=converted.error, error_code="UNIT_MISMATCH")
        warnings = [BoundaryWarning(field=getattr(w, "field", "value"), message=getattr(w, "message", str(w)), level=getattr(w, "level", "warning"), min_allowed=getattr(w, "min_allowed", None), max_allowed=getattr(w, "max_allowed", None)) for w in converted.warnings]
        if any(w.level == "error" for w in warnings):
            return ModelResult(False, error="; ".join(w.message for w in warnings), error_code="UNIT_MISMATCH")
        return ModelResult(True, result={"value": converted.value, "source_unit": converted.source_unit, "target_unit": converted.target_unit, "conversion_factor": converted.conversion_factor, "category": converted.category, "dimension": converted.dimension}, boundary_check=BoundaryCheck(True, warnings))


_SUBSCRIPTS = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")
_OPEN_TO_CLOSE = {"(": ")", "[": "]", "{": "}"}
_CLOSE = set(_OPEN_TO_CLOSE.values())
_PHASE_RE = re.compile(r"\((aq|s|l|g)\)$", re.IGNORECASE)
_NUMBER_RE = re.compile(r"(?:\d+(?:\.\d*)?|\.\d+)")


def _read_number(text: str, index: int) -> Tuple[float, int]:
    match = _NUMBER_RE.match(text, index)
    if not match:
        return 1.0, index
    value = float(match.group(0))
    if not math.isfinite(value) or value <= 0:
        raise ValueError("化学计量数必须为正有限数值")
    return value, match.end()


def _merge_counts(target: Dict[str, float], source: Dict[str, float], multiplier: float = 1.0) -> None:
    for element, count in source.items():
        target[element] = target.get(element, 0.0) + count * multiplier


def _parse_sequence(text: str, index: int = 0, expected_close: Optional[str] = None) -> Tuple[Dict[str, float], int]:
    counts: Dict[str, float] = {}
    while index < len(text):
        char = text[index]
        if char in _CLOSE:
            if char != expected_close:
                raise ValueError(f"括号不匹配: 收到 '{char}'")
            return counts, index + 1
        if char in _OPEN_TO_CLOSE:
            inner, index = _parse_sequence(text, index + 1, _OPEN_TO_CLOSE[char])
            multiplier, index = _read_number(text, index)
            _merge_counts(counts, inner, multiplier)
            continue
        if not char.isupper() or not char.isascii():
            raise ValueError(f"无法解析字符 '{char}'（位置 {index}）")
        end = index + 1
        if end < len(text) and text[end].islower() and text[end].isascii():
            end += 1
        element = text[index:end]
        if element not in ELEMENT_ATOMIC_WEIGHTS:
            raise ValueError(f"未知元素: {element}")
        multiplier, index = _read_number(text, end)
        counts[element] = counts.get(element, 0.0) + multiplier
    if expected_close is not None:
        raise ValueError(f"括号不匹配: 缺少 '{expected_close}'")
    return counts, index


def parse_formula_details(formula: str) -> Tuple[Optional[dict], Optional[str]]:
    """Fully parse a neutral formula, including hydrates and phase suffixes."""
    if not isinstance(formula, str) or not formula.strip():
        return None, "化学式为空"
    display = formula.strip()
    normalized = re.sub(r"\s+", "", display.translate(_SUBSCRIPTS))
    phase = None
    phase_match = _PHASE_RE.search(normalized)
    if phase_match:
        phase = phase_match.group(1).lower()
        normalized = normalized[:phase_match.start()]
    total: Dict[str, float] = {}
    try:
        for segment_index, segment in enumerate(normalized.split("·")):
            if not segment:
                raise ValueError("水合点两侧必须有化学式")
            coefficient = 1.0
            if segment_index:
                coefficient, start = _read_number(segment, 0)
                if start:
                    segment = segment[start:]
            elif _NUMBER_RE.match(segment):
                raise ValueError("单个化学式不能带前置反应系数")
            counts, end = _parse_sequence(segment)
            if end != len(segment) or not counts:
                raise ValueError("化学式未被完整解析")
            _merge_counts(total, counts, coefficient)
    except ValueError as exc:
        return None, str(exc)
    return {"elements": total, "formula_display": display, "normalized_formula": normalized, "phase": phase}, None


def parse_formula(formula: str) -> Tuple[Optional[Dict[str, float]], Optional[str]]:
    details, error = parse_formula_details(formula)
    return (details["elements"] if details else None), error


def calc_molar_mass_from_elements(elements: Dict[str, float]) -> float:
    return sum(count * ELEMENT_ATOMIC_WEIGHTS[element] for element, count in elements.items())


class A002_ChemicalFormulaParser(BaseModelTool):
    model_id, name, scenario, priority = "A002", "化学式解析", SCENARIO, "P0"
    version, status, qualification_status, count_eligible = "2.0.0", "qualified", "qualified", True
    description = "把中性化学式完整解析为元素化学计量组成，不计算摩尔质量。"
    applicable_boundary = "支持嵌套括号、水合点、Unicode下标和相态；不支持同位素与离子电荷。"
    data_source, source_version = ["IUPAC Red Book chemical formula conventions"], "IUPAC Recommendations 2005"
    formula_reference = "递归下降语法：formula := (element|group)+"
    source_records = [{"source_id": "IUPAC-RED-BOOK-2005", "name": "Nomenclature of Inorganic Chemistry", "version": "2005"}]
    failure_modes = ["未知元素", "非法字符或未完整消费", "括号不匹配", "离子/同位素超适用域"]
    independent_validation = ["总原子数等于各元素计量数之和", "括号展开与直接计数等价"]
    dependencies = []
    relations = [_relation("upstream_of", "A003", "元素计量数供摩尔质量加权求和"), _relation("upstream_of", "A006", "元素计量数供反应守恒校验")]
    input_fields = [InputField("formula", "化学式", "string", placeholder="如 Fe2(SO4)3", description="单个中性物种化学式")]
    output_fields = [
        OutputField("elements", "元素组成", "object", description="元素到计量数映射"), OutputField("element_count", "元素种类数", "number", "1", "不同元素数量"),
        OutputField("total_atoms", "原子总数", "number", "1", "所有元素计量数之和"), OutputField("formula_display", "原始显示式", "string", description="原始输入式"),
        OutputField("phase", "相态", "string", description="s/l/g/aq或空"), OutputField("is_stoichiometric", "是否整数计量", "boolean", description="计量数是否全为整数"),
    ]
    validation_rules = [{"rule": "full_string_parse", "field": "formula"}, {"rule": "known_elements_only", "field": "formula"}]
    qualification_cases = [
        {"id": "A002-N1", "kind": "normal", "input": {"formula": "Fe2O3"}}, {"id": "A002-N2", "kind": "normal", "input": {"formula": "Fe2(SO4)3"}},
        {"id": "A002-N3", "kind": "normal", "input": {"formula": "CuSO4·5H2O"}}, {"id": "A002-F1", "kind": "failure", "input": {"formula": "Fe2O3xyz"}},
        {"id": "A002-F2", "kind": "failure", "input": {"formula": "Mg(OH]2"}},
    ]

    def invoke(self, params: dict, context: Optional[InvocationContext] = None) -> ModelResult:
        details, error = parse_formula_details(params["formula"])
        if error:
            return ModelResult(False, error=error, error_code="INVALID_INPUT")
        elements = details["elements"]
        return ModelResult(True, result={"elements": elements, "element_count": len(elements), "total_atoms": sum(elements.values()), "formula_display": details["formula_display"], "phase": details["phase"] or "", "is_stoichiometric": all(float(v).is_integer() for v in elements.values())})


class A003_MolarMassCalculator(BaseModelTool):
    model_id, name, scenario, priority = "A003", "摩尔质量计算", SCENARIO, "P0"
    version, status, qualification_status, count_eligible = "2.0.0", "qualified", "qualified", True
    data_requirement = "REFERENCE_DATA_REQUIRED"
    data_access_mode = "database_repository"
    required_dataset_ids = ["DS_IUPAC_AW_2021"]
    database_tables = ["metallurgy_v2.element_reference"]
    description = "基于A002解析结果和固定原子量表计算摩尔质量。"
    applicable_boundary = "适用于A002可解析且原子量表覆盖的中性化学式；自然同位素组成。"
    data_source, source_version = ["IUPAC/CIAAW standard atomic weights 2021"], "IUPAC atomic weights 2021 repository snapshot"
    formula_reference = "M = sum(n_i*A_r,i)"
    source_records = [{"source_id": "IUPAC-AW-2021", "name": "IUPAC standard atomic weights", "version": "2021 snapshot"}]
    failure_modes = ["化学式语法错误", "元素不在原子量表", "离子或同位素超适用域"]
    independent_validation = ["逐元素原子量加权和", "g/mol与kg/kmol数值恒等"]
    dependencies = ["A002"]
    relations = [_relation("depends_on", "A002", "复用完整化学式解析"), _relation("feeds", "A007", "相同版本原子量用于元素kmol换算")]
    input_fields = [InputField("formula", "化学式", "string", placeholder="如 Fe2O3", description="A002适用域内的中性化学式")]
    output_fields = [OutputField("molar_mass_g_per_mol", "摩尔质量", "number", "g/mol", "每摩尔质量"), OutputField("molar_mass_kg_per_kmol", "千摩尔质量", "number", "kg/kmol", "每千摩尔质量"), OutputField("molar_mass", "兼容摩尔质量", "number", "g/mol", "旧协议兼容字段，与molar_mass_g_per_mol相同"), OutputField("formula", "化学式", "string", description="输入化学式"), OutputField("elements", "元素组成", "object", description="加权求和的元素计量数")]
    validation_rules = [{"rule": "A002_parseable", "field": "formula"}]
    qualification_cases = [
        {"id": "A003-N1", "kind": "normal", "input": {"formula": "H2O"}}, {"id": "A003-N2", "kind": "normal", "input": {"formula": "Fe2O3"}},
        {"id": "A003-N3", "kind": "normal", "input": {"formula": "CaCO3"}}, {"id": "A003-F1", "kind": "failure", "input": {"formula": "Xx2O"}},
        {"id": "A003-F2", "kind": "failure", "input": {"formula": "Fe2(O3"}},
    ]
    data_qualification_cases = [{"id": "A003-D1", "input": {"formula": "Fe2O3"}}]

    def invoke(self, params: dict, context: Optional[InvocationContext] = None) -> ModelResult:
        elements, error = parse_formula(params["formula"])
        if error:
            return ModelResult(False, error=error, error_code="INVALID_INPUT")
        try:
            weights, provenance = atomic_weights(elements)
        except RepositoryError as exc:
            return ModelResult(False, error=str(exc), error_code=exc.error_code)
        mass = math.fsum(count * weights[element] for element, count in elements.items())
        return ModelResult(True, result={"molar_mass_g_per_mol": mass, "molar_mass_kg_per_kmol": mass, "molar_mass": mass, "formula": params["formula"].strip(), "elements": elements}, provenance=provenance)


_BASIS_SUM = {"fraction": 1.0, "percent": 100.0, "ppm": 1_000_000.0, "arbitrary": None}


def normalize_composition(compositions: dict) -> Tuple[Optional[dict], Optional[str]]:
    if not isinstance(compositions, dict) or not compositions:
        return None, "组成必须是非空对象"
    converted = {}
    for component, raw in compositions.items():
        if not isinstance(component, str) or not component.strip() or isinstance(raw, bool):
            return None, "组分名称必须非空且数值有效"
        try:
            value = float(raw)
        except (TypeError, ValueError):
            return None, f"组分 {component} 必须是数值"
        if not math.isfinite(value) or value < 0:
            return None, f"组分 {component} 必须是非负有限数值"
        converted[component] = value
    total = math.fsum(converted.values())
    if total <= 0:
        return None, "组成总和必须大于0"
    normalized = {k: v / total for k, v in converted.items()}
    largest = max(normalized, key=normalized.get)
    normalized[largest] += 1.0 - math.fsum(normalized.values())
    return {"values": converted, "total": total, "normalized": normalized}, None


class A004_CompositionNormalizer(BaseModelTool):
    model_id, name, scenario, priority = "A004", "成分归一化", SCENARIO, "P0"
    version, status, qualification_status, count_eligible = "2.0.0", "qualified", "qualified", True
    description = "把非负组分按总和归一化，并检查fraction/percent/ppm声明基准。"
    applicable_boundary = "输入必须为非负有限数，且至少一项大于零；不判断质量/摩尔基准。"
    data_source, source_version = ["Deterministic normalization identity"], "formula-v1"
    formula_reference = "x_i,norm=x_i/sum_j(x_j)"
    source_records = [{"source_id": "MATH-NORMALIZATION", "name": "Deterministic normalization identity", "version": "1"}]
    failure_modes = ["空组成", "负值或非有限值", "总和为零", "未知输入基准"]
    independent_validation = ["输出和为1", "正比例缩放不变性", "幂等性"]
    dependencies = []
    relations = [_relation("upstream_of", "A005", "归一化完整组成可作为物流质量分数"), _relation("upstream_of", "A007", "归一化元素组成用于当量计算")]
    input_fields = [InputField("compositions", "组成", "object", unit="1", description="组分到非负数值映射"), InputField("input_basis", "输入基准", "select", False, "arbitrary", enum=list(_BASIS_SUM), description="fraction/percent/ppm/arbitrary"), InputField("tolerance", "基准总和容差", "number", False, 0.001, "1", 0, description="声明基准比较容差")]
    output_fields = [OutputField("normalized", "归一化组成", "object", description="总和为1的组成"), OutputField("sum_before", "归一化前总和", "number", "1", "输入总和"), OutputField("sum_after", "归一化后总和", "number", "1", "输出总和"), OutputField("expected_sum", "基准期望总和", "number", "1", "arbitrary用0表示"), OutputField("normalization_required", "是否调整", "boolean", description="原始总和是否不为1"), OutputField("input_basis", "输入基准", "string", description="采用基准"), OutputField("passed", "是否符合声明基准", "boolean", description="arbitrary总是通过")]
    validation_rules = [{"rule": "nonnegative_finite", "field": "compositions"}, {"rule": "positive_sum", "field": "compositions"}]
    qualification_cases = [
        {"id": "A004-N1", "kind": "normal", "input": {"compositions": {"Fe": .9, "C": .1}, "input_basis": "fraction"}}, {"id": "A004-N2", "kind": "normal", "input": {"compositions": {"Fe": 90, "C": 10}, "input_basis": "percent"}},
        {"id": "A004-N3", "kind": "normal", "input": {"compositions": {"Fe": 900000, "C": 100000}, "input_basis": "ppm"}}, {"id": "A004-F1", "kind": "failure", "input": {"compositions": {"Fe": 1.1, "C": -.1}}}, {"id": "A004-F2", "kind": "failure", "input": {"compositions": {"Fe": 0, "C": 0}}},
    ]

    def invoke(self, params: dict, context: Optional[InvocationContext] = None) -> ModelResult:
        parsed, error = normalize_composition(params["compositions"])
        if error:
            return ModelResult(False, error=error, error_code="INVALID_INPUT")
        basis, tolerance = params.get("input_basis", "arbitrary"), float(params.get("tolerance", .001))
        expected = _BASIS_SUM[basis]
        passed = expected is None or abs(parsed["total"] - expected) <= tolerance
        warnings = [] if passed else [BoundaryWarning("compositions", f"原始总和{parsed['total']}偏离{basis}基准{expected}")]
        return ModelResult(True, result={"normalized": parsed["normalized"], "sum_before": parsed["total"], "sum_after": math.fsum(parsed["normalized"].values()), "expected_sum": expected if expected is not None else 0.0, "normalization_required": not math.isclose(parsed["total"], 1.0, rel_tol=0, abs_tol=1e-15), "input_basis": basis, "passed": passed}, boundary_check=BoundaryCheck(passed, warnings))


def _validate_streams(streams: object, side: str) -> Tuple[Optional[List[dict]], Optional[str]]:
    if not isinstance(streams, list) or not streams:
        return None, f"{side}物流必须是非空数组"
    valid = []
    for i, stream in enumerate(streams):
        if not isinstance(stream, dict):
            return None, f"{side}物流[{i}]必须是对象"
        try:
            mass = float(stream.get("mass"))
        except (TypeError, ValueError):
            return None, f"{side}物流[{i}].mass必须是数值"
        if not math.isfinite(mass) or mass <= 0:
            return None, f"{side}物流[{i}].mass必须大于0且有限"
        elements = stream.get("elements")
        if not isinstance(elements, dict) or not elements:
            return None, f"{side}物流[{i}].elements必须是非空对象"
        fractions = {}
        for element, raw in elements.items():
            if element not in ELEMENT_ATOMIC_WEIGHTS:
                return None, f"{side}物流[{i}]含未知元素{element}"
            try:
                fraction = float(raw)
            except (TypeError, ValueError):
                return None, f"{element}分数必须是数值"
            if not math.isfinite(fraction) or not 0 <= fraction <= 1:
                return None, f"{element}分数必须在[0,1]"
            fractions[element] = fraction
        if math.fsum(fractions.values()) > 1 + 1e-12:
            return None, f"{side}物流[{i}]元素质量分数总和不能超过1"
        valid.append({"name": str(stream.get("name", f"{side}-{i+1}")), "mass": mass, "elements": fractions})
    return valid, None


class A005_MassBalanceChecker(BaseModelTool):
    model_id, name, scenario, priority = "A005", "元素质量守恒校验", SCENARIO, "P0"
    version, status, qualification_status, count_eligible = "2.0.0", "qualified", "qualified", True
    description = "计算输入输出物流总质量和逐元素残差，以绝对或相对容差判定闭合。"
    applicable_boundary = "正质量物流；元素质量分数在[0,1]且单流已列元素总和不超过1；质量单位一致。"
    data_source, source_version = ["Steady-state total and elemental mass conservation"], "mass-balance-contract-v2"
    formula_reference = "r_i=sum_in(mw_i)-sum_out(mw_i); closure=1-|r|/max(in,out)"
    source_records = [{"source_id": "MASS-CONSERVATION", "name": "Total and elemental mass conservation", "version": "v2"}]
    failure_modes = ["物流为空或结构错误", "质量非正或非有限", "质量分数越界或和超过1", "未知元素"]
    independent_validation = ["残差等于输入元素质量减输出元素质量", "物流拆分合并不改变结果"]
    dependencies = []
    relations = [_relation("accepts_output_of", "A004", "完整组成可先归一化"), _relation("uses_unit_contract_of", "A001", "物流质量应先换算到同一单位")]
    input_fields = [InputField("input_streams", "输入物流", "array", items={"type": "object"}, description="含mass与elements的数组"), InputField("output_streams", "输出物流", "array", items={"type": "object"}, description="含mass与elements的数组"), InputField("mass_unit", "质量单位", "select", False, "kg", enum=["kg", "g", "t"], description="所有物流共同单位"), InputField("absolute_tolerance", "绝对容差", "number", False, .001, "$mass_unit", 0, description="质量残差绝对容差"), InputField("relative_tolerance", "相对容差", "number", False, 1e-6, "1", 0, 1, description="质量残差相对容差")]
    output_fields = [OutputField("element_balances", "逐元素平衡", "object", description="输入输出残差和闭合率"), OutputField("total_input_mass", "总输入质量", "number", "$mass_unit", "输入质量和"), OutputField("total_output_mass", "总输出质量", "number", "$mass_unit", "输出质量和"), OutputField("mass_residual", "总质量残差", "number", "$mass_unit", "输入减输出"), OutputField("mass_closure_rate", "总质量闭合率", "number", "1", "闭合率"), OutputField("max_element_residual", "最大元素残差", "number", "$mass_unit", "最大绝对残差"), OutputField("passed", "是否闭合", "boolean", description="总质量和元素均满足容差"), OutputField("mass_unit", "质量单位", "string", description="输出单位")]
    validation_rules = [{"rule": "positive_finite", "field": "*.mass"}, {"rule": "fraction_range", "field": "*.elements.*"}]
    qualification_cases = [
        {"id": "A005-N1", "kind": "normal", "input": {"input_streams": [{"mass": 10, "elements": {"Fe": 1}}], "output_streams": [{"mass": 10, "elements": {"Fe": 1}}]}},
        {"id": "A005-N2", "kind": "normal", "input": {"input_streams": [{"mass": 6, "elements": {"Fe": 1}}, {"mass": 4, "elements": {"C": 1}}], "output_streams": [{"mass": 10, "elements": {"Fe": .6, "C": .4}}]}},
        {"id": "A005-N3", "kind": "normal", "input": {"input_streams": [{"mass": 1000, "elements": {"Fe": 1}}], "output_streams": [{"mass": 999.9995, "elements": {"Fe": 1}}], "absolute_tolerance": .001}},
        {"id": "A005-B1", "kind": "boundary", "input": {"input_streams": [{"mass": 10, "elements": {"Fe": 1}}], "output_streams": [{"mass": 9, "elements": {"Fe": 1}}]}},
        {"id": "A005-F1", "kind": "failure", "input": {"input_streams": [{"mass": -10, "elements": {"Fe": 1}}], "output_streams": [{"mass": 10, "elements": {"Fe": 1}}]}},
    ]

    @staticmethod
    def _within(residual, reference, absolute, relative):
        return abs(residual) <= absolute or abs(residual) / max(reference, 1e-30) <= relative

    def invoke(self, params: dict, context: Optional[InvocationContext] = None) -> ModelResult:
        inputs, error = _validate_streams(params["input_streams"], "输入")
        if error:
            return ModelResult(False, error=error, error_code="INVALID_INPUT")
        outputs, error = _validate_streams(params["output_streams"], "输出")
        if error:
            return ModelResult(False, error=error, error_code="INVALID_INPUT")
        absolute, relative = float(params.get("absolute_tolerance", .001)), float(params.get("relative_tolerance", 1e-6))
        ins: Dict[str, float] = {}; outs: Dict[str, float] = {}
        for stream, target in [(s, ins) for s in inputs] + [(s, outs) for s in outputs]:
            for element, fraction in stream["elements"].items(): target[element] = target.get(element, 0) + stream["mass"] * fraction
        balances, elements_ok, max_residual = {}, True, 0.0
        for element in sorted(set(ins) | set(outs)):
            incoming, outgoing = ins.get(element, 0.0), outs.get(element, 0.0)
            residual, reference = incoming - outgoing, max(abs(incoming), abs(outgoing))
            rel = abs(residual) / max(reference, 1e-30); ok = self._within(residual, reference, absolute, relative)
            elements_ok &= ok; max_residual = max(max_residual, abs(residual))
            balances[element] = {"input_mass": incoming, "output_mass": outgoing, "residual": residual, "relative_residual": rel, "closure_rate": 1-rel, "passed": ok}
        total_in, total_out = math.fsum(s["mass"] for s in inputs), math.fsum(s["mass"] for s in outputs)
        residual = total_in-total_out; rel = abs(residual)/max(total_in, total_out); passed = elements_ok and self._within(residual, max(total_in,total_out), absolute, relative)
        warnings = [] if passed else [BoundaryWarning("mass_balance", f"总质量残差={residual:g}，最大元素残差={max_residual:g}")]
        return ModelResult(True, result={"element_balances": balances, "total_input_mass": total_in, "total_output_mass": total_out, "mass_residual": residual, "mass_closure_rate": 1-rel, "max_element_residual": max_residual, "passed": passed, "mass_unit": params.get("mass_unit", "kg")}, boundary_check=BoundaryCheck(passed, warnings))


_ARROW_RE = re.compile(r"<=>|⇌|→|->|=>|=")
_CHARGE_RE = re.compile(r"(?:\be\s*[+-]|[A-Za-z0-9\]\)][+-](?=\s|$))")
_SPECIES_RE = re.compile(r"^\s*(?:(\d+(?:\.\d+)?)\s*)?(.+?)\s*$")


def _parse_reaction_side(side: str):
    parsed = []
    for token in side.split("+"):
        match = _SPECIES_RE.match(token)
        if not token.strip() or not match:
            return None, "反应式含空物种或非法物种"
        coefficient, formula = float(match.group(1) or 1), match.group(2).strip()
        if coefficient <= 0:
            return None, "反应系数必须大于0"
        details, error = parse_formula_details(formula)
        if error:
            return None, f"物种{formula}: {error}"
        parsed.append({"formula": formula, "coefficient": coefficient, "phase": details["phase"] or "", "elements": details["elements"]})
    return parsed, None


class A006_ReactionBalanceValidator(BaseModelTool):
    model_id, name, scenario, priority = "A006", "反应配平校验", SCENARIO, "P0"
    version, status, qualification_status, count_eligible = "1.0.0", "qualified", "qualified", True
    description = "解析中性反应式并逐元素比较反应物与生成物计量总数。"
    applicable_boundary = "支持显式系数、中性物种和常用箭头；不处理离子、电荷或电子守恒。"
    data_source, source_version = ["Law of conservation of atoms; IUPAC reaction notation"], "stoichiometric-balance-v1"
    formula_reference = "r_e=sum_products(nu*a)-sum_reactants(nu*a); |r_e|<=tolerance"
    source_records = [{"source_id": "ATOM-CONSERVATION", "name": "Stoichiometric conservation of atoms", "version": "v1"}]
    failure_modes = ["箭头缺失或重复", "化学式/系数非法", "离子或电子反应超适用域"]
    independent_validation = ["每个元素残差为零", "全部系数同比缩放判定不变"]
    dependencies = ["A002"]
    relations = [_relation("depends_on", "A002", "复用完整化学式语法"), _relation("overlaps", "A005", "分别校验化学计量与实际质量流守恒")]
    input_fields = [InputField("reaction", "反应式", "string", placeholder="Fe2O3 + 3CO -> 2Fe + 3CO2", description="含一个箭头的中性反应式"), InputField("tolerance", "计量残差容差", "number", False, 1e-12, "1", 0, description="绝对容差")]
    output_fields = [OutputField("reaction", "规范化反应式", "string", description="用->连接"), OutputField("reactants", "反应物", "array", description="物种解析结果"), OutputField("products", "生成物", "array", description="物种解析结果"), OutputField("element_residuals", "元素残差", "object", description="生成物减反应物"), OutputField("balanced", "是否配平", "boolean", description="全部残差在容差内"), OutputField("tolerance", "容差", "number", "1", "绝对容差")]
    validation_rules = [{"rule": "single_arrow", "field": "reaction"}, {"rule": "neutral_species_only", "field": "reaction"}]
    qualification_cases = [
        {"id": "A006-N1", "kind": "normal", "input": {"reaction": "Fe2O3 + 3CO -> 2Fe + 3CO2"}}, {"id": "A006-N2", "kind": "normal", "input": {"reaction": "CaCO3 -> CaO + CO2"}},
        {"id": "A006-N3", "kind": "normal", "input": {"reaction": "Fe2O3 + 2Al -> 2Fe + Al2O3"}}, {"id": "A006-B1", "kind": "boundary", "input": {"reaction": "Fe2O3 + CO -> Fe + CO2"}},
        {"id": "A006-F1", "kind": "failure", "input": {"reaction": "Fe3+ + e- -> Fe2+"}},
    ]

    def invoke(self, params: dict, context: Optional[InvocationContext] = None) -> ModelResult:
        reaction = params["reaction"].strip()
        if _CHARGE_RE.search(reaction):
            return ModelResult(False, error="本版本不支持离子、电荷或电子反应", error_code="MODEL_NOT_APPLICABLE")
        matches = list(_ARROW_RE.finditer(reaction))
        if len(matches) != 1:
            return ModelResult(False, error="反应式必须且只能含一个箭头", error_code="INVALID_INPUT")
        arrow_match = matches[0]
        left, right = reaction[:arrow_match.start()], reaction[arrow_match.end():]
        reactants, error = _parse_reaction_side(left)
        if error: return ModelResult(False, error=error, error_code="INVALID_INPUT")
        products, error = _parse_reaction_side(right)
        if error: return ModelResult(False, error=error, error_code="INVALID_INPUT")
        residuals: Dict[str, float] = {}
        for sign, species in ((-1, reactants), (1, products)):
            for item in species:
                for element, count in item["elements"].items(): residuals[element] = residuals.get(element, 0) + sign*item["coefficient"]*count
        tolerance = float(params.get("tolerance", 1e-12)); balanced = all(abs(v) <= tolerance for v in residuals.values())
        warnings = [] if balanced else [BoundaryWarning("reaction", "反应式未配平: "+", ".join(f"{k}={v:g}" for k,v in sorted(residuals.items()) if abs(v)>tolerance))]
        return ModelResult(True, result={"reaction": f"{left.strip()} -> {right.strip()}", "reactants": reactants, "products": products, "element_residuals": dict(sorted(residuals.items())), "balanced": balanced, "tolerance": tolerance}, boundary_check=BoundaryCheck(balanced, warnings))


class A007_OxygenReductantEquivalent(BaseModelTool):
    model_id, name, scenario, priority = "A007", "氧/还原剂当量", SCENARIO, "P0"
    version, status, qualification_status, count_eligible = "1.0.0", "qualified", "qualified", True
    data_requirement = "REFERENCE_DATA_REQUIRED"
    data_access_mode = "database_repository"
    required_dataset_ids = ["DS_IUPAC_AW_2021"]
    database_tables = ["metallurgy_v2.element_reference"]
    description = "由元素质量组成和初终价态计算电子当量，并换算纯氧或碳还原剂理论需求。"
    applicable_boundary = "质量基准且价态显式给出；O2接受4e-/mol；碳产物限CO或CO2；不含收得率和副反应。"
    data_source = ["IUPAC atomic weights 2021", "Faraday electron-equivalent stoichiometry", "ideal gas molar volume at 273.15K/101.325kPa"]
    source_version = "atomic-weights-2021; equivalent-model-v1"
    formula_reference = "n_e=sum((mw_i/M_i)(z_t-z_0)); n_O2=n_e/4; n_C=|n_e|/(2 or 4)"
    source_records = [{"source_id": "IUPAC-AW-2021", "name": "IUPAC standard atomic weights", "version": "2021 snapshot"}, {"source_id": "ELECTRON-EQUIVALENT", "name": "Electron-equivalent stoichiometry", "version": "v1"}]
    failure_modes = ["未知元素或负组成", "价态映射不完整", "氧纯度越界", "还原产物不支持"]
    independent_validation = ["电子当量为元素kmol与价态变化加权和", "4n_O2等于氧化电子当量", "碳供电子数等于还原需求"]
    dependencies = ["A004"]
    relations = [_relation("depends_on", "A004", "复用非负组成归一化"), _relation("uses_data_of", "A003", "使用相同原子量版本"), _relation("complements", "A006", "分别计算电子当量与校验原子守恒")]
    input_fields = [InputField("composition", "元素质量组成", "object", unit="1", description="元素到非负质量份额"), InputField("basis_mass_kg", "基准质量", "number", unit="kg", min_value=1e-30, description="总质量"), InputField("initial_valences", "初始价态", "object", unit="1", description="每个元素初始氧化数"), InputField("target_valences", "目标价态", "object", unit="1", description="每个元素目标氧化数"), InputField("oxygen_purity", "供氧纯度", "number", False, 1.0, "1", 1e-12, 1.0, description="O2摩尔分数"), InputField("reductant_product", "碳氧化产物", "select", False, "CO", enum=["CO", "CO2"], description="CO或CO2")]
    output_fields = [OutputField("mode", "模式", "string", description="oxidation/reduction/neutral"), OutputField("normalized_composition", "归一化组成", "object", description="质量分数"), OutputField("electron_breakdown", "逐元素当量", "object", description="kmol价态与电子变化"), OutputField("net_electron_change_kmol", "净电子变化", "number", "kmol e-", "正氧化负还原"), OutputField("electron_equivalents_kmol", "电子当量绝对值", "number", "kmol e-", "绝对值"), OutputField("oxygen_required_kmol", "理论纯氧", "number", "kmol O2", "纯O2需求"), OutputField("oxygen_required_mass_kg", "理论纯氧质量", "number", "kg O2", "纯O2质量"), OutputField("oxygen_supply_kmol", "按纯度供氧", "number", "kmol gas", "供氧气体量"), OutputField("oxygen_supply_normal_volume_m3", "标准供氧体积", "number", "Nm3", "273.15K和101.325kPa"), OutputField("carbon_equivalent_kmol", "理论碳当量", "number", "kmol C", "纯碳需求"), OutputField("carbon_equivalent_mass_kg", "理论碳质量", "number", "kg C", "纯碳质量"), OutputField("reductant_product", "碳氧化产物", "string", description="CO或CO2"), OutputField("electron_balance_residual_kmol", "电子闭合残差", "number", "kmol e-", "供需残差")]
    validation_rules = [{"rule": "A004_nonnegative_normalization", "field": "composition"}, {"rule": "complete_valence_maps", "fields": ["initial_valences", "target_valences"]}]
    qualification_cases = [
        {"id": "A007-N1", "kind": "normal", "input": {"composition": {"C": 1}, "basis_mass_kg": 12.011, "initial_valences": {"C": 0}, "target_valences": {"C": 4}}},
        {"id": "A007-N2", "kind": "normal", "input": {"composition": {"Si": 1}, "basis_mass_kg": 28.085, "initial_valences": {"Si": 0}, "target_valences": {"Si": 4}}},
        {"id": "A007-N3", "kind": "normal", "input": {"composition": {"Fe": 1}, "basis_mass_kg": 55.845, "initial_valences": {"Fe": 2}, "target_valences": {"Fe": 0}}},
        {"id": "A007-F1", "kind": "failure", "input": {"composition": {"Fe": 1}, "basis_mass_kg": 55.845, "initial_valences": {"Fe": 0}, "target_valences": {}}},
        {"id": "A007-F2", "kind": "failure", "input": {"composition": {"Fe": 1}, "basis_mass_kg": 55.845, "initial_valences": {"Fe": 0}, "target_valences": {"Fe": 2}, "oxygen_purity": 0}},
    ]
    data_qualification_cases = [{"id": "A007-D1", "input": {"composition": {"Si": 1}, "basis_mass_kg": 28.085, "initial_valences": {"Si": 0}, "target_valences": {"Si": 4}}}]

    def invoke(self, params: dict, context: Optional[InvocationContext] = None) -> ModelResult:
        parsed, error = normalize_composition(params["composition"])
        if error: return ModelResult(False, error=error, error_code="INVALID_INPUT")
        initial, target, elements = params["initial_valences"], params["target_valences"], set(parsed["normalized"])
        if not isinstance(initial, dict) or not isinstance(target, dict) or set(initial) != elements or set(target) != elements:
            return ModelResult(False, error="初始和目标价态必须恰好覆盖全部组成元素", error_code="INVALID_INPUT")
        try:
            weights, provenance = atomic_weights(elements | {"O", "C"})
        except RepositoryError as exc:
            return ModelResult(False, error=str(exc), error_code=exc.error_code)
        breakdown, net, basis = {}, 0.0, float(params["basis_mass_kg"])
        for element, fraction in parsed["normalized"].items():
            try: z0, z1 = float(initial[element]), float(target[element])
            except (TypeError, ValueError): return ModelResult(False, error=f"{element}价态必须是数值", error_code="INVALID_INPUT")
            if not math.isfinite(z0) or not math.isfinite(z1): return ModelResult(False, error=f"{element}价态必须有限", error_code="INVALID_INPUT")
            kmol = basis*fraction/weights[element]; change = kmol*(z1-z0); net += change
            breakdown[element] = {"mass_fraction": fraction, "element_kmol": kmol, "initial_valence": z0, "target_valence": z1, "electron_change_kmol": change}
        eq = abs(net); oxygen = oxygen_mass = supply = volume = carbon = carbon_mass = 0.0; product = params.get("reductant_product", "CO")
        if net > 0:
            mode = "oxidation"; oxygen = eq/4; oxygen_mass = oxygen*2*weights["O"]; supply = oxygen/float(params.get("oxygen_purity", 1)); volume = supply*(8.31446261815324*273.15/101.325); supplied = oxygen*4
        elif net < 0:
            mode = "reduction"; per_c = 2 if product == "CO" else 4; carbon = eq/per_c; carbon_mass = carbon*weights["C"]; supplied = carbon*per_c
        else: mode, supplied = "neutral", 0.0
        return ModelResult(True, result={"mode": mode, "normalized_composition": parsed["normalized"], "electron_breakdown": breakdown, "net_electron_change_kmol": net, "electron_equivalents_kmol": eq, "oxygen_required_kmol": oxygen, "oxygen_required_mass_kg": oxygen_mass, "oxygen_supply_kmol": supply, "oxygen_supply_normal_volume_m3": volume, "carbon_equivalent_kmol": carbon, "carbon_equivalent_mass_kg": carbon_mass, "reductant_product": product, "electron_balance_residual_kmol": eq-supplied}, provenance=provenance)


class A101_ChargeValenceBalance(BaseModelTool):
    """Catalog A007; A101 avoids colliding with the legacy runtime A007."""

    model_id, name, scenario, priority = "A101", "电荷与价态平衡", SCENARIO, "P0"
    version, status, qualification_status, count_eligible = "1.0.0", "qualified", "qualified", True
    tool_name = "metallurgy_check_charge_valence_balance"
    description = "根据化学式计量数和显式氧化态计算每化学式单元净电荷，校验电中性或指定离子电荷；混合价态必须拆分位点。"
    applicable_boundary = "适用于A002可解析的无机化学式；不从晶体结构猜测价态，也不自动求解欠定混合价态。"
    data_source = ["IUPAC Gold Book: oxidation state", "IUPAC Gold Book: electroneutrality"]
    source_version = "IUPAC Gold Book online definitions; charge-balance-v1"
    formula_reference = "q=sum_i(n_i*z_i); residual=q-target_charge"
    source_records = [
        {"source_id": "IUPAC-OS", "name": "IUPAC oxidation state definition", "version": "online", "url": "https://goldbook.iupac.org/terms/view/O04365"},
        {"source_id": "IUPAC-ELECTRONEUTRALITY", "name": "IUPAC electroneutrality principle", "version": "online", "url": "https://goldbook.iupac.org/terms/view/E01992/plain"},
    ]
    failure_modes = ["价态映射未覆盖全部元素或包含多余元素", "混合价态位点计量数与化学式不一致", "价态或目标电荷不是有限数值", "化学式超出A002语法"]
    independent_validation = ["总电荷等于计量数与氧化态乘积之和", "位点重排不改变总电荷", "化学式计量和目标电荷同比缩放时残差同比缩放"]
    dependencies = ["A002"]
    relations = [
        _relation("depends_on", "A002", "复用相同化学式解析语法和元素计量数"),
        _relation("complements", "A006", "分别校验物种电荷与反应元素守恒"),
        _relation("upstream_of", "A007", "价态校验可先于氧/还原剂电子当量计算"),
    ]
    input_fields = [
        InputField("formula", "化学式", "string", placeholder="如 Al2O3 或 SO4", description="不含离子上标；目标电荷单独给出"),
        InputField("oxidation_states", "氧化态映射", "object", unit="1", description="元素到氧化态数值，或[{oxidation_state,count}]混合价态位点列表"),
        InputField("target_charge", "目标电荷", "number", required=False, default=0.0, unit="e/formula_unit", description="中性物质为0，阴离子为负"),
        InputField("tolerance", "电荷残差容差", "number", required=False, default=1e-12, unit="e/formula_unit", min_value=0.0),
    ]
    output_fields = [
        OutputField("formula", "化学式", "string"),
        OutputField("element_counts", "元素计量数", "object"),
        OutputField("oxidation_state_assignments", "规范化价态位点", "object"),
        OutputField("charge_contributions", "逐元素电荷贡献", "object"),
        OutputField("calculated_charge", "计算电荷", "number", "e/formula_unit"),
        OutputField("target_charge", "目标电荷", "number", "e/formula_unit"),
        OutputField("charge_residual", "电荷残差", "number", "e/formula_unit"),
        OutputField("balanced", "是否满足目标电荷", "boolean"),
        OutputField("mixed_valence", "是否含混合价态", "boolean"),
        OutputField("tolerance", "判定容差", "number", "e/formula_unit"),
    ]
    validation_rules = [
        {"rule": "A002_formula", "field": "formula"},
        {"rule": "complete_oxidation_state_mapping", "field": "oxidation_states"},
        {"rule": "site_counts_match_formula", "field": "oxidation_states"},
    ]
    qualification_cases = [
        {"id": "A101-N1", "kind": "normal", "input": {"formula": "NaCl", "oxidation_states": {"Na": 1, "Cl": -1}}},
        {"id": "A101-N2", "kind": "normal", "input": {"formula": "Al2O3", "oxidation_states": {"Al": 3, "O": -2}}},
        {"id": "A101-N3", "kind": "normal", "input": {"formula": "SO4", "oxidation_states": {"S": 6, "O": -2}, "target_charge": -2}},
        {"id": "A101-B1", "kind": "boundary", "input": {"formula": "FeO", "oxidation_states": {"Fe": 3, "O": -2}}},
        {"id": "A101-F1", "kind": "failure", "input": {"formula": "Fe3O4", "oxidation_states": {"Fe": [{"oxidation_state": 2, "count": 1}], "O": -2}}},
    ]

    @staticmethod
    def _assignments(element: str, formula_count: float, raw_value):
        values = raw_value if isinstance(raw_value, list) else [
            {"oxidation_state": raw_value, "count": formula_count}
        ]
        if not values:
            return None, f"{element}价态位点不能为空"
        parsed, count_sum = [], 0.0
        for index, item in enumerate(values):
            if not isinstance(item, dict):
                return None, f"{element}混合价态位点[{index}]必须是对象"
            try:
                state = float(item["oxidation_state"])
                count = float(item["count"])
            except (KeyError, TypeError, ValueError):
                return None, f"{element}混合价态位点必须包含数值oxidation_state和count"
            if not math.isfinite(state) or not math.isfinite(count) or count <= 0:
                return None, f"{element}价态必须有限且位点计量数必须大于0"
            if not -8 <= state <= 8:
                return None, f"{element}氧化态{state:g}超出本工具[-8,8]适用域"
            parsed.append({"oxidation_state": state, "count": count})
            count_sum += count
        if not math.isclose(count_sum, formula_count, rel_tol=0.0, abs_tol=1e-12):
            return None, f"{element}位点计量数之和{count_sum:g}与化学式计量数{formula_count:g}不一致"
        return parsed, None

    def invoke(self, params: dict, context: Optional[InvocationContext] = None) -> ModelResult:
        details, error = parse_formula_details(params["formula"])
        if error:
            return ModelResult(False, error=error, error_code="INVALID_INPUT")
        states = params["oxidation_states"]
        elements = details["elements"]
        if not isinstance(states, dict) or set(states) != set(elements):
            return ModelResult(False, error="氧化态映射必须恰好覆盖化学式中的全部元素", error_code="INVALID_INPUT")
        assignments, contributions = {}, {}
        calculated_charge, mixed = 0.0, False
        for element, formula_count in elements.items():
            parsed, error = self._assignments(element, float(formula_count), states[element])
            if error:
                return ModelResult(False, error=error, error_code="INVALID_INPUT")
            mixed = mixed or len(parsed) > 1
            contribution = math.fsum(x["oxidation_state"] * x["count"] for x in parsed)
            assignments[element] = parsed
            contributions[element] = contribution
            calculated_charge += contribution
        target = float(params.get("target_charge", 0.0))
        tolerance = float(params.get("tolerance", 1e-12))
        residual = calculated_charge - target
        balanced = abs(residual) <= tolerance
        warnings = [] if balanced else [BoundaryWarning(
            "oxidation_states", f"计算电荷{calculated_charge:g}与目标电荷{target:g}不一致"
        )]
        return ModelResult(
            True,
            result={
                "formula": params["formula"],
                "element_counts": elements,
                "oxidation_state_assignments": assignments,
                "charge_contributions": contributions,
                "calculated_charge": calculated_charge,
                "target_charge": target,
                "charge_residual": residual,
                "balanced": balanced,
                "mixed_valence": mixed,
                "tolerance": tolerance,
            },
            boundary_check=BoundaryCheck(balanced, warnings),
        )


class A008_MissingValueImputer(BaseModelTool):
    model_id, name, scenario, priority = "A008", "缺失值处理", SCENARIO, "P0"
    version, status, qualification_status, count_eligible = "1.0.0", "qualified", "qualified", True
    tool_name = "metallurgy_impute_missing_values"
    description = "对带列名和单位的数值表执行可复现的常数、均值、中位数、众数、线性插值或KNN填补，并保留原始缺失掩码。"
    applicable_boundary = "仅处理二维数值表；观察值保持不变；v1不执行监督/生成式填补，也不允许把标签列隐式用于距离。"
    data_source = ["scikit-learn imputation algorithm definitions", "NumPy deterministic implementation"]
    source_version = "imputation-contract-v1; NumPy runtime"
    formula_reference = "column statistics; piecewise linear interpolation; nan-aware Euclidean KNN with inverse-distance weighting"
    source_records = [
        {"source_id": "SKLEARN-IMPUTE", "name": "scikit-learn Imputation API reference", "version": "online", "url": "https://scikit-learn.org/stable/api/sklearn.impute.html"},
        {"source_id": "NUMPY", "name": "NumPy numerical array algorithms", "version": np.__version__},
    ]
    failure_modes = ["二维数组为空或列数不一致", "列名/单位未完整声明", "整列缺失且方法无法形成统计量", "KNN没有具有共同观察特征的供体", "数据含非有限观察值"]
    independent_validation = ["所有非缺失观察值逐位保持不变", "无缺失输入幂等", "均值/中位数结果可人工复算", "行顺序置换不改变KNN对应结果"]
    dependencies = []
    relations = [
        _relation("complements", "A004", "分别处理缺失值和成分尺度归一化"),
        _relation("upstream_of", "D021", "可作为显式记录的工艺数据预处理步骤，但D021不隐式调用"),
    ]
    input_fields = [
        InputField("data", "数值数据矩阵", "array", items={"type": "array", "items": {"anyOf": [{"type": "number"}, {"type": "null"}]}}, description="行是样本，列是变量；缺失值用null"),
        InputField("columns", "列名", "array", items={"type": "string"}, description="列名数量必须等于矩阵列数"),
        InputField("column_units", "列单位", "object", description="每个列名到单位字符串的完整映射，无量纲写1"),
        InputField("method", "填补方法", "select", enum=["constant", "mean", "median", "most_frequent", "linear", "knn"]),
        InputField("constant_value", "常数填充值", "number", required=False, unit="$column_unit", description="method=constant时必填，按各列声明单位解释"),
        InputField("n_neighbors", "KNN邻居数", "number", required=False, default=3, unit="count", min_value=1, description="method=knn时使用"),
    ]
    output_fields = [
        OutputField("imputed_data", "填补后矩阵", "array"),
        OutputField("missing_mask", "原始缺失掩码", "array"),
        OutputField("columns", "列名", "array"),
        OutputField("column_units", "列单位", "object"),
        OutputField("method", "实际方法", "string"),
        OutputField("statistics", "统计量或逐格KNN记录", "object"),
        OutputField("imputed_count", "填补数量", "number", "count"),
        OutputField("remaining_missing_count", "剩余缺失数量", "number", "count"),
        OutputField("warnings", "质量警告", "array"),
    ]
    validation_rules = [
        {"rule": "rectangular_numeric_matrix", "field": "data"},
        {"rule": "columns_and_units_complete", "fields": ["columns", "column_units"]},
        {"rule": "observed_values_immutable", "field": "data"},
    ]
    qualification_cases = [
        {"id": "A008-N1", "kind": "normal", "input": {"data": [[1, 10], [None, 20], [3, 30]], "columns": ["x", "y"], "column_units": {"x": "1", "y": "K"}, "method": "mean"}},
        {"id": "A008-N2", "kind": "normal", "input": {"data": [[0, 10], [1, None], [2, 30]], "columns": ["time", "value"], "column_units": {"time": "s", "value": "K"}, "method": "linear"}},
        {"id": "A008-N3", "kind": "normal", "input": {"data": [[0, 0], [1, 1], [1.1, None], [10, 10]], "columns": ["x", "y"], "column_units": {"x": "1", "y": "1"}, "method": "knn", "n_neighbors": 1}},
        {"id": "A008-B1", "kind": "boundary", "input": {"data": [[1, 2], [3, 4]], "columns": ["x", "y"], "column_units": {"x": "1", "y": "1"}, "method": "median"}},
        {"id": "A008-F1", "kind": "failure", "input": {"data": [[None, 1], [None, 2]], "columns": ["x", "y"], "column_units": {"x": "1", "y": "1"}, "method": "mean"}},
    ]

    @staticmethod
    def _matrix(params):
        data = params["data"]
        columns = params["columns"]
        units = params["column_units"]
        if not isinstance(data, list) or not data or not all(isinstance(row, list) for row in data):
            return None, None, "data必须是非空二维数组"
        width = len(data[0])
        if width == 0 or any(len(row) != width for row in data):
            return None, None, "data每行列数必须一致且大于0"
        if not isinstance(columns, list) or len(columns) != width or any(not isinstance(x, str) or not x.strip() for x in columns) or len(set(columns)) != width:
            return None, None, "columns必须是与矩阵列数一致的唯一非空字符串"
        if not isinstance(units, dict) or set(units) != set(columns) or any(not isinstance(x, str) or not x.strip() for x in units.values()):
            return None, None, "column_units必须恰好覆盖全部列且值为非空单位字符串"
        matrix = np.empty((len(data), width), dtype=float)
        for row_index, row in enumerate(data):
            for column_index, value in enumerate(row):
                if value is None:
                    matrix[row_index, column_index] = np.nan
                    continue
                if isinstance(value, bool):
                    return None, None, f"data[{row_index}][{column_index}]必须是数值或null"
                try:
                    numeric = float(value)
                except (TypeError, ValueError):
                    return None, None, f"data[{row_index}][{column_index}]必须是数值或null"
                if not math.isfinite(numeric):
                    return None, None, f"data[{row_index}][{column_index}]观察值必须有限"
                matrix[row_index, column_index] = numeric
        return matrix, columns, None

    @staticmethod
    def _knn_impute(matrix: np.ndarray, neighbors: int):
        original = matrix.copy()
        output = matrix.copy()
        records = {}
        row_count, column_count = original.shape
        for row_index, column_index in zip(*np.where(np.isnan(original))):
            candidates = []
            for donor in range(row_count):
                if donor == row_index or np.isnan(original[donor, column_index]):
                    continue
                feature_mask = ~np.isnan(original[row_index]) & ~np.isnan(original[donor])
                feature_mask[column_index] = False
                common = int(feature_mask.sum())
                if common == 0:
                    continue
                delta = original[row_index, feature_mask] - original[donor, feature_mask]
                distance = float(math.sqrt(float(np.dot(delta, delta)) * max(column_count - 1, 1) / common))
                candidates.append((distance, donor, float(original[donor, column_index])))
            if not candidates:
                return None, None, f"data[{row_index}][{column_index}]没有具备共同观察特征的KNN供体"
            selected = sorted(candidates, key=lambda x: (x[0], x[1]))[:neighbors]
            zero = [item for item in selected if item[0] <= 1e-15]
            if zero:
                value = math.fsum(item[2] for item in zero) / len(zero)
            else:
                weights = [1.0 / item[0] for item in selected]
                value = math.fsum(weight * item[2] for weight, item in zip(weights, selected)) / math.fsum(weights)
            output[row_index, column_index] = value
            records[f"{row_index},{column_index}"] = {
                "donor_rows": [item[1] for item in selected],
                "distances": [item[0] for item in selected],
                "value": value,
            }
        return output, records, None

    def invoke(self, params: dict, context: Optional[InvocationContext] = None) -> ModelResult:
        matrix, columns, error = self._matrix(params)
        if error:
            return ModelResult(False, error=error, error_code="INVALID_INPUT")
        mask = np.isnan(matrix)
        missing_count = int(mask.sum())
        method = params["method"]
        output = matrix.copy()
        statistics = {}
        warnings = []
        if missing_count == 0:
            warnings.append("输入不含缺失值，未执行填补")
        elif method == "constant":
            if "constant_value" not in params:
                return ModelResult(False, error="method=constant时必须提供constant_value", error_code="INVALID_INPUT")
            value = float(params["constant_value"])
            output[mask] = value
            statistics = {column: {"fill_value": value} for column in columns}
        elif method in {"mean", "median", "most_frequent"}:
            for index, column in enumerate(columns):
                observed = matrix[~mask[:, index], index]
                if observed.size == 0:
                    return ModelResult(False, error=f"列{column}全部缺失，无法计算{method}统计量", error_code="OUT_OF_DOMAIN")
                if method == "mean":
                    value = float(np.mean(observed))
                elif method == "median":
                    value = float(np.median(observed))
                else:
                    values, counts = np.unique(observed, return_counts=True)
                    value = float(values[int(np.argmax(counts))])
                output[mask[:, index], index] = value
                statistics[column] = {"fill_value": value, "observed_count": int(observed.size)}
        elif method == "linear":
            row_axis = np.arange(matrix.shape[0], dtype=float)
            for index, column in enumerate(columns):
                observed_mask = ~mask[:, index]
                if int(observed_mask.sum()) < 2:
                    return ModelResult(False, error=f"列{column}至少需要2个观察值才能线性插值", error_code="OUT_OF_DOMAIN")
                output[:, index] = np.interp(row_axis, row_axis[observed_mask], matrix[observed_mask, index])
                statistics[column] = {"observed_rows": np.where(observed_mask)[0].tolist()}
        else:
            neighbors = int(float(params.get("n_neighbors", 3)))
            if not math.isclose(float(params.get("n_neighbors", 3)), neighbors):
                return ModelResult(False, error="n_neighbors必须是整数", error_code="INVALID_INPUT")
            output, records, error = self._knn_impute(matrix, neighbors)
            if error:
                return ModelResult(False, error=error, error_code="OUT_OF_DOMAIN")
            statistics = {"cells": records, "n_neighbors": neighbors}
        remaining = int(np.isnan(output).sum())
        boundary_warnings = [BoundaryWarning("data", message) for message in warnings]
        return ModelResult(
            True,
            result={
                "imputed_data": output.tolist(),
                "missing_mask": mask.tolist(),
                "columns": columns,
                "column_units": params["column_units"],
                "method": method,
                "statistics": statistics,
                "imputed_count": missing_count - remaining,
                "remaining_missing_count": remaining,
                "warnings": warnings,
            },
            boundary_check=BoundaryCheck(not warnings, boundary_warnings),
        )
