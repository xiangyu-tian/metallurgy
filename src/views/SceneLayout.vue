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
        <div class="sidebar-header">
          <span>场景导航</span>
          <small v-if="qualifiedExecutableCount">{{ qualifiedExecutableCount }} 个工具</small>
        </div>
        <nav class="sidebar-nav">
          <div
            v-for="scene in scenes"
            :key="scene.id"
            class="nav-item"
            :class="{ active: activeScene === scene.id }"
            @click="selectScene(scene.id)"
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
                  <!-- 整数类型 -->
                  <input v-else-if="field.type === 'integer'" :id="'f-' + field.name"
                    type="number" v-model.number="invokeParams[field.name]"
                    :placeholder="field.placeholder || '输入整数'"
                    :min="field.min" :max="field.max" step="1">
                  <!-- 布尔类型 -->
                  <select v-else-if="field.type === 'boolean'" :id="'f-' + field.name"
                    v-model="invokeParams[field.name]">
                    <option value="">请选择</option>
                    <option :value="true">是 / true</option>
                    <option :value="false">否 / false</option>
                  </select>
                  <!-- 数组和对象使用 JSON 编辑框，避免把结构化参数误传成字符串 -->
                  <textarea v-else-if="field.type === 'array' || field.type === 'object'"
                    :id="'f-' + field.name"
                    v-model="invokeParams[field.name]"
                    rows="5"
                    spellcheck="false"
                    :placeholder="field.type === 'array' ? '[...]' : '{...}'"></textarea>
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

              <div v-if="invokeFormError" class="form-error">
                <i class="fas fa-exclamation-circle"></i> {{ invokeFormError }}
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
                        @click.exact="setUnitParam($event.target.closest('.unit-chip').dataset.field || 'source_unit', u)"
                        @click.shift="setUnitParam('target_unit', u)"
                      >{{ u }}</span>
                    </div>
                  </div>
                  <p class="unit-help-tip"><i class="fas fa-info-circle"></i> 点击选择源单位，Shift+点击选择目标单位</p>
                </div>
              </div>

              <div class="invoke-artifact-control" :class="{ active: invokeArtifactEnabled }">
                <label>
                  <input v-model="invokeArtifactEnabled" type="checkbox">
                  <span>生成可复核文件产物</span>
                  <em v-if="invokeArtifactCapability && invokeArtifactCapability.recommended">建议生成</em>
                </label>
                <select v-if="invokeArtifactEnabled" v-model="invokeArtifactMode">
                  <option value="directory_and_zip">可读目录 + 可下载 ZIP</option>
                  <option value="directory">仅服务器可读目录</option>
                </select>
                <p>{{ invokeArtifactHint }}</p>
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
            <pre v-if="invokeOutput" class="result-json">{{ JSON.stringify(invokeOutput, null, 2) }}</pre>
            <div v-if="invokeResult.error" class="result-error">
              <i class="fas fa-times-circle"></i> {{ invokeResult.error }}
              <span v-if="invokeResult.error_code" class="error-code">({{ invokeResult.error_code }})</span>
            </div>
            <div v-if="invokeProvenance.length" class="result-provenance">
              <h4><i class="fas fa-database"></i> 数据来源</h4>
              <div v-for="p in invokeProvenance" :key="p.dataset_id" class="provenance-item">
                <code>{{ p.dataset_id }}</code> {{ p.name }} <span v-if="p.version">v{{ p.version }}</span>
              </div>
            </div>
            <div v-if="invokeArtifactInfo" class="invoke-artifact-result">
              <div>
                <strong>{{ invokeArtifactInfo.native ? '原生科学案例包' : '执行结果文件包' }}</strong>
                <p>{{ invokeArtifactInfo.files.length }} 个文件 · {{ invokeArtifactInfo.verified ? '回读验证通过' : '等待验证' }}</p>
              </div>
              <a v-if="invokeArtifactInfo.zipPath" :href="invokeArtifactDownloadUrl" download>
                下载 ZIP <i class="fas fa-download"></i>
              </a>
              <span v-else>仅目录模式</span>
            </div>
            <div v-if="invokeResult.runtime_ms" class="result-meta">
              耗时: {{ invokeResult.runtime_ms }}ms
            </div>
          </div>
        </div>

        <!-- 常规场景内容（模型调用面板未激活时显示） -->
        <template v-if="!showInvokePanel">
        <div v-if="registryLoading" class="registry-state">
          <i class="fas fa-spinner fa-spin"></i> 正在读取真实工具注册中心...
        </div>
        <div v-else-if="registryError" class="registry-state registry-error">
          <i class="fas fa-exclamation-circle"></i> {{ registryError }}
          <button @click="loadRegistry">重新加载</button>
        </div>
        <template v-else>
        <!-- Scene header -->
        <div class="scene-header">
          <div class="scene-info">
            <h2>{{ currentScene.name }}</h2>
            <p>
              {{ currentScene.desc }} · 当前分类 {{ currentScene.tools.length }} 个
              <template v-if="sceneSearch"> · 匹配 {{ filteredSceneTools.length }} 个</template>
            </p>
          </div>
          <label class="scene-search" aria-label="搜索当前场景工具">
            <i class="fas fa-search"></i>
            <input v-model="sceneSearch" type="search" placeholder="搜索工具名称、ID或专业域">
            <button v-if="sceneSearch" type="button" title="清空搜索" @click="sceneSearch = ''">
              <i class="fas fa-times"></i>
            </button>
          </label>
        </div>

        <!-- Tool cards grid -->
        <div class="tools-grid">
          <div v-for="tool in pagedTools" :key="tool.id" class="tool-card">
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
              <div class="scene-relations">
                <span class="primary-scene"><b>主要场景</b>{{ tool.primarySceneName }}</span>
                <span v-if="tool.otherSceneNames.length" class="other-scenes">
                  <b>同时适用</b>{{ tool.otherSceneNames.join('、') }}
                </span>
              </div>
              <div class="usage-hint">
                <i class="fas fa-lightbulb"></i> {{ tool.usage }}
              </div>
            </div>
            <div class="card-footer">
              <button type="button" class="btn-use" @click="openInvoke(tool)">
                立即使用 <i class="fas fa-arrow-right"></i>
              </button>
            </div>
          </div>
        </div>

        <div v-if="!filteredSceneTools.length" class="empty-tools">
          <i class="fas fa-search"></i>
          <strong>当前场景没有匹配工具</strong>
          <span>请更换关键词或清空搜索条件。</span>
        </div>

        <nav v-if="totalPages > 1" class="pagination" aria-label="工具列表分页">
          <span class="pagination-summary">
            共 {{ filteredSceneTools.length }} 项 · 第 {{ currentPage }} / {{ totalPages }} 页
          </span>
          <button type="button" :disabled="currentPage === 1" @click="setPage(currentPage - 1)">
            <i class="fas fa-chevron-left"></i> 上一页
          </button>
          <button
            v-for="page in totalPages"
            :key="page"
            type="button"
            class="page-number"
            :class="{ active: page === currentPage }"
            :aria-current="page === currentPage ? 'page' : null"
            @click="setPage(page)"
          >{{ page }}</button>
          <button type="button" :disabled="currentPage === totalPages" @click="setPage(currentPage + 1)">
            下一页 <i class="fas fa-chevron-right"></i>
          </button>
        </nav>
        </template>
        </template>
      </main>
    </div>
  </div>
  <Footer />
</template>

<script>
import Header from '@/components/Header.vue';
import Footer from '@/components/Footer.vue';

const CATEGORY_STYLES = [
  { icon: 'fa-vial', color: '#0046DB' },
  { icon: 'fa-fire', color: '#E53935' },
  { icon: 'fa-balance-scale', color: '#7C3AED' },
  { icon: 'fa-atom', color: '#0B7285' },
  { icon: 'fa-wind', color: '#1971C2' },
  { icon: 'fa-temperature-high', color: '#E67700' },
  { icon: 'fa-industry', color: '#5F3DC4' },
  { icon: 'fa-leaf', color: '#2B8A3E' },
  { icon: 'fa-filter', color: '#087F5B' },
  { icon: 'fa-snowflake', color: '#1864AB' },
  { icon: 'fa-calculator', color: '#495057' },
  { icon: 'fa-project-diagram', color: '#9C36B5' },
];

const CATEGORY_STYLE_OVERRIDES = {
  '通用数据与校验': { icon: 'fa-check-double', color: '#0046DB' },
  '基础化学与计量': { icon: 'fa-vial', color: '#364FC7' },
  '热力学与相平衡': { icon: 'fa-fire', color: '#E53935' },
  '相平衡与溶液热力学': { icon: 'fa-balance-scale', color: '#7C3AED' },
  '动力学与扩散': { icon: 'fa-atom', color: '#0B7285' },
  '动力学与传递': { icon: 'fa-wind', color: '#1971C2' },
  '传热传质': { icon: 'fa-temperature-high', color: '#E67700' },
  '冶金工艺、物料与热平衡': { icon: 'fa-industry', color: '#5F3DC4' },
  '冶金工艺与物料衡算': { icon: 'fa-weight-hanging', color: '#6741D9' },
  '转炉炼钢': { icon: 'fa-bullseye', color: '#C92A2A' },
  '高炉低碳': { icon: 'fa-leaf', color: '#2B8A3E' },
  '炉外精炼与洁净钢': { icon: 'fa-filter', color: '#087F5B' },
  '凝固与连铸': { icon: 'fa-snowflake', color: '#1864AB' },
  '数值方法与仿真': { icon: 'fa-calculator', color: '#495057' },
  '数值仿真与工具编排': { icon: 'fa-project-diagram', color: '#9C36B5' },
  '仿真/优化/智能体支撑': { icon: 'fa-cogs', color: '#D9480F' },
};

function getCategoryStyle(name, index) {
  return CATEGORY_STYLE_OVERRIDES[name] || CATEGORY_STYLES[index % CATEGORY_STYLES.length];
}

function getToolIcon(modelCode) {
  const family = String(modelCode || '').charAt(0).toUpperCase();
  return {
    A: 'fa-vial', B: 'fa-fire', C: 'fa-atom', T: 'fa-temperature-high',
    D: 'fa-industry', E: 'fa-leaf', F: 'fa-filter', G: 'fa-calculator',
    H: 'fa-project-diagram', DS: 'fa-database'
  }[family] || 'fa-cog';
}

export default {
  name: 'SceneLayout',
  components: { Header, Footer },
  data() {
    return {
      activeScene: '',
      scenes: [],
      registryLoading: true,
      registryError: '',
      registeredCount: 0,
      qualifiedExecutableCount: 0,
      currentPage: 1,
      pageSize: 12,
      sceneSearch: '',
      // 模型调用模式
      invokeModelId: '',
      invokeModelName: '',
      invokeToolName: '',
      invokeFields: [],          // 从后端 API 获取的字段定义
      invokeParams: {},
      invokeFormError: '',
      showInvokePanel: false,
      invokeResult: null,
      invokeLoading: false,
      schemaLoading: false,
      availableUnits: [],
      showUnitHelp: false,
      invokeArtifactCapability: null,
      invokeArtifactEnabled: false,
      invokeArtifactMode: 'directory_and_zip',
    };
  },
  computed: {
    currentScene() {
      return this.scenes.find(scene => scene.id === this.activeScene)
        || this.scenes[0]
        || { id: '', name: '真实冶金工具', desc: '暂无可用工具', tools: [], color: '#0046DB' };
    },
    filteredSceneTools() {
      const keyword = this.sceneSearch.trim().toLowerCase();
      if (!keyword) return this.currentScene.tools;
      return this.currentScene.tools.filter(tool => [
        tool.id,
        tool.name,
        tool.desc,
        tool.professionalDomain,
        tool.primarySceneName,
        ...tool.otherSceneNames,
      ].some(value => String(value || '').toLowerCase().includes(keyword)));
    },
    totalPages() {
      return Math.max(1, Math.ceil(this.filteredSceneTools.length / this.pageSize));
    },
    pagedTools() {
      const start = (this.currentPage - 1) * this.pageSize;
      return this.filteredSceneTools.slice(start, start + this.pageSize);
    },
    invokeOutput() {
      return this.invokeResult?.output || this.invokeResult?.result || null;
    },
    invokeProvenance() {
      return this.invokeResult?.actual_data_records || this.invokeResult?.provenance || [];
    },
    invokeArtifactHint() {
      const capability = this.invokeArtifactCapability;
      if (!capability) return '计算成功后可导出输入、结果、来源、清单和哈希。';
      if (capability.delivery === 'native_case_bundle') return '该工具会生成可交给专业求解器的原生案例目录。';
      const fields = capability.csv_output_fields || [];
      return fields.length
        ? `完整 JSON + ${fields.join('、')} 等数组结果的 CSV。`
        : '完整 JSON；无表格数组时不生成无意义 CSV。';
    },
    invokeArtifactInfo() {
      if (this.invokeResult?.status !== 'success') return null;
      if (this.invokeResult.artifact) {
        return {
          native: false,
          files: this.invokeResult.artifact.files || [],
          verified: Boolean(this.invokeResult.artifact.readback_verified),
          zipPath: this.invokeResult.artifact.zip_path || null
        };
      }
      const output = this.invokeOutput || {};
      if (this.invokeModelId === 'G005' && output.materialized) {
        return {
          native: true,
          files: [...Object.keys(output.files || {}), 'case_manifest.json'],
          verified: Boolean(output.readback_verified && output.structural_validation?.verified),
          zipPath: output.zip_path || null
        };
      }
      return null;
    },
    invokeArtifactDownloadUrl() {
      return this.invokeResult?.execution_id
        ? `/api/v1/executions/${encodeURIComponent(this.invokeResult.execution_id)}/artifact/download`
        : '#';
    },
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
  watch: {
    sceneSearch() { this.currentPage = 1; },
  },
  methods: {
    selectScene(sceneId) {
      this.activeScene = sceneId;
      this.currentPage = 1;
    },
    setPage(page) {
      const nextPage = Math.min(Math.max(Number(page) || 1, 1), this.totalPages);
      this.currentPage = nextPage;
      const contentTop = document.querySelector('.scene-header');
      if (contentTop) contentTop.scrollIntoView({ behavior: 'smooth', block: 'start' });
    },
    async loadRegistry() {
      this.registryLoading = true;
      this.registryError = '';
      try {
        const [modelResponse, sceneResponse] = await Promise.all([
          fetch('/api/v1/models'),
          fetch('/api/v1/scenes'),
        ]);
        const [data, sceneData] = await Promise.all([modelResponse.json(), sceneResponse.json()]);
        if (!modelResponse.ok) throw new Error(data.detail?.message || data.detail || `注册中心读取失败 (${modelResponse.status})`);
        if (!sceneResponse.ok) throw new Error(sceneData.detail?.message || sceneData.detail || `场景目录读取失败 (${sceneResponse.status})`);

        const models = (data.models || []).filter(model => model.count_eligible === true);
        const sceneDefinitions = sceneData.scenes || [];
        const sceneById = new Map(sceneDefinitions.map(scene => [scene.scene_id, scene]));
        const membershipByCode = new Map();
        for (const scene of sceneDefinitions) {
          for (const code of scene.applicable_tool_ids || []) {
            if (!membershipByCode.has(code)) membershipByCode.set(code, []);
            membershipByCode.get(code).push(scene);
          }
        }
        const primarySceneByFamily = {
          A: 'thermodynamics', B: 'thermodynamics', C: 'thermodynamics', T: 'thermodynamics',
          D: 'converter', E: 'blastfurnace', F: 'casting', G: 'simulation', H: 'simulation',
        };
        const cardsByCode = new Map();
        for (const model of models) {
          const modelCode = model.model_code || model.model_id;
          const memberships = membershipByCode.get(modelCode) || [];
          const preferredSceneId = primarySceneByFamily[String(modelCode || '').charAt(0).toUpperCase()];
          const primaryScene = memberships.find(scene => scene.scene_id === preferredSceneId)
            || sceneById.get(preferredSceneId)
            || memberships[0];
          const primarySceneName = primaryScene?.name || '未指定';
          const otherSceneNames = memberships
            .filter(scene => scene.scene_id !== primaryScene?.scene_id)
            .map(scene => scene.name);
          const requiredCount = (model.input_schema_json?.required || model.input_schema?.required || []).length;
          const dependencyText = (model.dependencies || []).length
            ? `依赖 ${model.dependencies.length} 个上游工具/组件`
            : '可独立执行';
          cardsByCode.set(modelCode, {
            id: modelCode,
            name: model.name || model.model_name || modelCode,
            toolName: model.tool_name,
            icon: getToolIcon(modelCode),
            badge: '可执行',
            desc: model.description || '注册中心合格冶金工具',
            professionalDomain: model.scenario || model.category || '未分类',
            primarySceneName,
            otherSceneNames,
            features: [
              `${modelCode} · v${model.version || '1.0.0'}`,
              `${requiredCount} 个必填参数 · ${model.model_type || '确定性工具'}`,
              dependencyText,
            ],
            usage: model.applicable_boundary || model.applicable_conditions || '请按输入 Schema 提供参数',
            model,
          });
        }

        this.scenes = sceneDefinitions.map((scene, index) => {
          const featuredCodes = new Set((scene.featured_tools || []).map(item => item.model_code));
          const tools = (scene.applicable_tool_ids || [])
            .map(code => cardsByCode.get(code))
            .filter(Boolean)
            .map(tool => ({ ...tool, badge: featuredCodes.has(tool.id) ? '核心' : '可执行' }));
          const style = getCategoryStyle(scene.name, index);
          return {
            id: scene.scene_id,
            name: scene.name,
            icon: scene.icon || style.icon,
            color: scene.color || style.color,
            desc: scene.description || '来自统一注册中心、已通过资格闸门的真实可执行工具',
            tools,
          };
        });
        this.registeredCount = Number(data.registered_count || models.length);
        this.qualifiedExecutableCount = Number(data.qualified_executable_count || models.length);
        if (!this.scenes.some(scene => scene.id === this.activeScene)) {
          this.activeScene = this.scenes[0]?.id || '';
          this.currentPage = 1;
        }

        const requestedModelId = this.$route.query.model;
        if (requestedModelId) {
          const targetScene = this.scenes.find(scene => scene.tools.some(tool => tool.id === requestedModelId));
          const targetTool = targetScene?.tools.find(tool => tool.id === requestedModelId);
          if (targetScene && targetTool) {
            this.activeScene = targetScene.id;
            this.currentPage = Math.floor(targetScene.tools.findIndex(tool => tool.id === requestedModelId) / this.pageSize) + 1;
            this.openInvoke(targetTool, false);
          }
        }
      } catch (error) {
        this.scenes = [];
        this.registryError = error.message || '真实工具注册中心不可用';
      } finally {
        this.registryLoading = false;
      }
    },
    openInvoke(tool, updateRoute = true) {
      this.invokeModelId = tool.id;
      this.invokeModelName = tool.name;
      this.invokeToolName = tool.toolName || tool.model?.tool_name || '';
      this.invokeParams = {};
      this.invokeFields = [];
      this.invokeFormError = '';
      this.invokeResult = null;
      this.invokeArtifactCapability = tool.model?.artifact_capability || null;
      this.invokeArtifactEnabled = Boolean(this.invokeArtifactCapability?.recommended);
      this.showInvokePanel = true;
      this.loadModelSchema(tool.id);
      if (tool.id === 'A001') this.loadAvailableUnits();
      if (updateRoute && this.$route.query.model !== tool.id) {
        this.$router.push({ path: '/scene', query: { model: tool.id } }).catch(() => {});
      }
    },
    async doInvoke() {
      this.invokeFormError = '';
      this.invokeResult = null;
      const params = {};

      try {
        for (const field of this.invokeFields) {
          const value = this.invokeParams[field.name];
          const empty = value === '' || value === undefined || value === null;
          if (empty) {
            if (field.required) throw new Error(`请填写必填参数“${field.label}”`);
            continue;
          }
          if (field.type === 'number' || field.type === 'integer') {
            const numeric = Number(value);
            if (!Number.isFinite(numeric)) throw new Error(`参数“${field.label}”必须是有限数值`);
            if (field.type === 'integer' && !Number.isInteger(numeric)) throw new Error(`参数“${field.label}”必须是整数`);
            params[field.name] = numeric;
          } else if (field.type === 'array' || field.type === 'object') {
            let parsed;
            try {
              parsed = typeof value === 'string' ? JSON.parse(value) : value;
            } catch (error) {
              throw new Error(`参数“${field.label}”不是合法 JSON`);
            }
            if (field.type === 'array' && !Array.isArray(parsed)) throw new Error(`参数“${field.label}”必须是 JSON 数组`);
            if (field.type === 'object' && (!parsed || Array.isArray(parsed) || typeof parsed !== 'object')) {
              throw new Error(`参数“${field.label}”必须是 JSON 对象`);
            }
            params[field.name] = parsed;
          } else {
            params[field.name] = value;
          }
        }
      } catch (error) {
        this.invokeFormError = error.message;
        return;
      }

      const options = { validate_boundary: true, return_provenance: true };
      if (this.invokeArtifactEnabled) {
        if (this.invokeModelId === 'G005') params.artifact_mode = this.invokeArtifactMode;
        else options.artifact = { mode: this.invokeArtifactMode };
      }

      this.invokeLoading = true;
      try {
        if (!this.invokeToolName) throw new Error('注册中心未返回工具函数名');
        const response = await fetch(`/api/v1/tools/${encodeURIComponent(this.invokeToolName)}/call`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ arguments: params, options })
        });
        const data = await response.json();
        if (!response.ok) {
          const detail = data.detail || data;
          const error = new Error(detail.message || detail.error || (typeof detail === 'string' ? detail : `调用失败 (${response.status})`));
          error.code = detail.error_code;
          throw error;
        }
        this.invokeResult = data;
      } catch (error) {
        this.invokeResult = {
          status: 'error',
          error: error.message || '网络错误或微服务不可用',
          error_code: error.code || 'NETWORK_ERROR'
        };
      } finally {
        this.invokeLoading = false;
      }
    },
    closeInvoke() {
      this.showInvokePanel = false;
      this.invokeModelId = '';
      this.invokeModelName = '';
      this.invokeToolName = '';
      this.invokeFields = [];
      this.invokeParams = {};
      this.invokeFormError = '';
      this.invokeResult = null;
      this.invokeArtifactCapability = null;
      this.invokeArtifactEnabled = false;
      this.$router.push('/scene');
    },
    // 从后端获取模型 Schema
    loadModelSchema(modelId) {
      this.schemaLoading = true;
      fetch(`/api/v1/models/${modelId}`)
        .then(async r => {
          const data = await r.json();
          if (!r.ok) throw new Error(data.detail?.message || data.detail || `Schema 加载失败 (${r.status})`);
          return data;
        })
        .then(data => {
          const schema = data.input_schema_json || {};
          this.invokeToolName = data.tool_name || this.invokeToolName;
          this.invokeArtifactCapability = data.artifact_capability || null;
          const props = schema.properties || {};
          const required = schema.required || [];
          this.invokeFields = Object.entries(props).map(([name, def]) => ({
            name,
            label: def.label || name,
            type: def.type || 'string',
            required: required.includes(name),
            unit: def.unit || '',
            min: def.minimum ?? def.min_value,
            max: def.maximum ?? def.max_value,
            enum: def.enum || null,
            default: def.default,
            placeholder: def.placeholder || '',
            description: def.description || '',
          }));
          // 设置默认值
          for (const f of this.invokeFields) {
            if (f.default !== undefined && f.default !== null) {
              this.invokeParams[f.name] = (f.type === 'array' || f.type === 'object')
                ? JSON.stringify(f.default, null, 2)
                : f.default;
            } else if (f.type === 'array') {
              this.invokeParams[f.name] = '[]';
            } else if (f.type === 'object') {
              this.invokeParams[f.name] = '{}';
            }
          }
          this.schemaLoading = false;
        })
        .catch(error => {
          this.invokeFormError = error.message || '无法读取工具输入 Schema';
          this.invokeFields = [];
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
    this.loadRegistry();
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
.sidebar-header { padding: 16px 20px; font-size: 15px; font-weight: 600; color: #333; background: #E8F0FE; border-bottom: 1px solid rgba(0,70,219,0.08); display: flex; justify-content: space-between; align-items: center; gap: 8px; }
.sidebar-header small { color: #0046DB; font-size: 11px; font-weight: 600; white-space: nowrap; }
.sidebar-nav { padding: 8px; }
.nav-item { display: flex; align-items: center; gap: 10px; padding: 12px 14px; border-radius: 8px; cursor: pointer; transition: all 0.2s; margin-bottom: 2px; }
.nav-item:hover { background: #f0f4ff; }
.nav-item.active { background: #E8F0FE; font-weight: 600; }
.nav-item i { font-size: 16px; width: 20px; text-align: center; }
.nav-item span { font-size: 14px; color: #333; }

/* Content */
.content { flex: 1; min-width: 0; }
.scene-header { display: flex; align-items: flex-end; justify-content: space-between; gap: 20px; margin-bottom: 28px; }
.scene-header h2 { font-size: 22px; color: #333; margin: 0 0 6px; }
.scene-header p { font-size: 14px; color: #666; margin: 0; }
.scene-search { width: min(320px, 42%); height: 40px; display: flex; align-items: center; gap: 8px; padding: 0 12px; border: 1px solid #d8dee9; border-radius: 8px; background: #fff; box-shadow: 0 2px 7px rgba(0,0,0,.035); transition: border-color .2s, box-shadow .2s; }
.scene-search:focus-within { border-color: #0046DB; box-shadow: 0 0 0 3px rgba(0,70,219,.09); }
.scene-search > i { color: #8a94a6; font-size: 13px; }
.scene-search input { width: 100%; min-width: 0; border: 0; outline: 0; background: transparent; color: #29364d; font: inherit; font-size: 13px; }
.scene-search button { padding: 3px; border: 0; background: transparent; color: #929bad; cursor: pointer; }
.registry-state { padding: 36px 24px; border: 1px solid #e4e8ef; border-radius: 12px; background: #fff; color: #667085; text-align: center; }
.registry-state i { margin-right: 6px; }
.registry-state.registry-error { color: #b42318; background: #fff7f6; }
.registry-state button { margin-left: 12px; padding: 6px 12px; border: 1px solid #0046DB; border-radius: 6px; background: #fff; color: #0046DB; cursor: pointer; }

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
.scene-relations { display: flex; flex-direction: column; gap: 5px; padding: 9px 11px; border-left: 3px solid #0046DB; border-radius: 0 6px 6px 0; background: #f3f7ff; color: #536176; font-size: 11px; line-height: 1.45; }
.scene-relations span { display: flex; gap: 7px; }
.scene-relations b { min-width: 49px; color: #1f355d; font-weight: 600; }
.usage-hint { font-size: 12px; color: #633806; background: #FAEEDA; border: 1px solid rgba(133,79,11,0.15); border-radius: 6px; padding: 8px 12px; display: flex; align-items: center; gap: 6px; line-height: 1.4; }
.usage-hint i { color: #EF9F27; flex-shrink: 0; }

/* Card Footer */
.card-footer { padding: 14px 20px; border-top: 1px solid #f0f0f0; }
.btn-use { display: inline-flex; align-items: center; gap: 6px; padding: 8px 20px; border: 0; background: #0046DB; color: #fff; border-radius: 8px; font-size: 14px; font-weight: 500; font-family: inherit; text-decoration: none; cursor: pointer; transition: all 0.3s; }
.btn-use:hover { background: #0038b3; box-shadow: 0 4px 12px rgba(0,70,219,0.3); }
.btn-use i { font-size: 12px; transition: transform 0.3s; }
.tool-card:hover .btn-use i { transform: translateX(4px); }

/* Pagination */
.pagination { display: flex; align-items: center; justify-content: flex-end; flex-wrap: wrap; gap: 7px; margin-top: 24px; padding: 14px 16px; background: #fff; border: 1px solid #e7ebf1; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); }
.pagination-summary { margin-right: auto; color: #667085; font-size: 12px; }
.pagination button { min-width: 36px; height: 34px; padding: 0 11px; border: 1px solid #d9dee8; border-radius: 6px; color: #344054; background: #fff; font-family: inherit; font-size: 12px; cursor: pointer; transition: border-color .2s, color .2s, background .2s; }
.pagination button:hover:not(:disabled) { border-color: #0046DB; color: #0046DB; background: #f3f7ff; }
.pagination button.page-number { padding: 0; }
.pagination button.active { border-color: #0046DB; color: #fff; background: #0046DB; font-weight: 700; }
.pagination button:disabled { opacity: .42; cursor: not-allowed; }
.empty-tools { display: flex; flex-direction: column; align-items: center; gap: 7px; padding: 54px 20px; border: 1px dashed #ccd4e0; border-radius: 12px; color: #7d8797; background: #fff; }
.empty-tools i { color: #0046DB; font-size: 23px; }
.empty-tools strong { color: #344054; font-size: 15px; }
.empty-tools span { font-size: 12px; }

/* Responsive */
@media (max-width: 992px) { .main-section { flex-direction: column; } .sidebar { width: 100%; position: static; } .sidebar-nav { display: flex; flex-wrap: wrap; gap: 4px; } .nav-item { flex: 1; min-width: 120px; justify-content: center; } }
@media (max-width: 768px) { .scene-header { align-items: stretch; flex-direction: column; } .scene-search { width: 100%; } .tools-grid { grid-template-columns: 1fr; } .pagination { justify-content: center; } .pagination-summary { width: 100%; margin: 0 0 4px; text-align: center; } }

/* ── 模型调用面板 ── */
.invoke-panel { background: #fff; border-radius: 12px; padding: 28px; box-shadow: 0 2px 12px rgba(0,0,0,0.05); }
.invoke-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px; padding-bottom: 20px; border-bottom: 2px solid #eef0f4; }
.invoke-header h2 { margin: 0; font-size: 20px; color: #333; }
.invoke-header .module-desc { margin: 4px 0 0; font-size: 13px; color: #999; }
.btn-close { background: none; border: 1px solid #ddd; padding: 8px 16px; border-radius: 6px; cursor: pointer; color: #666; font-size: 13px; }
.btn-close:hover { background: #f5f5f5; color: #333; }
.invoke-section { margin-bottom: 24px; padding: 20px; background: #fafbfc; border-radius: 8px; border: 1px solid #eef0f4; }
.invoke-section h3 { margin: 0 0 16px; font-size: 15px; color: #333; display: flex; align-items: center; gap: 6px; }
.invoke-section .btn-search { display: inline-flex; align-items: center; gap: 7px; margin-top: 12px; padding: 9px 18px; border: 0; border-radius: 7px; color: #fff; background: #0046DB; font-family: inherit; font-size: 13px; font-weight: 600; cursor: pointer; }
.invoke-section .btn-search:hover { background: #0038b3; }
.invoke-section .btn-search:disabled { opacity: .55; cursor: not-allowed; }
.invoke-form .form-row { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin-bottom: 12px; }
.invoke-form .form-row label { width: 120px; font-size: 13px; color: #333; flex-shrink: 0; text-align: right; font-weight: 500; }
.required-star { color: #e53935; margin-left: 2px; }
.field-control { flex: 1; display: flex; align-items: center; gap: 6px; min-width: 200px; }
.field-control input,
.field-control select,
.field-control textarea { flex: 1; padding: 8px 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 13px; background: #fff; }
.field-control input:focus,
.field-control select:focus,
.field-control textarea:focus { border-color: #0046DB; outline: none; box-shadow: 0 0 0 2px rgba(0,70,219,0.1); }
.field-control textarea { min-height: 92px; resize: vertical; font-family: Consolas, Monaco, monospace; line-height: 1.5; }
.field-unit { font-size: 12px; color: #999; white-space: nowrap; }
.field-desc { width: 100%; margin-left: 128px; font-size: 12px; color: #999; margin-top: -4px; margin-bottom: 4px; }
.form-error { margin: 4px 0 12px 128px; padding: 9px 12px; border-radius: 6px; background: #ffebee; color: #c62828; font-size: 12px; }
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
.invoke-artifact-control { display: grid; grid-template-columns: 1fr auto; gap: 9px 14px; align-items: center; margin-top: 16px; padding: 13px 15px; border: 1px dashed #cad1df; border-radius: 8px; background: #f7f9fd; }
.invoke-artifact-control.active { border-style: solid; border-color: #90aeea; box-shadow: inset 3px 0 0 #0046DB; }
.invoke-artifact-control label { display: flex; align-items: center; gap: 8px; color: #263655; font-size: 13px; font-weight: 600; }
.invoke-artifact-control input { accent-color: #0046DB; }
.invoke-artifact-control em { padding: 2px 6px; border: 1px solid #d4a72c; border-radius: 9px; color: #8a6510; font-size: 10px; font-style: normal; }
.invoke-artifact-control select { padding: 7px 9px; border: 1px solid #c7cfdd; border-radius: 6px; color: #263655; background: #fff; font-size: 12px; }
.invoke-artifact-control p { grid-column: 1 / -1; margin: 0; color: #7b8494; font-size: 11px; line-height: 1.5; }
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
.invoke-artifact-result { display: flex; justify-content: space-between; gap: 18px; align-items: center; margin-top: 14px; padding: 14px 16px; border: 1px solid #c5d5c8; border-radius: 8px; background: #f1f8f3; }
.invoke-artifact-result strong { color: #235d34; font-size: 13px; }
.invoke-artifact-result p { margin: 4px 0 0; color: #6f7d72; font-size: 11px; }
.invoke-artifact-result a { display: inline-flex; align-items: center; gap: 6px; padding: 8px 13px; border-radius: 6px; color: #fff; background: #235d34; font-size: 12px; text-decoration: none; }
.invoke-artifact-result span { color: #778078; font-size: 12px; }
.result-meta { font-size: 12px; color: #999; margin-top: 8px; }
</style>
