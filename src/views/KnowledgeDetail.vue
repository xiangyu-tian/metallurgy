<template>
  <div class="knowledge-detail">
    <Header></Header>

    <div class="mb-nav">
      <div class="container">
        <p>
          当前位置：<router-link to="/">首页</router-link> >
          <router-link to="/knowledge">专业文献中心</router-link> >
          <span>{{ doc.title }}</span>
        </p>
      </div>
    </div>

    <section v-if="loading" class="kd-loading">
      <i class="fas fa-spinner fa-spin"></i> 加载中…
    </section>

    <section v-else-if="error" class="kd-error">
      <i class="fas fa-exclamation-circle"></i>
      <p>{{ error }}</p>
      <router-link to="/knowledge" class="kd-back-link">返回文献中心</router-link>
    </section>

    <section v-else class="kd-main">
      <div class="container">
        <!-- 标题区 -->
        <div class="kd-header">
          <span class="kd-type-badge">{{ typeLabel(doc.document_type) }}</span>
          <h1 class="kd-title">{{ doc.title }}</h1>
          <p v-if="doc.title_en" class="kd-title-en">{{ doc.title_en }}</p>
          <div class="kd-authors">
            <span v-for="(a, i) in doc.authors" :key="a.author_id" class="kd-author">
              {{ a.author_name }}<sup v-if="a.is_corresponding">✉</sup>
              <span v-if="i < doc.authors.length - 1">, </span>
            </span>
          </div>
          <p v-if="doc.authors.length && doc.authors[0].institution" class="kd-institution">
            {{ doc.authors[0].institution }}
          </p>
        </div>

        <!-- 元数据卡片 -->
        <div class="kd-meta-card">
          <div class="kd-meta-item" v-if="doc.journal_name">
            <span class="kd-meta-label">期刊/会议</span>
            <span class="kd-meta-value">{{ doc.journal_name }}{{ doc.conference_name ? ' / ' + doc.conference_name : '' }}</span>
          </div>
          <div class="kd-meta-item" v-if="doc.publication_year">
            <span class="kd-meta-label">出版年份</span>
            <span class="kd-meta-value">{{ doc.publication_year }}</span>
          </div>
          <div class="kd-meta-item" v-if="doc.volume || doc.issue || doc.pages">
            <span class="kd-meta-label">卷/期/页码</span>
            <span class="kd-meta-value">{{ doc.volume || '' }}{{ doc.issue ? '(' + doc.issue + ')' : '' }}{{ doc.pages ? ', ' + doc.pages : '' }}</span>
          </div>
          <div class="kd-meta-item" v-if="doc.doi">
            <span class="kd-meta-label">DOI</span>
            <span class="kd-meta-value">
              <a :href="'https://doi.org/' + doc.doi" target="_blank">{{ doc.doi }}</a>
            </span>
          </div>
          <div class="kd-meta-item" v-if="doc.domains && doc.domains.length">
            <span class="kd-meta-label">研究领域</span>
            <span class="kd-meta-value">
              <span class="kd-domain-tag" v-for="dm in doc.domains" :key="dm.domain_code">
                <router-link :to="'/knowledge?domain=' + dm.domain_code">{{ dm.domain_name }}</router-link>
              </span>
            </span>
          </div>
          <div class="kd-meta-item" v-if="doc.language">
            <span class="kd-meta-label">语种</span>
            <span class="kd-meta-value">{{ doc.language === 'en' ? 'English' : '中文' }}</span>
          </div>
          <div class="kd-meta-item" v-if="doc.source_url">
            <span class="kd-meta-label">原始来源</span>
            <span class="kd-meta-value">
              <a :href="doc.source_url" target="_blank" rel="noopener noreferrer">
                <i class="fas fa-external-link-alt"></i> 查看原文
              </a>
            </span>
          </div>
          <div class="kd-meta-item" v-if="doc.pdf_url">
            <span class="kd-meta-label">PDF 全文</span>
            <span class="kd-meta-value">
              <a :href="doc.pdf_url" target="_blank" rel="noopener noreferrer">
                <i class="fas fa-file-pdf"></i> 打开 PDF
              </a>
            </span>
          </div>
          <div class="kd-meta-item" v-if="doc.discovery_source === 'google_scholar'">
            <span class="kd-meta-label">学术影响</span>
            <span class="kd-meta-value">
              <a v-if="doc.scholar_url" :href="doc.scholar_url" target="_blank" rel="noopener noreferrer">
                Google Scholar 引用 {{ doc.scholar_citation_count || 0 }} 次
              </a>
              <span v-else>Google Scholar 引用 {{ doc.scholar_citation_count || 0 }} 次</span>
            </span>
          </div>
        </div>

        <!-- 摘要 -->
        <div class="kd-section" v-if="doc.abstract">
          <h3>摘要</h3>
          <div class="kd-abstract" :class="{ 'kd-abstract-collapsed': abstractCollapsed }">
            {{ doc.abstract }}{{ abstractTruncated ? '…' : '' }}
          </div>
          <button v-if="abstractLong" class="kd-abstract-toggle" @click="abstractCollapsed = !abstractCollapsed">
            {{ abstractCollapsed ? '展开全部' : '收起' }}
          </button>
        </div>

        <!-- 关键词 -->
        <div class="kd-section" v-if="doc.keywords && doc.keywords.length">
          <h3>关键词</h3>
          <div class="kd-keywords">
            <span class="kd-keyword" v-for="kw in doc.keywords" :key="kw">{{ kw }}</span>
          </div>
        </div>

        <!-- 引用格式 -->
        <div class="kd-section" v-if="doc.citation_text">
          <h3>引用格式</h3>
          <div class="kd-citation">{{ doc.citation_text }}</div>
        </div>

        <!-- 相关文献 -->
        <div class="kd-section" v-if="doc.related && doc.related.length">
          <h3>相关文献</h3>
          <div class="kd-related-list">
            <div
              class="kd-related-item"
              v-for="r in doc.related"
              :key="r.document_code"
              @click="$router.push('/knowledge/documents/' + r.document_code)"
            >
              <span class="kd-related-title">{{ r.title }}</span>
              <span class="kd-related-year">{{ r.publication_year }}</span>
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
  name: 'KnowledgeDetail',
  components: { Header, Footer },
  data() {
    return {
      doc: {},
      loading: true,
      error: '',
      abstractCollapsed: true,
      abstractLong: false,
      abstractTruncated: false,
    };
  },
  methods: {
    typeLabel(type) {
      const map = { paper: '论文', standard: '标准', patent: '专利', report: '报告', book: '图书', manual: '手册' };
      return map[type] || type;
    },
    async fetchDetail() {
      const code = this.$route.params.documentCode;
      if (!code) {
        this.error = '缺少文献编号';
        this.loading = false;
        return;
      }
      try {
        const res = await request.get(`/literature/documents/${code}`);
        this.doc = res.data || {};
        this.abstractLong = (this.doc.abstract || '').length > 300;
        const a = this.doc.abstract || '';
        this.abstractTruncated = a.length > 0 && !/[。.!！?？\n]$/.test(a.trim());
      } catch (e) {
        this.error = e.message || '文献不存在或未发布';
      }
      this.loading = false;
    },
  },
  mounted() {
    this.fetchDetail();
  },
  watch: {
    '$route.params.documentCode'() {
      this.loading = true;
      this.error = '';
      this.doc = {};
      this.abstractCollapsed = true;
      this.abstractLong = false;
      this.abstractTruncated = false;
      this.fetchDetail();
    },
  },
};
</script>

<style scoped>
.kd-loading, .kd-error { text-align: center; padding: 100px 0; }
.kd-error i { font-size: 48px; color: #e74c3c; margin-bottom: 16px; }
.kd-error p { font-size: 15px; color: #999; }
.kd-back-link { display: inline-block; margin-top: 16px; color: #1a3a5c; }

.kd-main { padding: 30px 0 60px; background: #f5f7fa; }

.kd-header { background: #fff; border-radius: 8px; padding: 32px; margin-bottom: 20px; }
.kd-type-badge { display: inline-block; background: #1a3a5c; color: #fff; font-size: 12px; padding: 3px 12px; border-radius: 3px; margin-bottom: 12px; }
.kd-title { font-size: 24px; color: #222; line-height: 1.4; margin-bottom: 8px; }
.kd-title-en { font-size: 15px; color: #999; margin-bottom: 12px; }
.kd-authors { font-size: 15px; color: #444; margin-bottom: 4px; }
.kd-author sup { color: #e74c3c; font-size: 12px; }
.kd-institution { font-size: 13px; color: #888; }

.kd-meta-card { background: #fff; border-radius: 8px; padding: 20px 24px; margin-bottom: 20px; display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.kd-meta-item { display: flex; gap: 8px; font-size: 14px; }
.kd-meta-label { color: #999; white-space: nowrap; min-width: 72px; }
.kd-meta-value { color: #333; word-break: break-all; }
.kd-meta-value a { color: #1a3a5c; text-decoration: none; }
.kd-meta-value a:hover { text-decoration: underline; }
.kd-domain-tag { display: inline-block; margin-right: 8px; }
.kd-domain-tag a { color: #1a3a5c; background: #eef3f8; padding: 2px 10px; border-radius: 10px; font-size: 12px; text-decoration: none; }
.kd-domain-tag a:hover { background: #dce6ef; }

.kd-section { background: #fff; border-radius: 8px; padding: 24px 28px; margin-bottom: 20px; }
.kd-section h3 { font-size: 17px; color: #1a3a5c; margin-bottom: 14px; padding-bottom: 8px; border-bottom: 2px solid #1a3a5c; }
.kd-abstract { font-size: 14px; color: #444; line-height: 1.8; }
.kd-abstract-collapsed { max-height: 150px; overflow: hidden; position: relative; }
.kd-abstract-collapsed::after {
  content: ''; position: absolute; bottom: 0; left: 0; right: 0;
  height: 48px;
  background: linear-gradient(transparent, #fff);
  pointer-events: none;
}
.kd-abstract-toggle {
  display: inline-block; margin-top: 8px; padding: 4px 16px;
  font-size: 13px; color: #1a3a5c; background: #eef3f8;
  border: none; border-radius: 4px; cursor: pointer;
}
.kd-abstract-toggle:hover { background: #dce6ef; }
.kd-ellipsis { color: #999; font-size: 14px; }
.kd-keywords { display: flex; flex-wrap: wrap; gap: 8px; }
.kd-keyword { background: #eef3f8; color: #1a3a5c; padding: 4px 14px; border-radius: 14px; font-size: 13px; }
.kd-citation { font-size: 13px; color: #666; line-height: 1.6; padding: 12px; background: #f9f9f9; border-radius: 4px; border-left: 3px solid #1a3a5c; }

.kd-related-item { padding: 12px 0; border-bottom: 1px solid #f0f0f0; cursor: pointer; display: flex; justify-content: space-between; align-items: center; }
.kd-related-item:last-child { border-bottom: none; }
.kd-related-item:hover { background: #fafafa; }
.kd-related-title { font-size: 14px; color: #1a3a5c; }
.kd-related-year { font-size: 12px; color: #999; white-space: nowrap; margin-left: 12px; }
</style>
