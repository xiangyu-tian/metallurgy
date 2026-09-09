/**
 * OpenAlex 中文冶金文献批量导入脚本
 *
 * 使用 OpenAlex API 搜索中文冶金领域论文，自动写入 metallurgy_literature 数据库。
 *
 * 用法: node import_openalex_zh.js [--rows=30] [--domains=steel_metallurgy,energy_restructuring]
 */

const { Pool } = require('pg');
const https = require('https');

const ROWS_PER_DOMAIN = parseInt(process.argv.find(a => a.startsWith('--rows='))?.split('=')[1] || '30');
const DOMAIN_FILTER = process.argv.find(a => a.startsWith('--domains='))?.split('=')[1] || null;

const MAILTO = 'xiangyu@metallurgy.edu.cn';

// 5 个研究领域对应的中文搜索关键词
const DOMAIN_QUERIES = {
  basic_principles: [
    '冶金 热力学 相图 计算',
    '冶金 动力学 扩散 相变',
    '冶金 热力学 模型 预测',
    '相图 CALPHAD 钢铁 合金',
    '凝固 相变 冶金 热力学',
  ],
  steel_metallurgy: [
    '转炉 炼钢 冶金 工艺',
    '连铸 钢坯 质量 偏析',
    '电弧炉 炼钢 废钢 回收',
    '高炉 炼铁 焦比 碳排放',
    '氢冶金 直接还原 低碳 钢铁',
    '钢铁冶金 夹杂物 控制 洁净钢',
    '炼钢 炉外精炼 LF VD RH',
  ],
  non_ferrous: [
    '有色冶金 铝 电解 铜 冶炼',
    '铜 闪速熔炼 火法冶金',
    '湿法冶金 浸出 萃取 电积',
    '稀土 冶金 萃取 分离',
    '钛 镁 锌 铅 冶炼 工艺',
    '锂 镍 钴 电池 材料 回收',
    '铝电解 霍尔埃鲁 节能 减排',
  ],
  energy_restructuring: [
    '氢冶金 低碳 炼钢 减排',
    '碳捕集 钢铁 CCUS 冶金',
    '可再生能源 绿色 氢能 钢铁',
    '冶金 炉窑 节能 余热 回收',
    '生物质 碳 冶金 替代燃料',
    '钢铁 行业 碳中和 去碳化',
    '氢等离子体 熔融还原 炼铁',
  ],
  resource_utilization: [
    '冶金 渣 资源化 利用',
    '钢渣 利用 水泥 建材',
    '冶金 尘泥 回收 锌',
    '二次资源 冶金 城市矿山',
    '冶金 固废 处理 循环经济',
    '稀土 回收 磁材 电子 废料',
    '钢铁 废钢 回收 优化 利用',
  ],
};

// OpenAlex type → 我们的 document_type
const TYPE_MAP = {
  'article': 'paper',
  'review': 'paper',
  'book-chapter': 'book',
  'book': 'book',
  'monograph': 'book',
  'reference-book': 'book',
  'report': 'report',
  'standard': 'standard',
  'dissertation': 'report',
  'proceedings': 'paper',
  'proceedings-article': 'paper',
  'dataset': 'report',
  'other': 'paper',
};

// ========== 数据库连接 ==========
const pool = new Pool({
  host: '127.0.0.1', port: 5432,
  database: 'metallurgy_literature',
  user: 'postgres', password: '',
  max: 5,
});

// ========== 重建摘要 ==========
function invertAbstract(idx) {
  if (!idx || typeof idx !== 'object') return null;
  const tokens = [];
  for (const [word, positions] of Object.entries(idx)) {
    if (Array.isArray(positions)) {
      for (const pos of positions) tokens.push([pos, word]);
    }
  }
  if (tokens.length === 0) return null;
  tokens.sort((a, b) => a[0] - b[0]);
  return tokens.map(t => t[1]).join(' ');
}

// ========== OpenAlex API 调用 ==========
function searchOpenAlex(query, rows = 25, cursor = null) {
  return new Promise((resolve, reject) => {
    const params = new URLSearchParams({
      search: query,
      per_page: Math.min(rows, 200),
      mailto: MAILTO,
      select: 'doi,title,authorships,publication_year,primary_location,type,abstract_inverted_index,language,keywords',
    });
    if (cursor) params.set('cursor', cursor);
    const apiUrl = `https://api.openalex.org/works?${params.toString()}`;

    https.get(apiUrl, { timeout: 15000 }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const parsed = JSON.parse(data);
          resolve(parsed);
        } catch (e) {
          reject(new Error(`Parse error: ${e.message}`));
        }
      });
    }).on('error', reject).on('timeout', function () { this.destroy(); reject(new Error('Timeout')); });
  });
}

// ========== 格式化引用 ==========
function buildCitation(item) {
  const authors = (item.authorships || []).map(a => a.author?.display_name || '').filter(Boolean);
  const year = item.publication_year || '';
  const title = item.title || '';
  const journal = item.primary_location?.source?.display_name || '';
  const doi = item.doi ? item.doi.replace('https://doi.org/', '') : '';
  const parts = [];
  if (authors.length) parts.push(authors.join(', '));
  if (year) parts.push(`(${year})`);
  if (title) parts.push(title);
  if (journal) parts.push(journal);
  if (doi) parts.push(`https://doi.org/${doi}`);
  return parts.join('. ') + '.';
}

// ========== 提取年份 ==========
function extractYear(item) {
  return item.publication_year || null;
}

// ========== 入库逻辑 ==========
async function importPapers(domainCode, papers) {
  const client = await pool.connect();
  let imported = 0, skipped = 0;

  try {
    // 确保来源存在
    let sourceId;
    const srcRes = await client.query(
      `SELECT source_id FROM literature.sources WHERE source_name = 'OpenAlex'`
    );
    if (srcRes.rows.length === 0) {
      const ins = await client.query(
        `INSERT INTO literature.sources (source_name, source_type, provider, access_url)
         VALUES ('OpenAlex', 'journal', 'OpenAlex', 'https://openalex.org')
         RETURNING source_id`
      );
      sourceId = ins.rows[0].source_id;
      console.log('  📦 创建来源: OpenAlex');
    } else {
      sourceId = srcRes.rows[0].source_id;
    }

    for (const paper of papers) {
      const doi = paper.doi ? paper.doi.replace('https://doi.org/', '') : null;
      if (!doi) { skipped++; continue; }

      // 检查 DOI 是否已存在
      const existRes = await client.query(
        `SELECT document_id FROM literature.documents WHERE doi = $1 AND doi IS NOT NULL`,
        [doi]
      );
      if (existRes.rows.length > 0) { skipped++; continue; }

      const title = (paper.title || '').slice(0, 2000);
      if (!title) { skipped++; continue; }

      const year = extractYear(paper);
      const journal = (paper.primary_location?.source?.display_name || '').slice(0, 1000);
      const abstract = invertAbstract(paper.abstract_inverted_index) || null;
      const docType = TYPE_MAP[paper.type] || 'paper';
      const citation = buildCitation(paper);
      const sourceUrl = paper.doi || (doi ? `https://doi.org/${doi}` : null);
      const lang = paper.language || 'zh';

      await client.query('BEGIN');

      const docRes = await client.query(`
        INSERT INTO literature.documents
          (source_id, title, document_type, abstract, journal_name,
           publication_year, doi, source_url,
           citation_text, language, status, security_level, is_featured,
           published_at, created_by)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,NOW(),'openalex_import')
        RETURNING document_id, document_code
      `, [
        sourceId, title, docType, abstract, journal,
        year, doi, sourceUrl, citation, lang,
        'published', 'public', Math.random() < 0.1,
      ]);

      const { document_id, document_code } = docRes.rows[0];

      // 插入作者
      const authors = paper.authorships || [];
      for (let i = 0; i < authors.length; i++) {
        const authorName = authors[i].author?.display_name?.trim().slice(0, 255);
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

      // 提取关键词
      const keywordsFromApi = (paper.keywords || []).map(k => k.keyword).filter(Boolean);
      const titleWords = (title || '').split(/[\s,;:()，；：、]+/).filter(w => w.length > 1).slice(0, 8);
      const keywords = [...new Set([...keywordsFromApi, ...titleWords])].slice(0, 10);

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
  console.log('  OpenAlex 中文冶金文献批量导入');
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
      let cursor = null;
      let page = 0;

      // 第一页 cursor=null, 后续页用返回的 cursor
      while (allPapers.length < ROWS_PER_DOMAIN && (cursor !== null || page === 0)) {
        try {
          const batchSize = Math.min(25, ROWS_PER_DOMAIN - allPapers.length);
          console.log(`  🔍 [第${page+1}页] "${q.slice(0, 40)}"`);
          const result = await searchOpenAlex(q, batchSize, cursor);
          const items = result.results || [];
          cursor = result.meta?.next_cursor || null;

          for (const item of items) {
            const doi = item.doi ? item.doi.replace('https://doi.org/', '') : null;
            if (doi && !seenDOIs.has(doi) && item.title) {
              seenDOIs.add(doi);
              allPapers.push(item);
            }
          }
          console.log(`     → 获取 ${items.length} 条，去重后共 ${allPapers.length} 篇`);
          totalQueried += items.length;
          page++;

          if (!cursor) break;
          await new Promise(r => setTimeout(r, 200));
        } catch (e) {
          console.error(`     ⚠️  查询失败: ${e.message}`);
          await new Promise(r => setTimeout(r, 1000));
          break;
        }
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

    await new Promise(r => setTimeout(r, 500));
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
