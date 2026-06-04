<template>
  <Header></Header>
  <div class="scene-converter-tool">
    <!-- Breadcrumb -->
    <div class="mb-nav">
      <div class="container">
        <p>
          当前位置：<router-link to="/">首页</router-link> &gt;
          <router-link to="/scenes">智能场景</router-link> &gt;
          <router-link to="/scene/converter">转炉炼钢工艺优化</router-link> &gt;
          <span>{{ toolConfig.title }}</span>
        </p>
      </div>
    </div>

    <!-- Main Content -->
    <div class="container main-content">
      <!-- Back Link -->
      <router-link to="/scene/converter" class="back-link">
        <i class="fas fa-arrow-left"></i> 返回工具列表
      </router-link>

      <!-- Tool Header -->
      <div class="tool-header">
        <div class="tool-header-icon" :class="toolConfig.iconClass">
          <i :class="['fas', toolConfig.icon]"></i>
        </div>
        <div class="tool-header-info">
          <h1 class="tool-header-title">{{ toolConfig.title }}</h1>
          <p class="tool-header-desc">{{ toolConfig.description }}</p>
        </div>
      </div>

      <!-- Tool Form Card -->
      <div class="tool-card">
        <div class="tool-card-body">
          <!-- Form Section -->
          <div class="form-section">
            <div
              class="form-group"
              v-for="field in toolConfig.fields"
              :key="field.key"
            >
              <label :for="'field-' + field.key">
                <i :class="['fas', field.icon]"></i>
                {{ field.label }}
              </label>
              <input
                :id="'field-' + field.key"
                v-model.number="form[field.key]"
                type="number"
                :step="field.step"
                :min="field.min"
                :max="field.max"
                :placeholder="String(field.default)"
              />
            </div>

            <button
              class="btn-calculate"
              :disabled="loading"
              @click="handleCalculate"
            >
              <i :class="loading ? 'fas fa-spinner fa-spin' : 'fas fa-calculator'"></i>
              {{ loading ? '计算中...' : '开始计算' }}
            </button>
          </div>

          <!-- Error -->
          <div v-if="error" class="error-msg">
            <i class="fas fa-exclamation-circle"></i>
            <span>{{ error }}</span>
          </div>

          <!-- Result -->
          <div v-if="result && !loading" class="result-box">
            <h3 class="result-title">
              <i class="fas fa-chart-bar"></i> 计算结果
            </h3>
            <div class="result-items">
              <div
                class="result-item"
                v-for="(item, key) in resultItems"
                :key="key"
              >
                <span class="result-label">{{ item.label }}</span>
                <span class="result-value">{{ formatValue(item.value) }}</span>
              </div>
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
  endpoint: {
    title: "终点预测",
    description: "根据铁水成分和工艺参数预测转炉终点碳含量和温度",
    icon: "fa-bullseye",
    iconClass: "icon-endpoint",
    fields: [
      { key: "siContent", label: "铁水Si含量 (%)", icon: "fa-flask", default: 0.5, step: 0.1, min: 0, max: 5 },
      { key: "targetCarbon", label: "目标碳含量 (%)", icon: "fa-burn", default: 0.05, step: 0.01, min: 0, max: 2 },
      { key: "steelTemp", label: "钢水温度 (°C)", icon: "fa-temperature-high", default: 1600, step: 1, min: 1400, max: 1800 },
      { key: "oxygenFlow", label: "氧枪流量 (Nm³/h)", icon: "fa-wind", default: 25000, step: 100, min: 5000, max: 50000 },
    ],
    apiTool: "endpoint",
    resultMapping: {
      endpointC: "终点碳含量 (%)",
      carbonContent: "终点碳含量 (%)",
      endpointTemperature: "终点温度 (°C)",
      temperature: "终点温度 (°C)",
      oxygenConsumption: "耗氧量 (Nm³)",
      slagBasicity: "炉渣碱度 R",
      r: "炉渣碱度 R",
    },
  },
  oxygen: {
    title: "氧耗计算",
    description: "计算冶炼过程所需氧气消耗量",
    icon: "fa-gauge-high",
    iconClass: "icon-oxygen",
    fields: [
      { key: "siContent", label: "铁水Si含量 (%)", icon: "fa-flask", default: 0.5, step: 0.1, min: 0, max: 5 },
      { key: "targetCarbon", label: "目标碳含量 (%)", icon: "fa-burn", default: 0.05, step: 0.01, min: 0, max: 2 },
    ],
    apiTool: "oxygen",
    resultMapping: {
      oxygenConsumption: "耗氧量 (Nm³)",
      oxygenConsumed: "耗氧量 (Nm³)",
    },
  },
  temperature: {
    title: "温度预测",
    description: "预测转炉终点钢水温度，辅助温控决策",
    icon: "fa-temperature-high",
    iconClass: "icon-temperature",
    fields: [
      { key: "siContent", label: "铁水Si含量 (%)", icon: "fa-flask", default: 0.5, step: 0.1, min: 0, max: 5 },
      { key: "targetCarbon", label: "目标碳含量 (%)", icon: "fa-burn", default: 0.05, step: 0.01, min: 0, max: 2 },
      { key: "steelTemp", label: "钢水温度 (°C)", icon: "fa-temperature-high", default: 1600, step: 1, min: 1400, max: 1800 },
    ],
    apiTool: "temperature",
    resultMapping: {
      temperature: "终点温度 (°C)",
      endpointTemperature: "终点温度 (°C)",
      predictedTemperature: "终点温度 (°C)",
    },
  },
  slag: {
    title: "渣碱度计算",
    description: "计算炉渣碱度，优化造渣制度",
    icon: "fa-flask",
    iconClass: "icon-slag",
    fields: [
      { key: "siContent", label: "铁水Si含量 (%)", icon: "fa-flask", default: 0.5, step: 0.1, min: 0, max: 5 },
    ],
    apiTool: "slag",
    resultMapping: {
      basicity: "炉渣碱度 R",
      slagBasicity: "炉渣碱度 R",
      r: "炉渣碱度 R",
      limeConsumption: "石灰消耗 (kg)",
      lime: "石灰消耗 (kg)",
    },
  },
};

export default {
  name: "SceneConverterTool",
  components: {
    Header,
    Footer,
  },
  data() {
    const toolId = this.$route?.params?.toolId || "endpoint";
    const config = TOOL_CONFIG[toolId] || TOOL_CONFIG.endpoint;
    const form = {};
    config.fields.forEach((f) => {
      form[f.key] = f.default;
    });
    return {
      toolId,
      toolConfig: config,
      form,
      loading: false,
      result: null,
      error: "",
    };
  },
  computed: {
    resultItems() {
      if (!this.result) return [];
      const mapping = this.toolConfig.resultMapping;
      const items = [];
      for (const [key, label] of Object.entries(mapping)) {
        if (this.result[key] !== undefined && this.result[key] !== null) {
          items.push({ label, value: this.result[key] });
        }
      }
      for (const [key, value] of Object.entries(this.result)) {
        if (mapping[key] === undefined && typeof value === "number") {
          const label = key
            .replace(/([A-Z])/g, " $1")
            .replace(/^./, (s) => s.toUpperCase())
            .replace(/\br\b/i, "R");
          items.push({ label, value });
        }
      }
      return items;
    },
  },
  watch: {
    $route(to) {
      const toolId = to.params?.toolId || "endpoint";
      const config = TOOL_CONFIG[toolId] || TOOL_CONFIG.endpoint;
      const form = {};
      config.fields.forEach((f) => {
        form[f.key] = f.default;
      });
      this.toolId = toolId;
      this.toolConfig = config;
      this.form = form;
      this.loading = false;
      this.result = null;
      this.error = "";
    },
  },
  methods: {
    handleCalculate() {
      this.loading = true;
      this.error = "";
      this.result = null;

      const payload = { tool: this.toolConfig.apiTool };
      this.toolConfig.fields.forEach((f) => {
        payload[f.key] = this.form[f.key];
      });

      axios
        .post("/api/tools/converter", payload)
        .then((response) => {
          if (response.data && response.data.code === 200) {
            const data = response.data.data;
            if (data && typeof data === "object") {
              this.result = data.result || data;
            } else {
              this.result = { 结果: String(data) };
            }
          } else if (response.data && typeof response.data === "object") {
            this.result = response.data;
          } else {
            this.error = response.data?.message || "请求失败，请稍后重试";
          }
        })
        .catch((err) => {
          this.error =
            err.response?.data?.message ||
            err.message ||
            "网络错误，请检查网络连接后重试";
        })
        .finally(() => {
          this.loading = false;
        });
    },

    formatValue(value) {
      if (typeof value === "number") {
        if (Number.isInteger(value)) return value.toString();
        if (Math.abs(value) < 0.01 && value !== 0) return value.toExponential(2);
        return value.toFixed(2);
      }
      return String(value);
    },
  },
};
</script>

<style scoped>
/* ==================== Base ==================== */
.scene-converter-tool {
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
  padding: 30px 0 60px;
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

/* ==================== Back Link ==================== */
.back-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #0046db;
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 24px;
  transition: all 0.3s;
}

.back-link:hover {
  color: #0033a0;
  transform: translateX(-3px);
}

/* ==================== Tool Header ==================== */
.tool-header {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 30px;
  padding: 28px 32px;
  background: linear-gradient(135deg, #002266 0%, #0046db 40%, #0055ff 100%);
  border-radius: 14px;
  position: relative;
  overflow: hidden;
}

.tool-header::before {
  content: "";
  position: absolute;
  top: -50%;
  right: -10%;
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.05) 0%, transparent 70%);
  border-radius: 50%;
  pointer-events: none;
}

.tool-header-icon {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  color: #fff;
  flex-shrink: 0;
  position: relative;
  z-index: 1;
  background: rgba(255, 255, 255, 0.18);
  backdrop-filter: blur(8px);
  border: 2px solid rgba(255, 255, 255, 0.25);
}

.tool-header-info {
  position: relative;
  z-index: 1;
}

.tool-header-title {
  font-size: 26px;
  color: #fff;
  margin: 0 0 6px;
  font-weight: 700;
}

.tool-header-desc {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.8);
  margin: 0;
  line-height: 1.5;
}

/* ==================== Enterprise Card ==================== */
.tool-card {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid #f0f0f0;
  transition: box-shadow 0.3s, border-color 0.3s, transform 0.3s;
  overflow: hidden;
}

.tool-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 70, 219, 0.12);
  border-color: #e0ebff;
}

.tool-card-body {
  padding: 32px;
}

/* ==================== Form Section ==================== */
.form-section {
  max-width: 500px;
}

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
  width: 16px;
}

.form-group input {
  padding: 11px 14px;
  background: #fff;
  border: 1px solid #dcdfe6;
  border-radius: 8px;
  color: #333;
  font-size: 14px;
  transition: all 0.3s;
  outline: none;
}

.form-group input:focus {
  border-color: #0046db;
  box-shadow: 0 0 0 3px rgba(0, 70, 219, 0.1);
}

.form-group input::placeholder {
  color: #c0c4cc;
}

/* ==================== Button ==================== */
.btn-calculate {
  width: 100%;
  max-width: 500px;
  padding: 13px 24px;
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
  margin-top: 8px;
}

.btn-calculate:hover:not(:disabled) {
  background: #0033a0;
  transform: translateY(-1px);
  box-shadow: 0 4px 14px rgba(0, 70, 219, 0.3);
}

.btn-calculate:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

/* ==================== Error Message ==================== */
.error-msg {
  margin-top: 18px;
  padding: 12px 16px;
  background: #fef0f0;
  border: 1px solid #fde2e2;
  border-radius: 8px;
  color: #f56c6c;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.error-msg i {
  font-size: 16px;
  flex-shrink: 0;
}

/* ==================== Result Box ==================== */
.result-box {
  margin-top: 28px;
  padding: 24px;
  background: #f5f8ff;
  border: 1px solid #e0ebff;
  border-radius: 10px;
  animation: fadeIn 0.3s ease-out;
}

.result-title {
  font-size: 17px;
  color: #0046db;
  margin: 0 0 18px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.result-items {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.result-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #fff;
  border: 1px solid #e0ebff;
  border-radius: 8px;
}

.result-label {
  font-size: 13px;
  color: #666;
  font-weight: 500;
}

.result-value {
  font-size: 16px;
  color: #0046db;
  font-weight: 700;
  font-family: "Courier New", Courier, monospace;
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

/* ==================== Responsive ==================== */
@media (max-width: 1200px) {
  .container {
    max-width: 960px;
  }
}

@media (max-width: 992px) {
  .tool-header-title {
    font-size: 22px;
  }

  .tool-header-icon {
    width: 56px;
    height: 56px;
    font-size: 24px;
  }
}

@media (max-width: 768px) {
  .main-content {
    padding: 20px 0 40px;
  }

  .tool-header {
    flex-direction: column;
    align-items: flex-start;
    padding: 24px;
    gap: 14px;
  }

  .tool-header-title {
    font-size: 20px;
  }

  .tool-header-desc {
    font-size: 13px;
  }

  .tool-card-body {
    padding: 24px 20px;
  }

  .form-section {
    max-width: 100%;
  }

  .btn-calculate {
    max-width: 100%;
  }

  .result-items {
    grid-template-columns: 1fr;
  }

  .result-box {
    padding: 18px;
  }
}

@media (max-width: 576px) {
  .container {
    padding: 0 12px;
  }

  .tool-card-body {
    padding: 20px 16px;
  }

  .tool-header {
    padding: 20px 16px;
  }

  .form-group input {
    padding: 10px 12px;
    font-size: 13px;
  }

  .result-value {
    font-size: 14px;
  }
}
</style>
