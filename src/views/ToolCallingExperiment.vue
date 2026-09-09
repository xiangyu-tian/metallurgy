<template>
  <div class="experiment-page">
    <Header />

    <main class="experiment-shell">
      <section class="hero-panel">
        <div>
          <p class="eyebrow">METALLURGY PLATFORM · ORCHESTRATION LAB</p>
          <h1>生产级工具调用实验台</h1>
          <p class="hero-copy">
            从自然语言中选择候选工具、提取参数并执行；结果回传大模型后再组织答案。正式聊天页暂不接入本实验逻辑。
          </p>
        </div>
        <div class="baseline-stamp">
          <span>QUALIFIED</span>
          <strong>{{ tools.length || 120 }}</strong>
          <small>TOOL REGISTRY</small>
        </div>
      </section>

      <section class="scope-notice">
        <span>实验边界</span>
        <p>只验证新增调用编排层，不重复执行已通过的工具测试；最终验收阶段再进行 120 项总复核。</p>
        <code>/api/v1/experiments/tool-orchestration</code>
      </section>

      <section class="bench-grid">
        <form class="control-panel" @submit.prevent="runExperiment">
          <div class="panel-heading">
            <span class="panel-index">01</span>
            <div>
              <h2>编排条件</h2>
              <p>NATURAL LANGUAGE → TOOL CHAIN</p>
            </div>
          </div>

          <div v-if="conversationHistory.length" class="session-bar">
            <div>
              <strong>{{ awaitingClarification ? '同一编排正在等待补参' : '连续会话已开启' }}</strong>
              <small v-if="awaitingClarification">{{ result.orchestration_id }} · 已完成步骤不会重复执行</small>
              <small v-else>已保留 {{ conversationHistory.length / 2 }} 轮上下文</small>
            </div>
            <button type="button" @click="resetSession">新建实验会话</button>
          </div>

          <label class="field field-wide">
            <span>{{ awaitingClarification ? '补充缺失参数' : '用户问题' }}</span>
            <textarea
              ref="queryInput"
              v-model.trim="form.userQuery"
              rows="5"
              :placeholder="queryPlaceholder"
              required
            ></textarea>
            <small class="field-note">参数只从自然语言和当前会话提取；没有默认值的必填参数不会被猜测。</small>
          </label>

          <div class="mode-selector" role="radiogroup" aria-label="调用模式">
            <button
              v-for="mode in modes"
              :key="mode.value"
              type="button"
              :class="['mode-button', { active: form.mode === mode.value }]"
              :disabled="awaitingClarification"
              @click="form.mode = mode.value"
            >
              <span>{{ mode.code }}</span>
              <strong>{{ mode.label }}</strong>
              <small>{{ mode.hint }}</small>
            </button>
          </div>

          <div class="field-row">
            <label class="field">
              <span>业务场景</span>
              <select v-model="form.scene" :disabled="awaitingClarification">
                <option v-for="scene in scenes" :key="scene.value" :value="scene.value">
                  {{ scene.label }}
                </option>
              </select>
            </label>
            <label class="field">
              <span>候选集策略</span>
              <select v-model="form.catalogMode" :disabled="awaitingClarification">
                <option value="production">生产候选集（默认）</option>
                <option value="research_full">全量 120 工具研究</option>
              </select>
            </label>
          </div>

          <label class="field field-wide">
            <span>参数校验策略</span>
            <select v-model="form.parameterValidationMode" :disabled="awaitingClarification">
              <option value="traditional">传统 Tool Use（默认基线）</option>
              <option value="evidence_enhanced">参数证据增强（RQ3干预）</option>
            </select>
            <small class="field-note" v-if="form.parameterValidationMode === 'traditional'">
              仅由候选/权限、JSON、Schema和工具业务规则阻断；参数来源继续记录，但不阻断执行。
            </small>
            <small class="field-note" v-else>
              在传统校验之外，要求每个非默认参数可追溯到用户输入或前序工具结果。
            </small>
          </label>

          <label class="strict-field">
            <input v-model="form.strictToolSchemas" type="checkbox" :disabled="awaitingClarification" />
            <span>
              请求供应商 Strict Schema
              <small>仅在供应商端点和当前工具契约都兼容时启用；否则保留 Ajv 应用侧完整校验。</small>
            </span>
          </label>

          <label v-if="form.mode === 'forced'" class="field field-wide">
            <span>强制调用工具</span>
            <select v-model="form.forcedTool" :disabled="toolsLoading || awaitingClarification" required>
              <option value="">{{ toolsLoading ? '读取合格工具注册表中…' : '请选择工具' }}</option>
              <option v-for="tool in sortedTools" :key="tool.model_code" :value="tool.model_code">
                {{ tool.model_code }} · {{ tool.model_name || tool.function?.name }}
              </option>
            </select>
          </label>

          <div class="field-row compact-row">
            <label class="field">
              <span>最大候选数</span>
              <input v-model.number="form.maxCandidates" type="number" min="1" max="24" :disabled="awaitingClarification" />
            </label>
            <label v-if="form.mode === 'plan'" class="field">
              <span>最大工具调用数</span>
              <input v-model.number="form.maxToolCalls" type="number" min="1" max="6" :disabled="awaitingClarification" />
            </label>
            <div v-else class="fixed-limit">
              <span>本模式调用上限</span>
              <strong>1 个工具</strong>
            </div>
          </div>

          <div class="policy-note" :class="{ research: form.catalogMode === 'research_full' }">
            <strong>{{ form.catalogMode === 'research_full' ? 'RESEARCH FULL CATALOG' : 'PRODUCTION CANDIDATE SET' }}</strong>
            <p v-if="form.catalogMode === 'research_full'">显式向模型暴露全量合格工具，包括历史嵌套契约未收口项，仅用于后续 30 / 60 / 100+ 规模研究。</p>
            <p v-else>先隔离输入契约未收口项，再按问题与场景筛选候选；模型本轮只看到相关且契约完整的工具。</p>
          </div>

          <p v-if="errorMessage" class="error-message" role="alert">{{ errorMessage }}</p>
          <button class="run-button" type="submit" :disabled="running || toolsLoading">
            <span>{{ runButtonLabel }}</span>
            <span class="run-arrow">→</span>
          </button>
        </form>

        <section class="trace-panel">
          <div class="panel-heading">
            <span class="panel-index">02</span>
            <div>
              <h2>决策轨迹</h2>
              <p>{{ result ? result.orchestration_id : '等待实验运行' }}</p>
            </div>
            <span v-if="result" class="mode-tag">{{ modeLabel(result.request?.mode) }}</span>
          </div>

          <div v-if="!result" class="empty-state">
            <div class="empty-orbit"><span></span></div>
            <strong>尚无编排记录</strong>
            <p>提交左侧自然语言问题后，这里将呈现完整决策链。</p>
          </div>

          <template v-else>
            <div
              class="tool-use-status"
              :class="`is-${toolUseStatus.tone}`"
              role="status"
              :aria-label="toolUseStatus.label"
            >
              <span class="tool-use-indicator" aria-hidden="true"></span>
              <div>
                <small>TOOL EXECUTION STATUS</small>
                <strong>{{ toolUseStatus.label }}</strong>
                <p>{{ toolUseStatus.detail }}</p>
              </div>
              <code>{{ toolUseStatus.code }}</code>
            </div>

            <ol class="trace-list">
              <li v-for="step in traceSteps" :key="step.label" :class="step.state">
                <span class="trace-dot"></span>
                <div>
                  <strong>{{ step.label }}</strong>
                  <p>{{ step.value }}</p>
                </div>
              </li>
            </ol>

            <div class="evidence-grid">
              <article>
                <span>生产契约就绪</span>
                <strong>{{ result.candidate_selection?.production_contract_ready_count || 0 }} / {{ result.candidate_selection?.source_tool_count || 0 }}</strong>
              </article>
              <article>
                <span>向模型暴露</span>
                <strong>{{ result.candidate_selection?.exposed_tool_count || 0 }}</strong>
              </article>
              <article>
                <span>成功执行</span>
                <strong :class="{ 'status-success': result.successful_tool_call_count > 0 }">
                  {{ result.successful_tool_call_count || 0 }} / {{ result.tool_call_count || 0 }}
                </strong>
              </article>
              <article>
                <span>总延迟</span>
                <strong>{{ result.latency_ms }} ms</strong>
              </article>
            </div>

            <div v-if="result.clarification?.required" class="clarification-panel">
              <span>ORCHESTRATION WAITING FOR INPUT</span>
              <strong>{{ result.status === 'partially_completed_waiting_for_input' ? '已保留完成步骤，补参后继续原编排' : '参数不足，工具没有执行' }}</strong>
              <p>{{ result.clarification.question }}</p>
              <ul>
                <li v-for="field in result.clarification.fields" :key="`${field.tool}-${field.field}`">
                  <code>{{ field.tool }}.{{ field.field }}</code>
                  <span>{{ field.message }}</span>
                </li>
              </ul>
            </div>
          </template>
        </section>
      </section>

      <template v-if="result">
        <section class="result-grid">
          <article class="result-card answer-card">
            <div class="card-label">PRODUCT RESULT VIEW · NO TOOL TRACE</div>
            <h3>{{ result.clarification?.required ? '面向用户的必要追问' : '面向用户的最终结论' }}</h3>
            <p>{{ result.product_view?.content || result.answer }}</p>
            <aside v-if="result.product_view?.warning">{{ result.product_view.warning }}</aside>
          </article>

          <article class="result-card selection-card">
            <div class="card-label">CANDIDATE EXPOSURE</div>
            <h3>候选工具筛选</h3>
            <p class="selection-reason">{{ result.candidate_selection?.reason }}</p>
            <div v-if="candidateTools.length" class="candidate-list">
              <span v-for="tool in candidateTools" :key="tool.model_code">
                <b>{{ tool.model_code }}</b>{{ tool.model_name || tool.function_name }}
              </span>
            </div>
            <p v-else class="muted-copy">模型判断无需调用工具，或没有匹配的候选工具。</p>
            <dl class="selection-facts">
              <dt>筛选方法</dt><dd>{{ result.candidate_selection?.method }}</dd>
              <dt>识别场景</dt><dd>{{ result.candidate_selection?.inferred_scene || '未指定' }}</dd>
              <dt>上下文范围</dt><dd>{{ queryScopeLabel }}</dd>
              <dt>参数校验</dt><dd>{{ parameterValidationModeLabel(result.request?.parameter_validation_mode) }}</dd>
              <dt>Strict 状态</dt><dd>{{ toolContractLabel(result.tool_contract) }}</dd>
            </dl>
          </article>
        </section>

        <section v-if="result.plan?.steps?.length" class="plan-board">
          <div class="section-heading">
            <div>
              <span>03</span>
              <h2>多工具执行计划</h2>
            </div>
            <p>{{ result.plan.reason }}</p>
          </div>
          <ol>
            <li v-for="step in result.plan.steps" :key="step.step_id">
              <b>{{ step.step_id }}</b>
              <div>
                <strong>{{ step.model_code }} · {{ step.function_name }}</strong>
                <p>{{ step.purpose }}</p>
                <small>{{ step.depends_on?.length ? `依赖 ${step.depends_on.join('、')}` : '无前置依赖' }}</small>
              </div>
            </li>
          </ol>
        </section>

        <section class="audit-board">
          <div class="section-heading">
            <div>
              <span>{{ result.plan?.steps?.length ? '04' : '03' }}</span>
              <h2>工具执行审计</h2>
            </div>
            <p>选择了什么工具 — 输入什么 — 返回什么 — 依据什么</p>
          </div>

          <div v-if="!result.tool_calls?.length" class="no-call">
            本轮没有产生工具调用。候选筛选和模型回答仍绑定编排 ID，可用于复核决策。
          </div>

          <article
            v-for="(call, index) in result.tool_calls"
            :key="call.call_id || `${call.function_name}-${index}`"
            class="call-record"
          >
            <header>
              <span>{{ String(index + 1).padStart(2, '0') }}</span>
              <div>
                <strong>{{ call.model_code || call.function_name || '未识别工具' }}</strong>
                <small>{{ call.model_name || call.function_name }}</small>
              </div>
              <code :class="statusTone(call.status)">{{ call.status }}</code>
            </header>

            <div class="audit-grid">
              <section>
                <span>选择了什么工具</span>
                <strong>{{ call.model_code }} · {{ call.function_name }}</strong>
                <p>{{ call.selection_reason || result.candidate_selection?.reason }}</p>
                <dl>
                  <dt>计划步骤</dt><dd>{{ call.planned_step_id || '单工具调用' }}</dd>
                  <dt>分类</dt><dd>{{ call.category || '—' }}</dd>
                </dl>
              </section>
              <section>
                <span>输入什么</span>
                <pre>{{ formatJson(call.arguments) }}</pre>
                <small v-if="call.schema_validation?.defaults_applied?.length">
                  Schema 默认值：{{ call.schema_validation.defaults_applied.map(item => item.field).join('、') }}
                </small>
                <small v-else>Schema {{ call.schema_validation?.valid === false ? '校验失败' : '校验通过或未执行' }}</small>
                <ul v-if="parameterSources(call).length" class="parameter-sources">
                  <li v-for="item in parameterSources(call)" :key="item.field">
                    <code>{{ item.field }}</code><span>← {{ item.label }}</span>
                  </li>
                </ul>
              </section>
              <section>
                <span>返回什么</span>
                <pre v-if="call.output !== undefined && call.output !== null">{{ formatJson(call.output) }}</pre>
                <p v-else class="call-error">{{ call.error || '未执行，因此没有工具返回值。' }}</p>
              </section>
              <section>
                <span>依据什么</span>
                <dl class="basis-list">
                  <dt>执行 ID</dt><dd>{{ call.execution_id || '未执行' }}</dd>
                  <dt>工具版本</dt><dd>{{ call.model_version || '—' }}</dd>
                  <dt>工具 UID</dt><dd>{{ call.tool_uid || '—' }}</dd>
                  <dt>数据来源</dt>
                  <dd>
                    <ul>
                      <li v-for="source in sourceLabels(call)" :key="source">{{ source }}</li>
                    </ul>
                  </dd>
                  <dt>绑定 ID</dt><dd>{{ bindingFor(call)?.binding_id || '未生成' }}</dd>
                </dl>
              </section>
            </div>
          </article>
        </section>
      </template>
    </main>
  </div>
</template>

<script>
import Header from '@/components/Header.vue';

export default {
  name: 'ToolCallingExperiment',
  components: { Header },
  data() {
    return {
      tools: [],
      toolsLoading: false,
      running: false,
      result: null,
      errorMessage: '',
      conversationHistory: [],
      modes: [
        { value: 'forced', code: 'F', label: '强制调用', hint: '用户指定唯一工具' },
        { value: 'auto', code: 'A', label: '自动选择', hint: '筛选候选后自主决策' },
        { value: 'plan', code: 'P', label: '多工具规划', hint: '规划依赖并逐步执行' }
      ],
      scenes: [
        { value: '', label: '自动识别场景' },
        { value: 'general', label: '通用数据与基础计量' },
        { value: 'thermodynamics', label: '热力学与相平衡' },
        { value: 'converter', label: '转炉与炉外精炼' },
        { value: 'blastfurnace', label: '高炉低碳' },
        { value: 'casting', label: '凝固与连铸' },
        { value: 'simulation', label: '数值仿真与优化' }
      ],
      form: {
        userQuery: '请计算 Fe2O3 的摩尔质量',
        mode: 'auto',
        scene: '',
        catalogMode: 'production',
        parameterValidationMode: 'traditional',
        strictToolSchemas: false,
        forcedTool: '',
        maxCandidates: 12,
        maxToolCalls: 4
      }
    };
  },
  computed: {
    sortedTools() {
      return this.tools.slice().sort((left, right) =>
        String(left.model_code).localeCompare(String(right.model_code))
      );
    },
    awaitingClarification() {
      return Boolean(this.result?.clarification?.required);
    },
    queryPlaceholder() {
      if (this.awaitingClarification) return '直接补充缺失值，例如：温度为 1,600 K，压力为 101,325 Pa';
      return '例如：根据 Fe2O3 组成计算摩尔质量，并说明使用了哪个工具和数据依据';
    },
    runButtonLabel() {
      if (this.running) return '编排运行中';
      return this.awaitingClarification ? '提交补充参数并继续' : '运行编排实验';
    },
    candidateTools() {
      return this.result?.candidate_selection?.tools || [];
    },
    toolUseStatus() {
      const calls = this.result?.tool_calls || [];
      const executed = calls.filter(call => Boolean(call.execution_id));
      const successful = executed.filter(call => call.status === 'success');
      if (executed.length) {
        return {
          tone: 'called',
          label: '已调用工具',
          detail: `底层实际执行 ${executed.length} 次，其中 ${successful.length} 次成功`,
          code: 'CALLED'
        };
      }
      if (calls.length) {
        return {
          tone: 'blocked',
          label: '未执行工具',
          detail: `模型提出 ${calls.length} 个调用请求，但均在执行前被校验或策略拦截`,
          code: 'BLOCKED'
        };
      }
      return {
        tone: 'direct',
        label: '未调用工具',
        detail: '模型直接组织答案，本轮没有产生工具调用请求',
        code: 'DIRECT'
      };
    },
    queryScopeLabel() {
      return this.result?.candidate_selection?.query_scope === 'current_turn_and_history'
        ? '当前输入 + 会话历史'
        : '仅当前输入';
    },
    traceSteps() {
      if (!this.result) return [];
      const selection = this.result.candidate_selection || {};
      const calls = this.result.tool_calls || [];
      const needsInput = Boolean(this.result.clarification?.required);
      const partiallyCompleted = this.result.status === 'partially_completed_waiting_for_input';
      const executed = calls.filter(call => call.execution_id);
      const success = calls.filter(call => call.status === 'success');
      const plan = this.result.plan || {};
      return [
        {
          label: '候选工具筛选',
          value: `${selection.method || '—'} · ${selection.exposed_tool_count || 0} / ${selection.source_tool_count || 0} 项暴露`,
          state: 'done'
        },
        {
          label: this.result.request?.mode === 'plan' ? '生成多工具计划' : '确定调用策略',
          value: plan.steps?.length ? `${plan.steps.length} 个步骤 · ${plan.reason}` : (plan.reason || '无需多工具计划'),
          state: 'done'
        },
        {
          label: '自然语言参数提取与 Schema 校验',
          value: needsInput
            ? this.result.clarification.question
            : (calls.length
              ? (this.result.request?.parameter_validation_mode === 'evidence_enhanced'
                ? 'JSON、Schema与参数证据校验完成，允许执行'
                : 'JSON与Schema校验完成；参数来源仅记录，不阻断执行')
              : '本轮未生成工具参数'),
          state: needsInput ? (partiallyCompleted ? 'pending' : 'rejected') : 'done'
        },
        {
          label: '真实工具执行',
          value: executed.length ? `${success.length} 个成功，共 ${executed.length} 个获得执行 ID` : '未执行工具',
          state: executed.length ? 'done' : 'idle'
        },
        {
          label: '结果回传大模型',
          value: this.result.grounding?.tool_results_returned_to_model ? '真实工具结果已作为 tool 消息回传' : '没有可回传的成功结果',
          state: this.result.grounding?.tool_results_returned_to_model ? 'done' : 'idle'
        },
        {
          label: '答案与证据绑定',
          value: `${this.result.answer_bindings?.length || 0} 条绑定 · ${this.result.answer_mode}`,
          state: this.result.answer_bindings?.length || !calls.length ? 'done' : 'idle'
        }
      ];
    }
  },
  methods: {
    experimentApiUrl(path) {
      const port = process.env.VUE_APP_TOOL_EXPERIMENT_PORT || '3001';
      return `${window.location.protocol}//${window.location.hostname}:${port}${path}`;
    },
    modeLabel(mode) {
      return this.modes.find(item => item.value === mode)?.label || mode || '自动选择';
    },
    formatJson(value) {
      if (value === undefined || value === null) return '—';
      try {
        return JSON.stringify(value, null, 2);
      } catch (error) {
        return String(value);
      }
    },
    statusTone(status) {
      if (status === 'success') return 'success';
      if (status === 'needs_clarification' || status === 'rejected') return 'warning';
      return 'neutral';
    },
    parameterValidationModeLabel(mode) {
      return mode === 'evidence_enhanced' ? '参数证据增强（RQ3干预）' : '传统 Tool Use（默认基线）';
    },
    toolContractLabel(contract) {
      if (!contract?.strict_requested) return `${contract?.local_validator || 'Ajv'} 应用侧校验`;
      const enabled = contract.strict_enabled_count || 0;
      const total = contract.tools?.length || 0;
      return enabled === total && total > 0
        ? `供应商 Strict 已启用（${enabled}/${total}）`
        : `Strict ${enabled}/${total}；其余由应用侧完整校验`;
    },
    bindingFor(call) {
      return (this.result?.answer_bindings || []).find(binding =>
        binding.execution_id && binding.execution_id === call.execution_id
      );
    },
    sourceLabels(call) {
      const bindingSources = this.bindingFor(call)?.data_sources || [];
      const sources = call.actual_data_records?.length
        ? call.actual_data_records
        : (bindingSources.length ? bindingSources : (call.declared_sources || []));
      if (!sources.length) return ['注册工具未声明外部数据源'];
      return sources.map(source => {
        if (!source || typeof source !== 'object') return String(source);
        const name = source.dataset_id || source.name || source.reference || source.source_ref || source.table || '注册来源';
        const version = source.version || source.source_version;
        const record = source.record_id || source.source_record_key;
        return [name, version ? `版本 ${version}` : '', record ? `记录 ${record}` : ''].filter(Boolean).join(' · ');
      });
    },
    parameterSources(call) {
      const labels = {
        user_input: '用户自然语言输入',
        schema_default: 'Schema 声明默认值',
        tool_result: '前序工具真实返回',
        unverified: '来源未验证'
      };
      return Object.entries(call.parameter_provenance || {}).map(([field, detail]) => ({
        field,
        label: labels[detail?.source] || detail?.source || '来源未记录'
      }));
    },
    apiErrorMessage(data, fallback) {
      if (typeof data?.detail === 'string') return data.detail;
      if (data?.detail?.message) return data.detail.message;
      return data?.error || data?.message || fallback;
    },
    async fetchTools() {
      this.toolsLoading = true;
      try {
        const response = await fetch(this.experimentApiUrl('/api/v1/experiments/tool-registry'));
        const data = await response.json();
        if (!response.ok) throw new Error(this.apiErrorMessage(data, `工具注册表请求失败 (${response.status})`));
        this.tools = data.tools || [];
      } catch (error) {
        this.errorMessage = error.message || '无法读取工具注册表';
      } finally {
        this.toolsLoading = false;
      }
    },
    resetSession() {
      this.conversationHistory = [];
      this.result = null;
      this.errorMessage = '';
      this.form.userQuery = '';
      this.$nextTick(() => this.$refs.queryInput?.focus());
    },
    async runExperiment() {
      this.errorMessage = '';
      if (this.form.mode === 'forced' && !this.form.forcedTool) {
        this.errorMessage = '强制调用模式必须选择一个工具。';
        return;
      }
      const message = this.form.userQuery.trim();
      if (!message) return;
      this.running = true;
      try {
        const response = await fetch(this.experimentApiUrl('/api/v1/experiments/tool-orchestration'), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message,
            history: this.conversationHistory.slice(-10),
            mode: this.form.mode,
            scene: this.form.scene || null,
            catalog_mode: this.form.catalogMode,
            parameter_validation_mode: this.form.parameterValidationMode,
            strict_tool_schemas: this.form.strictToolSchemas,
            forced_tool: this.form.mode === 'forced' ? this.form.forcedTool : null,
            orchestration_id: this.awaitingClarification ? this.result.orchestration_id : null,
            max_candidates: Number(this.form.maxCandidates),
            max_tool_calls: this.form.mode === 'plan' ? Number(this.form.maxToolCalls) : 1
          })
        });
        const data = await response.json();
        if (!response.ok) throw new Error(this.apiErrorMessage(data, `编排实验请求失败 (${response.status})`));
        this.result = data;
        this.conversationHistory.push(
          { role: 'user', content: message },
          { role: 'assistant', content: data.product_view?.content || data.answer || '' }
        );
        this.form.userQuery = '';
        if (data.clarification?.required) {
          this.$nextTick(() => this.$refs.queryInput?.focus());
        }
      } catch (error) {
        this.errorMessage = error.message || '编排实验运行失败';
      } finally {
        this.running = false;
      }
    }
  },
  mounted() {
    this.fetchTools();
  }
};
</script>

<style scoped>
.experiment-page {
  --ink: #14201f;
  --paper: #f1efe8;
  --oxide: #b54a2b;
  --brass: #c7a15a;
  --green: #207252;
  --line: rgba(20, 32, 31, 0.17);
  min-height: 100vh;
  color: var(--ink);
  background:
    linear-gradient(rgba(20, 32, 31, 0.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(20, 32, 31, 0.035) 1px, transparent 1px),
    var(--paper);
  background-size: 30px 30px;
  font-family: "Noto Serif SC", "Songti SC", serif;
}

.experiment-shell { max-width: 1440px; margin: 0 auto; padding: 132px 5vw 80px; }
.hero-panel { display: flex; justify-content: space-between; gap: 48px; align-items: flex-end; padding-bottom: 34px; border-bottom: 1px solid var(--ink); }
.eyebrow, .card-label { margin: 0 0 12px; color: var(--oxide); font: 700 12px/1.2 Consolas, monospace; letter-spacing: .18em; }
.hero-panel h1 { margin: 0; font-size: clamp(38px, 5vw, 70px); font-weight: 700; letter-spacing: -.04em; }
.hero-copy { max-width: 820px; margin: 20px 0 0; color: #4d5a57; font-size: 17px; line-height: 1.8; }
.baseline-stamp { width: 168px; min-width: 168px; padding: 18px; border: 2px solid var(--oxide); color: var(--oxide); transform: rotate(-2deg); text-align: center; font-family: Consolas, monospace; }
.baseline-stamp span, .baseline-stamp small { display: block; font-size: 10px; letter-spacing: .16em; }
.baseline-stamp strong { display: block; margin: 5px 0; font-size: 32px; }

.scope-notice { display: grid; grid-template-columns: auto minmax(0, 1fr) auto; align-items: center; gap: 18px; margin-top: 20px; padding: 11px 14px; border-left: 4px solid var(--brass); background: rgba(255,255,255,.5); }
.scope-notice > span { color: #76571f; font-weight: 700; }
.scope-notice p { margin: 0; color: #606b68; font: 12px/1.6 "Noto Sans SC", sans-serif; }
.scope-notice code { color: var(--oxide); font: 11px Consolas, monospace; }

.bench-grid { display: grid; grid-template-columns: minmax(420px, .88fr) minmax(520px, 1.12fr); margin-top: 22px; border: 1px solid var(--ink); background: rgba(255,255,255,.45); box-shadow: 12px 12px 0 rgba(20,32,31,.1); }
.control-panel, .trace-panel { min-width: 0; padding: 30px; }
.control-panel { border-right: 1px solid var(--ink); }
.panel-heading { display: flex; align-items: center; gap: 14px; margin-bottom: 28px; }
.panel-heading h2 { margin: 0; font-size: 23px; }
.panel-heading p { margin: 3px 0 0; color: #66706e; font: 12px/1.4 Consolas, monospace; overflow-wrap: anywhere; }
.panel-index { display: grid; place-items: center; width: 38px; height: 38px; color: var(--paper); background: var(--ink); font: 700 14px Consolas, monospace; }
.mode-tag { margin-left: auto; padding: 7px 10px; color: var(--oxide); border: 1px solid currentColor; font-size: 12px; white-space: nowrap; }

.session-bar { display: flex; justify-content: space-between; gap: 16px; align-items: center; margin: -8px 0 18px; padding: 11px 12px; border: 1px solid rgba(32,114,82,.32); background: rgba(32,114,82,.07); }
.session-bar strong, .session-bar small { display: block; }
.session-bar small { margin-top: 3px; color: #65716e; font: 11px "Noto Sans SC", sans-serif; }
.session-bar button { padding: 7px 9px; border: 1px solid var(--green); color: var(--green); background: transparent; font-size: 11px; cursor: pointer; }

.field { display: grid; gap: 8px; width: 100%; font-size: 13px; font-weight: 700; }
.field-row { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-top: 18px; }
.field-wide { margin-top: 18px; }
.field input, .field textarea, .field select { box-sizing: border-box; width: 100%; border: 1px solid var(--line); border-radius: 0; padding: 13px 14px; color: var(--ink); background: rgba(255,255,255,.68); font: 14px/1.6 "Noto Sans SC", sans-serif; outline: none; transition: border-color .2s, box-shadow .2s; }
.field input:focus, .field textarea:focus, .field select:focus { border-color: var(--oxide); box-shadow: 3px 3px 0 rgba(181,74,43,.17); }
.field-note { color: #747c79; font-weight: 400; line-height: 1.55; }
.mode-selector { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin: 18px 0 4px; }
.mode-button { display: grid; gap: 5px; min-height: 106px; padding: 13px; text-align: left; color: var(--ink); border: 1px solid var(--line); background: transparent; cursor: pointer; transition: .2s ease; }
.mode-button > span { color: var(--oxide); font: 700 12px Consolas, monospace; }
.mode-button strong { font-size: 15px; }
.mode-button small { color: #737b79; line-height: 1.45; }
.mode-button:hover, .mode-button.active { border-color: var(--ink); background: var(--ink); color: var(--paper); transform: translateY(-3px); box-shadow: 0 6px 0 var(--brass); }
.mode-button.active small { color: #c9cfcc; }
.mode-button:disabled { cursor: not-allowed; }
.mode-button:disabled:not(.active) { opacity: .48; }
.fixed-limit { display: grid; gap: 8px; align-content: start; font-size: 13px; }
.fixed-limit > span { font-weight: 700; }
.fixed-limit strong { padding: 13px 14px; border: 1px dashed var(--line); color: #69726f; background: rgba(255,255,255,.3); font: 400 14px/1.6 "Noto Sans SC", sans-serif; }

.policy-note { margin-top: 18px; padding: 13px 15px; border-left: 4px solid var(--green); background: rgba(32,114,82,.07); }
.policy-note.research { border-color: var(--oxide); background: rgba(181,74,43,.07); }
.policy-note strong { font: 700 11px Consolas, monospace; letter-spacing: .1em; }
.policy-note p { margin: 5px 0 0; color: #5f6a67; font: 12px/1.6 "Noto Sans SC", sans-serif; }
.strict-field { display: flex; gap: 10px; align-items: flex-start; margin-top: 15px; color: #3f4b48; font: 700 12px/1.5 "Noto Sans SC", sans-serif; }
.strict-field input { margin-top: 3px; accent-color: var(--oxide); }
.strict-field span, .strict-field small { display: block; }
.strict-field small { margin-top: 3px; color: #747c79; font-weight: 400; }
.run-button { display: flex; justify-content: space-between; width: 100%; margin-top: 24px; padding: 16px 19px; border: 0; color: #fff; background: var(--oxide); font: 700 15px "Noto Sans SC", sans-serif; cursor: pointer; }
.run-button:hover:not(:disabled) { background: #92381f; }
.run-button:disabled { opacity: .55; cursor: wait; }
.run-arrow { font-size: 20px; }
.error-message { padding: 10px 12px; color: #8d2e1d; border-left: 3px solid var(--oxide); background: rgba(181,74,43,.08); font-size: 13px; }

.empty-state { display: grid; justify-items: center; align-content: center; min-height: 540px; color: #68716f; text-align: center; }
.empty-state strong { margin-top: 20px; color: var(--ink); font-size: 18px; }
.empty-state p { margin: 7px 0; }
.empty-orbit { position: relative; width: 84px; height: 84px; border: 1px solid var(--line); border-radius: 50%; }
.empty-orbit::before, .empty-orbit::after { content: ""; position: absolute; inset: 14px; border: 1px solid var(--brass); border-radius: 50%; }
.empty-orbit::after { inset: 31px; background: var(--oxide); border: 0; }
.empty-orbit span { position: absolute; width: 8px; height: 8px; top: 4px; left: 38px; border-radius: 50%; background: var(--ink); animation: orbit 4s linear infinite; transform-origin: 4px 38px; }
@keyframes orbit { to { transform: rotate(360deg); } }
.tool-use-status { display: grid; grid-template-columns: 14px minmax(0, 1fr) auto; gap: 13px; align-items: center; margin: -2px 0 22px; padding: 15px 16px; border: 1px solid currentColor; background: rgba(255,255,255,.58); }
.tool-use-status > div { min-width: 0; }
.tool-use-status small { display: block; margin-bottom: 3px; color: currentColor; font: 700 9px/1.2 Consolas, monospace; letter-spacing: .13em; opacity: .72; }
.tool-use-status strong { display: block; color: var(--ink); font-size: 17px; }
.tool-use-status p { margin: 3px 0 0; color: #63706c; font: 11px/1.5 "Noto Sans SC", sans-serif; }
.tool-use-status > code { padding: 6px 8px; border: 1px solid currentColor; font: 700 10px Consolas, monospace; letter-spacing: .08em; }
.tool-use-indicator { width: 10px; height: 10px; border-radius: 50%; background: currentColor; box-shadow: 0 0 0 4px color-mix(in srgb, currentColor 15%, transparent); }
.tool-use-status.is-called { color: var(--green); }
.tool-use-status.is-called .tool-use-indicator { animation: status-pulse 1.8s ease-out infinite; }
.tool-use-status.is-blocked { color: var(--oxide); }
.tool-use-status.is-direct { color: #6d7572; border-style: dashed; }
@keyframes status-pulse { 50% { box-shadow: 0 0 0 8px color-mix(in srgb, currentColor 0%, transparent); } }
.trace-list { list-style: none; margin: 0; padding: 5px 0 8px; }
.trace-list li { position: relative; display: grid; grid-template-columns: 22px 1fr; gap: 12px; min-height: 65px; }
.trace-list li::before { content: ""; position: absolute; top: 16px; bottom: -8px; left: 6px; width: 1px; background: var(--line); }
.trace-list li:last-child::before { display: none; }
.trace-dot { z-index: 1; width: 11px; height: 11px; margin-top: 4px; border: 2px solid var(--paper); border-radius: 50%; background: var(--brass); box-shadow: 0 0 0 1px var(--brass); }
.trace-list .done .trace-dot { background: var(--green); box-shadow: 0 0 0 1px var(--green); }
.trace-list .rejected .trace-dot { background: var(--oxide); box-shadow: 0 0 0 1px var(--oxide); }
.trace-list .idle { opacity: .52; }
.trace-list strong { font-size: 14px; }
.trace-list p { margin: 4px 0 0; color: #64706d; font: 12px/1.55 "Noto Sans SC", sans-serif; white-space: pre-wrap; }
.evidence-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1px; margin-top: 14px; background: var(--line); border: 1px solid var(--line); }
.evidence-grid article { padding: 17px; background: var(--paper); }
.evidence-grid span { display: block; color: #747c79; font-size: 11px; }
.evidence-grid strong { display: block; margin-top: 7px; font: 700 15px Consolas, monospace; }
.status-success { color: var(--green); }
.clarification-panel { margin-top: 18px; padding: 18px; color: #743923; border: 1px solid rgba(181,74,43,.38); border-left: 5px solid var(--oxide); background: rgba(181,74,43,.07); }
.clarification-panel > span { display: block; font: 700 10px Consolas, monospace; letter-spacing: .14em; }
.clarification-panel > strong { display: block; margin-top: 6px; font-size: 17px; }
.clarification-panel > p { white-space: pre-wrap; font: 12px/1.65 "Noto Sans SC", sans-serif; }
.clarification-panel ul { margin: 12px 0 0; padding: 0; list-style: none; }
.clarification-panel li { display: grid; grid-template-columns: minmax(100px, auto) 1fr; gap: 9px; margin-top: 7px; font-size: 11px; }
.clarification-panel code { font-family: Consolas, monospace; }

.result-grid { display: grid; grid-template-columns: 1.15fr .85fr; gap: 18px; margin-top: 30px; }
.result-card { min-width: 0; padding: 27px; border-top: 4px solid var(--ink); background: #fff; box-shadow: 0 8px 24px rgba(20,32,31,.08); }
.result-card h3 { margin: 0 0 18px; font-size: 21px; }
.answer-card { border-color: var(--oxide); }
.answer-card > p { min-height: 150px; margin: 0; color: #3f4a48; font: 15px/1.9 "Noto Sans SC", sans-serif; white-space: pre-wrap; }
.answer-card > aside { margin-top: 18px; padding: 11px 13px; color: #76571f; border-left: 3px solid var(--brass); background: rgba(199,161,90,.12); font: 12px/1.6 "Noto Sans SC", sans-serif; }
.answer-card footer { display: grid; grid-template-columns: auto 1fr; gap: 6px 14px; margin-top: 24px; padding-top: 15px; border-top: 1px solid var(--line); color: #707876; font-size: 11px; }
.answer-card code { color: var(--oxide); overflow-wrap: anywhere; }
.selection-reason, .muted-copy { color: #5d6865; font: 13px/1.7 "Noto Sans SC", sans-serif; }
.candidate-list { display: flex; flex-wrap: wrap; gap: 6px; margin: 15px 0; }
.candidate-list span { padding: 7px 8px; border: 1px solid var(--line); background: var(--paper); font: 10px Consolas, monospace; }
.candidate-list b { margin-right: 6px; color: var(--oxide); }
.selection-facts { display: grid; grid-template-columns: 78px 1fr; gap: 7px 10px; margin: 18px 0 0; padding-top: 15px; border-top: 1px solid var(--line); font: 11px/1.45 "Noto Sans SC", sans-serif; }
.selection-facts dt { color: #7b8380; }
.selection-facts dd { margin: 0; overflow-wrap: anywhere; }

.plan-board, .audit-board { margin-top: 26px; border: 1px solid var(--ink); background: rgba(255,255,255,.54); box-shadow: 8px 8px 0 rgba(20,32,31,.08); }
.section-heading { display: flex; justify-content: space-between; align-items: center; gap: 24px; padding: 20px 24px; border-bottom: 1px solid var(--ink); }
.section-heading > div { display: flex; align-items: center; gap: 13px; }
.section-heading span { display: grid; place-items: center; width: 34px; height: 34px; color: var(--paper); background: var(--ink); font: 700 12px Consolas, monospace; }
.section-heading h2 { margin: 0; font-size: 21px; }
.section-heading > p { max-width: 660px; margin: 0; color: #68716f; font: 12px/1.55 "Noto Sans SC", sans-serif; text-align: right; }
.plan-board > ol { display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 1px; margin: 0; padding: 0; background: var(--line); list-style: none; }
.plan-board li { display: grid; grid-template-columns: 35px 1fr; gap: 12px; padding: 20px; background: var(--paper); }
.plan-board li > b { color: var(--oxide); font: 700 13px Consolas, monospace; }
.plan-board li strong { font-size: 13px; }
.plan-board li p { margin: 7px 0; color: #5d6865; font: 12px/1.55 "Noto Sans SC", sans-serif; }
.plan-board li small { color: #7c8582; }

.no-call { padding: 30px; color: #626d6a; font: 13px/1.7 "Noto Sans SC", sans-serif; }
.call-record + .call-record { border-top: 1px solid var(--ink); }
.call-record > header { display: grid; grid-template-columns: 36px 1fr auto; gap: 13px; align-items: center; padding: 17px 22px; background: #fff; }
.call-record > header > span { color: #89908e; font: 700 12px Consolas, monospace; }
.call-record > header strong, .call-record > header small { display: block; }
.call-record > header small { margin-top: 3px; color: #747d7a; font: 11px "Noto Sans SC", sans-serif; }
.call-record > header code { padding: 5px 8px; border: 1px solid currentColor; font: 700 10px Consolas, monospace; }
.call-record > header code.success { color: var(--green); }
.call-record > header code.warning { color: var(--oxide); }
.call-record > header code.neutral { color: #66706e; }
.audit-grid { display: grid; grid-template-columns: .8fr 1fr 1.2fr 1fr; gap: 1px; border-top: 1px solid var(--line); background: var(--line); }
.audit-grid > section { min-width: 0; padding: 19px; background: var(--paper); }
.audit-grid > section > span { display: block; margin-bottom: 10px; color: var(--oxide); font: 700 10px Consolas, monospace; letter-spacing: .08em; }
.audit-grid strong { font-size: 12px; }
.audit-grid p { color: #5e6966; font: 11px/1.6 "Noto Sans SC", sans-serif; }
.audit-grid pre { max-height: 310px; margin: 0; padding: 13px; overflow: auto; color: #dfe8df; background: #17211f; font: 10px/1.65 Consolas, monospace; white-space: pre-wrap; overflow-wrap: anywhere; }
.audit-grid > section > small { display: block; margin-top: 9px; color: #7a8380; font: 10px/1.5 "Noto Sans SC", sans-serif; }
.parameter-sources { display: grid; gap: 5px; margin: 12px 0 0; padding: 10px 11px; list-style: none; border: 1px solid rgba(32,114,82,.24); background: rgba(32,114,82,.06); }
.parameter-sources li { display: flex; justify-content: space-between; gap: 8px; color: #54605d; font: 10px/1.45 "Noto Sans SC", sans-serif; }
.parameter-sources code { color: var(--green); font-family: Consolas, monospace; overflow-wrap: anywhere; }
.audit-grid dl { display: grid; grid-template-columns: 66px 1fr; gap: 7px 9px; margin: 16px 0 0; font: 10px/1.5 "Noto Sans SC", sans-serif; }
.audit-grid dt { color: #7f8785; }
.audit-grid dd { margin: 0; overflow-wrap: anywhere; }
.basis-list { margin-top: 0 !important; }
.basis-list ul { margin: 0; padding: 0; list-style: none; }
.basis-list li + li { margin-top: 5px; }
.call-error { color: #8d2e1d !important; }

@media (max-width: 1180px) {
  .audit-grid { grid-template-columns: 1fr 1fr; }
}
@media (max-width: 980px) {
  .hero-panel { align-items: flex-start; }
  .scope-notice { grid-template-columns: auto 1fr; }
  .scope-notice code { grid-column: 2; }
  .bench-grid { grid-template-columns: 1fr; }
  .control-panel { border-right: 0; border-bottom: 1px solid var(--ink); }
}
@media (max-width: 640px) {
  .experiment-shell { padding: 112px 16px 50px; }
  .hero-panel { display: block; }
  .baseline-stamp { margin-top: 26px; }
  .scope-notice, .scope-notice code { grid-template-columns: 1fr; grid-column: auto; }
  .control-panel, .trace-panel { padding: 20px; }
  .mode-selector, .field-row, .result-grid, .audit-grid { grid-template-columns: 1fr; }
  .mode-button { min-height: auto; }
  .section-heading { display: block; }
  .section-heading > p { margin-top: 12px; text-align: left; }
  .session-bar { align-items: flex-start; }
  .tool-use-status { grid-template-columns: 14px 1fr; }
  .tool-use-status > code { grid-column: 2; justify-self: start; }
}
</style>
