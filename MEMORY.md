# 冶金平台项目记忆

## 项目信息
- Vue 3 + Express + PostgreSQL 冶金平台
- 域名: sklam.fewai.com (原 sklam.dataset.org.cn)
- 数据库: 192.168.31.145:5432, 库名 metallurgy, schema User
- 后端端口: 3000
- 智能对话: 通义千问 API (qwen-plus)
- 服务器: Ubuntu, 宝塔面板, Node v18.20.8

## 部署架构
- 方案: PM2 + Nginx 纯静态
- 前端: Nginx 托管静态文件, SPA 路由用 try_files, root → /www/wwwroot/metallurgy-server
- 后端: PM2 运行 Express API, Nginx 反向代理 /api/ → localhost:3000
- PM2 进程名: metallurgy (script path: /www/wwwroot/metallurgy-server/server.js)
- 后端端口: 3000
- SSH: root@118.31.3.5, 已配置免密登录

## 已知问题与修复
- vue.config.js outputDir 原来为 'public', 已改为 'dist'
- public/index.html 被构建产物覆盖过, 已重建标准 Vue CLI 模板
- 添加了 chainWebpack 配置防止 copy-webpack-plugin 与 html-webpack-plugin 冲突
- 后端 npm 镜像源: https://npmmirror.com/mirrors/npm/
- Chat.vue 快速提问: 去掉 $nextTick, 直接调用 sendMessage()
- request.js: 本地开发直连 localhost:3000/api, 超时 60s → 已改为 120s
- server.js: 数据库连不上不再 process.exit(1), 改为无数据库模式运行; 通义千问超时 60s → 120s, max_tokens 2000 → 8192
- PM2 实际运行的 server.js 路径和预期可能不一致, 更新后需用 pm2 show 确认
- Chat.vue formatMessage: 用 marked + katex 渲染 markdown 和 LaTeX 公式; 先提取公式占位符再跑 marked 避免 HTML 被破坏
- server.js system prompt: 要求 AI 用 $$ 包裹 LaTeX 公式, 全程中文回答, 涉及计算必须调小模型

## 大小模型协同 (2026-05-20 实现)
- 后端 server.js 新增 smallModelRegistry，包含 5 个小模型：
  - thermodynamics (热力学推理)、converter (转炉)、blastfurnace (高炉低碳)、casting (连铸质量)、simulation (仿真工单)
- 解析函数 parseAndExecuteSmallModelCalls: 正则匹配 [调用:模型ID:参数JSON] 标记
- 格式化函数 formatSmallModelBlock: 将 handler 结果转为 Markdown 表格块
- System prompt 新增"大小模型协同能力"章节，说明模型 ID、参数、调用规则
- 前端 Chat.vue: 消息对象增加 smallModelCalled 标记，AI 头像旁显示 🔧 徽标，消息底部显示 "🔧 已调用专业小模型辅助计算" 指示条
- 架构卡片已移到快速提问下方，默认折叠
- 目前 handler 为模拟数据（随机数），后续可替换为真实 API

## 部署状态 (2026-05-19)
- PM2 进程 metallurgy 已正常运行, script path = /www/wwwroot/metallurgy-server/server.js
- 前端构建产物在 dist/, 部署到 /www/wwwroot/metallurgy-server/
- 聊天/快速提问功能已修复并部署上线
- CORS 已添加 sklam.fewai.com

## 热力学改造 (2026-05-20)
- thermodynamics handler 替换 Math.random() 为真实热化学数据库（10种反应）+ ΔG = ΔH - TΔS 公式
- 高炉碳利用率也从 Math.random() 改为基于焦比/煤比的确定性计算
- formatSmallModelBlock 从 markdown blockquote 改为输出 HTML 卡片结构（sml-card）
- CSS 坑: Vue scoped 样式不影响 v-html 内容，使用 :deep() 穿透（而不是去掉 scoped）

## 小模型 LLM 专家模式 (2026-05-20)
- 小模型从"本地计算引擎"改为"LLM 领域专家 + 身份约束"
- 每个模型有专属 system prompt，限定回答领域
- 新增 callSmallModelChat() 复用 LLM 调用逻辑
- 主聊天系统提示词中的调用格式统一为 {"query":"..."}

## 部署方式 (2026-05-20)
- 本地构建前端 → 复制到 backend/public → 通过 ssh2 npm 包上传 server.js + 前端文件到服务器
- 不需要 sshpass，直接用 Node.js ssh2 库处理密码连接
- 部署前必须询问用户确认
