<template>
  <Header></Header>
  <div class="Search">
    <!-- 搜索区域 -->
    <div class="search-banner">
      <div class="container">
        <div class="mb-nav">
          <p>
            当前位置： <router-link to="/">首页</router-link> >
            <span>数据库检索</span>
          </p>
        </div>

        <div class="search-header">
          <h1 class="search-title">冶金数据库智能检索</h1>
          <p class="search-subtitle">快速查找540,000+种材料数据与工艺参数</p>
        </div>

        <!-- 搜索框 -->
        <div class="search-container wow animate__animated animate__fadeInUp">
          <div class="search-type-select">
            <select v-model="searchType">
              <option value="all">全文检索</option>
              <option value="material">材料数据</option>
              <option value="process">工艺参数</option>
              <option value="thermo">热力学数据</option>
              <option value="fluid">流体力学数据</option>
            </select>
          </div>

          <div class="search-input-box">
            <input
                type="text"
                v-model="searchQuery"
                placeholder="请输入搜索内容"
                @keyup.enter="performSearch"
            >
            <div class="search-hints">
              <span class="hint-label">热门搜索：</span>
              <span class="hint-item" @click="setSearchHint('碳钢')">碳钢</span>
              <span class="hint-item" @click="setSearchHint('不锈钢')">不锈钢</span>
              <span class="hint-item" @click="setSearchHint('热处理')">热处理</span>
              <span class="hint-item" @click="setSearchHint('CFD模拟')">CFD模拟</span>
            </div>
          </div>

          <div class="search-button" @click="performSearch">
            <img src="../assets/images/icon-search.png" alt="搜索" />
            <span>搜索</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 热门分类 -->
    <div class="categories-section pt70">
      <div class="container">
        <div class="section-title-box wow animate__animated animate__fadeInUp">
          <h2 class="section-title">热门数据分类</h2>
          <p class="section-subtitle">快速访问常用冶金数据资源</p>
        </div>

        <div class="categories-grid">
          <div
              v-for="category in categories"
              :key="category.id"
              class="category-item wow animate__animated animate__fadeInUp"
              :style="{ animationDelay: category.delay }"
              @click="searchByCategory(category.id)"
          >
            <div class="category-img">
              <img :src="category.image" :alt="category.name" />
            </div>
            <div class="category-text">
              <h3>{{ category.name }}</h3>
              <p class="category-count">{{ category.count }} 数据集</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 特色功能 -->
    <div class="features-section bgcolor-two pt70">
      <div class="container">
        <div class="section-title-box wow animate__animated animate__fadeInUp">
          <h2 class="section-title">特色功能与服务</h2>
          <p class="section-subtitle">专业冶金数据资源，支持科研与生产</p>
        </div>

        <div class="features-box1 mt25 wow animate__animated animate__fadeInUp">
          <ul>
            <li v-for="feature in features1" :key="feature.id">
              <div class="feature-card">
                <div class="feature-icon">
                  <img :src="feature.icon" :alt="feature.title" />
                </div>
                <div class="feature-text">
                  <h3 class="feature-title">{{ feature.title }}</h3>
                  <div class="feature-tags">
                    <span v-for="tag in feature.tags" :key="tag">{{ tag }}</span>
                  </div>
                  <div class="feature-button" @click="navigateTo(feature.link)">
                    立即使用
                  </div>
                </div>
              </div>
            </li>
          </ul>
        </div>

        <div class="features-box2 mt100 wow animate__animated animate__fadeInUp">
          <ul>
            <li v-for="feature in features2" :key="feature.id">
              <div class="feature-card2">
                <div class="feature-header">
                  <img :src="feature.icon" :alt="feature.title" />
                  <h3>{{ feature.title }}</h3>
                </div>
                <div class="feature-description">
                  {{ feature.description }}
                </div>
              </div>
            </li>
          </ul>

          <div class="features-list">
            <ul>
              <li v-for="item in featureList" :key="item">
                <p>{{ item }}</p>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>

    <!-- 搜索结果 -->
    <div class="results-section pt70" v-if="showResults">
      <div class="container">
        <div class="results-header">
          <h3 class="results-title">搜索结果（{{ searchResults.length }}条）</h3>
          <div class="results-filter">
            <select v-model="sortBy" class="filter-select">
              <option value="relevance">按相关性排序</option>
              <option value="date">按时间排序</option>
              <option value="popular">按热度排序</option>
            </select>
          </div>
        </div>

        <div class="results-grid">
          <div
              v-for="result in paginatedResults"
              :key="result.id"
              class="result-card"
          >
            <div class="result-badge" :style="{ backgroundColor: result.typeColor }">
              {{ result.type }}
            </div>
            <h4 class="result-title">{{ result.title }}</h4>
            <p class="result-description">{{ result.description }}</p>
            <div class="result-meta">
              <span class="meta-item">
                <i class="far fa-calendar-alt"></i>
                {{ result.date }}
              </span>
              <span class="meta-item">
                <i class="far fa-eye"></i>
                {{ result.views }}
              </span>
              <span class="meta-item">
                <i class="far fa-download"></i>
                {{ result.downloads }}
              </span>
            </div>
            <div class="result-actions">
              <button class="action-btn preview" @click="previewResult(result)">
                <i class="far fa-eye"></i>
                预览
              </button>
              <button class="action-btn download" @click="downloadResult(result)">
                <i class="far fa-download"></i>
                下载
              </button>
            </div>
          </div>
        </div>

        <!-- 分页 -->
        <div class="pagination" v-if="totalPages > 1">
          <button
              class="page-btn prev"
              :disabled="currentPage === 1"
              @click="changePage(currentPage - 1)"
          >
            上一页
          </button>

          <div class="page-numbers">
            <button
                v-for="page in pageRange"
                :key="page"
                :class="['page-number', { active: page === currentPage }]"
                @click="changePage(page)"
            >
              {{ page }}
            </button>
          </div>

          <button
              class="page-btn next"
              :disabled="currentPage === totalPages"
              @click="changePage(currentPage + 1)"
          >
            下一页
          </button>
        </div>
      </div>
    </div>

    <!-- 推荐数据库 -->
    <div class="databases-section pt70 pb150">
      <div class="container">
        <div class="section-title-box wow animate__animated animate__fadeInUp">
          <h2 class="section-title">推荐专业数据库</h2>
          <p class="section-subtitle">访问特定领域的专业数据资源</p>
        </div>

        <div class="databases-grid">
          <div
              v-for="database in databases"
              :key="database.id"
              class="database-card wow animate__animated animate__fadeInUp"
              @click="navigateTo(database.link)"
          >
            <div class="database-icon">
              <i :class="database.icon"></i>
            </div>
            <div class="database-content">
              <h3 class="database-title">{{ database.name }}</h3>
              <p class="database-description">{{ database.description }}</p>
              <div class="database-stats">
                <span class="stat">
                  <i class="fas fa-database"></i>
                  {{ database.stats.datasets }}
                </span>
                <span class="stat">
                  <i class="fas fa-chart-line"></i>
                  {{ database.stats.updated }}
                </span>
              </div>
            </div>
            <div class="database-arrow">
              <i class="fas fa-arrow-right"></i>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  <Footer></Footer>
</template>

<script>
import Header from "@/components/Header.vue";
import Footer from "@/components/Footer.vue";

export default {
  name: "MySearch",
  components: {
    Header,
    Footer,
  },
  data() {
    return {
      searchType: 'all',
      searchQuery: '',
      sortBy: 'relevance',
      showResults: false,
      searchResults: [],
      currentPage: 1,
      itemsPerPage: 12,

      categories: [
        { id: 'ai', name: '人工智能', image: require('../assets/images/s1.png'), count: '2,450+', delay: '0.1s' },
        { id: 'hydrogen', name: '氢能源', image: require('../assets/images/s2.png'), count: '1,200+', delay: '0.2s' },
        { id: 'green', name: '绿色低碳', image: require('../assets/images/s3.png'), count: '3,800+', delay: '0.3s' },
        { id: 'supercomputing', name: '超算', image: require('../assets/images/s4.png'), count: '1,850+', delay: '0.4s' },
        { id: 'database', name: '数据库', image: require('../assets/images/s5.png'), count: '540,000+', delay: '0.5s' },
        { id: 'chemistry', name: '化学方程式', image: require('../assets/images/s6.png'), count: '5,600+', delay: '0.6s' },
        { id: 'tools', name: '工具软件', image: require('../assets/images/s7.png'), count: '350+', delay: '0.7s' },
        { id: 'simulation', name: '计算软件', image: require('../assets/images/s8.png'), count: '420+', delay: '0.8s' },
        { id: 'heat', name: '热传递', image: require('../assets/images/s9.png'), count: '2,800+', delay: '0.9s' },
        { id: 'force', name: '力传递', image: require('../assets/images/s10.png'), count: '3,200+', delay: '1.0s' }
      ],

      features1: [
        {
          id: 1,
          title: '扩展范围',
          icon: require('../assets/images/icon-flex1.png'),
          tags: ['应力应变', '蠕变和断裂', '疲劳数据', '成形性图表'],
          link: '/extensions'
        },
        {
          id: 2,
          title: '材料控制台',
          icon: require('../assets/images/icon-flex2.png'),
          tags: ['材料清单', '导出到CAx', '分享报告', '比较工具'],
          link: '/materials'
        },
        {
          id: 3,
          title: '合规',
          icon: require('../assets/images/icon-flex3.png'),
          tags: ['>300个全球法规', '豁免信息', '物质数据', '更新的规定'],
          link: '/compliance'
        },
        {
          id: 4,
          title: 'AI',
          icon: require('../assets/images/icon-flex4.png'),
          tags: ['材料识别', '专利算法', '专家模块', '光谱仪集成'],
          link: '/ai-tools'
        }
      ],

      features2: [
        {
          id: 1,
          title: '总搜索',
          icon: require('../assets/images/icon-flex5.png'),
          description: '智能检索540,000+种材料数据'
        },
        {
          id: 2,
          title: '数据加',
          icon: require('../assets/images/icon-flex6.png'),
          description: '增强数据分析和处理功能'
        },
        {
          id: 3,
          title: '总搜索',
          icon: require('../assets/images/icon-flex7.png'),
          description: '多维度数据检索与分析'
        },
        {
          id: 4,
          title: '跟踪器',
          icon: require('../assets/images/icon-flex8.png'),
          description: '实时跟踪数据更新与变化'
        }
      ],

      featureList: [
        '> 540,000种材料',
        '材料等效性',
        '80+标准',
        '化学成分',
        '机械性能',
        '物理特性',
        '热处理',
        '金相学',
        '焊接和钎焊',
        '腐蚀和老化',
        '涂层与摩擦学',
        '全球供应商'
      ],

      databases: [
        {
          id: 'thermo',
          name: '冶金热/动力学',
          icon: 'fas fa-fire',
          description: '热力学参数、相图、反应动力学数据',
          link: '/thermodynamics',
          stats: { datasets: '10,000+', updated: '2023-10' }
        },
        {
          id: 'carbon',
          name: '碳排放',
          icon: 'fas fa-leaf',
          description: '碳足迹计算、低碳工艺数据',
          link: '/carbon-emission',
          stats: { datasets: '5,200+', updated: '2023-09' }
        },
        {
          id: 'fluid',
          name: '冶金流体力学',
          icon: 'fas fa-wind',
          description: '流动特性、传热传质、CFD验证数据',
          link: '/fluid-dynamics',
          stats: { datasets: '8,700+', updated: '2023-10' }
        },
        {
          id: 'electro',
          name: '电化学冶金',
          icon: 'fas fa-bolt',
          description: '电化学过程、电解参数、电池材料',
          link: '/electrochemical',
          stats: { datasets: '4,500+', updated: '2023-08' }
        },
        {
          id: 'process',
          name: '工艺数据',
          icon: 'fas fa-industry',
          description: '全流程工艺参数、操作规范、优化方案',
          link: '/process-data',
          stats: { datasets: '15,000+', updated: '2023-10' }
        },
        {
          id: 'tools',
          name: '工具软件',
          icon: 'fas fa-tools',
          description: '冶金计算、模拟分析、数据处理工具',
          link: '/basic-tools',
          stats: { datasets: '350+', updated: '2023-10' }
        }
      ]
    };
  },
  computed: {
    paginatedResults() {
      const start = (this.currentPage - 1) * this.itemsPerPage;
      const end = start + this.itemsPerPage;
      return this.searchResults.slice(start, end);
    },
    totalPages() {
      return Math.ceil(this.searchResults.length / this.itemsPerPage);
    },
    pageRange() {
      const range = [];
      let start = Math.max(1, this.currentPage - 2);
      let end = Math.min(this.totalPages, start + 4);

      if (end - start < 4) {
        start = Math.max(1, end - 4);
      }

      for (let i = start; i <= end; i++) {
        range.push(i);
      }

      return range;
    }
  },
  methods: {
    performSearch() {
      if (!this.searchQuery.trim()) {
        alert('请输入搜索内容');
        return;
      }

      this.showResults = true;

      // 模拟搜索结果
      this.searchResults = [];
      const types = [
        { name: '材料数据', color: '#0046db' },
        { name: '工艺参数', color: '#2066fc' },
        { name: '热力学', color: '#082a78' },
        { name: '流体力学', color: '#0a5c7e' }
      ];

      for (let i = 1; i <= 48; i++) {
        const typeIndex = i % 4;
        this.searchResults.push({
          id: i,
          title: `${this.searchQuery}相关数据 ${i}`,
          description: `这是关于${this.searchQuery}的详细数据描述，包含完整的参数信息、应用案例和实验数据...`,
          type: types[typeIndex].name,
          typeColor: types[typeIndex].color,
          date: `2023-${10 - Math.floor(i/16)}-${(i%30)+1}`,
          views: Math.floor(Math.random() * 1000) + 100,
          downloads: Math.floor(Math.random() * 500) + 50
        });
      }

      this.currentPage = 1;
      window.scrollTo({ top: 600, behavior: 'smooth' });
    },

    setSearchHint(hint) {
      this.searchQuery = hint;
    },

    searchByCategory(categoryId) {
      const category = this.categories.find(c => c.id === categoryId);
      if (category) {
        this.searchQuery = category.name;
        this.performSearch();
      }
    },

    navigateTo(link) {
      this.$router.push(link);
    },

    previewResult(result) {
      alert(`预览数据：${result.title}`);
    },

    downloadResult(result) {
      alert(`开始下载：${result.title}`);
    },

    changePage(page) {
      if (page >= 1 && page <= this.totalPages) {
        this.currentPage = page;
        window.scrollTo({ top: 600, behavior: 'smooth' });
      }
    }
  },
  mounted() {
    // 初始化动画
    if (typeof WOW === 'function') {
      new WOW().init();
    }
  }
};
</script>

<style scoped>
/* 全局样式 */
.Search {
  background-color: #0a192f;
  min-height: 100vh;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

.pt70 {
  padding-top: 70px;
}

.mt25 {
  margin-top: 25px;
}

.mt100 {
  margin-top: 100px;
}

.pb150 {
  padding-bottom: 150px;
}

/* 头部样式 */
.header {
  background: #082a78;
  position: sticky;
}

/* 搜索横幅 */
.search-banner {
  background: linear-gradient(180deg, #082a78 0%, #0a192f 100%);
  padding: 40px 0 80px;
}

.mb-nav {
  margin-bottom: 30px;
}

.mb-nav p {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.7);
}

.mb-nav a {
  color: rgba(255, 255, 255, 0.7);
  text-decoration: none;
}

.mb-nav a:hover {
  color: #2066fc;
}

.mb-nav span {
  color: #2066fc;
}

.search-header {
  text-align: center;
  margin-bottom: 40px;
}

.search-title {
  font-size: 40px;
  color: #ffffff;
  font-weight: bold;
  margin-bottom: 15px;
}

.search-subtitle {
  font-size: 18px;
  color: rgba(255, 255, 255, 0.7);
}

/* 搜索容器 */
.search-container {
  max-width: 900px;
  margin: 0 auto;
  display: flex;
  background-color: #fff;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.2);
}

.search-type-select {
  width: 180px;
  position: relative;
  border-right: 1px solid #eeeeee;
}

.search-type-select select {
  width: 100%;
  height: 70px;
  border: none;
  outline: none;
  background: transparent;
  padding: 0 20px;
  font-size: 16px;
  color: #000000;
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6 9 12 15 18 9'%3e%3c/polyline%3e%3c/svg%3e");
  background-repeat: no-repeat;
  background-position: right 20px center;
  background-size: 16px;
}

.search-input-box {
  flex: 1;
  position: relative;
  padding: 10px 20px;
}

.search-input-box input {
  width: 100%;
  height: 50px;
  border: none;
  outline: none;
  font-size: 18px;
  color: #000000;
  background: transparent;
}

.search-hints {
  position: absolute;
  bottom: -25px;
  left: 20px;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
}

.hint-label {
  margin-right: 10px;
}

.hint-item {
  margin-right: 15px;
  color: #2066fc;
  cursor: pointer;
  transition: color 0.3s;
}

.hint-item:hover {
  color: #0046db;
  text-decoration: underline;
}

.search-button {
  width: 180px;
  height: 70px;
  background-color: #2066fc;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background-color 0.3s;
}

.search-button:hover {
  background-color: #0046db;
}

.search-button img {
  width: 20px;
  height: 20px;
  margin-right: 10px;
}

.search-button span {
  color: #ffffff;
  font-size: 18px;
  font-weight: 500;
}

/* 分类区域 */
.categories-section {
  padding-bottom: 70px;
}

.section-title-box {
  text-align: center;
  margin-bottom: 40px;
}

.section-title {
  font-size: 32px;
  color: #ffffff;
  font-weight: bold;
  margin-bottom: 15px;
}

.section-subtitle {
  font-size: 18px;
  color: rgba(255, 255, 255, 0.7);
}

.categories-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 30px;
}

.category-item {
  text-align: center;
  cursor: pointer;
  transition: transform 0.3s;
}

.category-item:hover {
  transform: translateY(-10px);
}

.category-img {
  height: 150px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 15px;
}

.category-img img {
  max-height: 100%;
}

.category-text h3 {
  font-size: 18px;
  color: #ffffff;
  margin-bottom: 5px;
}

.category-count {
  font-size: 14px;
  color: #2066fc;
}

/* 特色功能区域 */
.bgcolor-two {
  background: linear-gradient(180deg, #082a78 0%, #0a192f 100%);
}

.features-box1 ul {
  display: flex;
  flex-wrap: wrap;
  gap: 30px;
  list-style: none;
}

.features-box1 ul li {
  flex: 1;
  min-width: 250px;
}

.feature-card {
  background-color: rgba(255, 255, 255, 0.05);
  border-radius: 10px;
  padding: 30px;
  height: 100%;
  border: 1px solid rgba(255, 255, 255, 0.1);
  transition: all 0.3s;
}

.feature-card:hover {
  border-color: #2066fc;
  transform: translateY(-5px);
  box-shadow: 0 10px 30px rgba(32, 102, 252, 0.2);
}

.feature-icon {
  margin-bottom: 20px;
}

.feature-icon img {
  width: 60px;
  height: 60px;
}

.feature-title {
  font-size: 20px;
  color: #ffffff;
  margin-bottom: 15px;
  font-weight: bold;
}

.feature-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 20px;
}

.feature-tags span {
  display: inline-block;
  padding: 4px 12px;
  background-color: rgba(32, 102, 252, 0.1);
  color: #2066fc;
  font-size: 14px;
  border-radius: 4px;
}

.feature-button {
  display: inline-block;
  padding: 10px 20px;
  background-color: #0046db;
  color: #ffffff;
  border-radius: 5px;
  font-size: 16px;
  cursor: pointer;
  transition: background-color 0.3s;
  text-align: center;
}

.feature-button:hover {
  background-color: #2066fc;
}

/* 第二个特色功能区域 */
.features-box2 {
  display: flex;
  gap: 50px;
  align-items: flex-start;
}

.features-box2 ul {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 30px;
  list-style: none;
  flex: 2;
}

.feature-card2 {
  background-color: rgba(255, 255, 255, 0.05);
  border-radius: 10px;
  padding: 25px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  transition: all 0.3s;
}

.feature-card2:hover {
  border-color: #2066fc;
}

.feature-header {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 15px;
}

.feature-header img {
  width: 40px;
  height: 40px;
}

.feature-header h3 {
  font-size: 18px;
  color: #ffffff;
  font-weight: bold;
}

.feature-description {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
  line-height: 1.6;
}

.features-list {
  flex: 1;
  background-color: rgba(255, 255, 255, 0.05);
  border-radius: 10px;
  padding: 30px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.features-list ul {
  list-style: none;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
}

.features-list li {
  padding: 8px 0;
}

.features-list p {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.7);
  position: relative;
  padding-left: 20px;
}

.features-list p::before {
  content: ">";
  position: absolute;
  left: 0;
  color: #2066fc;
}

/* 搜索结果区域 */
.results-section {
  background-color: #0a192f;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.results-title {
  font-size: 24px;
  color: #ffffff;
  font-weight: bold;
}

.filter-select {
  padding: 10px 20px;
  background-color: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: #ffffff;
  border-radius: 5px;
  font-size: 16px;
  cursor: pointer;
  outline: none;
}

.filter-select:focus {
  border-color: #2066fc;
}

.results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 25px;
  margin-bottom: 40px;
}

.result-card {
  background-color: rgba(255, 255, 255, 0.05);
  border-radius: 10px;
  padding: 25px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  transition: all 0.3s;
}

.result-card:hover {
  border-color: #2066fc;
  transform: translateY(-3px);
}

.result-badge {
  display: inline-block;
  padding: 5px 15px;
  background-color: #0046db;
  color: #ffffff;
  font-size: 12px;
  border-radius: 15px;
  margin-bottom: 15px;
}

.result-title {
  font-size: 18px;
  color: #ffffff;
  margin-bottom: 10px;
  font-weight: bold;
  line-height: 1.4;
}

.result-description {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
  line-height: 1.6;
  margin-bottom: 15px;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.result-meta {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 5px;
}

.result-actions {
  display: flex;
  gap: 10px;
}

.action-btn {
  flex: 1;
  padding: 10px;
  border-radius: 5px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background-color: transparent;
  color: #ffffff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.3s;
  font-size: 14px;
}

.action-btn.preview:hover {
  background-color: rgba(32, 102, 252, 0.2);
  border-color: #2066fc;
  color: #2066fc;
}

.action-btn.download:hover {
  background-color: rgba(0, 70, 219, 0.2);
  border-color: #0046db;
  color: #0046db;
}

/* 分页 */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  margin-top: 40px;
}

.page-btn {
  padding: 10px 20px;
  background-color: transparent;
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: #ffffff;
  border-radius: 5px;
  cursor: pointer;
  transition: all 0.3s;
  font-size: 16px;
}

.page-btn:hover:not(:disabled) {
  background-color: rgba(32, 102, 252, 0.2);
  border-color: #2066fc;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-numbers {
  display: flex;
  gap: 5px;
}

.page-number {
  width: 40px;
  height: 40px;
  border-radius: 5px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background-color: transparent;
  color: #ffffff;
  cursor: pointer;
  transition: all 0.3s;
}

.page-number:hover:not(.active) {
  background-color: rgba(255, 255, 255, 0.1);
}

.page-number.active {
  background-color: #0046db;
  border-color: #0046db;
  color: #ffffff;
}

/* 数据库区域 */
.databases-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 30px;
}

.database-card {
  background-color: rgba(255, 255, 255, 0.05);
  border-radius: 10px;
  padding: 25px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  gap: 20px;
  cursor: pointer;
  transition: all 0.3s;
}

.database-card:hover {
  border-color: #2066fc;
  transform: translateY(-5px);
}

.database-icon {
  width: 60px;
  height: 60px;
  background: linear-gradient(135deg, #0046db, #2066fc);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: #ffffff;
}

.database-content {
  flex: 1;
}

.database-title {
  font-size: 18px;
  color: #ffffff;
  margin-bottom: 8px;
  font-weight: bold;
}

.database-description {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 12px;
  line-height: 1.4;
}

.database-stats {
  display: flex;
  gap: 15px;
  font-size: 12px;
  color: #2066fc;
}

.stat {
  display: flex;
  align-items: center;
  gap: 5px;
}

.database-arrow {
  color: rgba(255, 255, 255, 0.5);
  font-size: 18px;
  transition: all 0.3s;
}

.database-card:hover .database-arrow {
  color: #2066fc;
  transform: translateX(5px);
}

/* 响应式设计 */
@media (max-width: 1600px) {
  .search-title {
    font-size: 32px;
  }

  .section-title {
    font-size: 28px;
  }

  .categories-grid {
    grid-template-columns: repeat(4, 1fr);
  }

  .category-img {
    height: 130px;
  }
}

@media (max-width: 1200px) {
  .features-box2 {
    flex-direction: column;
  }

  .features-list ul {
    grid-template-columns: repeat(3, 1fr);
  }

  .categories-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 1000px) {
  .search-container {
    flex-direction: column;
    max-width: 500px;
  }

  .search-type-select {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid #eeeeee;
  }

  .search-button {
    width: 100%;
    height: 60px;
  }

  .categories-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 20px;
  }

  .features-box1 ul {
    grid-template-columns: repeat(2, 1fr);
  }

  .results-grid {
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  }

  .databases-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .search-title {
    font-size: 24px;
  }

  .search-subtitle {
    font-size: 16px;
  }

  .section-title {
    font-size: 22px;
  }

  .section-subtitle {
    font-size: 16px;
  }

  .categories-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 15px;
  }

  .category-img {
    height: 100px;
  }

  .features-box1 ul {
    grid-template-columns: 1fr;
  }

  .features-box2 ul {
    grid-template-columns: 1fr;
  }

  .features-list ul {
    grid-template-columns: repeat(2, 1fr);
  }

  .results-grid {
    grid-template-columns: 1fr;
  }

  .pagination {
    flex-direction: column;
    gap: 15px;
  }
}

@media (max-width: 480px) {
  .search-hints {
    display: none;
  }

  .categories-grid {
    grid-template-columns: 1fr;
  }

  .features-list ul {
    grid-template-columns: 1fr;
  }
}
</style>