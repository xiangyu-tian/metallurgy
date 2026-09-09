'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const {
    buildProviderToolDefinitions,
    createProductionToolOrchestrator,
    rankToolCandidates,
    restrictToolsToScene,
    unsupportedNarrativeNumbers,
    validateToolArguments,
} = require('../tool-orchestration');

function tool(modelCode, category, description, properties, required = Object.keys(properties)) {
    return {
        type: 'function',
        tool_uid: `uid-${modelCode}`,
        catalog_id: `catalog-${modelCode}`,
        model_code: modelCode,
        model_name: `${modelCode}测试工具`,
        model_version: '2.3.1',
        category,
        formula_reference: `${modelCode} reference`,
        source_version: 'source-1',
        source_records: [{ dataset_id: `DS-${modelCode}`, version: '1.0' }],
        fully_eligible: true,
        function: {
            name: `metallurgy_${modelCode.toLowerCase()}`,
            description,
            parameters: {
                type: 'object',
                properties,
                required,
                additionalProperties: false,
            },
        },
    };
}

const unitTool = tool('A001', '通用数据与校验', '把摄氏温度换算为开尔文温度', {
    value: { type: 'number', description: '待换算数值；单位: °C' },
    source_unit: { type: 'string', enum: ['°C', 'K'], description: '源单位' },
    target_unit: { type: 'string', enum: ['°C', 'K'], description: '目标单位' },
});

const heatTool = tool('B003', '热力学与相平衡', '计算物种在两个温度之间的显热焓增量', {
    species: { type: 'string', description: '物种' },
    temperature_start: { type: 'number', description: '起始温度；单位: K' },
    temperature_end: { type: 'number', description: '终止温度；单位: K' },
});

const equilibriumTool = tool('B009', '热力学与相平衡', '根据反应Gibbs能计算平衡常数', {
    delta_g: { type: 'number', description: '反应Gibbs能；单位: J/mol' },
    temperature: { type: 'number', description: '温度；单位: K', default: 1873 },
}, ['delta_g', 'temperature']);

const alloyOptimizationTool = tool('D019', '转炉炼钢', '求最低成本多合金加入方案', {
    heat_mass_kg: { type: 'number', description: '初始钢液质量；单位: kg' },
    current_composition_wt_pct: { type: 'object', description: '当前钢液成分；单位: wt%' },
    targets: {
        type: 'array',
        description: '目标元素区间',
        items: {
            type: 'object',
            properties: {
                element: { type: 'string' },
                min_wt_pct: { type: 'number' },
                max_wt_pct: { type: 'number' },
            },
            required: ['element', 'min_wt_pct', 'max_wt_pct'],
            additionalProperties: false,
        },
    },
    alloys: {
        type: 'array',
        description: '候选合金',
        items: {
            type: 'object',
            properties: {
                name: { type: 'string' },
                cost_per_kg: { type: 'number' },
                min_addition_kg: { type: 'number' },
                max_addition_kg: { type: 'number' },
                composition_wt_pct: { type: 'object' },
                element_recovery_fractions: { type: 'object' },
                mass_retention_fraction: { type: 'number' },
            },
            required: [
                'name', 'cost_per_kg', 'min_addition_kg', 'max_addition_kg',
                'composition_wt_pct', 'element_recovery_fractions', 'mass_retention_fraction',
            ],
            additionalProperties: false,
        },
    },
    max_total_addition_kg: { type: 'number', description: '最大总加入量；单位: kg' },
});

const blowingScheduleTool = tool('D018', '转炉炼钢', '离线优化转炉分段供氧制度', {
    total_oxygen_nm3: { type: 'number', description: '总供氧量；单位: Nm3' },
    stages: {
        type: 'array',
        description: '分段制度',
        items: {
            type: 'object',
            properties: {
                name: { type: 'string' },
                oxygen_flow_nm3_min: { type: 'number' },
                duration_min_min: { type: 'number' },
                duration_max_min: { type: 'number' },
                preferred_oxygen_fraction: { type: 'number' },
                deviation_weight: { type: 'number' },
                lance_height_m: { type: 'number' },
                oxygen_utilization_fraction: { type: 'number' },
            },
            required: [
                'name', 'oxygen_flow_nm3_min', 'duration_min_min', 'duration_max_min',
                'preferred_oxygen_fraction', 'deviation_weight', 'lance_height_m',
                'oxygen_utilization_fraction',
            ],
            additionalProperties: false,
        },
    },
});

const steelYieldIronLossTool = tool('D022', '冶金工艺与物料衡算', '计算钢水质量收得率、铁回收率、损失构成和未计量铁', {
    charge_streams: { type: 'array', description: '铁源装入物流' },
    steel_mass_kg: { type: 'number', description: '出钢钢水质量；单位: kg' },
    steel_iron_mass_fraction: { type: 'number', description: '钢水铁质量分数；单位: 1' },
    loss_streams: { type: 'array', description: '已知铁损物流' },
});

function catalog(tools) {
    return {
        registered_count: 120,
        qualified_executable_count: 120,
        tools,
    };
}

test('Schema闸门报告缺失字段，只采用Schema默认值', () => {
    const missing = validateToolArguments({ value: 100 }, unitTool.function.parameters);
    assert.equal(missing.valid, false);
    assert.deepEqual(missing.errors.filter(item => item.keyword === 'required').map(item => item.field), [
        'source_unit',
        'target_unit',
    ]);

    const withDefault = validateToolArguments({ delta_g: -1000 }, equilibriumTool.function.parameters);
    assert.equal(withDefault.valid, true);
    assert.equal(withDefault.arguments.temperature, 1873);
    assert.deepEqual(withDefault.defaults_applied, [{ field: 'temperature', value: 1873 }]);
});

test('Schema闸门使用完整JSON Schema约束并返回可追问字段路径', () => {
    const schema = {
        type: 'object',
        properties: {
            stages: {
                type: 'array',
                minItems: 1,
                maxItems: 1,
                items: {
                    type: 'object',
                    properties: {
                        name: { type: 'string', pattern: '^[a-z]+$' },
                        oxygen_flow_nm3_min: { type: 'number', exclusiveMinimum: 0 },
                    },
                    required: ['name', 'oxygen_flow_nm3_min'],
                    additionalProperties: false,
                },
            },
            composition_wt_pct: {
                type: 'object',
                minProperties: 1,
                additionalProperties: { type: 'number', minimum: 0, maximum: 100 },
            },
        },
        required: ['stages', 'composition_wt_pct'],
        additionalProperties: false,
    };
    const result = validateToolArguments({
        stages: [
            { name: 'early-1', oxygen_flow_nm3_min: 0, invented: true },
            { name: 'finish', oxygen_flow_nm3_min: 15 },
        ],
        composition_wt_pct: { Mn: 101 },
    }, schema);

    assert.equal(result.valid, false);
    assert.ok(result.errors.some(item => item.keyword === 'maxItems' && item.field === 'stages'));
    assert.ok(result.errors.some(item => item.keyword === 'pattern' && item.field === 'stages[0].name'));
    assert.ok(result.errors.some(item => item.keyword === 'exclusiveMinimum' && item.field === 'stages[0].oxygen_flow_nm3_min'));
    assert.ok(result.errors.some(item => item.keyword === 'additionalProperties' && item.field === 'stages[0].invented'));
    assert.ok(result.errors.some(item => item.keyword === 'maximum' && item.field === 'composition_wt_pct.Mn'));
});

test('Schema默认值不覆盖用户显式空值，空值由对应约束准确拒绝', () => {
    const result = validateToolArguments({ label: '' }, {
        type: 'object',
        properties: { label: { type: 'string', minLength: 1, default: 'default-label' } },
        required: ['label'],
        additionalProperties: false,
    });

    assert.equal(result.valid, false);
    assert.equal(result.arguments.label, '');
    assert.deepEqual(result.defaults_applied, []);
    assert.ok(result.errors.some(item => item.keyword === 'minLength' && item.field === 'label'));
});

test('供应商strict仅在不改变参数结构时启用，不兼容契约回退应用侧校验', () => {
    const strictCompatible = buildProviderToolDefinitions([unitTool], {
        provider: 'deepseek',
        strictRequested: true,
        endpointStrictCapable: true,
    });
    assert.equal(strictCompatible.definitions[0].function.strict, true);
    assert.equal(strictCompatible.reports[0].strict_enabled, true);

    const dynamicMapTool = tool('D199', '转炉炼钢', '动态元素映射', {
        composition: {
            type: 'object',
            minProperties: 1,
            additionalProperties: { type: 'number', minimum: 0, maximum: 1 },
        },
    });
    const fallback = buildProviderToolDefinitions([dynamicMapTool], {
        provider: 'deepseek',
        strictRequested: true,
        endpointStrictCapable: true,
    });
    assert.equal(fallback.definitions[0].function.strict, undefined);
    assert.equal(fallback.reports[0].strict_enabled, false);
    assert.equal(fallback.reports[0].fallback, 'application_json_schema_validation');
    assert.ok(fallback.reports[0].incompatibilities.some(item => item.reason === 'additionalProperties_must_be_false'));
    assert.deepEqual(fallback.definitions[0].function.parameters.properties.composition.additionalProperties, {
        type: 'number', minimum: 0, maximum: 1,
    });
});

test('工具答案允许有精度依据的舍入，但拒绝篡改值和新派生值', () => {
    const evidence = { result: { addition_kg: 7.04225352112676, total_cost: 14.08450704225352 }, target: [1, 1.1] };

    assert.deepEqual(unsupportedNarrativeNumbers('加入7.04 kg，成本14.08元。', evidence), [7.04, 14.08]);
    assert.deepEqual(unsupportedNarrativeNumbers('加入7.04 kg，成本14.08元。', evidence, { allowRounding: true }), []);
    assert.deepEqual(unsupportedNarrativeNumbers('温度约2395 K。', { raft_temperature_k: 2395.454565412365 }, { allowRounding: true }), []);
    assert.deepEqual(unsupportedNarrativeNumbers('温度约2450 K。', { raft_temperature_k: 2395.454565412365 }, { allowRounding: true }), [2450]);
    assert.deepEqual(unsupportedNarrativeNumbers('加入7.4 kg，目标中值1.05。', evidence, { allowRounding: true }), [7.4, 1.05]);
    assert.deepEqual(unsupportedNarrativeNumbers('平衡常数为1000000000000。', { input: '1×10^12' }), []);
});

test('工具答案允许比例以百分数表达，但不把普通放大数值视为等价', () => {
    const evidence = {
        steel_mass_yield_fraction: 0.92,
        iron_recovery_fraction: 0.9697033898305085,
        known_loss_fraction_of_input_iron: 0.023834745762711863,
        unaccounted_fraction_of_input_iron: 0.006461864406779661,
    };

    assert.deepEqual(
        unsupportedNarrativeNumbers(
            '钢水收得率92%，铁回收率96.97%，已知铁损率2.38%，未计量铁率0.65%。',
            evidence,
            { allowRounding: true },
        ),
        [],
    );
    assert.deepEqual(
        unsupportedNarrativeNumbers('钢水收得率被写成普通数值92。', evidence, { allowRounding: true }),
        [92],
    );
    const intervalEvidence = { failure_probability_wilson_95: [0.41618039421813385, 0.5376375990518288] };
    assert.deepEqual(
        unsupportedNarrativeNumbers('95%置信区间约为41.6%～53.8。', intervalEvidence, { allowRounding: true }),
        [],
    );
    assert.deepEqual(
        unsupportedNarrativeNumbers('95%置信区间约为41.6～53.8%。', intervalEvidence, { allowRounding: true }),
        [],
    );
});

test('候选召回受场景约束且按自然语言相关性排序', () => {
    const all = [unitTool, heatTool, equilibriumTool];
    assert.deepEqual(
        restrictToolsToScene(all, 'thermodynamics').map(item => item.model_code),
        ['B003', 'B009'],
    );
    const ranked = rankToolCandidates(all, '请计算铁物种从300K到1800K的显热', 'thermodynamics', 2);
    assert.equal(ranked[0].model_code, 'B003');
    assert.ok(ranked.every(item => item.category === '热力学与相平衡'));
});

test('转炉场景不会排除冶金工艺与物料衡算类别的专用工具', () => {
    const candidates = restrictToolsToScene(
        [unitTool, alloyOptimizationTool, steelYieldIronLossTool],
        'converter',
    );

    assert.deepEqual(candidates.map(item => item.model_code), ['D019', 'D022']);
});

test('强制模式参数不足时追问且绝不触发底层执行', async () => {
    let executeCount = 0;
    const modelCalls = [
        {
            tool_calls: [{
                id: 'call-missing',
                type: 'function',
                function: { name: unitTool.function.name, arguments: JSON.stringify({ value: 100 }) },
            }],
        },
    ];
    const orchestrator = createProductionToolOrchestrator({
        fetchCatalog: async () => catalog([unitTool, heatTool]),
        callModel: async () => modelCalls.shift(),
        executeToolCall: async () => {
            executeCount += 1;
            throw new Error('不应执行');
        },
        modelName: 'mock-llm',
    });

    const result = await orchestrator.run('把100换算一下', [], {
        mode: 'forced',
        forced_tool: 'A001',
    });
    assert.equal(executeCount, 0);
    assert.equal(result.status, 'needs_clarification');
    assert.equal(result.lifecycle, 'waiting_for_user_input');
    assert.equal(result.clarification.required, true);
    assert.deepEqual(result.clarification.fields.map(item => item.field), ['source_unit', 'target_unit']);
    assert.match(result.answer, /不会猜测/);
    assert.equal(result.tool_calls[0].execution_id, null);
});

test('强制工具模式保留追问能力，不用API级tool_choice迫使模型猜参', async () => {
    let receivedToolChoice = null;
    const orchestrator = createProductionToolOrchestrator({
        fetchCatalog: async () => catalog([unitTool]),
        callModel: async (messages, options) => {
            receivedToolChoice = options.tool_choice;
            return { content: '请补充源单位和目标单位；我不会猜测。' };
        },
        executeToolCall: async () => { throw new Error('参数不足时不应执行'); },
    });

    const result = await orchestrator.run('把100换算一下', [], {
        mode: 'forced',
        forced_tool: 'A001',
    });

    assert.equal(receivedToolChoice, 'auto');
    assert.equal(result.status, 'needs_clarification');
    assert.equal(result.successful_tool_call_count, 0);
    assert.match(result.answer, /补充源单位和目标单位/);
});

test('模型造成的可修复Schema错误回传模型一次，修正后才执行工具', async () => {
    const modelCalls = [
        { tool_calls: [{
            id: 'repair-1', type: 'function',
            function: { name: unitTool.function.name, arguments: JSON.stringify({ value: '100', source_unit: '°C', target_unit: 'K' }) },
        }] },
        { tool_calls: [{
            id: 'repair-2', type: 'function',
            function: { name: unitTool.function.name, arguments: JSON.stringify({ value: 100, source_unit: '°C', target_unit: 'K' }) },
        }] },
        { content: '换算结果为373.15 K。' },
    ];
    let sawRepairFeedback = false;
    let executeCount = 0;
    const orchestrator = createProductionToolOrchestrator({
        fetchCatalog: async () => catalog([unitTool]),
        callModel: async (messages) => {
            sawRepairFeedback = sawRepairFeedback || messages.some(item =>
                item.role === 'tool' && item.content.includes('SCHEMA_REPAIR_REQUESTED')
            );
            return modelCalls.shift();
        },
        executeToolCall: async toolCall => {
            executeCount += 1;
            return {
                call_id: toolCall.id,
                function_name: toolCall.function.name,
                model_code: 'A001',
                model_version: '2.3.1',
                status: 'success',
                execution_id: 'EXEC-REPAIR-001',
                output: { value: 373.15, unit: 'K' },
                actual_data_records: unitTool.source_records,
            };
        },
        unsupportedNumbers: () => [],
    });

    const result = await orchestrator.run('把100摄氏度换算成开尔文', [], {
        mode: 'forced', forced_tool: 'A001',
    });
    assert.equal(sawRepairFeedback, true);
    assert.equal(executeCount, 1);
    assert.equal(result.status, 'success');
    assert.equal(result.successful_tool_call_count, 1);
    assert.equal(result.tool_calls[0].error_code, 'SCHEMA_REPAIR_REQUESTED');
    assert.equal(result.tool_calls[1].execution_id, 'EXEC-REPAIR-001');
});

test('同一工具Schema错误二次失败后停止并追问，不循环也不执行', async () => {
    const invalidCall = id => ({ tool_calls: [{
        id, type: 'function',
        function: { name: unitTool.function.name, arguments: JSON.stringify({ value: '100', source_unit: '°C', target_unit: 'K' }) },
    }] });
    const modelCalls = [invalidCall('repair-failed-1'), invalidCall('repair-failed-2')];
    let executeCount = 0;
    const orchestrator = createProductionToolOrchestrator({
        fetchCatalog: async () => catalog([unitTool]),
        callModel: async () => modelCalls.shift(),
        executeToolCall: async () => { executeCount += 1; },
    });

    const result = await orchestrator.run('把100摄氏度换算成开尔文', [], {
        mode: 'forced', forced_tool: 'A001',
    });
    assert.equal(executeCount, 0);
    assert.equal(result.status, 'needs_clarification');
    assert.equal(result.clarification.fields[0].field, 'value');
    assert.equal(result.clarification.fields[0].issue, 'type');
});

test('元工具目标代码受本轮候选集约束，错误别名在执行前修正', async () => {
    const lookupTool = tool('G008', '数值仿真与工具编排', '对规则表执行线性插值', {
        query_x: { type: 'number' },
    });
    const monteCarloTool = tool('G010', '数值仿真与工具编排', '对注册目标工具执行蒙特卡洛传播', {
        target_model_code: { type: 'string', description: '目标注册工具代码' },
        base_arguments: { type: 'object', additionalProperties: true },
        output_path: { type: 'string' },
    });
    const modelCalls = [
        { content: JSON.stringify({ needs_tool: true, candidate_model_codes: ['G010', 'G008'], reason: '对规则表插值做不确定度传播' }) },
        { tool_calls: [{
            id: 'meta-invalid-target', type: 'function',
            function: { name: monteCarloTool.function.name, arguments: JSON.stringify({
                target_model_code: 'interpolate_lookup_table',
                base_arguments: { query_x: 0.5 },
                output_path: 'interpolated_value',
            }) },
        }] },
        { tool_calls: [{
            id: 'meta-valid-target', type: 'function',
            function: { name: monteCarloTool.function.name, arguments: JSON.stringify({
                target_model_code: 'G008',
                base_arguments: { query_x: 0.5 },
                output_path: 'interpolated_value',
            }) },
        }] },
        { content: '传播计算完成。' },
    ];
    const executedTargetCodes = [];
    const orchestrator = createProductionToolOrchestrator({
        fetchCatalog: async () => catalog([monteCarloTool, lookupTool]),
        callModel: async () => modelCalls.shift(),
        executeToolCall: async (toolCall) => {
            const argumentsValue = JSON.parse(toolCall.function.arguments);
            executedTargetCodes.push(argumentsValue.target_model_code);
            return {
                call_id: toolCall.id,
                function_name: toolCall.function.name,
                model_code: monteCarloTool.model_code,
                model_version: monteCarloTool.model_version,
                status: 'success',
                execution_id: 'EXEC-META-001',
                output: { estimated_failure_probability: 0.5 },
                actual_data_records: monteCarloTool.source_records,
            };
        },
        unsupportedNumbers: () => [],
    });

    const result = await orchestrator.run('对规则表插值结果执行蒙特卡洛传播', [], {
        mode: 'auto',
        scene: 'simulation',
    });

    assert.deepEqual(executedTargetCodes, ['G008']);
    assert.equal(result.successful_tool_call_count, 1);
    assert.equal(result.tool_calls[0].error_code, 'SCHEMA_REPAIR_REQUESTED');
    assert.equal(result.tool_calls[1].arguments.target_model_code, 'G008');
});

test('元工具基准参数继承唯一目标Schema，不确定参数占位缺失可受控修正', async () => {
    const lookupTool = tool('G008', '数值仿真与工具编排', '对规则表执行线性插值', {
        table_id: { type: 'string' },
        query_x: { type: 'number' },
    });
    const monteCarloTool = tool('G010', '数值仿真与工具编排', '对注册目标工具执行蒙特卡洛传播', {
        target_model_code: { type: 'string', description: '目标注册工具代码' },
        base_arguments: { type: 'object', additionalProperties: true },
        output_path: { type: 'string' },
        uncertain_parameters: {
            type: 'array',
            items: {
                type: 'object',
                additionalProperties: false,
                properties: { path: { type: 'string' } },
                required: ['path'],
            },
        },
    });
    const modelCalls = [
        { content: JSON.stringify({ needs_tool: true, candidate_model_codes: ['G010', 'G008'], reason: '传播规则表查询坐标的不确定度' }) },
        { tool_calls: [{
            id: 'meta-missing-placeholder', type: 'function',
            function: { name: monteCarloTool.function.name, arguments: JSON.stringify({
                target_model_code: 'G008',
                base_arguments: { table_id: 'rule-table' },
                output_path: 'interpolated_value',
                uncertain_parameters: [{ path: 'query_x' }],
            }) },
        }] },
        { tool_calls: [{
            id: 'meta-repaired-placeholder', type: 'function',
            function: { name: monteCarloTool.function.name, arguments: JSON.stringify({
                target_model_code: 'G008',
                base_arguments: { table_id: 'rule-table', query_x: 0.5 },
                output_path: 'interpolated_value',
                uncertain_parameters: [{ path: 'query_x' }],
            }) },
        }] },
        { content: '传播计算完成。' },
    ];
    const executedArguments = [];
    const orchestrator = createProductionToolOrchestrator({
        fetchCatalog: async () => catalog([monteCarloTool, lookupTool]),
        callModel: async () => modelCalls.shift(),
        executeToolCall: async (toolCall) => {
            const argumentsValue = JSON.parse(toolCall.function.arguments);
            executedArguments.push(argumentsValue);
            return {
                call_id: toolCall.id,
                function_name: toolCall.function.name,
                model_code: monteCarloTool.model_code,
                model_version: monteCarloTool.model_version,
                status: 'success',
                execution_id: 'EXEC-META-BASE-001',
                output: { estimated_failure_probability: 0.5 },
                actual_data_records: monteCarloTool.source_records,
            };
        },
        unsupportedNumbers: () => [],
    });

    const result = await orchestrator.run('传播query_x在0到1之间的不确定度', [], {
        mode: 'auto',
        scene: 'simulation',
    });

    assert.equal(executedArguments.length, 1);
    assert.equal(executedArguments[0].base_arguments.query_x, 0.5);
    assert.equal(result.tool_calls[0].error_code, 'SCHEMA_REPAIR_REQUESTED');
    assert.equal(result.successful_tool_call_count, 1);
});

test('元工具不确定参数路径受目标Schema约束，base_arguments前缀在执行前修正', async () => {
    const lookupTool = tool('G008', '数值仿真与工具编排', '对规则表执行线性插值', {
        table_id: { type: 'string' },
        query_x: { type: 'number' },
    });
    const monteCarloTool = tool('G010', '数值仿真与工具编排', '对注册目标工具执行蒙特卡洛传播', {
        target_model_code: { type: 'string', description: '目标注册工具代码' },
        base_arguments: { type: 'object', additionalProperties: true },
        output_path: { type: 'string' },
        uncertain_parameters: {
            type: 'array',
            items: {
                type: 'object',
                additionalProperties: false,
                properties: { path: { type: 'string' } },
                required: ['path'],
            },
        },
    });
    const modelCalls = [
        { content: JSON.stringify({ needs_tool: true, candidate_model_codes: ['G010', 'G008'], reason: '传播规则表查询坐标的不确定度' }) },
        { tool_calls: [{
            id: 'meta-prefixed-path', type: 'function',
            function: { name: monteCarloTool.function.name, arguments: JSON.stringify({
                target_model_code: 'G008',
                base_arguments: { table_id: 'rule-table', query_x: 0.5 },
                output_path: 'interpolated_value',
                uncertain_parameters: [{ path: 'base_arguments.query_x' }],
            }) },
        }] },
        { tool_calls: [{
            id: 'meta-relative-path', type: 'function',
            function: { name: monteCarloTool.function.name, arguments: JSON.stringify({
                target_model_code: 'G008',
                base_arguments: { table_id: 'rule-table', query_x: 0.5 },
                output_path: 'interpolated_value',
                uncertain_parameters: [{ path: 'query_x' }],
            }) },
        }] },
        { content: '传播计算完成。' },
    ];
    const executedPaths = [];
    const orchestrator = createProductionToolOrchestrator({
        fetchCatalog: async () => catalog([monteCarloTool, lookupTool]),
        callModel: async () => modelCalls.shift(),
        executeToolCall: async (toolCall) => {
            const argumentsValue = JSON.parse(toolCall.function.arguments);
            executedPaths.push(argumentsValue.uncertain_parameters[0].path);
            return {
                call_id: toolCall.id,
                function_name: toolCall.function.name,
                model_code: monteCarloTool.model_code,
                model_version: monteCarloTool.model_version,
                status: 'success',
                execution_id: 'EXEC-META-PATH-001',
                output: { estimated_failure_probability: 0.5 },
                actual_data_records: monteCarloTool.source_records,
            };
        },
        unsupportedNumbers: () => [],
    });

    const result = await orchestrator.run('传播query_x在0到1之间的不确定度', [], {
        mode: 'auto',
        scene: 'simulation',
    });

    assert.deepEqual(executedPaths, ['query_x']);
    assert.equal(result.tool_calls[0].error_code, 'SCHEMA_REPAIR_REQUESTED');
    assert.equal(result.tool_calls[1].arguments.uncertain_parameters[0].path, 'query_x');
    assert.equal(result.successful_tool_call_count, 1);
});

test('自动模式先筛候选、再执行一个工具、最后把结果回传模型并绑定证据', async () => {
    const modelCalls = [
        { content: JSON.stringify({ needs_tool: true, inferred_scene: 'general', candidate_model_codes: ['A001'], reason: '问题是单位换算' }) },
        {
            tool_calls: [{
                id: 'call-auto',
                type: 'function',
                function: {
                    name: unitTool.function.name,
                    arguments: JSON.stringify({ value: 100, source_unit: '°C', target_unit: 'K' }),
                },
            }],
        },
        { content: '换算结果为373.15 K，来自A001，执行 ID 为 EXEC-AUTO-001。' },
    ];
    let toolResultWasReturned = false;
    const orchestrator = createProductionToolOrchestrator({
        fetchCatalog: async () => catalog([unitTool, heatTool]),
        callModel: async (messages) => {
            toolResultWasReturned = toolResultWasReturned || messages.some(item => item.role === 'tool' && item.content.includes('373.15'));
            return modelCalls.shift();
        },
        executeToolCall: async (toolCall) => ({
            call_id: toolCall.id,
            function_name: toolCall.function.name,
            model_code: 'A001',
            model_version: '2.3.1',
            status: 'success',
            execution_id: 'EXEC-AUTO-001',
            trace_id: 'TRACE-AUTO-001',
            output: { value: 373.15, unit: 'K' },
            actual_data_records: [{ dataset_id: 'DS-A001', version: '1.0', record_id: 'unit-rule' }],
        }),
        unsupportedNumbers: () => [],
        modelName: 'mock-llm',
    });

    const result = await orchestrator.run('把100摄氏度换算成开尔文', [], { mode: 'auto' });
    assert.equal(result.status, 'success');
    assert.equal(result.candidate_selection.source_tool_count, 2);
    assert.equal(result.candidate_selection.exposed_tool_count, 1);
    assert.equal(result.tool_call_count, 1);
    assert.equal(result.successful_tool_call_count, 1);
    assert.equal(toolResultWasReturned, true);
    assert.equal(result.answer_bindings[0].execution_id, 'EXEC-AUTO-001');
    assert.equal(result.answer_bindings[0].tool_version, '2.3.1');
    assert.deepEqual(result.answer_bindings[0].parameters, { value: 100, source_unit: '°C', target_unit: 'K' });
    assert.deepEqual(result.answer_bindings[0].parameter_sources, {
        value: { source: 'user_input', verified: true },
        source_unit: { source: 'user_input', verified: true },
        target_unit: { source: 'user_input', verified: true },
    });
    assert.match(result.answer, /EXEC-AUTO-001/);
    assert.match(result.answer, /DS-A001/);
    assert.match(result.product_view.content, /373\.15 K/);
    assert.doesNotMatch(result.product_view.content, /EXEC-|DS-A001|A001/);
    assert.equal(result.tool_contract.local_validator, 'ajv-8');
    assert.equal(result.tool_contract.strict_requested, false);
    assert.equal(result.tool_contract.application_validated_count, 1);
});

test('数值安全兜底只向产品视图返回结果，不泄露工具和执行轨迹', async () => {
    const modelCalls = [
        { tool_calls: [{
            id: 'fallback-call',
            type: 'function',
            function: { name: unitTool.function.name, arguments: JSON.stringify({ value: 100, source_unit: '°C', target_unit: 'K' }) },
        }] },
        { content: '错误地总结成了999 K。' },
        { content: '换算结果为 373.15 K。' },
    ];
    let retryPayload = null;
    const orchestrator = createProductionToolOrchestrator({
        fetchCatalog: async () => catalog([unitTool]),
        callModel: async (messages) => {
            if (modelCalls.length === 1) retryPayload = JSON.parse(messages.at(-1).content);
            return modelCalls.shift();
        },
        executeToolCall: async toolCall => ({
            call_id: toolCall.id,
            function_name: toolCall.function.name,
            model_code: 'A001',
            model_version: '2.3.1',
            status: 'success',
            execution_id: 'EXEC-FALLBACK-001',
            output: { value: 373.15, unit: 'K' },
            actual_data_records: unitTool.source_records,
        }),
        unsupportedNumbers: narrative => narrative.includes('999') ? ['999'] : [],
    });

    const result = await orchestrator.run('把100摄氏度换算成开尔文', [], { mode: 'forced', forced_tool: 'A001' });

    assert.equal(result.answer_mode, 'tool_grounded_retry');
    assert.equal(result.product_view.content, '换算结果为 373.15 K。');
    assert.doesNotMatch(result.product_view.content, /```json|\{/);
    assert.doesNotMatch(result.product_view.content, /EXEC-|A001|tool|工具/);
    assert.match(result.answer, /EXEC-FALLBACK-001/);
    assert.doesNotMatch(retryPayload.question, /100/);
    assert.match(retryPayload.question, /输入数值/);
});

test('受约束重写仍失败时返回可读字段摘要而不是JSON', async () => {
    let modelCallIndex = 0;
    const orchestrator = createProductionToolOrchestrator({
        fetchCatalog: async () => catalog([unitTool]),
        callModel: async () => {
            modelCallIndex += 1;
            if (modelCallIndex === 1) {
                return { tool_calls: [{
                    id: 'readable-fallback-call',
                    type: 'function',
                    function: { name: unitTool.function.name, arguments: JSON.stringify({ value: 100, source_unit: '°C', target_unit: 'K' }) },
                }] };
            }
            if (modelCallIndex === 2) return { content: '错误地总结成了999 K。' };
            throw new Error('受约束重写服务不可用');
        },
        executeToolCall: async toolCall => ({
            call_id: toolCall.id,
            function_name: toolCall.function.name,
            model_code: 'A001',
            model_version: '2.3.1',
            status: 'success',
            execution_id: 'EXEC-READABLE-001',
            output: { value: 373.15, source_unit: '°C', target_unit: 'K' },
            actual_data_records: unitTool.source_records,
        }),
        unsupportedNumbers: narrative => narrative.includes('999') ? ['999'] : [],
    });

    const result = await orchestrator.run('把100摄氏度换算成开尔文', [], { mode: 'forced', forced_tool: 'A001' });

    assert.equal(result.answer_mode, 'readable_tool_fallback');
    assert.match(result.product_view.content, /value：373\.15/);
    assert.doesNotMatch(result.product_view.content, /```|\{|\}/);
    assert.equal(result.grounding.synthesis_retry.attempted, true);
    assert.equal(result.grounding.synthesis_retry.succeeded, false);
});

test('受约束重写只含局部无依据数字时删除对应分句并保留自然语言结果', async () => {
    const modelCalls = [
        { tool_calls: [{
            id: 'pruned-retry-call',
            type: 'function',
            function: { name: unitTool.function.name, arguments: JSON.stringify({ value: 100, source_unit: '°C', target_unit: 'K' }) },
        }] },
        { content: '换算结果为373.15 K，但错误补充为999 K。' },
        { content: '换算结果为373.15 K，每50单位会额外增加999单位。' },
    ];
    const orchestrator = createProductionToolOrchestrator({
        fetchCatalog: async () => catalog([unitTool]),
        callModel: async () => modelCalls.shift(),
        executeToolCall: async toolCall => ({
            call_id: toolCall.id,
            function_name: toolCall.function.name,
            model_code: 'A001',
            model_version: '2.3.1',
            status: 'success',
            execution_id: 'EXEC-PRUNE-001',
            output: { value: 373.15, unit: 'K' },
            actual_data_records: unitTool.source_records,
        }),
        unsupportedNumbers: (narrative, evidence) => unsupportedNarrativeNumbers(
            narrative,
            evidence,
            { allowRounding: true },
        ),
    });

    const result = await orchestrator.run('执行温度换算', [], { mode: 'forced', forced_tool: 'A001' });

    assert.equal(result.answer_mode, 'tool_grounded_retry_pruned');
    assert.match(result.product_view.content, /373\.15 K/);
    assert.doesNotMatch(result.product_view.content, /50|999/);
    assert.deepEqual(result.grounding.unsupported_numeric_values, []);
    assert.equal(result.grounding.synthesis_retry.succeeded, true);
    assert.equal(result.grounding.synthesis_retry.pruned, true);
});

test('多工具规划模式记录依赖计划并允许按计划执行多个候选', async () => {
    const modelCalls = [
        { content: JSON.stringify({ needs_tool: true, candidate_model_codes: ['B003', 'B009'], reason: '先算热力学量再求平衡' }) },
        { content: JSON.stringify({ objective: '得到平衡常数', reason: 'B009依赖前序热力学结果', steps: [
            { step_id: 'S1', function_name: heatTool.function.name, purpose: '计算显热', depends_on: [] },
            { step_id: 'S2', function_name: equilibriumTool.function.name, purpose: '计算平衡常数', depends_on: ['S1'] },
        ] }) },
        { tool_calls: [
            { id: 'call-b003', type: 'function', function: { name: heatTool.function.name, arguments: JSON.stringify({ species: 'Fe', temperature_start: 300, temperature_end: 1800 }) } },
        ] },
        { tool_calls: [
            { id: 'call-b009', type: 'function', function: { name: equilibriumTool.function.name, arguments: JSON.stringify({ delta_g: -12000, temperature: 1800 }) } },
        ] },
        { content: '组合计算完成。' },
    ];
    let executionIndex = 0;
    const orchestrator = createProductionToolOrchestrator({
        fetchCatalog: async () => catalog([unitTool, heatTool, equilibriumTool]),
        callModel: async () => modelCalls.shift(),
        executeToolCall: async (toolCall) => {
            executionIndex += 1;
            const metadata = toolCall.function.name === heatTool.function.name ? heatTool : equilibriumTool;
            return {
                call_id: toolCall.id,
                function_name: toolCall.function.name,
                model_code: metadata.model_code,
                model_version: metadata.model_version,
                status: 'success',
                execution_id: `EXEC-PLAN-00${executionIndex}`,
                trace_id: 'TRACE-PLAN',
                output: executionIndex === 1 ? { enthalpy: 12000, delta_g: -12000 } : { equilibrium_constant: 2.23 },
                actual_data_records: metadata.source_records,
            };
        },
        unsupportedNumbers: () => [],
        modelName: 'mock-llm',
    });

    const result = await orchestrator.run('先计算Fe从300 K到1800 K的显热，再把工具得到的delta_g在1800 K分析平衡常数', [], {
        mode: 'plan',
        scene: 'thermodynamics',
        max_tool_calls: 4,
    });
    assert.equal(result.plan.status, 'planned');
    assert.deepEqual(result.plan.steps[1].depends_on, ['S1']);
    assert.equal(result.successful_tool_call_count, 2);
    assert.deepEqual(result.tool_calls.map(item => item.planned_step_id), ['S1', 'S2']);
    assert.deepEqual(result.answer_bindings.map(item => item.execution_id), ['EXEC-PLAN-001', 'EXEC-PLAN-002']);
});

test('多工具计划将上游完整对象数组确定性绑定到下游，避免模型截断曲线', async () => {
    const shellTool = tool('F005', '凝固与连铸', '计算中心固相率时间历史', {
        duration_s: { type: 'number', description: '计算时长；单位: s' },
    });
    const endpointTool = tool('F006', '凝固与连铸', '根据中心固相率曲线预测凝固终点', {
        upstream_execution_id: { type: 'string', description: '上游真实执行ID' },
        center_solid_fraction_curve: {
            type: 'array',
            minItems: 2,
            maxItems: 2001,
            items: {
                type: 'object',
                additionalProperties: false,
                properties: {
                    time_s: { type: 'number' },
                    center_solid_fraction: { type: 'number', minimum: 0, maximum: 1 },
                },
                required: ['time_s', 'center_solid_fraction'],
            },
        },
    });
    const fullHistory = [
        { time_s: 0, center_solid_fraction: 0, center_temperature_k: 1750 },
        { time_s: 2.5, center_solid_fraction: 0.48, center_temperature_k: 1680 },
        { time_s: 3, center_solid_fraction: 0.824, center_temperature_k: 1600 },
        { time_s: 3.5, center_solid_fraction: 1, center_temperature_k: 1550 },
        { time_s: 10, center_solid_fraction: 1, center_temperature_k: 1516 },
    ];
    const truncatedCurve = fullHistory.slice(0, 4).map(({ time_s, center_solid_fraction }) => ({
        time_s, center_solid_fraction,
    }));
    const modelCalls = [
        { content: JSON.stringify({ needs_tool: true, candidate_model_codes: ['F005', 'F006'], reason: '先计算曲线再定位终点' }) },
        { content: JSON.stringify({ objective: '预测凝固终点', steps: [
            { step_id: 'S1', function_name: shellTool.function.name, purpose: '计算曲线', depends_on: [] },
            { step_id: 'S2', function_name: endpointTool.function.name, purpose: '预测终点', depends_on: ['S1'] },
        ] }) },
        { tool_calls: [{ id: 'shell-call', type: 'function', function: { name: shellTool.function.name, arguments: JSON.stringify({ duration_s: 10 }) } }] },
        { tool_calls: [{ id: 'endpoint-call', type: 'function', function: { name: endpointTool.function.name, arguments: JSON.stringify({
            upstream_execution_id: 'EXEC-MODEL-GUESSED',
            center_solid_fraction_curve: truncatedCurve,
        }) } }] },
        { content: '凝固终点计算完成。' },
    ];
    let downstreamArguments = null;
    const orchestrator = createProductionToolOrchestrator({
        fetchCatalog: async () => catalog([shellTool, endpointTool]),
        callModel: async () => modelCalls.shift(),
        executeToolCall: async (toolCall) => {
            const args = JSON.parse(toolCall.function.arguments);
            if (toolCall.function.name === shellTool.function.name) {
                return {
                    call_id: toolCall.id,
                    function_name: toolCall.function.name,
                    model_code: shellTool.model_code,
                    model_version: shellTool.model_version,
                    status: 'success',
                    execution_id: 'EXEC-F005-REAL',
                    output: { time_history: fullHistory },
                    actual_data_records: shellTool.source_records,
                };
            }
            downstreamArguments = args;
            const covered = args.center_solid_fraction_curve.at(-1)?.time_s >= 10;
            return {
                call_id: toolCall.id,
                function_name: toolCall.function.name,
                model_code: endpointTool.model_code,
                model_version: endpointTool.model_version,
                status: covered ? 'success' : 'failed',
                error_code: covered ? null : 'MISSING_DATA',
                error: covered ? null : '中心固相率曲线未覆盖设备出口时刻',
                execution_id: 'EXEC-F006-REAL',
                output: covered ? { solidification_end_position_m: 0.0593 } : null,
                actual_data_records: endpointTool.source_records,
            };
        },
        unsupportedNumbers: () => [],
    });

    const result = await orchestrator.run('先计算10秒中心固相率曲线，再用真实结果预测凝固终点', [], {
        mode: 'plan',
        scene: 'casting',
        max_tool_calls: 4,
    });

    assert.equal(result.successful_tool_call_count, 2);
    assert.equal(downstreamArguments.upstream_execution_id, 'EXEC-F005-REAL');
    assert.deepEqual(downstreamArguments.center_solid_fraction_curve, fullHistory.map(
        ({ time_s, center_solid_fraction }) => ({ time_s, center_solid_fraction }),
    ));
    assert.deepEqual(result.tool_calls[1].dependency_bindings.map(item => item.field), [
        'upstream_execution_id',
        'center_solid_fraction_curve',
    ]);
});

test('规划依赖在同轮提前调用时被延后，避免模型猜测上游结果', async () => {
    const modelCalls = [
        { content: JSON.stringify({ needs_tool: true, candidate_model_codes: ['B003', 'B009'], reason: '需要两步计算' }) },
        { content: JSON.stringify({ objective: '得到平衡常数', steps: [
            { step_id: 'S1', function_name: heatTool.function.name, purpose: '计算显热', depends_on: [] },
            { step_id: 'S2', function_name: equilibriumTool.function.name, purpose: '计算平衡常数', depends_on: ['S1'] },
        ] }) },
        { tool_calls: [
            { id: 'early-s1', type: 'function', function: { name: heatTool.function.name, arguments: JSON.stringify({ species: 'Fe', temperature_start: 300, temperature_end: 1800 }) } },
            { id: 'early-s2', type: 'function', function: { name: equilibriumTool.function.name, arguments: JSON.stringify({ delta_g: -99999, temperature: 1800 }) } },
        ] },
        { content: '请基于已回传的上游结果继续。' },
    ];
    const executed = [];
    const orchestrator = createProductionToolOrchestrator({
        fetchCatalog: async () => catalog([heatTool, equilibriumTool]),
        callModel: async () => modelCalls.shift(),
        executeToolCall: async (toolCall) => {
            executed.push(toolCall.function.name);
            return {
                call_id: toolCall.id,
                function_name: toolCall.function.name,
                model_code: 'B003',
                model_version: '2.3.1',
                status: 'success',
                execution_id: 'EXEC-DEPENDENCY-001',
                output: { enthalpy: 12000 },
                actual_data_records: heatTool.source_records,
            };
        },
        unsupportedNumbers: () => [],
    });

    const result = await orchestrator.run('分两步计算：Fe从300 K到1800 K的显热，然后用delta_g=-99999 J/mol和1800 K求平衡常数', [], { mode: 'plan', max_tool_calls: 4 });
    assert.deepEqual(executed, [heatTool.function.name]);
    const deferred = result.tool_calls.find(item => item.call_id === 'early-s2');
    assert.equal(deferred.status, 'deferred');
    assert.equal(deferred.error_code, 'DEPENDENCY_RESULT_REQUIRED');
    assert.equal(deferred.execution_id, null);
});

test('research_full是显式开关，生产模式默认仅暴露候选集', async () => {
    const productionToolCounts = [];
    const productionModelCalls = [
        { content: JSON.stringify({ needs_tool: true, candidate_model_codes: ['A001'], reason: '单位换算' }) },
        { content: '请补充具体数值。' },
    ];
    const production = createProductionToolOrchestrator({
        fetchCatalog: async () => catalog([unitTool, heatTool, equilibriumTool]),
        callModel: async (messages, options) => {
            if (options.tools) productionToolCounts.push(options.tools.length);
            return productionModelCalls.shift();
        },
        executeToolCall: async () => { throw new Error('不应执行'); },
    });
    await production.run('单位换算', [], { mode: 'auto' });
    assert.deepEqual(productionToolCounts, [1]);

    const researchToolCounts = [];
    const research = createProductionToolOrchestrator({
        fetchCatalog: async () => catalog([unitTool, heatTool, equilibriumTool]),
        callModel: async (messages, options) => {
            if (options.tools) researchToolCounts.push(options.tools.length);
            return { content: '研究模式已加载全量工具索引。' };
        },
        executeToolCall: async () => { throw new Error('不应执行'); },
    });
    const result = await research.run('研究工具暴露规模', [], { mode: 'auto', catalog_mode: 'research_full' });
    assert.deepEqual(researchToolCounts, [3]);
    assert.equal(result.candidate_selection.method, 'research_full');
    assert.equal(result.registry.exposed_tool_count, 3);
});

test('生产模式隔离嵌套契约未收口工具，research_full仍保留全量研究能力', async () => {
    const incompleteTool = {
        ...heatTool,
        model_code: 'B199',
        input_contract: { status: 'underspecified_nested_schema', gaps: ['$.streams[]'] },
        function: { ...heatTool.function, name: 'metallurgy_b199' },
    };
    let selectorIndex = [];
    let modelCallIndex = 0;
    const production = createProductionToolOrchestrator({
        fetchCatalog: async () => catalog([unitTool, incompleteTool]),
        callModel: async (messages) => {
            modelCallIndex += 1;
            if (modelCallIndex === 1) {
                selectorIndex = JSON.parse(messages.at(-1).content).tool_index;
                return { content: JSON.stringify({ needs_tool: false, reason: '无需工具' }) };
            }
            return { content: '直接回答。' };
        },
        executeToolCall: async () => { throw new Error('不应执行'); },
    });
    const result = await production.run('概念说明', [], { mode: 'auto' });
    assert.deepEqual(selectorIndex.map(item => item.model_code), ['A001']);
    assert.equal(result.candidate_selection.source_tool_count, 2);
    assert.equal(result.candidate_selection.production_contract_ready_count, 1);
    assert.equal(result.candidate_selection.contract_incomplete_count, 1);

    await assert.rejects(
        production.run('强制测试', [], { mode: 'forced', forced_tool: 'B199' }),
        error => error.errorCode === 'TOOL_INPUT_CONTRACT_INCOMPLETE',
    );

    let researchExposed = 0;
    const research = createProductionToolOrchestrator({
        fetchCatalog: async () => catalog([unitTool, incompleteTool]),
        callModel: async (messages, options) => {
            if (options.tools) researchExposed = options.tools.length;
            return { content: '研究观察完成。' };
        },
        executeToolCall: async () => { throw new Error('不应执行'); },
    });
    const researchResult = await research.run('检查工具规模', [], {
        mode: 'auto', catalog_mode: 'research_full',
    });
    assert.equal(researchExposed, 2);
    assert.equal(researchResult.candidate_selection.contract_incomplete_count, 1);
});

test('用户补参时，候选筛选同时使用当前输入与会话历史', async () => {
    let selectorQuestion = '';
    let modelCallIndex = 0;
    const orchestrator = createProductionToolOrchestrator({
        fetchCatalog: async () => catalog([unitTool, heatTool]),
        callModel: async (messages) => {
            modelCallIndex += 1;
            if (modelCallIndex === 1) {
                selectorQuestion = JSON.parse(messages.at(-1).content).question;
                return { content: JSON.stringify({ needs_tool: true, candidate_model_codes: ['A001'], reason: '结合上轮问题继续换算' }) };
            }
            return { content: '已收到补充参数，等待完整调用参数。' };
        },
        executeToolCall: async () => { throw new Error('本测试不执行工具'); },
    });

    const result = await orchestrator.run('源单位是摄氏度，目标单位是开尔文', [
        { role: 'user', content: '把100换算一下' },
        { role: 'assistant', content: '请补充源单位和目标单位。' },
    ], { mode: 'auto' });

    assert.match(selectorQuestion, /把100换算一下/);
    assert.match(selectorQuestion, /源单位是摄氏度/);
    assert.equal(result.candidate_selection.query_scope, 'current_turn_and_history');
});

test('传统Tool Use默认只校验JSON与Schema，不用参数来源阻断执行', async () => {
    let executeCount = 0;
    const modelCalls = [
        { content: JSON.stringify({ needs_tool: true, candidate_model_codes: ['A001'], reason: '需要单位换算' }) },
        { tool_calls: [{
            id: 'call-traditional-baseline',
            type: 'function',
            function: {
                name: unitTool.function.name,
                arguments: JSON.stringify({ value: 100, source_unit: '°C', target_unit: 'K' }),
            },
        }] },
        { content: '计算完成。' },
    ];
    const orchestrator = createProductionToolOrchestrator({
        fetchCatalog: async () => catalog([unitTool]),
        callModel: async () => modelCalls.shift(),
        executeToolCall: async (toolCall) => {
            executeCount += 1;
            return {
                call_id: toolCall.id,
                function_name: toolCall.function.name,
                model_code: 'A001',
                model_version: '2.3.1',
                status: 'success',
                execution_id: 'EXEC-TRADITIONAL-BASELINE',
                output: { value: 373.15, unit: 'K' },
                actual_data_records: [],
            };
        },
        unsupportedNumbers: () => [],
    });

    const result = await orchestrator.run('帮我把1000摄氏度换算成开尔文', [], { mode: 'auto' });

    assert.equal(result.status, 'success');
    assert.equal(executeCount, 1);
    assert.equal(result.request.parameter_validation_mode, 'traditional');
    assert.equal(result.tool_calls[0].parameter_provenance.value.source, 'unverified');
});

test('证据增强模式下Schema合法但来源不明的参数仍然追问', async () => {
    let executeCount = 0;
    const modelCalls = [
        { content: JSON.stringify({ needs_tool: true, candidate_model_codes: ['A001'], reason: '需要单位换算' }) },
        { tool_calls: [{
            id: 'call-guessed',
            type: 'function',
            function: {
                name: unitTool.function.name,
                arguments: JSON.stringify({ value: 100, source_unit: '°C', target_unit: 'K' }),
            },
        }] },
    ];
    const orchestrator = createProductionToolOrchestrator({
        fetchCatalog: async () => catalog([unitTool]),
        callModel: async () => modelCalls.shift(),
        executeToolCall: async () => { executeCount += 1; },
    });

    const result = await orchestrator.run('帮我把1000摄氏度换算成开尔文', [], {
        mode: 'auto',
        parameter_validation_mode: 'evidence_enhanced',
    });

    assert.equal(executeCount, 0);
    assert.equal(result.status, 'needs_clarification');
    assert.equal(result.request.parameter_validation_mode, 'evidence_enhanced');
    assert.equal(result.tool_calls[0].error_code, 'PROVENANCE_VALIDATION_FAILED');
    assert.equal(result.tool_calls[0].parameter_provenance.value.source, 'unverified');
    assert.match(result.clarification.question, /不会猜测/);
});

test('自然语言已给出嵌套业务值时不要求用户复述Schema内部键名', async () => {
    const userMessage = '钢液1000 kg，当前Mn为0.5 wt%，目标Mn为1.0～1.1 wt%。候选FeMn80成本2元/kg，允许加入0～20 kg，Mn含量80 wt%，Mn收得率0.9，质量保留率1，总加入量不超过20 kg。求最低成本加入方案。';
    const extractedArguments = {
        heat_mass_kg: 1000,
        current_composition_wt_pct: { Mn: 0.5 },
        targets: [{ element: 'Mn', min_wt_pct: 1, max_wt_pct: 1.1 }],
        alloys: [{
            name: 'FeMn80',
            cost_per_kg: 2,
            min_addition_kg: 0,
            max_addition_kg: 20,
            composition_wt_pct: { Mn: 80 },
            element_recovery_fractions: { Mn: 0.9 },
            mass_retention_fraction: 1,
        }],
        max_total_addition_kg: 20,
    };
    const modelCalls = [
        { content: JSON.stringify({ needs_tool: true, candidate_model_codes: ['D019'], reason: '需要合金优化' }) },
        { tool_calls: [{
            id: 'call-d019',
            type: 'function',
            function: { name: alloyOptimizationTool.function.name, arguments: JSON.stringify(extractedArguments) },
        }] },
        { content: '最低成本方案计算完成。' },
    ];
    let executeCount = 0;
    const orchestrator = createProductionToolOrchestrator({
        fetchCatalog: async () => catalog([alloyOptimizationTool]),
        callModel: async () => modelCalls.shift(),
        executeToolCall: async (toolCall) => {
            executeCount += 1;
            return {
                call_id: toolCall.id,
                function_name: toolCall.function.name,
                model_code: 'D019',
                model_version: '2.3.1',
                status: 'success',
                execution_id: 'EXEC-D019-NESTED',
                output: { feasible: true, total_cost: 14 },
                actual_data_records: [],
            };
        },
        unsupportedNumbers: () => [],
    });

    const result = await orchestrator.run(userMessage, [], { mode: 'auto', scene: 'converter' });

    assert.equal(result.status, 'success');
    assert.equal(executeCount, 1);
    assert.equal(result.tool_calls[0].parameter_provenance.targets.source, 'user_input');
    assert.equal(result.tool_calls[0].parameter_provenance.alloys.source, 'user_input');
});

test('嵌套业务值被模型改写时仍由来源闸门阻止执行', async () => {
    const modelCalls = [
        { content: JSON.stringify({ needs_tool: true, candidate_model_codes: ['D019'], reason: '需要合金优化' }) },
        { tool_calls: [{
            id: 'call-d019-guessed',
            type: 'function',
            function: {
                name: alloyOptimizationTool.function.name,
                arguments: JSON.stringify({
                    heat_mass_kg: 1000,
                    current_composition_wt_pct: { Mn: 0.5 },
                    targets: [{ element: 'Mn', min_wt_pct: 1, max_wt_pct: 1.1 }],
                    alloys: [{
                        name: 'FeMn80',
                        cost_per_kg: 3,
                        min_addition_kg: 0,
                        max_addition_kg: 20,
                        composition_wt_pct: { Mn: 80 },
                        element_recovery_fractions: { Mn: 0.9 },
                        mass_retention_fraction: 1,
                    }],
                    max_total_addition_kg: 20,
                }),
            },
        }] },
    ];
    let executeCount = 0;
    const orchestrator = createProductionToolOrchestrator({
        fetchCatalog: async () => catalog([alloyOptimizationTool]),
        callModel: async () => modelCalls.shift(),
        executeToolCall: async () => { executeCount += 1; },
    });

    const result = await orchestrator.run(
        '钢液1000 kg，当前Mn为0.5 wt%，目标Mn为1.0～1.1 wt%。候选FeMn80成本2元/kg，允许加入0～20 kg，Mn含量80 wt%，Mn收得率0.9，质量保留率1，总加入量不超过20 kg。',
        [],
        { mode: 'auto', scene: 'converter', parameter_validation_mode: 'evidence_enhanced' },
    );

    assert.equal(result.status, 'needs_clarification');
    assert.equal(executeCount, 0);
    assert.equal(result.tool_calls[0].parameter_provenance.alloys.source, 'unverified');
});

test('自然语言数值0.90被模型规范化为0.9时仍视为同一来源值', async () => {
    const stages = [
        { name: 'early', oxygen_flow_nm3_min: 30, duration_min_min: 1, duration_max_min: 3, preferred_oxygen_fraction: 0.5, deviation_weight: 1, lance_height_m: 1.8, oxygen_utilization_fraction: 0.82 },
        { name: 'middle', oxygen_flow_nm3_min: 20, duration_min_min: 1, duration_max_min: 3, preferred_oxygen_fraction: 0.3, deviation_weight: 1, lance_height_m: 1.5, oxygen_utilization_fraction: 0.9 },
        { name: 'finish', oxygen_flow_nm3_min: 15, duration_min_min: 1, duration_max_min: 3, preferred_oxygen_fraction: 0.2, deviation_weight: 2, lance_height_m: 1.3, oxygen_utilization_fraction: 0.94 },
    ];
    const modelCalls = [
        { content: JSON.stringify({ needs_tool: true, candidate_model_codes: ['D018'], reason: '需要分段供氧优化' }) },
        { tool_calls: [{
            id: 'call-d018',
            type: 'function',
            function: {
                name: blowingScheduleTool.function.name,
                arguments: JSON.stringify({ total_oxygen_nm3: 120, stages }),
            },
        }] },
        { content: '离线分段供氧方案已经生成。' },
    ];
    let executeCount = 0;
    const orchestrator = createProductionToolOrchestrator({
        fetchCatalog: async () => catalog([blowingScheduleTool]),
        callModel: async () => modelCalls.shift(),
        executeToolCall: async (toolCall) => {
            executeCount += 1;
            return {
                call_id: toolCall.id,
                function_name: toolCall.function.name,
                model_code: 'D018',
                model_version: '2.3.1',
                status: 'success',
                execution_id: 'EXEC-D018-NUMERIC-NORMALIZATION',
                output: { feasible: true },
                actual_data_records: [],
            };
        },
        unsupportedNumbers: () => [],
    });

    const result = await orchestrator.run(
        '总氧量120 Nm³；early、middle、finish三段流量30、20、15 Nm³/min，时长均为1～3 min，占比0.5、0.3、0.2，权重1、1、2，枪位1.8、1.5、1.3 m，氧利用率0.82、0.90、0.94。',
        [],
        { mode: 'auto', scene: 'converter' },
    );

    assert.equal(result.status, 'success');
    assert.equal(executeCount, 1);
    assert.equal(result.tool_calls[0].parameter_provenance.stages.source, 'user_input');
});

test('同一函数在计划中重复出现时按调用顺序绑定不同步骤', async () => {
    const modelCalls = [
        { content: JSON.stringify({ needs_tool: true, candidate_model_codes: ['A001'], reason: '需要两次温度换算' }) },
        { content: JSON.stringify({ objective: '完成两次换算', steps: [
            { step_id: 'S1', function_name: unitTool.function.name, purpose: '换算100摄氏度', depends_on: [] },
            { step_id: 'S2', function_name: unitTool.function.name, purpose: '换算0摄氏度', depends_on: [] },
        ] }) },
        { tool_calls: [{ id: 'repeat-1', type: 'function', function: { name: unitTool.function.name, arguments: JSON.stringify({ value: 100, source_unit: '°C', target_unit: 'K' }) } }] },
        { tool_calls: [{ id: 'repeat-2', type: 'function', function: { name: unitTool.function.name, arguments: JSON.stringify({ value: 0, source_unit: '°C', target_unit: 'K' }) } }] },
        { content: '两次换算都已完成。' },
    ];
    let index = 0;
    const orchestrator = createProductionToolOrchestrator({
        fetchCatalog: async () => catalog([unitTool]),
        callModel: async () => modelCalls.shift(),
        executeToolCall: async (toolCall) => ({
            call_id: toolCall.id,
            function_name: toolCall.function.name,
            model_code: 'A001',
            model_version: '2.3.1',
            status: 'success',
            execution_id: `EXEC-REPEAT-${++index}`,
            output: { value: index === 1 ? 373.15 : 273.15, unit: 'K' },
            actual_data_records: unitTool.source_records,
        }),
        unsupportedNumbers: () => [],
    });

    const result = await orchestrator.run('把100 °C和0 °C分别换算成K', [], { mode: 'plan', max_tool_calls: 4 });

    assert.equal(result.status, 'success');
    assert.deepEqual(result.tool_calls.map(item => item.planned_step_id), ['S1', 'S2']);
});

test('部分完成后补参会恢复同一编排，不重选工具也不重复执行已完成步骤', async () => {
    const modelCalls = [
        { content: JSON.stringify({ needs_tool: true, candidate_model_codes: ['B003', 'B009'], reason: '两步热力学计算' }) },
        { content: JSON.stringify({ objective: '先显热后平衡', steps: [
            { step_id: 'S1', function_name: heatTool.function.name, purpose: '计算显热', depends_on: [] },
            { step_id: 'S2', function_name: equilibriumTool.function.name, purpose: '计算平衡常数', depends_on: ['S1'] },
        ] }) },
        { tool_calls: [{ id: 'resume-s1', type: 'function', function: { name: heatTool.function.name, arguments: JSON.stringify({ species: 'Fe', temperature_start: 300, temperature_end: 1800 }) } }] },
        { content: '让我先检查依赖。我需要确认是否可以继续。\n\n## 执行结果\n\n### 第一步（B003）已完成\n\n- **执行ID**：`EXEC-RESUME-1`\n- 使用数据集 `B003_PROPERTY_V1`。\n\n第二步（B009）只缺少 `delta_g`；温度沿用第一步已确认值。' },
        { tool_calls: [{ id: 'resume-s2', type: 'function', function: { name: equilibriumTool.function.name, arguments: JSON.stringify({ delta_g: -12000, temperature: 1800 }) } }] },
        { content: '平衡常数计算完成。' },
    ];
    const executed = [];
    const orchestrator = createProductionToolOrchestrator({
        fetchCatalog: async () => catalog([heatTool, equilibriumTool]),
        callModel: async () => modelCalls.shift(),
        executeToolCall: async (toolCall) => {
            executed.push(toolCall.function.name);
            const first = toolCall.function.name === heatTool.function.name;
            return {
                call_id: toolCall.id,
                function_name: toolCall.function.name,
                model_code: first ? 'B003' : 'B009',
                model_version: '2.3.1',
                status: 'success',
                execution_id: first ? 'EXEC-RESUME-1' : 'EXEC-RESUME-2',
                output: first ? { enthalpy: 12000 } : { equilibrium_constant: 2.23 },
                actual_data_records: first ? heatTool.source_records : equilibriumTool.source_records,
            };
        },
        unsupportedNumbers: () => [],
    });

    const first = await orchestrator.run('先算Fe从300 K到1800 K的显热，再求平衡常数，但我还没有delta_g', [], {
        mode: 'plan',
        max_tool_calls: 4,
    });
    assert.equal(first.status, 'partially_completed_waiting_for_input');
    assert.equal(first.lifecycle, 'partially_completed');
    assert.deepEqual(first.clarification.pending_steps, ['S2']);
    assert.deepEqual(first.clarification.fields.map(item => item.field), ['delta_g']);
    assert.equal(first.product_view.clarification, first.product_view.content);
    assert.match(first.product_view.content, /^## 执行结果/);
    assert.match(first.product_view.content, /B003_PROPERTY_V1/);
    assert.doesNotMatch(first.product_view.content, /The first|Let me|让我|我需要|\b(?:B003|B009)\b|执行\s*ID|EXEC-|``|（）|工具版本|调用过程/);

    const resumed = await orchestrator.run('delta_g=-12000 J/mol，计算温度1800 K', [], {
        orchestration_id: first.orchestration_id,
    });
    assert.equal(resumed.orchestration_id, first.orchestration_id);
    assert.equal(resumed.status, 'success');
    assert.deepEqual(executed, [heatTool.function.name, equilibriumTool.function.name]);
    assert.deepEqual(resumed.tool_calls.filter(item => item.status === 'success').map(item => item.planned_step_id), ['S1', 'S2']);
    assert.deepEqual(resumed.answer_bindings.map(item => item.execution_id), ['EXEC-RESUME-1', 'EXEC-RESUME-2']);

    await assert.rejects(
        orchestrator.run('再继续', [], { orchestration_id: first.orchestration_id }),
        error => error.errorCode === 'ORCHESTRATION_NOT_RESUMABLE' && error.statusCode === 404,
    );
});
