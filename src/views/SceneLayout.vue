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
        <!-- 模型调用面板 -->
        <div v-if="showInvokePanel" class="invoke-panel">
          <div class="invoke-header">
            <div>
              <h2><i class="fas fa-cogs"></i> {{ invokeModelName }}</h2>
              <p class="module-desc">模型ID: {{ invokeModelId }} · 通过统一模型微服务调用</p>
            </div>
            <button class="btn-close" @click="closeInvoke"><i class="fas fa-times"></i> 关闭</button>
          </div>

          <!-- 参数输入 -->
          <div class="invoke-section">
            <h3><i class="fas fa-keyboard"></i> 参数输入</h3>
            <div v-if="schemaLoading" class="loading-hint"><i class="fas fa-spinner fa-spin"></i> 加载参数定义...</div>
            <div v-else class="invoke-form">
              <div class="form-row" v-for="field in invokeFields" :key="field.name">
                <label :for="'f-' + field.name">
                  {{ field.label }}
                  <span v-if="field.required" class="required-star">*</span>
                </label>
                <div class="field-control">
                  <!-- 枚举类型 → 下拉菜单 -->
                  <select v-if="field.enum" :id="'f-' + field.name"
                    v-model="invokeParams[field.name]">
                    <option value="">请选择 {{ field.label }}</option>
                    <option v-for="opt in field.enum" :key="opt" :value="opt">{{ opt }}</option>
                  </select>
                  <!-- 数值类型 -->
                  <input v-else-if="field.type === 'number'" :id="'f-' + field.name"
                    type="number" v-model.number="invokeParams[field.name]"
                    :placeholder="field.placeholder || '输入数值'"
                    :min="field.min" :max="field.max" step="any">
                  <!-- 文本类型 -->
                  <input v-else :id="'f-' + field.name"
                    type="text" v-model="invokeParams[field.name]"
                    :placeholder="field.placeholder || '输入' + field.label">
                  <!-- 单位后缀 -->
                  <span v-if="field.unit" class="field-unit">{{ field.unit }}</span>
                </div>
                <!-- 字段说明 -->
                <div v-if="field.description" class="field-desc">{{ field.description }}</div>
              </div>

              <!-- 单位换算辅助（A001 专用） -->
              <div v-if="invokeModelId === 'A001'" class="unit-help-section">
                <button class="btn-link" @click="toggleUnitHelp">
                  <i class="fas" :class="showUnitHelp ? 'fa-chevron-up' : 'fa-chevron-down'"></i>
                  查看可用单位
                </button>
                <div v-if="showUnitHelp" class="unit-help-grid">
                  <div v-for="(units, category) in commonUnits" :key="category" class="unit-group">
                    <h5>{{ category }}</h5>
                    <div class="unit-chips">
                      <span v-for="u in units" :key="u" class="unit-chip"
                        :class="{ active: invokeParams.source_unit === u || invokeParams.target_unit === u }"
                        @click="setUnitParam($event.target.closest('.unit-chip').dataset.field || 'source_unit', u)"
                        @click.shift="setUnitParam('target_unit', u)"
                      >{{ u }}</span>
                    </div>
                  </div>
                  <p class="unit-help-tip"><i class="fas fa-info-circle"></i> 点击选择源单位，Shift+点击选择目标单位</p>
                </div>
              </div>
            </div>
            <button class="btn-search" @click="doInvoke" :disabled="invokeLoading || schemaLoading">
              <i class="fas fa-play"></i> {{ invokeLoading ? '计算中...' : '执行计算' }}
            </button>
          </div>

          <!-- 计算结果 -->
          <div v-if="invokeResult" class="invoke-section invoke-result">
            <h3><i class="fas fa-chart-bar"></i> 计算结果</h3>
            <div class="result-status" :class="invokeResult.status">
              <i class="fas" :class="invokeResult.status === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'"></i>
              {{ invokeResult.status === 'success' ? '计算成功' : '计算失败' }}
            </div>
            <pre v-if="invokeResult.result" class="result-json">{{ JSON.stringify(invokeResult.result, null, 2) }}</pre>
            <div v-if="invokeResult.error" class="result-error">
              <i class="fas fa-times-circle"></i> {{ invokeResult.error }}
              <span v-if="invokeResult.error_code" class="error-code">({{ invokeResult.error_code }})</span>
            </div>
            <div v-if="invokeResult.provenance && invokeResult.provenance.length" class="result-provenance">
              <h4><i class="fas fa-database"></i> 数据来源</h4>
              <div v-for="p in invokeResult.provenance" :key="p.dataset_id" class="provenance-item">
                <code>{{ p.dataset_id }}</code> {{ p.name }} <span v-if="p.version">v{{ p.version }}</span>
              </div>
            </div>
            <div v-if="invokeResult.runtime_ms" class="result-meta">
              耗时: {{ invokeResult.runtime_ms }}ms
            </div>
          </div>
        </div>

        <!-- 常规场景内容（模型调用面板未激活时显示） -->
        <template v-if="!showInvokePanel">
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
        </template>
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
      { id: 'segregation', name: '偏析预测', icon: 'fa-chart-line', route: '/segregation/', badge: '推荐',
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
  data() {
    return {
      activeScene: 'thermodynamics',
      scenes: Object.values(sceneData),
      // 模型调用模式
      invokeModelId: '',
      invokeModelName: '',
      invokeFields: [],          // 从后端 API 获取的字段定义
      invokeParams: {},
      showInvokePanel: false,
      invokeResult: null,
      invokeLoading: false,
      schemaLoading: false,
      availableUnits: [],
      showUnitHelp: false,
    };
  },
  computed: {
    currentScene() { return sceneData[this.activeScene] || sceneData.thermodynamics; },
    // 常用单位列表（供 A001 等模型展示）
    commonUnits() {
      return {
        temperature: ['K', '°C', '°F'],
        mass: ['kg', 'g', 't', 'lb'],
        pressure: ['Pa', 'kPa', 'MPa', 'atm', 'bar', 'psi'],
        energy: ['J', 'kJ', 'cal'],
        length: ['m', 'cm', 'mm', 'km'],
        time: ['s', 'min', 'h'],
      };
    },
  },
  methods: {
    doInvoke() {
      this.invokeLoading = true;
      this.invokeResult = null;
      const modelId = this.invokeModelId;

      // 收集参数
      const params = {};
      for (const field of this.invokeFields) {
        const val = this.invokeParams[field.name];
        if (val !== '' && val !== undefined && val !== null) {
          params[field.name] = field.type === 'number' ? parseFloat(val) : val;
        }
      }

      fetch(`/api/v1/models/${modelId}/invoke`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ input: params, options: { validate_boundary: true, return_provenance: true } })
      })
      .then(r => r.json())
      .then(data => {
        this.invokeResult = data;
        this.invokeLoading = false;
      })
      .catch(err => {
        this.invokeResult = { status: 'error', error: '网络错误或微服务不可用', error_code: 'NETWORK_ERROR' };
        this.invokeLoading = false;
      });
    },
    closeInvoke() {
      this.showInvokePanel = false;
      this.invokeModelId = '';
      this.invokeFields = [];
      this.invokeParams = {};
      this.invokeResult = null;
      this.$router.push('/scene');
    },
    // 从后端获取模型 Schema
    loadModelSchema(modelId) {
      this.schemaLoading = true;
      fetch(`/api/v1/models/${modelId}`)
        .then(r => r.json())
        .then(data => {
          const schema = data.input_schema_json || {};
          const props = schema.properties || {};
          const required = schema.required || [];
          this.invokeFields = Object.entries(props).map(([name, def]) => ({
            name,
            label: def.label || name,
            type: def.type || 'string',
            required: required.includes(name),
            unit: def.unit || '',
            min: def.min_value,
            max: def.max_value,
            enum: def.enum || null,
            default: def.default,
            placeholder: def.placeholder || '',
            description: def.description || '',
          }));
          // 设置默认值
          for (const f of this.invokeFields) {
            if (f.default !== undefined && f.default !== null) {
              this.invokeParams[f.name] = f.default;
            }
          }
          this.schemaLoading = false;
        })
        .catch(err => {
          console.warn('获取 Schema 失败，使用基础表单', err);
          // 降级：使用基础文本表单
          this.invokeFields = [
            { name: 'input', label: '输入参数', type: 'text', required: true, unit: '', enum: null }
          ];
          this.schemaLoading = false;
        });
    },
    // 获取可用单位（A001 专用）
    loadAvailableUnits() {
      fetch('/api/v1/models/A001/invoke', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ input: { value: 1, source_unit: 'kg', target_unit: 'g' } })
      })
      .then(r => r.json())
      .catch(() => {});
    },
    fieldInputType(field) {
      if (field.type === 'number') return 'number';
      if (field.enum) return 'select';
      return 'text';
    },
    toggleUnitHelp() {
      this.showUnitHelp = !this.showUnitHelp;
    },
    setUnitParam(fieldName, unit) {
      this.invokeParams[fieldName] = unit;
    },
  },
  mounted() {
    // 处理 ?model=B008 查询参数
    const modelId = this.$route.query.model;
    if (modelId) {
      const modelNames = {
        'A001': '单位换算', 'A002': '化学式解析', 'A003': '摩尔质量计算',
        'A004': '成分归一化', 'A005': '质量守恒校验', 'B003': '显热与焓积分',
        'B006': '反应焓计算', 'B007': '反应熵计算', 'B008': 'Gibbs自由能计算',
        'B009': '平衡常数计算', 'B019': '杠杆规则计算', 'C001': 'Arrhenius速率常数',
      };
      this.invokeModelId = modelId;
      this.invokeModelName = modelNames[modelId] || modelId;
      this.showInvokePanel = true;
      this.loadModelSchema(modelId);
      if (modelId === 'A001') {
        this.loadAvailableUnits();
      }
    }
  },
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

/* ── 模型调用面板 ── */
.invoke-panel { background: #fff; border-radius: 12px; padding: 28px; box-shadow: 0 2px 12px rgba(0,0,0,0.05); }
.invoke-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px; padding-bottom: 20px; border-bottom: 2px solid #eef0f4; }
.invoke-header h2 { margin: 0; font-size: 20px; color: #333; }
.invoke-header .module-desc { margin: 4px 0 0; font-size: 13px; color: #999; }
.btn-close { background: none; border: 1px solid #ddd; padding: 8px 16px; border-radius: 6px; cursor: pointer; color: #666; font-size: 13px; }
.btn-close:hover { background: #f5f5f5; color: #333; }
.invoke-section { margin-bottom: 24px; padding: 20px; background: #fafbfc; border-radius: 8px; border: 1px solid #eef0f4; }
.invoke-section h3 { margin: 0 0 16px; font-size: 15px; color: #333; display: flex; align-items: center; gap: 6px; }
.invoke-section .btn-search { margin-top: 12px; }
.invoke-form .form-row { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin-bottom: 12px; }
.invoke-form .form-row label { width: 120px; font-size: 13px; color: #333; flex-shrink: 0; text-align: right; font-weight: 500; }
.required-star { color: #e53935; margin-left: 2px; }
.field-control { flex: 1; display: flex; align-items: center; gap: 6px; min-width: 200px; }
.field-control input,
.field-control select { flex: 1; padding: 8px 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 13px; background: #fff; }
.field-control input:focus,
.field-control select:focus { border-color: #0046DB; outline: none; box-shadow: 0 0 0 2px rgba(0,70,219,0.1); }
.field-unit { font-size: 12px; color: #999; white-space: nowrap; }
.field-desc { width: 100%; margin-left: 128px; font-size: 12px; color: #999; margin-top: -4px; margin-bottom: 4px; }
.loading-hint { padding: 20px; text-align: center; color: #999; font-size: 14px; }

/* ── 单位换算辅助 ── */
.unit-help-section { margin-top: 16px; padding-top: 16px; border-top: 1px dashed #ddd; }
.btn-link { background: none; border: none; color: #0046DB; cursor: pointer; font-size: 13px; padding: 4px 0; display: flex; align-items: center; gap: 4px; }
.btn-link:hover { text-decoration: underline; }
.unit-help-grid { margin-top: 12px; display: flex; flex-direction: column; gap: 12px; }
.unit-group h5 { margin: 0 0 4px; font-size: 12px; color: #666; text-transform: uppercase; letter-spacing: 0.5px; }
.unit-chips { display: flex; flex-wrap: wrap; gap: 4px; }
.unit-chip { display: inline-block; padding: 4px 10px; border: 1px solid #ddd; border-radius: 14px; font-size: 12px; cursor: pointer; transition: all 0.2s; font-family: monospace; }
.unit-chip:hover { border-color: #0046DB; color: #0046DB; background: #f0f4ff; }
.unit-chip.active { background: #0046DB; color: #fff; border-color: #0046DB; }
.unit-help-tip { font-size: 11px; color: #999; margin: 8px 0 0; display: flex; align-items: center; gap: 4px; }
.result-status { display: inline-flex; align-items: center; gap: 6px; padding: 6px 14px; border-radius: 6px; font-size: 13px; font-weight: 500; margin-bottom: 12px; }
.result-status.success { background: #e8f5e9; color: #2e7d32; }
.result-status.rejected { background: #fff8e1; color: #f57f17; }
.result-status.error { background: #ffebee; color: #c62828; }
.result-json { background: #1a2744; color: #e0e0e0; padding: 16px; border-radius: 8px; font-size: 13px; line-height: 1.6; overflow-x: auto; max-height: 400px; }
.result-error { color: #c62828; font-size: 13px; padding: 8px 12px; background: #ffebee; border-radius: 6px; }
.error-code { color: #999; font-size: 12px; margin-left: 4px; }
.result-provenance { margin-top: 12px; padding-top: 12px; border-top: 1px solid #eef0f4; }
.result-provenance h4 { font-size: 13px; color: #666; margin: 0 0 8px; }
.provenance-item { font-size: 13px; color: #333; padding: 4px 0; }
.provenance-item code { background: #f5f5f5; padding: 2px 6px; border-radius: 3px; font-size: 12px; color: #0046DB; }
.result-meta { font-size: 12px; color: #999; margin-top: 8px; }
</style>
