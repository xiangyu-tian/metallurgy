<template>
  <Header></Header>
  <div class="scene-thermo-tool">
    <!-- 面包屑导航 -->
    <div class="mb-nav">
      <div class="container">
        <p>
          <router-link to="/">首页</router-link>
          <span class="sep">></span>
          <router-link to="/scenes">智能场景</router-link>
          <span class="sep">></span>
          <router-link to="/scene/thermodynamics">热力学推理</router-link>
          <span class="sep">></span>
          <span class="current">{{ toolName }}</span>
        </p>
      </div>
    </div>

    <!-- Hero 区域（小型） -->
    <section class="hero-section">
      <div class="hero-bg-pattern"></div>
      <div class="container">
        <div class="hero-content">
          <router-link to="/scene/thermodynamics" class="hero-back">
            <i class="fas fa-arrow-left"></i> 返回工具列表
          </router-link>
          <h1 class="hero-title">{{ toolName }}</h1>
          <p class="hero-desc">{{ toolSubtitle }}</p>
        </div>
      </div>
    </section>

    <!-- 工具表单 + 结果 -->
    <section class="main-section">
      <div class="container">
        <div class="tool-form-card">
          <!-- ΔG 计算 -->
          <template v-if="toolId === 'delta-g'">
            <div class="form-header">
              <i class="fas fa-fire"></i>
              <span>参数输入</span>
            </div>
            <div class="form-group">
              <label><i class="fas fa-exchange-alt"></i> 反应式</label>
              <select v-model="reaction">
                <option v-for="r in reactionOptions" :key="r.value" :value="r.value">{{ r.label }}</option>
              </select>
            </div>
            <div class="form-group">
              <label><i class="fas fa-thermometer-half"></i> 温度（°C）</label>
              <input type="number" v-model.number="temperature" min="0" max="3000" step="10" placeholder="请输入温度值" />
            </div>
            <button class="btn-calc" @click="calculate" :disabled="loading">
              <i :class="loading ? 'fas fa-spinner fa-spin' : 'fas fa-calculator'"></i>
              {{ loading ? '计算中...' : '开始计算' }}
            </button>
            <div v-if="error" class="error-msg">
              <i class="fas fa-exclamation-circle"></i> {{ error }}
            </div>
            <div v-if="result" class="result-box">
              <div class="result-header">
                <i class="fas fa-chart-bar"></i>
                <span>计算结果</span>
              </div>
              <table class="result-table">
                <tbody>
                <tr>
                  <td class="result-label">ΔG</td>
                  <td class="result-value">{{ result.deltaG }}</td>
                </tr>
                <tr>
                  <td class="result-label">平衡常数 K</td>
                  <td class="result-value">{{ result.k }}</td>
                </tr>
                <tr>
                  <td class="result-label">反应方向</td>
                  <td class="result-value direction-tag">{{ result.direction }}</td>
                </tr>
                </tbody>
              </table>
            </div>
          </template>

          <!-- 反应焓变 -->
          <template v-else-if="toolId === 'enthalpy'">
            <div class="form-header">
              <i class="fas fa-chart-line"></i>
              <span>参数输入</span>
            </div>
            <div class="form-group">
              <label><i class="fas fa-exchange-alt"></i> 反应式</label>
              <select v-model="reaction">
                <option v-for="r in reactionOptions" :key="r.value" :value="r.value">{{ r.label }}</option>
              </select>
            </div>
            <button class="btn-calc" @click="calculate" :disabled="loading">
              <i :class="loading ? 'fas fa-spinner fa-spin' : 'fas fa-calculator'"></i>
              {{ loading ? '计算中...' : '开始计算' }}
            </button>
            <div v-if="error" class="error-msg">
              <i class="fas fa-exclamation-circle"></i> {{ error }}
            </div>
            <div v-if="result" class="result-box">
              <div class="result-header">
                <i class="fas fa-chart-bar"></i>
                <span>计算结果</span>
              </div>
              <table class="result-table">
                <tbody>
                <tr>
                  <td class="result-label">ΔH°</td>
                  <td class="result-value">{{ result.deltaH }}</td>
                </tr>
                <tr>
                  <td class="result-label">反应类型</td>
                  <td class="result-value direction-tag">{{ result.reactionType }}</td>
                </tr>
                </tbody>
              </table>
            </div>
          </template>

          <!-- 平衡常数 -->
          <template v-else-if="toolId === 'equilibrium'">
            <div class="form-header">
              <i class="fas fa-balance-scale"></i>
              <span>参数输入</span>
            </div>
            <div class="form-group">
              <label><i class="fas fa-exchange-alt"></i> 反应式</label>
              <select v-model="reaction">
                <option v-for="r in reactionOptions" :key="r.value" :value="r.value">{{ r.label }}</option>
              </select>
            </div>
            <div class="form-group">
              <label><i class="fas fa-thermometer-half"></i> 温度（°C）</label>
              <input type="number" v-model.number="temperature" min="0" max="3000" step="10" placeholder="请输入温度值" />
            </div>
            <button class="btn-calc" @click="calculate" :disabled="loading">
              <i :class="loading ? 'fas fa-spinner fa-spin' : 'fas fa-calculator'"></i>
              {{ loading ? '计算中...' : '开始计算' }}
            </button>
            <div v-if="error" class="error-msg">
              <i class="fas fa-exclamation-circle"></i> {{ error }}
            </div>
            <div v-if="result" class="result-box">
              <div class="result-header">
                <i class="fas fa-chart-bar"></i>
                <span>计算结果</span>
              </div>
              <table class="result-table">
                <tbody>
                <tr>
                  <td class="result-label">平衡常数 K</td>
                  <td class="result-value">{{ result.k }}</td>
                </tr>
                <tr>
                  <td class="result-label">ΔG</td>
                  <td class="result-value">{{ result.deltaG }}</td>
                </tr>
                </tbody>
              </table>
            </div>
          </template>

          <!-- 反应方向 -->
          <template v-else-if="toolId === 'direction'">
            <div class="form-header">
              <i class="fas fa-arrow-right"></i>
              <span>参数输入</span>
            </div>
            <div class="form-group">
              <label><i class="fas fa-exchange-alt"></i> 反应式</label>
              <select v-model="reaction">
                <option v-for="r in reactionOptions" :key="r.value" :value="r.value">{{ r.label }}</option>
              </select>
            </div>
            <div class="form-group">
              <label><i class="fas fa-thermometer-half"></i> 温度（°C）</label>
              <input type="number" v-model.number="temperature" min="0" max="3000" step="10" placeholder="请输入温度值" />
            </div>
            <button class="btn-calc" @click="calculate" :disabled="loading">
              <i :class="loading ? 'fas fa-spinner fa-spin' : 'fas fa-calculator'"></i>
              {{ loading ? '计算中...' : '开始计算' }}
            </button>
            <div v-if="error" class="error-msg">
              <i class="fas fa-exclamation-circle"></i> {{ error }}
            </div>
            <div v-if="result" class="result-box">
              <div class="result-header">
                <i class="fas fa-chart-bar"></i>
                <span>计算结果</span>
              </div>
              <table class="result-table">
                <tbody>
                <tr>
                  <td class="result-label">自发方向</td>
                  <td class="result-value direction-tag">{{ result.direction }}</td>
                </tr>
                <tr v-if="result.decompTemp">
                  <td class="result-label">分解温度</td>
                  <td class="result-value">{{ result.decompTemp }}</td>
                </tr>
                </tbody>
              </table>
            </div>
          </template>

          <!-- 未知工具 -->
          <div v-else class="not-found">
            <i class="fas fa-exclamation-triangle"></i>
            <p>未知的工具类型，请返回重试。</p>
            <router-link to="/scene/thermodynamics" class="btn-back-list">返回工具列表</router-link>
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
import axios from "axios";

const TOOL_INFO = {
  "delta-g": { name: "ΔG 计算", subtitle: "计算冶金反应的吉布斯自由能变化，判断反应自发性" },
  enthalpy: { name: "反应焓变", subtitle: "计算标准反应焓变，判断反应放热/吸热特性" },
  equilibrium: { name: "平衡常数", subtitle: "计算反应平衡常数 K，分析反应平衡状态" },
  direction: { name: "反应方向", subtitle: "结合温度判断反应自发方向，计算分解温度" },
};

export default {
  name: "SceneThermoTool",
  components: {
    Header,
    Footer,
  },
  data() {
    return {
      reactionOptions: [
        { value: "C + O2 = CO2", label: "C + O\u2082 \u2192 CO\u2082" },
        { value: "2C + O2 = 2CO", label: "2C + O\u2082 \u2192 2CO" },
        { value: "FeO + C = Fe + CO", label: "FeO + C \u2192 Fe + CO" },
        { value: "Fe2O3 + 3CO = 2Fe + 3CO2", label: "Fe\u2082O\u2083 + 3CO \u2192 2Fe + 3CO\u2082" },
        { value: "Fe3O4 + 4CO = 3Fe + 4CO2", label: "Fe\u2083O\u2084 + 4CO \u2192 3Fe + 4CO\u2082" },
        { value: "CaCO3 = CaO + CO2", label: "CaCO\u2083 \u2192 CaO + CO\u2082" },
        { value: "SiO2 + 2C = Si + 2CO", label: "SiO\u2082 + 2C \u2192 Si + 2CO" },
        { value: "2FeO + Si = 2Fe + SiO2", label: "2FeO + Si \u2192 2Fe + SiO\u2082" },
        { value: "MnO + C = Mn + CO", label: "MnO + C \u2192 Mn + CO" },
        { value: "Fe2O3 + 2Al = 2Fe + Al2O3", label: "Fe\u2082O\u2083 + 2Al \u2192 2Fe + Al\u2082O\u2083" },
      ],
      reaction: "C + O2 = CO2",
      temperature: 1600,
      loading: false,
      result: null,
      error: null,
    };
  },
  computed: {
    toolId() {
      return this.$route.params.toolId;
    },
    toolName() {
      const info = TOOL_INFO[this.toolId];
      return info ? info.name : "未知工具";
    },
    toolSubtitle() {
      const info = TOOL_INFO[this.toolId];
      return info ? info.subtitle : "";
    },
  },
  watch: {
    toolId() {
      this.resetForm();
    },
  },
  methods: {
    resetForm() {
      this.reaction = "C + O2 = CO2";
      this.temperature = 1600;
      this.loading = false;
      this.result = null;
      this.error = null;
    },
    getPayload() {
      const base = { tool: this.toolId, reaction: this.reaction };
      if (this.toolId === "delta-g" || this.toolId === "equilibrium" || this.toolId === "direction") {
        base.temperature = this.temperature;
      }
      return base;
    },
    async calculate() {
      this.loading = true;
      this.error = null;
      this.result = null;
      try {
        const res = await axios.post("/api/tools/thermodynamics", this.getPayload());
        if (res.data && res.data.code === 200) {
          this.result = res.data.data.result || res.data.data;
        } else {
          this.error = res.data?.message || "计算失败，请稍后重试";
        }
      } catch (err) {
        this.error =
          err.response?.data?.message ||
          err.message ||
          "网络错误，请检查网络连接后重试";
      } finally {
        this.loading = false;
      }
    },
  },
};
</script>

<style scoped>
/* ==================== 基础样式 ==================== */
.scene-thermo-tool {
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

/* ==================== Hero 区域（小型） ==================== */
.hero-section {
  background: linear-gradient(135deg, #0a1628 0%, #002a67 40%, #0046db 100%);
  padding: 40px 0 36px;
  position: relative;
  overflow: hidden;
}

.hero-bg-pattern {
  position: absolute;
  top: -40%;
  right: -15%;
  width: 500px;
  height: 500px;
  background: radial-gradient(circle, rgba(0, 70, 219, 0.2) 0%, transparent 65%);
  border-radius: 50%;
  pointer-events: none;
}

.hero-content {
  position: relative;
  z-index: 1;
  text-align: center;
}

.hero-back {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: rgba(255, 255, 255, 0.6);
  font-size: 13px;
  text-decoration: none;
  transition: color 0.25s;
  margin-bottom: 16px;
}

.hero-back:hover {
  color: #fff;
}

.hero-title {
  font-size: 28px;
  color: #fff;
  margin: 0 0 10px;
  font-weight: 700;
  letter-spacing: 1px;
}

.hero-desc {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
  margin: 0 auto;
  max-width: 560px;
  line-height: 1.6;
}

/* ==================== 主内容区域 ==================== */
.main-section {
  padding: 28px 0 80px;
}

/* ==================== 表单卡片 ==================== */
.tool-form-card {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  padding: 32px;
  max-width: 680px;
  margin: 0 auto;
}

.form-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 2px solid #e8f0fe;
  font-size: 16px;
  color: #0046db;
  font-weight: 600;
}

.form-header i {
  font-size: 18px;
}

/* ==================== 表单元素 ==================== */
.form-group {
  display: flex;
  flex-direction: column;
  margin-bottom: 18px;
}

.form-group label {
  font-size: 14px;
  color: #555;
  margin-bottom: 6px;
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 500;
}

.form-group label i {
  color: #0046db;
  font-size: 13px;
}

.form-group select,
.form-group input {
  padding: 10px 14px;
  background: #fafbfc;
  border: 1px solid #dcdfe6;
  border-radius: 8px;
  color: #333;
  font-size: 14px;
  transition: all 0.25s;
  outline: none;
}

.form-group select:focus,
.form-group input:focus {
  border-color: #0046db;
  box-shadow: 0 0 0 3px rgba(0, 70, 219, 0.1);
  background: #fff;
}

.form-group select {
  cursor: pointer;
  appearance: auto;
}

/* ==================== 计算按钮 ==================== */
.btn-calc {
  width: 100%;
  padding: 12px 24px;
  background: #0046db;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-top: 6px;
}

.btn-calc:hover:not(:disabled) {
  background: #0033a0;
  transform: translateY(-1px);
  box-shadow: 0 4px 14px rgba(0, 70, 219, 0.3);
}

.btn-calc:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

/* ==================== 错误消息 ==================== */
.error-msg {
  margin-top: 14px;
  padding: 10px 14px;
  background: #fef0f0;
  border: 1px solid #fde2e2;
  border-radius: 8px;
  color: #f56c6c;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.error-msg i {
  font-size: 15px;
  flex-shrink: 0;
}

/* ==================== 结果区域 ==================== */
.result-box {
  margin-top: 24px;
  border: 1px solid rgba(0, 70, 219, 0.1);
  border-radius: 12px;
  overflow: hidden;
  animation: fadeIn 0.35s ease-out;
}

.result-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 20px;
  background: #e8f0fe;
  color: #0046db;
  font-size: 14px;
  font-weight: 600;
  border-bottom: 1px solid rgba(0, 70, 219, 0.08);
}

.result-header i {
  font-size: 16px;
}

.result-table {
  width: 100%;
  border-collapse: collapse;
}

.result-table tr + tr {
  border-top: 1px solid #f0f2f5;
}

.result-table td {
  padding: 14px 20px;
  font-size: 14px;
}

.result-label {
  color: #888;
  font-weight: 500;
  width: 120px;
  background: #fafbfc;
}

.result-value {
  color: #1a1a2e;
  font-weight: 600;
}

.direction-tag {
  display: inline-block;
  padding: 2px 0;
  color: #0046db;
}

/* ==================== 未找到提示 ==================== */
.not-found {
  text-align: center;
  padding: 48px 0;
  color: #999;
}

.not-found i {
  font-size: 42px;
  color: #dcdfe6;
  margin-bottom: 18px;
}

.not-found p {
  font-size: 15px;
  margin: 0 0 22px;
}

.btn-back-list {
  display: inline-block;
  padding: 10px 24px;
  background: #0046db;
  color: #fff;
  border-radius: 8px;
  text-decoration: none;
  font-size: 14px;
  font-weight: 600;
  transition: background 0.3s;
}

.btn-back-list:hover {
  background: #0033a0;
}

/* ==================== 动画 ==================== */
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

/* ==================== 响应式 ==================== */
@media (max-width: 1200px) {
  .container {
    max-width: 960px;
  }

  .hero-title {
    font-size: 26px;
  }

  .hero-section {
    padding: 36px 0 30px;
  }
}

@media (max-width: 768px) {
  .hero-section {
    padding: 30px 0 24px;
  }

  .hero-title {
    font-size: 22px;
  }

  .hero-desc {
    font-size: 13px;
  }

  .main-section {
    padding: 22px 0 60px;
  }

  .tool-form-card {
    padding: 24px 20px;
  }

  .form-header {
    font-size: 15px;
    margin-bottom: 20px;
    padding-bottom: 14px;
  }

  .btn-calc {
    padding: 11px 20px;
    font-size: 14px;
  }

  .result-table td {
    padding: 12px 16px;
    font-size: 13px;
  }

  .result-header {
    padding: 12px 16px;
    font-size: 13px;
  }
}

@media (max-width: 576px) {
  .container {
    padding: 0 12px;
  }

  .hero-title {
    font-size: 20px;
  }

  .hero-section {
    padding: 24px 0 20px;
  }

  .tool-form-card {
    padding: 20px 16px;
  }

  .form-group select,
  .form-group input {
    padding: 9px 12px;
    font-size: 13px;
  }

  .result-table td {
    padding: 10px 14px;
    font-size: 13px;
  }

  .result-label {
    width: 90px;
  }
}
</style>
