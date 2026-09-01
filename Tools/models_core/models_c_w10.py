"""P1-W10 additive transport-number tool; existing C-series implementations stay frozen."""

from __future__ import annotations

import math
from typing import Any, Optional

from .base import BaseModelTool, BoundaryCheck, BoundaryWarning, InputField, ModelResult, OutputField


def rel(kind: str, target: str, description: str) -> dict[str, str]:
    return {"type": kind, "target": target, "description": description}


def fail(message: str, code: str = "INVALID_INPUT") -> ModelResult:
    return ModelResult(False, error=message, error_code=code)


def finite(value: Any, label: str, *, minimum: Optional[float] = None, strict_minimum: bool = False):
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
    return parsed, None


class C011_TransportDimensionlessNumbers(BaseModelTool):
    model_id, name, version = "C011", "传递过程无量纲数", "1.0.0"
    scenario, priority = "传热传质", "P1"
    tool_name = "metallurgy_calculate_transport_dimensionless_numbers"
    status = qualification_status = "qualified"
    count_eligible = True
    data_requirement = "FORMULA_ONLY"
    data_access_mode = "none"
    description = "由统一SI物性和特征尺度同时计算Re、Pr、Sc、热/质Peclet数、Lewis数及动量/热扩散率。"
    applicable_boundary = "均匀连续介质、单一特征速度和长度、常物性；允许速度为0的静止极限，其余物性和尺度必须为正。"
    data_source = ["Definitions of Reynolds, Prandtl, Schmidt, Peclet and Lewis numbers"]
    source_version = "transport-dimensionless-definitions-v1"
    formula_reference = (
        "Re=rho*u*L/mu; Pr=cp*mu/k; Sc=mu/(rho*D); Pe_h=Re*Pr; Pe_m=Re*Sc; "
        "nu=mu/rho; alpha=k/(rho*cp); Le=alpha/D=Sc/Pr"
    )
    source_records = [
        {"source_id": "BIRD-STEWART-LIGHTFOOT", "name": "Transport Phenomena dimensionless-group definitions", "version": "2nd edition"},
        {"source_id": "INCROPERA-HEAT-MASS", "name": "Fundamentals of Heat and Mass Transfer", "version": "standard definitions"},
    ]
    failure_modes = ["密度、尺度、黏度、热容、导热系数或扩散系数非正", "速度为负", "任一输入不是有限数值"]
    independent_validation = ["Pe_h等于Re乘Pr", "Pe_m等于Re乘Sc", "Le同时等于alpha/D和Sc/Pr", "nu和alpha按SI定义独立复算"]
    dependencies = []
    relations = [
        rel("accepts_output_from", "C002", "C002的扩散系数可作为本工具diffusivity_m2_s输入"),
        rel("upstream_of", "C010", "Re和Sc定义可独立审计C010关联式输入"),
        rel("overlaps", "G002", "都输出扩散相关无量纲数；本工具给物性群，G002给离散时间步稳定数"),
        rel("upstream_of", "G001", "Re等可用于后续数值模型工况相似性审查"),
    ]
    input_fields = [
        InputField("density_kg_m3", "密度", "number", unit="kg/m3", min_value=1e-300),
        InputField("velocity_m_s", "特征速度", "number", unit="m/s", min_value=0),
        InputField("characteristic_length_m", "特征长度", "number", unit="m", min_value=1e-300),
        InputField("dynamic_viscosity_pa_s", "动力黏度", "number", unit="Pa*s", min_value=1e-300),
        InputField("specific_heat_j_kg_k", "定压比热", "number", unit="J/(kg*K)", min_value=1e-300),
        InputField("thermal_conductivity_w_m_k", "导热系数", "number", unit="W/(m*K)", min_value=1e-300),
        InputField("diffusivity_m2_s", "质量扩散系数", "number", unit="m2/s", min_value=1e-300),
    ]
    output_fields = [
        OutputField("reynolds_number", "Reynolds数", "number", "1"),
        OutputField("prandtl_number", "Prandtl数", "number", "1"),
        OutputField("schmidt_number", "Schmidt数", "number", "1"),
        OutputField("thermal_peclet_number", "热Peclet数", "number", "1"),
        OutputField("mass_peclet_number", "质Peclet数", "number", "1"),
        OutputField("lewis_number", "Lewis数", "number", "1"),
        OutputField("kinematic_viscosity_m2_s", "运动黏度", "number", "m2/s"),
        OutputField("thermal_diffusivity_m2_s", "热扩散率", "number", "m2/s"),
        OutputField("thermal_peclet_identity_residual", "热Peclet恒等残差", "number", "1"),
        OutputField("mass_peclet_identity_residual", "质Peclet恒等残差", "number", "1"),
        OutputField("lewis_identity_residual", "Lewis恒等残差", "number", "1"),
        OutputField("definition_version", "定义版本", "string"),
    ]
    validation_rules = [
        {"rule": "strictly_positive_properties_and_length"},
        {"rule": "nonnegative_velocity"},
        {"rule": "dimensionless_identity_closure"},
    ]
    qualification_cases = [
        {"id": "C011-N1", "kind": "normal", "input": {"density_kg_m3": 1.2, "velocity_m_s": 2, "characteristic_length_m": 0.1, "dynamic_viscosity_pa_s": 1.8e-5, "specific_heat_j_kg_k": 1005, "thermal_conductivity_w_m_k": 0.026, "diffusivity_m2_s": 2e-5}},
        {"id": "C011-N2", "kind": "normal", "input": {"density_kg_m3": 7000, "velocity_m_s": 0.2, "characteristic_length_m": 0.5, "dynamic_viscosity_pa_s": 0.006, "specific_heat_j_kg_k": 800, "thermal_conductivity_w_m_k": 30, "diffusivity_m2_s": 1e-8}},
        {"id": "C011-N3", "kind": "normal", "input": {"density_kg_m3": 1000, "velocity_m_s": 0.01, "characteristic_length_m": 0.02, "dynamic_viscosity_pa_s": 0.001, "specific_heat_j_kg_k": 4200, "thermal_conductivity_w_m_k": 0.6, "diffusivity_m2_s": 1e-9}},
        {"id": "C011-B1", "kind": "boundary", "input": {"density_kg_m3": 1, "velocity_m_s": 0, "characteristic_length_m": 1, "dynamic_viscosity_pa_s": 1, "specific_heat_j_kg_k": 1, "thermal_conductivity_w_m_k": 1, "diffusivity_m2_s": 1}},
        {"id": "C011-F1", "kind": "failure", "input": {"density_kg_m3": 1, "velocity_m_s": 1, "characteristic_length_m": 1, "dynamic_viscosity_pa_s": 0, "specific_heat_j_kg_k": 1, "thermal_conductivity_w_m_k": 1, "diffusivity_m2_s": 1}},
        {"id": "C011-F2", "kind": "failure", "input": {"density_kg_m3": 1, "velocity_m_s": -1, "characteristic_length_m": 1, "dynamic_viscosity_pa_s": 1, "specific_heat_j_kg_k": 1, "thermal_conductivity_w_m_k": 1, "diffusivity_m2_s": 1}},
    ]

    def invoke(self, params: dict, context=None) -> ModelResult:
        parsed = {}
        for field in self.input_fields:
            strict = field.name != "velocity_m_s"
            value, error = finite(params.get(field.name), field.name, minimum=0, strict_minimum=strict)
            if error:
                return fail(error)
            parsed[field.name] = value
        density = parsed["density_kg_m3"]
        velocity = parsed["velocity_m_s"]
        length = parsed["characteristic_length_m"]
        viscosity = parsed["dynamic_viscosity_pa_s"]
        heat_capacity = parsed["specific_heat_j_kg_k"]
        conductivity = parsed["thermal_conductivity_w_m_k"]
        diffusivity = parsed["diffusivity_m2_s"]

        kinematic_viscosity = viscosity / density
        thermal_diffusivity = conductivity / (density * heat_capacity)
        reynolds = density * velocity * length / viscosity
        prandtl = heat_capacity * viscosity / conductivity
        schmidt = viscosity / (density * diffusivity)
        thermal_peclet = density * heat_capacity * velocity * length / conductivity
        mass_peclet = velocity * length / diffusivity
        lewis = thermal_diffusivity / diffusivity
        thermal_residual = thermal_peclet - reynolds * prandtl
        mass_residual = mass_peclet - reynolds * schmidt
        lewis_residual = lewis - schmidt / prandtl
        warnings = []
        if velocity == 0:
            warnings.append(BoundaryWarning("velocity_m_s", "速度为0，Re和两个Peclet数处于静止极限"))
        return ModelResult(True, result={
            "reynolds_number": reynolds,
            "prandtl_number": prandtl,
            "schmidt_number": schmidt,
            "thermal_peclet_number": thermal_peclet,
            "mass_peclet_number": mass_peclet,
            "lewis_number": lewis,
            "kinematic_viscosity_m2_s": kinematic_viscosity,
            "thermal_diffusivity_m2_s": thermal_diffusivity,
            "thermal_peclet_identity_residual": thermal_residual,
            "mass_peclet_identity_residual": mass_residual,
            "lewis_identity_residual": lewis_residual,
            "definition_version": "transport-dimensionless-definitions-v1",
        }, boundary_check=BoundaryCheck(not warnings, warnings))
