'use strict';

const fs = require('fs');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');

const {
    DATASET_ID,
    buildDataset,
} = require('../scripts/generate-tool-orchestration-cases');

const snapshotPath = path.resolve(__dirname, '..', '..', 'Tools', 'benchmarks', 'tool_orchestration_difficulty_cases_v1.json');

test('难度测试体固定为5级、40个基础问题和120个策略运行体', () => {
    const dataset = buildDataset();
    assert.equal(dataset.dataset_id, DATASET_ID);
    assert.equal(dataset.cases.length, 40);
    assert.equal(dataset.run_specs.length, 120);
    assert.deepEqual(dataset.scope.difficulty_distribution, { D0: 8, D1: 8, D2: 8, D3: 8, D4: 8 });

    const modeCounts = dataset.run_specs.reduce((counts, run) => {
        counts[run.request.mode] = (counts[run.request.mode] || 0) + 1;
        return counts;
    }, {});
    assert.deepEqual(modeCounts, { auto: 40, forced: 40, plan: 40 });
});

test('测试体ID唯一且每个强制条件都有明确工具', () => {
    const dataset = buildDataset();
    const caseIds = dataset.cases.map(item => item.case_id);
    const runIds = dataset.run_specs.map(item => item.run_id);
    assert.equal(new Set(caseIds).size, caseIds.length);
    assert.equal(new Set(runIds).size, runIds.length);
    for (const run of dataset.run_specs.filter(item => item.request.mode === 'forced')) {
        assert.equal(typeof run.request.forced_tool, 'string', run.run_id);
        assert.ok(run.request.forced_tool.length > 0, run.run_id);
    }
});

test('各难度层满足其最小结构约束', () => {
    const dataset = buildDataset();
    for (const item of dataset.cases) {
        assert.ok(item.title && item.prompt && item.rationale, item.case_id);
        assert.ok(item.research_questions.length > 0, item.case_id);
        assert.ok(Array.isArray(item.scoring_focus) && item.scoring_focus.length > 0, item.case_id);
        assert.ok(item.ground_truth.minimum_successful_tool_calls <= item.ground_truth.maximum_successful_tool_calls, item.case_id);

        if (item.difficulty === 'D0') {
            assert.equal(item.ground_truth.needs_tool, false, item.case_id);
            assert.equal(item.ground_truth.maximum_successful_tool_calls, 0, item.case_id);
        }
        if (item.difficulty === 'D1') {
            assert.equal(item.ground_truth.required_model_codes.length, 1, item.case_id);
            assert.equal(item.ground_truth.minimum_successful_tool_calls, 1, item.case_id);
            assert.ok(Object.keys(item.gold_parameters).length > 0, item.case_id);
        }
        if (item.difficulty === 'D2') {
            assert.notEqual(item.ground_truth.decision, 'call', item.case_id);
            assert.ok(item.ground_truth.clarification_fields.length > 0, item.case_id);
        }
        if (item.difficulty === 'D3') {
            assert.ok(item.ground_truth.plan_steps.length >= 2, item.case_id);
            assert.ok(item.ground_truth.maximum_successful_tool_calls >= 2, item.case_id);
        }
        if (item.difficulty === 'D4') {
            assert.ok(item.distractors.length > 0 || item.conversation_turns.length > 0, item.case_id);
        }
    }
});

test('每个运行体引用有效基础问题且请求满足三种模式契约', () => {
    const dataset = buildDataset();
    const casesById = new Map(dataset.cases.map(item => [item.case_id, item]));
    for (const run of dataset.run_specs) {
        assert.ok(casesById.has(run.case_id), run.run_id);
        assert.equal(run.request.message, casesById.get(run.case_id).prompt, run.run_id);
        assert.ok(['auto', 'forced', 'plan'].includes(run.request.mode), run.run_id);
        assert.equal(run.request.catalog_mode, 'production', run.run_id);
        assert.equal(run.request.parameter_validation_mode, 'traditional', run.run_id);
        assert.ok(run.metrics.includes('product_trace_leakage'), run.run_id);
        if (run.request.mode === 'plan') assert.equal(run.request.max_tool_calls, 6, run.run_id);
        else assert.equal(run.request.max_tool_calls, 1, run.run_id);
    }
    assert.equal(dataset.parameter_validation_extension.default_baseline, 'traditional');
    assert.deepEqual(dataset.parameter_validation_extension.supported_modes, ['traditional', 'evidence_enhanced']);
});

test('冻结JSON与生成器完全一致且不包含服务地址或密钥形态', () => {
    const generated = buildDataset();
    const frozen = JSON.parse(fs.readFileSync(snapshotPath, 'utf8'));
    assert.deepEqual(frozen, generated);
    const serialized = JSON.stringify(frozen);
    assert.doesNotMatch(serialized, /https?:\/\/(?:127\.0\.0\.1|localhost)|sk-[a-z0-9]{12,}/i);
});
