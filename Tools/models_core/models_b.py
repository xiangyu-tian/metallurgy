"""Qualified thermodynamics and phase-equilibrium tools for the 30-tool milestone."""
from __future__ import annotations

import math
from typing import Optional

from .base import BaseModelTool, BoundaryCheck, BoundaryWarning, InputField, InvocationContext, ModelResult, OutputField
from .models_a import normalize_composition, parse_formula
from .thermo_assets import R_J_MOL_K
from .repositories.reference_repository import RepositoryError, atomic_weights, nasa7, reaction_properties, shomate


SCENARIO = "热力学与相平衡"
THERMO_SOURCE = [{"source_id": "DS002", "name": "NIST-JANAF thermodynamic correlation records", "version": "1.0"}]
REACTION_SOURCE = [{"source_id": "DS002", "name": "NIST-JANAF/Barin reaction thermochemistry records", "version": "REACTION-THERMO-2026.08-v1"}]


def rel(kind, target, description):
    return {"type": kind, "target": target, "description": description}


def _fail(message, code="INVALID_INPUT"):
    return ModelResult(False, error=message, error_code=code)


class ThermoTool(BaseModelTool):
    data_requirement = "REFERENCE_DATA_REQUIRED"
    data_access_mode = "database_repository"
    required_dataset_ids = ["DS002"]
    database_tables = ["metallurgy_v2.thermodynamic_correlation"]
    scenario = SCENARIO
    priority = "P0"
    version = "2.0.0"
    status = "qualified"
    qualification_status = "qualified"
    count_eligible = True
    data_source = ["NIST Chemistry WebBook / JANAF fixed repository snapshot"]
    source_version = "2026.08-v1"
    source_records = THERMO_SOURCE


class B001_ShomateProperties(ThermoTool):
    model_id, name = "B001", "Shomate 热物性计算"
    description = "用版本化 Shomate 系数计算定压热容、焓增量和绝对熵。"
    applicable_boundary = "仅支持资产内物种和各自温区；相变点不得跨段外推。"
    formula_reference = "NIST Shomate: Cp=A+Bt+Ct²+Dt³+E/t², t=T/1000"
    failure_modes = ["未知物种", "温度超出系数区间", "温度非正或非有限"]
    independent_validation = ["Cp等于H对T的数值导数", "298.15K附近焓增量与参考态一致"]
    dependencies = []
    relations = [rel("overlaps", "B002", "输出Cp/H/S相同但采用不同多项式和物种域"), rel("upstream_of", "B003", "提供焓积分端点"), rel("upstream_of", "B004", "提供熵积分端点")]
    input_fields = [InputField("species", "物种", "string", description="带相态的资产键，如Fe(s)"), InputField("temperature", "温度", "number", unit="K", min_value=1e-12, description="绝对温度")]
    output_fields = [OutputField("species", "物种", "string", description="资产物种键"), OutputField("temperature", "温度", "number", "K", "评价温度"), OutputField("Cp", "定压热容", "number", "J/(mol·K)", "Shomate热容"), OutputField("H_minus_H298", "焓增量", "number", "kJ/mol", "相对298.15K的焓增量"), OutputField("S", "绝对熵", "number", "J/(mol·K)", "第三定律熵"), OutputField("G_sensible", "显热参考Gibbs量", "number", "kJ/mol", "H增量-T*S"), OutputField("method", "方法", "string", description="Shomate"), OutputField("data_source", "数据模式", "string", description="固定版本资产"), OutputField("temperature_range", "有效温区", "array", description="系数有效温区[K]")]
    validation_rules = [{"rule": "positive", "field": "temperature"}, {"rule": "asset_temperature_range", "fields": ["species", "temperature"]}]
    qualification_cases = [
        {"id":"B001-N1","kind":"normal","input":{"species":"Fe(s)","temperature":298.15}}, {"id":"B001-N2","kind":"normal","input":{"species":"Fe(s)","temperature":1000}}, {"id":"B001-N3","kind":"normal","input":{"species":"O2(g)","temperature":1200}},
        {"id":"B001-F1","kind":"failure","input":{"species":"Unknown(s)","temperature":1000}}, {"id":"B001-F2","kind":"failure","input":{"species":"Fe(s)","temperature":2500}},
    ]
    data_qualification_cases = [{"id":"B001-D1","input":{"species":"Fe(s)","temperature":1000}}]
    def invoke(self, params, context=None):
        species, temperature = params["species"], float(params["temperature"])
        try: result, provenance = shomate(species, temperature)
        except RepositoryError as exc: return _fail(str(exc), exc.error_code)
        return ModelResult(True, result={"species":species,"temperature":temperature,"Cp":result["Cp"],"H_minus_H298":result["H_minus_H298"],"S":result["S"],"G_sensible":result["H_minus_H298"]-temperature*result["S"]/1000,"method":"Shomate","data_source":"database_repository","temperature_range":result["temperature_range"]}, provenance=provenance)


class B002_NasaProperties(ThermoTool):
    required_dataset_ids = ["DS_NASA7_GRI30"]
    model_id, name = "B002", "NASA7 热物性计算"
    description = "使用独立 NASA7 系数计算气相物种的Cp、绝对H/S/G。"
    applicable_boundary = "仅支持NASA7资产内理想气体物种及200–3500K区间。"
    data_source = ["GRI-Mech 3.0 NASA7 thermodynamic subset"]
    source_version = "NASA7-GRI30-SUBSET-V1"
    source_records = [{"source_id":"DS_NASA7_GRI30","name":"GRI-Mech 3.0 NASA7 subset","version":"NASA7-GRI30-SUBSET-V1"}]
    formula_reference = "NASA7: Cp/R=Σa_iT^(i-1); H/RT and S/R standard seven-coefficient forms"
    failure_modes = ["未知物种", "温度超出NASA7区间", "非气相物种"]
    independent_validation = ["Cp由返回系数直接复算", "G=H-TS"]
    dependencies = []
    relations = [rel("overlaps", "B001", "输出相同但NASA7仅覆盖气体且H为绝对标准焓"), rel("alternative_to", "B003", "可为气相显热积分提供另一多项式路径")]
    input_fields = [InputField("species","气相物种","string",description="NASA7资产键，如O2(g)"),InputField("temperature","温度","number",unit="K",min_value=1e-12,description="绝对温度")]
    output_fields = [OutputField("species","物种","string",description="气相物种"),OutputField("temperature","温度","number","K","评价温度"),OutputField("Cp","定压热容","number","J/(mol·K)","NASA7热容"),OutputField("H","标准焓","number","kJ/mol","NASA7绝对标准焓"),OutputField("S","绝对熵","number","J/(mol·K)","NASA7绝对熵"),OutputField("G","Gibbs量","number","kJ/mol","H-TS"),OutputField("coefficients","使用系数","array",description="七系数"),OutputField("coefficient_region","温区段","string",description="low/high"),OutputField("gas_constant","气体常数","number","J/(mol·K)","CODATA常数"),OutputField("method","方法","string",description="NASA7"),OutputField("asset_id","资产版本","string",description="固定资产ID")]
    validation_rules = [{"rule":"positive","field":"temperature"},{"rule":"nasa7_asset_range","fields":["species","temperature"]}]
    qualification_cases = [
        {"id":"B002-N1","kind":"normal","input":{"species":"O2(g)","temperature":300}}, {"id":"B002-N2","kind":"normal","input":{"species":"O2(g)","temperature":900}}, {"id":"B002-N3","kind":"normal","input":{"species":"CO2(g)","temperature":1500}},
        {"id":"B002-F1","kind":"failure","input":{"species":"Fe(s)","temperature":1000}}, {"id":"B002-F2","kind":"failure","input":{"species":"O2(g)","temperature":5000}},
    ]
    data_qualification_cases = [{"id":"B002-D1","input":{"species":"O2(g)","temperature":900}}]
    def invoke(self, params, context=None):
        species, temperature = params["species"], float(params["temperature"])
        try: result, provenance = nasa7(species, temperature)
        except RepositoryError as exc: return _fail(str(exc), exc.error_code)
        return ModelResult(True,result={"species":species,"temperature":temperature,"Cp":result["Cp"],"H":result["H"],"S":result["S"],"G":result["G"],"coefficients":result["coefficients"],"coefficient_region":result["coefficient_region"],"gas_constant":R_J_MOL_K,"method":"NASA7","asset_id":result["asset_id"]}, provenance=provenance)


class B003_SensibleEnthalpy(ThermoTool):
    required_dataset_ids = ["DS002", "DS_IUPAC_AW_2021"]
    database_tables = ["metallurgy_v2.thermodynamic_correlation", "metallurgy_v2.element_reference"]
    model_id, name = "B003", "显热与焓积分"
    description = "由同一Shomate段的端点焓差计算摩尔显热，并明确转换到mol或kg数量基准。"
    applicable_boundary = "起止温度均须在同一物种资产范围；不含相变潜热。"
    formula_reference = "Δh=H(T2)-H(T1); Q=nΔh; n=m/M"
    failure_modes = ["温区缺数据", "起温不小于终温", "数量非正", "质量基准化学式不可解析"]
    independent_validation = ["端点Shomate焓差", "等摩尔的质量/摩尔基准结果一致"]
    dependencies = ["A003","B001"]
    relations = [rel("depends_on","B001","使用Shomate焓端点"),rel("depends_on","A003","质量基准通过摩尔质量换算"),rel("upstream_of","D002","为装料显热提供原子计算")]
    input_fields = [InputField("species","物种","string",description="带相态物种"),InputField("temperature_start","起始温度","number",unit="K",min_value=1e-12,description="起始绝对温度"),InputField("temperature_end","终止温度","number",unit="K",min_value=1e-12,description="终止绝对温度"),InputField("amount","数量","number",required=False,default=1.0,unit="$amount_basis",min_value=1e-30,description="mol或kg"),InputField("amount_basis","数量基准","select",required=False,default="mol",enum=["mol","kg"],description="数量单位")]
    output_fields = [OutputField("species","物种","string",description="物种"),OutputField("temperature_start","起始温度","number","K","起温"),OutputField("temperature_end","终止温度","number","K","终温"),OutputField("delta_H_molar_kj_mol","摩尔显热","number","kJ/mol","端点焓差"),OutputField("amount","数量","number","$amount_basis","输入数量"),OutputField("amount_basis","基准","string",description="mol/kg"),OutputField("equivalent_moles","等效摩尔数","number","mol","换算摩尔数"),OutputField("delta_H_total_kj","总显热","number","kJ","数量基准总显热"),OutputField("delta_H","兼容焓变","number","kJ","旧字段，等于总显热")]
    validation_rules=[{"rule":"ordered_temperature","fields":["temperature_start","temperature_end"]},{"rule":"positive","field":"amount"}]
    qualification_cases=[
        {"id":"B003-N1","kind":"normal","input":{"species":"Fe(s)","temperature_start":298.15,"temperature_end":1000}}, {"id":"B003-N2","kind":"normal","input":{"species":"Fe(s)","temperature_start":298.15,"temperature_end":1000,"amount":2,"amount_basis":"mol"}}, {"id":"B003-N3","kind":"normal","input":{"species":"Fe(s)","temperature_start":298.15,"temperature_end":1000,"amount":0.055845,"amount_basis":"kg"}},
        {"id":"B003-F1","kind":"failure","input":{"species":"Fe(s)","temperature_start":1000,"temperature_end":298.15}}, {"id":"B003-F2","kind":"failure","input":{"species":"Fe(s)","temperature_start":298.15,"temperature_end":2500}},
    ]
    data_qualification_cases = [{"id":"B003-D1","input":{"species":"Fe(s)","temperature_start":298.15,"temperature_end":1000,"amount":0.055845,"amount_basis":"kg"}}]
    def invoke(self,params,context=None):
        species=params["species"]; t1=float(params["temperature_start"]); t2=float(params["temperature_end"])
        if t1>=t2:return _fail("起始温度必须小于终止温度")
        try:
            p1, provenance1 = shomate(species,t1); p2, provenance2 = shomate(species,t2)
        except RepositoryError as exc:return _fail(str(exc),exc.error_code)
        amount=float(params.get("amount",1)); basis=params.get("amount_basis","mol"); moles=amount
        if basis=="kg":
            elements,error=parse_formula(species)
            if error:return _fail(error)
            try: weights, mass_provenance = atomic_weights(elements)
            except RepositoryError as exc:return _fail(str(exc),exc.error_code)
            molar_mass=math.fsum(count*weights[element] for element,count in elements.items())
            moles=amount*1000/molar_mass
        else: mass_provenance=[]
        molar=p2["H_minus_H298"]-p1["H_minus_H298"]; total=molar*moles
        return ModelResult(True,result={"species":species,"temperature_start":t1,"temperature_end":t2,"delta_H_molar_kj_mol":molar,"amount":amount,"amount_basis":basis,"equivalent_moles":moles,"delta_H_total_kj":total,"delta_H":total},provenance=provenance1+provenance2+mass_provenance)


class B004_EntropyIntegration(ThermoTool):
    model_id,name="B004","熵积分"
    description="计算同一物种两个温度之间的绝对熵差。"
    applicable_boundary="起止温度须落在Shomate资产有效范围，且不跨未建模相变。"
    formula_reference="ΔS=S(T2)-S(T1)=∫Cp/T dT"
    failure_modes=["温区缺数据","起温不小于终温","跨相变未建模"]
    independent_validation=["B001端点熵差","小温差下ΔS≈Cp ln(T2/T1)"]
    dependencies=["B001"]
    relations=[rel("depends_on","B001","使用Shomate绝对熵端点"),rel("overlaps","B003","输入相同但分别输出熵差和焓差")]
    input_fields=[InputField("species","物种","string",description="带相态物种"),InputField("temperature_start","起始温度","number",unit="K",min_value=1e-12,description="起温"),InputField("temperature_end","终止温度","number",unit="K",min_value=1e-12,description="终温")]
    output_fields=[OutputField("species","物种","string",description="物种"),OutputField("temperature_start","起始温度","number","K","起温"),OutputField("temperature_end","终止温度","number","K","终温"),OutputField("S_start","起始熵","number","J/(mol·K)","绝对熵"),OutputField("S_end","终止熵","number","J/(mol·K)","绝对熵"),OutputField("delta_S","熵差","number","J/(mol·K)","终态减初态")]
    validation_rules=[{"rule":"ordered_temperature","fields":["temperature_start","temperature_end"]}]
    qualification_cases=[
        {"id":"B004-N1","kind":"normal","input":{"species":"Fe(s)","temperature_start":298.15,"temperature_end":1000}}, {"id":"B004-N2","kind":"normal","input":{"species":"O2(g)","temperature_start":298,"temperature_end":800}}, {"id":"B004-N3","kind":"normal","input":{"species":"CO2(g)","temperature_start":400,"temperature_end":1000}},
        {"id":"B004-F1","kind":"failure","input":{"species":"Fe(s)","temperature_start":1000,"temperature_end":500}}, {"id":"B004-F2","kind":"failure","input":{"species":"Unknown","temperature_start":300,"temperature_end":500}},
    ]
    data_qualification_cases = [{"id":"B004-D1","input":{"species":"Fe(s)","temperature_start":298.15,"temperature_end":1000}}]
    def invoke(self,params,context=None):
        s=params["species"];t1=float(params["temperature_start"]);t2=float(params["temperature_end"])
        if t1>=t2:return _fail("起始温度必须小于终止温度")
        try:a,pa=shomate(s,t1);b,pb=shomate(s,t2)
        except RepositoryError as exc:return _fail(str(exc),exc.error_code)
        return ModelResult(True,result={"species":s,"temperature_start":t1,"temperature_end":t2,"S_start":a["S"],"S_end":b["S"],"delta_S":b["S"]-a["S"]},provenance=pa+pb)


class B005_SpeciesGibbs(ThermoTool):
    model_id,name="B005","物种Gibbs自由能"
    description="在显式焓参考态和第三定律熵基准下计算单物种G=H-TS。"
    applicable_boundary="H采用H(298.15K)=0显热参考，S采用Shomate绝对熵；不是标准生成Gibbs能。"
    formula_reference="G_ref(T)=[H(T)-H(298.15)]-T*S°(T)"
    failure_modes=["未知物种","温度超出Shomate范围","将结果误作生成Gibbs能"]
    independent_validation=["G=H-TS代数恒等","与B001同温H/S组合一致"]
    dependencies=["B001"]
    relations=[rel("depends_on","B001","组合同温Shomate H和S"),rel("distinct_from","B008","B005是单物种参考G，B008是反应ΔG")]
    input_fields=[InputField("species","物种","string",description="带相态物种"),InputField("temperature","温度","number",unit="K",min_value=1e-12,description="绝对温度")]
    output_fields=[OutputField("species","物种","string",description="物种"),OutputField("temperature","温度","number","K","评价温度"),OutputField("H","参考焓","number","kJ/mol","相对298.15K"),OutputField("S","绝对熵","number","J/(mol·K)","第三定律熵"),OutputField("G","参考Gibbs量","number","kJ/mol","H-TS"),OutputField("enthalpy_reference","焓参考态","string",description="显式参考态"),OutputField("entropy_reference","熵参考态","string",description="绝对熵基准")]
    validation_rules=[{"rule":"asset_temperature_range","fields":["species","temperature"]}]
    qualification_cases=[
        {"id":"B005-N1","kind":"normal","input":{"species":"Fe(s)","temperature":298.15}}, {"id":"B005-N2","kind":"normal","input":{"species":"Fe(s)","temperature":1000}}, {"id":"B005-N3","kind":"normal","input":{"species":"O2(g)","temperature":1000}},
        {"id":"B005-F1","kind":"failure","input":{"species":"Unknown","temperature":1000}}, {"id":"B005-F2","kind":"failure","input":{"species":"Fe(s)","temperature":2500}},
    ]
    data_qualification_cases = [{"id":"B005-D1","input":{"species":"Fe(s)","temperature":1000}}]
    def invoke(self,params,context=None):
        s=params["species"];t=float(params["temperature"])
        try:p,provenance=shomate(s,t)
        except RepositoryError as exc:return _fail(str(exc),exc.error_code)
        h=p["H_minus_H298"];entropy=p["S"]
        return ModelResult(True,result={"species":s,"temperature":t,"H":h,"S":entropy,"G":h-t*entropy/1000,"enthalpy_reference":"H(298.15 K)=0 sensible reference","entropy_reference":"third-law absolute entropy"},provenance=provenance)


class ReactionTool(ThermoTool):
    required_dataset_ids=["DS002"]
    database_tables=["metallurgy_v2.reaction_definition","metallurgy_v2.reaction_property"]
    source_records=REACTION_SOURCE
    data_source=["NIST-JANAF/Barin fixed reaction snapshot"]
    source_version="REACTION-THERMO-2026.08-v1"
    failure_modes=["反应不在固定资产","温度非正","反应式未按资产计量基准"]
    input_fields=[InputField("reaction","反应式","string",description="固定资产支持的配平反应"),InputField("temperature","温度","number",required=False,default=298.15,unit="K",min_value=1e-12,description="绝对温度")]
    validation_rules=[{"rule":"fixed_reaction_asset","field":"reaction"},{"rule":"positive","field":"temperature"}]
    def entry(self,params):return reaction_properties(params["reaction"],"DS002")


class B006_ReactionEnthalpy(ReactionTool):
    model_id,name="B006","反应焓计算"
    description="按固定反应计量基准返回标准反应焓。"
    applicable_boundary="当前资产为常数ΔH近似；温度参数用于链路一致性，不做Cp修正。"
    formula_reference="ΔH°=ΣνHf°(产物)-ΣνHf°(反应物)"
    independent_validation=["Hess定律计量加权","与B008中的ΔH分量一致"]
    dependencies=["A006"]
    relations=[rel("requires_validation_by","A006","反应式应先通过配平校验"),rel("upstream_of","B008","提供ΔG组合中的ΔH"),rel("upstream_of","D002","反应放热作为热平衡输入")]
    output_fields=[OutputField("reaction","反应式","string",description="资产规范式"),OutputField("temperature","温度","number","K","请求温度"),OutputField("delta_H","反应焓","number","kJ/mol-reaction","按反应式计量基准"),OutputField("reaction_type","热效应","string",description="exothermic/endothermic"),OutputField("data_version","数据版本","string",description="固定反应资产版本")]
    qualification_cases=[{"id":"B006-N1","kind":"normal","input":{"reaction":"C + O₂ → CO₂","temperature":298.15}},{"id":"B006-N2","kind":"normal","input":{"reaction":"CaCO₃ → CaO + CO₂","temperature":298.15}},{"id":"B006-N3","kind":"normal","input":{"reaction":"Fe₂O₃ + 2Al → 2Fe + Al₂O₃","temperature":298.15}},{"id":"B006-F1","kind":"failure","input":{"reaction":"Unknown -> X","temperature":298.15}},{"id":"B006-F2","kind":"failure","input":{"reaction":"C + O₂ → CO₂","temperature":0}}]
    data_qualification_cases = [{"id":"B006-D1","input":{"reaction":"C + O₂ → CO₂","temperature":298.15}}]
    def invoke(self,params,context=None):
        try:e,provenance=self.entry(params)
        except RepositoryError as exc:return _fail(str(exc),exc.error_code)
        dh=float(e["DELTA_H_STD"])
        return ModelResult(True,result={"reaction":e["reaction"],"temperature":float(params.get("temperature",298.15)),"delta_H":dh,"reaction_type":"exothermic" if dh<0 else "endothermic","data_version":e["source_version"]},provenance=provenance)


class B007_ReactionEntropy(ReactionTool):
    model_id,name="B007","反应熵计算"
    description="按固定反应计量基准返回标准反应熵。"
    applicable_boundary="当前资产为常数ΔS近似，不做温度Cp/T修正。"
    formula_reference="ΔS°=ΣνS°(产物)-ΣνS°(反应物)"
    independent_validation=["标准熵计量加权","与B008中的ΔS分量一致"]
    dependencies=["A006"]
    relations=[rel("requires_validation_by","A006","反应应先配平"),rel("upstream_of","B008","提供ΔG组合中的ΔS"),rel("overlaps","B006","相同输入但输出不同热力学状态函数")]
    output_fields=[OutputField("reaction","反应式","string",description="资产规范式"),OutputField("temperature","温度","number","K","请求温度"),OutputField("delta_S","反应熵","number","J/(mol-reaction·K)","按反应式计量基准"),OutputField("data_version","数据版本","string",description="固定资产版本")]
    qualification_cases=[{"id":"B007-N1","kind":"normal","input":{"reaction":"C + O₂ → CO₂","temperature":298.15}},{"id":"B007-N2","kind":"normal","input":{"reaction":"CaCO₃ → CaO + CO₂","temperature":298.15}},{"id":"B007-N3","kind":"normal","input":{"reaction":"Fe₂O₃ + 2Al → 2Fe + Al₂O₃","temperature":298.15}},{"id":"B007-F1","kind":"failure","input":{"reaction":"Unknown -> X","temperature":298.15}},{"id":"B007-F2","kind":"failure","input":{"reaction":"C + O₂ → CO₂","temperature":-1}}]
    data_qualification_cases = [{"id":"B007-D1","input":{"reaction":"CaCO₃ → CaO + CO₂","temperature":298.15}}]
    def invoke(self,params,context=None):
        try:e,provenance=self.entry(params)
        except RepositoryError as exc:return _fail(str(exc),exc.error_code)
        return ModelResult(True,result={"reaction":e["reaction"],"temperature":float(params.get("temperature",298.15)),"delta_S":float(e["DELTA_S_STD"]),"data_version":e["source_version"]},provenance=provenance)


class B008_ReactionGibbs(ReactionTool):
    model_id,name="B008","反应Gibbs自由能"
    description="组合B006反应焓与B007反应熵计算指定温度标准反应Gibbs能。"
    applicable_boundary="采用温度无关ΔH/ΔS近似；不含非标准活度项。"
    formula_reference="ΔG°(T)=ΔH°-TΔS°"
    independent_validation=["ΔG=ΔH-TΔS代数恒等","与B009的-lnK关系一致"]
    dependencies=["B006","B007"]
    relations=[rel("composes","B006","使用反应焓分量"),rel("composes","B007","使用反应熵分量"),rel("upstream_of","B009","标准ΔG换算平衡常数"),rel("distinct_from","B005","反应状态函数与单物种参考G不同")]
    output_fields=[OutputField("reaction","反应式","string",description="资产规范式"),OutputField("temperature","温度","number","K","绝对温度"),OutputField("delta_H","反应焓","number","kJ/mol-reaction","固定资产值"),OutputField("delta_S","反应熵","number","J/(mol-reaction·K)","固定资产值"),OutputField("delta_G","反应Gibbs能","number","kJ/mol-reaction","H-T*S"),OutputField("direction","标准态方向","string",description="forward/reverse/equilibrium"),OutputField("data_version","数据版本","string",description="固定资产版本")]
    qualification_cases=[{"id":"B008-N1","kind":"normal","input":{"reaction":"C + O₂ → CO₂","temperature":298.15}},{"id":"B008-N2","kind":"normal","input":{"reaction":"C + O₂ → CO₂","temperature":1000}},{"id":"B008-N3","kind":"normal","input":{"reaction":"CaCO₃ → CaO + CO₂","temperature":1200}},{"id":"B008-F1","kind":"failure","input":{"reaction":"Unknown -> X","temperature":1000}},{"id":"B008-F2","kind":"failure","input":{"reaction":"C + O₂ → CO₂","temperature":0}}]
    data_qualification_cases = [{"id":"B008-D1","input":{"reaction":"C + O₂ → CO₂","temperature":1000}}]
    def invoke(self,params,context=None):
        try:e,provenance=self.entry(params)
        except RepositoryError as exc:return _fail(str(exc),exc.error_code)
        t=float(params.get("temperature",298.15));dh=float(e["DELTA_H_STD"]);ds=float(e["DELTA_S_STD"]);dg=dh-t*ds/1000
        direction="forward" if dg<0 else "reverse" if dg>0 else "equilibrium"
        return ModelResult(True,result={"reaction":e["reaction"],"temperature":t,"delta_H":dh,"delta_S":ds,"delta_G":dg,"direction":direction,"data_version":e["source_version"]},provenance=provenance)


class B009_EquilibriumConstant(ReactionTool):
    model_id,name="B009","平衡常数计算"
    description="由标准反应Gibbs能换算无量纲热力学平衡常数。"
    applicable_boundary="K为选定标准态下的无量纲热力学平衡常数；采用B008常ΔH/ΔS近似。"
    formula_reference="ln K=-ΔG°/(RT)"
    independent_validation=["lnK=-ΔG/RT","ΔG=0时K=1"]
    dependencies=["B008"]
    relations=[rel("depends_on","B008","使用标准反应ΔG"),rel("distinct_from","B010","B009由绝对ΔG求K，B010从已知K做温度修正")]
    output_fields=[OutputField("reaction","反应式","string",description="资产规范式"),OutputField("temperature","温度","number","K","绝对温度"),OutputField("delta_G","反应Gibbs能","number","kJ/mol-reaction","B008结果"),OutputField("ln_K","自然对数平衡常数","number","1","-ΔG/RT"),OutputField("log10_K","常用对数平衡常数","number","1","lnK/ln10"),OutputField("K","平衡常数","number","1","无量纲热力学K"),OutputField("standard_state","标准态","string",description="unit-activity standard state")]
    qualification_cases=[{"id":"B009-N1","kind":"normal","input":{"reaction":"C + O₂ → CO₂","temperature":298.15}},{"id":"B009-N2","kind":"normal","input":{"reaction":"C + O₂ → CO₂","temperature":1000}},{"id":"B009-N3","kind":"normal","input":{"reaction":"CaCO₃ → CaO + CO₂","temperature":1200}},{"id":"B009-F1","kind":"failure","input":{"reaction":"Unknown -> X","temperature":1000}},{"id":"B009-F2","kind":"failure","input":{"reaction":"C + O₂ → CO₂","temperature":0}}]
    data_qualification_cases = [{"id":"B009-D1","input":{"reaction":"C + O₂ → CO₂","temperature":1000}}]
    def invoke(self,params,context=None):
        try:e,provenance=self.entry(params)
        except RepositoryError as exc:return _fail(str(exc),exc.error_code)
        t=float(params.get("temperature",298.15));dg=float(e["DELTA_H_STD"])-t*float(e["DELTA_S_STD"])/1000;lnk=-dg*1000/(R_J_MOL_K*t);k=math.exp(lnk)
        return ModelResult(True,result={"reaction":e["reaction"],"temperature":t,"delta_G":dg,"ln_K":lnk,"log10_K":lnk/math.log(10),"K":k,"standard_state":"unit-activity standard state"},provenance=provenance)


class B010_VantHoffCorrection(ThermoTool):
    data_requirement="FORMULA_ONLY"
    data_access_mode="none"
    required_dataset_ids=[]
    database_tables=[]
    model_id,name="B010","van't Hoff温度修正"
    description="由参考平衡常数和反应焓（可含常ΔCp修正）计算目标温度平衡常数。"
    applicable_boundary="ΔH和ΔCp在T1到T2间视为常数；温区过宽仅返回外推警告。"
    source_records=REACTION_SOURCE
    formula_reference="ln(K2/K1)=ΔH/R(1/T1-1/T2)+ΔCp/R[ln(T2/T1)+T1(1/T2-1/T1)]"
    failure_modes=["K1非正","温度非正","指数溢出","常ΔH/Cp假设不适用"]
    independent_validation=["T1=T2时K2=K1","正反温度修正互逆"]
    dependencies=["B006","B009"]
    relations=[rel("accepts_output_of","B009","K_reference可来自B009"),rel("accepts_output_of","B006","delta_H可来自B006"),rel("distinct_from","B009","温度修正而非绝对K计算")]
    input_fields=[InputField("K_reference","参考平衡常数","number",unit="1",min_value=1e-300,description="T1下无量纲K"),InputField("temperature_reference","参考温度","number",unit="K",min_value=1e-12,description="T1"),InputField("temperature_target","目标温度","number",unit="K",min_value=1e-12,description="T2"),InputField("delta_H_kj_mol","参考反应焓","number",unit="kJ/mol-reaction",description="T1下ΔH"),InputField("delta_Cp_j_mol_k","反应热容差","number",required=False,default=0.0,unit="J/(mol-reaction·K)",description="常数ΔCp")]
    output_fields=[OutputField("K_reference","参考K","number","1","输入K1"),OutputField("K_target","目标K","number","1","修正K2"),OutputField("ln_K_ratio","对数比","number","1","ln(K2/K1)"),OutputField("temperature_reference","参考温度","number","K","T1"),OutputField("temperature_target","目标温度","number","K","T2"),OutputField("delta_H_kj_mol","反应焓","number","kJ/mol-reaction","输入ΔH"),OutputField("delta_Cp_j_mol_k","热容差","number","J/(mol-reaction·K)","输入ΔCp"),OutputField("assumption","假设","string",description="constant ΔH/ΔCp")]
    validation_rules=[{"rule":"positive","fields":["K_reference","temperature_reference","temperature_target"]}]
    qualification_cases=[{"id":"B010-N1","kind":"normal","input":{"K_reference":10,"temperature_reference":1000,"temperature_target":1200,"delta_H_kj_mol":100}},{"id":"B010-N2","kind":"normal","input":{"K_reference":1,"temperature_reference":1000,"temperature_target":1000,"delta_H_kj_mol":-50}},{"id":"B010-N3","kind":"normal","input":{"K_reference":0.1,"temperature_reference":800,"temperature_target":1000,"delta_H_kj_mol":80,"delta_Cp_j_mol_k":10}},{"id":"B010-F1","kind":"failure","input":{"K_reference":0,"temperature_reference":1000,"temperature_target":1200,"delta_H_kj_mol":100}},{"id":"B010-F2","kind":"failure","input":{"K_reference":1,"temperature_reference":0,"temperature_target":1200,"delta_H_kj_mol":100}}]
    def invoke(self,params,context=None):
        k1=float(params["K_reference"]);t1=float(params["temperature_reference"]);t2=float(params["temperature_target"]);dh=float(params["delta_H_kj_mol"])*1000;dcp=float(params.get("delta_Cp_j_mol_k",0))
        ratio=dh/R_J_MOL_K*(1/t1-1/t2)+dcp/R_J_MOL_K*(math.log(t2/t1)+t1*(1/t2-1/t1))
        try:k2=k1*math.exp(ratio)
        except OverflowError:return _fail("目标平衡常数指数溢出","NUMERICAL_ERROR")
        return ModelResult(True,result={"K_reference":k1,"K_target":k2,"ln_K_ratio":ratio,"temperature_reference":t1,"temperature_target":t2,"delta_H_kj_mol":dh/1000,"delta_Cp_j_mol_k":dcp,"assumption":"constant delta_H and delta_Cp over interval"})


class B011_EllinghamLine(ThermoTool):
    required_dataset_ids=["DS_ELLINGHAM_BARIN_V1"]
    database_tables=["metallurgy_v2.reaction_definition","metallurgy_v2.reaction_property"]
    model_id,name="B011","Ellingham线"
    description="用固定氧化反应ΔH/ΔS生成ΔG-T直线和对应平衡氧分压。"
    applicable_boundary="仅支持资产内以O2计量的氧化反应，且假设凝聚相活度为1、ΔH/ΔS常数。"
    source_records=[{"source_id":"DS_ELLINGHAM_BARIN_V1","name":"Barin Ellingham parameter snapshot","version":"ELLINGHAM-BARIN-V1"}]
    source_version="ELLINGHAM-BARIN-V1"
    formula_reference="ΔG=ΔH-TΔS; ln(pO2)=ΔG/(νO2 RT)"
    failure_modes=["反应不在Ellingham资产","温度列表为空或非正","温度超出相态有效域"]
    independent_validation=["ΔG-T斜率为-ΔS","pO2满足氧势方程"]
    dependencies=["B006","B007","B008","B009"]
    relations=[rel("extends","B008","从单温点扩展为温区曲线"),rel("uses_relation_of","B009","氧分压来自平衡常数/氧势关系"),rel("overlaps","B010","都描述平衡的温度变化但输出目标不同")]
    input_fields=[InputField("reaction","氧化反应","string",description="Ellingham资产键"),InputField("temperatures","温度点","array",items={"type":"number"},description="至少一个K温度点")]
    output_fields=[OutputField("reaction","反应式","string",description="规范反应式"),OutputField("delta_H_kj_mol","反应焓","number","kJ/mol-reaction","线性参数"),OutputField("delta_S_j_mol_k","反应熵","number","J/(mol-reaction·K)","线性参数"),OutputField("oxygen_coefficient","氧系数","number","mol O2/mol-reaction","反应式O2系数"),OutputField("points","曲线点","array",description="T/ΔG/pO2"),OutputField("source","参数来源","string",description="固定资产来源")]
    validation_rules=[{"rule":"nonempty_positive_array","field":"temperatures"},{"rule":"ellingham_asset","field":"reaction"}]
    qualification_cases=[{"id":"B011-N1","kind":"normal","input":{"reaction":"2Fe + O2 -> 2FeO","temperatures":[800,1000,1200]}},{"id":"B011-N2","kind":"normal","input":{"reaction":"2Fe + O2 -> 2FeO","temperatures":[500]}},{"id":"B011-N3","kind":"normal","input":{"reaction":"4Al + 3O2 -> 2Al2O3","temperatures":[800,1200]}},{"id":"B011-B1","kind":"boundary","input":{"reaction":"2Fe + O2 -> 2FeO","temperatures":[1800]}},{"id":"B011-F1","kind":"failure","input":{"reaction":"Unknown","temperatures":[1000]}}]
    data_qualification_cases = [{"id":"B011-D1","input":{"reaction":"2Fe + O2 -> 2FeO","temperatures":[800,1000,1200]}}]
    def invoke(self,params,context=None):
        try:entry,provenance=reaction_properties(params["reaction"],"DS_ELLINGHAM_BARIN_V1")
        except RepositoryError as exc:return _fail(str(exc),exc.error_code)
        temps=params["temperatures"]
        if not isinstance(temps,list) or not temps:return _fail("temperatures必须是非空数组")
        points=[];outside=False
        for raw in temps:
            t=float(raw)
            if not math.isfinite(t) or t<=0:return _fail("温度必须为正有限值")
            outside|=not entry["temperature_min_k"]<=t<=entry["temperature_max_k"]
            dg=entry["DELTA_H_STD"]-t*entry["DELTA_S_STD"]/1000
            lnpo=dg*1000/(entry["OXYGEN_COEFFICIENT"]*R_J_MOL_K*t)
            points.append({"temperature_k":t,"delta_G_kj_mol":dg,"ln_pO2":lnpo,"pO2_atm":math.exp(lnpo)})
        warnings=[] if not outside else [BoundaryWarning("temperatures","至少一个温度超出固定相态参数范围")]
        return ModelResult(True,result={"reaction":entry["reaction"],"delta_H_kj_mol":entry["DELTA_H_STD"],"delta_S_j_mol_k":entry["DELTA_S_STD"],"oxygen_coefficient":entry["OXYGEN_COEFFICIENT"],"points":points,"source":entry["source_ref"]},boundary_check=BoundaryCheck(not outside,warnings),provenance=provenance)


class B014_IdealSolutionActivity(ThermoTool):
    data_requirement="FORMULA_ONLY"
    data_access_mode="none"
    required_dataset_ids=[]
    database_tables=[]
    model_id,name="B014","理想溶液活度"
    description="按Raoult理想溶液模型计算活度、化学势和混合Gibbs能。"
    applicable_boundary="同一相内理想混合；纯组元标准态；零摩尔分数组元化学势记为null。"
    source_records=[{"source_id":"SOLUTION-THERMO-TEXTBOOK","name":"Raoult ideal-solution model","version":"formula-v1"}]
    source_version="IDEAL-SOLUTION-v1"
    formula_reference="a_i=x_i; gamma_i=1; μ_i=μ_i°+RT ln x_i"
    failure_modes=["组成负值或总和零","温度非正","标准化学势字段不匹配"]
    independent_validation=["全部gamma=1","Gex=0","组成缩放不变"]
    dependencies=["A004"]
    relations=[rel("depends_on","A004","复用组成归一化"),rel("overlaps","B015","相同输入输出但B015含非理想相互作用")]
    input_fields=[InputField("compositions","摩尔组成","object",unit="1",description="组元到非负摩尔份额"),InputField("temperature","温度","number",unit="K",min_value=1e-12,description="绝对温度"),InputField("standard_chemical_potentials_kj_mol","标准化学势","object",required=False,default={},unit="kJ/mol",description="缺省为0")]
    output_fields=[OutputField("normalized_compositions","归一化组成","object",description="摩尔分数"),OutputField("activity_coefficients","活度系数","object",description="全为1"),OutputField("activities","活度","object",description="等于摩尔分数"),OutputField("chemical_potentials_kj_mol","化学势","object",description="零组分为null"),OutputField("ideal_mixing_gibbs_j_mol","理想混合Gibbs能","number","J/mol","RTΣxlnx"),OutputField("excess_gibbs_j_mol","超额Gibbs能","number","J/mol","理想模型为0"),OutputField("standard_state","标准态","string",description="Raoult pure-component")]
    validation_rules=[{"rule":"A004_nonnegative_normalization","field":"compositions"},{"rule":"positive","field":"temperature"}]
    qualification_cases=[{"id":"B014-N1","kind":"normal","input":{"compositions":{"A":0.5,"B":0.5},"temperature":1000}},{"id":"B014-N2","kind":"normal","input":{"compositions":{"Fe":0.7,"C":0.3},"temperature":1800}},{"id":"B014-N3","kind":"normal","input":{"compositions":{"A":2,"B":1},"temperature":1200}},{"id":"B014-B1","kind":"boundary","input":{"compositions":{"A":1,"B":0},"temperature":1000}},{"id":"B014-F1","kind":"failure","input":{"compositions":{"A":1,"B":-1},"temperature":1000}}]
    def invoke(self,params,context=None):
        parsed,error=normalize_composition(params["compositions"])
        if error:return _fail(error)
        t=float(params["temperature"]);x=parsed["normalized"];mu0=params.get("standard_chemical_potentials_kj_mol",{})
        mu={k:(float(mu0.get(k,0))+R_J_MOL_K*t*math.log(v)/1000 if v>0 else None) for k,v in x.items()}
        gmix=R_J_MOL_K*t*sum(v*math.log(v) for v in x.values() if v>0);boundary=any(v==0 for v in x.values())
        return ModelResult(True,result={"normalized_compositions":x,"activity_coefficients":{k:1.0 for k in x},"activities":dict(x),"chemical_potentials_kj_mol":mu,"ideal_mixing_gibbs_j_mol":gmix,"excess_gibbs_j_mol":0.0,"standard_state":"Raoult pure-component standard state"},boundary_check=BoundaryCheck(not boundary,[] if not boundary else [BoundaryWarning("compositions","零摩尔分数组元的化学势为负无穷，以null返回")]))


class B015_RegularSolutionActivity(ThermoTool):
    data_requirement="FORMULA_ONLY"
    data_access_mode="none"
    required_dataset_ids=[]
    database_tables=[]
    model_id,name="B015","二元正则溶液活度"
    description="计算对称二元正则溶液的活度系数、活度和超额Gibbs能。"
    applicable_boundary="仅二元、单相、对称常Ω正则溶液；Ω不随温度和组成变化。"
    source_records=[{"source_id":"REGULAR-SOLUTION-TEXTBOOK","name":"Symmetric binary regular-solution model","version":"formula-v1"}]
    source_version="REGULAR-SOLUTION-v1"
    formula_reference="lnγ1=Ωx2²/RT; lnγ2=Ωx1²/RT; Gex=Ωx1x2"
    failure_modes=["非二元组成","负组成或总和零","温度非正","指数溢出"]
    independent_validation=["Ω=0退化为B014","Gex=Ωx1x2","Gibbs-Duhem对称性"]
    dependencies=["A004","B014"]
    relations=[rel("depends_on","A004","复用组成归一化"),rel("overlaps","B014","Ω=0时严格退化为理想溶液")]
    input_fields=[InputField("compositions","二元摩尔组成","object",unit="1",description="恰好两个组元"),InputField("temperature","温度","number",unit="K",min_value=1e-12,description="绝对温度"),InputField("omega_j_mol","相互作用参数","number",unit="J/mol",description="对称正则溶液Ω")]
    output_fields=[OutputField("normalized_compositions","归一化组成","object",description="二元摩尔分数"),OutputField("activity_coefficients","活度系数","object",description="正则溶液gamma"),OutputField("activities","活度","object",description="gamma*x"),OutputField("excess_gibbs_j_mol","超额Gibbs能","number","J/mol","Ωx1x2"),OutputField("ideal_mixing_gibbs_j_mol","理想混合Gibbs能","number","J/mol","RTΣxlnx"),OutputField("mixing_gibbs_j_mol","总混合Gibbs能","number","J/mol","ideal+excess"),OutputField("model","模型","string",description="symmetric binary regular solution")]
    validation_rules=[{"rule":"exact_component_count","value":2},{"rule":"positive","field":"temperature"}]
    qualification_cases=[{"id":"B015-N1","kind":"normal","input":{"compositions":{"A":0.5,"B":0.5},"temperature":1000,"omega_j_mol":10000}},{"id":"B015-N2","kind":"normal","input":{"compositions":{"Fe":0.7,"C":0.3},"temperature":1800,"omega_j_mol":0}},{"id":"B015-N3","kind":"normal","input":{"compositions":{"A":0.2,"B":0.8},"temperature":1200,"omega_j_mol":-5000}},{"id":"B015-F1","kind":"failure","input":{"compositions":{"A":0.3,"B":0.3,"C":0.4},"temperature":1000,"omega_j_mol":0}},{"id":"B015-F2","kind":"failure","input":{"compositions":{"A":1,"B":-1},"temperature":1000,"omega_j_mol":0}}]
    def invoke(self,params,context=None):
        parsed,error=normalize_composition(params["compositions"])
        if error:return _fail(error)
        x=parsed["normalized"]
        if len(x)!=2:return _fail("正则溶液工具仅接受两个组元")
        t=float(params["temperature"]);omega=float(params["omega_j_mol"]);names=list(x);x1,x2=x[names[0]],x[names[1]]
        try:g1=math.exp(omega*x2*x2/(R_J_MOL_K*t));g2=math.exp(omega*x1*x1/(R_J_MOL_K*t))
        except OverflowError:return _fail("活度系数指数溢出","NUMERICAL_ERROR")
        gam={names[0]:g1,names[1]:g2};act={k:x[k]*gam[k] for k in names};ideal=R_J_MOL_K*t*sum(v*math.log(v) for v in x.values() if v>0);excess=omega*x1*x2
        return ModelResult(True,result={"normalized_compositions":x,"activity_coefficients":gam,"activities":act,"excess_gibbs_j_mol":excess,"ideal_mixing_gibbs_j_mol":ideal,"mixing_gibbs_j_mol":ideal+excess,"model":"symmetric binary regular solution"})


class B018_GibbsPhaseRule(ThermoTool):
    data_requirement="FORMULA_ONLY"
    data_access_mode="none"
    required_dataset_ids=[]
    database_tables=[]
    model_id,name="B018","Gibbs相律校验"
    description="计算含独立反应和外加约束的Gibbs相律自由度。"
    applicable_boundary="平衡宏观体系；components是独立组元数，约束必须相互独立。"
    source_records=[{"source_id":"GIBBS-PHASE-RULE","name":"Gibbs phase rule","version":"formula-v1"}]
    source_version="GIBBS-PHASE-RULE-v1"
    formula_reference="F=C-P+2-R-E"
    failure_modes=["组元或相数小于1","反应/外加约束为负","约束不独立"]
    independent_validation=["二元两相F=2","单元三相点F=0"]
    dependencies=[]
    relations=[rel("upstream_of","B019","相律确认两相区自由度后可用杠杆规则"),rel("complements","B014","相律给自由度，活度模型给化学势")]
    input_fields=[InputField("components","独立组元数","number",unit="1",min_value=1,description="C"),InputField("phases","相数","number",unit="1",min_value=1,description="P"),InputField("independent_reactions","独立反应数","number",required=False,default=0,unit="1",min_value=0,description="R"),InputField("external_constraints","外加独立约束数","number",required=False,default=0,unit="1",min_value=0,description="E")]
    output_fields=[OutputField("components","组元数","number","1","C"),OutputField("phases","相数","number","1","P"),OutputField("independent_reactions","反应数","number","1","R"),OutputField("external_constraints","外加约束","number","1","E"),OutputField("degrees_of_freedom","自由度","number","1","F"),OutputField("feasible","相律是否可行","boolean",description="F>=0"),OutputField("formula","公式","string",description="F=C-P+2-R-E")]
    validation_rules=[{"rule":"integer_counts","fields":["components","phases","independent_reactions","external_constraints"]}]
    qualification_cases=[{"id":"B018-N1","kind":"normal","input":{"components":2,"phases":2}},{"id":"B018-N2","kind":"normal","input":{"components":1,"phases":3}},{"id":"B018-N3","kind":"normal","input":{"components":3,"phases":2,"independent_reactions":1}},{"id":"B018-B1","kind":"boundary","input":{"components":1,"phases":4}},{"id":"B018-F1","kind":"failure","input":{"components":0,"phases":1}}]
    def invoke(self,params,context=None):
        vals={k:float(params.get(k,d)) for k,d in (("components",0),("phases",0),("independent_reactions",0),("external_constraints",0))}
        if any(not v.is_integer() for v in vals.values()):return _fail("相律计数必须为整数")
        c,p,r,e=(int(vals[k]) for k in ("components","phases","independent_reactions","external_constraints"));f=c-p+2-r-e;ok=f>=0
        return ModelResult(True,result={"components":c,"phases":p,"independent_reactions":r,"external_constraints":e,"degrees_of_freedom":f,"feasible":ok,"formula":"F=C-P+2-R-E"},boundary_check=BoundaryCheck(ok,[] if ok else [BoundaryWarning("degrees_of_freedom","自由度为负，输入相数/约束组合不可能")]))


class B019_LeverRule(ThermoTool):
    data_requirement="FORMULA_ONLY"
    data_access_mode="none"
    required_dataset_ids=[]
    database_tables=[]
    model_id,name="B019","杠杆规则计算"
    description="在二元两相区按相界组成计算两相分数并返回组成守恒残差。"
    applicable_boundary="总体组成必须位于两个不同相界组成之间；三元及以上不适用。"
    source_records=[{"source_id":"LEVER-RULE","name":"Binary phase-diagram lever rule","version":"formula-v1"}]
    source_version="LEVER-RULE-v1"
    formula_reference="f1=(C2-C0)/(C2-C1); f2=(C0-C1)/(C2-C1)"
    failure_modes=["总体组成在两相界外","两相组成相同","组成非有限"]
    independent_validation=["f1+f2=1","f1C1+f2C2=C0"]
    dependencies=["B018"]
    relations=[rel("requires_context_from","B018","应先确认体系处于二元两相自由度条件"),rel("overlaps","A005","都返回守恒残差但B019是相分数组成守恒")]
    input_fields=[InputField("overall_composition","总体成分","number",unit="1",min_value=0,max_value=1,description="C0"),InputField("phase1_composition","相1成分","number",unit="1",min_value=0,max_value=1,description="C1"),InputField("phase2_composition","相2成分","number",unit="1",min_value=0,max_value=1,description="C2"),InputField("component","组元","string",required=False,default="B",description="组元标签")]
    output_fields=[OutputField("phase1_fraction","相1分数","number","1","f1"),OutputField("phase2_fraction","相2分数","number","1","f2"),OutputField("phase1_composition","相1成分","number","1","C1"),OutputField("phase2_composition","相2成分","number","1","C2"),OutputField("overall_composition","总体成分","number","1","C0"),OutputField("conservation_residual","守恒残差","number","1","加权组成减总体组成"),OutputField("component","组元","string",description="组元标签")]
    validation_rules=[{"rule":"fraction_range","fields":["overall_composition","phase1_composition","phase2_composition"]},{"rule":"between_phase_boundaries","field":"overall_composition"}]
    qualification_cases=[{"id":"B019-N1","kind":"normal","input":{"overall_composition":0.4,"phase1_composition":0.2,"phase2_composition":0.8}},{"id":"B019-N2","kind":"normal","input":{"overall_composition":0.2,"phase1_composition":0.2,"phase2_composition":0.8}},{"id":"B019-N3","kind":"normal","input":{"overall_composition":0.5,"phase1_composition":0.8,"phase2_composition":0.2}},{"id":"B019-F1","kind":"failure","input":{"overall_composition":0.9,"phase1_composition":0.2,"phase2_composition":0.8}},{"id":"B019-F2","kind":"failure","input":{"overall_composition":0.5,"phase1_composition":0.5,"phase2_composition":0.5}}]
    def invoke(self,params,context=None):
        c0=float(params["overall_composition"]);c1=float(params["phase1_composition"]);c2=float(params["phase2_composition"])
        if abs(c2-c1)<1e-15:return _fail("两相组成相同，杠杆臂为零")
        if not min(c1,c2)<=c0<=max(c1,c2):return _fail("总体组成不在两相边界之间","OUT_OF_DOMAIN")
        f1=(c2-c0)/(c2-c1);f2=(c0-c1)/(c2-c1);res=f1*c1+f2*c2-c0
        return ModelResult(True,result={"phase1_fraction":f1,"phase2_fraction":f2,"phase1_composition":c1,"phase2_composition":c2,"overall_composition":c0,"conservation_residual":res,"component":params.get("component","B")})
