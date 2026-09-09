"""Qualified blast-furnace material and element balances for catalog P0-W2.

All plant observations and routing assumptions are explicit inputs.  Public
process references define stream boundaries only; they are never used as
hidden plant defaults.
"""

from __future__ import annotations

import math
from typing import Dict, Iterable, Optional

from .base import BaseModelTool, BoundaryCheck, BoundaryWarning, InputField, ModelResult, OutputField
from .repositories.reference_repository import RepositoryError, atomic_weights


SCENARIO = "高炉低碳"


def rel(kind: str, target: str, description: str) -> dict:
    return {"type": kind, "target": target, "description": description}


def fail(message: str, code: str = "INVALID_INPUT") -> ModelResult:
    return ModelResult(False, error=message, error_code=code)


def finite_number(value, label: str, *, minimum: Optional[float] = None, maximum: Optional[float] = None):
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


def mass_stream_schema(categories: Iterable[str], *, fraction_field: Optional[str] = None,
                       state_field: Optional[str] = None, moisture: bool = False) -> dict:
    properties = {
        "name": {"type": "string", "minLength": 1},
        "category": {"type": "string", "enum": sorted(categories)},
        "mass_kg": {"type": "number", "minimum": 0},
    }
    required = ["name", "category", "mass_kg"]
    if fraction_field:
        properties[fraction_field] = {"type": "number", "minimum": 0, "maximum": 1}
        required.append(fraction_field)
    if state_field:
        properties[state_field] = {"type": "number", "minimum": 0, "maximum": 8}
        required.append(state_field)
    if moisture:
        properties["moisture_fraction"] = {"type": "number", "minimum": 0, "maximum": 1, "default": 0}
    return {
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }


def gas_stream_schema(species: Iterable[str]) -> dict:
    composition = {
        "type": "object",
        "properties": {
            name: {"type": "number", "minimum": 0, "maximum": 1}
            for name in sorted(species)
        },
        "minProperties": 1,
        "additionalProperties": False,
    }
    return {
        "type": "object",
        "properties": {
            "name": {"type": "string", "minLength": 1},
            "amount_kmol": {"type": "number", "minimum": 0},
            "composition": composition,
        },
        "required": ["name", "amount_kmol", "composition"],
        "additionalProperties": False,
    }


class BFFormulaTool(BaseModelTool):
    scenario = SCENARIO
    priority = "P0"
    status = "qualified"
    qualification_status = "qualified"
    count_eligible = True
    data_requirement = "FORMULA_ONLY"
    data_access_mode = "none"


class BFAtomicWeightTool(BFFormulaTool):
    data_requirement = "REFERENCE_DATA_REQUIRED"
    data_access_mode = "database_repository"
    required_dataset_ids = ["DS_IUPAC_AW_2021"]
    database_tables = ["metallurgy_v2.element_reference"]


def parse_mass_streams(raw, label: str, categories: set[str], *, fraction_field: Optional[str] = None,
                       state_field: Optional[str] = None):
    if not isinstance(raw, list) or not raw:
        return None, f"{label}必须是非空数组"
    parsed, names = [], set()
    for index, stream in enumerate(raw):
        if not isinstance(stream, dict):
            return None, f"{label}[{index}]必须是对象"
        name, category = stream.get("name"), stream.get("category")
        if not isinstance(name, str) or not name.strip() or name in names:
            return None, f"{label}[{index}].name必须是唯一非空字符串"
        if category not in categories:
            return None, f"{label}[{index}].category不受支持"
        names.add(name)
        mass, error = finite_number(stream.get("mass_kg"), f"{label}[{index}].mass_kg", minimum=0)
        if error:
            return None, error
        item = {"name": name, "category": category, "mass_kg": mass}
        if fraction_field:
            fraction, error = finite_number(stream.get(fraction_field), f"{label}[{index}].{fraction_field}", minimum=0, maximum=1)
            if error:
                return None, error
            item[fraction_field] = fraction
        if state_field:
            state, error = finite_number(stream.get(state_field), f"{label}[{index}].{state_field}", minimum=0, maximum=8)
            if error:
                return None, error
            item[state_field] = state
        parsed.append(item)
    return parsed, None


def balance_metrics(input_value: float, output_value: float, absolute: float, relative: float):
    residual = input_value - output_value
    tolerance = max(absolute, relative * max(input_value, output_value, 1.0))
    return {
        "residual": residual,
        "closure_rate": 1.0 - abs(residual) / max(input_value, output_value, 1.0),
        "passed": abs(residual) <= tolerance,
    }


class E001_BFBurdenBalance(BFFormulaTool):
    model_id, name, version = "E001", "高炉炉料总物料平衡", "1.0.0"
    tool_name = "metallurgy_balance_bf_burden"
    description = "按统一统计基准审计高炉炉料、燃料、鼓风与铁水、炉渣、煤气、粉尘的总质量闭合，并报告干料和水分分解。"
    applicable_boundary = "稳态统计期；每条物流质量为同一基准下实际质量，水分质量分数显式给出；气体体积必须先换算为质量。"
    data_source = ["Conservation of total mass", "EU Iron and Steel BREF", "worldsteel LCI process boundaries"]
    source_version = "bf-total-mass-balance-v1; EU BREF 2013; worldsteel LCI 2020"
    formula_reference = "r_m=sum(m_input)-sum(m_output); m_dry=m*(1-w); rate=m_stream/m_hot_metal*1000"
    source_records = [
        {"source_id": "MASS-CONSERVATION", "name": "Conservation of total mass", "version": "v1"},
        {"source_id": "EU-IRON-STEEL-BREF", "name": "EU Iron and Steel Production BREF", "version": "2013", "url": "https://eippcb.jrc.ec.europa.eu/reference/iron-and-steel-production"},
        {"source_id": "WORLDSTEEL-LCI-2020", "name": "worldsteel Life Cycle Inventory study", "version": "2020", "url": "https://worldsteel.org/wp-content/uploads/Life-Cycle-Inventory-study-report-2020-data-release.pdf"},
    ]
    failure_modes = ["输入输出物流为空", "物流类别不支持", "质量或水分为负", "没有正的铁水产量", "不同统计基准混用"]
    independent_validation = ["总质量残差等于输入减输出", "全部物流同比缩放时闭合率不变", "湿质量等于干质量与水分质量之和", "物流拆分合并不改变总残差"]
    dependencies = ["A005"]
    relations = [
        rel("overlaps", "A005", "A005是通用质量/元素校验，本工具增加高炉标准物流、水分和吨铁指标"),
        rel("upstream_of", "E002", "统一统计基准和铁水产量供铁平衡使用"),
        rel("upstream_of", "E003", "统一统计基准和铁水产量供碳平衡使用"),
        rel("upstream_of", "E004", "统一统计基准和物流边界供氧平衡使用"),
    ]
    input_fields = [
        InputField("basis", "统计基准", "select", enum=["per_hour", "per_day", "per_t_hot_metal"]),
        InputField("input_streams", "输入物流", "array", items=mass_stream_schema({"ore", "sinter", "pellet", "coke", "coal", "biomass", "flux", "blast", "oxygen", "steam", "other"}, moisture=True), min_items=1, description="[{name,category,mass_kg,moisture_fraction?}]"),
        InputField("output_streams", "输出物流", "array", items=mass_stream_schema({"hot_metal", "slag", "top_gas", "dust", "sludge", "water_loss", "other"}, moisture=True), min_items=1, description="同输入结构；必须包含正质量hot_metal物流"),
        InputField("absolute_tolerance_kg", "绝对容差", "number", required=False, default=1e-6, unit="kg/$basis", min_value=0),
        InputField("relative_tolerance", "相对容差", "number", required=False, default=1e-8, unit="1", min_value=0, max_value=1),
    ]
    output_fields = [
        OutputField("basis", "统计基准", "string"),
        OutputField("input_streams", "规范化输入物流", "array"),
        OutputField("output_streams", "规范化输出物流", "array"),
        OutputField("total_input_mass_kg", "总输入质量", "number", "kg/$basis"),
        OutputField("total_output_mass_kg", "总输出质量", "number", "kg/$basis"),
        OutputField("mass_residual_kg", "总质量残差", "number", "kg/$basis"),
        OutputField("mass_closure_rate", "总质量闭合率", "number", "1"),
        OutputField("total_input_dry_mass_kg", "输入干质量", "number", "kg/$basis"),
        OutputField("total_output_dry_mass_kg", "输出干质量", "number", "kg/$basis"),
        OutputField("input_moisture_kg", "输入水分质量", "number", "kg/$basis"),
        OutputField("output_moisture_kg", "输出水分质量", "number", "kg/$basis"),
        OutputField("hot_metal_mass_kg", "铁水质量", "number", "kg/$basis"),
        OutputField("slag_mass_kg", "炉渣质量", "number", "kg/$basis"),
        OutputField("top_gas_mass_kg", "炉顶煤气质量", "number", "kg/$basis"),
        OutputField("burden_mass_kg_per_t_hot_metal", "吨铁炉料量", "number", "kg/t_hot_metal"),
        OutputField("fuel_mass_kg_per_t_hot_metal", "吨铁燃料量", "number", "kg/t_hot_metal"),
        OutputField("passed", "总质量是否闭合", "boolean"),
    ]
    validation_rules = [
        {"rule": "single_common_basis", "field": "basis"},
        {"rule": "nonnegative_mass_and_moisture", "fields": ["input_streams", "output_streams"]},
        {"rule": "positive_hot_metal_output", "field": "output_streams"},
    ]
    qualification_cases = [
        {"id": "E001-N1", "kind": "normal", "input": {"basis": "per_hour", "input_streams": [{"name": "ore", "category": "ore", "mass_kg": 100}], "output_streams": [{"name": "iron", "category": "hot_metal", "mass_kg": 60}, {"name": "slag", "category": "slag", "mass_kg": 40}]}},
        {"id": "E001-N2", "kind": "normal", "input": {"basis": "per_t_hot_metal", "input_streams": [{"name": "burden", "category": "sinter", "mass_kg": 90}, {"name": "coke", "category": "coke", "mass_kg": 10}], "output_streams": [{"name": "iron", "category": "hot_metal", "mass_kg": 60}, {"name": "slag", "category": "slag", "mass_kg": 30}, {"name": "gas", "category": "top_gas", "mass_kg": 10}]}},
        {"id": "E001-N3", "kind": "normal", "input": {"basis": "per_day", "input_streams": [{"name": "wet_ore", "category": "ore", "mass_kg": 100, "moisture_fraction": 0.1}, {"name": "blast", "category": "blast", "mass_kg": 10}], "output_streams": [{"name": "iron", "category": "hot_metal", "mass_kg": 50}, {"name": "slag", "category": "slag", "mass_kg": 40}, {"name": "gas", "category": "top_gas", "mass_kg": 20}]}},
        {"id": "E001-B1", "kind": "boundary", "input": {"basis": "per_hour", "input_streams": [{"name": "ore", "category": "ore", "mass_kg": 100}], "output_streams": [{"name": "iron", "category": "hot_metal", "mass_kg": 60}, {"name": "slag", "category": "slag", "mass_kg": 30}]}},
        {"id": "E001-F1", "kind": "failure", "input": {"basis": "per_hour", "input_streams": [{"name": "ore", "category": "ore", "mass_kg": 100, "moisture_fraction": 1.1}], "output_streams": [{"name": "iron", "category": "hot_metal", "mass_kg": 60}]}},
    ]
    _INPUT_CATEGORIES = {"ore", "sinter", "pellet", "coke", "coal", "biomass", "flux", "blast", "oxygen", "steam", "other"}
    _OUTPUT_CATEGORIES = {"hot_metal", "slag", "top_gas", "dust", "sludge", "water_loss", "other"}

    @staticmethod
    def _streams(raw, label, categories):
        streams, error = parse_mass_streams(raw, label, categories)
        if error:
            return None, error
        normalized = []
        for index, (source, stream) in enumerate(zip(raw, streams)):
            moisture, error = finite_number(source.get("moisture_fraction", 0.0), f"{label}[{index}].moisture_fraction", minimum=0, maximum=1)
            if error:
                return None, error
            normalized.append({**stream, "moisture_fraction": moisture, "dry_mass_kg": stream["mass_kg"] * (1 - moisture), "moisture_mass_kg": stream["mass_kg"] * moisture})
        return normalized, None

    def invoke(self, params, context=None):
        inputs, error = self._streams(params["input_streams"], "input_streams", self._INPUT_CATEGORIES)
        if error:
            return fail(error)
        outputs, error = self._streams(params["output_streams"], "output_streams", self._OUTPUT_CATEGORIES)
        if error:
            return fail(error)
        hot_metal = math.fsum(x["mass_kg"] for x in outputs if x["category"] == "hot_metal")
        if hot_metal <= 0:
            return fail("output_streams必须包含正质量hot_metal物流", "OUT_OF_DOMAIN")
        total_input = math.fsum(x["mass_kg"] for x in inputs)
        total_output = math.fsum(x["mass_kg"] for x in outputs)
        absolute = float(params.get("absolute_tolerance_kg", 1e-6))
        relative = float(params.get("relative_tolerance", 1e-8))
        metrics = balance_metrics(total_input, total_output, absolute, relative)
        burden = math.fsum(x["mass_kg"] for x in inputs if x["category"] in {"ore", "sinter", "pellet", "flux"})
        fuel = math.fsum(x["mass_kg"] for x in inputs if x["category"] in {"coke", "coal", "biomass"})
        warnings = [] if metrics["passed"] else [BoundaryWarning("streams", "高炉总物料平衡未在声明容差内闭合")]
        return ModelResult(True, result={
            "basis": params["basis"], "input_streams": inputs, "output_streams": outputs,
            "total_input_mass_kg": total_input, "total_output_mass_kg": total_output,
            "mass_residual_kg": metrics["residual"], "mass_closure_rate": metrics["closure_rate"],
            "total_input_dry_mass_kg": math.fsum(x["dry_mass_kg"] for x in inputs),
            "total_output_dry_mass_kg": math.fsum(x["dry_mass_kg"] for x in outputs),
            "input_moisture_kg": math.fsum(x["moisture_mass_kg"] for x in inputs),
            "output_moisture_kg": math.fsum(x["moisture_mass_kg"] for x in outputs),
            "hot_metal_mass_kg": hot_metal,
            "slag_mass_kg": math.fsum(x["mass_kg"] for x in outputs if x["category"] == "slag"),
            "top_gas_mass_kg": math.fsum(x["mass_kg"] for x in outputs if x["category"] == "top_gas"),
            "burden_mass_kg_per_t_hot_metal": burden / hot_metal * 1000,
            "fuel_mass_kg_per_t_hot_metal": fuel / hot_metal * 1000,
            "passed": metrics["passed"],
        }, boundary_check=BoundaryCheck(metrics["passed"], warnings))


class E002_BFIronBalance(BFFormulaTool):
    model_id, name, version = "E002", "高炉铁元素平衡与还原度", "1.0.0"
    tool_name = "metallurgy_calc_bf_iron_balance"
    description = "根据各物流铁质量分数和显式平均氧化态计算Fe输入输出、收得率、损失及氧化态还原度。"
    applicable_boundary = "稳态统计期；每条含铁物流必须显式给Fe质量分数和平均氧化态；只给总Fe而不给价态时不计算还原度。"
    data_source = ["Conservation of iron atoms", "Explicit oxidation-state electron balance"]
    source_version = "bf-iron-balance-v1"
    formula_reference = "m_Fe=sum(m*w_Fe); R=(sum(m_Fe*z)_in-sum(m_Fe*z)_out)/sum(m_Fe*z)_in"
    source_records = [
        {"source_id": "FE-CONSERVATION", "name": "Conservation of iron atoms", "version": "v1"},
        {"source_id": "IUPAC-OS", "name": "IUPAC oxidation state definition", "version": "online", "url": "https://goldbook.iupac.org/terms/view/O04365"},
    ]
    failure_modes = ["Fe质量分数或氧化态越界", "输入氧化态当量为零导致还原度无定义", "缺少必要铁去向", "统计基准混用"]
    independent_validation = ["Fe残差等于输入Fe减输出Fe", "全部物流同比缩放时Fe收得率和还原度不变", "相同总Fe的物流拆分不改变结果", "完全由Fe3+到Fe0时还原度为1"]
    dependencies = ["A101", "E001"]
    relations = [
        rel("depends_on", "A101", "价态应先满足物种电荷/计量约束"),
        rel("depends_on", "E001", "沿用高炉统计基准和物流边界"),
        rel("overlaps", "E004", "Fe氧化态变化与氧去向相互约束"),
    ]
    input_fields = [
        InputField("basis", "统计基准", "select", enum=["per_hour", "per_day", "per_t_hot_metal"]),
        InputField("input_streams", "含铁输入物流", "array", items=mass_stream_schema({"ore", "sinter", "pellet", "scrap", "metal_addition", "other"}, fraction_field="fe_mass_fraction", state_field="fe_oxidation_state"), min_items=1, description="[{name,category,mass_kg,fe_mass_fraction,fe_oxidation_state}]"),
        InputField("output_streams", "含铁输出物流", "array", items=mass_stream_schema({"hot_metal", "slag", "dust", "sludge", "other"}, fraction_field="fe_mass_fraction", state_field="fe_oxidation_state"), min_items=1, description="同输入结构"),
        InputField("absolute_tolerance_kg", "Fe绝对容差", "number", required=False, default=1e-6, unit="kg Fe/$basis", min_value=0),
        InputField("relative_tolerance", "Fe相对容差", "number", required=False, default=1e-8, unit="1", min_value=0, max_value=1),
    ]
    output_fields = [
        OutputField("basis", "统计基准", "string"), OutputField("input_streams", "规范化输入", "array"), OutputField("output_streams", "规范化输出", "array"),
        OutputField("total_input_fe_kg", "输入Fe", "number", "kg Fe/$basis"), OutputField("total_output_fe_kg", "输出Fe", "number", "kg Fe/$basis"),
        OutputField("fe_residual_kg", "Fe残差", "number", "kg Fe/$basis"), OutputField("fe_closure_rate", "Fe闭合率", "number", "1"),
        OutputField("hot_metal_fe_kg", "铁水Fe", "number", "kg Fe/$basis"), OutputField("slag_fe_kg", "炉渣Fe", "number", "kg Fe/$basis"),
        OutputField("dust_sludge_fe_kg", "尘泥Fe", "number", "kg Fe/$basis"), OutputField("iron_yield", "Fe收得率", "number", "1"),
        OutputField("input_oxidation_equivalent_kg_valence", "输入氧化态当量", "number", "kg Fe·valence/$basis"),
        OutputField("output_oxidation_equivalent_kg_valence", "输出氧化态当量", "number", "kg Fe·valence/$basis"),
        OutputField("reduction_degree", "Fe氧化态还原度", "number", "1"), OutputField("passed", "Fe平衡和还原度是否有效", "boolean"),
    ]
    validation_rules = [{"rule": "explicit_fe_fraction_and_state", "fields": ["input_streams", "output_streams"]}, {"rule": "positive_input_oxidation_equivalent", "field": "input_streams"}]
    qualification_cases = [
        {"id": "E002-N1", "kind": "normal", "input": {"basis": "per_hour", "input_streams": [{"name": "ore_fe", "category": "ore", "mass_kg": 100, "fe_mass_fraction": 1, "fe_oxidation_state": 3}], "output_streams": [{"name": "iron", "category": "hot_metal", "mass_kg": 100, "fe_mass_fraction": 1, "fe_oxidation_state": 0}]}},
        {"id": "E002-N2", "kind": "normal", "input": {"basis": "per_t_hot_metal", "input_streams": [{"name": "ore", "category": "ore", "mass_kg": 100, "fe_mass_fraction": 0.7, "fe_oxidation_state": 3}], "output_streams": [{"name": "iron", "category": "hot_metal", "mass_kg": 68, "fe_mass_fraction": 1, "fe_oxidation_state": 0}, {"name": "slag", "category": "slag", "mass_kg": 10, "fe_mass_fraction": 0.2, "fe_oxidation_state": 2}]}},
        {"id": "E002-N3", "kind": "normal", "input": {"basis": "per_day", "input_streams": [{"name": "fe2", "category": "sinter", "mass_kg": 50, "fe_mass_fraction": 1, "fe_oxidation_state": 2}, {"name": "fe3", "category": "pellet", "mass_kg": 50, "fe_mass_fraction": 1, "fe_oxidation_state": 3}], "output_streams": [{"name": "iron", "category": "hot_metal", "mass_kg": 100, "fe_mass_fraction": 1, "fe_oxidation_state": 0}]}},
        {"id": "E002-B1", "kind": "boundary", "input": {"basis": "per_hour", "input_streams": [{"name": "ore", "category": "ore", "mass_kg": 100, "fe_mass_fraction": 1, "fe_oxidation_state": 3}], "output_streams": [{"name": "iron", "category": "hot_metal", "mass_kg": 90, "fe_mass_fraction": 1, "fe_oxidation_state": 0}]}},
        {"id": "E002-F1", "kind": "failure", "input": {"basis": "per_hour", "input_streams": [{"name": "scrap", "category": "scrap", "mass_kg": 100, "fe_mass_fraction": 1, "fe_oxidation_state": 0}], "output_streams": [{"name": "iron", "category": "hot_metal", "mass_kg": 100, "fe_mass_fraction": 1, "fe_oxidation_state": 0}]}},
    ]
    _INPUT_CATEGORIES = {"ore", "sinter", "pellet", "scrap", "metal_addition", "other"}
    _OUTPUT_CATEGORIES = {"hot_metal", "slag", "dust", "sludge", "other"}

    def invoke(self, params, context=None):
        inputs, error = parse_mass_streams(params["input_streams"], "input_streams", self._INPUT_CATEGORIES, fraction_field="fe_mass_fraction", state_field="fe_oxidation_state")
        if error:
            return fail(error)
        outputs, error = parse_mass_streams(params["output_streams"], "output_streams", self._OUTPUT_CATEGORIES, fraction_field="fe_mass_fraction", state_field="fe_oxidation_state")
        if error:
            return fail(error)
        for stream in inputs + outputs:
            stream["fe_mass_kg"] = stream["mass_kg"] * stream["fe_mass_fraction"]
            stream["oxidation_equivalent_kg_valence"] = stream["fe_mass_kg"] * stream["fe_oxidation_state"]
        input_fe = math.fsum(x["fe_mass_kg"] for x in inputs)
        output_fe = math.fsum(x["fe_mass_kg"] for x in outputs)
        input_equiv = math.fsum(x["oxidation_equivalent_kg_valence"] for x in inputs)
        output_equiv = math.fsum(x["oxidation_equivalent_kg_valence"] for x in outputs)
        if input_fe <= 0 or input_equiv <= 0:
            return fail("输入Fe及其正氧化态当量必须大于0；金属废钢单独输入不能定义矿石还原度", "OUT_OF_DOMAIN")
        absolute = float(params.get("absolute_tolerance_kg", 1e-6))
        relative = float(params.get("relative_tolerance", 1e-8))
        metrics = balance_metrics(input_fe, output_fe, absolute, relative)
        reduction = (input_equiv - output_equiv) / input_equiv
        valid_reduction = -1e-12 <= reduction <= 1 + 1e-12
        passed = metrics["passed"] and valid_reduction
        warnings = [] if passed else [BoundaryWarning("iron_streams", "Fe平衡未闭合或氧化态还原度超出[0,1]")]
        hot_metal = math.fsum(x["fe_mass_kg"] for x in outputs if x["category"] == "hot_metal")
        return ModelResult(True, result={
            "basis": params["basis"], "input_streams": inputs, "output_streams": outputs,
            "total_input_fe_kg": input_fe, "total_output_fe_kg": output_fe,
            "fe_residual_kg": metrics["residual"], "fe_closure_rate": metrics["closure_rate"],
            "hot_metal_fe_kg": hot_metal,
            "slag_fe_kg": math.fsum(x["fe_mass_kg"] for x in outputs if x["category"] == "slag"),
            "dust_sludge_fe_kg": math.fsum(x["fe_mass_kg"] for x in outputs if x["category"] in {"dust", "sludge"}),
            "iron_yield": hot_metal / input_fe,
            "input_oxidation_equivalent_kg_valence": input_equiv,
            "output_oxidation_equivalent_kg_valence": output_equiv,
            "reduction_degree": min(1.0, max(0.0, reduction)) if valid_reduction else reduction,
            "passed": passed,
        }, boundary_check=BoundaryCheck(passed, warnings))


def parse_carbon_oxygen_materials(raw, label, categories, fraction_field):
    if raw is None:
        return [], None
    return parse_mass_streams(raw, label, categories, fraction_field=fraction_field)


def parse_gas_streams(raw, label: str, allowed_species: Dict[str, int]):
    if raw is None:
        return [], None
    if not isinstance(raw, list):
        return None, f"{label}必须是数组"
    parsed, names = [], set()
    for index, stream in enumerate(raw):
        if not isinstance(stream, dict):
            return None, f"{label}[{index}]必须是对象"
        name = stream.get("name")
        if not isinstance(name, str) or not name.strip() or name in names:
            return None, f"{label}[{index}].name必须是唯一非空字符串"
        names.add(name)
        amount, error = finite_number(stream.get("amount_kmol"), f"{label}[{index}].amount_kmol", minimum=0)
        if error:
            return None, error
        composition = stream.get("composition")
        if not isinstance(composition, dict) or not composition:
            return None, f"{label}[{index}].composition必须是非空对象"
        normalized = {}
        for species, raw_fraction in composition.items():
            if species not in allowed_species:
                return None, f"{label}[{index}]包含未支持气体物种{species}"
            fraction, error = finite_number(raw_fraction, f"{label}[{index}].composition.{species}", minimum=0, maximum=1)
            if error:
                return None, error
            normalized[species] = fraction
        if math.fsum(normalized.values()) > 1 + 1e-12:
            return None, f"{label}[{index}]气体摩尔分数之和不能超过1"
        parsed.append({"name": name, "amount_kmol": amount, "composition": normalized})
    return parsed, None


class E003_BFCarbonBalance(BFAtomicWeightTool):
    model_id, name, version = "E003", "高炉碳平衡", "1.0.0"
    tool_name = "metallurgy_calc_bf_carbon_balance"
    description = "平衡焦炭、煤等物料碳与铁水、尘渣及CO/CO2/CH4气体碳，返回吨铁碳耗和炉顶煤气碳去向。"
    applicable_boundary = "稳态统计期；固液物流用质量和C质量分数，气体用kmol和摩尔分数；不接受未声明温压基准的体积值。"
    data_source = ["Conservation of carbon atoms", "IUPAC atomic weights 2021", "worldsteel blast-furnace process boundary"]
    source_version = "bf-carbon-balance-v1; IUPAC atomic-weights-2021"
    formula_reference = "m_C,material=sum(m*w_C); m_C,gas=sum(n*x*nu_C*M_C); rate=m_C,input/m_hot_metal*1000"
    source_records = [
        {"source_id": "C-CONSERVATION", "name": "Conservation of carbon atoms", "version": "v1"},
        {"source_id": "IUPAC-AW-2021", "name": "IUPAC standard atomic weights", "version": "2021 snapshot"},
    ]
    failure_modes = ["C质量分数或气体摩尔分数越界", "气体使用体积但未先换算为kmol", "铁水产量不为正", "数据库缺少C原子量", "碳去向不完整"]
    independent_validation = ["C残差等于物料与气体逐项C原子质量差", "1 kmol CO/CO2/CH4均含1 kmol C", "整体缩放时闭合率和吨铁比不变", "观察物流拆分不改变总碳"]
    dependencies = ["A003", "E001"]
    relations = [rel("uses_data_of", "A003", "使用相同IUPAC原子量数据库版本"), rel("depends_on", "E001", "沿用统计基准和铁水产量"), rel("overlaps", "E004", "CO/CO2同时参与碳和氧平衡")]
    input_fields = [
        InputField("basis", "统计基准", "select", enum=["per_hour", "per_day", "per_t_hot_metal"]),
        InputField("material_inputs", "含碳输入物料", "array", required=False, items=mass_stream_schema({"coke", "coal", "biomass", "gas_fuel", "flux", "other"}, fraction_field="carbon_mass_fraction"), min_items=1, description="[{name,category,mass_kg,carbon_mass_fraction}]"),
        InputField("material_outputs", "含碳输出物料", "array", required=False, items=mass_stream_schema({"hot_metal", "dust", "slag", "sludge", "other"}, fraction_field="carbon_mass_fraction"), min_items=1, description="铁水/尘/渣等"),
        InputField("gas_outputs", "含碳气体输出", "array", required=False, items=gas_stream_schema({"CO", "CO2", "CH4"}), min_items=1, description="[{name,amount_kmol,composition:{CO,CO2,CH4}}]"),
        InputField("hot_metal_mass_kg", "铁水产量", "number", unit="kg/$basis", min_value=1e-12),
        InputField("absolute_tolerance_kg", "C绝对容差", "number", required=False, default=1e-6, unit="kg C/$basis", min_value=0),
        InputField("relative_tolerance", "C相对容差", "number", required=False, default=1e-8, unit="1", min_value=0, max_value=1),
    ]
    output_fields = [
        OutputField("basis", "统计基准", "string"), OutputField("material_inputs", "规范化输入物料", "array"), OutputField("material_outputs", "规范化输出物料", "array"), OutputField("gas_outputs", "规范化气体输出", "array"),
        OutputField("gas_carbon_breakdown", "气体碳分解", "object"), OutputField("total_input_carbon_kg", "输入碳", "number", "kg C/$basis"), OutputField("total_output_carbon_kg", "输出碳", "number", "kg C/$basis"),
        OutputField("carbon_residual_kg", "碳残差", "number", "kg C/$basis"), OutputField("carbon_closure_rate", "碳闭合率", "number", "1"),
        OutputField("hot_metal_carbon_kg", "铁水碳", "number", "kg C/$basis"), OutputField("dust_slag_carbon_kg", "尘渣碳", "number", "kg C/$basis"), OutputField("top_gas_carbon_kg", "煤气碳", "number", "kg C/$basis"),
        OutputField("carbon_input_kg_per_t_hot_metal", "吨铁碳输入", "number", "kg C/t_hot_metal"), OutputField("fuel_mass_kg_per_t_hot_metal", "吨铁燃料质量", "number", "kg/t_hot_metal"),
        OutputField("top_gas_co_to_co2_molar_ratio", "煤气CO/CO2摩尔比", "number", "1"), OutputField("passed", "碳是否闭合", "boolean"),
    ]
    validation_rules = [{"rule": "mass_fraction_material_carbon", "fields": ["material_inputs", "material_outputs"]}, {"rule": "kmol_mole_fraction_gas", "field": "gas_outputs"}, {"rule": "positive_hot_metal_mass", "field": "hot_metal_mass_kg"}]
    qualification_cases = [
        {"id": "E003-N1", "kind": "normal", "input": {"basis": "per_hour", "material_inputs": [{"name": "coke", "category": "coke", "mass_kg": 12.011, "carbon_mass_fraction": 1}], "gas_outputs": [{"name": "gas", "amount_kmol": 1, "composition": {"CO": 1}}], "hot_metal_mass_kg": 1000}},
        {"id": "E003-N2", "kind": "normal", "input": {"basis": "per_t_hot_metal", "material_inputs": [{"name": "fuel", "category": "coal", "mass_kg": 24.022, "carbon_mass_fraction": 1}], "material_outputs": [{"name": "iron_c", "category": "hot_metal", "mass_kg": 100, "carbon_mass_fraction": 0.12011}], "gas_outputs": [{"name": "gas", "amount_kmol": 1, "composition": {"CO2": 1}}], "hot_metal_mass_kg": 1000}},
        {"id": "E003-N3", "kind": "normal", "input": {"basis": "per_day", "material_inputs": [{"name": "fuel", "category": "coke", "mass_kg": 36.033, "carbon_mass_fraction": 1}], "material_outputs": [{"name": "dust", "category": "dust", "mass_kg": 12.011, "carbon_mass_fraction": 1}], "gas_outputs": [{"name": "gas", "amount_kmol": 2, "composition": {"CO": 0.5, "CO2": 0.5}}], "hot_metal_mass_kg": 2000}},
        {"id": "E003-B1", "kind": "boundary", "input": {"basis": "per_hour", "material_inputs": [{"name": "coke", "category": "coke", "mass_kg": 12.011, "carbon_mass_fraction": 1}], "hot_metal_mass_kg": 1000}},
        {"id": "E003-F1", "kind": "failure", "input": {"basis": "per_hour", "material_inputs": [{"name": "coke", "category": "coke", "mass_kg": 12.011, "carbon_mass_fraction": 1}], "gas_outputs": [{"name": "bad", "amount_kmol": 1, "composition": {"CO": 0.8, "CO2": 0.8}}], "hot_metal_mass_kg": 1000}},
    ]
    data_qualification_cases = [{"id": "E003-D1", "input": {"basis": "per_hour", "material_inputs": [{"name": "coke", "category": "coke", "mass_kg": 12.011, "carbon_mass_fraction": 1}], "gas_outputs": [{"name": "gas", "amount_kmol": 1, "composition": {"CO": 1}}], "hot_metal_mass_kg": 1000}}]
    _INPUT_CATEGORIES = {"coke", "coal", "biomass", "gas_fuel", "flux", "other"}
    _OUTPUT_CATEGORIES = {"hot_metal", "dust", "slag", "sludge", "other"}
    _GAS_SPECIES = {"CO": 1, "CO2": 1, "CH4": 1}

    def invoke(self, params, context=None):
        inputs, error = parse_carbon_oxygen_materials(params.get("material_inputs"), "material_inputs", self._INPUT_CATEGORIES, "carbon_mass_fraction")
        if error:
            return fail(error)
        outputs, error = parse_carbon_oxygen_materials(params.get("material_outputs"), "material_outputs", self._OUTPUT_CATEGORIES, "carbon_mass_fraction")
        if error:
            return fail(error)
        gases, error = parse_gas_streams(params.get("gas_outputs"), "gas_outputs", self._GAS_SPECIES)
        if error:
            return fail(error)
        if not inputs:
            return fail("material_inputs至少需要一个含碳输入物流")
        try:
            weights, provenance = atomic_weights({"C"})
        except RepositoryError as exc:
            return fail(str(exc), exc.error_code)
        carbon_weight = weights["C"]
        for stream in inputs + outputs:
            stream["carbon_mass_kg"] = stream["mass_kg"] * stream["carbon_mass_fraction"]
        gas_breakdown, gas_carbon, co, co2 = {}, 0.0, 0.0, 0.0
        for gas in gases:
            species_result = {}
            for species, fraction in gas["composition"].items():
                species_kmol = gas["amount_kmol"] * fraction
                carbon_kg = species_kmol * self._GAS_SPECIES[species] * carbon_weight
                species_result[species] = {"species_kmol": species_kmol, "carbon_kg": carbon_kg}
                gas_carbon += carbon_kg
                if species == "CO": co += species_kmol
                if species == "CO2": co2 += species_kmol
            gas_breakdown[gas["name"]] = species_result
        input_carbon = math.fsum(x["carbon_mass_kg"] for x in inputs)
        material_output_carbon = math.fsum(x["carbon_mass_kg"] for x in outputs)
        total_output = material_output_carbon + gas_carbon
        absolute = float(params.get("absolute_tolerance_kg", 1e-6)); relative = float(params.get("relative_tolerance", 1e-8))
        metrics = balance_metrics(input_carbon, total_output, absolute, relative)
        hot_mass = float(params["hot_metal_mass_kg"])
        warnings = [] if metrics["passed"] else [BoundaryWarning("carbon_streams", "高炉碳平衡未在声明容差内闭合")]
        return ModelResult(True, result={
            "basis": params["basis"], "material_inputs": inputs, "material_outputs": outputs, "gas_outputs": gases, "gas_carbon_breakdown": gas_breakdown,
            "total_input_carbon_kg": input_carbon, "total_output_carbon_kg": total_output,
            "carbon_residual_kg": metrics["residual"], "carbon_closure_rate": metrics["closure_rate"],
            "hot_metal_carbon_kg": math.fsum(x["carbon_mass_kg"] for x in outputs if x["category"] == "hot_metal"),
            "dust_slag_carbon_kg": math.fsum(x["carbon_mass_kg"] for x in outputs if x["category"] in {"dust", "slag", "sludge"}),
            "top_gas_carbon_kg": gas_carbon,
            "carbon_input_kg_per_t_hot_metal": input_carbon / hot_mass * 1000,
            "fuel_mass_kg_per_t_hot_metal": math.fsum(x["mass_kg"] for x in inputs if x["category"] in {"coke", "coal", "biomass", "gas_fuel"}) / hot_mass * 1000,
            "top_gas_co_to_co2_molar_ratio": co / co2 if co2 > 0 else 0.0,
            "passed": metrics["passed"],
        }, boundary_check=BoundaryCheck(metrics["passed"], warnings), provenance=provenance)


class E004_BFOxygenBalance(BFAtomicWeightTool):
    model_id, name, version = "E004", "高炉氧平衡", "1.0.0"
    tool_name = "metallurgy_calc_bf_oxygen_balance"
    description = "平衡矿石、鼓风等物料氧与渣尘及CO/CO2/H2O/O2气体氧，并基于显式分配计算直接/间接还原氧比例。"
    applicable_boundary = "稳态统计期；固液物流用O质量分数，气体用kmol和摩尔分数；还原氧总量及其中间接还原部分必须显式给出。"
    data_source = ["Conservation of oxygen atoms", "IUPAC atomic weights 2021", "Explicit direct/indirect reduction allocation"]
    source_version = "bf-oxygen-balance-v1; IUPAC atomic-weights-2021"
    formula_reference = "m_O,gas=sum(n*x*nu_O*M_O); direct_O=reduced_ore_O-indirect_O; r_O=input-output"
    source_records = [{"source_id": "O-CONSERVATION", "name": "Conservation of oxygen atoms", "version": "v1"}, {"source_id": "IUPAC-AW-2021", "name": "IUPAC standard atomic weights", "version": "2021 snapshot"}]
    failure_modes = ["O质量分数或气体摩尔分数越界", "还原氧超过矿石结合氧", "间接还原氧超过总还原氧", "数据库缺少O原子量", "气体体积未先换算为kmol"]
    independent_validation = ["O残差由每条物流O原子质量直接复算", "1 kmol CO/CO2/H2O/O2分别含1/2/1/2 kmol O", "直接与间接还原氧之和等于显式总还原氧", "整体缩放保持比例不变"]
    dependencies = ["A003", "E001", "E002", "E003"]
    relations = [rel("uses_data_of", "A003", "使用相同IUPAC原子量数据库版本"), rel("depends_on", "E001", "沿用高炉统计基准和物流边界"), rel("overlaps", "E002", "Fe氧化态变化约束矿石结合氧去向"), rel("overlaps", "E003", "CO/CO2同时参与碳和氧平衡")]
    input_fields = [
        InputField("basis", "统计基准", "select", enum=["per_hour", "per_day", "per_t_hot_metal"]),
        InputField("material_inputs", "含氧输入物料", "array", items=mass_stream_schema({"ore", "sinter", "pellet", "blast", "oxygen", "steam", "fuel", "flux", "other"}, fraction_field="oxygen_mass_fraction"), min_items=1, description="[{name,category,mass_kg,oxygen_mass_fraction}]"),
        InputField("material_outputs", "含氧输出物料", "array", required=False, items=mass_stream_schema({"hot_metal", "slag", "dust", "sludge", "water", "other"}, fraction_field="oxygen_mass_fraction"), min_items=1),
        InputField("gas_outputs", "含氧气体输出", "array", required=False, items=gas_stream_schema({"CO", "CO2", "H2O", "O2"}), min_items=1, description="[{name,amount_kmol,composition:{CO,CO2,H2O,O2}}]"),
        InputField("reduced_ore_oxygen_kg", "被还原矿石氧", "number", unit="kg O/$basis", min_value=0),
        InputField("indirect_reduction_oxygen_kg", "间接还原氧", "number", unit="kg O/$basis", min_value=0),
        InputField("absolute_tolerance_kg", "O绝对容差", "number", required=False, default=1e-6, unit="kg O/$basis", min_value=0),
        InputField("relative_tolerance", "O相对容差", "number", required=False, default=1e-8, unit="1", min_value=0, max_value=1),
    ]
    output_fields = [
        OutputField("basis", "统计基准", "string"), OutputField("material_inputs", "规范化输入", "array"), OutputField("material_outputs", "规范化输出", "array"), OutputField("gas_outputs", "规范化气体输出", "array"),
        OutputField("gas_oxygen_breakdown", "气体氧分解", "object"), OutputField("total_input_oxygen_kg", "输入氧", "number", "kg O/$basis"), OutputField("total_output_oxygen_kg", "输出氧", "number", "kg O/$basis"),
        OutputField("oxygen_residual_kg", "氧残差", "number", "kg O/$basis"), OutputField("oxygen_closure_rate", "氧闭合率", "number", "1"),
        OutputField("ore_bound_oxygen_input_kg", "矿石结合氧输入", "number", "kg O/$basis"), OutputField("reduced_ore_oxygen_kg", "被还原矿石氧", "number", "kg O/$basis"),
        OutputField("indirect_reduction_oxygen_kg", "间接还原氧", "number", "kg O/$basis"), OutputField("direct_reduction_oxygen_kg", "直接还原氧", "number", "kg O/$basis"),
        OutputField("indirect_reduction_fraction", "间接还原比例", "number", "1"), OutputField("passed", "氧平衡和分配是否有效", "boolean"),
    ]
    validation_rules = [{"rule": "mass_fraction_material_oxygen", "fields": ["material_inputs", "material_outputs"]}, {"rule": "kmol_mole_fraction_gas", "field": "gas_outputs"}, {"rule": "indirect_not_exceed_reduced_not_exceed_ore", "fields": ["reduced_ore_oxygen_kg", "indirect_reduction_oxygen_kg"]}]
    qualification_cases = [
        {"id": "E004-N1", "kind": "normal", "input": {"basis": "per_hour", "material_inputs": [{"name": "ore_o", "category": "ore", "mass_kg": 15.999, "oxygen_mass_fraction": 1}, {"name": "blast_o", "category": "blast", "mass_kg": 15.999, "oxygen_mass_fraction": 1}], "gas_outputs": [{"name": "gas", "amount_kmol": 1, "composition": {"O2": 1}}], "reduced_ore_oxygen_kg": 15.999, "indirect_reduction_oxygen_kg": 10}},
        {"id": "E004-N2", "kind": "normal", "input": {"basis": "per_t_hot_metal", "material_inputs": [{"name": "ore_o", "category": "ore", "mass_kg": 31.998, "oxygen_mass_fraction": 1}], "gas_outputs": [{"name": "gas", "amount_kmol": 1, "composition": {"CO2": 1}}], "reduced_ore_oxygen_kg": 31.998, "indirect_reduction_oxygen_kg": 20}},
        {"id": "E004-N3", "kind": "normal", "input": {"basis": "per_day", "material_inputs": [{"name": "ore_o", "category": "ore", "mass_kg": 15.999, "oxygen_mass_fraction": 1}, {"name": "steam_o", "category": "steam", "mass_kg": 15.999, "oxygen_mass_fraction": 1}], "gas_outputs": [{"name": "gas", "amount_kmol": 2, "composition": {"CO": 0.5, "H2O": 0.5}}], "reduced_ore_oxygen_kg": 15.999, "indirect_reduction_oxygen_kg": 5}},
        {"id": "E004-B1", "kind": "boundary", "input": {"basis": "per_hour", "material_inputs": [{"name": "ore_o", "category": "ore", "mass_kg": 15.999, "oxygen_mass_fraction": 1}, {"name": "blast_o", "category": "blast", "mass_kg": 15.999, "oxygen_mass_fraction": 1}], "gas_outputs": [{"name": "gas", "amount_kmol": 1, "composition": {"CO": 1}}], "reduced_ore_oxygen_kg": 15.999, "indirect_reduction_oxygen_kg": 10}},
        {"id": "E004-F1", "kind": "failure", "input": {"basis": "per_hour", "material_inputs": [{"name": "ore_o", "category": "ore", "mass_kg": 15.999, "oxygen_mass_fraction": 1}], "reduced_ore_oxygen_kg": 10, "indirect_reduction_oxygen_kg": 12}},
    ]
    data_qualification_cases = [{"id": "E004-D1", "input": {"basis": "per_hour", "material_inputs": [{"name": "ore_o", "category": "ore", "mass_kg": 15.999, "oxygen_mass_fraction": 1}, {"name": "blast_o", "category": "blast", "mass_kg": 15.999, "oxygen_mass_fraction": 1}], "gas_outputs": [{"name": "gas", "amount_kmol": 1, "composition": {"O2": 1}}], "reduced_ore_oxygen_kg": 15.999, "indirect_reduction_oxygen_kg": 10}}]
    _INPUT_CATEGORIES = {"ore", "sinter", "pellet", "blast", "oxygen", "steam", "fuel", "flux", "other"}
    _OUTPUT_CATEGORIES = {"hot_metal", "slag", "dust", "sludge", "water", "other"}
    _GAS_SPECIES = {"CO": 1, "CO2": 2, "H2O": 1, "O2": 2}

    def invoke(self, params, context=None):
        inputs, error = parse_carbon_oxygen_materials(params.get("material_inputs"), "material_inputs", self._INPUT_CATEGORIES, "oxygen_mass_fraction")
        if error:
            return fail(error)
        outputs, error = parse_carbon_oxygen_materials(params.get("material_outputs"), "material_outputs", self._OUTPUT_CATEGORIES, "oxygen_mass_fraction")
        if error:
            return fail(error)
        gases, error = parse_gas_streams(params.get("gas_outputs"), "gas_outputs", self._GAS_SPECIES)
        if error:
            return fail(error)
        try:
            weights, provenance = atomic_weights({"O"})
        except RepositoryError as exc:
            return fail(str(exc), exc.error_code)
        oxygen_weight = weights["O"]
        for stream in inputs + outputs:
            stream["oxygen_mass_kg"] = stream["mass_kg"] * stream["oxygen_mass_fraction"]
        gas_breakdown, gas_oxygen = {}, 0.0
        for gas in gases:
            species_result = {}
            for species, fraction in gas["composition"].items():
                species_kmol = gas["amount_kmol"] * fraction
                oxygen_kg = species_kmol * self._GAS_SPECIES[species] * oxygen_weight
                species_result[species] = {"species_kmol": species_kmol, "oxygen_kg": oxygen_kg}
                gas_oxygen += oxygen_kg
            gas_breakdown[gas["name"]] = species_result
        input_oxygen = math.fsum(x["oxygen_mass_kg"] for x in inputs)
        total_output = math.fsum(x["oxygen_mass_kg"] for x in outputs) + gas_oxygen
        ore_oxygen = math.fsum(x["oxygen_mass_kg"] for x in inputs if x["category"] in {"ore", "sinter", "pellet"})
        reduced = float(params["reduced_ore_oxygen_kg"]); indirect = float(params["indirect_reduction_oxygen_kg"])
        if reduced > ore_oxygen + 1e-9:
            return fail("reduced_ore_oxygen_kg不能超过矿石/烧结/球团结合氧输入", "OUT_OF_DOMAIN")
        if indirect > reduced + 1e-9:
            return fail("indirect_reduction_oxygen_kg不能超过总被还原矿石氧", "OUT_OF_DOMAIN")
        absolute = float(params.get("absolute_tolerance_kg", 1e-6)); relative = float(params.get("relative_tolerance", 1e-8))
        metrics = balance_metrics(input_oxygen, total_output, absolute, relative)
        warnings = [] if metrics["passed"] else [BoundaryWarning("oxygen_streams", "高炉氧平衡未在声明容差内闭合")]
        return ModelResult(True, result={
            "basis": params["basis"], "material_inputs": inputs, "material_outputs": outputs, "gas_outputs": gases, "gas_oxygen_breakdown": gas_breakdown,
            "total_input_oxygen_kg": input_oxygen, "total_output_oxygen_kg": total_output,
            "oxygen_residual_kg": metrics["residual"], "oxygen_closure_rate": metrics["closure_rate"],
            "ore_bound_oxygen_input_kg": ore_oxygen, "reduced_ore_oxygen_kg": reduced,
            "indirect_reduction_oxygen_kg": indirect, "direct_reduction_oxygen_kg": reduced - indirect,
            "indirect_reduction_fraction": indirect / reduced if reduced > 0 else 0.0,
            "passed": metrics["passed"],
        }, boundary_check=BoundaryCheck(metrics["passed"], warnings), provenance=provenance)
