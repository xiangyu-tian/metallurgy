-- 30-tool milestone: additive, auditable reference-data support.
-- All statements are additive DDL for preserving existing records.

CREATE SCHEMA IF NOT EXISTS metallurgy_v2;

CREATE TABLE IF NOT EXISTS metallurgy_v2.dataset_import_run (
    run_id              UUID PRIMARY KEY,
    dataset_id          VARCHAR(64) NOT NULL,
    source_version      VARCHAR(128) NOT NULL,
    source_checksum     VARCHAR(128) NOT NULL,
    dry_run             BOOLEAN NOT NULL,
    status              VARCHAR(32) NOT NULL,
    staged_count        INTEGER NOT NULL DEFAULT 0,
    inserted_count      INTEGER NOT NULL DEFAULT 0,
    unchanged_count     INTEGER NOT NULL DEFAULT 0,
    conflict_count      INTEGER NOT NULL DEFAULT 0,
    details             JSONB NOT NULL DEFAULT '{}'::jsonb,
    started_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at        TIMESTAMP
);

CREATE TABLE IF NOT EXISTS metallurgy_v2.dataset_import_issue (
    id                  BIGSERIAL PRIMARY KEY,
    run_id              UUID NOT NULL REFERENCES metallurgy_v2.dataset_import_run(run_id),
    severity            VARCHAR(16) NOT NULL,
    natural_key         TEXT NOT NULL,
    issue_code          VARCHAR(64) NOT NULL,
    details             JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS metallurgy_v2.element_reference (
    id                  BIGSERIAL PRIMARY KEY,
    dataset_id          VARCHAR(64) NOT NULL REFERENCES metallurgy_v2.dataset_registry(dataset_id),
    symbol              VARCHAR(3) NOT NULL,
    atomic_weight_g_mol NUMERIC(18, 9) NOT NULL,
    unit                VARCHAR(32) NOT NULL DEFAULT 'g/mol',
    source_version      VARCHAR(128) NOT NULL,
    source_ref          TEXT NOT NULL,
    source_record_key   VARCHAR(255) NOT NULL,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    metadata            JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_element_weight_positive CHECK (atomic_weight_g_mol > 0),
    CONSTRAINT uq_element_reference UNIQUE (dataset_id, symbol, source_version)
);

CREATE INDEX IF NOT EXISTS idx_element_reference_active
    ON metallurgy_v2.element_reference(symbol, is_active);

CREATE TABLE IF NOT EXISTS metallurgy_v2.process_parameter_set (
    id                  BIGSERIAL PRIMARY KEY,
    dataset_id          VARCHAR(64) NOT NULL REFERENCES metallurgy_v2.dataset_registry(dataset_id),
    parameter_set_id    VARCHAR(64) NOT NULL,
    process             VARCHAR(64) NOT NULL,
    parameter_code      VARCHAR(128) NOT NULL,
    parameter_value     NUMERIC(24, 12) NOT NULL,
    unit                VARCHAR(64) NOT NULL,
    source_version      VARCHAR(128) NOT NULL,
    source_ref          TEXT NOT NULL,
    applicability       JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    metadata            JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_process_parameter UNIQUE
        (dataset_id, parameter_set_id, parameter_code, source_version)
);

CREATE INDEX IF NOT EXISTS idx_process_parameter_active
    ON metallurgy_v2.process_parameter_set(process, parameter_set_id, is_active);

ALTER TABLE metallurgy_v2.reaction_property
    ADD COLUMN IF NOT EXISTS source_version VARCHAR(128),
    ADD COLUMN IF NOT EXISTS source_record_key VARCHAR(255),
    ADD COLUMN IF NOT EXISTS temperature_min_k NUMERIC(12, 4),
    ADD COLUMN IF NOT EXISTS temperature_max_k NUMERIC(12, 4),
    ADD COLUMN IF NOT EXISTS metadata JSONB NOT NULL DEFAULT '{}'::jsonb;

CREATE UNIQUE INDEX IF NOT EXISTS uq_reaction_property_source_record
    ON metallurgy_v2.reaction_property(dataset_id, source_record_key)
    WHERE source_record_key IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_thermo_correlation_source_record
    ON metallurgy_v2.thermodynamic_correlation(
        source_id, source_record_key, species_id, phase, equation_type,
        temperature_min_k, temperature_max_k
    )
    WHERE source_id IS NOT NULL AND source_record_key IS NOT NULL;
