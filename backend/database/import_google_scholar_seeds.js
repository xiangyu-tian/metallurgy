/**
 * 导入人工筛选的 Google Scholar 高引用种子论文。
 * Scholar 仅用于发现、领域判断和引用次数；DOI/元数据/PDF 由 OpenAlex 验证。
 * 默认 dry-run，传入 --apply 才写数据库。
 */

const { Pool } = require('pg');

const APPLY = process.argv.includes('--apply');

const SEEDS = [
  {
    domain: 'basic_principles', citations: 27,
    scholar_url: 'https://scholar.google.com/citations?user=XmPeaCkAAAAJ',
    title: 'On the elastocaloric effect in CuAlBe shape memory alloys: A quantitative phase-field modeling approach',
  },
  {
    domain: 'basic_principles', citations: 47,
    scholar_url: 'https://scholar.google.com/citations?user=XmPeaCkAAAAJ',
    title: 'An Asymmetric Elasto-Plastic Phase-Field Model for Shape Memory Effect, Pseudoelasticity and Thermomechanical Training in Polycrystalline Shape Memory Alloys',
  },
  {
    domain: 'basic_principles', citations: 38,
    scholar_url: 'https://scholar.google.com/citations?user=XmPeaCkAAAAJ',
    title: 'A Phase-Field Model for Non-Isothermal Phase Transformation and Plasticity in Polycrystalline Yttria-Stabilized Tetragonal Zirconia',
  },
  {
    domain: 'basic_principles', citations: 30,
    scholar_url: 'https://scholar.google.com/citations?user=XmPeaCkAAAAJ',
    title: 'Transformation-Induced Fracture Toughening in CuAlBe Shape Memory Alloys: A Phase-Field Study',
  },
  {
    domain: 'steel_metallurgy', citations: 85,
    scholar_url: 'https://scholar.google.com/citations?user=dfu-aB8AAAAJ',
    title: 'Hydrogen, as an alloying element, enables a greater strength-ductility balance in an Fe-Cr-Ni-based, stable austenitic stainless steel',
  },
  {
    domain: 'steel_metallurgy', citations: 84,
    scholar_url: 'https://scholar.google.com/citations?user=dfu-aB8AAAAJ',
    title: 'Comprehensive understanding of ductility loss mechanisms in various steels with external and internal hydrogen',
  },
  {
    domain: 'steel_metallurgy', citations: 78,
    scholar_url: 'https://scholar.google.com/citations?user=dfu-aB8AAAAJ',
    title: 'Hydrogen trapping and fatigue crack growth property of low-carbon steel in hydrogen-gas environment',
  },
  {
    domain: 'steel_metallurgy', citations: 184,
    scholar_url: 'https://scholar.google.com/citations?user=dfu-aB8AAAAJ',
    title: 'Slow strain rate tensile and fatigue properties of Cr-Mo and carbon steels in a 115 MPa hydrogen gas atmosphere',
  },
  {
    domain: 'steel_metallurgy', citations: 74,
    scholar_url: 'https://scholar.google.com/citations?user=dfu-aB8AAAAJ',
    title: 'Unified evaluation of hydrogen-induced crack growth in fatigue tests and fracture toughness tests of a carbon steel',
  },
  {
    domain: 'non_ferrous', citations: 148,
    scholar_url: 'https://scholar.google.com/citations?user=4bLI4tsAAAAJ',
    title: 'Solvent extraction fractionation of Li-ion battery leachate containing Li, Ni, and Co',
  },
  {
    domain: 'non_ferrous', citations: 125,
    scholar_url: 'https://scholar.google.com/citations?user=4bLI4tsAAAAJ',
    title: 'Removal of iron, aluminium, manganese and copper from leach solutions of lithium-ion battery waste using ion exchange',
  },
  {
    domain: 'non_ferrous', citations: 56,
    scholar_url: 'https://scholar.google.com/citations?user=4bLI4tsAAAAJ',
    title: 'Removal of calcium and magnesium from lithium brine concentrate via continuous counter-current solvent extraction',
  },
  {
    domain: 'non_ferrous', citations: 64,
    scholar_url: 'https://scholar.google.com/citations?user=4bLI4tsAAAAJ',
    title: 'Ion exchange recovery of silver from concentrated base metal-chloride solutions',
  },
  {
    domain: 'resource_utilization', citations: 71,
    scholar_url: 'https://scholar.google.com/citations?user=4bLI4tsAAAAJ',
    title: 'Recovering rare earth elements from phosphogypsum using a resin-in-leach process: Selection of resin, leaching agent, and eluent',
  },
  {
    domain: 'resource_utilization', citations: 60,
    scholar_url: 'https://scholar.google.com/citations?user=_2En5PkAAAAJ',
    title: 'RSM-CCD optimization approach for the adsorptive removal of Eriochrome Black T from aqueous system using steel slag-based adsorbent: Characterization, Isotherm, Kinetic and Thermodynamic studies',
  },
];

const pool = new Pool({
  host: process.env.LITERATURE_DB_HOST || '127.0.0.1',
  port: parseInt(process.env.LITERATURE_DB_PORT || '5432', 10),
  database: process.env.LITERATURE_DB_NAME || 'metallurgy_literature',
  user: process.env.LITERATURE_DB_USER || 'postgres',
  password: process.env.LITERATURE_DB_PASSWORD || '',
});

function normalizedTokens(value) {
  return new Set(String(value || '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, ' ')
    .trim()
    .split(/\s+/)
    .filter((token) => token.length > 1));
}

function titleSimilarity(left, right) {
  const a = normalizedTokens(left);
  const b = normalizedTokens(right);
  if (!a.size || !b.size) return 0;
  const intersection = [...a].filter((token) => b.has(token)).length;
  return (2 * intersection) / (a.size + b.size);
}

function normalizeDoi(value) {
  return value ? value.replace(/^https?:\/\/(?:dx\.)?doi\.org\//i, '').toLowerCase() : null;
}

function invertAbstract(index) {
  if (!index) return null;
  const words = [];
  for (const [word, positions] of Object.entries(index)) {
    for (const position of positions) words[position] = word;
  }
  return words.filter(Boolean).join(' ').slice(0, 10000) || null;
}

function pdfUrl(work) {
  if (work.best_oa_location?.is_oa && work.best_oa_location?.pdf_url) {
    return work.best_oa_location.pdf_url;
  }
  return work.locations?.find((location) => location?.is_oa && location?.pdf_url)?.pdf_url || null;
}

async function resolveSeed(seed) {
  const params = new URLSearchParams({
    search: seed.title,
    filter: 'has_pdf_url:true,is_oa:true',
    'per-page': '10',
    mailto: 'xiangyu@metallurgy.edu.cn',
  });
  const response = await fetch(`https://api.openalex.org/works?${params}`, {
    headers: { 'User-Agent': 'metallurgy-literature/1.0 (mailto:xiangyu@metallurgy.edu.cn)' },
    signal: AbortSignal.timeout(30000),
  });
  if (!response.ok) throw new Error(`OpenAlex HTTP ${response.status}`);
  const works = (await response.json()).results || [];
  const ranked = works
    .map((work) => ({ work, score: titleSimilarity(seed.title, work.title) }))
    .sort((a, b) => b.score - a.score);
  const match = ranked[0];
  if (!match || match.score < 0.72) return { seed, status: 'title_not_matched' };
  const doi = normalizeDoi(match.work.doi);
  const pdf = pdfUrl(match.work);
  if (!doi || !pdf) return { seed, status: 'no_open_pdf' };
  return { seed, work: match.work, doi, pdf, score: match.score, status: 'resolved' };
}

async function ensureSource(client) {
  const result = await client.query(
    "SELECT source_id FROM literature.sources WHERE source_name = 'Google Scholar Discovery' LIMIT 1",
  );
  if (result.rows.length) return result.rows[0].source_id;
  const inserted = await client.query(`
    INSERT INTO literature.sources
      (source_name, source_type, provider, access_url, license_note)
    VALUES ('Google Scholar Discovery', 'journal', 'Google Scholar',
            'https://scholar.google.com',
            'Scholar 用于人工发现与引用排序；元数据和开放 PDF 由 OpenAlex 验证')
    RETURNING source_id
  `);
  return inserted.rows[0].source_id;
}

async function addAuthorsAndKeywords(client, documentId, work) {
  for (let index = 0; index < (work.authorships || []).length; index += 1) {
    const authorship = work.authorships[index];
    const name = authorship.author?.display_name?.trim().slice(0, 255);
    if (!name) continue;
    const existing = await client.query(
      'SELECT author_id FROM literature.authors WHERE author_name = $1 LIMIT 1',
      [name],
    );
    let authorId = existing.rows[0]?.author_id;
    if (!authorId) {
      const inserted = await client.query(
        'INSERT INTO literature.authors (author_name, institution) VALUES ($1,$2) RETURNING author_id',
        [name, authorship.institutions?.[0]?.display_name?.slice(0, 1000) || null],
      );
      authorId = inserted.rows[0].author_id;
    }
    await client.query(`
      INSERT INTO literature.document_authors
        (document_id, author_id, author_order, is_corresponding)
      VALUES ($1,$2,$3,$4) ON CONFLICT DO NOTHING
    `, [documentId, authorId, index + 1, Boolean(authorship.is_corresponding)]);
  }

  for (const item of (work.keywords || []).slice(0, 10)) {
    const value = (item.display_name || item.keyword || '').slice(0, 128);
    if (!value) continue;
    const keyword = await client.query(`
      INSERT INTO literature.keywords (keyword_name) VALUES ($1)
      ON CONFLICT (keyword_name) DO UPDATE SET keyword_name = EXCLUDED.keyword_name
      RETURNING keyword_id
    `, [value]);
    await client.query(`
      INSERT INTO literature.document_keywords (document_id, keyword_id)
      VALUES ($1,$2) ON CONFLICT DO NOTHING
    `, [documentId, keyword.rows[0].keyword_id]);
  }
}

async function persist(client, sourceId, resolved) {
  const { seed, work, doi, pdf } = resolved;
  const existing = await client.query(
    'SELECT document_id, document_code FROM literature.documents WHERE LOWER(doi) = $1 LIMIT 1',
    [doi],
  );

  await client.query('BEGIN');
  try {
    let documentId;
    let outcome;
    if (existing.rows.length) {
      documentId = existing.rows[0].document_id;
      await client.query(`
        UPDATE literature.documents
        SET discovery_source = 'google_scholar',
            scholar_citation_count = GREATEST(COALESCE(scholar_citation_count, 0), $1),
            scholar_url = $2,
            scholar_checked_at = NOW(),
            updated_at = NOW()
        WHERE document_id = $3
      `, [seed.citations, seed.scholar_url, documentId]);
      outcome = 'updated_existing';
    } else {
      const biblio = work.biblio || {};
      const inserted = await client.query(`
        INSERT INTO literature.documents
          (source_id, title, document_type, abstract, journal_name, publication_year,
           volume, issue, pages, doi, source_url, citation_text, language,
           discovery_source, scholar_citation_count, scholar_url, scholar_checked_at,
           status, security_level, is_featured, published_at, created_by)
        VALUES ($1,$2,'paper',$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,
                'google_scholar',$13,$14,NOW(),'published','public',true,NOW(),'google_scholar_seed')
        RETURNING document_id, document_code
      `, [
        sourceId, work.title, invertAbstract(work.abstract_inverted_index),
        work.primary_location?.source?.display_name || null, work.publication_year || null,
        biblio.volume || null, biblio.issue || null,
        [biblio.first_page, biblio.last_page].filter(Boolean).join('-') || null,
        doi, `https://doi.org/${doi}`,
        `${work.title}. https://doi.org/${doi}`, work.language || 'en',
        seed.citations, seed.scholar_url,
      ]);
      documentId = inserted.rows[0].document_id;
      await addAuthorsAndKeywords(client, documentId, work);
      outcome = 'inserted';
    }

    await client.query(`
      INSERT INTO literature.document_domains (document_id, domain_code, is_primary, sort_order)
      VALUES ($1,$2,true,0) ON CONFLICT DO NOTHING
    `, [documentId, seed.domain]);
    await client.query(`
      INSERT INTO literature.attachments
        (document_id, file_name, storage_uri, mime_type, access_level, can_download)
      SELECT $1, d.document_code || '.pdf', $2, 'application/pdf', 'public', true
      FROM literature.documents d
      WHERE d.document_id = $1
        AND NOT EXISTS (
          SELECT 1 FROM literature.attachments a
          WHERE a.document_id = $1 AND a.mime_type = 'application/pdf'
        )
    `, [documentId, pdf]);

    await client.query('COMMIT');
    return outcome;
  } catch (error) {
    await client.query('ROLLBACK');
    throw error;
  }
}

async function main() {
  const client = await pool.connect();
  try {
    const sourceId = APPLY ? await ensureSource(client) : null;
    const summary = { inserted: 0, updated_existing: 0, title_not_matched: 0, no_open_pdf: 0, errors: 0 };
    for (const seed of SEEDS) {
      try {
        const resolved = await resolveSeed(seed);
        if (resolved.status !== 'resolved') {
          summary[resolved.status] += 1;
          console.log(resolved.status, seed.title);
          continue;
        }
        if (!APPLY) {
          console.log('resolved', resolved.score.toFixed(2), seed.title, resolved.doi);
          continue;
        }
        const outcome = await persist(client, sourceId, resolved);
        summary[outcome] += 1;
        console.log(outcome, seed.title);
      } catch (error) {
        summary.errors += 1;
        console.error('error', seed.title, error.message);
      }
    }
    console.log(JSON.stringify({ mode: APPLY ? 'apply' : 'dry-run', summary }, null, 2));
  } finally {
    client.release();
  }
}

main()
  .catch((error) => {
    console.error('Google Scholar 种子导入失败:', error);
    process.exitCode = 1;
  })
  .finally(() => pool.end());
