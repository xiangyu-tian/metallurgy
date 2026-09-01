"""P1-W9 transport-property tools with fixed, reviewable formula versions."""

from __future__ import annotations

import math
from typing import Any, Optional

from .base import BaseModelTool, BoundaryCheck, BoundaryWarning, InputField, ModelResult, OutputField


SCENARIO = "动力学与扩散"


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


class W9TransportTool(BaseModelTool):
    scenario = SCENARIO
    priority = "P2"
    status = "qualified"
    qualification_status = "qualified"
    count_eligible = True
    data_requirement = "FORMULA_ONLY"
    data_access_mode = "none"


class C009_ThermalConductivityMixing(W9TransportTool):
    model_id, name, version = "C009", "导热系数混合规则", "1.0.0"
    tool_name = "metallurgy_calculate_effective_thermal_conductivity"
    description = "按串联、并联或二相Maxwell–Eucken模型计算多相材料有效导热系数及严格串并联界。"
    applicable_boundary = (
        "各相为各向同性均匀介质且体积分数和为1；Maxwell–Eucken仅适用于连续基体中互不接触的球形夹杂，"
        "不含辐射、接触热阻、渗流和温度依赖。"
    )
    data_source = ["Series/parallel thermal-resistance bounds", "Maxwell-Eucken two-phase model"]
    source_version = "series-parallel-v1; Maxwell-Eucken-classical-v1"
    formula_reference = (
        "k_parallel=sum(phi_i*k_i); k_series=1/sum(phi_i/k_i); "
        "k_ME=k_m*(k_i+2k_m+2phi_i(k_i-k_m))/(k_i+2k_m-phi_i(k_i-k_m))"
    )
    source_records = [
        {"source_id": "MAXWELL-EUCKEN", "name": "Classical Maxwell-Eucken effective conductivity model", "version": "two-phase spherical-inclusion form", "url": "https://ntrs.nasa.gov/api/citations/20100036467/downloads/20100036467.pdf"},
        {"source_id": "THERMAL-RESISTANCE-BOUNDS", "name": "Series and parallel conduction bounds", "version": "v1"},
    ]
    failure_modes = ["相数组为空或名称重复", "导热系数非正", "体积分数不在[0,1]或和不为1", "Maxwell–Eucken不是二相或未指定有效基体"]
    independent_validation = ["并联值为体积分数加权算术平均", "串联值为体积分数加权调和平均", "所有相导热系数相同时三种模型返回该值", "交换整体导热系数量纲缩放时结果同比缩放"]
    dependencies = []
    relations = [
        rel("upstream_of", "T001", "有效导热系数可作为平板导热输入"),
        rel("upstream_of", "F005", "铸坯多相等效导热系数可作为凝固传热输入"),
        rel("overlaps", "B003", "均处理材料热物性，但B003计算显热而本工具计算有效导热系数"),
    ]
    input_fields = [
        InputField("phases", "相及体积分数", "array", items={"type": "object"}, min_items=1, description="[{name,conductivity_w_m_k,volume_fraction}]"),
        InputField("method", "混合模型", "select", enum=["parallel", "series", "maxwell_eucken"]),
        InputField("matrix_phase", "连续基体相名", "string", required=False, description="Maxwell–Eucken时必填"),
        InputField("fraction_tolerance", "体积分数和容差", "number", required=False, default=1e-9, unit="1", min_value=0, max_value=1e-3),
    ]
    output_fields = [
        OutputField("method", "所用模型", "string"),
        OutputField("normalized_phases", "规范化相输入", "array"),
        OutputField("effective_conductivity_w_m_k", "有效导热系数", "number", "W/(m*K)"),
        OutputField("series_bound_w_m_k", "串联界", "number", "W/(m*K)"),
        OutputField("parallel_bound_w_m_k", "并联界", "number", "W/(m*K)"),
        OutputField("matrix_phase", "连续基体相", "string", nullable=True),
        OutputField("inclusion_volume_fraction", "夹杂体积分数", "number", "1", nullable=True),
    ]
    validation_rules = [
        {"rule": "positive_conductivity_and_closed_volume_fraction", "field": "phases"},
        {"rule": "binary_matrix_inclusion_for_maxwell_eucken", "fields": ["method", "matrix_phase"]},
    ]
    qualification_cases = [
        {"id": "C009-N1", "kind": "normal", "input": {"phases": [{"name": "solid", "conductivity_w_m_k": 10, "volume_fraction": 0.6}, {"name": "gas", "conductivity_w_m_k": 1, "volume_fraction": 0.4}], "method": "parallel"}},
        {"id": "C009-N2", "kind": "normal", "input": {"phases": [{"name": "a", "conductivity_w_m_k": 4, "volume_fraction": 0.25}, {"name": "b", "conductivity_w_m_k": 1, "volume_fraction": 0.75}], "method": "series"}},
        {"id": "C009-N3", "kind": "normal", "input": {"phases": [{"name": "matrix", "conductivity_w_m_k": 10, "volume_fraction": 0.8}, {"name": "inclusion", "conductivity_w_m_k": 1, "volume_fraction": 0.2}], "method": "maxwell_eucken", "matrix_phase": "matrix"}},
        {"id": "C009-B1", "kind": "boundary", "input": {"phases": [{"name": "matrix", "conductivity_w_m_k": 10, "volume_fraction": 1}, {"name": "inclusion", "conductivity_w_m_k": 1, "volume_fraction": 0}], "method": "maxwell_eucken", "matrix_phase": "matrix"}},
        {"id": "C009-F1", "kind": "failure", "input": {"phases": [{"name": "a", "conductivity_w_m_k": 1, "volume_fraction": 0.8}, {"name": "b", "conductivity_w_m_k": 2, "volume_fraction": 0.3}], "method": "parallel"}},
    ]

    def invoke(self, params, context=None):
        raw = params.get("phases")
        if not isinstance(raw, list) or not raw:
            return fail("phases必须是非空数组")
        phases, names = [], set()
        for index, item in enumerate(raw):
            if not isinstance(item, dict):
                return fail(f"phases[{index}]必须是对象")
            name = item.get("name")
            if not isinstance(name, str) or not name.strip():
                return fail(f"phases[{index}].name必须是唯一非空字符串")
            name = name.strip()
            if name in names:
                return fail(f"phases[{index}].name必须是唯一非空字符串")
            conductivity, error = finite(item.get("conductivity_w_m_k"), f"phases[{index}].conductivity_w_m_k", minimum=0, strict_minimum=True)
            if error:
                return fail(error)
            fraction, error = finite(item.get("volume_fraction"), f"phases[{index}].volume_fraction", minimum=0, maximum=1)
            if error:
                return fail(error)
            names.add(name)
            phases.append({"name": name, "conductivity_w_m_k": conductivity, "volume_fraction": fraction})
        fraction_sum = math.fsum(row["volume_fraction"] for row in phases)
        tolerance = float(params.get("fraction_tolerance", 1e-9))
        if abs(fraction_sum - 1.0) > tolerance:
            return fail(f"体积分数和必须在容差内等于1，当前为{fraction_sum:g}", "MASS_BALANCE_ERROR")
        # Normalise tiny floating-point closure errors without changing declared physics.
        normalized = [{**row, "volume_fraction": row["volume_fraction"] / fraction_sum} for row in phases]
        series = 1.0 / math.fsum(row["volume_fraction"] / row["conductivity_w_m_k"] for row in normalized)
        parallel = math.fsum(row["volume_fraction"] * row["conductivity_w_m_k"] for row in normalized)
        method = params["method"]
        matrix_name = None
        inclusion_fraction = None
        warnings = []
        if method == "series":
            effective = series
        elif method == "parallel":
            effective = parallel
        else:
            if len(normalized) != 2:
                return fail("Maxwell–Eucken模型只接受二相", "OUT_OF_DOMAIN")
            raw_matrix_name = params.get("matrix_phase")
            matrix_name = raw_matrix_name.strip() if isinstance(raw_matrix_name, str) else raw_matrix_name
            if matrix_name not in names:
                return fail("Maxwell–Eucken必须指定存在的matrix_phase", "INVALID_INPUT")
            matrix = next(row for row in normalized if row["name"] == matrix_name)
            inclusion = next(row for row in normalized if row["name"] != matrix_name)
            km, ki, inclusion_fraction = matrix["conductivity_w_m_k"], inclusion["conductivity_w_m_k"], inclusion["volume_fraction"]
            denominator = ki + 2 * km - inclusion_fraction * (ki - km)
            if denominator <= 0:
                return fail("Maxwell–Eucken分母非正", "OUT_OF_DOMAIN")
            effective = km * (ki + 2 * km + 2 * inclusion_fraction * (ki - km)) / denominator
            if inclusion_fraction in {0.0, 1.0}:
                warnings.append(BoundaryWarning("phases", "夹杂体积分数位于纯相极限，模型退化为单相"))
        return ModelResult(True, result={
            "method": method,
            "normalized_phases": normalized,
            "effective_conductivity_w_m_k": effective,
            "series_bound_w_m_k": series,
            "parallel_bound_w_m_k": parallel,
            "matrix_phase": matrix_name,
            "inclusion_volume_fraction": inclusion_fraction,
        }, boundary_check=BoundaryCheck(not warnings, warnings))


class C010_PackedBedMassTransfer(W9TransportTool):
    model_id, name, version = "C010", "填充床颗粒-流体传质系数", "1.0.0"
    tool_name = "metallurgy_calculate_packed_bed_mass_transfer"
    description = "按Wakao–Funazkri关联式计算填充床颗粒-流体Re、Sc、Sh和膜传质系数。"
    applicable_boundary = "等效球形颗粒填充床；3≤Re≤10000；流体物性和扩散系数在膜层尺度视为常数。"
    data_source = ["Wakao and Funazkri packed-bed particle-to-fluid mass-transfer correlation"]
    source_version = "Wakao-Funazkri-1978"
    formula_reference = "Re=rho*u*d_p/mu; Sc=mu/(rho*D); Sh=2+1.1*Re^0.6*Sc^(1/3); k_m=Sh*D/d_p"
    source_records = [
        {"source_id": "WAKAO-FUNAZKRI-1978", "name": "Effect of fluid dispersion coefficients on particle-to-fluid mass transfer coefficients in packed beds", "version": "Chemical Engineering Science 33 (1978) 1375-1384", "url": "https://doi.org/10.1016/0009-2509(78)85120-3"},
    ]
    failure_modes = ["粒径、速度、密度、黏度或扩散系数非正", "Re低于3或高于10000", "输入不是有限数值"]
    independent_validation = ["Re、Sc按定义独立复算", "Sh减去2与Re^0.6和Sc^(1/3)成比例", "k_m*d_p/D等于Sh", "固定Re和Sc同比缩放D/d_p时k_m同比缩放"]
    dependencies = ["C002"]
    relations = [
        rel("depends_on", "C002", "分子扩散系数可由C002或实验数据提供"),
        rel("upstream_of", "C006", "外部膜传质系数可用于缩核模型的传质控制扩展"),
        rel("overlaps", "E014", "共用填充床粒径和流体物性，但本工具计算传质而E014计算压降"),
    ]
    input_fields = [
        InputField("superficial_velocity_m_s", "表观速度", "number", unit="m/s", min_value=0),
        InputField("particle_diameter_m", "颗粒等效直径", "number", unit="m", min_value=1e-12),
        InputField("fluid_density_kg_m3", "流体密度", "number", unit="kg/m3", min_value=1e-12),
        InputField("dynamic_viscosity_pa_s", "动力黏度", "number", unit="Pa*s", min_value=1e-18),
        InputField("diffusivity_m2_s", "分子扩散系数", "number", unit="m2/s", min_value=1e-20),
    ]
    output_fields = [
        OutputField("correlation", "关联式版本", "string"),
        OutputField("reynolds_number", "颗粒Reynolds数", "number", "1"),
        OutputField("schmidt_number", "Schmidt数", "number", "1"),
        OutputField("sherwood_number", "Sherwood数", "number", "1"),
        OutputField("mass_transfer_coefficient_m_s", "膜传质系数", "number", "m/s"),
        OutputField("reynolds_applicable_range", "Re适用域", "array"),
    ]
    validation_rules = [{"rule": "strictly_positive_transport_inputs"}, {"rule": "reynolds_within_3_to_10000"}]
    qualification_cases = [
        {"id": "C010-N1", "kind": "normal", "input": {"superficial_velocity_m_s": 1, "particle_diameter_m": 0.01, "fluid_density_kg_m3": 1.2, "dynamic_viscosity_pa_s": 1.8e-5, "diffusivity_m2_s": 2e-5}},
        {"id": "C010-N2", "kind": "normal", "input": {"superficial_velocity_m_s": 0.2, "particle_diameter_m": 0.005, "fluid_density_kg_m3": 1000, "dynamic_viscosity_pa_s": 0.001, "diffusivity_m2_s": 1e-9}},
        {"id": "C010-N3", "kind": "normal", "input": {"superficial_velocity_m_s": 2, "particle_diameter_m": 0.02, "fluid_density_kg_m3": 0.9, "dynamic_viscosity_pa_s": 2e-5, "diffusivity_m2_s": 3e-5}},
        {"id": "C010-B1", "kind": "boundary", "input": {"superficial_velocity_m_s": 3, "particle_diameter_m": 1, "fluid_density_kg_m3": 1, "dynamic_viscosity_pa_s": 1, "diffusivity_m2_s": 0.1}},
        {"id": "C010-F1", "kind": "failure", "input": {"superficial_velocity_m_s": 0.1, "particle_diameter_m": 0.01, "fluid_density_kg_m3": 1, "dynamic_viscosity_pa_s": 1, "diffusivity_m2_s": 1e-5}},
    ]

    def invoke(self, params, context=None):
        parsed = {}
        for field in self.input_fields:
            value, error = finite(params.get(field.name), field.name, minimum=0, strict_minimum=True)
            if error:
                return fail(error)
            parsed[field.name] = value
        reynolds = (parsed["fluid_density_kg_m3"] * parsed["superficial_velocity_m_s"] * parsed["particle_diameter_m"] / parsed["dynamic_viscosity_pa_s"])
        if reynolds < 3 or reynolds > 10000:
            return fail(f"Re={reynolds:g}超出Wakao–Funazkri适用域[3,10000]", "OUT_OF_DOMAIN")
        schmidt = parsed["dynamic_viscosity_pa_s"] / (parsed["fluid_density_kg_m3"] * parsed["diffusivity_m2_s"])
        sherwood = 2.0 + 1.1 * reynolds ** 0.6 * schmidt ** (1.0 / 3.0)
        coefficient = sherwood * parsed["diffusivity_m2_s"] / parsed["particle_diameter_m"]
        warnings = []
        if math.isclose(reynolds, 3.0, rel_tol=0, abs_tol=1e-12) or math.isclose(reynolds, 10000.0, rel_tol=0, abs_tol=1e-9):
            warnings.append(BoundaryWarning("reynolds_number", "Re位于关联式验证区间边界"))
        return ModelResult(True, result={
            "correlation": "Wakao-Funazkri-1978",
            "reynolds_number": reynolds,
            "schmidt_number": schmidt,
            "sherwood_number": sherwood,
            "mass_transfer_coefficient_m_s": coefficient,
            "reynolds_applicable_range": [3.0, 10000.0],
        }, boundary_check=BoundaryCheck(not warnings, warnings))
