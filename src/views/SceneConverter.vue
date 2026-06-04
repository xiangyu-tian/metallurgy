<template>
  <Header></Header>
  <div class="scene-converter">
    <!-- Breadcrumb -->
    <div class="mb-nav">
      <div class="container">
        <p>
          当前位置：<router-link to="/">首页</router-link> &gt;
          <router-link to="/scenes">智能场景</router-link> &gt;
          <span>转炉炼钢工艺优化</span>
        </p>
      </div>
    </div>

    <!-- Hero -->
    <div class="hero-section">
      <div class="container">
        <div class="hero-content">
          <div class="hero-icon">
            <i class="fas fa-industry"></i>
          </div>
          <h1 class="hero-title">转炉炼钢工艺优化</h1>
          <p class="hero-desc">
            基于铁水成分与工艺参数，智能优化转炉炼钢操作，精准预测终点碳含量与钢水温度，助力提升冶炼效率与产品质量
          </p>
        </div>
      </div>
    </div>

    <!-- 2x2 Enterprise Card Grid -->
    <div class="container main-content">
      <div class="tools-grid">

        <!-- Card 1: 终点预测 -->
        <div class="tool-card">
          <div class="tool-card-header">
            <div class="tool-card-icon">
              <i class="fas fa-bullseye"></i>
            </div>
            <div class="tool-card-title-wrap">
              <h3 class="tool-card-title">终点预测</h3>
              <span class="tool-card-badge badge-hot">热门</span>
            </div>
          </div>
          <div class="tool-card-body">
            <ul class="tool-metrics">
              <li><i class="fas fa-check-circle"></i> 预测终点碳/温度</li>
              <li><i class="fas fa-check-circle"></i> 计算氧耗</li>
            </ul>
            <router-link :to="'/scene/converter/tool/endpoint'" class="tool-link">
              进入工具 <i class="fas fa-arrow-right"></i>
            </router-link>
          </div>
        </div>

        <!-- Card 2: 氧耗计算 -->
        <div class="tool-card">
          <div class="tool-card-header">
            <div class="tool-card-icon icon-oxygen">
              <i class="fas fa-gauge-high"></i>
            </div>
            <div class="tool-card-title-wrap">
              <h3 class="tool-card-title">氧耗计算</h3>
            </div>
          </div>
          <div class="tool-card-body">
            <ul class="tool-metrics">
              <li><i class="fas fa-check-circle"></i> 计算氧气消耗</li>
              <li><i class="fas fa-check-circle"></i> 优化氧枪制度</li>
            </ul>
            <router-link :to="'/scene/converter/tool/oxygen'" class="tool-link">
              进入工具 <i class="fas fa-arrow-right"></i>
            </router-link>
          </div>
        </div>

        <!-- Card 3: 温度预测 -->
        <div class="tool-card">
          <div class="tool-card-header">
            <div class="tool-card-icon icon-temperature">
              <i class="fas fa-temperature-high"></i>
            </div>
            <div class="tool-card-title-wrap">
              <h3 class="tool-card-title">温度预测</h3>
            </div>
          </div>
          <div class="tool-card-body">
            <ul class="tool-metrics">
              <li><i class="fas fa-check-circle"></i> 预测终点温度</li>
              <li><i class="fas fa-check-circle"></i> 辅助温控决策</li>
            </ul>
            <router-link :to="'/scene/converter/tool/temperature'" class="tool-link">
              进入工具 <i class="fas fa-arrow-right"></i>
            </router-link>
          </div>
        </div>

        <!-- Card 4: 渣碱度计算 -->
        <div class="tool-card">
          <div class="tool-card-header">
            <div class="tool-card-icon icon-slag">
              <i class="fas fa-flask"></i>
            </div>
            <div class="tool-card-title-wrap">
              <h3 class="tool-card-title">渣碱度计算</h3>
            </div>
          </div>
          <div class="tool-card-body">
            <ul class="tool-metrics">
              <li><i class="fas fa-check-circle"></i> 计算渣碱度 R</li>
              <li><i class="fas fa-check-circle"></i> 优化造渣制度</li>
            </ul>
            <router-link :to="'/scene/converter/tool/slag'" class="tool-link">
              进入工具 <i class="fas fa-arrow-right"></i>
            </router-link>
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
  name: "SceneConverter",
  components: {
    Header,
    Footer,
  },
};
</script>

<style scoped>
/* ==================== Base ==================== */
.scene-converter {
  background-color: #f5f7fa;
  min-height: 100vh;
  font-family: "Microsoft YaHei", "Segoe UI", Arial, sans-serif;
  padding-top: 80px;
}

.container {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 15px;
}

.main-content {
  padding: 40px 0 60px;
}

/* ==================== Breadcrumb ==================== */
.mb-nav {
  background: linear-gradient(180deg, #082a78 0%, #0a192f 100%);
  padding: 15px 0 5px;
}

.mb-nav p {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
  margin: 0;
}

.mb-nav a {
  color: rgba(255, 255, 255, 0.7);
  text-decoration: none;
  transition: color 0.3s;
}

.mb-nav a:hover {
  color: #2066fc;
}

.mb-nav span {
  color: #2066fc;
}

/* ==================== Hero ==================== */
.hero-section {
  background: linear-gradient(135deg, #002266 0%, #0046db 40%, #0055ff 100%);
  padding: 60px 0;
  position: relative;
  overflow: hidden;
}

.hero-section::before {
  content: "";
  position: absolute;
  top: -50%;
  right: -20%;
  width: 500px;
  height: 500px;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.05) 0%, transparent 70%);
  border-radius: 50%;
}

.hero-section::after {
  content: "";
  position: absolute;
  bottom: -30%;
  left: -10%;
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.03) 0%, transparent 70%);
  border-radius: 50%;
}

.hero-content {
  position: relative;
  z-index: 1;
  text-align: center;
}

.hero-icon {
  width: 80px;
  height: 80px;
  margin: 0 auto 20px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36px;
  color: #fff;
  backdrop-filter: blur(10px);
  border: 2px solid rgba(255, 255, 255, 0.2);
}

.hero-title {
  font-size: 36px;
  color: #fff;
  margin: 0 0 15px;
  font-weight: 700;
  letter-spacing: 2px;
}

.hero-desc {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.85);
  margin: 0 auto;
  max-width: 700px;
  line-height: 1.6;
}

/* ==================== 2x2 Grid ==================== */
.tools-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

/* ==================== Enterprise Card ==================== */
.tool-card {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid #f0f0f0;
  transition: box-shadow 0.3s, border-color 0.3s, transform 0.3s;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.tool-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 70, 219, 0.12);
  border-color: #e0ebff;
}

/* ==================== Card Header ==================== */
.tool-card-header {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 22px 24px 16px;
  background: #e8f0fe;
}

.tool-card-icon {
  width: 48px;
  height: 48px;
  background: #0046db;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  color: #fff;
  flex-shrink: 0;
}

.tool-card-icon.icon-oxygen {
  background: #e53935;
}

.tool-card-icon.icon-temperature {
  background: #e53935;
}

.tool-card-icon.icon-slag {
  background: #e53935;
}

.tool-card-title-wrap {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 10px;
}

.tool-card-title {
  font-size: 18px;
  color: #333;
  margin: 0;
  font-weight: 600;
}

.tool-card-badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  line-height: 1.6;
}

.badge-hot {
  background: #e53935;
  color: #fff;
}

/* ==================== Card Body ==================== */
.tool-card-body {
  padding: 20px 24px 24px;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.tool-metrics {
  list-style: none;
  margin: 0 0 20px;
  padding: 0;
  flex: 1;
}

.tool-metrics li {
  font-size: 14px;
  color: #666;
  line-height: 1.8;
  display: flex;
  align-items: center;
  gap: 8px;
}

.tool-metrics li i {
  color: #0046db;
  font-size: 14px;
}

/* ==================== Button ==================== */
.tool-link {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: #0046db;
  color: #fff;
  text-decoration: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s;
  align-self: flex-start;
}

.tool-link:hover {
  background: #0033a0;
  box-shadow: 0 4px 14px rgba(0, 70, 219, 0.3);
}

.tool-link i {
  font-size: 12px;
  transition: transform 0.3s;
}

.tool-link:hover i {
  transform: translateX(4px);
}

/* ==================== Responsive ==================== */
@media (max-width: 1200px) {
  .container {
    max-width: 960px;
  }

  .hero-title {
    font-size: 30px;
  }

  .hero-section {
    padding: 50px 0;
  }

  .tools-grid {
    gap: 20px;
  }
}

@media (max-width: 992px) {
  .tools-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .hero-section {
    padding: 40px 0;
  }

  .hero-title {
    font-size: 26px;
  }

  .hero-desc {
    font-size: 14px;
  }

  .hero-icon {
    width: 64px;
    height: 64px;
    font-size: 28px;
  }

  .main-content {
    padding: 25px 0 40px;
  }

  .tool-card-header {
    padding: 18px 18px 14px;
  }

  .tool-card-body {
    padding: 16px 18px 20px;
  }

  .tool-card-title {
    font-size: 16px;
  }

  .tool-card-icon {
    width: 42px;
    height: 42px;
    font-size: 18px;
  }
}

@media (max-width: 576px) {
  .container {
    padding: 0 12px;
  }

  .hero-title {
    font-size: 22px;
  }

  .hero-desc {
    font-size: 13px;
  }

  .hero-section {
    padding: 30px 0;
  }

  .hero-icon {
    width: 56px;
    height: 56px;
    font-size: 24px;
    margin-bottom: 15px;
  }

  .tools-grid {
    gap: 16px;
  }

  .tool-link {
    width: 100%;
    justify-content: center;
  }
}

/* ==================== Animation ==================== */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
