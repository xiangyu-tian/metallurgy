-- P1-W5C-Data: additive casting-machine configuration and endpoint benchmarks.
-- This migration never alters or removes an existing scientific record.

CREATE SCHEMA IF NOT EXISTS metallurgy_v2;

CREATE TABLE IF NOT EXISTS metallurgy_v2.casting_machine_configuration (
    id                              BIGSERIAL PRIMARY KEY,
    machine_configuration_id        VARCHAR(160) NOT NULL UNIQUE,
    dataset_id                      VARCHAR(64) NOT NULL
        REFERENCES metallurgy_v2.dataset_registry(dataset_id),
    equipment_id                    VARCHAR(128) NOT NULL,
    configuration_name              VARCHAR(255) NOT NULL,
    configuration_version           VARCHAR(128) NOT NULL,
    section_shape                   VARCHAR(32) NOT NULL,
    section_width_m                 NUMERIC(16, 8) NOT NULL,
    section_thickness_m             NUMERIC(16, 8) NOT NULL,
    mold_length_m                   NUMERIC(16, 8) NOT NULL,
    effective_metallurgical_length_m NUMERIC(16, 8) NOT NULL,
    casting_speed_min_m_s           NUMERIC(16, 8) NOT NULL,
    casting_speed_max_m_s           NUMERIC(16, 8) NOT NULL,
    unit_system                     VARCHAR(16) NOT NULL DEFAULT 'SI',
    usage_scope                     VARCHAR(64) NOT NULL,
    source_kind                     VARCHAR(64) NOT NULL,
    source_ref                      TEXT NOT NULL,
    source_url                      TEXT,
    license                         TEXT NOT NULL,
    uncertainty_json                JSONB NOT NULL DEFAULT '{}'::jsonb,
    metadata                        JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_approved                     BOOLEAN NOT NULL DEFAULT FALSE,
    created_at                      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_casting_machine_geometry CHECK (
        section_width_m > 0 AND section_thickness_m > 0
        AND mold_length_m > 0
        AND effective_metallurgical_length_m >= mold_length_m
    ),
    CONSTRAINT chk_casting_machine_speed CHECK (
        casting_speed_min_m_s > 0
        AND casting_speed_max_m_s > casting_speed_min_m_s
    )
);

CREATE INDEX IF NOT EXISTS idx_casting_machine_configuration_approved
    ON metallurgy_v2.casting_machine_configuration(
        machine_configuration_id, is_approved, usage_scope
    );

CREATE TABLE IF NOT EXISTS metallurgy_v2.casting_endpoint_benchmark_case (
    id                              BIGSERIAL PRIMARY KEY,
    benchmark_id                    VARCHAR(160) NOT NULL UNIQUE,
    dataset_id                      VARCHAR(64) NOT NULL
        REFERENCES metallurgy_v2.dataset_registry(dataset_id),
    model_code                      VARCHAR(32) NOT NULL,
    machine_configuration_id        VARCHAR(160) NOT NULL
        REFERENCES metallurgy_v2.casting_machine_configuration(machine_configuration_id),
    reference_type                  VARCHAR(96) NOT NULL,
    input_json                      JSONB NOT NULL,
    expected_json                   JSONB NOT NULL,
    tolerance_json                  JSONB NOT NULL,
    source_ref                      TEXT NOT NULL,
    source_url                      TEXT,
    within_domain                   BOOLEAN NOT NULL,
    metadata                        JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at                      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_casting_endpoint_benchmark_model
    ON metallurgy_v2.casting_endpoint_benchmark_case(model_code, within_domain);
