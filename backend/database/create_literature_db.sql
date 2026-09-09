-- ============================================================
-- 冶金专业文献库 — 数据库初始化脚本
-- 数据库：metallurgy_literature
-- Schema： literature
-- 说明：按顺序执行即可创建完整的文献库结构
-- ============================================================

-- ==================== 第一部分：创建数据库 ====================
-- 注意：这部分需要以超级用户身份执行
-- 如果数据库已存在则跳过

-- CREATE DATABASE metallurgy_literature
--     WITH ENCODING = 'UTF8'
--          LC_COLLATE = 'Chinese_China.936'
--          LC_CTYPE = 'Chinese_China.936';

-- ==================== 第二部分：创建 Schema 和账号 ====================

-- 连接到 metallurgy_literature 后再执行以下内容
-- \c metallurgy_literature

-- 创建专用 Schema
CREATE SCHEMA IF NOT EXISTS literature;

-- ==================== 第三部分：建表 ====================

-- 3.1 文献来源表
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

COMMENT ON TABLE literature.sources IS '文献来源（期刊/会议/标准平台/专利平台等）';
COMMENT ON COLUMN literature.sources.source_type IS '取值：journal, conference, standard_platform, patent_platform, internal, manual_import';
COMMENT ON COLUMN literature.sources.security_level IS '取值：public, internal, confidential';

-- 3.2 文献主表
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
    discovery_source   VARCHAR(64),
    scholar_citation_count INTEGER,
    scholar_url        TEXT,
    scholar_checked_at TIMESTAMPTZ,
    language           VARCHAR(16) NOT NULL DEFAULT 'zh-CN',
    security_level     VARCHAR(32) NOT NULL DEFAULT 'public',
    status             VARCHAR(32) NOT NULL DEFAULT 'draft',
    is_featured        BOOLEAN NOT NULL DEFAULT FALSE,
    published_at       TIMESTAMPTZ,
    created_by         VARCHAR(64),
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE literature.documents IS '文献主表，存储论文/标准/专利/报告等元数据';
COMMENT ON COLUMN literature.documents.document_type IS '取值：paper, standard, patent, report, book, manual';
COMMENT ON COLUMN literature.documents.status IS '取值：draft, pending_review, published, archived';
COMMENT ON COLUMN literature.documents.document_code IS '自动生成的唯一文献编号，如 LIT-000001';

-- 文献编号序列
CREATE SEQUENCE IF NOT EXISTS literature.document_code_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

-- 自动生成 document_code 的函数
CREATE OR REPLACE FUNCTION literature.generate_document_code()
RETURNS TRIGGER AS $$
BEGIN
    NEW.document_code := 'LIT-' || LPAD(NEXTVAL('literature.document_code_seq')::TEXT, 6, '0');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 触发器：插入时自动生成编号
DROP TRIGGER IF EXISTS trg_documents_code ON literature.documents;
CREATE TRIGGER trg_documents_code
    BEFORE INSERT ON literature.documents
    FOR EACH ROW
    WHEN (NEW.document_code IS NULL)
    EXECUTE FUNCTION literature.generate_document_code();

-- 自动更新 updated_at 的函数
CREATE OR REPLACE FUNCTION literature.update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 触发器：更新时自动更新时间戳（documents）
DROP TRIGGER IF EXISTS trg_documents_updated_at ON literature.documents;
CREATE TRIGGER trg_documents_updated_at
    BEFORE UPDATE ON literature.documents
    FOR EACH ROW
    EXECUTE FUNCTION literature.update_timestamp();

-- 触发器：更新时自动更新时间戳（sources）
DROP TRIGGER IF EXISTS trg_sources_updated_at ON literature.sources;
CREATE TRIGGER trg_sources_updated_at
    BEFORE UPDATE ON literature.sources
    FOR EACH ROW
    EXECUTE FUNCTION literature.update_timestamp();

-- 3.3 作者表
CREATE TABLE IF NOT EXISTS literature.authors (
    author_id          BIGSERIAL PRIMARY KEY,
    author_name        VARCHAR(255) NOT NULL,
    author_name_en     VARCHAR(255),
    institution        TEXT,
    orcid              VARCHAR(64),
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE literature.authors IS '作者信息，与文献通过关系表关联';

-- 3.4 文献作者关系表
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

COMMENT ON TABLE literature.document_authors IS '文献与作者的多对多关系，含排序和通讯作者标记';

-- 3.5 研究领域表
CREATE TABLE IF NOT EXISTS literature.domains (
    domain_code        VARCHAR(64) PRIMARY KEY,
    domain_name        VARCHAR(128) NOT NULL,
    description        TEXT,
    route_path         VARCHAR(255),
    sort_order         INTEGER NOT NULL DEFAULT 0,
    is_active          BOOLEAN NOT NULL DEFAULT TRUE
);

COMMENT ON TABLE literature.domains IS '研究领域分类，与现有5个研究领域页面对应';

-- 初始化5个研究领域
INSERT INTO literature.domains (domain_code, domain_name, route_path, sort_order)
VALUES
    ('basic_principles', '冶金基础原理', '/basic-principles', 1),
    ('steel_metallurgy', '钢铁冶金', '/steel-metallurgy', 2),
    ('non_ferrous', '有色冶金', '/non-ferrous', 3),
    ('energy_restructuring', '冶金能源重构', '/energy-restructuring', 4),
    ('resource_utilization', '冶金资源利用', '/resource-utilization', 5)
ON CONFLICT (domain_code) DO NOTHING;

-- 3.6 文献领域关系表
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

COMMENT ON TABLE literature.document_domains IS '文献与研究领域的多对多关系，一篇文献可属于多个领域';

-- 3.7 关键词表
CREATE TABLE IF NOT EXISTS literature.keywords (
    keyword_id         BIGSERIAL PRIMARY KEY,
    keyword_name       VARCHAR(128) UNIQUE NOT NULL
);

COMMENT ON TABLE literature.keywords IS '关键词字典，去重存储';

-- 3.8 文献关键词关系表
CREATE TABLE IF NOT EXISTS literature.document_keywords (
    document_id        BIGINT NOT NULL
                       REFERENCES literature.documents(document_id)
                       ON DELETE CASCADE,
    keyword_id         BIGINT NOT NULL
                       REFERENCES literature.keywords(keyword_id),
    PRIMARY KEY (document_id, keyword_id)
);

COMMENT ON TABLE literature.document_keywords IS '文献与关键词的多对多关系';

-- 3.9 附件信息表
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

COMMENT ON TABLE literature.attachments IS '附件存储信息，二进制文件不入库，只存路径';

-- ==================== 第四部分：索引 ====================

-- DOI 唯一索引（忽略 NULL）
CREATE UNIQUE INDEX IF NOT EXISTS uq_documents_doi
    ON literature.documents(LOWER(doi))
    WHERE doi IS NOT NULL;

-- 对外查询的核心索引：状态 + 安全级别
CREATE INDEX IF NOT EXISTS idx_documents_status
    ON literature.documents(status, security_level);

-- 按年份倒序排列
CREATE INDEX IF NOT EXISTS idx_documents_year
    ON literature.documents(publication_year DESC);

-- 按文献类型筛选
CREATE INDEX IF NOT EXISTS idx_documents_type
    ON literature.documents(document_type);

-- 全文检索索引（标题 + 摘要，简单分词）
CREATE INDEX IF NOT EXISTS idx_documents_title_abstract
    ON literature.documents USING GIN
    (to_tsvector('simple', COALESCE(title, '') || ' ' || COALESCE(abstract, '')));

-- 推荐文献快速查询
CREATE INDEX IF NOT EXISTS idx_documents_featured
    ON literature.documents(is_featured, status, security_level);

-- 来源ID索引
CREATE INDEX IF NOT EXISTS idx_documents_source
    ON literature.documents(source_id);

-- 作者名检索索引
CREATE INDEX IF NOT EXISTS idx_authors_name
    ON literature.authors(author_name);

-- ==================== 第五部分：账号与权限 ====================

-- 创建只读账号（对外接口使用）
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'literature_reader') THEN
        CREATE ROLE literature_reader WITH LOGIN PASSWORD 'literature_reader_2026';
    END IF;
END
$$;

-- 创建读写账号（后台管理使用）
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'literature_admin') THEN
        CREATE ROLE literature_admin WITH LOGIN PASSWORD 'literature_admin_2026';
    END IF;
END
$$;

-- 授予连接权限
GRANT CONNECT ON DATABASE metallurgy_literature TO literature_reader, literature_admin;

-- 授予 Schema 使用权限
GRANT USAGE ON SCHEMA literature TO literature_reader, literature_admin;

-- 只读账号：仅 SELECT
GRANT SELECT ON ALL TABLES IN SCHEMA literature TO literature_reader;

-- 读写账号：增删改查
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA literature TO literature_admin;

-- 序列权限（读写账号需要）
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA literature TO literature_admin;

-- 默认权限：未来新建的表也自动授权
ALTER DEFAULT PRIVILEGES IN SCHEMA literature
    GRANT SELECT ON TABLES TO literature_reader;

ALTER DEFAULT PRIVILEGES IN SCHEMA literature
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO literature_admin;

ALTER DEFAULT PRIVILEGES IN SCHEMA literature
    GRANT USAGE, SELECT ON SEQUENCES TO literature_admin;

-- ==================== 第六部分：验证查询 ====================

-- 执行以下语句验证建库结果：
-- SELECT table_schema, table_name
-- FROM information_schema.tables
-- WHERE table_schema = 'literature'
-- ORDER BY table_name;

-- SELECT * FROM literature.domains ORDER BY sort_order;
