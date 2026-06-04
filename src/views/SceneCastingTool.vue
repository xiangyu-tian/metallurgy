<template>
  <Header />
  <div class="SceneCastingTool">
    <!-- Hero Section -->
    <div class="hero-section">
      <div class="hero-overlay"></div>
      <div class="container hero-content">
        <h1 class="hero-title">{{ toolConfig.label }}</h1>
        <p class="hero-desc">{{ toolConfig.desc }}</p>
      </div>
    </div>

    <div class="main-wrapper">
      <!-- Breadcrumb -->
      <div class="mb-nav">
        <div class="container">
          <p>
            当前位置：<router-link to="/">首页</router-link> &gt;
            <router-link to="/scene/casting">连铸质量辅助决策</router-link> &gt;
            <span>{{ toolConfig.label }}</span>
          </p>
        </div>
      </div>

      <!-- Main Content -->
      <div class="container main-section">
        <div class="tool-detail-card" :class="{ 'card-highlight': toolId === 'segregation' }">
          <!-- Back Link -->
          <router-link to="/scene/casting" class="back-link">
            <i class="fas fa-arrow-left"></i>
            <span>返回场景首页</span>
          </router-link>

          <!-- Tool Header -->
          <div class="detail-header">
            <i :class="['fas', toolConfig.icon, 'header-icon']"></i>
            <h2>{{ toolConfig.label }}</h2>
            <span v-if="toolId === 'segregation'" class="badge-hot">推荐</span>
          </div>

          <!-- Tool Form -->
          <div class="detail-body">
            <div class="form-row">
              <div class="form-group">
                <label class="form-label">钢种</label>
                <input
                  type="text"
                  class="form-input"
                  v-model="form.steelGrade"
                  placeholder="如 Q235B"
                />
              </div>
              <div class="form-group" v-if="toolConfig.showSectionSize">
                <label class="form-label">断面</label>
                <input
                  type="text"
                  class="form-input"
                  v-model="form.sectionSize"
                  placeholder="如 200x200mm"
                />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label class="form-label">拉速 (m/min)</label>
                <input
                  type="number"
                  class="form-input"
                  v-model.number="form.castingSpeed"
                  step="0.1"
                  placeholder="如 1.2"
                />
              </div>
              <div class="form-group">
                <label class="form-label">过热度 (°C)</label>
                <input
                  type="number"
                  class="form-input"
                  v-model.number="form.superheat"
                  placeholder="如 30"
                />
              </div>
            </div>

            <!-- Submit Button -->
            <button
              class="btn-submit"
              @click="submitTool"
              :disabled="loading"
            >
              <i
                class="fas"
                :class="loading ? 'fa-spinner fa-spin' : 'fa-play'"
              ></i>
              {{ loading ? '评估中...' : '开始评估' }}
            </button>

            <!-- Error State -->
            <div v-if="error" class="result-error">
              <i class="fas fa-exclamation-triangle"></i>
              <p>{{ error }}</p>
            </div>

            <!-- Loading State -->
            <div v-if="loading" class="result-loading">
              <i class="fas fa-spinner fa-spin"></i>
              <p>正在分析工艺参数，请稍候...</p>
            </div>

            <!-- Result Display -->
            <div v-if="result && !loading" class="result-section">

              <!-- Tool: quality -->
              <div v-if="toolId === 'quality'" class="quality-result">
                <div
                  class="score-badge"
                  :style="{ backgroundColor: getScoreColor(result.score) }"
                >
                  <span class="score-value">{{ result.score }}</span>
                  <span class="score-unit">分</span>
                </div>
                <div
                  v-if="result.suggestions && result.suggestions.length"
                  class="suggestions-box"
                >
                  <h4 class="suggestions-title">
                    <i class="fas fa-lightbulb"></i> 优化建议
                  </h4>
                  <ul class="suggestions-list">
                    <li v-for="(s, i) in result.suggestions" :key="i">
                      {{ s }}
                    </li>
                  </ul>
                </div>
              </div>

              <!-- Tool: segregation -->
              <div v-if="toolId === 'segregation'" class="segregation-result">
                <div class="metrics-grid">
                  <div class="metric-item">
                    <span class="metric-label">碳极差1</span>
                    <span class="metric-value">{{ result.carbonDifferential1 }}</span>
                  </div>
                  <div class="metric-item">
                    <span class="metric-label">碳极差2</span>
                    <span class="metric-value">{{ result.carbonDifferential2 }}</span>
                  </div>
                  <div class="metric-item">
                    <span class="metric-label">偏析指数</span>
                    <span class="metric-value">{{ result.carbonIndex }}</span>
                  </div>
                  <div class="metric-item">
                    <span class="metric-label">评级</span>
                    <span
                      class="metric-value grade"
                      :class="'grade-' + (result.grade || '').toLowerCase()"
                    >
                      {{ result.grade }}
                    </span>
                  </div>
                </div>
              </div>

              <!-- Tool: crack -->
              <div v-if="toolId === 'crack'" class="metrics-grid cols-2">
                <div class="metric-item">
                  <span class="metric-label">裂纹指数</span>
                  <span class="metric-value">{{ result.crackIndex }}</span>
                </div>
                <div class="metric-item">
                  <span class="metric-label">风险等级</span>
                  <span
                    class="metric-value"
                    :class="'risk-' + (result.riskLevel || '').toLowerCase()"
                  >
                    {{ result.riskLevel }}
                  </span>
                </div>
              </div>

              <!-- Tool: porosity -->
              <div v-if="toolId === 'porosity'" class="metrics-grid cols-2">
                <div class="metric-item">
                  <span class="metric-label">疏松指数</span>
                  <span class="metric-value">{{ result.porosityIndex }}</span>
                </div>
                <div class="metric-item">
                  <span class="metric-label">严重程度</span>
                  <span
                    class="metric-value"
                    :class="'severity-' + (result.severityLevel || '').toLowerCase()"
                  >
                    {{ result.severityLevel }}
                  </span>
                </div>
              </div>

            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  <Footer />
</template>

<script>
import Header from "@/components/Header.vue";
import Footer from "@/components/Footer.vue";
import axios from "axios";

const TOOL_MAP = {
  quality: {
    label: "质量综合评分",
    icon: "fa-star",
    desc: "基于工艺参数综合评估连铸坯质量等级",
    showSectionSize: true,
  },
  segregation: {
    label: "偏析预测",
    icon: "fa-chart-line",
    desc: "预测碳极差和偏析指数，优化连铸工艺",
    showSectionSize: true,
  },
  crack: {
    label: "表面裂纹预测",
    icon: "fa-exclamation-triangle",
    desc: "评估铸坯表面裂纹风险等级",
    showSectionSize: false,
  },
  porosity: {
    label: "中心疏松预测",
    icon: "fa-circle",
    desc: "预测铸坯中心疏松程度",
    showSectionSize: false,
  },
};

export default {
  name: "SceneCastingTool",
  components: {
    Header,
    Footer,
  },
  data() {
    return {
      form: {
        steelGrade: "Q235B",
        sectionSize: "200x200mm",
        castingSpeed: 1.2,
        superheat: 30,
      },
      loading: false,
      error: "",
      result: null,
    };
  },
  computed: {
    toolId() {
      return this.$route.params.toolId;
    },
    toolConfig() {
      return TOOL_MAP[this.toolId] || TOOL_MAP.quality;
    },
  },
  methods: {
    getScoreColor(score) {
      if (typeof score === "number") {
        if (score >= 85) return "#52c41a";
        if (score >= 70) return "#1890ff";
        if (score >= 55) return "#faad14";
        return "#ff4d4f";
      }
      return "#1890ff";
    },
    async submitTool() {
      this.error = "";
      this.result = null;
      this.loading = true;

      try {
        const payload = {
          tool: this.toolId,
          steelGrade: this.form.steelGrade,
          castingSpeed: Number(this.form.castingSpeed),
          superheat: Number(this.form.superheat),
        };
        if (this.toolConfig.showSectionSize) {
          payload.sectionSize = this.form.sectionSize;
        }

        const response = await axios.post("/api/tools/casting", payload);
        this.result = response.data;
      } catch (err) {
        if (err.response && err.response.data && err.response.data.message) {
          this.error = err.response.data.message;
        } else if (err.message) {
          this.error = err.message;
        } else {
          this.error = "请求失败，请稍后重试";
        }
      } finally {
        this.loading = false;
      }
    },
  },
};
</script>

<style scoped>
/* ===================== Hero Section ===================== */
.hero-section {
  position: relative;
  padding-top: 80px;
  height: 240px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #0a1628 0%, #002a67 40%, #0046db 100%);
}

.hero-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    135deg,
    rgba(0, 22, 58, 0.88),
    rgba(0, 70, 219, 0.6),
    rgba(0, 22, 58, 0.85)
  );
}

.hero-content {
  position: relative;
  z-index: 1;
  text-align: center;
}

.hero-title {
  font-size: 36px;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: 3px;
  margin-bottom: 12px;
}

.hero-desc {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.75);
  max-width: 560px;
  margin: 0 auto;
  line-height: 1.6;
}

/* ===================== Main Wrapper (light bg) ===================== */
.main-wrapper {
  background-color: #f5f7fa;
}

/* ===================== Breadcrumb ===================== */
.mb-nav {
  background: #ffffff;
  border-bottom: 1px solid #e8ecf1;
}

.mb-nav p {
  font-size: 14px;
  padding: 14px 0;
  color: #8c8c8c;
  margin: 0;
}

.mb-nav a {
  color: #8c8c8c;
  text-decoration: none;
  transition: color 0.3s;
}

.mb-nav a:hover {
  color: #0046db;
}

.mb-nav span {
  color: #0046db;
  font-weight: 500;
}

/* ===================== Main Layout ===================== */
.main-section {
  padding: 40px 0 80px;
}

/* ===================== Tool Detail Card ===================== */
.tool-detail-card {
  max-width: 700px;
  margin: 0 auto;
  background: #ffffff;
  border: 1px solid #eef1f6;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  overflow: hidden;
  transition: box-shadow 0.3s;
}

.tool-detail-card:hover {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
}

/* Highlighted card (偏析预测) */
.card-highlight {
  border: 1.5px solid #0046db;
  box-shadow: 0 2px 12px rgba(0, 70, 219, 0.12);
}

/* ===================== Back Link ===================== */
.back-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 16px 24px 0;
  font-size: 13px;
  color: #8c8c8c;
  text-decoration: none;
  transition: color 0.3s;
}

.back-link:hover {
  color: #0046db;
}

.back-link i {
  font-size: 12px;
}

/* ===================== Detail Header ===================== */
.detail-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 24px 14px;
  border-bottom: 1px solid #eef1f6;
}

.header-icon {
  color: #0046db;
  font-size: 20px;
  width: 22px;
  text-align: center;
}

.detail-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #1a1a2e;
}

/* Badge */
.badge-hot {
  margin-left: auto;
  display: inline-block;
  padding: 2px 12px;
  font-size: 11px;
  font-weight: 700;
  border-radius: 10px;
  background: #ff4d4f;
  color: #ffffff;
  letter-spacing: 1px;
}

/* ===================== Detail Body ===================== */
.detail-body {
  padding: 20px 24px 28px;
}

/* ===================== Form Inputs ===================== */
.form-row {
  display: flex;
  gap: 14px;
  margin-bottom: 4px;
}

.form-row .form-group {
  flex: 1;
}

.form-group {
  margin-bottom: 14px;
}

.form-label {
  display: block;
  font-size: 13px;
  color: #595959;
  margin-bottom: 6px;
  font-weight: 500;
}

.form-input {
  display: block;
  width: 100%;
  height: 40px;
  padding: 0 12px;
  background-color: #ffffff;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  font-size: 14px;
  color: #1a1a2e;
  outline: none;
  transition: border-color 0.3s, box-shadow 0.3s;
  box-sizing: border-box;
}

.form-input:focus {
  border-color: #0046db;
  box-shadow: 0 0 0 2px rgba(0, 70, 219, 0.1);
}

.form-input::placeholder {
  color: #bfbfbf;
}

/* Remove number input spinners */
.form-input[type="number"]::-webkit-outer-spin-button,
.form-input[type="number"]::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}
.form-input[type="number"] {
  -moz-appearance: textfield;
}

/* ===================== Submit Button ===================== */
.btn-submit {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  height: 44px;
  margin-top: 20px;
  border: none;
  border-radius: 8px;
  background-color: #0046db;
  color: #ffffff;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-submit:hover:not(:disabled) {
  background-color: #0038b3;
  box-shadow: 0 4px 16px rgba(0, 70, 219, 0.35);
}

.btn-submit:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* ===================== Result States ===================== */
.result-error {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 16px;
  padding: 10px 14px;
  background: #fff2f0;
  border: 1px solid #ffccc7;
  border-radius: 6px;
  color: #ff4d4f;
  font-size: 13px;
}

.result-error i {
  font-size: 16px;
  flex-shrink: 0;
}

.result-error p {
  margin: 0;
}

.result-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  margin-top: 20px;
  text-align: center;
  color: #8c8c8c;
  font-size: 13px;
}

.result-loading i {
  font-size: 28px;
  color: #0046db;
}

.result-loading p {
  margin: 0;
}

/* ===================== Result Section ===================== */
.result-section {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #eef1f6;
}

/* ------ Score Badge (quality) ------ */
.quality-result {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.score-badge {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100px;
  height: 100px;
  border-radius: 50%;
  color: #ffffff;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.score-value {
  font-size: 36px;
  font-weight: 700;
  line-height: 1;
}

.score-unit {
  font-size: 13px;
  opacity: 0.85;
  margin-top: 2px;
}

/* Suggestions */
.suggestions-box {
  width: 100%;
  background: #fffbe6;
  border: 1px solid #ffe58f;
  border-radius: 8px;
  padding: 16px 18px;
}

.suggestions-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 600;
  color: #d48806;
  margin: 0 0 10px 0;
}

.suggestions-title i {
  font-size: 14px;
}

.suggestions-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.suggestions-list li {
  position: relative;
  padding-left: 16px;
  margin-bottom: 6px;
  font-size: 13px;
  color: #595959;
  line-height: 1.6;
}

.suggestions-list li::before {
  content: "";
  position: absolute;
  left: 0;
  top: 9px;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: #0046db;
}

.suggestions-list li:last-child {
  margin-bottom: 0;
}

/* ------ Segregation Result ------ */
.segregation-result {
  width: 100%;
}

/* ------ Metrics Grid (segregation, crack, porosity) ------ */
.metrics-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

.metrics-grid.cols-2 {
  grid-template-columns: 1fr 1fr;
}

.metric-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 16px 18px;
  background: #f9fafb;
  border: 1px solid #eef1f6;
  border-radius: 8px;
  text-align: center;
}

.metric-label {
  font-size: 12px;
  color: #8c8c8c;
  font-weight: 500;
}

.metric-value {
  font-size: 22px;
  font-weight: 700;
  color: #1a1a2e;
}

/* Grade colors */
.metric-value.grade {
  font-size: 18px;
}
.grade-a,
.grade-优秀,
.grade-excellent {
  color: #52c41a;
}
.grade-b,
.grade-良好,
.grade-good {
  color: #1890ff;
}
.grade-c,
.grade-中等,
.grade-fair {
  color: #faad14;
}
.grade-d,
.grade-差,
.grade-poor {
  color: #ff4d4f;
}

/* Risk colors */
.risk-低,
.risk-low {
  color: #52c41a;
}
.risk-中,
.risk-medium {
  color: #faad14;
}
.risk-高,
.risk-high {
  color: #ff4d4f;
}

/* Severity colors */
.severity-轻微,
.severity-mild {
  color: #52c41a;
}
.severity-中等,
.severity-moderate {
  color: #faad14;
}
.severity-严重,
.severity-severe {
  color: #ff4d4f;
}

/* ===================== Responsive ===================== */
@media (max-width: 1200px) {
  .hero-title {
    font-size: 30px;
  }
  .hero-section {
    height: 220px;
  }
}

@media (max-width: 1000px) {
  .hero-title {
    font-size: 24px;
    letter-spacing: 2px;
  }
  .hero-desc {
    font-size: 14px;
  }
  .hero-section {
    height: 200px;
  }
}

@media (max-width: 768px) {
  .hero-title {
    font-size: 22px;
  }
  .hero-desc {
    font-size: 14px;
  }
  .hero-section {
    height: 180px;
  }
  .main-section {
    padding: 24px 0 60px;
  }
  .detail-header {
    padding: 10px 18px 12px;
  }
  .detail-header h2 {
    font-size: 16px;
  }
  .detail-body {
    padding: 16px 18px 24px;
  }
  .form-row {
    flex-direction: column;
    gap: 0;
  }
  .back-link {
    padding: 14px 18px 0;
  }
  .score-badge {
    width: 80px;
    height: 80px;
  }
  .score-value {
    font-size: 28px;
  }
  .metrics-grid {
    gap: 10px;
  }
  .metric-value {
    font-size: 18px;
  }
}
</style>
