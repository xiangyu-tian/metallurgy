-- ============================================================
-- 冶金平台 v2 — 数据库改造第一期迁移
-- Schema: metallurgy_v2 (新建专用 schema)
-- 基于 绿色低碳冶金_数据库资料源与120小模型清单.xlsx Sheet 03
-- ============================================================

-- 创建专用 schema
CREATE SCHEMA IF NOT EXISTS metallurgy_v2;

-- ============================================================
-- 1. 数据集注册表
-- ============================================================
CREATE TABLE metallurgy_v2.dataset_registry (
    dataset_id      VARCHAR(64) PRIMARY KEY,
    name            VARCHAR(255) NOT NULL,
    category        VARCHAR(64) NOT NULL,       -- 一级类别
    provider        VARCHAR(255),               -- 提供机构
    license         VARCHAR(255) NOT NULL,      -- 许可与再分发边界
    access_url      TEXT,                       -- 访问地址
    ingestion_mode  VARCHAR(64) NOT NULL,       -- API/网页/内部DB
    version         VARCHAR(64),                -- 数据版本
    retrieved_at    TIMESTAMP NOT NULL,          -- 抓取/接收时间
    checksum        VARCHAR(128),               -- sha256:...
    owner           VARCHAR(64) NOT NULL,        -- 责任人/责任组
    security_level  VARCHAR(32) NOT NULL DEFAULT '公开',  -- 公开/内部/受限
    quality_grade   VARCHAR(16),                -- A/B/C
    lineage_json    JSON,                       -- 血缘与处理记录
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE metallurgy_v2.dataset_registry IS '数据集注册表：记录44+个外部数据源的基本信息、许可和入库状态';

-- ============================================================
-- 2. 知识文档表
-- ============================================================
CREATE TABLE metallurgy_v2.knowledge_docs (
    doc_id              VARCHAR(64) PRIMARY KEY,
    dataset_id          VARCHAR(64) NOT NULL REFERENCES metallurgy_v2.dataset_registry(dataset_id),
    title               TEXT NOT NULL,
    doc_type            VARCHAR(32) NOT NULL,   -- paper/standard/patent/manual
    doi_or_standard_no  VARCHAR(128),           -- DOI/标准号/专利号
    publication_date    DATE,
    license             VARCHAR(255) NOT NULL,
    content_uri         TEXT,                   -- 合法保存的正文/附件位置
    source_url          TEXT NOT NULL,
    language            VARCHAR(16) NOT NULL DEFAULT 'zh-CN',
    chunk_policy_version VARCHAR(32),
    embedding_model     VARCHAR(128),
    citation_text       TEXT,                   -- 生成答案时的引用文本
    created_at          TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE metallurgy_v2.knowledge_docs IS '知识文档表：论文、标准、专利、手册等文档元数据';

-- ============================================================
-- 3. 模型注册表（核心）
-- ============================================================
CREATE TABLE metallurgy_v2.model_registry (
    model_id             VARCHAR(32) PRIMARY KEY,
    name                 VARCHAR(255) NOT NULL,
    scenario             VARCHAR(64) NOT NULL,          -- 业务场景
    model_type           VARCHAR(64) NOT NULL,          -- 模型类型
    api_name             VARCHAR(128) NOT NULL,         -- 工具函数名，与 Python 实现对应
    input_schema_json    JSON NOT NULL,                 -- 输入参数定义、单位、范围、必填项
    output_schema_json   JSON NOT NULL,                 -- 输出字段、单位、置信度与状态码
    applicable_boundary  TEXT NOT NULL,                 -- 适用边界
    validation_rules     JSON NOT NULL DEFAULT '[]'::json,  -- 调用前后规则校验
    priority             VARCHAR(8) NOT NULL DEFAULT 'P2',   -- P0/P1/P2
    owner                VARCHAR(64) NOT NULL,          -- 责任人/组
    status               VARCHAR(32) NOT NULL DEFAULT 'planned',  -- planned/dev/validated/deployed
    created_at           TIMESTAMP DEFAULT NOW(),
    updated_at           TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE metallurgy_v2.model_registry IS '模型注册表：120个小模型的统一注册中心，JSON Schema驱动前端动态表单';

-- ============================================================
-- 4. 模型版本表
-- ============================================================
CREATE TABLE metallurgy_v2.model_versions (
    id                  SERIAL PRIMARY KEY,
    model_id            VARCHAR(32) NOT NULL REFERENCES metallurgy_v2.model_registry(model_id),
    version             VARCHAR(64) NOT NULL,           -- 语义版本
    artifact_uri        TEXT NOT NULL,                  -- 代码/权重/容器地址
    git_commit          VARCHAR(64),                    -- 代码提交
    data_snapshot_id    VARCHAR(64),                    -- 训练/标定数据快照
    parameter_json      JSON,                           -- 参数/超参数
    dependency_lock     TEXT NOT NULL,                  -- 环境锁定
    created_at          TIMESTAMP NOT NULL DEFAULT NOW(),
    approved_by         VARCHAR(64),                    -- 审核人
    release_notes       TEXT,                           -- 版本说明
    UNIQUE (model_id, version)
);

COMMENT ON TABLE metallurgy_v2.model_versions IS '模型版本表：每个模型的版本历史、制品地址和审核记录';

-- ============================================================
-- 5. 调用日志表
-- ============================================================
CREATE TABLE metallurgy_v2.invocation_logs (
    id                  BIGSERIAL PRIMARY KEY,
    trace_id            VARCHAR(64) NOT NULL,           -- 端到端任务追踪ID
    call_id             VARCHAR(64) NOT NULL,           -- 单次工具调用ID
    model_id            VARCHAR(32) NOT NULL,
    model_version       VARCHAR(64) NOT NULL,
    requested_at        TIMESTAMP NOT NULL DEFAULT NOW(),
    input_json          JSON NOT NULL,                  -- 标准化输入及单位
    boundary_check      JSON NOT NULL,                  -- 边界校验结果
    output_json         JSON,                           -- 输出
    confidence          DECIMAL(8,6),                   -- 置信度/可信度
    validation_result   JSON,                           -- 规则/专家校验结果
    runtime_ms          INTEGER,                        -- 耗时
    status              VARCHAR(32) NOT NULL,           -- success/rejected/error
    error_code          VARCHAR(64),                    -- OUT_OF_RANGE / INVALID_INPUT / ...
    user_or_agent       VARCHAR(128) NOT NULL,          -- 调用主体
    created_at          TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_invocation_logs_model_id ON metallurgy_v2.invocation_logs(model_id);
CREATE INDEX idx_invocation_logs_trace_id ON metallurgy_v2.invocation_logs(trace_id);
CREATE INDEX idx_invocation_logs_requested_at ON metallurgy_v2.invocation_logs(requested_at);

COMMENT ON TABLE metallurgy_v2.invocation_logs IS '调用日志表：记录每次模型调用的完整输入输出和校验信息';

-- ============================================================
-- 6. 热力学物性数据表
-- ============================================================
CREATE TABLE metallurgy_v2.thermodynamic_property (
    id                  SERIAL PRIMARY KEY,
    dataset_id          VARCHAR(64) REFERENCES metallurgy_v2.dataset_registry(dataset_id),
    species             VARCHAR(128) NOT NULL,          -- 物种名
    chemical_formula    VARCHAR(128),                    -- 化学式
    phase               VARCHAR(64),                    -- 相态
    property_type       VARCHAR(64) NOT NULL,           -- Cp/H/S/G/ΔHf/...
    temperature         DECIMAL(10,2),                  -- 温度 (K)
    temperature_min     DECIMAL(10,2),                  -- 适用温区下限
    temperature_max     DECIMAL(10,2),                  -- 适用温区上限
    value               DECIMAL(18,8) NOT NULL,          -- 数值
    unit                VARCHAR(32) NOT NULL,
    uncertainty         DECIMAL(18,8),                  -- 不确定度
    data_type           VARCHAR(32) DEFAULT 'experimental',  -- experimental/calculated/compiled
    source_ref          TEXT,                            -- 来源引用
    quality_grade       VARCHAR(8),                      -- A/B/C
    created_at          TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_thermo_species ON metallurgy_v2.thermodynamic_property(species);
CREATE INDEX idx_thermo_property_type ON metallurgy_v2.thermodynamic_property(property_type);

COMMENT ON TABLE metallurgy_v2.thermodynamic_property IS '热力学物性表：存储温度-热力学函数表数据';

-- ============================================================
-- 7. 动力学参数表
-- ============================================================
CREATE TABLE metallurgy_v2.kinetic_parameter (
    id                  SERIAL PRIMARY KEY,
    dataset_id          VARCHAR(64) REFERENCES metallurgy_v2.dataset_registry(dataset_id),
    material_system     VARCHAR(128) NOT NULL,          -- 材料体系
    diffusing_element   VARCHAR(64),                    -- 扩散元素
    matrix_phase        VARCHAR(64),                    -- 基体相
    parameter_type      VARCHAR(64) NOT NULL,           -- D₀/A/活化能/速率常数/...
    parameter_value     DECIMAL(18,8) NOT NULL,
    unit                VARCHAR(32) NOT NULL,
    temperature_min     DECIMAL(10,2),
    temperature_max     DECIMAL(10,2),
    method              VARCHAR(128),                    -- 测试方法
    source_ref          TEXT,
    quality_grade       VARCHAR(8),
    created_at          TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_kinetic_material ON metallurgy_v2.kinetic_parameter(material_system);

COMMENT ON TABLE metallurgy_v2.kinetic_parameter IS '动力学参数表：扩散系数、指前因子、激活能等';

-- ============================================================
-- 8. 反应定义表
-- ============================================================
CREATE TABLE metallurgy_v2.reaction_definition (
    id                  SERIAL PRIMARY KEY,
    reaction_id         VARCHAR(32) UNIQUE NOT NULL,     -- R001, R002, ...
    reaction_equation   TEXT NOT NULL,                   -- 配平反应式
    name                VARCHAR(255),                    -- 反应名称
    category            VARCHAR(64),                     -- 氧化/还原/分解/...
    reactants           JSON NOT NULL,                   -- [{species, coefficient, phase}]
    products            JSON NOT NULL,                   -- [{species, coefficient, phase}]
    created_at          TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE metallurgy_v2.reaction_definition IS '反应定义表：化学反应的标准化定义';

-- ============================================================
-- 9. 反应物性表
-- ============================================================
CREATE TABLE metallurgy_v2.reaction_property (
    id                  SERIAL PRIMARY KEY,
    reaction_id         VARCHAR(32) NOT NULL REFERENCES metallurgy_v2.reaction_definition(reaction_id),
    dataset_id          VARCHAR(64) REFERENCES metallurgy_v2.dataset_registry(dataset_id),
    property_type       VARCHAR(64) NOT NULL,           -- ΔH/ΔS/ΔG/K/...
    temperature         DECIMAL(10,2),                  -- 温度 (K)
    value               DECIMAL(18,8) NOT NULL,
    unit                VARCHAR(32) NOT NULL,
    uncertainty         DECIMAL(18,8),
    data_type           VARCHAR(32) DEFAULT 'experimental',
    source_ref          TEXT,
    quality_grade       VARCHAR(8),
    created_at          TIMESTAMP DEFAULT NOW(),
    UNIQUE (reaction_id, property_type, temperature)
);

COMMENT ON TABLE metallurgy_v2.reaction_property IS '反应物性表：特定反应在特定温度下的热力学性质';

-- ============================================================
-- 10. 评测用例表
-- ============================================================
CREATE TABLE metallurgy_v2.benchmark_cases (
    case_id             VARCHAR(64) PRIMARY KEY,
    model_id            VARCHAR(32) NOT NULL REFERENCES metallurgy_v2.model_registry(model_id),
    case_type           VARCHAR(32) NOT NULL,           -- unit/regression/OOD/safety
    input_json          JSON NOT NULL,
    expected_json       JSON,                            -- 期望输出/范围
    reference_source    TEXT NOT NULL,                   -- 权威参考
    tolerance_json      JSON,                            -- {abs:..., rel:...}
    expert_label        TEXT,                            -- 专家结论
    created_at          TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE metallurgy_v2.benchmark_cases IS '评测用例表：模型验证的标准测试用例集';

-- ============================================================
-- 11. 模型评测指标表
-- ============================================================
CREATE TABLE metallurgy_v2.model_metrics (
    id                  SERIAL PRIMARY KEY,
    evaluation_id       VARCHAR(64) NOT NULL,
    model_id            VARCHAR(32) NOT NULL REFERENCES metallurgy_v2.model_registry(model_id),
    model_version       VARCHAR(64) NOT NULL,
    dataset_snapshot_id VARCHAR(64) NOT NULL,
    metric_name         VARCHAR(64) NOT NULL,           -- MAE/RMSE/R²/...
    metric_value        DECIMAL(18,8) NOT NULL,
    slice_json          JSON,                            -- 分层切片
    passed              BOOLEAN NOT NULL,
    evaluated_at        TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_metrics_model ON metallurgy_v2.model_metrics(model_id, model_version);

COMMENT ON TABLE metallurgy_v2.model_metrics IS '模型评测指标表：各版本模型在测试集上的量化表现';

-- ============================================================
-- 12. 相图平衡记录表（第二期）
-- ============================================================
CREATE TABLE metallurgy_v2.phase_equilibrium_record (
    id                  SERIAL PRIMARY KEY,
    dataset_id          VARCHAR(64) REFERENCES metallurgy_v2.dataset_registry(dataset_id),
    system_name         VARCHAR(128) NOT NULL,          -- Fe-C, Al-Si-Mg, ...
    temperature         DECIMAL(10,2) NOT NULL,
    pressure            DECIMAL(10,2) DEFAULT 101325,
    composition_json    JSON NOT NULL,                   -- [{element, fraction}]
    phases_present      JSON NOT NULL,                   -- [{phase_name, fraction}]
    calculation_method  VARCHAR(64),                    -- lever_rule / calphad / experiment
    software_version    VARCHAR(64),
    created_at          TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE metallurgy_v2.phase_equilibrium_record IS '相图平衡记录表：相图计算结果及实验数据点';

-- ============================================================
-- 索引：search_path
-- ============================================================
-- SET search_path TO metallurgy_v2, public;
