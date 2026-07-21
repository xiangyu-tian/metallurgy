"""
B 系列模型：热力学与相平衡（首批）
B003 显热与焓积分
B006 反应焓计算
B008 反应 Gibbs 自由能计算
B009 平衡常数计算
B019 杠杆规则计算
"""
from __future__ import annotations
import math
from typing import Dict, List, Optional

from .base import (
    BaseModelTool, ModelResult, InputField, OutputField,
    BoundaryCheck, BoundaryWarning, InvocationContext, Provenance,
)
from .chemical_data import (
    THERMOCHEMICAL_DB, find_reaction, list_reactions,
    SHOMATE_PARAMS, calc_shomate,
)
from .repositories.thermodynamic_repository import repo


def _lookup_reaction(reaction_str: str, temperature: float = 298.15):
    """查反应热力学数据：数据库优先 → 内置兜底"""
    # 1. 数据库
    import psycopg2
    import json
    try:
        conn = psycopg2.connect(host='127.0.0.1', port=5432, database='metallurgy',
                                 user='postgres', password='', connect_timeout=2)
        cur = conn.cursor()
        cur.execute("""
            SELECT reaction_equation, name, reactants, products
            FROM metallurgy_v2.reaction_definition
            WHERE reaction_equation = %s
        """, (reaction_str,))
        row = cur.fetchone()
        if not row:
            cur.close(); conn.close()
            return find_reaction(reaction_str)

        reactant_data = row[2] if isinstance(row[2], (list, dict)) else json.loads(row[2])
        product_data = row[3] if isinstance(row[3], (list, dict)) else json.loads(row[3])

        lookup = {}
        for sp in reactant_data + product_data:
            name = sp['species']
            if name not in lookup:
                phase_suffix = {'s': '(s)', 'g': '(g)', 'l': '(l)'}.get(sp.get('phase', 's'), '(s)')
                full_name = name + phase_suffix
                # ΔHf° from thermodynamic_property
                cur.execute("SELECT value FROM metallurgy_v2.thermodynamic_property WHERE species = %s AND property_code = 'HF_STD' LIMIT 1",
                             (full_name,))
                r = cur.fetchone()
                hf = float(r[0]) if r else 0.0

                # S(T) from Shomate correlation via repo
                s_at_t = 0.0
                try:
                    # Build species name with phase for repo lookup
                    # repo's evaluate_shomate strips the phase suffix internally
                    eval_result = repo.evaluate_shomate(full_name, sp.get('phase', 's'), temperature)
                    if eval_result and 'entropy' in eval_result.results:
                        s_at_t = eval_result.results['entropy']['value']
                except Exception:
                    # Fallback: S°(298K) from database
                    cur.execute("SELECT value FROM metallurgy_v2.thermodynamic_property WHERE species = %s AND property_code = 'S_STD' AND ABS(temperature - 298.15) < 5 LIMIT 1",
                                 (full_name,))
                    r = cur.fetchone()
                    s_at_t = float(r[0]) if r else 0.0

                lookup[name] = (hf, s_at_t)

        dh = sum(float(p['coeff']) * lookup[p['species']][0] for p in product_data) \
             - sum(float(r['coeff']) * lookup[r['species']][0] for r in reactant_data)
        ds = sum(float(p['coeff']) * lookup[p['species']][1] for p in product_data) \
             - sum(float(r['coeff']) * lookup[r['species']][1] for r in reactant_data)
        cur.close(); conn.close()

        if abs(dh) > 0.01:
            return {'reaction': row[0], 'name': row[1], 'deltaH': round(dh, 1), 'deltaS': round(ds, 1), 'note': 'NIST-JANAF'}
    except Exception:
        pass

    # 2. 内置兜底
    return find_reaction(reaction_str)


# ── B003 显热与焓积分 ──

class B003_SensibleEnthalpy(BaseModelTool):
    model_id = "B003"
    name = "显热与焓积分"
    scenario = "热力学与相平衡"
    priority = "P0"
    version = "1.0.0"
    applicable_boundary = "温度范围受 Shomate 参数有效区间限制；不支持相变潜热"

    input_fields = [
        InputField("species", "物种", type="string", required=True,
                    placeholder="如 Fe(s), O2(g), CO2(g)"),
        InputField("temperature_start", "起始温度 (K)", type="number", required=True, default=298.15),
        InputField("temperature_end", "终止温度 (K)", type="number", required=True, default=1873),
        InputField("mass", "质量 (g)", type="number", required=False, default=1,
                    description="如果不为1，结果乘以该质量"),
    ]

    output_fields = [
        OutputField("delta_H", "焓变 (kJ)", type="number"),
        OutputField("temperature_start", "起始温度 (K)", type="number"),
        OutputField("temperature_end", "终止温度 (K)", type="number"),
        OutputField("species", "物种", type="string"),
    ]

    def invoke(self, params: dict, context: Optional[InvocationContext] = None) -> ModelResult:
        species = params["species"]
        t_start = float(params.get("temperature_start", 298.15))
        t_end = float(params.get("temperature_end", 1873))
        mass = float(params.get("mass", 1))

        # 通过 repo 计算起止温度的热力学性质
        phase = "solid" if "(s)" in species else "gas" if "(g)" in species else "liquid"
        r_start = repo.evaluate(species, phase, t_start)
        r_end = repo.evaluate(species, phase, t_end)

        if not r_start.results or not r_end.results:
            # 兜底：尝试 chemical_data.py Shomate
            shomate_t = SHOMATE_PARAMS.get(species)
            if not shomate_t:
                return ModelResult(success=False, error=f"无 {species} 的热力学数据", error_code="NO_DATA")
            if t_start < shomate_t["T_min"] or t_end > shomate_t["T_max"]:
                return ModelResult(success=False, error=f"温度范围超出 {species} 的有效区间", error_code="OUT_OF_RANGE")
            # 用化学数据兜底的 Shomate 积分
            import numpy as np
            temps = np.linspace(t_start, t_end, 1000)
            t_k = temps / 1000.0
            A, B, C, D, E = (shomate_t[k] for k in ["A","B","C","D","E"])
            Cp = A + B*t_k + C*t_k**2 + D*t_k**3 + E/t_k**2
            delta_H = float(np.trapz(Cp, temps) / 1000.0)  # J → kJ
            return ModelResult(
                success=True,
                result={"delta_H": round(delta_H * mass, 4), "delta_H_unit": "kJ",
                        "temperature_start": t_start, "temperature_end": t_end,
                        "species": species, "data_source": "builtin_fallback"},
                provenance=[Provenance(dataset_id="DS002", name="NIST-JANAF")],
            )

        # 用 repository 结果：H_end - H_start
        H_start = r_start.results.get("enthalpy", {}).get("value", 0)
        H_end = r_end.results.get("enthalpy", {}).get("value", 0)
        delta_H = (H_end - H_start) * mass

        return ModelResult(
            success=True,
            result={
                "delta_H": round(delta_H, 4),
                "delta_H_unit": "kJ",
                "temperature_start": t_start,
                "temperature_end": t_end,
                "species": species,
                "mass": mass,
                "mass_unit": "g",
                "method": "Shomate 积分（H_end - H_start）",
                "data_source": r_start.provenance.get("method", "database"),
            },
            provenance=[Provenance(dataset_id="DS002", name="NIST-JANAF")],
        )


# ── B006 反应焓计算 ──

class B006_ReactionEnthalpy(BaseModelTool):
    model_id = "B006"
    name = "反应焓计算"
    scenario = "热力学与相平衡"
    priority = "P0"
    version = "1.0.0"
    applicable_boundary = "使用标准生成焓数据；默认温度 298.15K"

    input_fields = [
        InputField("reaction", "反应式", type="string", required=True,
                    placeholder="如 FeO + C → Fe + CO"),
        InputField("temperature", "温度 (K)", type="number", required=False, default=298.15),
    ]

    output_fields = [
        OutputField("delta_H", "反应焓 ΔH (kJ/mol)", type="number"),
        OutputField("reaction", "反应式", type="string"),
        OutputField("reaction_type", "反应类型", type="string"),
    ]

    def invoke(self, params: dict, context: Optional[InvocationContext] = None) -> ModelResult:
        reaction = params["reaction"]
        temperature = float(params.get("temperature", 298.15))

        # 在内置数据库中查找
        entry = _lookup_reaction(reaction, temperature)
        if entry is None:
            return ModelResult(
                success=False,
                error=f"不支持的化学反应: {reaction}。支持的: {list_reactions()}",
                error_code="UNSUPPORTED_REACTION",
            )

        delta_H = entry["deltaH"]
        delta_S = entry["deltaS"]
        # ΔG = ΔH - T*ΔS/1000 (ΔS 单位 J/mol·K, ΔH 单位 kJ/mol)
        delta_G = delta_H - temperature * delta_S / 1000.0

        reaction_type = "放热反应" if delta_H < 0 else "吸热反应"

        warnings = []
        if temperature > 2000:
            warnings.append(BoundaryWarning(
                field="temperature", level="warning",
                message=f"温度 {temperature}K 超出多数冶金反应适用范围",
            ))

        return ModelResult(
            success=True,
            result={
                "delta_H": delta_H,
                "delta_H_unit": "kJ/mol",
                "delta_S": delta_S,
                "delta_S_unit": "J/(mol·K)",
                "delta_G": round(delta_G, 2),
                "delta_G_unit": "kJ/mol",
                "temperature": temperature,
                "reaction": entry["reaction"],
                "name": entry["name"],
                "reaction_type": reaction_type,
                "note": entry.get("note", ""),
            },
            boundary_check=BoundaryCheck(
                passed=len(warnings) == 0,
                warnings=warnings,
            ),
            provenance=[Provenance(dataset_id="DS002", name="NIST-JANAF")],
        )


# ── B008 反应 Gibbs 自由能计算 ──

class B008_ReactionGibbs(BaseModelTool):
    model_id = "B008"
    name = "反应 Gibbs 自由能计算"
    scenario = "热力学与相平衡"
    priority = "P0"
    version = "1.0.0"
    applicable_boundary = "使用标准生成焓/熵数据；ΔG = ΔH - TΔS"

    input_fields = [
        InputField("reaction", "反应式", type="string", required=True,
                    placeholder="如 2Fe + O2 → 2FeO"),
        InputField("temperature", "温度 (K)", type="number", required=False, default=1873),
        InputField("pressure", "压力 (Pa)", type="number", required=False, default=101325),
    ]

    output_fields = [
        OutputField("delta_G", "Gibbs自由能 (kJ/mol)", type="number"),
        OutputField("direction", "反应方向", type="string"),
        OutputField("reaction", "反应式", type="string"),
    ]

    def invoke(self, params: dict, context: Optional[InvocationContext] = None) -> ModelResult:
        reaction = params["reaction"]
        temperature = float(params.get("temperature", 298.15))

        entry = _lookup_reaction(reaction, temperature)
        if entry is None:
            return ModelResult(
                success=False,
                error=f"不支持的化学反应: {reaction}。支持的: {list_reactions()}",
                error_code="UNSUPPORTED_REACTION",
            )

        TK = temperature
        delta_H = entry["deltaH"]
        delta_S = entry["deltaS"]
        delta_G = delta_H - TK * delta_S / 1000.0

        # 反应方向判定
        if delta_G < -10:
            direction = "正向强烈自发"
        elif delta_G < 0:
            direction = "正向自发"
        elif delta_G < 10:
            direction = "逆向自发（需能量输入）"
        else:
            direction = "逆向强烈自发"

        # 分解温度特殊处理
        note = ""
        if "CaCO₃" in reaction or "CaCO3" in reaction:
            dec_K = delta_H / (delta_S / 1000.0)
            note = f"CaCO₃理论分解温度约 {dec_K - 273.15:.0f}°C"

        return ModelResult(
            success=True,
            result={
                "delta_G": round(delta_G, 2),
                "delta_G_unit": "kJ/mol",
                "delta_H": delta_H,
                "delta_H_unit": "kJ/mol",
                "delta_S": delta_S,
                "delta_S_unit": "J/(mol·K)",
                "temperature": temperature,
                "temperature_unit": "K",
                "reaction": entry["reaction"],
                "name": entry["name"],
                "direction": direction,
                "note": note,
            },
            provenance=[Provenance(dataset_id="DS002", name="NIST-JANAF")],
        )


# ── B009 平衡常数计算 ──

class B009_EquilibriumConstant(BaseModelTool):
    model_id = "B009"
    name = "平衡常数计算"
    scenario = "热力学与相平衡"
    priority = "P0"
    version = "1.0.0"
    applicable_boundary = "K = exp(-ΔG°/RT)；ΔG° 基于内置热化学数据库"

    input_fields = [
        InputField("reaction", "反应式", type="string", required=True,
                    placeholder="如 FeO + C → Fe + CO"),
        InputField("temperature", "温度 (K)", type="number", required=False, default=1600),
    ]

    output_fields = [
        OutputField("K", "平衡常数", type="number"),
        OutputField("delta_G", "Gibbs自由能 (kJ/mol)", type="number"),
        OutputField("direction", "反应方向", type="string"),
    ]

    def invoke(self, params: dict, context: Optional[InvocationContext] = None) -> ModelResult:
        reaction = params["reaction"]
        temperature = float(params.get("temperature", 1600))
        R = 8.314  # J/(mol·K)

        entry = _lookup_reaction(reaction, temperature)
        if entry is None:
            return ModelResult(
                success=False,
                error=f"不支持的化学反应: {reaction}",
                error_code="UNSUPPORTED_REACTION",
            )

        TK = temperature
        delta_H = entry["deltaH"]
        delta_S = entry["deltaS"]
        delta_G = delta_H - TK * delta_S / 1000.0  # kJ/mol
        delta_G_J = delta_G * 1000  # J/mol

        K = math.exp(-delta_G_J / (R * TK))

        return ModelResult(
            success=True,
            result={
                "K": round(K, 6),
                "K_scientific": f"{K:.6e}",
                "log10_K": round(math.log10(K) if K > 0 else float('-inf'), 4),
                "delta_G": round(delta_G, 2),
                "delta_G_unit": "kJ/mol",
                "temperature": temperature,
                "temperature_unit": "K",
                "reaction": entry["reaction"],
                "name": entry["name"],
            },
            provenance=[Provenance(dataset_id="DS002", name="NIST-JANAF")],
        )


# ═══════════════════════════════════════════════
# B001 Shomate 热容计算
# ═══════════════════════════════════════════════

class B001_ShomateProperties(BaseModelTool):
    model_id = "B001"
    name = "Shomate 热容计算"
    scenario = "热力学与相平衡"
    priority = "P0"
    version = "1.0.0"
    applicable_boundary = "Cp = A + B·t + C·t² + D·t³ + E/t² (t=T/1000)；温度受 Shomate 参数有效区间限制"

    input_fields = [
        InputField("species", "物种", type="string", required=True,
                    placeholder="如 Fe(s), O2(g), CO2(g)"),
        InputField("temperature", "温度 (K)", type="number", required=True, default=298.15),
    ]

    output_fields = [
        OutputField("Cp", "热容 Cp", type="number", unit="J/(mol·K)"),
        OutputField("H_minus_H298", "H°-H°298", type="number", unit="kJ/mol"),
        OutputField("S", "熵 S°", type="number", unit="J/(mol·K)"),
    ]

    def invoke(self, params: dict, context: Optional[InvocationContext] = None) -> ModelResult:
        species = params["species"]
        temperature = float(params["temperature"])

        # 1. 数据库优先
        result = repo.evaluate(species, "solid" if "(s)" in species else "gas" if "(g)" in species else "liquid", temperature)
        if result.results:
            cp = result.results.get("cp", {}).get("value")
            s = result.results.get("entropy", {}).get("value")
            h = result.results.get("enthalpy", {}).get("value")
            prov = result.provenance
            return ModelResult(
                success=True,
                result={
                    "species": species,
                    "temperature": temperature,
                    "Cp": cp,
                    "Cp_unit": "J/(mol·K)",
                    "H_minus_H298": h,
                    "H_unit": "kJ/mol",
                    "S": s,
                    "S_unit": "J/(mol·K)",
                    "data_source": prov.get("method", "database"),
                    "correlation_id": prov.get("correlation_id"),
                    "temperature_range": prov.get("temperature_range", []),
                },
                provenance=[Provenance(dataset_id="DS002", name="NIST-JANAF")],
            )

        # 2. 兜底：chemical_data.py
        result_cd = calc_shomate(species, temperature)
        if result_cd is None:
            available = list(SHOMATE_PARAMS.keys())
            return ModelResult(
                success=False,
                error=f"不支持或温度超出范围: {species}。可用物种: {available}",
                error_code="NO_DATA",
            )

        return ModelResult(
            success=True,
            result={**result_cd, "data_source": "builtin_fallback"},
            provenance=[Provenance(dataset_id="DS002", name="NIST-JANAF")],
        )


# ═══════════════════════════════════════════════
# B002 NASA 多项式热物性计算（简化版）
# ═══════════════════════════════════════════════

class B002_NasaProperties(BaseModelTool):
    model_id = "B002"
    name = "NASA 多项式热物性计算"
    scenario = "热力学与相平衡"
    priority = "P0"
    version = "1.0.0"
    applicable_boundary = "Cp/R = a₁ + a₂·T + a₃·T² + a₄·T³ + a₅·T⁴；当前使用 Shomate 参数近似"

    input_fields = [
        InputField("species", "物种", type="string", required=True,
                    placeholder="如 Fe(s), O2(g)"),
        InputField("temperature", "温度 (K)", type="number", required=True, default=298.15),
    ]

    output_fields = [
        OutputField("Cp", "定压热容 Cp", type="number", unit="J/(mol·K)"),
        OutputField("H_minus_H298", "H°-H°298", type="number", unit="kJ/mol"),
        OutputField("S", "熵 S°", type="number", unit="J/(mol·K)"),
    ]

    def invoke(self, params: dict, context: Optional[InvocationContext] = None) -> ModelResult:
        species = params["species"]
        temperature = float(params["temperature"])

        # 数据库优先（Shomate 近似 NASA）
        result = repo.evaluate(species, "solid" if "(s)" in species else "gas" if "(g)" in species else "liquid", temperature)
        if result.results:
            return ModelResult(
                success=True,
                result={
                    "species": species, "temperature": temperature,
                    "Cp": result.results["cp"]["value"], "Cp_unit": "J/(mol·K)",
                    "H_minus_H298": result.results["enthalpy"]["value"], "H_unit": "kJ/mol",
                    "S": result.results["entropy"]["value"], "S_unit": "J/(mol·K)",
                    "method": "Shomate 多项式（NASA 近似）", "data_source": "database",
                },
                provenance=[Provenance(dataset_id="DS002", name="NIST-JANAF")],
            )

        # 兜底
        result_cd = calc_shomate(species, temperature)
        if result_cd is None:
            available = list(SHOMATE_PARAMS.keys())
            return ModelResult(success=False, error=f"不支持: {species}。可用: {available}", error_code="NO_DATA")
        return ModelResult(
            success=True,
            result={**result_cd, "method": "Shomate 多项式（NASA 近似）", "data_source": "builtin_fallback"},
            provenance=[Provenance(dataset_id="DS002", name="NIST-JANAF")],
        )


# ═══════════════════════════════════════════════
# B004 熵积分
# ═══════════════════════════════════════════════

class B004_EntropyIntegration(BaseModelTool):
    model_id = "B004"
    name = "熵积分"
    scenario = "热力学与相平衡"
    priority = "P0"
    version = "1.0.0"
    applicable_boundary = "ΔS = ∫(Cp/T)dT；使用 Shomate 热容数值积分"

    input_fields = [
        InputField("species", "物种", type="string", required=True,
                    placeholder="如 Fe(s)"),
        InputField("temperature_start", "起始温度 (K)", type="number", required=True, default=298.15),
        InputField("temperature_end", "终止温度 (K)", type="number", required=True, default=1873),
    ]

    output_fields = [
        OutputField("delta_S", "熵变 ΔS", type="number", unit="J/(mol·K)"),
        OutputField("S_start", "起始熵", type="number", unit="J/(mol·K)"),
        OutputField("S_end", "终止熵", type="number", unit="J/(mol·K)"),
    ]

    def invoke(self, params: dict, context: Optional[InvocationContext] = None) -> ModelResult:
        species = params["species"]
        t_start = float(params.get("temperature_start", 298.15))
        t_end = float(params.get("temperature_end", 1873))

        if t_start >= t_end:
            return ModelResult(success=False, error="起始温度必须小于终止温度", error_code="INVALID_INPUT")

        s_start = calc_shomate(species, t_start)
        s_end = calc_shomate(species, t_end)

        if not s_start or not s_end:
            available = list(SHOMATE_PARAMS.keys())
            return ModelResult(success=False, error=f"不支持: {species}。可用: {available}", error_code="NO_DATA")

        return ModelResult(
            success=True,
            result={
                "delta_S": round(s_end["S"] - s_start["S"], 4),
                "S_start": s_start["S"],
                "S_end": s_end["S"],
                "species": species,
                "temperature_start": t_start,
                "temperature_end": t_end,
                "S_unit": "J/(mol·K)",
            },
            provenance=[Provenance(dataset_id="DS002", name="NIST-JANAF")],
        )


# ═══════════════════════════════════════════════
# B005 Gibbs自由能计算（单物种）
# ═══════════════════════════════════════════════

class B005_SpeciesGibbs(BaseModelTool):
    model_id = "B005"
    name = "物种 Gibbs 自由能计算"
    scenario = "热力学与相平衡"
    priority = "P0"
    version = "1.0.0"
    applicable_boundary = "G = H - T·S；使用 Shomate 参数计算单物种热力学性质"

    input_fields = [
        InputField("species", "物种", type="string", required=True,
                    placeholder="如 Fe(s), O2(g)"),
        InputField("temperature", "温度 (K)", type="number", required=True, default=1873),
    ]

    output_fields = [
        OutputField("G", "Gibbs自由能 G", type="number", unit="kJ/mol"),
        OutputField("H", "焓 H", type="number", unit="kJ/mol"),
        OutputField("S", "熵 S", type="number", unit="J/(mol·K)"),
    ]

    def invoke(self, params: dict, context: Optional[InvocationContext] = None) -> ModelResult:
        species = params["species"]
        temperature = float(params["temperature"])

        # 1. 数据库优先
        result = repo.evaluate(species, "solid" if "(s)" in species else "gas" if "(g)" in species else "liquid", temperature)
        if result.results:
            r = result.results
            h = r.get("enthalpy", {}).get("value", 0)
            s = r.get("entropy", {}).get("value", 0)
            g = h - temperature * s / 1000.0
            return ModelResult(
                success=True,
                result={
                    "G": round(g, 4),
                    "G_unit": "kJ/mol",
                    "H": h,
                    "H_unit": "kJ/mol",
                    "S": s,
                    "S_unit": "J/(mol·K)",
                    "species": species,
                    "temperature": temperature,
                    "temperature_unit": "K",
                    "data_source": result.provenance.get("method", "database"),
                },
                provenance=[Provenance(dataset_id="DS002", name="NIST-JANAF")],
            )

        # 2. 兜底 calc_shomate
        result_cd = calc_shomate(species, temperature)
        if not result_cd:
            available = list(SHOMATE_PARAMS.keys())
            return ModelResult(success=False, error=f"不支持: {species}。可用: {available}", error_code="NO_DATA")

        G = result_cd["H_minus_H298"] - temperature * result_cd["S"] / 1000.0
        return ModelResult(
            success=True,
            result={
                "G": round(G, 4), "G_unit": "kJ/mol",
                "H": result_cd["H_minus_H298"], "H_unit": "kJ/mol",
                "S": result_cd["S"], "S_unit": "J/(mol·K)",
                "species": species, "temperature": temperature,
                "temperature_unit": "K", "data_source": "builtin_fallback",
            },
            provenance=[Provenance(dataset_id="DS002", name="NIST-JANAF")],
        )


# ═══════════════════════════════════════════════
# B007 反应熵计算
# ═══════════════════════════════════════════════

class B007_ReactionEntropy(BaseModelTool):
    model_id = "B007"
    name = "反应熵计算"
    scenario = "热力学与相平衡"
    priority = "P0"
    version = "1.0.0"
    applicable_boundary = "ΔS = ΣS°(产物) − ΣS°(反应物)；基于内置热化学数据库"

    input_fields = [
        InputField("reaction", "反应式", type="string", required=True,
                    placeholder="如 FeO + C → Fe + CO"),
        InputField("temperature", "温度 (K)", type="number", required=False, default=298.15),
    ]

    output_fields = [
        OutputField("delta_S", "反应熵 ΔS", type="number", unit="J/(mol·K)"),
        OutputField("delta_H", "反应焓 ΔH", type="number", unit="kJ/mol"),
        OutputField("reaction", "反应式", type="string"),
    ]

    def invoke(self, params: dict, context: Optional[InvocationContext] = None) -> ModelResult:
        reaction = params["reaction"]
        temperature = float(params.get("temperature", 298.15))

        entry = _lookup_reaction(reaction, temperature)
        if entry is None:
            return ModelResult(success=False, error=f"不支持的反应: {reaction}", error_code="UNSUPPORTED_REACTION")

        return ModelResult(
            success=True,
            result={
                "delta_S": entry["deltaS"],
                "delta_S_unit": "J/(mol·K)",
                "delta_H": entry["deltaH"],
                "delta_H_unit": "kJ/mol",
                "temperature": temperature,
                "temperature_unit": "K",
                "reaction": entry["reaction"],
                "name": entry["name"],
                "method": "ΔS = ΣS°(产物) − ΣS°(反应物)",
            },
            provenance=[Provenance(dataset_id="DS002", name="NIST-JANAF")],
        )


# ── B019 杠杆规则计算 ──

class B019_LeverRule(BaseModelTool):
    model_id = "B019"
    name = "杠杆规则计算"
    scenario = "热力学与相平衡"
    priority = "P2"
    version = "1.0.0"
    applicable_boundary = "仅适用于二元系两相区"

    input_fields = [
        InputField("overall_composition", "总体成分", type="number", required=True,
                    description="总体成分 (质量/摩尔分数)"),
        InputField("phase1_composition", "相1成分", type="number", required=True,
                    description="相1边界成分"),
        InputField("phase2_composition", "相2成分", type="number", required=True,
                    description="相2边界成分"),
        InputField("component", "组元", type="string", required=False, default="B",
                    description="组元名称"),
    ]

    output_fields = [
        OutputField("phase1_fraction", "相1分数", type="number"),
        OutputField("phase2_fraction", "相2分数", type="number"),
        OutputField("conservation_residual", "守恒残差", type="number"),
    ]

    def invoke(self, params: dict, context: Optional[InvocationContext] = None) -> ModelResult:
        C0 = float(params["overall_composition"])
        C1 = float(params["phase1_composition"])
        C2 = float(params["phase2_composition"])

        # 验证：总体成分必须在两相成分之间
        if not (min(C1, C2) <= C0 <= max(C1, C2)):
            return ModelResult(
                success=False,
                error=f"总体成分 {C0} 不在两相边界 [{min(C1, C2)}, {max(C1, C2)}] 之间",
                error_code="OUT_OF_RANGE",
            )

        if abs(C2 - C1) < 1e-12:
            return ModelResult(
                success=False, error="两相成分相同，无法计算",
                error_code="INVALID_INPUT",
            )

        # 杠杆规则
        f1 = (C2 - C0) / (C2 - C1)
        f2 = (C0 - C1) / (C2 - C1)

        # 守恒校验
        residual = abs(f1 * C1 + f2 * C2 - C0)

        return ModelResult(
            success=True,
            result={
                "phase1_fraction": round(f1, 6),
                "phase2_fraction": round(f2, 6),
                "phase1_composition": C1,
                "phase2_composition": C2,
                "overall_composition": C0,
                "conservation_residual": round(residual, 10),
                "conservation_passed": residual < 1e-8,
                "component": params.get("component", "B"),
                "method": "杠杆规则 (Lever Rule)",
            },
        )
