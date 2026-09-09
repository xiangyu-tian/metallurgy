"""P1-W8 numerical mesh-planning and explicit time-step verification tools."""

from __future__ import annotations

import math
from functools import reduce
from operator import mul
from typing import Optional

from .base import BaseModelTool, BoundaryCheck, BoundaryWarning, InputField, ModelResult, OutputField


SCENARIO = "数值方法与仿真"


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


RESOLUTION_DRIVER_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "name": {"type": "string", "description": "唯一物理尺度名称"},
        "characteristic_length_m": {"type": "number", "exclusiveMinimum": 0, "description": "需解析的特征尺度；单位: m"},
        "minimum_cells": {"type": "integer", "minimum": 2, "maximum": 100000, "description": "跨越该尺度的最低单元数；单位: 1"},
    },
    "required": ["name", "characteristic_length_m", "minimum_cells"],
}


class G001_MeshScaleEstimate(BaseModelTool):
    model_id, name, version = "G001", "网格尺度估计", "1.0.0"
    tool_name = "metallurgy_plan_mesh_scale_and_gci"
    scenario, priority = SCENARIO, "P1"
    status = qualification_status = "qualified"
    count_eligible = True
    data_requirement, data_access_mode = "FORMULA_ONLY", "none"
    model_type = "确定性网格规划/可选GCI验证"
    description = "由显式物理分辨率驱动生成粗中细三网格计划；可选用同一QOI的三网格结果计算观察阶、Richardson外推和细网格GCI。"
    applicable_boundary = "结构化各向同性目标网格；所有轴使用同一名义dx。GCI只接受固定细化比、同一离散格式和单调渐近收敛的三个QOI。"
    formula_reference = (
        "dx_target=min(L_driver/N_driver); N_axis=ceil(L_axis/dx); "
        "p=ln(|Q_c-Q_m|/|Q_m-Q_f|)/ln(r); "
        "Q_ext=Q_f+(Q_f-Q_m)/(r^p-1); GCI_f=1.25*|Q_f-Q_m|/[|Q_f|(r^p-1)]"
    )
    data_source = ["NASA grid convergence and verification guidance", "Richardson extrapolation"]
    source_version = "mesh-plan-gci-v1; NASA-TM-2000-209946; NASA-TP-2016-219422"
    source_records = [
        {"source_id": "NASA-TM-2000-209946", "name": "Examining Spatial (Grid) Convergence", "version": "2000", "url": "https://ntrs.nasa.gov/api/citations/20000054672/downloads/20000054672.pdf"},
        {"source_id": "NASA-TP-2016-219422", "name": "Examining Spatial (Grid) Convergence for CFD", "version": "2016", "url": "https://ntrs.nasa.gov/api/citations/20160013550/downloads/20160013550.pdf?attachment=true"},
    ]
    failure_modes = ["域轴或分辨率驱动为空、重名或数值非法", "细化比不大于1", "QOI不是三个有限数", "QOI不单调收敛或差值为零", "细网格QOI为零导致相对GCI无定义"]
    independent_validation = ["推荐dx等于所有特征尺度/最低单元数中的最小值", "各轴单元数向上取整后实际dx不大于名义dx", "合成二阶序列恢复p=2和已知Richardson极限", "细化比增大时三层名义dx保持固定几何比"]
    dependencies = []
    relations = [
        rel("upstream_of", "C103", "G001网格计划可作为一维Fick数值PDE的离散输入"),
        rel("upstream_of", "F005", "G001可为一维坯壳PDE提供独立网格加密计划"),
        rel("upstream_of", "G002", "G001输出的网格宽度可进入显式稳定性校验"),
    ]
    input_fields = [
        InputField("domain_lengths_m", "各轴计算域长度", "object", unit="m", description="1至3个唯一非空轴名到正长度的映射，例如{x:1,y:0.5}", json_schema={"type": "object", "minProperties": 1, "maxProperties": 3, "propertyNames": {"type": "string", "minLength": 1}, "additionalProperties": {"type": "number", "minimum": 1e-12}}),
        InputField("resolution_drivers", "分辨率驱动", "array", items=RESOLUTION_DRIVER_SCHEMA, min_items=1, max_items=100),
        InputField("refinement_ratio", "相邻网格细化比", "number", required=False, default=2.0, unit="1", min_value=1.1, max_value=4.0),
        InputField("qoi_values_coarse_to_fine", "粗中细网格同一QOI", "array", required=False, items={"type": "number"}, min_items=3, max_items=3, description="可选；顺序严格为coarse, medium, fine，三者单位相同"),
        InputField("qoi_name", "QOI名称", "string", required=False, description="提供QOI数组时必填"),
    ]
    output_fields = [
        OutputField("limiting_driver", "限制网格的物理尺度", "object"),
        OutputField("recommended_cell_size_m", "推荐中网格名义尺寸", "number", "m"),
        OutputField("refinement_ratio", "相邻网格细化比", "number", "1"),
        OutputField("mesh_plan", "粗中细三网格计划", "array", "cell_size:m; cells:1"),
        OutputField("observed_order", "观察收敛阶", "number", "1", nullable=True),
        OutputField("richardson_extrapolated_qoi", "Richardson外推QOI", "number", "same as QOI", nullable=True),
        OutputField("fine_grid_gci_percent", "细网格GCI", "number", "%", nullable=True),
        OutputField("qoi_name", "QOI名称", "string"),
        OutputField("verification_status", "验证状态", "string"),
    ]
    validation_rules = [{"rule": "resolve_each_driver_with_minimum_cells"}, {"rule": "three_geometrically_refined_grids"}, {"rule": "gci_only_for_monotonic_asymptotic_qoi"}]
    _COMMON = {
        "domain_lengths_m": {"x": 1.0, "y": 0.5},
        "resolution_drivers": [{"name": "boundary_layer", "characteristic_length_m": 0.1, "minimum_cells": 10}],
    }
    qualification_cases = [
        {"id": "G001-N1", "kind": "normal", "input": _COMMON},
        {"id": "G001-N2", "kind": "normal", "input": {"domain_lengths_m": {"x": 2.0}, "resolution_drivers": [{"name": "thermal_layer", "characteristic_length_m": 0.2, "minimum_cells": 10}, {"name": "particle", "characteristic_length_m": 0.03, "minimum_cells": 6}], "refinement_ratio": 1.5}},
        {"id": "G001-N3", "kind": "normal", "input": {**_COMMON, "qoi_values_coarse_to_fine": [1.04, 1.01, 1.0025], "qoi_name": "synthetic_second_order_temperature"}},
        {"id": "G001-B1", "kind": "boundary", "input": {"domain_lengths_m": {"x": 0.1}, "resolution_drivers": [{"name": "minimum_resolution", "characteristic_length_m": 0.1, "minimum_cells": 2}]}},
        {"id": "G001-F1", "kind": "failure", "input": {**_COMMON, "qoi_values_coarse_to_fine": [1.0, 0.9, 0.95], "qoi_name": "oscillatory"}},
    ]

    @staticmethod
    def _domains(raw):
        if not isinstance(raw, dict) or not raw or len(raw) > 3:
            return None, "domain_lengths_m必须包含1到3个轴"
        parsed = {}
        for axis, value in raw.items():
            if not isinstance(axis, str) or not axis.strip() or axis.strip() in parsed:
                return None, "domain_lengths_m轴名必须唯一且非空"
            number, error = finite(value, f"domain_lengths_m.{axis}", minimum=1e-12)
            if error: return None, error
            parsed[axis.strip()] = number
        return parsed, None

    @staticmethod
    def _drivers(raw):
        if not isinstance(raw, list) or not raw or len(raw) > 100:
            return None, "resolution_drivers必须包含1到100项"
        parsed, names = [], set()
        for index, item in enumerate(raw):
            if not isinstance(item, dict) or set(item) != {"name", "characteristic_length_m", "minimum_cells"}:
                return None, f"resolution_drivers[{index}]字段不完整或含未声明字段"
            name = item["name"]
            normalized_name = name.strip() if isinstance(name, str) else ""
            if not normalized_name or normalized_name in names:
                return None, f"resolution_drivers[{index}].name必须唯一且非空"
            names.add(normalized_name)
            length, error = finite(item["characteristic_length_m"], f"resolution_drivers[{index}].characteristic_length_m", minimum=1e-12)
            if error: return None, error
            cells = item["minimum_cells"]
            if isinstance(cells, bool) or not isinstance(cells, int) or not 2 <= cells <= 100000:
                return None, f"resolution_drivers[{index}].minimum_cells必须是2到100000的整数"
            parsed.append({"name": normalized_name, "characteristic_length_m": length,
                           "minimum_cells": cells, "required_cell_size_m": length / cells})
        return parsed, None

    def invoke(self, params, context=None):
        domains, error = self._domains(params["domain_lengths_m"])
        if error: return fail(error)
        drivers, error = self._drivers(params["resolution_drivers"])
        if error: return fail(error)
        ratio = float(params.get("refinement_ratio", 2.0))
        limiting = min(drivers, key=lambda item: item["required_cell_size_m"])
        recommended = limiting["required_cell_size_m"]
        plans = []
        for level, nominal in (("coarse", recommended * ratio), ("medium", recommended), ("fine", recommended / ratio)):
            axis_cells = {axis: int(math.ceil(length / nominal)) for axis, length in domains.items()}
            actual_sizes = {axis: domains[axis] / axis_cells[axis] for axis in domains}
            plans.append({"level": level, "nominal_cell_size_m": nominal,
                          "axis_cell_counts": axis_cells, "axis_actual_cell_sizes_m": actual_sizes,
                          "estimated_total_cells": reduce(mul, axis_cells.values(), 1)})
        qoi = params.get("qoi_values_coarse_to_fine")
        qoi_name = params.get("qoi_name", "")
        observed = extrapolated = gci = None
        verification = "mesh_plan_only"
        warnings = []
        if qoi is None:
            warnings.append(BoundaryWarning("qoi_values_coarse_to_fine", "未提供三网格QOI，仅生成网格计划，不计算GCI"))
        else:
            if not isinstance(qoi, list) or len(qoi) != 3:
                return fail("qoi_values_coarse_to_fine必须恰含粗、中、细三个值")
            if not isinstance(qoi_name, str) or not qoi_name.strip():
                return fail("提供QOI数组时qoi_name必须是非空字符串")
            values = []
            for index, value in enumerate(qoi):
                number, error = finite(value, f"qoi_values_coarse_to_fine[{index}]")
                if error: return fail(error)
                values.append(number)
            coarse, medium, fine = values
            delta_cm, delta_mf = coarse - medium, medium - fine
            if delta_cm == 0 or delta_mf == 0:
                return fail("QOI相邻网格差值为零，观察阶无定义", "MODEL_NOT_APPLICABLE")
            if delta_cm * delta_mf <= 0:
                return fail("QOI未呈单调收敛，首版GCI模型不适用", "MODEL_NOT_APPLICABLE")
            ratio_of_differences = abs(delta_cm / delta_mf)
            observed = math.log(ratio_of_differences) / math.log(ratio)
            if not math.isfinite(observed) or observed <= 0:
                return fail("观察收敛阶非正，未进入渐近收敛区", "MODEL_NOT_APPLICABLE")
            denominator = ratio ** observed - 1.0
            if denominator <= 0 or fine == 0:
                return fail("Richardson/GCI分母为零或非正", "DIVISION_BY_ZERO")
            extrapolated = fine + (fine - medium) / denominator
            gci = 1.25 * abs(fine - medium) / (abs(fine) * denominator) * 100.0
            verification = "monotonic_gci_computed"
        if any(driver["minimum_cells"] == 2 for driver in drivers):
            warnings.append(BoundaryWarning("resolution_drivers", "最低单元数位于允许下限，只适合边界验证"))
        return ModelResult(True, result={
            "limiting_driver": limiting, "recommended_cell_size_m": recommended,
            "refinement_ratio": ratio, "mesh_plan": plans, "observed_order": observed,
            "richardson_extrapolated_qoi": extrapolated, "fine_grid_gci_percent": gci,
            "qoi_name": qoi_name.strip() if isinstance(qoi_name, str) else "",
            "verification_status": verification,
        }, boundary_check=BoundaryCheck(not warnings, warnings))


class G002_TimeStepCFLCheck(BaseModelTool):
    model_id, name, version = "G002", "时间步与CFL校验", "1.0.0"
    tool_name = "metallurgy_check_explicit_timestep_stability"
    scenario, priority = SCENARIO, "P1"
    status = qualification_status = "qualified"
    count_eligible = True
    data_requirement, data_access_mode = "FORMULA_ONLY", "none"
    model_type = "确定性显式稳定性判据"
    description = "计算一至三维显式一阶迎风对流CFL和显式中心扩散Fourier数，返回最大时间步、限制机制与稳定结论。"
    applicable_boundary = "仅适用于正交结构网格、显式一阶迎风对流和显式二阶中心扩散；隐式、高阶、非结构或耦合源项格式不适用。"
    formula_reference = "CFL_sum=dt*sum(|u_i|/dx_i); Fo_sum=dt*sum(alpha_i/dx_i^2); dt_max=min(CFL_target/Su,Fo_target/Sa)"
    data_source = ["Courant-Friedrichs-Lewy necessary stability condition", "Explicit central-difference diffusion stability"]
    source_version = "explicit-cfl-fourier-check-v1; CFL-1928-English-translation"
    source_records = [
        {"source_id": "CFL-1928", "name": "On the Partial Difference Equations of Mathematical Physics", "version": "1928/English translation", "url": "https://galton.uchicago.edu/~lekheng/courses/302/classics/courant-friedrichs-lewy.pdf"},
        {"source_id": "EXPLICIT-DIFFUSION-STABILITY", "name": "Explicit central-difference diffusion stability identity", "version": "v1"},
    ]
    failure_modes = ["网格/速度/扩散率维数不一致", "所有机制均禁用", "启用机制但缺对应数组", "时间步、网格或物性非法", "请求未支持的数值格式"]
    independent_validation = ["一维CFL=u*dt/dx手算", "多维总CFL等于各轴分项和", "扩散Fourier数等于alpha*dt/dx^2分项和", "返回最大时间步代回后恰达到对应目标阈值"]
    dependencies = []
    relations = [
        rel("consumes_output_from", "G001", "G001网格宽度可直接作为cell_sizes_m"),
        rel("upstream_of", "C103", "在显式扩散实现中可用于选择稳定时间步；当前C103仍使用自身契约"),
        rel("upstream_of", "F005", "可审计显式替代求解器的时间步；F005当前隐式求解不受此判据充分约束"),
    ]
    input_fields = [
        InputField("cell_sizes_m", "各轴网格宽度", "array", items={"type": "number", "exclusiveMinimum": 0}, min_items=1, max_items=3, description="一至三维；单位: m"),
        InputField("time_step_s", "待校验时间步", "number", unit="s", min_value=1e-15),
        InputField("advection_scheme", "对流离散格式", "select", enum=["none", "explicit_first_order_upwind"]),
        InputField("velocity_components_m_s", "各轴速度分量", "array", required=False, items={"type": "number"}, min_items=1, max_items=3, description="启用对流时必填；单位: m/s"),
        InputField("diffusion_scheme", "扩散离散格式", "select", enum=["none", "explicit_central"]),
        InputField("diffusivity_components_m2_s", "各轴扩散率", "array", required=False, items={"type": "number", "minimum": 0}, min_items=1, max_items=3, description="启用扩散时必填；单位: m²/s"),
        InputField("target_cfl", "目标总CFL上限", "number", required=False, default=1.0, unit="1", min_value=1e-12),
        InputField("target_fourier", "目标总Fourier上限", "number", required=False, default=0.5, unit="1", min_value=1e-12),
    ]
    output_fields = [
        OutputField("advection_cfl_components", "各轴CFL", "array", "1"),
        OutputField("total_advection_cfl", "总CFL", "number", "1"),
        OutputField("diffusion_fourier_components", "各轴Fourier数", "array", "1"),
        OutputField("total_diffusion_fourier", "总Fourier数", "number", "1"),
        OutputField("maximum_advection_time_step_s", "对流最大时间步", "number", "s", nullable=True),
        OutputField("maximum_diffusion_time_step_s", "扩散最大时间步", "number", "s", nullable=True),
        OutputField("maximum_stable_time_step_s", "综合最大时间步", "number", "s", nullable=True),
        OutputField("limiting_mechanism", "限制机制", "string"),
        OutputField("advection_stable", "对流是否满足目标", "boolean"),
        OutputField("diffusion_stable", "扩散是否满足目标", "boolean"),
        OutputField("stable", "综合是否稳定", "boolean"),
        OutputField("time_step_margin_fraction", "相对最大步长余量", "number", "1", nullable=True),
    ]
    validation_rules = [{"rule": "one_to_three_matching_dimensions"}, {"rule": "explicit_supported_schemes_only"}, {"rule": "summed_multidimensional_cfl_and_fourier"}]
    qualification_cases = [
        {"id": "G002-N1", "kind": "normal", "input": {"cell_sizes_m": [0.1], "time_step_s": 0.05, "advection_scheme": "explicit_first_order_upwind", "velocity_components_m_s": [1], "diffusion_scheme": "none"}},
        {"id": "G002-N2", "kind": "normal", "input": {"cell_sizes_m": [0.1], "time_step_s": 1, "advection_scheme": "none", "diffusion_scheme": "explicit_central", "diffusivity_components_m2_s": [0.001]}},
        {"id": "G002-N3", "kind": "normal", "input": {"cell_sizes_m": [0.1, 0.2], "time_step_s": 0.02, "advection_scheme": "explicit_first_order_upwind", "velocity_components_m_s": [1, 2], "diffusion_scheme": "explicit_central", "diffusivity_components_m2_s": [0.001, 0.002]}},
        {"id": "G002-B1", "kind": "boundary", "input": {"cell_sizes_m": [0.1], "time_step_s": 0.1, "advection_scheme": "explicit_first_order_upwind", "velocity_components_m_s": [1], "diffusion_scheme": "none"}},
        {"id": "G002-F1", "kind": "failure", "input": {"cell_sizes_m": [0.1, 0.2], "time_step_s": 0.01, "advection_scheme": "explicit_first_order_upwind", "velocity_components_m_s": [1], "diffusion_scheme": "none"}},
    ]

    @staticmethod
    def _array(raw, label, *, minimum=None, allow_signed=False):
        if not isinstance(raw, list) or not 1 <= len(raw) <= 3:
            return None, f"{label}必须包含1到3个分量"
        parsed = []
        for index, value in enumerate(raw):
            number, error = finite(value, f"{label}[{index}]", minimum=None if allow_signed else minimum)
            if error: return None, error
            parsed.append(number)
        return parsed, None

    def invoke(self, params, context=None):
        dx, error = self._array(params["cell_sizes_m"], "cell_sizes_m", minimum=1e-15)
        if error: return fail(error)
        advection = params["advection_scheme"]
        diffusion = params["diffusion_scheme"]
        if advection == "none" and diffusion == "none":
            return fail("advection_scheme与diffusion_scheme不能同时为none", "MODEL_NOT_APPLICABLE")
        velocity_raw = params.get("velocity_components_m_s")
        diffusivity_raw = params.get("diffusivity_components_m2_s")
        if advection == "none" and velocity_raw is not None:
            return fail("advection_scheme=none时不得提供velocity_components_m_s")
        if diffusion == "none" and diffusivity_raw is not None:
            return fail("diffusion_scheme=none时不得提供diffusivity_components_m2_s")
        velocities = []
        diffusivities = []
        if advection != "none":
            if velocity_raw is None:
                return fail("启用显式对流时必须提供velocity_components_m_s", "MISSING_DATA")
            velocities, error = self._array(velocity_raw, "velocity_components_m_s", allow_signed=True)
            if error: return fail(error)
            if len(velocities) != len(dx):
                return fail("velocity_components_m_s与cell_sizes_m维数必须一致")
        if diffusion != "none":
            if diffusivity_raw is None:
                return fail("启用显式扩散时必须提供diffusivity_components_m2_s", "MISSING_DATA")
            diffusivities, error = self._array(diffusivity_raw, "diffusivity_components_m2_s", minimum=0)
            if error: return fail(error)
            if len(diffusivities) != len(dx):
                return fail("diffusivity_components_m2_s与cell_sizes_m维数必须一致")
        dt = float(params["time_step_s"])
        target_cfl = float(params.get("target_cfl", 1.0))
        target_fo = float(params.get("target_fourier", 0.5))
        adv_coefficients = [abs(u) / width for u, width in zip(velocities, dx)]
        diff_coefficients = [alpha / width ** 2 for alpha, width in zip(diffusivities, dx)]
        cfl_components = [dt * value for value in adv_coefficients]
        fo_components = [dt * value for value in diff_coefficients]
        total_cfl = math.fsum(cfl_components)
        total_fo = math.fsum(fo_components)
        sum_adv = math.fsum(adv_coefficients)
        sum_diff = math.fsum(diff_coefficients)
        max_adv = target_cfl / sum_adv if advection != "none" and sum_adv > 0 else None
        max_diff = target_fo / sum_diff if diffusion != "none" and sum_diff > 0 else None
        limits = [("advection_cfl", max_adv), ("diffusion_fourier", max_diff)]
        finite_limits = [(name, value) for name, value in limits if value is not None]
        if finite_limits:
            limiting, max_stable = min(finite_limits, key=lambda item: item[1])
            margin = (max_stable - dt) / max_stable
        else:
            limiting, max_stable, margin = "none_zero_transport", None, None
        adv_stable = advection == "none" or total_cfl <= target_cfl + 1e-12
        diff_stable = diffusion == "none" or total_fo <= target_fo + 1e-12
        stable = adv_stable and diff_stable
        warnings = []
        if math.isclose(total_cfl, target_cfl, rel_tol=0.0, abs_tol=1e-12) or math.isclose(total_fo, target_fo, rel_tol=0.0, abs_tol=1e-12):
            warnings.append(BoundaryWarning("time_step_s", "时间步位于显式稳定性目标边界"))
        if not stable:
            warnings.append(BoundaryWarning("time_step_s", "时间步超过至少一个显式稳定性目标"))
        if not finite_limits:
            warnings.append(BoundaryWarning("transport", "启用机制的传输系数均为零，没有有限稳定性上限"))
        return ModelResult(True, result={
            "advection_cfl_components": cfl_components, "total_advection_cfl": total_cfl,
            "diffusion_fourier_components": fo_components, "total_diffusion_fourier": total_fo,
            "maximum_advection_time_step_s": max_adv,
            "maximum_diffusion_time_step_s": max_diff,
            "maximum_stable_time_step_s": max_stable, "limiting_mechanism": limiting,
            "advection_stable": adv_stable, "diffusion_stable": diff_stable,
            "stable": stable, "time_step_margin_fraction": margin,
        }, boundary_check=BoundaryCheck(not warnings, warnings))
