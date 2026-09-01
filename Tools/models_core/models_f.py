"""Qualified continuous-casting and CALPHAD solidification tools."""

from __future__ import annotations

import math
import warnings
from functools import lru_cache

import numpy as np
from pycalphad import equilibrium, variables as v
from scheil import simulate_scheil_solidification
from scipy.linalg import solve_banded

from .base import BaseModelTool, BoundaryCheck, BoundaryWarning, InputField, ModelResult, OutputField
from .repositories.casting_endpoint_repository import approved_machine_configuration
from .repositories.casting_thermal_repository import (
    approved_property_model,
    boundary_profile,
    correlation_derivative,
    evaluate_correlation_rows,
)
from .repositories.reference_repository import RepositoryError
from .repositories.solidification_repository import load_database


MODEL_ASSET_ID = "MATCALC-MC_FE-2.059-PYCALPHAD"
LIQUID_THRESHOLD = 1e-6


def _normalise_composition(raw):
    if not isinstance(raw, dict) or not raw:
        return {}, "composition_wt_percent必须是至少含一个溶质的对象"
    result = {}
    for symbol, value in raw.items():
        key = str(symbol).upper()
        try:
            number = float(value)
        except (TypeError, ValueError):
            return {}, f"{symbol}质量百分数必须是数值"
        if not math.isfinite(number) or number < 0:
            return {}, f"{symbol}质量百分数必须是有限非负数"
        if number > 0:
            result[key] = number
    if not result:
        return {}, "至少一个溶质质量百分数必须大于0；纯铁请显式传入C=0后续版本支持"
    if sum(result.values()) >= 50:
        return {}, "当前版本限定铁基钢，溶质总量必须小于50 wt%"
    return result, None


def _validate_against_definition(composition, row):
    supported = set(row["supported_components"])
    unknown = sorted(set(composition) - supported)
    if unknown:
        return f"当前批准模型不支持组元: {', '.join(unknown)}"
    maxima = row["domain_json"]["component_max_wt_percent"]
    exceeded = [f"{key}={value:g} (必须小于{float(maxima[key]):g})"
                for key, value in composition.items() if value >= float(maxima[key])]
    return "组分超出数据库已评估域: " + "; ".join(exceeded) if exceeded else None


def _phase_fractions(eq_result, point_count):
    phases = np.asarray(eq_result.Phase.values).reshape(point_count, -1)
    amounts = np.asarray(eq_result.NP.values, dtype=float).reshape(point_count, -1)
    rows = []
    for names, values in zip(phases, amounts):
        merged = {}
        for name, value in zip(names, values):
            if name and math.isfinite(value):
                merged[str(name)] = merged.get(str(name), 0.0) + float(value)
        rows.append(merged)
    return rows


@lru_cache(maxsize=64)
def _equilibrium_curve(composition_key, start_k, end_k, step_k):
    db, row, provenance = load_database(MODEL_ASSET_ID)
    composition = dict(composition_key)
    components = ["FE", *composition, "VA"]
    phases = [name for name in row["phase_set"] if name in db.phases]
    temperatures = np.arange(start_k, end_k + step_k * 0.25, step_k, dtype=float)
    conditions = {v.P: 101325, v.N: 1, v.T: temperatures}
    conditions.update({v.W(symbol): value / 100.0 for symbol, value in composition.items()})
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="The type definition character.*", category=UserWarning)
        calculated = equilibrium(db, components, phases, conditions)
    fractions = _phase_fractions(calculated, len(temperatures))
    # A vectorized solve can occasionally leave an isolated vertex empty even
    # when both adjacent temperatures converge. Retry only those invalid points
    # as scalar equilibria; never reinterpret a missing numerical solution as
    # a physically all-solid state.
    solution_status = ["direct"] * len(fractions)
    for index, phase_row in enumerate(fractions):
        if phase_row and abs(sum(phase_row.values()) - 1.0) <= 1e-6:
            continue
        scalar_conditions = dict(conditions)
        scalar_conditions[v.T] = float(temperatures[index])
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="The type definition character.*", category=UserWarning)
            scalar = equilibrium(db, components, phases, scalar_conditions)
        retried = _phase_fractions(scalar, 1)[0]
        if retried and abs(sum(retried.values()) - 1.0) <= 1e-6:
            fractions[index] = retried
            solution_status[index] = "scalar_retry"
        else:
            fractions[index] = None
    index = 0
    while index < len(fractions):
        if fractions[index] is not None:
            index += 1
            continue
        gap_start = index
        while index < len(fractions) and fractions[index] is None:
            index += 1
        gap_end = index - 1
        if gap_start == 0 or index == len(fractions):
            raise ValueError(f"CALPHAD equilibrium did not close at {temperatures[gap_start]:g} K")
        left, right = fractions[gap_start-1], fractions[index]
        names = set(left) | set(right)
        span = index - (gap_start - 1)
        for failed_index in range(gap_start, gap_end + 1):
            alpha = (failed_index - (gap_start - 1)) / span
            interpolated = {
                name:(1-alpha)*left.get(name,0.0)+alpha*right.get(name,0.0)
                for name in names
            }
            total = sum(interpolated.values())
            fractions[failed_index] = {
                name:value/total for name,value in interpolated.items() if value > 1e-12
            }
            solution_status[failed_index] = "bounded_interpolation_after_failed_equilibrium"
    liquid = [min(1.0, max(0.0, item.get("LIQUID", 0.0))) for item in fractions]
    return temperatures.tolist(), liquid, fractions, provenance, solution_status


def _endpoint_result(composition, start_k, end_k, step_k):
    temperatures, liquid, phases, provenance, _ = _equilibrium_curve(
        tuple(sorted(composition.items())), start_k, end_k, step_k
    )
    positive = [i for i, value in enumerate(liquid) if value > LIQUID_THRESHOLD]
    all_liquid = [i for i, value in enumerate(liquid) if value >= 1 - LIQUID_THRESHOLD]
    if not positive or not all_liquid:
        raise ValueError("给定温区没有同时覆盖固相线和液相线")
    solidus_i, liquidus_i = positive[0], all_liquid[0]
    if solidus_i > liquidus_i:
        raise ValueError("求得的凝固区间顺序异常")
    return {
        "solidus_k": float(temperatures[solidus_i]),
        "liquidus_k": float(temperatures[liquidus_i]),
        "solidus_phases": phases[solidus_i],
        "liquidus_phases": phases[liquidus_i],
        "provenance": provenance,
    }


class _CalphadEndpointTool(BaseModelTool):
    model_type = "CALPHAD平衡计算"
    scenario = "凝固与连铸"
    priority = "P0"
    status = qualification_status = "qualified"
    count_eligible = True
    data_requirement = "VERSIONED_DATABASE_AND_MODEL_ASSET"
    data_access_mode = "database_repository"
    required_dataset_ids = ["DS_MATCALC_MC_FE_2059"]
    database_tables = ["metallurgy_v2.solidification_model_definition"]
    temperature_range = [673.0, 2000.0]
    data_source = ["MatCalc mc_fe v2.059 TDB", "pycalphad 0.11.2"]
    source_version = "mc_fe_v2.059@0a8dd091; pycalphad-0.11.2"
    formula_reference = "CALPHAD Gibbs-energy minimization at 101325 Pa; phase fraction from equilibrium NP"
    source_records = [{"source_id": "DS_MATCALC_MC_FE_2059", "name": "MatCalc mc_fe steel database", "version": "2.059", "url": "https://github.com/pyroll-project/pyroll-examples/blob/0a8dd09136e3c9c1e73afee054bb55a8f6cd84b0/mc_fe_v2.059.pycalphad.tdb"}]
    applicable_boundary = "铁基钢；wt%输入；仅C/Si/Mn/Cr/Ni/Mo/Cu/Al；673–2000 K；固定批准相集与1 atm平衡模型。"
    failure_modes = ["组元不受支持或超数据库评估域", "温区未覆盖完整凝固区间", "模型记录未批准、资产缺失或哈希不符", "CALPHAD数值求解失败"]
    independent_validation = ["纯铁熔点区间检查", "液相分数随温度非递减", "液相线不低于固相线", "F001/F002端点与F004平衡曲线一致"]
    input_fields = [
        InputField("composition_wt_percent", "钢中溶质质量百分数", "object", unit="wt%", description="Fe为余量；键限C/Si/Mn/Cr/Ni/Mo/Cu/Al"),
        InputField("temperature_min_k", "搜索温度下限", "number", required=False, default=1300.0, unit="K", min_value=673, max_value=1999),
        InputField("temperature_max_k", "搜索温度上限", "number", required=False, default=1950.0, unit="K", min_value=674, max_value=2000),
        InputField("grid_step_k", "温度网格步长", "number", required=False, default=2.0, unit="K", min_value=0.5, max_value=10),
    ]
    validation_rules = [{"rule": "iron_balance_weight_percent_domain"}, {"rule": "temperature_grid_covers_transition"}]

    def invoke(self, params, context=None):
        composition, error = _normalise_composition(params["composition_wt_percent"])
        if error:
            return ModelResult(False, error=error, error_code="INVALID_INPUT")
        low = float(params.get("temperature_min_k", 1300.0))
        high = float(params.get("temperature_max_k", 1950.0))
        step = float(params.get("grid_step_k", 2.0))
        if low >= high or high - low < 2 * step:
            return ModelResult(False, error="温度上限必须高于下限且至少跨越两个网格步长", error_code="TEMPERATURE_RANGE_ERROR")
        try:
            _, row, _ = load_database(MODEL_ASSET_ID)
            domain_error = _validate_against_definition(composition, row)
            if domain_error:
                return ModelResult(False, error=domain_error, error_code="OUT_OF_DOMAIN")
            endpoints = _endpoint_result(composition, low, high, step)
        except RepositoryError as exc:
            return ModelResult(False, error=str(exc), error_code=exc.error_code)
        except Exception as exc:
            return ModelResult(False, error=str(exc), error_code="NUMERICAL_ERROR")
        warnings_out = []
        maxima = row["domain_json"]["component_max_wt_percent"]
        if any(value >= 0.9 * float(maxima[key]) for key, value in composition.items()):
            warnings_out.append(BoundaryWarning("composition_wt_percent", "组分接近批准数据库评估域上限"))
        return self._success(composition, endpoints, step, warnings_out)


class F001_LiquidusTemperature(_CalphadEndpointTool):
    model_id, name, version = "F001", "钢液液相线温度", "1.0.0"
    tool_name = "metallurgy_calc_steel_liquidus_temperature"
    description = "用批准的CALPHAD钢数据库计算给定铁基钢成分的平衡液相线温度。"
    relations = [
        {"type": "overlaps_with", "target": "F004", "description": "F004平衡曲线包含同一液相端点，F001返回面向选型的单值端点"},
        {"type": "feeds", "target": "F003", "description": "液相线可作为F003钢液过热度的显式上游输入"},
        {"type": "paired_with", "target": "F002", "description": "相同模型和输入下分别给出凝固区间上、下端点"},
    ]
    output_fields = [
        OutputField("liquidus_temperature_k", "液相线温度", "number", "K"),
        OutputField("liquidus_temperature_degc", "液相线温度", "number", "degC"),
        OutputField("solidus_temperature_k", "同次计算固相线", "number", "K"),
        OutputField("mushy_zone_width_k", "凝固区间宽度", "number", "K"),
        OutputField("grid_uncertainty_k", "网格数值不确定度", "number", "K"),
        OutputField("composition_wt_percent", "计算成分", "object", "wt%"),
        OutputField("endpoint_phase_fractions", "液相端点相分数", "object", "fraction"),
        OutputField("model_asset_id", "模型资产编号", "string"),
    ]
    qualification_cases = [
        {"id":"F001-N1","kind":"normal","input":{"composition_wt_percent":{"C":0.1},"grid_step_k":10}},
        {"id":"F001-N2","kind":"normal","input":{"composition_wt_percent":{"C":0.2,"Mn":1.0,"Si":0.2},"grid_step_k":10}},
        {"id":"F001-N3","kind":"normal","input":{"composition_wt_percent":{"C":0.05,"Cr":1.0,"Ni":1.0},"grid_step_k":10}},
        {"id":"F001-B1","kind":"boundary","input":{"composition_wt_percent":{"Cr":23.0},"grid_step_k":10}},
        {"id":"F001-F1","kind":"failure","input":{"composition_wt_percent":{"P":0.001}}},
    ]
    data_qualification_cases = [{"id":"F001-D1","input":{"composition_wt_percent":{"C":0.1},"grid_step_k":10}}]

    def _success(self, composition, endpoints, step, warnings_out):
        liquidus, solidus = endpoints["liquidus_k"], endpoints["solidus_k"]
        return ModelResult(True, result={"liquidus_temperature_k":liquidus,"liquidus_temperature_degc":liquidus-273.15,"solidus_temperature_k":solidus,"mushy_zone_width_k":liquidus-solidus,"grid_uncertainty_k":step,"composition_wt_percent":composition,"endpoint_phase_fractions":endpoints["liquidus_phases"],"model_asset_id":MODEL_ASSET_ID}, boundary_check=BoundaryCheck(not warnings_out,warnings_out), provenance=endpoints["provenance"])


class F002_SolidusTemperature(_CalphadEndpointTool):
    model_id, name, version = "F002", "钢液固相线温度", "1.0.0"
    tool_name = "metallurgy_calc_steel_solidus_temperature"
    description = "用批准的CALPHAD钢数据库计算给定铁基钢成分的平衡固相线温度。"
    relations = [
        {"type": "overlaps_with", "target": "F004", "description": "F004平衡曲线包含同一固相端点，F002返回面向选型的单值端点"},
        {"type": "paired_with", "target": "F001", "description": "相同模型和输入下分别给出凝固区间下、上端点"},
    ]
    output_fields = [
        OutputField("solidus_temperature_k", "固相线温度", "number", "K"),
        OutputField("solidus_temperature_degc", "固相线温度", "number", "degC"),
        OutputField("liquidus_temperature_k", "同次计算液相线", "number", "K"),
        OutputField("mushy_zone_width_k", "凝固区间宽度", "number", "K"),
        OutputField("grid_uncertainty_k", "网格数值不确定度", "number", "K"),
        OutputField("composition_wt_percent", "计算成分", "object", "wt%"),
        OutputField("endpoint_phase_fractions", "固相端点相分数", "object", "fraction"),
        OutputField("model_asset_id", "模型资产编号", "string"),
    ]
    qualification_cases = [
        {"id":"F002-N1","kind":"normal","input":{"composition_wt_percent":{"C":0.1},"grid_step_k":10}},
        {"id":"F002-N2","kind":"normal","input":{"composition_wt_percent":{"C":0.2,"Mn":1.0,"Si":0.2},"grid_step_k":10}},
        {"id":"F002-N3","kind":"normal","input":{"composition_wt_percent":{"C":0.05,"Cr":1.0,"Ni":1.0},"grid_step_k":10}},
        {"id":"F002-B1","kind":"boundary","input":{"composition_wt_percent":{"Cr":23.0},"grid_step_k":10}},
        {"id":"F002-F1","kind":"failure","input":{"composition_wt_percent":{"S":0.01}}},
    ]
    data_qualification_cases = [{"id":"F002-D1","input":{"composition_wt_percent":{"C":0.1},"grid_step_k":10}}]

    def _success(self, composition, endpoints, step, warnings_out):
        liquidus, solidus = endpoints["liquidus_k"], endpoints["solidus_k"]
        return ModelResult(True, result={"solidus_temperature_k":solidus,"solidus_temperature_degc":solidus-273.15,"liquidus_temperature_k":liquidus,"mushy_zone_width_k":liquidus-solidus,"grid_uncertainty_k":step,"composition_wt_percent":composition,"endpoint_phase_fractions":endpoints["solidus_phases"],"model_asset_id":MODEL_ASSET_ID}, boundary_check=BoundaryCheck(not warnings_out,warnings_out), provenance=endpoints["provenance"])


class F004_SolidFractionCurve(BaseModelTool):
    model_id, name, version = "F004", "钢液凝固分数曲线", "1.0.0"
    tool_name = "metallurgy_calc_solid_fraction_curve"
    scenario = "凝固与连铸"; priority = "P0"; status = qualification_status = "qualified"; count_eligible = True
    model_type = "CALPHAD平衡/Scheil-Gulliver凝固"
    description = "用同一批准钢数据库计算平衡或Scheil-Gulliver凝固分数温度曲线。"
    applicable_boundary = "铁基钢、1 atm、673–2000 K；平衡模式允许完全扩散，Scheil模式假定液相完全混合且固相无回扩散。"
    temperature_range = [673.0,2000.0]
    data_requirement = "VERSIONED_DATABASE_AND_MODEL_ASSET"; data_access_mode = "database_repository"
    required_dataset_ids = ["DS_MATCALC_MC_FE_2059"]; database_tables = ["metallurgy_v2.solidification_model_definition"]
    data_source = ["MatCalc mc_fe v2.059 TDB","pycalphad 0.11.2","scheil 0.3.0"]
    source_version = "mc_fe_v2.059@0a8dd091; pycalphad-0.11.2; scheil-0.3.0"
    formula_reference = "Equilibrium Gibbs minimization or Scheil-Gulliver incremental solidification; fs=1-fl"
    source_records = [{"source_id":"DS_MATCALC_MC_FE_2059","name":"MatCalc mc_fe steel database","version":"2.059","url":"https://github.com/pyroll-project/pyroll-examples/blob/0a8dd09136e3c9c1e73afee054bb55a8f6cd84b0/mc_fe_v2.059.pycalphad.tdb"}]
    failure_modes = ["不支持或超域组分","温度方向或步长非法","模型资产未批准或哈希失配","Scheil未达到0.5%残余液相收敛条件","CALPHAD数值求解失败"]
    independent_validation = ["每一点液相与固相分数闭合为1","平衡液相分数随温度非递减","平衡端点与F001/F002一致","Scheil结果必须显式converged"]
    relations = [
        {"type":"contains_outputs_of","target":"F001","description":"平衡曲线的全液端点与F001液相线重叠"},
        {"type":"contains_outputs_of","target":"F002","description":"平衡曲线的初液端点与F002固相线重叠"},
    ]
    input_fields = [
        InputField("composition_wt_percent","钢中溶质质量百分数","object",unit="wt%",description="Fe为余量；键限C/Si/Mn/Cr/Ni/Mo/Cu/Al"),
        InputField("model","凝固模型","select",required=False,default="equilibrium",enum=["equilibrium","scheil"]),
        InputField("start_temperature_k","起始高温","number",required=False,default=1900.0,unit="K",min_value=674,max_value=2000),
        InputField("end_temperature_k","终止低温","number",required=False,default=1400.0,unit="K",min_value=673,max_value=1999),
        InputField("step_k","降温步长","number",required=False,default=5.0,unit="K",min_value=1,max_value=20),
    ]
    output_fields = [
        OutputField("model","凝固模型","string"), OutputField("curve","凝固曲线","array","temperature:K; fractions:1"),
        OutputField("liquidus_temperature_k","曲线液相线", "number","K"), OutputField("solidus_temperature_k","曲线固相线", "number","K"),
        OutputField("converged","数值收敛", "boolean"), OutputField("composition_wt_percent","计算成分","object","wt%"),
        OutputField("model_asset_id","模型资产编号","string"), OutputField("residual_liquid_stop_fraction","Scheil残余液相停止阈值","number","fraction"),
    ]
    validation_rules = [{"rule":"strictly_descending_temperature_path"},{"rule":"phase_fraction_closure"}]
    qualification_cases = [
        {"id":"F004-N1","kind":"normal","input":{"composition_wt_percent":{"C":0.1},"model":"equilibrium","step_k":5}},
        {"id":"F004-N2","kind":"normal","input":{"composition_wt_percent":{"C":0.1},"model":"scheil","step_k":5}},
        {"id":"F004-N3","kind":"normal","input":{"composition_wt_percent":{"C":0.15,"Mn":1.0,"Si":0.2},"model":"equilibrium","step_k":10}},
        {"id":"F004-B1","kind":"boundary","input":{"composition_wt_percent":{"Cr":23.0},"model":"equilibrium","step_k":10}},
        {"id":"F004-F1","kind":"failure","input":{"composition_wt_percent":{"C":0.1},"start_temperature_k":1500,"end_temperature_k":1900}},
    ]
    data_qualification_cases = [{"id":"F004-D1","input":{"composition_wt_percent":{"C":0.1},"model":"equilibrium","step_k":10}}]

    def invoke(self, params, context=None):
        composition,error = _normalise_composition(params["composition_wt_percent"])
        if error: return ModelResult(False,error=error,error_code="INVALID_INPUT")
        model=params.get("model","equilibrium"); start=float(params.get("start_temperature_k",1900)); end=float(params.get("end_temperature_k",1400)); step=float(params.get("step_k",5))
        if start <= end or start-end < 2*step:
            return ModelResult(False,error="起始温度必须高于终止温度且至少跨越两个步长",error_code="TEMPERATURE_RANGE_ERROR")
        try:
            db,row,provenance=load_database(MODEL_ASSET_ID)
            domain_error=_validate_against_definition(composition,row)
            if domain_error: return ModelResult(False,error=domain_error,error_code="OUT_OF_DOMAIN")
            if model == "equilibrium":
                temps,liquid,phase_rows,_,statuses=_equilibrium_curve(tuple(sorted(composition.items())),end,start,step)
                items=list(zip(reversed(temps),reversed(liquid),reversed(phase_rows),reversed(statuses)))
                converged=True; stop_fraction=0.0
            else:
                components=["FE",*composition,"VA"]; phases=[p for p in row["phase_set"] if p in db.phases]
                conditions={v.W(s):x/100 for s,x in composition.items()}
                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore",message="The type definition character.*",category=UserWarning)
                    simulation=simulate_scheil_solidification(db,components,phases,conditions,start,step,stop=0.005)
                if not simulation.converged:
                    return ModelResult(False,error="Scheil求解未达到0.5%残余液相停止条件",error_code="NUMERICAL_ERROR")
                items=[]
                for i,(temp,fl) in enumerate(zip(simulation.temperatures,simulation.fraction_liquid)):
                    phase_amounts={p:float(values[i]) for p,values in simulation.cum_phase_amounts.items() if i < len(values) and float(values[i])>1e-12}
                    solid_total=sum(phase_amounts.values())
                    if solid_total > 0:
                        phase_amounts={p:value*(1-float(fl))/solid_total for p,value in phase_amounts.items()}
                    if fl>1e-12: phase_amounts["LIQUID"]=float(fl)
                    items.append((float(temp),float(fl),phase_amounts,"direct"))
                converged=True; stop_fraction=0.005
            curve=[]
            for temp,fl,phase_amounts,solution_status in items:
                fl=min(1.0,max(0.0,float(fl)))
                curve.append({"temperature_k":float(temp),"fraction_liquid":fl,"fraction_solid":1-fl,"phase_fractions":phase_amounts,"solution_status":solution_status})
            mushy=[point for point in curve if point["fraction_liquid"]>LIQUID_THRESHOLD]
            all_liquid=[point for point in curve if point["fraction_liquid"]>=1-LIQUID_THRESHOLD]
            if not mushy or not all_liquid: raise ValueError("给定温区未覆盖完整凝固区间")
            liquidus=min(point["temperature_k"] for point in all_liquid)
            solidus=min(point["temperature_k"] for point in mushy)
        except RepositoryError as exc:
            return ModelResult(False,error=str(exc),error_code=exc.error_code)
        except Exception as exc:
            return ModelResult(False,error=str(exc),error_code="NUMERICAL_ERROR")
        warnings_out=[]; maxima=row["domain_json"]["component_max_wt_percent"]
        if any(x>=0.9*float(maxima[s]) for s,x in composition.items()): warnings_out.append(BoundaryWarning("composition_wt_percent","组分接近批准数据库评估域上限"))
        interpolated_count=sum(point["solution_status"] != "direct" for point in curve)
        if interpolated_count:
            warnings_out.append(BoundaryWarning("curve",f"{interpolated_count}个孤立温点在单点重算仍失败后使用相邻收敛点线性插值"))
        return ModelResult(True,result={"model":model,"curve":curve,"liquidus_temperature_k":liquidus,"solidus_temperature_k":solidus,"converged":converged,"composition_wt_percent":composition,"model_asset_id":MODEL_ASSET_ID,"residual_liquid_stop_fraction":stop_fraction},boundary_check=BoundaryCheck(not warnings_out,warnings_out),provenance=provenance)


class F003_SteelSuperheat(BaseModelTool):
    model_id, name, version = "F003", "钢液过热度", "1.0.0"
    tool_name = "metallurgy_calc_steel_superheat"
    scenario = "凝固与连铸"
    priority = "P0"
    status = "qualified"
    qualification_status = "qualified"
    count_eligible = True
    data_requirement = "FORMULA_ONLY"
    data_access_mode = "none"
    description = (
        "根据显式钢液温度和液相线温度计算过热度；温度可用K或degC。"
        "本工具不预测液相线；liquidus_source=F001时必须提供upstream_execution_id。"
    )
    applicable_boundary = (
        "适用于已知钢液温度与单值液相线温度的静态过热度计算；"
        "不接受液相线区间，不推断钢种液相线，不替代连铸控制或凝固模型。"
    )
    temperature_range = [0.0, 4000.0]
    data_source = ["Definition of liquid-steel superheat", "SI temperature-difference convention"]
    source_version = "steel-superheat-definition-v1; SI Brochure 9th edition"
    formula_reference = "DeltaT_superheat = T_steel - T_liquidus; Delta(degC) = Delta(K)"
    source_records = [
        {
            "source_id": "SUPERHEAT-DEFINITION",
            "name": "Liquid-steel superheat temperature difference",
            "version": "v1",
        },
        {
            "source_id": "BIPM-SI-BROCHURE",
            "name": "The International System of Units (SI Brochure)",
            "version": "9th edition v3.01",
            "url": "https://www.bipm.org/en/publications/si-brochure",
        },
    ]
    failure_modes = [
        "温度单位不受支持或绝对温标非法",
        "液相线不是单值",
        "要求限值判断但没有同时给上下限",
        "过热度下限高于上限",
        "声明液相线来自F001但缺少上游执行编号",
    ]
    independent_validation = [
        "过热度等于钢液温度减液相线温度",
        "同一输入走K与degC路径结果一致",
        "两个绝对温度同时平移时过热度不变",
        "钢液温度低于液相线时返回负过热度和物理边界警告",
    ]
    dependencies = []
    relations = [
        {
            "type": "uses_convention_of",
            "target": "A001",
            "description": "复用A001验证过的K/摄氏温标换算约定，但本工具计算的是温差与工艺限值状态",
        }
    ]
    related_catalog_ids = ["F001"]
    input_fields = [
        InputField("steel_temperature", "钢液温度", "number", unit="$temperature_unit"),
        InputField("liquidus_temperature", "液相线温度", "number", unit="$temperature_unit"),
        InputField("temperature_unit", "温度单位", "select", enum=["K", "degC"]),
        InputField(
            "liquidus_source",
            "液相线来源",
            "string",
            description="非空来源说明；若填F001，必须同时给upstream_execution_id",
        ),
        InputField("evaluate_limits", "是否按过热度限值判断", "boolean", required=False, default=False),
        InputField("minimum_superheat_k", "过热度下限", "number", required=False, unit="K", min_value=0),
        InputField("maximum_superheat_k", "过热度上限", "number", required=False, unit="K", min_value=0),
        InputField(
            "upstream_execution_id",
            "F001上游执行编号",
            "string",
            required=False,
            description="只有液相线确由F001执行结果提供时填写",
        ),
    ]
    output_fields = [
        OutputField("steel_temperature_k", "钢液温度", "number", "K"),
        OutputField("liquidus_temperature_k", "液相线温度", "number", "K"),
        OutputField("steel_temperature_degc", "钢液温度", "number", "degC"),
        OutputField("liquidus_temperature_degc", "液相线温度", "number", "degC"),
        OutputField("superheat_k", "钢液过热度", "number", "K"),
        OutputField("superheat_degc", "钢液过热度", "number", "degC"),
        OutputField("limits_applied", "是否执行限值判断", "boolean"),
        OutputField("limit_status", "限值状态", "string"),
        OutputField("liquidus_source", "液相线来源", "string"),
        OutputField("upstream_execution_id", "F001上游执行编号", "string"),
    ]
    validation_rules = [
        {"rule": "absolute_temperature_above_zero", "fields": ["steel_temperature", "liquidus_temperature"]},
        {"rule": "limit_pair_required_when_evaluated", "fields": ["minimum_superheat_k", "maximum_superheat_k"]},
        {"rule": "f001_source_requires_execution_id", "fields": ["liquidus_source", "upstream_execution_id"]},
    ]
    qualification_cases = [
        {
            "id": "F003-N1",
            "kind": "normal",
            "input": {
                "steel_temperature": 1873.15,
                "liquidus_temperature": 1823.15,
                "temperature_unit": "K",
                "liquidus_source": "laboratory_measurement",
            },
        },
        {
            "id": "F003-N2",
            "kind": "normal",
            "input": {
                "steel_temperature": 1600,
                "liquidus_temperature": 1530,
                "temperature_unit": "degC",
                "liquidus_source": "approved_external_model:v2",
                "evaluate_limits": True,
                "minimum_superheat_k": 20,
                "maximum_superheat_k": 80,
            },
        },
        {
            "id": "F003-N3",
            "kind": "normal",
            "input": {
                "steel_temperature": 1840,
                "liquidus_temperature": 1810,
                "temperature_unit": "K",
                "liquidus_source": "F001",
                "upstream_execution_id": "EXEC-F001-REFERENCE",
            },
        },
        {
            "id": "F003-B1",
            "kind": "boundary",
            "input": {
                "steel_temperature": 1500,
                "liquidus_temperature": 1510,
                "temperature_unit": "degC",
                "liquidus_source": "thermocouple_and_reference_liquidus",
            },
        },
        {
            "id": "F003-F1",
            "kind": "failure",
            "input": {
                "steel_temperature": -1,
                "liquidus_temperature": 100,
                "temperature_unit": "K",
                "liquidus_source": "invalid_test",
            },
        },
    ]

    @staticmethod
    def _to_kelvin(value: float, unit: str) -> float:
        return value if unit == "K" else value + 273.15

    def invoke(self, params, context=None):
        unit = params["temperature_unit"]
        steel_k = self._to_kelvin(float(params["steel_temperature"]), unit)
        liquidus_k = self._to_kelvin(float(params["liquidus_temperature"]), unit)
        if steel_k < 0 or liquidus_k < 0:
            return ModelResult(False, error="钢液温度和液相线温度不能低于绝对零度", error_code="OUT_OF_DOMAIN")

        source = params["liquidus_source"].strip()
        if not source:
            return ModelResult(False, error="liquidus_source必须是非空来源说明", error_code="INVALID_INPUT")
        upstream_id = str(params.get("upstream_execution_id", "")).strip()
        if source.upper() == "F001" and not upstream_id:
            return ModelResult(False, error="liquidus_source=F001时必须提供upstream_execution_id", error_code="MISSING_DATA")

        evaluate = bool(params.get("evaluate_limits", False))
        minimum = params.get("minimum_superheat_k")
        maximum = params.get("maximum_superheat_k")
        if evaluate and (minimum is None or maximum is None):
            return ModelResult(False, error="evaluate_limits=true时必须同时提供minimum_superheat_k和maximum_superheat_k", error_code="MISSING_DATA")
        if not evaluate and (minimum is not None or maximum is not None):
            return ModelResult(False, error="提供过热度限值时必须设置evaluate_limits=true", error_code="INVALID_INPUT")
        if evaluate:
            minimum, maximum = float(minimum), float(maximum)
            if minimum > maximum:
                return ModelResult(False, error="minimum_superheat_k不能大于maximum_superheat_k", error_code="INVALID_INPUT")

        superheat = steel_k - liquidus_k
        status = "not_evaluated"
        warnings = []
        if superheat < 0:
            warnings.append(BoundaryWarning("steel_temperature", "钢液温度低于液相线，结果为负过热度"))
        if evaluate:
            if superheat < minimum:
                status = "below_range"
                warnings.append(BoundaryWarning("superheat_k", "过热度低于显式工艺下限", min_allowed=minimum, max_allowed=maximum))
            elif superheat > maximum:
                status = "above_range"
                warnings.append(BoundaryWarning("superheat_k", "过热度高于显式工艺上限", min_allowed=minimum, max_allowed=maximum))
            else:
                status = "within_range"

        return ModelResult(
            True,
            result={
                "steel_temperature_k": steel_k,
                "liquidus_temperature_k": liquidus_k,
                "steel_temperature_degc": steel_k - 273.15,
                "liquidus_temperature_degc": liquidus_k - 273.15,
                "superheat_k": superheat,
                "superheat_degc": superheat,
                "limits_applied": evaluate,
                "limit_status": status,
                "liquidus_source": source,
                "upstream_execution_id": upstream_id,
            },
            boundary_check=BoundaryCheck(not warnings, warnings),
        )


class F007_MoldHeatFlux(BaseModelTool):
    """Average continuous-casting mold heat flux from water-side heat balance."""

    WATER_CRITICAL_TEMPERATURE_K = 647.096
    model_id, name, version = "F007", "结晶器热流计算", "1.0.0"
    tool_name = "metallurgy_calc_mold_heat_flux"
    scenario = "凝固与连铸"
    priority = "P1"
    status = qualification_status = "qualified"
    count_eligible = True
    model_type = "确定性公式/冷却水侧能量守恒"
    data_requirement = "FORMULA_ONLY"
    data_access_mode = "none"
    description = (
        "根据一个或多个结晶器冷却水回路的显式质量流量、比热和进出口温度，"
        "计算总移热率与给定有效面积上的平均热流密度；不内置水物性、设备面积或经验常数。"
    )
    applicable_boundary = (
        "适用于冷却水无相变、质量流量与温度可视为同一稳态时间窗平均值的结晶器整体或分区热平衡；"
        "结果是水侧平均热流，不代表铜板局部峰值、弯月面瞬态热流或热电偶反演结果。"
    )
    temperature_range = [0.0, 647.096]
    required_data = [
        "各冷却回路质量流量、进出口绝对温度、比热和测量来源",
        "与所选回路口径一致的有效换热面积",
    ]
    data_source = [
        "调用者提供的结晶器冷却水测量值与比热",
        "ISIJ International 63(8), 2023, Eq. (15)",
    ]
    source_version = (
        "water-side-energy-balance-v1; ISIJINT-2023-051 Eq.15; "
        "IAPWS R2-83(1992)"
    )
    formula_reference = (
        "For circuit i: Qdot_i = mdot_i * cp_i * (T_out_i - T_in_i); "
        "Qdot_total = sum(Qdot_i); q_mean = Qdot_total / A_effective"
    )
    source_records = [
        {
            "source_id": "ISIJINT-2023-051",
            "name": "A Three Dimensional Real-time Heat Transfer Model for Continuous Casting Blooms",
            "version": "ISIJ International 63(8), 2023, Eq. (15)",
            "url": "https://www.jstage.jst.go.jp/article/isijinternational/63/8/63_ISIJINT-2023-051/_html/-char/en",
        },
        {
            "source_id": "IAPWS-R2-83-1992",
            "name": "Revised Release on the Values of Temperature, Pressure and Density at Critical Points",
            "version": "R2-83(1992)",
            "url": "https://iapws.org/documents/release/crits",
        },
    ]
    failure_modes = [
        "冷却回路为空、字段缺失、回路编号重复或含未声明字段",
        "质量流量、比热、绝对温度或有效面积不是有限正数，或水温达到/超过临界温度",
        "出口温度低于入口温度且未定义反向换热模式",
        "测量来源或面积口径为空",
        "单位钢质量移热请求中的钢质量流量不是有限正数",
    ]
    independent_validation = [
        "单回路结果与手工能量衡算一致",
        "总移热率等于各回路移热率之和",
        "结果分别对质量流量、比热和温升呈线性",
        "平均热流密度等于总移热率除以显式有效面积",
        "给定钢质量流量时单位钢质量移热等于总移热率除以钢质量流量",
    ]
    dependencies = []
    relations = [
        {
            "type": "overlaps_with",
            "target": "T001",
            "description": "两者都可返回热流率/热流密度，但T001由平板温差与导热系数求稳态导热，F007由冷却水侧量热求结晶器平均移热。",
        },
        {
            "type": "complements",
            "target": "T002",
            "description": "T002计算指定表面间的灰体辐射子项，F007核算结晶器冷却水吸收的总体平均热量，理论对象与适用域不同。",
        },
    ]
    input_fields = [
        InputField(
            "cooling_circuits",
            "结晶器冷却水回路",
            "array",
            description=(
                "1至100个同一稳态时间窗的回路；每项必须显式给出回路编号、质量流量、"
                "入口/出口温度、该回路采用的水比热和测量来源。"
            ),
            min_items=1,
            max_items=100,
            items={
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "circuit_id": {
                        "type": "string",
                        "minLength": 1,
                        "description": "本次调用内唯一的冷却回路编号",
                    },
                    "mass_flow_kg_s": {
                        "type": "number",
                        "exclusiveMinimum": 0,
                        "description": "冷却水质量流量；单位: kg/s",
                    },
                    "inlet_temperature_k": {
                        "type": "number",
                        "exclusiveMinimum": 0,
                        "exclusiveMaximum": 647.096,
                        "description": "回路入口绝对温度；单位: K",
                    },
                    "outlet_temperature_k": {
                        "type": "number",
                        "exclusiveMinimum": 0,
                        "exclusiveMaximum": 647.096,
                        "description": "回路出口绝对温度；单位: K",
                    },
                    "water_specific_heat_j_kg_k": {
                        "type": "number",
                        "exclusiveMinimum": 0,
                        "description": "本次测量温区采用的水比热；单位: J/(kg*K)",
                    },
                    "measurement_source": {
                        "type": "string",
                        "minLength": 1,
                        "description": "流量、温度及比热的测量或批准来源",
                    },
                },
                "required": [
                    "circuit_id",
                    "mass_flow_kg_s",
                    "inlet_temperature_k",
                    "outlet_temperature_k",
                    "water_specific_heat_j_kg_k",
                    "measurement_source",
                ],
            },
        ),
        InputField(
            "effective_heat_transfer_area_m2",
            "有效换热面积",
            "number",
            unit="m^2",
            min_value=0,
            description="与所选冷却回路及面积口径一致的有效换热面积；必须显式提供且大于0",
        ),
        InputField(
            "area_definition",
            "面积口径",
            "string",
            description="例如broad_face、narrow_face、whole_mold或明确的调用者自定义口径",
        ),
        InputField(
            "steel_mass_flow_kg_s",
            "钢质量流量",
            "number",
            required=False,
            unit="kg/s",
            min_value=0,
            description="可选；提供时计算单位钢质量移热，必须大于0",
        ),
    ]
    output_fields = [
        OutputField(
            "circuit_results",
            "各冷却回路热平衡结果",
            "array",
            "mass_flow:kg/s; temperature:K; cp:J/(kg*K); heat_rate:W; contribution:fraction",
        ),
        OutputField("total_heat_rate_w", "总移热率", "number", "W"),
        OutputField("mean_heat_flux_w_m2", "平均热流密度", "number", "W/m^2"),
        OutputField("effective_heat_transfer_area_m2", "有效换热面积", "number", "m^2"),
        OutputField("area_definition", "面积口径", "string"),
        OutputField(
            "steel_mass_flow_kg_s",
            "钢质量流量",
            "number",
            "kg/s",
            description="调用者未提供时为null",
            nullable=True,
        ),
        OutputField(
            "heat_removed_j_kg_steel",
            "单位钢质量移热",
            "number",
            "J/kg",
            description="调用者未提供钢质量流量时为null",
            nullable=True,
        ),
        OutputField("energy_sum_residual_w", "回路求和残差", "number", "W"),
        OutputField("measurement_sources", "测量来源清单", "array"),
        OutputField("calculation_method", "计算方法", "string"),
    ]
    validation_rules = [
        {"rule": "one_to_one_hundred_unique_circuit_ids"},
        {"rule": "positive_finite_flow_cp_temperature_and_area"},
        {"rule": "outlet_temperature_not_below_inlet"},
        {"rule": "all_equipment_properties_and_measurement_sources_are_explicit"},
    ]
    qualification_cases = [
        {
            "id": "F007-N1",
            "kind": "normal",
            "input": {
                "cooling_circuits": [
                    {
                        "circuit_id": "whole-mold",
                        "mass_flow_kg_s": 10,
                        "inlet_temperature_k": 293.15,
                        "outlet_temperature_k": 298.15,
                        "water_specific_heat_j_kg_k": 4200,
                        "measurement_source": "calibrated_flowmeter_and_paired_rtd",
                    }
                ],
                "effective_heat_transfer_area_m2": 2,
                "area_definition": "whole_mold",
                "steel_mass_flow_kg_s": 2,
            },
        },
        {
            "id": "F007-N2",
            "kind": "normal",
            "input": {
                "cooling_circuits": [
                    {
                        "circuit_id": "wide-face",
                        "mass_flow_kg_s": 10,
                        "inlet_temperature_k": 293.15,
                        "outlet_temperature_k": 298.15,
                        "water_specific_heat_j_kg_k": 4200,
                        "measurement_source": "wide_face_instrumentation",
                    },
                    {
                        "circuit_id": "narrow-face",
                        "mass_flow_kg_s": 5,
                        "inlet_temperature_k": 294.15,
                        "outlet_temperature_k": 298.15,
                        "water_specific_heat_j_kg_k": 4200,
                        "measurement_source": "narrow_face_instrumentation",
                    },
                ],
                "effective_heat_transfer_area_m2": 3,
                "area_definition": "whole_mold",
            },
        },
        {
            "id": "F007-N3",
            "kind": "normal",
            "input": {
                "cooling_circuits": [
                    {
                        "circuit_id": "broad-face-a",
                        "mass_flow_kg_s": 12.5,
                        "inlet_temperature_k": 296.15,
                        "outlet_temperature_k": 302.15,
                        "water_specific_heat_j_kg_k": 4180,
                        "measurement_source": "approved_test_loop_2026Q3",
                    }
                ],
                "effective_heat_transfer_area_m2": 1.5,
                "area_definition": "broad_face",
            },
        },
        {
            "id": "F007-B1",
            "kind": "boundary",
            "input": {
                "cooling_circuits": [
                    {
                        "circuit_id": "zero-rise-check",
                        "mass_flow_kg_s": 10,
                        "inlet_temperature_k": 298.15,
                        "outlet_temperature_k": 298.15,
                        "water_specific_heat_j_kg_k": 4200,
                        "measurement_source": "sensor_zero_check",
                    }
                ],
                "effective_heat_transfer_area_m2": 2,
                "area_definition": "whole_mold",
            },
        },
        {
            "id": "F007-F1",
            "kind": "failure",
            "input": {
                "cooling_circuits": [
                    {
                        "circuit_id": "reverse-temperature",
                        "mass_flow_kg_s": 10,
                        "inlet_temperature_k": 300.15,
                        "outlet_temperature_k": 299.15,
                        "water_specific_heat_j_kg_k": 4200,
                        "measurement_source": "failure_case",
                    }
                ],
                "effective_heat_transfer_area_m2": 2,
                "area_definition": "whole_mold",
            },
        },
        {
            "id": "F007-F2",
            "kind": "failure",
            "input": {
                "cooling_circuits": [
                    {
                        "circuit_id": "invalid-area",
                        "mass_flow_kg_s": 10,
                        "inlet_temperature_k": 293.15,
                        "outlet_temperature_k": 298.15,
                        "water_specific_heat_j_kg_k": 4200,
                        "measurement_source": "failure_case",
                    }
                ],
                "effective_heat_transfer_area_m2": 0,
                "area_definition": "whole_mold",
            },
        },
    ]

    _CIRCUIT_FIELDS = {
        "circuit_id",
        "mass_flow_kg_s",
        "inlet_temperature_k",
        "outlet_temperature_k",
        "water_specific_heat_j_kg_k",
        "measurement_source",
    }

    @staticmethod
    def _finite_number(value, field_name):
        if isinstance(value, bool):
            return None, f"{field_name}必须是有限数值"
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None, f"{field_name}必须是有限数值"
        if not math.isfinite(number):
            return None, f"{field_name}必须是有限数值"
        return number, None

    def invoke(self, params, context=None):
        circuits = params["cooling_circuits"]
        if len(circuits) > 100:
            return ModelResult(False, error="cooling_circuits最多允许100个回路", error_code="OUT_OF_DOMAIN")

        area, error = self._finite_number(
            params["effective_heat_transfer_area_m2"],
            "effective_heat_transfer_area_m2",
        )
        if error or area <= 0:
            return ModelResult(
                False,
                error=error or "effective_heat_transfer_area_m2必须大于0",
                error_code="OUT_OF_DOMAIN",
            )
        area_definition = params["area_definition"].strip()
        if not area_definition:
            return ModelResult(False, error="area_definition必须是非空面积口径", error_code="INVALID_INPUT")

        steel_mass_flow = params.get("steel_mass_flow_kg_s")
        if steel_mass_flow is not None:
            steel_mass_flow, error = self._finite_number(steel_mass_flow, "steel_mass_flow_kg_s")
            if error or steel_mass_flow <= 0:
                return ModelResult(
                    False,
                    error=error or "steel_mass_flow_kg_s必须大于0",
                    error_code="OUT_OF_DOMAIN",
                )

        circuit_rows = []
        circuit_ids = set()
        warnings_out = []
        for index, raw in enumerate(circuits):
            prefix = f"cooling_circuits[{index}]"
            if not isinstance(raw, dict):
                return ModelResult(False, error=f"{prefix}必须是对象", error_code="INVALID_INPUT")
            missing = sorted(self._CIRCUIT_FIELDS - set(raw))
            unknown = sorted(set(raw) - self._CIRCUIT_FIELDS)
            if missing or unknown:
                details = []
                if missing:
                    details.append(f"缺少字段: {', '.join(missing)}")
                if unknown:
                    details.append(f"含未声明字段: {', '.join(unknown)}")
                return ModelResult(False, error=f"{prefix} " + "; ".join(details), error_code="INVALID_INPUT")

            circuit_id = raw["circuit_id"]
            if not isinstance(circuit_id, str) or not circuit_id.strip():
                return ModelResult(False, error=f"{prefix}.circuit_id必须是非空字符串", error_code="INVALID_INPUT")
            circuit_id = circuit_id.strip()
            if circuit_id in circuit_ids:
                return ModelResult(False, error=f"回路编号重复: {circuit_id}", error_code="INVALID_INPUT")
            circuit_ids.add(circuit_id)

            measurement_source = raw["measurement_source"]
            if not isinstance(measurement_source, str) or not measurement_source.strip():
                return ModelResult(False, error=f"{prefix}.measurement_source必须是非空字符串", error_code="INVALID_INPUT")
            measurement_source = measurement_source.strip()

            values = {}
            for field_name in (
                "mass_flow_kg_s",
                "inlet_temperature_k",
                "outlet_temperature_k",
                "water_specific_heat_j_kg_k",
            ):
                value, error = self._finite_number(raw[field_name], f"{prefix}.{field_name}")
                if error or value <= 0:
                    return ModelResult(
                        False,
                        error=error or f"{prefix}.{field_name}必须大于0",
                        error_code="OUT_OF_DOMAIN",
                    )
                values[field_name] = value

            if values["inlet_temperature_k"] >= self.WATER_CRITICAL_TEMPERATURE_K \
                    or values["outlet_temperature_k"] >= self.WATER_CRITICAL_TEMPERATURE_K:
                return ModelResult(
                    False,
                    error=(
                        f"{prefix}水温必须低于IAPWS临界温度"
                        f"{self.WATER_CRITICAL_TEMPERATURE_K} K；首版只适用无相变冷却水"
                    ),
                    error_code="OUT_OF_DOMAIN",
                )

            temperature_rise = values["outlet_temperature_k"] - values["inlet_temperature_k"]
            if temperature_rise < 0:
                return ModelResult(
                    False,
                    error=f"{prefix}出口温度低于入口温度；首版不支持反向换热模式",
                    error_code="OUT_OF_DOMAIN",
                )
            if temperature_rise == 0:
                warnings_out.append(
                    BoundaryWarning(
                        f"{prefix}.outlet_temperature_k",
                        "出口与入口温度相同，计算得到零移热；请核对传感器分辨率和时间窗同步",
                    )
                )
            heat_rate = (
                values["mass_flow_kg_s"]
                * values["water_specific_heat_j_kg_k"]
                * temperature_rise
            )
            circuit_rows.append(
                {
                    "circuit_id": circuit_id,
                    **values,
                    "temperature_rise_k": temperature_rise,
                    "heat_rate_w": heat_rate,
                    "contribution_fraction": 0.0,
                    "measurement_source": measurement_source,
                }
            )

        total_heat_rate = math.fsum(row["heat_rate_w"] for row in circuit_rows)
        if total_heat_rate > 0:
            for row in circuit_rows:
                row["contribution_fraction"] = row["heat_rate_w"] / total_heat_rate
        circuit_sum = math.fsum(row["heat_rate_w"] for row in circuit_rows)
        heat_removed_per_steel_mass = (
            total_heat_rate / steel_mass_flow if steel_mass_flow is not None else None
        )
        return ModelResult(
            True,
            result={
                "circuit_results": circuit_rows,
                "total_heat_rate_w": total_heat_rate,
                "mean_heat_flux_w_m2": total_heat_rate / area,
                "effective_heat_transfer_area_m2": area,
                "area_definition": area_definition,
                "steel_mass_flow_kg_s": steel_mass_flow,
                "heat_removed_j_kg_steel": heat_removed_per_steel_mass,
                "energy_sum_residual_w": total_heat_rate - circuit_sum,
                "measurement_sources": [row["measurement_source"] for row in circuit_rows],
                "calculation_method": "cooling_water_sensible_heat_balance_v1",
            },
            boundary_check=BoundaryCheck(not warnings_out, warnings_out),
        )


class F005_OneDimensionalShellGrowth(BaseModelTool):
    """Implicit finite-volume solution of one-dimensional strand cooling."""

    model_id, name, version = "F005", "一维坯壳厚度", "1.0.0"
    tool_name = "metallurgy_solve_1d_shell_growth"
    scenario = "凝固与连铸"
    priority = "P1"
    status = qualification_status = "qualified"
    count_eligible = True
    model_type = "确定性数值PDE/一维瞬态焓法有限体积"
    data_requirement = "VERSIONED_DATABASE_REFERENCE"
    data_access_mode = "database_repository"
    required_dataset_ids = ["DS_NIST_SRM1155A_316L_2019", "DS_F005_ANALYTIC_BENCH_V1"]
    database_tables = [
        "metallurgy_v2.casting_material_property_set",
        "metallurgy_v2.casting_material_property_correlation",
        "metallurgy_v2.casting_boundary_profile",
    ]
    temperature_range = [300.0, 2900.0]
    description = (
        "用隐式Euler、单元中心有限体积和Picard迭代求解铸坯表面到中心的一维瞬态焓方程，"
        "返回温度场、固相率、坯壳厚度、移热和能量闭合；物性与可选边界只读取批准的PostgreSQL记录。"
    )
    applicable_boundary = (
        "适用于可近似为表面到中心一维传热的平板半厚度域，中心为对称零热流；"
        "首版支持批准的常值表面温度、常值外向热流或数据库常值边界。"
        "NIST SRM 1155a物性仅用于验证，不代表其他钢种、设备、喷嘴或生产控制配置。"
    )
    required_data = [
        "批准物性集中的密度、比焓和导热系数；凝固计算还需固相率相关式",
        "显式半厚度、初温、计算时间、拉速、网格、时间步长和坯壳固相率阈值",
        "数据库批准边界，或带来源说明的显式定热流/定表温边界",
    ]
    data_source = [
        "PostgreSQL metallurgy_v2.casting_material_property_set/correlation",
        "Pichler et al. (2019) NIST SRM 1155a 316L thermophysical properties",
        "项目生成的一维热方程解析基准",
    ]
    source_version = (
        "P1-W5B-CASTING-THERMAL-2026.08-v1; implicit-enthalpy-fvm-v1; "
        "SciPy-1.18.1; NumPy-2.5.1"
    )
    formula_reference = (
        "rho(T)*dH(T)/dt = d/dx[k(T)*dT/dx]; cell-centred finite volume; "
        "backward Euler; Picard linearization H(T_new)~=H(T*)+dH/dT|*(T_new-T*); "
        "surface Dirichlet or outward-positive Neumann boundary; centre symmetry"
    )
    source_records = [
        {
            "source_id": "DS_NIST_SRM1155A_316L_2019",
            "name": "Measurements of thermophysical properties of solid and liquid NIST SRM 316L stainless steel",
            "version": "2019-12-09; DOI 10.1007/s10853-019-04261-6",
            "url": "https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=928362",
        },
        {
            "source_id": "SCIPY-LINALG-1.18.1",
            "name": "scipy.linalg.solve_banded",
            "version": "1.18.1",
            "url": "https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.solve_banded.html",
        },
    ]
    failure_modes = [
        "物性集未批准、必需属性缺失、数据库不可用或求解温度越出相关式温区",
        "边界字段组合冲突、数据库边界与物性集不匹配、显式边界缺来源或F007执行ID",
        "半厚度、拉速、网格、时间步、固相率阈值或非线性配置非法",
        "Picard迭代不收敛、三对角求解失败、温度或物性产生非有限/非正值",
        "工程用途请求使用仅限数学基准或参考验证的物性集",
    ]
    independent_validation = [
        "常物性定表温半无限体结果与erf解析解对照",
        "常物性定热流表面温度与Neumann解析解对照",
        "零热流保持均匀初温且累计移热为零",
        "逐步储能变化与表面累计移热闭合",
        "网格和时间步加密后温度/坯壳结果收敛",
        "固相率始终位于[0,1]且坯壳阈值插值位于[0,半厚度]",
    ]
    dependencies = []
    relations = [
        {
            "type": "accepts_output_from",
            "target": "F007",
            "description": "F007水侧平均热流可作为F005外向定热流边界，调用时必须携带F007执行ID。",
        },
        {
            "type": "overlaps_with",
            "target": "T001",
            "description": "T001给出常物性平板稳态总热流，F005求解温变物性、相变和时间演化的一维场。",
        },
    ]
    input_fields = [
        InputField("property_set_id", "批准物性集ID", "string", description="必须存在于PostgreSQL且is_approved=true"),
        InputField("calculation_purpose", "计算用途", "select", enum=["validation", "engineering"], description="validation允许参考/数学基准；engineering只允许工程或生产批准物性集"),
        InputField("half_thickness_m", "铸坯半厚度", "number", unit="m", min_value=0.001, max_value=1.0),
        InputField("initial_temperature_k", "初始均匀温度", "number", unit="K", min_value=1.0, max_value=5000.0),
        InputField("duration_s", "计算时长", "number", unit="s", min_value=1e-6, max_value=7200.0),
        InputField("casting_speed_m_s", "拉坯速度", "number", unit="m/s", min_value=1e-8, max_value=1.0),
        InputField("grid_cells", "空间单元数", "integer", unit="1", min_value=10, max_value=200, description="表面到中心的均匀有限体积单元数"),
        InputField("time_step_s", "隐式时间步", "number", unit="s", min_value=1e-6, max_value=60.0),
        InputField("shell_solid_fraction_threshold", "坯壳固相率阈值", "number", unit="1", min_value=0.01, max_value=0.99),
        InputField("boundary_mode", "表面边界模式", "select", enum=["database_profile", "constant_heat_flux", "constant_surface_temperature"]),
        InputField("boundary_profile_id", "数据库边界ID", "string", required=False, description="boundary_mode=database_profile时必填"),
        InputField("surface_heat_flux_w_m2", "外向表面热流", "number", required=False, unit="W/m^2", min_value=0.0, description="constant_heat_flux时必填；正值表示铸坯向外移热"),
        InputField("surface_temperature_k", "给定表面温度", "number", required=False, unit="K", min_value=1.0, max_value=5000.0, description="constant_surface_temperature时必填且低于初温"),
        InputField("boundary_source", "边界来源", "string", description="数据库记录、测量或上游工具来源；不得为空"),
        InputField("upstream_execution_id", "上游执行ID", "string", required=False, description="boundary_source=F007时必填"),
        InputField("picard_tolerance_k", "Picard温度收敛容差", "number", required=False, default=1e-6, unit="K", min_value=1e-8, max_value=1e-2),
        InputField("max_picard_iterations", "最大Picard迭代次数", "integer", required=False, default=40, unit="1", min_value=3, max_value=100),
        InputField("output_points", "历史输出点数上限", "integer", required=False, default=11, unit="1", min_value=2, max_value=51),
    ]
    output_fields = [
        OutputField(
            "time_history",
            "温度、中心固相率与坯壳历史",
            "array",
            "time:s; position:m; temperature:K; center_solid_fraction:1; shell:m; energy:J/m^2",
        ),
        OutputField("final_temperature_profile", "最终温度/固相率剖面", "array", "x:m; temperature:K; solid_fraction:1"),
        OutputField("shell_thickness_m", "最终坯壳厚度", "number", "m", nullable=True),
        OutputField("shell_status", "坯壳结果状态", "string"),
        OutputField("final_surface_temperature_k", "最终表面温度", "number", "K"),
        OutputField("final_center_temperature_k", "最终中心温度", "number", "K"),
        OutputField("total_time_s", "总计算时间", "number", "s"),
        OutputField("final_axial_position_m", "对应轴向位置", "number", "m"),
        OutputField("cumulative_removed_heat_j_m2", "累计向外移热", "number", "J/m^2"),
        OutputField("stored_energy_change_j_m2", "离散储能变化", "number", "J/m^2"),
        OutputField("energy_closure_residual_j_m2", "能量闭合残差", "number", "J/m^2"),
        OutputField("energy_closure_relative", "相对能量闭合残差", "number", "1"),
        OutputField("grid_cells", "空间单元数", "number", "1"),
        OutputField("cell_size_m", "单元尺寸", "number", "m"),
        OutputField("time_steps", "实际时间步数", "number", "1"),
        OutputField("nominal_time_step_s", "名义时间步", "number", "s"),
        OutputField("max_picard_iterations_used", "单步最大Picard迭代次数", "number", "1"),
        OutputField("all_steps_converged", "全部时间步收敛", "boolean"),
        OutputField("property_set_id", "物性集ID", "string"),
        OutputField("property_usage_scope", "物性使用域", "string"),
        OutputField("boundary_summary", "边界配置与来源", "object"),
        OutputField("calculation_purpose", "计算用途", "string"),
        OutputField("solver_version", "求解器版本", "string"),
    ]
    validation_rules = [
        {"rule": "approved_database_property_records_only"},
        {"rule": "exactly_one_surface_boundary_payload"},
        {"rule": "implicit_time_steps_at_most_2000"},
        {"rule": "enthalpy_and_conductivity_domain_checked_each_picard_iteration"},
        {"rule": "engineering_mode_rejects_reference_only_property_sets"},
    ]

    _ANALYTIC_COMMON = {
        "property_set_id": "F005_ANALYTIC_CONSTANT_V1",
        "calculation_purpose": "validation",
        "half_thickness_m": 0.1,
        "initial_temperature_k": 800.0,
        "casting_speed_m_s": 0.02,
        "grid_cells": 20,
        "shell_solid_fraction_threshold": 0.9,
        "boundary_source": "approved_database_benchmark",
        "output_points": 3,
    }
    qualification_cases = [
        {
            "id": "F005-N1",
            "kind": "normal",
            "input": {**_ANALYTIC_COMMON, "duration_s": 0.1, "time_step_s": 0.01,
                      "boundary_mode": "database_profile",
                      "boundary_profile_id": "F005_BENCH_SURFACE_TEMP_300K_V1"},
        },
        {
            "id": "F005-N2",
            "kind": "normal",
            "input": {**_ANALYTIC_COMMON, "duration_s": 0.1, "time_step_s": 0.01,
                      "boundary_mode": "database_profile",
                      "boundary_profile_id": "F005_BENCH_HEAT_FLUX_100KW_M2_V1"},
        },
        {
            "id": "F005-N3",
            "kind": "normal",
            "input": {
                "property_set_id": "NIST_SRM1155A_316L_2019_V1",
                "calculation_purpose": "validation",
                "half_thickness_m": 0.05,
                "initial_temperature_k": 1750.0,
                "duration_s": 0.5,
                "casting_speed_m_s": 0.02,
                "grid_cells": 12,
                "time_step_s": 0.05,
                "shell_solid_fraction_threshold": 0.9,
                "boundary_mode": "constant_surface_temperature",
                "surface_temperature_k": 1500.0,
                "boundary_source": "published_reference_validation_boundary",
                "output_points": 3,
            },
        },
        {
            "id": "F005-B1",
            "kind": "boundary",
            "input": {**_ANALYTIC_COMMON, "duration_s": 0.1, "time_step_s": 0.01,
                      "grid_cells": 10, "boundary_mode": "database_profile",
                      "boundary_profile_id": "F005_BENCH_ZERO_HEAT_FLUX_V1"},
        },
        {
            "id": "F005-F1",
            "kind": "failure",
            "input": {**_ANALYTIC_COMMON, "duration_s": 0.1, "time_step_s": 0.01,
                      "boundary_mode": "database_profile",
                      "boundary_profile_id": "DOES_NOT_EXIST"},
        },
        {
            "id": "F005-F2",
            "kind": "failure",
            "input": {**_ANALYTIC_COMMON, "duration_s": 0.1, "time_step_s": 0.01,
                      "boundary_mode": "constant_heat_flux",
                      "surface_heat_flux_w_m2": 100000.0,
                      "boundary_source": "F007"},
        },
    ]
    data_qualification_cases = [{"id": "F005-DATA-NIST", "input": qualification_cases[2]["input"]}]

    @staticmethod
    def _as_integer(value, name, minimum, maximum):
        if isinstance(value, bool):
            raise ValueError(f"{name}必须是整数")
        try:
            number = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{name}必须是整数") from exc
        if not math.isfinite(number) or not number.is_integer():
            raise ValueError(f"{name}必须是整数")
        integer = int(number)
        if integer < minimum or integer > maximum:
            raise ValueError(f"{name}必须在{minimum}到{maximum}之间")
        return integer

    @staticmethod
    def _values(rows, temperatures):
        return np.asarray(
            [evaluate_correlation_rows(rows, float(temperature))[0] for temperature in temperatures],
            dtype=float,
        )

    @staticmethod
    def _harmonic(left, right):
        denominator = left + right
        if left <= 0 or right <= 0 or denominator <= 0:
            raise RepositoryError("导热系数必须为有限正数", "OUT_OF_DOMAIN")
        return 2.0 * left * right / denominator

    @staticmethod
    def _shell_thickness(cell_fraction, surface_fraction, threshold, dx, half_thickness):
        if cell_fraction is None or surface_fraction is None:
            return None
        if surface_fraction < threshold:
            return 0.0
        for index, fraction in enumerate(cell_fraction):
            if fraction >= threshold:
                continue
            if index == 0:
                left_x, left_fraction = 0.0, surface_fraction
            else:
                left_x = (index - 0.5) * dx
                left_fraction = cell_fraction[index - 1]
            right_x = (index + 0.5) * dx
            if left_fraction <= fraction:
                return min(half_thickness, max(0.0, left_x))
            ratio = (left_fraction - threshold) / (left_fraction - fraction)
            return min(half_thickness, max(0.0, left_x + ratio * (right_x - left_x)))
        return half_thickness

    def _resolve_boundary(self, params, property_set_id, duration):
        mode = params["boundary_mode"]
        profile_id = str(params.get("boundary_profile_id") or "").strip()
        heat_flux = params.get("surface_heat_flux_w_m2")
        surface_temperature = params.get("surface_temperature_k")
        source = params["boundary_source"].strip()
        source_token = source.upper()
        upstream_id = str(params.get("upstream_execution_id") or "").strip()
        if not source:
            raise RepositoryError("boundary_source必须是非空来源说明", "INVALID_INPUT")
        supplied = {
            "boundary_profile_id": bool(profile_id),
            "surface_heat_flux_w_m2": heat_flux is not None,
            "surface_temperature_k": surface_temperature is not None,
        }
        provenance = []
        if mode == "database_profile":
            if not supplied["boundary_profile_id"] or supplied["surface_heat_flux_w_m2"] \
                    or supplied["surface_temperature_k"]:
                raise RepositoryError("database_profile只允许且必须提供boundary_profile_id", "INVALID_INPUT")
            profile, provenance = boundary_profile(profile_id, 0.0)
            if duration > profile["domain"][1]:
                raise RepositoryError("计算时长超出数据库边界批准域", "OUT_OF_DOMAIN")
            if profile["property_set_id"] and profile["property_set_id"] != property_set_id:
                raise RepositoryError("数据库边界与物性集不匹配", "MODEL_NOT_APPLICABLE")
            if profile["profile_type"] == "SURFACE_TEMPERATURE":
                resolved_mode = "constant_surface_temperature"
            elif profile["profile_type"] == "SURFACE_HEAT_FLUX":
                resolved_mode = "constant_heat_flux"
            else:
                raise RepositoryError("首版不支持该数据库边界类型", "MODEL_NOT_APPLICABLE")
            value = float(profile["value"])
            source = f"database:{profile_id}; caller:{source}"
        elif mode == "constant_heat_flux":
            if supplied["boundary_profile_id"] or not supplied["surface_heat_flux_w_m2"] \
                    or supplied["surface_temperature_k"]:
                raise RepositoryError("constant_heat_flux只允许且必须提供surface_heat_flux_w_m2", "INVALID_INPUT")
            resolved_mode, value = mode, float(heat_flux)
            if not math.isfinite(value) or value < 0:
                raise RepositoryError("surface_heat_flux_w_m2必须是有限非负数", "OUT_OF_DOMAIN")
        elif mode == "constant_surface_temperature":
            if supplied["boundary_profile_id"] or supplied["surface_heat_flux_w_m2"] \
                    or not supplied["surface_temperature_k"]:
                raise RepositoryError("constant_surface_temperature只允许且必须提供surface_temperature_k", "INVALID_INPUT")
            resolved_mode, value = mode, float(surface_temperature)
            if not math.isfinite(value) or value <= 0:
                raise RepositoryError("surface_temperature_k必须是有限正数", "OUT_OF_DOMAIN")
        else:
            raise RepositoryError("不支持的boundary_mode", "INVALID_INPUT")
        if source_token == "F007" and (resolved_mode != "constant_heat_flux" or not upstream_id):
            raise RepositoryError("boundary_source=F007时必须使用定热流并提供upstream_execution_id", "MISSING_DATA")
        return {
            "mode": resolved_mode,
            "value": value,
            "source": source,
            "upstream_execution_id": upstream_id or None,
            "boundary_profile_id": profile_id or None,
        }, provenance

    def invoke(self, params, context=None):
        try:
            grid_cells = self._as_integer(params["grid_cells"], "grid_cells", 10, 200)
            max_picard = self._as_integer(
                params.get("max_picard_iterations", 40), "max_picard_iterations", 3, 100
            )
            output_points = self._as_integer(params.get("output_points", 11), "output_points", 2, 51)
            half_thickness = float(params["half_thickness_m"])
            initial_temperature = float(params["initial_temperature_k"])
            duration = float(params["duration_s"])
            casting_speed = float(params["casting_speed_m_s"])
            nominal_dt = float(params["time_step_s"])
            threshold = float(params["shell_solid_fraction_threshold"])
            tolerance = float(params.get("picard_tolerance_k", 1e-6))
            if nominal_dt > duration:
                raise RepositoryError("time_step_s不能大于duration_s", "INVALID_INPUT")
            step_count = int(math.ceil(duration / nominal_dt - 1e-12))
            if step_count > 2000:
                raise RepositoryError("时间步数超过2000；请增大time_step_s或缩短duration_s", "OUT_OF_DOMAIN")

            property_set_id = params["property_set_id"].strip()
            if not property_set_id:
                raise RepositoryError("property_set_id不能为空", "INVALID_INPUT")
            boundary, boundary_provenance = self._resolve_boundary(
                params, property_set_id, duration
            )
            required_properties = ["DENSITY", "ENTHALPY", "THERMAL_CONDUCTIVITY"]
            model, provenance = approved_property_model(property_set_id, required_properties)
            property_set = model["property_set"]
            phase_model = property_set["phase_model"]
            if phase_model != "no_phase_change":
                model, provenance = approved_property_model(
                    property_set_id, [*required_properties, "SOLID_FRACTION"]
                )
            correlations = model["correlations"]
            usage_scope = property_set["usage_scope"]
            purpose = params["calculation_purpose"]
            if purpose == "engineering" and usage_scope not in {
                "ENGINEERING_APPROVED", "PRODUCTION_APPROVED"
            }:
                raise RepositoryError(
                    f"物性集{property_set_id}的{usage_scope}使用域不允许engineering计算",
                    "MODEL_NOT_APPLICABLE",
                )
            if purpose == "validation" and usage_scope not in {
                "REFERENCE_VALIDATION_ONLY", "MATHEMATICAL_BENCHMARK_ONLY",
                "ENGINEERING_APPROVED", "PRODUCTION_APPROVED",
            }:
                raise RepositoryError("物性集使用域不允许validation计算", "MODEL_NOT_APPLICABLE")
            if boundary["mode"] == "constant_surface_temperature" \
                    and boundary["value"] >= initial_temperature:
                raise RepositoryError("凝固冷却的给定表面温度必须低于初始温度", "MODEL_NOT_APPLICABLE")
            provenance.extend(boundary_provenance)

            dx = half_thickness / grid_cells
            x = (np.arange(grid_cells, dtype=float) + 0.5) * dx
            temperature = np.full(grid_cells, initial_temperature, dtype=float)
            capture_steps = set(np.linspace(
                0, step_count, min(output_points, step_count + 1), dtype=int
            ).tolist())
            time_history = []
            cumulative_removed = 0.0
            cumulative_stored = 0.0
            maximum_iterations_used = 0

            def evaluate(name, values):
                return self._values(correlations[name], values)

            def solid_state(values, surface_temperature):
                if phase_model == "no_phase_change":
                    return None, None, None
                fractions = evaluate("SOLID_FRACTION", values).tolist()
                surface_fraction = evaluate_correlation_rows(
                    correlations["SOLID_FRACTION"], float(surface_temperature)
                )[0]
                shell = self._shell_thickness(
                    fractions, surface_fraction, threshold, dx, half_thickness
                )
                return fractions, float(surface_fraction), shell

            def surface_state(values):
                conductivity = evaluate("THERMAL_CONDUCTIVITY", values)
                if boundary["mode"] == "constant_surface_temperature":
                    surface_temperature = boundary["value"]
                    surface_k = evaluate_correlation_rows(
                        correlations["THERMAL_CONDUCTIVITY"], surface_temperature
                    )[0]
                    face_k = self._harmonic(float(conductivity[0]), float(surface_k))
                    heat_flux = 2.0 * face_k * (float(values[0]) - surface_temperature) / dx
                else:
                    heat_flux = boundary["value"]
                    surface_temperature = float(values[0]) - heat_flux * dx / (2.0 * conductivity[0])
                    evaluate_correlation_rows(
                        correlations["THERMAL_CONDUCTIVITY"], surface_temperature
                    )
                return float(surface_temperature), float(heat_flux), conductivity

            initial_surface, _, _ = surface_state(temperature)
            initial_fraction, _, initial_shell = solid_state(temperature, initial_surface)
            time_history.append({
                "time_s": 0.0,
                "axial_position_m": 0.0,
                "surface_temperature_k": initial_surface,
                "center_temperature_k": initial_temperature,
                "center_solid_fraction": (
                    None if initial_fraction is None else float(initial_fraction[-1])
                ),
                "shell_thickness_m": initial_shell,
                "cumulative_removed_heat_j_m2": 0.0,
                "stored_energy_change_j_m2": 0.0,
                "energy_closure_residual_j_m2": 0.0,
                "picard_iterations": 0,
            })

            current_time = 0.0
            for step in range(1, step_count + 1):
                dt = duration - current_time if step == step_count else nominal_dt
                old_temperature = temperature.copy()
                old_enthalpy = evaluate("ENTHALPY", old_temperature)
                iterate = old_temperature.copy()
                converged = False
                final_density = None
                iterations_used = 0
                for iteration in range(1, max_picard + 1):
                    density = evaluate("DENSITY", iterate)
                    conductivity = evaluate("THERMAL_CONDUCTIVITY", iterate)
                    enthalpy_iterate = evaluate("ENTHALPY", iterate)
                    effective_cp = np.asarray([
                        correlation_derivative(correlations["ENTHALPY"], float(value))
                        for value in iterate
                    ], dtype=float)
                    if np.any(~np.isfinite(density)) or np.any(density <= 0) \
                            or np.any(~np.isfinite(conductivity)) or np.any(conductivity <= 0) \
                            or np.any(~np.isfinite(effective_cp)) or np.any(effective_cp <= 0):
                        raise RepositoryError("密度、导热系数和有效热容必须为有限正数", "OUT_OF_DOMAIN")

                    mass = density * effective_cp / dt
                    diagonal = mass.copy()
                    right_hand = density / dt * (
                        old_enthalpy - enthalpy_iterate + effective_cp * iterate
                    )
                    face_k = 2.0 * conductivity[:-1] * conductivity[1:] \
                        / (conductivity[:-1] + conductivity[1:])
                    face_coefficient = face_k / dx ** 2
                    diagonal[:-1] += face_coefficient
                    diagonal[1:] += face_coefficient
                    lower = -face_coefficient.copy()
                    upper = -face_coefficient.copy()
                    if boundary["mode"] == "constant_surface_temperature":
                        boundary_temperature = boundary["value"]
                        boundary_k = evaluate_correlation_rows(
                            correlations["THERMAL_CONDUCTIVITY"], boundary_temperature
                        )[0]
                        surface_k = self._harmonic(float(conductivity[0]), float(boundary_k))
                        surface_coefficient = 2.0 * surface_k / dx ** 2
                        diagonal[0] += surface_coefficient
                        right_hand[0] += surface_coefficient * boundary_temperature
                    else:
                        right_hand[0] -= boundary["value"] / dx

                    banded = np.zeros((3, grid_cells), dtype=float)
                    banded[0, 1:] = upper
                    banded[1, :] = diagonal
                    banded[2, :-1] = lower
                    solved = solve_banded((1, 1), banded, right_hand, check_finite=True)
                    if np.any(~np.isfinite(solved)):
                        raise RepositoryError("线性方程组产生非有限温度", "NUMERICAL_ERROR")
                    delta = float(np.max(np.abs(solved - iterate)))
                    iterations_used = iteration
                    final_density = density
                    if delta <= tolerance:
                        temperature = solved
                        converged = True
                        break
                    iterate = 0.7 * solved + 0.3 * iterate
                if not converged:
                    raise RepositoryError(
                        f"时间步{step}的Picard迭代在{max_picard}次内未收敛", "NUMERICAL_ERROR"
                    )
                maximum_iterations_used = max(maximum_iterations_used, iterations_used)
                new_enthalpy = evaluate("ENTHALPY", temperature)
                step_stored = float(np.sum(final_density * (new_enthalpy - old_enthalpy)) * dx)
                surface_temperature, heat_flux, _ = surface_state(temperature)
                step_removed = heat_flux * dt
                cumulative_stored += step_stored
                cumulative_removed += step_removed
                current_time += dt
                if step in capture_steps or step == step_count:
                    fractions, _, shell = solid_state(temperature, surface_temperature)
                    time_history.append({
                        "time_s": current_time,
                        "axial_position_m": casting_speed * current_time,
                        "surface_temperature_k": surface_temperature,
                        "center_temperature_k": float(temperature[-1]),
                        "center_solid_fraction": (
                            None if fractions is None else float(fractions[-1])
                        ),
                        "shell_thickness_m": shell,
                        "cumulative_removed_heat_j_m2": cumulative_removed,
                        "stored_energy_change_j_m2": cumulative_stored,
                        "energy_closure_residual_j_m2": cumulative_stored + cumulative_removed,
                        "picard_iterations": iterations_used,
                    })

            final_surface, _, _ = surface_state(temperature)
            final_fraction, _, final_shell = solid_state(temperature, final_surface)
            final_profile = [
                {
                    "x_m": float(position),
                    "temperature_k": float(value),
                    "solid_fraction": None if final_fraction is None else float(final_fraction[index]),
                }
                for index, (position, value) in enumerate(zip(x, temperature))
            ]
            closure = cumulative_stored + cumulative_removed
            closure_scale = max(abs(cumulative_stored), abs(cumulative_removed), 1.0)
            closure_relative = abs(closure) / closure_scale
            if final_shell is None:
                shell_status = "not_applicable_no_phase_model"
            elif final_shell <= 0:
                shell_status = "no_threshold_shell"
            elif final_shell >= half_thickness:
                shell_status = "fully_solid_to_center"
            else:
                shell_status = "partial_shell"
            warnings_out = []
            if grid_cells == 10:
                warnings_out.append(BoundaryWarning("grid_cells", "使用最低允许网格，仅适合边界/烟雾验证"))
            if usage_scope in {"REFERENCE_VALIDATION_ONLY", "MATHEMATICAL_BENCHMARK_ONLY"}:
                warnings_out.append(BoundaryWarning("property_set_id", f"物性使用域为{usage_scope}，不得用于生产控制"))
            if closure_relative > 0.005:
                warnings_out.append(BoundaryWarning("energy_closure_relative", "能量闭合相对残差超过0.5%"))
            if closure_relative > 0.02:
                raise RepositoryError("能量闭合相对残差超过2%，拒绝返回合格结果", "NUMERICAL_ERROR")
            return ModelResult(
                True,
                result={
                    "time_history": time_history,
                    "final_temperature_profile": final_profile,
                    "shell_thickness_m": final_shell,
                    "shell_status": shell_status,
                    "final_surface_temperature_k": final_surface,
                    "final_center_temperature_k": float(temperature[-1]),
                    "total_time_s": current_time,
                    "final_axial_position_m": casting_speed * current_time,
                    "cumulative_removed_heat_j_m2": cumulative_removed,
                    "stored_energy_change_j_m2": cumulative_stored,
                    "energy_closure_residual_j_m2": closure,
                    "energy_closure_relative": closure_relative,
                    "grid_cells": grid_cells,
                    "cell_size_m": dx,
                    "time_steps": step_count,
                    "nominal_time_step_s": nominal_dt,
                    "max_picard_iterations_used": maximum_iterations_used,
                    "all_steps_converged": True,
                    "property_set_id": property_set_id,
                    "property_usage_scope": usage_scope,
                    "boundary_summary": boundary,
                    "calculation_purpose": purpose,
                    "solver_version": "implicit-enthalpy-fvm-v1/scipy-1.18.1",
                },
                boundary_check=BoundaryCheck(not warnings_out, warnings_out),
                provenance=provenance,
            )
        except RepositoryError as exc:
            return ModelResult(False, error=str(exc), error_code=exc.error_code)
        except (ValueError, TypeError) as exc:
            return ModelResult(False, error=str(exc), error_code="INVALID_INPUT")
        except Exception as exc:
            return ModelResult(False, error=f"一维焓法求解失败: {exc}", error_code="NUMERICAL_ERROR")


class F006_SolidificationEndPrediction(BaseModelTool):
    """Locate the first centre-solid-fraction threshold and map it to strand position."""

    model_id, name, version = "F006", "凝固终点预测", "1.0.0"
    tool_name = "metallurgy_predict_solidification_end"
    scenario = "凝固与连铸"
    priority = "P1"
    status = qualification_status = "qualified"
    count_eligible = True
    model_type = "确定性物理后处理/中心固相率阈值事件定位"
    data_requirement = "VERSIONED_DATABASE_REFERENCE"
    data_access_mode = "database_repository"
    required_dataset_ids = ["DS_F006_ENDPOINT_BENCH_V1"]
    database_tables = ["metallurgy_v2.casting_machine_configuration"]
    description = (
        "校验F005产生的中心固相率时间曲线，定位首次达到给定阈值的时刻，"
        "用分段线性插值和z=v*t计算凝固终点，并依据批准的连铸机配置判断终点在设备内、"
        "设备出口或设备外。首版是物理阈值路径，不是DS042回归代理，也不输出统计置信区间。"
    )
    applicable_boundary = (
        "适用于拉速恒定、中心固相率曲线单调不减且覆盖设备出口时刻的一次F005后处理；"
        "验证用合成设备配置不得用于工程设计、生产控制或报警。真实设备调用必须先导入"
        "具有授权、版本和批准用途域的设备配置。"
    )
    required_data = [
        "F005上游执行ID及其time_history中的time_s和center_solid_fraction",
        "PostgreSQL中批准的设备配置、有效冶金长度和拉速范围",
        "显式凝固终点中心固相率阈值",
    ]
    data_source = [
        "PostgreSQL metallurgy_v2.casting_machine_configuration",
        "项目生成、可手算的分段线性事件定位基准",
    ]
    source_version = (
        "P1-W5C-CASTING-ENDPOINT-2026.09-v1; "
        "first-threshold-piecewise-linear-v1"
    )
    formula_reference = (
        "Find first fs_center(t)>=fs_threshold; for fs0<threshold<fs1, "
        "t*=t0+(threshold-fs0)*(t1-t0)/(fs1-fs0); z*=v_cast*t*"
    )
    source_records = [
        {
            "source_id": "DS_F006_ENDPOINT_BENCH_V1",
            "name": "F006 solidification-end event-location benchmarks",
            "version": "2026.09-v1",
            "table": "metallurgy_v2.casting_machine_configuration",
        }
    ]
    failure_modes = [
        "上游执行ID为空或不是F005执行ID",
        "设备配置缺失、未批准或其用途域不允许本次计算用途",
        "拉速超出设备配置批准范围",
        "曲线少于2点、字段异常、时间非严格递增、固相率越界或非单调",
        "曲线未达到终点固相率阈值，或未覆盖设备出口时刻",
    ]
    independent_validation = [
        "线性曲线交点与手算插值恒等式一致",
        "轴向位置严格满足z=v*t",
        "提高终点固相率阈值不得使预测终点提前",
        "在同一分段直线上加密曲线后交点保持不变",
        "设备出口中心固相率由独立的时间插值计算",
        "设备内外状态与批准的有效冶金长度直接比较",
    ]
    dependencies = ["F005"]
    relations = [
        {
            "type": "consumes_output_from",
            "target": "F005",
            "description": "F006消费F005的中心固相率时间曲线和执行ID，但独立完成阈值事件插值及设备边界判断。",
        },
        {
            "type": "overlaps_with",
            "target": "F004",
            "description": "两者都返回固相率相关结果；F004计算温度—固相率曲线，F006定位中心液芯消失的时间和轴向位置。",
        },
    ]
    input_fields = [
        InputField(
            "machine_configuration_id",
            "批准设备配置ID",
            "string",
            description="必须存在于PostgreSQL且is_approved=true",
        ),
        InputField(
            "calculation_purpose",
            "计算用途",
            "select",
            enum=["validation", "engineering"],
            description="合成数学基准配置只允许validation",
        ),
        InputField(
            "upstream_execution_id",
            "F005上游执行ID",
            "string",
            description="必须是实际F005调用返回的EXEC-执行编号",
        ),
        InputField(
            "casting_speed_m_s",
            "拉坯速度",
            "number",
            unit="m/s",
            min_value=1e-8,
            max_value=1.0,
        ),
        InputField(
            "endpoint_solid_fraction_threshold",
            "终点中心固相率阈值",
            "number",
            unit="1",
            min_value=0.0,
            max_value=1.0,
            description="必须满足0<阈值<=1",
        ),
        InputField(
            "center_solid_fraction_curve",
            "中心固相率时间曲线",
            "array",
            unit="time:s; center_solid_fraction:1",
            min_items=2,
            max_items=2001,
            description="按时间严格递增、固相率单调不减的F005输出子集",
            items={
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "time_s": {
                        "type": "number",
                        "minimum": 0,
                        "description": "自F005计算起点的时间；单位: s",
                    },
                    "center_solid_fraction": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1,
                        "description": "铸坯中心固相率；单位: 1",
                    },
                },
                "required": ["time_s", "center_solid_fraction"],
            },
        ),
    ]
    output_fields = [
        OutputField("solidification_end_time_s", "凝固终点时间", "number", "s"),
        OutputField("solidification_end_position_m", "凝固终点位置", "number", "m"),
        OutputField("endpoint_solid_fraction_threshold", "终点固相率阈值", "number", "1"),
        OutputField("interpolation_left_point", "插值左点", "object"),
        OutputField("interpolation_right_point", "插值右点", "object"),
        OutputField("time_resolution_s", "交点时间分辨率", "number", "s"),
        OutputField("position_resolution_m", "交点位置分辨率", "number", "m"),
        OutputField("position_interval_m", "交点包围位置区间", "array", "m"),
        OutputField("equipment_status", "设备边界状态", "string"),
        OutputField("effective_metallurgical_length_m", "有效冶金长度", "number", "m"),
        OutputField("machine_exit_time_s", "设备出口对应时间", "number", "s"),
        OutputField("exit_center_solid_fraction", "设备出口中心固相率", "number", "1"),
        OutputField("curve_point_count", "曲线点数", "integer", "1"),
        OutputField("upstream_execution_id", "F005上游执行ID", "string"),
        OutputField("machine_configuration_id", "设备配置ID", "string"),
        OutputField("machine_configuration_version", "设备配置版本", "string"),
        OutputField("calculation_purpose", "计算用途", "string"),
        OutputField("algorithm_version", "算法版本", "string"),
    ]
    validation_rules = [
        {"rule": "approved_database_machine_configuration_only"},
        {"rule": "strictly_increasing_time_and_monotone_fraction"},
        {"rule": "curve_must_cross_threshold_and_cover_machine_exit"},
        {"rule": "position_is_casting_speed_times_time"},
        {"rule": "benchmark_configuration_rejects_engineering_use"},
    ]

    _LINEAR_CURVE = [
        {"time_s": 0.0, "center_solid_fraction": 0.0},
        {"time_s": 5.0, "center_solid_fraction": 0.5},
        {"time_s": 10.0, "center_solid_fraction": 1.0},
    ]
    _COMMON = {
        "calculation_purpose": "validation",
        "upstream_execution_id": "EXEC-000000000000F005",
        "casting_speed_m_s": 0.02,
    }
    qualification_cases = [
        {
            "id": "F006-N1",
            "kind": "normal",
            "input": {
                **_COMMON,
                "machine_configuration_id": "F006_BENCH_LONG_020M_V1",
                "endpoint_solid_fraction_threshold": 0.8,
                "center_solid_fraction_curve": _LINEAR_CURVE,
            },
        },
        {
            "id": "F006-N2",
            "kind": "normal",
            "input": {
                **_COMMON,
                "machine_configuration_id": "F006_BENCH_LONG_020M_V1",
                "endpoint_solid_fraction_threshold": 0.9,
                "center_solid_fraction_curve": [
                    {"time_s": 0.0, "center_solid_fraction": 0.1},
                    {"time_s": 2.0, "center_solid_fraction": 0.3},
                    {"time_s": 6.0, "center_solid_fraction": 0.8},
                    {"time_s": 10.0, "center_solid_fraction": 1.0},
                ],
            },
        },
        {
            "id": "F006-N3",
            "kind": "normal",
            "input": {
                **_COMMON,
                "machine_configuration_id": "F006_BENCH_SHORT_008M_V1",
                "endpoint_solid_fraction_threshold": 0.8,
                "center_solid_fraction_curve": _LINEAR_CURVE,
            },
        },
        {
            "id": "F006-B1",
            "kind": "boundary",
            "input": {
                **_COMMON,
                "machine_configuration_id": "F006_BENCH_LONG_020M_V1",
                "endpoint_solid_fraction_threshold": 0.5,
                "center_solid_fraction_curve": _LINEAR_CURVE,
            },
        },
        {
            "id": "F006-F1",
            "kind": "failure",
            "input": {
                **_COMMON,
                "machine_configuration_id": "F006_BENCH_LONG_020M_V1",
                "endpoint_solid_fraction_threshold": 0.95,
                "center_solid_fraction_curve": [
                    {"time_s": 0.0, "center_solid_fraction": 0.0},
                    {"time_s": 10.0, "center_solid_fraction": 0.8},
                ],
            },
        },
        {
            "id": "F006-F2",
            "kind": "failure",
            "input": {
                **_COMMON,
                "machine_configuration_id": "F006_BENCH_LONG_020M_V1",
                "endpoint_solid_fraction_threshold": 0.8,
                "center_solid_fraction_curve": [
                    {"time_s": 0.0, "center_solid_fraction": 0.0},
                    {"time_s": 5.0, "center_solid_fraction": 0.9},
                    {"time_s": 10.0, "center_solid_fraction": 0.8},
                ],
            },
        },
    ]
    data_qualification_cases = [
        {"id": "F006-DATA-BENCH", "input": qualification_cases[0]["input"]}
    ]

    @staticmethod
    def _validated_curve(raw_curve):
        if not isinstance(raw_curve, list) or not 2 <= len(raw_curve) <= 2001:
            raise RepositoryError("center_solid_fraction_curve必须含2至2001个点", "INVALID_INPUT")
        curve = []
        allowed = {"time_s", "center_solid_fraction"}
        for index, point in enumerate(raw_curve):
            if not isinstance(point, dict) or set(point) != allowed:
                raise RepositoryError(
                    f"曲线第{index}点必须且只能含time_s和center_solid_fraction",
                    "INVALID_INPUT",
                )
            if isinstance(point["time_s"], bool) or isinstance(
                point["center_solid_fraction"], bool
            ):
                raise RepositoryError(f"曲线第{index}点必须是数值", "INVALID_INPUT")
            try:
                time_s = float(point["time_s"])
                fraction = float(point["center_solid_fraction"])
            except (TypeError, ValueError) as exc:
                raise RepositoryError(f"曲线第{index}点必须是数值", "INVALID_INPUT") from exc
            if not math.isfinite(time_s) or time_s < 0:
                raise RepositoryError("曲线时间必须是有限非负数", "INVALID_INPUT")
            if not math.isfinite(fraction) or not 0.0 <= fraction <= 1.0:
                raise RepositoryError("中心固相率必须是[0,1]内有限数值", "INVALID_INPUT")
            if curve and time_s <= curve[-1]["time_s"]:
                raise RepositoryError("曲线时间必须严格递增", "INVALID_INPUT")
            if curve and fraction < curve[-1]["center_solid_fraction"]:
                raise RepositoryError("中心固相率曲线必须单调不减", "INVALID_INPUT")
            curve.append({"time_s": time_s, "center_solid_fraction": fraction})
        return curve

    @staticmethod
    def _curve_value(curve, time_s):
        if time_s < curve[0]["time_s"] or time_s > curve[-1]["time_s"]:
            raise RepositoryError("中心固相率曲线未覆盖设备出口时刻", "MISSING_DATA")
        for point in curve:
            if math.isclose(point["time_s"], time_s, rel_tol=0.0, abs_tol=1e-12):
                return point["center_solid_fraction"]
        for left, right in zip(curve, curve[1:]):
            if left["time_s"] < time_s < right["time_s"]:
                ratio = (time_s - left["time_s"]) / (right["time_s"] - left["time_s"])
                return left["center_solid_fraction"] + ratio * (
                    right["center_solid_fraction"] - left["center_solid_fraction"]
                )
        raise RepositoryError("无法插值设备出口中心固相率", "NUMERICAL_ERROR")

    @staticmethod
    def _threshold_event(curve, threshold):
        crossing_index = next(
            (index for index, point in enumerate(curve)
             if point["center_solid_fraction"] >= threshold),
            None,
        )
        if crossing_index is None:
            raise RepositoryError("中心固相率曲线未达到终点阈值", "MODEL_NOT_APPLICABLE")
        right = curve[crossing_index]
        if crossing_index == 0 or right["center_solid_fraction"] == threshold:
            return right["time_s"], right, right, True
        left = curve[crossing_index - 1]
        fraction_span = right["center_solid_fraction"] - left["center_solid_fraction"]
        if fraction_span <= 0:
            raise RepositoryError("终点阈值包围区间的固相率增量必须大于0", "NUMERICAL_ERROR")
        ratio = (threshold - left["center_solid_fraction"]) / fraction_span
        event_time = left["time_s"] + ratio * (right["time_s"] - left["time_s"])
        return event_time, left, right, False

    def invoke(self, params, context=None):
        try:
            configuration_id = params["machine_configuration_id"].strip()
            purpose = params["calculation_purpose"]
            upstream_id = params["upstream_execution_id"].strip()
            if not configuration_id:
                raise RepositoryError("machine_configuration_id不能为空", "INVALID_INPUT")
            if not upstream_id:
                raise RepositoryError("upstream_execution_id不能为空", "MISSING_DATA")
            if not upstream_id.startswith("EXEC-"):
                raise RepositoryError("upstream_execution_id必须是F005返回的EXEC-执行编号", "INVALID_INPUT")

            speed = float(params["casting_speed_m_s"])
            threshold = float(params["endpoint_solid_fraction_threshold"])
            if not math.isfinite(speed) or speed <= 0:
                raise RepositoryError("casting_speed_m_s必须是有限正数", "OUT_OF_DOMAIN")
            if not math.isfinite(threshold) or not 0.0 < threshold <= 1.0:
                raise RepositoryError(
                    "endpoint_solid_fraction_threshold必须满足0<阈值<=1", "OUT_OF_DOMAIN"
                )
            curve = self._validated_curve(params["center_solid_fraction_curve"])
            configuration, provenance = approved_machine_configuration(configuration_id)
            speed_min = float(configuration["casting_speed_min_m_s"])
            speed_max = float(configuration["casting_speed_max_m_s"])
            if speed < speed_min or speed > speed_max:
                raise RepositoryError(
                    f"拉速{speed:g} m/s超出批准范围[{speed_min:g}, {speed_max:g}]",
                    "OUT_OF_DOMAIN",
                )
            usage_scope = configuration["usage_scope"]
            if purpose == "engineering" and usage_scope not in {
                "ENGINEERING_APPROVED", "PRODUCTION_APPROVED"
            }:
                raise RepositoryError(
                    f"设备配置{configuration_id}的{usage_scope}使用域不允许engineering计算",
                    "MODEL_NOT_APPLICABLE",
                )
            if purpose == "validation" and usage_scope not in {
                "MATHEMATICAL_BENCHMARK_ONLY", "REFERENCE_VALIDATION_ONLY",
                "ENGINEERING_APPROVED", "PRODUCTION_APPROVED",
            }:
                raise RepositoryError("设备配置使用域不允许validation计算", "MODEL_NOT_APPLICABLE")

            event_time, left, right, exact_point = self._threshold_event(curve, threshold)
            event_position = speed * event_time
            machine_length = float(configuration["effective_metallurgical_length_m"])
            exit_time = machine_length / speed
            exit_fraction = self._curve_value(curve, exit_time)
            absolute_tolerance = 1e-12
            if math.isclose(event_position, machine_length, rel_tol=0.0,
                            abs_tol=absolute_tolerance):
                equipment_status = "at_machine_exit"
            elif event_position < machine_length:
                equipment_status = "inside_machine"
            else:
                equipment_status = "beyond_machine_exit"

            def enriched(point):
                return {
                    "time_s": point["time_s"],
                    "center_solid_fraction": point["center_solid_fraction"],
                    "axial_position_m": speed * point["time_s"],
                }

            left_position = speed * left["time_s"]
            right_position = speed * right["time_s"]
            warnings_out = []
            if usage_scope in {"MATHEMATICAL_BENCHMARK_ONLY", "REFERENCE_VALIDATION_ONLY"}:
                warnings_out.append(BoundaryWarning(
                    "machine_configuration_id",
                    f"设备配置用途域为{usage_scope}，不得用于生产控制",
                ))
            if exact_point:
                warnings_out.append(BoundaryWarning(
                    "endpoint_solid_fraction_threshold",
                    "曲线采样点恰好达到阈值，交点包围区间退化为零宽",
                ))
            if equipment_status == "beyond_machine_exit":
                warnings_out.append(BoundaryWarning(
                    "solidification_end_position_m",
                    "预测凝固终点超过批准的有效冶金长度",
                    max_allowed=machine_length,
                ))
            elif equipment_status == "at_machine_exit":
                warnings_out.append(BoundaryWarning(
                    "solidification_end_position_m",
                    "预测凝固终点位于批准的有效冶金长度边界",
                    max_allowed=machine_length,
                ))
            return ModelResult(
                True,
                result={
                    "solidification_end_time_s": event_time,
                    "solidification_end_position_m": event_position,
                    "endpoint_solid_fraction_threshold": threshold,
                    "interpolation_left_point": enriched(left),
                    "interpolation_right_point": enriched(right),
                    "time_resolution_s": right["time_s"] - left["time_s"],
                    "position_resolution_m": right_position - left_position,
                    "position_interval_m": [left_position, right_position],
                    "equipment_status": equipment_status,
                    "effective_metallurgical_length_m": machine_length,
                    "machine_exit_time_s": exit_time,
                    "exit_center_solid_fraction": exit_fraction,
                    "curve_point_count": len(curve),
                    "upstream_execution_id": upstream_id,
                    "machine_configuration_id": configuration_id,
                    "machine_configuration_version": configuration["configuration_version"],
                    "calculation_purpose": purpose,
                    "algorithm_version": "first-threshold-piecewise-linear-v1",
                },
                boundary_check=BoundaryCheck(not warnings_out, warnings_out),
                provenance=[provenance],
            )
        except RepositoryError as exc:
            return ModelResult(False, error=str(exc), error_code=exc.error_code)
        except (TypeError, ValueError, KeyError) as exc:
            return ModelResult(False, error=str(exc), error_code="INVALID_INPUT")
