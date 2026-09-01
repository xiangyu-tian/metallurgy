"""P1-W12 additive analysis tools; all existing implementations stay frozen."""

from __future__ import annotations

import ast
import math
import re
from statistics import NormalDist
from typing import Any

import numpy as np

from .base import BaseModelTool, BoundaryCheck, BoundaryWarning, InputField, ModelResult, OutputField


def rel(kind: str, target: str, description: str) -> dict[str, str]:
    return {"type": kind, "target": target, "description": description}


def fail(message: str, code: str = "INVALID_INPUT") -> ModelResult:
    return ModelResult(False, error=message, error_code=code)


def _finite(value: Any, label: str) -> tuple[float | None, str | None]:
    if isinstance(value, bool):
        return None, f"{label}必须是数值"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None, f"{label}必须是数值"
    if not math.isfinite(number):
        return None, f"{label}必须是有限数值"
    return number, None


class W12AnalysisTool(BaseModelTool):
    scenario = "通用数据与校验"
    priority = "P1"
    status = qualification_status = "qualified"
    count_eligible = True
    data_requirement = "FORMULA_ONLY"
    data_access_mode = "none"


class A009_RobustOutlierDetection(W12AnalysisTool):
    model_id, name, version = "A009", "稳健异常值检测", "1.0.0"
    tool_name = "metallurgy_detect_outliers"
    description = "用IQR围栏或MAD修正Z分数标记调用方显式数组中的待调查异常点，不自动删除或修正数据。"
    model_type = "稳健统计/规则"
    applicable_boundary = (
        "一维、同单位、3至10000个有限标量；支持Tukey IQR与modified Z-score。"
        "不处理多变量异常、时序漂移、分布外检测、Isolation Forest或自动数据清洗。"
    )
    data_source = ["NIST/SEMATECH e-Handbook of Statistical Methods", "Iglewicz-Hoaglin modified Z-score"]
    source_version = "nist-eda-outlier-2025-snapshot; numpy-2.5-linear-quantile"
    formula_reference = (
        "IQR=Q3-Q1; fences=[Q1-k*IQR,Q3+k*IQR]; "
        "MAD=median(|x-median(x)|); modified_z=0.6744897501960817*(x-median)/MAD"
    )
    source_records = [
        {
            "source_id": "NIST-EDA-OUTLIERS",
            "name": "NIST/SEMATECH e-Handbook: Detection of Outliers",
            "version": "web snapshot 2025",
            "url": "https://www.itl.nist.gov/div898/handbook/eda/section3/eda35h.htm",
        },
        {
            "source_id": "NUMPY-QUANTILE-LINEAR",
            "name": "NumPy linear sample quantile convention",
            "version": "2.5",
        },
    ]
    failure_modes = [
        "数组不足3项、超过10000项或含非有限值",
        "标签数量与数值数量不一致或标签重复",
        "阈值非正",
        "非恒定样本的IQR或MAD为零，所选稳健尺度不能识别异常",
    ]
    independent_validation = [
        "IQR围栏和MAD修正Z分数由排序统计量独立复算",
        "平移和正比例缩放不改变异常标记",
        "输入置换只置换逐点结果，不改变异常标签集合",
        "完全恒定样本返回零异常并显式边界警告",
    ]
    dependencies = []
    relations = [
        rel("complements", "A004", "A004归一化成分；A009只标记一维数组中的可疑观测且保留原值"),
        rel("complements", "A008", "A008填补缺失值；A009不填补也不删除异常值，可作为其上游数据审查"),
    ]
    related_catalog_ids = ["G015"]
    input_fields = [
        InputField("values", "待检测数值", "array", unit="$value_unit", items={"type": "number"}, min_items=3, max_items=10000),
        InputField("value_unit", "数值单位", "string", description="非空调用方单位标识；工具不执行单位换算"),
        InputField("method", "检测方法", "select", enum=["iqr", "modified_z"]),
        InputField("threshold", "异常阈值", "number", unit="1", min_value=1e-12),
        InputField("labels", "逐点标签", "array", required=False, items={"type": "string"}, min_items=3, max_items=10000),
    ]
    output_fields = [
        OutputField("method", "检测方法", "string"),
        OutputField("threshold", "异常阈值", "number", "1"),
        OutputField("center", "稳健中心", "number", "$value_unit"),
        OutputField("scale", "稳健尺度", "number", "$value_unit"),
        OutputField("lower_fence", "下围栏", "number", "$value_unit"),
        OutputField("upper_fence", "上围栏", "number", "$value_unit"),
        OutputField("scores", "逐点无量纲分数", "array", "1"),
        OutputField("flags", "逐点异常标志", "array", "boolean"),
        OutputField("outlier_indices", "异常点零基索引", "array", "1"),
        OutputField("outlier_labels", "异常点标签", "array"),
        OutputField("outlier_count", "异常数量", "number", "1"),
        OutputField("sample_count", "样本数量", "number", "1"),
        OutputField("value_unit", "原数值单位", "string"),
        OutputField("algorithm_version", "算法版本", "string"),
    ]
    validation_rules = [
        {"rule": "finite_one_dimensional_values_between_3_and_10000"},
        {"rule": "positive_threshold_and_matching_unique_labels"},
        {"rule": "selected_robust_scale_must_be_nonzero_unless_sample_constant"},
    ]
    qualification_cases = [
        {"id": "A009-N1", "kind": "normal", "input": {"values": [10, 11, 10, 12, 50], "value_unit": "K", "method": "iqr", "threshold": 1.5}},
        {"id": "A009-N2", "kind": "normal", "input": {"values": [1, 1.1, 0.9, 1.05, 8], "value_unit": "wt%", "method": "modified_z", "threshold": 3.5}},
        {"id": "A009-N3", "kind": "normal", "input": {"values": [100, 101, 102, 103, 104, 105], "labels": ["a", "b", "c", "d", "e", "f"], "value_unit": "Pa", "method": "iqr", "threshold": 1.5}},
        {"id": "A009-B1", "kind": "boundary", "input": {"values": [7, 7, 7, 7], "value_unit": "1", "method": "modified_z", "threshold": 3.5}},
        {"id": "A009-F1", "kind": "failure", "input": {"values": [1, 2], "value_unit": "K", "method": "iqr", "threshold": 1.5}},
        {"id": "A009-F2", "kind": "failure", "input": {"values": [1, 1, 1, 2], "value_unit": "K", "method": "modified_z", "threshold": 3.5}},
    ]

    def invoke(self, params: dict, context=None) -> ModelResult:
        errors = self.validate_input(params)
        if errors:
            return fail("；".join(errors))
        raw_values = params.get("values")
        if not isinstance(raw_values, list) or not 3 <= len(raw_values) <= 10000:
            return fail("values必须含3至10000个数值")
        values = []
        for index, raw in enumerate(raw_values):
            value, error = _finite(raw, f"values[{index}]")
            if error:
                return fail(error)
            values.append(value)
        unit = params.get("value_unit")
        if not isinstance(unit, str) or not unit.strip():
            return fail("value_unit必须是非空字符串")
        unit = unit.strip()
        labels = params.get("labels")
        if labels is None:
            labels = [str(index) for index in range(len(values))]
        if not isinstance(labels, list) or len(labels) != len(values):
            return fail("labels数量必须与values一致")
        if any(not isinstance(label, str) or not label.strip() for label in labels):
            return fail("labels必须全部为非空字符串")
        labels = [label.strip() for label in labels]
        if len(set(labels)) != len(labels):
            return fail("labels不得重复")
        method = params.get("method")
        if method not in {"iqr", "modified_z"}:
            return fail("method必须是iqr或modified_z")
        threshold, error = _finite(params.get("threshold"), "threshold")
        if error or threshold <= 0:
            return fail(error or "threshold必须大于0")

        array = np.asarray(values, dtype=float)
        median = float(np.median(array))
        constant = bool(np.all(array == array[0]))
        warnings_out: list[BoundaryWarning] = []
        if method == "iqr":
            q1, q3 = (float(value) for value in np.quantile(array, [0.25, 0.75], method="linear"))
            scale = q3 - q1
            lower = q1 - threshold * scale
            upper = q3 + threshold * scale
            if scale == 0:
                if not constant:
                    return fail("IQR为零但样本并非恒定，IQR方法不适用", "MODEL_NOT_APPLICABLE")
                scores = np.zeros_like(array)
                flags = np.zeros(array.shape, dtype=bool)
                warnings_out.append(BoundaryWarning("values", "完全恒定样本的IQR为零；返回零异常"))
            else:
                scores = np.abs((array - median) / scale)
                flags = (array < lower) | (array > upper)
        else:
            absolute_deviation = np.abs(array - median)
            scale = float(np.median(absolute_deviation))
            if scale == 0:
                if not constant:
                    return fail("MAD为零但样本并非恒定，modified_z方法不适用", "MODEL_NOT_APPLICABLE")
                scores = np.zeros_like(array)
                flags = np.zeros(array.shape, dtype=bool)
                warnings_out.append(BoundaryWarning("values", "完全恒定样本的MAD为零；返回零异常"))
            else:
                signed = 0.6744897501960817 * (array - median) / scale
                scores = np.abs(signed)
                flags = scores > threshold
            width = threshold * scale / 0.6744897501960817 if scale else 0.0
            lower, upper = median - width, median + width
        indices = [int(index) for index in np.flatnonzero(flags)]
        return ModelResult(
            True,
            result={
                "method": method,
                "threshold": threshold,
                "center": median,
                "scale": float(scale),
                "lower_fence": float(lower),
                "upper_fence": float(upper),
                "scores": [float(value) for value in scores],
                "flags": [bool(value) for value in flags],
                "outlier_indices": indices,
                "outlier_labels": [labels[index] for index in indices],
                "outlier_count": len(indices),
                "sample_count": len(values),
                "value_unit": unit,
                "algorithm_version": "robust-outlier-iqr-modified-z-v1",
            },
            boundary_check=BoundaryCheck(not warnings_out, warnings_out),
        )


_ALLOWED_FUNCTIONS = {
    "exp": np.exp,
    "log": np.log,
    "sqrt": np.sqrt,
    "sin": np.sin,
    "cos": np.cos,
    "tan": np.tan,
    "abs": np.abs,
}
_ALLOWED_BINOPS = {
    ast.Add: lambda left, right: left + right,
    ast.Sub: lambda left, right: left - right,
    ast.Mult: lambda left, right: left * right,
    ast.Div: lambda left, right: left / right,
    ast.Pow: lambda left, right: left ** right,
}


def _parse_expression(expression: Any, variable_names: set[str]) -> ast.Expression:
    if not isinstance(expression, str) or not expression.strip() or len(expression) > 512:
        raise ValueError("expression必须是1至512字符的非空字符串")
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise ValueError("expression语法无效") from exc
    nodes = list(ast.walk(tree))
    if len(nodes) > 256:
        raise ValueError("expression语法树超过256节点")
    for node in nodes:
        if isinstance(node, ast.Expression | ast.Load | ast.operator | ast.unaryop):
            continue
        if isinstance(node, ast.Constant):
            if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
                raise ValueError("expression常量只能是数值")
        elif isinstance(node, ast.Name):
            if node.id not in variable_names and node.id not in _ALLOWED_FUNCTIONS:
                raise ValueError(f"expression包含未声明名称: {node.id}")
        elif isinstance(node, ast.BinOp):
            if type(node.op) not in _ALLOWED_BINOPS:
                raise ValueError("expression包含不支持的二元运算")
        elif isinstance(node, ast.UnaryOp):
            if not isinstance(node.op, (ast.UAdd, ast.USub)):
                raise ValueError("expression包含不支持的一元运算")
        elif isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in _ALLOWED_FUNCTIONS \
                    or len(node.args) != 1 or node.keywords:
                raise ValueError("expression函数调用不在允许列表或参数数量不为1")
        else:
            raise ValueError(f"expression包含不允许的语法: {type(node).__name__}")
    return tree


def _evaluate_expression(node: ast.AST, environment: dict[str, Any]):
    if isinstance(node, ast.Expression):
        return _evaluate_expression(node.body, environment)
    if isinstance(node, ast.Constant):
        return float(node.value)
    if isinstance(node, ast.Name):
        if node.id not in environment:
            raise ValueError(f"表达式变量未提供: {node.id}")
        return environment[node.id]
    if isinstance(node, ast.UnaryOp):
        value = _evaluate_expression(node.operand, environment)
        return value if isinstance(node.op, ast.UAdd) else -value
    if isinstance(node, ast.BinOp):
        left = _evaluate_expression(node.left, environment)
        right = _evaluate_expression(node.right, environment)
        return _ALLOWED_BINOPS[type(node.op)](left, right)
    if isinstance(node, ast.Call):
        argument = _evaluate_expression(node.args[0], environment)
        return _ALLOWED_FUNCTIONS[node.func.id](argument)
    raise ValueError("表达式含未批准语法")


class A010_UncertaintyPropagation(W12AnalysisTool):
    model_id, name, version = "A010", "标量测量模型不确定度传播", "1.0.0"
    tool_name = "metallurgy_propagate_uncertainty"
    description = "对受限标量数学表达式执行JCGM一阶协方差传播或固定种子Monte Carlo分布传播。"
    model_type = "不确定度分析/数值传播"
    applicable_boundary = (
        "1至12个显式变量、受限标量表达式；一阶法用于局部线性化，Monte Carlo最多200000样本。"
        "非独立相关变量在Monte Carlo模式下仅支持联合正态；不执行任意代码或任意注册工具。"
    )
    data_source = ["JCGM 100:2008 GUM", "JCGM 101:2008 Monte Carlo supplement"]
    source_version = "JCGM-100-2008; JCGM-101-2008; restricted-expression-v1"
    formula_reference = (
        "u_y^2=c^T U_x c, c_i=df/dx_i; Monte Carlo由声明分布和固定seed采样，"
        "报告样本均值、样本标准差与中心覆盖区间"
    )
    source_records = [
        {
            "source_id": "JCGM-100-2008",
            "name": "Evaluation of measurement data — Guide to the expression of uncertainty in measurement",
            "version": "JCGM 100:2008",
            "url": "https://doi.org/10.59161/JCGM100-2008E",
        },
        {
            "source_id": "JCGM-101-2008",
            "name": "Propagation of distributions using a Monte Carlo method",
            "version": "JCGM 101:2008",
            "url": "https://doi.org/10.59161/JCGM101-2008",
        },
    ]
    failure_modes = [
        "表达式使用未批准语法、函数或未声明变量",
        "变量名重复/非法、均值或标准不确定度非有限",
        "协方差维度错误、非对称、对角线与标准不确定度不一致或非半正定",
        "相关非正态变量请求Monte Carlo",
        "表达式在均值/扰动/样本上超定义域或产生非有限结果",
    ]
    independent_validation = [
        "线性模型的均值与c^T U c解析结果一致",
        "协方差交叉项由独立矩阵乘法复算",
        "固定随机种子重复调用逐字段一致",
        "线性正态模型Monte Carlo结果与解析结果在抽样误差内一致",
        "模型加常数只平移输出估计，不改变标准不确定度",
    ]
    dependencies = []
    relations = [
        rel("uses_convention_of", "A001", "调用方应先用A001统一变量单位；A010只传播已统一量纲的标量模型"),
        rel("complements", "A009", "A009标记可疑观测；A010量化已给输入不确定度对结果的传播"),
    ]
    related_catalog_ids = ["G010"]
    _variable_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string", "pattern": "^[A-Za-z_][A-Za-z0-9_]{0,31}$"},
            "mean": {"type": "number"},
            "standard_uncertainty": {"type": "number", "minimum": 0},
            "distribution": {"type": "string", "enum": ["normal", "uniform", "triangular"]},
        },
        "required": ["name", "mean", "standard_uncertainty", "distribution"],
        "additionalProperties": False,
    }
    input_fields = [
        InputField("expression", "标量测量模型", "string", description="受限数学表达式；允许+,-,*,/,**,exp,log,sqrt,sin,cos,tan,abs"),
        InputField("variables", "输入变量", "array", items=_variable_schema, min_items=1, max_items=12),
        InputField("method", "传播方法", "select", enum=["first_order", "monte_carlo"]),
        InputField("covariance_matrix", "协方差矩阵", "array", required=False, unit="$input_unit^2", items={"type": "array", "items": {"type": "number"}}, min_items=1, max_items=12),
        InputField("sample_count", "Monte Carlo样本数", "integer", required=False, default=20000, unit="1", min_value=1000, max_value=200000),
        InputField("random_seed", "随机种子", "integer", required=False, default=20260901, unit="1", min_value=0, max_value=4294967295),
        InputField("coverage_probability", "中心覆盖概率", "number", required=False, default=0.95, unit="1", min_value=0.5, max_value=0.999),
        InputField("input_unit", "输入统一单位说明", "string", description="变量可为不同量纲时写明表达式中的单位约定"),
        InputField("output_unit", "输出单位", "string", description="非空调用方输出单位标识"),
    ]
    output_fields = [
        OutputField("method", "传播方法", "string"),
        OutputField("output_estimate", "输出估计", "number", "$output_unit"),
        OutputField("standard_uncertainty", "合成标准不确定度", "number", "$output_unit"),
        OutputField("coverage_probability", "覆盖概率", "number", "1"),
        OutputField("coverage_interval", "覆盖区间", "array", "$output_unit"),
        OutputField("sensitivity_coefficients", "数值灵敏度系数", "object", "$output_unit/$input_unit"),
        OutputField("linearized_variance_contributions", "一阶方差贡献", "object", "$output_unit^2"),
        OutputField("linearized_standard_uncertainty", "一阶标准不确定度", "number", "$output_unit"),
        OutputField("linearized_variance_closure_residual", "一阶方差闭合残差", "number", "$output_unit^2"),
        OutputField("covariance_min_eigenvalue", "协方差最小特征值", "number", "$input_unit^2"),
        OutputField("sample_count", "实际样本数", "number", "1"),
        OutputField("random_seed", "随机种子", "number", "1"),
        OutputField("input_unit", "输入单位约定", "string"),
        OutputField("output_unit", "输出单位", "string"),
        OutputField("algorithm_version", "算法版本", "string"),
    ]
    validation_rules = [
        {"rule": "restricted_scalar_expression_only"},
        {"rule": "unique_finite_variables_and_nonnegative_standard_uncertainties"},
        {"rule": "covariance_symmetric_psd_and_diagonal_matches_declared_uncertainty"},
        {"rule": "correlated_monte_carlo_requires_joint_normal_inputs"},
    ]
    qualification_cases = [
        {"id": "A010-N1", "kind": "normal", "input": {"expression": "2*x+3*y", "variables": [{"name": "x", "mean": 10, "standard_uncertainty": 0.2, "distribution": "normal"}, {"name": "y", "mean": 5, "standard_uncertainty": 0.1, "distribution": "normal"}], "method": "first_order", "input_unit": "mixed_SI", "output_unit": "kJ", "coverage_probability": 0.95}},
        {"id": "A010-N2", "kind": "normal", "input": {"expression": "x*y", "variables": [{"name": "x", "mean": 2, "standard_uncertainty": 0.1, "distribution": "normal"}, {"name": "y", "mean": 4, "standard_uncertainty": 0.2, "distribution": "normal"}], "covariance_matrix": [[0.01, 0.005], [0.005, 0.04]], "method": "first_order", "input_unit": "mixed_SI", "output_unit": "1"}},
        {"id": "A010-N3", "kind": "normal", "input": {"expression": "x+y", "variables": [{"name": "x", "mean": 10, "standard_uncertainty": 1, "distribution": "normal"}, {"name": "y", "mean": 5, "standard_uncertainty": 2, "distribution": "normal"}], "method": "monte_carlo", "sample_count": 5000, "random_seed": 42, "input_unit": "K", "output_unit": "K"}},
        {"id": "A010-B1", "kind": "boundary", "input": {"expression": "x+1", "variables": [{"name": "x", "mean": 3, "standard_uncertainty": 0, "distribution": "normal"}], "method": "first_order", "input_unit": "1", "output_unit": "1"}},
        {"id": "A010-F1", "kind": "failure", "input": {"expression": "__import__('os')", "variables": [{"name": "x", "mean": 1, "standard_uncertainty": 0.1, "distribution": "normal"}], "method": "first_order", "input_unit": "1", "output_unit": "1"}},
        {"id": "A010-F2", "kind": "failure", "input": {"expression": "x+y", "variables": [{"name": "x", "mean": 1, "standard_uncertainty": 1, "distribution": "normal"}, {"name": "y", "mean": 1, "standard_uncertainty": 1, "distribution": "normal"}], "covariance_matrix": [[1, 2], [2, 1]], "method": "first_order", "input_unit": "1", "output_unit": "1"}},
    ]

    @staticmethod
    def _variables(payload: Any) -> tuple[list[dict[str, Any]] | None, str | None]:
        if not isinstance(payload, list) or not 1 <= len(payload) <= 12:
            return None, "variables必须含1至12项"
        variables = []
        names = set()
        allowed = {"name", "mean", "standard_uncertainty", "distribution"}
        for index, raw in enumerate(payload):
            if not isinstance(raw, dict) or set(raw) != allowed:
                return None, f"variables[{index}]字段必须且只能是{sorted(allowed)}"
            name = raw.get("name")
            if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,31}", name):
                return None, f"variables[{index}].name不符合标识符约束"
            if name in names or name in _ALLOWED_FUNCTIONS:
                return None, f"变量名重复或与函数名冲突: {name}"
            mean, error = _finite(raw.get("mean"), f"variables[{index}].mean")
            if error:
                return None, error
            uncertainty, error = _finite(raw.get("standard_uncertainty"), f"variables[{index}].standard_uncertainty")
            if error or uncertainty < 0:
                return None, error or "standard_uncertainty不能为负"
            distribution = raw.get("distribution")
            if distribution not in {"normal", "uniform", "triangular"}:
                return None, f"variables[{index}].distribution不受支持"
            names.add(name)
            variables.append({"name": name, "mean": mean, "u": uncertainty, "distribution": distribution})
        return variables, None

    @staticmethod
    def _covariance(payload: Any, variables: list[dict[str, Any]]) -> tuple[np.ndarray | None, str | None]:
        size = len(variables)
        if payload is None:
            covariance = np.diag([variable["u"] ** 2 for variable in variables])
            return covariance, None
        if not isinstance(payload, list) or len(payload) != size \
                or any(not isinstance(row, list) or len(row) != size for row in payload):
            return None, "covariance_matrix必须是与variables同维的方阵"
        try:
            covariance = np.asarray(payload, dtype=float)
        except (TypeError, ValueError):
            return None, "covariance_matrix必须只含数值"
        if not np.all(np.isfinite(covariance)):
            return None, "covariance_matrix必须只含有限数值"
        scale = max(1.0, float(np.max(np.abs(covariance))))
        if not np.allclose(covariance, covariance.T, rtol=0, atol=1e-12 * scale):
            return None, "covariance_matrix必须对称"
        declared = np.asarray([variable["u"] ** 2 for variable in variables])
        if not np.allclose(np.diag(covariance), declared, rtol=1e-9, atol=1e-15 * scale):
            return None, "covariance_matrix对角线必须等于声明标准不确定度的平方"
        minimum = float(np.linalg.eigvalsh(covariance)[0])
        if minimum < -1e-10 * scale:
            return None, "covariance_matrix不是半正定矩阵"
        return covariance, None

    @staticmethod
    def _scalar_value(tree: ast.Expression, environment: dict[str, Any]) -> float:
        with np.errstate(all="ignore"):
            value = _evaluate_expression(tree, environment)
        array = np.asarray(value)
        if array.ndim != 0:
            raise ValueError("表达式必须返回标量")
        number = float(array)
        if not math.isfinite(number):
            raise ValueError("表达式返回非有限值")
        return number

    @staticmethod
    def _gradient(tree: ast.Expression, variables: list[dict[str, Any]]) -> tuple[np.ndarray, float]:
        means = {variable["name"]: variable["mean"] for variable in variables}
        center = A010_UncertaintyPropagation._scalar_value(tree, means)
        gradient = []
        for variable in variables:
            mean = variable["mean"]
            step = max(abs(mean) * 1e-6, variable["u"] * 1e-4, 1e-7)
            upper = dict(means)
            lower = dict(means)
            upper[variable["name"]] = mean + step
            lower[variable["name"]] = mean - step
            try:
                upper_value = A010_UncertaintyPropagation._scalar_value(tree, upper)
                lower_value = A010_UncertaintyPropagation._scalar_value(tree, lower)
                derivative = (upper_value - lower_value) / (2 * step)
            except ValueError:
                upper_value = A010_UncertaintyPropagation._scalar_value(tree, upper)
                derivative = (upper_value - center) / step
            if not math.isfinite(derivative):
                raise ValueError(f"变量{variable['name']}的数值灵敏度非有限")
            gradient.append(derivative)
        return np.asarray(gradient, dtype=float), center

    def invoke(self, params: dict, context=None) -> ModelResult:
        errors = self.validate_input(params)
        if errors:
            return fail("；".join(errors))
        variables, error = self._variables(params.get("variables"))
        if error:
            return fail(error)
        try:
            tree = _parse_expression(params.get("expression"), {variable["name"] for variable in variables})
        except ValueError as exc:
            return fail(str(exc))
        covariance, error = self._covariance(params.get("covariance_matrix"), variables)
        if error:
            return fail(error)
        method = params.get("method")
        if method not in {"first_order", "monte_carlo"}:
            return fail("method必须是first_order或monte_carlo")
        try:
            sample_count = int(params.get("sample_count", 20000))
            random_seed = int(params.get("random_seed", 20260901))
        except (TypeError, ValueError):
            return fail("sample_count和random_seed必须是整数")
        if isinstance(params.get("sample_count", 20000), bool) or sample_count < 1000 or sample_count > 200000:
            return fail("sample_count必须是1000至200000的整数")
        if isinstance(params.get("random_seed", 20260901), bool) or random_seed < 0 or random_seed > 4294967295:
            return fail("random_seed必须是0至4294967295的整数")
        coverage, error = _finite(params.get("coverage_probability", 0.95), "coverage_probability")
        if error or not 0.5 <= coverage <= 0.999:
            return fail(error or "coverage_probability必须在0.5至0.999之间")
        input_unit = params.get("input_unit")
        output_unit = params.get("output_unit")
        if not isinstance(input_unit, str) or not input_unit.strip() \
                or not isinstance(output_unit, str) or not output_unit.strip():
            return fail("input_unit和output_unit必须是非空字符串")

        try:
            gradient, center = self._gradient(tree, variables)
            linear_variance = float(gradient @ covariance @ gradient)
        except (ValueError, FloatingPointError) as exc:
            return fail(str(exc), "OUT_OF_DOMAIN")
        scale = max(1.0, abs(linear_variance))
        if linear_variance < -1e-10 * scale:
            return fail("传播得到负方差", "NUMERICAL_ERROR")
        linear_variance = max(0.0, linear_variance)
        contributions_array = gradient * (covariance @ gradient)
        variance_closure = float(np.sum(contributions_array) - linear_variance)
        linear_uncertainty = math.sqrt(linear_variance)

        if method == "first_order":
            estimate = center
            standard_uncertainty = linear_uncertainty
            factor = NormalDist().inv_cdf((1.0 + coverage) / 2.0)
            interval = [estimate - factor * standard_uncertainty, estimate + factor * standard_uncertainty]
            actual_samples = 0
            reported_seed = 0
        else:
            off_diagonal = covariance - np.diag(np.diag(covariance))
            correlated = bool(np.any(np.abs(off_diagonal) > 1e-15 * max(1.0, float(np.max(np.abs(covariance))))))
            if correlated and any(variable["distribution"] != "normal" for variable in variables):
                return fail("相关Monte Carlo输入只支持联合正态分布", "MODEL_NOT_APPLICABLE")
            rng = np.random.default_rng(random_seed)
            means = np.asarray([variable["mean"] for variable in variables], dtype=float)
            try:
                if correlated:
                    samples = rng.multivariate_normal(means, covariance, size=sample_count, check_valid="raise", tol=1e-10)
                else:
                    columns = []
                    for variable in variables:
                        mean, uncertainty = variable["mean"], variable["u"]
                        if uncertainty == 0:
                            column = np.full(sample_count, mean)
                        elif variable["distribution"] == "normal":
                            column = rng.normal(mean, uncertainty, sample_count)
                        elif variable["distribution"] == "uniform":
                            half_width = math.sqrt(3.0) * uncertainty
                            column = rng.uniform(mean - half_width, mean + half_width, sample_count)
                        else:
                            half_width = math.sqrt(6.0) * uncertainty
                            column = rng.triangular(mean - half_width, mean, mean + half_width, sample_count)
                        columns.append(column)
                    samples = np.column_stack(columns)
                environment = {variable["name"]: samples[:, index] for index, variable in enumerate(variables)}
                with np.errstate(all="ignore"):
                    outputs = np.asarray(_evaluate_expression(tree, environment), dtype=float)
                if outputs.ndim == 0:
                    outputs = np.full(sample_count, float(outputs))
                if outputs.shape != (sample_count,) or not np.all(np.isfinite(outputs)):
                    return fail("Monte Carlo表达式输出维度错误或含非有限值", "OUT_OF_DOMAIN")
                estimate = float(np.mean(outputs))
                standard_uncertainty = float(np.std(outputs, ddof=1))
                alpha = (1.0 - coverage) / 2.0
                interval = [float(np.quantile(outputs, alpha)), float(np.quantile(outputs, 1.0 - alpha))]
            except (ValueError, FloatingPointError, np.linalg.LinAlgError) as exc:
                return fail(f"Monte Carlo传播失败: {exc}", "NUMERICAL_ERROR")
            actual_samples = sample_count
            reported_seed = random_seed

        warnings_out = []
        if all(variable["u"] == 0 for variable in variables):
            warnings_out.append(BoundaryWarning("variables", "全部输入标准不确定度为零；输出不确定度为零"))
        eigen_min = float(np.linalg.eigvalsh(covariance)[0])
        return ModelResult(
            True,
            result={
                "method": method,
                "output_estimate": float(estimate),
                "standard_uncertainty": float(standard_uncertainty),
                "coverage_probability": coverage,
                "coverage_interval": [float(value) for value in interval],
                "sensitivity_coefficients": {variable["name"]: float(gradient[index]) for index, variable in enumerate(variables)},
                "linearized_variance_contributions": {variable["name"]: float(contributions_array[index]) for index, variable in enumerate(variables)},
                "linearized_standard_uncertainty": linear_uncertainty,
                "linearized_variance_closure_residual": variance_closure,
                "covariance_min_eigenvalue": eigen_min,
                "sample_count": actual_samples,
                "random_seed": reported_seed,
                "input_unit": input_unit.strip(),
                "output_unit": output_unit.strip(),
                "algorithm_version": "JCGM100-101-restricted-expression-v1",
            },
            boundary_check=BoundaryCheck(not warnings_out, warnings_out),
        )
