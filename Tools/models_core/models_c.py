"""
C 系列模型：动力学与传递（首批）
C001 Arrhenius 速率常数
"""
from __future__ import annotations
import math
from typing import Dict, List, Optional

from .base import (
    BaseModelTool, ModelResult, InputField, OutputField,
    BoundaryCheck, BoundaryWarning, InvocationContext,
)


class C001_ArrheniusRate(BaseModelTool):
    model_id = "C001"
    name = "Arrhenius 速率常数"
    scenario = "动力学与传递"
    priority = "P0"
    version = "1.0.0"
    applicable_boundary = "k = A·exp(-Ea/RT)；适用 Arrhenius 行为反应"

    input_fields = [
        InputField("A", "指前因子 A", type="number", required=True,
                    description="指前因子，单位与 k 一致"),
        InputField("Ea", "活化能 Ea", type="number", required=True,
                    description="活化能 (J/mol 或 kJ/mol)"),
        InputField("temperature", "温度 T", type="number", required=True,
                    description="反应温度 (K)"),
        InputField("Ea_unit", "活化能单位", type="select", required=False,
                    default="J/mol", enum=["J/mol", "kJ/mol"]),
        InputField("R", "气体常数", type="number", required=False, default=8.314,
                    description="气体常数 (J/(mol·K))"),
    ]

    output_fields = [
        OutputField("k", "速率常数", type="number"),
        OutputField("ln_k", "ln(k)", type="number"),
        OutputField("temperature", "温度 (K)", type="number"),
    ]

    def invoke(self, params: dict, context: Optional[InvocationContext] = None) -> ModelResult:
        A = float(params["A"])
        Ea = float(params["Ea"])
        T = float(params["temperature"])
        Ea_unit = params.get("Ea_unit", "J/mol")
        R = float(params.get("R", 8.314))

        # 单位转换
        if Ea_unit == "kJ/mol":
            Ea_J = Ea * 1000
        else:
            Ea_J = Ea

        if T <= 0:
            return ModelResult(
                success=False, error=f"温度必须大于 0K，收到 {T}K",
                error_code="INVALID_INPUT",
            )

        k = A * math.exp(-Ea_J / (R * T))
        ln_k = math.log(k) if k > 0 else float('-inf')

        warnings = []
        if T > 3000:
            warnings.append(BoundaryWarning(
                field="temperature", level="warning",
                message=f"温度 {T}K 超出多数 Arrhenius 关系适用范围",
            ))

        return ModelResult(
            success=True,
            result={
                "k": round(k, 10),
                "k_scientific": f"{k:.6e}",
                "ln_k": round(ln_k, 4),
                "A": A,
                "Ea": Ea,
                "Ea_unit": Ea_unit,
                "Ea_J_per_mol": round(Ea_J, 2),
                "temperature": T,
                "temperature_unit": "K",
                "R": R,
                "method": "k = A·exp(-Ea/RT)",
            },
            boundary_check=BoundaryCheck(
                passed=len(warnings) == 0,
                warnings=warnings,
            ),
        )


# ═══════════════════════════════════════════════
# C002 扩散系数计算
# ═══════════════════════════════════════════════

class C002_DiffusionCoefficient(BaseModelTool):
    model_id = "C002"
    name = "扩散系数计算"
    scenario = "动力学与传递"
    priority = "P0"
    version = "1.0.0"
    applicable_boundary = "D = D₀·exp(-Q/RT)；支持 Arrhenius 扩散行为"

    input_fields = [
        InputField("D0", "指前因子 D₀", type="number", required=True,
                    description="扩散常数 (m²/s)"),
        InputField("Q", "激活能 Q", type="number", required=True,
                    description="扩散激活能"),
        InputField("temperature", "温度 T", type="number", required=True,
                    description="温度 (K)"),
        InputField("Q_unit", "激活能单位", type="select", required=False,
                    default="J/mol", enum=["J/mol", "kJ/mol", "eV"]),
    ]

    output_fields = [
        OutputField("D", "扩散系数 D", type="number", unit="m²/s"),
        OutputField("ln_D", "ln(D)", type="number"),
        OutputField("sqrt_Dt_1h", "1h 扩散距离 √(Dt)", type="number", unit="m"),
    ]

    def invoke(self, params: dict, context: Optional[InvocationContext] = None) -> ModelResult:
        D0 = float(params["D0"])
        Q = float(params["Q"])
        T = float(params["temperature"])
        Q_unit = params.get("Q_unit", "J/mol")

        # 单位转换
        if Q_unit == "kJ/mol":
            Q_J = Q * 1000
        elif Q_unit == "eV":
            Q_J = Q * 1.602176634e-19
        else:
            Q_J = Q

        R = 8.314  # J/(mol·K)
        if T <= 0:
            return ModelResult(success=False, error=f"温度必须 > 0K", error_code="INVALID_INPUT")

        D = D0 * math.exp(-Q_J / (R * T))
        ln_D = math.log(D) if D > 0 else float('-inf')
        sqrt_Dt_1h = math.sqrt(D * 3600)  # 1小时的扩散距离 √(D·t)

        return ModelResult(
            success=True,
            result={
                "D": round(D, 12),
                "D_scientific": f"{D:.6e}",
                "ln_D": round(ln_D, 4),
                "sqrt_Dt_1h": round(sqrt_Dt_1h, 8),
                "sqrt_Dt_1h_unit": "m",
                "D0": D0,
                "Q": Q,
                "Q_unit": Q_unit,
                "Q_J_per_mol": round(Q_J, 2),
                "temperature": T,
                "temperature_unit": "K",
                "method": "D = D₀·exp(-Q/RT)",
            },
        )
