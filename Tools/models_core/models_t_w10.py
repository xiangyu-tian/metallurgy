"""P1-W10 additive heat-transfer tools; T001/T002 stay unchanged."""

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


class W10HeatTransferTool(BaseModelTool):
    scenario = "传热传质"
    priority = "P1"
    status = "qualified"
    qualification_status = "qualified"
    count_eligible = True
    data_requirement = "FORMULA_ONLY"
    data_access_mode = "none"


class T003_LumpedCapacitanceTransient(W10HeatTransferTool):
    model_id, name, version = "T003", "集总热容瞬态温度", "1.0.0"
    tool_name = "metallurgy_calculate_lumped_transient_temperature"
    description = "在Bi≤0.1的集总热容适用域内，计算均温物体的瞬态温度、时间常数和有符号放热量。"
    applicable_boundary = "均匀固体、常物性、环境温度和对流换热系数恒定、内部温差可忽略；Bi=h(V/A)/k≤0.1。"
    data_source = ["Lumped-capacitance transient heat-transfer solution", "Biot-number applicability criterion"]
    source_version = "lumped-capacitance-v1; Bi-limit-0.1"
    formula_reference = "Lc=V/A; Bi=hLc/k; tau=rho*cp*V/(hA); T=Ta+(T0-Ta)exp(-t/tau); Q=rho*cp*V*(T0-T)"
    source_records = [
        {"source_id": "INCROPERA-LUMPED", "name": "Fundamentals of Heat and Mass Transfer - lumped-capacitance method", "version": "Bi<=0.1 criterion"},
    ]
    failure_modes = ["密度、热容、体积、面积、对流系数、导热系数或绝对温度非正", "时间为负", "Bi大于0.1"]
    independent_validation = ["无量纲温差等于exp(-t/tau)", "t=0时温度等于初温且换热量为0", "温度始终位于初温与环境温度之间", "能量变化等于rho*cp*V*(T0-T)"]
    dependencies = []
    relations = [
        rel("overlaps", "T001", "都计算固体温度驱动的导热响应；T001为稳态空间梯度，本工具为均温瞬态"),
        rel("complements", "T002", "T002可提供辐射分量，但本工具当前只接受等效恒定对流系数"),
        rel("overlaps", "F005", "都描述铸坯/固体热响应，但本工具限Bi≤0.1的零维均温模型"),
    ]
    input_fields = [
        InputField("density_kg_m3", "物体密度", "number", unit="kg/m3", min_value=1e-300),
        InputField("specific_heat_j_kg_k", "比热容", "number", unit="J/(kg*K)", min_value=1e-300),
        InputField("volume_m3", "体积", "number", unit="m3", min_value=1e-300),
        InputField("surface_area_m2", "换热表面积", "number", unit="m2", min_value=1e-300),
        InputField("convection_coefficient_w_m2_k", "对流换热系数", "number", unit="W/(m2*K)", min_value=1e-300),
        InputField("thermal_conductivity_w_m_k", "物体导热系数", "number", unit="W/(m*K)", min_value=1e-300),
        InputField("initial_temperature_k", "初始温度", "number", unit="K", min_value=1e-300),
        InputField("ambient_temperature_k", "环境温度", "number", unit="K", min_value=1e-300),
        InputField("time_s", "时间", "number", unit="s", min_value=0),
    ]
    output_fields = [
        OutputField("temperature_k", "时刻温度", "number", "K"),
        OutputField("heat_removed_j", "从物体移出的有符号热量", "number", "J"),
        OutputField("biot_number", "Biot数", "number", "1"),
        OutputField("characteristic_length_m", "特征长度V/A", "number", "m"),
        OutputField("time_constant_s", "时间常数", "number", "s"),
        OutputField("dimensionless_temperature", "无量纲温差", "number", "1"),
        OutputField("model_version", "模型版本", "string"),
    ]
    validation_rules = [
        {"rule": "strictly_positive_material_geometry_and_temperature"},
        {"rule": "nonnegative_time"},
        {"rule": "biot_not_greater_than_0.1"},
    ]
    qualification_cases = [
        {"id": "T003-N1", "kind": "normal", "input": {"density_kg_m3": 7800, "specific_heat_j_kg_k": 500, "volume_m3": 0.01, "surface_area_m2": 1, "convection_coefficient_w_m2_k": 100, "thermal_conductivity_w_m_k": 50, "initial_temperature_k": 1000, "ambient_temperature_k": 300, "time_s": 120}},
        {"id": "T003-N2", "kind": "normal", "input": {"density_kg_m3": 2700, "specific_heat_j_kg_k": 900, "volume_m3": 0.002, "surface_area_m2": 0.4, "convection_coefficient_w_m2_k": 20, "thermal_conductivity_w_m_k": 200, "initial_temperature_k": 300, "ambient_temperature_k": 500, "time_s": 60}},
        {"id": "T003-N3", "kind": "normal", "input": {"density_kg_m3": 1000, "specific_heat_j_kg_k": 4200, "volume_m3": 0.0005, "surface_area_m2": 0.1, "convection_coefficient_w_m2_k": 10, "thermal_conductivity_w_m_k": 0.6, "initial_temperature_k": 350, "ambient_temperature_k": 300, "time_s": 600}},
        {"id": "T003-B1", "kind": "boundary", "input": {"density_kg_m3": 7800, "specific_heat_j_kg_k": 500, "volume_m3": 0.01, "surface_area_m2": 1, "convection_coefficient_w_m2_k": 100, "thermal_conductivity_w_m_k": 50, "initial_temperature_k": 1000, "ambient_temperature_k": 300, "time_s": 0}},
        {"id": "T003-B2", "kind": "boundary", "input": {"density_kg_m3": 1000, "specific_heat_j_kg_k": 1000, "volume_m3": 0.01, "surface_area_m2": 1, "convection_coefficient_w_m2_k": 100, "thermal_conductivity_w_m_k": 10, "initial_temperature_k": 500, "ambient_temperature_k": 300, "time_s": 10}},
        {"id": "T003-F1", "kind": "failure", "input": {"density_kg_m3": 1000, "specific_heat_j_kg_k": 1000, "volume_m3": 0.02, "surface_area_m2": 1, "convection_coefficient_w_m2_k": 100, "thermal_conductivity_w_m_k": 10, "initial_temperature_k": 500, "ambient_temperature_k": 300, "time_s": 10}},
        {"id": "T003-F2", "kind": "failure", "input": {"density_kg_m3": 1000, "specific_heat_j_kg_k": 1000, "volume_m3": 0.01, "surface_area_m2": 1, "convection_coefficient_w_m2_k": 0, "thermal_conductivity_w_m_k": 10, "initial_temperature_k": 500, "ambient_temperature_k": 300, "time_s": 10}},
    ]

    def invoke(self, params: dict, context=None) -> ModelResult:
        parsed = {}
        for field in self.input_fields:
            strict = field.name != "time_s"
            value, error = finite(params.get(field.name), field.name, minimum=0, strict_minimum=strict)
            if error:
                return fail(error)
            parsed[field.name] = value
        characteristic_length = parsed["volume_m3"] / parsed["surface_area_m2"]
        biot = parsed["convection_coefficient_w_m2_k"] * characteristic_length / parsed["thermal_conductivity_w_m_k"]
        if biot > 0.1 and not math.isclose(biot, 0.1, rel_tol=0, abs_tol=1e-12):
            return fail(f"Bi={biot:g}大于0.1，集总热容假设不成立", "OUT_OF_DOMAIN")
        time_constant = (
            parsed["density_kg_m3"] * parsed["specific_heat_j_kg_k"] * parsed["volume_m3"]
            / (parsed["convection_coefficient_w_m2_k"] * parsed["surface_area_m2"])
        )
        dimensionless = math.exp(-parsed["time_s"] / time_constant)
        temperature = parsed["ambient_temperature_k"] + (
            parsed["initial_temperature_k"] - parsed["ambient_temperature_k"]
        ) * dimensionless
        heat_removed = (
            parsed["density_kg_m3"] * parsed["specific_heat_j_kg_k"] * parsed["volume_m3"]
            * (parsed["initial_temperature_k"] - temperature)
        )
        warnings = []
        if parsed["time_s"] == 0:
            warnings.append(BoundaryWarning("time_s", "时间为0，返回初始状态极限"))
        if math.isclose(biot, 0.1, rel_tol=0, abs_tol=1e-12):
            warnings.append(BoundaryWarning("biot_number", "Bi恰位于集总热容常用适用上界0.1"))
        return ModelResult(True, result={
            "temperature_k": temperature,
            "heat_removed_j": heat_removed,
            "biot_number": biot,
            "characteristic_length_m": characteristic_length,
            "time_constant_s": time_constant,
            "dimensionless_temperature": dimensionless,
            "model_version": "lumped-capacitance-v1",
        }, boundary_check=BoundaryCheck(not warnings, warnings))


class T004_MultilayerThermalResistance(W10HeatTransferTool):
    model_id, name, version = "T004", "多层热阻网络", "1.0.0"
    tool_name = "metallurgy_calculate_multilayer_thermal_resistance"
    description = "组合多层平板导热、层间接触热阻和可选两侧对流热阻，返回稳态热流与完整温度节点闭合。"
    applicable_boundary = "一维稳态、各层常导热系数、无内热源、公共截面积；接触热阻按面积比热阻输入，可选两侧恒定对流边界。"
    data_source = ["Series thermal-resistance network", "Fourier plane-wall conduction", "Newton convection boundary"]
    source_version = "multilayer-resistance-network-v1"
    formula_reference = "R=sum[L_i/(k_i A)]+sum[R''c_j/A]+1/(h_h A)+1/(h_c A); Q=(T_h-T_c)/R"
    source_records = [
        {"source_id": "INCROPERA-THERMAL-RESISTANCE", "name": "One-dimensional composite-wall thermal resistance network", "version": "steady-state series network"},
    ]
    failure_modes = ["层数组为空、名称重复、厚度或导热系数非正", "接触热阻数量不是层数减1或值为负", "面积或可选对流系数非正", "绝对温度非正"]
    independent_validation = ["单层且无接触/对流时与T001完全一致", "各分量温降之和等于边界温差", "交换边界温度后热流反号而热阻不变", "总热阻等于各串联热阻之和"]
    dependencies = []
    relations = [
        rel("overlaps", "T001", "T001是本工具单层且无接触/对流热阻的严格退化情形"),
        rel("accepts_output_from", "C009", "C009的有效导热系数可作为任一层conductivity_w_m_k输入"),
        rel("complements", "T002", "T002的辐射热流不在本线性热阻网络内，可在上层热损失模型组合"),
    ]
    _layer_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "thickness_m": {"type": "number", "exclusiveMinimum": 0},
            "conductivity_w_m_k": {"type": "number", "exclusiveMinimum": 0},
        },
        "required": ["name", "thickness_m", "conductivity_w_m_k"],
        "additionalProperties": False,
    }
    input_fields = [
        InputField("layers", "平板层", "array", items=_layer_schema, min_items=1, max_items=50, description="从热侧到冷侧排列；厚度m、导热系数W/(m*K)"),
        InputField("area_m2", "公共截面积", "number", unit="m2", min_value=1e-300),
        InputField("hot_boundary_temperature_k", "热侧边界温度", "number", unit="K", min_value=1e-300),
        InputField("cold_boundary_temperature_k", "冷侧边界温度", "number", unit="K", min_value=1e-300),
        InputField("contact_resistances_m2_k_w", "层间面积比接触热阻", "array", required=False, default=[], items={"type": "number", "minimum": 0}, min_items=0, max_items=49, description="从热侧到冷侧排列，数量必须为层数减1；单位m2*K/W"),
        InputField("hot_convection_coefficient_w_m2_k", "热侧对流系数", "number", required=False, unit="W/(m2*K)", min_value=1e-300, description="省略时热侧输入温度视为壁面温度"),
        InputField("cold_convection_coefficient_w_m2_k", "冷侧对流系数", "number", required=False, unit="W/(m2*K)", min_value=1e-300, description="省略时冷侧输入温度视为壁面温度"),
    ]
    output_fields = [
        OutputField("total_thermal_resistance_k_w", "总热阻", "number", "K/W"),
        OutputField("heat_rate_w", "热侧到冷侧有符号热流率", "number", "W"),
        OutputField("heat_flux_w_m2", "有符号热流密度", "number", "W/m2"),
        OutputField("resistance_breakdown", "热阻分解", "array"),
        OutputField("temperature_profile", "边界与界面温度", "array"),
        OutputField("closure_residual_k", "温降闭合残差", "number", "K"),
        OutputField("layer_count", "层数", "number", "1"),
        OutputField("direction", "换热方向", "string"),
        OutputField("model_version", "模型版本", "string"),
    ]
    validation_rules = [
        {"rule": "positive_layers_area_temperatures_and_optional_h"},
        {"rule": "contact_count_equals_layer_count_minus_one"},
        {"rule": "series_temperature_drop_closure"},
    ]
    qualification_cases = [
        {"id": "T004-N1", "kind": "normal", "input": {"layers": [{"name": "steel", "thickness_m": 0.1, "conductivity_w_m_k": 20}], "area_m2": 2, "hot_boundary_temperature_k": 1000, "cold_boundary_temperature_k": 500}},
        {"id": "T004-N2", "kind": "normal", "input": {"layers": [{"name": "refractory", "thickness_m": 0.2, "conductivity_w_m_k": 2}, {"name": "shell", "thickness_m": 0.02, "conductivity_w_m_k": 40}], "area_m2": 10, "hot_boundary_temperature_k": 1800, "cold_boundary_temperature_k": 320, "contact_resistances_m2_k_w": [0.001]}},
        {"id": "T004-N3", "kind": "normal", "input": {"layers": [{"name": "wall", "thickness_m": 0.1, "conductivity_w_m_k": 10}], "area_m2": 1, "hot_boundary_temperature_k": 300, "cold_boundary_temperature_k": 800, "hot_convection_coefficient_w_m2_k": 100, "cold_convection_coefficient_w_m2_k": 20}},
        {"id": "T004-B1", "kind": "boundary", "input": {"layers": [{"name": "wall", "thickness_m": 0.1, "conductivity_w_m_k": 10}], "area_m2": 1, "hot_boundary_temperature_k": 500, "cold_boundary_temperature_k": 500}},
        {"id": "T004-F1", "kind": "failure", "input": {"layers": [{"name": "a", "thickness_m": 0.1, "conductivity_w_m_k": 10}, {"name": "b", "thickness_m": 0.1, "conductivity_w_m_k": 5}], "area_m2": 1, "hot_boundary_temperature_k": 500, "cold_boundary_temperature_k": 300, "contact_resistances_m2_k_w": []}},
        {"id": "T004-F2", "kind": "failure", "input": {"layers": [{"name": "wall", "thickness_m": 0.1, "conductivity_w_m_k": 0}], "area_m2": 1, "hot_boundary_temperature_k": 500, "cold_boundary_temperature_k": 300}},
    ]

    def invoke(self, params: dict, context=None) -> ModelResult:
        raw_layers = params.get("layers")
        if not isinstance(raw_layers, list) or not 1 <= len(raw_layers) <= 50:
            return fail("layers必须包含1到50层")
        layers = []
        names = set()
        for index, item in enumerate(raw_layers):
            if not isinstance(item, dict) or set(item) != {"name", "thickness_m", "conductivity_w_m_k"}:
                return fail(f"layers[{index}]必须且只能包含name、thickness_m和conductivity_w_m_k")
            name = item.get("name")
            if not isinstance(name, str) or not name.strip() or name.strip() in names:
                return fail(f"layers[{index}].name必须是唯一非空字符串")
            thickness, error = finite(item.get("thickness_m"), f"layers[{index}].thickness_m", minimum=0, strict_minimum=True)
            if error:
                return fail(error)
            conductivity, error = finite(item.get("conductivity_w_m_k"), f"layers[{index}].conductivity_w_m_k", minimum=0, strict_minimum=True)
            if error:
                return fail(error)
            names.add(name.strip())
            layers.append({"name": name.strip(), "thickness_m": thickness, "conductivity_w_m_k": conductivity})

        area, error = finite(params.get("area_m2"), "area_m2", minimum=0, strict_minimum=True)
        if error:
            return fail(error)
        hot_temperature, error = finite(params.get("hot_boundary_temperature_k"), "hot_boundary_temperature_k", minimum=0, strict_minimum=True)
        if error:
            return fail(error)
        cold_temperature, error = finite(params.get("cold_boundary_temperature_k"), "cold_boundary_temperature_k", minimum=0, strict_minimum=True)
        if error:
            return fail(error)

        raw_contacts = params.get("contact_resistances_m2_k_w", [])
        if not isinstance(raw_contacts, list) or len(raw_contacts) != len(layers) - 1:
            return fail("contact_resistances_m2_k_w数量必须等于层数减1")
        contacts = []
        for index, raw_value in enumerate(raw_contacts):
            value, error = finite(raw_value, f"contact_resistances_m2_k_w[{index}]", minimum=0)
            if error:
                return fail(error)
            contacts.append(value)

        convection = {}
        for key in ("hot_convection_coefficient_w_m2_k", "cold_convection_coefficient_w_m2_k"):
            if params.get(key) is None:
                convection[key] = None
                continue
            value, error = finite(params.get(key), key, minimum=0, strict_minimum=True)
            if error:
                return fail(error)
            convection[key] = value

        components = []
        if convection["hot_convection_coefficient_w_m2_k"] is not None:
            components.append({"kind": "hot_convection", "name": "hot_convection", "resistance_k_w": 1 / (convection["hot_convection_coefficient_w_m2_k"] * area)})
        for index, layer in enumerate(layers):
            components.append({"kind": "layer", "name": layer["name"], "resistance_k_w": layer["thickness_m"] / (layer["conductivity_w_m_k"] * area)})
            if index < len(contacts):
                components.append({"kind": "contact", "name": f"{layers[index]['name']}|{layers[index + 1]['name']}", "resistance_k_w": contacts[index] / area})
        if convection["cold_convection_coefficient_w_m2_k"] is not None:
            components.append({"kind": "cold_convection", "name": "cold_convection", "resistance_k_w": 1 / (convection["cold_convection_coefficient_w_m2_k"] * area)})

        total_resistance = math.fsum(component["resistance_k_w"] for component in components)
        if not math.isfinite(total_resistance) or total_resistance <= 0:
            return fail("总热阻必须是正有限数", "NUMERICAL_ERROR")
        heat_rate = (hot_temperature - cold_temperature) / total_resistance
        profile = [{"node": "hot_boundary", "temperature_k": hot_temperature}]
        current_temperature = hot_temperature
        for index, component in enumerate(components, start=1):
            current_temperature -= heat_rate * component["resistance_k_w"]
            profile.append({"node": f"after_{index}_{component['name']}", "temperature_k": current_temperature})
        closure_residual = current_temperature - cold_temperature
        if abs(closure_residual) > 1e-8 * max(1.0, abs(hot_temperature - cold_temperature)):
            return fail("温降网络未数值闭合", "NUMERICAL_ERROR")
        warnings = []
        if hot_temperature == cold_temperature:
            warnings.append(BoundaryWarning("boundary_temperatures", "两侧温度相等，热流为0"))
        direction = "hot_to_cold" if heat_rate > 0 else "cold_to_hot" if heat_rate < 0 else "none"
        return ModelResult(True, result={
            "total_thermal_resistance_k_w": total_resistance,
            "heat_rate_w": heat_rate,
            "heat_flux_w_m2": heat_rate / area,
            "resistance_breakdown": components,
            "temperature_profile": profile,
            "closure_residual_k": closure_residual,
            "layer_count": len(layers),
            "direction": direction,
            "model_version": "multilayer-resistance-network-v1",
        }, boundary_check=BoundaryCheck(not warnings, warnings))
