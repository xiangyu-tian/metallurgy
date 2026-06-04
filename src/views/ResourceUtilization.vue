<template>
  <Header></Header>
  <div class="resource-utilization">
    <!-- 面包屑导航 -->
    <div class="mb-nav">
      <div class="container">
        <p>
          当前位置： <router-link to="/">首页</router-link> >
          <span>冶金资源利用</span>
        </p>
      </div>
    </div>

    <!-- 英雄区域 -->
    <section class="hero-section">
      <div class="hero-overlay"></div>
      <div class="container hero-content">
        <h1 class="hero-title">冶金资源综合利用</h1>
        <p class="hero-subtitle">
          推动冶金行业绿色转型，实现资源高效利用与循环经济发展
        </p>
        <div class="hero-stats">
          <div class="hero-stat-item">
            <span class="hero-stat-value">95%</span>
            <span class="hero-stat-label">固废综合利用率</span>
          </div>
          <div class="hero-stat-item">
            <span class="hero-stat-value">2.8亿</span>
            <span class="hero-stat-label">吨/年资源化处理量</span>
          </div>
          <div class="hero-stat-item">
            <span class="hero-stat-value">85%</span>
            <span class="hero-stat-label">二次资源回收率</span>
          </div>
          <div class="hero-stat-item">
            <span class="hero-stat-value">120+</span>
            <span class="hero-stat-label">项循环经济示范工程</span>
          </div>
        </div>
      </div>
    </section>

    <!-- 概述区域 -->
    <section class="overview-section">
      <div class="container">
        <div class="section-header">
          <h2><i class="fas fa-globe-asia"></i> 资源利用概况</h2>
          <p>冶金工业是我国国民经济的重要基础产业，资源综合利用水平直接关系到行业的可持续发展</p>
        </div>
        <div class="overview-grid">
          <div class="overview-card">
            <div class="overview-icon">
              <i class="fas fa-chart-pie"></i>
            </div>
            <div class="overview-content">
              <h3>资源消耗结构</h3>
              <p>冶金工业年消耗铁矿石约13.8亿吨、废钢约2.2亿吨、各种辅料约3.5亿吨，资源消耗量占全国工业总消耗的25%以上。</p>
            </div>
          </div>
          <div class="overview-card">
            <div class="overview-icon">
              <i class="fas fa-recycle"></i>
            </div>
            <div class="overview-content">
              <h3>循环利用现状</h3>
              <p>钢铁行业废钢利用率达到22.3%，冶金渣综合利用率超过85%，含铁尘泥回收利用率达90%以上，水资源循环利用率达97%。</p>
            </div>
          </div>
          <div class="overview-card">
            <div class="overview-icon">
              <i class="fas fa-chart-line"></i>
            </div>
            <div class="overview-content">
              <h3>发展趋势</h3>
              <p>"双碳"目标驱动下，冶金资源利用正向精细化、高值化、循环化方向发展，预计2030年固废综合利用率将突破98%。</p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 关键指标行 -->
    <section class="metrics-section">
      <div class="container">
        <div class="metrics-grid">
          <div class="metric-card">
            <div class="metric-icon">
              <i class="fas fa-mountain"></i>
            </div>
            <div class="metric-data">
              <div class="metric-value">1.2亿</div>
              <div class="metric-label">钢渣年产生量（吨）</div>
              <div class="metric-trend up">综合利用率 85%</div>
            </div>
          </div>
          <div class="metric-card">
            <div class="metric-icon">
              <i class="fas fa-dust"></i>
            </div>
            <div class="metric-data">
              <div class="metric-value">6,800万</div>
              <div class="metric-label">高炉渣年产生量（吨）</div>
              <div class="metric-trend up">利用率 95%</div>
            </div>
          </div>
          <div class="metric-card">
            <div class="metric-icon">
              <i class="fas fa-flask"></i>
            </div>
            <div class="metric-data">
              <div class="metric-value">1,200万</div>
              <div class="metric-label">含铁尘泥年产生量（吨）</div>
              <div class="metric-trend up">回收率 90%</div>
            </div>
          </div>
          <div class="metric-card">
            <div class="metric-icon">
              <i class="fas fa-water"></i>
            </div>
            <div class="metric-data">
              <div class="metric-value">97%</div>
              <div class="metric-label">水资源循环利用率</div>
              <div class="metric-trend up">年节水 4.5亿吨</div>
            </div>
          </div>
          <div class="metric-card">
            <div class="metric-icon">
              <i class="fas fa-bolt"></i>
            </div>
            <div class="metric-data">
              <div class="metric-value">2,800万</div>
              <div class="metric-label">余热回收发电量（万千瓦时）</div>
              <div class="metric-trend up">年减排 CO₂ 560万吨</div>
            </div>
          </div>
          <div class="metric-card">
            <div class="metric-icon">
              <i class="fas fa-gem"></i>
            </div>
            <div class="metric-data">
              <div class="metric-value">15万</div>
              <div class="metric-label">稀散金属年回收量（吨）</div>
              <div class="metric-trend up">价值超 200亿元</div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 重点资源利用领域 -->
    <section class="resource-areas-section">
      <div class="container">
        <div class="section-header">
          <h2><i class="fas fa-cubes"></i> 重点资源利用领域</h2>
          <p>围绕冶金资源综合利用的关键环节，推动四大重点领域的技术创新与产业升级</p>
        </div>

        <div class="areas-grid">
          <!-- 领域一：二次资源循环利用 -->
          <div class="area-card">
            <div class="card-image-area secondary-resources">
              <div class="card-icon-wrapper">
                <i class="fas fa-sync-alt"></i>
              </div>
              <div class="card-badge">二次资源</div>
            </div>
            <div class="card-body">
              <h3 class="card-title">二次资源循环利用</h3>
              <p class="card-desc">
                通过先进的分选、提纯和再生技术，将废钢、废有色金属、废合金等二次资源重新转化为高品质冶金原料，显著降低原生矿产消耗和能源消耗。
              </p>
              <div class="card-data">
                <div class="card-data-item">
                  <span class="data-label">废钢回收量</span>
                  <span class="data-value">2.2亿吨/年</span>
                </div>
                <div class="card-data-item">
                  <span class="data-label">再生铜产量</span>
                  <span class="data-value">320万吨/年</span>
                </div>
                <div class="card-data-item">
                  <span class="data-label">再生铝产量</span>
                  <span class="data-value">865万吨/年</span>
                </div>
              </div>
              <div class="card-tags">
                <span class="tag">废钢回收</span>
                <span class="tag">再生金属</span>
                <span class="tag">资源再生</span>
              </div>
            </div>
          </div>

          <!-- 领域二：固废资源化利用 -->
          <div class="area-card">
            <div class="card-image-area solid-waste">
              <div class="card-icon-wrapper">
                <i class="fas fa-dumpster"></i>
              </div>
              <div class="card-badge">固废利用</div>
            </div>
            <div class="card-body">
              <h3 class="card-title">冶金固废资源化利用</h3>
              <p class="card-desc">
                针对钢渣、高炉渣、赤泥、尾矿等大宗冶金固体废弃物，开发高附加值利用技术，将固废转化为建筑材料、化工原料、土壤改良剂等产品。
              </p>
              <div class="card-data">
                <div class="card-data-item">
                  <span class="data-label">钢渣利用率</span>
                  <span class="data-value">85%</span>
                </div>
                <div class="card-data-item">
                  <span class="data-label">矿渣微粉产量</span>
                  <span class="data-value">2.5亿吨/年</span>
                </div>
                <div class="card-data-item">
                  <span class="data-label">赤泥利用量</span>
                  <span class="data-value">800万吨/年</span>
                </div>
              </div>
              <div class="card-tags">
                <span class="tag">钢渣利用</span>
                <span class="tag">矿渣微粉</span>
                <span class="tag">赤泥处理</span>
              </div>
            </div>
          </div>

          <!-- 领域三：稀散金属回收 -->
          <div class="area-card">
            <div class="card-image-area rare-metals">
              <div class="card-icon-wrapper">
                <i class="fas fa-atom"></i>
              </div>
              <div class="card-badge">稀散金属</div>
            </div>
            <div class="card-body">
              <h3 class="card-title">稀散及贵金属回收</h3>
              <p class="card-desc">
                从冶金副产物、废催化剂、电子废弃物中高效回收镓、铟、锗、铂族金属等稀散和贵金属，服务国家战略新兴产业对关键金属材料的需求。
              </p>
              <div class="card-data">
                <div class="card-data-item">
                  <span class="data-label">镓回收量</span>
                  <span class="data-value">420吨/年</span>
                </div>
                <div class="card-data-item">
                  <span class="data-label">铟回收量</span>
                  <span class="data-value">580吨/年</span>
                </div>
                <div class="card-data-item">
                  <span class="data-label">铂族金属回收</span>
                  <span class="data-value">85吨/年</span>
                </div>
              </div>
              <div class="card-tags">
                <span class="tag">稀散金属</span>
                <span class="tag">贵金属回收</span>
                <span class="tag">城市矿山</span>
              </div>
            </div>
          </div>

          <!-- 领域四：循环经济 -->
          <div class="area-card">
            <div class="card-image-area circular-economy">
              <div class="card-icon-wrapper">
                <i class="fas fa-leaf"></i>
              </div>
              <div class="card-badge">循环经济</div>
            </div>
            <div class="card-body">
              <h3 class="card-title">循环经济与生态链接</h3>
              <p class="card-desc">
                构建"资源-产品-再生资源"的闭环产业链，推动冶金企业与建材、化工、电力等行业的跨产业协同，实现物质流、能量流的最优配置。
              </p>
              <div class="card-data">
                <div class="card-data-item">
                  <span class="data-label">循环经济园区</span>
                  <span class="data-value">45个</span>
                </div>
                <div class="card-data-item">
                  <span class="data-label">协同处置能力</span>
                  <span class="data-value">2,000万吨/年</span>
                </div>
                <div class="card-data-item">
                  <span class="data-label">产业链延伸</span>
                  <span class="data-value">120余条</span>
                </div>
              </div>
              <div class="card-tags">
                <span class="tag">生态链接</span>
                <span class="tag">产业协同</span>
                <span class="tag">绿色工厂</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 技术路线图 -->
    <section class="roadmap-section">
      <div class="container">
        <div class="section-header">
          <h2><i class="fas fa-road"></i> 资源综合利用技术路线</h2>
          <p>从传统末端治理向全过程资源化利用转变，构建冶金资源循环利用技术体系</p>
        </div>
        <div class="roadmap-grid">
          <div class="roadmap-step">
            <div class="step-number">01</div>
            <div class="step-content">
              <h4>源头减量</h4>
              <p>优化原料配比与工艺参数，减少固废产生量</p>
            </div>
          </div>
          <div class="roadmap-arrow">
            <i class="fas fa-chevron-right"></i>
          </div>
          <div class="roadmap-step">
            <div class="step-number">02</div>
            <div class="step-content">
              <h4>过程调控</h4>
              <p>在线监测与智能调控，提高资源转化效率</p>
            </div>
          </div>
          <div class="roadmap-arrow">
            <i class="fas fa-chevron-right"></i>
          </div>
          <div class="roadmap-step">
            <div class="step-number">03</div>
            <div class="step-content">
              <h4>末端利用</h4>
              <p>多途径资源化利用，实现固废近零排放</p>
            </div>
          </div>
          <div class="roadmap-arrow">
            <i class="fas fa-chevron-right"></i>
          </div>
          <div class="roadmap-step">
            <div class="step-number">04</div>
            <div class="step-content">
              <h4>循环链接</h4>
              <p>跨产业生态链接，构建循环经济网络</p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 展望区域 -->
    <section class="outlook-section">
      <div class="container">
        <div class="section-header">
          <h2><i class="fas fa-binoculars"></i> 未来展望</h2>
          <p>面向"双碳"目标，冶金资源利用领域将迎来深刻变革与重大发展机遇</p>
        </div>
        <div class="outlook-grid">
          <div class="outlook-card">
            <div class="outlook-card-icon">
              <i class="fas fa-robot"></i>
            </div>
            <h4>智能化分选技术</h4>
            <p>基于人工智能和机器视觉的智能分选系统，实现冶金固废的高精度分类与高效分离</p>
          </div>
          <div class="outlook-card">
            <div class="outlook-card-icon">
              <i class="fas fa-microchip"></i>
            </div>
            <h4>高值化利用技术</h4>
            <p>开发冶金渣高值化利用技术，从低端建材向高附加值功能材料方向升级</p>
          </div>
          <div class="outlook-card">
            <div class="outlook-card-icon">
              <i class="fas fa-cloud"></i>
            </div>
            <h4>数字化管理平台</h4>
            <p>建立覆盖全流程的冶金资源数字化管理平台，实现资源利用效率的实时优化</p>
          </div>
          <div class="outlook-card">
            <div class="outlook-card-icon">
              <i class="fas fa-handshake"></i>
            </div>
            <h4>产业协同发展</h4>
            <p>构建跨行业、跨区域的冶金资源循环利用产业联盟，推动协同创新与规模化发展</p>
          </div>
        </div>
      </div>
    </section>
  </div>
  <Footer></Footer>
</template>

<script>
import Header from "@/components/Header.vue";
import Footer from "@/components/Footer.vue";

export default {
  name: "ResourceUtilization",
  components: {
    Header,
    Footer,
  },
  data() {
    return {};
  },
  methods: {},
  mounted() {},
};
</script>

<style scoped>
/* ==================== 基础样式 ==================== */
.resource-utilization {
  background-color: #f5f7fa;
  min-height: 120vh;
  font-family: 'Microsoft YaHei', 'Segoe UI', Arial, sans-serif;
  display: flex;
  flex-direction: column;
  padding-top: 80px;
}

/* 容器 */
.container {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 15px;
}

/* ==================== 面包屑导航 ==================== */
.mb-nav {
  background: #fff;
  border-bottom: 1px solid #e8e8e8;
  padding: 12px 0;
}

.mb-nav p {
  font-size: 14px;
  color: #666;
  margin: 0;
}

.mb-nav a {
  color: #0046DB;
  text-decoration: none;
  transition: color 0.3s;
}

.mb-nav a:hover {
  color: #0033a0;
}

.mb-nav span {
  color: #999;
}

/* ==================== 通用区块标题 ==================== */
.section-header {
  text-align: center;
  margin-bottom: 40px;
}

.section-header h2 {
  font-size: 30px;
  color: #222;
  margin: 0 0 12px 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.section-header h2 i {
  color: #0046DB;
  font-size: 26px;
}

.section-header p {
  font-size: 15px;
  color: #666;
  margin: 0;
  line-height: 1.6;
  max-width: 700px;
  margin: 0 auto;
}

/* ==================== 英雄区域 ==================== */
.hero-section {
  position: relative;
  min-height: 420px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1440 600"><rect fill="%230a1628" width="1440" height="600"/><circle cx="200" cy="200" r="250" fill="%230046DB" opacity="0.15"/><circle cx="1200" cy="400" r="300" fill="%2300b894" opacity="0.1"/><circle cx="700" cy="100" r="200" fill="%230046DB" opacity="0.08"/></svg>');
  background-size: cover;
  background-position: center;
  background-color: #0a1628;
  overflow: hidden;
}

.hero-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(10, 22, 40, 0.92) 0%, rgba(0, 70, 219, 0.5) 50%, rgba(0, 184, 148, 0.25) 100%);
  z-index: 1;
}

.hero-content {
  position: relative;
  z-index: 2;
  text-align: center;
  padding: 60px 20px;
}

.hero-title {
  font-size: 42px;
  font-weight: 700;
  color: #fff;
  margin: 0 0 16px 0;
  letter-spacing: 3px;
}

.hero-subtitle {
  font-size: 18px;
  color: rgba(255, 255, 255, 0.8);
  margin: 0 0 50px 0;
  line-height: 1.6;
}

.hero-stats {
  display: flex;
  justify-content: center;
  gap: 50px;
  flex-wrap: wrap;
}

.hero-stat-item {
  text-align: center;
  min-width: 140px;
}

.hero-stat-value {
  display: block;
  font-size: 36px;
  font-weight: 700;
  color: #00d4a0;
  margin-bottom: 6px;
}

.hero-stat-label {
  display: block;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
}

/* ==================== 概述区域 ==================== */
.overview-section {
  padding: 70px 0;
  background: #fff;
}

.overview-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
}

.overview-card {
  background: #f8f9fc;
  border-radius: 12px;
  padding: 30px;
  border: 1px solid #eef0f5;
  transition: all 0.3s;
  display: flex;
  gap: 20px;
}

.overview-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 25px rgba(0, 70, 219, 0.1);
  border-color: #0046DB;
}

.overview-icon {
  width: 56px;
  height: 56px;
  min-width: 56px;
  background: linear-gradient(135deg, #0046DB 0%, #0066ff 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: #fff;
}

.overview-content h3 {
  font-size: 18px;
  color: #222;
  margin: 0 0 8px 0;
}

.overview-content p {
  font-size: 14px;
  color: #666;
  line-height: 1.7;
  margin: 0;
}

/* ==================== 关键指标行 ==================== */
.metrics-section {
  padding: 70px 0;
  background: #f5f7fa;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.metric-card {
  background: #fff;
  border-radius: 12px;
  padding: 25px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  border: 1px solid #f0f0f0;
  transition: all 0.3s;
  display: flex;
  align-items: flex-start;
  gap: 18px;
}

.metric-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 20px rgba(0, 70, 219, 0.1);
  border-color: #0046DB;
}

.metric-icon {
  width: 50px;
  height: 50px;
  min-width: 50px;
  background: rgba(0, 70, 219, 0.08);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  color: #0046DB;
}

.metric-data {
  flex: 1;
}

.metric-value {
  font-size: 24px;
  font-weight: 700;
  color: #0046DB;
  line-height: 1.2;
  margin-bottom: 4px;
}

.metric-label {
  font-size: 13px;
  color: #666;
  margin-bottom: 4px;
}

.metric-trend {
  font-size: 12px;
  font-weight: 500;
}

.metric-trend.up {
  color: #00a854;
}

.metric-card:hover .metric-icon {
  background: #0046DB;
  color: #fff;
}

/* ==================== 重点资源利用领域 ==================== */
.resource-areas-section {
  padding: 70px 0;
  background: #fff;
}

.areas-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 28px;
}

.area-card {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  border: 1px solid #f0f0f0;
  overflow: hidden;
  transition: all 0.4s;
}

.area-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 12px 35px rgba(0, 70, 219, 0.12);
  border-color: #0046DB;
}

.card-image-area {
  position: relative;
  height: 160px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.card-image-area.secondary-resources {
  background: linear-gradient(135deg, #0046DB 0%, #0080FF 100%);
}

.card-image-area.solid-waste {
  background: linear-gradient(135deg, #0a1628 0%, #00509e 100%);
}

.card-image-area.rare-metals {
  background: linear-gradient(135deg, #6c2bd9 0%, #a855f7 100%);
}

.card-image-area.circular-economy {
  background: linear-gradient(135deg, #008060 0%, #00b894 100%);
}

.card-icon-wrapper {
  width: 72px;
  height: 72px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 34px;
  color: #fff;
  transition: all 0.4s;
}

.area-card:hover .card-icon-wrapper {
  transform: scale(1.1);
  background: rgba(255, 255, 255, 0.25);
}

.card-badge {
  position: absolute;
  top: 14px;
  right: 14px;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(4px);
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  padding: 4px 14px;
  border-radius: 20px;
}

.card-body {
  padding: 24px;
}

.card-title {
  font-size: 20px;
  color: #222;
  margin: 0 0 10px 0;
}

.card-desc {
  font-size: 14px;
  color: #666;
  line-height: 1.7;
  margin: 0 0 18px 0;
}

.card-data {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}

.card-data-item {
  background: #f8f9fc;
  border-radius: 8px;
  padding: 12px;
  text-align: center;
  transition: background 0.3s;
}

.area-card:hover .card-data-item {
  background: #f0f4ff;
}

.data-label {
  display: block;
  font-size: 11px;
  color: #999;
  margin-bottom: 4px;
}

.data-value {
  display: block;
  font-size: 16px;
  font-weight: 700;
  color: #0046DB;
}

.card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag {
  font-size: 12px;
  color: #0046DB;
  background: rgba(0, 70, 219, 0.08);
  padding: 4px 12px;
  border-radius: 20px;
  transition: all 0.3s;
}

.area-card:hover .tag {
  background: rgba(0, 70, 219, 0.15);
}

/* ==================== 技术路线图 ==================== */
.roadmap-section {
  padding: 70px 0;
  background: #f5f7fa;
}

.roadmap-grid {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
  flex-wrap: wrap;
}

.roadmap-step {
  background: #fff;
  border-radius: 12px;
  padding: 28px 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  border: 1px solid #f0f0f0;
  text-align: center;
  flex: 1;
  min-width: 180px;
  max-width: 240px;
  transition: all 0.3s;
}

.roadmap-step:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 25px rgba(0, 70, 219, 0.1);
  border-color: #0046DB;
}

.step-number {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #0046DB, #0080FF);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 700;
  color: #fff;
  margin: 0 auto 14px;
}

.roadmap-step h4 {
  font-size: 17px;
  color: #222;
  margin: 0 0 8px 0;
}

.roadmap-step p {
  font-size: 13px;
  color: #666;
  line-height: 1.5;
  margin: 0;
}

.roadmap-arrow {
  font-size: 24px;
  color: #0046DB;
  opacity: 0.5;
}

/* ==================== 展望区域 ==================== */
.outlook-section {
  padding: 70px 0;
  background: #fff;
}

.outlook-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

.outlook-card {
  background: #fff;
  border-radius: 12px;
  padding: 30px 24px;
  text-align: center;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  border: 1px solid #f0f0f0;
  transition: all 0.3s;
}

.outlook-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 30px rgba(0, 70, 219, 0.1);
  border-color: #0046DB;
}

.outlook-card-icon {
  width: 60px;
  height: 60px;
  background: rgba(0, 70, 219, 0.08);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26px;
  color: #0046DB;
  margin: 0 auto 16px;
  transition: all 0.3s;
}

.outlook-card:hover .outlook-card-icon {
  background: #0046DB;
  color: #fff;
}

.outlook-card h4 {
  font-size: 17px;
  color: #222;
  margin: 0 0 10px 0;
}

.outlook-card p {
  font-size: 13px;
  color: #666;
  line-height: 1.6;
  margin: 0;
}

/* ==================== 动画 ==================== */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.hero-content,
.overview-card,
.metric-card,
.area-card,
.roadmap-step,
.outlook-card {
  animation: fadeInUp 0.5s ease-out;
}

/* ==================== 响应式设计 ==================== */
@media (max-width: 1200px) {
  .hero-stats {
    gap: 30px;
  }

  .hero-stat-value {
    font-size: 30px;
  }

  .overview-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .metrics-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .outlook-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 992px) {
  .hero-title {
    font-size: 32px;
  }

  .hero-subtitle {
    font-size: 16px;
  }

  .hero-stat-value {
    font-size: 26px;
  }

  .section-header h2 {
    font-size: 24px;
  }

  .roadmap-grid {
    flex-direction: column;
  }

  .roadmap-arrow {
    transform: rotate(90deg);
  }

  .roadmap-step {
    max-width: 100%;
  }
}

@media (max-width: 768px) {
  .resource-utilization {
    padding-top: 60px;
  }

  .hero-section {
    min-height: 320px;
  }

  .hero-title {
    font-size: 26px;
  }

  .hero-subtitle {
    font-size: 14px;
    margin-bottom: 30px;
  }

  .hero-stats {
    gap: 20px;
  }

  .hero-stat-item {
    min-width: 100px;
  }

  .hero-stat-value {
    font-size: 22px;
  }

  .hero-stat-label {
    font-size: 12px;
  }

  .overview-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .overview-card {
    padding: 20px;
  }

  .metrics-grid {
    grid-template-columns: 1fr;
    gap: 14px;
  }

  .areas-grid {
    grid-template-columns: 1fr;
    gap: 20px;
  }

  .card-data {
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
  }

  .card-data-item {
    padding: 10px 6px;
  }

  .data-value {
    font-size: 14px;
  }

  .outlook-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .section-header {
    margin-bottom: 28px;
  }

  .section-header h2 {
    font-size: 20px;
  }

  .section-header p {
    font-size: 13px;
  }

  .overview-section,
  .metrics-section,
  .resource-areas-section,
  .roadmap-section,
  .outlook-section {
    padding: 40px 0;
  }
}

@media (max-width: 576px) {
  .container {
    padding: 0 12px;
  }

  .hero-content {
    padding: 40px 15px;
  }

  .hero-stats {
    flex-wrap: wrap;
    gap: 16px;
  }

  .hero-stat-item {
    min-width: 80px;
  }

  .card-body {
    padding: 18px;
  }

  .card-title {
    font-size: 17px;
  }
}
</style>
