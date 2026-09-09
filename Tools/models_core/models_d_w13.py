"""P1-W13 additive BOF static optimization tools; existing tools stay frozen."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, linprog, milp

from .base import BaseModelTool, BoundaryCheck, BoundaryWarning, InputField, ModelResult, OutputField


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


def parse_nonnegative_mapping(value: Any, label: str, maximum: float | None = None) -> tuple[dict[str, float] | None, str | None]:
    if not isinstance(value, dict) or not value:
        return None, f"{label}必须是非空对象"
    parsed: dict[str, float] = {}
    for key, raw in value.items():
        if not isinstance(key, str) or not key.strip():
            return None, f"{label}键必须为非空字符串"
        number, error = finite(raw, f"{label}.{key}")
        if error or number < 0 or (maximum is not None and number > maximum):
            return None, error or f"{label}.{key}必须在0至{maximum if maximum is not None else '正无穷'}"
        parsed[key.strip()] = number
    if len(parsed) != len(value):
        return None, f"{label}键去空白后不得重复"
    return parsed, None


def solve_mixed_linear(
    cost: list[float],
    lower: list[float],
    upper: list[float],
    integrality: list[int],
    rows: list[list[float]],
    row_lower: list[float],
    row_upper: list[float],
):
    constraints = LinearConstraint(np.asarray(rows, dtype=float), np.asarray(row_lower), np.asarray(row_upper))
    return milp(
        c=np.asarray(cost, dtype=float),
        integrality=np.asarray(integrality, dtype=int),
        bounds=Bounds(np.asarray(lower, dtype=float), np.asarray(upper, dtype=float)),
        constraints=constraints,
        options={"presolve": True, "time_limit": 10.0, "mip_rel_gap": 1e-9},
    )


class W13BofTool(BaseModelTool):
    scenario = "转炉炼钢"
    priority = "P1"
    status = qualification_status = "qualified"
    count_eligible = True
    data_requirement = "FORMULA_ONLY"
    data_access_mode = "none"


_STAGE_SCHEMA = {
    "type": "object",
    "description": "一个离线供氧阶段；各数组元素按工艺先后顺序排列",
    "properties": {
        "name": {"type": "string", "minLength": 1, "description": "阶段唯一名称，如early、middle、finish"},
        "oxygen_flow_nm3_min": {"type": "number", "exclusiveMinimum": 0, "description": "该阶段固定氧流量；单位: Nm3/min"},
        "duration_min_min": {"type": "number", "minimum": 0, "description": "该阶段允许的最短时长；单位: min"},
        "duration_max_min": {"type": "number", "exclusiveMinimum": 0, "description": "该阶段允许的最长时长；单位: min，必须大于最短时长"},
        "preferred_oxygen_fraction": {"type": "number", "minimum": 0, "maximum": 1, "description": "期望分配给该阶段的总氧量比例；单位: 1，所有阶段合计为1"},
        "deviation_weight": {"type": "number", "exclusiveMinimum": 0, "description": "偏离期望氧量的目标函数权重；单位: 1"},
        "lance_height_m": {"type": "number", "exclusiveMinimum": 0, "description": "该阶段固定枪位；单位: m"},
        "oxygen_utilization_fraction": {"type": "number", "minimum": 0, "maximum": 1, "description": "该阶段氧利用率；单位: 1"},
    },
    "required": [
        "name", "oxygen_flow_nm3_min", "duration_min_min", "duration_max_min",
        "preferred_oxygen_fraction", "deviation_weight", "lance_height_m",
        "oxygen_utilization_fraction",
    ],
    "additionalProperties": False,
}


class D018_BofBlowingScheduleOptimization(W13BofTool):
    model_id, name, version = "D018", "BOF静态分段供氧制度优化", "1.0.0"
    tool_name = "metallurgy_optimize_bof_blowing_schedule"
    description = (
        "在调用方给定总氧量、分段固定流量、时长边界、期望氧量占比和枪位下，"
        "用线性规划生成离线分段供氧制度；不读取炉气/喷溅信号，不下发设备。"
    )
    model_type = "领域约束线性规划"
    applicable_boundary = (
        "2至12个静态阶段；流量和枪位是调用方审核后的固定设定，优化变量是各段氧量/时长。"
        "只保证总氧量、时长容量和期望曲线偏差最小，不预测终点C/T/P或在线控制。"
    )
    data_source = ["Dantzig linear programming", "SciPy HiGHS linprog 1.18.1"]
    source_version = "bof-static-stage-l1-lp-v1; scipy-1.18.1"
    formula_reference = (
        "min sum_i w_i*d_i; |V_i-f_i*V_total|<=d_i; "
        "sum_i V_i=V_total; flow_i*tmin_i<=V_i<=flow_i*tmax_i"
    )
    source_records = [
        {
            "source_id": "SCIPY-LINPROG-1.18.1",
            "name": "SciPy linprog/HiGHS linear programming",
            "version": "1.18.1",
            "url": "https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.linprog.html",
        }
    ]
    failure_modes = [
        "阶段少于2或多于12、阶段名重复或字段不完整",
        "流量/时长/枪位/权重非正，利用率或期望占比越界",
        "期望占比不闭合为1",
        "总氧量低于全部阶段最小容量或高于最大容量",
        "HiGHS未得到最优解或氧量/时长闭合超差",
    ]
    independent_validation = [
        "总氧量等式和逐段duration=volume/flow独立复算",
        "期望曲线本身可行时目标值必须为零",
        "总氧量等于容量边界时解析解为逐段相应边界",
        "阶段顺序置换不改变按名称映射后的解和目标值",
    ]
    dependencies = ["D001", "D007", "D016"]
    relations = [
        rel("consumes_output_from", "D001", "D001理论耗氧可作为D018的total_oxygen_nm3"),
        rel("consumes_output_from", "D007", "D007分段脱碳结果可用于构造期望氧量占比，但D018不重算动力学"),
        rel("consumes_output_from", "D016", "D016氧利用率可作为阶段利用率审查依据"),
        rel("complements", "D002", "D002做静态热平衡；D018只分配供氧制度并返回离线时序"),
    ]
    input_fields = [
        InputField("total_oxygen_nm3", "总供氧量", "number", unit="Nm3", min_value=1e-12),
        InputField("stages", "分段制度", "array", items=_STAGE_SCHEMA, min_items=2, max_items=12),
    ]
    output_fields = [
        OutputField("stages", "优化后的分段制度", "array"),
        OutputField("total_oxygen_nm3", "总供氧量", "number", "Nm3"),
        OutputField("total_duration_min", "总吹炼时间", "number", "min"),
        OutputField("useful_oxygen_nm3", "预计有用氧量", "number", "Nm3"),
        OutputField("oxygen_loss_nm3", "预计损失氧量", "number", "Nm3"),
        OutputField("weighted_l1_deviation_nm3", "加权期望曲线偏差", "number", "Nm3"),
        OutputField("oxygen_closure_residual_nm3", "氧量闭合残差", "number", "Nm3"),
        OutputField("max_duration_bound_violation_min", "最大时长边界违反", "number", "min"),
        OutputField("solver", "求解器", "string"),
        OutputField("solver_status", "求解状态", "string"),
        OutputField("algorithm_version", "算法版本", "string"),
    ]
    validation_rules = [
        {"rule": "two_to_twelve_unique_strict_stage_objects"},
        {"rule": "positive_flow_duration_lance_weight_and_fraction_bounds"},
        {"rule": "preferred_fractions_sum_to_one_and_total_within_capacity"},
    ]
    qualification_cases = [
        {"id": "D018-N1", "kind": "normal", "input": {"total_oxygen_nm3": 120, "stages": [
            {"name": "early", "oxygen_flow_nm3_min": 30, "duration_min_min": 1, "duration_max_min": 3, "preferred_oxygen_fraction": 0.5, "deviation_weight": 1, "lance_height_m": 1.8, "oxygen_utilization_fraction": 0.82},
            {"name": "middle", "oxygen_flow_nm3_min": 20, "duration_min_min": 1, "duration_max_min": 3, "preferred_oxygen_fraction": 0.3, "deviation_weight": 1, "lance_height_m": 1.5, "oxygen_utilization_fraction": 0.9},
            {"name": "finish", "oxygen_flow_nm3_min": 15, "duration_min_min": 1, "duration_max_min": 3, "preferred_oxygen_fraction": 0.2, "deviation_weight": 2, "lance_height_m": 1.3, "oxygen_utilization_fraction": 0.94},
        ]}},
        {"id": "D018-N2", "kind": "normal", "input": {"total_oxygen_nm3": 100, "stages": [
            {"name": "main", "oxygen_flow_nm3_min": 20, "duration_min_min": 2, "duration_max_min": 4, "preferred_oxygen_fraction": 0.7, "deviation_weight": 1, "lance_height_m": 1.7, "oxygen_utilization_fraction": 0.88},
            {"name": "trim", "oxygen_flow_nm3_min": 10, "duration_min_min": 2, "duration_max_min": 5, "preferred_oxygen_fraction": 0.3, "deviation_weight": 1, "lance_height_m": 1.2, "oxygen_utilization_fraction": 0.95},
        ]}},
        {"id": "D018-N3", "kind": "normal", "input": {"total_oxygen_nm3": 90, "stages": [
            {"name": "s1", "oxygen_flow_nm3_min": 15, "duration_min_min": 1, "duration_max_min": 3, "preferred_oxygen_fraction": 0.3333333333333333, "deviation_weight": 1, "lance_height_m": 1.8, "oxygen_utilization_fraction": 0.8},
            {"name": "s2", "oxygen_flow_nm3_min": 15, "duration_min_min": 1, "duration_max_min": 3, "preferred_oxygen_fraction": 0.3333333333333333, "deviation_weight": 1, "lance_height_m": 1.5, "oxygen_utilization_fraction": 0.9},
            {"name": "s3", "oxygen_flow_nm3_min": 15, "duration_min_min": 1, "duration_max_min": 3, "preferred_oxygen_fraction": 0.3333333333333334, "deviation_weight": 1, "lance_height_m": 1.2, "oxygen_utilization_fraction": 0.95},
        ]}},
        {"id": "D018-B1", "kind": "boundary", "input": {"total_oxygen_nm3": 50, "stages": [
            {"name": "a", "oxygen_flow_nm3_min": 30, "duration_min_min": 1, "duration_max_min": 2, "preferred_oxygen_fraction": 0.6, "deviation_weight": 1, "lance_height_m": 1.5, "oxygen_utilization_fraction": 0.9},
            {"name": "b", "oxygen_flow_nm3_min": 20, "duration_min_min": 1, "duration_max_min": 2, "preferred_oxygen_fraction": 0.4, "deviation_weight": 1, "lance_height_m": 1.2, "oxygen_utilization_fraction": 0.95},
        ]}},
        {"id": "D018-F1", "kind": "failure", "input": {"total_oxygen_nm3": 10, "stages": [
            {"name": "a", "oxygen_flow_nm3_min": 30, "duration_min_min": 1, "duration_max_min": 2, "preferred_oxygen_fraction": 0.5, "deviation_weight": 1, "lance_height_m": 1.5, "oxygen_utilization_fraction": 0.9},
            {"name": "b", "oxygen_flow_nm3_min": 20, "duration_min_min": 1, "duration_max_min": 2, "preferred_oxygen_fraction": 0.5, "deviation_weight": 1, "lance_height_m": 1.2, "oxygen_utilization_fraction": 0.95},
        ]}},
        {"id": "D018-F2", "kind": "failure", "input": {"total_oxygen_nm3": 60, "stages": [
            {"name": "same", "oxygen_flow_nm3_min": 20, "duration_min_min": 1, "duration_max_min": 2, "preferred_oxygen_fraction": 0.5, "deviation_weight": 1, "lance_height_m": 1.5, "oxygen_utilization_fraction": 0.9},
            {"name": "same", "oxygen_flow_nm3_min": 20, "duration_min_min": 1, "duration_max_min": 2, "preferred_oxygen_fraction": 0.5, "deviation_weight": 1, "lance_height_m": 1.2, "oxygen_utilization_fraction": 0.95},
        ]}},
    ]

    def invoke(self, params: dict, context=None) -> ModelResult:
        errors = self.validate_input(params)
        if errors:
            return fail("；".join(errors))
        total, error = finite(params.get("total_oxygen_nm3"), "total_oxygen_nm3")
        if error or total <= 0:
            return fail(error or "total_oxygen_nm3必须大于0")
        raw_stages = params.get("stages")
        if not isinstance(raw_stages, list) or not 2 <= len(raw_stages) <= 12:
            return fail("stages必须含2至12项")
        stages = []
        names = set()
        required = {
            "name", "oxygen_flow_nm3_min", "duration_min_min", "duration_max_min",
            "preferred_oxygen_fraction", "deviation_weight", "lance_height_m",
            "oxygen_utilization_fraction",
        }
        for index, raw in enumerate(raw_stages):
            problem = strict_object(raw, required, set(), f"stages[{index}]")
            if problem:
                return fail(problem)
            name = raw["name"]
            if not isinstance(name, str) or not name.strip() or name.strip() in names:
                return fail("阶段名必须为唯一非空字符串")
            name = name.strip(); names.add(name)
            parsed = {"name": name}
            for field in required - {"name"}:
                value, problem = finite(raw[field], f"stages[{index}].{field}")
                if problem:
                    return fail(problem)
                parsed[field] = value
            if parsed["oxygen_flow_nm3_min"] <= 0 or parsed["duration_min_min"] < 0 \
                    or parsed["duration_max_min"] <= parsed["duration_min_min"]:
                return fail("阶段流量必须为正且0≤最短时长<最长时长")
            if parsed["deviation_weight"] <= 0 or parsed["lance_height_m"] <= 0:
                return fail("阶段偏差权重和枪位必须大于0")
            if not 0 <= parsed["preferred_oxygen_fraction"] <= 1 \
                    or not 0 <= parsed["oxygen_utilization_fraction"] <= 1:
                return fail("阶段期望占比和氧利用率必须在0至1")
            stages.append(parsed)
        fraction_sum = sum(stage["preferred_oxygen_fraction"] for stage in stages)
        if abs(fraction_sum - 1.0) > 1e-9:
            return fail("阶段preferred_oxygen_fraction合计必须为1", "MASS_BALANCE_VIOLATION")
        lower = [stage["oxygen_flow_nm3_min"] * stage["duration_min_min"] for stage in stages]
        upper = [stage["oxygen_flow_nm3_min"] * stage["duration_max_min"] for stage in stages]
        if total < sum(lower) - 1e-9 or total > sum(upper) + 1e-9:
            return fail("总氧量不在阶段容量可行区间", "MODEL_NOT_APPLICABLE")
        count = len(stages)
        targets = [stage["preferred_oxygen_fraction"] * total for stage in stages]
        c = [0.0] * count + [stage["deviation_weight"] for stage in stages]
        a_ub, b_ub = [], []
        for index, target in enumerate(targets):
            positive = [0.0] * (2 * count); positive[index] = 1.0; positive[count + index] = -1.0
            negative = [0.0] * (2 * count); negative[index] = -1.0; negative[count + index] = -1.0
            a_ub.extend([positive, negative]); b_ub.extend([target, -target])
        solution = linprog(
            c=np.asarray(c), A_ub=np.asarray(a_ub), b_ub=np.asarray(b_ub),
            A_eq=np.asarray([[1.0] * count + [0.0] * count]), b_eq=np.asarray([total]),
            bounds=[*zip(lower, upper), *[(0.0, None)] * count], method="highs",
            options={"presolve": True},
        )
        if not solution.success:
            code = "MODEL_NOT_APPLICABLE" if solution.status in {2, 3} else "NUMERICAL_ERROR"
            return fail(f"供氧制度优化失败: {solution.message}", code)
        volumes = np.asarray(solution.x[:count], dtype=float)
        closure = float(volumes.sum() - total)
        output_stages = []
        clock = 0.0
        max_duration_violation = 0.0
        useful_total = 0.0
        warnings_out: list[BoundaryWarning] = []
        for index, (stage, volume) in enumerate(zip(stages, volumes)):
            duration = float(volume / stage["oxygen_flow_nm3_min"])
            max_duration_violation = max(
                max_duration_violation,
                max(0.0, stage["duration_min_min"] - duration, duration - stage["duration_max_min"]),
            )
            useful = float(volume * stage["oxygen_utilization_fraction"])
            useful_total += useful
            if abs(volume - lower[index]) <= 1e-8 or abs(volume - upper[index]) <= 1e-8:
                warnings_out.append(BoundaryWarning(
                    f"stages[{index}]", f"阶段{stage['name']}氧量位于时长容量边界",
                    min_allowed=lower[index], max_allowed=upper[index],
                ))
            output_stages.append({
                "name": stage["name"], "start_min": clock, "end_min": clock + duration,
                "duration_min": duration, "oxygen_volume_nm3": float(volume),
                "oxygen_fraction": float(volume / total),
                "oxygen_flow_nm3_min": stage["oxygen_flow_nm3_min"],
                "lance_height_m": stage["lance_height_m"],
                "oxygen_utilization_fraction": stage["oxygen_utilization_fraction"],
                "useful_oxygen_nm3": useful, "oxygen_loss_nm3": float(volume - useful),
                "preferred_oxygen_fraction": stage["preferred_oxygen_fraction"],
                "absolute_target_deviation_nm3": abs(float(volume) - targets[index]),
            })
            clock += duration
        if abs(closure) > 1e-7 or max_duration_violation > 1e-8:
            return fail("优化结果未通过氧量或时长闭合校验", "NUMERICAL_ERROR")
        return ModelResult(True, result={
            "stages": output_stages,
            "total_oxygen_nm3": total,
            "total_duration_min": clock,
            "useful_oxygen_nm3": useful_total,
            "oxygen_loss_nm3": total - useful_total,
            "weighted_l1_deviation_nm3": float(solution.fun),
            "oxygen_closure_residual_nm3": closure,
            "max_duration_bound_violation_min": max_duration_violation,
            "solver": "scipy-linprog-highs-1.18.1",
            "solver_status": str(solution.message),
            "algorithm_version": "d018-static-stage-l1-lp-v1",
        }, boundary_check=BoundaryCheck(not warnings_out, warnings_out))


_TARGET_SCHEMA = {
    "type": "object",
    "description": "一个目标元素的最终成分允许区间",
    "properties": {
        "element": {"type": "string", "minLength": 1, "description": "目标元素符号，须与成分映射中的键一致，如Mn"},
        "min_wt_pct": {"type": "number", "minimum": 0, "maximum": 100, "description": "目标成分下限；单位: wt%"},
        "max_wt_pct": {"type": "number", "minimum": 0, "maximum": 100, "description": "目标成分上限；单位: wt%"},
    },
    "required": ["element", "min_wt_pct", "max_wt_pct"],
    "additionalProperties": False,
}
_ALLOY_SCHEMA = {
    "type": "object",
    "description": "一种候选合金及其成本、加入边界、成分和收得率",
    "properties": {
        "name": {"type": "string", "minLength": 1, "description": "候选合金唯一名称"},
        "cost_per_kg": {"type": "number", "minimum": 0, "description": "每千克成本；币种由调用方统一"},
        "min_addition_kg": {"type": "number", "minimum": 0, "description": "最小允许加入量；单位: kg"},
        "max_addition_kg": {"type": "number", "minimum": 0, "description": "最大允许加入量；单位: kg"},
        "composition_wt_pct": {
            "type": "object", "minProperties": 1,
            "propertyNames": {"type": "string", "minLength": 1},
            "additionalProperties": {"type": "number", "minimum": 0, "maximum": 100},
            "description": "元素到该合金中质量百分数的映射；单位: wt%，如{Mn:80}",
        },
        "element_recovery_fractions": {
            "type": "object", "minProperties": 1,
            "propertyNames": {"type": "string", "minLength": 1},
            "additionalProperties": {"type": "number", "minimum": 0, "maximum": 1},
            "description": "元素到收得率的映射；单位: 1，如{Mn:0.9}",
        },
        "mass_retention_fraction": {"type": "number", "minimum": 0, "maximum": 1, "description": "加入质量保留在钢液中的比例；单位: 1"},
        "batch_size_kg": {"type": "number", "exclusiveMinimum": 0, "description": "可选离散加料批量；单位: kg"},
    },
    "required": [
        "name", "cost_per_kg", "min_addition_kg", "max_addition_kg",
        "composition_wt_pct", "element_recovery_fractions", "mass_retention_fraction",
    ],
    "additionalProperties": False,
}


class D019_AlloyAdditionOptimization(W13BofTool):
    model_id, name, version = "D019", "多合金最小成本补加优化", "1.0.0"
    tool_name = "metallurgy_optimize_alloy_additions"
    description = (
        "在显式钢液成分、目标区间、合金成分/收得率/保留率/价格和批量约束下，"
        "用LP或MILP求最低成本多合金加入方案。"
    )
    model_type = "线性/混合整数配料优化"
    applicable_boundary = (
        "1至12个目标元素、1至30种合金；所有价格、成分、元素收得率和质量保留率由调用方显式提供。"
        "只做静态配料，不从历史炉次学习收得率，不考虑加入顺序动力学和二次氧化。"
    )
    data_source = ["linear element mass balance", "SciPy HiGHS milp 1.18.1"]
    source_version = "alloy-mass-balance-milp-v1; scipy-1.18.1"
    formula_reference = (
        "m_e,f=m0*w_e0+sum_j x_j*w_ej*r_ej; mf=m0+sum_j x_j*r_mj; "
        "target_min_e*mf<=m_e,f<=target_max_e*mf; min sum_j cost_j*x_j"
    )
    source_records = [{
        "source_id": "SCIPY-MILP-1.18.1", "name": "SciPy milp/HiGHS mixed-integer linear programming",
        "version": "1.18.1", "url": "https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.milp.html",
    }]
    failure_modes = [
        "目标元素、合金名重复或对象字段不完整",
        "当前/合金成分、收得率、保留率、成本、加入边界或批量非法",
        "目标上下限矛盾或当前成分缺少目标元素",
        "批量约束使加入上下界无整数可行点",
        "元素目标不可达、求解器未得最优解或元素质量重构超差",
    ]
    independent_validation = [
        "逐元素初始质量加回收加入量独立重构最终成分",
        "单合金连续问题与D023闭式加入量一致",
        "含批量时加入量必须为batch_size的整数倍",
        "合金输入顺序置换不改变按名称映射后的最优成本与方案",
    ]
    dependencies = ["A004", "D023"]
    relations = [
        rel("uses_convention_of", "A004", "A004可用于上游成分归一化；D019要求wt%基准闭合"),
        rel("generalizes", "D023", "D023是单元素单合金闭式原子工具；D019处理多元素、多合金、价格和批量约束"),
        rel("complements", "D022", "D022分解钢水收得率/铁损；D019消费调用方确认的合金质量保留率"),
    ]
    input_fields = [
        InputField("heat_mass_kg", "初始钢液质量", "number", unit="kg", min_value=1e-12),
        InputField(
            "current_composition_wt_pct", "当前钢液成分", "object", unit="wt%",
            description="元素到当前钢液质量百分数的非空映射，如{Mn:0.5}",
            json_schema={
                "minProperties": 1,
                "propertyNames": {"type": "string", "minLength": 1},
                "additionalProperties": {"type": "number", "minimum": 0, "maximum": 100},
            },
        ),
        InputField("targets", "目标元素区间", "array", items=_TARGET_SCHEMA, min_items=1, max_items=12),
        InputField("alloys", "候选合金", "array", items=_ALLOY_SCHEMA, min_items=1, max_items=30),
        InputField("max_total_addition_kg", "最大总加入量", "number", unit="kg", min_value=0),
    ]
    output_fields = [
        OutputField("additions", "各合金加入方案", "array"),
        OutputField("total_addition_kg", "总加入量", "number", "kg"),
        OutputField("retained_addition_kg", "留在钢液中的加入质量", "number", "kg"),
        OutputField("final_heat_mass_kg", "最终钢液质量", "number", "kg"),
        OutputField("final_composition_wt_pct", "最终目标元素成分", "object", "wt%"),
        OutputField("element_balances", "逐元素质量账与约束余量", "array"),
        OutputField("total_cost", "总成本", "number", "caller_currency"),
        OutputField("max_constraint_violation_wt_pct", "最大成分约束违反", "number", "wt%"),
        OutputField("integrality_used", "是否使用批量整数约束", "boolean"),
        OutputField("mip_gap", "MIP相对间隙", "number", "1", nullable=True),
        OutputField("objective_lower_bound", "目标函数下界", "number", "caller_currency", nullable=True),
        OutputField("solver", "求解器", "string"),
        OutputField("solver_status", "求解状态", "string"),
        OutputField("algorithm_version", "算法版本", "string"),
    ]
    validation_rules = [
        {"rule": "strict_unique_targets_and_alloys"},
        {"rule": "composition_recovery_retention_and_bounds_are_physical"},
        {"rule": "exact_linear_final_mass_composition_constraints_and_optional_batches"},
    ]
    qualification_cases = [
        {"id": "D019-N1", "kind": "normal", "input": {
            "heat_mass_kg": 1000, "current_composition_wt_pct": {"Mn": 0.5},
            "targets": [{"element": "Mn", "min_wt_pct": 1.0, "max_wt_pct": 1.1}],
            "alloys": [{"name": "FeMn80", "cost_per_kg": 2, "min_addition_kg": 0, "max_addition_kg": 20,
                        "composition_wt_pct": {"Mn": 80}, "element_recovery_fractions": {"Mn": 0.9},
                        "mass_retention_fraction": 1.0}], "max_total_addition_kg": 20,
        }},
        {"id": "D019-N2", "kind": "normal", "input": {
            "heat_mass_kg": 1000, "current_composition_wt_pct": {"Mn": 0.4, "C": 0.05},
            "targets": [{"element": "Mn", "min_wt_pct": 0.9, "max_wt_pct": 1.1}, {"element": "C", "min_wt_pct": 0.12, "max_wt_pct": 0.16}],
            "alloys": [
                {"name": "FeMn75", "cost_per_kg": 1.8, "min_addition_kg": 0, "max_addition_kg": 20, "composition_wt_pct": {"Mn": 75, "C": 6}, "element_recovery_fractions": {"Mn": 0.9, "C": 0.8}, "mass_retention_fraction": 0.98},
                {"name": "Carbon", "cost_per_kg": 1.0, "min_addition_kg": 0, "max_addition_kg": 5, "composition_wt_pct": {"C": 98}, "element_recovery_fractions": {"C": 0.75}, "mass_retention_fraction": 0.8},
            ], "max_total_addition_kg": 25,
        }},
        {"id": "D019-N3", "kind": "normal", "input": {
            "heat_mass_kg": 1000, "current_composition_wt_pct": {"Mn": 0.5},
            "targets": [{"element": "Mn", "min_wt_pct": 1.0, "max_wt_pct": 1.25}],
            "alloys": [{"name": "FeMnBatch", "cost_per_kg": 2, "min_addition_kg": 0, "max_addition_kg": 25,
                        "composition_wt_pct": {"Mn": 80}, "element_recovery_fractions": {"Mn": 0.9},
                        "mass_retention_fraction": 1.0, "batch_size_kg": 5}], "max_total_addition_kg": 25,
        }},
        {"id": "D019-B1", "kind": "boundary", "input": {
            "heat_mass_kg": 1000, "current_composition_wt_pct": {"Mn": 1.0},
            "targets": [{"element": "Mn", "min_wt_pct": 0.9, "max_wt_pct": 1.1}],
            "alloys": [{"name": "FeMn80", "cost_per_kg": 2, "min_addition_kg": 0, "max_addition_kg": 20,
                        "composition_wt_pct": {"Mn": 80}, "element_recovery_fractions": {"Mn": 0.9},
                        "mass_retention_fraction": 1.0}], "max_total_addition_kg": 20,
        }},
        {"id": "D019-F1", "kind": "failure", "input": {
            "heat_mass_kg": 1000, "current_composition_wt_pct": {"Mn": 0.1},
            "targets": [{"element": "Mn", "min_wt_pct": 2.0, "max_wt_pct": 2.1}],
            "alloys": [{"name": "FeMn80", "cost_per_kg": 2, "min_addition_kg": 0, "max_addition_kg": 1,
                        "composition_wt_pct": {"Mn": 80}, "element_recovery_fractions": {"Mn": 0.9},
                        "mass_retention_fraction": 1.0}], "max_total_addition_kg": 1,
        }},
        {"id": "D019-F2", "kind": "failure", "input": {
            "heat_mass_kg": 1000, "current_composition_wt_pct": {"Mn": 0.5},
            "targets": [{"element": "Mn", "min_wt_pct": 1.0, "max_wt_pct": 1.1}],
            "alloys": [
                {"name": "dup", "cost_per_kg": 2, "min_addition_kg": 0, "max_addition_kg": 20, "composition_wt_pct": {"Mn": 80}, "element_recovery_fractions": {"Mn": 0.9}, "mass_retention_fraction": 1.0},
                {"name": "dup", "cost_per_kg": 3, "min_addition_kg": 0, "max_addition_kg": 20, "composition_wt_pct": {"Mn": 70}, "element_recovery_fractions": {"Mn": 0.9}, "mass_retention_fraction": 1.0},
            ], "max_total_addition_kg": 20,
        }},
    ]

    def invoke(self, params: dict, context=None) -> ModelResult:
        errors = self.validate_input(params)
        if errors:
            return fail("；".join(errors))
        heat_mass, error = finite(params.get("heat_mass_kg"), "heat_mass_kg")
        max_total, error2 = finite(params.get("max_total_addition_kg"), "max_total_addition_kg")
        if error or heat_mass <= 0 or error2 or max_total < 0:
            return fail(error or error2 or "heat_mass_kg必须大于0且max_total_addition_kg不得为负")
        current, error = parse_nonnegative_mapping(params.get("current_composition_wt_pct"), "current_composition_wt_pct", 100)
        if error or sum(current.values()) > 100 + 1e-9:
            return fail(error or "当前成分合计不得超过100 wt%")
        raw_targets = params.get("targets")
        if not isinstance(raw_targets, list) or not 1 <= len(raw_targets) <= 12:
            return fail("targets必须含1至12项")
        targets = []
        elements = set()
        for index, raw in enumerate(raw_targets):
            problem = strict_object(raw, {"element", "min_wt_pct", "max_wt_pct"}, set(), f"targets[{index}]")
            if problem:
                return fail(problem)
            element = raw["element"]
            if not isinstance(element, str) or not element.strip() or element.strip() in elements:
                return fail("目标元素必须为唯一非空字符串")
            element = element.strip(); elements.add(element)
            lower, problem = finite(raw["min_wt_pct"], f"targets[{index}].min_wt_pct")
            upper, problem2 = finite(raw["max_wt_pct"], f"targets[{index}].max_wt_pct")
            if problem or problem2 or not 0 <= lower <= upper <= 100:
                return fail(problem or problem2 or "目标成分必须满足0≤min≤max≤100")
            if element not in current:
                return fail(f"当前成分缺少目标元素{element}")
            targets.append({"element": element, "min": lower / 100, "max": upper / 100})
        raw_alloys = params.get("alloys")
        if not isinstance(raw_alloys, list) or not 1 <= len(raw_alloys) <= 30:
            return fail("alloys必须含1至30项")
        alloys = []
        names = set()
        required = {"name", "cost_per_kg", "min_addition_kg", "max_addition_kg", "composition_wt_pct", "element_recovery_fractions", "mass_retention_fraction"}
        for index, raw in enumerate(raw_alloys):
            problem = strict_object(raw, required, {"batch_size_kg"}, f"alloys[{index}]")
            if problem:
                return fail(problem)
            name = raw["name"]
            if not isinstance(name, str) or not name.strip() or name.strip() in names:
                return fail("合金名必须为唯一非空字符串")
            name = name.strip(); names.add(name)
            cost, problem = finite(raw["cost_per_kg"], f"alloys[{index}].cost_per_kg")
            lower, problem2 = finite(raw["min_addition_kg"], f"alloys[{index}].min_addition_kg")
            upper, problem3 = finite(raw["max_addition_kg"], f"alloys[{index}].max_addition_kg")
            retention, problem4 = finite(raw["mass_retention_fraction"], f"alloys[{index}].mass_retention_fraction")
            if problem or problem2 or problem3 or problem4 or cost < 0 or lower < 0 or upper < lower or not 0 <= retention <= 1:
                return fail(problem or problem2 or problem3 or problem4 or "合金成本/边界/保留率非法")
            composition, problem = parse_nonnegative_mapping(raw["composition_wt_pct"], f"alloys[{index}].composition_wt_pct", 100)
            recovery, problem2 = parse_nonnegative_mapping(raw["element_recovery_fractions"], f"alloys[{index}].element_recovery_fractions", 1)
            if problem or problem2 or set(composition) != set(recovery) or sum(composition.values()) > 100 + 1e-9:
                return fail(problem or problem2 or "合金成分与收得率键必须一致且成分合计不超过100 wt%")
            recovered_fraction = sum(composition[element] / 100 * recovery[element] for element in composition)
            if retention + 1e-12 < recovered_fraction:
                return fail("mass_retention_fraction不得小于已声明回收元素的质量分数")
            batch = None
            if "batch_size_kg" in raw:
                batch, problem = finite(raw["batch_size_kg"], f"alloys[{index}].batch_size_kg")
                if problem or batch <= 0:
                    return fail(problem or "batch_size_kg必须大于0")
            scale = batch or 1.0
            lower_units = math.ceil(lower / scale - 1e-12) if batch else lower
            upper_units = math.floor(upper / scale + 1e-12) if batch else upper
            if lower_units > upper_units + 1e-12:
                return fail(f"合金{name}的批量约束与加入上下界无可行点", "MODEL_NOT_APPLICABLE")
            alloys.append({
                "name": name, "cost": cost, "lower": lower_units, "upper": upper_units,
                "scale": scale, "integer": batch is not None, "batch": batch,
                "composition": composition, "recovery": recovery, "retention": retention,
            })
        cost = [alloy["cost"] * alloy["scale"] for alloy in alloys]
        rows, row_lower, row_upper = [], [], []
        for target in targets:
            element = target["element"]
            initial_mass = heat_mass * current[element] / 100
            min_row, max_row = [], []
            for alloy in alloys:
                recovered = alloy["composition"].get(element, 0) / 100 * alloy["recovery"].get(element, 0)
                min_row.append(alloy["scale"] * (target["min"] * alloy["retention"] - recovered))
                max_row.append(alloy["scale"] * (recovered - target["max"] * alloy["retention"]))
            rows.extend([min_row, max_row])
            row_lower.extend([-np.inf, -np.inf])
            row_upper.extend([initial_mass - target["min"] * heat_mass, target["max"] * heat_mass - initial_mass])
        rows.append([alloy["scale"] for alloy in alloys]); row_lower.append(-np.inf); row_upper.append(max_total)
        solution = solve_mixed_linear(
            cost, [alloy["lower"] for alloy in alloys], [alloy["upper"] for alloy in alloys],
            [1 if alloy["integer"] else 0 for alloy in alloys], rows, row_lower, row_upper,
        )
        if not solution.success:
            code = "MODEL_NOT_APPLICABLE" if solution.status in {2, 3} else "NUMERICAL_ERROR"
            return fail(f"合金加入优化失败: {solution.message}", code)
        amounts = [max(0.0, float(value) * alloy["scale"]) for value, alloy in zip(solution.x, alloys)]
        total_addition = sum(amounts)
        retained_addition = sum(amount * alloy["retention"] for amount, alloy in zip(amounts, alloys))
        final_mass = heat_mass + retained_addition
        balances, final_composition = [], {}
        max_violation = 0.0
        for target in targets:
            element = target["element"]
            initial_mass = heat_mass * current[element] / 100
            added_mass = sum(
                amount * alloy["composition"].get(element, 0) / 100 * alloy["recovery"].get(element, 0)
                for amount, alloy in zip(amounts, alloys)
            )
            final_element_mass = initial_mass + added_mass
            final_wt = 100 * final_element_mass / final_mass
            min_wt, max_wt = 100 * target["min"], 100 * target["max"]
            violation = max(0.0, min_wt - final_wt, final_wt - max_wt)
            max_violation = max(max_violation, violation)
            final_composition[element] = final_wt
            balances.append({
                "element": element, "initial_mass_kg": initial_mass,
                "recovered_added_mass_kg": added_mass, "final_element_mass_kg": final_element_mass,
                "final_wt_pct": final_wt, "target_min_wt_pct": min_wt, "target_max_wt_pct": max_wt,
                "lower_margin_wt_pct": final_wt - min_wt, "upper_margin_wt_pct": max_wt - final_wt,
                "mass_reconstruction_residual_kg": final_element_mass - initial_mass - added_mass,
            })
        if total_addition > max_total + 1e-7 or max_violation > 1e-6:
            return fail("优化结果未通过加入量或成分约束复核", "NUMERICAL_ERROR")
        additions = [{
            "name": alloy["name"], "addition_kg": amount,
            "batch_size_kg": alloy["batch"],
            "batch_count": int(round(amount / alloy["batch"])) if alloy["batch"] else None,
            "cost_per_kg": alloy["cost"], "cost": amount * alloy["cost"],
            "mass_retention_fraction": alloy["retention"],
        } for amount, alloy in zip(amounts, alloys)]
        warnings_out = []
        if total_addition <= 1e-10:
            warnings_out.append(BoundaryWarning("alloys", "当前成分已满足目标，最优加入量为零"))
        mip_gap = getattr(solution, "mip_gap", None)
        dual_bound = getattr(solution, "mip_dual_bound", None)
        return ModelResult(True, result={
            "additions": additions,
            "total_addition_kg": total_addition,
            "retained_addition_kg": retained_addition,
            "final_heat_mass_kg": final_mass,
            "final_composition_wt_pct": final_composition,
            "element_balances": balances,
            "total_cost": float(solution.fun),
            "max_constraint_violation_wt_pct": max_violation,
            "integrality_used": any(alloy["integer"] for alloy in alloys),
            "mip_gap": float(mip_gap) if mip_gap is not None else None,
            "objective_lower_bound": float(dual_bound) if dual_bound is not None else None,
            "solver": "scipy-milp-highs-1.18.1",
            "solver_status": str(solution.message),
            "algorithm_version": "d019-final-mass-milp-v1",
        }, boundary_check=BoundaryCheck(not warnings_out, warnings_out))


_COOLANT_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "effective_cooling_mj_per_kg": {"type": "number", "exclusiveMinimum": 0},
        "cost_per_kg": {"type": "number", "minimum": 0},
        "min_addition_kg": {"type": "number", "minimum": 0},
        "max_addition_kg": {"type": "number", "minimum": 0},
        "batch_size_kg": {"type": "number", "exclusiveMinimum": 0},
    },
    "required": ["name", "effective_cooling_mj_per_kg", "cost_per_kg", "min_addition_kg", "max_addition_kg"],
    "additionalProperties": False,
}


class D020_CoolantScrapOptimization(W13BofTool):
    model_id, name, version = "D020", "冷却剂/废钢静态加入优化", "1.0.0"
    tool_name = "metallurgy_optimize_coolant_scrap_addition"
    description = (
        "把显式钢浴热状态和目标温区换算为冷却量区间，再以LP/MILP求最低成本冷却剂/废钢组合。"
        "材料有效冷却能力必须由调用方在同一热基准下提供。"
    )
    model_type = "热平衡约束线性/混合整数优化"
    applicable_boundary = (
        "1至20种正冷却能力材料；钢浴采用常数有效比热，材料冷却能力已包含其升温/熔化/反应净效应。"
        "不内置物性、不预测动态传热、不读取历史炉次或下发设备。"
    )
    data_source = ["Q=m*cp*DeltaT energy conservation", "SciPy HiGHS milp 1.18.1"]
    source_version = "coolant-static-heat-milp-v1; scipy-1.18.1"
    formula_reference = (
        "Q_min=m*cp*(T_current-T_target_max)/1000; "
        "Q_max=m*cp*(T_current-T_target_min)/1000; "
        "Q_min<=sum_j q_j*x_j<=Q_max; min sum_j cost_j*x_j"
    )
    source_records = [{
        "source_id": "SCIPY-MILP-1.18.1", "name": "SciPy milp/HiGHS mixed-integer linear programming",
        "version": "1.18.1", "url": "https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.milp.html",
    }]
    failure_modes = [
        "钢浴质量/比热/温度非有限或非正，目标温区顺序错误",
        "当前温度低于目标下限，正冷却材料无法完成任务",
        "材料名重复、冷却能力/成本/加入边界/批量非法",
        "目标冷却区间不可达或批量约束无可行解",
        "求解器未得最优解或能量/温度复核超差",
    ]
    independent_validation = [
        "Q=m*cp*DeltaT独立重构预测终温和热量闭合",
        "单一连续冷却剂解等于Q_min/q",
        "无批量时单位冷却成本更低材料优先的交换检验",
        "含批量时加入量为batch_size整数倍且MIP gap满足容差",
    ]
    dependencies = ["B003", "D002"]
    relations = [
        rel("consumes_output_from", "B003", "B003可提供材料显热分项，用于构造effective_cooling_mj_per_kg"),
        rel("consumes_output_from", "D002", "D002静态热平衡可提供待移除热量或验证D020预测终温"),
        rel("complements", "D005", "D005估算炉渣量；D020只优化冷却剂/废钢热负荷与成本"),
    ]
    input_fields = [
        InputField("bath_mass_kg", "钢浴质量", "number", unit="kg", min_value=1e-12),
        InputField("bath_specific_heat_kj_kg_k", "钢浴有效比热", "number", unit="kJ/(kg*K)", min_value=1e-12),
        InputField("current_temperature_k", "当前温度", "number", unit="K", min_value=1e-12),
        InputField("target_temperature_min_k", "目标温度下限", "number", unit="K", min_value=1e-12),
        InputField("target_temperature_max_k", "目标温度上限", "number", unit="K", min_value=1e-12),
        InputField("materials", "候选冷却材料", "array", items=_COOLANT_SCHEMA, min_items=1, max_items=20),
        InputField("max_total_addition_kg", "最大总加入量", "number", unit="kg", min_value=0),
    ]
    output_fields = [
        OutputField("additions", "材料加入方案", "array"),
        OutputField("total_addition_kg", "总加入量", "number", "kg"),
        OutputField("target_heat_removal_range_mj", "目标冷却量区间", "array", "MJ"),
        OutputField("achieved_heat_removal_mj", "实现冷却量", "number", "MJ"),
        OutputField("predicted_final_temperature_k", "预测终温", "number", "K"),
        OutputField("temperature_lower_margin_k", "距目标下限余量", "number", "K"),
        OutputField("temperature_upper_margin_k", "距目标上限余量", "number", "K"),
        OutputField("total_cost", "总成本", "number", "caller_currency"),
        OutputField("energy_closure_residual_mj", "能量闭合残差", "number", "MJ"),
        OutputField("integrality_used", "是否使用批量整数约束", "boolean"),
        OutputField("mip_gap", "MIP相对间隙", "number", "1", nullable=True),
        OutputField("objective_lower_bound", "目标函数下界", "number", "caller_currency", nullable=True),
        OutputField("solver", "求解器", "string"),
        OutputField("solver_status", "求解状态", "string"),
        OutputField("algorithm_version", "算法版本", "string"),
    ]
    validation_rules = [
        {"rule": "positive_bath_mass_heat_capacity_and_ordered_temperature_range"},
        {"rule": "strict_unique_materials_with_positive_effective_cooling"},
        {"rule": "energy_interval_and_total_addition_feasibility_with_optional_batches"},
    ]
    qualification_cases = [
        {"id": "D020-N1", "kind": "normal", "input": {
            "bath_mass_kg": 100000, "bath_specific_heat_kj_kg_k": 0.8, "current_temperature_k": 1900,
            "target_temperature_min_k": 1850, "target_temperature_max_k": 1870,
            "materials": [
                {"name": "scrap", "effective_cooling_mj_per_kg": 1.2, "cost_per_kg": 0.45, "min_addition_kg": 0, "max_addition_kg": 3000},
                {"name": "ore", "effective_cooling_mj_per_kg": 2.0, "cost_per_kg": 0.5, "min_addition_kg": 0, "max_addition_kg": 2000},
            ], "max_total_addition_kg": 5000,
        }},
        {"id": "D020-N2", "kind": "normal", "input": {
            "bath_mass_kg": 50000, "bath_specific_heat_kj_kg_k": 0.82, "current_temperature_k": 1880,
            "target_temperature_min_k": 1840, "target_temperature_max_k": 1860,
            "materials": [
                {"name": "scrap_batch", "effective_cooling_mj_per_kg": 1.1, "cost_per_kg": 0.4, "min_addition_kg": 0, "max_addition_kg": 2000, "batch_size_kg": 100},
                {"name": "pellet_batch", "effective_cooling_mj_per_kg": 1.8, "cost_per_kg": 0.7, "min_addition_kg": 0, "max_addition_kg": 1500, "batch_size_kg": 50},
            ], "max_total_addition_kg": 2500,
        }},
        {"id": "D020-N3", "kind": "normal", "input": {
            "bath_mass_kg": 10000, "bath_specific_heat_kj_kg_k": 0.75, "current_temperature_k": 1850,
            "target_temperature_min_k": 1820, "target_temperature_max_k": 1830,
            "materials": [{"name": "single", "effective_cooling_mj_per_kg": 1.5, "cost_per_kg": 1, "min_addition_kg": 0, "max_addition_kg": 500}],
            "max_total_addition_kg": 500,
        }},
        {"id": "D020-B1", "kind": "boundary", "input": {
            "bath_mass_kg": 10000, "bath_specific_heat_kj_kg_k": 0.75, "current_temperature_k": 1860,
            "target_temperature_min_k": 1850, "target_temperature_max_k": 1870,
            "materials": [{"name": "single", "effective_cooling_mj_per_kg": 1.5, "cost_per_kg": 1, "min_addition_kg": 0, "max_addition_kg": 500}],
            "max_total_addition_kg": 500,
        }},
        {"id": "D020-F1", "kind": "failure", "input": {
            "bath_mass_kg": 10000, "bath_specific_heat_kj_kg_k": 0.75, "current_temperature_k": 1840,
            "target_temperature_min_k": 1850, "target_temperature_max_k": 1870,
            "materials": [{"name": "single", "effective_cooling_mj_per_kg": 1.5, "cost_per_kg": 1, "min_addition_kg": 0, "max_addition_kg": 500}],
            "max_total_addition_kg": 500,
        }},
        {"id": "D020-F2", "kind": "failure", "input": {
            "bath_mass_kg": 100000, "bath_specific_heat_kj_kg_k": 0.8, "current_temperature_k": 1900,
            "target_temperature_min_k": 1800, "target_temperature_max_k": 1810,
            "materials": [{"name": "weak", "effective_cooling_mj_per_kg": 0.1, "cost_per_kg": 1, "min_addition_kg": 0, "max_addition_kg": 10}],
            "max_total_addition_kg": 10,
        }},
    ]

    def invoke(self, params: dict, context=None) -> ModelResult:
        errors = self.validate_input(params)
        if errors:
            return fail("；".join(errors))
        numeric = {}
        for field in (
            "bath_mass_kg", "bath_specific_heat_kj_kg_k", "current_temperature_k",
            "target_temperature_min_k", "target_temperature_max_k", "max_total_addition_kg",
        ):
            value, error = finite(params.get(field), field)
            if error:
                return fail(error)
            numeric[field] = value
        if numeric["bath_mass_kg"] <= 0 or numeric["bath_specific_heat_kj_kg_k"] <= 0 \
                or numeric["current_temperature_k"] <= 0 or numeric["target_temperature_min_k"] <= 0 \
                or numeric["target_temperature_max_k"] <= 0 or numeric["max_total_addition_kg"] < 0:
            return fail("质量、比热和温度必须为正，最大加入量不得为负")
        if numeric["target_temperature_min_k"] > numeric["target_temperature_max_k"]:
            return fail("目标温度下限不得高于上限")
        if numeric["current_temperature_k"] < numeric["target_temperature_min_k"] - 1e-12:
            return fail("当前温度低于目标下限，正冷却材料不适用", "MODEL_NOT_APPLICABLE")
        heat_capacity_mj_k = numeric["bath_mass_kg"] * numeric["bath_specific_heat_kj_kg_k"] / 1000
        q_min = max(0.0, heat_capacity_mj_k * (numeric["current_temperature_k"] - numeric["target_temperature_max_k"]))
        q_max = max(0.0, heat_capacity_mj_k * (numeric["current_temperature_k"] - numeric["target_temperature_min_k"]))
        raw_materials = params.get("materials")
        if not isinstance(raw_materials, list) or not 1 <= len(raw_materials) <= 20:
            return fail("materials必须含1至20项")
        required = {"name", "effective_cooling_mj_per_kg", "cost_per_kg", "min_addition_kg", "max_addition_kg"}
        materials, names = [], set()
        for index, raw in enumerate(raw_materials):
            problem = strict_object(raw, required, {"batch_size_kg"}, f"materials[{index}]")
            if problem:
                return fail(problem)
            name = raw["name"]
            if not isinstance(name, str) or not name.strip() or name.strip() in names:
                return fail("材料名必须为唯一非空字符串")
            name = name.strip(); names.add(name)
            cooling, problem = finite(raw["effective_cooling_mj_per_kg"], f"materials[{index}].effective_cooling_mj_per_kg")
            cost, problem2 = finite(raw["cost_per_kg"], f"materials[{index}].cost_per_kg")
            lower, problem3 = finite(raw["min_addition_kg"], f"materials[{index}].min_addition_kg")
            upper, problem4 = finite(raw["max_addition_kg"], f"materials[{index}].max_addition_kg")
            if problem or problem2 or problem3 or problem4 or cooling <= 0 or cost < 0 or lower < 0 or upper < lower:
                return fail(problem or problem2 or problem3 or problem4 or "材料冷却能力/成本/加入边界非法")
            batch = None
            if "batch_size_kg" in raw:
                batch, problem = finite(raw["batch_size_kg"], f"materials[{index}].batch_size_kg")
                if problem or batch <= 0:
                    return fail(problem or "batch_size_kg必须大于0")
            scale = batch or 1.0
            lower_units = math.ceil(lower / scale - 1e-12) if batch else lower
            upper_units = math.floor(upper / scale + 1e-12) if batch else upper
            if lower_units > upper_units + 1e-12:
                return fail(f"材料{name}批量与加入上下界无可行点", "MODEL_NOT_APPLICABLE")
            materials.append({"name": name, "cooling": cooling, "cost": cost, "lower": lower_units, "upper": upper_units, "scale": scale, "batch": batch, "integer": batch is not None})
        rows = [
            [material["cooling"] * material["scale"] for material in materials],
            [material["scale"] for material in materials],
        ]
        solution = solve_mixed_linear(
            [material["cost"] * material["scale"] for material in materials],
            [material["lower"] for material in materials], [material["upper"] for material in materials],
            [1 if material["integer"] else 0 for material in materials],
            rows, [q_min, -np.inf], [q_max, numeric["max_total_addition_kg"]],
        )
        if not solution.success:
            code = "MODEL_NOT_APPLICABLE" if solution.status in {2, 3} else "NUMERICAL_ERROR"
            return fail(f"冷却材料优化失败: {solution.message}", code)
        amounts = [max(0.0, float(value) * material["scale"]) for value, material in zip(solution.x, materials)]
        achieved_q = sum(amount * material["cooling"] for amount, material in zip(amounts, materials))
        final_temperature = numeric["current_temperature_k"] - achieved_q / heat_capacity_mj_k
        total_addition = sum(amounts)
        energy_reconstructed = heat_capacity_mj_k * (numeric["current_temperature_k"] - final_temperature)
        residual = achieved_q - energy_reconstructed
        if achieved_q < q_min - 1e-7 or achieved_q > q_max + 1e-7 \
                or total_addition > numeric["max_total_addition_kg"] + 1e-7 or abs(residual) > 1e-8:
            return fail("优化结果未通过冷却量、加入量或能量闭合复核", "NUMERICAL_ERROR")
        additions = [{
            "name": material["name"], "addition_kg": amount,
            "batch_size_kg": material["batch"],
            "batch_count": int(round(amount / material["batch"])) if material["batch"] else None,
            "effective_cooling_mj_per_kg": material["cooling"],
            "cooling_mj": amount * material["cooling"], "cost_per_kg": material["cost"],
            "cost": amount * material["cost"],
        } for amount, material in zip(amounts, materials)]
        warnings_out = []
        if total_addition <= 1e-10:
            warnings_out.append(BoundaryWarning("materials", "当前温度已在目标区间，最优加入量为零"))
        elif abs(achieved_q - q_min) <= 1e-7 or abs(achieved_q - q_max) <= 1e-7:
            warnings_out.append(BoundaryWarning("predicted_final_temperature_k", "最优终温位于目标温区边界"))
        mip_gap = getattr(solution, "mip_gap", None)
        dual_bound = getattr(solution, "mip_dual_bound", None)
        return ModelResult(True, result={
            "additions": additions,
            "total_addition_kg": total_addition,
            "target_heat_removal_range_mj": [q_min, q_max],
            "achieved_heat_removal_mj": achieved_q,
            "predicted_final_temperature_k": final_temperature,
            "temperature_lower_margin_k": final_temperature - numeric["target_temperature_min_k"],
            "temperature_upper_margin_k": numeric["target_temperature_max_k"] - final_temperature,
            "total_cost": float(solution.fun),
            "energy_closure_residual_mj": residual,
            "integrality_used": any(material["integer"] for material in materials),
            "mip_gap": float(mip_gap) if mip_gap is not None else None,
            "objective_lower_bound": float(dual_bound) if dual_bound is not None else None,
            "solver": "scipy-milp-highs-1.18.1",
            "solver_status": str(solution.message),
            "algorithm_version": "d020-static-heat-milp-v1",
        }, boundary_check=BoundaryCheck(not warnings_out, warnings_out))
