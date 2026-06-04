<template>
  <Header></Header>
  <div class="steel-metallurgy">
    <!-- 面包屑导航 -->
    <div class="mb-nav">
      <div class="container">
        <p>
          当前位置： <router-link to="/">首页</router-link> >
          <span>钢铁冶金</span>
        </p>
      </div>
    </div>

    <!-- ==================== Hero 区域 ==================== -->
    <section class="hero-section">
      <div class="hero-overlay"></div>
      <div class="container hero-content">
        <div class="hero-text">
          <h1>钢铁冶金全流程技术</h1>
          <p class="hero-subtitle">Iron and Steel Metallurgy Process Technology</p>
          <p class="hero-desc">
            从铁矿石到高性能钢材，涵盖长流程、短流程、连铸及轧钢热处理等核心工艺，
            提供全面的钢铁冶金技术数据库与工艺优化方案。
          </p>
          <div class="hero-stats">
            <div class="hero-stat-item">
              <span class="hero-stat-value">10.13亿</span>
              <span class="hero-stat-label">年钢产量（吨）</span>
            </div>
            <div class="hero-stat-divider"></div>
            <div class="hero-stat-item">
              <span class="hero-stat-value">56%</span>
              <span class="hero-stat-label">长流程占比</span>
            </div>
            <div class="hero-stat-divider"></div>
            <div class="hero-stat-item">
              <span class="hero-stat-value">44%</span>
              <span class="hero-stat-label">短流程占比（目标）</span>
            </div>
          </div>
        </div>
        <div class="hero-visual">
          <div class="process-flow">
            <div class="flow-node" v-for="(node, index) in flowNodes" :key="index">
              <div class="flow-icon">
                <i :class="node.icon"></i>
              </div>
              <div class="flow-label">{{ node.label }}</div>
              <div class="flow-arrow" v-if="index < flowNodes.length - 1">
                <i class="fas fa-chevron-right"></i>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ==================== 主内容区域 ==================== -->
    <div class="container main-content">

      <!-- ==================== 行业概览 ==================== -->
      <section class="overview-section">
        <div class="section-header-center">
          <h2><i class="fas fa-industry"></i> 钢铁冶金行业概览</h2>
          <p>中国钢铁工业现状与关键指标一览</p>
        </div>

        <div class="stats-grid">
          <div class="stat-card" v-for="stat in industryStats" :key="stat.id">
            <div class="stat-icon-wrapper">
              <i :class="stat.icon"></i>
            </div>
            <div class="stat-info">
              <div class="stat-number">{{ stat.value }}</div>
              <div class="stat-label">{{ stat.label }}</div>
              <div class="stat-desc">{{ stat.description }}</div>
            </div>
          </div>
        </div>
      </section>

      <!-- ==================== 关键技术 ==================== -->
      <section class="technology-section">
        <div class="section-header-center">
          <h2><i class="fas fa-cogs"></i> 核心工艺技术</h2>
          <p>钢铁生产的四大关键工艺环节与技术解析</p>
        </div>

        <!-- 技术卡片列表 -->
        <div class="tech-cards">
          <div class="tech-card" v-for="(process, index) in steelProcesses" :key="process.id">
            <div class="tech-card-inner">
              <div class="tech-number">{{ String(index + 1).padStart(2, '0') }}</div>
              <div class="tech-icon-wrapper" :style="{ backgroundColor: process.accentColor + '15' }">
                <i :class="process.icon" :style="{ color: process.accentColor }"></i>
              </div>
              <h3 class="tech-title">{{ process.title }}</h3>
              <p class="tech-subtitle">{{ process.subtitle }}</p>
              <p class="tech-desc">{{ process.description }}</p>

              <div class="tech-params">
                <div class="tech-param" v-for="param in process.params" :key="param.label">
                  <span class="param-label">{{ param.label }}</span>
                  <span class="param-value">{{ param.value }}</span>
                </div>
              </div>

              <div class="tech-flow" v-if="process.flowSteps">
                <div class="flow-title">工艺流程</div>
                <div class="flow-steps">
                  <span class="flow-step" v-for="(step, sIndex) in process.flowSteps" :key="sIndex">
                    {{ step }}<span class="flow-sep" v-if="sIndex < process.flowSteps.length - 1"><i class="fas fa-arrow-right"></i></span>
                  </span>
                </div>
              </div>

              <div class="tech-features">
                <div class="tech-feature" v-for="feature in process.features" :key="feature">
                  <i class="fas fa-check-circle" :style="{ color: process.accentColor }"></i>
                  <span>{{ feature }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- ==================== 行业数据 ==================== -->
      <section class="data-section">
        <div class="section-header-center">
          <h2><i class="fas fa-chart-bar"></i> 行业关键数据</h2>
          <p>钢铁冶金行业核心工艺参数与统计数据</p>
        </div>

        <div class="data-table-wrapper">
          <table class="data-table">
            <thead>
              <tr>
                <th>工艺指标</th>
                <th>长流程 (BF-BOF)</th>
                <th>短流程 (EAF)</th>
                <th>行业平均水平</th>
                <th>国际先进水平</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in comparisonData" :key="row.label">
                <td class="row-label">{{ row.label }}</td>
                <td>{{ row.bfBof }}</td>
                <td>{{ row.eaf }}</td>
                <td>{{ row.industryAvg }}</td>
                <td>{{ row.international }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- ==================== 未来展望 ==================== -->
      <section class="outlook-section">
        <div class="section-header-center">
          <h2><i class="fas fa-rocket"></i> 未来展望</h2>
          <p>钢铁冶金技术发展趋势与绿色低碳转型方向</p>
        </div>

        <div class="outlook-grid">
          <div class="outlook-card" v-for="item in outlookItems" :key="item.id">
            <div class="outlook-icon">
              <i :class="item.icon"></i>
            </div>
            <h4>{{ item.title }}</h4>
            <p>{{ item.description }}</p>
            <div class="outlook-tag">{{ item.tag }}</div>
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
  name: "SteelMetallurgy",
  components: {
    Header,
    Footer,
  },
  data() {
    return {
      // Hero流程节点
      flowNodes: [
        { icon: 'fas fa-mountain', label: '采矿/选矿' },
        { icon: 'fas fa-fire', label: '炼铁' },
        { icon: 'fas fa-tint', label: '炼钢' },
        { icon: 'fas fa-layer-group', label: '连铸' },
        { icon: 'fas fa-cog', label: '轧钢' },
      ],

      // 行业统计数据
      industryStats: [
        {
          id: 1,
          icon: 'fas fa-weight-hanging',
          value: '10.13亿',
          label: '粗钢年产量',
          description: '2024年中国粗钢产量，全球第一'
        },
        {
          id: 2,
          icon: 'fas fa-building',
          value: '500+',
          label: '钢铁企业数量',
          description: '规模以上钢铁生产企业'
        },
        {
          id: 3,
          icon: 'fas fa-bolt',
          value: '550 kgce/t',
          label: '综合能耗',
          description: '重点统计钢铁企业平均吨钢综合能耗'
        },
        {
          id: 4,
          icon: 'fas fa-leaf',
          value: '1.8 tCO₂/t',
          label: '碳排放强度',
          description: '吨钢碳排放量，较2010年下降约20%'
        },
        {
          id: 5,
          icon: 'fas fa-users',
          value: '200万+',
          label: '从业人员',
          description: '钢铁行业直接从业人员数量'
        },
        {
          id: 6,
          icon: 'fas fa-globe',
          value: '57%',
          label: '全球占比',
          description: '中国粗钢产量占全球比例'
        },
      ],

      // 四大核心工艺
      steelProcesses: [
        {
          id: 'bf-bof',
          icon: 'fas fa-fire',
          accentColor: '#E53935',
          title: '高炉-转炉长流程',
          subtitle: 'BF-BOF Route',
          description: '以铁矿石、焦炭为主要原料，经高炉炼铁产生铁水，再经转炉吹氧炼钢的传统工艺路线。是目前我国最主要的钢铁生产方式，技术成熟、产量大，但碳排放强度较高。',
          params: [
            { label: '原料', value: '铁矿石+焦炭' },
            { label: '反应温度', value: '高炉>1500°C' },
            { label: '冶炼周期', value: '约6-8小时' },
            { label: '单炉产量', value: '100-300吨' },
            { label: '碳排强度', value: '约2.0 tCO₂/t' },
          ],
          flowSteps: ['烧结/球团', '高炉炼铁', '转炉炼钢', '炉外精炼', '连铸'],
          features: [
            '原料适应性广，适合大规模连续生产',
            '铁水质量稳定，杂质控制能力强',
            '余热余能回收利用空间大',
            '正在进行氢冶金低碳改造'
          ]
        },
        {
          id: 'eaf',
          icon: 'fas fa-bolt',
          accentColor: '#FB8C00',
          title: '电弧炉短流程',
          subtitle: 'EAF Route',
          description: '以废钢为原料，通过电弧炉熔化废钢进行冶炼的工艺路线。相比长流程投资少、建设周期短、碳排放低，是钢铁工业绿色低碳转型的重要方向。',
          params: [
            { label: '原料', value: '废钢+直接还原铁' },
            { label: '反应温度', value: '约1600°C' },
            { label: '冶炼周期', value: '约45-60分钟' },
            { label: '单炉产量', value: '50-150吨' },
            { label: '碳排强度', value: '约0.6 tCO₂/t' },
          ],
          flowSteps: ['废钢预处理', '电弧炉熔化', 'LF精炼', 'VD/VOD真空处理', '连铸'],
          features: [
            '碳排放仅为长流程的30%左右',
            '投资成本低，建设周期短',
            '废钢资源循环利用，符合循环经济',
            '灵活性高，适合多品种小批量生产'
          ]
        },
        {
          id: 'continuous-casting',
          icon: 'fas fa-layer-group',
          accentColor: '#0046DB',
          title: '连铸工艺',
          subtitle: 'Continuous Casting',
          description: '将冶炼合格的钢液通过连铸机直接浇注成各种断面形状的铸坯，省去传统的模铸-初轧开坯工序。连铸是现代钢铁生产的关键环节，直接影响最终产品质量。',
          params: [
            { label: '浇注温度', value: '1530-1580°C' },
            { label: '拉坯速度', value: '1.0-2.5 m/min' },
            { label: '铸坯断面', value: '150-300mm' },
            { label: '连浇炉数', value: '8-12炉' },
            { label: '收得率', value: '>98%' },
          ],
          flowSteps: ['中间罐', '结晶器', '扇形段', '拉矫机', '切割'],
          features: [
            '生产效率高，金属收得率比模铸提高10-15%',
            '铸坯质量均匀，内部缺陷少',
            '可实现全连铸生产，节能降耗',
            '配备电磁搅拌、动态轻压下等先进技术'
          ]
        },
        {
          id: 'rolling-heat-treatment',
          icon: 'fas fa-cog',
          accentColor: '#6A1B9A',
          title: '轧钢与热处理',
          subtitle: 'Rolling & Heat Treatment',
          description: '将连铸坯通过加热、轧制、冷却及热处理等工序，加工成具有特定形状、尺寸和性能的钢材产品。轧钢工艺决定了钢材的最终组织与性能，是钢铁生产的最后关键环节。',
          params: [
            { label: '加热温度', value: '1050-1250°C' },
            { label: '轧制速度', value: '最高120 m/s' },
            { label: '产品范围', value: '板/管/型/线材' },
            { label: '厚度精度', value: '±0.05mm' },
            { label: '屈服强度', value: '200-2000 MPa' },
          ],
          flowSteps: ['加热炉', '粗轧', '精轧', '层流冷却', '卷取/精整'],
          features: [
            '控轧控冷技术实现组织性能精确调控',
            '全自动厚度控制（AGC）确保尺寸精度',
            '板形控制（CVC/PC）技术成熟',
            '智能化热处理生产线，能耗降低15%以上'
          ]
        },
      ],

      // 对比数据
      comparisonData: [
        {
          label: '吨钢综合能耗 (kgce/t)',
          bfBof: '550-580',
          eaf: '280-320',
          industryAvg: '520',
          international: '510'
        },
        {
          label: '吨钢碳排放 (tCO₂/t)',
          bfBof: '1.8-2.2',
          eaf: '0.4-0.7',
          industryAvg: '1.6',
          international: '1.5'
        },
        {
          label: '金属收得率 (%)',
          bfBof: '92-95',
          eaf: '90-93',
          industryAvg: '93',
          international: '96'
        },
        {
          label: '吨钢耗新水 (m³/t)',
          bfBof: '2.5-3.5',
          eaf: '1.5-2.5',
          industryAvg: '2.8',
          international: '2.0'
        },
        {
          label: '固废利用率 (%)',
          bfBof: '95-98',
          eaf: '90-95',
          industryAvg: '94',
          international: '98'
        },
        {
          label: '吨钢投资成本 (元/t)',
          bfBof: '3000-4000',
          eaf: '1500-2500',
          industryAvg: '2800',
          international: '3500'
        },
      ],

      // 未来展望
      outlookItems: [
        {
          id: 1,
          icon: 'fas fa-atom',
          title: '氢基直接还原',
          description: '利用绿氢替代焦炭作为还原剂，从源头消除炼铁过程的碳排放。HYBRIT、Midrex等氢冶金技术已进入工业示范阶段。',
          tag: '低碳冶金'
        },
        {
          id: 2,
          icon: 'fas fa-robot',
          title: '智能化钢铁工厂',
          description: '基于工业互联网、数字孪生和AI技术的智能钢铁工厂，实现生产过程自主优化、质量在线预测和设备智能维护。',
          tag: '智能制造'
        },
        {
          id: 3,
          icon: 'fas fa-recycle',
          title: '循环经济模式',
          description: '构建钢铁与建材、化工、能源等行业的循环经济产业链，实现冶金渣、煤气、余热等副产物的高值化利用。',
          tag: '资源循环'
        },
        {
          id: 4,
          icon: 'fas fa-bolt',
          title: '全废钢电弧炉',
          description: '随着废钢积蓄量增加和绿电普及，全废钢电炉短流程将成为主流，配合连续装料和高效冶炼技术，实现近零碳排放。',
          tag: '绿色制造'
        },
        {
          id: 5,
          icon: 'fas fa-flask',
          title: 'CCUS碳捕集',
          description: '碳捕集、利用与封存技术在钢铁行业的规模化应用，与氢冶金协同，推动钢铁工业实现碳中和目标。',
          tag: '碳中和'
        },
        {
          id: 6,
          icon: 'fas fa-chart-line',
          title: '高性能钢铁材料',
          description: '开发新一代高强韧、轻量化、长寿命钢铁材料，服务于新能源汽车、航空航天、深海工程等战略性新兴产业。',
          tag: '材料创新'
        },
      ],
    };
  },
};
</script>

<style scoped>
/* ==================== 基础样式 ==================== */
.steel-metallurgy {
  background-color: #f5f7fa;
  min-height: 120vh;
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
  padding: 40px 0 60px;
  flex: 1;
}

/* ==================== 面包屑 ==================== */
.mb-nav {
  width: 100%;
  background-color: #fff;
  border-bottom: 1px solid #e8e8e8;
  line-height: 50px;
}

.mb-nav p {
  margin: 0;
  font-size: 14px;
  color: #666;
}

.mb-nav a {
  color: #666;
  text-decoration: none;
  transition: color 0.3s;
}

.mb-nav a:hover {
  color: #0046DB;
}

.mb-nav span {
  color: #0046DB;
  font-weight: 500;
}

/* ==================== Hero 区域 ==================== */
.hero-section {
  position: relative;
  background: linear-gradient(135deg, #0a1628 0%, #1a2a4a 30%, #0d2844 60%, #0a1628 100%);
  min-height: 400px;
  display: flex;
  align-items: center;
  overflow: hidden;
}

.hero-overlay {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse at 20% 50%, rgba(0, 70, 219, 0.15) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 50%, rgba(0, 180, 255, 0.1) 0%, transparent 50%),
    radial-gradient(ellipse at 50% 100%, rgba(229, 57, 53, 0.08) 0%, transparent 40%);
  pointer-events: none;
}

.hero-content {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 40px;
  align-items: center;
  padding: 60px 0;
}

.hero-text h1 {
  font-size: 36px;
  font-weight: 700;
  color: #fff;
  margin: 0 0 8px 0;
  letter-spacing: 2px;
}

.hero-subtitle {
  font-size: 18px;
  color: rgba(255, 255, 255, 0.6);
  margin: 0 0 20px 0;
  letter-spacing: 1px;
  font-weight: 300;
}

.hero-desc {
  font-size: 15px;
  color: rgba(255, 255, 255, 0.75);
  line-height: 1.8;
  margin: 0 0 32px 0;
  max-width: 540px;
}

.hero-stats {
  display: flex;
  align-items: center;
  gap: 24px;
}

.hero-stat-item {
  display: flex;
  flex-direction: column;
}

.hero-stat-value {
  font-size: 26px;
  font-weight: 700;
  color: #fff;
  line-height: 1.2;
}

.hero-stat-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.55);
  margin-top: 4px;
}

.hero-stat-divider {
  width: 1px;
  height: 40px;
  background: rgba(255, 255, 255, 0.2);
}

/* Hero 流程可视化 */
.hero-visual {
  display: flex;
  justify-content: center;
  align-items: center;
}

.process-flow {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
  justify-content: center;
}

.flow-node {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  position: relative;
}

.flow-icon {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: rgba(0, 70, 219, 0.2);
  border: 2px solid rgba(0, 70, 219, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: #fff;
  transition: all 0.3s;
}

.flow-node:hover .flow-icon {
  background: rgba(0, 70, 219, 0.4);
  border-color: #0046DB;
  transform: scale(1.08);
}

.flow-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.65);
  white-space: nowrap;
}

.flow-arrow {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.3);
  margin: 0 2px;
  margin-bottom: 24px;
}

/* ==================== 通用节标题 ==================== */
.section-header-center {
  text-align: center;
  margin-bottom: 40px;
}

.section-header-center h2 {
  font-size: 28px;
  color: #1a1a2e;
  margin: 0 0 10px 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.section-header-center h2 i {
  color: #0046DB;
  font-size: 24px;
}

.section-header-center p {
  font-size: 15px;
  color: #888;
  margin: 0;
}

/* ==================== 行业概览 ==================== */
.overview-section {
  background: #fff;
  border-radius: 12px;
  padding: 40px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  margin-bottom: 40px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 10px;
  border: 1px solid #f0f0f0;
  transition: all 0.3s;
}

.stat-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  border-color: #0046DB;
}

.stat-icon-wrapper {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: rgba(0, 70, 219, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-icon-wrapper i {
  font-size: 22px;
  color: #0046DB;
}

.stat-info {
  flex: 1;
  min-width: 0;
}

.stat-number {
  font-size: 22px;
  font-weight: 700;
  color: #0046DB;
  line-height: 1.2;
}

.stat-label {
  font-size: 14px;
  color: #333;
  font-weight: 500;
  margin: 2px 0;
}

.stat-desc {
  font-size: 12px;
  color: #999;
  line-height: 1.4;
}

/* ==================== 核心技术 ==================== */
.technology-section {
  background: #fff;
  border-radius: 12px;
  padding: 40px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  margin-bottom: 40px;
}

.tech-cards {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
}

.tech-card {
  border-radius: 12px;
  border: 1px solid #f0f0f0;
  overflow: hidden;
  transition: all 0.3s;
  background: #fff;
}

.tech-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
  border-color: #e0e0e0;
}

.tech-card-inner {
  padding: 28px;
  position: relative;
}

.tech-number {
  position: absolute;
  top: 12px;
  right: 16px;
  font-size: 48px;
  font-weight: 900;
  color: #f0f0f0;
  line-height: 1;
  pointer-events: none;
  user-select: none;
}

.tech-icon-wrapper {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
}

.tech-icon-wrapper i {
  font-size: 26px;
}

.tech-title {
  font-size: 20px;
  font-weight: 700;
  color: #1a1a2e;
  margin: 0 0 4px 0;
}

.tech-subtitle {
  font-size: 14px;
  color: #999;
  margin: 0 0 14px 0;
  font-weight: 400;
}

.tech-desc {
  font-size: 14px;
  color: #555;
  line-height: 1.7;
  margin: 0 0 18px 0;
}

.tech-params {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-bottom: 18px;
  padding: 14px;
  background: #f8f9fa;
  border-radius: 8px;
}

.tech-param {
  display: flex;
  flex-direction: column;
}

.param-label {
  font-size: 11px;
  color: #999;
  margin-bottom: 2px;
}

.param-value {
  font-size: 13px;
  color: #333;
  font-weight: 600;
}

.tech-flow {
  margin-bottom: 14px;
}

.flow-title {
  font-size: 13px;
  color: #666;
  font-weight: 500;
  margin-bottom: 8px;
}

.flow-steps {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px;
}

.flow-step {
  font-size: 12px;
  color: #555;
  background: #f0f4ff;
  padding: 4px 10px;
  border-radius: 4px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.flow-sep {
  margin-left: 4px;
  color: #0046DB;
  font-size: 10px;
}

.tech-features {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.tech-feature {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #555;
}

.tech-feature i {
  font-size: 14px;
  flex-shrink: 0;
}

/* ==================== 数据表格 ==================== */
.data-section {
  background: #fff;
  border-radius: 12px;
  padding: 40px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  margin-bottom: 40px;
}

.data-table-wrapper {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 700px;
}

.data-table thead {
  background: #f8f9fa;
}

.data-table th {
  padding: 14px 18px;
  text-align: left;
  font-size: 13px;
  color: #555;
  font-weight: 600;
  border-bottom: 2px solid #e8e8e8;
}

.data-table th:first-child {
  border-radius: 8px 0 0 0;
}

.data-table th:last-child {
  border-radius: 0 8px 0 0;
}

.data-table td {
  padding: 12px 18px;
  font-size: 13px;
  color: #444;
  border-bottom: 1px solid #f0f0f0;
}

.data-table tbody tr:hover {
  background: #f8f9fa;
}

.data-table .row-label {
  font-weight: 500;
  color: #333;
  white-space: nowrap;
}

.data-table tbody tr:last-child td {
  border-bottom: none;
}

/* ==================== 未来展望 ==================== */
.outlook-section {
  background: #fff;
  border-radius: 12px;
  padding: 40px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.outlook-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.outlook-card {
  padding: 28px 24px;
  background: #fff;
  border-radius: 10px;
  border: 1px solid #f0f0f0;
  transition: all 0.3s;
  position: relative;
  overflow: hidden;
}

.outlook-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  background: #0046DB;
  transition: width 0.3s;
}

.outlook-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.08);
  border-color: #0046DB;
}

.outlook-card:hover::before {
  width: 100%;
  opacity: 0.04;
}

.outlook-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  background: rgba(0, 70, 219, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
}

.outlook-icon i {
  font-size: 20px;
  color: #0046DB;
}

.outlook-card h4 {
  font-size: 17px;
  font-weight: 600;
  color: #1a1a2e;
  margin: 0 0 10px 0;
}

.outlook-card p {
  font-size: 13px;
  color: #666;
  line-height: 1.7;
  margin: 0 0 14px 0;
}

.outlook-tag {
  display: inline-block;
  font-size: 11px;
  color: #0046DB;
  background: rgba(0, 70, 219, 0.08);
  padding: 3px 10px;
  border-radius: 12px;
  font-weight: 500;
}

/* ==================== 响应式设计 ==================== */
@media (max-width: 1200px) {
  .container {
    max-width: 960px;
  }

  .tech-cards {
    grid-template-columns: 1fr;
    gap: 20px;
  }

  .outlook-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .hero-content {
    grid-template-columns: 1fr;
    gap: 30px;
    text-align: center;
  }

  .hero-text h1 {
    font-size: 30px;
  }

  .hero-desc {
    margin: 0 auto 32px;
  }

  .hero-stats {
    justify-content: center;
  }
}

@media (max-width: 992px) {
  .steel-metallurgy {
    padding-top: 80px;
  }

  .hero-section {
    min-height: 320px;
  }

  .hero-content {
    padding: 40px 0;
  }

  .hero-text h1 {
    font-size: 26px;
  }

  .hero-stats {
    flex-wrap: wrap;
    gap: 16px;
  }

  .hero-stat-divider {
    display: none;
  }

  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .outlook-grid {
    grid-template-columns: 1fr;
  }

  .overview-section,
  .technology-section,
  .data-section,
  .outlook-section {
    padding: 24px;
  }

  .section-header-center h2 {
    font-size: 22px;
  }

  .process-flow {
    gap: 2px;
  }

  .flow-icon {
    width: 52px;
    height: 52px;
    font-size: 20px;
  }
}

@media (max-width: 768px) {
  .main-content {
    padding: 20px 0 40px;
  }

  .hero-text h1 {
    font-size: 22px;
  }

  .hero-subtitle {
    font-size: 14px;
  }

  .hero-desc {
    font-size: 13px;
  }

  .hero-stats {
    gap: 12px;
  }

  .hero-stat-value {
    font-size: 20px;
  }

  .flow-icon {
    width: 44px;
    height: 44px;
    font-size: 16px;
  }

  .flow-label {
    font-size: 10px;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .tech-params {
    grid-template-columns: 1fr;
  }

  .section-header-center h2 {
    font-size: 20px;
  }

  .overview-section,
  .technology-section,
  .data-section,
  .outlook-section {
    padding: 20px;
  }

  .tech-card-inner {
    padding: 20px;
  }

  .tech-number {
    font-size: 36px;
  }

  .data-table th,
  .data-table td {
    padding: 10px 12px;
    font-size: 12px;
  }

  .section-header-center {
    margin-bottom: 24px;
  }
}

@media (max-width: 576px) {
  .container {
    padding: 0 10px;
  }

  .hero-section {
    min-height: 280px;
  }

  .hero-text h1 {
    font-size: 20px;
  }

  .hero-content {
    padding: 28px 0;
  }

  .hero-stats {
    flex-direction: column;
    align-items: center;
  }

  .hero-stat-item {
    align-items: center;
  }

  .process-flow {
    gap: 0;
  }

  .flow-icon {
    width: 36px;
    height: 36px;
    font-size: 14px;
  }

  .flow-label {
    font-size: 9px;
  }

  .flow-arrow {
    font-size: 10px;
  }

  .section-header-center h2 {
    font-size: 18px;
  }

  .section-header-center h2 i {
    font-size: 18px;
  }

  .section-header-center p {
    font-size: 13px;
  }

  .tech-title {
    font-size: 17px;
  }

  .tech-card-inner {
    padding: 16px;
  }

  .tech-number {
    font-size: 28px;
    top: 8px;
    right: 10px;
  }

  .outlook-card {
    padding: 20px 18px;
  }

  .outlook-card h4 {
    font-size: 15px;
  }
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
.section-header-center,
.stats-grid,
.tech-cards,
.outlook-grid {
  animation: fadeInUp 0.5s ease-out;
}

.stat-card,
.tech-card,
.outlook-card {
  animation: fadeInUp 0.4s ease-out;
}

.stat-card:nth-child(2),
.stat-card:nth-child(5) {
  animation-delay: 0.1s;
}

.stat-card:nth-child(3),
.stat-card:nth-child(6) {
  animation-delay: 0.2s;
}
</style>
