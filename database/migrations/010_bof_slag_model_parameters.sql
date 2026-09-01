-- P1-W7: additive, versioned BOF slag/metal reference-model parameters.
-- This migration never alters or removes an existing scientific record.

CREATE SCHEMA IF NOT EXISTS metallurgy_v2;

CREATE TABLE IF NOT EXISTS metallurgy_v2.bof_slag_model_parameter (
    id                          BIGSERIAL PRIMARY KEY,
    dataset_id                  VARCHAR(64) NOT NULL
        REFERENCES metallurgy_v2.dataset_registry(dataset_id),
    model_code                  VARCHAR(32) NOT NULL,
    parameter_set_id            VARCHAR(160) NOT NULL,
    parameter_code              VARCHAR(128) NOT NULL,
    parameter_value             NUMERIC(24, 12) NOT NULL,
    unit                        VARCHAR(96) NOT NULL,
    source_version              VARCHAR(128) NOT NULL,
    source_ref                  TEXT NOT NULL,
    source_url                  TEXT NOT NULL,
    temperature_min_k           NUMERIC(12, 4) NOT NULL,
    temperature_max_k           NUMERIC(12, 4) NOT NULL,
    usage_scope                 VARCHAR(64) NOT NULL,
    applicability               JSONB NOT NULL DEFAULT '{}'::jsonb,
    metadata                    JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_approved                 BOOLEAN NOT NULL DEFAULT FALSE,
    created_at                  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_bof_slag_parameter_model
        CHECK (model_code IN ('D010', 'D011', 'D012', 'D013')),
    CONSTRAINT chk_bof_slag_parameter_temperature
        CHECK (temperature_min_k > 0 AND temperature_max_k > temperature_min_k),
    CONSTRAINT chk_bof_slag_parameter_usage
        CHECK (usage_scope IN ('REFERENCE_VALIDATION_ONLY', 'ENGINEERING_SCREENING_ONLY')),
    CONSTRAINT uq_bof_slag_parameter
        UNIQUE (model_code, parameter_set_id, parameter_code, source_version)
);

CREATE INDEX IF NOT EXISTS idx_bof_slag_parameter_lookup
    ON metallurgy_v2.bof_slag_model_parameter(
        model_code, parameter_set_id, is_approved,
        temperature_min_k, temperature_max_k
    );
