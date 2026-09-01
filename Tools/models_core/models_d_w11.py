"""P1-W11 additive BOF iron-accounting tool; all existing implementations stay frozen."""

from __future__ import annotations

import math
from typing import Any, Optional

from .base import BaseModelTool, BoundaryCheck, BoundaryWarning, InputField, ModelResult, OutputField


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


_CHARGE_STREAM_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "name": {"type": "string"},
        "mass_kg": {"type": "number", "exclusiveMinimum": 0},
        "iron_mass_fraction": {"type": "number", "minimum": 0, "maximum": 1},
    },
    "required": ["name", "mass_kg", "iron_mass_fraction"],
}


_LOSS_STREAM_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "name": {"type": "string"},
        "category": {"type": "string", "enum": ["slag_oxidation", "dust", "splash", "skull", "other"]},
        "mass_kg": {"type": "number", "exclusiveMinimum": 0},
        "iron_mass_fraction": {"type": "number", "minimum": 0, "maximum": 1},
    },
    "required": ["name", "category", "mass_kg", "iron_mass_fraction"],
}


class D022_SteelYieldIronLossDecomposition(BaseModelTool):
    model_id, name, version = "D022", "钢水收得率与铁损分解", "1.0.0"
    scenario, priority = "冶金工艺与物料衡算", "P1"
    tool_name = "metallurgy_calculate_steel_yield_iron_loss"
    status = qualification_status = "qualified"
    count_eligible = True
    data_requirement = "FORMULA_ONLY"
    data_access_mode = "none"
    description = "按同一炉次边界内的铁源、钢水和分项损失物流，计算钢水质量收得率、铁回收率、损失构成和未计量铁。"
    applicable_boundary = (
        "单炉静态物料衡算；所有质量和铁质量分数由调用方显式提供并使用同一批次边界。"
        "允许存在非负未计量铁，不推断损失去向，不读取生产数据库。"
    )
    data_source = ["Explicit charge, steel and loss streams", "Elemental iron mass conservation"]
    source_version = "bof-iron-accounting-balance-v1"
    formula_reference = (
        "Fe_in=sum(m_i*wFe_i); Fe_steel=m_steel*wFe_steel; Fe_loss=sum(m_j*wFe_j); "
        "Fe_unaccounted=Fe_in-Fe_steel-Fe_loss; iron_recovery=Fe_steel/Fe_in; steel_yield=m_steel/sum(m_charge)"
    )
    source_records = [{
        "source_id": "BOF-IRON-MASS-CONSERVATION",
        "name": "Static converter iron input-output balance and steel yield definitions",
        "version": "v1",
    }]
    failure_modes = [
        "物流数组为空、字段不完整或名称重复", "质量非正或铁质量分数越界", "输入铁质量为0",
        "钢水质量大于总装入质量", "钢中铁加已知损失超过输入铁", "计算结果不是有限值",
    ]
    independent_validation = [
        "逐物流铁质量等于质量乘铁分数", "Fe输入等于钢中铁、已知损失和未计量铁之和",
        "铁回收率、已知损失率和未计量率之和等于1", "全部质量同比缩放时所有比例不变",
    ]
    dependencies = ["A004", "A005"]
    relations = [
        rel("depends_on", "A004", "各物流铁质量分数应采用A004归一化组成"),
        rel("depends_on", "A005", "A005可先验证总物流质量闭合，本工具再做铁元素分项闭合"),
        rel("overlaps", "D014", "D014只估算渣氧化态铁与金属夹带；本工具汇总全流程铁损"),
        rel("accepts_output_from", "D021", "D021的钢水量可作为本工具steel_mass_kg输入"),
    ]
    input_fields = [
        InputField("charge_streams", "铁源装入物流", "array", items=_CHARGE_STREAM_SCHEMA, min_items=1, max_items=30),
        InputField("steel_mass_kg", "出钢钢水质量", "number", unit="kg", min_value=1e-300),
        InputField("steel_iron_mass_fraction", "钢水铁质量分数", "number", unit="1", min_value=0, max_value=1),
        InputField("loss_streams", "已知铁损物流", "array", items=_LOSS_STREAM_SCHEMA, min_items=1, max_items=30),
        InputField("closure_tolerance_kg", "未计量铁闭合提示阈值", "number", required=False, default=1e-6, unit="kg", min_value=0),
    ]
    output_fields = [
        OutputField("total_charge_mass_kg", "总装入质量", "number", "kg"),
        OutputField("input_iron_mass_kg", "输入铁质量", "number", "kg"),
        OutputField("steel_iron_mass_kg", "钢中铁质量", "number", "kg"),
        OutputField("known_loss_iron_mass_kg", "已知损失铁质量", "number", "kg"),
        OutputField("unaccounted_iron_mass_kg", "未计量铁质量", "number", "kg"),
        OutputField("steel_mass_yield_fraction", "钢水质量收得率", "number", "1"),
        OutputField("iron_recovery_fraction", "铁回收率", "number", "1"),
        OutputField("known_loss_fraction_of_input_iron", "已知铁损率", "number", "1"),
        OutputField("unaccounted_fraction_of_input_iron", "未计量铁率", "number", "1"),
        OutputField("loss_breakdown", "逐物流铁损分解", "array", "kg"),
        OutputField("category_breakdown_iron_kg", "按类别汇总铁损", "object", "kg"),
        OutputField("fraction_closure_residual", "铁回收与损失比例闭合残差", "number", "1"),
        OutputField("mass_balance_residual_kg", "铁质量衡算残差", "number", "kg"),
        OutputField("model_version", "模型版本", "string"),
    ]
    validation_rules = [
        {"rule": "unique_stream_names_and_declared_fields"},
        {"rule": "positive_masses_and_bounded_iron_fractions"},
        {"rule": "steel_plus_known_loss_not_above_input_iron"},
        {"rule": "iron_mass_and_fraction_closure"},
    ]
    _base_charge = [
        {"name": "hot_metal", "mass_kg": 90000, "iron_mass_fraction": 0.94},
        {"name": "scrap", "mass_kg": 10000, "iron_mass_fraction": 0.98},
    ]
    qualification_cases = [
        {"id": "D022-N1", "kind": "normal", "input": {"charge_streams": _base_charge, "steel_mass_kg": 92000, "steel_iron_mass_fraction": 0.995, "loss_streams": [{"name": "slag", "category": "slag_oxidation", "mass_kg": 5000, "iron_mass_fraction": 0.35}, {"name": "dust", "category": "dust", "mass_kg": 1000, "iron_mass_fraction": 0.5}]}},
        {"id": "D022-N2", "kind": "normal", "input": {"charge_streams": [{"name": "hot_metal", "mass_kg": 80000, "iron_mass_fraction": 0.95}, {"name": "scrap", "mass_kg": 20000, "iron_mass_fraction": 0.97}], "steel_mass_kg": 90000, "steel_iron_mass_fraction": 0.994, "loss_streams": [{"name": "slag", "category": "slag_oxidation", "mass_kg": 8000, "iron_mass_fraction": 0.25}, {"name": "splash", "category": "splash", "mass_kg": 1000, "iron_mass_fraction": 0.9}]}},
        {"id": "D022-N3", "kind": "normal", "input": {"charge_streams": [{"name": "hot_metal", "mass_kg": 1000, "iron_mass_fraction": 0.94}], "steel_mass_kg": 900, "steel_iron_mass_fraction": 0.99, "loss_streams": [{"name": "slag", "category": "slag_oxidation", "mass_kg": 100, "iron_mass_fraction": 0.3}]}},
        {"id": "D022-B1", "kind": "boundary", "input": {"charge_streams": [{"name": "metal", "mass_kg": 1000, "iron_mass_fraction": 1}], "steel_mass_kg": 950, "steel_iron_mass_fraction": 1, "loss_streams": [{"name": "dust", "category": "dust", "mass_kg": 50, "iron_mass_fraction": 1}]}},
        {"id": "D022-F1", "kind": "failure", "input": {"charge_streams": [{"name": "metal", "mass_kg": 1000, "iron_mass_fraction": 0.9}], "steel_mass_kg": 950, "steel_iron_mass_fraction": 0.95, "loss_streams": [{"name": "dust", "category": "dust", "mass_kg": 50, "iron_mass_fraction": 1}]}},
        {"id": "D022-F2", "kind": "failure", "input": {"charge_streams": [{"name": "metal", "mass_kg": 1000, "iron_mass_fraction": 1}, {"name": "metal", "mass_kg": 10, "iron_mass_fraction": 1}], "steel_mass_kg": 950, "steel_iron_mass_fraction": 1, "loss_streams": [{"name": "dust", "category": "dust", "mass_kg": 50, "iron_mass_fraction": 1}]}},
    ]

    @staticmethod
    def _parse_streams(raw: Any, label: str, *, losses: bool):
        if not isinstance(raw, list) or not 1 <= len(raw) <= 30:
            return None, f"{label}必须包含1至30个物流"
        expected = {"name", "mass_kg", "iron_mass_fraction", *( ["category"] if losses else [] )}
        allowed_categories = {"slag_oxidation", "dust", "splash", "skull", "other"}
        names = set()
        parsed = []
        for index, item in enumerate(raw):
            if not isinstance(item, dict) or set(item) != expected:
                return None, f"{label}[{index}]字段必须严格为{sorted(expected)}"
            name = item.get("name")
            if not isinstance(name, str) or not name.strip():
                return None, f"{label}[{index}].name必须是非空字符串"
            name = name.strip()
            if name in names:
                return None, f"{label}物流名重复: {name}"
            names.add(name)
            mass, error = finite(item.get("mass_kg"), f"{label}[{index}].mass_kg", minimum=0, strict_minimum=True)
            if error:
                return None, error
            fraction, error = finite(item.get("iron_mass_fraction"), f"{label}[{index}].iron_mass_fraction", minimum=0, maximum=1)
            if error:
                return None, error
            record = {"name": name, "mass_kg": mass, "iron_mass_fraction": fraction}
            if losses:
                category = item.get("category")
                if category not in allowed_categories:
                    return None, f"{label}[{index}].category不是支持的损失类别"
                record["category"] = category
            parsed.append(record)
        return parsed, None

    def invoke(self, params: dict, context=None) -> ModelResult:
        charge_streams, error = self._parse_streams(params.get("charge_streams"), "charge_streams", losses=False)
        if error:
            return fail(error)
        loss_streams, error = self._parse_streams(params.get("loss_streams"), "loss_streams", losses=True)
        if error:
            return fail(error)
        steel_mass, error = finite(params.get("steel_mass_kg"), "steel_mass_kg", minimum=0, strict_minimum=True)
        if error:
            return fail(error)
        steel_fraction, error = finite(params.get("steel_iron_mass_fraction"), "steel_iron_mass_fraction", minimum=0, maximum=1)
        if error:
            return fail(error)
        tolerance, error = finite(params.get("closure_tolerance_kg", 1e-6), "closure_tolerance_kg", minimum=0)
        if error:
            return fail(error)

        total_charge = sum(item["mass_kg"] for item in charge_streams)
        if steel_mass > total_charge + 1e-12 * max(1.0, total_charge):
            return fail("steel_mass_kg不能大于总装入质量", "OUT_OF_DOMAIN")
        input_iron = sum(item["mass_kg"] * item["iron_mass_fraction"] for item in charge_streams)
        if input_iron <= 0:
            return fail("输入铁质量必须大于0", "OUT_OF_DOMAIN")
        steel_iron = steel_mass * steel_fraction
        breakdown = []
        category_totals = {category: 0.0 for category in ("slag_oxidation", "dust", "splash", "skull", "other")}
        for item in loss_streams:
            iron_mass = item["mass_kg"] * item["iron_mass_fraction"]
            breakdown.append({
                "name": item["name"],
                "category": item["category"],
                "stream_mass_kg": item["mass_kg"],
                "iron_mass_fraction": item["iron_mass_fraction"],
                "iron_mass_kg": iron_mass,
                "fraction_of_input_iron": iron_mass / input_iron,
            })
            category_totals[item["category"]] += iron_mass
        known_loss = sum(item["iron_mass_kg"] for item in breakdown)
        unaccounted = input_iron - steel_iron - known_loss
        numerical_tolerance = 1e-10 * max(1.0, input_iron)
        if unaccounted < -numerical_tolerance:
            return fail("钢中铁加已知损失超过输入铁质量", "OUT_OF_DOMAIN")
        if unaccounted < 0:
            unaccounted = 0.0
        iron_recovery = steel_iron / input_iron
        known_loss_fraction = known_loss / input_iron
        unaccounted_fraction = unaccounted / input_iron
        fraction_residual = iron_recovery + known_loss_fraction + unaccounted_fraction - 1.0
        mass_residual = input_iron - steel_iron - known_loss - unaccounted
        if abs(fraction_residual) > 1e-10 or abs(mass_residual) > numerical_tolerance:
            return fail("铁质量或比例衡算未数值闭合", "NUMERICAL_ERROR")
        warnings = []
        if unaccounted <= tolerance:
            warnings.append(BoundaryWarning("closure_tolerance_kg", "未计量铁不超过闭合阈值，处于完全闭合边界"))
        elif unaccounted_fraction > 0.1:
            warnings.append(BoundaryWarning("loss_streams", "未计量铁超过输入铁的10%，建议补充损失物流"))
        return ModelResult(True, result={
            "total_charge_mass_kg": total_charge,
            "input_iron_mass_kg": input_iron,
            "steel_iron_mass_kg": steel_iron,
            "known_loss_iron_mass_kg": known_loss,
            "unaccounted_iron_mass_kg": unaccounted,
            "steel_mass_yield_fraction": steel_mass / total_charge,
            "iron_recovery_fraction": iron_recovery,
            "known_loss_fraction_of_input_iron": known_loss_fraction,
            "unaccounted_fraction_of_input_iron": unaccounted_fraction,
            "loss_breakdown": breakdown,
            "category_breakdown_iron_kg": category_totals,
            "fraction_closure_residual": fraction_residual,
            "mass_balance_residual_kg": mass_residual,
            "model_version": "bof-iron-accounting-balance-v1",
        }, boundary_check=BoundaryCheck(not warnings, warnings))
