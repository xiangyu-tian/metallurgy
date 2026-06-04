<template>
  <Header></Header>
  <div class="scene-thermodynamics">
    <!-- 面包屑导航 -->
    <div class="mb-nav">
      <div class="container">
        <p>
          <router-link to="/">首页</router-link>
          <span class="sep">></span>
          <router-link to="/scenes">智能场景</router-link>
          <span class="sep">></span>
          <span class="current">热力学推理</span>
        </p>
      </div>
    </div>

    <!-- Hero 区域 -->
    <section class="hero-section">
      <div class="hero-bg-pattern"></div>
      <div class="container">
        <div class="hero-content">
          <div class="hero-tag">智能场景</div>
          <h1 class="hero-title">热力学推理</h1>
          <p class="hero-desc">
            基于热力学原理，计算冶金反应在不同温度下的热力学参数，<br />
            辅助工艺设计与反应条件优化。
          </p>
        </div>
      </div>
    </section>

    <!-- 工具卡片区域 -->
    <section class="main-section">
      <div class="container">
        <div class="section-title-bar">
          <h2 class="section-title">热力学工具</h2>
          <span class="section-badge">(4)</span>
        </div>

        <div class="tools-grid">
          <!-- Card 1: ΔG 计算 -->
          <router-link to="/scene/thermodynamics/tool/delta-g" class="tool-card">
            <div class="card-header">
              <div class="card-icon">
                <i class="fas fa-fire"></i>
              </div>
              <h3 class="card-title">ΔG 计算</h3>
              <span class="card-badge badge-recommend">推荐</span>
            </div>
            <div class="card-body">
              <p class="card-desc">
                计算冶金反应的吉布斯自由能变化，判断反应自发性方向
              </p>
              <div class="card-metrics">
                <span class="metric-item">
                  <i class="fas fa-check-circle"></i>
                  支持 10 种反应
                </span>
                <span class="metric-item">
                  <i class="fas fa-check-circle"></i>
                  计算 ΔG/K
                </span>
              </div>
            </div>
            <div class="card-footer">
              <span class="card-btn">进入工具 <i class="fas fa-arrow-right"></i></span>
            </div>
          </router-link>

          <!-- Card 2: 反应焓变 -->
          <router-link to="/scene/thermodynamics/tool/enthalpy" class="tool-card">
            <div class="card-header">
              <div class="card-icon">
                <i class="fas fa-chart-line"></i>
              </div>
              <h3 class="card-title">反应焓变</h3>
            </div>
            <div class="card-body">
              <p class="card-desc">
                计算标准反应焓变，判断反应放热/吸热特性
              </p>
              <div class="card-metrics">
                <span class="metric-item">
                  <i class="fas fa-check-circle"></i>
                  计算 ΔH°
                </span>
                <span class="metric-item">
                  <i class="fas fa-check-circle"></i>
                  放热/吸热
                </span>
              </div>
            </div>
            <div class="card-footer">
              <span class="card-btn">进入工具 <i class="fas fa-arrow-right"></i></span>
            </div>
          </router-link>

          <!-- Card 3: 平衡常数 -->
          <router-link to="/scene/thermodynamics/tool/equilibrium" class="tool-card">
            <div class="card-header">
              <div class="card-icon">
                <i class="fas fa-balance-scale"></i>
              </div>
              <h3 class="card-title">平衡常数</h3>
            </div>
            <div class="card-body">
              <p class="card-desc">
                计算反应平衡常数 K，分析反应平衡状态
              </p>
              <div class="card-metrics">
                <span class="metric-item">
                  <i class="fas fa-check-circle"></i>
                  计算 K 值
                </span>
                <span class="metric-item">
                  <i class="fas fa-check-circle"></i>
                  温度相关
                </span>
              </div>
            </div>
            <div class="card-footer">
              <span class="card-btn">进入工具 <i class="fas fa-arrow-right"></i></span>
            </div>
          </router-link>

          <!-- Card 4: 反应方向 -->
          <router-link to="/scene/thermodynamics/tool/direction" class="tool-card">
            <div class="card-header">
              <div class="card-icon">
                <i class="fas fa-arrow-right"></i>
              </div>
              <h3 class="card-title">反应方向</h3>
            </div>
            <div class="card-body">
              <p class="card-desc">
                结合温度判断反应自发方向，计算分解温度
              </p>
              <div class="card-metrics">
                <span class="metric-item">
                  <i class="fas fa-check-circle"></i>
                  自发方向
                </span>
                <span class="metric-item">
                  <i class="fas fa-check-circle"></i>
                  分解温度
                </span>
              </div>
            </div>
            <div class="card-footer">
              <span class="card-btn">进入工具 <i class="fas fa-arrow-right"></i></span>
            </div>
          </router-link>
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
  name: "SceneThermodynamics",
  components: {
    Header,
    Footer,
  },
};
</script>

<style scoped>
/* ==================== 基础样式 ==================== */
.scene-thermodynamics {
  background-color: #f5f7fa;
  min-height: 100vh;
  font-family: "Microsoft YaHei", "PingFang SC", "Helvetica Neue", Arial, sans-serif;
  padding-top: 80px;
}

.container {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 15px;
}

/* ==================== 面包屑 ==================== */
.mb-nav {
  background: linear-gradient(180deg, #0a1628 0%, #0f1f3a 100%);
  padding: 14px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
}

.mb-nav p {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.5);
  margin: 0;
}

.mb-nav a {
  color: rgba(255, 255, 255, 0.6);
  text-decoration: none;
  transition: color 0.25s;
}

.mb-nav a:hover {
  color: #5a8eff;
}

.sep {
  margin: 0 8px;
  color: rgba(255, 255, 255, 0.25);
  font-size: 12px;
}

.current {
  color: #5a8eff;
  font-weight: 500;
}

/* ==================== Hero 区域 ==================== */
.hero-section {
  background: linear-gradient(135deg, #0a1628 0%, #002a67 40%, #0046db 100%);
  padding: 64px 0 56px;
  position: relative;
  overflow: hidden;
}

.hero-bg-pattern {
  position: absolute;
  top: -30%;
  right: -10%;
  width: 600px;
  height: 600px;
  background: radial-gradient(circle, rgba(0, 70, 219, 0.25) 0%, transparent 65%);
  border-radius: 50%;
  pointer-events: none;
}

.hero-bg-pattern::after {
  content: "";
  position: absolute;
  bottom: -40%;
  left: -20%;
  width: 450px;
  height: 450px;
  background: radial-gradient(circle, rgba(90, 142, 255, 0.12) 0%, transparent 70%);
  border-radius: 50%;
}

.hero-content {
  position: relative;
  z-index: 1;
  text-align: center;
}

.hero-tag {
  display: inline-block;
  padding: 4px 14px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 20px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.75);
  letter-spacing: 1px;
  margin-bottom: 18px;
  backdrop-filter: blur(4px);
}

.hero-title {
  font-size: 34px;
  color: #fff;
  margin: 0 0 14px;
  font-weight: 700;
  letter-spacing: 2px;
}

.hero-desc {
  font-size: 15px;
  color: rgba(255, 255, 255, 0.75);
  margin: 0 auto;
  max-width: 620px;
  line-height: 1.7;
}

/* ==================== 主内容区域 ==================== */
.main-section {
  padding: 44px 0 80px;
}

/* ==================== 区域标题栏 ==================== */
.section-title-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 28px;
  padding-bottom: 16px;
  border-bottom: 2px solid #e8edf4;
}

.section-title {
  font-size: 20px;
  color: #1a1a2e;
  margin: 0;
  font-weight: 600;
}

.section-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 28px;
  height: 24px;
  padding: 0 8px;
  background: #e8f0fe;
  color: #0046db;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 600;
}

/* ==================== 2x2 网格 ==================== */
.tools-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

/* ==================== 工具卡片 ==================== */
.tool-card {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  text-decoration: none;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: all 0.35s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  cursor: pointer;
}

.tool-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 70, 219, 0.12);
}

/* ==================== 卡片头部 ==================== */
.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px 24px;
  background: #e8f0fe;
  border-bottom: 1px solid rgba(0, 70, 219, 0.06);
  position: relative;
}

.card-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: linear-gradient(135deg, #0046db 0%, #2066fc 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  color: #fff;
  flex-shrink: 0;
  transition: transform 0.3s;
}

.tool-card:hover .card-icon {
  transform: scale(1.08);
}

.card-title {
  font-size: 18px;
  color: #1a1a2e;
  margin: 0;
  font-weight: 600;
  flex: 1;
}

.card-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.5px;
  flex-shrink: 0;
}

.badge-recommend {
  background: #fff1f0;
  color: #cf1322;
  border: 1px solid rgba(207, 19, 34, 0.12);
}

/* ==================== 卡片主体 ==================== */
.card-body {
  padding: 20px 24px;
  flex: 1;
}

.card-desc {
  font-size: 14px;
  color: #666;
  margin: 0 0 16px;
  line-height: 1.6;
}

.card-metrics {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.metric-item {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 13px;
  color: #888;
  padding: 4px 12px;
  background: #f7f9fc;
  border-radius: 6px;
  border: 1px solid #eef1f6;
}

.metric-item i {
  color: #0046db;
  font-size: 11px;
}

/* ==================== 卡片底部按钮 ==================== */
.card-footer {
  padding: 0 24px 20px;
}

.card-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 20px;
  background: #0046db;
  color: #fff;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.3s;
  width: 100%;
  justify-content: center;
}

.card-btn i {
  transition: transform 0.3s;
  font-size: 13px;
}

.tool-card:hover .card-btn i {
  transform: translateX(4px);
}

.tool-card:hover .card-btn {
  background: #0033a0;
  box-shadow: 0 4px 14px rgba(0, 70, 219, 0.3);
}

/* ==================== 响应式 ==================== */
@media (max-width: 1200px) {
  .container {
    max-width: 960px;
  }

  .hero-title {
    font-size: 30px;
  }

  .hero-section {
    padding: 54px 0 46px;
  }
}

@media (max-width: 992px) {
  .tools-grid {
    grid-template-columns: 1fr;
    max-width: 520px;
    margin: 0 auto;
  }

  .main-section {
    padding: 36px 0 60px;
  }
}

@media (max-width: 768px) {
  .hero-section {
    padding: 44px 0 36px;
  }

  .hero-title {
    font-size: 26px;
  }

  .hero-desc {
    font-size: 14px;
  }

  .hero-tag {
    font-size: 11px;
    margin-bottom: 14px;
  }

  .section-title {
    font-size: 18px;
  }

  .section-title-bar {
    margin-bottom: 22px;
    padding-bottom: 14px;
  }

  .card-header {
    padding: 16px 20px;
  }

  .card-body {
    padding: 16px 20px;
  }

  .card-footer {
    padding: 0 20px 18px;
  }

  .tools-grid {
    gap: 20px;
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
    padding: 36px 0 30px;
  }

  .card-icon {
    width: 36px;
    height: 36px;
    font-size: 16px;
  }

  .card-title {
    font-size: 16px;
  }

  .card-desc {
    font-size: 13px;
  }

  .card-btn {
    padding: 9px 16px;
    font-size: 13px;
  }

  .metric-item {
    font-size: 12px;
    padding: 3px 10px;
  }
}
</style>
