"""P1-W11 additive thermodynamic tools; all existing implementations stay frozen."""

from __future__ import annotations

import math
from typing import Any, Optional

import numpy as np

from .base import BaseModelTool, BoundaryCheck, BoundaryWarning, InputField, ModelResult, OutputField


R_J_MOL_K = 8.31446261815324


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


class W11ThermodynamicTool(BaseModelTool):
    scenario = "热力学与相平衡"
    priority = "P1"
    status = "qualified"
    qualification_status = "qualified"
    count_eligible = True
    data_requirement = "FORMULA_ONLY"
    data_access_mode = "none"


class B026_PengRobinsonPureFugacity(W11ThermodynamicTool):
    model_id, name, version = "B026", "Peng-Robinson状态方程与逸度", "1.0.0"
    tool_name = "metallurgy_calculate_peng_robinson_fugacity"
    description = "由显式临界温度、临界压力和偏心因子计算纯流体Peng-Robinson压缩因子、摩尔体积、逸度系数与逸度。"
    applicable_boundary = (
        "原始Peng-Robinson 1976纯组分EOS；0.3<=T/Tc<=5、P/Pc<=20、-0.5<=omega<=1.5。"
        "不处理混合规则、闪蒸、体积平移或全局相稳定性分析。"
    )
    data_source = ["Caller-supplied critical properties", "Peng-Robinson 1976 equation of state"]
    source_version = "peng-robinson-pure-fluid-1976-v1; R-CODATA-2018"
    formula_reference = (
        "kappa=0.37464+1.54226w-0.26992w^2; alpha=[1+kappa(1-sqrt(Tr))]^2; "
        "A=a*P/(R*T)^2; B=b*P/(R*T); Z^3-(1-B)Z^2+(A-3B^2-2B)Z-(AB-B^2-B^3)=0; "
        "ln(phi)=Z-1-ln(Z-B)-A/(2sqrt(2)B)ln[(Z+(1+sqrt(2))B)/(Z+(1-sqrt(2))B)]"
    )
    source_records = [
        {
            "source_id": "PENG-ROBINSON-1976",
            "name": "D.-Y. Peng and D. B. Robinson, A New Two-Constant Equation of State",
            "version": "Industrial & Engineering Chemistry Fundamentals 15(1), 59-64",
            "url": "https://doi.org/10.1021/i160057a011",
        },
        {"source_id": "CODATA-R-2018", "name": "Molar gas constant", "version": "2018 SI"},
    ]
    failure_modes = [
        "温度、压力或临界参数非正", "约化温度、约化压力或偏心因子超适用域", "不存在Z>B的物理解",
        "逸度系数对数项超出定义域", "三次方程或压力回代残差超限",
    ]
    independent_validation = [
        "所有返回实根代回PR三次方程", "选定摩尔体积代回压力形式EOS", "逸度满足f=phi*P",
        "低压极限Z和phi趋近1", "vapor/liquid分别选择最大/最小物理解",
    ]
    dependencies = []
    relations = [
        rel("overlaps", "B013", "都计算气体PVT；B013采用理想气体，本工具处理纯流体非理想性"),
        rel("complements", "B009", "B009给理想标准态平衡常数，本工具可为后续非理想反应商提供纯组分逸度系数"),
        rel("overlaps", "B027", "都涉及气液热力学；本工具输出单相EOS根，B027输出理想气液相边界"),
    ]
    input_fields = [
        InputField("temperature_k", "温度", "number", unit="K", min_value=1e-300),
        InputField("pressure_pa", "压力", "number", unit="Pa", min_value=1e-300),
        InputField("critical_temperature_k", "临界温度", "number", unit="K", min_value=1e-300),
        InputField("critical_pressure_pa", "临界压力", "number", unit="Pa", min_value=1e-300),
        InputField("acentric_factor", "偏心因子", "number", unit="1", min_value=-0.5, max_value=1.5),
        InputField("phase_root", "根选择", "select", enum=["vapor", "liquid", "stable"], description="vapor取最大根，liquid取最小根，stable取最低逸度根"),
    ]
    output_fields = [
        OutputField("compressibility_factor", "选定压缩因子", "number", "1"),
        OutputField("real_compressibility_roots", "物理实根", "array", "1"),
        OutputField("physical_root_count", "物理实根数", "number", "1"),
        OutputField("selected_root_kind", "选根结果", "string"),
        OutputField("molar_volume_m3_mol", "摩尔体积", "number", "m3/mol"),
        OutputField("fugacity_coefficient", "逸度系数", "number", "1"),
        OutputField("fugacity_pa", "逸度", "number", "Pa"),
        OutputField("reduced_temperature", "约化温度", "number", "1"),
        OutputField("reduced_pressure", "约化压力", "number", "1"),
        OutputField("a_dimensionless", "PR参数A", "number", "1"),
        OutputField("b_dimensionless", "PR参数B", "number", "1"),
        OutputField("selected_cubic_residual", "选定根三次方程残差", "number", "1"),
        OutputField("pressure_residual_pa", "压力形式EOS残差", "number", "Pa"),
        OutputField("model_version", "模型版本", "string"),
    ]
    validation_rules = [
        {"rule": "positive_temperature_pressure_and_critical_properties"},
        {"rule": "0.3<=T/Tc<=5_and_P/Pc<=20"},
        {"rule": "physical_root_requires_Z_above_B"},
        {"rule": "cubic_and_pressure_residual_closure"},
    ]
    qualification_cases = [
        {"id": "B026-N1", "kind": "normal", "input": {"temperature_k": 300, "pressure_pa": 5e6, "critical_temperature_k": 190.564, "critical_pressure_pa": 4.5992e6, "acentric_factor": 0.011, "phase_root": "vapor"}},
        {"id": "B026-N2", "kind": "normal", "input": {"temperature_k": 280, "pressure_pa": 5e6, "critical_temperature_k": 304.1282, "critical_pressure_pa": 7.3773e6, "acentric_factor": 0.22394, "phase_root": "liquid"}},
        {"id": "B026-N3", "kind": "normal", "input": {"temperature_k": 370, "pressure_pa": 2e6, "critical_temperature_k": 369.83, "critical_pressure_pa": 4.248e6, "acentric_factor": 0.152, "phase_root": "stable"}},
        {"id": "B026-B1", "kind": "boundary", "input": {"temperature_k": 300, "pressure_pa": 1, "critical_temperature_k": 190.564, "critical_pressure_pa": 4.5992e6, "acentric_factor": 0.011, "phase_root": "vapor"}},
        {"id": "B026-F1", "kind": "failure", "input": {"temperature_k": 50, "pressure_pa": 1e5, "critical_temperature_k": 190.564, "critical_pressure_pa": 4.5992e6, "acentric_factor": 0.011, "phase_root": "vapor"}},
        {"id": "B026-F2", "kind": "failure", "input": {"temperature_k": 300, "pressure_pa": 1e8, "critical_temperature_k": 190.564, "critical_pressure_pa": 4.5992e6, "acentric_factor": 0.011, "phase_root": "vapor"}},
    ]

    @staticmethod
    def _ln_phi(z_value: float, a_value: float, b_value: float) -> float:
        sqrt_two = math.sqrt(2.0)
        if z_value <= b_value:
            raise ValueError("Z必须大于B")
        upper = z_value + (1.0 + sqrt_two) * b_value
        lower = z_value + (1.0 - sqrt_two) * b_value
        if upper <= 0 or lower <= 0:
            raise ValueError("逸度系数对数比值超出定义域")
        attraction = a_value / (2.0 * sqrt_two * b_value) * math.log(upper / lower)
        return z_value - 1.0 - math.log(z_value - b_value) - attraction

    def invoke(self, params: dict, context=None) -> ModelResult:
        parsed = {}
        for key in ("temperature_k", "pressure_pa", "critical_temperature_k", "critical_pressure_pa"):
            value, error = finite(params.get(key), key, minimum=0, strict_minimum=True)
            if error:
                return fail(error)
            parsed[key] = value
        omega, error = finite(params.get("acentric_factor"), "acentric_factor", minimum=-0.5, maximum=1.5)
        if error:
            return fail(error)
        phase_root = params.get("phase_root")
        if phase_root not in {"vapor", "liquid", "stable"}:
            return fail("phase_root必须是vapor、liquid或stable")

        temperature = parsed["temperature_k"]
        pressure = parsed["pressure_pa"]
        critical_temperature = parsed["critical_temperature_k"]
        critical_pressure = parsed["critical_pressure_pa"]
        reduced_temperature = temperature / critical_temperature
        reduced_pressure = pressure / critical_pressure
        if not 0.3 <= reduced_temperature <= 5.0:
            return fail("约化温度必须位于[0.3,5]", "OUT_OF_DOMAIN")
        if reduced_pressure > 20.0:
            return fail("约化压力不能大于20", "OUT_OF_DOMAIN")

        kappa = 0.37464 + 1.54226 * omega - 0.26992 * omega * omega
        alpha = (1.0 + kappa * (1.0 - math.sqrt(reduced_temperature))) ** 2
        a_parameter = 0.45724 * R_J_MOL_K ** 2 * critical_temperature ** 2 / critical_pressure * alpha
        b_parameter = 0.07780 * R_J_MOL_K * critical_temperature / critical_pressure
        a_dimensionless = a_parameter * pressure / (R_J_MOL_K ** 2 * temperature ** 2)
        b_dimensionless = b_parameter * pressure / (R_J_MOL_K * temperature)
        coefficients = [
            1.0,
            -(1.0 - b_dimensionless),
            a_dimensionless - 3.0 * b_dimensionless ** 2 - 2.0 * b_dimensionless,
            -(a_dimensionless * b_dimensionless - b_dimensionless ** 2 - b_dimensionless ** 3),
        ]
        raw_roots = np.roots(coefficients)
        roots = sorted({
            round(float(root.real), 14)
            for root in raw_roots
            if abs(float(root.imag)) <= 1e-8 and float(root.real) > b_dimensionless * (1.0 + 1e-12)
        })
        if not roots:
            return fail("Peng-Robinson三次方程不存在Z>B的物理实根", "NUMERICAL_ERROR")
        try:
            root_records = [(root, self._ln_phi(root, a_dimensionless, b_dimensionless)) for root in roots]
        except (ValueError, OverflowError) as exc:
            return fail(str(exc), "NUMERICAL_ERROR")
        if phase_root == "vapor":
            selected_z, selected_ln_phi = max(root_records, key=lambda item: item[0])
            selected_kind = "vapor_maximum_root" if len(roots) > 1 else "single_physical_root"
        elif phase_root == "liquid":
            selected_z, selected_ln_phi = min(root_records, key=lambda item: item[0])
            selected_kind = "liquid_minimum_root" if len(roots) > 1 else "single_physical_root"
        else:
            selected_z, selected_ln_phi = min(root_records, key=lambda item: item[1])
            selected_kind = "minimum_fugacity_root" if len(roots) > 1 else "single_physical_root"
        fugacity_coefficient = math.exp(selected_ln_phi)
        fugacity = fugacity_coefficient * pressure
        molar_volume = selected_z * R_J_MOL_K * temperature / pressure
        cubic_residual = float(np.polyval(coefficients, selected_z))
        denominator = molar_volume * (molar_volume + b_parameter) + b_parameter * (molar_volume - b_parameter)
        if molar_volume <= b_parameter or denominator <= 0:
            return fail("选定摩尔体积不满足PR压力形式定义域", "NUMERICAL_ERROR")
        pressure_from_eos = (
            R_J_MOL_K * temperature / (molar_volume - b_parameter)
            - a_parameter / denominator
        )
        pressure_residual = pressure_from_eos - pressure
        if abs(cubic_residual) > 1e-8 or abs(pressure_residual) > max(1e-4, pressure * 1e-8):
            return fail("Peng-Robinson根或压力回代未数值闭合", "NUMERICAL_ERROR")
        warnings = []
        if reduced_pressure < 1e-6:
            warnings.append(BoundaryWarning("pressure_pa", "处于低压理想极限，Z和逸度系数应趋近1"))
        if abs(reduced_temperature - 1.0) < 1e-8:
            warnings.append(BoundaryWarning("temperature_k", "温度位于临界温度附近，根对数值扰动敏感"))
        return ModelResult(True, result={
            "compressibility_factor": selected_z,
            "real_compressibility_roots": roots,
            "physical_root_count": len(roots),
            "selected_root_kind": selected_kind,
            "molar_volume_m3_mol": molar_volume,
            "fugacity_coefficient": fugacity_coefficient,
            "fugacity_pa": fugacity,
            "reduced_temperature": reduced_temperature,
            "reduced_pressure": reduced_pressure,
            "a_dimensionless": a_dimensionless,
            "b_dimensionless": b_dimensionless,
            "selected_cubic_residual": cubic_residual,
            "pressure_residual_pa": pressure_residual,
            "model_version": "peng-robinson-pure-fluid-1976-v1",
        }, boundary_check=BoundaryCheck(not warnings, warnings))


_ANTOINE_COMPONENT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "name": {"type": "string"},
        "mole_fraction": {"type": "number", "minimum": 0, "maximum": 1},
        "antoine_a": {"type": "number"},
        "antoine_b": {"type": "number"},
        "antoine_c": {"type": "number"},
        "temperature_min_k": {"type": "number", "exclusiveMinimum": 0},
        "temperature_max_k": {"type": "number", "exclusiveMinimum": 0},
    },
    "required": ["name", "mole_fraction", "antoine_a", "antoine_b", "antoine_c", "temperature_min_k", "temperature_max_k"],
}


_WATER = {"name": "water", "mole_fraction": 0.4, "antoine_a": 7.19622, "antoine_b": 1730.63, "antoine_c": 233.426, "temperature_min_k": 273.15, "temperature_max_k": 373.15}
_ETHANOL = {"name": "ethanol", "mole_fraction": 0.6, "antoine_a": 7.32908, "antoine_b": 1642.89, "antoine_c": 230.300, "temperature_min_k": 273.15, "temperature_max_k": 351.47}


class B027_IdealVLEBubbleDew(W11ThermodynamicTool):
    model_id, name, version = "B027", "理想气液泡点与露点", "1.0.0"
    tool_name = "metallurgy_solve_ideal_vle_bubble_dew"
    description = "用调用方显式提供且带有效温区的Antoine系数，按Raoult-Dalton理想模型计算多组分泡点/露点温度或压力。"
    applicable_boundary = (
        "2至12组分、理想液相、理想气相、无化学反应；log10(Psat/kPa)=A-B/(T/°C+C)。"
        "所有组分系数必须覆盖计算温度，定压求根只在有效温区交集内进行。"
    )
    data_source = ["Caller-supplied Antoine coefficients with validity ranges", "Raoult and Dalton laws"]
    source_version = "ideal-vle-raoult-antoine-kpa-v1"
    formula_reference = (
        "log10(Psat/kPa)=A-B/(T_C+C); bubble P=sum(x_i Psat_i); "
        "dew 1/P=sum(y_i/Psat_i); K_i=Psat_i/P; bubble sum(x_i K_i)=1; dew sum(y_i/K_i)=1"
    )
    source_records = [
        {"source_id": "RAOULT-DALTON-IDEAL-VLE", "name": "Ideal vapor-liquid equilibrium from Raoult and Dalton laws", "version": "fixed equations v1"},
        {"source_id": "ANTOINE-EQUATION", "name": "Antoine vapor-pressure equation; coefficients supplied by caller", "version": "P in kPa, T in degC"},
    ]
    failure_modes = [
        "组分名重复、组分数超限或摩尔分数不闭合", "Antoine系数或有效温区非法", "指定温度不在全部有效温区内",
        "定压求根温区无交集或目标压力没有根", "Antoine指数溢出或求根不收敛", "模式所需温度/压力缺失或参数歧义",
    ]
    independent_validation = [
        "泡点回代sum(x_i K_i)=1", "露点回代sum(y_i/K_i)=1", "输出相组成和为1",
        "定温计算与对应定压反算温度一致", "纯组分极限下泡点与露点一致",
    ]
    dependencies = []
    relations = [
        rel("uses_model_of", "B014", "B014给理想液相活度a=x；本工具进一步求理想气液相边界"),
        rel("overlaps", "B026", "都涉及气液热力学；本工具使用理想逸度，B026计算纯流体非理想逸度"),
        rel("overlaps", "B019", "都输出相状态信息；B019给定相分数杠杆规则，本工具求泡露点边界"),
    ]
    input_fields = [
        InputField("mode", "计算模式", "select", enum=["bubble_pressure", "dew_pressure", "bubble_temperature", "dew_temperature"]),
        InputField("components", "组分、摩尔分数与Antoine系数", "array", items=_ANTOINE_COMPONENT_SCHEMA, min_items=2, max_items=12),
        InputField("temperature_k", "定温模式温度", "number", required=False, unit="K", min_value=1e-300),
        InputField("pressure_kpa", "定压模式压力", "number", required=False, unit="kPa", min_value=1e-300),
        InputField("temperature_tolerance_k", "定压求根温度容差", "number", required=False, default=1e-8, unit="K", min_value=1e-12, max_value=0.1),
        InputField("max_iterations", "最大二分迭代数", "number", required=False, default=200, unit="1", min_value=10, max_value=1000),
    ]
    output_fields = [
        OutputField("mode", "计算模式", "string"),
        OutputField("equilibrium_temperature_k", "泡点或露点温度", "number", "K"),
        OutputField("equilibrium_pressure_kpa", "泡点或露点压力", "number", "kPa"),
        OutputField("feed_phase", "给定组成所属相", "string"),
        OutputField("feed_mole_fractions", "给定相摩尔分数", "object", "1"),
        OutputField("equilibrium_mole_fractions", "另一平衡相摩尔分数", "object", "1"),
        OutputField("saturation_pressures_kpa", "各组分饱和蒸气压", "object", "kPa"),
        OutputField("k_values", "各组分K值", "object", "1"),
        OutputField("feed_composition_residual", "给定组成闭合残差", "number", "1"),
        OutputField("equilibrium_composition_residual", "另一相组成闭合残差", "number", "1"),
        OutputField("phase_equilibrium_residual", "泡露点方程残差", "number", "1"),
        OutputField("solver_iterations", "求根迭代数", "number", "1"),
        OutputField("model_version", "模型版本", "string"),
    ]
    validation_rules = [
        {"rule": "two_to_twelve_unique_components"},
        {"rule": "mole_fraction_sum_equals_one"},
        {"rule": "temperature_or_pressure_required_by_mode"},
        {"rule": "temperature_inside_all_Antoine_ranges"},
        {"rule": "bubble_or_dew_equation_closure"},
    ]
    qualification_cases = [
        {"id": "B027-N1", "kind": "normal", "input": {"mode": "bubble_pressure", "components": [_WATER, _ETHANOL], "temperature_k": 340}},
        {"id": "B027-N2", "kind": "normal", "input": {"mode": "dew_pressure", "components": [_WATER, _ETHANOL], "temperature_k": 340}},
        {"id": "B027-N3", "kind": "normal", "input": {"mode": "bubble_temperature", "components": [_WATER, _ETHANOL], "pressure_kpa": 70}},
        {"id": "B027-B1", "kind": "boundary", "input": {"mode": "bubble_pressure", "components": [{**_WATER, "mole_fraction": 1.0}, {**_ETHANOL, "mole_fraction": 0.0}], "temperature_k": 340}},
        {"id": "B027-F1", "kind": "failure", "input": {"mode": "bubble_pressure", "components": [{**_WATER, "mole_fraction": 0.7}, {**_ETHANOL, "mole_fraction": 0.7}], "temperature_k": 340}},
        {"id": "B027-F2", "kind": "failure", "input": {"mode": "dew_temperature", "components": [_WATER, _ETHANOL], "pressure_kpa": 5000}},
    ]

    @staticmethod
    def _parse_components(raw: Any):
        if not isinstance(raw, list) or not 2 <= len(raw) <= 12:
            return None, "components必须包含2至12个组分"
        parsed = []
        names = set()
        required = {"name", "mole_fraction", "antoine_a", "antoine_b", "antoine_c", "temperature_min_k", "temperature_max_k"}
        for index, item in enumerate(raw):
            if not isinstance(item, dict) or set(item) != required:
                return None, f"components[{index}]字段必须严格为{sorted(required)}"
            name = item.get("name")
            if not isinstance(name, str) or not name.strip():
                return None, f"components[{index}].name必须是非空字符串"
            name = name.strip()
            if name in names:
                return None, f"组分名重复: {name}"
            names.add(name)
            numbers = {}
            for key in required - {"name"}:
                value, error = finite(item.get(key), f"components[{index}].{key}")
                if error:
                    return None, error
                numbers[key] = value
            if not 0 <= numbers["mole_fraction"] <= 1:
                return None, f"components[{index}].mole_fraction必须位于[0,1]"
            if numbers["temperature_min_k"] <= 0 or numbers["temperature_max_k"] <= numbers["temperature_min_k"]:
                return None, f"components[{index}]有效温区必须为正且上界大于下界"
            parsed.append({"name": name, **numbers})
        total = sum(item["mole_fraction"] for item in parsed)
        if abs(total - 1.0) > 1e-10:
            return None, f"组分摩尔分数和必须为1，当前为{total:.12g}"
        for item in parsed:
            item["mole_fraction"] /= total
        return parsed, None

    @staticmethod
    def _psat(component: dict[str, float], temperature_k: float) -> float:
        temperature_c = temperature_k - 273.15
        denominator = temperature_c + component["antoine_c"]
        if abs(denominator) <= 1e-12:
            raise ValueError(f"{component['name']}的Antoine分母为0")
        exponent = component["antoine_a"] - component["antoine_b"] / denominator
        if not -300 <= exponent <= 300:
            raise ValueError(f"{component['name']}的Antoine指数超出稳定范围")
        pressure = 10.0 ** exponent
        if not math.isfinite(pressure) or pressure <= 0:
            raise ValueError(f"{component['name']}的饱和蒸气压不是正有限值")
        return pressure

    @classmethod
    def _evaluate_at_temperature(cls, components: list[dict], temperature_k: float) -> dict[str, float]:
        for component in components:
            if not component["temperature_min_k"] <= temperature_k <= component["temperature_max_k"]:
                raise ValueError(f"温度{temperature_k:g} K超出{component['name']}的Antoine有效温区")
        return {component["name"]: cls._psat(component, temperature_k) for component in components}

    @staticmethod
    def _bisection(function, lower: float, upper: float, tolerance: float, max_iterations: int):
        f_lower = function(lower)
        f_upper = function(upper)
        if abs(f_lower) <= 1e-12:
            return lower, 0, True
        if abs(f_upper) <= 1e-12:
            return upper, 0, True
        if f_lower * f_upper > 0:
            raise ValueError("指定压力在Antoine有效温区交集内没有泡点/露点根")
        for iteration in range(1, max_iterations + 1):
            midpoint = 0.5 * (lower + upper)
            f_mid = function(midpoint)
            if abs(f_mid) <= 1e-12 or upper - lower <= tolerance:
                return midpoint, iteration, False
            if f_lower * f_mid <= 0:
                upper = midpoint
                f_upper = f_mid
            else:
                lower = midpoint
                f_lower = f_mid
        raise RuntimeError("泡点/露点温度二分求根未在最大迭代数内收敛")

    def invoke(self, params: dict, context=None) -> ModelResult:
        mode = params.get("mode")
        if mode not in {"bubble_pressure", "dew_pressure", "bubble_temperature", "dew_temperature"}:
            return fail("mode不是支持的泡点/露点模式")
        components, error = self._parse_components(params.get("components"))
        if error:
            return fail(error)
        tolerance, error = finite(params.get("temperature_tolerance_k", 1e-8), "temperature_tolerance_k", minimum=1e-12, maximum=0.1)
        if error:
            return fail(error)
        max_iterations_value, error = finite(params.get("max_iterations", 200), "max_iterations", minimum=10, maximum=1000)
        if error or not float(max_iterations_value).is_integer():
            return fail(error or "max_iterations必须是整数")
        max_iterations = int(max_iterations_value)
        is_pressure_mode = mode.endswith("_pressure")
        if is_pressure_mode:
            if params.get("temperature_k") is None or params.get("pressure_kpa") is not None:
                return fail("定温泡/露点压力模式必须且只能提供temperature_k")
            temperature, error = finite(params.get("temperature_k"), "temperature_k", minimum=0, strict_minimum=True)
            if error:
                return fail(error)
            try:
                saturation = self._evaluate_at_temperature(components, temperature)
            except ValueError as exc:
                return fail(str(exc), "OUT_OF_DOMAIN")
            fractions = {item["name"]: item["mole_fraction"] for item in components}
            if mode == "bubble_pressure":
                pressure = sum(fractions[name] * saturation[name] for name in fractions)
                k_values = {name: saturation[name] / pressure for name in fractions}
                equilibrium = {name: fractions[name] * k_values[name] for name in fractions}
                phase_residual = sum(fractions[name] * k_values[name] for name in fractions) - 1.0
                feed_phase = "liquid"
            else:
                pressure = 1.0 / sum(fractions[name] / saturation[name] for name in fractions)
                k_values = {name: saturation[name] / pressure for name in fractions}
                equilibrium = {name: fractions[name] / k_values[name] for name in fractions}
                phase_residual = sum(fractions[name] / k_values[name] for name in fractions) - 1.0
                feed_phase = "vapor"
            iterations = 0
            endpoint = False
        else:
            if params.get("pressure_kpa") is None or params.get("temperature_k") is not None:
                return fail("定压泡/露点温度模式必须且只能提供pressure_kpa")
            pressure, error = finite(params.get("pressure_kpa"), "pressure_kpa", minimum=0, strict_minimum=True)
            if error:
                return fail(error)
            lower = max(item["temperature_min_k"] for item in components)
            upper = min(item["temperature_max_k"] for item in components)
            if lower >= upper:
                return fail("各组分Antoine有效温区没有公共交集", "OUT_OF_DOMAIN")
            fractions = {item["name"]: item["mole_fraction"] for item in components}

            def objective(temperature_value: float) -> float:
                psat = self._evaluate_at_temperature(components, temperature_value)
                if mode == "bubble_temperature":
                    return sum(fractions[name] * psat[name] for name in fractions) / pressure - 1.0
                return sum(fractions[name] * pressure / psat[name] for name in fractions) - 1.0

            try:
                temperature, iterations, endpoint = self._bisection(objective, lower, upper, tolerance, max_iterations)
                saturation = self._evaluate_at_temperature(components, temperature)
            except ValueError as exc:
                return fail(str(exc), "OUT_OF_DOMAIN")
            except RuntimeError as exc:
                return fail(str(exc), "NUMERICAL_ERROR")
            k_values = {name: saturation[name] / pressure for name in fractions}
            if mode == "bubble_temperature":
                equilibrium = {name: fractions[name] * k_values[name] for name in fractions}
                phase_residual = sum(fractions[name] * k_values[name] for name in fractions) - 1.0
                feed_phase = "liquid"
            else:
                equilibrium = {name: fractions[name] / k_values[name] for name in fractions}
                phase_residual = sum(fractions[name] / k_values[name] for name in fractions) - 1.0
                feed_phase = "vapor"

        equilibrium_sum = sum(equilibrium.values())
        if equilibrium_sum <= 0 or not math.isfinite(equilibrium_sum):
            return fail("平衡相组成无法归一", "NUMERICAL_ERROR")
        equilibrium = {name: value / equilibrium_sum for name, value in equilibrium.items()}
        composition_residual = sum(equilibrium.values()) - 1.0
        if abs(phase_residual) > 1e-8 or abs(composition_residual) > 1e-12:
            return fail("泡点/露点方程或组成未数值闭合", "NUMERICAL_ERROR")
        warnings = []
        if any(item["mole_fraction"] == 0 for item in components):
            warnings.append(BoundaryWarning("components", "至少一个组分摩尔分数为0，处于低维组成边界"))
        if endpoint:
            warnings.append(BoundaryWarning("components", "温度根位于Antoine有效温区边界"))
        return ModelResult(True, result={
            "mode": mode,
            "equilibrium_temperature_k": temperature,
            "equilibrium_pressure_kpa": pressure,
            "feed_phase": feed_phase,
            "feed_mole_fractions": fractions,
            "equilibrium_mole_fractions": equilibrium,
            "saturation_pressures_kpa": saturation,
            "k_values": k_values,
            "feed_composition_residual": sum(fractions.values()) - 1.0,
            "equilibrium_composition_residual": composition_residual,
            "phase_equilibrium_residual": phase_residual,
            "solver_iterations": iterations,
            "model_version": "ideal-vle-raoult-antoine-kpa-v1",
        }, boundary_check=BoundaryCheck(not warnings, warnings))
