-- P0-W4: additive registry for versioned CALPHAD solidification assets.
-- This migration never alters or removes an existing scientific record.

CREATE SCHEMA IF NOT EXISTS metallurgy_v2;

CREATE TABLE IF NOT EXISTS metallurgy_v2.solidification_model_definition (
    id                      BIGSERIAL PRIMARY KEY,
    model_asset_id          VARCHAR(128) NOT NULL UNIQUE,
    dataset_id              VARCHAR(64) NOT NULL REFERENCES metallurgy_v2.dataset_registry(dataset_id),
    model_family            VARCHAR(128) NOT NULL,
    model_version           VARCHAR(128) NOT NULL,
    solver_name             VARCHAR(64) NOT NULL,
    solver_version          VARCHAR(32) NOT NULL,
    solidification_solver_name VARCHAR(64),
    solidification_solver_version VARCHAR(32),
    asset_uri               TEXT NOT NULL,
    asset_sha256            CHAR(64) NOT NULL,
    license                 TEXT NOT NULL,
    source_url              TEXT NOT NULL,
    source_commit           CHAR(40) NOT NULL,
    temperature_min_k       NUMERIC(12, 4) NOT NULL,
    temperature_max_k       NUMERIC(12, 4) NOT NULL,
    composition_basis       VARCHAR(96) NOT NULL,
    domain_json             JSONB NOT NULL,
    supported_components    JSONB NOT NULL,
    phase_set               JSONB NOT NULL,
    metadata                JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_approved             BOOLEAN NOT NULL DEFAULT FALSE,
    created_at              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_solidification_temperature_range
        CHECK (temperature_min_k > 0 AND temperature_max_k > temperature_min_k),
    CONSTRAINT chk_solidification_sha256
        CHECK (asset_sha256 ~ '^[0-9a-f]{64}$')
);

CREATE INDEX IF NOT EXISTS idx_solidification_model_approved
    ON metallurgy_v2.solidification_model_definition(model_asset_id, is_approved);

CREATE TABLE IF NOT EXISTS metallurgy_v2.solidification_benchmark_case (
    id                  BIGSERIAL PRIMARY KEY,
    benchmark_id        VARCHAR(128) NOT NULL UNIQUE,
    model_asset_id      VARCHAR(128) NOT NULL REFERENCES metallurgy_v2.solidification_model_definition(model_asset_id),
    composition_json    JSONB NOT NULL,
    reference_type      VARCHAR(64) NOT NULL,
    expected_json       JSONB NOT NULL,
    tolerance_json      JSONB NOT NULL,
    source_ref          TEXT NOT NULL,
    source_url          TEXT,
    within_domain       BOOLEAN NOT NULL,
    metadata            JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_solidification_benchmark_model
    ON metallurgy_v2.solidification_benchmark_case(model_asset_id, within_domain);
