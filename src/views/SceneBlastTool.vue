<template>
  <Header></Header>
  <div class="scene-blast-tool">
    <!-- 面包屑导航 -->
    <div class="mb-nav">
      <div class="container">
        <p>
          当前位置：<router-link to="/">首页</router-link> &gt;
          <router-link to="/scene/thermodynamics">智能场景</router-link> &gt;
          <router-link to="/scene/blastfurnace">高炉低碳运行分析</router-link> &gt;
          <span>{{ toolTitle }}</span>
        </p>
      </div>
    </div>

    <!-- 主内容 -->
    <div class="container main-content">
      <div class="tool-detail-card">
        <!-- 返回链接 -->
        <router-link to="/scene/blastfurnace" class="back-link">
          <i class="fas fa-arrow-left"></i> 返回场景首页
        </router-link>

        <!-- 工具头部 -->
        <div class="tool-header">
          <div class="tool-header-icon">
            <i :class="toolIcon"></i>
          </div>
          <div class="tool-header-info">
            <h1 class="tool-header-title">{{ toolTitle }}</h1>
            <p class="tool-header-desc">{{ toolDesc }}</p>
          </div>
        </div>

        <!-- 输入区域 -->
        <div class="tool-form-section">
          <h3 class="section-title"><i class="fas fa-sliders-h"></i> 输入参数</h3>
          <div class="form-grid">
            <div class="form-group" v-for="field in formFields" :key="field.key">
              <label :for="field.key">
                <i :class="field.icon"></i> {{ field.label }}
              </label>
              <div class="input-wrap">
                <input
                  :id="field.key"
                  type="number"
                  v-model.number="formData[field.key]"
                  :placeholder="field.placeholder"
                  :min="field.min"
                  :step="field.step"
                />
                <span class="input-suffix">{{ field.unit }}</span>
              </div>
            </div>
          </div>
          <button class="btn-calc" @click="runTool" :disabled="loading">
            <i :class="loading ? 'fas fa-spinner fa-spin' : 'fas fa-calculator'"></i>
            {{ loading ? '计算中...' : '开始计算' }}
          </button>
        </div>

        <!-- 错误消息 -->
        <div v-if="error" class="error-msg">
          <i class="fas fa-exclamation-circle"></i> {{ error }}
        </div>

        <!-- 结果区域 -->
        <div v-if="result && !loading" class="tool-result-section">
          <h3 class="section-title"><i class="fas fa-chart-bar"></i> 计算结果</h3>
          <div class="result-grid">
            <div class="result-item" v-for="item in resultFields" :key="item.key">
              <span class="result-value" :class="item.highlight ? 'highlight-green' : ''">
                {{ formatResult(result[item.key], item.suffix) }}
              </span>
              <span class="result-label">{{ item.label }}</span>
            </div>
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
import axios from "axios";

const TOOL_CONFIG = {
  carbon: {
    title: "碳排放核算",
    desc: "核算高炉冶炼过程的碳排放量和碳排放强度",
    icon: "fas fa-leaf",
    formFields: [
      { key: "cokeRate", label: "焦比", icon: "fas fa-weight", placeholder: "请输入焦比", unit: "kg/t", min: 0, step: 1 },
      { key: "coalRate", label: "煤比", icon: "fas fa-weight", placeholder: "请输入煤比", unit: "kg/t", min: 0, step: 1 },
      { key: "production", label: "日产量", icon: "fas fa-industry", placeholder: "请输入日产量", unit: "t/d", min: 0, step: 100 },
      { key: "oreGrade", label: "入炉矿品位", icon: "fas fa-percentage", placeholder: "请输入品位", unit: "%", min: 0, step: 0.1 },
    ],
    defaultData: { cokeRate: 360, coalRate: 160, production: 5000, oreGrade: 62 },
    resultFields: [
      { key: "dailyEmission", label: "日CO₂排放量 (t)", suffix: "", highlight: false },
      { key: "carbonIntensity", label: "碳排放强度 (kgCO₂/t)", suffix: "", highlight: false },
      { key: "reduction", label: "较基准减排 (%)", suffix: "%", highlight: true },
    ],
    apiPayload: (data) => ({ tool: "carbon", ...data }),
  },
  efficiency: {
    title: "能效评估",
    desc: "评估高炉能源利用效率，分析节能潜力",
    icon: "fas fa-bolt",
    formFields: [
      { key: "cokeRate", label: "焦比", icon: "fas fa-weight", placeholder: "请输入焦比", unit: "kg/t", min: 0, step: 1 },
      { key: "coalRate", label: "煤比", icon: "fas fa-weight", placeholder: "请输入煤比", unit: "kg/t", min: 0, step: 1 },
    ],
    defaultData: { cokeRate: 360, coalRate: 160 },
    resultFields: [
      { key: "energyEfficiency", label: "综合能效", suffix: "%", highlight: false },
      { key: "grade", label: "能效等级", suffix: "", highlight: false },
    ],
    apiPayload: (data) => ({ tool: "efficiency", cokeRate: data.cokeRate, coalRate: data.coalRate }),
  },
  reduction: {
    title: "降碳潜力",
    desc: "分析对比行业基准，评估降碳空间",
    icon: "fas fa-arrow-down",
    formFields: [
      { key: "cokeRate", label: "焦比", icon: "fas fa-weight", placeholder: "请输入焦比", unit: "kg/t", min: 0, step: 1 },
      { key: "coalRate", label: "煤比", icon: "fas fa-weight", placeholder: "请输入煤比", unit: "kg/t", min: 0, step: 1 },
      { key: "production", label: "日产量", icon: "fas fa-industry", placeholder: "请输入日产量", unit: "t/d", min: 0, step: 100 },
    ],
    defaultData: { cokeRate: 360, coalRate: 160, production: 5000 },
    resultFields: [
      { key: "potential", label: "降碳潜力", suffix: "%", highlight: true },
      { key: "benchmark", label: "行业基准值", suffix: "", highlight: false },
      { key: "suggestions", label: "优化建议", suffix: "", highlight: false },
    ],
    apiPayload: (data) => ({ tool: "reduction", cokeRate: data.cokeRate, coalRate: data.coalRate, production: data.production }),
  },
  utilization: {
    title: "碳利用效率",
    desc: "计算碳素利用效率，优化燃料配比",
    icon: "fas fa-recycle",
    formFields: [
      { key: "cokeRate", label: "焦比", icon: "fas fa-weight", placeholder: "请输入焦比", unit: "kg/t", min: 0, step: 1 },
    ],
    defaultData: { cokeRate: 360 },
    resultFields: [
      { key: "utilizationRate", label: "碳利用效率", suffix: "%", highlight: false },
      { key: "benchmark", label: "行业基准", suffix: "%", highlight: false },
      { key: "gap", label: "与基准差距", suffix: "", highlight: true },
    ],
    apiPayload: (data) => ({ tool: "utilization", cokeRate: data.cokeRate }),
  },
};

export default {
  name: "SceneBlastTool",
  components: {
    Header,
    Footer,
  },
  data() {
    const toolId = this.$route?.params?.toolId || "carbon";
    const config = TOOL_CONFIG[toolId] || TOOL_CONFIG.carbon;
    return {
      toolId: toolId,
      formData: { ...config.defaultData },
      loading: false,
      result: null,
      error: "",
    };
  },
  computed: {
    toolConfig() {
      return TOOL_CONFIG[this.toolId] || TOOL_CONFIG.carbon;
    },
    toolTitle() {
      return this.toolConfig.title;
    },
    toolDesc() {
      return this.toolConfig.desc;
    },
    toolIcon() {
      return this.toolConfig.icon;
    },
    formFields() {
      return this.toolConfig.formFields;
    },
    resultFields() {
      return this.toolConfig.resultFields;
    },
  },
  watch: {
    "$route.params.toolId": {
      immediate: true,
      handler(val) {
        if (val && val !== this.toolId) {
          this.toolId = val;
          const config = TOOL_CONFIG[val] || TOOL_CONFIG.carbon;
          this.formData = { ...config.defaultData };
          this.result = null;
          this.error = "";
          this.loading = false;
        }
      },
    },
  },
  methods: {
    formatResult(value, suffix) {
      if (value === null || value === undefined || value === "") return "--";
      if (typeof value === "number") {
        if (suffix === "%") return value + "%";
        return value;
      }
      return value;
    },
    async runTool() {
      const config = this.toolConfig;
      this.error = "";
      this.result = null;
      this.loading = true;

      try {
        const payload = config.apiPayload(this.formData);
        const res = await axios.post("/api/tools/blastfurnace", payload);

        let data = res;
        if (res && res.data) {
          data = res.data;
        }
        if (data && data.code === 200 && data.data) {
          data = data.data;
        }
        if (data && data.result) {
          data = data.result;
        }

        if (!data.timestamp) {
          data.timestamp = new Date().toLocaleString("zh-CN");
        }

        this.result = data;
      } catch (err) {
        console.error(`高炉低碳分析 [${this.toolId}] 请求失败:`, err);
        this.error =
          err.response?.data?.message ||
          err.message ||
          "请求失败，请稍后重试";
        this.result = null;
      } finally {
        this.loading = false;
      }
    },
  },
};
</script>

<style scoped>
/* ==================== 基础样式 ==================== */
.scene-blast-tool {
  background: linear-gradient(180deg, #f0f4ff 0%, #ffffff 100%);
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

/* ==================== 面包屑 ==================== */
.mb-nav {
  color: #6b7a99;
  font-size: 15px;
  margin-top: 28px;
  margin-bottom: 10px;
}

.mb-nav p {
  margin: 0;
}

.mb-nav a {
  color: #6b7a99;
  font-size: 15px;
  transition: color 0.3s;
  text-decoration: none;
}

.mb-nav a:hover {
  color: #0046db;
}

.mb-nav span {
  color: #40c057;
}

/* ==================== 主内容 ==================== */
.main-content {
  padding: 30px 0 80px;
}

/* ==================== 工具详情卡片 ==================== */
.tool-detail-card {
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  padding: 32px;
  transition: box-shadow 0.3s;
}

/* ==================== 返回链接 ==================== */
.back-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #6b7a99;
  font-size: 14px;
  text-decoration: none;
  transition: color 0.3s;
  margin-bottom: 24px;
}

.back-link:hover {
  color: #0046db;
}

/* ==================== 工具头部 ==================== */
.tool-header {
  display: flex;
  align-items: center;
  gap: 18px;
  padding: 20px 24px;
  background: #e8f0fe;
  border-radius: 10px;
  margin-bottom: 28px;
}

.tool-header-icon {
  width: 52px;
  height: 52px;
  border-radius: 12px;
  background: #ffffff;
  color: #0046db;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  flex-shrink: 0;
  box-shadow: 0 1px 4px rgba(0, 70, 219, 0.1);
}

.tool-header-info {
  flex: 1;
}

.tool-header-title {
  font-size: 24px;
  font-weight: 700;
  color: #1a2744;
  margin: 0 0 4px;
}

.tool-header-desc {
  font-size: 14px;
  color: #5a6a8a;
  margin: 0;
  line-height: 1.5;
}

/* ==================== 分区标题 ==================== */
.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #1a2744;
  margin: 0 0 18px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-title i {
  color: #40c057;
  font-size: 15px;
}

/* ==================== 输入区域 ==================== */
.tool-form-section {
  margin-bottom: 24px;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  font-size: 14px;
  color: #4a5a78;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 6px;
}

.form-group label i {
  color: #0046db;
  font-size: 13px;
  width: 14px;
}

.input-wrap {
  display: flex;
  align-items: center;
  background: #f5f8ff;
  border: 1px solid #d6e0f0;
  border-radius: 8px;
  transition: border-color 0.3s, box-shadow 0.3s;
}

.input-wrap:focus-within {
  border-color: #0046db;
  box-shadow: 0 0 0 2px rgba(0, 70, 219, 0.12);
}

.input-wrap input {
  flex: 1;
  height: 42px;
  background: transparent;
  border: none;
  outline: none;
  color: #1a2744;
  font-size: 14px;
  padding: 0 12px;
  min-width: 0;
}

.input-wrap input::placeholder {
  color: #a8b5cc;
}

.input-suffix {
  padding: 0 12px;
  color: #8a9abb;
  font-size: 12px;
  white-space: nowrap;
}

/* ==================== 按钮 ==================== */
.btn-calc {
  width: 100%;
  height: 46px;
  border: none;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: #0046db;
  color: #ffffff;
}

.btn-calc:hover:not(:disabled) {
  background: #0035b0;
  box-shadow: 0 4px 14px rgba(0, 70, 219, 0.3);
  transform: translateY(-1px);
}

.btn-calc:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ==================== 错误消息 ==================== */
.error-msg {
  margin-bottom: 24px;
  padding: 12px 16px;
  text-align: center;
  color: #e74c3c;
  font-size: 14px;
  background: #fef0ef;
  border-radius: 10px;
  border: 1px solid #f5c6cb;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

/* ==================== 结果区域 ==================== */
.tool-result-section {
  padding-top: 24px;
  border-top: 2px solid #e8f0fe;
  animation: fadeIn 0.3s ease-out;
}

.result-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 14px;
  padding: 20px;
  background: #f5f8ff;
  border: 1px solid #e8f0fe;
  border-radius: 12px;
}

.result-item {
  text-align: center;
  padding: 10px 6px;
}

.result-value {
  display: block;
  font-size: 24px;
  font-weight: 700;
  color: #1a2744;
  line-height: 1.3;
  word-break: break-all;
}

.result-value.highlight-green {
  color: #40c057;
}

.result-label {
  display: block;
  font-size: 13px;
  color: #6b7a99;
  margin-top: 6px;
}

/* ==================== 动画 ==================== */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(12px);
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
}

@media (max-width: 992px) {
  .tool-detail-card {
    padding: 24px;
  }

  .tool-header-title {
    font-size: 22px;
  }

  .tool-header-desc {
    font-size: 13px;
  }
}

@media (max-width: 768px) {
  .scene-blast-tool {
    padding-top: 60px;
  }

  .mb-nav {
    font-size: 14px;
    margin-top: 15px;
  }

  .mb-nav a {
    font-size: 14px;
  }

  .main-content {
    padding: 20px 0 50px;
  }

  .tool-detail-card {
    padding: 18px;
  }

  .tool-header {
    flex-direction: column;
    text-align: center;
    gap: 12px;
    padding: 16px 18px;
  }

  .tool-header-title {
    font-size: 20px;
  }

  .tool-header-desc {
    font-size: 13px;
  }

  .form-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .result-grid {
    grid-template-columns: 1fr;
    gap: 10px;
    padding: 14px;
  }

  .result-value {
    font-size: 20px;
  }

  .back-link {
    font-size: 13px;
  }
}

@media (max-width: 576px) {
  .container {
    padding: 0 12px;
  }

  .tool-detail-card {
    padding: 14px;
  }
}
</style>
