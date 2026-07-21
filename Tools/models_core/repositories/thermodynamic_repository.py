"""
thermodynamic_repository — 统一热力学数据访问层

所有 B 系列模型通过此层获取数据，不直接写 SQL。
查询顺序：关联式 → 离散点 → 内存兜底
返回结果带完整溯源。
"""
from __future__ import annotations
import json
import math
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field


# ── 返回类型 ──

@dataclass
class ThermoResult:
    species: str
    phase: str
    temperature: float
    property_code: str
    value: float
    unit: str
    method: str = "unknown"           # correlation / table / builtin_fallback
    equation_type: str = ""
    correlation_id: int = 0
    source_id: str = ""
    temperature_range: list = field(default_factory=list)
    confidence: float = 1.0


@dataclass
class EvaluateResult:
    species: str
    phase: str
    temperature: float
    results: Dict[str, Dict]  # {"cp": {"value": ..., "unit": ...}, ...}
    provenance: Dict = field(default_factory=dict)


class ThermodynamicRepository:
    """热力学数据仓库"""

    def __init__(self):
        self._db = None

    def _get_db(self):
        if self._db is None:
            import psycopg2
            import psycopg2.extras
            self._db = psycopg2.connect(
                host='127.0.0.1', port=5432, database='metallurgy',
                user='postgres', password='', connect_timeout=3,
            )
        return self._db

    def find_correlation(self, species_id: str, phase: str,
                         temperature: float,
                         equation_type: str = "SHOMATE") -> Optional[Dict]:
        """查关联式表，找到覆盖目标温度的系数"""
        import psycopg2
        import psycopg2.extras
        conn = self._get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT id, equation_type, temperature_min_k, temperature_max_k,
                   coefficients, coefficient_units, source_id, reference_text
            FROM metallurgy_v2.thermodynamic_correlation
            WHERE species_id = %s AND phase = %s
              AND %s BETWEEN temperature_min_k AND temperature_max_k
              AND equation_type = %s
              AND is_active = TRUE
            ORDER BY priority
            LIMIT 1
        """, (species_id, phase, temperature, equation_type))
        row = cur.fetchone()
        cur.close()
        return dict(row) if row else None

    def evaluate_shomate(self, species_id: str, phase: str,
                         temperature: float) -> Optional[EvaluateResult]:
        """用 Shomate 关联式计算 Cp/H/S/G"""
        # 去掉相态后缀（Fe(s) → Fe）
        clean_species = species_id.split('(')[0].strip()

        # 尝试指定相态
        for p in [phase, 'solid', 'gas', 'liquid']:
            corr = self.find_correlation(clean_species, p, temperature, "SHOMATE")
            if corr:
                break

        if not corr and temperature > 1200:
            # 高温下尝试液体/气体相
            for p in ['liquid', 'gas']:
                corr = self.find_correlation(clean_species, p, temperature, "SHOMATE")
                if corr:
                    break
        if not corr:
            return None

        coeffs = corr["coefficients"]
        A = coeffs["A"]; B = coeffs["B"]; C = coeffs["C"]
        D = coeffs["D"]; E = coeffs["E"]
        F = coeffs["F"]; G_val = coeffs["G"]; H_val = coeffs["H"]

        t = temperature / 1000.0
        ln_t = math.log(t) if t > 0 else 0

        Cp = A + B*t + C*t**2 + D*t**3 + E/t**2
        H_inc = A*t + B*t**2/2 + C*t**3/3 + D*t**4/4 - E/t + F - H_val
        S = A*ln_t + B*t + C*t**2/2 + D*t**3/3 - E/(2*t**2) + G_val
        gibbs = H_inc - temperature * S / 1000.0

        prov = {
            "method": "SHOMATE",
            "equation_type": corr["equation_type"],
            "correlation_id": corr["id"],
            "temperature_range": [corr["temperature_min_k"], corr["temperature_max_k"]],
            "source_id": corr["source_id"],
        }

        return EvaluateResult(
            species=species_id,
            phase=phase,
            temperature=temperature,
            results={
                "cp": {"value": round(Cp, 6), "unit": "J/(mol·K)"},
                "entropy": {"value": round(S, 6), "unit": "J/(mol·K)"},
                "enthalpy": {"value": round(H_inc, 6), "unit": "kJ/mol"},
                "gibbs": {"value": round(gibbs, 6), "unit": "kJ/mol"},
            },
            provenance=prov,
        )

    def get_property(self, species: str, property_code: str,
                     temperature: float) -> Optional[ThermoResult]:
        """查离散点值表"""
        try:
            conn = self._get_db()
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("""
                SELECT value, unit, data_origin, source_ref, correlation_id
                FROM metallurgy_v2.thermodynamic_property
                WHERE species LIKE %s AND property_code = %s
                  AND ABS(temperature - %s) < 1
                LIMIT 1
            """, (f'{species}%', property_code, temperature))
            row = cur.fetchone()
            cur.close()
            if row:
                return ThermoResult(
                    species=species,
                    phase='',
                    temperature=temperature,
                    property_code=property_code,
                    value=row["value"],
                    unit=row["unit"],
                    method=row.get("data_origin", "table") or "table",
                    source_id=row.get("source_ref", ""),
                )
            return None
        except Exception:
            return None

    def evaluate(self, species: str, phase: str, temperature: float,
                 properties: List[str] = None) -> EvaluateResult:
        """统一评价：关联式优先 → 离散点 → 空结果"""
        if properties is None:
            properties = ["cp", "entropy", "enthalpy"]

        # 1. Shomate
        result = self.evaluate_shomate(species, phase, temperature)
        if result:
            # Filter requested properties
            filtered = {}
            for p in properties:
                if p in result.results:
                    filtered[p] = result.results[p]
            result.results = filtered
            return result

        # 2. 离散点
        code_map = {"cp": "CP_STD", "entropy": "S_STD",
                     "enthalpy": "H_INCREMENT_298", "gibbs": "G_STD"}
        results = {}
        provenance = {}
        for p in properties:
            code = code_map.get(p)
            if code:
                tp = self.get_property(species, code, temperature)
                if tp:
                    results[p] = {"value": tp.value, "unit": tp.unit}
                    provenance[p] = {"source": tp.source_id, "method": tp.method}

        # 3. 兜底：chemical_data.py
        if not results:
            try:
                from .chemical_data import calc_shomate
                cd = calc_shomate(f"{species}({phase[0]})", temperature)
                if cd:
                    results["cp"] = {"value": cd["Cp"], "unit": "J/(mol·K)"}
                    results["entropy"] = {"value": cd["S"], "unit": "J/(mol·K)"}
                    results["enthalpy"] = {"value": cd["H_minus_H298"], "unit": "kJ/mol"}
                    provenance = {"method": "builtin_fallback"}
            except ImportError:
                pass

        return EvaluateResult(
            species=species, phase=phase, temperature=temperature,
            results=results, provenance=provenance,
        )


# 全局单例
repo = ThermodynamicRepository()
