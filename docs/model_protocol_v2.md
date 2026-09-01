# Metallurgy Platform v2.0 统一模型协议

## 实施边界

本协议覆盖P1-W6B完成后的53个已注册且最终合格工具，表格主能力目录覆盖49项。保留旧 `/invoke` 接口，并以新增接口承载四维资格、执行追踪和大模型function calling。新增工具必须先有蓝图；数据必需型工具还必须先明确数据集、数据库表和Repository契约。

## 模型卡

每张模型卡至少包含：

`model_code`、`model_name`、`category`、`description`、`input_schema`、`output_schema`、`input_units`、`output_units`、`applicable_conditions`、`temperature_range`、`pressure_range`、`required_data`、`data_source`、`formula_reference`、`dependencies`、`version`、`status`、`error_codes`、`tool_name`、`data_requirement`、`data_access_mode`、`required_dataset_ids`、`database_tables`、`eligibility`。

旧字段 `model_id`、`name`、`scenario`、`input_schema_json`、`output_schema_json` 保留，供现有前端和数据库兼容使用。

## 接口契约

### `GET /api/v1/models`

返回全部模型卡。可使用 `scenario` 查询参数筛选。

### `GET /api/v1/models/{model_code}`

返回单个模型卡；不存在时返回 HTTP 404。

### `GET /api/v1/tools?fully_eligible=true`

返回标准function-tool数组，默认只暴露通过实现、数据、接口和科学验证四维资格的工具。无目录编号冲突的历史函数继续使用 `metallurgy_{model_code小写}`；编号冲突的新工具使用唯一语义函数名，例如 `metallurgy_check_charge_valence_balance`。参数来自输入JSON Schema，函数名一经发布保持稳定。

示例：

```json
{
  "type": "function",
  "function": {
    "name": "metallurgy_t001",
    "description": "计算均质平板一维稳态导热的热流密度、热流率和热阻。",
    "parameters": {
      "type": "object",
      "properties": {
        "thermal_conductivity": {"type": "number", "minimum": 1e-300},
        "thickness": {"type": "number", "minimum": 1e-300},
        "area": {"type": "number", "minimum": 1e-300},
        "hot_temperature": {"type": "number", "minimum": 1e-12},
        "cold_temperature": {"type": "number", "minimum": 1e-12}
      },
      "required": ["thermal_conductivity", "thickness", "area", "hot_temperature", "cold_temperature"],
      "additionalProperties": false
    }
  },
  "model_code": "T001",
  "fully_eligible": true
}
```

### `POST /api/v1/tools/{tool_name}/call`

用于执行大模型产生的function call：

```json
{
  "arguments": {
    "thermal_conductivity": 20,
    "thickness": 0.1,
    "area": 2,
    "hot_temperature": 1000,
    "cold_temperature": 500
  },
  "options": {
    "validate_boundary": true,
    "return_provenance": true
  }
}
```

未知函数返回HTTP 404。已注册但未通过最终资格的函数返回HTTP 409和 `TOOL_NOT_FULLY_ELIGIBLE`，不会执行其静态数据路径。

#### F007结晶器热流调用约束

函数名为 `metallurgy_calc_mold_heat_flux`。每个冷却回路必须同时给出质量流量、入口/出口K温度、显式水比热和测量来源；还必须给出与回路口径一致的有效换热面积及面积定义。不得把体积流量直接填入质量流量字段，不得由大模型补水密度、比热、设备面积或经验常数。

```json
{
  "arguments": {
    "cooling_circuits": [
      {
        "circuit_id": "whole-mold",
        "mass_flow_kg_s": 10,
        "inlet_temperature_k": 293.15,
        "outlet_temperature_k": 298.15,
        "water_specific_heat_j_kg_k": 4200,
        "measurement_source": "calibrated_flowmeter_and_paired_rtd"
      }
    ],
    "effective_heat_transfer_area_m2": 2,
    "area_definition": "whole_mold",
    "steel_mass_flow_kg_s": 2
  },
  "options": {
    "validate_boundary": true,
    "return_provenance": true
  }
}
```

该输入返回总移热率 `210000 W`、平均热流密度 `105000 W/m²` 和单位钢质量移热 `105000 J/kg`。`T_out=T_in` 是带警告的零移热边界；`T_out<T_in`、非正面积或水温达到/超过647.096 K返回 `OUT_OF_DOMAIN`。

#### F005一维坯壳厚度调用约束

函数名为 `metallurgy_solve_1d_shell_growth`。调用者必须给出批准物性集、计算用途、铸坯半厚度、初温、时长、拉速、网格、时间步和坯壳固相率阈值。表面边界只能三选一：数据库边界ID、显式外向热流或显式表面温度；显式边界必须带来源，来自F007时还必须携带其执行ID。不得由大模型补钢种物性、相变参数、设备边界或隐藏经验常数。

```json
{
  "arguments": {
    "property_set_id": "F005_ANALYTIC_CONSTANT_V1",
    "calculation_purpose": "validation",
    "half_thickness_m": 0.1,
    "initial_temperature_k": 800,
    "duration_s": 0.1,
    "casting_speed_m_s": 0.02,
    "grid_cells": 20,
    "time_step_s": 0.01,
    "shell_solid_fraction_threshold": 0.9,
    "boundary_mode": "database_profile",
    "boundary_profile_id": "F005_BENCH_HEAT_FLUX_100KW_M2_V1",
    "boundary_source": "approved_database_benchmark",
    "output_points": 3
  },
  "options": {
    "validate_boundary": true,
    "return_provenance": true
  }
}
```

数学基准和NIST参考物性集只允许 `calculation_purpose=validation`，不得用于生产控制。数据库记录缺失、温度越出相关式范围、边界与物性集不匹配、F007执行ID缺失或非线性求解不收敛均显式失败，不使用JSON常数或默认钢种回退。

#### B012绝热反应温度调用约束

函数名为 `metallurgy_calculate_adiabatic_reaction_temperature`。反应式必须匹配数据库登记反应；`feed_moles` 的键必须带相态，例如 `C(s)`、`O2(g)`。不得由大模型补反应焓、热容或默认惰性气体。求根温区必须显式给出；相变六项参数要么全部省略，要么全部提供来源和版本。

```json
{
  "arguments": {
    "reaction": "C + O₂ → CO₂",
    "feed_moles": {"C(s)": 1, "O2(g)": 1, "N2(g)": 3.76},
    "initial_temperature_k": 298.15,
    "conversion_fraction": 1,
    "temperature_lower_k": 298.15,
    "temperature_upper_k": 3500
  }
}
```

数据库无反应/热物性记录、转化后出现负物质的量、温区未括住能量零点或能量残差超限均失败关闭。当前公式是固定反应进度的绝热定压能量衡算，不是化学平衡或燃烧动力学模型。

#### B013理想气体混合平衡调用约束

函数名为 `metallurgy_solve_ideal_gas_equilibrium`。调用者必须显式给出完整候选气体集合、初始物质的量、温度和压力；物种键必须带 `(g)`。大模型不得自行删减可能生成的候选物种，也不得把凝聚相或无NASA7记录的物种加入首版求解。

```json
{
  "arguments": {
    "candidate_species": ["CO(g)", "H2O(g)", "CO2(g)", "H2(g)"],
    "initial_moles": {"CO(g)": 1, "H2O(g)": 1},
    "temperature_k": 1000,
    "pressure_pa": 100000
  }
}
```

结果只有同时满足求解器收敛、逐元素守恒和总Gibbs能不升三个闸门才成功。当前范围为200–3500 K、最多12种中性理想气体和8种元素，不处理真实气体逸度、离子或凝聚相。

#### B016/B017溶液参数调用约束

`B016` 函数名为 `metallurgy_calculate_redlich_kister_activity`；`B017` 函数名为 `metallurgy_convert_henry_raoult_standard_state`。两项都禁止内置或由大模型猜测合金参数，每次调用必须显式传入 `parameter_source` 与 `parameter_version`。

- B016仅接受恰好两个组元和按 `L0,L1,...` 排列的 `interaction_parameters_j_mol`；首版系数视为给定温度常数。
- B017的 `conversion_mode=gamma_infinite` 时必须给 `gamma_infinite`；取 `henry_over_pure_fugacity` 时必须同时给同为Pa的 `henry_constant_pa` 与 `pure_component_fugacity_pa`。
- B017在溶质摩尔分数大于0.1时返回超稀释域警告；它只变换标准态，不拟合Henry常数。

### `POST /api/v1/models/{model_code}/validate`

请求：

```json
{
  "input": {"formula": "Fe2O3"}
}
```

响应：

```json
{
  "valid": true,
  "model_code": "A003",
  "model_version": "1.0.0",
  "errors": []
}
```

该接口只检查参数完整性、类型、枚举和模型声明的数值范围，不执行公式。

### `POST /api/v1/models/{model_code}/execute`

请求：

```json
{
  "input": {"formula": "Fe2O3"},
  "options": {
    "validate_boundary": true,
    "return_provenance": true
  }
}
```

响应包含 `execution_id`、`trace_id`、`tool_uid`、`catalog_id`、`model_code`、`model_version`、标准化输入、实际数据记录、边界检查、输出、状态、标准错误码、运行时间和调用主体。

### `GET /api/v1/executions/{execution_id}`

读取本进程内已完成的执行轨迹。生产环境应通过迁移 `003_model_experiments.sql` 将同构记录持久化。

### `POST /api/v1/experiments/run`

请求：

```json
{
  "user_query": "请计算 Fe2O3 的摩尔质量",
  "mode": "autonomous",
  "model_code": null,
  "arguments": {"formula": "Fe2O3"},
  "llm_name": "external-orchestrator",
  "prompt_version": "v1",
  "result_validation_enabled": true
}
```

`mode` 取值：

- `direct`：禁止调用工具，保存直接回答基线；
- `forced`：必须提供 `model_code`，校验通过后调用；
- `autonomous`：按问题召回候选并决定是否调用，可用 `model_code` 固定候选以复现实验。

响应保存 `user_query`、大模型与 Prompt 版本、候选模型、选中模型、选择原因、生成参数、校验和执行结果、重试次数、最终回答、延迟与 Token 用量占位。

### `GET /api/v1/experiments/{experiment_id}`

读取单次实验完整轨迹。

以上接口同时提供不带 `/v1` 的兼容路径。

## 标准错误码

`INVALID_INPUT`、`UNIT_MISMATCH`、`OUT_OF_DOMAIN`、`MISSING_DATA`、`DATA_BACKEND_UNAVAILABLE`、`MULTIPLE_SPECIES_MATCH`、`PHASE_MISMATCH`、`TEMPERATURE_RANGE_ERROR`、`REACTION_NOT_BALANCED`、`NUMERICAL_ERROR`、`MODEL_NOT_APPLICABLE`、`MODEL_ARTIFACT_UNAVAILABLE`、`UNKNOWN_MODEL`、`INTERNAL_ERROR`。

## 四维资格与计数

- `implementation_qualified`：真实实现、Schema、单位、错误、关系和5个准入样例通过；
- `data_qualified`：公式工具自动满足；数据工具必须通过数据库Repository并返回记录级溯源；
- `interface_qualified`：function名称、描述和parameters Schema有效且唯一；
- `scientific_validation_qualified`：至少3个正常及2个边界/失败验证通过。

只有四项均通过，`fully_eligible=true`。健康检查和工具清单分别报告：

```json
{
  "registered_count": 53,
  "runtime_tool_count": 53,
  "catalog_coverage_count": 49,
  "qualified_executable_count": 53,
  "implementation_qualified_count": 53,
  "data_required_count": 23,
  "data_qualified_count": 23,
  "interface_qualified_count": 53,
  "fully_eligible_count": 53
}
```

这些值由注册中心实时计算，不得在运行时代码中写死。当前23个数据必需型工具均通过数据库Repository执行并返回记录级溯源；F005读取版本化连铸热物性和边界记录，B012/B013读取现有热化学/NASA7记录，F007及B016/B017为显式输入的公式工具。

历史错误码在注册中心统一归一化，不要求 17 个旧模型同时重写。

## 自动验证

运行：

```powershell
python Tools/run_baseline_tests.py
```

测试包含原17个黄金种子回归、原30项资产保留、当前53工具资格测试、四维数据资格、function-tool契约、自动生成异常输入，以及三种实验模式的调用闭环。各波新增工具另有专项准入测试和隔离大模型调用用例。

黄金算例源文件：`Tools/benchmarks/golden_cases.json`。
