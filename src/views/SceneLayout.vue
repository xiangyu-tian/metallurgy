<template>
  <Header />
  <div class="scene-layout">
    <!-- Breadcrumb -->
    <div class="mb-nav">
      <div class="container">
        <p>当前位置：<router-link to="/">首页</router-link> &gt; <span>智能场景</span></p>
      </div>
    </div>

    <div class="container main-section">
      <!-- Left Sidebar -->
      <aside class="sidebar">
        <div class="sidebar-header">场景导航</div>
        <nav class="sidebar-nav">
          <div
            v-for="scene in scenes"
            :key="scene.id"
            class="nav-item"
            :class="{ active: activeScene === scene.id }"
            @click="activeScene = scene.id"
          >
            <i :class="['fas', scene.icon]" :style="{ color: scene.color }"></i>
            <span>{{ scene.name }}</span>
          </div>
        </nav>
      </aside>

      <!-- Right Content -->
      <main class="content">
        <!-- Scene header -->
        <div class="scene-header">
          <div class="scene-info">
            <h2>{{ currentScene.name }}</h2>
            <p>{{ currentScene.desc }}</p>
          </div>
        </div>

        <!-- Tool cards grid -->
        <div class="tools-grid">
          <div v-for="tool in currentScene.tools" :key="tool.id" class="tool-card">
            <div class="card-header">
              <div class="card-icon" :style="{ background: currentScene.color }">
                <i :class="['fas', tool.icon]"></i>
              </div>
              <div class="card-title-group">
                <h3>{{ tool.name }}</h3>
                <span v-if="tool.badge" class="badge">{{ tool.badge }}</span>
              </div>
            </div>
            <div class="card-body">
              <p class="card-desc">{{ tool.desc }}</p>
              <ul class="feature-list">
                <li v-for="f in tool.features" :key="f"><i class="fas fa-check-circle"></i> {{ f }}</li>
              </ul>
              <div class="usage-hint">
                <i class="fas fa-lightbulb"></i> {{ tool.usage }}
              </div>
            </div>
            <div class="card-footer">
              <a v-if="tool.external" :href="tool.route" target="_blank" class="btn-use">打开系统 <i class="fas fa-external-link-alt"></i></a>
              <router-link v-else :to="tool.route" class="btn-use">立即使用 <i class="fas fa-arrow-right"></i></router-link>
            </div>
          </div>
        </div>
      </main>
    </div>
  </div>
  <Footer />
</template>

<script>
import Header from '@/components/Header.vue';
import Footer from '@/components/Footer.vue';

const sceneData = {
  thermodynamics: {
    id: 'thermodynamics', name: '热力学推理', icon: 'fa-fire', color: '#0046DB',
    desc: '基于热化学数据库进行冶金反应热力学计算与分析',
    tools: [
      { id: 'delta-g', name: 'ΔG 计算', icon: 'fa-fire', route: '/scene/thermodynamics/tool/delta-g', badge: '推荐',
        desc: '计算冶金反应的吉布斯自由能变化，判断反应自发性方向',
        features: ['支持 10 种常见冶金反应', '自动计算 ΔG / K / 反应方向'], usage: '选择反应式 → 输入温度 → 查看结果' },
      { id: 'enthalpy', name: '反应焓变', icon: 'fa-chart-line', route: '/scene/thermodynamics/tool/enthalpy',
        desc: '计算标准反应焓变，判断反应放热或吸热特性',
        features: ['基于标准热化学数据', '自动判断反应热效应'], usage: '选择反应式 → 查看 ΔH° 和反应类型' },
      { id: 'equilibrium', name: '平衡常数', icon: 'fa-balance-scale', route: '/scene/thermodynamics/tool/equilibrium',
        desc: '计算反应平衡常数 K，分析反应平衡状态',
        features: ['温度可调', '同时计算 ΔG 和 K'], usage: '选择反应式 → 输入温度 → 查看平衡常数' },
      { id: 'direction', name: '反应方向', icon: 'fa-arrow-right', route: '/scene/thermodynamics/tool/direction',
        desc: '结合温度判断反应自发方向，计算分解温度',
        features: ['温度相关分析', '支持 CaCO₃ 分解温度计算'], usage: '选择反应式 → 输入温度 → 判断方向' }
    ]
  },
  converter: {
    id: 'converter', name: '转炉炼钢工艺优化', icon: 'fa-bullseye', color: '#E53935',
    desc: '基于工艺参数预测转炉冶炼终点，优化冶炼过程',
    tools: [
      { id: 'endpoint', name: '终点预测', icon: 'fa-bullseye', route: '/scene/converter/tool/endpoint', badge: '热门',
        desc: '根据铁水成分和工艺参数预测转炉终点碳含量和温度',
        features: ['预测终点碳和温度', '计算氧耗和渣碱度'], usage: '输入 Si/温度/氧流量 → 开始预测' },
      { id: 'oxygen', name: '氧耗计算', icon: 'fa-gauge-high', route: '/scene/converter/tool/oxygen',
        desc: '计算转炉冶炼过程所需氧气消耗量',
        features: ['基于 Si 和碳含量计算', '优化氧枪制度'], usage: '输入 Si 和碳含量 → 计算氧耗' },
      { id: 'temperature', name: '温度预测', icon: 'fa-temperature-high', route: '/scene/converter/tool/temperature',
        desc: '预测转炉终点钢水温度，辅助温控决策',
        features: ['考虑 Si 和碳影响', '评估温降'], usage: '输入 Si/碳/温度 → 预测终点温度' },
      { id: 'slag', name: '渣碱度计算', icon: 'fa-flask', route: '/scene/converter/tool/slag',
        desc: '计算炉渣碱度，优化造渣制度',
        features: ['计算碱度 R', '推荐石灰用量'], usage: '输入 Si 含量 → 计算渣碱度' }
    ]
  },
  blastfurnace: {
    id: 'blastfurnace', name: '高炉低碳运行分析', icon: 'fa-leaf', color: '#40C057',
    desc: '评估高炉碳排放与能效水平，分析降碳潜力',
    tools: [
      { id: 'carbon', name: '碳排放核算', icon: 'fa-leaf', route: '/scene/blastfurnace/tool/carbon', badge: '核心',
        desc: '核算高炉冶炼过程碳排放量和碳排放强度',
        features: ['计算日碳排放量', '对比行业基准'], usage: '输入焦比/煤比/产量 → 核算碳排放' },
      { id: 'efficiency', name: '能效评估', icon: 'fa-bolt', route: '/scene/blastfurnace/tool/efficiency',
        desc: '评估高炉能源利用效率，分析节能潜力',
        features: ['综合能效评分', '能效等级判定'], usage: '输入焦比/煤比 → 评估能效' },
      { id: 'reduction', name: '降碳潜力', icon: 'fa-arrow-down', route: '/scene/blastfurnace/tool/reduction',
        desc: '对比行业基准，评估降碳空间和潜力',
        features: ['对比行业基准', '量化降碳目标'], usage: '输入焦比/煤比/产量 → 分析潜力' },
      { id: 'utilization', name: '碳利用效率', icon: 'fa-recycle', route: '/scene/blastfurnace/tool/utilization',
        desc: '计算碳素利用效率，优化燃料配比',
        features: ['碳效率计算', '行业标杆对比'], usage: '输入焦比 → 计算利用率' }
    ]
  },
  casting: {
    id: 'casting', name: '连铸质量辅助决策', icon: 'fa-star', color: '#7C3AED',
    desc: '基于工艺参数智能评估连铸坯质量，优化生产工艺',
    tools: [
      { id: 'quality', name: '质量综合评分', icon: 'fa-star', route: '/scene/casting/tool/quality',
        desc: '基于工艺参数综合评估连铸坯质量等级',
        features: ['综合质量评分', '优化建议'], usage: '输入钢种/断面/拉速/过热度 → 评分' },
      { id: 'segregation', name: '偏析预测', icon: 'fa-chart-line', route: 'http://localhost:8001', badge: '推荐',
        desc: '基于机器学习模型的连铸圆坯偏析预测系统',
        features: ['真实 ML 模型预测', '碳极差 + 偏析指数', '可视化图表展示'], usage: '打开独立预测系统进行操作', external: true },
      { id: 'crack', name: '表面裂纹预测', icon: 'fa-exclamation-triangle', route: '/scene/casting/tool/crack',
        desc: '评估铸坯表面裂纹风险等级',
        features: ['裂纹指数计算', '风险等级判定'], usage: '输入钢种/拉速/过热度 → 风险评估' },
      { id: 'porosity', name: '中心疏松预测', icon: 'fa-circle', route: '/scene/casting/tool/porosity',
        desc: '预测铸坯中心疏松程度',
        features: ['疏松指数', '严重程度判定'], usage: '输入钢种/拉速/过热度 → 疏松评估' }
    ]
  },
  simulation: {
    id: 'simulation', name: '仿真与工单协同', icon: 'fa-clipboard-list', color: '#F59E0B',
    desc: '生成标准化操作工单，评估生产风险，推荐工艺参数',
    tools: [
      { id: 'work-order', name: '操作工单生成', icon: 'fa-clipboard-list', route: '/scene/simulation/tool/work-order', badge: '自动化',
        desc: '根据工艺场景自动生成标准化操作工单',
        features: ['详细操作步骤', '风险与优先级标注'], usage: '输入场景/设备/时长 → 生成工单' },
      { id: 'risk', name: '风险评估', icon: 'fa-shield-alt', route: '/scene/simulation/tool/risk', badge: '预警',
        desc: '评估生产工艺风险等级，量化风险概率',
        features: ['风险等级判定', '概率量化'], usage: '输入场景/设备 → 评估风险' },
      { id: 'params', name: '参数推荐', icon: 'fa-sliders-h', route: '/scene/simulation/tool/params', badge: '优化',
        desc: '基于场景类型推荐最优工艺参数',
        features: ['推荐温度/压力/时长', '场景匹配'], usage: '输入场景 → 获取推荐参数' }
    ]
  }
};

export default {
  name: 'SceneLayout',
  components: { Header, Footer },
  data() { return { activeScene: 'thermodynamics', scenes: Object.values(sceneData) } },
  computed: {
    currentScene() { return sceneData[this.activeScene] || sceneData.thermodynamics; }
  }
};
</script>

<style scoped>
.scene-layout { padding-top: 80px; min-height: 100vh; background: #f5f7fa; }
.mb-nav { background: rgba(0,22,58,0.6); border-bottom: 1px solid rgba(0,70,219,0.15); }
.mb-nav p { font-size: 14px; padding: 14px 0; color: rgba(255,255,255,0.5); margin: 0; }
.mb-nav a { color: rgba(255,255,255,0.6); text-decoration: none; }
.mb-nav a:hover { color: #0046DB; }
.mb-nav span { color: #fff; }
.main-section { display: flex; gap: 28px; padding: 32px 0 80px; align-items: flex-start; }

/* Sidebar */
.sidebar { width: 220px; flex-shrink: 0; background: #fff; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); overflow: hidden; position: sticky; top: 112px; }
.sidebar-header { padding: 16px 20px; font-size: 15px; font-weight: 600; color: #333; background: #E8F0FE; border-bottom: 1px solid rgba(0,70,219,0.08); }
.sidebar-nav { padding: 8px; }
.nav-item { display: flex; align-items: center; gap: 10px; padding: 12px 14px; border-radius: 8px; cursor: pointer; transition: all 0.2s; margin-bottom: 2px; }
.nav-item:hover { background: #f0f4ff; }
.nav-item.active { background: #E8F0FE; font-weight: 600; }
.nav-item i { font-size: 16px; width: 20px; text-align: center; }
.nav-item span { font-size: 14px; color: #333; }

/* Content */
.content { flex: 1; min-width: 0; }
.scene-header { margin-bottom: 28px; }
.scene-header h2 { font-size: 22px; color: #333; margin: 0 0 6px; }
.scene-header p { font-size: 14px; color: #666; margin: 0; }

/* Tool cards grid */
.tools-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; }

/* Card */
.tool-card { background: #fff; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); border: 1px solid #f0f0f0; overflow: hidden; transition: all 0.3s; display: flex; flex-direction: column; }
.tool-card:hover { transform: translateY(-4px); box-shadow: 0 8px 24px rgba(0,70,219,0.12); border-color: #0046DB; }

/* Card Header */
.card-header { display: flex; align-items: center; gap: 14px; padding: 18px 20px; background: #E8F0FE; border-bottom: 1px solid rgba(0,70,219,0.08); }
.card-icon { width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.card-icon i { font-size: 18px; color: #fff; }
.card-title-group { display: flex; align-items: center; gap: 8px; min-width: 0; }
.card-title-group h3 { font-size: 16px; color: #1a2744; margin: 0; font-weight: 600; }
.badge { font-size: 11px; font-weight: 600; padding: 2px 10px; border-radius: 10px; background: #FF6B6B; color: #fff; letter-spacing: 0.5px; flex-shrink: 0; }

/* Card Body */
.card-body { padding: 18px 20px; flex: 1; display: flex; flex-direction: column; gap: 14px; }
.card-desc { font-size: 13px; color: #666; margin: 0; line-height: 1.6; }
.feature-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 6px; }
.feature-list li { font-size: 13px; color: #085041; display: flex; align-items: center; gap: 6px; }
.feature-list li i { color: #40C057; font-size: 12px; }
.usage-hint { font-size: 12px; color: #633806; background: #FAEEDA; border: 1px solid rgba(133,79,11,0.15); border-radius: 6px; padding: 8px 12px; display: flex; align-items: center; gap: 6px; line-height: 1.4; }
.usage-hint i { color: #EF9F27; flex-shrink: 0; }

/* Card Footer */
.card-footer { padding: 14px 20px; border-top: 1px solid #f0f0f0; }
.btn-use { display: inline-flex; align-items: center; gap: 6px; padding: 8px 20px; background: #0046DB; color: #fff; border-radius: 8px; font-size: 14px; font-weight: 500; text-decoration: none; transition: all 0.3s; }
.btn-use:hover { background: #0038b3; box-shadow: 0 4px 12px rgba(0,70,219,0.3); }
.btn-use i { font-size: 12px; transition: transform 0.3s; }
.tool-card:hover .btn-use i { transform: translateX(4px); }

/* Responsive */
@media (max-width: 992px) { .main-section { flex-direction: column; } .sidebar { width: 100%; position: static; } .sidebar-nav { display: flex; flex-wrap: wrap; gap: 4px; } .nav-item { flex: 1; min-width: 120px; justify-content: center; } }
@media (max-width: 768px) { .tools-grid { grid-template-columns: 1fr; } }
</style>
