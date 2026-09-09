"""P1-W12 additive phase-equilibrium tools; all existing implementations stay frozen."""

from __future__ import annotations

import math
import warnings
from typing import Any

import numpy as np
from pycalphad import equilibrium, variables as v
from scheil import simulate_scheil_solidification
from scipy.interpolate import PchipInterpolator
from scipy.optimize import linprog, minimize

from .base import BaseModelTool, BoundaryCheck, BoundaryWarning, InputField, ModelResult, OutputField
from .repositories.reference_repository import RepositoryError
from .repositories.solidification_repository import load_database


R_GAS = 8.31446261815324
MODEL_ASSET_ID = "MATCALC-MC_FE-2.059-PYCALPHAD"


def rel(kind: str, target: str, description: str) -> dict[str, str]:
    return {"type": kind, "target": target, "description": description}


def fail(message: str, code: str = "INVALID_INPUT") -> ModelResult:
    return ModelResult(False, error=message, error_code=code)


def finite(value: Any, label: str) -> tuple[float | None, str | None]:
    if isinstance(value, bool):
        return None, f"{label}必须是数值"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None, f"{label}必须是数值"
    if not math.isfinite(number):
        return None, f"{label}必须是有限数值"
    return number, None


def strict_object(value: Any, required: set[str], optional: set[str], label: str) -> str | None:
    if not isinstance(value, dict):
        return f"{label}必须是对象"
    keys = set(value)
    if not required <= keys or keys - required - optional:
        return f"{label}字段必须包含{sorted(required)}且只能额外包含{sorted(optional)}"
    return None


class W12PhaseTool(BaseModelTool):
    scenario = "相平衡与溶液热力学"
    priority = "P1"
    status = qualification_status = "qualified"
    count_eligible = True
    data_requirement = "FORMULA_ONLY"
    data_access_mode = "none"


class B020_BinaryPhaseBoundaryInterpolation(W12PhaseTool):
    model_id, name, version = "B020", "二元相界保形插值", "1.0.0"
    tool_name = "metallurgy_interpolate_binary_phase_boundary"
    description = "在调用方声明来源与单位的二元相界离散点内执行不外推的线性或保形PCHIP插值。"
    model_type = "数值插值/不确定度传播"
    applicable_boundary = (
        "2至500个严格递增、有限的二元相界点；查询值必须落在闭区间；"
        "仅做一维边界插值，不从成分数据库推导相界、不外推、不判定相稳定性。"
    )
    data_source = ["Fritsch-Butland monotone piecewise cubic interpolation", "SciPy PchipInterpolator 1.18.1"]
    source_version = "Fritsch-Butland-1984; scipy-1.18.1"
    formula_reference = (
        "分段线性y=(1-w)y_i+w*y_(i+1)；PCHIP节点导数采用Fritsch-Butland保形规则；"
        "输入标准不确定度按局部数值灵敏度平方和传播"
    )
    source_records = [
        {
            "source_id": "FRITSCH-BUTLAND-1984",
            "name": "A Method for Constructing Local Monotone Piecewise Cubic Interpolants",
            "version": "SIAM J. Sci. Stat. Comput. 5(2), 1984",
            "url": "https://doi.org/10.1137/0905021",
        },
        {
            "source_id": "SCIPY-PCHIP-1.18.1",
            "name": "SciPy PchipInterpolator",
            "version": "1.18.1",
            "url": "https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.PchipInterpolator.html",
        },
    ]
    failure_modes = [
        "点数越界、点字段不完整、x或y非有限",
        "x不是调用顺序下的严格递增序列",
        "标准不确定度只给出部分点或为负",
        "查询值超出闭区间（禁止外推）",
        "PCHIP数值结果非有限",
    ]
    independent_validation = [
        "线性与PCHIP均精确重现输入节点",
        "线性数据上两种算法精确重现直线和导数",
        "单调输入的PCHIP结果位于相邻节点范围内",
        "线性插值标准不确定度由两个权重的平方和独立复算",
    ]
    dependencies = []
    relations = [
        rel("feeds", "B019", "B020可在给定温度/成分处提供两相端点，B019再由总体成分计算相分数"),
        rel("overlaps_with", "B027", "二者都可返回二元边界；B020插值调用方离散点，B027求解理想VLE方程"),
    ]
    _point_schema = {
        "type": "object",
        "properties": {
            "x": {"type": "number"},
            "y": {"type": "number"},
            "standard_uncertainty_y": {"type": "number", "minimum": 0},
        },
        "required": ["x", "y"],
        "additionalProperties": False,
    }
    input_fields = [
        InputField("points", "相界离散点", "array", items=_point_schema, min_items=2, max_items=500),
        InputField("query_value", "查询独立量", "number", unit="$independent_unit"),
        InputField("method", "插值方法", "select", enum=["linear", "pchip"]),
        InputField("boundary_kind", "相界类型", "string", description="例如liquidus、solidus或alpha_beta_boundary"),
        InputField("independent_quantity", "独立量名称", "string", description="例如temperature或composition"),
        InputField("independent_unit", "独立量单位", "string"),
        InputField("dependent_unit", "相界值单位", "string"),
        InputField("source_id", "调用方数据来源编号", "string"),
        InputField("source_version", "调用方数据版本", "string"),
    ]
    output_fields = [
        OutputField("method", "插值方法", "string"),
        OutputField("boundary_kind", "相界类型", "string"),
        OutputField("query_value", "查询值", "number", "$independent_unit"),
        OutputField("interpolated_value", "插值相界值", "number", "$dependent_unit"),
        OutputField("first_derivative", "一阶导数", "number", "$dependent_unit/$independent_unit"),
        OutputField("bracketing_interval", "包围区间", "array", "$independent_unit"),
        OutputField("exact_knot", "是否命中输入节点", "boolean"),
        OutputField("propagated_standard_uncertainty", "传播标准不确定度", "number", "$dependent_unit", nullable=True),
        OutputField("pchip_minus_linear", "PCHIP与线性结果差", "number", "$dependent_unit"),
        OutputField("independent_quantity", "独立量名称", "string"),
        OutputField("independent_unit", "独立量单位", "string"),
        OutputField("dependent_unit", "相界值单位", "string"),
        OutputField("source_id", "调用方数据来源编号", "string"),
        OutputField("source_version", "调用方数据版本", "string"),
        OutputField("algorithm_version", "算法版本", "string"),
    ]
    validation_rules = [
        {"rule": "points_strictly_increasing_and_finite"},
        {"rule": "uncertainty_present_for_all_points_or_none"},
        {"rule": "closed_interval_only_no_extrapolation"},
    ]
    qualification_cases = [
        {"id": "B020-N1", "kind": "normal", "input": {"points": [{"x": 0, "y": 1000, "standard_uncertainty_y": 2}, {"x": 0.5, "y": 1200, "standard_uncertainty_y": 3}, {"x": 1, "y": 1400, "standard_uncertainty_y": 4}], "query_value": 0.25, "method": "linear", "boundary_kind": "liquidus", "independent_quantity": "mole_fraction_B", "independent_unit": "1", "dependent_unit": "K", "source_id": "USER-PHASE-POINTS-1", "source_version": "1"}},
        {"id": "B020-N2", "kind": "normal", "input": {"points": [{"x": 900, "y": 0.1}, {"x": 1000, "y": 0.2}, {"x": 1200, "y": 0.4}], "query_value": 1100, "method": "pchip", "boundary_kind": "alpha_solubility", "independent_quantity": "temperature", "independent_unit": "K", "dependent_unit": "mole_fraction", "source_id": "USER-PHASE-POINTS-2", "source_version": "2026-09"}},
        {"id": "B020-N3", "kind": "normal", "input": {"points": [{"x": 0, "y": 0}, {"x": 1, "y": 2}, {"x": 2, "y": 4}], "query_value": 1, "method": "pchip", "boundary_kind": "test_boundary", "independent_quantity": "x", "independent_unit": "1", "dependent_unit": "1", "source_id": "ANALYTIC-LINE", "source_version": "1"}},
        {"id": "B020-B1", "kind": "boundary", "input": {"points": [{"x": 0, "y": 1000}, {"x": 1, "y": 1200}], "query_value": 0, "method": "linear", "boundary_kind": "liquidus", "independent_quantity": "composition", "independent_unit": "1", "dependent_unit": "K", "source_id": "ENDPOINT", "source_version": "1"}},
        {"id": "B020-F1", "kind": "failure", "input": {"points": [{"x": 0, "y": 1}, {"x": 0, "y": 2}], "query_value": 0, "method": "linear", "boundary_kind": "x", "independent_quantity": "x", "independent_unit": "1", "dependent_unit": "1", "source_id": "BAD", "source_version": "1"}},
        {"id": "B020-F2", "kind": "failure", "input": {"points": [{"x": 0, "y": 1}, {"x": 1, "y": 2}], "query_value": 2, "method": "pchip", "boundary_kind": "x", "independent_quantity": "x", "independent_unit": "1", "dependent_unit": "1", "source_id": "BAD", "source_version": "1"}},
    ]

    @staticmethod
    def _parse_points(payload: Any) -> tuple[np.ndarray | None, np.ndarray | None, np.ndarray | None, str | None]:
        if not isinstance(payload, list) or not 2 <= len(payload) <= 500:
            return None, None, None, "points必须含2至500项"
        x_values, y_values, uncertainties = [], [], []
        uncertainty_flags = []
        for index, point in enumerate(payload):
            error = strict_object(point, {"x", "y"}, {"standard_uncertainty_y"}, f"points[{index}]")
            if error:
                return None, None, None, error
            x, error = finite(point["x"], f"points[{index}].x")
            if error:
                return None, None, None, error
            y, error = finite(point["y"], f"points[{index}].y")
            if error:
                return None, None, None, error
            present = "standard_uncertainty_y" in point
            uncertainty_flags.append(present)
            if present:
                uncertainty, error = finite(point["standard_uncertainty_y"], f"points[{index}].standard_uncertainty_y")
                if error or uncertainty < 0:
                    return None, None, None, error or "标准不确定度不能为负"
                uncertainties.append(uncertainty)
            x_values.append(x)
            y_values.append(y)
        if any(uncertainty_flags) and not all(uncertainty_flags):
            return None, None, None, "标准不确定度必须对全部点给出或全部省略"
        x_array = np.asarray(x_values, dtype=float)
        if np.any(np.diff(x_array) <= 0):
            return None, None, None, "points.x必须按调用顺序严格递增，禁止重复或隐式排序"
        u_array = np.asarray(uncertainties, dtype=float) if all(uncertainty_flags) else None
        return x_array, np.asarray(y_values, dtype=float), u_array, None

    @staticmethod
    def _pchip_uncertainty(x: np.ndarray, y: np.ndarray, u: np.ndarray, query: float) -> float:
        sensitivities = []
        for index in range(len(y)):
            step = max(abs(float(y[index])) * 1e-7, float(u[index]) * 1e-4, 1e-8)
            upper, lower = y.copy(), y.copy()
            upper[index] += step
            lower[index] -= step
            plus = float(PchipInterpolator(x, upper, extrapolate=False)(query))
            minus = float(PchipInterpolator(x, lower, extrapolate=False)(query))
            sensitivities.append((plus - minus) / (2 * step))
        return math.sqrt(sum((weight * value) ** 2 for weight, value in zip(sensitivities, u)))

    def invoke(self, params, context=None):
        errors = self.validate_input(params)
        if errors:
            return fail("; ".join(errors))
        for field in ("boundary_kind", "independent_quantity", "independent_unit", "dependent_unit", "source_id", "source_version"):
            if not isinstance(params.get(field), str) or not params[field].strip():
                return fail(f"{field}必须是非空字符串")
        x, y, uncertainty, error = self._parse_points(params.get("points"))
        if error:
            return fail(error)
        query, error = finite(params.get("query_value"), "query_value")
        if error:
            return fail(error)
        if query < x[0] or query > x[-1]:
            return fail("query_value超出输入相界点闭区间，禁止外推", "OUT_OF_DOMAIN")
        index = int(np.searchsorted(x, query, side="right") - 1)
        index = max(0, min(index, len(x) - 2))
        weight = (query - x[index]) / (x[index + 1] - x[index])
        linear_value = float((1 - weight) * y[index] + weight * y[index + 1])
        linear_derivative = float((y[index + 1] - y[index]) / (x[index + 1] - x[index]))
        pchip = PchipInterpolator(x, y, extrapolate=False)
        pchip_value = float(pchip(query))
        if not math.isfinite(pchip_value):
            return fail("PCHIP插值返回非有限结果", "NUMERICAL_ERROR")
        method = params["method"]
        value = linear_value if method == "linear" else pchip_value
        derivative = linear_derivative if method == "linear" else float(pchip.derivative()(query))
        exact = bool(np.any(np.isclose(x, query, rtol=0, atol=1e-12 * max(1.0, abs(query)))))
        propagated = None
        if uncertainty is not None:
            if method == "linear":
                propagated = math.hypot((1 - weight) * uncertainty[index], weight * uncertainty[index + 1])
            else:
                propagated = self._pchip_uncertainty(x, y, uncertainty, query)
        warnings_out = []
        if query == x[0] or query == x[-1]:
            warnings_out.append(BoundaryWarning("query_value", "查询值位于输入闭区间端点；结果为节点值且未外推"))
        return ModelResult(
            True,
            result={
                "method": method,
                "boundary_kind": params["boundary_kind"].strip(),
                "query_value": query,
                "interpolated_value": value,
                "first_derivative": derivative,
                "bracketing_interval": [float(x[index]), float(x[index + 1])],
                "exact_knot": exact,
                "propagated_standard_uncertainty": propagated,
                "pchip_minus_linear": pchip_value - linear_value,
                "independent_quantity": params["independent_quantity"].strip(),
                "independent_unit": params["independent_unit"].strip(),
                "dependent_unit": params["dependent_unit"].strip(),
                "source_id": params["source_id"].strip(),
                "source_version": params["source_version"].strip(),
                "algorithm_version": "linear-pchip-scipy-1.18.1-v1",
            },
            boundary_check=BoundaryCheck(not warnings_out, warnings_out),
        )


class B022_MultiphaseGibbsMinimization(W12PhaseTool):
    model_id, name, version = "B022", "多元多相Gibbs能最小化", "1.0.0"
    tool_name = "metallurgy_minimize_multiphase_gibbs_energy"
    description = "在显式物种计量和标准Gibbs能约束下，求纯相与理想混合相的非负多相平衡物种量。"
    model_type = "约束热力学优化"
    applicable_boundary = (
        "1至8种元素、2至40个物种、定温定压；支持单物种纯相和多物种理想混合相。"
        "调用方必须显式提供同一参考态下的标准Gibbs能；不替代CALPHAD数据库或非理想溶液模型。"
    )
    data_source = ["Gibbs energy minimization", "ideal-solution chemical potentials", "SciPy optimize 1.18.1"]
    source_version = "thermodynamic-constrained-minimization-v1; scipy-1.18.1"
    formula_reference = (
        "min G=sum(n_i*g_i^0)+RT*sum_ideal[n_i ln(n_i/N_phase)]，"
        "约束A n=b且n>=0；全纯相问题使用HiGHS线性规划，含理想相时使用SLSQP"
    )
    source_records = [
        {"source_id": "GIBBS-MINIMIZATION", "name": "Constrained total Gibbs-energy minimization", "version": "formula-v1"},
        {"source_id": "SCIPY-OPTIMIZE-1.18.1", "name": "SciPy linprog and SLSQP", "version": "1.18.1", "url": "https://docs.scipy.org/doc/scipy/reference/optimize.html"},
    ]
    failure_modes = [
        "元素总量、物种字段、计量系数或Gibbs能非有限",
        "元素守恒矩阵缺项或约束不可行",
        "同一相混用pure与ideal声明，或pure相含多个物种",
        "求解器未收敛、元素闭合残差超容差或结果非有限",
    ]
    independent_validation = [
        "全纯相问题由线性规划目标和元素守恒独立复算",
        "二元理想相固定总量时平衡量由解析Boltzmann比例复核",
        "任意可行结果的元素残差必须低于1e-8 mol",
        "给全部标准Gibbs能加同一元素线性组合只平移总G而不改变平衡组成",
    ]
    dependencies = []
    relations = [
        rel("generalizes", "B014", "B014直接给理想溶液活度；B022在元素守恒下以同一理想混合项求平衡物种量"),
        rel("overlaps_with", "B013", "二者都求化学平衡；B013以反应进度和气相平衡常数求解，B022以总G最小化求多相状态"),
        rel("reference_implementation_for", "B023", "B022是调用方显式Gibbs能的通用原子求解器；B023使用批准CALPHAD数据库"),
    ]
    _species_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "phase": {"type": "string"},
            "phase_model": {"type": "string", "enum": ["pure", "ideal"]},
            "standard_gibbs_j_mol": {"type": "number"},
            "stoichiometry": {"type": "object", "additionalProperties": {"type": "number", "minimum": 0}},
        },
        "required": ["name", "phase", "phase_model", "standard_gibbs_j_mol", "stoichiometry"],
        "additionalProperties": False,
    }
    input_fields = [
        InputField("temperature_k", "温度", "number", unit="K", min_value=1, max_value=10000),
        InputField("pressure_pa", "压力", "number", unit="Pa", min_value=1, max_value=1e9),
        InputField("element_totals_mol", "元素总量", "object", unit="mol", description="1至8个元素标签到非负摩尔量的映射，且至少一项大于0", json_schema={"type": "object", "minProperties": 1, "maxProperties": 8, "propertyNames": {"type": "string", "minLength": 1, "maxLength": 32}, "additionalProperties": {"type": "number", "minimum": 0}}),
        InputField("species", "候选物种", "array", items=_species_schema, min_items=2, max_items=40),
    ]
    output_fields = [
        OutputField("temperature_k", "温度", "number", "K"),
        OutputField("pressure_pa", "压力", "number", "Pa"),
        OutputField("solver_method", "求解方法", "string"),
        OutputField("converged", "是否收敛", "boolean"),
        OutputField("iterations", "迭代次数", "number", "1"),
        OutputField("species_amounts_mol", "平衡物种量", "object", "mol"),
        OutputField("phase_amounts_mol", "平衡相量", "object", "mol"),
        OutputField("phase_species_mole_fractions", "相内物种摩尔分数", "object", "1"),
        OutputField("active_species", "有效物种", "array"),
        OutputField("total_gibbs_energy_j", "总Gibbs能", "number", "J"),
        OutputField("element_residuals_mol", "元素守恒残差", "object", "mol"),
        OutputField("max_abs_element_residual_mol", "最大元素残差", "number", "mol"),
        OutputField("minimum_species_amount_mol", "最小物种量", "number", "mol"),
        OutputField("algorithm_version", "算法版本", "string"),
    ]
    validation_rules = [
        {"rule": "strict_species_contract_and_common_reference_state"},
        {"rule": "nonnegative_element_stoichiometry_and_amounts"},
        {"rule": "phase_model_consistent_within_phase"},
        {"rule": "element_balance_feasible_and_closed"},
    ]
    qualification_cases = [
        {"id": "B022-N1", "kind": "normal", "input": {"temperature_k": 1000, "pressure_pa": 101325, "element_totals_mol": {"A": 1}, "species": [{"name": "A_alpha", "phase": "ALPHA", "phase_model": "pure", "standard_gibbs_j_mol": 0, "stoichiometry": {"A": 1}}, {"name": "A_beta", "phase": "BETA", "phase_model": "pure", "standard_gibbs_j_mol": 1000, "stoichiometry": {"A": 1}}]}},
        {"id": "B022-N2", "kind": "normal", "input": {"temperature_k": 1200, "pressure_pa": 101325, "element_totals_mol": {"A": 1, "B": 1}, "species": [{"name": "A", "phase": "A_PURE", "phase_model": "pure", "standard_gibbs_j_mol": 0, "stoichiometry": {"A": 1}}, {"name": "B", "phase": "B_PURE", "phase_model": "pure", "standard_gibbs_j_mol": 0, "stoichiometry": {"B": 1}}, {"name": "AB", "phase": "AB_SOLID", "phase_model": "pure", "standard_gibbs_j_mol": -10000, "stoichiometry": {"A": 1, "B": 1}}]}},
        {"id": "B022-N3", "kind": "normal", "input": {"temperature_k": 1000, "pressure_pa": 101325, "element_totals_mol": {"A": 1}, "species": [{"name": "A1", "phase": "IDEAL", "phase_model": "ideal", "standard_gibbs_j_mol": 0, "stoichiometry": {"A": 1}}, {"name": "A2", "phase": "IDEAL", "phase_model": "ideal", "standard_gibbs_j_mol": 1000, "stoichiometry": {"A": 1}}]}},
        {"id": "B022-B1", "kind": "boundary", "input": {"temperature_k": 1, "pressure_pa": 1, "element_totals_mol": {"A": 1}, "species": [{"name": "A1", "phase": "P1", "phase_model": "pure", "standard_gibbs_j_mol": 0, "stoichiometry": {"A": 1}}, {"name": "A2", "phase": "P2", "phase_model": "pure", "standard_gibbs_j_mol": 1000, "stoichiometry": {"A": 1}}]}},
        {"id": "B022-F1", "kind": "failure", "input": {"temperature_k": 1000, "pressure_pa": 101325, "element_totals_mol": {"A": 1, "B": 1}, "species": [{"name": "A1", "phase": "P1", "phase_model": "pure", "standard_gibbs_j_mol": 0, "stoichiometry": {"A": 1}}, {"name": "A2", "phase": "P2", "phase_model": "pure", "standard_gibbs_j_mol": 0, "stoichiometry": {"A": 1}}]}},
        {"id": "B022-F2", "kind": "failure", "input": {"temperature_k": 1000, "pressure_pa": 101325, "element_totals_mol": {"A": 1}, "species": [{"name": "A1", "phase": "P", "phase_model": "pure", "standard_gibbs_j_mol": 0, "stoichiometry": {"A": 1}}, {"name": "A2", "phase": "P", "phase_model": "pure", "standard_gibbs_j_mol": 1, "stoichiometry": {"A": 1}}]}},
    ]

    @staticmethod
    def _parse(params: dict[str, Any]):
        totals_raw = params.get("element_totals_mol")
        if not isinstance(totals_raw, dict) or not 1 <= len(totals_raw) <= 8:
            return None, "element_totals_mol必须含1至8种元素"
        elements, totals = [], []
        for key, raw in totals_raw.items():
            if not isinstance(key, str) or not key.strip() or len(key) > 32:
                return None, "元素标签必须是1至32字符的非空字符串"
            amount, error = finite(raw, f"element_totals_mol.{key}")
            if error or amount < 0:
                return None, error or "元素总量不能为负"
            elements.append(key.strip())
            totals.append(amount)
        if len(set(elements)) != len(elements) or not any(value > 0 for value in totals):
            return None, "元素标签必须唯一且至少一个元素总量大于0"
        raw_species = params.get("species")
        if not isinstance(raw_species, list) or not 2 <= len(raw_species) <= 40:
            return None, "species必须含2至40项"
        species, names = [], set()
        required = {"name", "phase", "phase_model", "standard_gibbs_j_mol", "stoichiometry"}
        for index, raw in enumerate(raw_species):
            error = strict_object(raw, required, set(), f"species[{index}]")
            if error:
                return None, error
            name, phase, phase_model = raw["name"], raw["phase"], raw["phase_model"]
            if not isinstance(name, str) or not name.strip() or name in names:
                return None, f"species[{index}].name必须非空且唯一"
            if not isinstance(phase, str) or not phase.strip():
                return None, f"species[{index}].phase必须是非空字符串"
            if phase_model not in {"pure", "ideal"}:
                return None, f"species[{index}].phase_model不受支持"
            gibbs, error = finite(raw["standard_gibbs_j_mol"], f"species[{index}].standard_gibbs_j_mol")
            if error:
                return None, error
            stoich_raw = raw["stoichiometry"]
            if not isinstance(stoich_raw, dict) or not stoich_raw:
                return None, f"species[{index}].stoichiometry必须是非空对象"
            unknown = set(stoich_raw) - set(elements)
            if unknown:
                return None, f"species[{index}]含未声明元素: {sorted(unknown)}"
            stoich = {}
            for element, value in stoich_raw.items():
                coefficient, error = finite(value, f"species[{index}].stoichiometry.{element}")
                if error or coefficient < 0:
                    return None, error or "计量系数不能为负"
                if coefficient > 0:
                    stoich[element] = coefficient
            if not stoich:
                return None, f"species[{index}]必须至少含一个正计量系数"
            names.add(name)
            species.append({"name": name.strip(), "phase": phase.strip(), "model": phase_model, "g0": gibbs, "stoich": stoich})
        phase_groups: dict[str, list[dict[str, Any]]] = {}
        for item in species:
            phase_groups.setdefault(item["phase"], []).append(item)
        for phase, members in phase_groups.items():
            models = {item["model"] for item in members}
            if len(models) != 1:
                return None, f"相{phase}不能混用pure与ideal模型"
            if next(iter(models)) == "pure" and len(members) != 1:
                return None, f"pure相{phase}只能含一个物种；多物种相请声明ideal"
        matrix = np.asarray([[item["stoich"].get(element, 0.0) for item in species] for element in elements], dtype=float)
        missing = [elements[index] for index, row in enumerate(matrix) if not np.any(row > 0)]
        if missing:
            return None, f"没有候选物种承载元素: {missing}"
        return {"elements": elements, "totals": np.asarray(totals), "species": species, "groups": phase_groups, "matrix": matrix}, None

    @staticmethod
    def _objective(amounts: np.ndarray, parsed: dict[str, Any], temperature: float) -> float:
        gibbs = float(np.dot(amounts, np.asarray([item["g0"] for item in parsed["species"]])))
        for members in parsed["groups"].values():
            if members[0]["model"] != "ideal":
                continue
            indexes = [parsed["species"].index(item) for item in members]
            phase_amount = float(np.sum(amounts[indexes]))
            if phase_amount <= 0:
                continue
            for index in indexes:
                if amounts[index] > 0:
                    gibbs += R_GAS * temperature * amounts[index] * math.log(amounts[index] / phase_amount)
        return gibbs

    def invoke(self, params, context=None):
        errors = self.validate_input(params)
        if errors:
            return fail("; ".join(errors))
        temperature, error = finite(params.get("temperature_k"), "temperature_k")
        if error or not 1 <= temperature <= 10000:
            return fail(error or "temperature_k超出1至10000 K", "OUT_OF_DOMAIN")
        pressure, error = finite(params.get("pressure_pa"), "pressure_pa")
        if error or not 1 <= pressure <= 1e9:
            return fail(error or "pressure_pa超出1至1e9 Pa", "OUT_OF_DOMAIN")
        parsed, error = self._parse(params)
        if error:
            return fail(error, "MODEL_NOT_APPLICABLE" if "pure相" in error or "混用" in error else "INVALID_INPUT")
        matrix, totals = parsed["matrix"], parsed["totals"]
        g0 = np.asarray([item["g0"] for item in parsed["species"]], dtype=float)
        feasibility = linprog(np.zeros(len(g0)), A_eq=matrix, b_eq=totals, bounds=(0, None), method="highs")
        if not feasibility.success:
            return fail(f"元素守恒约束不可行: {feasibility.message}", "MODEL_NOT_APPLICABLE")
        has_ideal = any(item["model"] == "ideal" for item in parsed["species"])
        if not has_ideal:
            solved = linprog(g0, A_eq=matrix, b_eq=totals, bounds=(0, None), method="highs")
            if not solved.success:
                return fail(f"线性Gibbs最小化失败: {solved.message}", "NUMERICAL_ERROR")
            amounts, method, iterations = np.asarray(solved.x), "highs-linear-programming", int(solved.nit)
        else:
            scale = max(1.0, float(np.sum(totals)))
            lower = np.full(len(g0), 1e-14 * scale)
            positive_start = np.maximum(np.asarray(feasibility.x), lower)
            # Projection is handled by the equality constraints; a tiny positive start
            # keeps ideal logarithms differentiable without changing the reported zeros.
            solved = minimize(
                lambda values: self._objective(values, parsed, temperature),
                positive_start,
                method="SLSQP",
                bounds=[(0.0, None)] * len(g0),
                constraints=[{"type": "eq", "fun": lambda values: matrix @ values - totals}],
                options={"ftol": 1e-11, "maxiter": 1000, "disp": False},
            )
            if not solved.success:
                return fail(f"理想相Gibbs最小化未收敛: {solved.message}", "NUMERICAL_ERROR")
            amounts, method, iterations = np.asarray(solved.x), "slsqp-ideal-multiphase", int(solved.nit)
        amounts[np.abs(amounts) < 1e-12 * max(1.0, float(np.sum(amounts)))] = 0.0
        residuals = matrix @ amounts - totals
        max_residual = float(np.max(np.abs(residuals)))
        if not np.all(np.isfinite(amounts)) or np.any(amounts < -1e-10) or max_residual > 1e-8 * max(1.0, float(np.max(totals))):
            return fail("Gibbs最小化结果未通过非负性或元素闭合校验", "NUMERICAL_ERROR")
        species_amounts = {item["name"]: float(amount) for item, amount in zip(parsed["species"], amounts)}
        phase_amounts, phase_compositions = {}, {}
        for phase, members in parsed["groups"].items():
            indexes = [parsed["species"].index(item) for item in members]
            total = float(np.sum(amounts[indexes]))
            phase_amounts[phase] = total
            phase_compositions[phase] = {
                parsed["species"][index]["name"]: (float(amounts[index] / total) if total > 0 else 0.0)
                for index in indexes
            }
        warnings_out = []
        if temperature <= 1 or temperature >= 10000 or pressure <= 1 or pressure >= 1e9:
            warnings_out.append(BoundaryWarning("temperature_k/pressure_pa", "输入位于通用求解器数值适用域端点"))
        extinct = [item["name"] for item, amount in zip(parsed["species"], amounts) if amount == 0]
        if extinct:
            warnings_out.append(BoundaryWarning("species", f"平衡中有{len(extinct)}个候选物种量为零"))
        return ModelResult(
            True,
            result={
                "temperature_k": temperature,
                "pressure_pa": pressure,
                "solver_method": method,
                "converged": True,
                "iterations": iterations,
                "species_amounts_mol": species_amounts,
                "phase_amounts_mol": phase_amounts,
                "phase_species_mole_fractions": phase_compositions,
                "active_species": [name for name, amount in species_amounts.items() if amount > 0],
                "total_gibbs_energy_j": self._objective(amounts, parsed, temperature),
                "element_residuals_mol": {element: float(value) for element, value in zip(parsed["elements"], residuals)},
                "max_abs_element_residual_mol": max_residual,
                "minimum_species_amount_mol": float(np.min(amounts)),
                "algorithm_version": "gibbs-min-lp-slsqp-scipy-1.18.1-v1",
            },
            boundary_check=BoundaryCheck(not warnings_out, warnings_out),
        )


def _normalise_steel_composition(payload: Any) -> tuple[dict[str, float] | None, str | None]:
    if not isinstance(payload, dict) or not payload:
        return None, "composition_wt_percent必须是至少含一个正溶质量的对象"
    composition: dict[str, float] = {}
    for raw_symbol, raw_value in payload.items():
        if not isinstance(raw_symbol, str) or not raw_symbol.strip():
            return None, "成分键必须是非空元素符号"
        symbol = raw_symbol.strip().upper()
        if symbol == "FE":
            return None, "Fe必须作为余量，不能在composition_wt_percent中显式给出"
        if symbol in composition:
            return None, f"大小写归一化后元素重复: {symbol}"
        value, error = finite(raw_value, f"composition_wt_percent.{raw_symbol}")
        if error or value < 0:
            return None, error or f"{symbol}质量百分数不能为负"
        if value > 0:
            composition[symbol] = value
    if not composition:
        return None, "至少一个溶质质量百分数必须大于0"
    if sum(composition.values()) >= 50:
        return None, "当前批准资产仅适用于铁基钢，溶质总量必须小于50 wt%"
    return composition, None


def _calphad_domain_error(composition: dict[str, float], row: dict[str, Any]) -> str | None:
    supported = {str(item).upper() for item in row["supported_components"]}
    unknown = sorted(set(composition) - supported)
    if unknown:
        return f"当前批准模型不支持组元: {', '.join(unknown)}"
    maxima = row["domain_json"]["component_max_wt_percent"]
    exceeded = [
        f"{symbol}={value:g} wt%（必须小于{float(maxima[symbol]):g} wt%）"
        for symbol, value in composition.items()
        if value >= float(maxima[symbol])
    ]
    return "组分超出数据库已评估域: " + "; ".join(exceeded) if exceeded else None


def _selected_phases(payload: Any, row: dict[str, Any], database: Any) -> tuple[list[str] | None, str | None]:
    approved = [str(name) for name in row["phase_set"] if str(name) in database.phases]
    if payload is None:
        return approved, None
    if not isinstance(payload, list) or not payload:
        return None, "phases省略时使用批准相集；显式给出时必须是非空数组"
    if any(not isinstance(name, str) or not name.strip() for name in payload):
        return None, "phases只能包含非空相名字符串"
    phases = [name.strip().upper() for name in payload]
    if len(phases) != len(set(phases)):
        return None, "phases不能含重复相名"
    invalid = sorted(set(phases) - set(approved))
    if invalid:
        return None, f"相不在数据库批准相集中: {', '.join(invalid)}"
    return phases, None


def _equilibrium_state(database: Any, composition: dict[str, float], phases: list[str], temperature: float, pressure: float):
    components = ["FE", *sorted(composition), "VA"]
    conditions = {v.P: pressure, v.N: 1, v.T: temperature}
    conditions.update({v.W(symbol): amount / 100.0 for symbol, amount in composition.items()})
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="The type definition character.*", category=UserWarning)
        return equilibrium(database, components, phases, conditions)


def _extract_equilibrium_state(calculated: Any) -> dict[str, Any]:
    phase_names = np.asarray(calculated.Phase.values).reshape(-1)
    phase_amounts = np.asarray(calculated.NP.values, dtype=float).reshape(-1)
    components = [str(item) for item in calculated.X.coords["component"].values]
    phase_compositions = np.asarray(calculated.X.values, dtype=float).reshape(-1, len(components))
    stable = []
    seen: set[str] = set()
    for index, (raw_name, raw_amount) in enumerate(zip(phase_names, phase_amounts)):
        name = str(raw_name)
        if not name or not math.isfinite(float(raw_amount)) or float(raw_amount) <= 1e-12:
            continue
        if name in seen:
            raise ValueError(f"当前版本不接受同名相多顶点/互溶间隙结果: {name}")
        values = phase_compositions[index]
        if not np.all(np.isfinite(values)):
            raise ValueError(f"相{name}组成含非有限值")
        composition_sum = float(np.sum(values))
        if abs(composition_sum - 1.0) > 1e-8:
            raise ValueError(f"相{name}摩尔分数组成未闭合")
        stable.append(
            {
                "phase": name,
                "phase_amount_fraction": float(raw_amount),
                "component_mole_fractions": {component: float(value) for component, value in zip(components, values)},
                "composition_sum_residual": composition_sum - 1.0,
            }
        )
        seen.add(name)
    if not stable:
        raise ValueError("CALPHAD平衡没有返回有效稳定相")
    total = sum(item["phase_amount_fraction"] for item in stable)
    if abs(total - 1.0) > 1e-7:
        raise ValueError(f"稳定相分数未闭合，残差={total - 1.0:g}")
    chemical = np.asarray(calculated.MU.values, dtype=float).reshape(-1, len(components))[0]
    gibbs = float(np.asarray(calculated.GM.values, dtype=float).reshape(-1)[0])
    if not np.all(np.isfinite(chemical)) or not math.isfinite(gibbs):
        raise ValueError("CALPHAD化学势或Gibbs能含非有限值")
    return {
        "stable_phases": stable,
        "phase_fraction_closure_residual": total - 1.0,
        "chemical_potentials_j_mol": {component: float(value) for component, value in zip(components, chemical)},
        "molar_gibbs_energy_j_mol": gibbs,
    }


class _ApprovedSteelCalphadTool(W12PhaseTool):
    model_type = "数据库驱动CALPHAD/Scheil计算"
    data_requirement = "VERSIONED_DATABASE_AND_MODEL_ASSET"
    data_access_mode = "database_repository"
    required_dataset_ids = ["DS_MATCALC_MC_FE_2059"]
    database_tables = ["metallurgy_v2.solidification_model_definition"]
    dependencies = []
    temperature_range = [673.0, 2000.0]
    pressure_range = [1.0, 1e7]
    data_source = ["MatCalc mc_fe v2.059 TDB", "pycalphad 0.11.2", "database-approved SHA-256 verified asset"]
    source_version = "mc_fe_v2.059@0a8dd091; pycalphad-0.11.2; asset-a8628b6e"
    source_records = [
        {
            "source_id": "DS_MATCALC_MC_FE_2059",
            "name": "MatCalc mc_fe steel thermodynamic database",
            "version": "2.059",
            "url": "https://github.com/pyroll-project/pyroll-examples/blob/0a8dd09136e3c9c1e73afee054bb55a8f6cd84b0/mc_fe_v2.059.pycalphad.tdb",
        }
    ]
    _composition_field = InputField(
        "composition_wt_percent",
        "钢中溶质质量百分数",
        "object",
        unit="wt%",
        description="Fe为余量；批准键限C/Si/Mn/Cr/Ni/Mo/Cu/Al，实际上限由数据库记录读取",
        json_schema={
            "type": "object",
            "properties": {
                component: {"type": "number", "minimum": 0}
                for component in ("C", "Si", "Mn", "Cr", "Ni", "Mo", "Cu", "Al")
            },
            "minProperties": 1,
            "additionalProperties": False,
        },
    )
    _asset_field = InputField(
        "model_asset_id",
        "批准模型资产编号",
        "select",
        required=False,
        default=MODEL_ASSET_ID,
        enum=[MODEL_ASSET_ID],
    )

    @staticmethod
    def _load_and_validate(composition_payload: Any, model_asset_id: str):
        composition, error = _normalise_steel_composition(composition_payload)
        if error:
            return None, None, None, None, fail(error)
        if model_asset_id != MODEL_ASSET_ID:
            return None, None, None, None, fail("model_asset_id不是当前批准资产", "MODEL_NOT_APPLICABLE")
        try:
            database, row, provenance = load_database(model_asset_id)
        except RepositoryError as exc:
            return None, None, None, None, fail(str(exc), exc.error_code)
        error = _calphad_domain_error(composition, row)
        if error:
            return None, None, None, None, fail(error, "OUT_OF_DOMAIN")
        return composition, database, row, provenance, None

    @staticmethod
    def _domain_warnings(composition: dict[str, float], row: dict[str, Any], temperature: float) -> list[BoundaryWarning]:
        maxima = row["domain_json"]["component_max_wt_percent"]
        warnings_out = []
        if any(value >= 0.9 * float(maxima[symbol]) for symbol, value in composition.items()):
            warnings_out.append(BoundaryWarning("composition_wt_percent", "至少一个组分达到批准数据库评估上限的90%"))
        if temperature <= float(row["temperature_min_k"]) or temperature >= float(row["temperature_max_k"]):
            warnings_out.append(BoundaryWarning("temperature_k", "温度位于批准数据库温区端点"))
        return warnings_out


class B023_CalphadEquilibrium(_ApprovedSteelCalphadTool):
    model_id, name, version = "B023", "钢系CALPHAD单状态平衡", "1.0.0"
    tool_name = "metallurgy_calculate_calphad_equilibrium_state"
    description = "用数据库批准且哈希校验的钢系TDB计算单一温压成分状态的稳定相、相量、相组成、化学势与Gibbs能。"
    applicable_boundary = (
        "铁基钢；Fe为余量；C/Si/Mn/Cr/Ni/Mo/Cu/Al且低于数据库逐元素上限；673至2000 K、1至1e7 Pa。"
        "只允许数据库批准相集；不计算温度曲线、相变端点或亚稳相图。"
    )
    formula_reference = "pycalphad在批准TDB与相集上求定T、P、N和质量分数组成约束下的全局Gibbs能最小状态"
    failure_modes = [
        "批准数据库记录缺失、资产缺失或SHA-256不一致",
        "组元/温压/相集超出数据库批准域",
        "平衡无稳定相、同名相发生多顶点分裂或求解结果非有限",
        "相分数或相内摩尔分数组成闭合残差超容差",
    ]
    independent_validation = [
        "稳定相分数和每个相的摩尔分数组成分别闭合到1",
        "化学势与摩尔Gibbs能必须有限",
        "B023在同成分温度点的液相分数与F004平衡曲线直接点一致",
        "不同输入键顺序给出相同稳定状态",
    ]
    relations = [
        rel("specializes", "B022", "B023从批准CALPHAD数据库构建非理想多相Gibbs模型；B022要求调用方显式给物种Gibbs能"),
        rel("overlaps_with", "F001", "F001搜索液相线端点；B023只返回一个给定温度的完整平衡状态"),
        rel("overlaps_with", "F002", "F002搜索固相线端点；B023只返回一个给定温度的完整平衡状态"),
        rel("overlaps_with", "F004", "F004返回平衡/Scheil凝固曲线；B023返回单状态相组成、化学势和Gibbs能"),
        rel("feeds", "B025", "B023稳定相和Gibbs能结果可作为B025相图一致性检查输入"),
    ]
    input_fields = [
        _ApprovedSteelCalphadTool._composition_field,
        InputField("temperature_k", "温度", "number", unit="K", min_value=673, max_value=2000),
        InputField("pressure_pa", "压力", "number", required=False, default=101325.0, unit="Pa", min_value=1, max_value=1e7),
        InputField("phases", "候选相集", "array", required=False, items={"type": "string"}, min_items=1, max_items=6),
        _ApprovedSteelCalphadTool._asset_field,
    ]
    output_fields = [
        OutputField("temperature_k", "温度", "number", "K"),
        OutputField("pressure_pa", "压力", "number", "Pa"),
        OutputField("composition_wt_percent", "输入溶质成分", "object", "wt%"),
        OutputField("stable_phases", "稳定相及相组成", "array"),
        OutputField("phase_fraction_closure_residual", "相分数闭合残差", "number", "1"),
        OutputField("chemical_potentials_j_mol", "组元化学势", "object", "J/mol"),
        OutputField("molar_gibbs_energy_j_mol", "体系摩尔Gibbs能", "number", "J/mol"),
        OutputField("model_asset_id", "模型资产编号", "string"),
        OutputField("dataset_id", "数据集编号", "string"),
        OutputField("database_version", "热力学数据库版本", "string"),
        OutputField("solver_version", "求解器版本", "string"),
        OutputField("phase_set_used", "实际候选相集", "array"),
    ]
    validation_rules = [
        {"rule": "database_approved_asset_and_sha256_required"},
        {"rule": "composition_temperature_pressure_and_phase_domain"},
        {"rule": "phase_and_composition_fraction_closure"},
    ]
    qualification_cases = [
        {"id": "B023-N1", "kind": "normal", "input": {"composition_wt_percent": {"C": 0.1}, "temperature_k": 1700}},
        {"id": "B023-N2", "kind": "normal", "input": {"composition_wt_percent": {"C": 0.2, "Mn": 1.0, "Si": 0.2}, "temperature_k": 1800}},
        {"id": "B023-N3", "kind": "normal", "input": {"composition_wt_percent": {"C": 0.05, "Cr": 1.0, "Ni": 1.0}, "temperature_k": 1600, "pressure_pa": 101325}},
        {"id": "B023-B1", "kind": "boundary", "input": {"composition_wt_percent": {"Cr": 23.0}, "temperature_k": 1700}},
        {"id": "B023-F1", "kind": "failure", "input": {"composition_wt_percent": {"P": 0.01}, "temperature_k": 1700}},
        {"id": "B023-F2", "kind": "failure", "input": {"composition_wt_percent": {"C": 0.1}, "temperature_k": 1700, "phases": ["SIGMA"]}},
    ]
    data_qualification_cases = [{"id": "B023-D1", "input": qualification_cases[0]["input"]}]

    def invoke(self, params, context=None):
        errors = self.validate_input(params)
        if errors:
            return fail("; ".join(errors))
        temperature, error = finite(params.get("temperature_k"), "temperature_k")
        if error or not 673 <= temperature <= 2000:
            return fail(error or "temperature_k超出673至2000 K", "OUT_OF_DOMAIN")
        pressure, error = finite(params.get("pressure_pa", 101325.0), "pressure_pa")
        if error or not 1 <= pressure <= 1e7:
            return fail(error or "pressure_pa超出1至1e7 Pa", "OUT_OF_DOMAIN")
        asset_id = params.get("model_asset_id", MODEL_ASSET_ID)
        composition, database, row, provenance, failure = self._load_and_validate(params.get("composition_wt_percent"), asset_id)
        if failure:
            return failure
        phases, error = _selected_phases(params.get("phases"), row, database)
        if error:
            return fail(error, "OUT_OF_DOMAIN")
        try:
            state = _extract_equilibrium_state(_equilibrium_state(database, composition, phases, temperature, pressure))
        except Exception as exc:
            return fail(f"CALPHAD单状态平衡失败: {exc}", "NUMERICAL_ERROR")
        warnings_out = self._domain_warnings(composition, row, temperature)
        return ModelResult(
            True,
            result={
                "temperature_k": temperature,
                "pressure_pa": pressure,
                "composition_wt_percent": composition,
                **state,
                "model_asset_id": asset_id,
                "dataset_id": str(row["dataset_id"]),
                "database_version": str(row["model_version"]),
                "solver_version": str(row["solver_version"]),
                "phase_set_used": phases,
            },
            boundary_check=BoundaryCheck(not warnings_out, warnings_out),
            provenance=provenance,
        )


class B024_ScheilMicrosegregation(_ApprovedSteelCalphadTool):
    model_id, name, version = "B024", "Scheil–Gulliver微偏析路径", "1.0.0"
    tool_name = "metallurgy_calculate_scheil_microsegregation"
    description = "用批准钢系TDB和Scheil求解器返回液相富集、瞬时固相组成、累计相量与逐组元守恒残差。"
    applicable_boundary = (
        "铁基钢、批准组元/相集与673至2000 K数据库温区；起始点必须为全液相；温降步长1至50 K。"
        "假设液相完全混合、固相无回扩散、界面局部平衡；不适用于有限扩散、流动偏析或现场预测。"
    )
    formula_reference = (
        "scheil 0.3.0逐步局部平衡；f_L+sum(delta f_s)=1；"
        "x_i^0=f_L*x_i^L+sum(delta f_phase*x_i^phase)逐步复算组元守恒"
    )
    source_version = "mc_fe_v2.059@0a8dd091; pycalphad-0.11.2; scheil-0.3.0; asset-a8628b6e"
    data_source = ["MatCalc mc_fe v2.059 TDB", "pycalphad 0.11.2", "scheil 0.3.0", "database-approved SHA-256 verified asset"]
    dependencies = ["B023"]
    failure_modes = [
        "批准数据库记录缺失、资产缺失或SHA-256不一致",
        "组元、温度、相集、步长或停止阈值超批准域",
        "起始温度不是近似全液相",
        "Scheil求解未收敛或未达到残余液相停止条件",
        "相分数闭合或逐组元物料守恒残差超数值容差",
    ]
    independent_validation = [
        "每个路径点液相量加累计固相增量闭合到1",
        "用每步新生固相组成独立重构各组元初始摩尔分数",
        "温度路径非增、液相分数非增、累计相量非减",
        "起始温点的全液相组成与输入约束一致并作为守恒基准",
    ]
    relations = [
        rel("depends_on", "B023", "B024每步使用与B023相同的批准CALPHAD局部平衡模型"),
        rel("overlaps_with", "F004", "F004面向凝固曲线与端点；B024面向液相/新生固相组成和逐元素微偏析闭合"),
        rel("feeds", "B025", "B024的相量与相组成路径可由B025执行杠杆/相区一致性检查"),
    ]
    input_fields = [
        _ApprovedSteelCalphadTool._composition_field,
        InputField("start_temperature_k", "起始全液相温度", "number", unit="K", min_value=673, max_value=2000),
        InputField("step_temperature_k", "降温步长", "number", required=False, default=10.0, unit="K", min_value=1, max_value=50),
        InputField("residual_liquid_stop_fraction", "残余液相停止阈值", "number", required=False, default=0.01, unit="1", min_value=0.001, max_value=0.05),
        InputField("phases", "候选相集", "array", required=False, items={"type": "string"}, min_items=2, max_items=6),
        _ApprovedSteelCalphadTool._asset_field,
    ]
    output_fields = [
        OutputField("composition_wt_percent", "输入溶质成分", "object", "wt%"),
        OutputField("initial_liquid_mole_fractions", "起始液相摩尔分数", "object", "1"),
        OutputField("path", "微偏析路径", "array"),
        OutputField("final_cumulative_phase_amounts", "最终累计相量", "object", "1"),
        OutputField("component_balance_residuals", "逐组元守恒残差", "object", "mole_fraction"),
        OutputField("max_abs_component_balance_residual", "最大组元守恒残差", "number", "mole_fraction"),
        OutputField("maximum_liquid_enrichment_factors", "液相最大富集倍数", "object", "1"),
        OutputField("max_abs_phase_fraction_closure_residual", "最大相分数闭合残差", "number", "1"),
        OutputField("converged", "求解是否收敛", "boolean"),
        OutputField("start_temperature_k", "起始温度", "number", "K"),
        OutputField("step_temperature_k", "降温步长", "number", "K"),
        OutputField("residual_liquid_stop_fraction", "残余液相停止阈值", "number", "1"),
        OutputField("model_asset_id", "模型资产编号", "string"),
        OutputField("dataset_id", "数据集编号", "string"),
        OutputField("database_version", "热力学数据库版本", "string"),
        OutputField("solver_version", "Scheil求解器版本", "string"),
        OutputField("phase_set_used", "实际候选相集", "array"),
    ]
    validation_rules = [
        {"rule": "database_approved_asset_and_sha256_required"},
        {"rule": "initial_state_is_all_liquid"},
        {"rule": "temperature_and_liquid_fraction_nonincreasing"},
        {"rule": "phase_fraction_and_component_material_balance_closure"},
    ]
    qualification_cases = [
        {"id": "B024-N1", "kind": "normal", "input": {"composition_wt_percent": {"C": 0.1}, "start_temperature_k": 1900, "step_temperature_k": 20, "residual_liquid_stop_fraction": 0.01}},
        {"id": "B024-N2", "kind": "normal", "input": {"composition_wt_percent": {"C": 0.15, "Mn": 1.0}, "start_temperature_k": 1900, "step_temperature_k": 25, "residual_liquid_stop_fraction": 0.02}},
        {"id": "B024-N3", "kind": "normal", "input": {"composition_wt_percent": {"C": 0.05, "Cr": 1.0, "Ni": 1.0}, "start_temperature_k": 1950, "step_temperature_k": 25, "residual_liquid_stop_fraction": 0.02}},
        {"id": "B024-B1", "kind": "boundary", "input": {"composition_wt_percent": {"C": 0.1}, "start_temperature_k": 2000, "step_temperature_k": 50, "residual_liquid_stop_fraction": 0.05}},
        {"id": "B024-F1", "kind": "failure", "input": {"composition_wt_percent": {"P": 0.01}, "start_temperature_k": 1900}},
        {"id": "B024-F2", "kind": "failure", "input": {"composition_wt_percent": {"C": 0.1}, "start_temperature_k": 1400, "step_temperature_k": 20}},
    ]
    data_qualification_cases = [{"id": "B024-D1", "input": qualification_cases[0]["input"]}]

    def invoke(self, params, context=None):
        errors = self.validate_input(params)
        if errors:
            return fail("; ".join(errors))
        start, error = finite(params.get("start_temperature_k"), "start_temperature_k")
        if error or not 673 <= start <= 2000:
            return fail(error or "start_temperature_k超出673至2000 K", "OUT_OF_DOMAIN")
        step, error = finite(params.get("step_temperature_k", 10.0), "step_temperature_k")
        if error or not 1 <= step <= 50:
            return fail(error or "step_temperature_k超出1至50 K", "OUT_OF_DOMAIN")
        stop, error = finite(params.get("residual_liquid_stop_fraction", 0.01), "residual_liquid_stop_fraction")
        if error or not 0.001 <= stop <= 0.05:
            return fail(error or "residual_liquid_stop_fraction超出0.001至0.05", "OUT_OF_DOMAIN")
        asset_id = params.get("model_asset_id", MODEL_ASSET_ID)
        composition, database, row, provenance, failure = self._load_and_validate(params.get("composition_wt_percent"), asset_id)
        if failure:
            return failure
        phases, error = _selected_phases(params.get("phases"), row, database)
        if error:
            return fail(error, "OUT_OF_DOMAIN")
        if "LIQUID" not in phases or len(phases) < 2:
            return fail("Scheil候选相集必须包含LIQUID和至少一个固相", "MODEL_NOT_APPLICABLE")
        try:
            initial_state = _extract_equilibrium_state(_equilibrium_state(database, composition, phases, start, 101325.0))
            liquid_amount = next((item["phase_amount_fraction"] for item in initial_state["stable_phases"] if item["phase"] == "LIQUID"), 0.0)
            if liquid_amount < 1 - 1e-8:
                return fail(f"起始温度不是全液相，CALPHAD液相分数={liquid_amount:g}", "MODEL_NOT_APPLICABLE")
            components = ["FE", *sorted(composition), "VA"]
            conditions = {v.W(symbol): amount / 100.0 for symbol, amount in composition.items()}
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", message="The type definition character.*", category=UserWarning)
                simulation = simulate_scheil_solidification(
                    database,
                    components,
                    phases,
                    conditions,
                    start,
                    step,
                    stop=stop,
                )
        except Exception as exc:
            return fail(f"Scheil微偏析求解失败: {exc}", "NUMERICAL_ERROR")
        if not simulation.converged:
            return fail("Scheil求解未达到声明的残余液相停止条件", "NUMERICAL_ERROR")
        temperatures = np.asarray(simulation.temperatures, dtype=float)
        liquid_fractions = np.asarray(simulation.fraction_liquid, dtype=float)
        if not np.all(np.isfinite(temperatures)) or not np.all(np.isfinite(liquid_fractions)):
            return fail("Scheil温度或液相分数路径含非有限值", "NUMERICAL_ERROR")
        if np.any(np.diff(temperatures) > 1e-9) or np.any(np.diff(liquid_fractions) > 1e-8):
            return fail("Scheil路径不满足温度和液相分数非增性质", "NUMERICAL_ERROR")
        # The library appends a zero-liquid terminal sentinel after reaching
        # ``stop``. Its cumulative phase arrays intentionally retain the
        # stopped state rather than assigning the residual liquid to a solid.
        # Report and validate the last positive-liquid physical state.
        positive_indexes = np.flatnonzero(liquid_fractions > 0)
        if len(positive_indexes) == 0:
            return fail("Scheil结果没有正液相路径点", "NUMERICAL_ERROR")
        physical_count = int(positive_indexes[-1]) + 1
        temperatures = temperatures[:physical_count]
        liquid_fractions = liquid_fractions[:physical_count]
        if liquid_fractions[-1] > stop + 1e-10:
            return fail("Scheil最后物理路径点没有达到声明停止阈值", "NUMERICAL_ERROR")
        liquid_compositions = simulation.phase_compositions.get("LIQUID", {})
        component_names = sorted(liquid_compositions)
        if not component_names:
            return fail("Scheil结果缺少液相组成", "NUMERICAL_ERROR")
        # scheil 0.3.0 reserves index zero as an all-liquid path sentinel and
        # stores NaN compositions there.  Use the first index where every
        # liquid component is finite; the preceding sentinel has zero solid
        # increment and therefore does not change the material balance.
        initial_index = next(
            (
                index
                for index in range(len(temperatures))
                if all(math.isfinite(float(liquid_compositions[component][index])) for component in component_names)
            ),
            None,
        )
        if initial_index is None or liquid_fractions[initial_index] < 1 - 1e-8:
            return fail("Scheil结果缺少可验证的全液相初始组成", "NUMERICAL_ERROR")
        initial_liquid = {component: float(liquid_compositions[component][initial_index]) for component in component_names}
        solid_phases = [phase for phase in simulation.phase_amounts if phase != "LIQUID"]
        path = []
        maximum_enrichment = {component: 1.0 for component in component_names if component != "FE" and initial_liquid[component] > 0}
        max_closure = 0.0
        for index, (temperature, liquid_fraction) in enumerate(zip(temperatures, liquid_fractions)):
            incremental = {phase: float(simulation.phase_amounts[phase][index]) for phase in solid_phases if float(simulation.phase_amounts[phase][index]) > 1e-14}
            cumulative = {phase: float(simulation.cum_phase_amounts[phase][index]) for phase in solid_phases if float(simulation.cum_phase_amounts[phase][index]) > 1e-14}
            liquid_x = {}
            for component in component_names:
                raw = float(liquid_compositions[component][index])
                if math.isfinite(raw):
                    liquid_x[component] = raw
                    if component in maximum_enrichment and liquid_fraction > 0:
                        maximum_enrichment[component] = max(maximum_enrichment[component], raw / initial_liquid[component])
            new_solid_compositions = {}
            for phase in incremental:
                phase_values = simulation.phase_compositions.get(phase, {})
                composition_row = {
                    component: float(phase_values[component][index])
                    for component in component_names
                    if component in phase_values and math.isfinite(float(phase_values[component][index]))
                }
                if composition_row:
                    new_solid_compositions[phase] = composition_row
            closure = float(liquid_fraction + sum(cumulative.values()) - 1.0)
            max_closure = float(max(max_closure, abs(closure)))
            path.append(
                {
                    "temperature_k": float(temperature),
                    "fraction_liquid": float(liquid_fraction),
                    "fraction_solid": float(1.0 - liquid_fraction),
                    "incremental_solid_phase_amounts": incremental,
                    "cumulative_solid_phase_amounts": cumulative,
                    "liquid_mole_fractions": liquid_x,
                    "new_solid_phase_mole_fractions": new_solid_compositions,
                    "phase_fraction_closure_residual": closure,
                }
            )
        last_physical_index = len(path) - 1
        reconstructed = {
            component: liquid_fractions[-1] * float(liquid_compositions[component][last_physical_index])
            if math.isfinite(float(liquid_compositions[component][last_physical_index]))
            else 0.0
            for component in component_names
        }
        for index in range(len(path)):
            for phase, amount in path[index]["incremental_solid_phase_amounts"].items():
                for component, value in path[index]["new_solid_phase_mole_fractions"].get(phase, {}).items():
                    reconstructed[component] += amount * value
        residuals = {component: float(reconstructed[component] - initial_liquid[component]) for component in component_names}
        max_component_residual = float(max(abs(value) for value in residuals.values()))
        if max_closure > 2e-8 or max_component_residual > 2e-5:
            return fail(
                f"Scheil独立守恒复算未闭合: phase={max_closure:g}, component={max_component_residual:g}",
                "NUMERICAL_ERROR",
            )
        warnings_out = self._domain_warnings(composition, row, start)
        if step >= 50 or stop >= 0.05:
            warnings_out.append(BoundaryWarning("step_temperature_k/residual_liquid_stop_fraction", "离散步长或停止阈值位于允许上限，路径分辨率较低"))
        final_index = len(path) - 1
        final_cumulative = {phase: float(values[final_index]) for phase, values in simulation.cum_phase_amounts.items() if float(values[final_index]) > 1e-14}
        return ModelResult(
            True,
            result={
                "composition_wt_percent": composition,
                "initial_liquid_mole_fractions": initial_liquid,
                "path": path,
                "final_cumulative_phase_amounts": final_cumulative,
                "component_balance_residuals": residuals,
                "max_abs_component_balance_residual": max_component_residual,
                "maximum_liquid_enrichment_factors": maximum_enrichment,
                "max_abs_phase_fraction_closure_residual": max_closure,
                "converged": True,
                "start_temperature_k": start,
                "step_temperature_k": step,
                "residual_liquid_stop_fraction": stop,
                "model_asset_id": asset_id,
                "dataset_id": str(row["dataset_id"]),
                "database_version": str(row["model_version"]),
                "solver_version": str(row["solidification_solver_version"]),
                "phase_set_used": phases,
            },
            boundary_check=BoundaryCheck(not warnings_out, warnings_out),
            provenance=provenance,
        )


class B025_PhaseDiagramConsistencyValidation(W12PhaseTool):
    model_id, name, version = "B025", "相图热力学一致性校验", "1.0.0"
    tool_name = "metallurgy_validate_phase_diagram_consistency"
    description = "对显式相区执行Gibbs相律、邻接相集、杠杆重构和最低Gibbs能四类一致性校验并逐项报告违规。"
    model_type = "热力学规则/数值校验"
    applicable_boundary = (
        "1至10个独立组元；相区、邻接、杠杆测试和候选Gibbs能由调用方显式提供。"
        "校验不生成相图、不推断缺失相区、不访问CALPHAD数据库；物理违规作为成功执行的检查结果返回。"
    )
    data_source = ["Gibbs phase rule", "lever rule", "minimum Gibbs-energy stability criterion"]
    source_version = "phase-diagram-consistency-rules-v1"
    formula_reference = (
        "F=C-P+2-R-X；邻接相区相集对称差应为1；"
        "z=f_alpha*x_alpha+f_beta*x_beta且sum(f)=1；声明稳定候选的G应在容差内为最小"
    )
    source_records = [
        {"source_id": "GIBBS-PHASE-RULE", "name": "Gibbs phase rule", "version": "formula-v1"},
        {"source_id": "LEVER-RULE", "name": "Multicomponent lever material-balance rule", "version": "formula-v1"},
        {"source_id": "MINIMUM-GIBBS-STABILITY", "name": "Minimum Gibbs-energy stability criterion", "version": "formula-v1"},
    ]
    failure_modes = [
        "相区ID/相名为空或重复",
        "邻接检查引用未知相区或重复无向边",
        "杠杆测试向量维数与组元数不一致、含非有限值或候选相重名",
        "Gibbs测试为空、含非有限值或声明稳定候选不存在",
        "没有任何可执行检查项",
    ]
    independent_validation = [
        "每个相区自由度由F=C-P+2-R-X独立整数复算",
        "邻接相集由集合对称差独立复算",
        "杠杆测试逐组元重构并报告最大绝对残差",
        "Gibbs稳定性由候选最小值和声明值差独立复算",
    ]
    dependencies = []
    relations = [
        rel("uses_convention_of", "B018", "B025对多个相区批量应用与B018相同的Gibbs相律并联合其他一致性检查"),
        rel("validates_output_of", "B019", "B025的杠杆测试可独立复核B019或其他两相分数结果"),
        rel("validates_output_of", "B022", "B025最低Gibbs检查可复核显式多候选求解结果"),
        rel("validates_output_of", "B023", "B025可校验B023导出的稳定相、相区和候选能量记录"),
    ]
    _region_schema = {
        "type": "object",
        "properties": {"region_id": {"type": "string"}, "phases": {"type": "array", "items": {"type": "string"}, "minItems": 1}},
        "required": ["region_id", "phases"],
        "additionalProperties": False,
    }
    _adjacency_schema = {
        "type": "object",
        "properties": {"region_a": {"type": "string"}, "region_b": {"type": "string"}},
        "required": ["region_a", "region_b"],
        "additionalProperties": False,
    }
    _lever_schema = {
        "type": "object",
        "properties": {
            "test_id": {"type": "string"},
            "phase_a_composition": {"type": "array", "items": {"type": "number"}},
            "phase_b_composition": {"type": "array", "items": {"type": "number"}},
            "bulk_composition": {"type": "array", "items": {"type": "number"}},
            "phase_a_fraction": {"type": "number"},
            "phase_b_fraction": {"type": "number"},
        },
        "required": ["test_id", "phase_a_composition", "phase_b_composition", "bulk_composition", "phase_a_fraction", "phase_b_fraction"],
        "additionalProperties": False,
    }
    _gibbs_schema = {
        "type": "object",
        "properties": {
            "test_id": {"type": "string"},
            "declared_stable": {"type": "string"},
            "candidate_gibbs_j_mol": {"type": "object", "additionalProperties": {"type": "number"}},
        },
        "required": ["test_id", "declared_stable", "candidate_gibbs_j_mol"],
        "additionalProperties": False,
    }
    input_fields = [
        InputField("components_count", "独立组元数", "integer", unit="1", min_value=1, max_value=10),
        InputField("independent_reactions", "独立反应数", "integer", required=False, default=0, unit="1", min_value=0, max_value=10),
        InputField("fixed_external_constraints", "固定外加约束数", "integer", required=False, default=2, unit="1", min_value=0, max_value=10),
        InputField("phase_regions", "相区", "array", items=_region_schema, min_items=1, max_items=100),
        InputField("adjacency_checks", "相区邻接检查", "array", required=False, items=_adjacency_schema, max_items=200),
        InputField("lever_tests", "杠杆规则测试", "array", required=False, items=_lever_schema, max_items=100),
        InputField("gibbs_tests", "最低Gibbs能测试", "array", required=False, items=_gibbs_schema, max_items=100),
        InputField("fraction_tolerance", "分数/组成容差", "number", required=False, default=1e-8, unit="1", min_value=1e-12, max_value=0.01),
        InputField("gibbs_tolerance_j_mol", "Gibbs能容差", "number", required=False, default=1e-6, unit="J/mol", min_value=0, max_value=1000),
    ]
    output_fields = [
        OutputField("passed", "是否全部通过", "boolean"),
        OutputField("check_count", "检查总数", "number", "1"),
        OutputField("violation_count", "违规总数", "number", "1"),
        OutputField("phase_rule_results", "相律检查结果", "array"),
        OutputField("adjacency_results", "邻接检查结果", "array"),
        OutputField("lever_rule_results", "杠杆检查结果", "array"),
        OutputField("gibbs_stability_results", "Gibbs稳定性结果", "array"),
        OutputField("violations", "全部违规", "array"),
        OutputField("max_abs_lever_residual", "最大杠杆重构残差", "number", "1"),
        OutputField("max_gibbs_penalty_j_mol", "最大声明稳定能量罚值", "number", "J/mol"),
        OutputField("components_count", "独立组元数", "number", "1"),
        OutputField("independent_reactions", "独立反应数", "number", "1"),
        OutputField("fixed_external_constraints", "固定外加约束数", "number", "1"),
        OutputField("algorithm_version", "算法版本", "string"),
    ]
    validation_rules = [
        {"rule": "phase_region_identifiers_and_phase_names_unique"},
        {"rule": "adjacency_references_known_regions"},
        {"rule": "lever_vectors_match_component_dimension"},
        {"rule": "declared_stable_gibbs_candidate_exists"},
    ]
    qualification_cases = [
        {"id": "B025-N1", "kind": "normal", "input": {"components_count": 2, "independent_reactions": 0, "fixed_external_constraints": 2, "phase_regions": [{"region_id": "L", "phases": ["LIQUID"]}]}},
        {"id": "B025-N2", "kind": "normal", "input": {"components_count": 2, "fixed_external_constraints": 2, "phase_regions": [{"region_id": "A", "phases": ["ALPHA"]}, {"region_id": "AB", "phases": ["ALPHA", "BETA"]}], "adjacency_checks": [{"region_a": "A", "region_b": "AB"}]}},
        {"id": "B025-N3", "kind": "normal", "input": {"components_count": 2, "fixed_external_constraints": 2, "phase_regions": [{"region_id": "AB", "phases": ["ALPHA", "BETA"]}], "lever_tests": [{"test_id": "L1", "phase_a_composition": [0.2, 0.8], "phase_b_composition": [0.8, 0.2], "bulk_composition": [0.5, 0.5], "phase_a_fraction": 0.5, "phase_b_fraction": 0.5}], "gibbs_tests": [{"test_id": "G1", "declared_stable": "ALPHA", "candidate_gibbs_j_mol": {"ALPHA": -100, "BETA": 0}}]}},
        {"id": "B025-B1", "kind": "boundary", "input": {"components_count": 1, "fixed_external_constraints": 2, "phase_regions": [{"region_id": "IMPOSSIBLE", "phases": ["A", "B"]}]}},
        {"id": "B025-F1", "kind": "failure", "input": {"components_count": 2, "phase_regions": [{"region_id": "A", "phases": ["ALPHA"]}], "adjacency_checks": [{"region_a": "A", "region_b": "UNKNOWN"}]}},
        {"id": "B025-F2", "kind": "failure", "input": {"components_count": 2, "phase_regions": [{"region_id": "AB", "phases": ["A", "B"]}], "lever_tests": [{"test_id": "BAD", "phase_a_composition": [1], "phase_b_composition": [0, 1], "bulk_composition": [0.5, 0.5], "phase_a_fraction": 0.5, "phase_b_fraction": 0.5}]}},
    ]

    @staticmethod
    def _strict_array(payload: Any, maximum: int, label: str) -> tuple[list[Any] | None, str | None]:
        if payload is None:
            return [], None
        if not isinstance(payload, list) or len(payload) > maximum:
            return None, f"{label}必须是最多{maximum}项的数组"
        return payload, None

    def invoke(self, params, context=None):
        errors = self.validate_input(params)
        if errors:
            return fail("; ".join(errors))
        integer_values = {}
        for key, low, high, default in (("components_count", 1, 10, None), ("independent_reactions", 0, 10, 0), ("fixed_external_constraints", 0, 10, 2)):
            raw = params.get(key, default)
            if isinstance(raw, bool) or not isinstance(raw, int) or not low <= raw <= high:
                return fail(f"{key}必须是{low}至{high}的整数")
            integer_values[key] = raw
        tolerance, error = finite(params.get("fraction_tolerance", 1e-8), "fraction_tolerance")
        if error or not 1e-12 <= tolerance <= 0.01:
            return fail(error or "fraction_tolerance超出1e-12至0.01")
        gibbs_tolerance, error = finite(params.get("gibbs_tolerance_j_mol", 1e-6), "gibbs_tolerance_j_mol")
        if error or not 0 <= gibbs_tolerance <= 1000:
            return fail(error or "gibbs_tolerance_j_mol超出0至1000")
        regions_raw = params.get("phase_regions")
        if not isinstance(regions_raw, list) or not 1 <= len(regions_raw) <= 100:
            return fail("phase_regions必须含1至100项")
        regions: dict[str, set[str]] = {}
        for index, raw in enumerate(regions_raw):
            error = strict_object(raw, {"region_id", "phases"}, set(), f"phase_regions[{index}]")
            if error:
                return fail(error)
            region_id, phases = raw["region_id"], raw["phases"]
            if not isinstance(region_id, str) or not region_id.strip() or region_id in regions:
                return fail(f"phase_regions[{index}].region_id必须非空且唯一")
            if not isinstance(phases, list) or not phases or any(not isinstance(phase, str) or not phase.strip() for phase in phases):
                return fail(f"phase_regions[{index}].phases必须是非空相名数组")
            normalized = [phase.strip() for phase in phases]
            if len(normalized) != len(set(normalized)):
                return fail(f"phase_regions[{index}].phases不能重复")
            regions[region_id.strip()] = set(normalized)
        adjacency, error = self._strict_array(params.get("adjacency_checks"), 200, "adjacency_checks")
        if error:
            return fail(error)
        lever_tests, error = self._strict_array(params.get("lever_tests"), 100, "lever_tests")
        if error:
            return fail(error)
        gibbs_tests, error = self._strict_array(params.get("gibbs_tests"), 100, "gibbs_tests")
        if error:
            return fail(error)
        phase_results, adjacency_results, lever_results, gibbs_results, violations = [], [], [], [], []
        c = integer_values["components_count"]
        reactions = integer_values["independent_reactions"]
        constraints = integer_values["fixed_external_constraints"]
        for region_id, phases in regions.items():
            freedom = c - len(phases) + 2 - reactions - constraints
            passed = freedom >= 0
            record = {"region_id": region_id, "phase_count": len(phases), "degrees_of_freedom": freedom, "passed": passed}
            phase_results.append(record)
            if not passed:
                violations.append({"check": "phase_rule", "id": region_id, "message": f"Gibbs相律自由度为{freedom}，小于0"})
        seen_edges: set[tuple[str, str]] = set()
        for index, raw in enumerate(adjacency):
            error = strict_object(raw, {"region_a", "region_b"}, set(), f"adjacency_checks[{index}]")
            if error:
                return fail(error)
            a, b = raw["region_a"], raw["region_b"]
            if a not in regions or b not in regions or a == b:
                return fail(f"adjacency_checks[{index}]必须引用两个不同的已知相区")
            edge = tuple(sorted((a, b)))
            if edge in seen_edges:
                return fail(f"邻接无向边重复: {edge}")
            seen_edges.add(edge)
            difference = sorted(regions[a] ^ regions[b])
            passed = len(difference) == 1
            adjacency_results.append({"region_a": a, "region_b": b, "symmetric_difference": difference, "passed": passed})
            if not passed:
                violations.append({"check": "adjacency", "id": f"{a}|{b}", "message": f"邻接相集对称差含{len(difference)}个相，应为1"})
        max_lever = 0.0
        lever_ids: set[str] = set()
        required_lever = {"test_id", "phase_a_composition", "phase_b_composition", "bulk_composition", "phase_a_fraction", "phase_b_fraction"}
        for index, raw in enumerate(lever_tests):
            error = strict_object(raw, required_lever, set(), f"lever_tests[{index}]")
            if error:
                return fail(error)
            test_id = raw["test_id"]
            if not isinstance(test_id, str) or not test_id.strip() or test_id in lever_ids:
                return fail(f"lever_tests[{index}].test_id必须非空且唯一")
            lever_ids.add(test_id)
            vectors = []
            for field in ("phase_a_composition", "phase_b_composition", "bulk_composition"):
                payload = raw[field]
                if not isinstance(payload, list) or len(payload) != c:
                    return fail(f"lever_tests[{index}].{field}维数必须等于components_count")
                values = []
                for value in payload:
                    number, error = finite(value, f"lever_tests[{index}].{field}")
                    if error or not 0 <= number <= 1:
                        return fail(error or f"{field}分量必须在0至1")
                    values.append(number)
                vectors.append(np.asarray(values))
            fraction_a, error = finite(raw["phase_a_fraction"], f"lever_tests[{index}].phase_a_fraction")
            fraction_b, error_b = finite(raw["phase_b_fraction"], f"lever_tests[{index}].phase_b_fraction")
            if error or error_b or not 0 <= fraction_a <= 1 or not 0 <= fraction_b <= 1:
                return fail(error or error_b or "相分数必须在0至1")
            reconstructed = fraction_a * vectors[0] + fraction_b * vectors[1]
            residuals = reconstructed - vectors[2]
            maximum = float(np.max(np.abs(residuals)))
            closure = max(abs(float(np.sum(vector)) - 1.0) for vector in vectors)
            fraction_closure = abs(fraction_a + fraction_b - 1.0)
            maximum = max(maximum, closure, fraction_closure)
            max_lever = max(max_lever, maximum)
            passed = maximum <= tolerance
            lever_results.append({"test_id": test_id, "reconstructed_bulk_composition": reconstructed.tolist(), "component_residuals": residuals.tolist(), "max_abs_residual": maximum, "passed": passed})
            if not passed:
                violations.append({"check": "lever_rule", "id": test_id, "message": f"杠杆重构/闭合最大残差{maximum:g}超过容差{tolerance:g}"})
        max_gibbs_penalty = 0.0
        gibbs_ids: set[str] = set()
        required_gibbs = {"test_id", "declared_stable", "candidate_gibbs_j_mol"}
        for index, raw in enumerate(gibbs_tests):
            error = strict_object(raw, required_gibbs, set(), f"gibbs_tests[{index}]")
            if error:
                return fail(error)
            test_id, declared, candidates_raw = raw["test_id"], raw["declared_stable"], raw["candidate_gibbs_j_mol"]
            if not isinstance(test_id, str) or not test_id.strip() or test_id in gibbs_ids:
                return fail(f"gibbs_tests[{index}].test_id必须非空且唯一")
            gibbs_ids.add(test_id)
            if not isinstance(candidates_raw, dict) or not candidates_raw:
                return fail(f"gibbs_tests[{index}].candidate_gibbs_j_mol必须是非空对象")
            candidates = {}
            for name, value in candidates_raw.items():
                if not isinstance(name, str) or not name.strip():
                    return fail(f"gibbs_tests[{index}]候选名必须非空")
                number, error = finite(value, f"gibbs_tests[{index}].candidate_gibbs_j_mol.{name}")
                if error:
                    return fail(error)
                candidates[name] = number
            if not isinstance(declared, str) or declared not in candidates:
                return fail(f"gibbs_tests[{index}].declared_stable必须存在于候选表")
            minimum = min(candidates.values())
            penalty = candidates[declared] - minimum
            max_gibbs_penalty = max(max_gibbs_penalty, penalty)
            passed = penalty <= gibbs_tolerance
            gibbs_results.append({"test_id": test_id, "declared_stable": declared, "minimum_candidates": sorted(name for name, value in candidates.items() if value - minimum <= gibbs_tolerance), "gibbs_penalty_j_mol": penalty, "passed": passed})
            if not passed:
                violations.append({"check": "gibbs_stability", "id": test_id, "message": f"声明稳定候选高于最低Gibbs能{penalty:g} J/mol"})
        check_count = len(phase_results) + len(adjacency_results) + len(lever_results) + len(gibbs_results)
        if check_count == 0:
            return fail("没有任何可执行一致性检查项")
        passed = not violations
        warnings_out = [] if passed else [BoundaryWarning("phase_diagram", f"发现{len(violations)}项物理一致性违规；执行本身成功")]
        return ModelResult(
            True,
            result={
                "passed": passed,
                "check_count": check_count,
                "violation_count": len(violations),
                "phase_rule_results": phase_results,
                "adjacency_results": adjacency_results,
                "lever_rule_results": lever_results,
                "gibbs_stability_results": gibbs_results,
                "violations": violations,
                "max_abs_lever_residual": max_lever,
                "max_gibbs_penalty_j_mol": max_gibbs_penalty,
                "components_count": c,
                "independent_reactions": reactions,
                "fixed_external_constraints": constraints,
                "algorithm_version": "phase-rule-adjacency-lever-gibbs-v1",
            },
            boundary_check=BoundaryCheck(not warnings_out, warnings_out),
        )
