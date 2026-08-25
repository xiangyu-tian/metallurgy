"""Qualified kinetics and diffusion tools for the 30-tool milestone."""
from __future__ import annotations

import math

from .base import BaseModelTool, InputField, ModelResult, OutputField
from .thermo_assets import R_J_MOL_K


SCENARIO = "动力学与扩散"
FARADAY_J_MOL_EV = 96485.33212331001
SOURCE = [{"source_id": "KINETICS-FORMULAE-V1", "name": "IUPAC/Crank/Avrami formula set", "version": "2026.08-v1"}]


def rel(kind, target, description):
    return {"type": kind, "target": target, "description": description}


def fail(message, code="INVALID_INPUT"):
    return ModelResult(False, error=message, error_code=code)


def activation_to_j_mol(value, unit):
    if unit == "kJ/mol":
        return value * 1000.0
    if unit == "eV/particle":
        return value * FARADAY_J_MOL_EV
    return value


class KineticsTool(BaseModelTool):
    scenario = SCENARIO
    priority = "P0"
    version = "2.0.0"
    status = "qualified"
    qualification_status = "qualified"
    count_eligible = True
    source_version = "2026.08-v1"
    source_records = SOURCE
    data_source = ["公开解析公式的版本化实现"]


class C001_ArrheniusRate(KineticsTool):
    model_id, name = "C001", "Arrhenius 速率常数"
    description = "把摩尔活化能或单粒子eV统一到J/mol后计算速率常数。"
    applicable_boundary = "单一活化过程、温度无关指前因子和活化能；T>0、A>0。"
    formula_reference = "Arrhenius: k=A exp[-Ea/(RT)]"
    failure_modes = ["温度不为正", "指前因子不为正", "活化能为负", "单位不受支持"]
    independent_validation = ["ln(k/A)=-Ea/(RT)", "Ea=0时k=A"]
    dependencies = []
    relations = [rel("overlaps", "C002", "数学形式相同但输出目标和单位不同"), rel("upstream_of", "C004", "可为等温JMAK速率参数提供温度修正")]
    input_fields = [
        InputField("A", "指前因子", "number", unit="与k相同", min_value=1e-300),
        InputField("Ea", "活化能", "number", unit="$Ea_unit", min_value=0),
        InputField("temperature", "绝对温度", "number", unit="K", min_value=1e-12),
        InputField("Ea_unit", "活化能单位", "select", required=False, default="J/mol", enum=["J/mol", "kJ/mol", "eV/particle"]),
    ]
    output_fields = [
        OutputField("A", "指前因子", "number", "与k相同"), OutputField("Ea_j_mol", "摩尔活化能", "number", "J/mol"),
        OutputField("temperature", "温度", "number", "K"), OutputField("gas_constant", "气体常数", "number", "J/(mol·K)"),
        OutputField("k", "速率常数", "number", "与A相同"), OutputField("ln_k", "速率常数自然对数", "number", "dimensionless"),
    ]
    validation_rules = [{"rule": "positive", "fields": ["A", "temperature"]}, {"rule": "nonnegative", "field": "Ea"}]
    qualification_cases = [
        {"id":"C001-N1","kind":"normal","input":{"A":1e7,"Ea":80000,"temperature":1000}},
        {"id":"C001-N2","kind":"normal","input":{"A":2.5,"Ea":0,"temperature":500,"Ea_unit":"kJ/mol"}},
        {"id":"C001-N3","kind":"normal","input":{"A":1e12,"Ea":1,"temperature":1200,"Ea_unit":"eV/particle"}},
        {"id":"C001-F1","kind":"failure","input":{"A":0,"Ea":1,"temperature":1000}},
        {"id":"C001-F2","kind":"failure","input":{"A":1,"Ea":1,"temperature":0}},
    ]

    def invoke(self, params, context=None):
        a = float(params["A"]); ea = float(params["Ea"]); temperature = float(params["temperature"])
        ea_j_mol = activation_to_j_mol(ea, params.get("Ea_unit", "J/mol"))
        ln_k = math.log(a) - ea_j_mol / (R_J_MOL_K * temperature)
        k = math.exp(ln_k) if ln_k > -745 else 0.0
        return ModelResult(True, result={"A":a,"Ea_j_mol":ea_j_mol,"temperature":temperature,"gas_constant":R_J_MOL_K,"k":k,"ln_k":ln_k})


class C002_DiffusionCoefficient(KineticsTool):
    model_id, name = "C002", "Arrhenius 扩散系数"
    description = "计算常温度下扩散系数，并正确区分eV/particle与J/mol。"
    applicable_boundary = "单一扩散机制且D0、Q不随温度变化；T>0、D0>0、Q>=0。"
    formula_reference = "D=D0 exp[-Q/(RT)]; 1 eV/particle=96485.33212331001 J/mol"
    failure_modes = ["温度不为正", "D0不为正", "激活能为负", "单位不受支持"]
    independent_validation = ["eV与J/mol两种输入路径等价", "Q=0时D=D0"]
    dependencies = []
    relations = [rel("overlaps", "C001", "共享Arrhenius结构但D具有m²/s物理单位"), rel("upstream_of", "C003", "为Fick解析解提供常扩散系数")]
    input_fields = [
        InputField("D0", "扩散指前因子", "number", unit="m²/s", min_value=1e-300),
        InputField("Q", "扩散激活能", "number", unit="$Q_unit", min_value=0),
        InputField("temperature", "绝对温度", "number", unit="K", min_value=1e-12),
        InputField("Q_unit", "激活能单位", "select", required=False, default="J/mol", enum=["J/mol", "kJ/mol", "eV/particle"]),
    ]
    output_fields = [
        OutputField("D0", "扩散指前因子", "number", "m²/s"), OutputField("Q_j_mol", "摩尔激活能", "number", "J/mol"),
        OutputField("temperature", "温度", "number", "K"), OutputField("gas_constant", "气体常数", "number", "J/(mol·K)"),
        OutputField("D", "扩散系数", "number", "m²/s"), OutputField("ln_D", "扩散系数自然对数", "number", "ln(m²/s)"),
        OutputField("one_hour_diffusion_length_m", "一小时特征长度", "number", "m"),
    ]
    validation_rules = [{"rule":"positive","fields":["D0","temperature"]},{"rule":"nonnegative","field":"Q"}]
    qualification_cases = [
        {"id":"C002-N1","kind":"normal","input":{"D0":1e-4,"Q":80000,"temperature":1000}},
        {"id":"C002-N2","kind":"normal","input":{"D0":2e-5,"Q":80,"temperature":1200,"Q_unit":"kJ/mol"}},
        {"id":"C002-N3","kind":"normal","input":{"D0":1e-4,"Q":1,"temperature":1000,"Q_unit":"eV/particle"}},
        {"id":"C002-F1","kind":"failure","input":{"D0":0,"Q":1,"temperature":1000}},
        {"id":"C002-F2","kind":"failure","input":{"D0":1,"Q":1,"temperature":0}},
    ]

    def invoke(self, params, context=None):
        d0 = float(params["D0"]); q = float(params["Q"]); temperature = float(params["temperature"])
        q_j_mol = activation_to_j_mol(q, params.get("Q_unit", "J/mol"))
        ln_d = math.log(d0) - q_j_mol / (R_J_MOL_K * temperature)
        diffusion = math.exp(ln_d) if ln_d > -745 else 0.0
        return ModelResult(True, result={"D0":d0,"Q_j_mol":q_j_mol,"temperature":temperature,"gas_constant":R_J_MOL_K,"D":diffusion,"ln_D":ln_d,"one_hour_diffusion_length_m":math.sqrt(diffusion*3600.0)})


class C003_SemiInfiniteFick(KineticsTool):
    model_id, name = "C003", "半无限体 Fick 解析解"
    description = "计算恒表面浓度、常扩散系数半无限体中的浓度剖面和表面通量。"
    applicable_boundary = "一维半无限体、初始均匀、t>0、x>=0、D常数且表面浓度恒定。"
    formula_reference = "Crank: C=Cs+(C0-Cs)erf[x/(2√Dt)]; J(0)=(Cs-C0)√[D/(πt)]"
    failure_modes = ["D不为正", "时间不为正", "位置为负", "浓度或位置非有限"]
    independent_validation = ["x=0时C=Cs", "x趋于无穷时C趋于C0", "剖面满足误差函数相似变量"]
    dependencies = ["C002"]
    relations = [rel("depends_on", "C002", "可接受C002输出的常扩散系数"), rel("overlaps", "C002", "C002给材料参数，C003给时空分布")]
    input_fields = [
        InputField("diffusion_coefficient", "扩散系数", "number", unit="m²/s", min_value=1e-300),
        InputField("initial_concentration", "初始浓度", "number", unit="user concentration unit"),
        InputField("surface_concentration", "表面浓度", "number", unit="user concentration unit"),
        InputField("time_s", "扩散时间", "number", unit="s", min_value=1e-300),
        InputField("positions_m", "位置数组", "array", items={"type":"number","minimum":0}, description="距表面的非负位置"),
    ]
    output_fields = [OutputField("profile", "浓度剖面", "array"), OutputField("surface_flux", "进入固体的表面通量", "number", "concentration·m/s"), OutputField("characteristic_depth_2sqrt_dt", "特征深度", "number", "m"), OutputField("similarity_solution", "解析形式", "string")]
    validation_rules = [{"rule":"positive","fields":["diffusion_coefficient","time_s"]},{"rule":"nonnegative_array","field":"positions_m"}]
    qualification_cases = [
        {"id":"C003-N1","kind":"normal","input":{"diffusion_coefficient":1e-10,"initial_concentration":0,"surface_concentration":1,"time_s":3600,"positions_m":[0,0.001]}},
        {"id":"C003-N2","kind":"normal","input":{"diffusion_coefficient":2e-9,"initial_concentration":1,"surface_concentration":0,"time_s":10,"positions_m":[0,0.0001]}},
        {"id":"C003-N3","kind":"normal","input":{"diffusion_coefficient":1e-12,"initial_concentration":0.2,"surface_concentration":0.8,"time_s":100,"positions_m":[0,0.00001,0.001]}},
        {"id":"C003-F1","kind":"failure","input":{"diffusion_coefficient":0,"initial_concentration":0,"surface_concentration":1,"time_s":1,"positions_m":[0]}},
        {"id":"C003-F2","kind":"failure","input":{"diffusion_coefficient":1,"initial_concentration":0,"surface_concentration":1,"time_s":1,"positions_m":[-1]}},
    ]

    def invoke(self, params, context=None):
        diffusion = float(params["diffusion_coefficient"]); time_s = float(params["time_s"])
        c0 = float(params["initial_concentration"]); cs = float(params["surface_concentration"]); positions = params["positions_m"]
        if not positions or any(isinstance(x, bool) or not math.isfinite(float(x)) or float(x) < 0 for x in positions):
            return fail("positions_m必须是非空、有限、非负位置数组")
        scale = 2.0 * math.sqrt(diffusion*time_s)
        profile = [{"position_m":float(x),"concentration":cs+(c0-cs)*math.erf(float(x)/scale)} for x in positions]
        flux = (cs-c0)*math.sqrt(diffusion/(math.pi*time_s))
        return ModelResult(True, result={"profile":profile,"surface_flux":flux,"characteristic_depth_2sqrt_dt":scale,"similarity_solution":"constant-surface-concentration erf solution"})


class C004_JMAKTransformation(KineticsTool):
    model_id, name = "C004", "JMAK 等温转变动力学"
    description = "计算等温条件下随时间变化的转变量及半转变时间。"
    applicable_boundary = "等温、随机形核/长大可由常数k和Avrami指数n表征；k>0、n>0、t>=0。"
    formula_reference = "JMAK: X(t)=1-exp[-(kt)^n]"
    failure_modes = ["k不为正", "Avrami指数不为正", "时间为负", "时间数组为空"]
    independent_validation = ["X(0)=0", "X随时间单调不减", "t50=(ln2)^(1/n)/k"]
    dependencies = ["C001"]
    relations = [rel("depends_on", "C001", "k可由Arrhenius工具作温度修正"), rel("distinct_from", "C003", "同为时变解析模型但描述相变分数而非空间扩散")]
    input_fields = [InputField("k", "JMAK速率参数", "number", unit="1/s", min_value=1e-300), InputField("avrami_exponent", "Avrami指数", "number", unit="dimensionless", min_value=1e-12), InputField("times_s", "时间数组", "array", items={"type":"number","minimum":0})]
    output_fields = [OutputField("curve", "转变曲线", "array"), OutputField("half_time_s", "半转变时间", "number", "s"), OutputField("k", "速率参数", "number", "1/s"), OutputField("avrami_exponent", "Avrami指数", "number", "dimensionless"), OutputField("method", "方法", "string")]
    validation_rules = [{"rule":"positive","fields":["k","avrami_exponent"]},{"rule":"nonnegative_array","field":"times_s"}]
    qualification_cases = [
        {"id":"C004-N1","kind":"normal","input":{"k":0.01,"avrami_exponent":2,"times_s":[0,10,20]}},
        {"id":"C004-N2","kind":"normal","input":{"k":0.1,"avrami_exponent":1,"times_s":[1,2,3]}},
        {"id":"C004-N3","kind":"normal","input":{"k":0.001,"avrami_exponent":3,"times_s":[0,100,1000]}},
        {"id":"C004-F1","kind":"failure","input":{"k":0,"avrami_exponent":2,"times_s":[1]}},
        {"id":"C004-F2","kind":"failure","input":{"k":1,"avrami_exponent":2,"times_s":[-1]}},
    ]

    def invoke(self, params, context=None):
        k = float(params["k"]); exponent = float(params["avrami_exponent"]); times = params["times_s"]
        if not times or any(isinstance(t, bool) or not math.isfinite(float(t)) or float(t) < 0 for t in times):
            return fail("times_s必须是非空、有限、非负时间数组")
        curve = [{"time_s":float(t),"fraction_transformed":1.0-math.exp(-((k*float(t))**exponent))} for t in times]
        half_time = math.log(2.0)**(1.0/exponent)/k
        return ModelResult(True, result={"curve":curve,"half_time_s":half_time,"k":k,"avrami_exponent":exponent,"method":"JMAK"})
