<template>
  <section class="lit-section">
    <div class="container">
      <div class="section-header">
        <h2>{{ domainName }} · 相关文献</h2>
        <div class="section-line"></div>
        <p class="section-desc">本领域相关论文、标准、专利与报告</p>
      </div>

      <div v-if="loading" class="lit-loading">
        <i class="fas fa-spinner fa-spin"></i> 加载文献数据…
      </div>

      <div v-else-if="error" class="lit-error">
        <p>{{ error }}</p>
      </div>

      <div v-else-if="items.length === 0" class="lit-empty">
        <p>暂未收录本领域文献</p>
      </div>

      <div v-else class="lit-grid">
        <div
          class="lit-card"
          v-for="doc in items"
          :key="doc.document_code"
          @click="$router.push('/knowledge/documents/' + doc.document_code)"
        >
          <span class="lit-type-badge">{{ typeLabel(doc.document_type) }}</span>
          <h4 class="lit-card-title">{{ doc.title }}</h4>
          <p class="lit-card-meta">
            <span v-if="doc.journal_name">{{ doc.journal_name }}</span>
            <span v-if="doc.publication_year">，{{ doc.publication_year }}</span>
          </p>
          <p v-if="doc.abstract" class="lit-card-abstract">{{ doc.abstract }}…</p>
        </div>
      </div>

      <div v-if="items.length > 0" class="lit-more">
        <router-link :to="'/knowledge?domain=' + domainCode" class="lit-more-link">
          查看全部 <i class="fas fa-arrow-right"></i>
        </router-link>
      </div>
    </div>
  </section>
</template>

<script>
import request from '@/utils/request.js';

export default {
  name: 'LiteratureSection',
  props: {
    domainCode: { type: String, required: true },
    domainName: { type: String, default: '' },
  },
  data() {
    return {
      items: [],
      loading: true,
      error: '',
    };
  },
  methods: {
    typeLabel(type) {
      const map = { paper: '论文', standard: '标准', patent: '专利', report: '报告', book: '图书', manual: '手册' };
      return map[type] || type;
    },
    async fetchData() {
      this.loading = true;
      this.error = '';
      try {
        const res = await request.get(`/literature/domains/${this.domainCode}/documents`, {
          params: { limit: 6 },
        });
        this.items = res.data.items || [];
      } catch (e) {
        this.error = '文献数据加载失败';
        console.error(e);
      }
      this.loading = false;
    },
  },
  mounted() {
    this.fetchData();
  },
  watch: {
    domainCode() { this.fetchData(); },
  },
};
</script>

<style scoped>
.lit-section {
  padding: 60px 0;
  background: #f5f7fa;
}
.lit-loading, .lit-error, .lit-empty {
  text-align: center;
  padding: 40px 0;
  color: #999;
  font-size: 14px;
}
.lit-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}
.lit-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  cursor: pointer;
  transition: box-shadow .2s, transform .2s;
}
.lit-card:hover {
  box-shadow: 0 4px 16px rgba(0,0,0,.08);
  transform: translateY(-2px);
}
.lit-type-badge {
  display: inline-block;
  font-size: 11px;
  background: #eef3f8;
  color: #1a3a5c;
  padding: 2px 10px;
  border-radius: 3px;
  margin-bottom: 10px;
}
.lit-card-title {
  font-size: 15px;
  color: #1a3a5c;
  line-height: 1.5;
  margin-bottom: 6px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.lit-card-meta {
  font-size: 12px;
  color: #999;
  margin-bottom: 8px;
}
.lit-card-abstract {
  font-size: 13px;
  color: #777;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.lit-more {
  text-align: center;
  margin-top: 30px;
}
.lit-more-link {
  display: inline-block;
  padding: 10px 28px;
  background: #1a3a5c;
  color: #fff;
  border-radius: 4px;
  text-decoration: none;
  font-size: 14px;
}
.lit-more-link:hover {
  background: #2c5f8a;
}

@media (max-width: 992px) {
  .lit-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 576px) {
  .lit-grid { grid-template-columns: 1fr; }
}
</style>
