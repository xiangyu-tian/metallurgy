# Metallurgy Platform v2.0 统一模型协议

## 实施边界

本协议覆盖当前30个已注册工具。保留旧 `/invoke` 接口，并以新增接口承载四维资格、执行追踪和大模型function calling。新增工具必须先有蓝图；数据必需型工具还必须先明确数据集、数据库表和Repository契约。

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

返回标准function-tool数组，默认只暴露通过实现、数据、接口和科学验证四维资格的工具。每个函数名固定为 `metallurgy_{model_code小写}`，参数来自输入JSON Schema。

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

响应包含 `execution_id`、`trace_id`、`model_code`、`model_version`、标准化输入、实际数据记录、边界检查、输出、状态、标准错误码、运行时间和调用主体。

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

`INVALID_INPUT`、`UNIT_MISMATCH`、`OUT_OF_DOMAIN`、`MISSING_DATA`、`DATA_BACKEND_UNAVAILABLE`、`MULTIPLE_SPECIES_MATCH`、`PHASE_MISMATCH`、`TEMPERATURE_RANGE_ERROR`、`REACTION_NOT_BALANCED`、`NUMERICAL_ERROR`、`MODEL_NOT_APPLICABLE`、`UNKNOWN_MODEL`、`INTERNAL_ERROR`。

## 四维资格与计数

- `implementation_qualified`：真实实现、Schema、单位、错误、关系和5个准入样例通过；
- `data_qualified`：公式工具自动满足；数据工具必须通过数据库Repository并返回记录级溯源；
- `interface_qualified`：function名称、描述和parameters Schema有效且唯一；
- `scientific_validation_qualified`：至少3个正常及2个边界/失败验证通过。

只有四项均通过，`fully_eligible=true`。健康检查和工具清单分别报告：

```json
{
  "registered_count": 30,
  "qualified_executable_count": 30,
  "implementation_qualified_count": 30,
  "data_required_count": 14,
  "data_qualified_count": 0,
  "interface_qualified_count": 30,
  "fully_eligible_count": 16
}
```

这些值由注册中心实时计算，不得写死。当前14个数据必需型工具仍使用静态资产，因而不会出现在默认大模型工具清单中。

历史错误码在注册中心统一归一化，不要求 17 个旧模型同时重写。

## 自动验证

运行：

```powershell
python Tools/run_baseline_tests.py
```

测试包含原17个黄金种子回归、30工具资格测试、四维数据资格、function-tool契约、超过100个自动生成异常输入，以及三种实验模式的调用闭环。

黄金算例源文件：`Tools/benchmarks/golden_cases.json`。
