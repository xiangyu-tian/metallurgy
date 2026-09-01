"""P1-W11 additive external-transfer tool; all existing implementations stay frozen."""

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


class C012_SphereExternalConvectionTransfer(BaseModelTool):
    model_id, name, version = "C012", "球体外流对流换热与传质系数", "1.0.0"
    scenario, priority = "传热传质", "P1"
    tool_name = "metallurgy_calculate_sphere_external_convection_transfer"
    status = qualification_status = "qualified"
    count_eligible = True
    data_requirement = "FORMULA_ONLY"
    data_access_mode = "none"
    description = "消费显式Re/Pr/Sc与物性，按固定Ranz-Marshall球体外流关联式计算Nu、Sh、换热系数和传质系数。"
    applicable_boundary = (
        "单个近球形颗粒或液滴、均匀外流、常物性；0<=Re<=200，热支路0.7<=Pr<=380，"
        "质传递支路0.6<=Sc<=3000。至少提供完整热支路或质传递支路。"
    )
    data_source = ["Ranz-Marshall 1952 sphere correlation", "Caller-supplied dimensionless groups and properties"]
    source_version = "ranz-marshall-sphere-1952-v1"
    formula_reference = (
        "Nu=2+0.6*Re^0.5*Pr^(1/3); Sh=2+0.6*Re^0.5*Sc^(1/3); "
        "h=Nu*k/d; km=Sh*D/d"
    )
    source_records = [{
        "source_id": "RANZ-MARSHALL-1952",
        "name": "W. E. Ranz and W. R. Marshall, Evaporation from Drops, Part II",
        "version": "Chemical Engineering Progress 48(4), 173-180",
        "url": "https://cir.nii.ac.jp/crid/1571135651322950144",
    }]
    failure_modes = [
        "Re、Pr或Sc超关联式适用域", "球径或所需物性非正", "热或质传递输入组只提供一部分",
        "热和质传递两组都未提供", "计算结果不是有限值",
    ]
    independent_validation = [
        "Re=0时Nu和Sh等于纯扩散极限2", "h=Nu*k/d", "km=Sh*D/d",
        "Re放大4倍时Nu-2与Sh-2放大2倍",
    ]
    dependencies = ["C011"]
    relations = [
        rel("depends_on", "C011", "C011计算的Re、Pr、Sc可直接作为本工具无量纲输入"),
        rel("overlaps", "C010", "都给出传质系数；C010面向填充床，本工具面向孤立球体外流"),
        rel("upstream_of", "T003", "本工具换热系数可作为T003的恒定对流换热系数输入"),
    ]
    input_fields = [
        InputField("reynolds_number", "Reynolds数", "number", unit="1", min_value=0, max_value=200),
        InputField("characteristic_diameter_m", "球体特征直径", "number", unit="m", min_value=1e-300),
        InputField("prandtl_number", "Prandtl数", "number", required=False, unit="1", min_value=0.7, max_value=380),
        InputField("thermal_conductivity_w_m_k", "流体导热系数", "number", required=False, unit="W/(m*K)", min_value=1e-300),
        InputField("schmidt_number", "Schmidt数", "number", required=False, unit="1", min_value=0.6, max_value=3000),
        InputField("mass_diffusivity_m2_s", "质量扩散系数", "number", required=False, unit="m2/s", min_value=1e-300),
    ]
    output_fields = [
        OutputField("nusselt_number", "Nusselt数", "number", "1", nullable=True),
        OutputField("heat_transfer_coefficient_w_m2_k", "对流换热系数", "number", "W/(m2*K)", nullable=True),
        OutputField("sherwood_number", "Sherwood数", "number", "1", nullable=True),
        OutputField("mass_transfer_coefficient_m_s", "对流传质系数", "number", "m/s", nullable=True),
        OutputField("conduction_limit_number", "静止球体纯扩散极限", "number", "1"),
        OutputField("heat_definition_residual_w_m2_k", "换热系数定义残差", "number", "W/(m2*K)", nullable=True),
        OutputField("mass_definition_residual_m_s", "传质系数定义残差", "number", "m/s", nullable=True),
        OutputField("correlation_version", "关联式版本", "string"),
    ]
    validation_rules = [
        {"rule": "0<=Re<=200"},
        {"rule": "complete_heat_pair_or_complete_mass_pair"},
        {"rule": "0.7<=Pr<=380_and_0.6<=Sc<=3000"},
        {"rule": "Nu_Sh_and_dimensional_coefficient_identity"},
    ]
    qualification_cases = [
        {"id": "C012-N1", "kind": "normal", "input": {"reynolds_number": 100, "characteristic_diameter_m": 0.01, "prandtl_number": 0.71, "thermal_conductivity_w_m_k": 0.026}},
        {"id": "C012-N2", "kind": "normal", "input": {"reynolds_number": 50, "characteristic_diameter_m": 0.005, "schmidt_number": 0.9, "mass_diffusivity_m2_s": 2e-5}},
        {"id": "C012-N3", "kind": "normal", "input": {"reynolds_number": 20, "characteristic_diameter_m": 0.02, "prandtl_number": 7, "thermal_conductivity_w_m_k": 0.6, "schmidt_number": 500, "mass_diffusivity_m2_s": 1e-9}},
        {"id": "C012-B1", "kind": "boundary", "input": {"reynolds_number": 0, "characteristic_diameter_m": 0.01, "prandtl_number": 1, "thermal_conductivity_w_m_k": 0.1, "schmidt_number": 1, "mass_diffusivity_m2_s": 1e-5}},
        {"id": "C012-F1", "kind": "failure", "input": {"reynolds_number": 10, "characteristic_diameter_m": 0.01, "prandtl_number": 1}},
        {"id": "C012-F2", "kind": "failure", "input": {"reynolds_number": 250, "characteristic_diameter_m": 0.01, "prandtl_number": 1, "thermal_conductivity_w_m_k": 0.1}},
    ]

    def invoke(self, params: dict, context=None) -> ModelResult:
        reynolds, error = finite(params.get("reynolds_number"), "reynolds_number", minimum=0, maximum=200)
        if error:
            return fail(error, "OUT_OF_DOMAIN" if params.get("reynolds_number") is not None else "INVALID_INPUT")
        diameter, error = finite(params.get("characteristic_diameter_m"), "characteristic_diameter_m", minimum=0, strict_minimum=True)
        if error:
            return fail(error)
        heat_values = (params.get("prandtl_number"), params.get("thermal_conductivity_w_m_k"))
        mass_values = (params.get("schmidt_number"), params.get("mass_diffusivity_m2_s"))
        heat_provided = [value is not None for value in heat_values]
        mass_provided = [value is not None for value in mass_values]
        if any(heat_provided) and not all(heat_provided):
            return fail("热支路必须同时提供prandtl_number和thermal_conductivity_w_m_k", "MISSING_DATA")
        if any(mass_provided) and not all(mass_provided):
            return fail("质传递支路必须同时提供schmidt_number和mass_diffusivity_m2_s", "MISSING_DATA")
        if not all(heat_provided) and not all(mass_provided):
            return fail("至少需要一组完整的热支路或质传递支路输入", "MISSING_DATA")

        nusselt = heat_coefficient = heat_residual = None
        if all(heat_provided):
            prandtl, error = finite(heat_values[0], "prandtl_number", minimum=0.7, maximum=380)
            if error:
                return fail(error, "OUT_OF_DOMAIN")
            conductivity, error = finite(heat_values[1], "thermal_conductivity_w_m_k", minimum=0, strict_minimum=True)
            if error:
                return fail(error)
            nusselt = 2.0 + 0.6 * math.sqrt(reynolds) * prandtl ** (1.0 / 3.0)
            heat_coefficient = nusselt * conductivity / diameter
            heat_residual = heat_coefficient - nusselt * conductivity / diameter

        sherwood = mass_coefficient = mass_residual = None
        if all(mass_provided):
            schmidt, error = finite(mass_values[0], "schmidt_number", minimum=0.6, maximum=3000)
            if error:
                return fail(error, "OUT_OF_DOMAIN")
            diffusivity, error = finite(mass_values[1], "mass_diffusivity_m2_s", minimum=0, strict_minimum=True)
            if error:
                return fail(error)
            sherwood = 2.0 + 0.6 * math.sqrt(reynolds) * schmidt ** (1.0 / 3.0)
            mass_coefficient = sherwood * diffusivity / diameter
            mass_residual = mass_coefficient - sherwood * diffusivity / diameter

        outputs = [value for value in (nusselt, heat_coefficient, sherwood, mass_coefficient) if value is not None]
        if any(not math.isfinite(value) for value in outputs):
            return fail("Ranz-Marshall计算结果不是有限值", "NUMERICAL_ERROR")
        warnings = []
        if reynolds == 0:
            warnings.append(BoundaryWarning("reynolds_number", "Re=0，返回静止球体纯扩散极限Nu/Sh=2"))
        return ModelResult(True, result={
            "nusselt_number": nusselt,
            "heat_transfer_coefficient_w_m2_k": heat_coefficient,
            "sherwood_number": sherwood,
            "mass_transfer_coefficient_m_s": mass_coefficient,
            "conduction_limit_number": 2.0,
            "heat_definition_residual_w_m2_k": heat_residual,
            "mass_definition_residual_m_s": mass_residual,
            "correlation_version": "ranz-marshall-sphere-1952-v1",
        }, boundary_check=BoundaryCheck(not warnings, warnings))
