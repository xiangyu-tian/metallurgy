/**
 * Semantic Scholar 摘要补全脚本
 *
 * 对已有 DOI 但缺摘要的文献，从 Semantic Scholar API 拉取摘要。
 *
 * 用法: node fill_abstracts_s2.js [--limit=50] [--dry-run]
 */

const { Pool } = require('pg');
const https = require('https');

const LIMIT = parseInt(process.argv.find(a => a.startsWith('--limit='))?.split('=')[1] || '9999');
const DRY_RUN = process.argv.includes('--dry-run');

const pool = new Pool({
  host: '127.0.0.1', port: 5432,
  database: 'metallurgy_literature',
  user: 'postgres', password: '',
  max: 5,
});

function fetchFromS2(doi) {
  return new Promise((resolve) => {
    const url = `https://api.semanticscholar.org/graph/v1/paper/DOI:${encodeURIComponent(doi)}?fields=title,abstract`;
    https.get(url, { timeout: 15000 }, (res) => {
      let data = '';
      res.on('data', c => data += c);
      res.on('end', () => {
        if (res.statusCode !== 200) return resolve(null);
        try {
          const parsed = JSON.parse(data);
          resolve(parsed || null);
        } catch { resolve(null); }
      });
    }).on('error', () => resolve(null)).on('timeout', function () { this.destroy(); resolve(null); });
  });
}

async function main() {
  console.log('========================================');
  console.log('  Semantic Scholar 摘要补全脚本');
  console.log(`  Limit: ${LIMIT === 9999 ? '无限制' : LIMIT}`);
  console.log(`  Mode: ${DRY_RUN ? 'DRY RUN' : '正式更新'}`);
  console.log('========================================\n');

  const missing = await pool.query(`
    SELECT document_id, document_code, doi, title
    FROM literature.documents
    WHERE status = 'published'
      AND doi IS NOT NULL
      AND (abstract IS NULL OR abstract = '')
    ORDER BY document_id
    LIMIT ${LIMIT}
  `);

  console.log(`需要补摘要的文献: ${missing.rows.length} 篇\n`);

  if (missing.rows.length === 0) {
    console.log('🎉 所有文献已有摘要！');
    await pool.end();
    return;
  }

  let fetched = 0, updated = 0, failed = 0;

  for (const row of missing.rows) {
    const { document_id, document_code, doi } = row;
    process.stdout.write(`[${String(++fetched).padStart(3, '0')}/${missing.rows.length}] ${document_code}... `);

    try {
      const paper = await fetchFromS2(doi);

      if (!paper || !paper.abstract) {
        console.log('⏭️  S2 无摘要');
        failed++;
        await new Promise(r => setTimeout(r, 1100));
        continue;
      }

      const abstract = paper.abstract.slice(0, 10000);

      if (!DRY_RUN) {
        await pool.query(
          `UPDATE literature.documents SET abstract = $1, abstract_en = $1 WHERE document_id = $2`,
          [abstract, document_id]
        );
      }
      updated++;
      const preview = abstract.length > 60 ? abstract.slice(0, 60) + '…' : abstract;
      console.log(`✅ ${preview}`);
    } catch (e) {
      console.log(`❌ ${e.message}`);
      failed++;
    }

    // Semantic Scholar rate limit: ~1 req/s (free tier)
    await new Promise(r => setTimeout(r, 1100));
  }

  console.log('\n========================================');
  console.log('  补全完成');
  console.log(`  处理: ${fetched} 篇`);
  console.log(`  更新摘要: ${updated} 篇`);
  console.log(`  失败/S2无数据: ${failed} 篇`);
  if (DRY_RUN) console.log('  (DRY RUN)');
  console.log('========================================');

  await pool.end();
}

main().catch(e => {
  console.error('❌ 严重错误:', e.message);
  pool.end();
  process.exit(1);
});
