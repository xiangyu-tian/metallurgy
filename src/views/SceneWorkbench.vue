<template>
  <Header />
  <div class="scene-workbench" :style="sceneCssVars">
    <div class="scene-rail">
      <div class="container rail-inner">
        <router-link to="/">首页</router-link>
        <span>/</span>
        <router-link to="/scene">智能场景</router-link>
        <span>/</span>
        <strong>{{ scene?.name || '场景工作台' }}</strong>
      </div>
    </div>

    <section class="scene-hero">
      <div class="hero-grid"></div>
      <div class="container hero-inner">
        <div class="hero-copy">
          <span class="eyebrow">METALLURGY · SCENE ORCHESTRATION</span>
          <h1>{{ scene?.name || '正在加载场景' }}</h1>
          <p>{{ scene?.description || '正在读取已认证工具与场景配方。' }}</p>
        </div>
        <div class="hero-metrics" v-if="scene">
          <div><b>{{ scene.applicable_tool_count }}</b><span>适用工具</span></div>
          <div><b>{{ registryCounts.qualified }}</b><span>全库合格</span></div>
          <div><b>{{ scene.recipes.length }}</b><span>版本化配方</span></div>
        </div>
      </div>
    </section>

    <nav class="scene-tabs container" aria-label="五大场景">
      <router-link
        v-for="item in publicScenes"
        :key="item.scene_id"
        :to="`/scene/${item.scene_id}`"
        :class="{ active: item.scene_id === sceneId }"
      >
        <i :class="['fas', item.icon]"></i>
        <span>{{ item.short_name }}</span>
      </router-link>
    </nav>

    <main class="container workbench-body">
      <div v-if="loading" class="state-panel"><i class="fas fa-circle-notch fa-spin"></i> 正在加载场景契约…</div>
      <div v-else-if="errorMessage && !scene" class="state-panel error">{{ errorMessage }}</div>

      <template v-else-if="scene">
        <section class="recipe-strip">
          <div class="section-heading">
            <div>
              <span class="section-index">01</span>
              <h2>选择场景配方</h2>
            </div>
            <p>配方只编排现有注册工具，不改变120工具计数。</p>
          </div>
          <button
            v-for="recipe in scene.recipes"
            :key="recipe.recipe_id"
            class="recipe-card"
            :class="{ selected: recipe.recipe_id === selectedRecipeId }"
            @click="selectRecipe(recipe.recipe_id)"
          >
            <span class="recipe-version">v{{ recipe.version }}</span>
            <strong>{{ recipe.name }}</strong>
            <small>{{ recipe.description }}</small>
            <span class="recipe-count">{{ recipe.steps.length }} 个工具节点</span>
          </button>
        </section>

        <section v-if="recipe" class="pipeline-section">
          <div class="section-heading compact">
            <div><span class="section-index">02</span><h2>执行链</h2></div>
            <p>箭头表示配方依赖；每个节点仍由统一注册中心独立校验和执行。</p>
          </div>
          <div class="pipeline" role="list">
            <template v-for="(step, index) in recipe.steps" :key="step.step_id">
              <div class="pipeline-step" :class="stepStatus(step.step_id)" role="listitem">
                <span class="step-no">{{ String(index + 1).padStart(2, '0') }}</span>
                <div>
                  <b>{{ step.model_code }}</b>
                  <strong>{{ step.model_name }}</strong>
                  <small>{{ step.purpose }}</small>
                </div>
                <i v-if="step.artifact_recommended" class="fas fa-file-zipper artifact-mark" title="建议生成文件产物"></i>
              </div>
              <i v-if="index < recipe.steps.length - 1" class="fas fa-arrow-right pipeline-arrow"></i>
            </template>
          </div>
        </section>

        <section v-if="recipe" class="execution-grid">
          <div class="control-panel">
            <div class="panel-title">
              <div><span class="section-index">03</span><h2>工况输入</h2></div>
              <button class="text-button" @click="resetExample"><i class="fas fa-rotate-left"></i> 恢复认证示例</button>
            </div>
            <p class="panel-note">JSON中的每个键对应一个配方步骤。上游输出绑定字段由后端覆盖，避免人工复制产生漂移。</p>
            <textarea v-model="requestText" spellcheck="false" aria-label="场景配方请求JSON"></textarea>
            <div v-if="inputError" class="inline-alert"><i class="fas fa-triangle-exclamation"></i> {{ inputError }}</div>
            <div class="control-actions">
              <label class="check-control">
                <input v-model="autoCompileWorkOrder" type="checkbox">
                <span>成功后编译工单</span>
              </label>
              <button class="primary-action" :disabled="running" @click="executeRecipe">
                <i :class="['fas', running ? 'fa-circle-notch fa-spin' : 'fa-play']"></i>
                {{ running ? '执行工具链中' : '执行已选配方' }}
              </button>
            </div>
          </div>

          <div class="run-panel">
            <div class="panel-title">
              <div><span class="section-index">04</span><h2>执行证据</h2></div>
              <span v-if="run" class="run-id">{{ run.run_id }}</span>
            </div>
            <div v-if="!run" class="empty-run">
              <i class="fas fa-diagram-project"></i>
              <strong>等待执行</strong>
              <p>执行后显示每个工具的状态、版本、边界警告、来源与文件附件。</p>
            </div>
            <template v-else>
              <div class="run-summary">
                <span :class="['status-dot', run.status]"></span>
                <div><strong>{{ runStatusLabel }}</strong><small>{{ run.successful_step_count }}/{{ run.requested_step_count }} 节点成功</small></div>
                <div class="safety-chip" :class="{ passed: run.safety_gate_passed }">
                  <i class="fas fa-shield-halved"></i> {{ run.safety_gate_passed ? '安全闸门通过' : '安全闸门未通过' }}
                </div>
              </div>
              <div class="trace-list">
                <details v-for="step in run.steps" :key="step.step_id" class="trace-item" :class="step.status">
                  <summary>
                    <span class="trace-icon"><i :class="['fas', statusIcon(step.status)]"></i></span>
                    <div><b>{{ step.model_code }}</b><strong>{{ step.purpose || step.step_id }}</strong></div>
                    <small>{{ step.status }}</small>
                  </summary>
                  <div class="trace-detail">
                    <p v-if="step.execution_id"><b>执行ID</b><code>{{ step.execution_id }}</code></p>
                    <p v-if="step.model_version"><b>版本</b><code>{{ step.model_version }}</code></p>
                    <p v-if="step.error" class="trace-error"><b>{{ step.error_code }}</b>{{ step.error }}</p>
                    <p v-if="warningCount(step)"><b>边界警告</b>{{ warningCount(step) }} 条</p>
                    <p v-if="sourceCount(step)"><b>来源记录</b>{{ sourceCount(step) }} 条</p>
                    <a v-if="hasDownload(step)" :href="artifactDownload(step)" class="artifact-link" download>
                      <i class="fas fa-download"></i> 下载可复核文件包
                    </a>
                    <pre v-if="step.output">{{ JSON.stringify(step.output, null, 2) }}</pre>
                  </div>
                </details>
              </div>
            </template>
          </div>
        </section>

        <section v-if="workOrder" class="work-order-section">
          <div class="section-heading compact">
            <div><span class="section-index">05</span><h2>证据工单</h2></div>
            <span class="order-state" :class="workOrder.status">{{ workOrderStatusLabel }}</span>
          </div>
          <div class="order-grid">
            <article class="order-paper">
              <div class="paper-stamp">DECISION SUPPORT</div>
              <pre>{{ displayedNarrative }}</pre>
            </article>
            <aside class="order-controls">
              <div class="guard-card">
                <i class="fas fa-shield-halved"></i>
                <div><strong>数值由工具锁定</strong><p>大模型只能改写文本，不能新增或改变数值、单位和状态；仅发送执行标识与短标量证据。</p></div>
              </div>
              <label class="switch-row">
                <span><b>大模型文本辅助</b><small>可选；失败时保留确定性模板</small></span>
                <input v-model="llmEnabled" type="checkbox">
              </label>
              <template v-if="llmEnabled">
                <label class="field-label">文本风格
                  <select v-model="narrativeStyle">
                    <option value="concise">简洁</option>
                    <option value="standard">标准工单</option>
                    <option value="detailed">详细复核</option>
                  </select>
                </label>
                <label class="field-label">目标读者
                  <select v-model="narrativeAudience">
                    <option value="operator">操作人员</option>
                    <option value="engineer">工艺工程师</option>
                    <option value="reviewer">审核人员</option>
                  </select>
                </label>
                <button class="secondary-action" :disabled="narrativeLoading" @click="generateNarrative">
                  <i :class="['fas', narrativeLoading ? 'fa-circle-notch fa-spin' : 'fa-wand-magic-sparkles']"></i>
                  {{ narrativeLoading ? '约束生成中' : '生成辅助文本' }}
                </button>
              </template>
              <div v-if="narrativeMessage" class="inline-alert" :class="{ success: narrativeMode === 'llm' }">{{ narrativeMessage }}</div>
              <div class="review-box">
                <strong>人工审核</strong>
                <input v-model.trim="reviewer" maxlength="120" placeholder="审核人姓名">
                <textarea v-model="reviewComment" maxlength="1000" placeholder="审核意见（可选）"></textarea>
                <div>
                  <button class="reject-button" :disabled="reviewing" @click="reviewWorkOrder('reject')">退回</button>
                  <button class="approve-button" :disabled="reviewing || !workOrder.release_eligible" @click="reviewWorkOrder('approve')">批准人工执行</button>
                </div>
                <small>平台不连接生产控制系统，批准动作仅记录审核状态。</small>
              </div>
            </aside>
          </div>
        </section>

        <section class="tool-coverage">
          <details>
            <summary><span><span class="section-index">06</span><b>本场景可复用工具</b></span><em>{{ scene.applicable_tool_count }} / {{ registryCounts.registered }}</em></summary>
            <div class="tool-tags">
              <router-link v-for="tool in scene.featured_tools" :key="tool.model_code" :to="`/scene?model=${tool.model_code}`">
                <b>{{ tool.model_code }}</b>{{ tool.name }}
              </router-link>
              <span v-for="code in nonFeaturedToolIds" :key="code">{{ code }}</span>
            </div>
          </details>
        </section>
      </template>
    </main>
  </div>
  <Footer />
</template>

<script>
import Header from '@/components/Header.vue';
import Footer from '@/components/Footer.vue';

export default {
  name: 'SceneWorkbench',
  components: { Header, Footer },
  props: { sceneId: { type: String, required: true } },
  data() {
    return {
      scenes: [], scene: null, recipe: null, selectedRecipeId: '',
      registryCounts: { registered: 0, qualified: 0 },
      requestText: '', pristineRequest: '', loading: true, running: false,
      inputError: '', errorMessage: '', run: null, workOrder: null,
      autoCompileWorkOrder: true, llmEnabled: false, narrativeStyle: 'standard',
      narrativeAudience: 'engineer', narrativeLoading: false, narrativeText: '',
      narrativeMode: 'template', narrativeMessage: '', reviewer: '', reviewComment: '', reviewing: false,
    };
  },
  computed: {
    sceneCssVars() { return { '--scene-accent': this.scene?.color || '#345B8C' }; },
    runStatusLabel() {
      return { success: '工具链执行成功', rejected: '工具链被拒绝', partial: '工具链部分完成' }[this.run?.status] || this.run?.status;
    },
    workOrderStatusLabel() {
      return {
        ready_for_human_review: '等待人工审核', draft_unverified: '未验证草案',
        approved_for_manual_execution: '已批准人工执行', rejected_by_reviewer: '已退回',
      }[this.workOrder?.status] || this.workOrder?.status;
    },
    displayedNarrative() { return this.narrativeText || this.workOrder?.deterministic_markdown || ''; },
    publicScenes() { return this.scenes.filter(item => item.scene_id !== 'simulation'); },
    nonFeaturedToolIds() {
      const featured = new Set((this.scene?.featured_tools || []).map(item => item.model_code));
      return (this.scene?.applicable_tool_ids || []).filter(code => !featured.has(code));
    },
  },
  watch: {
    sceneId() { this.loadScenes(); },
  },
  mounted() { this.loadScenes(); },
  methods: {
    async fetchJson(url, options) {
      const response = await fetch(url, options);
      const body = await response.json();
      if (!response.ok) {
        const detail = body.detail || body;
        const message = detail.message || detail.error || body.message || `请求失败 (${response.status})`;
        const error = new Error(message);
        error.payload = body;
        throw error;
      }
      return body;
    },
    async loadScenes() {
      this.loading = true; this.errorMessage = ''; this.scene = null; this.recipe = null;
      try {
        const payload = await this.fetchJson('/api/v1/scenes');
        this.scenes = payload.scenes || [];
        this.registryCounts = { registered: payload.registered_count || 0, qualified: payload.qualified_executable_count || 0 };
        this.scene = this.scenes.find(item => item.scene_id === this.sceneId);
        if (!this.scene) throw new Error(`未知场景：${this.sceneId}`);
        const initial = this.scene.recipes[0];
        if (initial) await this.selectRecipe(initial.recipe_id);
      } catch (error) {
        this.errorMessage = error.message;
      } finally { this.loading = false; }
    },
    async selectRecipe(recipeId) {
      this.selectedRecipeId = recipeId; this.run = null; this.workOrder = null;
      this.narrativeText = ''; this.narrativeMessage = ''; this.inputError = '';
      try {
        this.recipe = await this.fetchJson(`/api/v1/scenes/${encodeURIComponent(this.sceneId)}/recipes/${encodeURIComponent(recipeId)}`);
        this.pristineRequest = JSON.stringify(this.recipe.sample_request, null, 2);
        this.requestText = this.pristineRequest;
      } catch (error) { this.inputError = error.message; }
    },
    resetExample() { this.requestText = this.pristineRequest; this.inputError = ''; },
    async executeRecipe() {
      this.inputError = ''; this.errorMessage = ''; this.run = null; this.workOrder = null;
      this.narrativeText = ''; this.narrativeMessage = '';
      let payload;
      try { payload = JSON.parse(this.requestText); }
      catch (error) { this.inputError = `JSON格式错误：${error.message}`; return; }
      this.running = true;
      try {
        this.run = await this.fetchJson(`/api/v1/scenes/${encodeURIComponent(this.sceneId)}/recipes/${encodeURIComponent(this.selectedRecipeId)}/execute`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload),
        });
        if (this.autoCompileWorkOrder && this.run.successful_step_count > 0) await this.compileWorkOrder();
      } catch (error) { this.inputError = error.message; }
      finally { this.running = false; }
    },
    async compileWorkOrder() {
      this.workOrder = await this.fetchJson(`/api/v1/scenes/${encodeURIComponent(this.sceneId)}/work-orders`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ run_id: this.run.run_id }),
      });
      this.narrativeMode = 'template';
    },
    stepStatus(stepId) {
      const record = this.run?.steps?.find(item => item.step_id === stepId);
      return record?.status || (this.run ? 'pending' : 'idle');
    },
    statusIcon(status) { return { success: 'fa-check', rejected: 'fa-xmark', error: 'fa-xmark', skipped: 'fa-forward' }[status] || 'fa-minus'; },
    warningCount(step) { return step.boundary_check?.warnings?.length || 0; },
    sourceCount(step) { return step.actual_data_records?.length || 0; },
    hasDownload(step) { return Boolean(step.artifact?.zip_path || (step.model_code === 'G005' && step.output?.zip_path)); },
    artifactDownload(step) { return `/api/v1/executions/${encodeURIComponent(step.execution_id)}/artifact/download`; },
    async generateNarrative() {
      if (!this.llmEnabled || !this.workOrder) return;
      this.narrativeLoading = true; this.narrativeMessage = '';
      try {
        const result = await this.fetchJson(`/api/v1/scenes/${encodeURIComponent(this.sceneId)}/work-orders/${encodeURIComponent(this.workOrder.work_order_id)}/narrative`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ enabled: true, style: this.narrativeStyle, audience: this.narrativeAudience }),
        });
        this.narrativeText = result.narrative;
        this.narrativeMode = 'llm';
        this.narrativeMessage = `辅助文本已通过数值漂移与越权声明检查 · ${result.generator.model}`;
      } catch (error) {
        this.narrativeText = error.payload?.fallback_text || '';
        this.narrativeMode = 'template';
        this.narrativeMessage = `${error.message}；已保留确定性模板。`;
      } finally { this.narrativeLoading = false; }
    },
    async reviewWorkOrder(action) {
      if (!this.reviewer) { this.narrativeMessage = '请先填写审核人。'; return; }
      this.reviewing = true;
      try {
        this.workOrder = await this.fetchJson(`/api/v1/work-orders/${encodeURIComponent(this.workOrder.work_order_id)}/review`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ action, reviewer: this.reviewer, comment: this.reviewComment }),
        });
        this.narrativeMessage = action === 'approve' ? '已记录人工批准；平台不会自动下发控制指令。' : '工单已退回。';
      } catch (error) { this.narrativeMessage = error.message; }
      finally { this.reviewing = false; }
    },
  },
};
</script>

<style scoped>
.scene-workbench { min-height: 100vh; padding-top: 80px; color: #17212d; background: #eef1f3; font-family: "Microsoft YaHei", "Noto Sans SC", sans-serif; }
.scene-rail { color: #aeb8c5; background: #111b26; border-bottom: 1px solid #2c3947; }
.rail-inner { display: flex; gap: 9px; padding-top: 11px; padding-bottom: 11px; font-size: 12px; }
.scene-rail a { color: #d4dbe2; text-decoration: none; }
.scene-rail strong { color: #fff; }
.scene-hero { position: relative; overflow: hidden; color: #fff; background: #172532; }
.hero-grid { position: absolute; inset: 0; opacity: .2; background-image: linear-gradient(rgba(255,255,255,.14) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.14) 1px, transparent 1px); background-size: 34px 34px; mask-image: linear-gradient(90deg, #000, transparent 72%); }
.scene-hero::after { content: ""; position: absolute; right: -8vw; top: -16vw; width: 42vw; height: 42vw; border: 90px solid var(--scene-accent); border-radius: 50%; opacity: .32; }
.hero-inner { position: relative; z-index: 1; min-height: 230px; display: flex; align-items: center; justify-content: space-between; gap: 50px; }
.hero-copy { max-width: 720px; }
.eyebrow { display: block; margin-bottom: 16px; color: #d7dde3; font-family: Consolas, monospace; font-size: 11px; letter-spacing: .18em; }
.hero-copy h1 { margin: 0 0 12px; font-family: "STZhongsong", "SimSun", serif; font-size: clamp(34px, 4vw, 56px); font-weight: 700; letter-spacing: .05em; }
.hero-copy p { max-width: 670px; margin: 0; color: #c9d0d7; font-size: 16px; line-height: 1.8; }
.hero-metrics { display: grid; grid-template-columns: repeat(3, 1fr); min-width: 390px; border: 1px solid rgba(255,255,255,.2); background: rgba(9,18,27,.65); backdrop-filter: blur(10px); }
.hero-metrics div { padding: 20px 18px; border-right: 1px solid rgba(255,255,255,.15); text-align: center; }
.hero-metrics div:last-child { border-right: 0; }
.hero-metrics b { display: block; color: #fff; font: 700 28px/1 Consolas, monospace; }
.hero-metrics span { display: block; margin-top: 8px; color: #aeb8c2; font-size: 11px; }
.scene-tabs { display: flex; gap: 0; margin-top: -1px; padding: 0; background: #fff; border: 1px solid #d8dde1; box-shadow: 0 8px 24px rgba(31,44,55,.07); }
.scene-tabs a { flex: 1; display: flex; align-items: center; justify-content: center; gap: 9px; min-height: 58px; color: #66717b; border-right: 1px solid #e2e6e9; text-decoration: none; font-size: 13px; transition: .2s ease; }
.scene-tabs a:last-child { border-right: 0; }
.scene-tabs a:hover { color: #1d2b38; background: #f7f8f9; }
.scene-tabs a.active { color: #fff; background: var(--scene-accent); }
.workbench-body { padding-top: 36px; padding-bottom: 90px; }
.state-panel { padding: 60px; text-align: center; background: #fff; border: 1px solid #d9dee2; }
.state-panel i { margin-right: 8px; color: var(--scene-accent); }
.state-panel.error, .inline-alert { color: #9a342e; background: #fff2ef; border: 1px solid #edc1ba; }
.section-heading { display: flex; justify-content: space-between; align-items: end; gap: 24px; margin-bottom: 20px; }
.section-heading > div, .panel-title > div { display: flex; align-items: center; gap: 12px; }
.section-heading h2, .panel-title h2 { margin: 0; font-family: "STZhongsong", "SimSun", serif; font-size: 24px; }
.section-heading p { margin: 0; color: #74808a; font-size: 12px; }
.section-index { color: var(--scene-accent); font: 700 12px/1 Consolas, monospace; letter-spacing: .08em; }
.recipe-strip { display: grid; grid-template-columns: minmax(240px, .7fr) repeat(2, 1fr); gap: 18px; margin-bottom: 34px; }
.recipe-strip .section-heading { grid-column: 1 / -1; }
.recipe-card { position: relative; min-height: 142px; padding: 24px; text-align: left; color: #263340; background: #fff; border: 1px solid #d7dde1; cursor: pointer; transition: .2s ease; }
.recipe-card:hover, .recipe-card.selected { border-color: var(--scene-accent); box-shadow: inset 4px 0 var(--scene-accent), 0 10px 25px rgba(26,39,52,.08); transform: translateY(-2px); }
.recipe-card strong, .recipe-card small { display: block; }
.recipe-card strong { margin: 13px 0 8px; font-size: 17px; }
.recipe-card small { color: #68747f; line-height: 1.6; }
.recipe-version { color: var(--scene-accent); font: 700 11px Consolas, monospace; }
.recipe-count { position: absolute; right: 16px; top: 16px; color: #89939c; font-size: 10px; }
.pipeline-section { margin-bottom: 34px; padding: 24px; background: #fff; border: 1px solid #d7dde1; }
.section-heading.compact { align-items: center; }
.pipeline { display: flex; align-items: stretch; gap: 8px; overflow-x: auto; padding: 8px 2px 14px; }
.pipeline-step { position: relative; flex: 0 0 190px; display: flex; gap: 10px; min-height: 94px; padding: 15px; background: #f4f6f7; border: 1px solid #dce1e4; }
.pipeline-step.success { border-color: #77a990; background: #eef7f2; }
.pipeline-step.rejected, .pipeline-step.error { border-color: #d99387; background: #fff1ef; }
.pipeline-step.skipped { opacity: .55; }
.step-no { color: #8c969e; font: 700 10px Consolas, monospace; }
.pipeline-step b, .pipeline-step strong, .pipeline-step small { display: block; }
.pipeline-step b { color: var(--scene-accent); font: 700 12px Consolas, monospace; }
.pipeline-step strong { margin: 3px 0; font-size: 13px; }
.pipeline-step small { color: #75808a; font-size: 10px; line-height: 1.45; }
.artifact-mark { position: absolute; right: 9px; top: 9px; color: #a76a1d; }
.pipeline-arrow { align-self: center; color: #a7b0b8; }
.execution-grid { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.1fr); gap: 20px; margin-bottom: 36px; }
.control-panel, .run-panel { min-width: 0; padding: 25px; background: #fff; border: 1px solid #d7dde1; }
.panel-title { display: flex; align-items: center; justify-content: space-between; gap: 16px; margin-bottom: 14px; }
.panel-title h2 { font-size: 20px; }
.panel-note { color: #707c86; font-size: 11px; line-height: 1.7; }
.control-panel > textarea { width: 100%; height: 430px; box-sizing: border-box; padding: 15px; resize: vertical; color: #dce7ef; background: #16212b; border: 1px solid #2e3c48; outline: none; font: 12px/1.65 Consolas, monospace; }
.control-panel > textarea:focus { border-color: var(--scene-accent); box-shadow: 0 0 0 2px color-mix(in srgb, var(--scene-accent) 20%, transparent); }
.text-button { padding: 0; color: var(--scene-accent); background: none; border: 0; cursor: pointer; font-size: 11px; }
.control-actions { display: flex; align-items: center; justify-content: space-between; gap: 14px; margin-top: 15px; }
.check-control { display: flex; align-items: center; gap: 8px; color: #58636c; font-size: 12px; }
.check-control input, .switch-row input { accent-color: var(--scene-accent); }
.primary-action, .secondary-action, .approve-button, .reject-button { border: 0; cursor: pointer; transition: .2s ease; }
.primary-action { min-width: 180px; padding: 13px 18px; color: #fff; background: var(--scene-accent); font-weight: 700; }
.primary-action:hover { filter: brightness(.9); transform: translateY(-1px); }
button:disabled { cursor: not-allowed; opacity: .45; transform: none !important; }
.run-id { max-width: 210px; overflow: hidden; color: #64717b; font: 10px Consolas, monospace; text-overflow: ellipsis; white-space: nowrap; }
.empty-run { display: grid; place-items: center; min-height: 430px; color: #87919a; text-align: center; border: 1px dashed #cbd2d7; }
.empty-run i { color: var(--scene-accent); font-size: 34px; }
.empty-run strong { margin-top: -100px; color: #43505b; }
.empty-run p { max-width: 300px; margin-top: -130px; font-size: 12px; line-height: 1.7; }
.run-summary { display: flex; align-items: center; gap: 12px; padding: 14px; background: #f4f6f7; border-left: 4px solid var(--scene-accent); }
.status-dot { width: 10px; height: 10px; border-radius: 50%; background: #b9c0c5; }
.status-dot.success { background: #2f8b61; box-shadow: 0 0 0 5px rgba(47,139,97,.12); }
.status-dot.rejected { background: #bd4138; }
.run-summary strong, .run-summary small { display: block; }
.run-summary small { margin-top: 3px; color: #7d878e; font-size: 10px; }
.safety-chip { margin-left: auto; padding: 7px 10px; color: #99413b; background: #f9e9e7; font-size: 10px; }
.safety-chip.passed { color: #256948; background: #e4f1e9; }
.trace-list { max-height: 500px; margin-top: 13px; overflow: auto; }
.trace-item { border-bottom: 1px solid #e4e8ea; }
.trace-item summary { display: flex; align-items: center; gap: 11px; padding: 13px 5px; cursor: pointer; list-style: none; }
.trace-item summary::-webkit-details-marker { display: none; }
.trace-icon { display: grid; place-items: center; width: 24px; height: 24px; color: #fff; background: #7f8a93; border-radius: 50%; font-size: 10px; }
.trace-item.success .trace-icon { background: #2f8b61; }
.trace-item.rejected .trace-icon, .trace-item.error .trace-icon { background: #bd4138; }
.trace-item summary div { flex: 1; }
.trace-item summary b { margin-right: 8px; color: var(--scene-accent); font: 700 11px Consolas, monospace; }
.trace-item summary strong { font-size: 12px; }
.trace-item summary small { color: #7d878e; font: 10px Consolas, monospace; }
.trace-detail { padding: 0 8px 16px 40px; }
.trace-detail p { display: flex; gap: 10px; margin: 6px 0; color: #68747d; font-size: 11px; }
.trace-detail p b { min-width: 62px; color: #303d47; }
.trace-detail code { word-break: break-all; }
.trace-detail pre { max-height: 260px; overflow: auto; padding: 12px; color: #d8e2ea; background: #17222c; font: 10px/1.5 Consolas, monospace; white-space: pre-wrap; }
.trace-error { color: #a23831 !important; }
.artifact-link { display: inline-flex; gap: 7px; margin-top: 8px; color: var(--scene-accent); font-size: 11px; text-decoration: none; }
.work-order-section { margin-bottom: 36px; padding: 28px; background: #dfe4e6; border: 1px solid #c8d0d4; }
.order-state { padding: 7px 11px; color: #8c5c1c; background: #fff3d8; font-size: 11px; }
.order-state.approved_for_manual_execution { color: #1e6946; background: #dff1e7; }
.order-state.rejected_by_reviewer, .order-state.draft_unverified { color: #91362f; background: #f8e5e3; }
.order-grid { display: grid; grid-template-columns: minmax(0, 1.4fr) minmax(280px, .6fr); gap: 22px; }
.order-paper { position: relative; min-height: 430px; padding: 42px; overflow: hidden; background: #fffdfa; border: 1px solid #cec8bc; box-shadow: 0 13px 35px rgba(35,43,48,.12); }
.order-paper::before { content: ""; position: absolute; inset: 12px; pointer-events: none; border: 1px solid #ded8cb; }
.paper-stamp { position: absolute; right: 34px; top: 27px; padding: 7px 10px; color: #9e3f32; border: 2px solid #9e3f32; opacity: .7; transform: rotate(2deg); font: 700 10px Consolas, monospace; letter-spacing: .08em; }
.order-paper pre { position: relative; z-index: 1; margin: 0; color: #29323a; font: 12px/1.85 "Microsoft YaHei", sans-serif; white-space: pre-wrap; word-break: break-word; }
.order-controls { display: flex; flex-direction: column; gap: 13px; }
.guard-card { display: flex; gap: 12px; padding: 16px; color: #315b45; background: #edf7f1; border: 1px solid #bcd9c8; }
.guard-card i { margin-top: 3px; }
.guard-card strong, .guard-card p { display: block; margin: 0; }
.guard-card p { margin-top: 5px; color: #627a6c; font-size: 10px; line-height: 1.6; }
.switch-row { display: flex; justify-content: space-between; gap: 16px; padding: 15px; background: #fff; border: 1px solid #d3d9dc; }
.switch-row b, .switch-row small { display: block; }
.switch-row b { font-size: 12px; }
.switch-row small { margin-top: 4px; color: #78828a; font-size: 9px; }
.field-label { display: grid; grid-template-columns: 75px 1fr; align-items: center; gap: 10px; color: #59646d; font-size: 11px; }
.field-label select, .review-box input, .review-box textarea { padding: 9px 10px; background: #fff; border: 1px solid #cbd2d6; outline: none; }
.secondary-action { padding: 11px; color: #fff; background: #273a49; }
.inline-alert { margin-top: 10px; padding: 10px 12px; font-size: 10px; line-height: 1.5; }
.inline-alert.success { color: #256948; background: #e8f4ed; border-color: #b9d7c5; }
.review-box { display: flex; flex-direction: column; gap: 9px; padding: 16px; background: #fff; border: 1px solid #d3d9dc; }
.review-box > strong { font-size: 13px; }
.review-box textarea { min-height: 65px; resize: vertical; }
.review-box > div { display: grid; grid-template-columns: 1fr 1.5fr; gap: 8px; }
.reject-button, .approve-button { padding: 10px; }
.reject-button { color: #87352f; background: #f7e8e6; }
.approve-button { color: #fff; background: #2e7452; }
.review-box > small { color: #7c868d; font-size: 9px; line-height: 1.5; }
.tool-coverage details { background: #fff; border: 1px solid #d7dde1; }
.tool-coverage summary { display: flex; justify-content: space-between; padding: 18px 22px; cursor: pointer; list-style: none; }
.tool-coverage summary span { display: flex; align-items: center; gap: 12px; }
.tool-coverage summary em { color: var(--scene-accent); font: normal 700 12px Consolas, monospace; }
.tool-tags { display: flex; flex-wrap: wrap; gap: 7px; padding: 0 22px 22px; }
.tool-tags a, .tool-tags > span { padding: 6px 9px; color: #59656e; background: #f1f3f4; border: 1px solid #e0e4e6; font-size: 10px; text-decoration: none; }
.tool-tags a { color: #fff; background: var(--scene-accent); border-color: var(--scene-accent); }
.tool-tags a b { margin-right: 5px; font-family: Consolas, monospace; }
@media (max-width: 1050px) {
  .hero-inner { align-items: flex-start; flex-direction: column; padding-top: 42px; padding-bottom: 42px; }
  .hero-metrics { width: 100%; min-width: 0; }
  .execution-grid, .order-grid { grid-template-columns: 1fr; }
  .recipe-strip { grid-template-columns: 1fr; }
  .recipe-strip .section-heading { grid-column: auto; }
}
@media (max-width: 720px) {
  .scene-tabs { overflow-x: auto; }
  .scene-tabs a { flex: 0 0 145px; }
  .section-heading { align-items: flex-start; flex-direction: column; }
  .hero-metrics div { padding: 15px 8px; }
  .hero-metrics b { font-size: 22px; }
  .control-panel, .run-panel, .work-order-section { padding: 16px; }
  .order-paper { padding: 34px 24px; }
  .control-actions { align-items: stretch; flex-direction: column; }
  .primary-action { width: 100%; }
}
</style>
