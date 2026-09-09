/**
 * 从 OpenAlex 导入有开放 PDF 且通过冶金领域关键词校验的论文。
 * 默认 dry-run；传入 --apply 才写数据库。
 *
 * 用法：node import_openalex_oa_curated.js --apply --rows=20
 */

const { Pool } = require('pg');

const APPLY = process.argv.includes('--apply');
const ROWS_PER_DOMAIN = Math.max(1, Math.min(50, parseInt(
  process.argv.find((arg) => arg.startsWith('--rows='))?.split('=')[1] || '20',
  10,
)));
const DOMAIN_FILTER = process.argv.find((arg) => arg.startsWith('--domains='))?.split('=')[1] || null;

const DOMAIN_CONFIG = {
  basic_principles: {
    searches: [
      'CALPHAD alloy phase diagram thermodynamics',
      'metallurgical thermodynamics diffusion phase transformation',
    ],
    required: [
      /\bcalphad\b/i, /phase[- ]?diagram/i, /thermodynamic/i, /phase[- ]?field/i,
      /phase transformation/i, /diffusion/i, /metallurg/i, /alloy/i,
    ],
  },
  steel_metallurgy: {
    searches: [
      'steelmaking ironmaking blast furnace electric arc furnace',
      'continuous casting steel direct reduction iron',
    ],
    required: [
      /steelmak/i, /ironmak/i, /blast furnace/i, /electric arc furnace/i, /\bEAF\b/,
      /\bBOF\b/, /continuous cast/i, /direct reduction/i, /steel slag/i,
    ],
  },
  non_ferrous: {
    searches: [
      'hydrometallurgy nonferrous metal extraction leaching',
      'copper aluminum zinc nickel smelting refining metallurgy',
    ],
    required: [
      /hydrometallurg/i, /pyrometallurg/i, /non[- ]?ferrous/i, /solvent extraction/i,
      /metal leach/i, /copper smelt/i, /alumin(?:um|ium) electrolysis/i,
      /(?:zinc|nickel|cobalt|titanium|magnesium).{0,30}(?:extract|smelt|refin|recover|leach)/i,
    ],
  },
  energy_restructuring: {
    searches: [
      'steel decarbonization hydrogen direct reduction',
      'carbon capture steel industry energy efficiency metallurgy',
    ],
    required: [
      /steel decarboni/i, /low[- ]carbon steel/i, /green hydrogen/i,
      /hydrogen.{0,30}(?:direct reduction|ironmaking|steelmaking)/i,
      /carbon capture.{0,40}(?:steel|iron|metallurg)/i, /\bCCUS\b/i,
      /energy efficiency.{0,40}(?:steel|furnace|metallurg)/i,
    ],
  },
  resource_utilization: {
    searches: [
      'metallurgical slag recycling resource utilization',
      'steel dust waste recovery circular economy metallurgy',
    ],
    required: [
      /metallurgical slag/i, /steel slag/i, /blast furnace slag/i,
      /steelmak(?:ing)? dust/i, /metallurgical waste/i,
      /(?:slag|red mud|steel dust|metallurgical dust).{0,40}(?:recycl|utili|recover|valor)/i,
      /resource recovery.{0,40}metallurg/i,
    ],
  },
};

const pool = new Pool({
  host: process.env.LITERATURE_DB_HOST || '127.0.0.1',
  port: parseInt(process.env.LITERATURE_DB_PORT || '5432', 10),
  database: process.env.LITERATURE_DB_NAME || 'metallurgy_literature',
  user: process.env.LITERATURE_DB_USER || 'postgres',
  password: process.env.LITERATURE_DB_PASSWORD || '',
  max: 5,
});

function invertAbstract(index) {
  if (!index) return null;
  const words = [];
  for (const [word, positions] of Object.entries(index)) {
    for (const position of positions) words[position] = word;
  }
  return words.filter(Boolean).join(' ').slice(0, 10000) || null;
}

function normalizeDoi(value) {
  return value ? value.replace(/^https?:\/\/(?:dx\.)?doi\.org\//i, '').trim().toLowerCase() : null;
}

function findPdf(work) {
  if (work.best_oa_location?.is_oa && work.best_oa_location?.pdf_url) {
    return work.best_oa_location.pdf_url;
  }
  return work.locations?.find((location) => location?.is_oa && location?.pdf_url)?.pdf_url || null;
}

function isRelevant(domainCode, work) {
  const config = DOMAIN_CONFIG[domainCode];
  const abstract = invertAbstract(work.abstract_inverted_index) || '';
  const text = `${work.title || ''}\n${abstract}`;
  return config.required.some((pattern) => pattern.test(text));
}

async function searchOpenAlex(search) {
  const params = new URLSearchParams({
    search,
    filter: 'has_pdf_url:true,is_oa:true,from_publication_date:2015-01-01,type:article',
    sort: 'relevance_score:desc',
    'per-page': '50',
    mailto: 'xiangyu@metallurgy.edu.cn',
  });
  const response = await fetch(`https://api.openalex.org/works?${params}`, {
    headers: { 'User-Agent': 'metallurgy-literature/1.0 (mailto:xiangyu@metallurgy.edu.cn)' },
    signal: AbortSignal.timeout(30000),
  });
  if (!response.ok) throw new Error(`OpenAlex HTTP ${response.status}`);
  return (await response.json()).results || [];
}

async function ensureSource(client) {
  const existing = await client.query(
    "SELECT source_id FROM literature.sources WHERE source_name = 'OpenAlex OA Curated' LIMIT 1",
  );
  if (existing.rows.length) return existing.rows[0].source_id;
  const inserted = await client.query(`
    INSERT INTO literature.sources (source_name, source_type, provider, access_url, license_note)
    VALUES ('OpenAlex OA Curated', 'journal', 'OpenAlex', 'https://openalex.org',
            '仅导入 OpenAlex 标记为开放获取且提供 pdf_url 的记录')
    RETURNING source_id
  `);
  return inserted.rows[0].source_id;
}

async function insertWork(client, sourceId, domainCode, work, pdfUrl) {
  const doi = normalizeDoi(work.doi);
  if (!doi) return 'no_doi';
  const duplicate = await client.query(
    'SELECT document_id FROM literature.documents WHERE LOWER(doi) = $1 LIMIT 1',
    [doi],
  );
  if (duplicate.rows.length) return 'duplicate';

  const title = (work.title || '').trim().slice(0, 2000);
  if (!title) return 'no_title';
  const abstract = invertAbstract(work.abstract_inverted_index);
  const journal = work.primary_location?.source?.display_name?.slice(0, 1000) || null;
  const biblio = work.biblio || {};
  const citation = [
    (work.authorships || []).map((a) => a.author?.display_name).filter(Boolean).join(', '),
    work.publication_year ? `(${work.publication_year})` : null,
    title,
    journal,
    `https://doi.org/${doi}`,
  ].filter(Boolean).join('. ');

  await client.query('BEGIN');
  try {
    const inserted = await client.query(`
      INSERT INTO literature.documents
        (source_id, title, document_type, abstract, journal_name, publication_year,
         volume, issue, pages, doi, source_url, citation_text, language,
         status, security_level, is_featured, published_at, created_by)
      VALUES ($1,$2,'paper',$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,
              'published','public',$13,NOW(),'openalex_oa_curated')
      RETURNING document_id, document_code
    `, [
      sourceId, title, abstract, journal, work.publication_year || null,
      biblio.volume || null, biblio.issue || null,
      [biblio.first_page, biblio.last_page].filter(Boolean).join('-') || null,
      doi, `https://doi.org/${doi}`, citation, work.language || 'en',
      (work.cited_by_count || 0) >= 20,
    ]);
    const { document_id: documentId, document_code: documentCode } = inserted.rows[0];

    await client.query(`
      INSERT INTO literature.attachments
        (document_id, file_name, storage_uri, mime_type, access_level, can_download)
      VALUES ($1,$2,$3,'application/pdf','public',true)
    `, [documentId, `${documentCode}.pdf`, pdfUrl]);

    await client.query(`
      INSERT INTO literature.document_domains (document_id, domain_code, is_primary, sort_order)
      VALUES ($1,$2,true,0)
    `, [documentId, domainCode]);

    for (let index = 0; index < (work.authorships || []).length; index += 1) {
      const authorship = work.authorships[index];
      const name = authorship.author?.display_name?.trim().slice(0, 255);
      if (!name) continue;
      const institution = authorship.institutions?.[0]?.display_name?.slice(0, 1000) || null;
      const existingAuthor = await client.query(
        'SELECT author_id FROM literature.authors WHERE author_name = $1 LIMIT 1',
        [name],
      );
      let authorId = existingAuthor.rows[0]?.author_id;
      if (!authorId) {
        const author = await client.query(`
          INSERT INTO literature.authors (author_name, institution)
          VALUES ($1,$2) RETURNING author_id
        `, [name, institution]);
        authorId = author.rows[0].author_id;
      }
      if (authorId) {
        await client.query(`
          INSERT INTO literature.document_authors
            (document_id, author_id, author_order, is_corresponding)
          VALUES ($1,$2,$3,$4) ON CONFLICT DO NOTHING
        `, [documentId, authorId, index + 1, Boolean(authorship.is_corresponding)]);
      }
    }

    const keywords = (work.keywords || [])
      .map((item) => item.display_name || item.keyword)
      .filter(Boolean)
      .slice(0, 10);
    for (const value of keywords) {
      const keyword = value.slice(0, 128);
      const keywordResult = await client.query(`
        INSERT INTO literature.keywords (keyword_name) VALUES ($1)
        ON CONFLICT (keyword_name) DO UPDATE SET keyword_name = EXCLUDED.keyword_name
        RETURNING keyword_id
      `, [keyword]);
      await client.query(`
        INSERT INTO literature.document_keywords (document_id, keyword_id)
        VALUES ($1,$2) ON CONFLICT DO NOTHING
      `, [documentId, keywordResult.rows[0].keyword_id]);
    }

    await client.query('COMMIT');
    return 'inserted';
  } catch (error) {
    await client.query('ROLLBACK');
    throw error;
  }
}

async function main() {
  const domains = DOMAIN_FILTER ? DOMAIN_FILTER.split(',') : Object.keys(DOMAIN_CONFIG);
  const client = await pool.connect();
  try {
    const sourceId = APPLY ? await ensureSource(client) : null;
    const globalSeen = new Set();
    const summary = {};

    for (const domainCode of domains) {
      const config = DOMAIN_CONFIG[domainCode];
      if (!config) continue;
      const candidates = [];
      for (const search of config.searches) {
        const works = await searchOpenAlex(search);
        for (const work of works) {
          const doi = normalizeDoi(work.doi);
          const pdfUrl = findPdf(work);
          if (!doi || !pdfUrl || globalSeen.has(doi) || !isRelevant(domainCode, work)) continue;
          globalSeen.add(doi);
          candidates.push({ work, pdfUrl });
          if (candidates.length >= ROWS_PER_DOMAIN) break;
        }
        if (candidates.length >= ROWS_PER_DOMAIN) break;
      }

      const stats = { candidates: candidates.length, inserted: 0, duplicate: 0, skipped: 0 };
      for (const candidate of candidates) {
        if (!APPLY) continue;
        const result = await insertWork(client, sourceId, domainCode, candidate.work, candidate.pdfUrl);
        if (result === 'inserted') stats.inserted += 1;
        else if (result === 'duplicate') stats.duplicate += 1;
        else stats.skipped += 1;
      }
      summary[domainCode] = stats;
      console.log(domainCode, stats);
    }
    console.log(JSON.stringify({ mode: APPLY ? 'apply' : 'dry-run', summary }, null, 2));
  } finally {
    client.release();
  }
}

main()
  .catch((error) => {
    console.error('OpenAlex OA 导入失败:', error);
    process.exitCode = 1;
  })
  .finally(() => pool.end());
