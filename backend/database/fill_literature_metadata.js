/**
 * CrossRef DOI 批量补数据脚本
 *
 * 对已有 DOI 但缺作者/摘要的文献，逐条从 CrossRef API 拉取补全。
 *
 * 用法: node fill_literature_metadata.js [--limit=50] [--dry-run]
 */

const { Pool } = require('pg');
const https = require('https');

// ========== 配置 ==========
const LIMIT = parseInt(process.argv.find(a => a.startsWith('--limit='))?.split('=')[1] || '9999');
const DRY_RUN = process.argv.includes('--dry-run');

const MAILTO = 'xiangyu@metallurgy.edu.cn';

// ========== 数据库连接 ==========
const pool = new Pool({
  host: '127.0.0.1',
  port: 5432,
  database: 'metallurgy_literature',
  user: 'postgres',
  password: '',
  max: 5,
});

// ========== CrossRef API: 按 DOI 获取单篇 ==========
function fetchByDOI(doi) {
  return new Promise((resolve, reject) => {
    const url = `https://api.crossref.org/works/${encodeURIComponent(doi)}?mailto=${MAILTO}`;
    https.get(url, { timeout: 15000 }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        if (res.statusCode === 404) return resolve(null);
        if (res.statusCode !== 200) {
          return reject(new Error(`HTTP ${res.statusCode}: ${data.slice(0, 200)}`));
        }
        try {
          const parsed = JSON.parse(data);
          if (parsed.status !== 'ok') return resolve(null);
          resolve(parsed.message);
        } catch (e) {
          reject(new Error(`Parse error: ${e.message}`));
        }
      });
    }).on('error', reject).on('timeout', function () {
      this.destroy();
      reject(new Error('Timeout'));
    });
  });
}

// ========== 提取年份 ==========
function extractYear(item) {
  const src = item['published-print'] || item['published-online'] || item['issued'] || {};
  const parts = src['date-parts'];
  if (parts && parts[0] && parts[0][0]) return parts[0][0];
  return null;
}

// ========== 格式化引用（重建 citation_text） ==========
function buildCitation(item) {
  const authors = (item.author || []).map(a => `${a.family || ''} ${a.given || ''}`.trim() || a.name || '').filter(Boolean);
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

// ========== 主流程 ==========
async function main() {
  console.log('========================================');
  console.log('  CrossRef 文献元数据补全脚本');
  console.log(`  Limit: ${LIMIT === 9999 ? '无限制' : LIMIT}`);
  console.log(`  Mode: ${DRY_RUN ? 'DRY RUN（只查不写）' : '正式更新'}`);
  console.log('========================================\n');

  // 查缺作者的已发表文献（CrossRef 作者数据覆盖较好）
  const missing = await pool.query(`
    SELECT d.document_id, d.document_code, d.title, d.doi
    FROM literature.documents d
    WHERE d.status = 'published'
      AND d.doi IS NOT NULL
      AND NOT EXISTS (SELECT 1 FROM literature.document_authors WHERE document_id = d.document_id)
    ORDER BY d.document_id
    LIMIT ${LIMIT}
  `);

  console.log(`需要补作者的文献: ${missing.rows.length} 篇\n`);

  if (missing.rows.length === 0) {
    console.log('🎉 所有文献数据已完整！');
    await pool.end();
    return;
  }

  let fetched = 0;
  let updated = 0;
  let authorAdded = 0;
  let failed = 0;

  for (const row of missing.rows) {
    const { document_id, document_code, doi } = row;
    process.stdout.write(`[${String(++fetched).padStart(3, '0')}/${missing.rows.length}] ${document_code}... `);

    try {
      const msg = await fetchByDOI(doi);

      if (!msg) {
        console.log(`⚠️  DOI 无响应 (${doi})`);
        failed++;
        await new Promise(r => setTimeout(r, 200));
        continue;
      }

      const abstract = (msg.abstract || '').replace(/<[^>]*>/g, '').slice(0, 10000) || null;
      const authors = msg.author || [];
      const citation = buildCitation(msg);

      // 更新引用格式（可能有更好格式）
      if (!DRY_RUN) {
        await pool.query(
          `UPDATE literature.documents SET citation_text = $1 WHERE document_id = $2`,
          [citation, document_id]
        );
      }
      updated++;

      // 补作者
      if (authors.length > 0) {
        let added = 0;
        for (let i = 0; i < authors.length; i++) {
          const a = authors[i];
          const authorName = ([a.given, a.family].filter(Boolean).join(' ').trim() || a.name || '').slice(0, 255);
          if (!authorName) continue;

          if (!DRY_RUN) {
            const existing = await pool.query(
              'SELECT author_id FROM literature.authors WHERE author_name = $1',
              [authorName]
            );
            let authorId;
            if (existing.rows.length > 0) {
              authorId = existing.rows[0].author_id;
            } else {
              const ins = await pool.query(
                'INSERT INTO literature.authors (author_name) VALUES ($1) RETURNING author_id',
                [authorName]
              );
              authorId = ins.rows[0].author_id;
            }

            await pool.query(
              `INSERT INTO literature.document_authors (document_id, author_id, author_order)
               VALUES ($1,$2,$3) ON CONFLICT DO NOTHING`,
              [document_id, authorId, i + 1]
            );
          }
          added++;
        }
        authorAdded += added;
        process.stdout.write(`✅ +${added} 位作者`);
      } else {
        process.stdout.write(`⚠️  CrossRef 无作者数据`);
      }

      console.log();
    } catch (e) {
      console.log(`❌ ${e.message}`);
      failed++;
    }

    // CrossRef 限流：最多 50 req/s，这里每秒约 3-5 条
    await new Promise(r => setTimeout(r, 350));
  }

  console.log('\n========================================');
  console.log('  补全完成');
  console.log(`  处理: ${fetched} 篇`);
  console.log(`  更新字段: ${updated} 篇`);
  console.log(`  新增作者: ${authorAdded} 人次`);
  console.log(`  失败: ${failed} 篇`);
  if (DRY_RUN) console.log('  (DRY RUN — 未写入数据库)');
  console.log('========================================');

  await pool.end();
}

main().catch(e => {
  console.error('❌ 严重错误:', e.message);
  pool.end();
  process.exit(1);
});
