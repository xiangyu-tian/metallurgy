"""Qualified BOF process tools for the 30-tool milestone.

These are transparent static balances, not plant-control models.  All empirical
assumptions are inputs or versioned defaults so that later metallurgical review
can replace them without changing the tool contract.
"""
from __future__ import annotations

import math
import re

from .base import BaseModelTool, BoundaryCheck, BoundaryWarning, InputField, ModelResult, OutputField
from .repositories.reference_repository import RepositoryError, atomic_weights, process_parameters


SUPPORTED_ELEMENTS = ("C", "Si", "Mn", "P", "Fe")

BOF_MASS_FRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        element: {"type": "number", "minimum": 0, "maximum": 1}
        for element in SUPPORTED_ELEMENTS
    },
    "minProperties": 1,
    "additionalProperties": False,
}

BOF_METAL_INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "minLength": 1},
        "mass_kg": {"type": "number", "exclusiveMinimum": 0},
        "composition": BOF_MASS_FRACTION_SCHEMA,
    },
    "required": ["mass_kg", "composition"],
    "additionalProperties": False,
}

OXIDE_MASS_MAP_SCHEMA = {
    "type": "object",
    "properties": {
        "CaO": {"type": "number", "minimum": 0},
        "SiO2": {"type": "number", "minimum": 0},
        "MgO": {"type": "number", "minimum": 0},
    },
    "required": ["CaO", "SiO2", "MgO"],
    "additionalProperties": {"type": "number", "minimum": 0},
}

OXIDE_ASSAY_SCHEMA = {
    "type": "object",
    "properties": {
        "CaO": {"type": "number", "minimum": 0, "maximum": 1},
        "SiO2": {"type": "number", "minimum": 0, "maximum": 1},
        "MgO": {"type": "number", "minimum": 0, "maximum": 1},
    },
    "required": ["CaO", "SiO2", "MgO"],
    "additionalProperties": {"type": "number", "minimum": 0, "maximum": 1},
}


def rel(kind, target, description):
    return {"type": kind, "target": target, "description": description}


def fail(message, code="INVALID_INPUT"):
    return ModelResult(False, error=message, error_code=code)


class ProcessTool(BaseModelTool):
    data_requirement = "PROCESS_PARAMETER_REQUIRED"
    data_access_mode = "database_repository"
    required_dataset_ids = ["DS_BOF_PROCESS_PARAMETERS"]
    database_tables = ["metallurgy_v2.process_parameter_set"]
    scenario = "冶金工艺、物料与热平衡"
    priority = "P0"
    status = "qualified"
    qualification_status = "qualified"
    count_eligible = True
    source_version = "BOF-STATIC-BALANCE-2026.08-v1"
    source_records = [{"source_id":"BOF-STATIC-BALANCE-V1","name":"BOF stoichiometric material and energy balance assumptions","version":"2026.08-v1"}]
    data_source = ["氧化还原计量与透明静态能量守恒参数集"]


class FormulaProcessTool(BaseModelTool):
    """Explicit-input process balances that do not use hidden plant defaults."""

    data_requirement = "FORMULA_ONLY"
    data_access_mode = "none"
    scenario = "冶金工艺、物料与热平衡"
    priority = "P0"
    status = "qualified"
    qualification_status = "qualified"
    count_eligible = True


class D001_BOFOxygenDemand(ProcessTool):
    required_dataset_ids = ["DS_IUPAC_AW_2021", "DS_BOF_PROCESS_PARAMETERS"]
    database_tables = ["metallurgy_v2.element_reference", "metallurgy_v2.process_parameter_set"]
    model_id, name, version = "D001", "BOF 理论耗氧", "1.0.0"
    description = "按装料与目标钢水的元素差额，计算C/Si/Mn/P/Fe氧化的分元素理论耗氧和供氧量。"
    applicable_boundary = "静态完全混合物料衡算；只覆盖C、Si、Mn、P、Fe；组成用质量分数，未计炉渣还原与气体逸散动力学。"
    formula_reference = "元素差额×氧化计量：C→CO/CO2, Si→SiO2, Mn→MnO, P→P2O5, Fe→FeO/Fe2O3"
    failure_modes = ["组成超出0到1或单流总和大于1", "目标元素质量大于输入", "氧利用率不在(0,1]", "未知组成元素"]
    independent_validation = ["每个元素按电子/氧原子当量复算", "纯1 kmol C完全生成CO2恰需1 kmol O2", "分元素耗氧之和等于总耗氧"]
    dependencies = ["A002","A006","A007"]
    relations = [rel("depends_on","A002","化学式元素识别采用同一元素符号约定"),rel("depends_on","A006","氧化去向必须满足已配平反应"),rel("depends_on","A007","采用相同电子与O2当量"),rel("upstream_of","D002","氧化反应量可用于生成反应热输入")]
    input_fields = [
        InputField("metal_inputs", "金属装料", "array", items=BOF_METAL_INPUT_SCHEMA, min_items=1, description="[{name,mass_kg,composition:{C,Si,Mn,P,Fe}}]；name可省略，不参与计算"),
        InputField("target_steel_mass_kg", "目标钢水质量", "number", unit="kg", min_value=1e-12),
        InputField("target_composition", "目标钢水组成", "object", description="C/Si/Mn/P/Fe元素质量分数；总和不得超过1", json_schema=BOF_MASS_FRACTION_SCHEMA),
        InputField("carbon_to_co2_fraction", "碳生成CO2的比例", "number", required=False, default=0.0, unit="dimensionless", min_value=0,max_value=1),
        InputField("iron_oxide", "铁氧化物去向", "select", required=False, default="FeO", enum=["FeO","Fe2O3"]),
        InputField("oxygen_utilization", "氧利用率", "number", required=False, default=1.0, unit="dimensionless", min_value=1e-12,max_value=1),
    ]
    output_fields = [
        OutputField("element_oxygen_breakdown", "分元素耗氧", "object"), OutputField("input_element_masses_kg", "输入元素质量", "object"),
        OutputField("target_element_masses_kg", "目标元素质量", "object"), OutputField("oxidized_element_masses_kg", "氧化元素质量", "object"),
        OutputField("theoretical_oxygen_kmol", "理论氧量", "number", "kmol O2"), OutputField("theoretical_oxygen_mass_kg", "理论氧质量", "number", "kg O2"),
        OutputField("theoretical_oxygen_normal_volume_m3", "理论标准态氧体积", "number", "Nm³ O2"), OutputField("supplied_oxygen_kmol", "考虑利用率的供氧量", "number", "kmol O2"),
        OutputField("supplied_oxygen_normal_volume_m3", "考虑利用率的供氧体积", "number", "Nm³ O2"), OutputField("oxygen_utilization", "氧利用率", "number", "dimensionless"),
        OutputField("basis_input_mass_kg", "总金属输入质量", "number", "kg"), OutputField("target_steel_mass_kg", "目标钢水质量", "number", "kg"),
    ]
    validation_rules = [{"rule":"mass_fraction_compositions","fields":["metal_inputs","target_composition"]},{"rule":"positive","fields":["target_steel_mass_kg","oxygen_utilization"]}]
    qualification_cases = [
        {"id":"D001-N1","kind":"normal","input":{"metal_inputs":[{"name":"carbon","mass_kg":12.011,"composition":{"C":1}}],"target_steel_mass_kg":0.000001,"target_composition":{"C":0},"carbon_to_co2_fraction":1}},
        {"id":"D001-N2","kind":"normal","input":{"metal_inputs":[{"name":"hot metal","mass_kg":1000,"composition":{"Fe":0.95,"C":0.04,"Si":0.01}}],"target_steel_mass_kg":950,"target_composition":{"Fe":0.995,"C":0.005},"oxygen_utilization":0.9}},
        {"id":"D001-N3","kind":"normal","input":{"metal_inputs":[{"name":"carbon","mass_kg":24.022,"composition":{"C":1}}],"target_steel_mass_kg":0.000001,"target_composition":{"C":0},"carbon_to_co2_fraction":0}},
        {"id":"D001-F1","kind":"failure","input":{"metal_inputs":[{"name":"bad","mass_kg":1,"composition":{"C":1.1}}],"target_steel_mass_kg":1,"target_composition":{"C":0}}},
        {"id":"D001-F2","kind":"failure","input":{"metal_inputs":[{"name":"iron","mass_kg":1,"composition":{"Fe":1}}],"target_steel_mass_kg":2,"target_composition":{"Fe":1}}},
    ]
    data_qualification_cases = [{"id":"D001-D1","input":{"metal_inputs":[{"name":"carbon","mass_kg":12.011,"composition":{"C":1}}],"target_steel_mass_kg":0.000001,"target_composition":{"C":0},"carbon_to_co2_fraction":1}}]

    @staticmethod
    def _composition(value, label):
        if not isinstance(value, dict) or not value:
            return None, f"{label}必须是非空对象"
        parsed = {}
        for element, fraction in value.items():
            if element not in SUPPORTED_ELEMENTS:
                return None, f"{label}包含未支持元素 {element}"
            if isinstance(fraction,bool):
                return None, f"{label}.{element}必须是数值"
            try: fraction = float(fraction)
            except (TypeError,ValueError): return None, f"{label}.{element}必须是数值"
            if not math.isfinite(fraction) or not 0 <= fraction <= 1:
                return None, f"{label}.{element}必须在[0,1]"
            parsed[element] = fraction
        if math.fsum(parsed.values()) > 1+1e-12:
            return None, f"{label}质量分数之和不能超过1"
        return parsed, None

    def invoke(self, params, context=None):
        try:
            weights, element_provenance = atomic_weights(set(SUPPORTED_ELEMENTS) | {"O"})
            process, process_provenance = process_parameters(["normal_molar_volume", "oxygen_molar_mass"])
        except RepositoryError as exc:
            return fail(str(exc), exc.error_code)
        if not math.isclose(process["oxygen_molar_mass"], 2*weights["O"], rel_tol=0, abs_tol=1e-9):
            return fail("BOF参数集氧摩尔质量与原子量数据不一致", "MISSING_DATA")
        normal_m3_kmol=process["normal_molar_volume"]; o2_kg_kmol=process["oxygen_molar_mass"]
        streams = params["metal_inputs"]
        if not isinstance(streams,list) or not streams:
            return fail("metal_inputs必须是非空数组")
        input_masses = {e:0.0 for e in SUPPORTED_ELEMENTS}; basis_mass = 0.0
        for index, stream in enumerate(streams):
            if not isinstance(stream,dict): return fail(f"metal_inputs[{index}]必须是对象")
            try: mass = float(stream["mass_kg"])
            except (KeyError,TypeError,ValueError): return fail(f"metal_inputs[{index}].mass_kg无效")
            if not math.isfinite(mass) or mass <= 0: return fail(f"metal_inputs[{index}].mass_kg必须大于0")
            composition,error = self._composition(stream.get("composition"),f"metal_inputs[{index}].composition")
            if error: return fail(error)
            basis_mass += mass
            for element,fraction in composition.items(): input_masses[element] += mass*fraction
        target_composition,error = self._composition(params["target_composition"],"target_composition")
        if error: return fail(error)
        target_mass = float(params["target_steel_mass_kg"])
        target_masses = {e:target_mass*target_composition.get(e,0.0) for e in SUPPORTED_ELEMENTS}
        oxidized = {e:input_masses[e]-target_masses[e] for e in SUPPORTED_ELEMENTS}
        too_large = [e for e,v in oxidized.items() if v < -1e-9]
        if too_large: return fail(f"目标元素质量超过输入: {too_large}","MASS_BALANCE_ERROR")
        oxidized = {e:max(0.0,v) for e,v in oxidized.items()}
        co2_fraction = float(params.get("carbon_to_co2_fraction",0.0)); iron_oxide = params.get("iron_oxide","FeO")
        oxygen_ratio = {"C":0.5*(1-co2_fraction)+co2_fraction,"Si":1.0,"Mn":0.5,"P":1.25,"Fe":0.5 if iron_oxide=="FeO" else 0.75}
        breakdown = {}
        for element,mass in oxidized.items():
            kmol_element = mass/weights[element]
            kmol_o2 = kmol_element*oxygen_ratio[element]
            breakdown[element] = {"oxidized_mass_kg":mass,"oxygen_ratio_kmol_o2_per_kmol_element":oxygen_ratio[element],"oxygen_kmol":kmol_o2,"oxygen_mass_kg":kmol_o2*o2_kg_kmol,"oxygen_normal_volume_m3":kmol_o2*normal_m3_kmol}
        theoretical = math.fsum(x["oxygen_kmol"] for x in breakdown.values()); utilization=float(params.get("oxygen_utilization",1.0)); supplied=theoretical/utilization
        return ModelResult(True,result={"element_oxygen_breakdown":breakdown,"input_element_masses_kg":input_masses,"target_element_masses_kg":target_masses,"oxidized_element_masses_kg":oxidized,"theoretical_oxygen_kmol":theoretical,"theoretical_oxygen_mass_kg":theoretical*o2_kg_kmol,"theoretical_oxygen_normal_volume_m3":theoretical*normal_m3_kmol,"supplied_oxygen_kmol":supplied,"supplied_oxygen_normal_volume_m3":supplied*normal_m3_kmol,"oxygen_utilization":utilization,"basis_input_mass_kg":basis_mass,"target_steel_mass_kg":target_mass},provenance=element_provenance+process_provenance)


class D002_BOFStaticHeatBalance(ProcessTool):
    required_dataset_ids = ["DS_BOF_PROCESS_PARAMETERS"]
    database_tables = ["metallurgy_v2.process_parameter_set"]
    model_id, name, version = "D002", "BOF 静态热平衡", "1.0.0"
    description = "用显式常热容、废钢潜热和热损参数，求终温或目标温度下最大可熔废钢量。"
    applicable_boundary = "零维绝热混合加显式热损；热容常数、废钢单一熔点；仅用于静态估算，非炉况控制。"
    formula_reference = "ΣH_initial+Qreaction+Qother-Qloss=ΣH_final；熔点区间用潜热熔化分数闭合"
    failure_modes = ["能量低于参考态或高于3500K模型上限", "热物性或质量不为正", "目标温度下单位废钢净需热非正", "热损为负"]
    independent_validation = ["求解后能量闭合误差小于1e-6 kJ", "无废钢时可由常热容代数复算", "熔点平台用潜热分数精确闭合"]
    dependencies = ["B003","B006","D001","T001","T002"]
    relations = [rel("depends_on","B003","显热项与通用焓积分目标重叠"),rel("depends_on","B006","反应热可由反应焓工具组合"),rel("depends_on","D001","氧化量定义反应热路径"),rel("depends_on","T001","导热损失可作为heat_loss_kj输入"),rel("depends_on","T002","辐射损失可作为heat_loss_kj输入")]
    input_fields = [
        InputField("hot_metal_mass_kg","铁水质量","number",unit="kg",min_value=1e-12),InputField("hot_metal_temperature_k","铁水温度","number",unit="K",min_value=1e-12),
        InputField("scrap_mass_kg","废钢质量","number",unit="kg",min_value=0),InputField("scrap_temperature_k","废钢初温","number",unit="K",min_value=1e-12),
        InputField("reaction_heat_kj","反应放热","number",unit="kJ"),InputField("heat_loss_kj","总热损","number",unit="kJ",min_value=0),
        InputField("solve_for","求解目标","select",required=False,default="final_temperature",enum=["final_temperature","max_scrap"]),
        InputField("target_temperature_k","目标温度","number",required=False,default=1873.0,unit="K",min_value=1e-12),
        InputField("other_heat_input_kj","其他净热输入","number",required=False,default=0.0,unit="kJ"),
        InputField("reference_temperature_k","焓参考温度","number",required=False,unit="K",min_value=1e-12,description="省略时由版本化BOF参数集提供"),
        InputField("scrap_melting_temperature_k","废钢熔点","number",required=False,unit="K",min_value=1e-12,description="省略时由版本化BOF参数集提供"),
        InputField("cp_hot_metal_kj_kg_k","液态铁水比热","number",required=False,unit="kJ/(kg·K)",min_value=1e-12,description="省略时由版本化BOF参数集提供"),
        InputField("cp_scrap_solid_kj_kg_k","固态废钢比热","number",required=False,unit="kJ/(kg·K)",min_value=1e-12,description="省略时由版本化BOF参数集提供"),
        InputField("latent_heat_scrap_kj_kg","废钢熔化潜热","number",required=False,unit="kJ/kg",min_value=0,description="省略时由版本化BOF参数集提供"),
        InputField("cp_scrap_liquid_kj_kg_k","液态废钢比热","number",required=False,unit="kJ/(kg·K)",min_value=1e-12,description="省略时由版本化BOF参数集提供"),
    ]
    output_fields = [
        OutputField("solve_for","求解目标","string"),OutputField("final_temperature_k","终温","number","K"),OutputField("maximum_meltable_scrap_kg","最大可熔废钢量","number","kg"),
        OutputField("actual_scrap_mass_kg","实际废钢质量","number","kg"),OutputField("scrap_melt_fraction","废钢熔化分数","number","dimensionless"),OutputField("fully_molten","废钢是否全熔","boolean"),
        OutputField("initial_energy_kj","初始显热与净输入总量","number","kJ"),OutputField("reaction_heat_kj","反应热","number","kJ"),OutputField("other_heat_input_kj","其他热输入","number","kJ"),
        OutputField("heat_loss_kj","热损","number","kJ"),OutputField("final_energy_kj","终态显热与潜热","number","kJ"),OutputField("energy_closure_error_kj","能量闭合误差","number","kJ"),
        OutputField("target_temperature_k","目标温度/求得终温","number","K"),OutputField("assumptions","模型假设","array"),
    ]
    validation_rules = [{"rule":"nonnegative","fields":["scrap_mass_kg","heat_loss_kj","latent_heat_scrap_kj_kg"]},{"rule":"positive","fields":["hot_metal_mass_kg","hot_metal_temperature_k","scrap_temperature_k","reference_temperature_k","scrap_melting_temperature_k","cp_hot_metal_kj_kg_k","cp_scrap_solid_kj_kg_k","cp_scrap_liquid_kj_kg_k"]}]
    qualification_cases = [
        {"id":"D002-N1","kind":"normal","input":{"hot_metal_mass_kg":1000,"hot_metal_temperature_k":1773,"scrap_mass_kg":100,"scrap_temperature_k":298.15,"reaction_heat_kj":200000,"heat_loss_kj":10000,"solve_for":"final_temperature"}},
        {"id":"D002-N2","kind":"normal","input":{"hot_metal_mass_kg":1000,"hot_metal_temperature_k":1800,"scrap_mass_kg":0,"scrap_temperature_k":298.15,"reaction_heat_kj":50000,"heat_loss_kj":10000}},
        {"id":"D002-N3","kind":"normal","input":{"hot_metal_mass_kg":1000,"hot_metal_temperature_k":1773,"scrap_mass_kg":100,"scrap_temperature_k":298.15,"reaction_heat_kj":250000,"heat_loss_kj":10000,"solve_for":"max_scrap","target_temperature_k":1873}},
        {"id":"D002-F1","kind":"failure","input":{"hot_metal_mass_kg":1000,"hot_metal_temperature_k":300,"scrap_mass_kg":100,"scrap_temperature_k":298.15,"reaction_heat_kj":0,"heat_loss_kj":100000}},
        {"id":"D002-F2","kind":"failure","input":{"hot_metal_mass_kg":1000,"hot_metal_temperature_k":1773,"scrap_mass_kg":100,"scrap_temperature_k":1000,"reaction_heat_kj":100000,"heat_loss_kj":0,"solve_for":"max_scrap","target_temperature_k":500}},
    ]
    data_qualification_cases = [{"id":"D002-D1","input":{"hot_metal_mass_kg":1000,"hot_metal_temperature_k":1773,"scrap_mass_kg":100,"scrap_temperature_k":298.15,"reaction_heat_kj":200000,"heat_loss_kj":10000,"solve_for":"final_temperature"}}]

    @staticmethod
    def _scrap_h(temperature, reference, melting, cp_solid, latent, cp_liquid, melt_fraction=None):
        if temperature < melting:
            return cp_solid*(temperature-reference)
        sensible_to_melt = cp_solid*(melting-reference)
        fraction = 1.0 if melt_fraction is None else melt_fraction
        return sensible_to_melt+fraction*latent+(cp_liquid*(temperature-melting) if fraction >= 1 else 0.0)

    def invoke(self, params, context=None):
        try:
            defaults, provenance = process_parameters(["reference_temperature","scrap_melting_temperature","cp_hot_metal","cp_scrap_solid","latent_heat_scrap","cp_scrap_liquid"])
        except RepositoryError as exc:
            return fail(str(exc), exc.error_code)
        hot_mass=float(params["hot_metal_mass_kg"]); hot_t=float(params["hot_metal_temperature_k"]); scrap_mass=float(params["scrap_mass_kg"]); scrap_t=float(params["scrap_temperature_k"])
        reaction=float(params["reaction_heat_kj"]); loss=float(params["heat_loss_kj"]); other=float(params.get("other_heat_input_kj",0.0)); mode=params.get("solve_for","final_temperature")
        reference=float(params.get("reference_temperature_k",defaults["reference_temperature"])); melting=float(params.get("scrap_melting_temperature_k",defaults["scrap_melting_temperature"])); cp_hot=float(params.get("cp_hot_metal_kj_kg_k",defaults["cp_hot_metal"])); cp_solid=float(params.get("cp_scrap_solid_kj_kg_k",defaults["cp_scrap_solid"])); latent=float(params.get("latent_heat_scrap_kj_kg",defaults["latent_heat_scrap"])); cp_liquid=float(params.get("cp_scrap_liquid_kj_kg_k",defaults["cp_scrap_liquid"]))
        if melting <= reference: return fail("废钢熔点必须高于焓参考温度")
        initial_scrap_per_kg=self._scrap_h(scrap_t,reference,melting,cp_solid,latent,cp_liquid)
        initial=hot_mass*cp_hot*(hot_t-reference)+scrap_mass*initial_scrap_per_kg+reaction+other-loss
        assumptions=["constant heat capacities","single scrap melting point","zero-dimensional static balance","reaction heat and losses supplied externally"]
        if mode == "max_scrap":
            target=float(params.get("target_temperature_k",1873.0)); required_per_kg=self._scrap_h(target,reference,melting,cp_solid,latent,cp_liquid)-initial_scrap_per_kg
            available=hot_mass*cp_hot*(hot_t-target)+reaction+other-loss
            if required_per_kg <= 0: return fail("目标温度下单位废钢净需热必须大于0","OUT_OF_DOMAIN")
            maximum=available/required_per_kg
            if maximum < 0: return fail("可用能量不足以维持目标温度","OUT_OF_DOMAIN")
            final=hot_mass*cp_hot*(target-reference)+scrap_mass*self._scrap_h(target,reference,melting,cp_solid,latent,cp_liquid)
            closure=initial-final
            fraction=1.0 if target>=melting else 0.0
            return ModelResult(True,result={"solve_for":mode,"final_temperature_k":target,"maximum_meltable_scrap_kg":maximum,"actual_scrap_mass_kg":scrap_mass,"scrap_melt_fraction":fraction,"fully_molten":bool(target>=melting),"initial_energy_kj":initial,"reaction_heat_kj":reaction,"other_heat_input_kj":other,"heat_loss_kj":loss,"final_energy_kj":final,"energy_closure_error_kj":closure,"target_temperature_k":target,"assumptions":assumptions},boundary_check=BoundaryCheck(scrap_mass<=maximum,[] if scrap_mass<=maximum else [BoundaryWarning("scrap_mass_kg","实际废钢量超过目标温度下最大可熔量")]),provenance=provenance)
        if initial < 0: return fail("净能量低于参考态","OUT_OF_DOMAIN")
        def final_energy(temperature, fraction=None):
            return hot_mass*cp_hot*(temperature-reference)+scrap_mass*self._scrap_h(temperature,reference,melting,cp_solid,latent,cp_liquid,fraction)
        solid_at_melt=hot_mass*cp_hot*(melting-reference)+scrap_mass*cp_solid*(melting-reference)
        liquid_at_melt=solid_at_melt+scrap_mass*latent
        if scrap_mass>0 and solid_at_melt <= initial <= liquid_at_melt:
            temperature=melting; fraction=(initial-solid_at_melt)/(scrap_mass*latent) if latent>0 else 1.0; final=final_energy(temperature,fraction)
        else:
            low=reference; high=melting if initial<solid_at_melt else 3500.0
            if initial>final_energy(high): return fail("净能量超过3500K模型上限","OUT_OF_DOMAIN")
            for _ in range(120):
                middle=(low+high)/2
                if final_energy(middle)<initial: low=middle
                else: high=middle
            temperature=(low+high)/2; fraction=1.0 if temperature>=melting else 0.0; final=final_energy(temperature)
        closure=initial-final; fully=bool(scrap_mass==0 or (temperature>=melting and fraction>=1-1e-12))
        return ModelResult(True,result={"solve_for":mode,"final_temperature_k":temperature,"maximum_meltable_scrap_kg":scrap_mass,"actual_scrap_mass_kg":scrap_mass,"scrap_melt_fraction":fraction,"fully_molten":fully,"initial_energy_kj":initial,"reaction_heat_kj":reaction,"other_heat_input_kj":other,"heat_loss_kj":loss,"final_energy_kj":final,"energy_closure_error_kj":closure,"target_temperature_k":temperature,"assumptions":assumptions},provenance=provenance)


_BOF_STREAM_COMPOSITION_SCHEMA = {
    "type": "object",
    "description": "元素符号到质量分数的非空映射；各值在0至1之间且总和不超过1",
    "minProperties": 1,
    "propertyNames": {"type": "string", "pattern": "^[A-Z][a-z]?$"},
    "additionalProperties": {"type": "number", "minimum": 0, "maximum": 1},
}

_BOF_INPUT_STREAM_SCHEMA = {
    "type": "object",
    "description": "一条BOF输入物流；质量与其他物流使用同一统计基准",
    "properties": {
        "name": {"type": "string", "minLength": 1, "description": "物流唯一名称"},
        "category": {
            "type": "string",
            "enum": ["hot_metal", "scrap", "metal_addition", "flux", "oxygen", "other"],
            "description": "输入物流类别",
        },
        "mass_kg": {"type": "number", "minimum": 0, "description": "物流质量；单位: kg/$basis"},
        "composition": _BOF_STREAM_COMPOSITION_SCHEMA,
    },
    "required": ["name", "category", "mass_kg", "composition"],
    "additionalProperties": False,
}

_BOF_OUTPUT_STREAM_SCHEMA = {
    "type": "object",
    "description": "一条BOF输出物流；审计模式必须给mass_kg，单未知求解时仅目标物流可省略mass_kg",
    "properties": {
        "name": {"type": "string", "minLength": 1, "description": "物流唯一名称"},
        "category": {
            "type": "string",
            "enum": ["steel", "slag", "offgas", "dust", "splash", "other"],
            "description": "输出物流类别",
        },
        "mass_kg": {"type": "number", "minimum": 0, "description": "物流质量；单位: kg/$basis"},
        "composition": _BOF_STREAM_COMPOSITION_SCHEMA,
    },
    "required": ["name", "category", "composition"],
    "additionalProperties": False,
}


class D021_BOFChargeBalance(FormulaProcessTool):
    """Catalog D001; D021 avoids colliding with legacy runtime D001."""

    model_id, name, version = "D021", "转炉装料物料平衡", "1.0.0"
    tool_name = "metallurgy_balance_bof_charge"
    description = "在统一炉次或吨钢基准下审计BOF输入/输出总质量和逐元素闭合，或用一个指定元素求解唯一未知输出物流质量。"
    applicable_boundary = "零维静态完全混合；所有物流成分、路由和收得结果必须显式输入；最多求解一个未知输出质量，不用于在线配料控制。"
    data_source = ["Conservation of mass and chemical elements", "EU Iron and Steel BREF process boundaries"]
    source_version = "bof-charge-balance-v1; EU Iron and Steel BREF process-boundary reference"
    formula_reference = "r_m=sum(m_in)-sum(m_out); r_e=sum(m_in*w_e)-sum(m_out*w_e); m_unknown=(E_in-E_known_out)/w_unknown"
    source_records = [
        {"source_id": "MASS-CONSERVATION", "name": "Conservation of mass and chemical elements", "version": "v1"},
        {"source_id": "EU-IRON-STEEL-BREF", "name": "EU Iron and Steel Production BREF", "version": "2013", "url": "https://eippcb.jrc.ec.europa.eu/reference/iron-and-steel-production"},
    ]
    failure_modes = ["物流质量为负或组成不闭合", "统计基准缺失或混用", "多于一个未知物流导致欠定", "求解元素在未知物流中含量为零", "约束产生负质量解"]
    independent_validation = ["总质量及逐元素残差按输入减输出直接复算", "所有物流同比缩放时闭合率不变", "物流拆分合并不改变元素残差", "单未知解代回指定元素方程残差为零"]
    dependencies = ["A004", "A005"]
    relations = [
        rel("depends_on", "A004", "每个物流的质量分数组成遵循相同非负归一化约束"),
        rel("overlaps", "A005", "A005是通用校验原子工具，本工具增加BOF物流类别、钢水收得率和单未知求解"),
        rel("complements", "D001", "现有D001只计算目录D003理论耗氧，本工具计算全装料静态闭合"),
        rel("upstream_of", "D002", "闭合后的装料质量可进入BOF静态热平衡"),
        rel("overlaps", "D004", "D004求熔剂子问题，本工具接收其熔剂物流结果"),
    ]
    input_fields = [
        InputField("basis", "统计基准", "select", enum=["per_heat", "per_t_steel", "per_hour"], description="所有质量都按同一基准给出"),
        InputField("input_streams", "输入物流", "array", items=_BOF_INPUT_STREAM_SCHEMA, min_items=1, description="BOF输入物流数组；每项包含名称、类别、质量和元素质量分数组成"),
        InputField("output_streams", "输出物流", "array", items=_BOF_OUTPUT_STREAM_SCHEMA, min_items=1, description="BOF输出物流数组；审计模式每项均给质量，单未知求解时仅目标物流省略质量"),
        InputField("solve_stream_name", "待求输出物流名", "string", required=False, description="省略表示仅审计；给出时必须只有该输出物流缺mass_kg"),
        InputField("solve_element", "求解约束元素", "string", required=False, description="单未知求解时必填，且该元素在待求物流中质量分数大于0"),
        InputField("absolute_tolerance_kg", "绝对闭合容差", "number", required=False, default=1e-6, unit="kg/$basis", min_value=0),
        InputField("relative_tolerance", "相对闭合容差", "number", required=False, default=1e-8, unit="1", min_value=0, max_value=1),
    ]
    output_fields = [
        OutputField("basis", "统计基准", "string"),
        OutputField("mode", "执行模式", "string"),
        OutputField("stream_summary", "规范化物流", "object"),
        OutputField("element_balances", "逐元素平衡", "object"),
        OutputField("total_input_mass_kg", "总输入质量", "number", "kg/$basis"),
        OutputField("total_output_mass_kg", "总输出质量", "number", "kg/$basis"),
        OutputField("mass_residual_kg", "总质量残差", "number", "kg/$basis"),
        OutputField("mass_closure_rate", "总质量闭合率", "number", "1"),
        OutputField("max_element_residual_kg", "最大元素残差", "number", "kg/$basis"),
        OutputField("metallic_charge_mass_kg", "金属装料质量", "number", "kg/$basis"),
        OutputField("target_steel_mass_kg", "钢水质量", "number", "kg/$basis"),
        OutputField("steel_yield", "金属装料钢水收得率", "number", "1"),
        OutputField("solved_stream", "求解物流信息", "object"),
        OutputField("passed", "是否闭合", "boolean"),
    ]
    validation_rules = [
        {"rule": "single_common_basis", "field": "basis"},
        {"rule": "nonnegative_mass_fraction_streams", "fields": ["input_streams", "output_streams"]},
        {"rule": "at_most_one_unknown_output", "field": "output_streams"},
    ]
    qualification_cases = [
        {"id": "D021-N1", "kind": "normal", "input": {"basis": "per_heat", "input_streams": [{"name": "hot_metal", "category": "hot_metal", "mass_kg": 100, "composition": {"Fe": 0.96, "C": 0.04}}], "output_streams": [{"name": "steel", "category": "steel", "mass_kg": 96, "composition": {"Fe": 1}}, {"name": "offgas_carbon", "category": "offgas", "mass_kg": 4, "composition": {"C": 1}}]}},
        {"id": "D021-N2", "kind": "normal", "input": {"basis": "per_t_steel", "input_streams": [{"name": "iron", "category": "metal_addition", "mass_kg": 60, "composition": {"Fe": 1}}, {"name": "carbon", "category": "other", "mass_kg": 40, "composition": {"C": 1}}], "output_streams": [{"name": "product", "category": "steel", "mass_kg": 100, "composition": {"Fe": 0.6, "C": 0.4}}]}},
        {"id": "D021-N3", "kind": "normal", "input": {"basis": "per_heat", "input_streams": [{"name": "iron", "category": "hot_metal", "mass_kg": 100, "composition": {"Fe": 1}}], "output_streams": [{"name": "steel", "category": "steel", "composition": {"Fe": 1}}], "solve_stream_name": "steel", "solve_element": "Fe"}},
        {"id": "D021-B1", "kind": "boundary", "input": {"basis": "per_heat", "input_streams": [{"name": "iron", "category": "hot_metal", "mass_kg": 100, "composition": {"Fe": 1}}], "output_streams": [{"name": "steel", "category": "steel", "mass_kg": 90, "composition": {"Fe": 1}}]}},
        {"id": "D021-F1", "kind": "failure", "input": {"basis": "per_heat", "input_streams": [{"name": "iron", "category": "hot_metal", "mass_kg": 100, "composition": {"Fe": 1}}], "output_streams": [{"name": "known", "category": "steel", "mass_kg": 110, "composition": {"Fe": 1}}, {"name": "unknown", "category": "dust", "composition": {"Fe": 1}}], "solve_stream_name": "unknown", "solve_element": "Fe"}},
    ]

    _INPUT_CATEGORIES = {"hot_metal", "scrap", "metal_addition", "flux", "oxygen", "other"}
    _OUTPUT_CATEGORIES = {"steel", "slag", "offgas", "dust", "splash", "other"}

    @staticmethod
    def _composition(raw, label):
        if not isinstance(raw, dict) or not raw:
            return None, f"{label}必须是非空对象"
        parsed = {}
        for element, raw_fraction in raw.items():
            if not isinstance(element, str) or not re.fullmatch(r"[A-Z][a-z]?", element):
                return None, f"{label}包含非法元素符号 {element}"
            if isinstance(raw_fraction, bool):
                return None, f"{label}.{element}必须是数值"
            try:
                fraction = float(raw_fraction)
            except (TypeError, ValueError):
                return None, f"{label}.{element}必须是数值"
            if not math.isfinite(fraction) or not 0 <= fraction <= 1:
                return None, f"{label}.{element}必须在[0,1]"
            parsed[element] = fraction
        if math.fsum(parsed.values()) > 1 + 1e-12:
            return None, f"{label}质量分数之和不能超过1"
        return parsed, None

    def _streams(self, raw, direction, allow_unknown=False):
        if not isinstance(raw, list) or not raw:
            return None, f"{direction}_streams必须是非空数组"
        categories = self._INPUT_CATEGORIES if direction == "input" else self._OUTPUT_CATEGORIES
        parsed, names = [], set()
        for index, stream in enumerate(raw):
            if not isinstance(stream, dict):
                return None, f"{direction}_streams[{index}]必须是对象"
            name, category = stream.get("name"), stream.get("category")
            if not isinstance(name, str) or not name.strip() or name in names:
                return None, f"{direction}_streams[{index}].name必须是唯一非空字符串"
            if category not in categories:
                return None, f"{direction}_streams[{index}].category不受支持"
            names.add(name)
            composition, error = self._composition(stream.get("composition"), f"{direction}_streams[{index}].composition")
            if error:
                return None, error
            mass = stream.get("mass_kg")
            if mass is None and allow_unknown:
                parsed.append({"name": name, "category": category, "mass_kg": None, "composition": composition})
                continue
            if isinstance(mass, bool):
                return None, f"{direction}_streams[{index}].mass_kg必须是数值"
            try:
                mass = float(mass)
            except (TypeError, ValueError):
                return None, f"{direction}_streams[{index}].mass_kg必须是数值"
            if not math.isfinite(mass) or mass < 0:
                return None, f"{direction}_streams[{index}].mass_kg必须是非负有限数值"
            parsed.append({"name": name, "category": category, "mass_kg": mass, "composition": composition})
        return parsed, None

    @staticmethod
    def _element_totals(streams):
        totals = {}
        for stream in streams:
            for element, fraction in stream["composition"].items():
                totals[element] = totals.get(element, 0.0) + stream["mass_kg"] * fraction
        return totals

    def invoke(self, params, context=None):
        inputs, error = self._streams(params["input_streams"], "input")
        if error:
            return fail(error)
        solve_name = params.get("solve_stream_name")
        outputs, error = self._streams(params["output_streams"], "output", allow_unknown=bool(solve_name))
        if error:
            return fail(error)
        unknowns = [stream for stream in outputs if stream["mass_kg"] is None]
        solved_stream = {}
        if solve_name:
            if len(unknowns) != 1 or unknowns[0]["name"] != solve_name:
                return fail("单未知模式必须且只能有solve_stream_name指定的一个输出物流缺少mass_kg")
            solve_element = params.get("solve_element")
            if not isinstance(solve_element, str) or not re.fullmatch(r"[A-Z][a-z]?", solve_element):
                return fail("单未知模式必须提供合法solve_element")
            fraction = unknowns[0]["composition"].get(solve_element, 0.0)
            if fraction <= 0:
                return fail("待求物流中solve_element质量分数必须大于0")
            input_element = self._element_totals(inputs).get(solve_element, 0.0)
            known_output_element = self._element_totals([x for x in outputs if x["mass_kg"] is not None]).get(solve_element, 0.0)
            solved_mass = (input_element - known_output_element) / fraction
            if solved_mass < -1e-12:
                return fail("指定元素约束产生负质量解", "OUT_OF_DOMAIN")
            unknowns[0]["mass_kg"] = max(0.0, solved_mass)
            solved_stream = {"name": solve_name, "solve_element": solve_element, "mass_kg": unknowns[0]["mass_kg"]}
            mode = "single_unknown_mass"
        else:
            if unknowns:
                return fail("审计模式下所有输出物流必须提供mass_kg")
            if params.get("solve_element"):
                return fail("未指定solve_stream_name时不得单独提供solve_element")
            mode = "audit"
        total_input = math.fsum(x["mass_kg"] for x in inputs)
        total_output = math.fsum(x["mass_kg"] for x in outputs)
        input_elements = self._element_totals(inputs)
        output_elements = self._element_totals(outputs)
        absolute = float(params.get("absolute_tolerance_kg", 1e-6))
        relative = float(params.get("relative_tolerance", 1e-8))
        element_balances = {}
        for element in sorted(set(input_elements) | set(output_elements)):
            incoming, outgoing = input_elements.get(element, 0.0), output_elements.get(element, 0.0)
            residual = incoming - outgoing
            tolerance = max(absolute, relative * max(incoming, outgoing, 1.0))
            element_balances[element] = {"input_mass_kg": incoming, "output_mass_kg": outgoing, "residual_kg": residual, "closure_rate": 1.0 - abs(residual) / max(incoming, outgoing, 1.0), "passed": abs(residual) <= tolerance}
        mass_residual = total_input - total_output
        mass_tolerance = max(absolute, relative * max(total_input, total_output, 1.0))
        passed = abs(mass_residual) <= mass_tolerance and all(x["passed"] for x in element_balances.values())
        max_element = max((abs(x["residual_kg"]) for x in element_balances.values()), default=0.0)
        metallic = math.fsum(x["mass_kg"] for x in inputs if x["category"] in {"hot_metal", "scrap", "metal_addition"})
        steel = math.fsum(x["mass_kg"] for x in outputs if x["category"] == "steel")
        yield_value = steel / metallic if metallic > 0 else 0.0
        warnings = [] if passed else [BoundaryWarning("streams", "BOF装料总质量或逐元素平衡未在声明容差内闭合")]
        return ModelResult(
            True,
            result={
                "basis": params["basis"],
                "mode": mode,
                "stream_summary": {"inputs": inputs, "outputs": outputs},
                "element_balances": element_balances,
                "total_input_mass_kg": total_input,
                "total_output_mass_kg": total_output,
                "mass_residual_kg": mass_residual,
                "mass_closure_rate": 1.0 - abs(mass_residual) / max(total_input, total_output, 1.0),
                "max_element_residual_kg": max_element,
                "metallic_charge_mass_kg": metallic,
                "target_steel_mass_kg": steel,
                "steel_yield": yield_value,
                "solved_stream": solved_stream,
                "passed": passed,
            },
            boundary_check=BoundaryCheck(passed, warnings),
        )


class D004_BOFFluxAddition(FormulaProcessTool):
    model_id, name, version = "D004", "石灰/白云石加入量", "1.0.0"
    tool_name = "metallurgy_calc_bof_flux_addition"
    description = "根据现有渣源、石灰/白云石化验和利用率，联立目标CaO/SiO2碱度与MgO质量分数，求非负熔剂加入量。"
    applicable_boundary = "静态完全混合且各氧化物按给定利用率进入渣相；不模拟溶解动力学、喷溅、挥发或分批加料。"
    data_source = ["Oxide mass conservation", "CaO/SiO2 basicity definition"]
    source_version = "bof-flux-linear-balance-v1"
    formula_reference = "CaO_f-B*SiO2_f=0; MgO_f-f_MgO*m_slag,f=0; solve 2x2 nonnegative system"
    source_records = [
        {"source_id": "OXIDE-MASS-BALANCE", "name": "Oxide mass conservation and binary basicity definition", "version": "v1"},
        {"source_id": "EU-IRON-STEEL-BREF", "name": "EU Iron and Steel Production BREF process boundary", "version": "2013", "url": "https://eippcb.jrc.ec.europa.eu/reference/iron-and-steel-production"},
    ]
    failure_modes = ["氧化物质量或化验为负", "化验质量分数不闭合", "约束矩阵奇异", "目标不可达并产生负加入量", "最终SiO2或总渣量为零"]
    independent_validation = ["将加入量代回碱度与MgO方程残差为零", "现有渣与熔剂量同比缩放时目标组成不变", "零加入边界保持初始渣组成", "两种熔剂化验相同导致奇异系统并失败"]
    dependencies = ["A004"]
    relations = [
        rel("depends_on", "A004", "熔剂化验遵循质量分数闭合约束"),
        rel("overlaps", "D021", "本工具求解D021全炉物料平衡中的熔剂子问题"),
        rel("upstream_of", "D002", "熔剂质量和预计渣量可进入热平衡"),
    ]
    input_fields = [
        InputField("existing_oxide_masses_kg", "现有渣源氧化物质量", "object", unit="kg/$basis", description="必须包含CaO、SiO2、MgO，可含其他非负氧化物质量", json_schema=OXIDE_MASS_MAP_SCHEMA),
        InputField("lime_assay", "石灰化验", "object", unit="1", description="必须包含CaO、SiO2、MgO；可含其他氧化物，质量分数和必须为1", json_schema=OXIDE_ASSAY_SCHEMA),
        InputField("dolomite_assay", "白云石化验", "object", unit="1", description="必须包含CaO、SiO2、MgO；可含其他氧化物，质量分数和必须为1", json_schema=OXIDE_ASSAY_SCHEMA),
        InputField("target_basicity", "目标二元碱度", "number", unit="1", min_value=1e-12, description="最终CaO/SiO2"),
        InputField("target_mgo_fraction", "目标MgO质量分数", "number", unit="1", min_value=0, max_value=0.5),
        InputField("lime_utilization", "石灰入渣利用率", "number", required=False, default=1.0, unit="1", min_value=1e-12, max_value=1),
        InputField("dolomite_utilization", "白云石入渣利用率", "number", required=False, default=1.0, unit="1", min_value=1e-12, max_value=1),
        InputField("basis", "统计基准", "select", required=False, default="per_heat", enum=["per_heat", "per_t_steel"]),
    ]
    output_fields = [
        OutputField("basis", "统计基准", "string"),
        OutputField("lime_addition_kg", "石灰加入量", "number", "kg/$basis"),
        OutputField("dolomite_addition_kg", "白云石加入量", "number", "kg/$basis"),
        OutputField("predicted_oxide_masses_kg", "预计渣中氧化物质量", "object"),
        OutputField("predicted_slag_mass_kg", "预计渣量", "number", "kg/$basis"),
        OutputField("achieved_basicity", "实际二元碱度", "number", "1"),
        OutputField("achieved_mgo_fraction", "实际MgO质量分数", "number", "1"),
        OutputField("basicity_residual", "碱度残差", "number", "1"),
        OutputField("mgo_fraction_residual", "MgO分数残差", "number", "1"),
        OutputField("constraint_determinant", "约束矩阵行列式", "number", "1"),
        OutputField("passed", "约束是否闭合", "boolean"),
    ]
    validation_rules = [
        {"rule": "nonnegative_oxide_masses", "field": "existing_oxide_masses_kg"},
        {"rule": "closed_assay", "fields": ["lime_assay", "dolomite_assay"]},
        {"rule": "nonnegative_unique_solution", "fields": ["target_basicity", "target_mgo_fraction"]},
    ]
    qualification_cases = [
        {"id": "D004-N1", "kind": "normal", "input": {"existing_oxide_masses_kg": {"CaO": 10, "SiO2": 20, "MgO": 1, "Other": 9}, "lime_assay": {"CaO": 0.9, "SiO2": 0.05, "MgO": 0.02, "Other": 0.03}, "dolomite_assay": {"CaO": 0.55, "SiO2": 0.05, "MgO": 0.35, "Other": 0.05}, "target_basicity": 1.0481927710843373, "target_mgo_fraction": 0.053636363636363635}},
        {"id": "D004-N2", "kind": "normal", "input": {"existing_oxide_masses_kg": {"CaO": 5, "SiO2": 15, "MgO": 0.5, "Other": 4.5}, "lime_assay": {"CaO": 0.9, "SiO2": 0.05, "MgO": 0.02, "Other": 0.03}, "dolomite_assay": {"CaO": 0.55, "SiO2": 0.05, "MgO": 0.35, "Other": 0.05}, "target_basicity": 1.7272727272727273, "target_mgo_fraction": 0.08}},
        {"id": "D004-N3", "kind": "normal", "input": {"existing_oxide_masses_kg": {"CaO": 5, "SiO2": 10, "MgO": 1, "Other": 14}, "lime_assay": {"CaO": 0.9, "SiO2": 0.05, "MgO": 0.02, "Other": 0.03}, "dolomite_assay": {"CaO": 0.55, "SiO2": 0.05, "MgO": 0.35, "Other": 0.05}, "target_basicity": 1.5806451612903225, "target_mgo_fraction": 0.09170212765957447, "lime_utilization": 0.8, "dolomite_utilization": 0.9}},
        {"id": "D004-B1", "kind": "boundary", "input": {"existing_oxide_masses_kg": {"CaO": 20, "SiO2": 10, "MgO": 2, "Other": 8}, "lime_assay": {"CaO": 0.9, "SiO2": 0.05, "MgO": 0.02, "Other": 0.03}, "dolomite_assay": {"CaO": 0.55, "SiO2": 0.05, "MgO": 0.35, "Other": 0.05}, "target_basicity": 2, "target_mgo_fraction": 0.05}},
        {"id": "D004-F1", "kind": "failure", "input": {"existing_oxide_masses_kg": {"CaO": 10, "SiO2": 20, "MgO": 1, "Other": 9}, "lime_assay": {"CaO": 0.8, "SiO2": 0.1, "MgO": 0.05, "Other": 0.05}, "dolomite_assay": {"CaO": 0.8, "SiO2": 0.1, "MgO": 0.05, "Other": 0.05}, "target_basicity": 2, "target_mgo_fraction": 0.08}},
    ]

    @staticmethod
    def _oxide_mapping(raw, label, require_closed):
        if not isinstance(raw, dict) or not raw:
            return None, f"{label}必须是非空对象"
        parsed = {}
        for oxide, raw_value in raw.items():
            if not isinstance(oxide, str) or not oxide.strip():
                return None, f"{label}氧化物名称必须是非空字符串"
            if isinstance(raw_value, bool):
                return None, f"{label}.{oxide}必须是数值"
            try:
                value = float(raw_value)
            except (TypeError, ValueError):
                return None, f"{label}.{oxide}必须是数值"
            if not math.isfinite(value) or value < 0:
                return None, f"{label}.{oxide}必须是非负有限数值"
            parsed[oxide] = value
        if require_closed and not math.isclose(math.fsum(parsed.values()), 1.0, rel_tol=0.0, abs_tol=1e-9):
            return None, f"{label}质量分数之和必须为1"
        for required in ("CaO", "SiO2", "MgO"):
            if required not in parsed:
                return None, f"{label}必须包含{required}"
        return parsed, None

    def invoke(self, params, context=None):
        existing, error = self._oxide_mapping(params["existing_oxide_masses_kg"], "existing_oxide_masses_kg", False)
        if error:
            return fail(error)
        lime, error = self._oxide_mapping(params["lime_assay"], "lime_assay", True)
        if error:
            return fail(error)
        dolomite, error = self._oxide_mapping(params["dolomite_assay"], "dolomite_assay", True)
        if error:
            return fail(error)
        basicity = float(params["target_basicity"])
        mgo_fraction = float(params["target_mgo_fraction"])
        lime_util = float(params.get("lime_utilization", 1.0))
        dolo_util = float(params.get("dolomite_utilization", 1.0))
        total_existing = math.fsum(existing.values())
        if total_existing <= 0 or existing["SiO2"] <= 0:
            return fail("现有渣源总量和SiO2质量必须大于0", "OUT_OF_DOMAIN")
        a11 = lime_util * (lime["CaO"] - basicity * lime["SiO2"])
        a12 = dolo_util * (dolomite["CaO"] - basicity * dolomite["SiO2"])
        b1 = basicity * existing["SiO2"] - existing["CaO"]
        a21 = lime_util * (lime["MgO"] - mgo_fraction)
        a22 = dolo_util * (dolomite["MgO"] - mgo_fraction)
        b2 = mgo_fraction * total_existing - existing["MgO"]
        determinant = a11 * a22 - a12 * a21
        if abs(determinant) <= 1e-12:
            return fail("石灰与白云石化验形成奇异约束矩阵，无法唯一求解", "NUMERICAL_ERROR")
        lime_mass = (b1 * a22 - a12 * b2) / determinant
        dolomite_mass = (a11 * b2 - b1 * a21) / determinant
        if lime_mass < -1e-9 or dolomite_mass < -1e-9:
            return fail("目标碱度/MgO约束产生负熔剂加入量，当前原料下不可达", "OUT_OF_DOMAIN")
        lime_mass, dolomite_mass = max(0.0, lime_mass), max(0.0, dolomite_mass)
        final = dict(existing)
        for oxide in sorted(set(final) | set(lime) | set(dolomite)):
            final[oxide] = final.get(oxide, 0.0) + lime_mass * lime_util * lime.get(oxide, 0.0) + dolomite_mass * dolo_util * dolomite.get(oxide, 0.0)
        slag_mass = math.fsum(final.values())
        if final.get("SiO2", 0.0) <= 0 or slag_mass <= 0:
            return fail("最终SiO2或总渣量为零，无法定义目标指标", "OUT_OF_DOMAIN")
        achieved_basicity = final["CaO"] / final["SiO2"]
        achieved_mgo = final["MgO"] / slag_mass
        basicity_residual = achieved_basicity - basicity
        mgo_residual = achieved_mgo - mgo_fraction
        passed = abs(basicity_residual) <= 1e-10 and abs(mgo_residual) <= 1e-10
        boundary_messages = []
        if lime_mass <= 1e-9:
            boundary_messages.append("石灰加入量位于零边界")
        if dolomite_mass <= 1e-9:
            boundary_messages.append("白云石加入量位于零边界")
        if not passed:
            boundary_messages.append("代回约束的数值残差超过容差")
        warnings = [BoundaryWarning("flux_addition", message) for message in boundary_messages]
        return ModelResult(
            True,
            result={
                "basis": params.get("basis", "per_heat"),
                "lime_addition_kg": lime_mass,
                "dolomite_addition_kg": dolomite_mass,
                "predicted_oxide_masses_kg": final,
                "predicted_slag_mass_kg": slag_mass,
                "achieved_basicity": achieved_basicity,
                "achieved_mgo_fraction": achieved_mgo,
                "basicity_residual": basicity_residual,
                "mgo_fraction_residual": mgo_residual,
                "constraint_determinant": determinant,
                "passed": passed,
            },
            boundary_check=BoundaryCheck(passed and not boundary_messages, warnings),
        )
