/**
 * CrossRef 冶金文献批量导入脚本
 *
 * 使用 CrossRef REST API 搜索冶金领域论文，自动写入 metallurgy_literature 数据库。
 *
 * 用法: node import_crossref.js [--rows=50] [--domains=steel_metallurgy,energy_restructuring]
 *
 * 默认每领域拉取 50 篇，全部以 published 状态插入。
 */

const { Pool } = require('pg');
const https = require('https');
const http = require('http');
const url = require('url');

// ========== 配置 ==========
const ROWS_PER_DOMAIN = parseInt(process.argv.find(a => a.startsWith('--rows='))?.split('=')[1] || '50');
const DOMAIN_FILTER = process.argv.find(a => a.startsWith('--domains='))?.split('=')[1] || null;

const MAILTO = 'xiangyu@metallurgy.edu.cn'; // CrossRef 要求提供邮箱用于限流

// 5 个研究领域对应的搜索关键词
const DOMAIN_QUERIES = {
  basic_principles: [
    'metallurgy thermodynamics phase transformation kinetics',
    'metallurgical thermodynamics slag metal reaction',
    'phase diagram calculation CALPHAD steel',
    'diffusion transformation metallurgy solidification',
    'thermodynamic modeling metallurgical process',
  ],
  steel_metallurgy: [
    'steelmaking converter BOF EAF refining',
    'continuous casting steel slab quality segregation',
    'hydrogen direct reduction iron DRI HBI',
    'blast furnace ironmaking coke rate carbon emission',
    'steel metallurgy secondary refining ladle',
    'electric arc furnace steel scrap recycling',
    'tundish metallurgy inclusion control clean steel',
  ],
  non_ferrous: [
    'non-ferrous metallurgy aluminum copper nickel',
    'aluminum electrolysis Hall-Heroult smelting',
    'copper smelting flash furnace pyrometallurgy',
    'hydrometallurgy leaching solvent extraction electrowinning',
    'rare earth metallurgy extraction separation',
    'titanium magnesium zinc lead smelting',
    'battery materials lithium nickel cobalt recycling',
  ],
  energy_restructuring: [
    'hydrogen metallurgy low carbon steelmaking',
    'carbon capture steel industry CCUS metallurgy',
    'renewable energy green hydrogen iron',
    'energy efficiency metallurgical furnace waste heat',
    'biomass carbon metallurgy alternative fuel',
    'electrification steel decarbonization sustainable',
    'hydrogen plasma smelting reduction ironmaking',
  ],
  resource_utilization: [
    'metallurgical slag recycling resource utilization',
    'steel slag utilization cement construction material',
    'recycling metallurgical dust sludge zinc recovery',
    'secondary resource metallurgy urban mining',
    'metallurgical waste treatment circular economy',
    'rare earth recycling magnets electronic waste',
    'iron steel scrap recycling optimization',
  ],
};

// CrossRef 类型 → 我们的 document_type
const TYPE_MAP = {
  'journal-article': 'paper',
  'proceedings-article': 'paper',
  'book-chapter': 'book',
  'book': 'book',
  'monograph': 'book',
  'reference-book': 'book',
  'report': 'report',
  'standard': 'standard',
  'dissertation': 'report',
  'peer-review': 'paper',
  'other': 'paper',
};

// ========== 数据库连接 ==========
const pool = new Pool({
  host: '127.0.0.1',
  port: 5432,
  database: 'metallurgy_literature',
  user: 'postgres',
  password: '',
  max: 5,
});

// ========== CrossRef API 调用 ==========
function crossrefSearch(query, rows = 20, offset = 0) {
  return new Promise((resolve, reject) => {
    const params = new url.URLSearchParams({
      query,
      rows: Math.min(rows, 100),
      offset,
      select: 'DOI,title,author,abstract,container-title,published-print,published-online,issued,type,URL,subject,ISSN,page,volume,issue,license,link',
      sort: 'relevance',
      mailto: MAILTO,
    });

    const apiUrl = `https://api.crossref.org/works?${params.toString()}`;

    https.get(apiUrl, { timeout: 15000 }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const parsed = JSON.parse(data);
          if (parsed.status !== 'ok') {
            reject(new Error(`CrossRef API error: ${parsed.message?.join(',') || 'unknown'}`));
          } else {
            resolve(parsed.message);
          }
        } catch (e) {
          reject(new Error(`Parse error: ${e.message}, raw: ${data.slice(0, 200)}`));
        }
      });
    }).on('error', reject).on('timeout', function() { this.destroy(); reject(new Error('Timeout')); });
  });
}

// ========== 提取年份 ==========
function extractYear(item) {
  const src = item['published-print'] || item['published-online'] || item['issued'] || {};
  const parts = src['date-parts'];
  if (parts && parts[0] && parts[0][0]) return parts[0][0];
  // Try from ISBN or other metadata
  return null;
}

// ========== 格式化引用 ==========
function buildCitation(item) {
  const authors = (item.author || []).map(a => `${a.family || ''} ${a.given || ''}`.trim()).filter(Boolean);
  const year = extractYear(item);
  const title = item.title?.[0] || '';
  const journal = item['container-title']?.[0] || '';
  const vol = item.volume || '';
  const iss = item.issue || '';
  const pages = item.page || '';
  const doi = item.DOI || '';
  const parts = [];
  if (authors.length) parts.push(authors.join(', '));
  if (year) parts.push(`(${year})`);
  if (title) parts.push(title);
  if (journal) parts.push(journal);
  const volIss = [vol, iss].filter(Boolean).join('(') + (iss ? ')' : '');
  if (volIss) parts.push(volIss);
  if (pages) parts.push(pages);
  if (doi) parts.push(`https://doi.org/${doi}`);
  return parts.join('. ') + '.';
}

// ========== 入库逻辑 ==========
async function importPapers(domainCode, papers) {
  const client = await pool.connect();
  let imported = 0;
  let skipped = 0;

  try {
    // 确保来源存在
    let sourceId;
    const srcRes = await client.query(
      `SELECT source_id FROM literature.sources WHERE source_name = 'CrossRef'`
    );
    if (srcRes.rows.length === 0) {
      const ins = await client.query(
        `INSERT INTO literature.sources (source_name, source_type, provider, access_url)
         VALUES ('CrossRef', 'journal', 'CrossRef', 'https://www.crossref.org')
         RETURNING source_id`
      );
      sourceId = ins.rows[0].source_id;
      console.log('  📦 创建来源: CrossRef');
    } else {
      sourceId = srcRes.rows[0].source_id;
    }

    for (const paper of papers) {
      const doi = paper.DOI;
      if (!doi) { skipped++; continue; }

      // 检查 DOI 是否已存在
      const existRes = await client.query(
        `SELECT document_id FROM literature.documents WHERE doi = $1 AND doi IS NOT NULL`,
        [doi]
      );
      if (existRes.rows.length > 0) { skipped++; continue; }

      const title = (paper.title?.[0] || '').slice(0, 2000);
      if (!title) { skipped++; continue; }

      const year = extractYear(paper);
      const journal = (paper['container-title']?.[0] || '').slice(0, 1000);
      const abstract = (paper.abstract || '').replace(/<[^>]*>/g, '').slice(0, 10000) || null;
      const docType = TYPE_MAP[paper.type] || 'paper';
      const citation = buildCitation(paper);
      const sourceUrl = paper.URL || `https://doi.org/${doi}`;

      await client.query('BEGIN');

      // 插入文献
      const docRes = await client.query(`
        INSERT INTO literature.documents
          (source_id, title, document_type, abstract, journal_name,
           publication_year, volume, issue, pages, doi, source_url,
           citation_text, language, status, security_level, is_featured,
           published_at, created_by)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,NOW(),'crossref_import')
        RETURNING document_id, document_code
      `, [
        sourceId, title, docType, abstract, journal,
        year, paper.volume || null, paper.issue || null, paper.page || null,
        doi, sourceUrl, citation, 'en',
        'published', 'public', Math.random() < 0.1, // 10% 标记为推荐
      ]);

      const { document_id, document_code } = docRes.rows[0];

      // 插入作者
      const authors = paper.author || [];
      for (let i = 0; i < authors.length; i++) {
        const a = authors[i];
        const authorName = [a.given, a.family].filter(Boolean).join(' ').trim().slice(0, 255);
        if (!authorName) continue;

        let authorId;
        const existing = await client.query(
          'SELECT author_id FROM literature.authors WHERE author_name = $1',
          [authorName]
        );
        if (existing.rows.length > 0) {
          authorId = existing.rows[0].author_id;
        } else {
          const ins = await client.query(
            'INSERT INTO literature.authors (author_name) VALUES ($1) RETURNING author_id',
            [authorName]
          );
          authorId = ins.rows[0].author_id;
        }

        await client.query(
          `INSERT INTO literature.document_authors (document_id, author_id, author_order)
           VALUES ($1,$2,$3) ON CONFLICT DO NOTHING`,
          [document_id, authorId, i + 1]
        );
      }

      // 关联领域
      await client.query(
        `INSERT INTO literature.document_domains (document_id, domain_code, is_primary, sort_order)
         VALUES ($1,$2,true,0) ON CONFLICT DO NOTHING`,
        [document_id, domainCode]
      );

      // 从 subjects 和 title 提取关键词
      const subjects = paper.subject || [];
      const titleWords = title.split(/[\s,;:()]+/).filter(w => w.length > 3 && /^[a-zA-Z]/.test(w)).slice(0, 8);
      const keywords = [...new Set([...subjects, ...titleWords])].slice(0, 10);

      for (const kw of keywords) {
        if (!kw || kw.length > 128) continue;
        const kwRes = await client.query(
          `INSERT INTO literature.keywords (keyword_name) VALUES ($1)
           ON CONFLICT (keyword_name) DO UPDATE SET keyword_name = EXCLUDED.keyword_name
           RETURNING keyword_id`,
          [kw.slice(0, 128)]
        );
        await client.query(
          `INSERT INTO literature.document_keywords (document_id, keyword_id)
           VALUES ($1,$2) ON CONFLICT DO NOTHING`,
          [document_id, kwRes.rows[0].keyword_id]
        );
      }

      await client.query('COMMIT');
      imported++;
      process.stdout.write(`  ✅ ${document_code} ${title.slice(0, 60)}...\n`);
    }
  } catch (e) {
    await client.query('ROLLBACK');
    throw e;
  } finally {
    client.release();
  }

  return { imported, skipped };
}

// ========== 主流程 ==========
async function main() {
  console.log('========================================');
  console.log('  CrossRef 冶金文献批量导入');
  console.log(`  Rows per domain: ${ROWS_PER_DOMAIN}`);
  console.log('========================================\n');

  const domainCodes = DOMAIN_FILTER
    ? DOMAIN_FILTER.split(',')
    : Object.keys(DOMAIN_QUERIES);

  let totalImported = 0;
  let totalSkipped = 0;
  let totalQueried = 0;

  for (const domainCode of domainCodes) {
    const queries = DOMAIN_QUERIES[domainCode];
    if (!queries) {
      console.warn(`⚠️  Unknown domain: ${domainCode}, skipping`);
      continue;
    }

    console.log(`\n📂 领域: ${domainCode}`);
    const allPapers = [];
    const seenDOIs = new Set();

    // 按关键词逐批查询，每次 30 篇
    for (const q of queries) {
      if (allPapers.length >= ROWS_PER_DOMAIN) break;
      try {
        const batchSize = Math.min(30, ROWS_PER_DOMAIN - allPapers.length);
        console.log(`  🔍 搜索: "${q.slice(0, 60)}" (${batchSize}篇)`);
        const result = await crossrefSearch(q, batchSize);
        const items = result.items || [];

        for (const item of items) {
          if (item.DOI && !seenDOIs.has(item.DOI) && (item.title?.[0])) {
            seenDOIs.add(item.DOI);
            allPapers.push(item);
          }
        }
        console.log(`     → 获取 ${items.length} 条，去重后共 ${allPapers.length} 篇`);
        totalQueried += items.length;

        // CrossRef 限流：约 50 req/s，加个小间隔
        await new Promise(r => setTimeout(r, 300));
      } catch (e) {
        console.error(`     ⚠️  查询失败: ${e.message}`);
        await new Promise(r => setTimeout(r, 1000));
      }
    }

    console.log(`  📥 入库 ${allPapers.length} 篇文献...`);
    if (allPapers.length === 0) continue;

    try {
      const result = await importPapers(domainCode, allPapers.slice(0, ROWS_PER_DOMAIN));
      totalImported += result.imported;
      totalSkipped += result.skipped;
      console.log(`  📊 结果: ${result.imported} 篇入库, ${result.skipped} 篇跳过（重复）`);
    } catch (e) {
      console.error(`  ❌ 入库失败: ${e.message}`);
    }
  }

  console.log('\n========================================');
  console.log('  导入完成');
  console.log(`  查询总数: ${totalQueried}`);
  console.log(`  入库总数: ${totalImported}`);
  console.log(`  跳过总数: ${totalSkipped}`);
  console.log('========================================');

  await pool.end();
}

main().catch(e => {
  console.error('❌ 严重错误:', e.message);
  pool.end();
  process.exit(1);
});
