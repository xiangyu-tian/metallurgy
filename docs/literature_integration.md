# 文献数据库集成说明

## 模块边界

文献数据保存在独立 PostgreSQL 数据库 `metallurgy_literature` 的 `literature` Schema 中。平台后端通过独立连接池访问该库，前端只通过 `/api` 契约读取或管理文献，不直接连接数据库。

## 运行配置

后端支持以下环境变量；未设置时使用本机 PostgreSQL 默认配置：

- `LITERATURE_DB_HOST`：数据库主机，默认 `127.0.0.1`
- `LITERATURE_DB_PORT`：数据库端口，默认 `5432`
- `LITERATURE_DB_NAME`：数据库名，默认 `metallurgy_literature`
- `LITERATURE_DB_USER`：数据库用户，默认 `postgres`
- `LITERATURE_DB_PASSWORD`：数据库密码，默认空字符串

新环境先创建 `metallurgy_literature` 数据库，再在该数据库中执行 `backend/database/create_literature_db.sql`。`backend/database/` 下其余脚本用于从 Crossref、OpenAlex、Semantic Scholar 和 arXiv 导入或补全文献元数据。

## API 契约

所有成功响应均为 `{ code: 200, data: ... }`，失败响应为 `{ code, message, error? }`。

### 公开接口

- `GET /api/literature/documents`：分页检索；参数 `q`、`domain`、`document_type`、`year_from`、`year_to`、`page`、`page_size`、`sort`
- `GET /api/literature/documents/:documentCode`：文献详情、PDF 附件及相关文献
- `GET /api/literature/domains/:domainCode/documents`：领域文献；参数 `document_type`、`featured`、`limit`
- `GET /api/literature/featured`：推荐文献
- `GET /api/literature/domains`：启用的领域列表

公开接口只返回 `status = published` 且 `security_level = public` 的数据。

### 管理接口

管理接口复用平台账号系统，通过 `X-User-Id` 请求头验证管理员身份：

- `POST /api/admin/literature/documents`：新增文献
- `GET /api/admin/literature/documents`：管理列表
- `POST /api/admin/literature/documents/:documentCode/review`：发布、退回或转草稿
- `POST /api/admin/literature/documents/:documentCode/archive`：下架归档
- `PUT /api/admin/literature/documents/:documentCode`：更新文献字段

## 前端入口

- `/knowledge`：专业文献中心
- `/knowledge/documents/:documentCode`：文献详情
- `/admin/knowledge`：管理员文献管理

五个专业领域页通过 `LiteratureSection` 组件展示各自领域的最新文献。

## PDF 数据维护

- `node backend/database/sync_open_access_pdfs.js`：只读审计 PDF 覆盖率
- `node backend/database/sync_open_access_pdfs.js --apply --delete-missing`：写入开放 PDF 附件并删除无 PDF/查询失败文献
- `node backend/database/import_openalex_oa_curated.js --apply --rows=20`：按五个冶金领域严格筛选并补充开放获取论文
- `node backend/database/import_google_scholar_seeds.js --apply`：导入人工筛选的 Google Scholar 高引用种子论文，并用 OpenAlex 验证 DOI/PDF
- `node backend/database/backup_literature_db.js`：清理前导出 gzip JSON 备份
