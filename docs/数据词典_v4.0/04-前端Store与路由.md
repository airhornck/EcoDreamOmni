# 04-前端Store与路由

> **版本**: v4.0
> **生成日期**: 2026-06-03
> **前端基线**: `apps/frontend/src/`

---

## 一、Store 总览（Zustand）

`src/stores/` 共 24 个 Store 文件：

| Store | 说明 | v4.0 变更 |
|-------|------|----------|
| `authStore.ts` | 认证状态 | — |
| `aiCopilotStore.ts` | **AI Copilot 面板状态** | **P6-2 新增** → **Phase 10 扩展字段 + 持久化** |
| `labStore.ts` | **实验室 容器状态（能力切换）** | **P6-3 新增** |
| `playgroundStore.ts` | **爆款笔记分析 能力状态** | **P6-3 新增** |
| `inlineAIStore.ts` | **Inline AI 建议状态** | **P6-4 新增** |
| `agentFlowStore.ts` | **Agent Flow 状态** | **P6-5 新增** |
| `taskHubStore.ts` | 任务中心 | — |
| `contentForgeStore.ts` | 内容工坊 | — |
| `reviewPublishStore.ts` | 审核发布 | — |
| `dashboardStore.ts` | 驾驶舱 | — |
| `dataAnalystStore.ts` | 数据分析师 | — |
| `agentOrchestraStore.ts` | Agent 驾驶舱 | — |
| `agentCockpitStore.ts` | Agent 管理 | — |
| `llmCockpitStore.ts` | LLM 管理 | — |
| `skillHubStore.ts` | Skill 管理 | — |
| `cronCockpitStore.ts` | 定时调度 | — |
| `personaPoolStore.ts` | 人设池 | — |
| `personaStoryStore.ts` | 剧本管理 | — |
| `brandKnowledgeStore.ts` | 品牌知识库 | — |
| `assetPoolStore.ts` | 素材库 | — |
| `platformRulesStore.ts` | 平台规则 | — |
| `platformSchemaStore.ts` | 格式规范 | — |
| `complianceStore.ts` | 合规审核 | — |
| `predictionsStore.ts` | 互动预演 | — |
| `proxyStore.ts` | 代理配置 | — |

---

## 二、路由表（React Router v7）

### 2.1 完整路由列表

| 路径 | 页面组件 | 布局 | v4.0 变更 |
|------|---------|------|----------|
| `/login` | `LoginPage` | 无 | — |
| `/dashboard` | `DashboardPage` | AppLayout / WorkspaceLayout | — |
| `/generate` | `TaskHubPage` | **WorkspaceLayout** | **v4.0 路由对齐（原 `/task-hub`）** |
| `/generate/create` | `TaskHubCreatePage` | **WorkspaceLayout** | **v4.0 路由对齐（原 `/task-hub/create`）** |
| `/generate/editor/:taskId` | `ContentForgePage` | **WorkspaceLayout** | **v4.0 路由对齐（原 `/content-forge/:taskId`）** |
| `/task-hub` | → `/generate` | 重定向 | **v4.0 重命名** |
| `/task-hub/create` | → `/generate/create` | 重定向 | **v4.0 重命名** |
| `/content-forge/:taskId` | → `/generate/editor/:taskId` | 重定向 | **v4.0 重命名** |
| `/trend-scout` | → `/analytics` | 重定向 | **P1-2 合并入数据报表** |
| `/predictions` | `PredictionsPage` | AppLayout / WorkspaceLayout | — |
| **`/lab`** | **`LabPage`** | **WorkspaceLayout** | **P6-3 新增** |
| `/compliance` | `CompliancePage` | AppLayout / WorkspaceLayout | — |
| **`/review`** | **`ReviewPublishCenterPage`** | **WorkspaceLayout** | **v4.0 路由对齐（原 `/review-publish-center`）🔒 已冻结** |
| **`/review/:taskId`** | **`ReviewPublishDetailPage`** | **WorkspaceLayout** | **v4.0 路由对齐 🔒 已冻结** |
| `/publisher` | `PublisherPage` | AppLayout / WorkspaceLayout | — |
| `/data-analyst` | `DataAnalystPage` | AppLayout / WorkspaceLayout | — |
| `/engagement-tracking` | `EngagementTrackingPage` | AppLayout / WorkspaceLayout | — |
| `/account-pool` | `AccountPoolPage` | AppLayout / WorkspaceLayout | — |
| `/personas` | → `/accounts` | 重定向 | **P1-2 合并入账号矩阵** |
| `/skillhub` | `SkillHubPage` | AppLayout / WorkspaceLayout | — |
| `/agent-orchestra` | `AgentOrchestraPage` | AppLayout / WorkspaceLayout | — |
| `/llm-cockpit` | `LlmCockpitPage` | AppLayout / WorkspaceLayout | — |
| `/workflows` | `WorkflowCockpitPage` | AppLayout / WorkspaceLayout | **P1-2 新增** |
| `/workflow-cockpit` | `WorkflowCockpitPage` | AppLayout / WorkspaceLayout | — |
| `/cron-cockpit` | `CronCockpitPage` | AppLayout / WorkspaceLayout | — |
| `/rules` | `PlatformRulesPage` | AppLayout / WorkspaceLayout | **P1-2 新增** |
| `/platform-rules` | → `/rules` | 重定向 | **P1-2 重命名** |
| `/platform-rules/schema` | `PlatformSchemaPage` | AppLayout / WorkspaceLayout | — |
| `/proxy-config` | `ProxyConfigPage` | AppLayout / WorkspaceLayout | — |
| `/keywords` | `KeywordLibraryPage` | **WorkspaceLayout** | **P6-3 新增**（关键词库管理） |
| `/templates` | `TemplateLibraryPage` | **WorkspaceLayout** | **P6-3 新增**（模板库管理） |
| `/settings` | `SettingsPage` | AppLayout / WorkspaceLayout | — |
| `/assets` | `AssetPoolPage` | AppLayout / WorkspaceLayout | — |
| `/brand-knowledge` | → `/rules` | 重定向 | **P1-2 合并入平台规则** |
| `/timeline` | `TimelinePage` | AppLayout / WorkspaceLayout | — |
| `/vetdrug` | `VetDrugPage` | AppLayout / WorkspaceLayout | — |
| `/` | `DashboardPage` | AppLayout / WorkspaceLayout | **v4.0 主入口** |
| `/dashboard` | → `/` | 重定向 | — |

### 2.2 布局切换（P6-1）

```tsx
// Feature Flag: localStorage 'v4_workspace_layout'
// true  → WorkspaceLayout (Three-Panel)
// false → AppLayout (Sidebar + Header)
```

### 2.3 `WorkspaceLayout` CSS Grid 布局（Phase 10 修复）

Phase 10 将 `WorkspaceLayout` 从 Flex 布局重构为 **CSS Grid 布局**，解决 Header 被 Copilot 展开压缩的问题：

| 属性 | 旧值（Flex） | 新值（Grid） |
|------|------------|------------|
| 根容器 | `flex` | `grid` |
| 列定义 | `48px + 1fr + 320px`（手动计算） | `gridTemplateColumns: 48px 1fr 320px/0fr`（inline style） |
| Header | `flex` 子元素，受右侧宽度影响 | `col-start-2 col-span-2`，**横跨顶行，不受 Copilot 影响** |
| IconNav | `w-[48px]` | `row-span-2 col-start-1`，**占满两行** |
| Main | `flex-1` | `col-start-2 row-start-2 flex flex-col min-w-0` |
| Copilot | `fixed right-0 top-0 w-[320px]` | `col-start-3 row-start-2`，**Grid 控制显隐，无 fixed 定位** |
| 过渡动画 | `width` 过渡 | `grid-template-columns 0.3s ease` |

**关键修复点**：
- Header 使用 `col-span-2` 横跨第 2-3 列顶行，Copilot 展开时 Header 宽度恒定
- Copilot Panel 移除 `position: fixed`，由父级 Grid `gridTemplateColumns` 控制列宽为 `320px`（开）或 `0fr`（关）
- Toggle 按钮从 AICopilotPanel 内部移至 Header 右侧，全局可访问
- `AICopilotPanel` 使用 `opacity + pointerEvents` 控制视觉显隐，保留过渡动画

---

## 三、Store → API 映射

| Store | 调用的 API | 说明 |
|-------|-----------|------|
| `aiCopilotStore` | `POST /api/ai/copilot/context`<br>`GET /api/ai/copilot/action-cards`<br>`POST /api/ai/copilot/execute`<br>`WS /ws/copilot` | **AI Copilot 通用网关（v4.0 Step 2 新增）**<br>Phase 10 新增：`welcomeMessage`, `setWelcomeMessage`, `setQuickActions`, `isOpen` 持久化 |
| `labStore` | — | 实验室能力切换（无独立 API） |
| `playgroundStore` | `POST /api/playground/analyze`<br>`POST /api/playground/template`<br>`GET /api/playground/keywords`<br>`GET /api/playground/categories` | 爆款笔记分析（实验室第一个能力） |
| `keywordStore` | `POST /api/playground/keywords`<br>`PUT /api/playground/keywords/{id}`<br>`DELETE /api/playground/keywords/{id}`<br>`GET /api/playground/keywords/changelog` | 关键词库管理（v4.0 新增） |
| `templateStore` | `GET /api/content-templates`<br>`GET /api/content-templates/recommend` | 模板库管理（v4.0 新增） |
| `agentFlowStore` | `WS /ws/pipeline/{id}` | Pipeline 实时状态 |
| `taskHubStore` | `GET /api/task-hub/tasks`<br>`GET /api/task-hub/tasks/{id}`<br>`POST /api/task-hub/tasks`<br>`GET /api/agents`<br>`GET /api/agents/recommend`<br>`GET /api/account-pool`<br>`GET /api/personas`<br>`GET /api/platform-schemas` | **任务管理 + Agent 选择（v4.0 Step 2 新增 Copilot 字段）** |
| **`reviewPublishStore`** | **`GET /api/review-publish-center/conclusions`**<br>**`GET /api/review-publish-center/conclusions/{id}`**<br>**`POST /api/human-in-the-loop/tasks/{id}/{decision}`**<br>**`PUT /api/review-publish-center/conclusions/{id}/content`**<br>**`POST /api/review-publish-center/conclusions/{id}/confirm-publish`**<br>**`POST /api/review-publish-center/conclusions/{id}/regenerate`**<br>**`POST /api/ai/generate-cover`** | **审核发布（v4.0 Step 2 新增 Copilot 字段 + 封面生成）**<br>Phase 10：`ReviewPublishDetailPage` 的 Copilot Action Handler 已从本地自定义逻辑 **迁移到后端统一网关** `POST /api/ai/copilot/execute`。前端仅保留 UI 副作用（封面轮询、导航回列表、处理 `copilot_followup`）。 |
| `authStore` | `POST /auth/login` | 登录 |

---

## 四、新增组件目录（P6）

```
src/components/
├── layout/
│   ├── AppLayout.tsx           ← 原布局
│   ├── WorkspaceLayout.tsx     ← P6-1 Three-Panel
│   ├── IconNav.tsx             ← P6-1 48px 图标导航
│   ├── Sidebar.tsx             ← 更新 实验室 入口
│   └── Header.tsx
├── ai-copilot/                 ← P6-2
│   ├── AICopilotPanel.tsx
│   ├── ContextBar.tsx
│   ├── MessageHistory.tsx
│   ├── ActionCardStack.tsx
│   ├── QuickActionBar.tsx
│   └── InputBox.tsx
├── lab/                        ← P6-3 实验室容器
│   ├── CapabilityNav.tsx         ← 能力导航栏（水平 pills）
│   ├── ViralAnalyzerCapability.tsx ← 爆款笔记分析能力画布
│   └── LockedCapabilityPlaceholder.tsx ← 锁定能力占位页
├── pages/
│   ├── KeywordLibraryPage.tsx    ← P6-3 新增：关键词库管理页
│   └── TemplateLibraryPage.tsx   ← P6-3 新增：模板库管理页
├── playground/                 ← P6-3 爆款笔记分析（能力级组件）
│   ├── NoteEditorZone.tsx
│   ├── AnalysisPreviewZone.tsx
│   ├── ReportDetailZone.tsx
│   ├── TemplatePreviewZone.tsx
│   ├── ViralInputZone.tsx
│   ├── StructureParseZone.tsx
│   ├── TemplateGenZone.tsx
│   ├── VariableReplaceZone.tsx
│   ├── DiffPreviewZone.tsx
│   └── ActionBar.tsx
├── inline-ai/                  ← P6-4
│   └── InlineSuggestionCard.tsx
└── agent-flow/                 ← P6-5
    └── AgentFlowBar.tsx
```

---

## 五、Hooks（v4.0 新增）

| Hook | 路径 | 说明 |
|------|------|------|
| `useSSEStream` | `src/hooks/useSSEStream.ts` | SSE 流式响应（P6-2） |
| `useAlertStream` | `src/hooks/useAlertStream.ts` | WebSocket 告警（已有） |
| **`useCopilotPageSync`** | **`src/hooks/useCopilotPageSync.ts`** | **Phase 10 新增：统一页面-Copilot 上下文同步。自动检测当前路由，上报后端 `POST /api/ai/copilot/context`，获取 `GET /api/ai/copilot/action-cards`，更新 Store 的 `welcomeMessage`、`pageActionCards`、`quickActions`。所有 WorkspaceLayout 下的页面共用，无需每页手动注入。** |

### 5.1 `useCopilotPageSync` 工作流程

```
location.pathname 变化
  ├─→ POST /api/ai/copilot/context  { page, pageTitle, selectedItems }
  │     ├─→ 成功：setContext(ctx) + setWelcomeMessage(ai_insights[0])
  │     └─→ 失败：静默，不阻塞页面
  ├─→ GET  /api/ai/copilot/action-cards?page={page}
  │     ├─→ 成功：setPageActionCards(cards) + setQuickActions(actions)
  │     └─→ 失败：清空，不硬编码兜底
  └─→ 页面卸载：setPageActionCards([]) + setWelcomeMessage(null) + setQuickActions([])
```

### 5.2 `aiCopilotStore` 字段扩展（Phase 10）

| 字段 | 类型 | 说明 |
|------|------|------|
| `welcomeMessage` | `string \| null` | 动态欢迎语，来自后端 `ai_insights[0]` |
| `setWelcomeMessage` | `(msg) => void` | 设置欢迎语 |
| `setQuickActions` | `(actions) => void` | 动态设置快捷动作（替换默认硬编码列表） |
| `isOpen` | `boolean` | **新增持久化**：通过 `zustand/middleware` 的 `persist` 写入 `localStorage['ai-copilot-store']`，刷新后保持上一次开关状态 |
