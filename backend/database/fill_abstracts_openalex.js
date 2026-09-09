/**
 * OpenAlex 摘要补全脚本
 *
 * 对已有 DOI 但缺摘要的文献，从 OpenAlex API 拉取摘要补全。
 * 摘要格式：abstract_inverted_index → 重构为纯文本。
 *
 * 用法: node fill_abstracts_openalex.js [--limit=50] [--dry-run]
 */

const { Pool } = require('pg');
const https = require('https');

const LIMIT = parseInt(process.argv.find(a => a.startsWith('--limit='))?.split('=')[1] || '9999');
const DRY_RUN = process.argv.includes('--dry-run');

const MAILTO = 'xiangyu@metallurgy.edu.cn';
const pool = new Pool({
  host: '127.0.0.1', port: 5432,
  database: 'metallurgy_literature',
  user: 'postgres', password: '',
  max: 5,
});

// ========== 从 OpenAlex 拉取 ==========
function fetchFromOpenAlex(doi) {
  return new Promise((resolve) => {
    const url = `https://api.openalex.org/works/doi:${encodeURIComponent(doi)}?mailto=${MAILTO}`;
    https.get(url, { timeout: 15000 }, (res) => {
      let data = '';
      res.on('data', c => data += c);
      res.on('end', () => {
        if (res.statusCode !== 200) {
          if (res.statusCode === 404) return resolve({ notFound: true });
          return resolve(null);
        }
        try {
          resolve(JSON.parse(data));
        } catch { resolve(null); }
      });
    }).on('error', () => resolve(null)).on('timeout', function () { this.destroy(); resolve(null); });
  });
}

// ========== 转换 inverted index → plain text ==========
function invertAbstract(idx) {
  if (!idx || typeof idx !== 'object') return null;
  const tokens = [];
  for (const [word, positions] of Object.entries(idx)) {
    if (Array.isArray(positions)) {
      for (const pos of positions) {
        tokens.push([pos, word]);
      }
    }
  }
  if (tokens.length === 0) return null;
  tokens.sort((a, b) => a[0] - b[0]);
  return tokens.map(t => t[1]).join(' ');
}

async function main() {
  console.log('========================================');
  console.log('  OpenAlex 摘要补全脚本');
  console.log(`  Limit: ${LIMIT === 9999 ? '无限制' : LIMIT}`);
  console.log(`  Mode: ${DRY_RUN ? 'DRY RUN' : '正式更新'}`);
  console.log('========================================\n');

  const missing = await pool.query(`
    SELECT document_id, document_code, doi, title, document_type
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

  let fetched = 0, updated = 0, failed = 0, notFound = 0;

  for (const row of missing.rows) {
    const { document_id, document_code, doi, document_type } = row;
    process.stdout.write(`[${String(++fetched).padStart(3, '0')}/${missing.rows.length}] ${document_code} (${document_type})... `);

    try {
      const work = await fetchFromOpenAlex(doi);

      if (!work) {
        console.log('❌ API 错误');
        failed++;
        await new Promise(r => setTimeout(r, 200));
        continue;
      }

      if (work.notFound) {
        console.log('⏭️  OpenAlex 无此文献');
        notFound++;
        await new Promise(r => setTimeout(r, 200));
        continue;
      }

      const abstract = invertAbstract(work.abstract_inverted_index);
      if (!abstract) {
        console.log('⏭️  OpenAlex 无摘要');
        notFound++;
        await new Promise(r => setTimeout(r, 200));
        continue;
      }

      const trimmed = abstract.slice(0, 10000);

      if (!DRY_RUN) {
        await pool.query(
          `UPDATE literature.documents SET abstract = $1, abstract_en = $1 WHERE document_id = $2`,
          [trimmed, document_id]
        );
      }
      updated++;
      const preview = trimmed.length > 60 ? trimmed.slice(0, 60) + '…' : trimmed;
      console.log(`✅ ${preview}`);
    } catch (e) {
      console.log(`❌ ${e.message}`);
      failed++;
    }

    // OpenAlex 限流 10 req/s，这里保守 300ms
    await new Promise(r => setTimeout(r, 300));
  }

  console.log('\n========================================');
  console.log('  补全完成');
  console.log(`  处理: ${fetched} 篇`);
  console.log(`  更新摘要: ${updated} 篇`);
  console.log(`  OpenAlex无记录/无摘要: ${notFound} 篇`);
  console.log(`  失败: ${failed} 篇`);
  if (DRY_RUN) console.log('  (DRY RUN)');
  console.log('========================================');

  await pool.end();
}

main().catch(e => {
  console.error('❌ 严重错误:', e.message);
  pool.end();
  process.exit(1);
});
