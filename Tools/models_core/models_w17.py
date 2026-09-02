"""P1-W17 executable G004/G008/G009/G010 numerical orchestration tools."""

from __future__ import annotations

import bisect
import copy
import math
import random
from statistics import NormalDist
from typing import Any

import numpy as np
from scipy.integrate import solve_ivp

from .base import BaseModelTool, BoundaryCheck, BoundaryWarning, InputField, ModelResult, OutputField


def rel(kind: str, target: str, description: str) -> dict[str, str]:
    return {"type": kind, "target": target, "description": description}


def fail(message: str, code: str = "INVALID_INPUT") -> ModelResult:
    return ModelResult(False, error=message, error_code=code)


def finite(
    value: Any,
    label: str,
    *,
    minimum: float | None = None,
    maximum: float | None = None,
    strict_minimum: bool = False,
) -> tuple[float | None, str | None]:
    if isinstance(value, bool):
        return None, f"{label}必须是数值"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None, f"{label}必须是数值"
    if not math.isfinite(number):
        return None, f"{label}必须是有限数值"
    if minimum is not None and (number <= minimum if strict_minimum else number < minimum):
        return None, f"{label}必须{'大于' if strict_minimum else '不小于'}{minimum:g}"
    if maximum is not None and number > maximum:
        return None, f"{label}不能大于{maximum:g}"
    return number, None


def integer(value: Any, label: str, minimum: int, maximum: int) -> tuple[int | None, str | None]:
    if isinstance(value, bool) or not isinstance(value, int):
        return None, f"{label}必须是整数"
    if not minimum <= value <= maximum:
        return None, f"{label}必须在{minimum}到{maximum}之间"
    return value, None


def nonempty_text(value: Any, label: str) -> tuple[str | None, str | None]:
    normalized = value.strip() if isinstance(value, str) else ""
    if not normalized:
        return None, f"{label}必须是非空字符串"
    return normalized, None


def boundary_result(warnings: list[BoundaryWarning]) -> BoundaryCheck:
    return BoundaryCheck(passed=not warnings, warnings=warnings)


class W17FormulaTool(BaseModelTool):
    priority = "P1"
    status = qualification_status = "qualified"
    count_eligible = True
    data_requirement = "FORMULA_ONLY"
    data_access_mode = "none"


STOICHIOMETRIC_TERM_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "species": {"type": "string", "minLength": 1},
        "coefficient": {"type": "number", "exclusiveMinimum": 0},
    },
    "required": ["species", "coefficient"],
}


REACTION_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "name": {"type": "string", "minLength": 1},
        "reactants": {
            "type": "array",
            "items": STOICHIOMETRIC_TERM_SCHEMA,
            "minItems": 1,
            "maxItems": 25,
        },
        "products": {
            "type": "array",
            "items": STOICHIOMETRIC_TERM_SCHEMA,
            "maxItems": 25,
        },
        "forward_rate_constant_per_s": {"type": "number", "minimum": 0},
        "reverse_rate_constant_per_s": {"type": "number", "minimum": 0},
        "reference_concentration_mol_m3": {"type": "number", "exclusiveMinimum": 0},
    },
    "required": [
        "name",
        "reactants",
        "products",
        "forward_rate_constant_per_s",
        "reverse_rate_constant_per_s",
        "reference_concentration_mol_m3",
    ],
}


class G004_ReactionODESolver(W17FormulaTool):
    model_id, name, version = "G004", "结构化质量作用反应ODE求解", "1.0.0"
    tool_name = "metallurgy_solve_reaction_ode"
    scenario = "数值仿真与工具编排"
    model_type = "结构化质量作用网络/SciPy自适应ODE积分"
    description = (
        "对显式物种、化学计量和正逆速率常数构成的安全质量作用网络执行自适应ODE积分，"
        "返回浓度轨迹、事件和求解器统计；不接受可执行表达式。"
    )
    applicable_boundary = (
        "封闭、均匀、等温批式体系，速率常数由调用方确定；浓度单位mol/m3。"
        "不含传热传质、活度修正、现场反馈、参数拟合或任意代码执行。"
    )
    data_source = ["SciPy solve_ivp 1.18", "dimensionless-concentration mass-action law"]
    source_version = "structured-mass-action-solve-ivp-v1-scipy-1.18.1"
    formula_reference = (
        "r_j=c_ref,j[k_f,j*product((c_i/c_ref,j)^nu_ij)-k_r,j*product((c_i/c_ref,j)^nu'_ij)]; "
        "dc_i/dt=sum_j(nu'_ij-nu_ij)r_j; scipy.integrate.solve_ivp"
    )
    source_records = [
        {
            "source_id": "SCIPY-SOLVE-IVP-1.18",
            "name": "scipy.integrate.solve_ivp",
            "version": "SciPy 1.18.1 project pin",
            "url": "https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.solve_ivp.html",
        },
        {
            "source_id": "MASS-ACTION-NORMALIZED-V1",
            "name": "Dimensionless concentration mass-action normalization",
            "version": "project-algorithm-v1",
        },
    ]
    failure_modes = [
        "物种或反应名称重复、反应引用未知物种或化学计量字段非法",
        "浓度、速率常数、参考浓度、时间范围、容差或最大步长非法",
        "事件启用但物种或阈值不完整",
        "求解器失败、结果非有限或产生超过数值容差的负浓度",
        "把均匀等温批式结果解释为含传热传质或现场控制的完整反应器模型",
    ]
    independent_validation = [
        "一阶不可逆A到B网络与指数解析解交叉验证",
        "可逆A与B网络与解析平衡及守恒量交叉验证",
        "无反应体系严格保持初始浓度",
        "封闭A到B网络总浓度守恒且刚性BDF案例收敛",
    ]
    dependencies = ["C001"]
    relations = [
        rel("accepts_output_from", "C001", "C001可提供温度下的Arrhenius速率常数，G004执行显式反应网络积分"),
        rel("complements", "G002", "G002审核显式步长稳定性，G004使用自适应初值问题求解器并返回收敛统计"),
        rel("target_of", "G009", "G009可通过注册中心对G004标量末态输出做局部敏感性分析"),
        rel("target_of", "G010", "G010可通过注册中心传播G004显式参数的不确定度"),
    ]
    input_fields = [
        InputField("species_names", "物种名称", "array", items={"type": "string", "minLength": 1}, min_items=1, max_items=25),
        InputField("initial_concentrations_mol_m3", "初始浓度", "array", unit="mol/m3", items={"type": "number", "minimum": 0}, min_items=1, max_items=25),
        InputField("reactions", "结构化质量作用反应", "array", required=False, default=[], items=REACTION_SCHEMA, min_items=0, max_items=100),
        InputField("start_time_s", "起始时间", "number", unit="s", min_value=0),
        InputField("end_time_s", "终止时间", "number", unit="s", min_value=0),
        InputField("sample_count", "输出采样点数", "number", unit="1", min_value=2, max_value=1001),
        InputField("solver_method", "求解器方法", "select", default="RK45", enum=["RK45", "DOP853", "Radau", "BDF", "LSODA"]),
        InputField("relative_tolerance", "相对容差", "number", required=False, default=1e-7, unit="1", min_value=1e-12, max_value=1e-2),
        InputField("absolute_tolerance_mol_m3", "绝对容差", "number", required=False, default=1e-9, unit="mol/m3", min_value=1e-15, max_value=1),
        InputField("maximum_step_s", "最大积分步长", "number", required=False, unit="s", min_value=1e-15),
        InputField("event_enabled", "启用浓度阈值事件", "boolean", required=False, default=False),
        InputField("event_species", "事件物种", "string", required=False),
        InputField("event_threshold_mol_m3", "事件浓度阈值", "number", required=False, unit="mol/m3", min_value=0),
        InputField("event_direction", "事件穿越方向", "select", required=False, default="any", enum=["any", "increasing", "decreasing"]),
    ]
    output_fields = [
        OutputField("time_series", "时间与浓度轨迹", "array", "time:s; concentration:mol/m3"),
        OutputField("final_concentrations_mol_m3", "末态物种浓度", "object", "mol/m3"),
        OutputField("final_reaction_rates_mol_m3_s", "末态逐反应净速率", "object", "mol/(m3*s)"),
        OutputField("solver_method", "求解器方法", "string"),
        OutputField("solver_status", "SciPy求解器状态", "number", "1"),
        OutputField("solver_message", "求解器消息", "string"),
        OutputField("function_evaluations", "右端函数求值次数", "number", "1"),
        OutputField("jacobian_evaluations", "Jacobian求值次数", "number", "1"),
        OutputField("lu_decompositions", "LU分解次数", "number", "1"),
        OutputField("minimum_raw_concentration_mol_m3", "积分原始最小浓度", "number", "mol/m3"),
        OutputField("event_triggered", "是否触发事件", "boolean"),
        OutputField("event_time_s", "首次事件时间", "number", "s", nullable=True),
        OutputField("calculation_method", "计算方法", "string"),
    ]
    validation_rules = [
        {"rule": "unique_species_and_reaction_names"},
        {"rule": "structured_stoichiometry_only_no_executable_expressions"},
        {"rule": "positive_time_span_tolerances_and_reference_concentrations"},
        {"rule": "finite_solution_and_no_significant_negative_concentration"},
    ]
    _IRREVERSIBLE = [{
        "name": "A_to_B", "reactants": [{"species": "A", "coefficient": 1}],
        "products": [{"species": "B", "coefficient": 1}],
        "forward_rate_constant_per_s": 0.2, "reverse_rate_constant_per_s": 0,
        "reference_concentration_mol_m3": 1,
    }]
    qualification_cases = [
        {"id": "G004-N1", "kind": "normal", "input": {"species_names": ["A", "B"], "initial_concentrations_mol_m3": [10, 0], "reactions": _IRREVERSIBLE, "start_time_s": 0, "end_time_s": 10, "sample_count": 21, "solver_method": "RK45"}},
        {"id": "G004-N2", "kind": "normal", "input": {"species_names": ["A", "B"], "initial_concentrations_mol_m3": [10, 0], "reactions": [{"name": "A_reversible_B", "reactants": [{"species": "A", "coefficient": 1}], "products": [{"species": "B", "coefficient": 1}], "forward_rate_constant_per_s": 0.4, "reverse_rate_constant_per_s": 0.1, "reference_concentration_mol_m3": 1}], "start_time_s": 0, "end_time_s": 20, "sample_count": 41, "solver_method": "BDF"}},
        {"id": "G004-N3", "kind": "normal", "input": {"species_names": ["inert"], "initial_concentrations_mol_m3": [7.5], "reactions": [], "start_time_s": 0, "end_time_s": 100, "sample_count": 11, "solver_method": "DOP853"}},
        {"id": "G004-B1", "kind": "boundary", "input": {"species_names": ["A", "B"], "initial_concentrations_mol_m3": [10, 0], "reactions": _IRREVERSIBLE, "start_time_s": 0, "end_time_s": 1, "sample_count": 2, "solver_method": "RK45"}},
        {"id": "G004-F1", "kind": "failure", "input": {"species_names": ["A", "A"], "initial_concentrations_mol_m3": [1, 0], "reactions": [], "start_time_s": 0, "end_time_s": 1, "sample_count": 2}},
        {"id": "G004-F2", "kind": "failure", "input": {"species_names": ["A"], "initial_concentrations_mol_m3": [1], "reactions": [{"name": "bad", "reactants": [{"species": "X", "coefficient": 1}], "products": [], "forward_rate_constant_per_s": 1, "reverse_rate_constant_per_s": 0, "reference_concentration_mol_m3": 1}], "start_time_s": 0, "end_time_s": 1, "sample_count": 2}},
    ]

    @staticmethod
    def _parse_terms(raw: Any, species_index: dict[str, int], label: str, allow_empty: bool) -> tuple[list[tuple[int, float]] | None, str | None]:
        if not isinstance(raw, list) or (not allow_empty and not raw) or len(raw) > 25:
            return None, f"{label}必须包含{'0到' if allow_empty else '1到'}25个化学计量项"
        parsed: list[tuple[int, float]] = []
        seen: set[str] = set()
        for index, item in enumerate(raw):
            if not isinstance(item, dict) or set(item) != {"species", "coefficient"}:
                return None, f"{label}[{index}]字段必须且只能为species和coefficient"
            species, error = nonempty_text(item.get("species"), f"{label}[{index}].species")
            if error:
                return None, error
            if species not in species_index:
                return None, f"{label}[{index}]引用未知物种{species}"
            if species in seen:
                return None, f"{label}内物种{species}重复"
            coefficient, error = finite(item.get("coefficient"), f"{label}[{index}].coefficient", minimum=0, strict_minimum=True)
            if error:
                return None, error
            seen.add(species)
            parsed.append((species_index[species], coefficient))
        return parsed, None

    def _parse_network(self, params: dict) -> tuple[dict[str, Any] | None, str | None]:
        species_raw = params.get("species_names")
        initials_raw = params.get("initial_concentrations_mol_m3")
        if not isinstance(species_raw, list) or not 1 <= len(species_raw) <= 25:
            return None, "species_names必须包含1到25个物种"
        species: list[str] = []
        for index, value in enumerate(species_raw):
            name, error = nonempty_text(value, f"species_names[{index}]")
            if error:
                return None, error
            if name in species:
                return None, f"species_names中物种{name}重复"
            species.append(name)
        if not isinstance(initials_raw, list) or len(initials_raw) != len(species):
            return None, "initial_concentrations_mol_m3长度必须等于species_names长度"
        initials: list[float] = []
        for index, value in enumerate(initials_raw):
            concentration, error = finite(value, f"initial_concentrations_mol_m3[{index}]", minimum=0)
            if error:
                return None, error
            initials.append(concentration)

        reactions_raw = params.get("reactions", [])
        if not isinstance(reactions_raw, list) or len(reactions_raw) > 100:
            return None, "reactions必须包含0到100个反应"
        species_index = {name: index for index, name in enumerate(species)}
        reactions: list[dict[str, Any]] = []
        reaction_names: set[str] = set()
        required = {
            "name", "reactants", "products", "forward_rate_constant_per_s",
            "reverse_rate_constant_per_s", "reference_concentration_mol_m3",
        }
        for index, item in enumerate(reactions_raw):
            if not isinstance(item, dict) or set(item) != required:
                return None, f"reactions[{index}]字段必须且只能为{sorted(required)}"
            name, error = nonempty_text(item.get("name"), f"reactions[{index}].name")
            if error:
                return None, error
            if name in reaction_names:
                return None, f"反应名称{name}重复"
            reactants, error = self._parse_terms(item.get("reactants"), species_index, f"reactions[{index}].reactants", False)
            if error:
                return None, error
            products, error = self._parse_terms(item.get("products"), species_index, f"reactions[{index}].products", True)
            if error:
                return None, error
            forward, error = finite(item.get("forward_rate_constant_per_s"), f"reactions[{index}].forward_rate_constant_per_s", minimum=0)
            if error:
                return None, error
            reverse, error = finite(item.get("reverse_rate_constant_per_s"), f"reactions[{index}].reverse_rate_constant_per_s", minimum=0)
            if error:
                return None, error
            reference, error = finite(item.get("reference_concentration_mol_m3"), f"reactions[{index}].reference_concentration_mol_m3", minimum=0, strict_minimum=True)
            if error:
                return None, error
            if forward == 0 and reverse == 0:
                return None, f"reactions[{index}]正逆速率常数不能同时为0"
            reaction_names.add(name)
            reactions.append({"name": name, "reactants": reactants, "products": products, "forward": forward, "reverse": reverse, "reference": reference})
        return {"species": species, "initials": initials, "reactions": reactions}, None

    @staticmethod
    def _rates(concentrations: np.ndarray, reactions: list[dict[str, Any]]) -> np.ndarray:
        nonnegative = np.maximum(concentrations, 0.0)
        rates = np.zeros(len(reactions), dtype=float)
        for index, reaction in enumerate(reactions):
            reference = reaction["reference"]
            forward = reaction["forward"] * reference
            for species_index, coefficient in reaction["reactants"]:
                forward *= (nonnegative[species_index] / reference) ** coefficient
            reverse = reaction["reverse"] * reference
            for species_index, coefficient in reaction["products"]:
                reverse *= (nonnegative[species_index] / reference) ** coefficient
            rates[index] = forward - reverse
        return rates

    def invoke(self, params, context=None):
        errors = self.validate_input(params)
        if errors:
            return fail("；".join(errors))
        network, error = self._parse_network(params)
        if error:
            return fail(error)
        start, error = finite(params.get("start_time_s"), "start_time_s", minimum=0)
        if error:
            return fail(error, "OUT_OF_DOMAIN")
        end, error = finite(params.get("end_time_s"), "end_time_s", minimum=0)
        if error or end <= start:
            return fail(error or "end_time_s必须大于start_time_s", "OUT_OF_DOMAIN")
        sample_count_value = params.get("sample_count")
        if isinstance(sample_count_value, float) and sample_count_value.is_integer():
            sample_count_value = int(sample_count_value)
        sample_count, error = integer(sample_count_value, "sample_count", 2, 1001)
        if error:
            return fail(error, "OUT_OF_DOMAIN")
        rtol, error = finite(params.get("relative_tolerance", 1e-7), "relative_tolerance", minimum=1e-12, maximum=1e-2)
        if error:
            return fail(error, "OUT_OF_DOMAIN")
        atol, error = finite(params.get("absolute_tolerance_mol_m3", 1e-9), "absolute_tolerance_mol_m3", minimum=1e-15, maximum=1)
        if error:
            return fail(error, "OUT_OF_DOMAIN")
        max_step_raw = params.get("maximum_step_s", math.inf)
        if max_step_raw == math.inf:
            max_step = math.inf
        else:
            max_step, error = finite(max_step_raw, "maximum_step_s", minimum=0, strict_minimum=True)
            if error:
                return fail(error, "OUT_OF_DOMAIN")
        method = params.get("solver_method", "RK45")

        species = network["species"]
        reactions = network["reactions"]
        stoichiometry = np.zeros((len(species), len(reactions)), dtype=float)
        for reaction_index, reaction in enumerate(reactions):
            for species_index, coefficient in reaction["reactants"]:
                stoichiometry[species_index, reaction_index] -= coefficient
            for species_index, coefficient in reaction["products"]:
                stoichiometry[species_index, reaction_index] += coefficient

        def rhs(_time, concentrations):
            if not reactions:
                return np.zeros(len(species), dtype=float)
            return stoichiometry @ self._rates(concentrations, reactions)

        event_enabled = params.get("event_enabled", False)
        event_function = None
        if event_enabled:
            event_species, error = nonempty_text(params.get("event_species"), "event_species")
            if error:
                return fail(error)
            if event_species not in species:
                return fail(f"event_species引用未知物种{event_species}")
            event_threshold, error = finite(params.get("event_threshold_mol_m3"), "event_threshold_mol_m3", minimum=0)
            if error:
                return fail(error, "OUT_OF_DOMAIN")
            event_index = species.index(event_species)
            direction = params.get("event_direction", "any")

            def threshold_event(_time, concentrations):
                return concentrations[event_index] - event_threshold

            threshold_event.direction = {"any": 0.0, "increasing": 1.0, "decreasing": -1.0}[direction]
            threshold_event.terminal = False
            event_function = threshold_event
        elif "event_species" in params or "event_threshold_mol_m3" in params:
            return fail("event_enabled=false时不得提交事件物种或阈值")

        times = np.linspace(start, end, sample_count)
        try:
            solution = solve_ivp(
                rhs,
                (start, end),
                np.asarray(network["initials"], dtype=float),
                method=method,
                t_eval=times,
                events=event_function,
                rtol=rtol,
                atol=atol,
                max_step=max_step,
            )
        except (ValueError, FloatingPointError, OverflowError) as exc:
            return fail(f"ODE积分输入或数值计算失败: {exc}", "NUMERICAL_ERROR")
        if not solution.success:
            return fail(f"ODE积分未收敛: {solution.message}", "NUMERICAL_ERROR")
        if solution.y.shape != (len(species), sample_count) or not np.all(np.isfinite(solution.y)):
            return fail("ODE积分结果维度异常或包含非有限值", "NUMERICAL_ERROR")
        minimum_raw = float(np.min(solution.y))
        negative_tolerance = max(1e-8, 100 * atol)
        if minimum_raw < -negative_tolerance:
            return fail(f"ODE积分产生显著负浓度{minimum_raw:g} mol/m3", "OUT_OF_DOMAIN")
        clipped = np.maximum(solution.y, 0.0)
        final = clipped[:, -1]
        final_rates = self._rates(final, reactions)
        time_series = [
            {
                "time_s": float(solution.t[column]),
                "concentrations_mol_m3": {species[row]: float(clipped[row, column]) for row in range(len(species))},
            }
            for column in range(solution.t.size)
        ]
        event_times = [] if not event_enabled else [float(value) for value in solution.t_events[0]]
        warnings: list[BoundaryWarning] = []
        if sample_count <= 2:
            warnings.append(BoundaryWarning("sample_count", "仅输出起止两点，可能无法展示中间动力学形状"))
        if minimum_raw < 0:
            warnings.append(BoundaryWarning("concentrations", "求解器产生容差内微小负值，输出已截断为0"))
        return ModelResult(
            True,
            result={
                "time_series": time_series,
                "final_concentrations_mol_m3": {name: float(final[index]) for index, name in enumerate(species)},
                "final_reaction_rates_mol_m3_s": {reaction["name"]: float(final_rates[index]) for index, reaction in enumerate(reactions)},
                "solver_method": method,
                "solver_status": int(solution.status),
                "solver_message": str(solution.message),
                "function_evaluations": int(solution.nfev),
                "jacobian_evaluations": int(solution.njev or 0),
                "lu_decompositions": int(solution.nlu or 0),
                "minimum_raw_concentration_mol_m3": minimum_raw,
                "event_triggered": bool(event_times),
                "event_time_s": event_times[0] if event_times else None,
                "calculation_method": "structured dimensionless-concentration mass action + scipy.solve_ivp",
            },
            boundary_check=boundary_result(warnings),
        )


SENSITIVITY_PARAMETER_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "path": {"type": "string", "minLength": 1},
        "label": {"type": "string", "minLength": 1},
        "unit": {"type": "string", "minLength": 1},
        "absolute_step": {"type": "number", "exclusiveMinimum": 0},
    },
    "required": ["path", "label", "unit", "absolute_step"],
}


UNCERTAIN_PARAMETER_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "path": {"type": "string", "minLength": 1},
        "label": {"type": "string", "minLength": 1},
        "unit": {"type": "string", "minLength": 1},
        "distribution": {"type": "string", "enum": ["uniform", "normal", "triangular"]},
        "minimum": {"type": "number"},
        "maximum": {"type": "number"},
        "mean": {"type": "number"},
        "standard_deviation": {"type": "number", "exclusiveMinimum": 0},
        "mode": {"type": "number"},
    },
    "required": ["path", "label", "unit", "distribution"],
}


def _split_path(path: Any, label: str) -> tuple[list[str] | None, str | None]:
    normalized, error = nonempty_text(path, label)
    if error:
        return None, error
    parts = normalized.split(".")
    if any(not part or part.startswith("_") for part in parts):
        return None, f"{label}必须是由非空公开字段构成的点分路径"
    return parts, None


def _read_path(root: Any, path: str, label: str) -> tuple[Any, str | None]:
    parts, error = _split_path(path, label)
    if error:
        return None, error
    current = root
    for part in parts:
        if isinstance(current, dict):
            if part not in current:
                return None, f"{label}路径不存在: {path}"
            current = current[part]
        elif isinstance(current, list) and part.isdigit():
            index = int(part)
            if index >= len(current):
                return None, f"{label}数组索引越界: {path}"
            current = current[index]
        else:
            return None, f"{label}无法穿过非对象字段: {path}"
    return current, None


def _write_numeric_path(root: dict[str, Any], path: str, value: float, label: str) -> str | None:
    parts, error = _split_path(path, label)
    if error:
        return error
    current: Any = root
    for part in parts[:-1]:
        if isinstance(current, dict) and part in current:
            current = current[part]
        elif isinstance(current, list) and part.isdigit() and int(part) < len(current):
            current = current[int(part)]
        else:
            return f"{label}路径不存在: {path}"
    leaf = parts[-1]
    if isinstance(current, dict) and leaf in current:
        old_value = current[leaf]
        current[leaf] = value
    elif isinstance(current, list) and leaf.isdigit() and int(leaf) < len(current):
        index = int(leaf)
        old_value = current[index]
        current[index] = value
    else:
        return f"{label}路径不存在: {path}"
    if isinstance(old_value, bool) or not isinstance(old_value, (int, float)) or not math.isfinite(float(old_value)):
        return f"{label}目标必须是有限数值: {path}"
    return None


def _registered_target(model_code: Any) -> tuple[Any | None, str | None, str | None]:
    code, error = nonempty_text(model_code, "target_model_code")
    if error:
        return None, None, error
    if code in {"G009", "G010"}:
        return None, code, "禁止把敏感性或不确定度编排工具作为嵌套目标"
    from .registry import registry as global_registry

    target = global_registry.get(code)
    if target is None:
        return None, code, f"未知目标工具: {code}"
    eligibility = global_registry.eligibility_report(code)
    if not eligibility.get("fully_eligible"):
        return None, code, f"目标工具{code}未通过完整资格闸门"
    return target, code, None


def _invoke_target_scalar(
    target: Any,
    arguments: dict[str, Any],
    output_path: str,
    allow_boundary_warnings: bool,
) -> tuple[float | None, int, str | None]:
    from .registry import registry as global_registry

    result = global_registry.invoke(target.model_id, arguments)
    if not result.success:
        return None, 0, f"目标工具{target.model_id}调用失败[{result.error_code}]: {result.error}"
    warning_count = len(result.boundary_check.warnings) if result.boundary_check else 0
    if result.boundary_check and not result.boundary_check.passed and not allow_boundary_warnings:
        return None, warning_count, f"目标工具{target.model_id}返回适用域警告，当前配置拒绝传播"
    raw_value, error = _read_path(result.result, output_path, "output_path")
    if error:
        return None, warning_count, error
    value, error = finite(raw_value, "目标输出标量")
    if error:
        return None, warning_count, error
    return value, warning_count, None


def _target_output_unit(target: Any, output_path: str) -> str:
    top_level = output_path.split(".", 1)[0]
    for field_spec in target.output_fields:
        if field_spec.name == top_level:
            return field_spec.unit or "declared target output unit"
    return "declared target output unit"


class G009_LocalSensitivity(W17FormulaTool):
    model_id, name, version = "G009", "注册工具局部敏感性分析", "1.0.0"
    tool_name = "metallurgy_run_local_sensitivity_analysis"
    scenario = "数值仿真与工具编排"
    model_type = "注册工具中心差分/局部弹性"
    description = "对一个已通过资格闸门的注册工具标量输出执行安全中心差分，返回一阶、二阶局部敏感度与排序。"
    applicable_boundary = (
        "目标必须是本注册中心中已完整认证且输入输出确定的工具；参数路径必须指向base_arguments中的有限数值。"
        "只评估调用点附近，不接受表达式、任意Python代码、G009/G010嵌套或跨不连续点的全局解释。"
    )
    data_source = ["Fornberg finite-difference weights", "registered qualified executable tool outputs"]
    source_version = "registered-tool-central-difference-v1"
    formula_reference = "dy/dx≈[y(x+h)-y(x-h)]/(2h); d2y/dx2≈[y(x+h)-2y(x)+y(x-h)]/h2; elasticity=(x/y)dy/dx"
    source_records = [
        {
            "source_id": "FORNBERG-1988-FD",
            "name": "Generation of finite difference formulas on arbitrarily spaced grids",
            "version": "Mathematics of Computation 51 (1988)",
            "url": "https://doi.org/10.1090/S0025-5718-1988-0935077-0",
        },
        {
            "source_id": "PROJECT-QUALIFIED-REGISTRY-V1",
            "name": "Qualified executable tool registry as a safe callable target",
            "version": "project-contract-v1",
        },
    ]
    failure_modes = [
        "目标不存在、未通过完整资格闸门或试图嵌套G009/G010",
        "base_arguments、output_path或参数路径不存在，或参数/输出不是有限标量",
        "扰动后的目标工具调用失败或返回未获允许的适用域警告",
        "步长非正、参数路径重复、参数项字段不完整或含额外字段",
        "把局部中心差分解释为全局敏感性、因果关系或跨不连续点导数",
    ]
    independent_validation = [
        "对G008仿射查表y=2x+1恢复一阶导数2且二阶导数0",
        "对T001的热导率和面积分别恢复解析偏导并比较弹性",
        "对C001温度参数的差分结果与Arrhenius解析导数交叉验证",
        "缩小步长时平滑目标的一阶导数收敛并保持排序确定性",
    ]
    dependencies = ["G008"]
    relations = [
        rel("depends_on", "G008", "以G008仿射查表作为独立可解析准入基准"),
        rel("can_analyze", "G004", "可对G004显式网络的标量末态字段做局部参数扰动"),
        rel("overlaps", "A010", "A010传播给定解析导数的不确定度；G009通过注册工具调用估计局部导数"),
        rel("upstream_of", "G010", "G009可先筛选敏感参数，G010再执行联合分布传播"),
    ]
    input_fields = [
        InputField("target_model_code", "目标注册工具代码", "string"),
        InputField("base_arguments", "目标工具基准参数", "object"),
        InputField("output_path", "目标标量输出点分路径", "string"),
        InputField("parameter_steps", "待扰动参数与绝对步长", "array", items=SENSITIVITY_PARAMETER_SCHEMA, min_items=1, max_items=12),
        InputField("allow_target_boundary_warnings", "允许目标适用域警告", "boolean", required=False, default=False),
    ]
    output_fields = [
        OutputField("target_model_code", "目标工具代码", "string"),
        OutputField("target_tool_name", "目标函数名", "string"),
        OutputField("target_tool_uid", "目标不可变工具UID", "string"),
        OutputField("target_model_version", "目标工具版本", "string"),
        OutputField("output_path", "目标输出路径", "string"),
        OutputField("output_unit", "目标输出单位", "string"),
        OutputField("baseline_output_value", "基准输出值", "number", "declared target output unit"),
        OutputField("evaluation_count", "目标调用次数", "number", "1"),
        OutputField("parameter_results", "逐参数局部敏感度", "array", "derivative: output/parameter unit"),
        OutputField("sensitivity_ranking", "按中心差分尺度效应排序", "array", "declared target output unit"),
        OutputField("ranking_method", "排序规则", "string"),
        OutputField("target_boundary_warning_count", "目标适用域警告总数", "number", "1"),
        OutputField("calculation_method", "计算方法", "string"),
    ]
    validation_rules = [
        {"rule": "target_must_be_fully_eligible_and_not_nested_orchestrator"},
        {"rule": "dot_paths_resolve_to_finite_scalars"},
        {"rule": "positive_unique_absolute_steps"},
        {"rule": "central_difference_requires_two_successful_target_calls_per_parameter"},
    ]
    _AFFINE_BASE = {
        "table_id": "sensitivity-affine", "table_version": "1", "dimension": "one_dimensional",
        "x_axis": [0, 5], "x_unit": "1", "values": [1, 11], "value_unit": "K",
        "query_x": 2, "method": "linear", "out_of_bounds_policy": "reject",
    }
    qualification_cases = [
        {"id": "G009-N1", "kind": "normal", "input": {"target_model_code": "G008", "base_arguments": _AFFINE_BASE, "output_path": "interpolated_value", "parameter_steps": [{"path": "query_x", "label": "查询坐标", "unit": "1", "absolute_step": 0.1}]}},
        {"id": "G009-N2", "kind": "normal", "input": {"target_model_code": "C001", "base_arguments": {"A": 10000000, "Ea": 80000, "temperature": 1000, "Ea_unit": "J/mol"}, "output_path": "k", "parameter_steps": [{"path": "temperature", "label": "温度", "unit": "K", "absolute_step": 0.1}]}},
        {"id": "G009-N3", "kind": "normal", "input": {"target_model_code": "T001", "base_arguments": {"thermal_conductivity": 20, "thickness": 0.1, "area": 2, "hot_temperature": 1000, "cold_temperature": 500}, "output_path": "heat_rate_w", "parameter_steps": [{"path": "thermal_conductivity", "label": "导热系数", "unit": "W/(m*K)", "absolute_step": 0.1}, {"path": "area", "label": "面积", "unit": "m2", "absolute_step": 0.01}]}},
        {"id": "G009-B1", "kind": "boundary", "input": {"target_model_code": "T001", "base_arguments": {"thermal_conductivity": 20, "thickness": 0.1, "area": 2, "hot_temperature": 1000, "cold_temperature": 500}, "output_path": "heat_rate_w", "parameter_steps": [{"path": "thickness", "label": "厚度", "unit": "m", "absolute_step": 0.05}]}},
        {"id": "G009-F1", "kind": "failure", "input": {"target_model_code": "UNKNOWN", "base_arguments": {"x": 1}, "output_path": "y", "parameter_steps": [{"path": "x", "label": "x", "unit": "1", "absolute_step": 0.1}]}},
        {"id": "G009-F2", "kind": "failure", "input": {"target_model_code": "G008", "base_arguments": {"table_id": "cross-domain", "table_version": "1", "dimension": "one_dimensional", "x_axis": [0, 1], "x_unit": "1", "values": [0, 1], "value_unit": "1", "query_x": 0.05, "method": "linear", "out_of_bounds_policy": "reject"}, "output_path": "interpolated_value", "parameter_steps": [{"path": "query_x", "label": "查询坐标", "unit": "1", "absolute_step": 0.1}]}},
    ]

    @staticmethod
    def _parse_steps(raw: Any, base_arguments: dict[str, Any]) -> tuple[list[dict[str, Any]] | None, str | None]:
        if not isinstance(raw, list) or not 1 <= len(raw) <= 12:
            return None, "parameter_steps必须包含1到12项"
        required = {"path", "label", "unit", "absolute_step"}
        parsed: list[dict[str, Any]] = []
        seen: set[str] = set()
        for index, item in enumerate(raw):
            if not isinstance(item, dict) or set(item) != required:
                return None, f"parameter_steps[{index}]字段必须且只能为{sorted(required)}"
            path, error = nonempty_text(item.get("path"), f"parameter_steps[{index}].path")
            if error:
                return None, error
            if path in seen:
                return None, f"参数路径重复: {path}"
            label, error = nonempty_text(item.get("label"), f"parameter_steps[{index}].label")
            if error:
                return None, error
            unit, error = nonempty_text(item.get("unit"), f"parameter_steps[{index}].unit")
            if error:
                return None, error
            base_value, error = _read_path(base_arguments, path, f"parameter_steps[{index}].path")
            if error:
                return None, error
            base_value, error = finite(base_value, f"parameter_steps[{index}]基准值")
            if error:
                return None, error
            step, error = finite(item.get("absolute_step"), f"parameter_steps[{index}].absolute_step", minimum=0, strict_minimum=True)
            if error:
                return None, error
            seen.add(path)
            parsed.append({"path": path, "label": label, "unit": unit, "base_value": base_value, "step": step})
        return parsed, None

    def invoke(self, params, context=None):
        errors = self.validate_input(params)
        if errors:
            return fail("；".join(errors))
        base_arguments = params.get("base_arguments")
        if not isinstance(base_arguments, dict) or not base_arguments:
            return fail("base_arguments必须是非空对象")
        output_path, error = nonempty_text(params.get("output_path"), "output_path")
        if error:
            return fail(error)
        target, target_code, error = _registered_target(params.get("target_model_code"))
        if error:
            return fail(error, "UNKNOWN_MODEL" if target_code == "UNKNOWN" else "MODEL_NOT_APPLICABLE")
        steps, error = self._parse_steps(params.get("parameter_steps"), base_arguments)
        if error:
            return fail(error)
        allow_warnings = params.get("allow_target_boundary_warnings", False)
        baseline, warning_count, error = _invoke_target_scalar(target, copy.deepcopy(base_arguments), output_path, allow_warnings)
        if error:
            return fail(error, "MODEL_NOT_APPLICABLE")
        total_warnings = warning_count
        results: list[dict[str, Any]] = []
        warnings: list[BoundaryWarning] = []
        for item in steps:
            if item["step"] > 0.1 * max(abs(item["base_value"]), 1e-12):
                warnings.append(BoundaryWarning(item["path"], "绝对步长超过基准值幅度的10%，局部线性解释需谨慎"))
            plus_arguments = copy.deepcopy(base_arguments)
            minus_arguments = copy.deepcopy(base_arguments)
            write_error = _write_numeric_path(plus_arguments, item["path"], item["base_value"] + item["step"], "parameter_path")
            write_error = write_error or _write_numeric_path(minus_arguments, item["path"], item["base_value"] - item["step"], "parameter_path")
            if write_error:
                return fail(write_error)
            plus, count, error = _invoke_target_scalar(target, plus_arguments, output_path, allow_warnings)
            total_warnings += count
            if error:
                return fail(f"参数{item['path']}正向扰动失败: {error}", "MODEL_NOT_APPLICABLE")
            minus, count, error = _invoke_target_scalar(target, minus_arguments, output_path, allow_warnings)
            total_warnings += count
            if error:
                return fail(f"参数{item['path']}负向扰动失败: {error}", "MODEL_NOT_APPLICABLE")
            derivative = (plus - minus) / (2 * item["step"])
            second_derivative = (plus - 2 * baseline + minus) / (item["step"] ** 2)
            elasticity = None if baseline == 0 else derivative * item["base_value"] / baseline
            scale_effect = abs(plus - minus) / 2
            results.append({
                "path": item["path"], "label": item["label"], "unit": item["unit"],
                "base_value": item["base_value"], "absolute_step": item["step"],
                "minus_output": minus, "baseline_output": baseline, "plus_output": plus,
                "first_derivative": derivative, "second_derivative": second_derivative,
                "local_elasticity": elasticity, "central_scale_effect": scale_effect,
            })
        if total_warnings:
            warnings.append(BoundaryWarning("target", f"目标工具累计返回{total_warnings}条已允许的适用域警告"))
        ranking = [
            {"rank": index + 1, "path": item["path"], "central_scale_effect": item["central_scale_effect"]}
            for index, item in enumerate(sorted(results, key=lambda row: (-row["central_scale_effect"], row["path"])))
        ]
        return ModelResult(True, result={
            "target_model_code": target.model_id,
            "target_tool_name": target.tool_name,
            "target_tool_uid": target.tool_uid,
            "target_model_version": target.version,
            "output_path": output_path,
            "output_unit": _target_output_unit(target, output_path),
            "baseline_output_value": baseline,
            "evaluation_count": 1 + 2 * len(steps),
            "parameter_results": results,
            "sensitivity_ranking": ranking,
            "ranking_method": "descending absolute central two-sided output change; path ascending on ties",
            "target_boundary_warning_count": total_warnings,
            "calculation_method": "safe registered-tool central difference with explicit numeric dot paths",
        }, boundary_check=boundary_result(warnings))


def _normal_cdf(value: float) -> float:
    return 0.5 * (1.0 + math.erf(value / math.sqrt(2.0)))


def _quantile_type7(sorted_values: list[float], probability: float) -> float:
    if len(sorted_values) == 1:
        return sorted_values[0]
    position = (len(sorted_values) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    weight = position - lower
    return (1 - weight) * sorted_values[lower] + weight * sorted_values[upper]


class G010_MonteCarloUncertainty(W17FormulaTool):
    model_id, name, version = "G010", "注册工具蒙特卡洛不确定度传播", "1.0.0"
    tool_name = "metallurgy_run_monte_carlo_uncertainty"
    scenario = "数值仿真与工具编排"
    model_type = "固定种子相关蒙特卡洛传播"
    description = "按显式分布和相关矩阵采样注册工具参数，以固定随机种子传播到标量输出并给出分位数和失效概率。"
    applicable_boundary = (
        "目标必须是已完整认证且确定执行的注册工具；1到8个连续不确定参数，10到2000个样本，相关矩阵须正定。"
        "支持uniform、normal、triangular边缘分布和Gaussian copula，不接受现场流、任意代码或G009/G010嵌套。"
    )
    data_source = ["BIPM JCGM 101:2008", "fixed-seed Gaussian-copula sampling", "qualified executable tool registry"]
    source_version = "registered-tool-monte-carlo-jcgm101-v1"
    formula_reference = "z=L*u, u~N(0,I); marginal x=F^-1(Phi(z)); output statistics use sample SD and Hyndman-Fan type-7 quantiles; Wilson binomial interval"
    source_records = [
        {
            "source_id": "JCGM-101-2008",
            "name": "Evaluation of measurement data—Supplement 1: Propagation of distributions using a Monte Carlo method",
            "version": "JCGM 101:2008",
            "url": "https://doi.org/10.59161/JCGM101-2008",
        },
        {
            "source_id": "PROJECT-GAUSSIAN-COPULA-V1",
            "name": "Fixed-seed Gaussian-copula parameter sampler",
            "version": "project-algorithm-v1",
        },
    ]
    failure_modes = [
        "目标不存在、未完整认证或试图嵌套G009/G010",
        "不确定参数路径不存在/重复，分布字段组合非法或相关矩阵非对称、非正定",
        "样本扰动导致目标调用失败、输出非标量或返回未获允许的适用域警告",
        "样本数或随机种子越界，统计量产生非有限值",
        "把有限样本结果解释为现场概率、因果置信度或未声明尾部之外的可靠外推",
    ]
    independent_validation = [
        "固定种子、相同输入重复执行得到逐字段相同统计结果",
        "常数G008响应的均值等于常数且样本标准差严格为0",
        "仿射G008响应的样本均值和方差与均匀分布解析矩近似一致",
        "样本均落入uniform/triangular声明边界，输出分位数单调且Wilson区间包含样本失效率",
    ]
    dependencies = ["G008"]
    relations = [
        rel("depends_on", "G008", "以显式仿射和常数查表验证采样传播的统计性质"),
        rel("can_analyze", "G004", "可把显式反应网络参数分布传播到末态标量输出"),
        rel("overlaps", "A010", "A010是一阶解析传播；G010通过注册工具重复执行传播非线性分布"),
        rel("downstream_of", "G009", "可根据G009局部排序选择需要联合传播的不确定参数"),
    ]
    input_fields = [
        InputField("target_model_code", "目标注册工具代码", "string"),
        InputField("base_arguments", "目标工具基准参数", "object"),
        InputField("output_path", "目标标量输出点分路径", "string"),
        InputField("uncertain_parameters", "不确定参数分布", "array", items=UNCERTAIN_PARAMETER_SCHEMA, min_items=1, max_items=8),
        InputField("correlation_matrix", "潜在正态相关矩阵", "array", unit="1", items={"type": "array", "items": {"type": "number"}, "minItems": 1, "maxItems": 8}, min_items=1, max_items=8),
        InputField("random_seed", "固定随机种子", "number", unit="1", min_value=0, max_value=2147483647),
        InputField("sample_count", "蒙特卡洛样本数", "number", unit="1", min_value=10, max_value=2000),
        InputField("failure_operator", "失效判据", "select", enum=["greater_than", "less_than"]),
        InputField("failure_threshold", "失效阈值", "number", unit="declared target output unit"),
        InputField("allow_target_boundary_warnings", "允许目标适用域警告", "boolean", required=False, default=False),
    ]
    output_fields = [
        OutputField("target_model_code", "目标工具代码", "string"),
        OutputField("target_tool_name", "目标函数名", "string"),
        OutputField("target_tool_uid", "目标不可变工具UID", "string"),
        OutputField("target_model_version", "目标工具版本", "string"),
        OutputField("output_path", "目标输出路径", "string"),
        OutputField("output_unit", "目标输出单位", "string"),
        OutputField("sample_count", "样本数", "number", "1"),
        OutputField("evaluation_count", "目标调用次数", "number", "1"),
        OutputField("random_seed", "随机种子", "number", "1"),
        OutputField("parameter_sample_summaries", "参数样本统计", "array", "declared parameter units"),
        OutputField("realized_correlation_matrix", "实现的Pearson相关矩阵", "array", "1"),
        OutputField("output_statistics", "输出统计量", "object", "declared target output unit"),
        OutputField("failure_operator", "失效判据", "string"),
        OutputField("failure_threshold", "失效阈值", "number", "declared target output unit"),
        OutputField("failure_count", "失效样本数", "number", "1"),
        OutputField("estimated_failure_probability", "估计失效概率", "number", "1"),
        OutputField("failure_probability_wilson_95", "失效概率Wilson 95%区间", "array", "1"),
        OutputField("target_boundary_warning_count", "目标适用域警告总数", "number", "1"),
        OutputField("quantile_method", "分位数算法", "string"),
        OutputField("calculation_method", "计算方法", "string"),
    ]
    validation_rules = [
        {"rule": "target_must_be_fully_eligible_and_not_nested_orchestrator"},
        {"rule": "distribution_specific_parameters_and_unique_numeric_paths"},
        {"rule": "symmetric_positive_definite_unit_diagonal_correlation_matrix"},
        {"rule": "fixed_seed_bounded_sample_count_and_all_target_calls_succeed"},
    ]
    _AFFINE_BASE = {
        "table_id": "mc-affine", "table_version": "1", "dimension": "one_dimensional",
        "x_axis": [0, 1], "x_unit": "1", "values": [1, 3], "value_unit": "K",
        "query_x": 0.5, "method": "linear", "out_of_bounds_policy": "reject",
    }
    _UNIFORM_X = [{"path": "query_x", "label": "查询坐标", "unit": "1", "distribution": "uniform", "minimum": 0, "maximum": 1}]
    qualification_cases = [
        {"id": "G010-N1", "kind": "normal", "input": {"target_model_code": "G008", "base_arguments": _AFFINE_BASE, "output_path": "interpolated_value", "uncertain_parameters": _UNIFORM_X, "correlation_matrix": [[1]], "random_seed": 20260902, "sample_count": 256, "failure_operator": "greater_than", "failure_threshold": 2}},
        {"id": "G010-N2", "kind": "normal", "input": {"target_model_code": "G008", "base_arguments": {"table_id": "mc-biaffine", "table_version": "1", "dimension": "two_dimensional", "x_axis": [0, 1], "x_unit": "1", "y_axis": [0, 1], "y_unit": "1", "values": [0, 1, 1, 2], "value_unit": "1", "query_x": 0.5, "query_y": 0.5, "method": "linear", "out_of_bounds_policy": "reject"}, "output_path": "interpolated_value", "uncertain_parameters": [{"path": "query_x", "label": "x", "unit": "1", "distribution": "uniform", "minimum": 0, "maximum": 1}, {"path": "query_y", "label": "y", "unit": "1", "distribution": "uniform", "minimum": 0, "maximum": 1}], "correlation_matrix": [[1, 0.5], [0.5, 1]], "random_seed": 42, "sample_count": 256, "failure_operator": "greater_than", "failure_threshold": 1}},
        {"id": "G010-N3", "kind": "normal", "input": {"target_model_code": "G008", "base_arguments": {"table_id": "mc-constant", "table_version": "1", "dimension": "one_dimensional", "x_axis": [0, 1], "x_unit": "1", "values": [5, 5], "value_unit": "K", "query_x": 0.5, "method": "linear", "out_of_bounds_policy": "reject"}, "output_path": "interpolated_value", "uncertain_parameters": _UNIFORM_X, "correlation_matrix": [[1]], "random_seed": 7, "sample_count": 128, "failure_operator": "less_than", "failure_threshold": 4}},
        {"id": "G010-B1", "kind": "boundary", "input": {"target_model_code": "G008", "base_arguments": _AFFINE_BASE, "output_path": "interpolated_value", "uncertain_parameters": _UNIFORM_X, "correlation_matrix": [[1]], "random_seed": 1, "sample_count": 10, "failure_operator": "greater_than", "failure_threshold": 2}},
        {"id": "G010-F1", "kind": "failure", "input": {"target_model_code": "G008", "base_arguments": {"table_id": "bad-correlation", "table_version": "1", "dimension": "two_dimensional", "x_axis": [0, 1], "x_unit": "1", "y_axis": [0, 1], "y_unit": "1", "values": [0, 1, 1, 2], "value_unit": "1", "query_x": 0.5, "query_y": 0.5, "method": "linear", "out_of_bounds_policy": "reject"}, "output_path": "interpolated_value", "uncertain_parameters": [{"path": "query_x", "label": "x", "unit": "1", "distribution": "uniform", "minimum": 0, "maximum": 1}, {"path": "query_y", "label": "y", "unit": "1", "distribution": "uniform", "minimum": 0, "maximum": 1}], "correlation_matrix": [[1, 2], [2, 1]], "random_seed": 1, "sample_count": 10, "failure_operator": "greater_than", "failure_threshold": 1}},
        {"id": "G010-F2", "kind": "failure", "input": {"target_model_code": "G008", "base_arguments": {"table_id": "sample-domain", "table_version": "1", "dimension": "one_dimensional", "x_axis": [0, 1], "x_unit": "1", "values": [0, 1], "value_unit": "1", "query_x": 0.5, "method": "linear", "out_of_bounds_policy": "reject"}, "output_path": "interpolated_value", "uncertain_parameters": [{"path": "query_x", "label": "x", "unit": "1", "distribution": "uniform", "minimum": -1, "maximum": 1}], "correlation_matrix": [[1]], "random_seed": 1, "sample_count": 10, "failure_operator": "greater_than", "failure_threshold": 0}},
    ]

    @staticmethod
    def _parse_parameters(raw: Any, base_arguments: dict[str, Any]) -> tuple[list[dict[str, Any]] | None, str | None]:
        if not isinstance(raw, list) or not 1 <= len(raw) <= 8:
            return None, "uncertain_parameters必须包含1到8项"
        common = {"path", "label", "unit", "distribution"}
        allowed = common | {"minimum", "maximum", "mean", "standard_deviation", "mode"}
        parsed: list[dict[str, Any]] = []
        seen: set[str] = set()
        for index, item in enumerate(raw):
            if not isinstance(item, dict) or not common <= set(item) or not set(item) <= allowed:
                return None, f"uncertain_parameters[{index}]字段不完整或含额外字段"
            path, error = nonempty_text(item.get("path"), f"uncertain_parameters[{index}].path")
            if error:
                return None, error
            if path in seen:
                return None, f"参数路径重复: {path}"
            label, error = nonempty_text(item.get("label"), f"uncertain_parameters[{index}].label")
            if error:
                return None, error
            unit, error = nonempty_text(item.get("unit"), f"uncertain_parameters[{index}].unit")
            if error:
                return None, error
            _, error = _read_path(base_arguments, path, f"uncertain_parameters[{index}].path")
            if error:
                return None, error
            distribution = item.get("distribution")
            values: dict[str, float] = {}
            if distribution == "uniform":
                expected = common | {"minimum", "maximum"}
                if set(item) != expected:
                    return None, f"uniform参数{path}必须且只能提供minimum和maximum"
                minimum, error = finite(item.get("minimum"), f"{path}.minimum")
                maximum, error2 = finite(item.get("maximum"), f"{path}.maximum")
                if error or error2 or maximum <= minimum:
                    return None, error or error2 or f"{path}.maximum必须大于minimum"
                values = {"minimum": minimum, "maximum": maximum}
            elif distribution == "normal":
                expected = common | {"mean", "standard_deviation"}
                if set(item) != expected:
                    return None, f"normal参数{path}必须且只能提供mean和standard_deviation"
                mean, error = finite(item.get("mean"), f"{path}.mean")
                sd, error2 = finite(item.get("standard_deviation"), f"{path}.standard_deviation", minimum=0, strict_minimum=True)
                if error or error2:
                    return None, error or error2
                values = {"mean": mean, "standard_deviation": sd}
            elif distribution == "triangular":
                expected = common | {"minimum", "maximum", "mode"}
                if set(item) != expected:
                    return None, f"triangular参数{path}必须且只能提供minimum、maximum和mode"
                minimum, error = finite(item.get("minimum"), f"{path}.minimum")
                maximum, error2 = finite(item.get("maximum"), f"{path}.maximum")
                mode, error3 = finite(item.get("mode"), f"{path}.mode")
                if error or error2 or error3 or maximum <= minimum or not minimum <= mode <= maximum:
                    return None, error or error2 or error3 or f"{path}须满足minimum<=mode<=maximum且minimum<maximum"
                values = {"minimum": minimum, "maximum": maximum, "mode": mode}
            else:
                return None, f"{path}.distribution不受支持"
            seen.add(path)
            parsed.append({"path": path, "label": label, "unit": unit, "distribution": distribution, **values})
        return parsed, None

    @staticmethod
    def _parse_correlation(raw: Any, size: int) -> tuple[np.ndarray | None, str | None]:
        if not isinstance(raw, list) or len(raw) != size or any(not isinstance(row, list) or len(row) != size for row in raw):
            return None, f"correlation_matrix必须为{size}x{size}矩阵"
        try:
            matrix = np.asarray(raw, dtype=float)
        except (TypeError, ValueError):
            return None, "correlation_matrix必须只含数值"
        if not np.all(np.isfinite(matrix)):
            return None, "correlation_matrix必须只含有限数值"
        if not np.allclose(matrix, matrix.T, rtol=0, atol=1e-12):
            return None, "correlation_matrix必须对称"
        if not np.allclose(np.diag(matrix), 1.0, rtol=0, atol=1e-12):
            return None, "correlation_matrix对角线必须为1"
        if np.any(np.abs(matrix) > 1 + 1e-12):
            return None, "correlation_matrix相关系数必须位于[-1,1]"
        try:
            np.linalg.cholesky(matrix)
        except np.linalg.LinAlgError:
            return None, "correlation_matrix必须正定"
        return matrix, None

    @staticmethod
    def _transform(latent: float, parameter: dict[str, Any]) -> float:
        probability = min(max(_normal_cdf(latent), 0.0), 1.0)
        if parameter["distribution"] == "uniform":
            return parameter["minimum"] + probability * (parameter["maximum"] - parameter["minimum"])
        if parameter["distribution"] == "normal":
            return parameter["mean"] + parameter["standard_deviation"] * latent
        minimum, maximum, mode = parameter["minimum"], parameter["maximum"], parameter["mode"]
        split = (mode - minimum) / (maximum - minimum)
        if probability <= split:
            return minimum + math.sqrt(probability * (maximum - minimum) * (mode - minimum))
        return maximum - math.sqrt((1 - probability) * (maximum - minimum) * (maximum - mode))

    def invoke(self, params, context=None):
        errors = self.validate_input(params)
        if errors:
            return fail("；".join(errors))
        base_arguments = params.get("base_arguments")
        if not isinstance(base_arguments, dict) or not base_arguments:
            return fail("base_arguments必须是非空对象")
        output_path, error = nonempty_text(params.get("output_path"), "output_path")
        if error:
            return fail(error)
        target, target_code, error = _registered_target(params.get("target_model_code"))
        if error:
            return fail(error, "UNKNOWN_MODEL" if target_code == "UNKNOWN" else "MODEL_NOT_APPLICABLE")
        uncertain, error = self._parse_parameters(params.get("uncertain_parameters"), base_arguments)
        if error:
            return fail(error)
        correlation, error = self._parse_correlation(params.get("correlation_matrix"), len(uncertain))
        if error:
            return fail(error)
        seed_raw = params.get("random_seed")
        sample_raw = params.get("sample_count")
        if isinstance(seed_raw, float) and seed_raw.is_integer():
            seed_raw = int(seed_raw)
        if isinstance(sample_raw, float) and sample_raw.is_integer():
            sample_raw = int(sample_raw)
        seed, error = integer(seed_raw, "random_seed", 0, 2147483647)
        if error:
            return fail(error, "OUT_OF_DOMAIN")
        sample_count, error = integer(sample_raw, "sample_count", 10, 2000)
        if error:
            return fail(error, "OUT_OF_DOMAIN")
        threshold, error = finite(params.get("failure_threshold"), "failure_threshold")
        if error:
            return fail(error)
        operator = params.get("failure_operator")
        allow_warnings = params.get("allow_target_boundary_warnings", False)
        lower = np.linalg.cholesky(correlation)
        rng = random.Random(seed)
        standard_normal = NormalDist()
        parameter_samples = [[] for _ in uncertain]
        outputs: list[float] = []
        total_warnings = 0
        for sample_index in range(sample_count):
            independent = np.asarray([
                standard_normal.inv_cdf(min(max(rng.random(), 1e-15), 1 - 1e-15))
                for _ in uncertain
            ], dtype=float)
            latent = lower @ independent
            sampled_arguments = copy.deepcopy(base_arguments)
            for index, parameter in enumerate(uncertain):
                sampled_value = self._transform(float(latent[index]), parameter)
                write_error = _write_numeric_path(sampled_arguments, parameter["path"], sampled_value, "uncertain_parameter_path")
                if write_error:
                    return fail(write_error)
                parameter_samples[index].append(sampled_value)
            output, warning_count, error = _invoke_target_scalar(target, sampled_arguments, output_path, allow_warnings)
            total_warnings += warning_count
            if error:
                return fail(f"第{sample_index + 1}个样本失败: {error}", "MODEL_NOT_APPLICABLE")
            outputs.append(output)
        if not outputs or not all(math.isfinite(value) for value in outputs):
            return fail("蒙特卡洛输出为空或包含非有限值", "NUMERICAL_ERROR")
        sorted_outputs = sorted(outputs)
        mean_output = math.fsum(outputs) / sample_count
        sample_variance = math.fsum((value - mean_output) ** 2 for value in outputs) / (sample_count - 1)
        sample_sd = math.sqrt(max(0.0, sample_variance))
        if len(uncertain) == 1:
            realized_correlation = [[1.0]]
        else:
            realized_array = np.corrcoef(np.asarray(parameter_samples, dtype=float))
            realized_correlation = [[float(value) for value in row] for row in realized_array]
        summaries = []
        for parameter, samples in zip(uncertain, parameter_samples):
            mean_value = math.fsum(samples) / sample_count
            variance = math.fsum((value - mean_value) ** 2 for value in samples) / (sample_count - 1)
            summaries.append({
                "path": parameter["path"], "label": parameter["label"], "unit": parameter["unit"],
                "distribution": parameter["distribution"], "sample_mean": mean_value,
                "sample_standard_deviation": math.sqrt(max(0.0, variance)),
                "sample_minimum": min(samples), "sample_maximum": max(samples),
            })
        if operator == "greater_than":
            failure_count = sum(value > threshold for value in outputs)
        else:
            failure_count = sum(value < threshold for value in outputs)
        probability = failure_count / sample_count
        z = 1.959963984540054
        denominator = 1 + z * z / sample_count
        centre = (probability + z * z / (2 * sample_count)) / denominator
        half_width = z * math.sqrt(probability * (1 - probability) / sample_count + z * z / (4 * sample_count * sample_count)) / denominator
        warnings: list[BoundaryWarning] = []
        if sample_count < 100:
            warnings.append(BoundaryWarning("sample_count", "样本数小于100，仅适合执行链与边界验证，不宜解释尾部概率"))
        if total_warnings:
            warnings.append(BoundaryWarning("target", f"目标工具累计返回{total_warnings}条已允许的适用域警告"))
        return ModelResult(True, result={
            "target_model_code": target.model_id,
            "target_tool_name": target.tool_name,
            "target_tool_uid": target.tool_uid,
            "target_model_version": target.version,
            "output_path": output_path,
            "output_unit": _target_output_unit(target, output_path),
            "sample_count": sample_count,
            "evaluation_count": sample_count,
            "random_seed": seed,
            "parameter_sample_summaries": summaries,
            "realized_correlation_matrix": realized_correlation,
            "output_statistics": {
                "mean": mean_output, "sample_standard_deviation": sample_sd,
                "standard_error_of_mean": sample_sd / math.sqrt(sample_count),
                "minimum": sorted_outputs[0], "maximum": sorted_outputs[-1],
                "p05": _quantile_type7(sorted_outputs, 0.05),
                "p50": _quantile_type7(sorted_outputs, 0.50),
                "p95": _quantile_type7(sorted_outputs, 0.95),
            },
            "failure_operator": operator,
            "failure_threshold": threshold,
            "failure_count": failure_count,
            "estimated_failure_probability": probability,
            "failure_probability_wilson_95": [max(0.0, centre - half_width), min(1.0, centre + half_width)],
            "target_boundary_warning_count": total_warnings,
            "quantile_method": "Hyndman-Fan type 7 linear interpolation",
            "calculation_method": "fixed-seed Gaussian-copula sampling + safe qualified registered-tool execution",
        }, boundary_check=boundary_result(warnings))


class G008_RegularGridLookup(W17FormulaTool):
    model_id, name, version = "G008", "一二维规则网格插值与查表", "1.0.0"
    tool_name = "metallurgy_interpolate_lookup_table"
    scenario = "数值仿真与工具编排"
    model_type = "确定性规则网格线性/最近邻插值"
    description = "对调用方显式提交并带ID、版本和单位的一维或二维规则网格执行线性、双线性或最近邻查表。"
    applicable_boundary = (
        "严格递增的一维或二维直角规则网格，单轴2到200点；支持reject或clamp边界策略。"
        "不连接企业实时表，不处理散点、高维、样条或隐式外推。"
    )
    data_source = ["SciPy RegularGridInterpolator semantics", "piecewise linear and bilinear interpolation"]
    source_version = "explicit-regular-grid-lookup-v1"
    formula_reference = (
        "1D: f=(1-w)f_i+w f_(i+1); 2D: bilinear tensor-product corner weights; "
        "nearest ties select the lower grid index"
    )
    source_records = [
        {
            "source_id": "SCIPY-REGULAR-GRID-1.18",
            "name": "scipy.interpolate.RegularGridInterpolator semantics",
            "version": "SciPy 1.18",
            "url": "https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.RegularGridInterpolator.html",
        },
        {
            "source_id": "EXPLICIT-BILINEAR-V1",
            "name": "Auditable one/two dimensional regular-grid interpolation",
            "version": "project-algorithm-v1",
        },
    ]
    failure_modes = [
        "表ID、版本或单位为空，轴非严格递增或包含非有限值",
        "扁平值数组长度与一维/二维网格形状不一致",
        "二维查询缺少y轴或query_y，一维查询提交多余二维字段",
        "reject策略下查询点超出网格域",
        "把直角网格插值结果解释为散点拟合、外部数据库查询或现场实时数据",
    ]
    independent_validation = [
        "一维线性插值精确再现仿射函数",
        "二维双线性角点权重和为1并精确再现双仿射函数",
        "查询落在网格点时精确返回原表值",
        "最近邻中点固定选择低索引且clamp结果位于域边界",
    ]
    dependencies = []
    relations = [
        rel("accepts_output_from", "A004", "A004可先把坐标和表值统一到调用方声明的轴与输出单位"),
        rel("target_of", "G009", "G008为G009提供可解析验证的确定性标量响应"),
        rel("target_of", "G010", "G008为G010提供版本化显式查表响应，不连接现场表"),
    ]
    input_fields = [
        InputField("table_id", "查找表ID", "string"),
        InputField("table_version", "查找表版本", "string"),
        InputField("dimension", "网格维数", "select", enum=["one_dimensional", "two_dimensional"]),
        InputField("x_axis", "X轴坐标", "array", unit="declared x_unit", items={"type": "number"}, min_items=2, max_items=200),
        InputField("x_unit", "X轴单位", "string"),
        InputField("y_axis", "Y轴坐标", "array", required=False, unit="declared y_unit", items={"type": "number"}, min_items=2, max_items=200),
        InputField("y_unit", "Y轴单位", "string", required=False),
        InputField("values", "按X优先、Y次序展平的表值", "array", unit="declared value_unit", items={"type": "number"}, min_items=2, max_items=40000),
        InputField("value_unit", "输出值单位", "string"),
        InputField("query_x", "X查询坐标", "number", unit="declared x_unit"),
        InputField("query_y", "Y查询坐标", "number", required=False, unit="declared y_unit"),
        InputField("method", "插值方法", "select", default="linear", enum=["linear", "nearest"]),
        InputField("out_of_bounds_policy", "域外策略", "select", default="reject", enum=["reject", "clamp"]),
    ]
    output_fields = [
        OutputField("table_id", "查找表ID", "string"),
        OutputField("table_version", "查找表版本", "string"),
        OutputField("dimension", "网格维数", "string"),
        OutputField("method", "插值方法", "string"),
        OutputField("out_of_bounds_policy", "域外策略", "string"),
        OutputField("interpolated_value", "插值结果", "number", "declared value_unit"),
        OutputField("value_unit", "结果单位", "string"),
        OutputField("effective_query", "实际使用的查询坐标", "object", "declared axis units"),
        OutputField("clamped_axes", "发生夹持的轴", "array"),
        OutputField("exact_grid_point", "是否精确命中网格点", "boolean"),
        OutputField("corner_points", "参与插值的网格点与权重", "array", "weight:1"),
        OutputField("distance_outside_domain", "查询点超域距离", "object", "declared axis units"),
        OutputField("calculation_method", "计算方法", "string"),
    ]
    validation_rules = [
        {"rule": "strictly_increasing_finite_axes"},
        {"rule": "flat_values_shape_matches_axis_product"},
        {"rule": "explicit_table_identity_version_and_units"},
        {"rule": "reject_or_clamp_no_implicit_extrapolation"},
    ]
    qualification_cases = [
        {"id": "G008-N1", "kind": "normal", "input": {"table_id": "affine-1d", "table_version": "1", "dimension": "one_dimensional", "x_axis": [0, 1, 3], "x_unit": "s", "values": [1, 3, 7], "value_unit": "K", "query_x": 2, "method": "linear", "out_of_bounds_policy": "reject"}},
        {"id": "G008-N2", "kind": "normal", "input": {"table_id": "biaffine-2d", "table_version": "1", "dimension": "two_dimensional", "x_axis": [0, 1], "x_unit": "m", "y_axis": [0, 2], "y_unit": "s", "values": [0, 4, 1, 5], "value_unit": "Pa", "query_x": 0.25, "query_y": 0.5, "method": "linear", "out_of_bounds_policy": "reject"}},
        {"id": "G008-N3", "kind": "normal", "input": {"table_id": "nearest-1d", "table_version": "2026-09", "dimension": "one_dimensional", "x_axis": [0, 10, 20], "x_unit": "K", "values": [100, 200, 400], "value_unit": "J/mol", "query_x": 15, "method": "nearest", "out_of_bounds_policy": "reject"}},
        {"id": "G008-B1", "kind": "boundary", "input": {"table_id": "clamp", "table_version": "1", "dimension": "one_dimensional", "x_axis": [0, 1], "x_unit": "1", "values": [10, 20], "value_unit": "K", "query_x": -0.5, "method": "linear", "out_of_bounds_policy": "clamp"}},
        {"id": "G008-F1", "kind": "failure", "input": {"table_id": "reject", "table_version": "1", "dimension": "one_dimensional", "x_axis": [0, 1], "x_unit": "1", "values": [10, 20], "value_unit": "K", "query_x": 2, "method": "linear", "out_of_bounds_policy": "reject"}},
        {"id": "G008-F2", "kind": "failure", "input": {"table_id": "shape", "table_version": "1", "dimension": "two_dimensional", "x_axis": [0, 1], "x_unit": "1", "y_axis": [0, 1], "y_unit": "1", "values": [0, 1, 2], "value_unit": "1", "query_x": 0.5, "query_y": 0.5, "method": "linear", "out_of_bounds_policy": "reject"}},
    ]

    @staticmethod
    def _parse_axis(raw: Any, label: str) -> tuple[list[float] | None, str | None]:
        if not isinstance(raw, list) or not 2 <= len(raw) <= 200:
            return None, f"{label}必须包含2到200个坐标"
        axis: list[float] = []
        for index, item in enumerate(raw):
            value, error = finite(item, f"{label}[{index}]")
            if error:
                return None, error
            if axis and value <= axis[-1]:
                return None, f"{label}必须严格递增"
            axis.append(value)
        return axis, None

    @staticmethod
    def _bracket(axis: list[float], query: float) -> tuple[int, int, float]:
        upper = bisect.bisect_left(axis, query)
        if upper == 0:
            return 0, 0, 0.0
        if upper == len(axis):
            return len(axis) - 1, len(axis) - 1, 0.0
        if axis[upper] == query:
            return upper, upper, 0.0
        lower = upper - 1
        weight = (query - axis[lower]) / (axis[upper] - axis[lower])
        return lower, upper, weight

    @staticmethod
    def _effective_query(query: float, axis: list[float], axis_name: str, policy: str) -> tuple[float | None, float, bool, str | None]:
        if query < axis[0]:
            distance = axis[0] - query
            if policy == "reject":
                return None, distance, False, f"query_{axis_name}低于{axis_name}_axis下限"
            return axis[0], distance, True, None
        if query > axis[-1]:
            distance = query - axis[-1]
            if policy == "reject":
                return None, distance, False, f"query_{axis_name}高于{axis_name}_axis上限"
            return axis[-1], distance, True, None
        return query, 0.0, False, None

    def invoke(self, params, context=None):
        errors = self.validate_input(params)
        if errors:
            return fail("；".join(errors))
        table_id, error = nonempty_text(params.get("table_id"), "table_id")
        if error:
            return fail(error)
        table_version, error = nonempty_text(params.get("table_version"), "table_version")
        if error:
            return fail(error)
        x_unit, error = nonempty_text(params.get("x_unit"), "x_unit")
        if error:
            return fail(error)
        value_unit, error = nonempty_text(params.get("value_unit"), "value_unit")
        if error:
            return fail(error)
        dimension = params.get("dimension")
        method = params.get("method", "linear")
        policy = params.get("out_of_bounds_policy", "reject")
        x_axis, error = self._parse_axis(params.get("x_axis"), "x_axis")
        if error:
            return fail(error)
        query_x, error = finite(params.get("query_x"), "query_x")
        if error:
            return fail(error)
        y_axis = None
        query_y = None
        y_unit = None
        if dimension == "two_dimensional":
            y_axis, error = self._parse_axis(params.get("y_axis"), "y_axis")
            if error:
                return fail(error)
            y_unit, error = nonempty_text(params.get("y_unit"), "y_unit")
            if error:
                return fail(error)
            query_y, error = finite(params.get("query_y"), "query_y")
            if error:
                return fail(error)
        elif "y_axis" in params or "y_unit" in params or "query_y" in params:
            return fail("one_dimensional模式不得提交y_axis、y_unit或query_y")

        raw_values = params.get("values")
        expected = len(x_axis) if dimension == "one_dimensional" else len(x_axis) * len(y_axis)
        if not isinstance(raw_values, list) or len(raw_values) != expected:
            return fail(f"values长度必须为{expected}，收到{len(raw_values) if isinstance(raw_values, list) else '非数组'}")
        values: list[float] = []
        for index, item in enumerate(raw_values):
            value, error = finite(item, f"values[{index}]")
            if error:
                return fail(error)
            values.append(value)

        effective_x, distance_x, clamped_x, error = self._effective_query(query_x, x_axis, "x", policy)
        if error:
            return fail(error, "OUT_OF_DOMAIN")
        clamped_axes = ["x"] if clamped_x else []
        distance = {"x": distance_x}
        effective_query = {"x": effective_x}
        corners: list[dict[str, Any]] = []

        x0, x1, wx = self._bracket(x_axis, effective_x)
        if dimension == "one_dimensional":
            if method == "nearest":
                selected = x0 if x0 == x1 or abs(effective_x - x_axis[x0]) <= abs(x_axis[x1] - effective_x) else x1
                interpolated = values[selected]
                corners = [{"indices": [selected], "coordinates": [x_axis[selected]], "value": values[selected], "weight": 1.0}]
            elif x0 == x1:
                interpolated = values[x0]
                corners = [{"indices": [x0], "coordinates": [x_axis[x0]], "value": values[x0], "weight": 1.0}]
            else:
                interpolated = (1 - wx) * values[x0] + wx * values[x1]
                corners = [
                    {"indices": [x0], "coordinates": [x_axis[x0]], "value": values[x0], "weight": 1 - wx},
                    {"indices": [x1], "coordinates": [x_axis[x1]], "value": values[x1], "weight": wx},
                ]
            exact = effective_x in x_axis
        else:
            effective_y, distance_y, clamped_y, error = self._effective_query(query_y, y_axis, "y", policy)
            if error:
                return fail(error, "OUT_OF_DOMAIN")
            if clamped_y:
                clamped_axes.append("y")
            distance["y"] = distance_y
            effective_query["y"] = effective_y
            y0, y1, wy = self._bracket(y_axis, effective_y)

            def grid_value(ix: int, iy: int) -> float:
                return values[ix * len(y_axis) + iy]

            if method == "nearest":
                selected_x = x0 if x0 == x1 or abs(effective_x - x_axis[x0]) <= abs(x_axis[x1] - effective_x) else x1
                selected_y = y0 if y0 == y1 or abs(effective_y - y_axis[y0]) <= abs(y_axis[y1] - effective_y) else y1
                interpolated = grid_value(selected_x, selected_y)
                corners = [{"indices": [selected_x, selected_y], "coordinates": [x_axis[selected_x], y_axis[selected_y]], "value": interpolated, "weight": 1.0}]
            else:
                x_terms = [(x0, 1.0)] if x0 == x1 else [(x0, 1 - wx), (x1, wx)]
                y_terms = [(y0, 1.0)] if y0 == y1 else [(y0, 1 - wy), (y1, wy)]
                interpolated = 0.0
                for ix, x_weight in x_terms:
                    for iy, y_weight in y_terms:
                        weight = x_weight * y_weight
                        value = grid_value(ix, iy)
                        interpolated += weight * value
                        corners.append({"indices": [ix, iy], "coordinates": [x_axis[ix], y_axis[iy]], "value": value, "weight": weight})
            exact = effective_x in x_axis and effective_y in y_axis

        # Piecewise interpolation must preserve a constant table exactly, not
        # merely to floating-point accumulation tolerance.
        if min(values) == max(values):
            interpolated = values[0]
        if not math.isfinite(interpolated) or abs(math.fsum(item["weight"] for item in corners) - 1.0) > 1e-12:
            return fail("插值结果非有限或角点权重未闭合", "NUMERICAL_ERROR")
        warnings = [
            BoundaryWarning("query", f"查询点在{','.join(clamped_axes)}轴超域，已按clamp策略使用边界值")
        ] if clamped_axes else []
        return ModelResult(
            True,
            result={
                "table_id": table_id,
                "table_version": table_version,
                "dimension": dimension,
                "method": method,
                "out_of_bounds_policy": policy,
                "interpolated_value": float(interpolated),
                "value_unit": value_unit,
                "effective_query": effective_query,
                "clamped_axes": clamped_axes,
                "exact_grid_point": exact,
                "corner_points": corners,
                "distance_outside_domain": distance,
                "calculation_method": "piecewise linear/bilinear or deterministic nearest-neighbor regular-grid lookup",
            },
            boundary_check=boundary_result(warnings),
        )
