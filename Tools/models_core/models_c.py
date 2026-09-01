"""Qualified kinetics and diffusion tools for the 30-tool milestone."""
from __future__ import annotations

import math

import numpy as np
from scipy.linalg import solve_banded

from .base import (
    BaseModelTool,
    BoundaryCheck,
    BoundaryWarning,
    InputField,
    ModelResult,
    OutputField,
)
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


class C103_Fick1DNumerical(KineticsTool):
    """Finite-volume solver for the workbook's general C003 capability."""

    model_id, name = "C103", "一维 Fick 数值扩散"
    tool_name = "metallurgy_solve_fick_1d"
    version = "1.0.0"
    source_version = "2026.09-p1-w6a"
    description = "用隐式有限体积法求解有限一维域、分段时空扩散系数下的Fick第二定律。"
    applicable_boundary = (
        "一维无源扩散；D(t,x)按输入时间段和单元分段常数且严格为正；"
        "支持定浓度或零通量边界，3～200个网格且不超过5000个时间步。"
    )
    formula_reference = (
        "∂C/∂t=∂/∂x(D∂C/∂x); cell-centred finite volume, harmonic face D, "
        "backward Euler tridiagonal solve"
    )
    source_records = [
        {
            "source_id": "NIST-FIPY-1D-DIFFUSION",
            "name": "NIST FiPy one-dimensional diffusion example and finite-volume discretization",
            "version": "accessed-2026-09-01",
            "url": "https://www.ctcms.nist.gov/~wd15/fipy/examples/diffusion/generated/examples.diffusion.mesh1D.html",
        },
        {
            "source_id": "SCIPY-SOLVE-BANDED-1.18.1",
            "name": "SciPy solve_banded",
            "version": "1.18.1",
            "url": "https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.solve_banded.html",
        },
    ]
    data_source = ["公开控制方程和数值离散；扩散参数由调用者提供并标明来源"]
    failure_modes = [
        "网格数、初值数组或扩散系数数组长度不一致",
        "扩散系数、域长或时间步非正",
        "扩散系数时间剖面未覆盖计算时长或不是严格递增",
        "固定浓度边界缺少边界值",
        "超过5000时间步、线性求解非有限或质量闭合失败",
    ]
    independent_validation = [
        "双零通量边界下离散总库存守恒",
        "均匀初值和零通量边界下常数解不变",
        "常D恒表面浓度结果可与C003误差函数解析解比较",
        "每步库存变化等于净边界通量时间积分",
    ]
    dependencies = ["C002"]
    relations = [
        rel("depends_on", "C002", "可把C002返回的扩散系数作为各时间段的标量D输入"),
        rel("overlaps", "C003", "两者都输出一维浓度剖面；C003是半无限常D解析解，本工具是有限域数值解"),
    ]
    _profile_item = {
        "type": "object",
        "properties": {
            "end_time_s": {"type": "number", "exclusiveMinimum": 0},
            "diffusivity_m2_s": {"type": "number", "exclusiveMinimum": 0},
            "cell_diffusivities_m2_s": {
                "type": "array",
                "items": {"type": "number", "exclusiveMinimum": 0},
                "minItems": 3,
                "maxItems": 200,
            },
        },
        "required": ["end_time_s"],
        "oneOf": [
            {"required": ["diffusivity_m2_s"]},
            {"required": ["cell_diffusivities_m2_s"]},
        ],
        "additionalProperties": False,
    }
    input_fields = [
        InputField("domain_length_m", "一维域长度", "number", unit="m", min_value=1e-12),
        InputField("grid_cells", "有限体积单元数", "number", unit="count", min_value=3, max_value=200),
        InputField("duration_s", "计算总时长", "number", unit="s", min_value=1e-12),
        InputField("time_step_s", "名义时间步", "number", unit="s", min_value=1e-12),
        InputField(
            "initial_concentrations", "各单元初始浓度", "array",
            unit="$concentration_unit", items={"type": "number"}, min_items=3, max_items=200,
        ),
        InputField(
            "diffusivity_profiles", "分段时空扩散系数", "array", items=_profile_item,
            min_items=1, max_items=100,
            description="按end_time_s严格递增；每段提供一个标量D或长度等于grid_cells的单元D数组",
        ),
        InputField("left_boundary_type", "左边界类型", "select", enum=["fixed_concentration", "zero_flux"]),
        InputField("right_boundary_type", "右边界类型", "select", enum=["fixed_concentration", "zero_flux"]),
        InputField("left_boundary_value", "左定浓度值", "number", required=False, unit="$concentration_unit"),
        InputField("right_boundary_value", "右定浓度值", "number", required=False, unit="$concentration_unit"),
        InputField("concentration_unit", "浓度单位", "select", enum=["1", "mol/m3", "kg/m3"]),
        InputField("diffusivity_source", "扩散参数来源", "string"),
        InputField("diffusivity_version", "扩散参数版本", "string"),
        InputField("snapshot_stride", "历史输出步长", "number", required=False, default=10, unit="step", min_value=1, max_value=5000),
    ]
    output_fields = [
        OutputField("positions_m", "单元中心位置", "array", "m"),
        OutputField("final_concentrations", "终态浓度", "array", "$concentration_unit"),
        OutputField("time_history", "抽样浓度历史", "array", "time:s; concentration:$concentration_unit"),
        OutputField("left_inward_flux", "左边界向域内通量", "number", "$concentration_unit·m/s"),
        OutputField("right_outward_flux", "右边界向域外通量", "number", "$concentration_unit·m/s"),
        OutputField("initial_inventory", "初始线库存", "number", "$concentration_unit·m"),
        OutputField("final_inventory", "终态线库存", "number", "$concentration_unit·m"),
        OutputField("cumulative_net_boundary_transfer", "累计净边界传递", "number", "$concentration_unit·m"),
        OutputField("mass_balance_residual", "质量闭合残差", "number", "$concentration_unit·m"),
        OutputField("relative_mass_balance_error", "相对质量闭合误差", "number", "1"),
        OutputField("max_fourier_number", "最大网格Fourier数", "number", "1"),
        OutputField("time_steps", "实际时间步数", "number", "count"),
        OutputField("concentration_unit", "浓度单位", "string"),
        OutputField("diffusivity_source", "扩散参数来源", "string"),
        OutputField("diffusivity_version", "扩散参数版本", "string"),
        OutputField("method", "数值方法", "string"),
    ]
    validation_rules = [
        {"rule": "integer_range", "field": "grid_cells", "minimum": 3, "maximum": 200},
        {"rule": "strictly_increasing", "field": "diffusivity_profiles.end_time_s"},
        {"rule": "mass_closure", "relative_tolerance": 1e-8},
    ]
    qualification_cases = [
        {
            "id": "C103-N1", "kind": "normal",
            "input": {"domain_length_m": 0.01, "grid_cells": 3, "duration_s": 10, "time_step_s": 1,
                      "initial_concentrations": [1, 1, 1],
                      "diffusivity_profiles": [{"end_time_s": 10, "diffusivity_m2_s": 1e-8}],
                      "left_boundary_type": "zero_flux", "right_boundary_type": "zero_flux",
                      "concentration_unit": "1", "diffusivity_source": "qualification-uniform",
                      "diffusivity_version": "v1"},
        },
        {
            "id": "C103-N2", "kind": "normal",
            "input": {"domain_length_m": 0.005, "grid_cells": 5, "duration_s": 100, "time_step_s": 5,
                      "initial_concentrations": [0, 0, 0, 0, 0],
                      "diffusivity_profiles": [{"end_time_s": 100, "diffusivity_m2_s": 1e-8}],
                      "left_boundary_type": "fixed_concentration", "left_boundary_value": 1,
                      "right_boundary_type": "zero_flux", "concentration_unit": "mol/m3",
                      "diffusivity_source": "qualification-dirichlet", "diffusivity_version": "v1"},
        },
        {
            "id": "C103-N3", "kind": "normal",
            "input": {"domain_length_m": 0.004, "grid_cells": 4, "duration_s": 20, "time_step_s": 2,
                      "initial_concentrations": [1, 0.8, 0.2, 0],
                      "diffusivity_profiles": [
                          {"end_time_s": 8, "cell_diffusivities_m2_s": [1e-9, 2e-9, 3e-9, 4e-9]},
                          {"end_time_s": 20, "cell_diffusivities_m2_s": [2e-9, 2e-9, 2e-9, 2e-9]}],
                      "left_boundary_type": "zero_flux", "right_boundary_type": "fixed_concentration",
                      "right_boundary_value": 0, "concentration_unit": "kg/m3",
                      "diffusivity_source": "qualification-variable", "diffusivity_version": "v1"},
        },
        {
            "id": "C103-F1", "kind": "failure",
            "input": {"domain_length_m": 0.01, "grid_cells": 3, "duration_s": 1, "time_step_s": 1,
                      "initial_concentrations": [0, 0],
                      "diffusivity_profiles": [{"end_time_s": 1, "diffusivity_m2_s": 1e-9}],
                      "left_boundary_type": "zero_flux", "right_boundary_type": "zero_flux",
                      "concentration_unit": "1", "diffusivity_source": "failure", "diffusivity_version": "v1"},
        },
        {
            "id": "C103-F2", "kind": "failure",
            "input": {"domain_length_m": 0.01, "grid_cells": 3, "duration_s": 10, "time_step_s": 1,
                      "initial_concentrations": [0, 0, 0],
                      "diffusivity_profiles": [{"end_time_s": 5, "diffusivity_m2_s": 1e-9}],
                      "left_boundary_type": "zero_flux", "right_boundary_type": "zero_flux",
                      "concentration_unit": "1", "diffusivity_source": "failure", "diffusivity_version": "v1"},
        },
    ]

    @staticmethod
    def _finite_number(value, label):
        if isinstance(value, bool):
            raise ValueError(f"{label}必须是有限数值")
        number = float(value)
        if not math.isfinite(number):
            raise ValueError(f"{label}必须是有限数值")
        return number

    def _parse_profiles(self, raw_profiles, cells, duration):
        if not isinstance(raw_profiles, list) or not raw_profiles:
            raise ValueError("diffusivity_profiles必须是非空数组")
        parsed = []
        previous_end = 0.0
        for index, item in enumerate(raw_profiles):
            if not isinstance(item, dict):
                raise ValueError(f"diffusivity_profiles[{index}]必须是对象")
            allowed = {"end_time_s", "diffusivity_m2_s", "cell_diffusivities_m2_s"}
            if set(item) - allowed:
                raise ValueError(f"diffusivity_profiles[{index}]包含未声明字段")
            end_time = self._finite_number(item.get("end_time_s"), f"diffusivity_profiles[{index}].end_time_s")
            if end_time <= previous_end:
                raise ValueError("扩散系数时间段end_time_s必须严格递增且大于0")
            has_scalar = "diffusivity_m2_s" in item
            has_cells = "cell_diffusivities_m2_s" in item
            if has_scalar == has_cells:
                raise ValueError("每个扩散系数时间段必须且只能提供标量D或单元D数组")
            if has_scalar:
                value = self._finite_number(item["diffusivity_m2_s"], "diffusivity_m2_s")
                diffusivities = np.full(cells, value, dtype=float)
            else:
                raw_cells = item["cell_diffusivities_m2_s"]
                if not isinstance(raw_cells, list) or len(raw_cells) != cells:
                    raise ValueError("cell_diffusivities_m2_s长度必须等于grid_cells")
                diffusivities = np.asarray([
                    self._finite_number(value, "cell_diffusivities_m2_s") for value in raw_cells
                ], dtype=float)
            if np.any(diffusivities <= 0):
                raise ValueError("所有扩散系数必须为有限正数")
            parsed.append((end_time, diffusivities))
            previous_end = end_time
        if previous_end + 1e-12 < duration:
            raise ValueError("扩散系数时间剖面未覆盖duration_s")
        return parsed

    def invoke(self, params, context=None):
        try:
            length = self._finite_number(params["domain_length_m"], "domain_length_m")
            duration = self._finite_number(params["duration_s"], "duration_s")
            nominal_dt = self._finite_number(params["time_step_s"], "time_step_s")
            cells_number = self._finite_number(params["grid_cells"], "grid_cells")
            if not cells_number.is_integer():
                return fail("grid_cells必须是整数")
            cells = int(cells_number)
            if not 3 <= cells <= 200:
                return fail("grid_cells必须在3到200之间", "OUT_OF_DOMAIN")
            if math.ceil(duration / nominal_dt) > 5000:
                return fail("时间步数超过5000；请增大time_step_s或缩短duration_s", "OUT_OF_DOMAIN")
            initial_raw = params["initial_concentrations"]
            if not isinstance(initial_raw, list) or len(initial_raw) != cells:
                return fail("initial_concentrations长度必须等于grid_cells")
            concentrations = np.asarray([
                self._finite_number(value, "initial_concentrations") for value in initial_raw
            ], dtype=float)
            profiles = self._parse_profiles(params["diffusivity_profiles"], cells, duration)
            left_type = params["left_boundary_type"]
            right_type = params["right_boundary_type"]
            left_value = params.get("left_boundary_value")
            right_value = params.get("right_boundary_value")
            if left_type == "fixed_concentration" and left_value is None:
                return fail("fixed_concentration左边界必须提供left_boundary_value")
            if right_type == "fixed_concentration" and right_value is None:
                return fail("fixed_concentration右边界必须提供right_boundary_value")
            if left_value is not None:
                left_value = self._finite_number(left_value, "left_boundary_value")
            if right_value is not None:
                right_value = self._finite_number(right_value, "right_boundary_value")
            snapshot_number = self._finite_number(params.get("snapshot_stride", 10), "snapshot_stride")
            if not snapshot_number.is_integer():
                return fail("snapshot_stride必须是整数")
            snapshot_stride = int(snapshot_number)
        except (KeyError, TypeError, ValueError) as exc:
            return fail(str(exc))

        dx = length / cells
        positions = (np.arange(cells, dtype=float) + 0.5) * dx
        initial_inventory = float(np.sum(concentrations) * dx)
        cumulative_transfer = 0.0
        current_time = 0.0
        profile_index = 0
        step = 0
        max_fo = 0.0
        left_flux = 0.0
        right_flux = 0.0
        history = [{"time_s": 0.0, "concentrations": concentrations.tolist()}]
        tolerance = max(1e-14, duration * 1e-14)

        try:
            while current_time < duration - tolerance:
                while profile_index < len(profiles) - 1 and current_time >= profiles[profile_index][0] - tolerance:
                    profile_index += 1
                profile_end, diffusivities = profiles[profile_index]
                dt = min(nominal_dt, duration - current_time, profile_end - current_time)
                if dt <= tolerance:
                    profile_index += 1
                    continue
                step += 1
                if step > 5000:
                    return fail("分段边界细分后时间步数超过5000", "OUT_OF_DOMAIN")
                face_d = 2.0 * diffusivities[:-1] * diffusivities[1:] / (
                    diffusivities[:-1] + diffusivities[1:]
                )
                alpha = dt * face_d / (dx * dx)
                diagonal = np.ones(cells, dtype=float)
                upper = np.zeros(cells - 1, dtype=float)
                lower = np.zeros(cells - 1, dtype=float)
                rhs = concentrations.copy()
                diagonal[:-1] += alpha
                diagonal[1:] += alpha
                upper[:] = -alpha
                lower[:] = -alpha
                if left_type == "fixed_concentration":
                    beta = 2.0 * dt * diffusivities[0] / (dx * dx)
                    diagonal[0] += beta
                    rhs[0] += beta * left_value
                if right_type == "fixed_concentration":
                    beta = 2.0 * dt * diffusivities[-1] / (dx * dx)
                    diagonal[-1] += beta
                    rhs[-1] += beta * right_value
                banded = np.zeros((3, cells), dtype=float)
                banded[0, 1:] = upper
                banded[1, :] = diagonal
                banded[2, :-1] = lower
                concentrations = solve_banded((1, 1), banded, rhs, check_finite=True)
                if not np.all(np.isfinite(concentrations)):
                    return fail("线性方程组产生非有限浓度", "NUMERICAL_ERROR")
                left_flux = (
                    2.0 * diffusivities[0] * (left_value - concentrations[0]) / dx
                    if left_type == "fixed_concentration" else 0.0
                )
                right_flux = (
                    2.0 * diffusivities[-1] * (concentrations[-1] - right_value) / dx
                    if right_type == "fixed_concentration" else 0.0
                )
                cumulative_transfer += dt * (left_flux - right_flux)
                current_time += dt
                max_fo = max(max_fo, float(np.max(diffusivities) * dt / (dx * dx)))
                if step % snapshot_stride == 0 or current_time >= duration - tolerance:
                    history.append({"time_s": current_time, "concentrations": concentrations.tolist()})
        except (ValueError, np.linalg.LinAlgError) as exc:
            return fail(f"一维扩散线性求解失败: {exc}", "NUMERICAL_ERROR")

        final_inventory = float(np.sum(concentrations) * dx)
        residual = final_inventory - initial_inventory - cumulative_transfer
        scale = max(abs(initial_inventory), abs(final_inventory), abs(cumulative_transfer), 1e-30)
        relative_error = abs(residual) / scale
        if relative_error > 1e-8:
            return fail(f"质量闭合相对误差{relative_error:.3e}超过1e-8", "NUMERICAL_ERROR")
        boundary = BoundaryCheck()
        if max_fo > 1.0:
            boundary = BoundaryCheck(False, [BoundaryWarning(
                "time_step_s", "隐式格式稳定但最大Fourier数大于1，建议缩小时间步检查时间离散精度"
            )])
        return ModelResult(True, result={
            "positions_m": positions.tolist(),
            "final_concentrations": concentrations.tolist(),
            "time_history": history,
            "left_inward_flux": float(left_flux),
            "right_outward_flux": float(right_flux),
            "initial_inventory": initial_inventory,
            "final_inventory": final_inventory,
            "cumulative_net_boundary_transfer": cumulative_transfer,
            "mass_balance_residual": residual,
            "relative_mass_balance_error": relative_error,
            "max_fourier_number": max_fo,
            "time_steps": step,
            "concentration_unit": params["concentration_unit"],
            "diffusivity_source": params["diffusivity_source"],
            "diffusivity_version": params["diffusivity_version"],
            "method": "cell-centred finite volume / harmonic face D / backward Euler",
        }, boundary_check=boundary)


class C005_GrainGrowth(KineticsTool):
    model_id, name = "C005", "正常晶粒长大动力学"
    tool_name = "metallurgy_predict_grain_growth"
    version = "1.0.0"
    source_version = "2026.09-p1-w6a"
    description = "按分段等温Arrhenius晶粒长大律计算平均晶粒直径历程。"
    applicable_boundary = "正常、各向同性平均晶粒长大；参数在输入温区有效，不适用于异常长大或钉扎机制突变。"
    formula_reference = "D^n-D0^n=Σ K0 exp[-Q/(RT_i)] Δt_i"
    source_records = [{
        "source_id": "BURKE-TURNBULL-1952",
        "name": "Recrystallization and grain growth",
        "version": "Progress in Metal Physics 3 (1952) 220-292",
        "url": "https://doi.org/10.1016/0502-8205(52)90009-9",
    }]
    data_source = ["公开晶粒长大关系；全部材料参数由调用者提供并标明来源"]
    failure_modes = ["初始尺寸、指数、K0或温度非正", "激活能或分段时长为负", "温程为空", "计算结果非有限"]
    independent_validation = ["单段温程与闭式解一致", "分段长大项具有可加性", "Q=0时退化为D^n-D0^n=K0t", "最终尺寸代回公式残差为零"]
    dependencies = []
    relations = [
        rel("shares_model_form_with", "C001", "温度因子使用与C001相同的Arrhenius指数结构"),
        rel("distinct_from", "C004", "C004输出相变分数，本工具输出平均晶粒直径"),
    ]
    _segment_item = {
        "type": "object",
        "properties": {
            "temperature_k": {"type": "number", "exclusiveMinimum": 0},
            "duration_s": {"type": "number", "minimum": 0},
        },
        "required": ["temperature_k", "duration_s"],
        "additionalProperties": False,
    }
    input_fields = [
        InputField("initial_grain_diameter_m", "初始平均晶粒直径", "number", unit="m", min_value=1e-15),
        InputField("growth_exponent", "晶粒长大指数", "number", unit="1", min_value=1e-6, max_value=10),
        InputField("rate_prefactor_m_power_per_s", "晶粒长大指前因子", "number", unit="m^n/s", min_value=1e-300),
        InputField("activation_energy_j_mol", "晶粒长大激活能", "number", unit="J/mol", min_value=0),
        InputField("temperature_segments", "分段等温温程", "array", items=_segment_item, min_items=1, max_items=100),
        InputField("parameter_source", "材料参数来源", "string"),
        InputField("parameter_version", "材料参数版本", "string"),
    ]
    output_fields = [
        OutputField("initial_grain_diameter_m", "初始平均晶粒直径", "number", "m"),
        OutputField("final_grain_diameter_m", "最终平均晶粒直径", "number", "m"),
        OutputField("growth_exponent", "晶粒长大指数", "number", "1"),
        OutputField("integrated_growth_term_m_power", "累计长大项", "number", "m^n"),
        OutputField("total_time_s", "总保温时间", "number", "s"),
        OutputField("history", "各温段晶粒尺寸历程", "array", "temperature:K; duration:s; diameter:m"),
        OutputField("formula_residual_m_power", "公式回代残差", "number", "m^n"),
        OutputField("parameter_source", "材料参数来源", "string"),
        OutputField("parameter_version", "材料参数版本", "string"),
        OutputField("method", "计算方法", "string"),
    ]
    validation_rules = [{"rule": "positive", "fields": ["initial_grain_diameter_m", "growth_exponent", "rate_prefactor_m_power_per_s"]}, {"rule": "nonnegative", "field": "activation_energy_j_mol"}]
    qualification_cases = [
        {"id":"C005-N1","kind":"normal","input":{"initial_grain_diameter_m":1e-5,"growth_exponent":2,"rate_prefactor_m_power_per_s":1e-8,"activation_energy_j_mol":100000,"temperature_segments":[{"temperature_k":1000,"duration_s":3600}],"parameter_source":"qualification","parameter_version":"v1"}},
        {"id":"C005-N2","kind":"normal","input":{"initial_grain_diameter_m":2e-5,"growth_exponent":2,"rate_prefactor_m_power_per_s":1e-14,"activation_energy_j_mol":0,"temperature_segments":[{"temperature_k":800,"duration_s":100}],"parameter_source":"qualification-zero-Q","parameter_version":"v1"}},
        {"id":"C005-N3","kind":"normal","input":{"initial_grain_diameter_m":5e-6,"growth_exponent":3,"rate_prefactor_m_power_per_s":1e-12,"activation_energy_j_mol":120000,"temperature_segments":[{"temperature_k":900,"duration_s":600},{"temperature_k":1100,"duration_s":300}],"parameter_source":"qualification-segments","parameter_version":"v1"}},
        {"id":"C005-F1","kind":"failure","input":{"initial_grain_diameter_m":1e-5,"growth_exponent":2,"rate_prefactor_m_power_per_s":1e-12,"activation_energy_j_mol":1,"temperature_segments":[],"parameter_source":"failure","parameter_version":"v1"}},
        {"id":"C005-F2","kind":"failure","input":{"initial_grain_diameter_m":1e-5,"growth_exponent":2,"rate_prefactor_m_power_per_s":1e-12,"activation_energy_j_mol":1,"temperature_segments":[{"temperature_k":1000,"duration_s":-1}],"parameter_source":"failure","parameter_version":"v1"}},
    ]

    def invoke(self, params, context=None):
        segments = params["temperature_segments"]
        if not isinstance(segments, list) or not segments:
            return fail("temperature_segments必须是非空数组")
        diameter0 = float(params["initial_grain_diameter_m"])
        exponent = float(params["growth_exponent"])
        prefactor = float(params["rate_prefactor_m_power_per_s"])
        activation = float(params["activation_energy_j_mol"])
        accumulated = 0.0
        total_time = 0.0
        history = []
        allowed = {"temperature_k", "duration_s"}
        try:
            for index, segment in enumerate(segments):
                if not isinstance(segment, dict) or set(segment) != allowed:
                    return fail(f"temperature_segments[{index}]必须且只能包含temperature_k和duration_s")
                temperature = float(segment["temperature_k"])
                duration = float(segment["duration_s"])
                if not math.isfinite(temperature) or temperature <= 0 or not math.isfinite(duration) or duration < 0:
                    return fail("温段温度必须为有限正数且时长必须为有限非负数")
                rate = prefactor * math.exp(-activation / (R_J_MOL_K * temperature))
                increment = rate * duration
                accumulated += increment
                total_time += duration
                diameter = (diameter0 ** exponent + accumulated) ** (1.0 / exponent)
                history.append({"temperature_k": temperature, "duration_s": duration, "rate_m_power_per_s": rate, "increment_m_power": increment, "grain_diameter_m": diameter})
        except (KeyError, TypeError, ValueError, OverflowError) as exc:
            return fail(f"温程解析失败: {exc}")
        final = (diameter0 ** exponent + accumulated) ** (1.0 / exponent)
        if not math.isfinite(final):
            return fail("晶粒尺寸计算产生非有限结果", "NUMERICAL_ERROR")
        residual = final ** exponent - diameter0 ** exponent - accumulated
        return ModelResult(True, result={
            "initial_grain_diameter_m": diameter0,
            "final_grain_diameter_m": final,
            "growth_exponent": exponent,
            "integrated_growth_term_m_power": accumulated,
            "total_time_s": total_time,
            "history": history,
            "formula_residual_m_power": residual,
            "parameter_source": params["parameter_source"],
            "parameter_version": params["parameter_version"],
            "method": "piecewise-isothermal normal grain growth law",
        })


class C006_ShrinkingCore(KineticsTool):
    model_id, name = "C006", "球形颗粒缩核反应"
    tool_name = "metallurgy_solve_shrinking_core"
    version = "1.0.0"
    source_version = "2026.09-p1-w6a"
    description = "按膜传质、表面反应和产物层扩散加成时间求球形颗粒转化率。"
    applicable_boundary = "等温球形非多孔颗粒、拟稳态、恒定气相浓度；至少启用一种阻力。"
    formula_reference = "t=τf X+τr[1-(1-X)^(1/3)]+τd[1-3(1-X)^(2/3)+2(1-X)]"
    source_records = [{
        "source_id": "SOHN-2019-ART",
        "name": "The law of additive reaction times in fluid-solid reactions",
        "version": "Canadian Journal of Chemical Engineering 2019",
        "url": "https://doi.org/10.1002/cjce.23468",
    }]
    data_source = ["公开缩核模型；传质、反应和扩散参数由调用者提供"]
    failure_modes = ["颗粒或浓度物性非正", "三种阻力均未启用", "时间为负", "系数非有限", "求根未闭合"]
    independent_validation = ["纯膜控制X=t/τf", "纯反应控制闭式反演", "纯产物层扩散时间函数", "混合阻力时间函数严格单调且端点闭合"]
    dependencies = []
    relations = [rel("shares_parameter_path_with", "C001", "C001可用于温度修正表面反应速率常数，但本工具还包含传质阻力")]
    input_fields = [
        InputField("particle_radius_m", "初始颗粒半径", "number", unit="m", min_value=1e-12),
        InputField("solid_molar_density_mol_m3", "固体B摩尔密度", "number", unit="mol/m3", min_value=1e-12),
        InputField("gas_concentration_mol_m3", "气相反应物A浓度", "number", unit="mol/m3", min_value=1e-12),
        InputField("solid_moles_per_gas_mole", "每摩尔气体A对应的固体B化学计量数b", "number", unit="mol B/mol A", min_value=1e-12),
        InputField("time_s", "反应时间", "number", unit="s", min_value=0),
        InputField("film_mass_transfer_coefficient_m_s", "膜传质系数", "number", required=False, unit="m/s", min_value=1e-300),
        InputField("surface_reaction_rate_constant_m_s", "表面反应速率常数", "number", required=False, unit="m/s", min_value=1e-300),
        InputField("product_layer_diffusivity_m2_s", "产物层有效扩散系数", "number", required=False, unit="m²/s", min_value=1e-300),
        InputField("parameter_source", "动力学参数来源", "string"),
        InputField("parameter_version", "动力学参数版本", "string"),
    ]
    output_fields = [
        OutputField("conversion_fraction", "固体转化分数", "number", "1"),
        OutputField("unreacted_core_radius_m", "未反应核半径", "number", "m"),
        OutputField("film_time_contribution_s", "膜传质时间贡献", "number", "s"),
        OutputField("surface_reaction_time_contribution_s", "表面反应时间贡献", "number", "s"),
        OutputField("product_layer_time_contribution_s", "产物层扩散时间贡献", "number", "s"),
        OutputField("complete_conversion_time_s", "理论完全转化时间", "number", "s"),
        OutputField("dominant_resistance", "完全转化时主控阻力", "string"),
        OutputField("time_residual_s", "反演时间残差", "number", "s"),
        OutputField("parameter_source", "动力学参数来源", "string"),
        OutputField("parameter_version", "动力学参数版本", "string"),
        OutputField("method", "计算方法", "string"),
    ]
    validation_rules = [{"rule": "positive", "fields": ["particle_radius_m", "solid_molar_density_mol_m3", "gas_concentration_mol_m3", "solid_moles_per_gas_mole"]}, {"rule": "at_least_one_present", "fields": ["film_mass_transfer_coefficient_m_s", "surface_reaction_rate_constant_m_s", "product_layer_diffusivity_m2_s"]}]
    qualification_cases = [
        {"id":"C006-N1","kind":"normal","input":{"particle_radius_m":0.001,"solid_molar_density_mol_m3":50000,"gas_concentration_mol_m3":10,"solid_moles_per_gas_mole":1,"time_s":10,"film_mass_transfer_coefficient_m_s":0.01,"parameter_source":"qualification-film","parameter_version":"v1"}},
        {"id":"C006-N2","kind":"normal","input":{"particle_radius_m":0.001,"solid_molar_density_mol_m3":50000,"gas_concentration_mol_m3":10,"solid_moles_per_gas_mole":1,"time_s":20,"surface_reaction_rate_constant_m_s":0.02,"parameter_source":"qualification-reaction","parameter_version":"v1"}},
        {"id":"C006-N3","kind":"normal","input":{"particle_radius_m":0.0005,"solid_molar_density_mol_m3":40000,"gas_concentration_mol_m3":20,"solid_moles_per_gas_mole":0.5,"time_s":5,"film_mass_transfer_coefficient_m_s":0.05,"surface_reaction_rate_constant_m_s":0.01,"product_layer_diffusivity_m2_s":1e-5,"parameter_source":"qualification-mixed","parameter_version":"v1"}},
        {"id":"C006-F1","kind":"failure","input":{"particle_radius_m":0.001,"solid_molar_density_mol_m3":50000,"gas_concentration_mol_m3":10,"solid_moles_per_gas_mole":1,"time_s":10,"parameter_source":"failure","parameter_version":"v1"}},
        {"id":"C006-F2","kind":"failure","input":{"particle_radius_m":0.001,"solid_molar_density_mol_m3":50000,"gas_concentration_mol_m3":10,"solid_moles_per_gas_mole":1,"time_s":-1,"film_mass_transfer_coefficient_m_s":0.01,"parameter_source":"failure","parameter_version":"v1"}},
    ]

    @staticmethod
    def _shape_terms(conversion):
        remaining = max(0.0, 1.0 - conversion)
        root = remaining ** (1.0 / 3.0)
        return conversion, 1.0 - root, 1.0 - 3.0 * root * root + 2.0 * remaining

    def invoke(self, params, context=None):
        radius = float(params["particle_radius_m"])
        rho_b = float(params["solid_molar_density_mol_m3"])
        concentration = float(params["gas_concentration_mol_m3"])
        stoich = float(params["solid_moles_per_gas_mole"])
        time_s = float(params["time_s"])
        coefficients = {
            "film_mass_transfer": params.get("film_mass_transfer_coefficient_m_s"),
            "surface_reaction": params.get("surface_reaction_rate_constant_m_s"),
            "product_layer_diffusion": params.get("product_layer_diffusivity_m2_s"),
        }
        active = {key: float(value) for key, value in coefficients.items() if value is not None}
        if not active:
            return fail("至少必须提供一种膜传质、表面反应或产物层扩散系数")
        if any(not math.isfinite(value) or value <= 0 for value in active.values()):
            return fail("启用的传质、反应和扩散系数必须为有限正数")
        denominator = stoich * concentration
        taus = {
            "film_mass_transfer": rho_b * radius / (3.0 * denominator * active["film_mass_transfer"]) if "film_mass_transfer" in active else 0.0,
            "surface_reaction": rho_b * radius / (denominator * active["surface_reaction"]) if "surface_reaction" in active else 0.0,
            "product_layer_diffusion": rho_b * radius * radius / (6.0 * denominator * active["product_layer_diffusion"]) if "product_layer_diffusion" in active else 0.0,
        }
        complete_time = sum(taus.values())

        def required_time(conversion):
            film_shape, reaction_shape, diffusion_shape = self._shape_terms(conversion)
            return (taus["film_mass_transfer"] * film_shape
                    + taus["surface_reaction"] * reaction_shape
                    + taus["product_layer_diffusion"] * diffusion_shape)

        if time_s <= 0:
            conversion = 0.0
        elif time_s >= complete_time:
            conversion = 1.0
        else:
            low, high = 0.0, 1.0
            for _ in range(100):
                midpoint = 0.5 * (low + high)
                if required_time(midpoint) < time_s:
                    low = midpoint
                else:
                    high = midpoint
            conversion = 0.5 * (low + high)
        film_shape, reaction_shape, diffusion_shape = self._shape_terms(conversion)
        contributions = {
            "film": taus["film_mass_transfer"] * film_shape,
            "reaction": taus["surface_reaction"] * reaction_shape,
            "diffusion": taus["product_layer_diffusion"] * diffusion_shape,
        }
        residual = sum(contributions.values()) - min(time_s, complete_time)
        if abs(residual) > max(1e-10, complete_time * 1e-10):
            return fail("缩核模型二分反演未达到时间闭合容差", "NUMERICAL_ERROR")
        dominant = max(taus, key=taus.get)
        return ModelResult(True, result={
            "conversion_fraction": conversion,
            "unreacted_core_radius_m": radius * max(0.0, 1.0 - conversion) ** (1.0 / 3.0),
            "film_time_contribution_s": contributions["film"],
            "surface_reaction_time_contribution_s": contributions["reaction"],
            "product_layer_time_contribution_s": contributions["diffusion"],
            "complete_conversion_time_s": complete_time,
            "dominant_resistance": dominant,
            "time_residual_s": residual,
            "parameter_source": params["parameter_source"],
            "parameter_version": params["parameter_version"],
            "method": "spherical shrinking-core model / additive reaction times",
        })


class C007_ParabolicOxidation(KineticsTool):
    model_id, name = "C007", "抛物线氧化动力学"
    tool_name = "metallurgy_predict_parabolic_oxidation"
    version = "1.0.0"
    source_version = "2026.09-p1-w6a"
    description = "按厚膜扩散控制抛物线律计算氧化增重与等效氧化层厚度。"
    applicable_boundary = "致密附着单层等效氧化皮的厚膜扩散控制；不适用于薄膜、线性氧化、失稳氧化或剥落。"
    formula_reference = "(Δm/A)^2=(Δm/A)_0^2+k_p t; x=(Δm/A)/(ρ_oxide w_oxidant)"
    source_records = [
        {"source_id":"ATKINSON-WAGNER-1988","name":"Wagner theory and short circuit diffusion","version":"Materials Science and Technology 4 (1988)","url":"https://doi.org/10.1179/mst.1988.4.12.1046"},
        {"source_id":"NIST-JRES-OXIDATION","name":"Rate of Oxidation of Nonferrous Metals","version":"NBS Journal of Research 28","url":"https://nvlpubs.nist.gov/nistpubs/jres/28/jresv28n5p593_A1b.pdf"},
    ]
    data_source = ["公开Wagner抛物线关系；温度/气氛对应的kp和氧化物参数由调用者提供"]
    failure_modes = ["kp、温度或密度非正", "时间或初始增重为负", "氧化剂质量分数不在(0,1]", "观测机制不是保护性抛物线氧化"]
    independent_validation = ["增重平方对时间为斜率kp的直线", "t=0恢复初始增重", "质量增重按密度和氧化剂质量分数换算厚度", "公式回代残差为零"]
    dependencies = []
    relations = [rel("shares_parameter_path_with", "C001", "kp可按Arrhenius关系做温度修正，但本工具只使用指定温度下的已知kp")]
    input_fields = [
        InputField("temperature_k", "氧化温度", "number", unit="K", min_value=1e-12),
        InputField("time_s", "氧化时间", "number", unit="s", min_value=0),
        InputField("parabolic_rate_constant_kg2_m4_s", "质量增重抛物线速率常数", "number", unit="kg²/(m⁴·s)", min_value=1e-300),
        InputField("initial_mass_gain_kg_m2", "初始单位面积增重", "number", required=False, default=0, unit="kg/m²", min_value=0),
        InputField("oxide_density_kg_m3", "等效氧化物密度", "number", unit="kg/m³", min_value=1e-12),
        InputField("oxidant_mass_fraction_in_oxide", "氧化剂在氧化物中的质量分数", "number", unit="1", min_value=1e-12, max_value=1),
        InputField("observed_regime", "已确认的氧化机制", "select", enum=["protective_parabolic", "thin_film", "linear", "breakaway_or_spalling"]),
        InputField("parameter_source", "速率常数与氧化物参数来源", "string"),
        InputField("parameter_version", "参数版本", "string"),
    ]
    output_fields = [
        OutputField("mass_gain_kg_m2", "终态单位面积增重", "number", "kg/m²"),
        OutputField("parabolic_increment_kg2_m4", "增重平方增量", "number", "kg²/m⁴"),
        OutputField("equivalent_oxide_thickness_m", "等效氧化层厚度", "number", "m"),
        OutputField("instantaneous_mass_gain_rate_kg_m2_s", "终态瞬时增重速率", "number", "kg/(m²·s)", nullable=True),
        OutputField("formula_residual_kg2_m4", "公式回代残差", "number", "kg²/m⁴"),
        OutputField("temperature_k", "氧化温度", "number", "K"),
        OutputField("observed_regime", "氧化机制", "string"),
        OutputField("parameter_source", "参数来源", "string"),
        OutputField("parameter_version", "参数版本", "string"),
        OutputField("method", "计算方法", "string"),
    ]
    validation_rules = [{"rule":"positive","fields":["temperature_k","parabolic_rate_constant_kg2_m4_s","oxide_density_kg_m3","oxidant_mass_fraction_in_oxide"]},{"rule":"nonnegative","fields":["time_s","initial_mass_gain_kg_m2"]}]
    qualification_cases = [
        {"id":"C007-N1","kind":"normal","input":{"temperature_k":1200,"time_s":3600,"parabolic_rate_constant_kg2_m4_s":1e-10,"oxide_density_kg_m3":5200,"oxidant_mass_fraction_in_oxide":0.3,"observed_regime":"protective_parabolic","parameter_source":"qualification","parameter_version":"v1"}},
        {"id":"C007-N2","kind":"normal","input":{"temperature_k":1000,"time_s":0,"parabolic_rate_constant_kg2_m4_s":2e-12,"initial_mass_gain_kg_m2":0.01,"oxide_density_kg_m3":5000,"oxidant_mass_fraction_in_oxide":0.25,"observed_regime":"protective_parabolic","parameter_source":"qualification-initial","parameter_version":"v1"}},
        {"id":"C007-N3","kind":"normal","input":{"temperature_k":1400,"time_s":10000,"parabolic_rate_constant_kg2_m4_s":5e-11,"initial_mass_gain_kg_m2":0.002,"oxide_density_kg_m3":4500,"oxidant_mass_fraction_in_oxide":0.2,"observed_regime":"protective_parabolic","parameter_source":"qualification-high-T","parameter_version":"v2"}},
        {"id":"C007-F1","kind":"failure","input":{"temperature_k":1200,"time_s":10,"parabolic_rate_constant_kg2_m4_s":0,"oxide_density_kg_m3":5000,"oxidant_mass_fraction_in_oxide":0.3,"observed_regime":"protective_parabolic","parameter_source":"failure","parameter_version":"v1"}},
        {"id":"C007-F2","kind":"failure","input":{"temperature_k":1200,"time_s":10,"parabolic_rate_constant_kg2_m4_s":1e-10,"oxide_density_kg_m3":5000,"oxidant_mass_fraction_in_oxide":0.3,"observed_regime":"breakaway_or_spalling","parameter_source":"failure","parameter_version":"v1"}},
    ]

    def invoke(self, params, context=None):
        if params["observed_regime"] != "protective_parabolic":
            return fail("观测机制不是保护性抛物线氧化，Wagner厚膜模型不适用", "MODEL_NOT_APPLICABLE")
        temperature = float(params["temperature_k"])
        time_s = float(params["time_s"])
        rate_constant = float(params["parabolic_rate_constant_kg2_m4_s"])
        initial = float(params.get("initial_mass_gain_kg_m2", 0))
        density = float(params["oxide_density_kg_m3"])
        oxidant_fraction = float(params["oxidant_mass_fraction_in_oxide"])
        squared = initial * initial + rate_constant * time_s
        mass_gain = math.sqrt(squared)
        thickness = mass_gain / (density * oxidant_fraction)
        rate = rate_constant / (2.0 * mass_gain) if mass_gain > 0 else None
        residual = mass_gain * mass_gain - initial * initial - rate_constant * time_s
        return ModelResult(True, result={
            "mass_gain_kg_m2": mass_gain,
            "parabolic_increment_kg2_m4": rate_constant * time_s,
            "equivalent_oxide_thickness_m": thickness,
            "instantaneous_mass_gain_rate_kg_m2_s": rate,
            "formula_residual_kg2_m4": residual,
            "temperature_k": temperature,
            "observed_regime": params["observed_regime"],
            "parameter_source": params["parameter_source"],
            "parameter_version": params["parameter_version"],
            "method": "Wagner thick-film parabolic mass-gain law",
        })
