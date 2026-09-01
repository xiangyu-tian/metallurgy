"""P1-W13 additive melt-viscosity tool; existing tools remain frozen."""

from __future__ import annotations

import math
from typing import Any

from .base import BaseModelTool, BoundaryCheck, BoundaryWarning, InputField, ModelResult, OutputField
from .repositories.reference_repository import RepositoryError, atomic_weights
from .repositories.viscosity_repository import approved_model


DATASET_ID = "DS_MELT_VISCOSITY_W13"
MODEL_IDS = ["URBAIN_SLAG_1981", "HIRAI_LIQUID_ALLOY_1993"]


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


class C008_MeltViscosity(BaseModelTool):
    model_id, name, version = "C008", "熔渣/液态金属黏度估算", "1.0.0"
    tool_name = "metallurgy_estimate_melt_viscosity"
    scenario = "动力学与传递"
    priority = "P1"
    status = qualification_status = "qualified"
    count_eligible = True
    model_type = "版本化公开经验关联式"
    description = (
        "从批准的PostgreSQL模型定义读取Urbain全液态四元渣或Hirai液态金属关联式，"
        "返回动力黏度、中间参数和适用域诊断。"
    )
    applicable_boundary = (
        "URBAIN_SLAG_1981仅适用于1400–2000 K的全液态SiO2-Al2O3-CaO-MgO渣；"
        "HIRAI_LIQUID_ALLOY_1993要求同一合金基准的密度、液相线和平均摩尔质量，且Tm≤T≤1.5Tm。"
        "不处理含固相渣、非牛顿流变、在线测量或本地回归。"
    )
    data_source = [
        "Urbain et al. slag-viscosity model",
        "Vargas et al. 2001 equation transcription",
        "Hirai 1993 liquid-alloy viscosity equation",
    ]
    source_version = "MELT-VISCOSITY-CORRELATIONS-W13-V1"
    formula_reference = (
        "Urbain: eta=A*T*exp(1000*B/T), ln(A)=-11.57-0.29B; "
        "Hirai: eta=A*exp(B/RT), B=2.65*Tm^1.27, "
        "A=1.7e-7*rho^(2/3)*Tm^(1/2)*M^(-1/6)/exp(B/(R*Tm))"
    )
    source_records = [
        {
            "source_id": "URBAIN-SLAG-1987",
            "name": "Viscosity estimation of slags",
            "version": "Steel Research 58 (1987) 111-116",
            "url": "https://doi.org/10.1002/srin.198701513",
        },
        {
            "source_id": "HIRAI-ISIJ-1993",
            "name": "Estimation of Viscosities of Liquid Alloys",
            "version": "ISIJ International 33 (1993) 251-258",
            "url": "https://doi.org/10.2355/isijinternational.33.251",
        },
    ]
    failure_modes = [
        "数据库不可用、关联式未批准或温度超数据库记录范围",
        "Urbain组分缺失、多余、非正或质量百分数不闭合",
        "Hirai密度、液相线、平均摩尔质量缺失/非正或温度不在Tm至1.5Tm",
        "模型专用字段与correlation_id不匹配",
        "计算所得黏度或中间参数非有限",
    ]
    independent_validation = [
        "Urbain质量百分数到摩尔分数、alpha、B和A均由独立手算复核",
        "Urbain同成分下温度升高时黏度严格下降",
        "Hirai在T=Tm时重现其熔点Andrade表达式",
        "Hirai任意两温度黏度比满足解析Arrhenius关系",
    ]
    dependencies = ["A004"]
    relations = [
        rel("uses_convention_of", "A004", "C008要求输入质量百分数组成闭合；A004可作为上游归一化工具"),
        rel("complements", "B003", "B003积分显热，C008估算流动物性黏度"),
        rel("complements", "C009", "C009计算有效导热系数，C008计算动力黏度"),
        rel("complements", "B023", "B023判定相平衡；C008要求调用方确认处于关联式规定的全液态域"),
    ]
    data_requirement = "VERSIONED_DATABASE_CORRELATION"
    data_access_mode = "database_repository"
    required_dataset_ids = [DATASET_ID, "DS_IUPAC_AW_2021"]
    database_tables = [
        "metallurgy_v2.melt_viscosity_model_definition",
        "metallurgy_v2.element_reference",
    ]
    input_fields = [
        InputField("correlation_id", "关联式ID", "select", enum=MODEL_IDS),
        InputField("temperature_k", "温度", "number", unit="K", min_value=1e-12),
        InputField(
            "composition_wt_pct", "四元渣质量百分数组成", "object", required=False, unit="wt%",
            description="Urbain模式必填且只能包含SiO2、Al2O3、CaO、MgO，合计100 wt%",
        ),
        InputField("density_kg_m3", "液态合金密度", "number", required=False, unit="kg/m3", min_value=1e-12),
        InputField("liquidus_temperature_k", "液相线温度", "number", required=False, unit="K", min_value=1e-12),
        InputField("mean_molar_mass_kg_mol", "平均摩尔质量", "number", required=False, unit="kg/mol", min_value=1e-12),
        InputField(
            "relative_log_standard_uncertainty", "ln黏度相对标准不确定度", "number",
            required=False, unit="1", min_value=0, max_value=1,
            description="调用方给定时，以eta*exp(±1.96u)返回95%区间；工具不臆造模型误差",
        ),
    ]
    output_fields = [
        OutputField("correlation_id", "关联式ID", "string"),
        OutputField("material_kind", "材料类别", "string"),
        OutputField("temperature_k", "温度", "number", "K"),
        OutputField("dynamic_viscosity_pa_s", "动力黏度", "number", "Pa*s"),
        OutputField("ln_dynamic_viscosity", "动力黏度自然对数", "number", "1"),
        OutputField("d_ln_viscosity_d_temperature", "ln黏度温度导数", "number", "1/K"),
        OutputField("correlation_parameters", "计算中间参数", "object"),
        OutputField("relative_log_standard_uncertainty", "ln黏度相对标准不确定度", "number", "1", nullable=True),
        OutputField("confidence_interval_95_pa_s", "95%黏度区间", "array", "Pa*s", nullable=True),
        OutputField("dataset_id", "数据集ID", "string"),
        OutputField("source_version", "来源版本", "string"),
        OutputField("algorithm_version", "算法版本", "string"),
    ]
    validation_rules = [
        {"rule": "approved_database_model_and_temperature_domain"},
        {"rule": "urbain_exact_four_component_100_wt_pct_or_hirai_complete_property_triplet"},
        {"rule": "finite_positive_viscosity_and_model_specific_domain"},
    ]
    qualification_cases = [
        {
            "id": "C008-N1", "kind": "normal",
            "input": {"correlation_id": "URBAIN_SLAG_1981", "temperature_k": 1773.15,
                      "composition_wt_pct": {"SiO2": 40, "Al2O3": 15, "CaO": 35, "MgO": 10}},
        },
        {
            "id": "C008-N2", "kind": "normal",
            "input": {"correlation_id": "HIRAI_LIQUID_ALLOY_1993", "temperature_k": 1873.0,
                      "density_kg_m3": 7000, "liquidus_temperature_k": 1809.0,
                      "mean_molar_mass_kg_mol": 0.055845},
        },
        {
            "id": "C008-N3", "kind": "normal",
            "input": {"correlation_id": "HIRAI_LIQUID_ALLOY_1993", "temperature_k": 2000.0,
                      "density_kg_m3": 7400, "liquidus_temperature_k": 1700.0,
                      "mean_molar_mass_kg_mol": 0.052,
                      "relative_log_standard_uncertainty": 0.08},
        },
        {
            "id": "C008-B1", "kind": "boundary",
            "input": {"correlation_id": "HIRAI_LIQUID_ALLOY_1993", "temperature_k": 1809.0,
                      "density_kg_m3": 7000, "liquidus_temperature_k": 1809.0,
                      "mean_molar_mass_kg_mol": 0.055845},
        },
        {
            "id": "C008-F1", "kind": "failure",
            "input": {"correlation_id": "URBAIN_SLAG_1981", "temperature_k": 1773.15,
                      "composition_wt_pct": {"SiO2": 50, "Al2O3": 20, "CaO": 30}},
        },
        {
            "id": "C008-F2", "kind": "failure",
            "input": {"correlation_id": "HIRAI_LIQUID_ALLOY_1993", "temperature_k": 1700.0,
                      "density_kg_m3": 7000, "liquidus_temperature_k": 1809.0,
                      "mean_molar_mass_kg_mol": 0.055845},
        },
    ]
    data_qualification_cases = [
        {"id": "C008-D1", "input": qualification_cases[0]["input"]},
        {"id": "C008-D2", "input": qualification_cases[1]["input"]},
    ]

    @staticmethod
    def _uncertainty(params: dict[str, Any], viscosity: float) -> tuple[float | None, list[float] | None, str | None]:
        raw = params.get("relative_log_standard_uncertainty")
        if raw is None:
            return None, None, None
        uncertainty, error = finite(raw, "relative_log_standard_uncertainty")
        if error or not 0 <= uncertainty <= 1:
            return None, None, error or "relative_log_standard_uncertainty必须在0至1"
        factor = math.exp(1.96 * uncertainty)
        return uncertainty, [viscosity / factor, viscosity * factor], None

    @staticmethod
    def _strict_positive_optional(params: dict[str, Any], field: str) -> tuple[float | None, str | None]:
        if field not in params:
            return None, f"{field}在Hirai模式必填"
        value, error = finite(params[field], field)
        if error or value <= 0:
            return None, error or f"{field}必须大于0"
        return value, None

    def _urbain(self, params: dict[str, Any], row: dict[str, Any]) -> tuple[dict[str, Any] | None, list, str | None, str | None]:
        if any(field in params for field in ("density_kg_m3", "liquidus_temperature_k", "mean_molar_mass_kg_mol")):
            return None, [], "Urbain模式不得提交Hirai专用物性字段", "INVALID_INPUT"
        composition = params.get("composition_wt_pct")
        required = {"SiO2", "Al2O3", "CaO", "MgO"}
        if not isinstance(composition, dict) or set(composition) != required:
            return None, [], "Urbain模式组成必须且只能包含SiO2、Al2O3、CaO、MgO", "INVALID_INPUT"
        values: dict[str, float] = {}
        for component in sorted(required):
            value, error = finite(composition[component], f"composition_wt_pct.{component}")
            if error or value <= 0:
                return None, [], error or f"{component}质量百分数必须大于0", "INVALID_INPUT"
            values[component] = value
        tolerance = float(row["applicability"]["composition_sum_tolerance_wt_pct"])
        if abs(sum(values.values()) - 100.0) > tolerance:
            return None, [], f"四元渣质量百分数合计必须为100±{tolerance:g}", "MASS_BALANCE_VIOLATION"
        try:
            weights, provenance = atomic_weights(["Si", "O", "Al", "Ca", "Mg"])
        except RepositoryError as exc:
            return None, [], str(exc), exc.error_code
        molar_masses = {
            "SiO2": weights["Si"] + 2 * weights["O"],
            "Al2O3": 2 * weights["Al"] + 3 * weights["O"],
            "CaO": weights["Ca"] + weights["O"],
            "MgO": weights["Mg"] + weights["O"],
        }
        raw_moles = {component: values[component] / molar_masses[component] for component in required}
        total_moles = sum(raw_moles.values())
        mole_fractions = {component: raw_moles[component] / total_moles for component in sorted(required)}
        x_silica = mole_fractions["SiO2"]
        modifier = mole_fractions["CaO"] + mole_fractions["MgO"]
        amphoteric = mole_fractions["Al2O3"]
        alpha = modifier / (modifier + amphoteric)
        coefficients = row["parameters"]
        b_terms = []
        for key in ("b0", "b1", "b2", "b3"):
            c0, c1, c2 = (float(value) for value in coefficients[key])
            b_terms.append(c0 + c1 * alpha + c2 * alpha * alpha)
        b_value = sum(coefficient * x_silica ** power for power, coefficient in enumerate(b_terms))
        ln_a = float(coefficients["ln_a_intercept"]) + float(coefficients["ln_a_b_slope"]) * b_value
        temperature = float(params["temperature_k"])
        scale = float(coefficients["activation_scale_k"])
        ln_viscosity = ln_a + math.log(temperature) + scale * b_value / temperature
        viscosity = math.exp(ln_viscosity)
        derivative = 1.0 / temperature - scale * b_value / temperature ** 2
        result = {
            "viscosity": viscosity,
            "ln_viscosity": ln_viscosity,
            "derivative": derivative,
            "parameters": {
                "composition_wt_pct": values,
                "oxide_molar_masses_g_mol": molar_masses,
                "oxide_mole_fractions": mole_fractions,
                "glass_former_fraction": x_silica,
                "modifier_fraction": modifier,
                "amphoteric_fraction": amphoteric,
                "alpha": alpha,
                "b_polynomial_terms": b_terms,
                "B": b_value,
                "ln_A": ln_a,
                "A_pa_s_per_k": math.exp(ln_a),
            },
        }
        return result, provenance, None, None

    def _hirai(self, params: dict[str, Any], row: dict[str, Any]) -> tuple[dict[str, Any] | None, list, str | None, str | None, list[BoundaryWarning]]:
        if "composition_wt_pct" in params:
            return None, [], "Hirai模式不得提交Urbain专用组成字段", "INVALID_INPUT", []
        density, error = self._strict_positive_optional(params, "density_kg_m3")
        if error:
            return None, [], error, "INVALID_INPUT", []
        liquidus, error = self._strict_positive_optional(params, "liquidus_temperature_k")
        if error:
            return None, [], error, "INVALID_INPUT", []
        molar_mass, error = self._strict_positive_optional(params, "mean_molar_mass_kg_mol")
        if error:
            return None, [], error, "INVALID_INPUT", []
        domain = row["applicability"]
        if not float(domain["density_min_kg_m3"]) <= density <= float(domain["density_max_kg_m3"]):
            return None, [], "density_kg_m3超出批准适用域", "OUT_OF_DOMAIN", []
        if not float(domain["molar_mass_min_kg_mol"]) <= molar_mass <= float(domain["molar_mass_max_kg_mol"]):
            return None, [], "mean_molar_mass_kg_mol超出批准适用域", "OUT_OF_DOMAIN", []
        temperature = float(params["temperature_k"])
        ratio = temperature / liquidus
        ratio_min = float(domain["temperature_to_liquidus_ratio_min"])
        ratio_max = float(domain["temperature_to_liquidus_ratio_max"])
        if ratio < ratio_min - 1e-12 or ratio > ratio_max + 1e-12:
            return None, [], f"Hirai模式要求{ratio_min:g}≤T/Tm≤{ratio_max:g}", "OUT_OF_DOMAIN", []
        p = row["parameters"]
        gas_constant = float(p["gas_constant_j_mol_k"])
        activation = float(p["activation_factor"]) * liquidus ** float(p["liquidus_exponent"])
        ln_melting_viscosity = (
            math.log(float(p["universal_prefactor"]))
            + (2.0 / 3.0) * math.log(density)
            + 0.5 * math.log(liquidus)
            - (1.0 / 6.0) * math.log(molar_mass)
        )
        ln_a = ln_melting_viscosity - activation / (gas_constant * liquidus)
        ln_viscosity = ln_a + activation / (gas_constant * temperature)
        viscosity = math.exp(ln_viscosity)
        derivative = -activation / (gas_constant * temperature ** 2)
        warnings_out = []
        if abs(ratio - ratio_min) <= 1e-12 or abs(ratio - ratio_max) <= 1e-12:
            warnings_out.append(BoundaryWarning(
                "temperature_k", "温度位于Hirai相对液相线适用域边界",
                min_allowed=ratio_min * liquidus, max_allowed=ratio_max * liquidus,
            ))
        result = {
            "viscosity": viscosity,
            "ln_viscosity": ln_viscosity,
            "derivative": derivative,
            "parameters": {
                "density_kg_m3": density,
                "liquidus_temperature_k": liquidus,
                "mean_molar_mass_kg_mol": molar_mass,
                "temperature_to_liquidus_ratio": ratio,
                "activation_energy_j_mol": activation,
                "ln_A_pa_s": ln_a,
                "A_pa_s": math.exp(ln_a),
                "viscosity_at_liquidus_pa_s": math.exp(ln_melting_viscosity),
            },
        }
        return result, [], None, None, warnings_out

    def invoke(self, params: dict, context=None) -> ModelResult:
        errors = self.validate_input(params)
        if errors:
            return fail("；".join(errors))
        correlation_id = params.get("correlation_id")
        temperature, error = finite(params.get("temperature_k"), "temperature_k")
        if error or temperature <= 0:
            return fail(error or "temperature_k必须大于0")
        try:
            row, provenance = approved_model(correlation_id, temperature)
        except RepositoryError as exc:
            return fail(str(exc), exc.error_code)

        warnings_out: list[BoundaryWarning] = []
        if correlation_id == "URBAIN_SLAG_1981":
            calculation, extra_provenance, error, code = self._urbain(params, row)
        elif correlation_id == "HIRAI_LIQUID_ALLOY_1993":
            calculation, extra_provenance, error, code, warnings_out = self._hirai(params, row)
        else:
            return fail("correlation_id没有批准实现", "MISSING_DATA")
        if error:
            return fail(error, code or "INVALID_INPUT")
        viscosity = float(calculation["viscosity"])
        if not math.isfinite(viscosity) or viscosity <= 0:
            return fail("黏度计算结果非有限或非正", "NUMERICAL_ERROR")
        uncertainty, interval, error = self._uncertainty(params, viscosity)
        if error:
            return fail(error)
        output = {
            "correlation_id": correlation_id,
            "material_kind": str(row["material_kind"]),
            "temperature_k": temperature,
            "dynamic_viscosity_pa_s": viscosity,
            "ln_dynamic_viscosity": float(calculation["ln_viscosity"]),
            "d_ln_viscosity_d_temperature": float(calculation["derivative"]),
            "correlation_parameters": calculation["parameters"],
            "relative_log_standard_uncertainty": uncertainty,
            "confidence_interval_95_pa_s": interval,
            "dataset_id": str(row["dataset_id"]),
            "source_version": str(row["source_version"]),
            "algorithm_version": "c008-melt-viscosity-db-v1",
        }
        return ModelResult(
            True,
            result=output,
            boundary_check=BoundaryCheck(not warnings_out, warnings_out),
            provenance=[*provenance, *extra_provenance],
        )
