"""Run goal-oriented, cross-tool runtime checks through the HTTP tool API.

This is an engineering integration audit.  It is deliberately separate from
the qualification cases and from any model-evaluation dataset: every scenario
uses newly selected inputs, calls the real registered HTTP tools, and checks a
scientific identity, conservation closure, model-overlap identity, or expected
process trend.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path
from typing import Any, Callable


TOOLS_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = TOOLS_ROOT.parent


def http_json(url: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        method="GET" if payload is None else "POST",
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    try:
        with urllib.request.urlopen(request, timeout=240) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {body}") from exc


def compact(value: Any, depth: int = 0) -> Any:
    if depth >= 2:
        if isinstance(value, dict):
            return f"<object:{len(value)}>"
        if isinstance(value, list):
            return f"<array:{len(value)}>"
        return value
    if isinstance(value, dict):
        preview = {key: compact(item, depth + 1) for key, item in list(value.items())[:8]}
        if len(value) > 8:
            preview["…"] = f"另{len(value) - 8}项"
        return preview
    if isinstance(value, list):
        return {"count": len(value), "first": compact(value[0], depth + 1) if value else None}
    if isinstance(value, float):
        return float(f"{value:.10g}")
    return value


class GoalContext:
    def __init__(self, base_url: str, tool_names: dict[str, str]):
        self.base_url = base_url.rstrip("/")
        self.tool_names = tool_names
        self.calls: list[dict[str, Any]] = []
        self.checks: list[dict[str, Any]] = []

    def call(self, model_code: str, arguments: dict[str, Any], label: str) -> tuple[dict[str, Any], dict[str, Any]]:
        tool_name = self.tool_names[model_code]
        response = http_json(
            f"{self.base_url}/api/v1/tools/{tool_name}/call",
            {"arguments": arguments},
        )
        record = {
            "label": label,
            "model_code": model_code,
            "tool_name": tool_name,
            "input": arguments,
            "status": response.get("status"),
            "execution_id": response.get("execution_id"),
            "error_code": response.get("error_code"),
            "error": response.get("error"),
            "output": response.get("output"),
            "actual_data_records": response.get("actual_data_records", []),
            "boundary_check": response.get("boundary_check"),
            "expected_status": "success",
            "outcome_matches_expectation": response.get("status") == "success",
        }
        self.calls.append(record)
        if response.get("status") != "success" or not isinstance(response.get("output"), dict):
            raise RuntimeError(
                f"{model_code}调用失败: {response.get('error_code')} {response.get('error')}"
            )
        return response["output"], response

    def expect_rejection(
        self,
        model_code: str,
        arguments: dict[str, Any],
        label: str,
        expected_error_code: str,
    ) -> dict[str, Any]:
        tool_name = self.tool_names[model_code]
        response = http_json(
            f"{self.base_url}/api/v1/tools/{tool_name}/call",
            {"arguments": arguments},
        )
        matches = response.get("status") != "success" and response.get("error_code") == expected_error_code
        self.calls.append({
            "label": label,
            "model_code": model_code,
            "tool_name": tool_name,
            "input": arguments,
            "status": response.get("status"),
            "execution_id": response.get("execution_id"),
            "error_code": response.get("error_code"),
            "error": response.get("error"),
            "output": response.get("output"),
            "actual_data_records": response.get("actual_data_records", []),
            "boundary_check": response.get("boundary_check"),
            "expected_status": "rejected",
            "expected_error_code": expected_error_code,
            "outcome_matches_expectation": matches,
        })
        if not matches:
            raise RuntimeError(
                f"{model_code}预期{expected_error_code}拒绝，实际为"
                f"{response.get('status')}/{response.get('error_code')}"
            )
        return response

    def check(
        self,
        name: str,
        passed: bool,
        *,
        actual: Any = None,
        expected: Any = None,
        tolerance: Any = None,
    ) -> None:
        self.checks.append({
            "name": name,
            "passed": bool(passed),
            "actual": actual,
            "expected": expected,
            "tolerance": tolerance,
        })

    def close(self, goal_id: str, title: str, target: str, metrics: dict[str, Any]) -> dict[str, Any]:
        return {
            "goal_id": goal_id,
            "title": title,
            "target": target,
            "passed": bool(self.calls) and all(call["outcome_matches_expectation"] for call in self.calls)
            and bool(self.checks) and all(check["passed"] for check in self.checks),
            "call_count": len(self.calls),
            "tools": sorted({call["model_code"] for call in self.calls}),
            "metrics": metrics,
            "checks": self.checks,
            "calls": self.calls,
        }


def close(a: float, b: float, *, rel: float = 1e-9, abs_: float = 1e-9) -> bool:
    return math.isclose(float(a), float(b), rel_tol=rel, abs_tol=abs_)


def goal_chemistry(ctx: GoalContext) -> dict[str, Any]:
    species = ([{"formula": "Ca"}, {"formula": "O2"}], [{"formula": "CaO"}])
    solved, _ = ctx.call("A011", {"reactants": species[0], "products": species[1]}, "求Ca氧化反应最小整数系数")
    validated, _ = ctx.call("A006", {"reaction": solved["balanced_reaction"]}, "独立校验A011输出反应式")
    masses = {}
    for formula in ("Ca", "O2", "CaO"):
        output, _ = ctx.call("A003", {"formula": formula}, f"计算{formula}摩尔质量")
        masses[formula] = output["molar_mass_g_per_mol"]
    reactant_mass = solved["reactant_coefficients"][0] * masses["Ca"] + solved["reactant_coefficients"][1] * masses["O2"]
    product_mass = solved["product_coefficients"][0] * masses["CaO"]
    ctx.check("A011给出最简且守恒的2Ca+O2=2CaO", solved["passed"] and solved["gcd_is_one"] and solved["reactant_coefficients"] == [2, 1] and solved["product_coefficients"] == [2], actual=solved["balanced_reaction"], expected="2 Ca + O2 -> 2 CaO")
    ctx.check("A006逐元素残差为零", validated["balanced"] and all(abs(value) < 1e-12 for value in validated["element_residuals"].values()), actual=validated["element_residuals"], expected={"Ca": 0, "O": 0}, tolerance=1e-12)
    ctx.check("基于A003摩尔质量的反应两侧质量闭合", close(reactant_mass, product_mass, abs_=1e-9), actual=reactant_mass-product_mass, expected=0.0, tolerance="1e-9 g/mol-reaction")
    return ctx.close("GOAL-01", "反应配平与质量闭合", "从未配平方程得到最小整数系数，并独立验证元素与质量守恒", {"reaction": solved["balanced_reaction"], "reactant_mass_g_per_mol_reaction": reactant_mass, "product_mass_g_per_mol_reaction": product_mass, "mass_residual_g_per_mol_reaction": reactant_mass-product_mass})


def goal_thermodynamics(ctx: GoalContext) -> dict[str, Any]:
    reaction = "Fe₂O₃ + 2Al → 2Fe + Al₂O₃"
    temperature = 973.0
    h, _ = ctx.call("B006", {"reaction": reaction, "temperature": temperature}, "取反应焓")
    s, _ = ctx.call("B007", {"reaction": reaction, "temperature": temperature}, "取反应熵")
    g, _ = ctx.call("B008", {"reaction": reaction, "temperature": temperature}, "组合计算Gibbs能")
    k, _ = ctx.call("B009", {"reaction": reaction, "temperature": temperature}, "由Gibbs能计算平衡常数")
    expected_g = h["delta_H"] - temperature * s["delta_S"] / 1000.0
    expected_ln_k = -expected_g * 1000.0 / (8.31446261815324 * temperature)
    ctx.check("B008分量与B006/B007完全一致", close(g["delta_H"], h["delta_H"]) and close(g["delta_S"], s["delta_S"]), actual={"B008_H": g["delta_H"], "B008_S": g["delta_S"]}, expected={"B006_H": h["delta_H"], "B007_S": s["delta_S"]})
    ctx.check("ΔG=ΔH-TΔS", close(g["delta_G"], expected_g, abs_=1e-10), actual=g["delta_G"], expected=expected_g, tolerance="1e-10 kJ/mol-reaction")
    ctx.check("lnK=-ΔG/(RT)", close(k["ln_K"], expected_ln_k, rel=1e-10, abs_=1e-10), actual=k["ln_K"], expected=expected_ln_k, tolerance="1e-10")
    ctx.check("B009使用的ΔG与B008一致", close(k["delta_G"], g["delta_G"], abs_=1e-10), actual=k["delta_G"], expected=g["delta_G"], tolerance="1e-10 kJ/mol-reaction")
    return ctx.close("GOAL-02", "热力学状态函数闭合", "在973 K贯通反应焓、熵、Gibbs能和平衡常数", {"temperature_k": temperature, "delta_h_kj_mol_reaction": h["delta_H"], "delta_s_j_mol_reaction_k": s["delta_S"], "delta_g_kj_mol_reaction": g["delta_G"], "ln_k": k["ln_K"], "equilibrium_constant": k["K"]})


def goal_solution_models(ctx: GoalContext) -> dict[str, Any]:
    arguments = {"compositions": {"Fe": 0.64, "C": 0.36}, "temperature": 1725.0}
    ideal, _ = ctx.call("B014", arguments, "理想溶液基准")
    regular, _ = ctx.call("B015", {**arguments, "omega_j_mol": 0.0}, "正则溶液Ω=0退化")
    max_activity_delta = max(abs(ideal["activities"][name]-regular["activities"][name]) for name in ideal["activities"])
    ctx.check("Ω=0时两模型活度完全相同", max_activity_delta < 1e-12, actual=max_activity_delta, expected=0.0, tolerance=1e-12)
    ctx.check("Ω=0时全部活度系数为1", all(close(value, 1.0, abs_=1e-12) for value in regular["activity_coefficients"].values()), actual=regular["activity_coefficients"], expected={"Fe": 1.0, "C": 1.0}, tolerance=1e-12)
    ctx.check("Ω=0时超额Gibbs能为零且混合Gibbs能等于理想值", close(regular["excess_gibbs_j_mol"], 0.0, abs_=1e-12) and close(regular["mixing_gibbs_j_mol"], ideal["ideal_mixing_gibbs_j_mol"], abs_=1e-9), actual={"Gex": regular["excess_gibbs_j_mol"], "Gmix": regular["mixing_gibbs_j_mol"]}, expected={"Gex": 0.0, "Gmix": ideal["ideal_mixing_gibbs_j_mol"]})
    return ctx.close("GOAL-03", "溶液模型退化关系", "验证正则溶液在Ω=0时严格退化为理想溶液", {"activities": regular["activities"], "activity_coefficients": regular["activity_coefficients"], "ideal_mixing_gibbs_j_mol": ideal["ideal_mixing_gibbs_j_mol"], "excess_gibbs_j_mol": regular["excess_gibbs_j_mol"]})


def goal_diffusion(ctx: GoalContext) -> dict[str, Any]:
    diffusion, _ = ctx.call("C002", {"D0": 2.5e-6, "Q": 135.0, "temperature": 1150.0, "Q_unit": "kJ/mol"}, "计算1150 K扩散系数")
    d_value = diffusion["D"]
    time_s = 14400.0
    scale = 2.0 * math.sqrt(d_value*time_s)
    positions = [0.0, 0.5*scale, scale, 3.0*scale]
    fick, _ = ctx.call("C003", {"diffusion_coefficient": d_value, "initial_concentration": 0.2, "surface_concentration": 0.8, "time_s": time_s, "positions_m": positions}, "将C002输出传入Fick解析解")
    concentrations = [point["concentration"] for point in fick["profile"]]
    expected_flux = 0.6 * math.sqrt(d_value/(math.pi*time_s))
    ctx.check("C003特征深度等于2√Dt", close(fick["characteristic_depth_2sqrt_dt"], scale, rel=1e-12, abs_=1e-15), actual=fick["characteristic_depth_2sqrt_dt"], expected=scale, tolerance="1e-12 relative")
    ctx.check("表面浓度严格等于给定Cs", close(concentrations[0], 0.8, abs_=1e-12), actual=concentrations[0], expected=0.8, tolerance=1e-12)
    ctx.check("浓度从表面向内部单调趋近初始值", all(a >= b for a, b in zip(concentrations, concentrations[1:])) and abs(concentrations[-1]-0.2) < 2e-5, actual=concentrations, expected="单调下降且末点距0.2小于2e-5")
    ctx.check("表面通量与独立公式一致", close(fick["surface_flux"], expected_flux, rel=1e-12, abs_=1e-18), actual=fick["surface_flux"], expected=expected_flux, tolerance="1e-12 relative")
    return ctx.close("GOAL-04", "Arrhenius扩散到Fick剖面", "以C002结果驱动C003，并验证相似解的边界、单调性和通量", {"diffusion_coefficient_m2_s": d_value, "characteristic_depth_m": scale, "positions_m": positions, "concentrations": concentrations, "surface_flux": fick["surface_flux"]})


def goal_conduction_overlap(ctx: GoalContext) -> dict[str, Any]:
    base = {"thermal_conductivity": 45.0, "thickness": 0.075, "area": 1.8, "hot_temperature": 1250.0, "cold_temperature": 325.0}
    plane, _ = ctx.call("T001", base, "均质平板解析解")
    network, _ = ctx.call("T004", {"layers": [{"name": "single_plate", "thickness_m": base["thickness"], "conductivity_w_m_k": base["thermal_conductivity"]}], "area_m2": base["area"], "hot_boundary_temperature_k": base["hot_temperature"], "cold_boundary_temperature_k": base["cold_temperature"]}, "同一平板作为单层热阻网络")
    ctx.check("T004单层热流率与T001完全一致", close(network["heat_rate_w"], plane["heat_rate_w"], rel=1e-12, abs_=1e-9), actual=network["heat_rate_w"], expected=plane["heat_rate_w"], tolerance="1e-12 relative")
    ctx.check("T004单层热阻与T001完全一致", close(network["total_thermal_resistance_k_w"], plane["thermal_resistance_k_per_w"], rel=1e-12, abs_=1e-15), actual=network["total_thermal_resistance_k_w"], expected=plane["thermal_resistance_k_per_w"], tolerance="1e-12 relative")
    ctx.check("T004温降闭合残差近零", abs(network["closure_residual_k"]) < 1e-9, actual=network["closure_residual_k"], expected=0.0, tolerance="1e-9 K")
    return ctx.close("GOAL-05", "单层导热模型交叉验证", "用同一物理案例验证T004退化为T001", {"heat_rate_w": plane["heat_rate_w"], "heat_flux_w_m2": plane["heat_flux_w_m2"], "thermal_resistance_k_w": plane["thermal_resistance_k_per_w"], "network_closure_residual_k": network["closure_residual_k"]})


def goal_bof_heat_chain(ctx: GoalContext) -> dict[str, Any]:
    oxygen, _ = ctx.call("D001", {"metal_inputs": [{"name": "controlled carbon source", "mass_kg": 18.0165, "composition": {"C": 1.0}}], "target_steel_mass_kg": 0.000001, "target_composition": {"C": 0.0}, "carbon_to_co2_fraction": 1.0, "oxygen_utilization": 0.92}, "计算1.5 kmol碳完全氧化耗氧")
    reaction, _ = ctx.call("B006", {"reaction": "C + O₂ → CO₂", "temperature": 1773.0}, "取得碳完全氧化反应焓")
    conduction, _ = ctx.call("T001", {"thermal_conductivity": 2.0, "thickness": 0.18, "area": 4.0, "hot_temperature": 1800.0, "cold_temperature": 350.0}, "估算炉壁导热损失率")
    radiation, _ = ctx.call("T002", {"emitter_temperature": 1800.0, "surroundings_temperature": 350.0, "emissivity": 0.75, "area": 4.0, "view_factor": 1.0}, "估算炉口辐射损失率")
    carbon_reaction_kmol = oxygen["element_oxygen_breakdown"]["C"]["oxygen_kmol"]
    reaction_heat_kj = -reaction["delta_H"] * carbon_reaction_kmol * 1000.0
    exposure_s = 60.0
    heat_loss_kj = (conduction["heat_rate_w"] + radiation["net_radiation_w"]) * exposure_s / 1000.0
    balance, _ = ctx.call("D002", {"hot_metal_mass_kg": 1100.0, "hot_metal_temperature_k": 1773.0, "scrap_mass_kg": 180.0, "scrap_temperature_k": 298.15, "reaction_heat_kj": reaction_heat_kj, "heat_loss_kj": heat_loss_kj, "solve_for": "final_temperature"}, "将反应放热和两项热损送入BOF静态热平衡")
    ctx.check("D001受控碳源耗氧为1.5 kmol O2", close(oxygen["theoretical_oxygen_kmol"], 1.5, rel=1e-10, abs_=1e-10), actual=oxygen["theoretical_oxygen_kmol"], expected=1.5, tolerance="1e-10 kmol")
    ctx.check("供氧量等于理论量除以利用率", close(oxygen["supplied_oxygen_kmol"], oxygen["theoretical_oxygen_kmol"]/0.92, rel=1e-12), actual=oxygen["supplied_oxygen_kmol"], expected=oxygen["theoretical_oxygen_kmol"]/0.92)
    ctx.check("D002接收的反应热与上游计算一致", close(balance["reaction_heat_kj"], reaction_heat_kj, rel=1e-12), actual=balance["reaction_heat_kj"], expected=reaction_heat_kj)
    ctx.check("D002接收的热损与T001+T002积分一致", close(balance["heat_loss_kj"], heat_loss_kj, rel=1e-12), actual=balance["heat_loss_kj"], expected=heat_loss_kj)
    ctx.check("BOF终态能量严格闭合", abs(balance["energy_closure_error_kj"]) < 1e-6, actual=balance["energy_closure_error_kj"], expected=0.0, tolerance="1e-6 kJ")
    return ctx.close("GOAL-06", "BOF氧量—反应热—热损—终温链", "把D001、B006、T001和T002的结果组合成D002真实输入", {"theoretical_oxygen_kmol": oxygen["theoretical_oxygen_kmol"], "supplied_oxygen_nm3": oxygen["supplied_oxygen_normal_volume_m3"], "reaction_heat_kj": reaction_heat_kj, "conduction_loss_rate_w": conduction["heat_rate_w"], "radiation_loss_rate_w": radiation["net_radiation_w"], "integrated_heat_loss_kj": heat_loss_kj, "final_temperature_k": balance["final_temperature_k"], "energy_closure_error_kj": balance["energy_closure_error_kj"]})


def goal_bf_gas(ctx: GoalContext) -> dict[str, Any]:
    top_gas, _ = ctx.call("E010", {"bosh_gas_kmol": {"CO": 3.0, "H2": 0.8, "N2": 4.2}, "reduced_ore_oxygen_kmol": 1.8, "direct_reduction_fraction": 0.4, "hydrogen_share_of_indirect_reduction": 0.25, "additional_top_gas_kmol": {"N2": 0.25}}, "计算新的理论炉顶煤气")
    utilization, _ = ctx.call("E011", {"composition_basis": "mole_fraction", "composition_scope": "full_gas", "gas_samples": [{"time_s": 0.0, "composition": top_gas["wet_mole_fractions"]}]}, "由E010湿基组成独立复算CO/H2利用率")
    ctx.check("E010 C/O/H/N原子账闭合", top_gas["passed"] and max(abs(value) for value in top_gas["atom_balance_residuals_kmol"].values()) < 1e-9, actual=top_gas["atom_balance_residuals_kmol"], expected={"C": 0, "O": 0, "H": 0, "N": 0}, tolerance="1e-9 kmol atoms")
    ctx.check("湿基摩尔分数归一", close(sum(top_gas["wet_mole_fractions"].values()), 1.0, abs_=1e-12), actual=sum(top_gas["wet_mole_fractions"].values()), expected=1.0, tolerance=1e-12)
    ctx.check("E011复算CO利用率与E010一致", close(utilization["latest_co_utilization_fraction"], top_gas["co_utilization_fraction"], rel=1e-12, abs_=1e-12), actual=utilization["latest_co_utilization_fraction"], expected=top_gas["co_utilization_fraction"], tolerance=1e-12)
    ctx.check("E011复算H2利用率与E010一致", close(utilization["latest_h2_utilization_fraction"], top_gas["h2_utilization_fraction"], rel=1e-12, abs_=1e-12), actual=utilization["latest_h2_utilization_fraction"], expected=top_gas["h2_utilization_fraction"], tolerance=1e-12)
    return ctx.close("GOAL-07", "高炉理论煤气到利用率复算", "由元素守恒生成炉顶气，再把组成交给独立利用率工具", {"wet_total_gas_kmol": top_gas["wet_total_gas_kmol"], "wet_mole_fractions": top_gas["wet_mole_fractions"], "co_utilization_fraction": top_gas["co_utilization_fraction"], "h2_utilization_fraction": top_gas["h2_utilization_fraction"], "atom_balance_residuals_kmol": top_gas["atom_balance_residuals_kmol"]})


def goal_casting(ctx: GoalContext) -> dict[str, Any]:
    liquidus, response = ctx.call("F001", {"composition_wt_percent": {"C": 0.18, "Mn": 1.2, "Si": 0.25}, "grid_step_k": 5.0}, "CALPHAD计算新钢种液相线")
    steel_temperature = liquidus["liquidus_temperature_k"] + 45.0
    superheat, _ = ctx.call("F003", {"steel_temperature": steel_temperature, "liquidus_temperature": liquidus["liquidus_temperature_k"], "temperature_unit": "K", "liquidus_source": "F001", "upstream_execution_id": response["execution_id"], "evaluate_limits": True, "minimum_superheat_k": 25.0, "maximum_superheat_k": 65.0}, "把F001液相线和执行编号传入过热度工具")
    ctx.check("F003精确消费F001液相线", close(superheat["liquidus_temperature_k"], liquidus["liquidus_temperature_k"], abs_=1e-12), actual=superheat["liquidus_temperature_k"], expected=liquidus["liquidus_temperature_k"])
    ctx.check("设定钢液温度产生45 K过热度", close(superheat["superheat_k"], 45.0, abs_=1e-12), actual=superheat["superheat_k"], expected=45.0, tolerance="1e-12 K")
    ctx.check("45 K位于25–65 K目标窗", superheat["limit_status"] == "within_range", actual=superheat["limit_status"], expected="within_range")
    return ctx.close("GOAL-08", "CALPHAD液相线到连铸过热度", "为新钢种求液相线，并设定45 K目标过热度运行下游工具", {"composition_wt_percent": liquidus["composition_wt_percent"], "liquidus_temperature_k": liquidus["liquidus_temperature_k"], "solidus_temperature_k": liquidus["solidus_temperature_k"], "steel_temperature_k": steel_temperature, "superheat_k": superheat["superheat_k"], "limit_status": superheat["limit_status"], "upstream_execution_id": response["execution_id"]})


def goal_pde(ctx: GoalContext) -> dict[str, Any]:
    mesh, _ = ctx.call("G001", {"domain_lengths_m": {"x": 0.1}, "resolution_drivers": [{"name": "thermal_layer", "characteristic_length_m": 0.025, "minimum_cells": 5}], "refinement_ratio": 2.0}, "按最小热层分辨率生成网格计划")
    dx = mesh["recommended_cell_size_m"]
    alpha = 1.0e-5
    generic_step = 1.0
    generic_stability, _ = ctx.call("G002", {"cell_sizes_m": [dx], "time_step_s": generic_step, "advection_scheme": "none", "diffusion_scheme": "explicit_central", "diffusivity_components_m2_s": [alpha]}, "用G002默认Fo上限校验通用内部节点")
    node_count = int(round(0.1/dx))
    common = {"length_m": 0.1, "node_count": node_count, "density_kg_m3": 1000.0, "specific_heat_j_kg_k": 1000.0, "thermal_conductivity_w_m_k": 10.0, "left_boundary_type": "dirichlet", "left_boundary_temperature_k": 1000.0, "right_boundary_type": "dirichlet", "right_boundary_temperature_k": 300.0}
    boundary_rejection = ctx.expect_rejection("G003", {**common, "duration_s": 10.0, "time_step_s": generic_step, "initial_condition_mode": "uniform", "initial_temperature_k": 650.0}, "验证G003对Dirichlet边界采用更严格3Fo判据", "OUT_OF_DOMAIN")
    time_step = 0.5
    stability, _ = ctx.call("G002", {"cell_sizes_m": [dx], "time_step_s": time_step, "advection_scheme": "none", "diffusion_scheme": "explicit_central", "diffusivity_components_m2_s": [alpha], "target_fourier": 1.0/3.0}, "按G003 Dirichlet边界要求设置Fo上限1/3")
    closure_rejection = ctx.expect_rejection("G003", {**common, "duration_s": 10.0, "time_step_s": time_step, "initial_condition_mode": "uniform", "initial_temperature_k": 650.0}, "复现稳定对称瞬态的近零净能量容差误拒绝", "NUMERICAL_ERROR")
    steady_profile = [1000.0-700.0*((index+0.5)/node_count) for index in range(node_count)]
    pde, _ = ctx.call("G003", {**common, "duration_s": 10.0, "time_step_s": time_step, "initial_condition_mode": "profile", "initial_temperature_profile_k": steady_profile}, "用精确稳态剖面运行G003正常路径")
    steady, _ = ctx.call("T001", {"thermal_conductivity": 10.0, "thickness": 0.1, "area": 1.0, "hot_temperature": 1000.0, "cold_temperature": 300.0}, "用稳态解析工具作为PDE终态参照")
    ctx.check("G001网格尺度满足目标0.005 m", close(dx, 0.005, abs_=1e-12) and node_count == 20, actual={"dx_m": dx, "nodes": node_count}, expected={"dx_m": 0.005, "nodes": 20})
    ctx.check("G002默认Fo上限会判定dt=1 s稳定", generic_stability["stable"] and close(generic_stability["maximum_stable_time_step_s"], 1.25), actual={"stable": generic_stability["stable"], "maximum_dt_s": generic_stability["maximum_stable_time_step_s"]}, expected={"stable": True, "maximum_dt_s": 1.25})
    ctx.check("G003明确拒绝同一dt=1 s的Dirichlet边界离散", boundary_rejection["error_code"] == "OUT_OF_DOMAIN" and "0.833333" in boundary_rejection["error"], actual={"error_code": boundary_rejection["error_code"], "error": boundary_rejection["error"]}, expected="OUT_OF_DOMAIN and maximum dt 0.833333 s")
    ctx.check("G002使用边界特定Fo上限1/3后与G003最大步长一致", stability["stable"] and close(stability["maximum_stable_time_step_s"], 5.0/6.0, rel=1e-12), actual={"stable": stability["stable"], "Fourier": stability["total_diffusion_fourier"], "maximum_dt_s": stability["maximum_stable_time_step_s"]}, expected={"stable": True, "maximum_dt_s": 5.0/6.0})
    ctx.check("已复现G003近零净能量容差误拒绝", closure_rejection["error_code"] == "NUMERICAL_ERROR" and "能量闭合" in closure_rejection["error"], actual={"error_code": closure_rejection["error_code"], "error": closure_rejection["error"]}, expected="NUMERICAL_ERROR for near-zero net-energy scale")
    relative_flux_error = abs(pde["final_left_heat_flux_into_domain_w_m2"]-steady["heat_flux_w_m2"])/abs(steady["heat_flux_w_m2"])
    ctx.check("G003精确稳态热流等于T001解析解", relative_flux_error < 1e-12, actual=pde["final_left_heat_flux_into_domain_w_m2"], expected=steady["heat_flux_w_m2"], tolerance="1e-12 relative")
    ctx.check("G003能量闭合", abs(pde["energy_closure_relative"]) < 1e-9, actual=pde["energy_closure_relative"], expected=0.0, tolerance=1e-9)
    return ctx.close("GOAL-09", "网格—步长—PDE—稳态解析解", "先显式暴露G002/G003边界判据差异与近零净能量容差问题，再用适配的稳定步长和精确稳态剖面完成正常运行", {"recommended_cell_size_m": dx, "node_count": node_count, "generic_g002_maximum_dt_s": generic_stability["maximum_stable_time_step_s"], "g003_dirichlet_maximum_dt_s": 5.0/6.0, "adapted_time_step_s": time_step, "adapted_diffusion_fourier": stability["total_diffusion_fourier"], "pde_final_left_heat_flux_w_m2": pde["final_left_heat_flux_into_domain_w_m2"], "steady_heat_flux_w_m2": steady["heat_flux_w_m2"], "relative_flux_error": relative_flux_error, "energy_closure_relative": pde["energy_closure_relative"], "known_issue": "stable symmetric transient is falsely rejected by near-zero net-energy relative scale"})


def goal_analysis(ctx: GoalContext) -> dict[str, Any]:
    base = {"thermal_conductivity": 32.0, "thickness": 0.12, "area": 1.4, "hot_temperature": 1250.0, "cold_temperature": 350.0}
    plane, _ = ctx.call("T001", base, "敏感性与优化的物理基准")
    sensitivity, _ = ctx.call("G009", {"target_model_code": "T001", "base_arguments": base, "output_path": "heat_rate_w", "parameter_steps": [{"path": "thermal_conductivity", "label": "导热系数", "unit": "W/(m*K)", "absolute_step": 0.2}, {"path": "area", "label": "面积", "unit": "m2", "absolute_step": 0.01}]}, "对T001执行局部敏感性分析")
    results = {item["path"]: item for item in sensitivity["parameter_results"]}
    expected_dk = base["area"]*(base["hot_temperature"]-base["cold_temperature"])/base["thickness"]
    expected_da = base["thermal_conductivity"]*(base["hot_temperature"]-base["cold_temperature"])/base["thickness"]
    optimization, _ = ctx.call("G011", {"target_model_code": "T001", "base_params": base, "variables": [{"path": "thermal_conductivity", "lower_bound": 12.0, "upper_bound": 75.0}, {"path": "area", "lower_bound": 0.5, "upper_bound": 2.2}], "objective_output_path": "heat_rate_w", "objective_sense": "maximize", "constraints": [], "initial_samples": 6, "evaluation_budget": 10, "seed": 19, "expected_improvement_xi": 0.01, "allow_boundary_warning": False}, "在新边界内最大化T001热流率")
    expected_best = 75.0*2.2*(base["hot_temperature"]-base["cold_temperature"])/base["thickness"]
    ctx.check("G009基准输出与直接T001调用一致", close(sensitivity["baseline_output_value"], plane["heat_rate_w"], rel=1e-12), actual=sensitivity["baseline_output_value"], expected=plane["heat_rate_w"])
    ctx.check("G009导热系数一阶导数与解析式一致", close(results["thermal_conductivity"]["first_derivative"], expected_dk, rel=1e-10), actual=results["thermal_conductivity"]["first_derivative"], expected=expected_dk, tolerance="1e-10 relative")
    ctx.check("G009面积一阶导数与解析式一致", close(results["area"]["first_derivative"], expected_da, rel=1e-10), actual=results["area"]["first_derivative"], expected=expected_da, tolerance="1e-10 relative")
    ctx.check("G011找到单调目标的上边界最优点", close(optimization["best_parameters"]["thermal_conductivity"], 75.0, abs_=1e-12) and close(optimization["best_parameters"]["area"], 2.2, abs_=1e-12), actual=optimization["best_parameters"], expected={"thermal_conductivity": 75.0, "area": 2.2})
    ctx.check("G011最优目标值与T001解析式一致", close(optimization["best_objective_value"], expected_best, rel=1e-12), actual=optimization["best_objective_value"], expected=expected_best, tolerance="1e-12 relative")
    return ctx.close("GOAL-10", "注册工具敏感性与优化", "对新的T001工况验证数值导数，并搜索可解析验证的单调最优点", {"baseline_heat_rate_w": plane["heat_rate_w"], "derivative_w_per_k_w_m_k": results["thermal_conductivity"]["first_derivative"], "derivative_w_per_m2": results["area"]["first_derivative"], "best_parameters": optimization["best_parameters"], "best_heat_rate_w": optimization["best_objective_value"], "evaluation_count": optimization["evaluation_count"]})


def goal_ladle(ctx: GoalContext) -> dict[str, Any]:
    sulfur_low, _ = ctx.call("H002", {"steel_mass_kg": 95000.0, "slag_mass_kg": 2600.0, "initial_steel_sulfur_mass_fraction": 0.00028, "initial_slag_sulfur_mass_fraction": 0.0015, "sulfur_partition_ratio": 40.0}, "较低硫分配比平衡")
    sulfur_high, _ = ctx.call("H002", {"steel_mass_kg": 95000.0, "slag_mass_kg": 2600.0, "initial_steel_sulfur_mass_fraction": 0.00028, "initial_slag_sulfur_mass_fraction": 0.0015, "sulfur_partition_ratio": 160.0}, "较高硫分配比平衡")
    mixing_low, _ = ctx.call("H003", {"steel_temperature_k": 1850.0, "steel_mass_t": 120.0, "argon_flow_nm3_min": 0.8, "injection_depth_m": 3.2, "surface_pressure_pa": 101325.0, "plug_count": 1}, "低氩流量均混时间")
    mixing_high, _ = ctx.call("H003", {"steel_temperature_k": 1850.0, "steel_mass_t": 120.0, "argon_flow_nm3_min": 1.6, "injection_depth_m": 3.2, "surface_pressure_pa": 101325.0, "plug_count": 1}, "高氩流量均混时间")
    ctx.check("两组脱硫结果均质量闭合", abs(sulfur_low["total_sulfur_balance_residual_kg"]) < 1e-9 and abs(sulfur_high["total_sulfur_balance_residual_kg"]) < 1e-9, actual={"L40": sulfur_low["total_sulfur_balance_residual_kg"], "L160": sulfur_high["total_sulfur_balance_residual_kg"]}, expected=0.0, tolerance="1e-9 kg")
    ctx.check("提高硫分配比降低平衡钢中硫", sulfur_high["equilibrium_steel_sulfur_mass_fraction"] < sulfur_low["equilibrium_steel_sulfur_mass_fraction"], actual={"L40": sulfur_low["equilibrium_steel_sulfur_mass_fraction"], "L160": sulfur_high["equilibrium_steel_sulfur_mass_fraction"]}, expected="L160 < L40")
    ctx.check("提高氩流量增加比搅拌功", mixing_high["specific_stirring_power_w_t"] > mixing_low["specific_stirring_power_w_t"], actual={"0.8 Nm3/min": mixing_low["specific_stirring_power_w_t"], "1.6 Nm3/min": mixing_high["specific_stirring_power_w_t"]}, expected="high > low")
    ctx.check("提高氩流量缩短均混时间", mixing_high["mixing_time_s"] < mixing_low["mixing_time_s"], actual={"0.8 Nm3/min": mixing_low["mixing_time_s"], "1.6 Nm3/min": mixing_high["mixing_time_s"]}, expected="high-flow time < low-flow time")
    return ctx.close("GOAL-11", "钢包脱硫与氩搅拌趋势", "用成对新工况验证脱硫分配与均混时间的物理趋势和守恒", {"steel_sulfur_fraction_at_L40": sulfur_low["equilibrium_steel_sulfur_mass_fraction"], "steel_sulfur_fraction_at_L160": sulfur_high["equilibrium_steel_sulfur_mass_fraction"], "mixing_time_s_at_0_8_nm3_min": mixing_low["mixing_time_s"], "mixing_time_s_at_1_6_nm3_min": mixing_high["mixing_time_s"]})


GOALS: list[Callable[[GoalContext], dict[str, Any]]] = [
    goal_chemistry,
    goal_thermodynamics,
    goal_solution_models,
    goal_diffusion,
    goal_conduction_overlap,
    goal_bof_heat_chain,
    goal_bf_gas,
    goal_casting,
    goal_pde,
    goal_analysis,
    goal_ladle,
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=os.environ.get("METALLURGY_MODELS_BASE_URL"))
    parser.add_argument("--output-dir", default=str(PROJECT_ROOT / "outputs" / "tool_runtime_cross_audit_20260903"))
    args = parser.parse_args()
    if not args.base_url:
        parser.error("必须提供 --base-url 或 METALLURGY_MODELS_BASE_URL")
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest = http_json(f"{args.base_url.rstrip('/')}/api/v1/tools")
    tool_names = {entry["model_code"]: entry["function"]["name"] for entry in manifest["tools"]}
    rows = []
    for function in GOALS:
        context = GoalContext(args.base_url, tool_names)
        try:
            row = function(context)
        except Exception as exc:  # retain a goal-local failure and continue the remaining audit
            row = {
                "goal_id": function.__name__,
                "title": function.__name__,
                "target": "目标执行中断",
                "passed": False,
                "call_count": len(context.calls),
                "tools": sorted({call["model_code"] for call in context.calls}),
                "metrics": {},
                "checks": context.checks,
                "calls": context.calls,
                "error": f"{type(exc).__name__}: {exc}",
            }
        rows.append(row)

    passed = sum(row["passed"] for row in rows)
    total_calls = sum(row["call_count"] for row in rows)
    unique_tools = sorted({code for row in rows for code in row["tools"]})
    report = {
        "report_type": "goal_oriented_cross_tool_runtime_audit",
        "not_a_research_dataset": True,
        "external_llm_api_used": False,
        "date": str(date.today()),
        "base_url": args.base_url,
        "registered_count": manifest.get("registered_count"),
        "qualified_executable_count": manifest.get("qualified_executable_count"),
        "goal_count": len(rows),
        "passed_goal_count": passed,
        "failed_goal_count": len(rows)-passed,
        "http_call_count": total_calls,
        "unique_tool_count": len(unique_tools),
        "unique_tools": unique_tools,
        "known_issue_count": 2,
        "known_issues": [
            {
                "id": "G002-G003-BOUNDARY-CONTRACT",
                "severity": "contract_gap",
                "summary": "G002默认Fo上限0.5不能直接证明G003单元中心Dirichlet边界稳定；该边界需target_fourier=1/3。",
            },
            {
                "id": "G003-NEAR-ZERO-ENERGY-SCALE",
                "severity": "implementation_defect",
                "summary": "G003在对称等量进出热、净储能接近零时用净量构造相对误差尺度，可将约2.06e-9 J/m2舍入残差误判为NUMERICAL_ERROR。",
            },
        ],
        "goals": rows,
    }
    json_path = output_dir / "目标驱动跨工具运行审计.json"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8")

    lines = [
        "# 目标驱动跨工具运行审计",
        "",
        f"日期：{date.today()}",
        "",
        "性质：工程集成审计，不是正式研究数据集；未调用外部大模型 API。",
        "",
        f"汇总：{passed}/{len(rows)} 个目标按预期通过，共执行 {total_calls} 次真实 HTTP 工具调用，涉及 {len(unique_tools)} 个不同工具。",
        "",
        "每个目标均采用不同于工具准入案例的新输入，完整输入、完整输出、执行编号、数据来源与逐项断言见同目录 JSON。",
        "",
        "注意：目标内包含2项预期拒绝探针，确认了G002/G003边界判据契约差异和G003近零净能量容差缺陷；目标通过不代表这两项问题已修复。",
        "",
        "## 目标结果",
        "",
        "| 目标 | 工具链 | 具体输出 | 校验结论 |",
        "| --- | --- | --- | --- |",
    ]
    for row in rows:
        metrics = json.dumps(compact(row.get("metrics", {})), ensure_ascii=False, separators=(",", ":")).replace("|", "\\|")
        if len(metrics) > 700:
            metrics = metrics[:697]+"…"
        failed_checks = [check["name"] for check in row.get("checks", []) if not check["passed"]]
        conclusion = "通过" if row["passed"] else ("失败："+"；".join(failed_checks) if failed_checks else row.get("error", "调用失败"))
        escaped_conclusion = conclusion.replace("|", "\\|")
        tool_chain = " -> ".join(row["tools"])
        lines.append(f"| {row['goal_id']} {row['title']} | {tool_chain} | `{metrics}` | {escaped_conclusion} |")
    lines.extend(["", "## 逐目标调用与断言", ""])
    for row in rows:
        lines.extend([f"### {row['goal_id']} {row['title']}", "", row["target"], "", "调用输出：", ""])
        for call in row.get("calls", []):
            shown = call.get("output") if call.get("output") is not None else {"error_code": call.get("error_code"), "error": call.get("error")}
            output_text = json.dumps(compact(shown), ensure_ascii=False, separators=(",", ":"))
            expectation = "成功" if call.get("expected_status") == "success" else f"预期拒绝/{call.get('expected_error_code')}"
            lines.append(f"- {call['model_code']}（{call['label']}，{expectation}）：`{output_text}`；execution_id=`{call.get('execution_id')}`")
        lines.extend(["", "断言：", ""])
        for check in row.get("checks", []):
            actual = json.dumps(compact(check.get("actual")), ensure_ascii=False, separators=(",", ":"))
            expected = json.dumps(compact(check.get("expected")), ensure_ascii=False, separators=(",", ":"))
            lines.append(f"- {'通过' if check['passed'] else '失败'}：{check['name']}；实际 `{actual}`；期望 `{expected}`")
        if row.get("error"):
            lines.extend(["", f"错误：`{row['error']}`"])
        lines.append("")
    md_path = output_dir / "目标驱动跨工具运行审计.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps({"goals": len(rows), "passed": passed, "failed": len(rows)-passed, "http_calls": total_calls, "unique_tools": len(unique_tools), "json": str(json_path), "markdown": str(md_path)}, ensure_ascii=False, indent=2))
    return 0 if passed == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
