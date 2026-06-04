<template>
  <Header></Header>
  <div class="scene-blastfurnace">
    <!-- 面包屑导航 -->
    <div class="blastfurnace-banner">
      <div class="container">
        <div class="mb-nav">
          <p>
            当前位置：<router-link to="/">首页</router-link> &gt;
            <router-link to="/scene/thermodynamics">智能场景</router-link> &gt;
            <span>高炉低碳运行分析</span>
          </p>
        </div>
        <div class="banner-content">
          <h1 class="banner-title">高炉低碳运行分析</h1>
          <p class="banner-subtitle">
            基于高炉操作参数与原料条件，智能评估碳排放水平，提供低碳运行优化建议，
            助力钢铁行业绿色转型与可持续发展。
          </p>
        </div>
      </div>
    </div>

    <!-- 2x2 工具卡片区域 -->
    <div class="main-section">
      <div class="container">
        <div class="tools-grid">

          <!-- 卡片 1: 碳排放核算 -->
          <router-link to="/scene/blastfurnace/tool/carbon" class="tool-card">
            <div class="tool-card-header">
              <div class="tool-icon">
                <i class="fas fa-leaf"></i>
              </div>
              <div class="tool-title-area">
                <h2 class="tool-title">碳排放核算</h2>
                <span class="tool-badge">核心</span>
              </div>
            </div>
            <div class="tool-card-body">
              <ul class="tool-metrics">
                <li><i class="fas fa-check-circle"></i> 核算 CO₂ 排放</li>
                <li><i class="fas fa-check-circle"></i> 计算碳强度</li>
              </ul>
              <div class="tool-card-action">
                <span class="tool-card-btn">进入工具 <i class="fas fa-arrow-right"></i></span>
              </div>
            </div>
          </router-link>

          <!-- 卡片 2: 能效评估 -->
          <router-link to="/scene/blastfurnace/tool/efficiency" class="tool-card">
            <div class="tool-card-header">
              <div class="tool-icon">
                <i class="fas fa-bolt"></i>
              </div>
              <div class="tool-title-area">
                <h2 class="tool-title">能效评估</h2>
              </div>
            </div>
            <div class="tool-card-body">
              <ul class="tool-metrics">
                <li><i class="fas fa-check-circle"></i> 评估能效等级</li>
                <li><i class="fas fa-check-circle"></i> 分析节能潜力</li>
              </ul>
              <div class="tool-card-action">
                <span class="tool-card-btn">进入工具 <i class="fas fa-arrow-right"></i></span>
              </div>
            </div>
          </router-link>

          <!-- 卡片 3: 降碳潜力 -->
          <router-link to="/scene/blastfurnace/tool/reduction" class="tool-card">
            <div class="tool-card-header">
              <div class="tool-icon">
                <i class="fas fa-arrow-down"></i>
              </div>
              <div class="tool-title-area">
                <h2 class="tool-title">降碳潜力</h2>
              </div>
            </div>
            <div class="tool-card-body">
              <ul class="tool-metrics">
                <li><i class="fas fa-check-circle"></i> 对比行业基准</li>
                <li><i class="fas fa-check-circle"></i> 评估降碳空间</li>
              </ul>
              <div class="tool-card-action">
                <span class="tool-card-btn">进入工具 <i class="fas fa-arrow-right"></i></span>
              </div>
            </div>
          </router-link>

          <!-- 卡片 4: 碳利用效率 -->
          <router-link to="/scene/blastfurnace/tool/utilization" class="tool-card">
            <div class="tool-card-header">
              <div class="tool-icon">
                <i class="fas fa-recycle"></i>
              </div>
              <div class="tool-title-area">
                <h2 class="tool-title">碳利用效率</h2>
              </div>
            </div>
            <div class="tool-card-body">
              <ul class="tool-metrics">
                <li><i class="fas fa-check-circle"></i> 计算碳素效率</li>
                <li><i class="fas fa-check-circle"></i> 优化燃料配比</li>
              </ul>
              <div class="tool-card-action">
                <span class="tool-card-btn">进入工具 <i class="fas fa-arrow-right"></i></span>
              </div>
            </div>
          </router-link>

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
  name: "SceneBlastfurnace",
  components: {
    Header,
    Footer,
  },
};
</script>

<style scoped>
/* ========== 全局页面样式 ========== */
.scene-blastfurnace {
  padding-top: 80px;
  background: linear-gradient(180deg, #f0f4ff 0%, #ffffff 100%);
  min-height: 100vh;
  font-family: "Microsoft YaHei", "Segoe UI", Arial, sans-serif;
}

/* ========== 面包屑导航 ========== */
.mb-nav {
  color: #6b7a99;
  font-size: 15px;
  margin-top: 28px;
}
.mb-nav a {
  color: #6b7a99;
  font-size: 15px;
  text-decoration: none;
  transition: color 0.3s;
}
.mb-nav a:hover {
  color: #0046db;
}
.mb-nav span {
  color: #40c057;
}

/* ========== 英雄区域 ========== */
.blastfurnace-banner {
  background: linear-gradient(135deg, #e8f0fe 0%, #d6e4ff 50%, #ffffff 100%);
  padding-bottom: 60px;
  position: relative;
  overflow: hidden;
}
.blastfurnace-banner::before {
  content: "";
  position: absolute;
  top: -50%;
  right: -10%;
  width: 600px;
  height: 600px;
  background: radial-gradient(circle, rgba(0, 70, 219, 0.06) 0%, transparent 70%);
  border-radius: 50%;
  pointer-events: none;
}
.blastfurnace-banner::after {
  content: "";
  position: absolute;
  bottom: -30%;
  left: -5%;
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, rgba(64, 192, 87, 0.06) 0%, transparent 70%);
  border-radius: 50%;
  pointer-events: none;
}

.banner-content {
  text-align: center;
  padding-top: 30px;
  position: relative;
  z-index: 1;
}

.banner-title {
  font-size: 38px;
  font-weight: 700;
  color: #1a2744;
  margin-bottom: 16px;
  letter-spacing: 2px;
}

.banner-subtitle {
  font-size: 16px;
  color: #5a6a8a;
  max-width: 660px;
  margin: 0 auto;
  line-height: 1.8;
}

/* ========== 主内容区域 ========== */
.main-section {
  padding: 48px 0 100px;
  background: #f5f8ff;
}

/* ========== 2x2 工具卡片网格 ========== */
.tools-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.tool-card {
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  overflow: hidden;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  text-decoration: none;
  cursor: pointer;
}
.tool-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 70, 219, 0.15);
}

/* ========== 卡片头部 ========== */
.tool-card-header {
  padding: 20px 24px;
  background: #e8f0fe;
  display: flex;
  align-items: center;
  gap: 14px;
}

.tool-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  background: #ffffff;
  color: #0046db;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
  box-shadow: 0 1px 4px rgba(0, 70, 219, 0.1);
}

.tool-title-area {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.tool-title {
  font-size: 18px;
  font-weight: 600;
  color: #1a2744;
  margin: 0;
}

.tool-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 10px;
  font-size: 11px;
  font-weight: 600;
  color: #40c057;
  background: rgba(64, 192, 87, 0.12);
  border-radius: 10px;
  line-height: 1.6;
  letter-spacing: 0.5px;
}

/* ========== 卡片主体 ========== */
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
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.tool-metrics li {
  font-size: 14px;
  color: #4a5a78;
  display: flex;
  align-items: center;
  gap: 8px;
}

.tool-metrics li i {
  color: #40c057;
  font-size: 14px;
}

.tool-card-action {
  margin-top: auto;
}

.tool-card-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 42px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  background: #0046db;
  color: #ffffff;
  text-decoration: none;
}
.tool-card:hover .tool-card-btn {
  background: #0035b0;
  box-shadow: 0 4px 14px rgba(0, 70, 219, 0.3);
}

.tool-card-btn i {
  font-size: 13px;
  transition: transform 0.3s ease;
}
.tool-card:hover .tool-card-btn i {
  transform: translateX(4px);
}

/* ========== 响应式 ========== */
@media (max-width: 1400px) {
  .banner-title {
    font-size: 34px;
  }
  .banner-subtitle {
    font-size: 15px;
  }
}

@media (max-width: 1100px) {
  .tools-grid {
    grid-template-columns: 1fr;
    gap: 20px;
  }
}

@media (max-width: 1000px) {
  .scene-blastfurnace {
    padding-top: 60px;
  }

  .mb-nav {
    font-size: 14px;
    margin-top: 15px;
  }
  .mb-nav a {
    font-size: 14px;
  }

  .banner-title {
    font-size: 28px;
  }
  .banner-subtitle {
    font-size: 14px;
  }

  .main-section {
    padding: 30px 0 60px;
  }

  .tool-card-header {
    padding: 16px 18px;
  }
  .tool-card-body {
    padding: 16px 18px 20px;
  }

  .tool-title {
    font-size: 17px;
  }
}

@media (max-width: 768px) {
  .banner-title {
    font-size: 22px;
  }
  .banner-content {
    padding-top: 15px;
  }
  .tool-title-area {
    flex-wrap: wrap;
  }
}
</style>
