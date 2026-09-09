-- Google Scholar 发现来源与引用信息
ALTER TABLE literature.documents
    ADD COLUMN IF NOT EXISTS discovery_source VARCHAR(64),
    ADD COLUMN IF NOT EXISTS scholar_citation_count INTEGER,
    ADD COLUMN IF NOT EXISTS scholar_url TEXT,
    ADD COLUMN IF NOT EXISTS scholar_checked_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_documents_scholar_citations
    ON literature.documents(scholar_citation_count DESC)
    WHERE scholar_citation_count IS NOT NULL;
