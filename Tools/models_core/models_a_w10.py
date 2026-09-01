"""P1-W10 additive chemistry tools; existing A-series implementations stay frozen."""

from __future__ import annotations

import math
from fractions import Fraction
from functools import reduce
from math import gcd
from typing import Any, Iterable, Optional

from .base import BaseModelTool, BoundaryCheck, BoundaryWarning, InputField, ModelResult, OutputField
from .models_a import parse_formula_details


SCENARIO = "基础化学与计量"


def rel(kind: str, target: str, description: str) -> dict[str, str]:
    return {"type": kind, "target": target, "description": description}


def fail(message: str, code: str = "INVALID_INPUT") -> ModelResult:
    return ModelResult(False, error=message, error_code=code)


def _lcm(left: int, right: int) -> int:
    return abs(left * right) // gcd(left, right) if left and right else 0


def _rref_null_vector(matrix: list[list[Fraction]]) -> tuple[Optional[list[Fraction]], int]:
    """Return the unique (up to scale) null vector and the matrix nullity."""
    rows = [list(row) for row in matrix]
    row_count = len(rows)
    column_count = len(rows[0]) if rows else 0
    pivot_columns: list[int] = []
    pivot_row = 0
    for column in range(column_count):
        selected = next((row for row in range(pivot_row, row_count) if rows[row][column]), None)
        if selected is None:
            continue
        rows[pivot_row], rows[selected] = rows[selected], rows[pivot_row]
        pivot = rows[pivot_row][column]
        rows[pivot_row] = [value / pivot for value in rows[pivot_row]]
        for row in range(row_count):
            if row == pivot_row or not rows[row][column]:
                continue
            factor = rows[row][column]
            rows[row] = [value - factor * pivot_value for value, pivot_value in zip(rows[row], rows[pivot_row])]
        pivot_columns.append(column)
        pivot_row += 1
        if pivot_row == row_count:
            break

    free_columns = [column for column in range(column_count) if column not in pivot_columns]
    nullity = len(free_columns)
    if nullity != 1:
        return None, nullity
    free_column = free_columns[0]
    vector = [Fraction(0) for _ in range(column_count)]
    vector[free_column] = Fraction(1)
    for row, column in reversed(list(enumerate(pivot_columns))):
        vector[column] = -sum(rows[row][j] * vector[j] for j in free_columns)
    return vector, nullity


def _coefficient_text(coefficient: int, formula: str) -> str:
    return formula if coefficient == 1 else f"{coefficient} {formula}"


class A011_ReactionStoichiometrySolver(BaseModelTool):
    model_id, name, version = "A011", "反应计量系数求解", "1.0.0"
    scenario, priority = SCENARIO, "P1"
    tool_name = "metallurgy_solve_reaction_stoichiometry"
    status = qualification_status = "qualified"
    count_eligible = True
    data_requirement = "FORMULA_ONLY"
    data_access_mode = "none"
    description = "由反应物和生成物化学式构造精确有理数守恒矩阵，求唯一的最小正整数反应计量系数。"
    applicable_boundary = (
        "适用于元素组成确定的物种；可通过独立charge字段加入电荷守恒。要求守恒矩阵零空间维数恰为1，"
        "且存在所有物种系数均为正的解；不处理非整数计量化合物、电子物种或多自由度反应网络。"
    )
    data_source = ["Stoichiometric matrix null-space method", "Law of conservation of atoms and charge"]
    source_version = "exact-rational-rref-v1"
    formula_reference = "A*nu=0；有理数RREF求一维零空间；分母最小公倍数整数化并以最大公约数约简"
    source_records = [
        {"source_id": "STOICHIOMETRIC-NULLSPACE", "name": "Exact stoichiometric matrix null-space algorithm", "version": "rational-rref-v1"},
        {"source_id": "IUPAC-RED-BOOK-2005", "name": "Nomenclature of Inorganic Chemistry", "version": "2005"},
    ]
    failure_modes = [
        "任一化学式不能由A002语法完整解析",
        "反应两侧元素集合不同",
        "零空间维数不是1或唯一零空间向量含零/异号系数",
        "物种含非整数元素计量数或整数化分母超过上限",
        "启用电荷守恒时charge不是整数",
    ]
    independent_validation = [
        "将输出方程送入A006后逐元素残差为零",
        "输出系数最大公约数为1",
        "用整数矩阵乘法独立复算A*nu为零",
    ]
    dependencies = ["A002"]
    relations = [
        rel("depends_on", "A002", "复用A002的中性化学式解析语法与元素计量数"),
        rel("upstream_of", "A006", "求得的显式系数反应式可交由A006独立校验"),
        rel("overlaps", "A006", "都处理反应计量；A011求系数，A006校验用户给定系数"),
    ]
    _species_schema = {
        "type": "object",
        "properties": {
            "formula": {"type": "string", "description": "A002适用域内的中性化学式"},
            "charge": {"type": "integer", "description": "可选净电荷数；启用电荷守恒时使用"},
        },
        "required": ["formula"],
        "additionalProperties": False,
    }
    input_fields = [
        InputField("reactants", "反应物", "array", items=_species_schema, min_items=1, max_items=20, description="反应物物种数组；系数由工具求解"),
        InputField("products", "生成物", "array", items=_species_schema, min_items=1, max_items=20, description="生成物物种数组；系数由工具求解"),
        InputField("include_charge_balance", "是否包含电荷守恒", "boolean", required=False, default=False, description="为true时将每个物种charge加入守恒矩阵"),
        InputField("max_denominator", "有理数分母上限", "integer", required=False, default=10000, unit="1", min_value=1, max_value=1_000_000, description="解析计量数有理化时允许的最大分母"),
    ]
    output_fields = [
        OutputField("reactant_coefficients", "反应物最小整数系数", "array", description="与reactants同序；单位1"),
        OutputField("product_coefficients", "生成物最小整数系数", "array", description="与products同序；单位1"),
        OutputField("balanced_reaction", "规范配平方程", "string", description="以->连接并省略系数1"),
        OutputField("element_residuals", "逐元素残差", "object", description="生成物减反应物；单位1"),
        OutputField("charge_residual", "电荷残差", "number", "1", nullable=True, description="未启用电荷守恒时为null"),
        OutputField("nullity", "守恒矩阵零空间维数", "number", "1"),
        OutputField("gcd_is_one", "系数是否已最简", "boolean"),
        OutputField("passed", "是否通过精确守恒复算", "boolean"),
        OutputField("algorithm_version", "算法版本", "string"),
    ]
    validation_rules = [
        {"rule": "one_to_twenty_species_per_side", "fields": ["reactants", "products"]},
        {"rule": "unique_one_dimensional_positive_nullspace"},
        {"rule": "exact_atom_and_optional_charge_conservation"},
    ]
    qualification_cases = [
        {"id": "A011-N1", "kind": "normal", "input": {"reactants": [{"formula": "Fe"}, {"formula": "O2"}], "products": [{"formula": "Fe2O3"}]}},
        {"id": "A011-N2", "kind": "normal", "input": {"reactants": [{"formula": "C2H6"}, {"formula": "O2"}], "products": [{"formula": "CO2"}, {"formula": "H2O"}]}},
        {"id": "A011-N3", "kind": "normal", "input": {"reactants": [{"formula": "KMnO4"}, {"formula": "HCl"}], "products": [{"formula": "KCl"}, {"formula": "MnCl2"}, {"formula": "H2O"}, {"formula": "Cl2"}]}},
        {"id": "A011-N4", "kind": "normal", "input": {"reactants": [{"formula": "Ag", "charge": 1}, {"formula": "Cl", "charge": -1}], "products": [{"formula": "AgCl", "charge": 0}], "include_charge_balance": True}},
        {"id": "A011-B1", "kind": "boundary", "input": {"reactants": [{"formula": "C"}, {"formula": "O2"}], "products": [{"formula": "CO2"}]}},
        {"id": "A011-F1", "kind": "failure", "input": {"reactants": [{"formula": "C"}, {"formula": "O2"}], "products": [{"formula": "CO"}, {"formula": "CO2"}]}},
        {"id": "A011-F2", "kind": "failure", "input": {"reactants": [{"formula": "Fe"}], "products": [{"formula": "Cu"}]}},
        {"id": "A011-F3", "kind": "failure", "input": {"reactants": [{"formula": "Ag", "charge": 1}, {"formula": "Cl"}], "products": [{"formula": "AgCl", "charge": 0}], "include_charge_balance": True}},
    ]

    @staticmethod
    def _parse_species(raw: Any, side: str, max_denominator: int, include_charge: bool):
        if not isinstance(raw, list) or not 1 <= len(raw) <= 20:
            return None, f"{side}必须包含1到20个物种"
        parsed = []
        for index, item in enumerate(raw):
            if not isinstance(item, dict) or set(item) - {"formula", "charge"}:
                return None, f"{side}[{index}]必须是仅含formula和可选charge的对象"
            formula = item.get("formula")
            details, error = parse_formula_details(formula)
            if error:
                return None, f"{side}[{index}]: {error}"
            elements: dict[str, Fraction] = {}
            for element, raw_count in details["elements"].items():
                if not math.isfinite(float(raw_count)) or not float(raw_count).is_integer():
                    return None, f"{side}[{index}]含非整数元素计量数，超出当前适用域"
                count = Fraction(str(raw_count)).limit_denominator(max_denominator)
                if count.denominator > max_denominator:
                    return None, f"{side}[{index}]计量数分母超过max_denominator"
                elements[element] = count
            if include_charge and "charge" not in item:
                return None, f"{side}[{index}].charge在启用电荷守恒时必须显式提供"
            charge = item.get("charge", 0)
            if include_charge and (isinstance(charge, bool) or not isinstance(charge, int)):
                return None, f"{side}[{index}].charge必须是整数"
            parsed.append({"formula": details["formula_display"], "elements": elements, "charge": int(charge) if include_charge else 0})
        return parsed, None

    def invoke(self, params: dict, context=None) -> ModelResult:
        raw_limit = params.get("max_denominator", 10000)
        if isinstance(raw_limit, bool):
            return fail("max_denominator必须是1到1000000之间的整数")
        try:
            max_denominator = int(raw_limit)
        except (TypeError, ValueError, OverflowError):
            return fail("max_denominator必须是1到1000000之间的整数")
        if max_denominator != raw_limit or not 1 <= max_denominator <= 1_000_000:
            return fail("max_denominator必须是1到1000000之间的整数")
        include_charge = params.get("include_charge_balance", False)
        if not isinstance(include_charge, bool):
            return fail("include_charge_balance必须是布尔值")
        reactants, error = self._parse_species(params.get("reactants"), "reactants", max_denominator, include_charge)
        if error:
            return fail(error, "MODEL_NOT_APPLICABLE" if "非整数" in error else "INVALID_INPUT")
        products, error = self._parse_species(params.get("products"), "products", max_denominator, include_charge)
        if error:
            return fail(error, "MODEL_NOT_APPLICABLE" if "非整数" in error else "INVALID_INPUT")

        left_elements = set().union(*(item["elements"] for item in reactants))
        right_elements = set().union(*(item["elements"] for item in products))
        if left_elements != right_elements:
            missing_left = sorted(right_elements - left_elements)
            missing_right = sorted(left_elements - right_elements)
            return fail(f"反应两侧元素集合不同；仅生成物侧={missing_left}，仅反应物侧={missing_right}", "REACTION_NOT_BALANCED")

        species = reactants + products
        signs = [Fraction(1)] * len(reactants) + [Fraction(-1)] * len(products)
        matrix = [
            [sign * item["elements"].get(element, Fraction(0)) for sign, item in zip(signs, species)]
            for element in sorted(left_elements)
        ]
        if include_charge:
            matrix.append([sign * item["charge"] for sign, item in zip(signs, species)])
        vector, nullity = _rref_null_vector(matrix)
        if vector is None:
            return fail(f"守恒矩阵零空间维数为{nullity}，不能确定唯一反应计量系数", "MODEL_NOT_APPLICABLE")
        if any(value == 0 for value in vector) or not (all(value > 0 for value in vector) or all(value < 0 for value in vector)):
            return fail("唯一零空间解不包含所有物种的同号非零系数", "MODEL_NOT_APPLICABLE")
        if all(value < 0 for value in vector):
            vector = [-value for value in vector]

        denominator_lcm = reduce(_lcm, (value.denominator for value in vector), 1)
        if denominator_lcm > max_denominator:
            return fail("零空间整数化分母超过max_denominator", "NUMERICAL_ERROR")
        coefficients = [int(value * denominator_lcm) for value in vector]
        common = reduce(gcd, coefficients)
        coefficients = [value // common for value in coefficients]

        reactant_coefficients = coefficients[:len(reactants)]
        product_coefficients = coefficients[len(reactants):]
        residuals = {}
        for row_index, element in enumerate(sorted(left_elements)):
            residuals[element] = int(sum(matrix[row_index][column] * coefficients[column] for column in range(len(coefficients))))
        charge_residual = None
        if include_charge:
            charge_residual = int(sum(matrix[-1][column] * coefficients[column] for column in range(len(coefficients))))
        passed = all(value == 0 for value in residuals.values()) and (charge_residual in {None, 0})
        if not passed:
            return fail("整数化后守恒复算未闭合", "NUMERICAL_ERROR")

        left = " + ".join(_coefficient_text(value, item["formula"]) for value, item in zip(reactant_coefficients, reactants))
        right = " + ".join(_coefficient_text(value, item["formula"]) for value, item in zip(product_coefficients, products))
        warnings = []
        if all(value == 1 for value in coefficients):
            warnings.append(BoundaryWarning("coefficients", "全部最简计量系数均为1，处于单位系数边界"))
        return ModelResult(True, result={
            "reactant_coefficients": reactant_coefficients,
            "product_coefficients": product_coefficients,
            "balanced_reaction": f"{left} -> {right}",
            "element_residuals": residuals,
            "charge_residual": charge_residual,
            "nullity": nullity,
            "gcd_is_one": reduce(gcd, coefficients) == 1,
            "passed": passed,
            "algorithm_version": "exact-rational-rref-v1",
        }, boundary_check=BoundaryCheck(not warnings, warnings))
