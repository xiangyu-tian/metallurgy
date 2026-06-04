<template>
  <Header></Header>
  <div class="energy-restructuring">
    <!-- 面包屑导航 -->
    <div class="mb-nav">
      <div class="container">
        <p>
          当前位置： <router-link to="/">首页</router-link> >
          <span>冶金能源重构</span>
        </p>
      </div>
    </div>

    <!-- Hero区域 -->
    <section class="hero-section">
      <div class="hero-overlay"></div>
      <div class="container hero-content">
        <div class="hero-text">
          <h1>冶金能源重构</h1>
          <p class="hero-subtitle">驱动冶金行业绿色低碳转型，构建清洁能源新生态</p>
          <p class="hero-desc">
            以氢冶金、碳捕集、电气化改造和余热回收为核心技术路径，推动冶金行业能源结构根本性变革，助力实现"双碳"目标
          </p>
          <div class="hero-stats">
            <div class="hero-stat-item">
              <span class="hero-stat-value">2030</span>
              <span class="hero-stat-label">碳达峰目标年份</span>
            </div>
            <div class="hero-stat-divider"></div>
            <div class="hero-stat-item">
              <span class="hero-stat-value">50%+</span>
              <span class="hero-stat-label">预计减排潜力</span>
            </div>
            <div class="hero-stat-divider"></div>
            <div class="hero-stat-item">
              <span class="hero-stat-value">4大</span>
              <span class="hero-stat-label">核心技术路径</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 主内容区域 -->
    <div class="container main-content">

      <!-- 关键指标统计 -->
      <section class="stats-row">
        <div class="stat-card" v-for="stat in keyStats" :key="stat.id">
          <div class="stat-card-icon">
            <i :class="stat.icon"></i>
          </div>
          <div class="stat-card-body">
            <div class="stat-card-value">{{ stat.value }}</div>
            <div class="stat-card-title">{{ stat.title }}</div>
            <div class="stat-card-desc">{{ stat.description }}</div>
          </div>
        </div>
      </section>

      <!-- 概述 -->
      <section class="overview-section">
        <div class="section-header">
          <h2><i class="fas fa-globe-asia"></i> 行业背景与战略意义</h2>
          <p class="section-desc">冶金行业作为国民经济支柱产业，其能源结构重构是实现碳中和目标的关键环节</p>
        </div>
        <div class="overview-content">
          <div class="overview-text">
            <p>
              冶金行业是能源消耗和碳排放的大户，约占全国碳排放总量的15%以上。传统的"高炉-转炉"长流程工艺依赖煤炭作为主要能源和还原剂，导致大量的二氧化碳排放。冶金能源重构旨在通过技术革新和能源替代，从根本上改变冶金行业的能源消费结构，实现从"高碳"向"低碳"乃至"零碳"的跨越式转型。
            </p>
            <p>
              在当前全球气候治理和中国"3060双碳目标"的背景下，冶金能源重构不仅是环保要求，更是行业可持续发展的必由之路。通过整合氢能、可再生能源、碳捕集等前沿技术，冶金行业有望在2030年前实现碳达峰，并在2050-2060年逐步接近碳中和目标。
            </p>
            <div class="overview-highlights">
              <div class="highlight-item">
                <i class="fas fa-check-circle"></i>
                <span>短流程电炉炼钢占比将从当前的10%提升至2035年的30%以上</span>
              </div>
              <div class="highlight-item">
                <i class="fas fa-check-circle"></i>
                <span>氢基直接还原铁（H₂-DRI）技术有望减少钢铁生产碳排放50%-80%</span>
              </div>
              <div class="highlight-item">
                <i class="fas fa-check-circle"></i>
                <span>余热余能回收利用率将从目前的45%提升至2030年的70%以上</span>
              </div>
            </div>
          </div>
          <div class="overview-chart">
            <div class="chart-box">
              <div class="chart-title">碳排放结构占比</div>
              <div class="mock-pie">
                <div class="pie-hole"></div>
              </div>
              <div class="chart-legend-h">
                <div class="legend-h-item">
                  <span class="legend-h-dot" style="background: #0046DB;"></span>
                  <span>长流程炼钢</span>
                </div>
                <div class="legend-h-item">
                  <span class="legend-h-dot" style="background: #40C057;"></span>
                  <span>短流程炼钢</span>
                </div>
                <div class="legend-h-item">
                  <span class="legend-h-dot" style="background: #00B4FF;"></span>
                  <span>其他工艺</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- 四大技术领域 -->
      <section class="tech-areas-section">
        <div class="section-header">
          <h2><i class="fas fa-microchip"></i> 关键技术领域</h2>
          <p class="section-desc">四大核心技术路径驱动冶金能源结构深度重构</p>
        </div>

        <div class="tech-areas-grid">
          <div class="tech-card" v-for="area in techAreas" :key="area.id" @click="viewTechDetail(area)">
            <div class="tech-card-header">
              <div class="tech-card-icon" :style="{ background: area.gradient }">
                <i :class="area.icon"></i>
              </div>
              <span class="tech-card-badge">{{ area.badge }}</span>
            </div>
            <div class="tech-card-body">
              <h3>{{ area.title }}</h3>
              <p>{{ area.description }}</p>
              <div class="tech-card-metrics">
                <div class="tech-metric">
                  <i class="fas fa-leaf"></i>
                  <span>减排潜力：<strong>{{ area.reduction }}</strong></span>
                </div>
                <div class="tech-metric">
                  <i class="fas fa-clock"></i>
                  <span>成熟周期：{{ area.timeline }}</span>
                </div>
                <div class="tech-metric">
                  <i class="fas fa-chart-line"></i>
                  <span>投资需求：{{ area.investment }}</span>
                </div>
              </div>
            </div>
            <div class="tech-card-features">
              <div class="feature-tag" v-for="feature in area.features" :key="feature">
                {{ feature }}
              </div>
            </div>
            <div class="tech-card-footer">
              <button class="btn-learn-more">
                了解详情 <i class="fas fa-arrow-right"></i>
              </button>
            </div>
          </div>
        </div>
      </section>

      <!-- 效益与前景 -->
      <section class="significance-section">
        <div class="section-header">
          <h2><i class="fas fa-rocket"></i> 能源重构效益与前景</h2>
          <p class="section-desc">冶金能源重构将带来深远的 environmental 和 economic 双重效益</p>
        </div>

        <div class="significance-grid">
          <div class="significance-card">
            <div class="significance-icon">
              <i class="fas fa-temperature-low"></i>
            </div>
            <h4>碳排放大幅削减</h4>
            <p>到2030年，冶金行业有望实现碳排放总量较峰值水平下降20%-30%。氢冶金和CCUS技术的规模化应用将推动行业在2050年实现近零排放。</p>
          </div>

          <div class="significance-card">
            <div class="significance-icon">
              <i class="fas fa-bolt"></i>
            </div>
            <h4>能源效率显著提升</h4>
            <p>通过余热回收、电气化改造和智能能源管理，冶金行业综合能源利用效率有望从当前的45%提升至2030年的65%以上。</p>
          </div>

          <div class="significance-card">
            <div class="significance-icon">
              <i class="fas fa-chart-bar"></i>
            </div>
            <h4>经济效益持续增长</h4>
            <p>能源成本降低、碳交易收益、绿色产品溢价等将为冶金企业带来新的利润增长点，预计每年可创造超过千亿元的经济价值。</p>
          </div>

          <div class="significance-card">
            <div class="significance-icon">
              <i class="fas fa-shield-alt"></i>
            </div>
            <h4>产业竞争力增强</h4>
            <p>率先完成能源重构的冶金企业将在全球绿色贸易壁垒中占据先机，提升产品国际竞争力和品牌价值，实现可持续发展。</p>
          </div>
        </div>

        <!-- 时间路线图 -->
        <div class="roadmap-section">
          <h3><i class="fas fa-road"></i> 能源重构路线图</h3>
          <div class="roadmap-timeline">
            <div class="roadmap-phase">
              <div class="phase-marker" style="background: #0046DB;">
                <i class="fas fa-flag"></i>
              </div>
              <div class="phase-content">
                <h4>近期 (2025-2030)</h4>
                <p>推广余热回收与电气化改造，氢冶金示范项目投产，碳捕集试点工程落地</p>
              </div>
            </div>
            <div class="roadmap-phase">
              <div class="phase-marker" style="background: #2F6EFF;">
                <i class="fas fa-chart-line"></i>
              </div>
              <div class="phase-content">
                <h4>中期 (2030-2040)</h4>
                <p>氢冶金技术规模化应用，CCUS产业化推广，绿电占比提升至50%以上</p>
              </div>
            </div>
            <div class="roadmap-phase">
              <div class="phase-marker" style="background: #40C057;">
                <i class="fas fa-check-double"></i>
              </div>
              <div class="phase-content">
                <h4>远期 (2040-2060)</h4>
                <p>实现冶金行业近零碳排放，建成绿色低碳冶金产业体系，全面实现碳中和</p>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
  <Footer></Footer>
</template>

<script>
import Header from "@/components/Header.vue";
import Footer from "@/components/Footer.vue";

export default {
  name: "EnergyRestructuring",
  components: {
    Header,
    Footer,
  },
  data() {
    return {
      keyStats: [
        {
          id: 1,
          icon: "fas fa-industry",
          value: "15%+",
          title: "碳排放占比",
          description: "冶金行业占全国碳排放总量比例"
        },
        {
          id: 2,
          icon: "fas fa-tachometer-alt",
          value: "45%",
          title: "能效利用率",
          description: "当前综合能源利用效率"
        },
        {
          id: 3,
          icon: "fas fa-bullseye",
          value: "30%",
          title: "减排目标",
          description: "2030年前碳排放下降目标"
        },
        {
          id: 4,
          icon: "fas fa-solar-panel",
          value: "50%+",
          title: "绿电占比",
          description: "2040年可再生能源电力占比目标"
        },
        {
          id: 5,
          icon: "fas fa-dollar-sign",
          value: "千亿",
          title: "经济价值",
          description: "能源重构每年带来的经济收益"
        },
        {
          id: 6,
          icon: "fas fa-globe",
          value: "2060",
          title: "碳中和目标",
          description: "冶金行业碳中和目标年份"
        }
      ],

      techAreas: [
        {
          id: 1,
          icon: "fas fa-atom",
          title: "氢冶金技术",
          badge: "核心技术",
          gradient: "linear-gradient(135deg, #0046DB, #2F6EFF)",
          description: "以氢气替代传统焦炭作为还原剂，从根本上消除炼铁过程中的碳排放。氢基直接还原铁（H₂-DRI）技术可减少钢铁生产碳排放50%-80%，是冶金行业实现碳中和的关键路径。",
          reduction: "50%-80%",
          timeline: "5-10年",
          investment: "较高",
          features: ["氢基直接还原", "绿氢制备", "富氢高炉", "氢等离子体"]
        },
        {
          id: 2,
          icon: "fas fa-filter",
          title: "碳捕集利用与封存",
          badge: "关键技术",
          gradient: "linear-gradient(135deg, #2F6EFF, #40C057)",
          description: "对无法避免的碳排放进行捕集、利用和封存（CCUS）。包括燃烧后捕集、富氧燃烧、化学链燃烧等技术，实现工业尾气中CO₂的高效分离与资源化利用。",
          reduction: "80%-95%",
          timeline: "3-8年",
          investment: "很高",
          features: ["燃烧后捕集", "富氧燃烧", "矿化利用", "CO₂驱油"]
        },
        {
          id: 3,
          icon: "fas fa-bolt",
          title: "电气化改造",
          badge: "支撑技术",
          gradient: "linear-gradient(135deg, #40C057, #00B4FF)",
          description: "推动冶金生产过程从化石能源向电力能源转型。包括电炉短流程炼钢、感应加热、电热回转窑等技术的推广，结合绿电使用，实现生产过程的深度脱碳。",
          reduction: "30%-60%",
          timeline: "3-5年",
          investment: "中等",
          features: ["电炉短流程", "感应加热", "绿电消纳", "智能电网"]
        },
        {
          id: 4,
          icon: "fas fa-fire",
          title: "余热回收利用",
          badge: "增效技术",
          gradient: "linear-gradient(135deg, #00B4FF, #40C057)",
          description: "回收冶金生产过程中产生的大量余热余能，通过换热、发电、供热等方式实现能源梯级利用。包括烧结余热发电、高炉炉顶余压发电、转炉余热回收等技术。",
          reduction: "15%-25%",
          timeline: "1-3年",
          investment: "较低",
          features: ["余热发电", "余压发电", "梯级利用", "区域供热"]
        }
      ]
    };
  },
  methods: {
    viewTechDetail(area) {
      alert([
        `${area.title}`,
        `减排潜力：${area.reduction}`,
        `成熟周期：${area.timeline}`,
        `投资需求：${area.investment}`
      ].join('\n'));
    }
  }
};
</script>

<style scoped>
/* ==================== 基础样式 ==================== */
.energy-restructuring {
  background-color: #f5f7fa;
  min-height: 100vh;
  font-family: 'Microsoft YaHei', 'Segoe UI', Arial, sans-serif;
  display: flex;
  flex-direction: column;
  padding-top: 80px;
}

.container {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 15px;
}

.main-content {
  padding: 30px 0 50px;
  flex: 1;
}

/* ==================== 面包屑导航 ==================== */
.mb-nav {
  width: 100%;
  background: #fff;
  border-bottom: 1px solid #e8e8e8;
  padding: 12px 0;
}

.mb-nav p {
  margin: 0;
  font-size: 14px;
  color: #999;
}

.mb-nav a {
  color: #0046DB;
  text-decoration: none;
}

.mb-nav a:hover {
  text-decoration: underline;
}

.mb-nav span {
  color: #333;
  font-weight: 500;
}

/* ==================== Hero区域 ==================== */
.hero-section {
  position: relative;
  min-height: 480px;
  display: flex;
  align-items: center;
  background: linear-gradient(135deg, #001529 0%, #003366 30%, #0046DB 60%, #2F6EFF 80%, #40C057 100%);
  overflow: hidden;
}

.hero-overlay {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse at 20% 50%, rgba(64, 192, 87, 0.15) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 30%, rgba(0, 70, 219, 0.3) 0%, transparent 50%),
    radial-gradient(ellipse at 50% 80%, rgba(0, 180, 255, 0.1) 0%, transparent 40%);
  pointer-events: none;
}

.hero-content {
  position: relative;
  z-index: 1;
  padding: 60px 15px;
}

.hero-text {
  max-width: 800px;
}

.hero-text h1 {
  font-size: 48px;
  font-weight: 800;
  color: #fff;
  margin: 0 0 16px 0;
  letter-spacing: 4px;
  text-shadow: 0 2px 20px rgba(0, 0, 0, 0.3);
}

.hero-subtitle {
  font-size: 22px;
  color: rgba(255, 255, 255, 0.9);
  margin: 0 0 16px 0;
  font-weight: 500;
}

.hero-desc {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.75);
  line-height: 1.8;
  margin: 0 0 36px 0;
  max-width: 680px;
}

.hero-stats {
  display: flex;
  align-items: center;
  gap: 32px;
  padding: 24px 32px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  max-width: 620px;
}

.hero-stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.hero-stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #fff;
}

.hero-stat-label {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.7);
}

.hero-stat-divider {
  width: 1px;
  height: 40px;
  background: rgba(255, 255, 255, 0.2);
}

/* ==================== 通用板块标题 ==================== */
.section-header {
  text-align: center;
  margin-bottom: 32px;
}

.section-header h2 {
  font-size: 28px;
  color: #1a1a1a;
  margin: 0 0 10px 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.section-header h2 i {
  color: #0046DB;
  font-size: 26px;
}

.section-desc {
  font-size: 15px;
  color: #888;
  margin: 0;
  line-height: 1.6;
}

/* ==================== 关键指标统计行 ==================== */
.stats-row {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 12px;
  margin-bottom: 40px;
}

.stat-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px 14px;
  text-align: center;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  border: 1px solid #f0f0f0;
  transition: all 0.3s;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 70, 219, 0.12);
  border-color: #0046DB;
}

.stat-card-icon {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(135deg, #0046DB 0%, #2F6EFF 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 20px;
}

.stat-card-body {
  flex: 1;
}

.stat-card-value {
  font-size: 26px;
  font-weight: 800;
  color: #0046DB;
  line-height: 1.2;
  margin-bottom: 4px;
}

.stat-card-title {
  font-size: 14px;
  color: #333;
  font-weight: 600;
  margin-bottom: 4px;
}

.stat-card-desc {
  font-size: 11px;
  color: #999;
  line-height: 1.4;
}

/* ==================== 概述区域 ==================== */
.overview-section {
  background: #fff;
  border-radius: 12px;
  padding: 32px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  margin-bottom: 40px;
  border: 1px solid #f0f0f0;
  transition: all 0.3s;
}

.overview-section:hover {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.overview-content {
  display: grid;
  grid-template-columns: 1.3fr 1fr;
  gap: 32px;
  align-items: start;
}

.overview-text p {
  font-size: 15px;
  color: #555;
  line-height: 1.8;
  margin: 0 0 16px 0;
}

.overview-highlights {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 20px;
}

.highlight-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  font-size: 14px;
  color: #444;
  line-height: 1.5;
}

.highlight-item i {
  color: #40C057;
  font-size: 16px;
  margin-top: 2px;
  flex-shrink: 0;
}

/* 模拟图表 */
.overview-chart {
  display: flex;
  justify-content: center;
  align-items: center;
}

.chart-box {
  width: 100%;
  max-width: 340px;
  background: #f8f9fc;
  border-radius: 12px;
  padding: 24px;
  text-align: center;
}

.chart-title {
  font-size: 15px;
  font-weight: 600;
  color: #333;
  margin-bottom: 20px;
}

.mock-pie {
  position: relative;
  width: 180px;
  height: 180px;
  border-radius: 50%;
  margin: 0 auto 20px;
  background: conic-gradient(
    #0046DB 0deg 252deg,
    #40C057 252deg 324deg,
    #00B4FF 324deg 360deg
  );
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}

.pie-hole {
  width: 80px;
  height: 80px;
  background: #f8f9fc;
  border-radius: 50%;
  z-index: 1;
}

.chart-legend-h {
  display: flex;
  justify-content: center;
  gap: 16px;
  flex-wrap: wrap;
}

.legend-h-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #666;
}

.legend-h-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}


/* ==================== 技术领域区域 ==================== */
.tech-areas-section {
  margin-bottom: 40px;
}

.tech-areas-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.tech-card {
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  border: 1px solid #f0f0f0;
  transition: all 0.3s;
  cursor: pointer;
  display: flex;
  flex-direction: column;
}

.tech-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 12px 32px rgba(0, 70, 219, 0.12);
  border-color: #0046DB;
}

.tech-card-header {
  position: relative;
  padding: 28px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.tech-card-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 26px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.tech-card-badge {
  font-size: 12px;
  padding: 4px 12px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.9);
  color: #0046DB;
  font-weight: 600;
}

.tech-card-body {
  padding: 0 24px 20px;
}

.tech-card-body h3 {
  font-size: 20px;
  color: #1a1a1a;
  margin: 0 0 10px 0;
}

.tech-card-body p {
  font-size: 14px;
  color: #666;
  line-height: 1.7;
  margin: 0 0 16px 0;
}

.tech-card-metrics {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tech-metric {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  color: #888;
  padding: 5px 10px;
  background: #f5f7fa;
  border-radius: 6px;
}

.tech-metric i {
  color: #0046DB;
  font-size: 12px;
}

.tech-metric strong {
  color: #0046DB;
  font-weight: 700;
}

.tech-card-features {
  padding: 0 24px 16px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.feature-tag {
  font-size: 11px;
  color: #0046DB;
  background: rgba(0, 70, 219, 0.08);
  padding: 3px 10px;
  border-radius: 4px;
  font-weight: 500;
}

.tech-card-footer {
  padding: 16px 24px;
  border-top: 1px solid #f0f0f0;
  margin-top: auto;
}

.btn-learn-more {
  width: 100%;
  padding: 10px 20px;
  background: transparent;
  border: 1px solid #0046DB;
  border-radius: 8px;
  color: #0046DB;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-weight: 500;
}

.btn-learn-more:hover {
  background: #0046DB;
  color: #fff;
}

/* ==================== 效益与前景区域 ==================== */
.significance-section {
  background: #fff;
  border-radius: 12px;
  padding: 32px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  margin-bottom: 40px;
  border: 1px solid #f0f0f0;
  transition: all 0.3s;
}

.significance-section:hover {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.significance-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 36px;
}

.significance-card {
  background: #f8f9fc;
  border-radius: 12px;
  padding: 24px;
  text-align: center;
  transition: all 0.3s;
  border: 1px solid transparent;
}

.significance-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 70, 219, 0.1);
  border-color: #0046DB;
  background: #fff;
}

.significance-icon {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: linear-gradient(135deg, #0046DB 0%, #40C057 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
  color: #fff;
  font-size: 24px;
}

.significance-card h4 {
  font-size: 16px;
  color: #1a1a1a;
  margin: 0 0 10px 0;
}

.significance-card p {
  font-size: 13px;
  color: #666;
  line-height: 1.7;
  margin: 0;
}

/* ==================== 路线图 ==================== */
.roadmap-section {
  background: #f8f9fc;
  border-radius: 12px;
  padding: 28px;
}

.roadmap-section h3 {
  font-size: 20px;
  color: #1a1a1a;
  margin: 0 0 28px 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.roadmap-section h3 i {
  color: #0046DB;
}

.roadmap-timeline {
  display: flex;
  flex-direction: column;
  gap: 0;
  position: relative;
  padding-left: 40px;
}

.roadmap-timeline::before {
  content: '';
  position: absolute;
  left: 19px;
  top: 0;
  bottom: 0;
  width: 2px;
  background: linear-gradient(to bottom, #0046DB, #40C057);
}

.roadmap-phase {
  position: relative;
  padding-bottom: 28px;
}

.roadmap-phase:last-child {
  padding-bottom: 0;
}

.phase-marker {
  position: absolute;
  left: -40px;
  top: 0;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  z-index: 1;
}

.phase-content {
  padding-left: 20px;
}

.phase-content h4 {
  font-size: 16px;
  color: #0046DB;
  margin: 0 0 6px 0;
  font-weight: 600;
}

.phase-content p {
  font-size: 14px;
  color: #666;
  line-height: 1.6;
  margin: 0;
}

/* ==================== 响应式设计 ==================== */
@media (max-width: 1200px) {
  .container {
    max-width: 960px;
  }

  .stats-row {
    grid-template-columns: repeat(3, 1fr);
  }

  .significance-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 992px) {
  .energy-restructuring {
    padding-top: 80px;
  }

  .hero-text h1 {
    font-size: 36px;
  }

  .hero-subtitle {
    font-size: 18px;
  }

  .hero-stats {
    flex-wrap: wrap;
    gap: 16px;
    padding: 20px 24px;
  }

  .hero-stat-divider {
    display: none;
  }

  .overview-content {
    grid-template-columns: 1fr;
    gap: 24px;
  }

  .tech-areas-grid {
    grid-template-columns: 1fr;
  }

  .significance-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .main-content {
    padding: 20px 0 30px;
  }

  .hero-section {
    min-height: 380px;
  }

  .hero-text h1 {
    font-size: 28px;
    letter-spacing: 2px;
  }

  .hero-subtitle {
    font-size: 16px;
  }

  .hero-desc {
    font-size: 14px;
  }

  .hero-stats {
    padding: 16px 20px;
    justify-content: space-around;
  }

  .hero-stat-value {
    font-size: 22px;
  }

  .hero-stat-label {
    font-size: 11px;
  }

  .stats-row {
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
  }

  .stat-card {
    padding: 16px 10px;
  }

  .stat-card-value {
    font-size: 22px;
  }

  .section-header h2 {
    font-size: 22px;
  }

  .overview-section,
  .significance-section {
    padding: 20px;
  }

  .significance-grid {
    grid-template-columns: 1fr;
  }

  .tech-card-header {
    padding: 20px 18px;
  }

  .tech-card-body {
    padding: 0 18px 16px;
  }

  .tech-card-features {
    padding: 0 18px 12px;
  }

  .tech-card-footer {
    padding: 12px 18px;
  }

  .roadmap-section {
    padding: 20px;
  }

  .roadmap-timeline {
    padding-left: 36px;
  }

  .phase-marker {
    left: -36px;
    width: 36px;
    height: 36px;
    font-size: 14px;
  }
}

@media (max-width: 576px) {
  .container {
    padding: 0 10px;
  }

  .hero-text h1 {
    font-size: 24px;
  }

  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }

  .section-header h2 {
    font-size: 20px;
    flex-wrap: wrap;
  }

  .overview-section,
  .significance-section {
    padding: 16px;
  }

  .tech-card-icon {
    width: 48px;
    height: 48px;
    font-size: 20px;
  }

  .tech-card-body h3 {
    font-size: 18px;
  }
}

/* 动画 */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(15px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.hero-text,
.stat-card,
.tech-card,
.significance-card,
.overview-section,
.significance-section {
  animation: fadeIn 0.5s ease-out;
}

.tech-card:nth-child(2) { animation-delay: 0.1s; }
.tech-card:nth-child(3) { animation-delay: 0.2s; }
.tech-card:nth-child(4) { animation-delay: 0.3s; }
</style>
