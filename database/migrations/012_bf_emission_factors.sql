-- P1-W15: additive storage for public, versioned E020 emission factors.
-- Existing tables and rows are never altered, updated or deleted.

CREATE SCHEMA IF NOT EXISTS metallurgy_v2;

CREATE TABLE IF NOT EXISTS metallurgy_v2.emission_factor (
    id                  BIGSERIAL PRIMARY KEY,
    dataset_id          VARCHAR(64) NOT NULL REFERENCES metallurgy_v2.dataset_registry(dataset_id),
    factor_set_id       VARCHAR(128) NOT NULL,
    factor_code         VARCHAR(160) NOT NULL,
    activity_name       TEXT NOT NULL,
    activity_unit       VARCHAR(32) NOT NULL,
    scope               VARCHAR(16) NOT NULL,
    co2_kg_per_unit     NUMERIC(24, 10),
    ch4_kg_per_unit     NUMERIC(24, 10),
    n2o_kg_per_unit     NUMERIC(24, 10),
    co2e_kg_per_unit    NUMERIC(24, 10),
    gwp_ch4             NUMERIC(12, 6),
    gwp_n2o             NUMERIC(12, 6),
    methodology         TEXT NOT NULL,
    applicability       JSONB NOT NULL DEFAULT '{}'::jsonb,
    source_version      VARCHAR(160) NOT NULL,
    source_ref          TEXT NOT NULL,
    source_url          TEXT NOT NULL,
    is_approved         BOOLEAN NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_emission_factor_scope CHECK (scope IN ('scope1', 'scope2', 'scope3')),
    CONSTRAINT chk_emission_factor_nonnegative CHECK (
        (co2_kg_per_unit IS NULL OR co2_kg_per_unit >= 0) AND
        (ch4_kg_per_unit IS NULL OR ch4_kg_per_unit >= 0) AND
        (n2o_kg_per_unit IS NULL OR n2o_kg_per_unit >= 0) AND
        (co2e_kg_per_unit IS NULL OR co2e_kg_per_unit >= 0)
    ),
    CONSTRAINT chk_emission_factor_payload CHECK (
        co2e_kg_per_unit IS NOT NULL OR
        (co2_kg_per_unit IS NOT NULL AND ch4_kg_per_unit IS NOT NULL AND
         n2o_kg_per_unit IS NOT NULL AND gwp_ch4 IS NOT NULL AND gwp_n2o IS NOT NULL)
    ),
    CONSTRAINT uq_emission_factor UNIQUE (dataset_id, factor_set_id, factor_code, source_version)
);

CREATE INDEX IF NOT EXISTS idx_emission_factor_approved
    ON metallurgy_v2.emission_factor(factor_set_id, factor_code, is_approved);

COMMENT ON TABLE metallurgy_v2.emission_factor IS
    'Versioned public activity emission factors used by E020; runtime access is read-only.';
