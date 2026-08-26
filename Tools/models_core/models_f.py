"""Qualified continuous-casting and solidification formula tools."""

from __future__ import annotations

from .base import BaseModelTool, BoundaryCheck, BoundaryWarning, InputField, ModelResult, OutputField


class F003_SteelSuperheat(BaseModelTool):
    model_id, name, version = "F003", "钢液过热度", "1.0.0"
    tool_name = "metallurgy_calc_steel_superheat"
    scenario = "凝固与连铸"
    priority = "P0"
    status = "qualified"
    qualification_status = "qualified"
    count_eligible = True
    data_requirement = "FORMULA_ONLY"
    data_access_mode = "none"
    description = (
        "根据显式钢液温度和液相线温度计算过热度；温度可用K或degC。"
        "本工具不预测液相线；liquidus_source=F001时必须提供upstream_execution_id。"
    )
    applicable_boundary = (
        "适用于已知钢液温度与单值液相线温度的静态过热度计算；"
        "不接受液相线区间，不推断钢种液相线，不替代连铸控制或凝固模型。"
    )
    temperature_range = [0.0, 4000.0]
    data_source = ["Definition of liquid-steel superheat", "SI temperature-difference convention"]
    source_version = "steel-superheat-definition-v1; SI Brochure 9th edition"
    formula_reference = "DeltaT_superheat = T_steel - T_liquidus; Delta(degC) = Delta(K)"
    source_records = [
        {
            "source_id": "SUPERHEAT-DEFINITION",
            "name": "Liquid-steel superheat temperature difference",
            "version": "v1",
        },
        {
            "source_id": "BIPM-SI-BROCHURE",
            "name": "The International System of Units (SI Brochure)",
            "version": "9th edition v3.01",
            "url": "https://www.bipm.org/en/publications/si-brochure",
        },
    ]
    failure_modes = [
        "温度单位不受支持或绝对温标非法",
        "液相线不是单值",
        "要求限值判断但没有同时给上下限",
        "过热度下限高于上限",
        "声明液相线来自F001但缺少上游执行编号",
    ]
    independent_validation = [
        "过热度等于钢液温度减液相线温度",
        "同一输入走K与degC路径结果一致",
        "两个绝对温度同时平移时过热度不变",
        "钢液温度低于液相线时返回负过热度和物理边界警告",
    ]
    dependencies = []
    relations = [
        {
            "type": "uses_convention_of",
            "target": "A001",
            "description": "复用A001验证过的K/摄氏温标换算约定，但本工具计算的是温差与工艺限值状态",
        }
    ]
    related_catalog_ids = ["F001"]
    input_fields = [
        InputField("steel_temperature", "钢液温度", "number", unit="$temperature_unit"),
        InputField("liquidus_temperature", "液相线温度", "number", unit="$temperature_unit"),
        InputField("temperature_unit", "温度单位", "select", enum=["K", "degC"]),
        InputField(
            "liquidus_source",
            "液相线来源",
            "string",
            description="非空来源说明；若填F001，必须同时给upstream_execution_id",
        ),
        InputField("evaluate_limits", "是否按过热度限值判断", "boolean", required=False, default=False),
        InputField("minimum_superheat_k", "过热度下限", "number", required=False, unit="K", min_value=0),
        InputField("maximum_superheat_k", "过热度上限", "number", required=False, unit="K", min_value=0),
        InputField(
            "upstream_execution_id",
            "F001上游执行编号",
            "string",
            required=False,
            description="只有液相线确由F001执行结果提供时填写",
        ),
    ]
    output_fields = [
        OutputField("steel_temperature_k", "钢液温度", "number", "K"),
        OutputField("liquidus_temperature_k", "液相线温度", "number", "K"),
        OutputField("steel_temperature_degc", "钢液温度", "number", "degC"),
        OutputField("liquidus_temperature_degc", "液相线温度", "number", "degC"),
        OutputField("superheat_k", "钢液过热度", "number", "K"),
        OutputField("superheat_degc", "钢液过热度", "number", "degC"),
        OutputField("limits_applied", "是否执行限值判断", "boolean"),
        OutputField("limit_status", "限值状态", "string"),
        OutputField("liquidus_source", "液相线来源", "string"),
        OutputField("upstream_execution_id", "F001上游执行编号", "string"),
    ]
    validation_rules = [
        {"rule": "absolute_temperature_above_zero", "fields": ["steel_temperature", "liquidus_temperature"]},
        {"rule": "limit_pair_required_when_evaluated", "fields": ["minimum_superheat_k", "maximum_superheat_k"]},
        {"rule": "f001_source_requires_execution_id", "fields": ["liquidus_source", "upstream_execution_id"]},
    ]
    qualification_cases = [
        {
            "id": "F003-N1",
            "kind": "normal",
            "input": {
                "steel_temperature": 1873.15,
                "liquidus_temperature": 1823.15,
                "temperature_unit": "K",
                "liquidus_source": "laboratory_measurement",
            },
        },
        {
            "id": "F003-N2",
            "kind": "normal",
            "input": {
                "steel_temperature": 1600,
                "liquidus_temperature": 1530,
                "temperature_unit": "degC",
                "liquidus_source": "approved_external_model:v2",
                "evaluate_limits": True,
                "minimum_superheat_k": 20,
                "maximum_superheat_k": 80,
            },
        },
        {
            "id": "F003-N3",
            "kind": "normal",
            "input": {
                "steel_temperature": 1840,
                "liquidus_temperature": 1810,
                "temperature_unit": "K",
                "liquidus_source": "F001",
                "upstream_execution_id": "EXEC-F001-REFERENCE",
            },
        },
        {
            "id": "F003-B1",
            "kind": "boundary",
            "input": {
                "steel_temperature": 1500,
                "liquidus_temperature": 1510,
                "temperature_unit": "degC",
                "liquidus_source": "thermocouple_and_reference_liquidus",
            },
        },
        {
            "id": "F003-F1",
            "kind": "failure",
            "input": {
                "steel_temperature": -1,
                "liquidus_temperature": 100,
                "temperature_unit": "K",
                "liquidus_source": "invalid_test",
            },
        },
    ]

    @staticmethod
    def _to_kelvin(value: float, unit: str) -> float:
        return value if unit == "K" else value + 273.15

    def invoke(self, params, context=None):
        unit = params["temperature_unit"]
        steel_k = self._to_kelvin(float(params["steel_temperature"]), unit)
        liquidus_k = self._to_kelvin(float(params["liquidus_temperature"]), unit)
        if steel_k < 0 or liquidus_k < 0:
            return ModelResult(False, error="钢液温度和液相线温度不能低于绝对零度", error_code="OUT_OF_DOMAIN")

        source = params["liquidus_source"].strip()
        if not source:
            return ModelResult(False, error="liquidus_source必须是非空来源说明", error_code="INVALID_INPUT")
        upstream_id = str(params.get("upstream_execution_id", "")).strip()
        if source.upper() == "F001" and not upstream_id:
            return ModelResult(False, error="liquidus_source=F001时必须提供upstream_execution_id", error_code="MISSING_DATA")

        evaluate = bool(params.get("evaluate_limits", False))
        minimum = params.get("minimum_superheat_k")
        maximum = params.get("maximum_superheat_k")
        if evaluate and (minimum is None or maximum is None):
            return ModelResult(False, error="evaluate_limits=true时必须同时提供minimum_superheat_k和maximum_superheat_k", error_code="MISSING_DATA")
        if not evaluate and (minimum is not None or maximum is not None):
            return ModelResult(False, error="提供过热度限值时必须设置evaluate_limits=true", error_code="INVALID_INPUT")
        if evaluate:
            minimum, maximum = float(minimum), float(maximum)
            if minimum > maximum:
                return ModelResult(False, error="minimum_superheat_k不能大于maximum_superheat_k", error_code="INVALID_INPUT")

        superheat = steel_k - liquidus_k
        status = "not_evaluated"
        warnings = []
        if superheat < 0:
            warnings.append(BoundaryWarning("steel_temperature", "钢液温度低于液相线，结果为负过热度"))
        if evaluate:
            if superheat < minimum:
                status = "below_range"
                warnings.append(BoundaryWarning("superheat_k", "过热度低于显式工艺下限", min_allowed=minimum, max_allowed=maximum))
            elif superheat > maximum:
                status = "above_range"
                warnings.append(BoundaryWarning("superheat_k", "过热度高于显式工艺上限", min_allowed=minimum, max_allowed=maximum))
            else:
                status = "within_range"

        return ModelResult(
            True,
            result={
                "steel_temperature_k": steel_k,
                "liquidus_temperature_k": liquidus_k,
                "steel_temperature_degc": steel_k - 273.15,
                "liquidus_temperature_degc": liquidus_k - 273.15,
                "superheat_k": superheat,
                "superheat_degc": superheat,
                "limits_applied": evaluate,
                "limit_status": status,
                "liquidus_source": source,
                "upstream_execution_id": upstream_id,
            },
            boundary_check=BoundaryCheck(not warnings, warnings),
        )
