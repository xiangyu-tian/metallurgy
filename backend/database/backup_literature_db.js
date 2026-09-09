/** 导出 literature Schema 的全部业务数据为 gzip JSON，便于清理前恢复。 */

const fs = require('fs');
const path = require('path');
const zlib = require('zlib');
const { Pool } = require('pg');

const outputArg = process.argv.find((arg) => arg.startsWith('--output='));
const outputPath = path.resolve(
  outputArg?.slice('--output='.length)
    || `backups/metallurgy_literature_${new Date().toISOString().replace(/[:.]/g, '-')}.json.gz`,
);

const tables = [
  'sources',
  'domains',
  'documents',
  'authors',
  'keywords',
  'document_authors',
  'document_domains',
  'document_keywords',
  'attachments',
];

const pool = new Pool({
  host: process.env.LITERATURE_DB_HOST || '127.0.0.1',
  port: parseInt(process.env.LITERATURE_DB_PORT || '5432', 10),
  database: process.env.LITERATURE_DB_NAME || 'metallurgy_literature',
  user: process.env.LITERATURE_DB_USER || 'postgres',
  password: process.env.LITERATURE_DB_PASSWORD || '',
});

async function main() {
  const client = await pool.connect();
  try {
    await client.query('BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY');
    const data = {};
    const counts = {};
    for (const table of tables) {
      const result = await client.query(`SELECT * FROM literature.${table}`);
      data[table] = result.rows;
      counts[table] = result.rowCount;
    }
    await client.query('COMMIT');

    const backup = {
      format: 'metallurgy-literature-json-v1',
      created_at: new Date().toISOString(),
      database: 'metallurgy_literature',
      schema: 'literature',
      counts,
      data,
    };
    fs.mkdirSync(path.dirname(outputPath), { recursive: true });
    fs.writeFileSync(outputPath, zlib.gzipSync(JSON.stringify(backup)));
    console.log(JSON.stringify({ output: outputPath, counts }, null, 2));
  } catch (error) {
    await client.query('ROLLBACK');
    throw error;
  } finally {
    client.release();
  }
}

main()
  .catch((error) => {
    console.error('备份失败:', error);
    process.exitCode = 1;
  })
  .finally(() => pool.end());
