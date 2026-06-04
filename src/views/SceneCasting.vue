<template>
  <Header />
  <div class="SceneCasting">
    <!-- Hero Section -->
    <div class="hero-section">
      <div class="hero-overlay"></div>
      <div class="container hero-content">
        <h1 class="hero-title">连铸质量辅助决策</h1>
        <p class="hero-desc">基于工艺参数智能评估连铸坯质量，优化连铸生产工艺参数</p>
      </div>
    </div>

    <div class="main-wrapper">
      <!-- Breadcrumb -->
      <div class="mb-nav">
        <div class="container">
          <p>
            当前位置：<router-link to="/">首页</router-link> &gt;
            <router-link to="/">智能场景</router-link> &gt;
            <span>连铸质量辅助决策</span>
          </p>
        </div>
      </div>

      <!-- 2x2 Card Grid -->
      <div class="container main-section">
        <div class="cards-grid">
          <div
            v-for="(tool, index) in tools"
            :key="tool.key"
            class="tool-card"
            :class="{ 'card-highlight': tool.highlight }"
          >
            <!-- Card Header -->
            <div class="card-header">
              <i :class="['fas', tool.icon, 'card-icon']"></i>
              <span class="card-title">{{ tool.label }}</span>
              <span v-if="tool.highlight" class="badge-hot">推荐</span>
            </div>

            <!-- Card Body -->
            <div class="card-body">
              <div class="metrics">
                <div class="metric-item">
                  <span class="metric-label">{{ tool.metrics[0] }}</span>
                </div>
                <div class="metric-item">
                  <span class="metric-label">{{ tool.metrics[1] }}</span>
                </div>
              </div>
              <router-link :to="tool.link" class="card-btn">
                <span>进入工具</span>
                <i class="fas fa-arrow-right"></i>
              </router-link>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  <Footer />
</template>

<script>
import Header from "@/components/Header.vue";
import Footer from "@/components/Footer.vue";

export default {
  name: "SceneCasting",
  components: {
    Header,
    Footer,
  },
  data() {
    return {
      tools: [
        {
          key: "quality",
          label: "质量综合评分",
          icon: "fa-star",
          metrics: ["综合质量评分", "优化建议"],
          link: "/scene/casting/tool/quality",
          highlight: false,
        },
        {
          key: "segregation",
          label: "偏析预测",
          icon: "fa-chart-line",
          metrics: ["碳极差预测", "偏析指数评估"],
          link: "/scene/casting/tool/segregation",
          highlight: true,
        },
        {
          key: "crack",
          label: "表面裂纹预测",
          icon: "fa-exclamation-triangle",
          metrics: ["裂纹指数", "风险评估"],
          link: "/scene/casting/tool/crack",
          highlight: false,
        },
        {
          key: "porosity",
          label: "中心疏松预测",
          icon: "fa-circle",
          metrics: ["疏松指数", "严重程度"],
          link: "/scene/casting/tool/porosity",
          highlight: false,
        },
      ],
    };
  },
};
</script>

<style scoped>
/* ===================== Hero Section ===================== */
.hero-section {
  position: relative;
  padding-top: 80px;
  height: 320px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #0a1628 0%, #002a67 40%, #0046db 100%);
}

.hero-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    135deg,
    rgba(0, 22, 58, 0.88),
    rgba(0, 70, 219, 0.6),
    rgba(0, 22, 58, 0.85)
  );
}

.hero-content {
  position: relative;
  z-index: 1;
  text-align: center;
}

.hero-title {
  font-size: 42px;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: 4px;
  margin-bottom: 16px;
}

.hero-desc {
  font-size: 18px;
  color: rgba(255, 255, 255, 0.75);
  max-width: 600px;
  margin: 0 auto;
  line-height: 1.6;
}

/* ===================== Main Wrapper (light bg) ===================== */
.main-wrapper {
  background-color: #f5f7fa;
}

/* ===================== Breadcrumb ===================== */
.mb-nav {
  background: #ffffff;
  border-bottom: 1px solid #e8ecf1;
}

.mb-nav p {
  font-size: 14px;
  padding: 14px 0;
  color: #8c8c8c;
  margin: 0;
}

.mb-nav a {
  color: #8c8c8c;
  text-decoration: none;
  transition: color 0.3s;
}

.mb-nav a:hover {
  color: #0046db;
}

.mb-nav span {
  color: #0046db;
  font-weight: 500;
}

/* ===================== Main Layout ===================== */
.main-section {
  padding: 50px 0 100px;
}

.cards-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

/* ===================== Tool Card ===================== */
.tool-card {
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  overflow: hidden;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.tool-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 70, 219, 0.15);
}

/* Highlighted card (偏析预测) - subtle blue border */
.card-highlight {
  border: 1.5px solid #0046db;
  position: relative;
}

/* ===================== Card Header ===================== */
.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 18px 24px;
  background-color: #e8f0fe;
  border-bottom: 1px solid #d6e4f5;
}

.card-icon {
  color: #0046db;
  font-size: 18px;
  width: 20px;
  text-align: center;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a2e;
}

/* Hot badge */
.badge-hot {
  margin-left: auto;
  display: inline-block;
  padding: 2px 12px;
  font-size: 11px;
  font-weight: 700;
  border-radius: 10px;
  background: #ff4d4f;
  color: #ffffff;
  letter-spacing: 1px;
}

/* ===================== Card Body ===================== */
.card-body {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* Metrics */
.metrics {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.metric-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 14px 16px;
  background: #f9fafb;
  border: 1px solid #eef1f6;
  border-radius: 8px;
  text-align: center;
}

.metric-label {
  font-size: 13px;
  font-weight: 600;
  color: #1a1a2e;
}

.metric-desc {
  font-size: 12px;
  color: #8c8c8c;
}

/* ===================== Card Button ===================== */
.card-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  height: 44px;
  border: none;
  border-radius: 8px;
  background-color: #0046db;
  color: #ffffff;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  text-decoration: none;
}

.card-btn:hover {
  background-color: #0038b3;
  box-shadow: 0 4px 16px rgba(0, 70, 219, 0.35);
}

.card-btn i {
  font-size: 13px;
  transition: transform 0.3s;
}

.card-btn:hover i {
  transform: translateX(4px);
}

/* ===================== Responsive ===================== */
@media (max-width: 1200px) {
  .hero-title {
    font-size: 32px;
  }
  .hero-section {
    height: 260px;
  }
}

@media (max-width: 1000px) {
  .hero-title {
    font-size: 26px;
    letter-spacing: 2px;
  }
  .hero-desc {
    font-size: 15px;
  }
  .hero-section {
    height: 220px;
  }
  .cards-grid {
    gap: 18px;
  }
}

@media (max-width: 768px) {
  .cards-grid {
    grid-template-columns: 1fr;
    gap: 20px;
  }
  .hero-title {
    font-size: 22px;
  }
  .hero-desc {
    font-size: 14px;
  }
  .hero-section {
    height: 200px;
  }
  .main-section {
    padding: 30px 0 60px;
  }
  .card-header {
    padding: 14px 18px;
  }
  .card-body {
    padding: 18px;
  }
  .metrics {
    gap: 10px;
  }
  .metric-item {
    padding: 12px 10px;
  }
}
</style>
