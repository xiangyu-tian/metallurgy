"""P1-W7 qualified BOF slag/metal balance and equilibrium tools."""
from __future__ import annotations

import math
from typing import Any, Optional

from .base import (
    BaseModelTool,
    BoundaryCheck,
    BoundaryWarning,
    InputField,
    InvocationContext,
    ModelResult,
    OutputField,
)
from .models_a import parse_formula
from .repositories.bof_slag_repository import approved_parameter_set
from .repositories.reference_repository import RepositoryError, atomic_weights


SCENARIO = "冶金工艺、物料与热平衡"
PARAMETER_TABLE = "metallurgy_v2.bof_slag_model_parameter"
ELEMENT_TABLE = "metallurgy_v2.element_reference"

DYNAMIC_NONNEGATIVE_MAP_SCHEMA = {
    "type": "object",
    "minProperties": 1,
    "propertyNames": {"type": "string", "minLength": 1},
    "additionalProperties": {"type": "number", "minimum": 0},
}

MASS_FRACTION_COMPONENT_MAP_SCHEMA = {
    "type": "object",
    "minProperties": 1,
    "propertyNames": {"type": "string", "minLength": 1},
    "additionalProperties": {"type": "number", "minimum": 0, "maximum": 1},
}

MASS_PERCENT_COMPONENT_MAP_SCHEMA = {
    "type": "object",
    "minProperties": 1,
    "propertyNames": {"type": "string", "minLength": 1},
    "additionalProperties": {"type": "number", "minimum": 0, "maximum": 100},
}

SLAG_MASS_STREAM_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "minLength": 1},
        "mass_kg": {"type": "number", "exclusiveMinimum": 0},
        "composition": MASS_FRACTION_COMPONENT_MAP_SCHEMA,
    },
    "required": ["name", "mass_kg", "composition"],
    "additionalProperties": False,
}


def _rel(kind: str, target: str, description: str) -> dict[str, str]:
    return {"type": kind, "target": target, "description": description}


def _fail(message: str, code: str = "INVALID_INPUT") -> ModelResult:
    return ModelResult(False, error=message, error_code=code)


def _number(value: Any, label: str, *, positive: bool = False,
            nonnegative: bool = False) -> tuple[Optional[float], Optional[str]]:
    if isinstance(value, bool):
        return None, f"{label}必须是数值"
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None, f"{label}必须是数值"
    if not math.isfinite(parsed):
        return None, f"{label}必须是有限数值"
    if positive and parsed <= 0:
        return None, f"{label}必须大于0"
    if nonnegative and parsed < 0:
        return None, f"{label}不能为负"
    return parsed, None


def _nonnegative_map(raw: Any, label: str, *, upper: float | None = None,
                     require_positive: bool = True) -> tuple[Optional[dict[str, float]], Optional[str]]:
    if not isinstance(raw, dict) or not raw:
        return None, f"{label}必须是非空对象"
    parsed: dict[str, float] = {}
    for key, value in raw.items():
        if not isinstance(key, str) or not key.strip():
            return None, f"{label}包含空组分名"
        number, error = _number(value, f"{label}.{key}", nonnegative=True)
        if error:
            return None, error
        assert number is not None
        if upper is not None and number > upper:
            return None, f"{label}.{key}不能超过{upper:g}"
        parsed[key.strip()] = number
    if require_positive and not any(value > 0 for value in parsed.values()):
        return None, f"{label}至少一个值必须大于0"
    return parsed, None


def _mass_streams(raw: Any, label: str) \
        -> tuple[Optional[list[dict[str, Any]]], Optional[str]]:
    if raw is None:
        return [], None
    if not isinstance(raw, list):
        return None, f"{label}必须是数组"
    parsed: list[dict[str, Any]] = []
    for index, stream in enumerate(raw):
        if not isinstance(stream, dict):
            return None, f"{label}[{index}]必须是对象"
        name = stream.get("name")
        if not isinstance(name, str) or not name.strip():
            return None, f"{label}[{index}].name不能为空"
        mass, error = _number(stream.get("mass_kg"), f"{label}[{index}].mass_kg", positive=True)
        if error:
            return None, error
        composition, error = _nonnegative_map(
            stream.get("composition"), f"{label}[{index}].composition", upper=1.0
        )
        if error:
            return None, error
        assert composition is not None and mass is not None
        total = math.fsum(composition.values())
        if not math.isclose(total, 1.0, rel_tol=0, abs_tol=1e-9):
            return None, f"{label}[{index}].composition质量分数之和必须等于1"
        parsed.append({"name": name.strip(), "mass_kg": mass, "composition": composition})
    return parsed, None


def _merge_streams(streams: list[dict[str, Any]], components: dict[str, float]) -> float:
    total = 0.0
    for stream in streams:
        mass = float(stream["mass_kg"])
        total += mass
        for component, fraction in stream["composition"].items():
            components[component] = components.get(component, 0.0) + mass * fraction
    return total


def _mass_balance_equilibrium(total_mass_kg: float, metal_mass_kg: float,
                              slag_mass_kg: float, partition: float) -> tuple[float, float, float]:
    denominator = metal_mass_kg + slag_mass_kg * partition
    if denominator <= 0 or not math.isfinite(denominator):
        raise ValueError("分配质量守恒分母必须为有限正值")
    metal_percent = 100.0 * total_mass_kg / denominator
    slag_percent = partition * metal_percent
    reconstructed = (
        metal_mass_kg * metal_percent / 100.0
        + slag_mass_kg * slag_percent / 100.0
    )
    return metal_percent, slag_percent, total_mass_kg - reconstructed


class _P1FormulaProcessTool(BaseModelTool):
    scenario = SCENARIO
    priority = "P1"
    status = "qualified"
    qualification_status = "qualified"
    count_eligible = True
    data_requirement = "FORMULA_ONLY"
    data_access_mode = "none"


class _P1DataProcessTool(BaseModelTool):
    scenario = SCENARIO
    priority = "P1"
    status = "qualified"
    qualification_status = "qualified"
    count_eligible = True
    data_requirement = "VERSIONED_DATABASE_REFERENCE"
    data_access_mode = "database_repository"


class D005_BOFSlagMassEstimate(_P1DataProcessTool):
    model_id, name, version = "D005", "炉渣量估算", "1.0.0"
    tool_name = "metallurgy_estimate_bof_slag_mass"
    required_dataset_ids = ["DS_IUPAC_AW_2021"]
    database_tables = [ELEMENT_TABLE]
    description = "把D001分元素氧化量按指定氧化物计量换算，并与熔剂、炉衬侵蚀、其他渣源和显式金属夹带汇总为静态总渣量与组成。"
    applicable_boundary = "零维单炉静态估算；元素氧化去向、捕集率、熔剂、侵蚀和夹带必须显式输入；不提供企业默认收得率或在线炉况预测。"
    formula_reference = "m_oxide=m_element*capture/(n_element*A_element/M_oxide); m_slag=sum(oxidation products, flux, refractory, other, entrained metal)"
    source_version = "IUPAC-AW-2021 + P1-W7-STATIC-SLAG-BALANCE-v1"
    source_records = [{"source_id": "IUPAC-AW-2021", "name": "IUPAC standard atomic weights", "version": "2021 snapshot"}]
    data_source = ["IUPAC/CIAAW标准原子量2021数据库", "显式单炉物料输入"]
    failure_modes = ["氧化物不含声明元素或化学式非法", "氧化量/流股质量为负", "流股组成不闭合", "无任何有效渣相来源"]
    independent_validation = ["1 kmol Si生成1 kmol SiO2的手算计量", "来源质量之和等于总渣量", "捕集率对氧化物生成量呈线性", "组分质量之和闭合"]
    dependencies = ["A002", "A003", "D001", "D004"]
    relations = [
        _rel("depends_on", "A002", "氧化物化学式采用A002完整解析规则"),
        _rel("depends_on", "A003", "复用A003的数据库原子量和摩尔质量定义"),
        _rel("consumes_output_from", "D001", "D001分元素氧化质量可直接作为本工具输入"),
        _rel("consumes_output_from", "D004", "D004求得的熔剂物流可作为flux_streams输入"),
        _rel("upstream_of", "D006", "总渣组成供碱度评价"),
        _rel("upstream_of", "D014", "总渣量和铁氧化物组成供TFe与铁损计算"),
    ]
    input_fields = [
        InputField("oxidized_element_masses_kg", "分元素氧化质量", "object", unit="kg/basis", description="元素符号到非负氧化质量的非空映射，例如{Si:10,Mn:2}", json_schema=DYNAMIC_NONNEGATIVE_MAP_SCHEMA),
        InputField("oxide_product_formulas", "元素氧化物去向", "object", description="元素符号到唯一氧化物化学式的非空映射；键必须与氧化质量完全一致", json_schema={"type": "object", "minProperties": 1, "propertyNames": {"type": "string", "minLength": 1}, "additionalProperties": {"type": "string", "minLength": 1}}),
        InputField("oxide_capture_fractions", "氧化物入渣捕集率", "object", required=False, description="元素到[0,1]捕集率；省略元素按1", json_schema={"type": "object", "propertyNames": {"type": "string", "minLength": 1}, "additionalProperties": {"type": "number", "minimum": 0, "maximum": 1}}),
        InputField("flux_streams", "熔剂流股", "array", required=False, items=SLAG_MASS_STREAM_SCHEMA, description="[{name,mass_kg,composition:{CaO:0.9,...}}]，组成质量分数和为1"),
        InputField("refractory_streams", "炉衬侵蚀流股", "array", required=False, items=SLAG_MASS_STREAM_SCHEMA, description="格式同flux_streams"),
        InputField("other_slag_streams", "其他渣源流股", "array", required=False, items=SLAG_MASS_STREAM_SCHEMA, description="格式同flux_streams"),
        InputField("entrained_metal_mass_kg", "显式金属夹带", "number", required=False, default=0.0, unit="kg/basis", min_value=0),
        InputField("basis", "计算基准", "select", required=False, default="per_heat", enum=["per_heat", "per_t_steel"]),
    ]
    output_fields = [
        OutputField("oxidation_product_masses_kg", "氧化产物质量", "object"),
        OutputField("oxidized_elements_captured_kg", "入渣氧化元素质量", "object"),
        OutputField("source_masses_kg", "来源质量分项", "object"),
        OutputField("component_masses_kg", "渣组分质量", "object"),
        OutputField("component_mass_fractions", "渣组分质量分数", "object"),
        OutputField("total_slag_mass_kg", "总渣量", "number", "kg/basis"),
        OutputField("entrained_metal_mass_kg", "金属夹带质量", "number", "kg/basis"),
        OutputField("mass_closure_residual_kg", "质量闭合残差", "number", "kg/basis"),
        OutputField("basis", "计算基准", "string"),
        OutputField("assumptions", "模型假设", "array"),
    ]
    validation_rules = [{"rule": "nonnegative", "fields": ["oxidized_element_masses_kg", "entrained_metal_mass_kg"]}, {"rule": "stream_composition_sum", "value": 1.0}]
    qualification_cases = [
        {"id": "D005-N1", "kind": "normal", "input": {"oxidized_element_masses_kg": {"Si": 28.085}, "oxide_product_formulas": {"Si": "SiO2"}}},
        {"id": "D005-N2", "kind": "normal", "input": {"oxidized_element_masses_kg": {"Mn": 5.494, "Fe": 5.5845}, "oxide_product_formulas": {"Mn": "MnO", "Fe": "FeO"}, "flux_streams": [{"name": "lime", "mass_kg": 10, "composition": {"CaO": 0.9, "SiO2": 0.1}}]}},
        {"id": "D005-N3", "kind": "normal", "input": {"oxidized_element_masses_kg": {"P": 3.09738}, "oxide_product_formulas": {"P": "P2O5"}, "refractory_streams": [{"name": "lining", "mass_kg": 2, "composition": {"MgO": 1}}], "other_slag_streams": [{"name": "carryover", "mass_kg": 1, "composition": {"CaO": 1}}], "entrained_metal_mass_kg": 0.5}},
        {"id": "D005-B1", "kind": "boundary", "input": {"oxidized_element_masses_kg": {"Si": 1}, "oxide_product_formulas": {"Si": "SiO2"}, "oxide_capture_fractions": {"Si": 0}, "flux_streams": [{"name": "lime", "mass_kg": 1, "composition": {"CaO": 1}}]}},
        {"id": "D005-F1", "kind": "failure", "input": {"oxidized_element_masses_kg": {"Si": 1}, "oxide_product_formulas": {"Si": "FeO"}}},
    ]
    data_qualification_cases = [{"id": "D005-D1", "input": qualification_cases[0]["input"]}]

    def invoke(self, params: dict, context: Optional[InvocationContext] = None) -> ModelResult:
        oxidized, error = _nonnegative_map(params.get("oxidized_element_masses_kg"), "oxidized_element_masses_kg")
        if error:
            return _fail(error)
        formulas = params.get("oxide_product_formulas")
        if not isinstance(formulas, dict) or not formulas:
            return _fail("oxide_product_formulas必须是非空对象")
        assert oxidized is not None
        if set(formulas) != set(oxidized):
            return _fail("oxide_product_formulas的元素键必须与oxidized_element_masses_kg完全一致")
        captures_raw = params.get("oxide_capture_fractions") or {}
        if not isinstance(captures_raw, dict) or set(captures_raw) - set(oxidized):
            return _fail("oxide_capture_fractions必须是氧化元素键的子集")
        captures: dict[str, float] = {}
        all_elements: set[str] = set()
        parsed_formulas: dict[str, dict[str, float]] = {}
        for element, formula in formulas.items():
            if not isinstance(formula, str):
                return _fail(f"oxide_product_formulas.{element}必须是化学式字符串")
            composition, formula_error = parse_formula(formula)
            if formula_error:
                return _fail(f"氧化物{formula}无法解析: {formula_error}")
            assert composition is not None
            if element not in composition:
                return _fail(f"氧化物{formula}不含声明元素{element}")
            if "O" not in composition:
                return _fail(f"{formula}不含氧，不能作为氧化物产物", "MODEL_NOT_APPLICABLE")
            if set(composition) - {element, "O"}:
                return _fail(f"{formula}不是仅含{element}和O的单一氧化物", "MODEL_NOT_APPLICABLE")
            capture, capture_error = _number(captures_raw.get(element, 1.0), f"oxide_capture_fractions.{element}", nonnegative=True)
            if capture_error or capture is None or capture > 1:
                return _fail(capture_error or f"oxide_capture_fractions.{element}必须在[0,1]")
            captures[element] = capture
            parsed_formulas[element] = composition
            all_elements.update(composition)
        try:
            weights, provenance = atomic_weights(all_elements)
        except RepositoryError as exc:
            return _fail(str(exc), exc.error_code)

        components: dict[str, float] = {}
        products: dict[str, float] = {}
        captured: dict[str, float] = {}
        for element, element_mass in oxidized.items():
            composition = parsed_formulas[element]
            molar_mass = math.fsum(weights[symbol] * count for symbol, count in composition.items())
            element_fraction = composition[element] * weights[element] / molar_mass
            captured_mass = element_mass * captures[element]
            product_mass = captured_mass / element_fraction if captured_mass else 0.0
            formula = str(formulas[element])
            products[formula] = products.get(formula, 0.0) + product_mass
            components[formula] = components.get(formula, 0.0) + product_mass
            captured[element] = captured_mass

        stream_groups = {}
        for field in ("flux_streams", "refractory_streams", "other_slag_streams"):
            streams, stream_error = _mass_streams(params.get(field), field)
            if stream_error:
                return _fail(stream_error)
            assert streams is not None
            stream_groups[field] = _merge_streams(streams, components)
        entrained = float(params.get("entrained_metal_mass_kg", 0.0))
        if entrained:
            components["Metal"] = components.get("Metal", 0.0) + entrained
        source_masses = {
            "oxidation_products": math.fsum(products.values()),
            "flux_streams": stream_groups["flux_streams"],
            "refractory_streams": stream_groups["refractory_streams"],
            "other_slag_streams": stream_groups["other_slag_streams"],
            "entrained_metal": entrained,
        }
        total = math.fsum(source_masses.values())
        if total <= 0:
            return _fail("没有形成任何有效渣相", "MISSING_DATA")
        component_total = math.fsum(components.values())
        fractions = {key: value / total for key, value in sorted(components.items())}
        warnings = []
        if any(value < 1 for value in captures.values()):
            warnings.append(BoundaryWarning("oxide_capture_fractions", "存在未入渣氧化产物；捕集率由调用者显式给定"))
        if entrained > 0:
            warnings.append(BoundaryWarning("entrained_metal_mass_kg", "总渣量包含显式金属夹带，化学渣与物理夹带已分项"))
        return ModelResult(
            True,
            result={
                "oxidation_product_masses_kg": dict(sorted(products.items())),
                "oxidized_elements_captured_kg": dict(sorted(captured.items())),
                "source_masses_kg": source_masses,
                "component_masses_kg": dict(sorted(components.items())),
                "component_mass_fractions": fractions,
                "total_slag_mass_kg": total,
                "entrained_metal_mass_kg": entrained,
                "mass_closure_residual_kg": total - component_total,
                "basis": params.get("basis", "per_heat"),
                "assumptions": ["zero-dimensional static balance", "explicit capture and entrainment", "one oxide product per oxidized element"],
            },
            boundary_check=BoundaryCheck(not warnings, warnings),
            provenance=provenance,
        )


class D006_SlagBasicity(_P1FormulaProcessTool):
    model_id, name, version = "D006", "炉渣碱度计算", "1.0.0"
    tool_name = "metallurgy_calculate_slag_basicity"
    description = "按明确命名的质量基二元、三元、四元或自定义分子/分母定义计算炉渣碱度，并按调用者目标区间判定。"
    applicable_boundary = "仅计算质量基组分比；不替代活度、黏度、液相区或生产标定。自定义定义必须显式列出互不重叠的分子和分母组分。"
    formula_reference = "R=sum(mass of numerator components)/sum(mass of denominator components)"
    source_version = "P1-W7-EXPLICIT-MASS-BASICITY-v1"
    source_records = [{"source_id": "P1-W7-BASICITY-DEFINITIONS", "name": "Explicit mass-ratio basicity definitions", "version": "2026.09-v1"}]
    data_source = ["显式质量基碱度定义"]
    failure_modes = ["分母组分质量为零", "负组分质量", "自定义集合为空或重叠", "目标上下限倒置"]
    independent_validation = ["CaO/SiO2手算", "所有质量同比缩放时碱度不变", "定义分子和分母逐项求和复算"]
    dependencies = ["D004", "D005"]
    relations = [
        _rel("consumes_output_from", "D005", "D005渣组分质量可直接输入"),
        _rel("overlaps", "D004", "D004反求熔剂加入量，本工具只评价已知渣样"),
        _rel("upstream_of", "D010", "碱度和渣组成用于解释磷分配结果"),
        _rel("upstream_of", "D011", "渣组成用于硫容量与分配计算"),
    ]
    input_fields = [
        InputField("component_masses_kg", "渣组分质量", "object", unit="kg/basis", description="组分名到非负质量的非空映射，且至少一项大于0", json_schema=DYNAMIC_NONNEGATIVE_MAP_SCHEMA),
        InputField("definition", "碱度定义", "select", required=False, default="R2_CaO_SiO2", enum=["R2_CaO_SiO2", "R3_CaO_MgO_SiO2", "R4_CaO_MgO_SiO2_Al2O3", "CUSTOM"]),
        InputField("custom_numerator_components", "自定义分子组分", "array", required=False, items={"type": "string"}),
        InputField("custom_denominator_components", "自定义分母组分", "array", required=False, items={"type": "string"}),
        InputField("target_min", "目标下限", "number", required=False, unit="dimensionless", min_value=0),
        InputField("target_max", "目标上限", "number", required=False, unit="dimensionless", min_value=0),
    ]
    output_fields = [
        OutputField("definition", "碱度定义", "string"),
        OutputField("numerator_components", "分子组分", "array"),
        OutputField("denominator_components", "分母组分", "array"),
        OutputField("numerator_mass_kg", "分子质量", "number", "kg/basis"),
        OutputField("denominator_mass_kg", "分母质量", "number", "kg/basis"),
        OutputField("basicity", "碱度", "number", "dimensionless"),
        OutputField("component_mass_fractions", "规范化组分质量分数", "object"),
        OutputField("target_range", "目标区间", "object"),
        OutputField("compliance_status", "合格状态", "string"),
        OutputField("is_compliant", "是否合格", "boolean", nullable=True),
    ]
    validation_rules = [{"rule": "nonnegative_map", "field": "component_masses_kg"}, {"rule": "positive_denominator"}]
    qualification_cases = [
        {"id": "D006-N1", "kind": "normal", "input": {"component_masses_kg": {"CaO": 40, "SiO2": 20}, "definition": "R2_CaO_SiO2"}},
        {"id": "D006-N2", "kind": "normal", "input": {"component_masses_kg": {"CaO": 40, "MgO": 10, "SiO2": 25}, "definition": "R3_CaO_MgO_SiO2", "target_min": 1.8, "target_max": 2.2}},
        {"id": "D006-N3", "kind": "normal", "input": {"component_masses_kg": {"CaO": 30, "MgO": 10, "SiO2": 15, "Al2O3": 5}, "definition": "CUSTOM", "custom_numerator_components": ["CaO", "MgO"], "custom_denominator_components": ["SiO2", "Al2O3"]}},
        {"id": "D006-B1", "kind": "boundary", "input": {"component_masses_kg": {"CaO": 0, "SiO2": 10}, "definition": "R2_CaO_SiO2"}},
        {"id": "D006-F1", "kind": "failure", "input": {"component_masses_kg": {"CaO": 10, "SiO2": 0}, "definition": "R2_CaO_SiO2"}},
    ]

    def invoke(self, params: dict, context: Optional[InvocationContext] = None) -> ModelResult:
        masses, error = _nonnegative_map(params.get("component_masses_kg"), "component_masses_kg")
        if error:
            return _fail(error)
        assert masses is not None
        definition = params.get("definition", "R2_CaO_SiO2")
        definitions = {
            "R2_CaO_SiO2": (["CaO"], ["SiO2"]),
            "R3_CaO_MgO_SiO2": (["CaO", "MgO"], ["SiO2"]),
            "R4_CaO_MgO_SiO2_Al2O3": (["CaO", "MgO"], ["SiO2", "Al2O3"]),
        }
        if definition == "CUSTOM":
            numerator = params.get("custom_numerator_components")
            denominator = params.get("custom_denominator_components")
            if not isinstance(numerator, list) or not numerator or not all(isinstance(x, str) and x for x in numerator):
                return _fail("CUSTOM必须提供非空custom_numerator_components")
            if not isinstance(denominator, list) or not denominator or not all(isinstance(x, str) and x for x in denominator):
                return _fail("CUSTOM必须提供非空custom_denominator_components")
            if len(numerator) != len(set(numerator)) or len(denominator) != len(set(denominator)):
                return _fail("自定义分子/分母组分不能重复")
            if set(numerator) & set(denominator):
                return _fail("自定义分子和分母组分不能重叠")
        else:
            numerator, denominator = definitions[definition]
            if params.get("custom_numerator_components") or params.get("custom_denominator_components"):
                return _fail("非CUSTOM定义不能提供自定义组分")
        missing = sorted((set(numerator) | set(denominator)) - set(masses))
        if missing:
            return _fail(f"渣组成缺少定义所需组分: {', '.join(missing)}", "MISSING_DATA")
        numerator_mass = math.fsum(masses[name] for name in numerator)
        denominator_mass = math.fsum(masses[name] for name in denominator)
        if denominator_mass <= 0:
            return _fail("碱度分母组分质量必须大于0", "DIVISION_BY_ZERO")
        basicity = numerator_mass / denominator_mass
        target_min = params.get("target_min")
        target_max = params.get("target_max")
        if target_min is not None:
            target_min = float(target_min)
        if target_max is not None:
            target_max = float(target_max)
        if target_min is not None and target_max is not None and target_min > target_max:
            return _fail("target_min不能大于target_max")
        if target_min is None and target_max is None:
            status, compliant = "not_evaluated", None
        elif target_min is not None and basicity < target_min:
            status, compliant = "below_target", False
        elif target_max is not None and basicity > target_max:
            status, compliant = "above_target", False
        else:
            status, compliant = "within_target", True
        total = math.fsum(masses.values())
        warnings = []
        if numerator_mass == 0:
            warnings.append(BoundaryWarning("component_masses_kg", "碱度为零：所有分子组分质量均为零", min_allowed=0))
        return ModelResult(True, result={
            "definition": definition,
            "numerator_components": numerator,
            "denominator_components": denominator,
            "numerator_mass_kg": numerator_mass,
            "denominator_mass_kg": denominator_mass,
            "basicity": basicity,
            "component_mass_fractions": {key: value / total for key, value in sorted(masses.items())},
            "target_range": {"min": target_min, "max": target_max},
            "compliance_status": status,
            "is_compliant": compliant,
        }, boundary_check=BoundaryCheck(not warnings, warnings))


class D010_PhosphorusPartition(_P1DataProcessTool):
    model_id, name, version = "D010", "磷分配比", "1.0.0"
    tool_name = "metallurgy_predict_phosphorus_partition"
    required_dataset_ids = ["DS_BOF_P_PARTITION_ISIJ_2016"]
    database_tables = [PARAMETER_TABLE]
    description = "读取版本化BOF磷分配经验式，根据温度、渣成分和TFe计算Lp，并以金属/渣P总量守恒给出平衡P。"
    applicable_boundary = "1600–2000 K公开参考筛选；渣成分和TFe用质量百分数；输出是平衡潜力而非吹炼动力学终点，禁止生产控制。"
    temperature_range = [1600.0, 2000.0]
    formula_reference = "log10(Lp/TFe^2.5)=0.06(CaO+0.37MgO+4.65P2O5-0.05Al2O3-0.2SiO2)+11570/T-10.52"
    source_version = "ISIJINT-2016-361-EQ6-v1"
    source_records = [{"source_id": "DS_BOF_P_PARTITION_ISIJ_2016", "name": "Spooner et al. BOF phosphorus partition Eq.6", "version": "2016", "url": "https://doi.org/10.2355/isijinternational.ISIJINT-2016-361"}]
    data_source = ["ISIJINT-2016-361 Eq.6版本化数据库参数"]
    failure_modes = ["温度超参数集批准域", "缺必要渣组分或TFe为零", "P输入超过100%", "平衡质量分数超物理范围", "参数集缺失/未批准"]
    independent_validation = ["逐项代入论文Eq.6手算", "Lp随温度升高降低", "Lp对TFe满足2.5次幂", "金属与渣P质量守恒"]
    dependencies = ["D005", "D006", "D014"]
    relations = [
        _rel("consumes_output_from", "D005", "使用总渣量与渣组成"),
        _rel("complements", "D006", "D006给出碱度指标，本工具计算磷分配平衡潜力"),
        _rel("consumes_output_from", "D014", "使用D014给出的TFe质量百分数"),
        _rel("overlaps", "B009", "均计算平衡关系，但本工具是特定BOF经验分配式"),
    ]
    input_fields = [
        InputField("parameter_set_id", "参数集ID", "string", required=False, default="D010_SPOONER_ISIJ_2016_V1"),
        InputField("calculation_purpose", "计算用途", "select", enum=["reference_validation", "engineering_screening"]),
        InputField("temperature_k", "温度", "number", unit="K", min_value=1e-12),
        InputField("slag_composition_mass_percent", "渣成分", "object", unit="mass percent", description="必须含CaO,MgO,P2O5,Al2O3,SiO2，可含其他非负组分；总和不得超过100", json_schema={**MASS_PERCENT_COMPONENT_MAP_SCHEMA, "properties": {component: {"type": "number", "minimum": 0, "maximum": 100} for component in ("CaO", "MgO", "P2O5", "Al2O3", "SiO2")}, "required": ["CaO", "MgO", "P2O5", "Al2O3", "SiO2"]}),
        InputField("tfe_mass_percent", "渣中TFe", "number", unit="mass percent", min_value=1e-12, max_value=100),
        InputField("metal_mass_kg", "金属质量", "number", unit="kg/basis", min_value=1e-12),
        InputField("slag_mass_kg", "渣质量", "number", unit="kg/basis", min_value=1e-12),
        InputField("initial_metal_p_mass_percent", "初始金属P", "number", unit="mass percent", min_value=0, max_value=100),
        InputField("initial_slag_p_mass_percent", "初始渣P", "number", required=False, default=0.0, unit="mass percent", min_value=0, max_value=100),
    ]
    output_fields = [
        OutputField("log10_apparent_partition", "表观分配对数", "number", "dimensionless"),
        OutputField("phosphorus_partition_ratio", "磷分配比Lp", "number", "dimensionless"),
        OutputField("equilibrium_metal_p_mass_percent", "平衡金属P", "number", "mass percent"),
        OutputField("equilibrium_slag_p_mass_percent", "平衡渣P", "number", "mass percent"),
        OutputField("total_p_mass_kg", "体系P总质量", "number", "kg/basis"),
        OutputField("p_mass_balance_residual_kg", "P守恒残差", "number", "kg/basis"),
        OutputField("parameter_set_id", "参数集ID", "string"),
        OutputField("temperature_k", "温度", "number", "K"),
        OutputField("usage_scope", "数据使用范围", "string"),
        OutputField("assumptions", "模型假设", "array"),
    ]
    validation_rules = [{"rule": "required_components", "values": ["CaO", "MgO", "P2O5", "Al2O3", "SiO2"]}, {"rule": "closed_p_mass_balance"}]
    qualification_cases = [
        {"id": "D010-N1", "kind": "normal", "input": {"calculation_purpose": "reference_validation", "temperature_k": 1873, "slag_composition_mass_percent": {"CaO": 45, "MgO": 8, "P2O5": 2, "Al2O3": 3, "SiO2": 15}, "tfe_mass_percent": 20, "metal_mass_kg": 1000, "slag_mass_kg": 100, "initial_metal_p_mass_percent": 0.1}},
        {"id": "D010-N2", "kind": "normal", "input": {"calculation_purpose": "engineering_screening", "temperature_k": 1800, "slag_composition_mass_percent": {"CaO": 50, "MgO": 5, "P2O5": 1, "Al2O3": 2, "SiO2": 12}, "tfe_mass_percent": 18, "metal_mass_kg": 900, "slag_mass_kg": 90, "initial_metal_p_mass_percent": 0.08, "initial_slag_p_mass_percent": 0.2}},
        {"id": "D010-N3", "kind": "normal", "input": {"parameter_set_id": "D010_SPOONER_ISIJ_2016_V1", "calculation_purpose": "reference_validation", "temperature_k": 1950, "slag_composition_mass_percent": {"CaO": 40, "MgO": 10, "P2O5": 3, "Al2O3": 4, "SiO2": 18}, "tfe_mass_percent": 25, "metal_mass_kg": 1200, "slag_mass_kg": 120, "initial_metal_p_mass_percent": 0.12}},
        {"id": "D010-B1", "kind": "boundary", "input": {"calculation_purpose": "reference_validation", "temperature_k": 1600, "slag_composition_mass_percent": {"CaO": 45, "MgO": 8, "P2O5": 2, "Al2O3": 3, "SiO2": 15}, "tfe_mass_percent": 20, "metal_mass_kg": 1000, "slag_mass_kg": 100, "initial_metal_p_mass_percent": 0.1}},
        {"id": "D010-F1", "kind": "failure", "input": {"calculation_purpose": "reference_validation", "temperature_k": 1500, "slag_composition_mass_percent": {"CaO": 45, "MgO": 8, "P2O5": 2, "Al2O3": 3, "SiO2": 15}, "tfe_mass_percent": 20, "metal_mass_kg": 1000, "slag_mass_kg": 100, "initial_metal_p_mass_percent": 0.1}},
    ]
    data_qualification_cases = [{"id": "D010-D1", "input": qualification_cases[0]["input"]}]

    def invoke(self, params: dict, context: Optional[InvocationContext] = None) -> ModelResult:
        composition, error = _nonnegative_map(params.get("slag_composition_mass_percent"), "slag_composition_mass_percent", upper=100)
        if error:
            return _fail(error)
        assert composition is not None
        required = {"CaO", "MgO", "P2O5", "Al2O3", "SiO2"}
        missing = sorted(required - set(composition))
        if missing:
            return _fail(f"渣成分缺少: {', '.join(missing)}", "MISSING_DATA")
        if math.fsum(composition.values()) > 100 + 1e-9:
            return _fail("渣成分质量百分数之和不能超过100")
        temperature = float(params["temperature_k"])
        set_id = params.get("parameter_set_id", "D010_SPOONER_ISIJ_2016_V1")
        try:
            model, provenance = approved_parameter_set("D010", set_id, temperature)
        except RepositoryError as exc:
            return _fail(str(exc), exc.error_code)
        p = model["values"]
        required_codes = {"CAO_COEFF", "MGO_COEFF", "P2O5_COEFF", "AL2O3_COEFF", "SIO2_COEFF", "INV_T_COEFF", "INTERCEPT", "TFE_EXPONENT"}
        if set(p) != required_codes:
            return _fail("D010批准参数集字段不完整或含未认证字段", "MODEL_ARTIFACT_UNAVAILABLE")
        tfe = float(params["tfe_mass_percent"])
        log_apparent = (
            p["CAO_COEFF"] * composition["CaO"]
            + p["MGO_COEFF"] * composition["MgO"]
            + p["P2O5_COEFF"] * composition["P2O5"]
            + p["AL2O3_COEFF"] * composition["Al2O3"]
            + p["SIO2_COEFF"] * composition["SiO2"]
            + p["INV_T_COEFF"] / temperature + p["INTERCEPT"]
        )
        log_lp = log_apparent + p["TFE_EXPONENT"] * math.log10(tfe)
        if not -300 < log_lp < 300:
            return _fail("D010分配比超出稳定数值范围", "NUMERICAL_ERROR")
        lp = 10.0 ** log_lp
        metal_mass = float(params["metal_mass_kg"])
        slag_mass = float(params["slag_mass_kg"])
        total_p = (
            metal_mass * float(params["initial_metal_p_mass_percent"]) / 100.0
            + slag_mass * float(params.get("initial_slag_p_mass_percent", 0.0)) / 100.0
        )
        metal_p, slag_p, residual = _mass_balance_equilibrium(total_p, metal_mass, slag_mass, lp)
        if metal_p > 100 + 1e-9 or slag_p > 100 + 1e-9:
            return _fail("平衡P质量分数超过100%，输入超出模型物理域", "OUT_OF_DOMAIN")
        boundary = temperature in model["temperature_range_k"]
        warnings = [BoundaryWarning("calculation_purpose", "公开平衡关联只用于参考验证/工程筛选，不是BOF动力学终点或生产控制")]
        if boundary:
            warnings.append(BoundaryWarning("temperature_k", "温度位于参数集批准边界", min_allowed=model["temperature_range_k"][0], max_allowed=model["temperature_range_k"][1]))
        return ModelResult(True, result={
            "log10_apparent_partition": log_apparent,
            "phosphorus_partition_ratio": lp,
            "equilibrium_metal_p_mass_percent": metal_p,
            "equilibrium_slag_p_mass_percent": slag_p,
            "total_p_mass_kg": total_p,
            "p_mass_balance_residual_kg": residual,
            "parameter_set_id": set_id,
            "temperature_k": temperature,
            "usage_scope": model["usage_scope"],
            "assumptions": ["equilibrium partition potential", "fixed final slag composition", "closed metal-slag phosphorus balance", "not a kinetic endpoint model"],
        }, boundary_check=BoundaryCheck(False, warnings), provenance=provenance)


class D011_SulfurPartition(_P1DataProcessTool):
    model_id, name, version = "D011", "硫分配比", "1.0.0"
    tool_name = "metallurgy_predict_sulfur_partition"
    required_dataset_ids = ["DS_IUPAC_AW_2021", "DS_SLAG_S_CAPACITY_ISIJ_2013", "DS_S_DISTRIBUTION_ISIJ_2016"]
    database_tables = [ELEMENT_TABLE, PARAMETER_TABLE]
    description = "由版本化光学碱度参数计算多组元渣硫容量Cs，再结合氧活度和硫活度系数求Ls并闭合金属/渣硫质量。"
    applicable_boundary = "1773–1923 K公开平衡筛选；只支持批准的八种组分；氧活度与硫活度系数必须显式输入；不代表BOF实际动力学脱硫。"
    temperature_range = [1773.0, 1923.0]
    formula_reference = "Lambda=sum(n_i*N_O,i*Lambda_i)/sum(n_i*N_O,i); logCs=-6.08+4.49/Lambda+(15893-15864/Lambda)/T; logLs=logCs-log(aO)+log(fS)-420/T+1.14"
    source_version = "ISIJ-53-761-EQ10-TABLE2 + ISIJINT-2016-274-EQ7-8"
    source_records = [
        {"source_id": "DS_SLAG_S_CAPACITY_ISIJ_2013", "name": "Zhang-Chou-Uday sulfide capacity Eq.10/Table 2", "version": "2013", "url": "https://doi.org/10.2355/isijinternational.53.761"},
        {"source_id": "DS_S_DISTRIBUTION_ISIJ_2016", "name": "Ma et al. sulfur partition Eq.7-8", "version": "2016", "url": "https://doi.org/10.2355/isijinternational.ISIJINT-2016-274"},
    ]
    data_source = ["ISIJ多组元硫容量公开关联", "IUPAC原子量数据库"]
    failure_modes = ["未知渣组分", "氧活度或硫活度系数非正", "温度超域", "参数集/原子量缺失", "平衡S质量分数超物理范围"]
    independent_validation = ["光学碱度逐摩尔氧当量手算", "论文Eq.10和Eq.7逐项复算", "Ls与Cs和fS成正比、与aO成反比", "金属与渣S质量守恒"]
    dependencies = ["A002", "A003", "D005", "D006"]
    relations = [
        _rel("depends_on", "A002", "解析渣组分化学式"),
        _rel("depends_on", "A003", "数据库摩尔质量用于光学碱度"),
        _rel("consumes_output_from", "D005", "使用总渣量与渣组分"),
        _rel("complements", "D006", "质量基碱度与光学碱度是不同指标"),
        _rel("overlaps", "D010", "都输出渣钢分配比，但元素和理论模型不同"),
    ]
    input_fields = [
        InputField("parameter_set_id", "参数集ID", "string", required=False, default="D011_ZHANG_MA_ISIJ_V1"),
        InputField("calculation_purpose", "计算用途", "select", enum=["reference_validation", "engineering_screening"]),
        InputField("temperature_k", "温度", "number", unit="K", min_value=1e-12),
        InputField("slag_component_masses_kg", "渣组分质量", "object", unit="kg/basis", description="仅支持CaO,MgO,Al2O3,SiO2,FeO,MnO,TiO2,CaF2；至少一项大于0", json_schema={"type": "object", "properties": {component: {"type": "number", "minimum": 0} for component in ("CaO", "MgO", "Al2O3", "SiO2", "FeO", "MnO", "TiO2", "CaF2")}, "minProperties": 1, "additionalProperties": False}),
        InputField("oxygen_activity", "金属中氧活度", "number", unit="dimensionless", min_value=1e-15),
        InputField("sulfur_activity_coefficient", "金属中硫活度系数", "number", unit="dimensionless", min_value=1e-15),
        InputField("metal_mass_kg", "金属质量", "number", unit="kg/basis", min_value=1e-12),
        InputField("slag_mass_kg", "渣质量", "number", unit="kg/basis", min_value=1e-12),
        InputField("initial_metal_s_mass_percent", "初始金属S", "number", unit="mass percent", min_value=0, max_value=100),
        InputField("initial_slag_s_mass_percent", "初始渣S", "number", required=False, default=0.0, unit="mass percent", min_value=0, max_value=100),
    ]
    output_fields = [
        OutputField("optical_basicity", "光学碱度", "number", "dimensionless"),
        OutputField("log10_sulfide_capacity", "硫容量对数", "number", "dimensionless"),
        OutputField("sulfide_capacity", "硫容量Cs", "number", "dimensionless"),
        OutputField("log10_sulfur_partition_ratio", "硫分配比对数", "number", "dimensionless"),
        OutputField("sulfur_partition_ratio", "硫分配比Ls", "number", "dimensionless"),
        OutputField("equilibrium_metal_s_mass_percent", "平衡金属S", "number", "mass percent"),
        OutputField("equilibrium_slag_s_mass_percent", "平衡渣S", "number", "mass percent"),
        OutputField("total_s_mass_kg", "体系S总质量", "number", "kg/basis"),
        OutputField("s_mass_balance_residual_kg", "S守恒残差", "number", "kg/basis"),
        OutputField("component_mole_amounts_kmol", "组分千摩尔量", "object"),
        OutputField("parameter_set_id", "参数集ID", "string"),
        OutputField("temperature_k", "温度", "number", "K"),
        OutputField("usage_scope", "数据使用范围", "string"),
        OutputField("assumptions", "模型假设", "array"),
    ]
    validation_rules = [{"rule": "approved_component_set"}, {"rule": "positive", "fields": ["oxygen_activity", "sulfur_activity_coefficient"]}, {"rule": "closed_s_mass_balance"}]
    qualification_cases = [
        {"id": "D011-N1", "kind": "normal", "input": {"calculation_purpose": "reference_validation", "temperature_k": 1773, "slag_component_masses_kg": {"CaO": 45, "SiO2": 35, "Al2O3": 15, "MgO": 5}, "oxygen_activity": 0.001, "sulfur_activity_coefficient": 1.0, "metal_mass_kg": 1000, "slag_mass_kg": 100, "initial_metal_s_mass_percent": 0.05}},
        {"id": "D011-N2", "kind": "normal", "input": {"calculation_purpose": "engineering_screening", "temperature_k": 1823, "slag_component_masses_kg": {"CaO": 40, "SiO2": 25, "Al2O3": 10, "MgO": 5, "FeO": 20}, "oxygen_activity": 0.002, "sulfur_activity_coefficient": 1.2, "metal_mass_kg": 900, "slag_mass_kg": 90, "initial_metal_s_mass_percent": 0.04, "initial_slag_s_mass_percent": 0.1}},
        {"id": "D011-N3", "kind": "normal", "input": {"parameter_set_id": "D011_ZHANG_MA_ISIJ_V1", "calculation_purpose": "reference_validation", "temperature_k": 1900, "slag_component_masses_kg": {"CaO": 50, "SiO2": 20, "MnO": 10, "TiO2": 10, "CaF2": 10}, "oxygen_activity": 0.0005, "sulfur_activity_coefficient": 1.5, "metal_mass_kg": 1200, "slag_mass_kg": 120, "initial_metal_s_mass_percent": 0.06}},
        {"id": "D011-B1", "kind": "boundary", "input": {"calculation_purpose": "reference_validation", "temperature_k": 1923, "slag_component_masses_kg": {"CaO": 50, "SiO2": 50}, "oxygen_activity": 0.001, "sulfur_activity_coefficient": 1.0, "metal_mass_kg": 1000, "slag_mass_kg": 100, "initial_metal_s_mass_percent": 0.05}},
        {"id": "D011-F1", "kind": "failure", "input": {"calculation_purpose": "reference_validation", "temperature_k": 1800, "slag_component_masses_kg": {"CaO": 50, "B2O3": 50}, "oxygen_activity": 0.001, "sulfur_activity_coefficient": 1.0, "metal_mass_kg": 1000, "slag_mass_kg": 100, "initial_metal_s_mass_percent": 0.05}},
    ]
    data_qualification_cases = [{"id": "D011-D1", "input": qualification_cases[0]["input"]}]

    def invoke(self, params: dict, context: Optional[InvocationContext] = None) -> ModelResult:
        masses, error = _nonnegative_map(params.get("slag_component_masses_kg"), "slag_component_masses_kg")
        if error:
            return _fail(error)
        assert masses is not None
        temperature = float(params["temperature_k"])
        set_id = params.get("parameter_set_id", "D011_ZHANG_MA_ISIJ_V1")
        try:
            model, parameter_provenance = approved_parameter_set("D011", set_id, temperature)
        except RepositoryError as exc:
            return _fail(str(exc), exc.error_code)
        p = model["values"]
        required_codes = {"CS_INTERCEPT", "CS_INV_LAMBDA", "CS_INV_T", "CS_INV_LAMBDA_INV_T", "LOGK5_INV_T", "LOGK5_INTERCEPT"}
        optical_rows = {
            metadata.get("component_formula"): (code, p[code], metadata)
            for code, metadata in model["metadata"].items()
            if code.startswith("OPTICAL_BASICITY_")
        }
        if not required_codes.issubset(p) or len(optical_rows) != 8 or None in optical_rows:
            return _fail("D011批准参数集字段不完整", "MODEL_ARTIFACT_UNAVAILABLE")
        unknown = sorted(set(masses) - set(optical_rows))
        if unknown:
            return _fail(f"参数集不支持渣组分: {', '.join(unknown)}", "MODEL_NOT_APPLICABLE")
        formulas: dict[str, dict[str, float]] = {}
        symbols: set[str] = set()
        for formula in masses:
            composition, formula_error = parse_formula(formula)
            if formula_error:
                return _fail(f"渣组分{formula}无法解析: {formula_error}")
            assert composition is not None
            formulas[formula] = composition
            symbols.update(composition)
        try:
            weights, element_provenance = atomic_weights(symbols)
        except RepositoryError as exc:
            return _fail(str(exc), exc.error_code)
        mole_amounts: dict[str, float] = {}
        numerator = 0.0
        denominator = 0.0
        for formula, mass_kg in masses.items():
            molar_mass = math.fsum(weights[symbol] * count for symbol, count in formulas[formula].items())
            amount_kmol = mass_kg / molar_mass
            mole_amounts[formula] = amount_kmol
            _, optical_basicity, metadata = optical_rows[formula]
            oxygen_equivalent = float(metadata["oxygen_equivalent"])
            weight = amount_kmol * oxygen_equivalent
            numerator += weight * optical_basicity
            denominator += weight
        if denominator <= 0:
            return _fail("光学碱度氧当量分母必须大于0", "DIVISION_BY_ZERO")
        optical_basicity = numerator / denominator
        log_cs = (
            p["CS_INTERCEPT"] + p["CS_INV_LAMBDA"] / optical_basicity
            + (p["CS_INV_T"] + p["CS_INV_LAMBDA_INV_T"] / optical_basicity) / temperature
        )
        oxygen_activity = float(params["oxygen_activity"])
        sulfur_coefficient = float(params["sulfur_activity_coefficient"])
        log_k5 = p["LOGK5_INV_T"] / temperature + p["LOGK5_INTERCEPT"]
        log_ls = log_cs - math.log10(oxygen_activity) + math.log10(sulfur_coefficient) + log_k5
        if not (-300 < log_cs < 300 and -300 < log_ls < 300):
            return _fail("D011硫容量/分配比超出稳定数值范围", "NUMERICAL_ERROR")
        cs = 10.0 ** log_cs
        ls = 10.0 ** log_ls
        metal_mass = float(params["metal_mass_kg"])
        slag_mass = float(params["slag_mass_kg"])
        total_s = (
            metal_mass * float(params["initial_metal_s_mass_percent"]) / 100.0
            + slag_mass * float(params.get("initial_slag_s_mass_percent", 0.0)) / 100.0
        )
        metal_s, slag_s, residual = _mass_balance_equilibrium(total_s, metal_mass, slag_mass, ls)
        if metal_s > 100 + 1e-9 or slag_s > 100 + 1e-9:
            return _fail("平衡S质量分数超过100%，输入超出模型物理域", "OUT_OF_DOMAIN")
        warnings = [BoundaryWarning("calculation_purpose", "公开硫容量/平衡关联只用于参考验证或工程筛选，不是BOF动力学脱硫或生产控制")]
        if temperature in model["temperature_range_k"]:
            warnings.append(BoundaryWarning("temperature_k", "温度位于参数集批准边界", min_allowed=model["temperature_range_k"][0], max_allowed=model["temperature_range_k"][1]))
        return ModelResult(True, result={
            "optical_basicity": optical_basicity,
            "log10_sulfide_capacity": log_cs,
            "sulfide_capacity": cs,
            "log10_sulfur_partition_ratio": log_ls,
            "sulfur_partition_ratio": ls,
            "equilibrium_metal_s_mass_percent": metal_s,
            "equilibrium_slag_s_mass_percent": slag_s,
            "total_s_mass_kg": total_s,
            "s_mass_balance_residual_kg": residual,
            "component_mole_amounts_kmol": dict(sorted(mole_amounts.items())),
            "parameter_set_id": set_id,
            "temperature_k": temperature,
            "usage_scope": model["usage_scope"],
            "assumptions": ["equilibrium sulfur partition", "fixed slag composition and oxygen activity", "closed metal-slag sulfur balance", "not a kinetic BOF model"],
        }, boundary_check=BoundaryCheck(False, warnings), provenance=parameter_provenance + element_provenance)


class D012_ManganeseOxidationEquilibrium(_P1DataProcessTool):
    model_id, name, version = "D012", "锰氧化平衡", "1.0.0"
    tool_name = "metallurgy_calculate_manganese_oxidation_equilibrium"
    required_dataset_ids = ["DS_MN_EQUILIBRIUM_ISIJ_1963"]
    database_tables = [PARAMETER_TABLE]
    description = "按液态FeO–MnO标准态的版本化平衡常数，结合显式渣活度和金属Mn活度系数计算平衡残余Mn与氧化方向质量差。"
    applicable_boundary = "1823.15–1936.15 K；固定渣活度的局部平衡极限；不耦合渣量变化或动力学，禁止生产控制。"
    temperature_range = [1823.15, 1936.15]
    formula_reference = "(FeO)+[Mn]=(MnO)+[Fe]; log10K=6440/T-2.83; aMn,eq=aMnO/(K*aFeO)"
    source_version = "TETSU-49-5-756-LIQUID-v1"
    source_records = [{"source_id": "DS_MN_EQUILIBRIUM_ISIJ_1963", "name": "Gunji-Matoba Mn equilibrium", "version": "1963", "url": "https://doi.org/10.2355/tetsutohagane1955.49.5_756"}]
    data_source = ["Tetsu-to-Hagane 1963液态氧化物标准态平衡式"]
    failure_modes = ["温度超实验域", "活度/活度系数非正", "参数集缺失", "平衡残余Mn超过100%"]
    independent_validation = ["三个实验温点logK逐式复算", "aMnO/aFeO比例缩放性质", "初始Mn等于平衡Mn时驱动力和氧化量为零"]
    dependencies = ["B009", "B016", "D005"]
    relations = [
        _rel("overlaps", "B009", "B009计算通用K，本工具使用特定渣钢交换平衡数据库式"),
        _rel("depends_on", "B016", "渣活度可由更高阶溶液模型提供"),
        _rel("consumes_output_from", "D005", "MnO/FeO渣组成可用于外部活度模型"),
        _rel("overlaps", "D013", "输入粒度相似但反应计量与FeO指数不同"),
    ]
    input_fields = [
        InputField("parameter_set_id", "参数集ID", "string", required=False, default="D012_GUNJI_MATOBA_LIQUID_V1"),
        InputField("calculation_purpose", "计算用途", "select", enum=["reference_validation", "engineering_screening"]),
        InputField("temperature_k", "温度", "number", unit="K", min_value=1e-12),
        InputField("mno_activity", "渣中MnO活度", "number", unit="dimensionless", min_value=1e-15),
        InputField("feo_activity", "渣中FeO活度", "number", unit="dimensionless", min_value=1e-15),
        InputField("mn_activity_coefficient", "金属Mn活度系数", "number", unit="dimensionless", min_value=1e-15),
        InputField("initial_mn_mass_percent", "初始金属Mn", "number", unit="mass percent", min_value=1e-15, max_value=100, description="反应商采用对数形式，必须为正"),
        InputField("metal_mass_kg", "金属质量", "number", unit="kg/basis", min_value=1e-12),
    ]
    output_fields = [
        OutputField("log10_equilibrium_constant", "平衡常数对数", "number", "dimensionless"),
        OutputField("equilibrium_constant", "平衡常数", "number", "dimensionless"),
        OutputField("equilibrium_mn_activity", "平衡Mn活度", "number", "dimensionless"),
        OutputField("equilibrium_mn_mass_percent", "平衡残余Mn", "number", "mass percent"),
        OutputField("initial_mn_activity", "初始Mn活度", "number", "dimensionless"),
        OutputField("reaction_quotient", "反应商", "number", "dimensionless"),
        OutputField("log10_driving_force", "正向氧化对数驱动力", "number", "dimensionless"),
        OutputField("equilibrium_direction", "平衡趋向", "string"),
        OutputField("potential_oxidized_mn_kg", "潜在氧化Mn质量", "number", "kg/basis"),
        OutputField("parameter_set_id", "参数集ID", "string"),
        OutputField("temperature_k", "温度", "number", "K"),
        OutputField("assumptions", "模型假设", "array"),
    ]
    validation_rules = [{"rule": "positive", "fields": ["mno_activity", "feo_activity", "mn_activity_coefficient"]}, {"rule": "temperature_in_approved_domain"}]
    qualification_cases = [
        {"id": "D012-N1", "kind": "normal", "input": {"calculation_purpose": "reference_validation", "temperature_k": 1823.15, "mno_activity": 0.2, "feo_activity": 0.4, "mn_activity_coefficient": 1.0, "initial_mn_mass_percent": 0.5, "metal_mass_kg": 1000}},
        {"id": "D012-N2", "kind": "normal", "input": {"calculation_purpose": "engineering_screening", "temperature_k": 1880.15, "mno_activity": 0.1, "feo_activity": 0.3, "mn_activity_coefficient": 0.9, "initial_mn_mass_percent": 0.3, "metal_mass_kg": 900}},
        {"id": "D012-N3", "kind": "normal", "input": {"parameter_set_id": "D012_GUNJI_MATOBA_LIQUID_V1", "calculation_purpose": "reference_validation", "temperature_k": 1936.15, "mno_activity": 0.3, "feo_activity": 0.5, "mn_activity_coefficient": 1.1, "initial_mn_mass_percent": 0.8, "metal_mass_kg": 1200}},
        {"id": "D012-B1", "kind": "boundary", "input": {"calculation_purpose": "reference_validation", "temperature_k": 1936.15, "mno_activity": 0.2, "feo_activity": 0.4, "mn_activity_coefficient": 1.0, "initial_mn_mass_percent": 0.5, "metal_mass_kg": 1000}},
        {"id": "D012-F1", "kind": "failure", "input": {"calculation_purpose": "reference_validation", "temperature_k": 1800, "mno_activity": 0.2, "feo_activity": 0.4, "mn_activity_coefficient": 1.0, "initial_mn_mass_percent": 0.5, "metal_mass_kg": 1000}},
    ]
    data_qualification_cases = [{"id": "D012-D1", "input": qualification_cases[0]["input"]}]

    def invoke(self, params: dict, context: Optional[InvocationContext] = None) -> ModelResult:
        temperature = float(params["temperature_k"])
        set_id = params.get("parameter_set_id", "D012_GUNJI_MATOBA_LIQUID_V1")
        try:
            model, provenance = approved_parameter_set("D012", set_id, temperature)
        except RepositoryError as exc:
            return _fail(str(exc), exc.error_code)
        if set(model["values"]) != {"LOGK_A", "LOGK_B"}:
            return _fail("D012批准参数集字段不完整", "MODEL_ARTIFACT_UNAVAILABLE")
        p = model["values"]
        log_k = p["LOGK_A"] / temperature + p["LOGK_B"]
        k_value = 10.0 ** log_k
        mno = float(params["mno_activity"])
        feo = float(params["feo_activity"])
        coefficient = float(params["mn_activity_coefficient"])
        equilibrium_activity = mno / (k_value * feo)
        equilibrium_percent = equilibrium_activity / coefficient
        if equilibrium_percent > 100:
            return _fail("平衡Mn质量百分数超过100%，活度输入超出物理域", "OUT_OF_DOMAIN")
        initial_percent = float(params["initial_mn_mass_percent"])
        initial_activity = coefficient * initial_percent
        if initial_activity <= 0:
            return _fail("initial_mn_mass_percent必须大于0，零活度下对数反应商无定义", "MODEL_NOT_APPLICABLE")
        quotient = mno / (feo * initial_activity)
        driving = log_k - math.log10(quotient)
        if math.isclose(driving, 0.0, abs_tol=1e-12):
            direction = "at_equilibrium"
        elif driving > 0:
            direction = "mn_oxidation_favored"
        else:
            direction = "mno_reduction_favored"
        oxidized = max(0.0, initial_percent - equilibrium_percent) * float(params["metal_mass_kg"]) / 100.0
        warnings = [BoundaryWarning("calculation_purpose", "固定渣活度的公开局部平衡只用于参考/筛选，不是BOF动力学或生产控制")]
        if temperature in model["temperature_range_k"]:
            warnings.append(BoundaryWarning("temperature_k", "温度位于实验批准边界", min_allowed=model["temperature_range_k"][0], max_allowed=model["temperature_range_k"][1]))
        return ModelResult(True, result={
            "log10_equilibrium_constant": log_k,
            "equilibrium_constant": k_value,
            "equilibrium_mn_activity": equilibrium_activity,
            "equilibrium_mn_mass_percent": equilibrium_percent,
            "initial_mn_activity": initial_activity,
            "reaction_quotient": quotient,
            "log10_driving_force": driving,
            "equilibrium_direction": direction,
            "potential_oxidized_mn_kg": oxidized,
            "parameter_set_id": set_id,
            "temperature_k": temperature,
            "assumptions": ["liquid oxide standard state", "fixed FeO and MnO activities", "local equilibrium limit", "no slag-mass coupling"],
        }, boundary_check=BoundaryCheck(False, warnings), provenance=provenance)


class D013_SiliconOxidationEquilibrium(_P1DataProcessTool):
    model_id, name, version = "D013", "硅氧化平衡", "1.0.0"
    tool_name = "metallurgy_calculate_silicon_oxidation_equilibrium"
    required_dataset_ids = ["DS_SI_EQUILIBRIUM_ISIJ_2017"]
    database_tables = [PARAMETER_TABLE]
    description = "按[Si]+2(FeO)=(SiO2)+2[Fe]版本化平衡常数，结合显式渣活度和金属Si活度系数计算平衡残余Si与氧化方向质量差。"
    applicable_boundary = "1700–2000 K；来源为ESR渣钢界面平衡参考，不是企业BOF标定；固定渣活度局部平衡，禁止生产控制。"
    temperature_range = [1700.0, 2000.0]
    formula_reference = "[Si]+2(FeO)=(SiO2)+2[Fe]; log10K=18100/T-6.372; aSi,eq=aSiO2/(K*aFeO^2)"
    source_version = "ISIJINT-2017-147-EQ5-v1"
    source_records = [{"source_id": "DS_SI_EQUILIBRIUM_ISIJ_2017", "name": "Dong et al. Si oxidation equilibrium Eq.5", "version": "2017", "url": "https://doi.org/10.2355/isijinternational.ISIJINT-2017-147"}]
    data_source = ["ISIJ International 2017 Si/SiO2/FeO平衡式"]
    failure_modes = ["温度超域", "活度/活度系数非正", "参数集缺失", "平衡残余Si超过100%"]
    independent_validation = ["论文Eq.5逐项复算", "FeO活度二次指数性质", "初始Si等于平衡Si时驱动力和氧化量为零"]
    dependencies = ["B009", "B016", "D005"]
    relations = [
        _rel("overlaps", "B009", "B009计算通用K，本工具使用特定Si/FeO交换平衡数据库式"),
        _rel("depends_on", "B016", "渣活度可由更高阶溶液模型提供"),
        _rel("consumes_output_from", "D005", "SiO2/FeO渣组成可用于外部活度模型"),
        _rel("overlaps", "D012", "输入粒度相似但反应计量与FeO指数不同"),
    ]
    input_fields = [
        InputField("parameter_set_id", "参数集ID", "string", required=False, default="D013_DONG_ISIJ_2017_V1"),
        InputField("calculation_purpose", "计算用途", "select", enum=["reference_validation", "engineering_screening"]),
        InputField("temperature_k", "温度", "number", unit="K", min_value=1e-12),
        InputField("sio2_activity", "渣中SiO2活度", "number", unit="dimensionless", min_value=1e-15),
        InputField("feo_activity", "渣中FeO活度", "number", unit="dimensionless", min_value=1e-15),
        InputField("si_activity_coefficient", "金属Si活度系数", "number", unit="dimensionless", min_value=1e-15),
        InputField("initial_si_mass_percent", "初始金属Si", "number", unit="mass percent", min_value=1e-15, max_value=100, description="反应商采用对数形式，必须为正"),
        InputField("metal_mass_kg", "金属质量", "number", unit="kg/basis", min_value=1e-12),
    ]
    output_fields = [
        OutputField("log10_equilibrium_constant", "平衡常数对数", "number", "dimensionless"),
        OutputField("equilibrium_constant", "平衡常数", "number", "dimensionless"),
        OutputField("equilibrium_si_activity", "平衡Si活度", "number", "dimensionless"),
        OutputField("equilibrium_si_mass_percent", "平衡残余Si", "number", "mass percent"),
        OutputField("initial_si_activity", "初始Si活度", "number", "dimensionless"),
        OutputField("reaction_quotient", "反应商", "number", "dimensionless"),
        OutputField("log10_driving_force", "正向氧化对数驱动力", "number", "dimensionless"),
        OutputField("equilibrium_direction", "平衡趋向", "string"),
        OutputField("potential_oxidized_si_kg", "潜在氧化Si质量", "number", "kg/basis"),
        OutputField("parameter_set_id", "参数集ID", "string"),
        OutputField("temperature_k", "温度", "number", "K"),
        OutputField("assumptions", "模型假设", "array"),
    ]
    validation_rules = [{"rule": "positive", "fields": ["sio2_activity", "feo_activity", "si_activity_coefficient"]}, {"rule": "temperature_in_approved_domain"}]
    qualification_cases = [
        {"id": "D013-N1", "kind": "normal", "input": {"calculation_purpose": "reference_validation", "temperature_k": 1700, "sio2_activity": 0.2, "feo_activity": 0.4, "si_activity_coefficient": 1.0, "initial_si_mass_percent": 0.5, "metal_mass_kg": 1000}},
        {"id": "D013-N2", "kind": "normal", "input": {"calculation_purpose": "engineering_screening", "temperature_k": 1850, "sio2_activity": 0.1, "feo_activity": 0.3, "si_activity_coefficient": 0.8, "initial_si_mass_percent": 0.3, "metal_mass_kg": 900}},
        {"id": "D013-N3", "kind": "normal", "input": {"parameter_set_id": "D013_DONG_ISIJ_2017_V1", "calculation_purpose": "reference_validation", "temperature_k": 1950, "sio2_activity": 0.3, "feo_activity": 0.5, "si_activity_coefficient": 1.2, "initial_si_mass_percent": 0.8, "metal_mass_kg": 1200}},
        {"id": "D013-B1", "kind": "boundary", "input": {"calculation_purpose": "reference_validation", "temperature_k": 2000, "sio2_activity": 0.2, "feo_activity": 0.4, "si_activity_coefficient": 1.0, "initial_si_mass_percent": 0.5, "metal_mass_kg": 1000}},
        {"id": "D013-F1", "kind": "failure", "input": {"calculation_purpose": "reference_validation", "temperature_k": 2100, "sio2_activity": 0.2, "feo_activity": 0.4, "si_activity_coefficient": 1.0, "initial_si_mass_percent": 0.5, "metal_mass_kg": 1000}},
    ]
    data_qualification_cases = [{"id": "D013-D1", "input": qualification_cases[0]["input"]}]

    def invoke(self, params: dict, context: Optional[InvocationContext] = None) -> ModelResult:
        temperature = float(params["temperature_k"])
        set_id = params.get("parameter_set_id", "D013_DONG_ISIJ_2017_V1")
        try:
            model, provenance = approved_parameter_set("D013", set_id, temperature)
        except RepositoryError as exc:
            return _fail(str(exc), exc.error_code)
        if set(model["values"]) != {"LOGK_A", "LOGK_B"}:
            return _fail("D013批准参数集字段不完整", "MODEL_ARTIFACT_UNAVAILABLE")
        p = model["values"]
        log_k = p["LOGK_A"] / temperature + p["LOGK_B"]
        k_value = 10.0 ** log_k
        sio2 = float(params["sio2_activity"])
        feo = float(params["feo_activity"])
        coefficient = float(params["si_activity_coefficient"])
        equilibrium_activity = sio2 / (k_value * feo ** 2)
        equilibrium_percent = equilibrium_activity / coefficient
        if equilibrium_percent > 100:
            return _fail("平衡Si质量百分数超过100%，活度输入超出物理域", "OUT_OF_DOMAIN")
        initial_percent = float(params["initial_si_mass_percent"])
        initial_activity = coefficient * initial_percent
        if initial_activity <= 0:
            return _fail("initial_si_mass_percent必须大于0，零活度下对数反应商无定义", "MODEL_NOT_APPLICABLE")
        quotient = sio2 / (feo ** 2 * initial_activity)
        driving = log_k - math.log10(quotient)
        if math.isclose(driving, 0.0, abs_tol=1e-12):
            direction = "at_equilibrium"
        elif driving > 0:
            direction = "si_oxidation_favored"
        else:
            direction = "sio2_reduction_favored"
        oxidized = max(0.0, initial_percent - equilibrium_percent) * float(params["metal_mass_kg"]) / 100.0
        warnings = [BoundaryWarning("calculation_purpose", "ESR来源的公开局部平衡只用于参考/筛选，不是企业BOF标定或生产控制")]
        if temperature in model["temperature_range_k"]:
            warnings.append(BoundaryWarning("temperature_k", "温度位于参数集批准边界", min_allowed=model["temperature_range_k"][0], max_allowed=model["temperature_range_k"][1]))
        return ModelResult(True, result={
            "log10_equilibrium_constant": log_k,
            "equilibrium_constant": k_value,
            "equilibrium_si_activity": equilibrium_activity,
            "equilibrium_si_mass_percent": equilibrium_percent,
            "initial_si_activity": initial_activity,
            "reaction_quotient": quotient,
            "log10_driving_force": driving,
            "equilibrium_direction": direction,
            "potential_oxidized_si_kg": oxidized,
            "parameter_set_id": set_id,
            "temperature_k": temperature,
            "assumptions": ["fixed FeO and SiO2 activities", "local equilibrium limit", "ESR reference standard state", "no slag-mass coupling"],
        }, boundary_check=BoundaryCheck(False, warnings), provenance=provenance)


class D014_TFeIronLoss(_P1DataProcessTool):
    model_id, name, version = "D014", "TFe与铁损估算", "1.0.0"
    tool_name = "metallurgy_estimate_tfe_iron_loss"
    required_dataset_ids = ["DS_IUPAC_AW_2021"]
    database_tables = [ELEMENT_TABLE]
    description = "把终渣FeO、Fe2O3、Fe3O4按数据库原子量换算为化学TFe，并与金属夹带Fe分项计算总铁损、吨钢铁损、收得率和经济损失。"
    applicable_boundary = "静态终渣质量收支；组成用质量分数；化学铁损与金属夹带分开；不计算FeO活度、过程动力学或在线优化。"
    formula_reference = "m_Fe,oxide=m_slag*w_oxide*(n_Fe*A_Fe/M_oxide); total iron loss=oxidic Fe+entrained metallic Fe"
    source_version = "IUPAC-AW-2021 + P1-W7-TFE-BALANCE-v1"
    source_records = [{"source_id": "IUPAC-AW-2021", "name": "IUPAC standard atomic weights", "version": "2021 snapshot"}]
    data_source = ["IUPAC/CIAAW标准原子量2021数据库", "显式终渣组成"]
    failure_modes = ["组成含不支持铁物种", "组成和超过1", "负质量/价值", "出钢量非正", "氧化物化学式或原子量数据缺失"]
    independent_validation = ["纯FeO/Fe2O3/Fe3O4的Fe质量分数计量复算", "所有质量同比缩放时质量分数不变", "分项铁损之和等于总铁损", "收得率质量恒等"]
    dependencies = ["A002", "A003", "D005", "D021"]
    relations = [
        _rel("depends_on", "A003", "使用相同版本数据库原子量计算氧化物Fe当量"),
        _rel("consumes_output_from", "D005", "使用D005总渣量和铁组分"),
        _rel("feeds", "D021", "铁损可作为全炉物料平衡损失流股"),
        _rel("upstream_of", "D010", "氧化物TFe质量百分数可作为磷分配输入"),
    ]
    input_fields = [
        InputField("slag_mass_kg", "总渣量", "number", unit="kg/basis", min_value=1e-12),
        InputField("iron_species_mass_fractions", "含铁物种质量分数", "object", unit="mass fraction", description="允许FeO,Fe2O3,Fe3O4,Fe，和不得超过1", json_schema={"type": "object", "properties": {species: {"type": "number", "minimum": 0, "maximum": 1} for species in ("FeO", "Fe2O3", "Fe3O4", "Fe")}, "minProperties": 1, "additionalProperties": False}),
        InputField("steel_tapped_mass_kg", "出钢量", "number", unit="kg/basis", min_value=1e-12),
        InputField("iron_value_per_kg", "铁价值", "number", required=False, default=0.0, unit="currency/kg Fe", min_value=0),
        InputField("currency", "货币代码", "string", required=False, default="CNY"),
    ]
    output_fields = [
        OutputField("iron_breakdown_kg", "铁损分项", "object"),
        OutputField("oxidic_iron_mass_kg", "氧化态铁损", "number", "kg Fe/basis"),
        OutputField("metallic_iron_mass_kg", "金属夹带铁", "number", "kg Fe/basis"),
        OutputField("total_iron_loss_kg", "总铁损", "number", "kg Fe/basis"),
        OutputField("oxidic_tfe_mass_percent", "氧化物TFe", "number", "mass percent of slag"),
        OutputField("total_slag_iron_mass_percent", "含夹带总铁", "number", "mass percent of slag"),
        OutputField("iron_loss_kg_per_t_steel", "吨钢铁损", "number", "kg Fe/t steel"),
        OutputField("metal_recovery_fraction", "相对铁收得率", "number", "dimensionless"),
        OutputField("economic_loss", "经济损失", "number", "currency/basis"),
        OutputField("currency", "货币代码", "string"),
        OutputField("slag_mass_kg", "总渣量", "number", "kg/basis"),
        OutputField("steel_tapped_mass_kg", "出钢量", "number", "kg/basis"),
    ]
    validation_rules = [{"rule": "mass_fraction_sum", "max": 1.0}, {"rule": "supported_species", "values": ["FeO", "Fe2O3", "Fe3O4", "Fe"]}]
    qualification_cases = [
        {"id": "D014-N1", "kind": "normal", "input": {"slag_mass_kg": 100, "iron_species_mass_fractions": {"FeO": 0.2}, "steel_tapped_mass_kg": 1000}},
        {"id": "D014-N2", "kind": "normal", "input": {"slag_mass_kg": 120, "iron_species_mass_fractions": {"FeO": 0.1, "Fe2O3": 0.05, "Fe3O4": 0.03, "Fe": 0.01}, "steel_tapped_mass_kg": 900, "iron_value_per_kg": 2.5}},
        {"id": "D014-N3", "kind": "normal", "input": {"slag_mass_kg": 80, "iron_species_mass_fractions": {"Fe2O3": 0.15, "Fe": 0.02}, "steel_tapped_mass_kg": 1100, "iron_value_per_kg": 3, "currency": "CNY"}},
        {"id": "D014-B1", "kind": "boundary", "input": {"slag_mass_kg": 100, "iron_species_mass_fractions": {"FeO": 0, "Fe": 0}, "steel_tapped_mass_kg": 1000}},
        {"id": "D014-F1", "kind": "failure", "input": {"slag_mass_kg": 100, "iron_species_mass_fractions": {"FeO": 0.8, "Fe2O3": 0.3}, "steel_tapped_mass_kg": 1000}},
    ]
    data_qualification_cases = [{"id": "D014-D1", "input": qualification_cases[0]["input"]}]

    def invoke(self, params: dict, context: Optional[InvocationContext] = None) -> ModelResult:
        fractions, error = _nonnegative_map(
            params.get("iron_species_mass_fractions"),
            "iron_species_mass_fractions", upper=1.0, require_positive=False,
        )
        if error:
            return _fail(error)
        assert fractions is not None
        allowed = {"FeO", "Fe2O3", "Fe3O4", "Fe"}
        unknown = sorted(set(fractions) - allowed)
        if unknown:
            return _fail(f"不支持含铁物种: {', '.join(unknown)}", "MODEL_NOT_APPLICABLE")
        if math.fsum(fractions.values()) > 1 + 1e-12:
            return _fail("含铁物种质量分数之和不能超过1")
        formulas: dict[str, dict[str, float]] = {}
        symbols: set[str] = set()
        for formula in fractions:
            composition, formula_error = parse_formula(formula)
            if formula_error:
                return _fail(f"含铁物种{formula}无法解析: {formula_error}")
            assert composition is not None
            formulas[formula] = composition
            symbols.update(composition)
        try:
            weights, provenance = atomic_weights(symbols or {"Fe", "O"})
        except RepositoryError as exc:
            return _fail(str(exc), exc.error_code)
        slag_mass = float(params["slag_mass_kg"])
        breakdown: dict[str, float] = {}
        oxidic = 0.0
        metallic = 0.0
        for formula, fraction in fractions.items():
            species_mass = slag_mass * fraction
            composition = formulas[formula]
            molar_mass = math.fsum(weights[element] * count for element, count in composition.items())
            iron_fraction = composition.get("Fe", 0.0) * weights["Fe"] / molar_mass
            iron_mass = species_mass * iron_fraction
            breakdown[formula] = iron_mass
            if formula == "Fe":
                metallic += iron_mass
            else:
                oxidic += iron_mass
        total_loss = oxidic + metallic
        steel_mass = float(params["steel_tapped_mass_kg"])
        recovery = steel_mass / (steel_mass + total_loss)
        value = float(params.get("iron_value_per_kg", 0.0))
        warnings = []
        if total_loss == 0:
            warnings.append(BoundaryWarning("iron_species_mass_fractions", "输入终渣不含铁物种，TFe与铁损均为零", min_allowed=0))
        if metallic > 0:
            warnings.append(BoundaryWarning("iron_species_mass_fractions.Fe", "金属夹带与氧化态TFe已分开报告"))
        return ModelResult(True, result={
            "iron_breakdown_kg": dict(sorted(breakdown.items())),
            "oxidic_iron_mass_kg": oxidic,
            "metallic_iron_mass_kg": metallic,
            "total_iron_loss_kg": total_loss,
            "oxidic_tfe_mass_percent": 100.0 * oxidic / slag_mass,
            "total_slag_iron_mass_percent": 100.0 * total_loss / slag_mass,
            "iron_loss_kg_per_t_steel": total_loss / steel_mass * 1000.0,
            "metal_recovery_fraction": recovery,
            "economic_loss": total_loss * value,
            "currency": params.get("currency", "CNY"),
            "slag_mass_kg": slag_mass,
            "steel_tapped_mass_kg": steel_mass,
        }, boundary_check=BoundaryCheck(not warnings, warnings), provenance=provenance)
