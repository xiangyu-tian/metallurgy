<template>
  <Header />
  <div class="page-wrapper">
    <!-- Breadcrumb -->
    <div class="mb-nav">
      <div class="container">
        <p>当前位置：<router-link to="/">首页</router-link> &gt; <router-link to="/">智能场景</router-link> &gt; <span>仿真与工单协同</span></p>
      </div>
    </div>

    <!-- Hero -->
    <div class="hero-section">
      <div class="hero-overlay"></div>
      <div class="container hero-content">
        <h1 class="hero-title">仿真与工单协同</h1>
        <p class="hero-desc">基于工艺场景生成标准化操作工单，评估生产风险，推荐最优工艺参数</p>
      </div>
    </div>

    <!-- Tool Cards -->
    <div class="main-section">
      <div class="container">
        <div class="section-title">
          <h2>选择工具</h2>
          <p>点击进入对应的仿真与工单工具</p>
        </div>
        <div class="cards-grid">
          <!-- Card 1: 操作工单生成 -->
          <router-link to="/scene/simulation/tool/work-order" class="tool-card">
            <div class="card-header">
              <div class="card-icon"><i class="fas fa-clipboard-list"></i></div>
              <div class="card-header-text">
                <h3>操作工单生成</h3>
                <span class="card-badge">自动化</span>
              </div>
            </div>
            <div class="card-body">
              <p class="card-desc">根据工艺场景自动生成标准化操作工单，包含详细操作步骤和注意事项</p>
              <div class="card-metrics">
                <div class="metric-item">
                  <span class="metric-value">标准化工单</span>
                  <span class="metric-label">输出格式</span>
                </div>
                <div class="metric-divider"></div>
                <div class="metric-item">
                  <span class="metric-value">操作步骤</span>
                  <span class="metric-label">核心内容</span>
                </div>
              </div>
            </div>
            <div class="card-footer">
              <span class="card-link">进入工具 <i class="fas fa-arrow-right"></i></span>
            </div>
          </router-link>

          <!-- Card 2: 风险评估 -->
          <router-link to="/scene/simulation/tool/risk" class="tool-card">
            <div class="card-header">
              <div class="card-icon"><i class="fas fa-shield-alt"></i></div>
              <div class="card-header-text">
                <h3>风险评估</h3>
                <span class="card-badge card-badge-accent">预警</span>
              </div>
            </div>
            <div class="card-body">
              <p class="card-desc">评估生产工艺风险等级，量化风险概率，提供预警信息和防控建议</p>
              <div class="card-metrics">
                <div class="metric-item">
                  <span class="metric-value">风险等级</span>
                  <span class="metric-label">综合评定</span>
                </div>
                <div class="metric-divider"></div>
                <div class="metric-item">
                  <span class="metric-value">概率量化</span>
                  <span class="metric-label">数据驱动</span>
                </div>
              </div>
            </div>
            <div class="card-footer">
              <span class="card-link">进入工具 <i class="fas fa-arrow-right"></i></span>
            </div>
          </router-link>

          <!-- Card 3: 参数推荐 -->
          <router-link to="/scene/simulation/tool/params" class="tool-card">
            <div class="card-header">
              <div class="card-icon"><i class="fas fa-sliders-h"></i></div>
              <div class="card-header-text">
                <h3>参数推荐</h3>
                <span class="card-badge">优化</span>
              </div>
            </div>
            <div class="card-body">
              <p class="card-desc">基于场景类型推荐最优工艺参数，包括温度、压力、时长等关键指标</p>
              <div class="card-metrics">
                <div class="metric-item">
                  <span class="metric-value">最优参数</span>
                  <span class="metric-label">智能匹配</span>
                </div>
                <div class="metric-divider"></div>
                <div class="metric-item">
                  <span class="metric-value">工艺优化</span>
                  <span class="metric-label">持续改进</span>
                </div>
              </div>
            </div>
            <div class="card-footer">
              <span class="card-link">进入工具 <i class="fas fa-arrow-right"></i></span>
            </div>
          </router-link>
        </div>
      </div>
    </div>
  </div>
  <Footer />
</template>

<script>
import Header from '@/components/Header.vue';
import Footer from '@/components/Footer.vue';
export default { name: 'SceneSimulation', components: { Header, Footer } };
</script>

<style scoped>
.page-wrapper { padding-top: 80px; min-height: 100vh; background: #f5f7fa; }

/* Breadcrumb */
.mb-nav { background: rgba(0,22,58,0.6); border-bottom: 1px solid rgba(0,70,219,0.15); }
.mb-nav p { font-size: 14px; padding: 14px 0; color: rgba(255,255,255,0.5); margin: 0; }
.mb-nav a { color: rgba(255,255,255,0.6); text-decoration: none; transition: color 0.3s; }
.mb-nav a:hover { color: #0046DB; }
.mb-nav span { color: #fff; }

/* Hero */
.hero-section { position: relative; height: 260px; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #0a1628 0%, #002a67 40%, #0046DB 100%); }
.hero-overlay { position: absolute; inset: 0; background: linear-gradient(135deg, rgba(0,22,58,0.88), rgba(0,70,219,0.6), rgba(0,22,58,0.85)); }
.hero-content { position: relative; z-index: 1; text-align: center; }
.hero-title { font-size: 36px; font-weight: 700; color: #fff; margin: 0 0 12px; letter-spacing: 3px; }
.hero-desc { font-size: 18px; color: rgba(255,255,255,0.75); max-width: 600px; margin: 0 auto; line-height: 1.6; }

/* Main Section */
.main-section { padding: 60px 0 100px; }
.section-title { text-align: center; margin-bottom: 50px; }
.section-title h2 { font-size: 28px; color: #333; margin: 0 0 10px; }
.section-title p { font-size: 16px; color: #666; margin: 0; }

/* Cards Grid */
.cards-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 30px; max-width: 1100px; margin: 0 auto; }

/* Tool Card */
.tool-card {
  display: flex; flex-direction: column; text-decoration: none; background: #fff;
  border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  border: 1px solid #f0f0f0; overflow: hidden;
  transition: all 0.3s ease; cursor: pointer;
}
.tool-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 28px rgba(0,70,219,0.2);
  border-color: #0046DB;
}

/* Card Header */
.card-header {
  display: flex; align-items: center; gap: 14px;
  padding: 20px 24px; background: #E8F0FE;
  border-bottom: 1px solid rgba(0,70,219,0.08);
}
.card-icon {
  width: 48px; height: 48px; border-radius: 12px;
  background: #0046DB; display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.card-icon i { font-size: 22px; color: #fff; }
.card-header-text { display: flex; flex-direction: column; gap: 4px; min-width: 0; }
.card-header-text h3 { font-size: 18px; color: #0046DB; margin: 0; font-weight: 600; }
.card-badge {
  display: inline-block; align-self: flex-start; font-size: 11px; font-weight: 600;
  padding: 2px 10px; border-radius: 10px; background: rgba(0,70,219,0.12); color: #0046DB;
  letter-spacing: 0.5px;
}
.card-badge-accent { background: rgba(245,158,11,0.15); color: #B45309; }

/* Card Body */
.card-body { padding: 20px 24px; flex: 1; display: flex; flex-direction: column; gap: 18px; }
.card-desc { font-size: 14px; color: #666; margin: 0; line-height: 1.7; }

/* Metrics */
.card-metrics { display: flex; align-items: center; gap: 16px; padding: 14px 16px; background: #f8faff; border-radius: 10px; border: 1px solid #e8f0fe; }
.metric-item { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 2px; }
.metric-value { font-size: 14px; font-weight: 600; color: #0046DB; }
.metric-label { font-size: 11px; color: #999; }
.metric-divider { width: 1px; height: 28px; background: #e0e8f0; }

/* Card Footer */
.card-footer {
  padding: 16px 24px; border-top: 1px solid #f0f0f0;
  display: flex; justify-content: flex-end;
}
.card-link {
  font-size: 14px; color: #0046DB; font-weight: 500;
  display: inline-flex; align-items: center; gap: 6px;
  transition: all 0.3s;
}
.card-link i { font-size: 13px; transition: transform 0.3s; }
.tool-card:hover .card-link i { transform: translateX(4px); }

/* Responsive */
@media (max-width: 992px) { .cards-grid { grid-template-columns: 1fr; max-width: 480px; } }
@media (max-width: 768px) { .hero-title { font-size: 26px; } .hero-section { height: 200px; } }
</style>
