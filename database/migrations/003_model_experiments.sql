-- 冶金平台 v2 — 统一执行轨迹与大模型工具调用实验
CREATE SCHEMA IF NOT EXISTS metallurgy_v2;

CREATE TABLE IF NOT EXISTS metallurgy_v2.model_execution_log (
    execution_id       VARCHAR(64) PRIMARY KEY,
    trace_id           VARCHAR(64) NOT NULL,
    model_code         VARCHAR(32) NOT NULL,
    model_version      VARCHAR(64),
    input_json         JSONB NOT NULL,
    actual_data_records JSONB NOT NULL DEFAULT '[]'::jsonb,
    boundary_check     JSONB,
    output_json        JSONB,
    status             VARCHAR(32) NOT NULL,
    error_code         VARCHAR(64),
    error_message      TEXT,
    runtime_ms         NUMERIC(14, 3),
    user_or_agent      VARCHAR(128) NOT NULL,
    started_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at       TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_model_execution_trace
    ON metallurgy_v2.model_execution_log(trace_id);
CREATE INDEX IF NOT EXISTS idx_model_execution_model
    ON metallurgy_v2.model_execution_log(model_code, started_at DESC);

CREATE TABLE IF NOT EXISTS metallurgy_v2.llm_tool_trace (
    trace_id            VARCHAR(64) PRIMARY KEY,
    user_query          TEXT NOT NULL,
    llm_name            VARCHAR(128) NOT NULL,
    prompt_version      VARCHAR(64) NOT NULL,
    mode                VARCHAR(32) NOT NULL,
    candidate_models    JSONB NOT NULL DEFAULT '[]'::jsonb,
    selected_model      VARCHAR(32),
    selection_reason    TEXT,
    generated_arguments JSONB NOT NULL DEFAULT '{}'::jsonb,
    validation_result   JSONB,
    execution_result    JSONB,
    retry_count         INTEGER NOT NULL DEFAULT 0,
    final_answer        TEXT,
    latency_ms          NUMERIC(14, 3),
    token_usage         JSONB,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS metallurgy_v2.experiment_run (
    experiment_id       VARCHAR(64) PRIMARY KEY,
    trace_id            VARCHAR(64) NOT NULL REFERENCES metallurgy_v2.llm_tool_trace(trace_id),
    benchmark_case_id   VARCHAR(64),
    mode                VARCHAR(32) NOT NULL,
    result_validation_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    status              VARCHAR(32) NOT NULL DEFAULT 'completed',
    metrics_json        JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_experiment_mode CHECK (mode IN ('direct', 'forced', 'autonomous'))
);

COMMENT ON TABLE metallurgy_v2.model_execution_log IS '统一小模型执行轨迹，记录输入、实际数据、输出、错误与耗时';
COMMENT ON TABLE metallurgy_v2.llm_tool_trace IS '大模型工具选择、参数、校验、执行与最终回答的完整轨迹';
COMMENT ON TABLE metallurgy_v2.experiment_run IS '直接回答、强制调用、自主调用三模式实验记录';
