# 小模型工具箱页面设计方案

## 目标

在聊天调用之外，提供一个独立页面让用户直接使用 5 个专业小模型（热力学推理、转炉工艺优化、高炉低碳分析、连铸质量决策、仿真工单协同），无需经过大模型对话。

## 改动文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `src/views/Tools.vue` | 新增 | 工具箱主页，含 5 个模型卡片+表单 |
| `src/router/index.js` | 修改 | 添加 `/tools` 路由 |
| `src/components/Header.vue` | 修改 | 导航栏添加"小模型工具箱"入口 |
| `backend/server.js` | 修改 | 新增 5 个 API 端点复用已有 handler |

## 后端改动

在 `backend/server.js` 中新增路由，为每个小模型暴露一个 API 端点：

```
POST /api/tools/thermodynamics  →  handler('thermodynamics')
POST /api/tools/converter       →  handler('converter')
POST /api/tools/blastfurnace    →  handler('blastfurnace')
POST /api/tools/casting         →  handler('casting')
POST /api/tools/simulation      →  handler('simulation')
```

每个端点直接调用 `smallModelRegistry` 中对应 handler，参数透传，返回 `{ summary, data, unit }` 结构。无需经过大模型。

## 前端改动

### 路由 (router/index.js)
```
/tools  →  Tools.vue  (name: 'SmallModelTools')
```

### 导航 (Header.vue)
在"工具软件"下拉菜单末尾添加：
```html
<p><router-link to="/tools">🧰 小模型工具箱</router-link></p>
```

### 工具箱页面 (Tools.vue)

布局：

```
┌─────────────────────────────────────────┐
│  🧰 专业小模型工具箱                      │
│  选择以下小模型进行独立计算...             │
│                                          │
│  ┌──────┐  ┌──────┐  ┌──────┐           │
│  │ 🔬   │  │ 🔥   │  │ 🏭   │           │
│  │热力学 │  │转炉  │  │高炉  │           │
│  │推理   │  │工艺  │  │低碳  │           │
│  └──────┘  └──────┘  └──────┘           │
│  ┌──────┐  ┌──────┐                     │
│  │ 📊   │  │ 💻   │                     │
│  │连铸  │  │仿真  │                     │
│  │质量  │  │工单  │                     │
│  └──────┘  └──────┘                     │
│                                          │
│  ─── 展开的计算区域 ───                   │
│  [反应选择下拉] [温度输入] [计算按钮]     │
│                                          │
│  ┌── 结果卡片 ──────────────────────┐    │
│  │  🔬 热力学推理    小模型计算结果 │    │
│  │  ΔG = -122.97 kJ/mol            │    │
│  │  ┌──────────┬──────────────┐    │    │
│  │  │ 反应式   │ FeO + C...   │    │    │
│  │  │ ΔG       │ -122.97      │    │    │
│  │  └──────────┴──────────────┘    │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

交互逻辑：
- 初始显示 5 个模型卡片网格
- 点击卡片 → 展开对应表单，其他卡片保持可见
- 表单参数来自各 handler 所需的 params
- 点击"计算" → 调对应 API → 结果用 sml-card 样式展示
- 可切换模型或多次计算

每个模型的表单参数：

| 模型 | 表单字段 |
|------|---------|
| 🔬 热力学推理 | reaction(下拉选择10种), temperature(数字输入) |
| 🔥 转炉工艺优化 | siContent, targetCarbon, steelTemp, oxygenFlow |
| 🏭 高炉低碳分析 | cokeRate, coalRate, production, oreGrade |
| 📊 连铸质量决策 | steelGrade, sectionSize, castingSpeed, superheat |
| 💻 仿真工单协同 | scenario, equipment, duration |

## 结果展示

复用聊天页已有的 `sml-card` CSS 样式（已在 `:deep()` 中定义），确保结果卡片在工具箱页面的外观与聊天中一致。

## 不涉及

- 不改动现有 5 个 handler 的逻辑
- 不改动聊天页面
- 不新增数据库表
