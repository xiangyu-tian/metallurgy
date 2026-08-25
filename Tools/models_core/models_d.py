"""Qualified BOF process tools for the 30-tool milestone.

These are transparent static balances, not plant-control models.  All empirical
assumptions are inputs or versioned defaults so that later metallurgical review
can replace them without changing the tool contract.
"""
from __future__ import annotations

import math

from .base import BaseModelTool, BoundaryCheck, BoundaryWarning, InputField, ModelResult, OutputField
from .repositories.reference_repository import RepositoryError, atomic_weights, process_parameters


SUPPORTED_ELEMENTS = ("C", "Si", "Mn", "P", "Fe")


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
        InputField("metal_inputs", "金属装料", "array", items={"type":"object"}, description="[{name,mass_kg,composition:{C,Si,Mn,P,Fe}}]"),
        InputField("target_steel_mass_kg", "目标钢水质量", "number", unit="kg", min_value=1e-12),
        InputField("target_composition", "目标钢水组成", "object", description="元素质量分数"),
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
