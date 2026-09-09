<template>
  <div class="knowledge-center">
    <Header></Header>

    <!-- 面包屑 -->
    <div class="mb-nav">
      <div class="container">
        <p>
          当前位置：<router-link to="/">首页</router-link> >
          <span>专业文献中心</span>
        </p>
      </div>
    </div>

    <!-- Hero -->
    <section class="kc-hero">
      <div class="container">
        <div class="kc-hero-content">
          <h1>冶金专业文献中心</h1>
          <p class="kc-hero-sub">Metallurgy Literature Center</p>
          <p class="kc-hero-desc">
            汇聚冶金领域论文、标准、专利和技术报告，支持多维度检索与分类浏览
          </p>
        </div>
      </div>
    </section>

    <!-- 搜索栏 -->
    <section class="kc-search-section">
      <div class="container">
        <div class="kc-search-bar">
          <i class="fas fa-search"></i>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="搜索标题、作者、关键词…"
            @keyup.enter="doSearch"
          />
          <button class="kc-search-btn" @click="doSearch">检索</button>
        </div>
      </div>
    </section>

    <!-- 主区域 -->
    <section class="kc-main">
      <div class="container">
        <div class="kc-layout">
          <!-- 侧边筛选 -->
          <aside class="kc-sidebar">
            <!-- 研究领域 -->
            <div class="kc-filter-block">
              <h3>研究领域</h3>
              <ul class="kc-filter-list">
                <li
                  v-for="d in domains"
                  :key="d.domain_code"
                  :class="{ active: filterDomain === d.domain_code }"
                  @click="setDomain(d.domain_code)"
                >
                  {{ d.domain_name }}
                </li>
                <li
                  :class="{ active: filterDomain === '' }"
                  @click="setDomain('')"
                >全部领域</li>
              </ul>
            </div>

            <!-- 文献类型 -->
            <div class="kc-filter-block">
              <h3>文献类型</h3>
              <ul class="kc-filter-list">
                <li
                  v-for="t in docTypes"
                  :key="t.value"
                  :class="{ active: filterType === t.value }"
                  @click="setType(t.value)"
                >{{ t.label }}</li>
              </ul>
            </div>

            <!-- 出版年份 -->
            <div class="kc-filter-block">
              <h3>出版年份</h3>
              <div class="kc-year-range">
                <input v-model.number="yearFrom" type="number" placeholder="起始" min="1900" max="2030" />
                <span>—</span>
                <input v-model.number="yearTo" type="number" placeholder="结束" min="1900" max="2030" />
              </div>
              <button class="kc-year-btn" @click="doSearch">确定</button>
            </div>
          </aside>

          <!-- 主内容 -->
          <div class="kc-content">
            <!-- 推荐文献 -->
            <div v-if="featured.length > 0" class="kc-featured">
              <h3><i class="fas fa-star"></i> 推荐文献</h3>
              <div class="kc-featured-list">
                <div
                  class="kc-featured-item"
                  v-for="doc in featured"
                  :key="doc.document_code"
                  @click="$router.push(`/knowledge/documents/${doc.document_code}`)"
                >
                  <span class="kc-featured-type">{{ typeLabel(doc.document_type) }}</span>
                  <span class="kc-featured-title">{{ doc.title }}</span>
                  <span class="kc-featured-meta">{{ doc.journal_name }} {{ doc.publication_year }}</span>
                </div>
              </div>
            </div>

            <!-- 结果统计 -->
            <div class="kc-result-header">
              <span class="kc-result-count">共 {{ total }} 条结果</span>
              <div class="kc-sort">
                <label>排序：</label>
                <select v-model="sortOrder" @change="fetchDocs">
                  <option value="newest">最新优先</option>
                  <option value="oldest">最早优先</option>
                </select>
              </div>
            </div>

            <!-- 文献列表 -->
            <div v-if="loading" class="kc-loading">
              <i class="fas fa-spinner fa-spin"></i> 加载中…
            </div>

            <div v-else-if="docs.length === 0" class="kc-empty">
              <i class="fas fa-book-open"></i>
              <p>暂无文献数据</p>
            </div>

            <div v-else class="kc-doc-list">
              <div
                class="kc-doc-card"
                v-for="doc in docs"
                :key="doc.document_code"
                @click="$router.push(`/knowledge/documents/${doc.document_code}`)"
              >
                <div class="kc-doc-type">{{ typeLabel(doc.document_type) }}</div>
                <div class="kc-doc-body">
                  <h4 class="kc-doc-title">{{ doc.title }}</h4>
                  <p class="kc-doc-authors">{{ doc.authors.join('、') }}</p>
                  <p class="kc-doc-meta">
                    <span v-if="doc.journal_name">{{ doc.journal_name }}</span>
                    <span v-if="doc.publication_year">，{{ doc.publication_year }}</span>
                    <span v-if="doc.doi">，DOI: {{ doc.doi }}</span>
                  </p>
                  <p v-if="doc.abstract" class="kc-doc-abstract">{{ doc.abstract }}…</p>
                  <div class="kc-doc-tags" v-if="doc.keywords.length">
                    <span class="kc-tag" v-for="kw in doc.keywords.slice(0,4)" :key="kw">{{ kw }}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- 分页 -->
            <div v-if="totalPages > 1" class="kc-pagination">
              <button :disabled="page <= 1" @click="goPage(page - 1)"><i class="fas fa-chevron-left"></i></button>
              <button
                v-for="p in visiblePages"
                :key="p"
                :class="{ active: p === page }"
                @click="goPage(p)"
              >{{ p }}</button>
              <button :disabled="page >= totalPages" @click="goPage(page + 1)"><i class="fas fa-chevron-right"></i></button>
            </div>
          </div>
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
  name: 'KnowledgeCenter',
  components: { Header, Footer },
  data() {
    return {
      domains: [],
      featured: [],
      docs: [],
      searchQuery: '',
      filterDomain: '',
      filterType: '',
      yearFrom: null,
      yearTo: null,
      sortOrder: 'newest',
      page: 1,
      pageSize: 20,
      total: 0,
      loading: false,
      docTypes: [
        { value: '', label: '全部类型' },
        { value: 'paper', label: '论文' },
        { value: 'standard', label: '标准' },
        { value: 'patent', label: '专利' },
        { value: 'report', label: '报告' },
        { value: 'book', label: '图书' },
        { value: 'manual', label: '手册' },
      ],
    };
  },
  computed: {
    totalPages() {
      return Math.ceil(this.total / this.pageSize);
    },
    visiblePages() {
      const p = this.page;
      const t = this.totalPages;
      if (t <= 7) return Array.from({ length: t }, (_, i) => i + 1);
      if (p <= 4) return [1, 2, 3, 4, 5, '...', t];
      if (p >= t - 3) return [1, '...', t - 4, t - 3, t - 2, t - 1, t];
      return [1, '...', p - 1, p, p + 1, '...', t];
    },
  },
  methods: {
    typeLabel(type) {
      const map = { paper: '论文', standard: '标准', patent: '专利', report: '报告', book: '图书', manual: '手册' };
      return map[type] || type;
    },
    setDomain(code) {
      this.filterDomain = code;
      this.page = 1;
      this.fetchDocs();
    },
    setType(val) {
      this.filterType = val;
      this.page = 1;
      this.fetchDocs();
    },
    doSearch() {
      this.page = 1;
      this.fetchDocs();
    },
    goPage(p) {
      if (p < 1 || p > this.totalPages || p === this.page) return;
      this.page = p;
      this.fetchDocs();
    },
    async fetchDomains() {
      try {
        const res = await request.get('/literature/domains');
        this.domains = res.data.items;
      } catch (e) {
        console.error('获取领域失败', e);
      }
    },
    async fetchFeatured() {
      try {
        const res = await request.get('/literature/featured');
        this.featured = res.data.items || [];
      } catch (e) {
        console.error('获取推荐文献失败', e);
      }
    },
    async fetchDocs() {
      this.loading = true;
      try {
        const params = {
          page: this.page,
          page_size: this.pageSize,
          sort: this.sortOrder,
        };
        if (this.searchQuery) params.q = this.searchQuery;
        if (this.filterDomain) params.domain = this.filterDomain;
        if (this.filterType) params.document_type = this.filterType;
        if (this.yearFrom) params.year_from = this.yearFrom;
        if (this.yearTo) params.year_to = this.yearTo;

        const res = await request.get('/literature/documents', { params });
        this.docs = res.data.items || [];
        this.total = res.data.total || 0;
      } catch (e) {
        console.error('获取文献列表失败', e);
        this.docs = [];
        this.total = 0;
      }
      this.loading = false;
    },
  },
  mounted() {
    this.fetchDomains();
    this.fetchFeatured();
    this.fetchDocs();
  },
};
</script>

<style scoped>
.knowledge-center {
  padding-top: 90px;
}
.kc-hero {
  padding: 60px 0 40px;
  background: linear-gradient(135deg, #1a3a5c 0%, #2c5f8a 100%);
  color: #fff;
  text-align: center;
}
.kc-hero h1 { font-size: 32px; margin-bottom: 8px; }
.kc-hero-sub { font-size: 16px; opacity: 0.8; margin-bottom: 12px; }
.kc-hero-desc { font-size: 14px; opacity: 0.65; max-width: 600px; margin: 0 auto; }

.kc-search-section { padding: 24px 0; background: #f5f7fa; }
.kc-search-bar { display: flex; align-items: center; background: #fff; border: 1px solid #ddd; border-radius: 6px; padding: 4px; max-width: 700px; margin: 0 auto; }
.kc-search-bar i { padding: 0 12px; color: #999; }
.kc-search-bar input { flex: 1; border: none; outline: none; padding: 10px 0; font-size: 15px; }
.kc-search-btn { background: #1a3a5c; color: #fff; border: none; padding: 10px 28px; border-radius: 4px; cursor: pointer; font-size: 14px; }
.kc-search-btn:hover { background: #2c5f8a; }

.kc-main { padding: 30px 0 60px; background: #f5f7fa; }
.kc-layout { display: flex; gap: 30px; }
.kc-sidebar { width: 240px; flex-shrink: 0; }
.kc-content { flex: 1; min-width: 0; }

.kc-filter-block { background: #fff; border-radius: 6px; padding: 18px; margin-bottom: 16px; }
.kc-filter-block h3 { font-size: 15px; color: #333; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 2px solid #1a3a5c; }
.kc-filter-list { list-style: none; padding: 0; margin: 0; }
.kc-filter-list li { padding: 8px 12px; cursor: pointer; font-size: 13px; color: #555; border-radius: 4px; transition: all .2s; }
.kc-filter-list li:hover { background: #eef3f8; color: #1a3a5c; }
.kc-filter-list li.active { background: #1a3a5c; color: #fff; }
.kc-year-range { display: flex; align-items: center; gap: 6px; margin-bottom: 10px; }
.kc-year-range input { width: 80px; padding: 6px 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 13px; text-align: center; }
.kc-year-range span { color: #999; }
.kc-year-btn { width: 100%; padding: 8px; background: #1a3a5c; color: #fff; border: none; border-radius: 4px; cursor: pointer; font-size: 13px; }
.kc-year-btn:hover { background: #2c5f8a; }

.kc-featured { background: #fff; border-radius: 6px; padding: 18px; margin-bottom: 16px; border-left: 4px solid #f1c40f; }
.kc-featured h3 { font-size: 15px; color: #333; margin-bottom: 12px; }
.kc-featured h3 i { color: #f1c40f; margin-right: 6px; }
.kc-featured-item { display: flex; align-items: center; gap: 12px; padding: 10px 0; border-bottom: 1px solid #f0f0f0; cursor: pointer; }
.kc-featured-item:last-child { border-bottom: none; }
.kc-featured-item:hover { background: #fafafa; }
.kc-featured-type { font-size: 11px; background: #f1c40f; color: #333; padding: 2px 8px; border-radius: 3px; white-space: nowrap; }
.kc-featured-title { flex: 1; font-size: 14px; color: #333; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.kc-featured-meta { font-size: 12px; color: #999; white-space: nowrap; }

.kc-result-header { display: flex; justify-content: space-between; align-items: center; background: #fff; padding: 12px 18px; border-radius: 6px; margin-bottom: 16px; }
.kc-result-count { font-size: 14px; color: #666; }
.kc-sort select { padding: 4px 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 13px; }

.kc-loading { text-align: center; padding: 60px 0; color: #999; font-size: 15px; }
.kc-empty { text-align: center; padding: 80px 0; color: #ccc; }
.kc-empty i { font-size: 48px; margin-bottom: 16px; }
.kc-empty p { font-size: 15px; color: #999; }

.kc-doc-card { display: flex; background: #fff; border-radius: 6px; padding: 18px; margin-bottom: 12px; cursor: pointer; transition: box-shadow .2s; }
.kc-doc-card:hover { box-shadow: 0 2px 12px rgba(0,0,0,.08); }
.kc-doc-type { width: 52px; height: 36px; background: #eef3f8; color: #1a3a5c; font-size: 12px; border-radius: 4px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; margin-right: 16px; font-weight: 600; }
.kc-doc-body { flex: 1; min-width: 0; }
.kc-doc-title { font-size: 16px; color: #1a3a5c; margin-bottom: 4px; }
.kc-doc-authors { font-size: 13px; color: #666; margin-bottom: 4px; }
.kc-doc-meta { font-size: 12px; color: #999; margin-bottom: 6px; }
.kc-doc-abstract { font-size: 13px; color: #777; line-height: 1.6; margin-bottom: 6px; }
.kc-doc-tags { display: flex; flex-wrap: wrap; gap: 6px; }
.kc-tag { font-size: 11px; background: #eef3f8; color: #555; padding: 2px 10px; border-radius: 10px; }

.kc-pagination { display: flex; justify-content: center; gap: 6px; margin-top: 24px; }
.kc-pagination button { width: 36px; height: 36px; border: 1px solid #ddd; background: #fff; border-radius: 4px; cursor: pointer; color: #555; font-size: 13px; }
.kc-pagination button:hover:not(:disabled) { border-color: #1a3a5c; color: #1a3a5c; }
.kc-pagination button.active { background: #1a3a5c; color: #fff; border-color: #1a3a5c; }
.kc-pagination button:disabled { opacity: .4; cursor: default; }
</style>
