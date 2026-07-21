-- ============================================================
-- 数据库改造 V2 — 迁移 002：热力学关联式表
-- ============================================================

-- 1. 扩展 thermodynamic_property 增加必要字段
ALTER TABLE metallurgy_v2.thermodynamic_property
    ADD COLUMN IF NOT EXISTS property_code VARCHAR(50),
    ADD COLUMN IF NOT EXISTS phase VARCHAR(20),
    ADD COLUMN IF NOT EXISTS pressure_pa NUMERIC(16, 4),
    ADD COLUMN IF NOT EXISTS data_origin VARCHAR(30) DEFAULT 'unknown',
    ADD COLUMN IF NOT EXISTS correlation_id BIGINT,
    ADD COLUMN IF NOT EXISTS source_id BIGINT,
    ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'::jsonb;

-- 2. 热力学关联式表
CREATE TABLE IF NOT EXISTS metallurgy_v2.thermodynamic_correlation (
    id              BIGSERIAL PRIMARY KEY,
    species_id      VARCHAR(128) NOT NULL,
    phase           VARCHAR(20) NOT NULL DEFAULT 's',
    equation_type   VARCHAR(50) NOT NULL,          -- SHOMATE / NASA7 / NASA9 / Antoine / Wagner
    temperature_min_k NUMERIC(12, 4) NOT NULL,
    temperature_max_k NUMERIC(12, 4) NOT NULL,
    reference_temperature_k NUMERIC(12, 4) DEFAULT 298.15,
    reference_pressure_pa NUMERIC(16, 4) DEFAULT 101325,
    coefficients    JSONB NOT NULL,                 -- Shomate: {A,B,C,D,E,F,G,H}
    coefficient_units JSONB DEFAULT '{}'::jsonb,
    source_id       VARCHAR(64),                   -- 关联 dataset_registry
    source_record_key VARCHAR(255),
    reference_text  TEXT,
    priority        INTEGER DEFAULT 100,
    quality_level   VARCHAR(30),
    is_active       BOOLEAN DEFAULT TRUE,
    metadata        JSONB DEFAULT '{}'::jsonb,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_correlation_temp CHECK (temperature_max_k > temperature_min_k)
);

COMMENT ON TABLE metallurgy_v2.thermodynamic_correlation IS '热力学关联式表：Shomate/NASA 等多多项式系数，通过 JSONB 统一存储';

CREATE INDEX IF NOT EXISTS idx_corr_species ON metallurgy_v2.thermodynamic_correlation(species_id, phase, equation_type);
CREATE INDEX IF NOT EXISTS idx_corr_temp ON metallurgy_v2.thermodynamic_correlation(species_id, temperature_min_k, temperature_max_k);

-- 3. 更新已有数据：根据 property_type 设置 property_code
UPDATE metallurgy_v2.thermodynamic_property
SET property_code = CASE
    WHEN property_type LIKE '%Cp%' OR property_type = 'Cp' THEN 'CP_STD'
    WHEN property_type = 'S' OR property_type LIKE '%熵%' THEN 'S_STD'
    WHEN property_type LIKE '%H-H298%' OR property_type = 'H_minus_H298' THEN 'H_INCREMENT_298'
    WHEN property_type LIKE '%ΔHf%' OR property_type LIKE '%生成焓%' THEN 'HF_STD'
    WHEN property_type = 'G' OR property_type LIKE '%Gibbs%' THEN 'G_STD'
    WHEN property_type = 'Shomate参数' THEN 'SHOMATE_COEFF'
    ELSE 'OTHER'
END,
phase = CASE
    WHEN species LIKE '%(g)%' THEN 'gas'
    WHEN species LIKE '%(l)%' THEN 'liquid'
    ELSE 'solid'
END,
data_origin = CASE
    WHEN source_ref LIKE '%Shomate%' THEN 'calculated'
    WHEN source_ref LIKE '%NIST%' THEN 'compiled'
    ELSE 'unknown'
END
WHERE property_code IS NULL;

-- 4. 属性定义字典表
CREATE TABLE IF NOT EXISTS metallurgy_v2.thermo_property_definition (
    id              BIGSERIAL PRIMARY KEY,
    property_code   VARCHAR(50) UNIQUE NOT NULL,
    name_zh         VARCHAR(100) NOT NULL,
    name_en         VARCHAR(100),
    symbol          VARCHAR(50),
    default_unit    VARCHAR(50),
    description     TEXT
);

INSERT INTO metallurgy_v2.thermo_property_definition (property_code, name_zh, name_en, symbol, default_unit, description) VALUES
    ('CP_STD', '标准摩尔定压热容', 'Standard molar heat capacity at constant pressure', 'Cp°', 'J/(mol·K)', '标准压力下摩尔定压热容'),
    ('S_STD', '标准摩尔熵', 'Standard molar entropy', 'S°', 'J/(mol·K)', '标准熵'),
    ('H_INCREMENT_298', '相对于298.15K的焓增量', 'Enthalpy increment relative to 298.15 K', 'H°-H°298', 'kJ/mol', 'H(T) - H(298.15)'),
    ('H_ABSOLUTE', '摩尔焓', 'Molar enthalpy', 'H', 'kJ/mol', '绝对摩尔焓'),
    ('G_STD', '标准Gibbs自由能', 'Standard Gibbs free energy', 'G°', 'kJ/mol', 'G = H - TS'),
    ('HF_STD', '标准生成焓', 'Standard enthalpy of formation', 'ΔfH°', 'kJ/mol', '标准生成焓'),
    ('GF_STD', '标准生成Gibbs自由能', 'Standard Gibbs free energy of formation', 'ΔfG°', 'kJ/mol', '标准生成Gibbs自由能'),
    ('SHOMATE_COEFF', 'Shomate方程系数', 'Shomate equation coefficients', '-', '-', 'Cp = A+Bt+Ct²+Dt³+E/t²'),
ON CONFLICT (property_code) DO NOTHING;
