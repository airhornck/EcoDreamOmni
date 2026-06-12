# EcoDream Omni v4.0 — Copilot 与工作区交互模式规范 v2.0

> **状态**: 评审通过（待实施）  
> **日期**: 2026-06-04  
> **评审结论**: 全面推广 Copilot-Driven 模式，工作区仅保留编辑/预览能力，所有操作按钮迁移至 Copilot Action Cards  
> **影响范围**: 全局 10 页面 + AI Copilot 面板 + 后端 API 全面改造  
> **上一版本**: v1.0（已废弃 Mode A）

---

## 一、设计哲学：画布 vs 指挥中心

```
┌─────────────────────────────────────────────────────────────────────┐
│                    v4.0 交互范式重新定义                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   工作区 Workspace Canvas          AI Copilot Panel                 │
│   ─────────────────────            ─────────────────                │
│                                                                     │
│   🎨 内容展示                       🎮 操作入口                     │
│   ✏️ 内容编辑                       🤖 AI 建议                      │
│   👁️ 实时预览                       ✅ 决策按钮                     │
│   📊 数据可视化                     🔄 状态流转                     │
│   📋 信息浏览                       📋 历史记录                     │
│                                                                     │
│   ❌ 不放置操作按钮                  ✅ 所有操作通过 Action Card      │
│   ❌ 不放置提交/确认/保存            ✅ 所有决策通过对话式交互       │
│   ❌ 不放置新建/添加/删除            ✅ 所有生成通过 AI 驱动        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.1 核心原则（不可违背）

| 原则 | 工作区 | Copilot |
|------|--------|---------|
| **内容展示** | ✅ 承担 | ❌ 不承担（仅摘要） |
| **内容编辑** | ✅ 承担（输入框、编辑器、画布） | ❌ 不承担（除 Prompt 输入） |
| **实时预览** | ✅ 承担（平台预览、数据图表） | ❌ 不承担 |
| **操作按钮** | ❌ **禁止放置** | ✅ **唯一入口** |
| **AI 建议** | ❌ 禁止 Inline 浮层（干扰编辑） | ✅ 承担 |
| **状态流转** | ❌ 禁止在工作区展示流程按钮 | ✅ 承担 |
| **批量操作** | ❌ 禁止勾选后顶部按钮 | ✅ 承担 |

### 1.2 为什么舍弃 Mode A（Direct）

在 v1.0 中，我们保留了 Mode A（工作区按钮为主）用于「低认知负担、高频」操作。评审结论：**全部舍弃**。理由：

1. **认知一致性**: 用户无需判断「这个按钮在工作区还是 Copilot」，所有操作统一在 Copilot
2. **AI 原生体验**: 任何操作都可以附带 AI 建议、风险提示、预测数据
3. **上下文完整性**: Copilot 掌握用户当前在看什么、选中了什么，给出的操作建议更精准
4. **可扩展性**: 新增功能无需考虑「放工作区还是 Copilot」，统一走 Copilot
5. **历史债务清理**: v2.7.x 遗留的大量工作区按钮一次性迁移，避免长期双轨制

**例外**（经评审确认，以下场景可在工作区保留纯展示性交互）：
- 表格行的展开/折叠（信息浏览，非操作）
- 编辑器内的格式化工具栏（编辑辅助，非业务操作）
- 画布内的拖拽调整（空间编辑，非业务操作）

---

## 二、两种交互模式定义

### 2.1 Mode B: Copilot-Driven（纯副驾驶驱动）

**定义**: 工作区无任何操作按钮，所有业务操作均通过 Copilot Action Card 完成。

**适用页面**: 审核发布、数据报表、账号矩阵、Agent 舰队

**典型流程**:
```
1. 用户进入页面
2. Copilot 主动推送 Action Card（基于上下文分析）
3. 用户在工作区浏览/编辑内容
4. 用户在 Copilot 中点击 Action Card 执行操作
5. 操作结果实时同步到工作区（预览更新、状态变化）
6. Copilot 推送下一步建议（状态流转）
```

### 2.2 Mode C: Hybrid（混合模式）— 编辑增强型

**定义**: 工作区承担内容编辑（输入框、画布、表格单元格编辑），但所有「提交类操作」均通过 Copilot Action Card 完成。

**适用页面**: 内容生产、工作台、实验室、素材库

**与 Mode B 的区别**:
- 工作区有编辑控件（输入框、选择器、开关）
- 但**没有**「保存」「提交」「确认」「生成」等按钮
- 用户编辑完成后，Copilot 感知变更，主动提供「保存并提交」Action Card

---

## 三、10 页面改造方案（逐个详细设计）

### 3.1 审核发布 /review（本次已完成 ✅）

**当前状态**: HTML 预览已完成，Copilot-Driven 范式已落地

**工作区职责**:
- 列表页：内容浏览、复选框勾选（纯选择态，无批量按钮）
- 详情页：内容编辑（标题、正文、标签、元数据）、平台预览、审核历史浏览

**Copilot 职责**:
- 列表页：批量通过 Action Card、合规趋势分析 Card、风险项 Card
- 详情页：审核决策 Action Card（通过/打回/驳回）、生成封面 Action Card、AI 优化建议 Card

**已完成的改造**:
- ✅ 详情页右侧移除审核决策按钮
- ✅ 封面弹框移除 AI 生成 Tab
- ✅ Copilot 详情模式新增审核决策 Card + 生成封面 Card
- ✅ 快捷动作区动态切换

**后续 React 实现注意**:
- 审核决策 API 调用必须从 Copilot Action Card 发起
- 封面生成走 `POST /api/ai/generate-cover`，结果通过 WebSocket 推送到 Copilot

---

### 3.2 工作台 /（P2-1 已完成，需回炉改造 🔴）

**当前状态**: React 实现已完成，但采用传统 Direct 模式，需全面改造

**现有问题**:
- PageHeader 有 `[+ 新建任务]` 按钮 ❌
- ContentCard 上有 `[一键发布]` `[修改]` 按钮 ❌
- BentoCard 上有操作入口 ❌

**改造方案**:

**工作区改造**:
```
PageHeader:
  之前: 工作台  [+ 新建任务]
  之后: 工作台  （无按钮，仅标题+副标题）

ContentCard:
  之前: [一键发布] [修改] [查看详情]
  之后: （无按钮，Hover 仅显示信息层，点击选中态）
        选中后 Copilot 感知，提供对应 Action Cards

MetricCard / BentoCard:
  之前: Hover 显示「AI 分析」快捷入口
  之后: Hover 仅高亮，点击后 Copilot 推送「分析此指标」Card
```

**Copilot 改造**:
```
列表页默认态:
  ├── Action Card: 「➕ 新建任务」（输入主题直接创建）
  ├── Action Card: "你有 5 个待审任务，优先处理哪个？"
  └── 快捷动作: 📊 查看趋势 / 🔔 查看告警

选中 ContentCard 后:
  ├── Action Card: 「📤 一键发布」（如果可发布）
  ├── Action Card: 「✏️ 编辑内容」（跳转编辑器）
  ├── Action Card: 「🔍 查看详情」（跳转详情页）
  └── Action Card: "该内容合规分 96 分，建议立即发布"

批量选中后:
  └── Action Card: "已选中 3 个任务，批量生成内容？批量发布？"
```

**影响文件**:
- `pages/DashboardPage/DashboardPage.tsx` — 移除所有按钮
- `pages/DashboardPage/ContentStream.tsx` — 卡片移除操作按钮
- `components/common/BentoCard.tsx` — 移除 Hover 操作入口
- `stores/aiCopilotStore.ts` — 新增工作台专属 Action Cards

---

### 3.3 内容生产 /generate（P2-2 已完成，需回炉改造 🔴）

**当前状态**: React 实现已完成，编辑器/预览/创建流程均采用 Direct 模式

**现有问题**:
- 编辑器有 `[保存]` `[发布]` 按钮 ❌
- 创建向导每步有 `[下一步]` `[确认创建]` 按钮 ❌
- 看板列上有 `[+ 新建内容]` 按钮 ❌

**改造方案**:

**工作区改造**:
```
看板页 /generate:
  之前: [看板 ▼] [筛选 ▼]  [+ 新建内容]
  之后: [看板 ▼] [筛选 ▼]  （无新建按钮）
        看板卡片无操作按钮，点击选中态

创建向导 /generate/create:
  之前: 4 步向导，每步有 [下一步] [确认创建]
  之后: 4 步内容展示（配置预览），无提交按钮
        用户在 Copilot 中确认配置并点击「创建任务」

编辑器 /generate/editor/:id:
  之前: [保存] [发布] [重新生成]
  之后: （无按钮，仅编辑区 + 预览区）
        编辑器内保留格式化工具栏（编辑辅助，非业务操作）
```

**Copilot 改造**:
```
看板页:
  ├── Action Card: 「➕ 新建内容」（快速创建，输入主题+平台）
  ├── Action Card: 「🤖 Agent 推荐任务」（AI 分析后推荐选题）
  └── 快捷动作: 📋 查看全部 / ⚡ 紧急任务

编辑器页:
  ├── Action Card: 「💾 保存草稿」（感知用户编辑后主动提供）
  ├── Action Card: 「🚀 提交审核」（保存后提供）
  ├── Action Card: "标题可优化，点击率预计提升 15%"
  ├── Action Card: 「🔄 重新生成」（含风格/长度选择）
  └── 六层 Prompt 可视化（在 Copilot 中展示拼接过程）

创建向导页:
  ├── Action Card: 「✅ 确认创建」（汇总 4 步配置，一键确认）
  ├── Action Card: "推荐 Agent：小红书图文生成（成功率 94%）"
  └── 快捷动作: ← 上一步 / → 下一步（导航级，非提交级）
```

**影响文件**:
- `pages/TaskHubPage.tsx` — 移除新建按钮，卡片移除操作
- `pages/TaskHubCreatePage.tsx` — 4 步向导移除提交按钮
- `pages/ContentForgePage.tsx` — 编辑器移除保存/发布/重新生成按钮
- `components/inline-ai/InlineAIFloat.tsx` — 保留（编辑辅助，非业务操作）

---

### 3.4 数据报表 /analytics（待开发，按新规范 🟢）

**工作区职责**:
- 指标卡片展示（纯数字，无操作）
- 图表展示（折线图、饼图，无操作）
- 排行榜表格（纯浏览，无导出按钮）

**Copilot 职责**:
```
默认态:
  ├── Action Card: 「📊 生成 AI 战报」（自然语言总结）
  ├── Action Card: 「🔍 异常诊断」（数据下降时自动推送）
  └── 快捷动作: 7天 / 30天 / 自定义日期

选中异常指标后:
  ├── Action Card: "互动量下降 15%，分析原因？"
  ├── Action Card: 「📈 预测未来 7 天趋势」
  └── Action Card: 「📋 导出报表」（之前在工作区的导出按钮移至此）
```

---

### 3.5 账号矩阵 /accounts（待开发，按新规范 🟢）

**工作区职责**:
- 账号卡片网格展示（头像、名称、健康度、发布进度）
- 账号详情页（人设展示、数据浏览）
- **无** `[+ 添加账号]` `[查看详情]` `[修复]` 按钮

**Copilot 职责**:
```
默认态:
  ├── Action Card: 「➕ 添加账号」（输入平台+账号信息）
  ├── Action Card: 「📅 生成发布计划」（AI 排期）
  └── 快捷动作: 全部平台 / 健康度筛选

选中低健康度账号:
  ├── Action Card: "该账号 3 天未发布，健康度 65，建议补发？"
  ├── Action Card: 「🛠️ 修复健康度」（具体修复步骤 Card）
  └── Action Card: 「👤 调整人设」（基于历史数据建议）

账号详情页:
  ├── Action Card: 「✏️ 编辑人设」（跳转人设编辑器）
  └── Action Card: 「📊 查看数据趋势」
```

---

### 3.6 Agent 舰队 /agents（待开发，按新规范 🟢）

**工作区职责**:
- Agent 列表展示（状态、成功率、耗时）
- 编排流程图展示（只读浏览）
- **无** `[日志]` `[配置]` `[暂停]` `[重启]` 按钮

**Copilot 职责**:
```
默认态:
  ├── Action Card: 「🚀 部署 Agent」（选择 Agent 类型+配置）
  ├── Action Card: 「📊 查看性能报告」
  └── 快捷动作: 运行中 / 已暂停 / 全部

选中异常 Agent:
  ├── Action Card: "TrendScout 失败率上升至 8%，诊断原因？"
  ├── Action Card: 「🔄 重启 Agent」
  ├── Action Card: 「⚙️ 修改配置」
  └── Action Card: "建议增加实例数，当前队列堆积 12 个任务"

编排流程图页:
  └── Action Card: 「➕ 添加节点」 / 「🔗 连接节点」 / 「▶️ 执行编排」
```

---

### 3.7 模型中心 /models（待开发，按新规范 🟢）

**工作区职责**:
- 模型表格展示（模型名、提供商、状态、成本）
- 成本趋势图表展示
- **无** `[添加模型]` `[编辑]` `[删除]` 按钮

**Copilot 职责**:
```
默认态:
  ├── Action Card: 「➕ 添加模型」（输入 API Key+配置）
  ├── Action Card: 「📊 成本分析」
  └── 快捷动作: 全部 / 文本 / 图像 / 多模态

成本超预算时（自动推送）:
  ├── Action Card: "本月 LLM 成本已达 80%（¥4,200/¥5,000），建议调整路由策略"
  ├── Action Card: 「🔀 切换至低成本模型」
  └── Action Card: 「📋 查看详细账单」
```

---

### 3.8 素材库 /assets（待开发，按新规范 🟢）

**工作区职责**:
- 图片/视频网格展示
- 拖拽上传区域（编辑辅助，非业务操作）
- **无** `[上传]` `[删除]` `[AI 打标签]` 按钮

**Copilot 职责**:
```
默认态:
  ├── Action Card: 「📤 上传素材」（支持批量，拖拽后 Copilot 询问分类）
  ├── Action Card: 「🏷️ AI 批量打标签」（选中多张后提供）
  └── 快捷动作: 图片 / 视频 / 全部

选中素材后:
  ├── Action Card: 「✏️ 编辑信息」（标题、标签、版权）
  ├── Action Card: 「🗑️ 删除」（二次确认 Card）
  └── Action Card: "建议添加版权来源标注，避免合规风险"
```

---

### 3.9 实验室 /lab（待开发，按新规范 🟢）

**工作区职责**:
- 爆款输入区（粘贴链接/上传截图）
- 结构解析展示（只读）
- 变量替换编辑区（输入框）
- 对比预览区（原爆款 vs 新生成）
- **无** `[一键生成]` `[保存模板]` 按钮

**Copilot 职责**:
```
默认态:
  ├── Action Card: 「🔍 解析爆款」（输入链接后 Copilot 驱动解析）
  ├── Action Card: 「📋 生成模板」（解析完成后提供）
  └── Action Card: 「🚀 一键生成」（修改变量后提供）

解析完成后:
  ├── Action Card: "识别出 5 个关键结构点，生成 ContentTemplate？"
  └── Action Card: 「📊 对比原爆款相似度：72%」
```

---

### 3.10 设置 /settings（待开发，按新规范 🟢）

**工作区职责**:
- 表单展示（系统设置、权限、通知配置）
- 开关、选择器、输入框（编辑辅助）
- **无** `[保存设置]` `[确认修改]` 按钮

**Copilot 职责**:
```
默认态:
  ├── Action Card: "检测到 3 项设置未保存，现在保存？"
  ├── Action Card: 「💾 保存所有变更」
  └── Action Card: 「↩️ 撤销本次修改」

修改敏感设置后:
  └── Action Card: "修改了权限配置，建议通知团队成员。发送通知？"
```

---

## 四、Action Card 统一规范

### 4.1 Action Card 视觉规范

```
┌─────────────────────────────────────┐
│  [Icon] 标题                         │  ← 14px 字体，加粗
│  说明文案（AI 建议/上下文）            │  ← 13px 字体，灰色
│  ─────────────────────────────────  │
│  [输入框 / 选择器 / 开关]（可选）     │
│  ─────────────────────────────────  │
│  [主要按钮] [次要按钮] [忽略]         │  ← 至少一个可执行按钮
│                                     │
│  [结果展示区]（执行后展开）           │  ← diff / preview / list
└─────────────────────────────────────┘
```

### 4.2 状态流转（全局统一）

```
进入页面 → Copilot 分析上下文 → 推送 Action Card(s)
                                      │
              ┌───────────────────────┼───────────────────────┐
              │                       │                       │
              ▼                       ▼                       ▼
        用户点击按钮            用户修改输入            用户忽略
              │                       │                       │
              ▼                       ▼                       ▼
        执行中（loading）      实时更新预览            Card 淡出
              │                       │
              ▼                       ▼
        ┌─────────────┐       ┌─────────────┐
        │   成功      │       │   失败      │
        │  展示结果   │       │  展示错误   │
        │  [应用]     │       │  [重试]     │
        │  [再优化]   │       │  [取消]     │
        └─────────────┘       └─────────────┘
              │
              ▼
        应用到工作区
        推送下一状态 Card
```

### 4.3 快捷动作区规范（Quick Action Bar）

位于 Copilot 面板输入框上方，根据页面上下文动态更新：

```typescript
// 通用快捷动作（所有页面共享）
const GLOBAL_QUICK_ACTIONS = [
  { icon: 'search', label: '搜索', command: '/search' },
  { icon: 'help-circle', label: '帮助', command: '/help' },
]

// 页面专属快捷动作（动态注册）
const PAGE_QUICK_ACTIONS: Record<string, QuickAction[]> = {
  '/review': [
    { icon: 'check-circle', label: '通过', command: 'approve' },
    { icon: 'rotate-ccw', label: '打回', command: 'revise' },
    { icon: 'x-circle', label: '驳回', command: 'reject' },
    { icon: 'image', label: '生成封面', command: 'generate_cover' },
  ],
  '/generate': [
    { icon: 'save', label: '保存', command: 'save_draft' },
    { icon: 'send', label: '提交审核', command: 'submit_review' },
    { icon: 'sparkles', label: '重新生成', command: 'regenerate' },
  ],
  '/': [
    { icon: 'plus', label: '新建任务', command: 'create_task' },
    { icon: 'bar-chart', label: '趋势', command: 'show_trend' },
  ],
  // ... 其他页面
}
```

---

## 五、工作区组件改造清单

### 5.1 全局组件

| 组件 | 当前状态 | 改造要求 | 负责人 |
|------|---------|---------|--------|
| `PageHeader` | 有 `actions` 属性可放按钮 | 保留 `actions` 但仅用于信息展示（Badge、标签），禁止放可执行按钮 | 前端 |
| `BentoCard` | Hover 显示操作入口 | Hover 仅高亮/放大，操作入口移除 | 前端 |
| `ContentCard` | 有 `[发布]` `[编辑]` 按钮 | 移除所有操作按钮，点击即选中态 | 前端 |
| `CommandPalette` | 全局搜索+命令 | 保留，作为 Copilot 的补充快捷入口 | 前端 |

### 5.2 页面级组件

| 页面 | 组件 | 改造要求 |
|------|------|---------|
| 工作台 | `MetricCard` | 移除「AI 分析」Hover 入口 |
| 工作台 | `ContentStream` | 卡片移除操作按钮，点击选中 |
| 内容生产 | `KanbanBoard` | 列头移除 `[+]` 按钮 |
| 内容生产 | `ContentEditor` | 移除 `[保存]` `[发布]` `[重新生成]` |
| 内容生产 | `Stepper`（向导） | 移除 `[下一步]` `[确认创建]`，改为纯展示 |
| 审核发布 | `ReviewDecisionPanel` | **已移除**，功能迁移至 Copilot |
| 审核发布 | `CoverPickerModal` | 移除 AI 生成 Tab |
| 全部 | 所有 `[删除]` `[编辑]` `[确认]` 按钮 | 全部迁移至 Copilot Action Cards |

---

## 六、后端 API 统一规范

### 6.1 通用响应扩展

所有 API 响应（除 SSE/WebSocket 外）可选择性包含 `copilot_followup` 字段：

```json
{
  "code": "OK",
  "message": "操作成功",
  "data": { ... },
  "copilot_followup": {
    "message": "审核已通过！要现在发布还是定时发布？",
    "suggested_cards": [
      {
        "type": "decision",
        "title": "发布确认",
        "actions": [
          { "id": "publish_now", "label": "立即发布" },
          { "id": "schedule", "label": "定时发布" }
        ]
      }
    ]
  }
}
```

### 6.2 新增通用 API

| API | 说明 | 优先级 |
|-----|------|--------|
| `POST /api/ai/copilot/context` | 上下文上报 | 🔴 P0 |
| `GET /api/ai/copilot/action-cards` | 获取推荐 Cards | 🔴 P0 |
| `POST /api/ai/generate-cover` | 封面生成 | 🔴 P0 |
| `POST /api/ai/copilot/execute` | 通用 Action 执行网关 | 🟡 P1 |
| `WS /ws/copilot` | Copilot 实时通道 | 🟡 P1 |

### 6.3 现有 API 改造清单

| API | 改造内容 |
|-----|---------|
| `GET /api/dashboard/overview` | 新增 `copilot_summary` 字段（AI 建议摘要） |
| `GET /api/task-hub/tasks` | 新增 `copilot_recommended_action` 字段 |
| `GET /api/review-publish-center/conclusions/:id` | 新增 `copilot_context` 字段 |
| `POST /api/human-in-the-loop/tasks/:id/approve` | 新增 `copilot_suggested`/`copilot_card_id` 字段 |
| 全部 POST/PUT/DELETE | 响应中可选包含 `copilot_followup` |

---

## 七、实施路线图

### Phase 1: 审核发布（当前，Week 5）
- ✅ HTML 预览已完成（Copilot-Driven）
- 🔄 React 实现（等待后端 API）
- 🔄 后端 API 开发（7 天）

### Phase 2: 工作台 + 内容生产回炉（Week 6）
- 🔴 工作台移除所有按钮，迁移至 Copilot
- 🔴 内容生产编辑器/向导/看板移除按钮
- 🔴 后端 API 扩展（通用 Copilot 网关）

### Phase 3: 剩余 P1 页面（Week 7）
- 🟡 数据报表、账号矩阵、Agent 舰队、模型中心
- 🟡 全部按 Copilot-Driven 开发

### Phase 4: P2/P3 页面 + 全局优化（Week 8）
- 🟢 素材库、实验室、设置
- 🟢 响应式适配、性能优化、E2E 测试

---

## 八、已完成页面回炉修改方案

### 8.1 工作台 `/`（P2-1 已完成的修改项）

**需要修改的文件**:
1. `pages/DashboardPage/DashboardPage.tsx`
   - 移除 `PageHeader` 中的 `[+ 新建任务]` 按钮
   - 移除 metric cards 上的点击操作

2. `pages/DashboardPage/ContentStream.tsx`
   - 移除 ContentCard 上的 `[一键发布]` `[修改]` `[查看详情]` 按钮
   - 点击卡片变为选中态（Checkbox 或高亮边框）
   - 选中后触发 Copilot 上下文更新

3. `components/common/BentoCard.tsx`
   - 移除 `onClick` 业务操作
   - 移除 Hover 时的操作入口浮层

4. `stores/aiCopilotStore.ts`
   - 新增工作台专属 Action Cards 推送逻辑

### 8.2 内容生产 `/generate`（P2-2 已完成的修改项）

**需要修改的文件**:
1. `pages/TaskHubPage.tsx`
   - 移除 `[+ 新建内容]` 按钮
   - 看板卡片移除拖拽操作（或保留为编辑辅助，但发布/编辑走 Copilot）

2. `pages/TaskHubCreatePage/TaskHubCreatePage.tsx`
   - 4 步向导改为纯展示（Stepper 无提交功能）
   - 移除 `[下一步]` `[确认创建]` 按钮
   - 在 Copilot 中提供「确认创建」Action Card（汇总配置）

3. `pages/ContentForgePage.tsx`
   - 移除编辑器顶部的 `[保存]` `[发布]` 按钮
   - 移除 `[重新生成]` 按钮
   - 保留 Inline AI 浮层（编辑辅助，非业务操作）
   - 在 Copilot 中提供：保存/发布/重新生成 Action Cards

4. `components/inline-ai/InlineAIFloat.tsx`
   - 保留（这是编辑辅助工具，不属于业务操作按钮）

---

## 九、附录

### 9.1 术语表

| 术语 | 定义 |
|------|------|
| **工作区 Workspace** | 中央画布区域，承担内容展示、编辑、预览 |
| **Copilot 面板** | 右侧 320px 持久 AI 副驾驶面板 |
| **Action Card** | Copilot 中的可执行卡片，含标题、说明、输入区、操作按钮 |
| **快捷动作 Quick Action** | Copilot 输入框上方的 pill 按钮，快速触发常用命令 |
| **Copilot-Driven** | 所有业务操作通过 Copilot 发起的交互模式 |
| **编辑辅助** | 不属于业务操作的编辑工具（格式化工具栏、拖拽、展开折叠） |

### 9.2 禁止清单（工作区绝对禁止）

- ❌ `[保存]` `[提交]` `[确认]` `[确定]` 等提交类按钮
- ❌ `[新建]` `[添加]` `[创建]` 等新建类按钮
- ❌ `[删除]` `[移除]` `[清空]` 等删除类按钮
- ❌ `[发布]` `[发送]` `[导出]` 等执行类按钮
- ❌ `[通过]` `[驳回]` `[打回]` 等决策类按钮
- ❌ `[生成]` `[重新生成]` `[优化]` 等 AI 操作按钮
- ❌ `[批量操作]` `[全选]` `[批量通过]` 等批量类按钮
- ✅ 例外：编辑辅助类（格式化工具栏、展开折叠、拖拽调整）

### 9.3 参考文档

- `demo/page-preview/review.html`（Copilot-Driven 完整实现参考）
- `docs/后端需求/后端需求补充_审核发布_Copilot-Driven_2026-06-04.md`
- `EcoDream_Omni_PRD_v2_对齐核心方案.md`（需求真源）
- `04-全局设计规范_浅色主题_AI工作台.md`（设计真源）

---

*文档版本: v2.0*  
*评审日期: 2026-06-04*  
*评审结论: 全面推广 Copilot-Driven*  
*实施状态: 审核发布先行，其余页面按路线图推进*
