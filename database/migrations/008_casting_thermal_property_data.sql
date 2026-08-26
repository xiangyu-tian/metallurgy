-- P1-W5B-Data: additive casting thermal-property, boundary and benchmark data.
-- This migration never alters or removes an existing scientific record.

CREATE SCHEMA IF NOT EXISTS metallurgy_v2;

CREATE TABLE IF NOT EXISTS metallurgy_v2.casting_material_property_set (
    id                          BIGSERIAL PRIMARY KEY,
    property_set_id             VARCHAR(128) NOT NULL UNIQUE,
    dataset_id                  VARCHAR(64) NOT NULL REFERENCES metallurgy_v2.dataset_registry(dataset_id),
    material_name               VARCHAR(255) NOT NULL,
    material_grade              VARCHAR(128) NOT NULL,
    reference_material_id       VARCHAR(128),
    property_set_version        VARCHAR(128) NOT NULL,
    composition_basis           VARCHAR(96) NOT NULL,
    composition_json            JSONB NOT NULL,
    temperature_min_k           NUMERIC(12, 4) NOT NULL,
    temperature_max_k           NUMERIC(12, 4) NOT NULL,
    solidus_temperature_k       NUMERIC(12, 4),
    liquidus_temperature_k      NUMERIC(12, 4),
    phase_model                 VARCHAR(128) NOT NULL,
    unit_system                 VARCHAR(16) NOT NULL DEFAULT 'SI',
    usage_scope                 VARCHAR(64) NOT NULL,
    source_ref                  TEXT NOT NULL,
    source_url                  TEXT,
    license                     TEXT NOT NULL,
    uncertainty_json            JSONB NOT NULL DEFAULT '{}'::jsonb,
    metadata                    JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_approved                 BOOLEAN NOT NULL DEFAULT FALSE,
    created_at                  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_casting_property_set_temperature
        CHECK (temperature_min_k > 0 AND temperature_max_k > temperature_min_k),
    CONSTRAINT chk_casting_property_set_phase_endpoints
        CHECK (
            (solidus_temperature_k IS NULL AND liquidus_temperature_k IS NULL)
            OR
            (solidus_temperature_k IS NOT NULL AND liquidus_temperature_k IS NOT NULL
             AND solidus_temperature_k >= temperature_min_k
             AND liquidus_temperature_k <= temperature_max_k
             AND liquidus_temperature_k > solidus_temperature_k)
        )
);

CREATE INDEX IF NOT EXISTS idx_casting_property_set_approved
    ON metallurgy_v2.casting_material_property_set(property_set_id, is_approved);

CREATE TABLE IF NOT EXISTS metallurgy_v2.casting_material_property_correlation (
    id                          BIGSERIAL PRIMARY KEY,
    correlation_id              VARCHAR(160) NOT NULL UNIQUE,
    property_set_id             VARCHAR(128) NOT NULL
        REFERENCES metallurgy_v2.casting_material_property_set(property_set_id),
    property_type               VARCHAR(64) NOT NULL,
    equation_type               VARCHAR(96) NOT NULL,
    phase                       VARCHAR(32) NOT NULL,
    temperature_min_k           NUMERIC(12, 4) NOT NULL,
    temperature_max_k           NUMERIC(12, 4) NOT NULL,
    input_unit                  VARCHAR(32) NOT NULL,
    output_unit                 VARCHAR(64) NOT NULL,
    coefficients                JSONB NOT NULL,
    uncertainty_json            JSONB NOT NULL DEFAULT '{}'::jsonb,
    source_kind                 VARCHAR(64) NOT NULL,
    source_ref                  TEXT NOT NULL,
    source_url                  TEXT,
    source_record_key           VARCHAR(255) NOT NULL,
    priority                    INTEGER NOT NULL DEFAULT 100,
    metadata                    JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_active                   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at                  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_casting_correlation_temperature
        CHECK (temperature_min_k > 0 AND temperature_max_k > temperature_min_k),
    CONSTRAINT chk_casting_correlation_priority CHECK (priority > 0),
    CONSTRAINT uq_casting_correlation_source
        UNIQUE (property_set_id, source_record_key)
);

CREATE INDEX IF NOT EXISTS idx_casting_correlation_lookup
    ON metallurgy_v2.casting_material_property_correlation(
        property_set_id, property_type, temperature_min_k, temperature_max_k, is_active, priority
    );

CREATE TABLE IF NOT EXISTS metallurgy_v2.casting_boundary_profile (
    id                          BIGSERIAL PRIMARY KEY,
    boundary_profile_id         VARCHAR(160) NOT NULL UNIQUE,
    dataset_id                  VARCHAR(64) NOT NULL REFERENCES metallurgy_v2.dataset_registry(dataset_id),
    property_set_id             VARCHAR(128)
        REFERENCES metallurgy_v2.casting_material_property_set(property_set_id),
    profile_name                VARCHAR(255) NOT NULL,
    profile_type                VARCHAR(64) NOT NULL,
    independent_variable        VARCHAR(32) NOT NULL,
    profile_version             VARCHAR(128) NOT NULL,
    domain_min                  NUMERIC(20, 8) NOT NULL,
    domain_max                  NUMERIC(20, 8) NOT NULL,
    independent_unit            VARCHAR(32) NOT NULL,
    value_unit                  VARCHAR(64) NOT NULL,
    profile_json                JSONB NOT NULL,
    equipment_scope             JSONB NOT NULL DEFAULT '{}'::jsonb,
    source_kind                 VARCHAR(64) NOT NULL,
    source_ref                  TEXT NOT NULL,
    source_url                  TEXT,
    license                     TEXT NOT NULL,
    usage_scope                 VARCHAR(64) NOT NULL,
    metadata                    JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_approved                 BOOLEAN NOT NULL DEFAULT FALSE,
    created_at                  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_casting_boundary_domain CHECK (domain_max > domain_min)
);

CREATE INDEX IF NOT EXISTS idx_casting_boundary_approved
    ON metallurgy_v2.casting_boundary_profile(boundary_profile_id, profile_type, is_approved);

CREATE TABLE IF NOT EXISTS metallurgy_v2.casting_model_benchmark_case (
    id                          BIGSERIAL PRIMARY KEY,
    benchmark_id                VARCHAR(160) NOT NULL UNIQUE,
    model_code                  VARCHAR(32) NOT NULL,
    property_set_id             VARCHAR(128) NOT NULL
        REFERENCES metallurgy_v2.casting_material_property_set(property_set_id),
    boundary_profile_id         VARCHAR(160)
        REFERENCES metallurgy_v2.casting_boundary_profile(boundary_profile_id),
    reference_type              VARCHAR(96) NOT NULL,
    input_json                  JSONB NOT NULL,
    expected_json               JSONB NOT NULL,
    tolerance_json              JSONB NOT NULL,
    source_ref                  TEXT NOT NULL,
    source_url                  TEXT,
    within_domain               BOOLEAN NOT NULL,
    metadata                    JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at                  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_casting_benchmark_model
    ON metallurgy_v2.casting_model_benchmark_case(model_code, within_domain);
