<template>
  <div class="chat-container">
    <Header />

    <div class="chat-content">
      <!-- 顶部标题栏 -->
      <div class="chat-header-bar">
        <div class="header-bar-inner">
          <div class="header-brand">
            <span class="brand-icon">AI</span>
            <div class="brand-text">
              <h1>冶金智能助手</h1>
              <p>专业的冶金领域 AI 助手，为您解答相关问题</p>
            </div>
          </div>
          <span class="status-badge">在线</span>
        </div>
      </div>

      <div class="chat-main-layout">
        <!-- 左侧：聊天窗口 -->
        <div class="chat-primary">
          <div class="chat-window">
            <!-- 消息区域 -->
            <div class="messages" ref="messagesRef">
              <!-- 欢迎消息 -->
              <div class="message assistant welcome-message">
                <div class="avatar avatar-ai">AI</div>
                <div class="content">
                  <div class="text">
                    <h3>欢迎使用冶金智能助手</h3>
                    <p>我可以帮助您解答以下领域的问题：</p>
                    <ul class="expertise-list">
                      <li><span class="expertise-dot" style="--dot-color: #0046DB"></span>冶金工艺与材料科学</li>
                      <li><span class="expertise-dot" style="--dot-color: #40C057"></span>碳中和与绿色冶金</li>
                      <li><span class="expertise-dot" style="--dot-color: #FF6B6B"></span>氢冶金技术</li>
                      <li><span class="expertise-dot" style="--dot-color: #FFC107"></span>碳排放计算</li>
                      <li><span class="expertise-dot" style="--dot-color: #4ECDC4"></span>工业生产优化</li>
                      <li><span class="expertise-dot" style="--dot-color: #667EEA"></span>电化学与电池材料</li>
                    </ul>
                    <p class="welcome-footer">请随时提问，我会尽力为您提供专业的解答</p>
                  </div>
                  <div class="time">{{ formatTime(new Date()) }}</div>
                </div>
              </div>

              <!-- 对话消息 -->
              <div
                  v-for="(message, index) in messages"
                  :key="index"
                  :class="['message', message.role]"
              >
                <div class="avatar" :class="message.role === 'user' ? 'avatar-user' : 'avatar-ai'">
                  <span v-if="message.role === 'user'">U</span>
                  <span v-if="message.role === 'assistant'">
                    AI
                    <span v-if="message.smallModelCalled" class="sml-badge">SML</span>
                  </span>
                </div>
                <div class="content">
                  <div class="text" v-html="formatMessage(message.content)"></div>
                  <div v-if="message.files && message.files.length" class="message-files">
                    <div v-for="(f, fi) in message.files" :key="fi" class="message-file-item">
                      <img v-if="f.type === 'image'" :src="f.url" :alt="f.name" class="message-file-img">
                      <div v-else class="message-file-icon" :style="{ background: f._color || '#6E6E73' }">
                        <span class="message-file-ext">{{ f._ext || '?' }}</span>
                      </div>
                      <span class="message-file-label">{{ f.name }}</span>
                    </div>
                  </div>
                  <div v-if="message.smallModelCalled" class="sml-indicator">已调用专业小模型辅助</div>
                  <div class="time">{{ formatTime(message.timestamp) }}</div>
                </div>
              </div>

              <!-- 加载状态 -->
              <div v-if="isLoading" class="message assistant loading-message">
                <div class="avatar avatar-ai">AI</div>
                <div class="content">
                  <div class="text typing">
                    <span class="dot"></span>
                    <span class="dot"></span>
                    <span class="dot"></span>
                  </div>
                </div>
              </div>

              <!-- 错误消息 -->
              <div v-if="error" class="error-message">
                <div class="error-content">
                  <span class="error-icon">!</span>
                  <span>{{ error }}</span>
                </div>
              </div>
            </div>

            <!-- 输入区域 -->
            <div class="input-area">
              <div class="input-wrapper">
                <div class="input-row">
                  <button
                      @click="triggerFilePicker"
                      class="attach-btn"
                      title="添加附件"
                      :disabled="isLoading"
                  >
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"></path>
                    </svg>
                  </button>
                  <input
                      type="file"
                      ref="fileInput"
                      @change="handleFileSelect"
                      multiple
                      hidden
                  >
                  <textarea
                      v-model="inputMessage"
                      @keydown.enter.exact.prevent="sendMessage"
                      @keydown.ctrl.enter.exact="handleCtrlEnter"
                      placeholder="请输入您的问题，例如：什么是绿色冶金？如何计算碳排放？"
                      rows="1"
                      :disabled="isLoading"
                      ref="inputRef"
                      class="message-input"
                      @input="autoResizeInput"
                  ></textarea>
                  <button
                      @click="sendMessage"
                      :disabled="isLoading || !inputMessage.trim()"
                      class="send-btn"
                  >
                    <svg v-if="!isLoading" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                      <line x1="22" y1="2" x2="11" y2="13"></line>
                      <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                    </svg>
                    <span v-else class="thinking-text">思考中...</span>
                  </button>
                </div>
                <!-- 附件预览 -->
                <div v-if="attachedFiles.length > 0" class="file-previews">
                  <div
                      v-for="(file, index) in attachedFiles"
                      :key="index"
                      class="file-preview-item"
                  >
                    <div class="file-preview-thumb">
                      <img v-if="isImageFile(file)" :src="file.url" :alt="file.name" class="file-preview-img">
                      <div v-else class="file-preview-icon" :style="{ background: fileTypeInfo(file).color }">
                        <span class="file-preview-icon-text">{{ fileTypeInfo(file).ext }}</span>
                      </div>
                    </div>
                    <button
                        @click="removeFile(index)"
                        class="file-preview-remove"
                        title="移除"
                    >
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                      </svg>
                    </button>
                    <span class="file-preview-name">{{ file.name }}</span>
                  </div>
                </div>
                <div class="input-footer">
                  <span class="input-hint">Enter 发送 · Ctrl+Enter 换行</span>
                  <button
                      @click="clearConversation"
                      class="clear-btn"
                      title="清空对话"
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <polyline points="3 6 5 6 21 6"></polyline>
                      <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                    </svg>
                    清空
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 右侧边栏：快捷提问 + 架构 -->
        <div class="chat-sidebar">
          <!-- 快捷问题 -->
          <div class="quick-questions">
            <span class="quick-label">快速提问</span>
            <div class="quick-buttons">
              <button @click="quickQuestion('什么是绿色冶金？')">
                <span class="quick-icon" style="--icon-bg: #e8f5e9; --icon-color: #40C057">G</span>
                什么是绿色冶金？
              </button>
              <button @click="quickQuestion('如何计算冶金过程的碳排放量？')">
                <span class="quick-icon" style="--icon-bg: #fff8e1; --icon-color: #FFC107">C</span>
                如何计算碳排放？
              </button>
              <button @click="quickQuestion('氢冶金技术的原理是什么？')">
                <span class="quick-icon" style="--icon-bg: #fce4ec; --icon-color: #FF6B6B">H</span>
                氢冶金技术
              </button>
              <button @click="quickQuestion('冶金中的AI应用有哪些？')">
                <span class="quick-icon" style="--icon-bg: #e8f0fe; --icon-color: #0046DB">AI</span>
                AI在冶金中的应用
              </button>
            </div>
          </div>

          <!-- 大小模型协同架构卡片 -->
          <div class="architecture-section">
            <div
                class="architecture-toggle"
                @click="toggleArchitecture"
            >
              <svg :class="['toggle-chevron', { open: showArchitecture }]" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="9 18 15 12 9 6"></polyline>
              </svg>
              <span class="toggle-title">大小模型协同架构</span>
              <span class="toggle-hint">{{ showArchitecture ? '收起' : '创新点' }}</span>
            </div>
            <transition name="arch-fade">
              <div v-if="showArchitecture" class="architecture-content">
                <!-- 流程图 -->
                <div class="flow-diagram">
                  <div class="flow-step">
                    <div class="flow-node user-node">
                      <span class="node-icon">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                          <circle cx="12" cy="7" r="4"></circle>
                        </svg>
                      </span>
                      <span class="node-label">用户提问</span>
                    </div>
                  </div>
                  <div class="flow-arrow">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <line x1="5" y1="12" x2="19" y2="12"></line>
                      <polyline points="12 5 19 12 12 19"></polyline>
                    </svg>
                  </div>
                  <div class="flow-step">
                    <div class="flow-node llm-node">
                      <span class="node-icon">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                          <path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 0 1 7 7h1a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-1.27A7.04 7.04 0 0 1 17 22h-4"></path>
                        </svg>
                      </span>
                      <span class="node-label">大模型</span>
                      <span class="node-desc">意图识别</span>
                    </div>
                  </div>
                  <div class="flow-arrow">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <line x1="5" y1="12" x2="19" y2="12"></line>
                      <polyline points="12 5 19 12 12 19"></polyline>
                    </svg>
                  </div>
                  <div class="flow-step">
                    <div class="flow-node sml-node">
                      <span class="node-icon">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                          <circle cx="12" cy="12" r="10"></circle>
                          <path d="M12 6v6l4 2"></path>
                        </svg>
                      </span>
                      <span class="node-label">小模型</span>
                      <span class="node-desc">数值计算</span>
                    </div>
                  </div>
                  <div class="flow-arrow">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <line x1="5" y1="12" x2="19" y2="12"></line>
                      <polyline points="12 5 19 12 12 19"></polyline>
                    </svg>
                  </div>
                  <div class="flow-step">
                    <div class="flow-node result-node">
                      <span class="node-icon">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                          <polyline points="14 2 14 8 20 8"></polyline>
                          <line x1="16" y1="13" x2="8" y2="13"></line>
                          <line x1="16" y1="17" x2="8" y2="17"></line>
                        </svg>
                      </span>
                      <span class="node-label">结果汇总</span>
                    </div>
                  </div>
                  <div class="flow-arrow">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <line x1="5" y1="12" x2="19" y2="12"></line>
                      <polyline points="12 5 19 12 12 19"></polyline>
                    </svg>
                  </div>
                  <div class="flow-step">
                    <div class="flow-node user-node">
                      <span class="node-icon">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                          <circle cx="12" cy="7" r="4"></circle>
                        </svg>
                      </span>
                      <span class="node-label">返回用户</span>
                    </div>
                  </div>
                </div>

                <!-- 小模型能力列表 -->
                <div class="capabilities-section">
                  <h4>专业小模型能力</h4>
                  <div class="capability-tags">
                    <span class="capability-tag" :class="{ 'tag-active': activeTool === 'thermodynamics' }" @click="selectTool('thermodynamics')">热力学推理</span>
                    <span class="capability-tag" :class="{ 'tag-active': activeTool === 'converter' }" @click="selectTool('converter')">转炉炼钢优化</span>
                    <span class="capability-tag" :class="{ 'tag-active': activeTool === 'blastfurnace' }" @click="selectTool('blastfurnace')">高炉低碳运行</span>
                    <span class="capability-tag" :class="{ 'tag-active': activeTool === 'casting' }" @click="selectTool('casting')">连铸质量分析</span>
                    <span class="capability-tag" :class="{ 'tag-active': activeTool === 'simulation' }" @click="selectTool('simulation')">仿真与工单</span>
                  </div>
                </div>

                <!-- 小模型对话 -->
                <div v-if="activeTool" class="tool-form-section">
                  <div class="tool-form-header">
                    <span class="tool-form-icon">{{ toolIcon }}</span>
                    <span class="tool-form-title">{{ toolName }}</span>
                  </div>
                  <div v-if="toolMessages.length === 0" class="tool-dialog-hint">
                    <div class="tool-dialog-examples">
                      <div class="tool-example-list">
                        <p><strong>试试这样提问：</strong></p>
                        <p class="example-item" @click="sendToolMsg($event, true)"
                           v-for="(ex, i) in toolExamples" :key="i">{{ ex }}</p>
                      </div>
                    </div>
                  </div>
                  <div class="tool-msg-list" v-if="toolMessages.length > 0">
                    <div v-for="(msg, i) in toolMessages" :key="i" class="tool-msg-item">
                      <div class="tool-msg-role" :class="msg.role">{{ msg.role === 'user' ? '你' : toolName }}</div>
                      <div class="tool-msg-bubble" :class="msg.role">{{ msg.content }}</div>
                      <div v-if="msg.result" class="tool-result-section" v-html="makeToolCard(msg.result)"></div>
                    </div>
                  </div>
                  <div class="tool-dialog-input">
                    <textarea
                      v-model="toolQuery"
                      placeholder="输入问题..."
                      rows="2"
                      class="tool-textarea"
                      @keydown.enter.ctrl="sendToolMsg"
                    ></textarea>
                    <button class="tool-btn-run" @click="sendToolMsg" :disabled="toolLoading || !toolQuery.trim()">
                      {{ toolLoading ? '思考中...' : '发送' }}
                    </button>
                  </div>
                </div>
              </div>
            </transition>
          </div>
        </div>
      </div>
    </div>

    <Footer />
  </div>
</template>

<script>
import Header from '@/components/Header.vue';
import Footer from '@/components/Footer.vue';
import request from '@/utils/request';
import { marked } from 'marked';
import katex from 'katex';
import 'katex/dist/katex.min.css';

// 配置 marked
marked.setOptions({
  breaks: true,
  gfm: true
});

export default {
  name: 'MyChat',
  components: {
    Header,
    Footer
  },
  data() {
    return {
      messages: [],
      inputMessage: '',
      isLoading: false,
      error: null,
      attachedFiles: [],
      showArchitecture: false,
      // 小模型独立工具
      activeTool: null,
      toolLoading: false,
      toolResult: null,
      toolQuery: '',
      toolMessages: []
    };
  },
  computed: {
    toolIcon() {
      const icons = { thermodynamics: 'TD', converter: 'CO', blastfurnace: 'BF', casting: 'CC', simulation: 'SIM' };
      return icons[this.activeTool] || 'TL';
    },
    toolName() {
      const names = { thermodynamics: '热力学推理', converter: '转炉炼钢工艺优化', blastfurnace: '高炉低碳运行分析', casting: '连铸质量辅助决策', simulation: '对话式仿真与工单协同' };
      return names[this.activeTool] || '';
    },
    toolExamples() {
      const examples = {
        thermodynamics: ['FeO + C → Fe + CO 在 1600°C 能否反应', 'CaCO₃ 在 900°C 能分解吗', '铝热反应需要多高温度'],
        converter: ['铁水 Si 0.5% 目标碳 0.05% 温度 1600°C 终点预测', 'Si 0.8% 目标碳 0.08% 需要多少氧'],
        blastfurnace: ['焦比 360 煤比 160 日产量 5000t 碳排放多少', '焦比 380 煤比 150 产量 4500 评估碳排放'],
        casting: ['Q235B 200x200mm 拉速 1.2 过热度 30 质量预测', 'HRB400 150x150mm 拉速 1.8 过热度 25'],
        simulation: ['转炉炼钢 45分钟 生成操作工单', 'LF精炼 30分钟 精炼炉 仿真工单']
      };
      return examples[this.activeTool] || [];
    }
  },
  mounted() {
    console.log('🚀 聊天页面加载，使用统一的request.js');
    this.scrollToBottom();
    this.$nextTick(() => {
      if (this.$refs.inputRef) {
        this.$refs.inputRef.focus();
      }
    });
  },
  updated() {
    this.scrollToBottom();
  },
  methods: {
    autoResizeInput(e) {
      const el = e.target;
      el.style.height = 'auto';
      el.style.height = el.scrollHeight + 'px';
    },
    async sendMessage() {
      if (!this.inputMessage.trim() || this.isLoading) return;

      const userMessage = this.inputMessage.trim();
      this.inputMessage = '';
      this.error = null;

      // 收集附件
      const files = [...this.attachedFiles];
      this.attachedFiles = [];

      // 添加用户消息
      this.messages.push({
        role: 'user',
        content: userMessage,
        files: files.map(f => {
          const isImg = f.file && f.file.type && f.file.type.startsWith('image/');
          const ext = f.name.includes('.') ? f.name.split('.').pop().toUpperCase() : '?';
          const colors = { PDF: '#e74c3c', DOC: '#2b5797', DOCX: '#2b5797', XLS: '#217346', XLSX: '#217346', PPT: '#d24726', PPTX: '#d24726', ZIP: '#f5a623', RAR: '#f5a623', '7Z': '#f5a623' };
          return {
            name: f.name, url: f.url, size: f.size,
            type: isImg ? 'image' : 'file',
            _ext: ext,
            _color: colors[ext] || '#6E6E73'
          };
        }),
        timestamp: new Date()
      });

      // 释放临时 URL
      files.forEach(f => URL.revokeObjectURL(f.url));

      this.isLoading = true;

      try {
        // 构建历史消息
        const history = this.messages
            .filter(msg => msg.role !== 'system')
            .slice(-10)
            .map(msg => ({
              role: msg.role,
              content: msg.content
            }));

        console.log('📤 发送请求到 /chat/completion');
        console.log('消息内容:', userMessage);
        console.log('历史消息数:', history.length);

        // 使用统一的request发送请求
        const response = await request.post('/chat/completion', {
          message: userMessage,
          history: history
        });

        console.log('📥 API响应:', response);

        // 处理响应数据
        if (response.code === 200) {
          // 根据你的后端结构：response.data.content
          const content = response.data?.content || '收到响应';
          const smallModelCalled = response.data?.smallModelCalled || false;

          this.messages.push({
            role: 'assistant',
            content: content,
            smallModelCalled: smallModelCalled,
            timestamp: new Date()
          });

          console.log('✅ 助手回复已添加');
        } else {
          // 处理非200响应
          throw new Error(response.message || `API错误: ${response.code}`);
        }
      } catch (error) {
        console.error('❌ 发送消息失败:', error);

        // 显示错误信息
        this.error = error.message || '请求失败';

        // 在界面上显示错误消息
        this.messages.push({
          role: 'assistant',
          content: `抱歉，处理请求时出现问题：${this.error}`,
          timestamp: new Date()
        });
      } finally {
        this.isLoading = false;
        this.$nextTick(() => {
          if (this.$refs.inputRef) {
            this.$refs.inputRef.focus();
          }
        });
      }
    },

    _escapeHtml(str) {
      return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    },

    toggleArchitecture() {
      this.showArchitecture = !this.showArchitecture;
    },

    selectTool(toolId) {
      if (this.activeTool === toolId) {
        this.activeTool = null;
        this.toolResult = null;
        this.toolMessages = [];
      } else {
        this.activeTool = toolId;
        this.toolResult = null;
        this.toolQuery = '';
        this.toolMessages = [];
      }
    },

    makeToolCard(r) {
      if (!r) return '';
      let html = `<div class="sml-card sml-model-${r.modelId}">`;
      html += `<div class="sml-card-header"><span class="sml-card-icon">${r.icon}</span><span class="sml-card-title">${r.modelName}</span><span class="sml-card-badge">计算结果</span></div>`;
      html += `<div class="sml-card-body">`;
      html += `<div class="sml-card-summary">${this._escapeHtml(r.result.summary)}</div>`;
      if (r.result.data && Object.keys(r.result.data).length > 0) {
        html += `<table class="sml-card-table">`;
        for (const [key, value] of Object.entries(r.result.data)) {
          html += `<tr><td class="sml-label">${this._escapeHtml(key)}</td><td class="sml-value">${this._escapeHtml(String(value))}</td></tr>`;
        }
        html += `</table>`;
      }
      if (r.result.unit) {
        html += `<div class="sml-card-unit">单位：${this._escapeHtml(r.result.unit)}</div>`;
      }
      html += `</div></div>`;
      return html;
    },

    async sendToolMsg(event, isExample = false) {
      const text = isExample ? event.target.textContent.trim().replace(/^•\s*/, '') : this.toolQuery;
      if (!text.trim()) return;
      this.toolQuery = '';
      this.toolMessages.push({ role: 'user', content: text });
      this.toolLoading = true;
      try {
        const history = this.toolMessages.slice(0, -1).map(m => ({ role: m.role === '你' ? 'user' : 'assistant', content: m.content }));
        const res = await request.post(`/tools/${this.activeTool}/chat`, { message: text, history });
        if (res.code === 200) {
          this.toolMessages.push({
            role: 'assistant',
            content: res.data.reply,
            result: res.data.result
          });
        } else {
          this.toolMessages.push({ role: 'assistant', content: '抱歉，处理时出现问题。' });
        }
      } catch (err) {
        this.toolMessages.push({ role: 'assistant', content: '请求失败：' + (err.message || '网络错误') });
      } finally {
        this.toolLoading = false;
        this.$nextTick(() => {
          const el = this.$el.querySelector('.tool-msg-list');
          if (el) el.scrollTop = el.scrollHeight;
        });
      }
    },

    quickQuestion(question) {
      this.inputMessage = question;
      this.sendMessage();
    },

    formatTime(date) {
      if (!(date instanceof Date)) {
        date = new Date(date);
      }
      return date.toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit'
      });
    },

    formatMessage(content) {
      if (!content) return '';

      // 1. 提取 $$...$$ 和 $...$ 内容，用占位符替换（先不渲染 KaTeX）
      const katexItems = [];
      content = content.replace(/\$\$([\s\S]*?)\$\$/g, (_, f) => {
        const id = `§§K${katexItems.length}§§`;
        katexItems.push({ formula: f.trim(), mode: 'block' });
        return id;
      });
      content = content.replace(/\$(.+?)\$/g, (_, f) => {
        if (!f.trim()) return _;
        const id = `§§K${katexItems.length}§§`;
        katexItems.push({ formula: f.trim(), mode: 'inline' });
        return id;
      });

      // 2. 按行检测裸 LaTeX，替换为占位符
      const lines = content.split('\n');
      for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        if (line && /\\[a-z]+\{/.test(line) && !/^#{1,6}\s|^\*\*|^>|^- /m.test(line)) {
          const id = `§§K${katexItems.length}§§`;
          katexItems.push({ formula: line, mode: 'block' });
          lines[i] = id;
        }
      }
      content = lines.join('\n');

      // 3. 保护 _x, _{} 防止被 marked 当斜体
      const subItems = [];
      content = content.replace(/(?<!\\)(_\{[^}]*\}|\^\{[^}]*\}|_([a-zA-Z0-9])(?!\w)|\^([a-zA-Z0-9])(?!\w))/g, (m) => {
        if (subItems.length > 200) return m.replace(/_/g, '\\_').replace(/\^/g, '\\^');
        const id = `§§S${subItems.length}§§`;
        subItems.push(m);
        return id;
      });

      // 4. 渲染 Markdown（此时内容不含任何 KaTeX HTML）
      let html = marked.parse(content);

      // 5. 还原下标占位符（用 KaTeX 渲染）
      subItems.forEach((m, i) => {
        try {
          const rendered = katex.renderToString('x'+m, { displayMode: false, throwOnError: false }).replace(/^x/, '');
          html = html.replace(`§§S${i}§§`, rendered);
        } catch {
          html = html.replace(`§§S${i}§§`, m);
        }
      });

      // 6. 还原公式占位符（用 KaTeX 渲染）
      katexItems.forEach((item, i) => {
        try {
          const rendered = katex.renderToString(item.formula, { displayMode: item.mode === 'block', throwOnError: false });
          html = html.replace(`§§K${i}§§`, rendered);
        } catch {
          html = html.replace(`§§K${i}§§`, item.formula);
        }
      });

      return html;
    },

    scrollToBottom() {
      this.$nextTick(() => {
        const container = this.$refs.messagesRef;
        if (container) {
          container.scrollTop = container.scrollHeight;
        }
      });
    },

    clearConversation() {
      if (confirm('确定要清空当前对话吗？')) {
        this.messages = [];
        this.error = null;
      }
    },

    handleCtrlEnter() {
      // Ctrl+Enter 换行
      this.inputMessage += '\n';
    },

    triggerFilePicker() {
      this.$refs.fileInput.click();
    },

    handleFileSelect(e) {
      const files = Array.from(e.target.files);
      files.forEach(file => {
        if (file.size > 10 * 1024 * 1024) return;
        this.attachedFiles.push({
          file,
          url: URL.createObjectURL(file),
          name: file.name,
          size: file.size
        });
      });
      e.target.value = '';
    },

    removeFile(index) {
      URL.revokeObjectURL(this.attachedFiles[index].url);
      this.attachedFiles.splice(index, 1);
    },

    isImageFile(file) {
      return file.file && file.file.type && file.file.type.startsWith('image/');
    },

    fileTypeInfo(file) {
      const ext = file.name.includes('.') ? file.name.split('.').pop().toUpperCase() : '?';
      const colors = { PDF: '#e74c3c', DOC: '#2b5797', DOCX: '#2b5797', XLS: '#217346', XLSX: '#217346', PPT: '#d24726', PPTX: '#d24726', ZIP: '#f5a623', RAR: '#f5a623', '7Z': '#f5a623' };
      return { ext, color: colors[ext] || '#6E6E73' };
    }
  }
};
</script>

<style scoped>
/* ============================================
   聊天页面 - 完整重设计
   品牌色: #0046DB
   ============================================ */
.chat-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: #f5f5f7;
}

.chat-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  margin-top: 90px;
}

/* ---- 顶部标题栏 ---- */
.chat-header-bar {
  padding: 0 24px;
  margin-bottom: 20px;
}

.header-bar-inner {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 28px;
  background: linear-gradient(135deg, #082A78 0%, #0046DB 100%);
  border-radius: 16px;
}

.header-brand {
  display: flex;
  align-items: center;
  gap: 16px;
}

.brand-icon {
  width: 42px;
  height: 42px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
  font-size: 14px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  letter-spacing: 0.5px;
  backdrop-filter: blur(4px);
}

.brand-text h1 {
  font-size: 22px;
  font-weight: 700;
  color: #fff;
  margin: 0;
  line-height: 1.3;
}

.brand-text p {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.75);
  margin: 2px 0 0;
  line-height: 1.4;
}

.status-badge {
  font-size: 12px;
  color: #fff;
  background: rgba(255, 255, 255, 0.15);
  padding: 5px 14px;
  border-radius: 20px;
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-badge::before {
  content: '';
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #40C057;
  display: inline-block;
}

/* ---- 聊天主区域：双栏布局 ---- */
.chat-main-layout {
  flex: 1;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px 30px;
  width: 100%;
  display: flex;
  gap: 20px;
  align-items: stretch;
  min-height: 0;
}

.chat-primary {
  flex: 1;
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chat-sidebar {
  width: 340px;
  min-width: 340px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  position: sticky;
  top: 110px;
}

.chat-window {
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 4px 24px rgba(0, 70, 219, 0.08);
  overflow: hidden;
  flex: 1;
  min-height: 800px;
  display: flex;
  flex-direction: column;
}

/* ---- 消息区域 ---- */
.messages {
  flex: 1;
  overflow-y: scroll;
  padding: 28px 28px 20px;
  background: #FAFBFC;
  display: flex;
  flex-direction: column;
  gap: 22px;
  scrollbar-width: auto;
  scrollbar-color: #c0c4cc transparent;
}

.messages::-webkit-scrollbar {
  width: 8px;
}

.messages::-webkit-scrollbar-track {
  background: #f0f1f3;
  border-radius: 4px;
}

.messages::-webkit-scrollbar-thumb {
  background: #c0c4cc;
  border-radius: 4px;
  border: 2px solid #f0f1f3;
}

.messages::-webkit-scrollbar-thumb:hover {
  background: #a0a5b0;
}

.message {
  display: flex;
  gap: 12px;
  animation: msgIn 0.3s ease;
  max-width: 88%;
}

.message.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message.user .content {
  align-items: flex-end;
}

/* ---- 头像 ---- */
.avatar {
  width: 40px;
  height: 40px;
  min-width: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.3px;
  flex-shrink: 0;
  position: relative;
}

.avatar-ai {
  background: linear-gradient(135deg, #0046DB, #0033A0);
  color: #fff;
}

.avatar-user {
  background: #40C057;
  color: #fff;
}

.sml-badge {
  position: absolute;
  bottom: -3px;
  right: -3px;
  font-size: 8px;
  font-weight: 700;
  background: #FF6B35;
  color: #fff;
  border-radius: 4px;
  padding: 1px 4px;
  line-height: 1.3;
  box-shadow: 0 2px 6px rgba(255, 107, 53, 0.4);
  animation: badgePop 0.3s ease;
}

@keyframes badgePop {
  0% { transform: scale(0); }
  50% { transform: scale(1.3); }
  100% { transform: scale(1); }
}

/* ---- 消息内容 ---- */
.content {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.text {
  padding: 16px 20px;
  border-radius: 14px;
  line-height: 1.7;
  font-size: 14px;
  word-wrap: break-word;
}

.message.assistant .text {
  background: #fff;
  color: #333;
  border: 1px solid #e8ecf4;
  border-bottom-left-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.message.user .text {
  background: #0046DB;
  color: #fff;
  border-bottom-right-radius: 4px;
}

/* ---- 欢迎消息 ---- */
.message.assistant.welcome-message .text {
  background: #fff;
  color: #333;
  border: 1.5px solid #0046DB;
  border-bottom-left-radius: 4px;
}

.welcome-message .text h3 {
  color: #0046DB;
  margin: 0 0 12px;
  font-size: 18px;
  font-weight: 700;
}

.welcome-message .text p {
  margin: 8px 0;
  color: #555;
  font-size: 14px;
}

.welcome-footer {
  margin-top: 12px !important;
  padding-top: 12px;
  border-top: 1px solid #e8ecf4;
  color: #6E6E73 !important;
  font-size: 13px !important;
}

.expertise-list {
  list-style: none;
  margin: 12px 0;
  padding: 0;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px 20px;
}

.expertise-list li {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #444;
  font-size: 14px;
  padding: 4px 0;
}

.expertise-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--dot-color, #0046DB);
  flex-shrink: 0;
}

/* ---- Markdown 渲染 ---- */
.message.assistant .text h1,
.message.assistant .text h2,
.message.assistant .text h3,
.message.assistant .text h4 {
  color: #0046DB;
  margin: 16px 0 8px;
  font-weight: 700;
}
.message.assistant .text h1 { font-size: 20px; }
.message.assistant .text h2 { font-size: 18px; }
.message.assistant .text h3 { font-size: 16px; }
.message.assistant .text p {
  margin: 8px 0;
  line-height: 1.7;
}
.message.assistant .text ul,
.message.assistant .text ol {
  margin: 8px 0;
  padding-left: 24px;
}
.message.assistant .text li {
  margin: 4px 0;
  line-height: 1.6;
}
.message.assistant .text code {
  background: #eef1f8;
  color: #d63384;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
  font-family: 'Consolas', 'Monaco', monospace;
}
.message.assistant .text pre {
  background: #1d1d1f;
  color: #f8f8f8;
  padding: 16px 20px;
  border-radius: 10px;
  overflow-x: auto;
  margin: 12px 0;
}
.message.assistant .text pre code {
  background: none;
  color: #f8f8f8;
  padding: 0;
  font-size: 13px;
  line-height: 1.5;
}
.message.assistant .text blockquote {
  border-left: 4px solid #0046DB;
  margin: 12px 0;
  padding: 8px 16px;
  background: #f5f8ff;
  color: #555;
  border-radius: 0 8px 8px 0;
}
.message.assistant .text table {
  border-collapse: collapse;
  width: 100%;
  margin: 12px 0;
  font-size: 13px;
}
.message.assistant .text th,
.message.assistant .text td {
  border: 1px solid #d0d5e0;
  padding: 8px 12px;
  text-align: left;
}
.message.assistant .text th {
  background: #eef1f8;
  font-weight: 600;
}
.message.assistant .text tr:nth-child(even) {
  background: #f8faff;
}
.message.assistant .text a {
  color: #0046DB;
  text-decoration: underline;
}
.message.assistant .text hr {
  border: none;
  border-top: 2px solid #e0e7ff;
  margin: 16px 0;
}
.message.assistant .text strong {
  font-weight: 700;
}
.message.assistant .text .katex-display {
  margin: 16px 0;
  overflow-x: auto;
  overflow-y: hidden;
  padding: 8px 0;
}
.message.assistant .text .katex {
  font-size: 1.1em;
}

/* ---- SML 卡片（makeToolCard 生成） ---- */
.message.assistant .text :deep(.sml-card) {
  margin: 12px 0;
  border: 1px solid #e0e4ed;
  border-radius: 12px;
  overflow: hidden;
  background: #ffffff;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  animation: smlCardIn 0.35s ease-out;
}

@keyframes smlCardIn {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}

.message.assistant .text :deep(.sml-card-header) {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  font-size: 13px;
}

.message.assistant .text :deep(.sml-card-error .sml-card-header) {
  background: linear-gradient(135deg, #f56565 0%, #c53030 100%);
}

.message.assistant .text :deep(.sml-model-thermodynamics .sml-card-header) {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.message.assistant .text :deep(.sml-model-converter .sml-card-header) {
  background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
}

.message.assistant .text :deep(.sml-model-blastfurnace .sml-card-header) {
  background: linear-gradient(135deg, #a1c4fd 0%, #c2e9fb 100%);
}

.message.assistant .text :deep(.sml-model-casting .sml-card-header) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.message.assistant .text :deep(.sml-card-icon) {
  font-size: 16px;
  line-height: 1;
}

.message.assistant .text :deep(.sml-card-title) {
  font-weight: 600;
  flex: 1;
}

.message.assistant .text :deep(.sml-card-badge) {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  background: rgba(255,255,255,0.25);
  color: #fff;
  white-space: nowrap;
}

.message.assistant .text :deep(.sml-badge-error) {
  background: rgba(0,0,0,0.2);
}

.message.assistant .text :deep(.sml-card-body) {
  padding: 14px 16px;
}

.message.assistant .text :deep(.sml-card-summary) {
  font-size: 14px;
  line-height: 1.6;
  color: #333;
  margin-bottom: 10px;
}

.message.assistant .text :deep(.sml-card-table) {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  margin: 0;
}

.message.assistant .text :deep(.sml-card-table tr) {
  border-bottom: 1px solid #f0f0f0;
}

.message.assistant .text :deep(.sml-card-table tr:last-child) {
  border-bottom: none;
}

.message.assistant .text :deep(.sml-card-table td) {
  padding: 6px 8px;
  vertical-align: top;
}

.message.assistant .text :deep(.sml-label) {
  width: 110px;
  color: #666;
  font-weight: 500;
  white-space: nowrap;
}

.message.assistant .text :deep(.sml-value) {
  color: #1d1d1f;
  word-break: break-word;
}

.message.assistant .text :deep(.sml-card-table tr:nth-child(even)) {
  background: #fafbff;
}

.message.assistant .text :deep(.sml-card-unit) {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed #e0e0e0;
  font-size: 12px;
  color: #999;
  text-align: right;
}

/* ---- SML 指示器 ---- */
.sml-indicator {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin-top: 8px;
  padding: 4px 10px;
  background: #fef7f3;
  border: 1px solid #feebd5;
  border-radius: 8px;
  font-size: 11px;
  color: #e65c00;
  width: fit-content;
}

/* ---- 时间戳 ---- */
.time {
  font-size: 11px;
  color: #9a9a9e;
  margin-top: 6px;
}

.message.user .time {
  text-align: right;
}

/* ---- 输入区域 ---- */
.input-area {
  padding: 20px 24px 24px;
  border-top: 1px solid #e8e8ed;
  background: #fff;
  flex-shrink: 0;
}

.input-wrapper {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.input-row {
  display: flex;
  gap: 10px;
  align-items: flex-end;
}

.message-input {
  flex: 1;
  padding: 12px 16px;
  border: 1.5px solid #e0e4ed;
  border-radius: 10px;
  font-size: 14px;
  line-height: 1.5;
  resize: none;
  transition: all 0.25s ease;
  font-family: inherit;
  color: #333;
  background: #FAFBFC;
  max-height: 120px;
}

.message-input:focus {
  outline: none;
  border-color: #0046DB;
  box-shadow: 0 0 0 3px rgba(0, 70, 219, 0.1);
  background: #fff;
}

.message-input:disabled {
  background: #f0f1f3;
  cursor: not-allowed;
}

.message-input::placeholder {
  color: #b0b0b8;
}

/* ---- 附件按钮 ---- */
.attach-btn {
  width: 44px;
  height: 44px;
  min-width: 44px;
  border-radius: 10px;
  background: transparent;
  color: #9a9a9e;
  border: 1.5px solid #e0e4ed;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.attach-btn:hover:not(:disabled) {
  color: #0046DB;
  border-color: #0046DB;
  background: #f5f8ff;
}

.attach-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* ---- 附件预览 ---- */
.file-previews {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  padding: 0 4px;
}

.file-preview-item {
  position: relative;
  width: 80px;
  border-radius: 8px;
  overflow: hidden;
  border: 1.5px solid #e0e4ed;
  background: #f5f7fa;
  animation: msgIn 0.2s ease;
}

.file-preview-img {
  width: 100%;
  height: 60px;
  object-fit: cover;
  display: block;
  background: #f0f1f3;
}

.file-preview-name {
  display: block;
  padding: 3px 6px;
  font-size: 9px;
  color: #6E6E73;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-preview-remove {
  position: absolute;
  top: 3px;
  right: 3px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.55);
  color: #fff;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s ease;
  padding: 0;
}

.file-preview-item:hover .file-preview-remove {
  opacity: 1;
}

.file-preview-thumb {
  width: 100%;
  height: 60px;
  overflow: hidden;
}

.file-preview-icon {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.file-preview-icon-text {
  font-size: 14px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.9);
  letter-spacing: 0.5px;
}

/* ---- 消息内嵌文件/图片 ---- */
.message-files {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}

.message-file-item {
  width: 120px;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #e0e4ed;
  background: #f5f7fa;
}

.message-file-img {
  width: 100%;
  height: 80px;
  object-fit: cover;
  display: block;
}

.message-file-icon {
  width: 100%;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.message-file-ext {
  font-size: 16px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.9);
  letter-spacing: 0.5px;
}

.message-file-label {
  display: block;
  padding: 4px 8px;
  font-size: 10px;
  color: #6E6E73;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.message.user .message-files {
  justify-content: flex-end;
}

.send-btn {
  width: 44px;
  height: 44px;
  min-width: 44px;
  border-radius: 10px;
  background: #0046DB;
  color: #fff;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.25s ease;
  flex-shrink: 0;
}

.send-btn:hover:not(:disabled) {
  background: #003db9;
  transform: translateY(-1px);
  box-shadow: 0 4px 14px rgba(0, 70, 219, 0.25);
}

.send-btn:active:not(:disabled) {
  transform: translateY(0);
}

.send-btn:disabled {
  background: #d0d5e0;
  cursor: not-allowed;
}

.thinking-text {
  font-size: 12px;
  font-weight: 500;
}

.input-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 4px;
}

.input-hint {
  font-size: 11px;
  color: #b0b0b8;
}

.clear-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 5px 12px;
  border-radius: 6px;
  font-size: 12px;
  color: #9a9a9e;
  background: transparent;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
}

.clear-btn:hover {
  color: #d32f2f;
  background: #fef2f2;
}

/* ---- 快捷问题 ---- */
.quick-questions {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 18px 16px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 70, 219, 0.06);
}

.quick-label {
  font-size: 13px;
  font-weight: 600;
  color: #333;
}

.quick-buttons {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.quick-buttons button {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  background: #F5F7FA;
  border: 1px solid #e8ecf4;
  border-radius: 8px;
  font-size: 13px;
  color: #444;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.quick-buttons button:hover {
  background: #eef3ff;
  border-color: #0046DB;
  color: #0046DB;
  transform: translateY(-1px);
}

.quick-icon {
  width: 24px;
  height: 24px;
  border-radius: 6px;
  background: var(--icon-bg, #eef1f8);
  color: var(--icon-color, #0046DB);
  font-size: 10px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

/* ---- 错误消息 ---- */
.error-message {
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 10px;
  padding: 12px 16px;
}

.error-content {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #dc2626;
  font-size: 14px;
}

.error-icon {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #dc2626;
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

/* ---- 加载动画 ---- */
.typing {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 12px 16px;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #0046DB;
  opacity: 0.4;
  animation: typing 1.4s infinite ease-in-out;
}

.dot:nth-child(1) {
  animation-delay: -0.32s;
}

.dot:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes typing {
  0%, 80%, 100% {
    transform: scale(0.8);
    opacity: 0.3;
  }
  40% {
    transform: scale(1.2);
    opacity: 1;
  }
}

@keyframes msgIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* ---- 架构折叠区 ---- */
.architecture-section {
  width: 100%;
}

.architecture-toggle {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 16px 24px;
  background: #fff;
  border: 1px solid #e8ecf4;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.25s ease;
  user-select: none;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
}

.architecture-toggle:hover {
  border-color: #0046DB;
  box-shadow: 0 4px 16px rgba(0, 70, 219, 0.08);
}

.toggle-chevron {
  color: #0046DB;
  transition: transform 0.25s ease;
  flex-shrink: 0;
}

.toggle-chevron.open {
  transform: rotate(90deg);
}

.toggle-title {
  font-size: 15px;
  font-weight: 600;
  color: #1d1d1f;
  flex: 1;
}

.toggle-hint {
  font-size: 12px;
  color: #6E6E73;
  background: #f5f7fa;
  padding: 4px 14px;
  border-radius: 20px;
  white-space: nowrap;
}

.architecture-content {
  background: #fff;
  border: 1px solid #e8ecf4;
  border-top: none;
  border-radius: 0 0 12px 12px;
  padding: 24px 20px;
  margin-top: -1px;
}

/* ---- 流程图 ---- */
.flow-diagram {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  margin-bottom: 24px;
  flex-wrap: nowrap;
  overflow-x: auto;
  padding: 8px 0;
}

.flow-step {
  flex-shrink: 0;
}

.flow-node {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 12px 16px;
  border-radius: 10px;
  min-width: 80px;
  text-align: center;
  transition: all 0.3s ease;
}

.flow-node:hover {
  transform: translateY(-2px);
}

.user-node {
  background: #f5f7fa;
  border: 1.5px solid #e0e4ed;
  color: #333;
}

.llm-node {
  background: linear-gradient(135deg, #082A78 0%, #0046DB 100%);
  color: #fff;
  box-shadow: 0 4px 12px rgba(0, 70, 219, 0.2);
}

.sml-node {
  background: #1d1d1f;
  color: #fff;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.result-node {
  background: #0046DB;
  color: #fff;
  box-shadow: 0 4px 12px rgba(0, 70, 219, 0.2);
}

.node-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0.9;
}

.node-label {
  font-size: 12px;
  font-weight: 600;
}

.node-desc {
  font-size: 10px;
  opacity: 0.8;
  line-height: 1.4;
}

.flow-arrow {
  color: #0046DB;
  opacity: 0.6;
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

/* ---- 小模型能力标签 ---- */
.capabilities-section {
  border-top: 1px solid #e8ecf4;
  padding-top: 20px;
}

.capabilities-section h4 {
  font-size: 14px;
  font-weight: 600;
  color: #333;
  margin-bottom: 12px;
  text-align: center;
}

.capability-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
}

.capability-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: #f5f7fa;
  border: 1.5px solid #e8ecf4;
  border-radius: 8px;
  font-size: 13px;
  color: #444;
  transition: all 0.2s ease;
  cursor: pointer;
  user-select: none;
}

.capability-tag:hover {
  background: #eef3ff;
  border-color: #0046DB;
  color: #0046DB;
  transform: translateY(-1px);
  box-shadow: 0 3px 10px rgba(0, 70, 219, 0.1);
}

.tag-active {
  background: #0046DB !important;
  color: #fff !important;
  border-color: #0046DB !important;
}

.cap-hint {
  font-size: 11px;
  color: #9a9a9e;
  font-weight: 400;
}

/* ---- 小模型对话 ---- */
.tool-form-section {
  margin-top: 16px;
  padding: 16px;
  background: #f8faff;
  border: 1px solid #e0e7ff;
  border-radius: 10px;
  animation: msgIn 0.25s ease;
}

.tool-form-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.tool-form-icon {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  background: #0046DB;
  color: #fff;
  font-size: 9px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.tool-form-title {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.tool-dialog-hint {
  margin-bottom: 10px;
}

.tool-dialog-examples {
  margin-bottom: 4px;
}

.tool-example-list p {
  margin: 2px 0;
  font-size: 13px;
  color: #555;
}

.example-item {
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: background 0.15s;
  color: #0046DB !important;
}

.example-item:hover {
  background: #eef3ff;
}

.tool-msg-list {
  max-height: 300px;
  overflow-y: auto;
  margin-bottom: 10px;
  padding: 8px;
  background: #fff;
  border-radius: 8px;
  border: 1px solid #e8ecf4;
}

.tool-msg-item {
  margin-bottom: 10px;
}

.tool-msg-item:last-child {
  margin-bottom: 0;
}

.tool-msg-role {
  font-size: 11px;
  font-weight: 600;
  margin-bottom: 2px;
  padding: 0 4px;
}

.tool-msg-role.user {
  color: #40C057;
}

.tool-msg-role.assistant {
  color: #0046DB;
}

.tool-msg-bubble {
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 13px;
  line-height: 1.5;
  color: #333;
}

.tool-msg-bubble.user {
  background: #e8f5e9;
}

.tool-msg-bubble.assistant {
  background: #eef3ff;
}

.tool-msg-item .tool-result-section {
  margin-top: 6px;
}

.tool-dialog-input {
  display: flex;
  gap: 8px;
  align-items: flex-start;
}

.tool-textarea {
  flex: 1;
  padding: 10px 12px;
  border: 1.5px solid #d0d5e0;
  border-radius: 8px;
  font-size: 13px;
  outline: none;
  resize: vertical;
  font-family: inherit;
  line-height: 1.5;
  transition: border-color 0.2s;
  background: #fff;
  color: #333;
}

.tool-textarea:focus {
  border-color: #0046DB;
  box-shadow: 0 0 0 2px rgba(0, 70, 219, 0.1);
}

.tool-btn-run {
  padding: 10px 20px;
  background: #0046DB;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.tool-btn-run:hover {
  background: #003db9;
}

.tool-btn-run:disabled {
  background: #99b8e8;
  cursor: not-allowed;
}

/* ---- 展开/折叠动画 ---- */
.arch-fade-enter-active,
.arch-fade-leave-active {
  transition: all 0.3s ease;
  overflow: hidden;
}

.arch-fade-enter-from,
.arch-fade-leave-to {
  opacity: 0;
  max-height: 0;
  padding-top: 0;
  padding-bottom: 0;
  margin-top: 0;
  margin-bottom: 0;
}

.arch-fade-enter-to,
.arch-fade-leave-from {
  opacity: 1;
}

/* ---- 响应式 ---- */
@media (max-width: 768px) {
  .chat-content {
    margin-top: 70px;
  }

  .chat-main-layout {
    flex-direction: column;
    padding: 0 16px 24px;
    gap: 16px;
  }

  .chat-sidebar {
    width: 100%;
    min-width: 0;
    position: static;
  }

  .chat-header-bar {
    padding: 0 16px;
    margin-bottom: 16px;
  }

  .header-bar-inner {
    padding: 16px 20px;
    border-radius: 14px;
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .brand-text h1 {
    font-size: 18px;
  }

  .brand-text p {
    font-size: 12px;
  }

  .chat-window {
    min-height: 380px;
    border-radius: 14px;
  }

  .messages {
    padding: 20px 16px;
    gap: 18px;
  }

  .message {
    max-width: 95%;
  }

  .avatar {
    width: 34px;
    height: 34px;
    min-width: 34px;
    font-size: 10px;
  }

  .text {
    padding: 14px 16px;
    font-size: 14px;
    border-radius: 12px;
  }

  .message.assistant .text {
    border-bottom-left-radius: 4px;
  }

  .message.user .text {
    border-bottom-right-radius: 4px;
  }

  .expertise-list {
    grid-template-columns: 1fr;
  }

  .input-area {
    padding: 16px 16px 18px;
  }

  .quick-questions {
    flex-direction: column;
    gap: 10px;
    padding: 14px 16px;
  }

  .quick-buttons {
    flex-direction: row;
    flex-wrap: wrap;
  }

  .architecture-toggle {
    padding: 14px 18px;
  }

  .flow-diagram {
    gap: 3px;
    justify-content: flex-start;
  }

  .flow-node {
    padding: 10px 12px;
    min-width: 68px;
  }

  .node-desc {
    display: none;
  }

  .capability-tag {
    font-size: 12px;
    padding: 7px 12px;
  }
}

@media (max-width: 480px) {
  .header-bar-inner {
    padding: 14px 16px;
  }

  .brand-icon {
    width: 36px;
    height: 36px;
    font-size: 12px;
  }

  .brand-text h1 {
    font-size: 16px;
  }

  .chat-window {
    min-height: 360px;
  }

  .quick-buttons button {
    font-size: 12px;
    padding: 7px 12px;
  }

  .toggle-title {
    font-size: 14px;
  }

  .toggle-hint {
    font-size: 11px;
    padding: 3px 10px;
  }

  .architecture-content {
    padding: 16px 12px;
  }
}
</style>
