/**
 * arXiv 冶金相关论文批量导入脚本
 *
 * 使用 arXiv API 搜索冶金/材料领域论文，自动写入 metallurgy_literature 数据库。
 *
 * 用法: node import_arxiv.js [--rows=30] [--domains=basic_principles,steel_metallurgy]
 */

const { Pool } = require('pg');
const https = require('https'); // arXiv API → HTTPS

const ROWS_PER_DOMAIN = parseInt(process.argv.find(a => a.startsWith('--rows='))?.split('=')[1] || '30');
const DOMAIN_FILTER = process.argv.find(a => a.startsWith('--domains='))?.split('=')[1] || null;

// arXiv 冶金相关搜索关键词（带分类过滤）
const DOMAIN_QUERIES = {
  basic_principles: [
    '(all:metallurgy+AND+all:thermodynamics+AND+all:phase+AND+all:diagram)+AND+cat:cond-mat.mtrl-sci',
    '(all:phase+AND+all:transformation+AND+all:steel+AND+all:alloy)+AND+cat:cond-mat.mtrl-sci',
    '(all:CALPHAD+OR+all:phase+field+OR+all:thermodynamic+modeling)+AND+cat:cond-mat.mtrl-sci',
    '(all:diffusion+AND+all:kinetics+AND+all:metallurgy)+AND+cat:cond-mat.mtrl-sci',
    '(all:first+AND+all:principles+AND+all:alloy+AND+all:phase)+AND+cat:cond-mat.mtrl-sci',
  ],
  steel_metallurgy: [
    '(all:steelmaking+OR+all:converter+OR+all:BOF+OR+all:EAF)+AND+cat:cond-mat.mtrl-sci',
    '(all:continuous+AND+all:casting+AND+all:steel+AND+all:solidification)+AND+cat:cond-mat.mtrl-sci',
    '(all:hydrogen+AND+all:direct+AND+all:reduction+AND+all:iron)+AND+cat:cond-mat.mtrl-sci',
    '(all:blast+furnace+OR+all:ironmaking+OR+all:coke+rate)+AND+cat:cond-mat.mtrl-sci',
    '(all:steel+AND+all:inclusion+OR+all:clean+steel)+AND+cat:cond-mat.mtrl-sci',
    '(all:electric+AND+all:arc+furnace+AND+all:scrap)+AND+cat:cond-mat.mtrl-sci',
  ],
  non_ferrous: [
    '(all:aluminum+AND+all:electrolysis+OR+all:smelting)+AND+cat:cond-mat.mtrl-sci',
    '(all:copper+AND+all:smelting+OR+all:pyrometallurgy)+AND+cat:cond-mat.mtrl-sci',
    '(all:hydrometallurgy+OR+all:leaching+OR+all:solvent+extraction)+AND+cat:cond-mat.mtrl-sci',
    '(all:rare+AND+all:earth+AND+all:metallurgy+OR+all:separation)+AND+cat:cond-mat.mtrl-sci',
    '(all:titanium+OR+all:magnesium+OR+all:zinc+OR+all:lead+smelting)+AND+cat:cond-mat.mtrl-sci',
    '(all:lithium+OR+all:battery+AND+all:recycling+AND+all:metallurgy)+AND+cat:cond-mat.mtrl-sci',
  ],
  energy_restructuring: [
    '(all:hydrogen+AND+all:metallurgy+OR+all:low+carbon+steel)+AND+cat:cond-mat.mtrl-sci',
    '(all:carbon+capture+AND+all:steel+OR+all:CCUS)+AND+cat:cond-mat.mtrl-sci',
    '(all:green+hydrogen+AND+all:iron+AND+all:reduction)+AND+cat:cond-mat.mtrl-sci',
    '(all:energy+efficiency+AND+all:metallurgical+furnace)+AND+cat:cond-mat.mtrl-sci',
    '(all:steel+AND+all:decarbonization+OR+all:sustainable)+AND+cat:cond-mat.mtrl-sci',
    '(all:biomass+AND+all:metallurgy+OR+all:alternative+fuel)+AND+cat:cond-mat.mtrl-sci',
  ],
  resource_utilization: [
    '(all:metallurgical+AND+all:slag+OR+all:recycling)+AND+cat:cond-mat.mtrl-sci',
    '(all:steel+AND+all:slag+AND+all:utilization+OR+all:cement)+AND+cat:cond-mat.mtrl-sci',
    '(all:recycling+AND+all:metallurgical+AND+all:dust+OR+all:zinc)+AND+cat:cond-mat.mtrl-sci',
    '(all:secondary+AND+all:resource+AND+all:metallurgy)+AND+cat:cond-mat.mtrl-sci',
    '(all:metallurgical+AND+all:waste+OR+all:circular+economy)+AND+cat:cond-mat.mtrl-sci',
    '(all:rare+AND+all:earth+AND+all:recycling+AND+all:magnets)+AND+cat:cond-mat.mtrl-sci',
  ],
};

// arXiv 分类 → 我们的 document_type
const TYPE_MAP = { 'paper': 'paper' }; // arXiv 全是预印本论文

const MAILTO = 'xiangyu@metallurgy.edu.cn';

// ========== 数据库连接 ==========
const pool = new Pool({
  host: '127.0.0.1', port: 5432,
  database: 'metallurgy_literature',
  user: 'postgres', password: '',
  max: 5,
});

// ========== arXiv XML 解析 ==========
function parseArxivXML(xml) {
  const entries = [];
  // 拆分每个 <entry>
  const entryRegex = /<entry>([\s\S]*?)<\/entry>/g;
  let match;
  while ((match = entryRegex.exec(xml)) !== null) {
    const entryXml = match[1];
    entries.push({
      id: extractTag(entryXml, 'id'),
      title: extractTag(entryXml, 'title')?.replace(/\s+/g, ' ').trim(),
      summary: extractTag(entryXml, 'summary')?.replace(/\s+/g, ' ').trim(),
      published: extractTag(entryXml, 'published')?.slice(0, 4), // 只取年份
      doi: extractArxivDOI(entryXml),
      authors: extractAuthors(entryXml),
      link: extractTag(entryXml, 'link'),
      categories: extractCategories(entryXml),
    });
  }
  return entries;
}

function extractTag(xml, tag) {
  const m = new RegExp(`<${tag}[^>]*>([\\s\\S]*?)<\\/${tag}>`).exec(xml);
  return m ? m[1].trim() : '';
}

function extractArxivDOI(xml) {
  // arXiv 有时在 <arxiv:doi> 里
  const m = /<arxiv:doi[^>]*>([^<]*)<\/arxiv:doi>/.exec(xml);
  if (m && m[1].trim()) return m[1].trim();
  // 或者用 arxiv ID 构建虚拟 DOI
  const idMatch = /<id>[^<]*\/abs\/([^<]+)<\/id>/.exec(xml);
  if (idMatch) return `arxiv.${idMatch[1].replace(/v\d+$/, '')}`;
  return null;
}

function extractAuthors(xml) {
  const authors = [];
  const regex = /<author>[\s\S]*?<name>([^<]*)<\/name>[\s\S]*?<\/author>/g;
  let m;
  while ((m = regex.exec(xml)) !== null) {
    authors.push(m[1].trim());
  }
  return authors;
}

function extractCategories(xml) {
  const cats = [];
  const regex = /<category[^>]*term="([^"]+)"/g;
  let m;
  while ((m = regex.exec(xml)) !== null) cats.push(m[1]);
  return cats;
}

function extractLink(xml) {
  const m = /<link[^>]*href="([^"]*)"[^>]*title="doi"[^>]*\/>/.exec(xml);
  return m ? m[1] : null;
}

// ========== arXiv API 调用 ==========
function searchArxiv(query, maxResults = 25, start = 0) {
  return new Promise((resolve, reject) => {
    // arXiv API 的 + 是搜索语法的一部分（AND/OR），不能 URL 编码
    // 手动拼 URL，只编码特殊字符
    const encoded = encodeURIComponent(query).replace(/%2B/g, '+').replace(/%28/g, '(').replace(/%29/g, ')').replace(/%3A/g, ':');
    const apiUrl = `https://export.arxiv.org/api/query?search_query=${encoded}&start=${start}&max_results=${Math.min(maxResults, 100)}&sortBy=relevance&sortOrder=descending`;

    https.get(apiUrl, { timeout: 20000 }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        if (res.statusCode !== 200) {
          return reject(new Error(`HTTP ${res.statusCode}`));
        }
        try {
          const entries = parseArxivXML(data);
          // 获取总结果数
          const totalMatch = /<opensearch:totalResults[^>]*>(\d+)<\/opensearch:totalResults>/.exec(data);
          const total = totalMatch ? parseInt(totalMatch[1]) : entries.length;
          resolve({ entries, total });
        } catch (e) {
          reject(new Error(`Parse error: ${e.message}`));
        }
      });
    }).on('error', reject).on('timeout', function () { this.destroy(); reject(new Error('Timeout')); });
  });
}

// ========== 格式化引用 ==========
function buildCitation(title, authors, year, doi, arxivId) {
  const parts = [];
  if (authors.length) parts.push(authors.join(', '));
  if (year) parts.push(`(${year})`);
  if (title) parts.push(title);
  parts.push('arXiv preprint');
  if (arxivId) parts.push(arxivId);
  if (doi && !doi.startsWith('arxiv.')) parts.push(`https://doi.org/${doi}`);
  return parts.join('. ') + '.';
}

// ========== 入库逻辑 ==========
async function importPapers(domainCode, papers) {
  const client = await pool.connect();
  let imported = 0, skipped = 0;

  try {
    let sourceId;
    const srcRes = await client.query(
      `SELECT source_id FROM literature.sources WHERE source_name = 'arXiv'`
    );
    if (srcRes.rows.length === 0) {
      const ins = await client.query(
        `INSERT INTO literature.sources (source_name, source_type, provider, access_url)
         VALUES ('arXiv', 'journal', 'arXiv', 'https://arxiv.org')
         RETURNING source_id`
      );
      sourceId = ins.rows[0].source_id;
      console.log('  📦 创建来源: arXiv');
    } else {
      sourceId = srcRes.rows[0].source_id;
    }

    for (const paper of papers) {
      const title = (paper.title || '').slice(0, 2000);
      if (!title) { skipped++; continue; }

      const doi = paper.doi;
      const arxivId = paper.id ? paper.id.replace(/.*\/abs\//, '') : null;

      // DOI 查重（arxiv 的虚拟 DOI 也可能重复）
      if (doi) {
        const existRes = await client.query(
          `SELECT document_id FROM literature.documents WHERE doi = $1 AND doi IS NOT NULL`,
          [doi]
        );
        if (existRes.rows.length > 0) { skipped++; continue; }
      }

      const year = paper.published ? parseInt(paper.published) : null;
      const abstract = (paper.summary || '').slice(0, 10000);
      const citation = buildCitation(title, paper.authors, year, doi, arxivId);
      const sourceUrl = paper.id || (arxivId ? `https://arxiv.org/abs/${arxivId}` : null);
      const journal = `arXiv ${paper.categories.slice(0, 3).join(', ')}`;

      // arXiv 论文默认语言是 en
      await client.query('BEGIN');

      const docRes = await client.query(`
        INSERT INTO literature.documents
          (source_id, title, document_type, abstract, journal_name,
           publication_year, doi, source_url,
           citation_text, language, status, security_level, is_featured,
           published_at, created_by)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,NOW(),'arxiv_import')
        RETURNING document_id, document_code
      `, [
        sourceId, title, 'paper', abstract, journal,
        year, doi, sourceUrl, citation, 'en',
        'published', 'public', Math.random() < 0.1,
      ]);

      const { document_id, document_code } = docRes.rows[0];

      // arXiv 为每篇预印本提供公开 PDF；同步写入附件表，避免产生无 PDF 文献。
      if (arxivId) {
        await client.query(`
          INSERT INTO literature.attachments
            (document_id, file_name, storage_uri, mime_type, access_level, can_download)
          VALUES ($1, $2, $3, 'application/pdf', 'public', true)
        `, [document_id, `${document_code}.pdf`, `https://arxiv.org/pdf/${arxivId.replace(/v\d+$/, '')}.pdf`]);
      }

      // 插入作者
      for (let i = 0; i < paper.authors.length; i++) {
        const authorName = paper.authors[i].slice(0, 255);
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

      // arXiv 分类作为关键词
      const keywords = [...new Set(paper.categories)].slice(0, 10);
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
      process.stdout.write(`  ✅ ${document_code} ${(title || '').slice(0, 60)}...\n`);
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
  console.log('  arXiv 冶金论文批量导入');
  console.log(`  Rows per domain: ${ROWS_PER_DOMAIN}`);
  console.log('========================================\n');

  const domainCodes = DOMAIN_FILTER
    ? DOMAIN_FILTER.split(',')
    : Object.keys(DOMAIN_QUERIES);

  let totalImported = 0, totalSkipped = 0, totalQueried = 0;

  for (const domainCode of domainCodes) {
    const queries = DOMAIN_QUERIES[domainCode];
    if (!queries) { console.warn(`⚠️  Unknown domain: ${domainCode}`); continue; }

    console.log(`\n📂 领域: ${domainCode}`);
    const allPapers = [];
    const seenDOIs = new Set();

    for (const q of queries) {
      if (allPapers.length >= ROWS_PER_DOMAIN) break;

      try {
        const batchSize = Math.min(25, ROWS_PER_DOMAIN - allPapers.length);
        console.log(`  🔍 "${q.slice(0, 60)}" (${batchSize}篇)`);
        const result = await searchArxiv(q, batchSize);
        const items = result.entries || [];

        for (const item of items) {
          const doi = item.doi || `arxiv.${(item.id || '').replace(/.*\/abs\//, '').replace(/v\d+$/, '')}`;
          if (item.title && !seenDOIs.has(doi)) {
            seenDOIs.add(doi);
            allPapers.push(item);
          }
        }
        console.log(`     → 获取 ${items.length} 条，去重后共 ${allPapers.length} 篇`);
        totalQueried += items.length;

        // arXiv 限流：约 1 req/3s
        await new Promise(r => setTimeout(r, 4000));
      } catch (e) {
        console.error(`     ⚠️  查询失败: ${e.message}`);
        await new Promise(r => setTimeout(r, 5000));
      }
    }

    console.log(`  📥 入库 ${allPapers.length} 篇文献...`);
    if (allPapers.length === 0) continue;

    try {
      const result = await importPapers(domainCode, allPapers.slice(0, ROWS_PER_DOMAIN));
      totalImported += result.imported;
      totalSkipped += result.skipped;
      console.log(`  📊 结果: ${result.imported} 篇入库, ${result.skipped} 篇跳过`);
    } catch (e) {
      console.error(`  ❌ 入库失败: ${e.message}`);
    }

    await new Promise(r => setTimeout(r, 1000));
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
