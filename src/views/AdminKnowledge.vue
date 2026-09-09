<template>
  <div class="admin-knowledge">
    <Header></Header>

    <div class="mb-nav">
      <div class="container">
        <p>
          当前位置：<router-link to="/">首页</router-link> >
          <router-link to="/profile">个人中心</router-link> >
          <span>文献管理</span>
        </p>
      </div>
    </div>

    <section class="ak-main">
      <div class="container">
        <div class="ak-header">
          <h2>文献管理</h2>
          <div class="ak-actions">
            <button class="ak-btn ak-btn-primary" @click="showForm = true; editDoc = {};">
              <i class="fas fa-plus"></i> 新增文献
            </button>
            <select v-model="filterStatus" @change="fetchDocs" class="ak-status-filter">
              <option value="">全部状态</option>
              <option value="draft">草稿</option>
              <option value="pending_review">待审核</option>
              <option value="published">已发布</option>
              <option value="archived">已下架</option>
            </select>
          </div>
        </div>

        <!-- 新增/编辑表单 -->
        <div v-if="showForm" class="ak-form-overlay" @click.self="showForm = false">
          <div class="ak-form-card">
            <h3>{{ editDoc.document_code ? '编辑文献' : '新增文献' }}</h3>
            <div class="ak-form-grid">
              <div class="ak-form-group full">
                <label>标题 *</label>
                <input v-model="form.title" placeholder="文献标题" />
              </div>
              <div class="ak-form-group">
                <label>文献类型 *</label>
                <select v-model="form.document_type">
                  <option value="paper">论文</option>
                  <option value="standard">标准</option>
                  <option value="patent">专利</option>
                  <option value="report">报告</option>
                  <option value="book">图书</option>
                  <option value="manual">手册</option>
                </select>
              </div>
              <div class="ak-form-group">
                <label>出版年份</label>
                <input v-model.number="form.publication_year" type="number" placeholder="2025" />
              </div>
              <div class="ak-form-group full">
                <label>期刊/会议</label>
                <input v-model="form.journal_name" placeholder="期刊名称" />
              </div>
              <div class="ak-form-group full">
                <label>摘要</label>
                <textarea v-model="form.abstract" rows="4" placeholder="文献摘要"></textarea>
              </div>
              <div class="ak-form-group">
                <label>DOI</label>
                <input v-model="form.doi" placeholder="10.xxxx/xxxxx" />
              </div>
              <div class="ak-form-group">
                <label>来源链接</label>
                <input v-model="form.source_url" placeholder="https://..." />
              </div>
              <div class="ak-form-group full">
                <label>作者（每行一个：姓名, 机构, 序号）</label>
                <textarea v-model="form.authorsText" rows="3" placeholder="张明, 北京科技大学, 1&#10;李华, 东北大学, 2"></textarea>
              </div>
              <div class="ak-form-group">
                <label>研究领域</label>
                <div class="ak-checkbox-group">
                  <label v-for="d in domains" :key="d.domain_code" class="ak-checkbox">
                    <input type="checkbox" :value="d.domain_code" v-model="form.domain_codes" />
                    {{ d.domain_name }}
                  </label>
                </div>
              </div>
              <div class="ak-form-group">
                <label>关键词（逗号分隔）</label>
                <input v-model="form.keywordsText" placeholder="氢冶金, 直接还原" />
              </div>
              <div class="ak-form-group">
                <label>公开级别</label>
                <select v-model="form.security_level">
                  <option value="public">公开</option>
                  <option value="internal">内部</option>
                </select>
              </div>
            </div>
            <div class="ak-form-actions">
              <button class="ak-btn" @click="showForm = false">取消</button>
              <button class="ak-btn ak-btn-primary" @click="saveDoc" :disabled="saving">
                {{ saving ? '保存中…' : '保存' }}
              </button>
            </div>
            <div v-if="formError" class="ak-form-error">{{ formError }}</div>
          </div>
        </div>

        <!-- 文献列表 -->
        <div class="ak-table-wrap">
          <table class="ak-table">
            <thead>
              <tr>
                <th>编号</th>
                <th>标题</th>
                <th>类型</th>
                <th>年份</th>
                <th>状态</th>
                <th>公开</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody v-if="docs.length === 0">
              <tr><td colspan="7" class="ak-empty">暂无文献</td></tr>
            </tbody>
            <tbody v-else>
              <tr v-for="doc in docs" :key="doc.document_id">
                <td>{{ doc.document_code }}</td>
                <td class="ak-title-cell">{{ doc.title }}</td>
                <td>{{ typeLabel(doc.document_type) }}</td>
                <td>{{ doc.publication_year }}</td>
                <td>
                  <span :class="'ak-status ak-status-' + doc.status">
                    {{ statusLabel(doc.status) }}
                  </span>
                </td>
                <td>{{ doc.security_level === 'public' ? '公开' : '内部' }}</td>
                <td class="ak-actions-cell">
                  <button
                    v-if="doc.status === 'draft' || doc.status === 'pending_review'"
                    class="ak-action-btn publish"
                    @click="reviewDoc(doc.document_code, 'publish')"
                    title="发布"
                  ><i class="fas fa-check"></i></button>
                  <button
                    v-if="doc.status === 'published'"
                    class="ak-action-btn archive"
                    @click="archiveDoc(doc.document_code)"
                    title="下架"
                  ><i class="fas fa-archive"></i></button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- 分页 -->
        <div v-if="totalPages > 1" class="ak-pagination">
          <button :disabled="page <= 1" @click="goPage(page - 1)"><i class="fas fa-chevron-left"></i></button>
          <span>{{ page }} / {{ totalPages }}</span>
          <button :disabled="page >= totalPages" @click="goPage(page + 1)"><i class="fas fa-chevron-right"></i></button>
        </div>
      </div>
    </section>

    <Footer></Footer>
  </div>
</template>

<script>
import Header from '@/components/Header.vue';
import Footer from '@/components/Footer.vue';
import request from '@/utils/request.js';

export default {
  name: 'AdminKnowledge',
  components: { Header, Footer },
  data() {
    return {
      docs: [],
      domains: [],
      filterStatus: '',
      page: 1,
      pageSize: 20,
      total: 0,
      showForm: false,
      editDoc: {},
      form: {
        title: '', document_type: 'paper', publication_year: null,
        journal_name: '', abstract: '', doi: '', source_url: '',
        authorsText: '', domain_codes: [], keywordsText: '',
        security_level: 'public',
      },
      saving: false,
      formError: '',
    };
  },
  computed: {
    totalPages() { return Math.ceil(this.total / this.pageSize); },
  },
  methods: {
    typeLabel(t) { return { paper: '论文', standard: '标准', patent: '专利', report: '报告', book: '图书', manual: '手册' }[t] || t; },
    statusLabel(s) { return { draft: '草稿', pending_review: '待审核', published: '已发布', archived: '已下架' }[s] || s; },
    async fetchDomains() {
      try { const r = await request.get('/literature/domains'); this.domains = r.data.items; }
      catch (e) { console.error(e); }
    },
    async fetchDocs() {
      try {
        const params = { page: this.page, page_size: this.pageSize };
        if (this.filterStatus) params.status = this.filterStatus;
        const r = await request.get('/admin/literature/documents', { params });
        this.docs = r.data.items || [];
        this.total = r.data.total || 0;
      } catch (e) { console.error(e); this.docs = []; this.total = 0; }
    },
    async saveDoc() {
      if (!this.form.title) { this.formError = '标题为必填项'; return; }
      this.saving = true;
      this.formError = '';
      try {
        const authors = this.form.authorsText.split('\n')
          .filter(l => l.trim())
          .map((l, i) => {
            const parts = l.split(',').map(s => s.trim());
            return { author_name: parts[0], institution: parts[1] || '', author_order: parseInt(parts[2]) || i + 1 };
          });
        const keywords = this.form.keywordsText.split(/[,，、]/).map(s => s.trim()).filter(Boolean);
        const body = {
          title: this.form.title,
          document_type: this.form.document_type,
          publication_year: this.form.publication_year || null,
          journal_name: this.form.journal_name || null,
          abstract: this.form.abstract || null,
          doi: this.form.doi || null,
          source_url: this.form.source_url || null,
          authors,
          domain_codes: this.form.domain_codes,
          keywords,
          security_level: this.form.security_level,
        };
        await request.post('/admin/literature/documents', body);
        this.showForm = false;
        this.fetchDocs();
        alert('文献已创建');
      } catch (e) { this.formError = e.message || '保存失败'; }
      this.saving = false;
    },
    async reviewDoc(code, action) {
      try { await request.post(`/admin/literature/documents/${code}/review`, { action }); this.fetchDocs(); }
      catch (e) { alert(e.message); }
    },
    async archiveDoc(code) {
      try { await request.post(`/admin/literature/documents/${code}/archive`); this.fetchDocs(); }
      catch (e) { alert(e.message); }
    },
    goPage(p) { if (p >= 1 && p <= this.totalPages) { this.page = p; this.fetchDocs(); } },
  },
  mounted() {
    this.fetchDomains();
    this.fetchDocs();
  },
};
</script>

<style scoped>
.ak-main { padding: 30px 0 60px; background: #f5f7fa; min-height: 60vh; }
.ak-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.ak-header h2 { font-size: 22px; color: #333; }
.ak-actions { display: flex; gap: 10px; align-items: center; }
.ak-btn { padding: 8px 18px; border: 1px solid #ddd; background: #fff; border-radius: 4px; cursor: pointer; font-size: 13px; }
.ak-btn-primary { background: #1a3a5c; color: #fff; border-color: #1a3a5c; }
.ak-btn-primary:hover { background: #2c5f8a; }
.ak-btn:disabled { opacity: .5; cursor: default; }
.ak-status-filter { padding: 6px 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 13px; }

/* 表单覆盖层 */
.ak-form-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,.4); z-index: 1000; display: flex; align-items: center; justify-content: center; }
.ak-form-card { background: #fff; border-radius: 8px; padding: 28px; width: 720px; max-height: 85vh; overflow-y: auto; }
.ak-form-card h3 { font-size: 18px; margin-bottom: 20px; }
.ak-form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.ak-form-group.full { grid-column: 1 / -1; }
.ak-form-group label { display: block; font-size: 13px; color: #666; margin-bottom: 4px; }
.ak-form-group input, .ak-form-group select, .ak-form-group textarea { width: 100%; padding: 8px 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 13px; box-sizing: border-box; }
.ak-form-group textarea { resize: vertical; }
.ak-checkbox-group { display: flex; flex-wrap: wrap; gap: 8px; }
.ak-checkbox { font-size: 13px; cursor: pointer; }
.ak-checkbox input { margin-right: 4px; width: auto !important; }
.ak-form-actions { display: flex; gap: 10px; justify-content: flex-end; margin-top: 20px; }
.ak-form-error { color: #e74c3c; font-size: 13px; margin-top: 10px; }

/* 表格 */
.ak-table-wrap { background: #fff; border-radius: 6px; overflow: hidden; }
.ak-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.ak-table th { background: #f5f7fa; color: #666; padding: 12px 14px; text-align: left; font-weight: 600; border-bottom: 2px solid #e0e0e0; }
.ak-table td { padding: 12px 14px; border-bottom: 1px solid #f0f0f0; }
.ak-table tr:hover td { background: #fafbfc; }
.ak-title-cell { max-width: 280px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ak-empty { text-align: center; color: #999; padding: 40px !important; }
.ak-status { display: inline-block; padding: 2px 10px; border-radius: 10px; font-size: 12px; }
.ak-status-draft { background: #fff3e0; color: #e67e22; }
.ak-status-pending_review { background: #e3f2fd; color: #1976d2; }
.ak-status-published { background: #e8f5e9; color: #388e3c; }
.ak-status-archived { background: #f5f5f5; color: #999; }
.ak-actions-cell { white-space: nowrap; }
.ak-action-btn { width: 30px; height: 30px; border: 1px solid #ddd; border-radius: 4px; background: #fff; cursor: pointer; margin-right: 4px; }
.ak-action-btn.publish { color: #388e3c; }
.ak-action-btn.publish:hover { background: #e8f5e9; border-color: #388e3c; }
.ak-action-btn.archive { color: #e67e22; }
.ak-action-btn.archive:hover { background: #fff3e0; border-color: #e67e22; }
.ak-pagination { display: flex; justify-content: center; align-items: center; gap: 10px; margin-top: 20px; font-size: 13px; }
.ak-pagination button { width: 32px; height: 32px; border: 1px solid #ddd; background: #fff; border-radius: 4px; cursor: pointer; }
.ak-pagination button:disabled { opacity: .4; cursor: default; }
</style>
