"""Create metallurgy_literature database, schema, and tables."""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

conn = psycopg2.connect(host='127.0.0.1', port=5432, user='postgres', dbname='postgres')
conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
cur = conn.cursor()

# 1. Create database if not exists
cur.execute("SELECT 1 FROM pg_database WHERE datname = 'metallurgy_literature'")
if not cur.fetchone():
    cur.execute('CREATE DATABASE metallurgy_literature WITH ENCODING = "UTF8"')
    print("Created database: metallurgy_literature")
else:
    print("Database metallurgy_literature already exists")
cur.close()
conn.close()

# 2. Connect to new database and create schema + tables
conn = psycopg2.connect(host='127.0.0.1', port=5432, user='postgres', dbname='metallurgy_literature')
cur = conn.cursor()

cur.execute('CREATE SCHEMA IF NOT EXISTS literature')
print("Schema literature ready")

# Drop existing tables for clean creation (safe since new db)
tables_sql = """
CREATE TABLE IF NOT EXISTS literature.sources (
    source_id          BIGSERIAL PRIMARY KEY,
    source_name        VARCHAR(255) NOT NULL,
    source_type        VARCHAR(32) NOT NULL,
    provider           VARCHAR(255),
    access_url         TEXT,
    license_note       TEXT,
    security_level     VARCHAR(32) NOT NULL DEFAULT 'public',
    is_active          BOOLEAN NOT NULL DEFAULT TRUE,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS literature.documents (
    document_id        BIGSERIAL PRIMARY KEY,
    source_id          BIGINT REFERENCES literature.sources(source_id),
    document_code      VARCHAR(64) UNIQUE NOT NULL,
    title              TEXT NOT NULL,
    title_en           TEXT,
    document_type      VARCHAR(32) NOT NULL,
    abstract           TEXT,
    abstract_en        TEXT,
    journal_name       TEXT,
    conference_name    TEXT,
    publication_date   DATE,
    publication_year   INTEGER,
    volume             VARCHAR(32),
    issue              VARCHAR(32),
    pages              VARCHAR(32),
    doi                VARCHAR(255),
    standard_no        VARCHAR(128),
    patent_no          VARCHAR(128),
    source_url         TEXT,
    citation_text      TEXT,
    language           VARCHAR(16) NOT NULL DEFAULT 'zh-CN',
    security_level     VARCHAR(32) NOT NULL DEFAULT 'public',
    status             VARCHAR(32) NOT NULL DEFAULT 'draft',
    is_featured        BOOLEAN NOT NULL DEFAULT FALSE,
    published_at       TIMESTAMPTZ,
    created_by         VARCHAR(64),
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS literature.authors (
    author_id          BIGSERIAL PRIMARY KEY,
    author_name        VARCHAR(255) NOT NULL,
    author_name_en     VARCHAR(255),
    institution        TEXT,
    orcid              VARCHAR(64),
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS literature.document_authors (
    document_id        BIGINT NOT NULL
                       REFERENCES literature.documents(document_id)
                       ON DELETE CASCADE,
    author_id          BIGINT NOT NULL
                       REFERENCES literature.authors(author_id),
    author_order       INTEGER NOT NULL,
    is_corresponding   BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (document_id, author_id)
);

CREATE TABLE IF NOT EXISTS literature.domains (
    domain_code        VARCHAR(64) PRIMARY KEY,
    domain_name        VARCHAR(128) NOT NULL,
    description        TEXT,
    route_path         VARCHAR(255),
    sort_order         INTEGER NOT NULL DEFAULT 0,
    is_active          BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS literature.document_domains (
    document_id        BIGINT NOT NULL
                       REFERENCES literature.documents(document_id)
                       ON DELETE CASCADE,
    domain_code        VARCHAR(64) NOT NULL
                       REFERENCES literature.domains(domain_code),
    is_primary         BOOLEAN NOT NULL DEFAULT FALSE,
    sort_order         INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (document_id, domain_code)
);

CREATE TABLE IF NOT EXISTS literature.keywords (
    keyword_id         BIGSERIAL PRIMARY KEY,
    keyword_name       VARCHAR(128) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS literature.document_keywords (
    document_id        BIGINT NOT NULL
                       REFERENCES literature.documents(document_id)
                       ON DELETE CASCADE,
    keyword_id         BIGINT NOT NULL
                       REFERENCES literature.keywords(keyword_id),
    PRIMARY KEY (document_id, keyword_id)
);

CREATE TABLE IF NOT EXISTS literature.attachments (
    attachment_id      BIGSERIAL PRIMARY KEY,
    document_id        BIGINT NOT NULL
                       REFERENCES literature.documents(document_id)
                       ON DELETE CASCADE,
    file_name          TEXT NOT NULL,
    storage_uri        TEXT NOT NULL,
    mime_type          VARCHAR(128),
    file_size          BIGINT,
    checksum_sha256    VARCHAR(128),
    access_level       VARCHAR(32) NOT NULL DEFAULT 'restricted',
    can_download       BOOLEAN NOT NULL DEFAULT FALSE,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""

cur.execute(tables_sql)
print("All tables created")

# Seed 5 domains
domains_sql = """
INSERT INTO literature.domains
    (domain_code, domain_name, route_path, sort_order)
VALUES
    ('basic_principles', '冶金基础原理', '/basic-principles', 1),
    ('steel_metallurgy', '钢铁冶金', '/steel-metallurgy', 2),
    ('non_ferrous', '有色冶金', '/non-ferrous', 3),
    ('energy_restructuring', '冶金能源重构', '/energy-restructuring', 4),
    ('resource_utilization', '冶金资源利用', '/resource-utilization', 5)
ON CONFLICT (domain_code) DO NOTHING;
"""
cur.execute(domains_sql)

# Create indexes
indexes_sql = """
CREATE UNIQUE INDEX IF NOT EXISTS uq_documents_doi
    ON literature.documents(LOWER(doi))
    WHERE doi IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_documents_status
    ON literature.documents(status, security_level);

CREATE INDEX IF NOT EXISTS idx_documents_year
    ON literature.documents(publication_year DESC);

CREATE INDEX IF NOT EXISTS idx_documents_type
    ON literature.documents(document_type);

CREATE INDEX IF NOT EXISTS idx_documents_title
    ON literature.documents USING GIN
    (to_tsvector('simple', COALESCE(title, '') || ' ' || COALESCE(abstract, '')));
"""
cur.execute(indexes_sql)

conn.commit()

# Verify
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'literature' ORDER BY table_name")
tables = [r[0] for r in cur.fetchall()]
print(f"\nTables in literature schema ({len(tables)}):")
for t in tables:
    cur.execute(f"SELECT count(*) FROM information_schema.columns WHERE table_schema='literature' AND table_name='{t}'")
    cols = cur.fetchone()[0]
    print(f"  {t} ({cols} columns)")

cur.execute("SELECT domain_code, domain_name FROM literature.domains ORDER BY sort_order")
domains = cur.fetchall()
print(f"\nDomains ({len(domains)}):")
for d in domains:
    print(f"  {d[0]} -> {d[1]}")

# Check indexes
cur.execute("""
    SELECT indexname, indexdef FROM pg_indexes
    WHERE schemaname = 'literature'
    ORDER BY indexname
""")
indexes = cur.fetchall()
print(f"\nIndexes ({len(indexes)}):")
for idx in indexes:
    print(f"  {idx[0]}")

cur.close()
conn.close()
print("\nDone!")
