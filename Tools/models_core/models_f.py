"""Qualified continuous-casting and CALPHAD solidification tools."""

from __future__ import annotations

import math
import warnings
from functools import lru_cache

import numpy as np
from pycalphad import equilibrium, variables as v
from scheil import simulate_scheil_solidification

from .base import BaseModelTool, BoundaryCheck, BoundaryWarning, InputField, ModelResult, OutputField
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
