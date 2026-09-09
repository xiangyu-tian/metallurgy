/**
 * 为文献库补充开放 PDF 附件，并可删除确认没有开放 PDF 的文献。
 *
 * 默认只审计，不写数据库：
 *   node sync_open_access_pdfs.js
 *
 * 写入附件：
 *   node sync_open_access_pdfs.js --apply
 *
 * 写入附件并删除确认无 PDF 的文献：
 *   node sync_open_access_pdfs.js --apply --delete-missing
 *
 * 使用 --delete-missing 时，明确无 PDF 以及查询失败的文献都会删除。
 */

const fs = require('fs');
const path = require('path');
const { Pool } = require('pg');

const APPLY = process.argv.includes('--apply');
const DELETE_MISSING = process.argv.includes('--delete-missing');
const REPORT_ARG = process.argv.find((arg) => arg.startsWith('--report='));
const REPORT_PATH = REPORT_ARG
  ? path.resolve(REPORT_ARG.slice('--report='.length))
  : path.resolve(__dirname, '../../logs/literature_pdf_audit.json');
const CONCURRENCY = Math.max(1, Math.min(10, parseInt(
  process.argv.find((arg) => arg.startsWith('--concurrency='))?.split('=')[1] || '4',
  10,
)));

const pool = new Pool({
  host: process.env.LITERATURE_DB_HOST || '127.0.0.1',
  port: parseInt(process.env.LITERATURE_DB_PORT || '5432', 10),
  database: process.env.LITERATURE_DB_NAME || 'metallurgy_literature',
  user: process.env.LITERATURE_DB_USER || 'postgres',
  password: process.env.LITERATURE_DB_PASSWORD || '',
  max: CONCURRENCY + 2,
});

function arxivPdfUrl(doc) {
  const candidates = [doc.source_url, doc.doi];
  for (const value of candidates) {
    if (!value) continue;
    const match = String(value).match(/(?:arxiv\.org\/abs\/|arxiv\.)([^?#]+)/i);
    if (!match) continue;
    const arxivId = match[1].replace(/v\d+$/i, '').replace(/\.pdf$/i, '');
    if (arxivId) return `https://arxiv.org/pdf/${arxivId}.pdf`;
  }
  return null;
}

function pickOpenAlexPdf(work) {
  const best = work?.best_oa_location;
  if (best?.is_oa && best?.pdf_url) {
    return { url: best.pdf_url, license: best.license || null, version: best.version || null };
  }

  const location = (work?.locations || []).find((item) => item?.is_oa && item?.pdf_url);
  if (!location) return null;
  return {
    url: location.pdf_url,
    license: location.license || null,
    version: location.version || null,
  };
}

async function fetchJson(url, attempts = 3) {
  let lastError;
  for (let attempt = 1; attempt <= attempts; attempt += 1) {
    try {
      const response = await fetch(url, {
        headers: { 'User-Agent': 'metallurgy-literature/1.0 (mailto:xiangyu@metallurgy.edu.cn)' },
        signal: AbortSignal.timeout(20000),
      });
      if (response.status === 404) return { notFound: true };
      if (response.status === 429 || response.status >= 500) {
        throw new Error(`OpenAlex HTTP ${response.status}`);
      }
      if (!response.ok) throw new Error(`OpenAlex HTTP ${response.status}`);
      return { data: await response.json() };
    } catch (error) {
      lastError = error;
      if (attempt < attempts) {
        await new Promise((resolve) => setTimeout(resolve, attempt * 1000));
      }
    }
  }
  throw lastError;
}

async function resolveDocument(doc) {
  if (doc.attachment_uri) {
    return { ...doc, result: 'existing', pdf_url: doc.attachment_uri };
  }

  const arxivUrl = arxivPdfUrl(doc);
  if (arxivUrl) {
    return { ...doc, result: 'found', pdf_url: arxivUrl, provider: 'arXiv' };
  }

  if (!doc.doi) {
    return { ...doc, result: 'missing', reason: 'no_doi' };
  }

  const workUrl = `https://api.openalex.org/works/https://doi.org/${encodeURIComponent(doc.doi)}`;
  try {
    const response = await fetchJson(workUrl);
    if (response.notFound) {
      return { ...doc, result: 'missing', reason: 'openalex_not_found' };
    }
    const pdf = pickOpenAlexPdf(response.data);
    if (!pdf) {
      return { ...doc, result: 'missing', reason: 'no_open_pdf' };
    }
    return {
      ...doc,
      result: 'found',
      pdf_url: pdf.url,
      license: pdf.license,
      version: pdf.version,
      provider: 'OpenAlex',
    };
  } catch (error) {
    return { ...doc, result: 'error', reason: error.message };
  }
}

async function mapConcurrent(items, limit, mapper) {
  const results = new Array(items.length);
  let next = 0;
  async function worker() {
    while (true) {
      const index = next;
      next += 1;
      if (index >= items.length) return;
      results[index] = await mapper(items[index]);
      if ((index + 1) % 25 === 0 || index + 1 === items.length) {
        process.stdout.write(`\r已检查 ${index + 1}/${items.length}`);
      }
    }
  }
  await Promise.all(Array.from({ length: limit }, worker));
  process.stdout.write('\n');
  return results;
}

async function applyChanges(results) {
  const found = results.filter((item) => item.result === 'found');
  const removable = results.filter((item) => item.result === 'missing' || item.result === 'error');
  const client = await pool.connect();
  try {
    await client.query('BEGIN');

    for (const item of found) {
      await client.query(`
        INSERT INTO literature.attachments
          (document_id, file_name, storage_uri, mime_type, access_level, can_download)
        SELECT $1, $2, $3, 'application/pdf', 'public', true
        WHERE NOT EXISTS (
          SELECT 1 FROM literature.attachments
          WHERE document_id = $1 AND mime_type = 'application/pdf'
        )
      `, [item.document_id, `${item.document_code}.pdf`, item.pdf_url]);
    }

    let deleted = 0;
    if (DELETE_MISSING && removable.length > 0) {
      const ids = removable.map((item) => item.document_id);
      const deletion = await client.query(
        'DELETE FROM literature.documents WHERE document_id = ANY($1::bigint[])',
        [ids],
      );
      deleted = deletion.rowCount;

      await client.query(`
        DELETE FROM literature.authors a
        WHERE NOT EXISTS (
          SELECT 1 FROM literature.document_authors da WHERE da.author_id = a.author_id
        )
      `);
      await client.query(`
        DELETE FROM literature.keywords k
        WHERE NOT EXISTS (
          SELECT 1 FROM literature.document_keywords dk WHERE dk.keyword_id = k.keyword_id
        )
      `);
    }

    await client.query('COMMIT');
    return { attachmentsInsertedOrPresent: found.length, deleted };
  } catch (error) {
    await client.query('ROLLBACK');
    throw error;
  } finally {
    client.release();
  }
}

async function main() {
  const query = await pool.query(`
    SELECT d.document_id, d.document_code, d.title, d.doi, d.source_url,
           s.source_name,
           a.storage_uri AS attachment_uri
    FROM literature.documents d
    LEFT JOIN literature.sources s ON s.source_id = d.source_id
    LEFT JOIN LATERAL (
      SELECT storage_uri
      FROM literature.attachments
      WHERE document_id = d.document_id AND mime_type = 'application/pdf'
      ORDER BY attachment_id
      LIMIT 1
    ) a ON true
    ORDER BY d.document_id
  `);

  console.log(`文献总数: ${query.rows.length}; 并发数: ${CONCURRENCY}; 模式: ${APPLY ? '写入' : '只读审计'}`);
  const results = await mapConcurrent(query.rows, CONCURRENCY, resolveDocument);
  const summary = results.reduce((acc, item) => {
    acc[item.result] = (acc[item.result] || 0) + 1;
    return acc;
  }, {});

  const report = {
    generated_at: new Date().toISOString(),
    mode: APPLY ? 'apply' : 'audit',
    delete_missing: DELETE_MISSING,
    summary,
    found: results.filter((item) => item.result === 'found'),
    missing: results.filter((item) => item.result === 'missing'),
    errors: results.filter((item) => item.result === 'error'),
    delete_candidates: results.filter((item) => item.result === 'missing' || item.result === 'error'),
    existing: results.filter((item) => item.result === 'existing'),
  };
  fs.mkdirSync(path.dirname(REPORT_PATH), { recursive: true });
  fs.writeFileSync(REPORT_PATH, JSON.stringify(report, null, 2), 'utf8');
  console.log('审计汇总:', summary);
  console.log(`报告: ${REPORT_PATH}`);

  if (APPLY) {
    const applied = await applyChanges(results);
    console.log('数据库变更:', applied);
  } else {
    console.log('当前为 dry-run；未修改数据库。');
  }
}

main()
  .catch((error) => {
    console.error('PDF 同步失败:', error);
    process.exitCode = 1;
  })
  .finally(() => pool.end());
