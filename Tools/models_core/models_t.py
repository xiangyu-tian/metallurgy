"""Qualified heat-transfer tools for the 30-tool milestone."""
from __future__ import annotations

from .base import BaseModelTool, InputField, ModelResult, OutputField


SIGMA_W_M2_K4 = 5.670374419e-8


def rel(kind, target, description):
    return {"type": kind, "target": target, "description": description}


class HeatTransferTool(BaseModelTool):
    scenario = "传热传质"
    priority = "P0"
    version = "1.0.0"
    status = "qualified"
    qualification_status = "qualified"
    count_eligible = True
    source_version = "CODATA-2018/Fourier-v1"
    source_records = [{"source_id":"HEAT-TRANSFER-FORMULAE-V1","name":"Fourier law and CODATA Stefan-Boltzmann constant","version":"2026.08-v1"}]
    data_source = ["Fourier定律与CODATA固定常数"]


class T001_PlaneWallConduction(HeatTransferTool):
    model_id, name = "T001", "稳态平板导热"
    description = "计算均质平板一维稳态导热的热流密度、热流率和热阻。"
    applicable_boundary = "常导热系数、一维稳态、无内热源、接触热阻忽略；k、L、A均大于0。"
    formula_reference = "Fourier plane wall: q''=k(Th-Tc)/L; Q=q''A; R=L/(kA)"
    failure_modes = ["导热系数不为正", "厚度不为正", "面积不为正", "绝对温度不为正"]
    independent_validation = ["Q=ΔT/R", "交换冷热端后热流率反号", "等温边界时热流为零"]
    dependencies = []
    relations = [rel("overlaps", "T002", "输入均为边界温度和面积但传热机制不同"), rel("upstream_of", "D002", "可为BOF热损失提供导热分量")]
    input_fields = [
        InputField("thermal_conductivity", "导热系数", "number", unit="W/(m·K)", min_value=1e-300),
        InputField("thickness", "厚度", "number", unit="m", min_value=1e-300), InputField("area", "面积", "number", unit="m²", min_value=1e-300),
        InputField("hot_temperature", "热端温度", "number", unit="K", min_value=1e-12), InputField("cold_temperature", "冷端温度", "number", unit="K", min_value=1e-12),
    ]
    output_fields = [
        OutputField("temperature_difference_k", "热端减冷端温差", "number", "K"), OutputField("heat_flux_w_m2", "有符号热流密度", "number", "W/m²"),
        OutputField("heat_rate_w", "有符号热流率", "number", "W"), OutputField("thermal_resistance_k_per_w", "热阻", "number", "K/W"),
        OutputField("direction", "正向定义", "string", description="hot_to_cold/cold_to_hot/none"),
    ]
    validation_rules = [{"rule":"positive","fields":["thermal_conductivity","thickness","area","hot_temperature","cold_temperature"]}]
    qualification_cases = [
        {"id":"T001-N1","kind":"normal","input":{"thermal_conductivity":20,"thickness":0.1,"area":2,"hot_temperature":1000,"cold_temperature":500}},
        {"id":"T001-N2","kind":"normal","input":{"thermal_conductivity":10,"thickness":0.2,"area":1,"hot_temperature":500,"cold_temperature":1000}},
        {"id":"T001-N3","kind":"normal","input":{"thermal_conductivity":1,"thickness":1,"area":1,"hot_temperature":300,"cold_temperature":300}},
        {"id":"T001-F1","kind":"failure","input":{"thermal_conductivity":0,"thickness":1,"area":1,"hot_temperature":300,"cold_temperature":200}},
        {"id":"T001-F2","kind":"failure","input":{"thermal_conductivity":1,"thickness":0,"area":1,"hot_temperature":300,"cold_temperature":200}},
    ]

    def invoke(self, params, context=None):
        conductivity = float(params["thermal_conductivity"]); thickness = float(params["thickness"]); area = float(params["area"])
        delta = float(params["hot_temperature"])-float(params["cold_temperature"])
        resistance = thickness/(conductivity*area); heat_flux = conductivity*delta/thickness; heat_rate = heat_flux*area
        direction = "hot_to_cold" if heat_rate > 0 else "cold_to_hot" if heat_rate < 0 else "none"
        return ModelResult(True, result={"temperature_difference_k":delta,"heat_flux_w_m2":heat_flux,"heat_rate_w":heat_rate,"thermal_resistance_k_per_w":resistance,"direction":direction})


class T002_GrayBodyRadiation(HeatTransferTool):
    model_id, name = "T002", "灰体辐射换热"
    description = "计算灰体表面与大包围环境之间的净辐射换热。"
    applicable_boundary = "漫灰表面、环境可视为大包围体；0<=ε,F<=1、面积>0、绝对温度>0。"
    formula_reference = "Q=σ ε F A (Te⁴-Ts⁴), σ=5.670374419e-8 W/(m²K⁴)"
    failure_modes = ["绝对温度不为正", "发射率或视角因子超出0到1", "面积不为正"]
    independent_validation = ["交换温度后净热流反号", "ε=0或F=0时热流为零", "结果与Stefan-Boltzmann代数复算一致"]
    dependencies = []
    relations = [rel("overlaps", "T001", "同为两温度边界热流但采用辐射机制"), rel("upstream_of", "D002", "可为BOF热损失提供辐射分量")]
    input_fields = [
        InputField("emitter_temperature", "发射表面温度", "number", unit="K", min_value=1e-12), InputField("surroundings_temperature", "环境温度", "number", unit="K", min_value=1e-12),
        InputField("emissivity", "发射率", "number", unit="dimensionless", min_value=0, max_value=1), InputField("area", "面积", "number", unit="m²", min_value=1e-300),
        InputField("view_factor", "视角因子", "number", required=False, default=1.0, unit="dimensionless", min_value=0, max_value=1),
    ]
    output_fields = [
        OutputField("net_radiation_w", "从发射表面流出的净热率", "number", "W"), OutputField("radiative_heat_flux_w_m2", "净辐射热流密度", "number", "W/m²"),
        OutputField("sigma", "Stefan-Boltzmann常数", "number", "W/(m²·K⁴)"), OutputField("direction", "换热方向", "string"),
    ]
    validation_rules = [{"rule":"positive","fields":["emitter_temperature","surroundings_temperature","area"]},{"rule":"closed_interval","fields":["emissivity","view_factor"],"range":[0,1]}]
    qualification_cases = [
        {"id":"T002-N1","kind":"normal","input":{"emitter_temperature":1000,"surroundings_temperature":500,"emissivity":0.8,"area":2,"view_factor":1}},
        {"id":"T002-N2","kind":"normal","input":{"emitter_temperature":500,"surroundings_temperature":1000,"emissivity":0.8,"area":2,"view_factor":1}},
        {"id":"T002-N3","kind":"normal","input":{"emitter_temperature":1000,"surroundings_temperature":500,"emissivity":0,"area":2,"view_factor":1}},
        {"id":"T002-F1","kind":"failure","input":{"emitter_temperature":0,"surroundings_temperature":500,"emissivity":0.8,"area":2}},
        {"id":"T002-F2","kind":"failure","input":{"emitter_temperature":1000,"surroundings_temperature":500,"emissivity":1.1,"area":2}},
    ]

    def invoke(self, params, context=None):
        emitter = float(params["emitter_temperature"]); surroundings = float(params["surroundings_temperature"])
        emissivity = float(params["emissivity"]); area = float(params["area"]); factor = float(params.get("view_factor",1.0))
        flux = SIGMA_W_M2_K4*emissivity*factor*(emitter**4-surroundings**4); heat_rate = flux*area
        direction = "emitter_to_surroundings" if heat_rate > 0 else "surroundings_to_emitter" if heat_rate < 0 else "none"
        return ModelResult(True, result={"net_radiation_w":heat_rate,"radiative_heat_flux_w_m2":flux,"sigma":SIGMA_W_M2_K4,"direction":direction})
