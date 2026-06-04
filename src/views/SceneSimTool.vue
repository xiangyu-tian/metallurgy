<template>
  <Header />
  <div class="page-wrapper">
    <!-- Breadcrumb -->
    <div class="mb-nav">
      <div class="container">
        <p>当前位置：<router-link to="/">首页</router-link> &gt; <router-link to="/scene/simulation">仿真与工单协同</router-link> &gt; <span>{{ toolName }}</span></p>
      </div>
    </div>

    <!-- Hero -->
    <div class="hero-section">
      <div class="hero-overlay"></div>
      <div class="container hero-content">
        <h1 class="hero-title">{{ toolName }}</h1>
        <p class="hero-desc">{{ heroDesc }}</p>
      </div>
    </div>

    <!-- Main -->
    <div class="main-section">
      <div class="container">
        <router-link to="/scene/simulation" class="back-link"><i class="fas fa-arrow-left"></i> 返回工具列表</router-link>

        <!-- Tool Panel -->
        <div class="tool-panel">
          <!-- ==================== Work Order ==================== -->
          <div v-if="toolId === 'work-order'">
            <div class="form-row">
              <div class="form-group">
                <label><i class="fas fa-industry"></i> 场景</label>
                <input v-model="form.scenario" placeholder="如 标准冶炼" />
              </div>
              <div class="form-group">
                <label><i class="fas fa-microchip"></i> 设备</label>
                <input v-model="form.equipment" placeholder="如 转炉" />
              </div>
              <div class="form-group">
                <label><i class="fas fa-clock"></i> 耗时（分钟）</label>
                <input type="number" v-model.number="form.duration" placeholder="如 45" />
              </div>
            </div>
            <button class="btn-submit" @click="submit" :disabled="loading">
              <i class="fas" :class="loading ? 'fa-spinner fa-spin' : 'fa-play'"></i>
              {{ loading ? '生成中...' : '生成工单' }}
            </button>
            <div v-if="error" class="result-error"><i class="fas fa-exclamation-triangle"></i> {{ error }}</div>

            <!-- Result: Steps List -->
            <div v-if="result && !loading" class="result-section">
              <div class="result-header">
                <i class="fas fa-clipboard-check"></i> 工单详情
              </div>
              <div v-if="result.steps && result.steps.length" class="steps-list">
                <div class="step-item" v-for="(step, idx) in result.steps" :key="idx">
                  <div class="step-index">{{ idx + 1 }}</div>
                  <div class="step-content">
                    <span class="step-text">{{ step }}</span>
                  </div>
                </div>
              </div>
              <div class="badges-row">
                <span class="badge badge-risk" v-if="result.riskLevel">
                  <i class="fas fa-exclamation-circle"></i> 风险：{{ result.riskLevel }}
                </span>
                <span class="badge badge-priority" v-if="result.priority">
                  <i class="fas fa-flag"></i> 优先级：{{ result.priority }}
                </span>
              </div>
              <div v-if="result.summary" class="summary-card">{{ result.summary }}</div>
            </div>
          </div>

          <!-- ==================== Risk ==================== -->
          <div v-if="toolId === 'risk'">
            <div class="form-row">
              <div class="form-group">
                <label><i class="fas fa-industry"></i> 场景</label>
                <input v-model="form.scenario" placeholder="如 标准冶炼" />
              </div>
              <div class="form-group">
                <label><i class="fas fa-microchip"></i> 设备</label>
                <input v-model="form.equipment" placeholder="如 转炉" />
              </div>
            </div>
            <button class="btn-submit" @click="submit" :disabled="loading">
              <i class="fas" :class="loading ? 'fa-spinner fa-spin' : 'fa-play'"></i>
              {{ loading ? '评估中...' : '评估风险' }}
            </button>
            <div v-if="error" class="result-error"><i class="fas fa-exclamation-triangle"></i> {{ error }}</div>

            <!-- Result: Risk Level + Probability -->
            <div v-if="result && !loading" class="result-section">
              <div class="result-header">
                <i class="fas fa-shield-alt"></i> 风险评估结果
              </div>
              <div class="risk-result-grid">
                <div class="risk-card" v-if="result.riskLevel">
                  <div class="risk-card-icon"><i class="fas fa-exclamation-triangle"></i></div>
                  <div class="risk-card-label">风险等级</div>
                  <div class="risk-card-value">{{ result.riskLevel }}</div>
                </div>
                <div class="risk-card" v-if="result.probability">
                  <div class="risk-card-icon"><i class="fas fa-chart-line"></i></div>
                  <div class="risk-card-label">概率量化</div>
                  <div class="risk-card-value">{{ result.probability }}</div>
                </div>
              </div>
              <div v-if="result.summary" class="summary-card">{{ result.summary }}</div>
            </div>
          </div>

          <!-- ==================== Params ==================== -->
          <div v-if="toolId === 'params'">
            <div class="form-row">
              <div class="form-group">
                <label><i class="fas fa-industry"></i> 场景</label>
                <input v-model="form.scenario" placeholder="如 标准冶炼" />
              </div>
            </div>
            <button class="btn-submit" @click="submit" :disabled="loading">
              <i class="fas" :class="loading ? 'fa-spinner fa-spin' : 'fa-play'"></i>
              {{ loading ? '推荐中...' : '获取推荐' }}
            </button>
            <div v-if="error" class="result-error"><i class="fas fa-exclamation-triangle"></i> {{ error }}</div>

            <!-- Result: Temperature, Pressure, Duration -->
            <div v-if="result && !loading" class="result-section">
              <div class="result-header">
                <i class="fas fa-sliders-h"></i> 推荐参数
              </div>
              <div class="params-result-grid">
                <div class="param-card" v-if="result.temperature">
                  <div class="param-card-header">温度</div>
                  <div class="param-card-value">{{ result.temperature }}</div>
                </div>
                <div class="param-card" v-if="result.pressure">
                  <div class="param-card-header">压力</div>
                  <div class="param-card-value">{{ result.pressure }}</div>
                </div>
                <div class="param-card" v-if="result.duration">
                  <div class="param-card-header">时长</div>
                  <div class="param-card-value">{{ result.duration }}</div>
                </div>
              </div>
              <div v-if="result.summary" class="summary-card">{{ result.summary }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  <Footer />
</template>

<script>
import Header from '@/components/Header.vue';
import Footer from '@/components/Footer.vue';
import axios from 'axios';

const toolMeta = {
  'work-order': { name: '操作工单生成', desc: '生成标准化操作步骤，含风险提示与优先级标识' },
  'risk': { name: '风险评估', desc: '量化风险等级与概率，辅助工艺安全决策' },
  'params': { name: '参数推荐', desc: '基于场景推荐最优温度、压力、时长等工艺参数' }
};
const defaults = {
  'work-order': { scenario: '标准冶炼', equipment: '转炉', duration: 45 },
  'risk': { scenario: '标准冶炼', equipment: '转炉' },
  'params': { scenario: '标准冶炼' }
};

export default {
  name: 'SceneSimTool',
  components: { Header, Footer },
  data() {
    return {
      toolId: '',
      form: {},
      loading: false,
      result: null,
      error: ''
    };
  },
  computed: {
    toolName() { return (toolMeta[this.toolId] || {}).name || '工具详情'; },
    heroDesc() { return (toolMeta[this.toolId] || {}).desc || ''; }
  },
  methods: {
    async submit() {
      this.loading = true;
      this.error = '';
      this.result = null;
      try {
        const res = await axios.post('/api/tools/simulation', { tool: this.toolId, ...this.form });
        if (res.data.code === 200) {
          this.result = res.data.data.result;
        } else {
          this.error = res.data.message || '请求失败';
        }
      } catch (e) {
        this.error = e.message || '网络错误';
      } finally {
        this.loading = false;
      }
    }
  },
  created() {
    this.toolId = this.$route.params.toolId;
    this.form = JSON.parse(JSON.stringify(defaults[this.toolId] || {}));
  }
};
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
.hero-section { position: relative; height: 200px; display: flex; align-items: center; background: linear-gradient(135deg, #0a1628 0%, #002a67 40%, #0046DB 100%); }
.hero-overlay { position: absolute; inset: 0; background: linear-gradient(135deg, rgba(0,22,58,0.88), rgba(0,70,219,0.6), rgba(0,22,58,0.85)); }
.hero-content { position: relative; z-index: 1; }
.hero-title { font-size: 28px; font-weight: 700; color: #fff; margin: 0 0 8px; }
.hero-desc { font-size: 15px; color: rgba(255,255,255,0.65); margin: 0; }

/* Main */
.main-section { padding: 40px 0 80px; }
.back-link { display: inline-flex; align-items: center; gap: 6px; color: #0046DB; text-decoration: none; font-size: 15px; margin-bottom: 24px; transition: color 0.3s; }
.back-link:hover { color: #0038b3; }
.back-link i { font-size: 13px; }

/* Tool Panel */
.tool-panel {
  background: #fff; border-radius: 12px; padding: 32px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06); max-width: 720px;
}

/* Form */
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; margin-bottom: 20px; }
.form-row > .form-group:last-child:nth-child(odd) { grid-column: 1 / -1; }
.form-group { margin-bottom: 0; }
.form-group label { display: flex; align-items: center; gap: 6px; font-size: 14px; color: #333; margin-bottom: 6px; font-weight: 500; }
.form-group label i { color: #0046DB; font-size: 13px; }
.form-group input {
  width: 100%; height: 42px; padding: 0 14px;
  border: 1px solid #dcdfe6; border-radius: 8px; font-size: 14px; color: #333;
  outline: none; transition: border-color 0.3s, box-shadow 0.3s; box-sizing: border-box;
}
.form-group input:focus { border-color: #0046DB; box-shadow: 0 0 0 3px rgba(0,70,219,0.1); }

/* Button */
.btn-submit {
  display: flex; align-items: center; justify-content: center; gap: 8px;
  width: 100%; height: 46px; border: none; border-radius: 10px;
  background: #0046DB; color: #fff; font-size: 16px; font-weight: 600;
  cursor: pointer; transition: all 0.3s; margin-top: 4px;
}
.btn-submit:hover:not(:disabled) { background: #0038b3; box-shadow: 0 4px 16px rgba(0,70,219,0.35); transform: translateY(-1px); }
.btn-submit:disabled { opacity: 0.55; cursor: not-allowed; }

/* Error */
.result-error { display: flex; align-items: center; gap: 8px; margin-top: 16px; padding: 12px 16px; background: rgba(255,77,79,0.08); border: 1px solid rgba(255,77,79,0.2); border-radius: 10px; color: #e54545; font-size: 14px; }

/* Result Section */
.result-section { margin-top: 28px; }
.result-header { display: flex; align-items: center; gap: 8px; font-size: 16px; font-weight: 600; color: #0046DB; margin-bottom: 18px; padding-bottom: 12px; border-bottom: 2px solid #E8F0FE; }
.result-header i { font-size: 18px; }

/* Steps List (work-order) */
.steps-list { display: flex; flex-direction: column; gap: 10px; margin-bottom: 20px; }
.step-item { display: flex; align-items: flex-start; gap: 12px; padding: 12px 16px; background: #f8faff; border-radius: 10px; border: 1px solid #e8f0fe; }
.step-index { width: 28px; height: 28px; border-radius: 50%; background: #0046DB; color: #fff; font-size: 13px; font-weight: 600; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.step-content { flex: 1; display: flex; flex-direction: column; gap: 4px; }
.step-text { font-size: 14px; color: #333; line-height: 1.5; }

/* Badges (work-order) */
.badges-row { display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 16px; }
.badge { display: inline-flex; align-items: center; gap: 5px; font-size: 12px; font-weight: 600; padding: 5px 14px; border-radius: 20px; }
.badge-risk { background: rgba(245,158,11,0.12); color: #B45309; }
.badge-priority { background: rgba(0,70,219,0.1); color: #0046DB; }

/* Risk Result Grid (risk) */
.risk-result-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 20px; }
.risk-card { background: #f8faff; border: 1px solid #e8f0fe; border-radius: 12px; padding: 24px 20px; text-align: center; }
.risk-card-icon { margin-bottom: 10px; }
.risk-card-icon i { font-size: 28px; color: #F59E0B; }
.risk-card-label { font-size: 13px; color: #888; margin-bottom: 6px; }
.risk-card-value { font-size: 22px; font-weight: 700; color: #0046DB; }

/* Params Result Grid (params) */
.params-result-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 20px; }
.param-card { background: #f8faff; border: 1px solid #e8f0fe; border-radius: 12px; padding: 24px 16px; text-align: center; }
.param-card-header { font-size: 13px; color: #888; margin-bottom: 8px; }
.param-card-value { font-size: 20px; font-weight: 700; color: #0046DB; }

/* Summary Card (shared) */
.summary-card { background: #E8F0FE; border: 1px solid rgba(0,70,219,0.12); border-radius: 10px; padding: 16px 20px; color: #0046DB; font-size: 14px; line-height: 1.6; }

/* Responsive */
@media (max-width: 768px) {
  .hero-title { font-size: 22px; }
  .form-row { grid-template-columns: 1fr; }
  .risk-result-grid { grid-template-columns: 1fr; }
  .params-result-grid { grid-template-columns: 1fr; }
  .tool-panel { padding: 20px; }
}
</style>
