-- P1-W13: additive storage for approved C008 viscosity correlations.
-- Existing tables and rows are never altered or overwritten.

CREATE SCHEMA IF NOT EXISTS metallurgy_v2;

CREATE TABLE IF NOT EXISTS metallurgy_v2.melt_viscosity_model_definition (
    id                  BIGSERIAL PRIMARY KEY,
    dataset_id          VARCHAR(64) NOT NULL REFERENCES metallurgy_v2.dataset_registry(dataset_id),
    model_id            VARCHAR(128) NOT NULL,
    material_kind       VARCHAR(32) NOT NULL,
    equation_type       VARCHAR(64) NOT NULL,
    temperature_min_k   NUMERIC(12, 4) NOT NULL,
    temperature_max_k   NUMERIC(12, 4) NOT NULL,
    parameters          JSONB NOT NULL,
    component_groups    JSONB NOT NULL DEFAULT '{}'::jsonb,
    applicability       JSONB NOT NULL DEFAULT '{}'::jsonb,
    source_version      VARCHAR(128) NOT NULL,
    source_ref          TEXT NOT NULL,
    source_url          TEXT NOT NULL,
    is_approved         BOOLEAN NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_melt_viscosity_temperature
        CHECK (temperature_min_k > 0 AND temperature_max_k > temperature_min_k),
    CONSTRAINT uq_melt_viscosity_model
        UNIQUE (dataset_id, model_id, source_version)
);

CREATE INDEX IF NOT EXISTS idx_melt_viscosity_model_approved
    ON metallurgy_v2.melt_viscosity_model_definition(model_id, is_approved);

COMMENT ON TABLE metallurgy_v2.melt_viscosity_model_definition IS
    'Versioned, approved public correlation definitions used by C008; runtime access is read-only.';
