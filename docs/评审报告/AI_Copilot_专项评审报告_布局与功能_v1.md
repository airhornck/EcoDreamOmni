# AI Copilot 专项评审报告 — 布局缺陷与功能联动缺失

> **评审日期**: 2026-06-05  
> **评审范围**: EcoDream Omni v4.0 前端 AI Copilot 面板（布局层 + 功能层）  
> **评审维度**: 前端架构 / UI/UX 设计 / LLM 集成 / 页面联动  
> **评审结论**: 🔴 **2 项 P0 阻断性问题**，需立即修复  
> **报告状态**: 待决策采纳

---

## 一、报告摘要

| # | 问题 | 严重级别 | 影响范围 | 状态 |
|---|------|---------|---------|------|
| 1 | **布局缺陷**: AI Copilot 顶到视口顶部（遮挡 Header），左侧画布被遮挡，无抽拉效果 | 🔴 P0 | 所有页面 | 待修复 |
| 2 | **功能联动缺失**: 仅 4/20+ 页面注入 Copilot 上下文；无页面欢迎语；LLM 后端未连接；Mock 关闭导致功能不可用 | 🔴 P0 | 核心产品体验 | 待修复 |

**综合评分**: 2.1/5（布局 1.5/5，功能联动 2.0/5，工作区-Copilot 映射 2.0/5，LLM 驱动 2.0/5，代码质量 3.0/5）

---

## 二、问题一：AI Copilot 布局缺陷（P0）

### 2.1 现状分析

**当前布局结构**（`WorkspaceLayout.tsx`）：

```
┌─────────────────────────────────────────────────────────────┐
│ IconNav (48px) │  Header (56px)                              │
│                ├─────────────────────────────────────────────┤
│                │                                              │
│                │    Main Canvas (flex-1)                      │
│                │    ← 宽度 = 100vw - 48px                     │
│                │    ← 被 AICopilot (fixed) 遮挡右侧 320px     │
│                │                                              │
│                │                                              │
└─────────────────────────────────────────────────────────────┘
                 ↑ AICopilotPanel (fixed right-0 top-0)
                   z-30, w-[320px], h-screen
```

**关键代码**（`AICopilotPanel.tsx`）：

```tsx
// 展开状态 — 遮挡顶部和右侧
<aside className="fixed right-0 top-0 z-30 h-screen w-[320px] ...">

// 收起状态 — 悬浮按钮
<button className="fixed right-0 top-1/2 ...">
```

**关键代码**（`WorkspaceLayout.tsx`）：

```tsx
<div className="h-screen w-screen ... flex">
  <IconNav />                                   {/* 48px */}
  <main className="flex-1 flex flex-col ...">   {/* 占满剩余宽度 */}
    <Header />                                  {/* 56px */}
    <div className="flex-1 p-6 overflow-y-auto">{children}</div>
  </main>
  <AICopilotPanel />                            {/* fixed 定位，不占文档流 */}
</div>
```

### 2.2 具体缺陷

#### 缺陷 A：Copilot 顶到视口顶部，覆盖 Header 区域

| 期望 | 现状 |
|------|------|
| Copilot 顶部对齐 Header 下沿（`top: 56px`） | Copilot 顶部对齐视口顶部（`top: 0`） |
| Copilot 高度 = `100vh - 56px` | Copilot 高度 = `100vh` |
| Header 始终完整可见 | Header 右侧被 Copilot 覆盖 |

**截图示意**：
```
期望状态                          现状（错误）
┌────────┬─────────────────┐     ┌────────┬──────────┬──────┐
│        │    Header       │     │        │ Header   │██████│ ← 被遮挡
├────────┼─────────────────┤     ├────────┼──────────┴──────┤
│        │                 │     │        │                 │
│ IconNav│   Main Canvas   │     │ IconNav│   Main Canvas   │
│        │                 │     │        │                 │
│        │                 │     │        │                 │
├────────┴─────────────────┤     ├────────┴────────────┬────┤
│                          │     │                     │CP │ ← 顶到顶部
└──────────────────────────┘     └─────────────────────┴────┘
                              Copilot 应该在这里 ↓
```

#### 缺陷 B：左侧工作画布被 Copilot 遮挡

| 期望 | 现状 |
|------|------|
| Copilot 展开时，Main Canvas 宽度自适应收缩 | Main Canvas 宽度不变，右侧 320px 内容被遮挡 |
| 画布内容始终完整可见 | 画布右侧内容被 Copilot 覆盖，无法滚动查看 |

**根本原因**：`AICopilotPanel` 使用 `position: fixed`，脱离文档流。`main` 区域的 `flex-1` 计算的是 `100vw - 48px`（IconNav 宽度），没有为 Copilot 预留空间。

#### 缺陷 C：无抽拉效果

| 期望 | 现状 |
|------|------|
| Copilot 展开/收起时，Main Canvas 宽度平滑过渡（CSS transition） | 无过渡动画，Copilot 瞬间出现/消失 |
| 收起时 Copilot 完全隐藏，Main Canvas 占满宽度 | 收起时仍有悬浮按钮占用右侧空间 |

### 2.3 根因分析

```
设计决策错误（WorkspaceLayout.tsx）
  ├── AICopilotPanel 使用 position: fixed
  │     ├── 不占文档流 → main 区域不知道它的存在
  │     ├── top-0 → 覆盖 Header
  │     └── h-screen → 覆盖整个视口高度
  │
  └── main 区域使用 flex-1
        └── 宽度计算 = 100% - 48px（仅减去 IconNav）
            └── 没有减去 Copilot 的 320px
```

### 2.4 修复方案

#### 方案 A：Flex 布局改造（推荐）

将 `AICopilotPanel` 从 `fixed` 改为文档流内的 `flex` 子项，通过 CSS Grid 或 Flex + transition 实现抽拉效果。

```tsx
// WorkspaceLayout.tsx 改造后
function WorkspaceLayout({ children }: WorkspaceLayoutProps) {
  const { isOpen } = useAICopilotStore()

  return (
    <div className="h-screen w-screen bg-background ... flex">
      {/* Left: IconNav */}
      <IconNav />

      {/* Center: Main Canvas */}
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden
        transition-[width] duration-300 ease-in-out">
        <Header />
        <div className="flex-1 p-6 overflow-y-auto">{children}</div>
      </main>

      {/* Right: AI Copilot Panel — 文档流内，非 fixed */}
      <aside className={cn(
        "h-[calc(100vh-56px)] mt-14 border-l border-border flex flex-col
         bg-card transition-all duration-300 ease-in-out overflow-hidden",
        isOpen ? "w-[320px] opacity-100" : "w-0 opacity-0"
      )}>
        <AICopilotPanelContent />
      </aside>
    </div>
  )
}
```

**关键变更点**：

| 变更项 | 当前值 | 目标值 |
|--------|--------|--------|
| 定位方式 | `position: fixed` | 文档流 `flex` 子项 |
| 顶部偏移 | `top-0` | `mt-14`（56px，Header 高度） |
| 高度 | `h-screen` | `h-[calc(100vh-56px)]` |
| 宽度切换 | 瞬间切换 | `transition-all duration-300` |
| 收起状态 | 悬浮按钮 | 宽度收缩为 0 + 保留触发按钮在 Header 内 |

#### 方案 B：CSS Grid 改造（备选）

```css
.workspace-grid {
  display: grid;
  grid-template-columns: 48px 1fr 0fr;
  grid-template-rows: 56px 1fr;
  transition: grid-template-columns 0.3s ease;
}

.workspace-grid.copilot-open {
  grid-template-columns: 48px 1fr 320px;
}
```

**方案对比**：

| 维度 | 方案 A（Flex） | 方案 B（Grid） |
|------|---------------|---------------|
| 兼容性 | 极好 | 极好 |
| 动画支持 | `width` transition | `grid-template-columns` transition |
| 代码侵入性 | 中（需改 2 个文件） | 中（需改 2 个文件） |
| 响应式扩展 | 容易 | 容易 |
| 推荐度 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

### 2.5 实现步骤

1. **修改 `WorkspaceLayout.tsx`**：
   - 引入 `useAICopilotStore` 读取 `isOpen`
   - 将 `AICopilotPanel` 从 `fixed` 改为文档流内的 `aside`
   - 调整 `main` 区域过渡动画
   - 将 Copilot 触发按钮集成到 `Header` 右侧

2. **修改 `AICopilotPanel.tsx`**：
   - 移除 `fixed` 相关样式
   - 移除收起状态的悬浮按钮（改由 Header 控制）
   - 确保内部滚动正常工作

3. **修改 `Header.tsx`**：
   - 右侧添加 Copilot 展开/收起按钮
   - 按钮状态与 `isOpen` 联动

---

## 三、问题二：AI Copilot 功能联动与 LLM 驱动能力缺失（P0）

### 3.1 现状全景分析

#### 3.1.1 页面上下文覆盖率

| 页面 | 路由 | Copilot 上下文注入 | Action Cards | 状态 |
|------|------|-------------------|-------------|------|
| 工作台 | `/` | ✅ `useDashboardContext` | ✅ 后端获取 | 后端未启动 → 空 |
| 审核发布列表 | `/review` | ✅ 手动注入 | ✅ 后端获取 | 后端未启动 → 空 |
| 审核发布详情 | `/review/:taskId` | ✅ 手动注入 | ✅ 后端获取 | 后端未启动 → 空 |
| 实验室 | `/lab` | ✅ 手动注入 | ❌ 无 | 仅上下文 |
| 内容生产 | `/generate` | ❌ **无** | ❌ 无 | **完全缺失** |
| 内容生产创建 | `/generate/create` | ❌ **无** | ❌ 无 | **完全缺失** |
| 编辑器 | `/generate/editor/:taskId` | ❌ **无** | ❌ 无 | **完全缺失** |
| 数据报表 | `/analytics` | ❌ **无** | ❌ 无 | **完全缺失** |
| 账号矩阵 | `/accounts` | ❌ **无** | ❌ 无 | **完全缺失** |
| 素材库 | `/assets` | ❌ **无** | ❌ 无 | **完全缺失** |
| Agent 舰队 | `/agents` | ❌ **无** | ❌ 无 | **完全缺失** |
| 模型中心 | `/models` | ❌ **无** | ❌ 无 | **完全缺失** |
| 关键词库 | `/keywords` | ❌ **无** | ❌ 无 | **完全缺失** |
| 模板库 | `/templates` | ❌ **无** | ❌ 无 | **完全缺失** |
| 设置 | `/settings` | ❌ **无** | ❌ 无 | **完全缺失** |
| 工作流 | `/workflows` | ❌ **无** | ❌ 无 | **完全缺失** |
| 平台规则 | `/rules` | ❌ **无** | ❌ 无 | **完全缺失** |
| 实验室其他能力 | `/lab/*` | ⚠️ 仅基础 | ❌ 无 | 不完整 |

**覆盖率**: 4/18 页面（22%），严重不达标。

#### 3.1.2 欢迎语与页面联动

**当前 `MessageHistory` 空状态**（所有页面统一）：

```tsx
<div className="text-center space-y-2">
  <Bot className="w-5 h-5 text-primary" />
  <p className="text-sm text-muted-foreground">有什么可以帮你的？</p>
  <p className="text-xs text-muted-foreground">
    AI Copilot 可协助内容生成、数据分析和任务执行
  </p>
</div>
```

**问题**：
- 无页面特定欢迎语（如工作台应提示"今日有 X 项待处理任务"）
- 无上下文感知的操作建议（如审核页应提示"3 条待审，建议优先处理合规分低于 80 分的"）
- `QuickActionBar` 快捷动作是全局硬编码的，不随页面变化

#### 3.1.3 LLM 连接状态

**SSE 连接配置**（`useSSEStream.ts`）：

```ts
export function useSSEStream(endpoint = '/api/v1/ai/conversations/stream')
```

**实际运行时状态**（Vite 代理日志）：

```
[vite] http proxy error: /ai/copilot/action-cards?page=/
AggregateError [ECONNREFUSED]

[vite] http proxy error: /llm-hub/models
AggregateError [ECONNREFUSED]
```

**结论**：后端服务（端口 8001）未启动，所有 Copilot API 调用均失败。

#### 3.1.4 Mock 策略

**`reviewPublishStore.ts`**：
```ts
const USE_MOCK = false // Backend is ready — using real API
```

**问题**：
- `USE_MOCK = false`，所有 Copilot 功能走真实 API
- 后端未启动 → API 全部失败 → Copilot 功能完全不可用
- 没有前端降级策略（如 Mock 回退或本地模拟对话）

### 3.2 具体缺陷

#### 缺陷 A：页面上下文覆盖率严重不足（18 页面仅 4 个注入）

**根因**：
- 没有统一的 Copilot 上下文注入机制（如 Route Guard 或 Layout Effect）
- 每个页面需要手动写 `useEffect` 注入，开发成本高，容易遗漏
- 新页面开发时没有 Copilot 联动的强制检查清单

**影响**：
- 用户切换页面时，Copilot 面板显示的上下文仍是上一个页面的
- Copilot 无法感知当前页面，无法提供相关建议

#### 缺陷 B：无页面特定欢迎语

**期望 vs 现状**：

| 页面 | 期望欢迎语（运营视角） | 现状 |
|------|----------------------|------|
| 工作台 `/` | "当前矩阵 {accountCount} 个素人账号活跃，{pendingTasks} 项内容待排期。需要我帮你安排批量生产计划吗？" | "有什么可以帮你的？" |
| 审核发布 `/review` | "{pendingCount} 条内容来自 {accountCount} 个账号待审，其中 1 条合规分低于 80 分建议优先处理。" | "有什么可以帮你的？" |
| 内容生产 `/generate` | "当前 {pendingCount} 个素人账号有待创作任务。需要我为哪个账号批量安排内容？" | "有什么可以帮你的？" |
| 数据报表 `/analytics` | "本周 {accountCount} 个素人账号总互动量环比 {trend}，其中 {topAccount} 表现最佳。要生成战报吗？" | "有什么可以帮你的？" |
| 账号矩阵 `/accounts` | "矩阵内 {accountCount} 个素人账号，{lowHealthCount} 个健康度低于 70 需要关注。要制定养号计划吗？" | "有什么可以帮你的？" |
| Agent 舰队 `/agents` | "{activeAgents} 个 Agent 正在驱动内容生产队列，当前堆积 {queuedTasks} 个任务。" | "有什么可以帮你的？" |
| 素材库 `/assets` | "素材库共 {assetCount} 条素材，{untaggedCount} 条待打标签。需要批量整理吗？" | "有什么可以帮你的？" |

#### 缺陷 C：QuickActionBar 全局硬编码，无页面适配

**当前**（`aiCopilotStore.ts`）：
```ts
quickActions: [
  "为@省钱狗爸生成驱虫内容",
  "分析最近7天爆款趋势",
  "优化这条文案的标题",
  "检查合规风险",
]
```

**问题**：
- 4 个快捷动作在所有页面固定显示
- 与当前页面无关的快捷动作会造成干扰（如在设置页显示"生成驱虫内容"）
- 没有根据页面状态动态生成快捷动作的机制

#### 缺陷 D：LLM 后端未连接，对话功能不可用

**对话流程**：
```
用户输入 → AICopilotPanel.handleSend → useSSEStream.sendStreamMessage
  → fetch('/api/v1/ai/conversations/stream')
    → Vite Proxy → localhost:8001
      → ❌ ECONNREFUSED（后端未启动）
```

**结果**：
- 用户发送消息后，界面显示"thinking"状态，然后报错
- 没有任何 AI 回复
- Copilot 沦为纯展示面板

#### 缺陷 E：Action Cards 后端依赖过重，无前端兜底

**Dashboard 的 Action Cards 获取**（`useDashboardContext.ts`）：
```ts
apiClient<{ cards: unknown[] }>("/api/ai/copilot/action-cards?page=/")
  .then((res) => { ... setPageActionCards(cards) })
  .catch(() => { setPageActionCards([]) }) // ← 失败时直接清空
```

**问题**：
- 后端失败时，Action Cards 直接为空
- 没有前端兜底逻辑（如根据页面状态本地生成默认 Action Cards）
- 用户在大多数页面看不到任何 Action Cards

### 3.3 根因分析

```
架构设计缺失
  ├── 无统一 Copilot 上下文注入机制
  │     └── 每个页面手动注入 → 遗漏率高（18 页面仅 4 个）
  │
  ├── 无页面状态 → 欢迎语/快捷动作/Action Cards 的映射层
  │     └── MessageHistory / QuickActionBar 全局硬编码
  │     └── 工作区按钮已移除（Mode C），但 Copilot Action Cards 未补齐 → 双盲状态
  │
  ├── LLM 集成未解耦
  │     ├── USE_MOCK = false，无降级路径
  │     ├── 后端未启动 → 全部功能不可用
  │     └── 没有"本地模式"或"模拟模式"供前端独立开发
  │
  └── Action Cards 纯后端驱动
        ├── 后端失败时无兜底
        └── 延迟高（需等待 API 返回）
```

### 3.4 修复方案

#### 3.4.1 统一 Copilot 上下文注入机制（P0）

**方案**：在 `WorkspaceLayout` 或 `AppRoutes` 层统一注入，而非每个页面手动注入。

```tsx
// AppRoutes.tsx 或 WorkspaceLayout.tsx
import { useLocation } from 'react-router-dom'
import { useAICopilotStore } from '../stores/aiCopilotStore'

const PAGE_CONFIG: Record<string, { title: string; welcome: string; quickActions: string[] }> = {
  '/': {
    title: '工作台',
    welcome: '当前矩阵 {accountCount} 个素人账号活跃，{pendingTasks} 项内容待排期。需要我帮你安排批量生产计划吗？',
    quickActions: ['批量排期', '查看待审内容', '生成本周战报'],
  },
  '/generate': {
    title: '内容生产',
    welcome: '当前 {pendingCount} 个素人账号有待创作任务。需要我为哪个账号批量安排内容？',
    quickActions: ['为省钱狗爸排期', '为阿明救助站排期', '批量生成驱虫内容'],
  },
  '/review': {
    title: '审核发布',
    welcome: '当前有 {pendingCount} 条待审内容。',
    quickActions: ['批量审核', '优先处理低合规分'],
  },
  // ... 其他页面
}

function useCopilotPageSync() {
  const location = useLocation()
  const { setContext, setWelcomeMessage, setQuickActions } = useAICopilotStore()

  useEffect(() => {
    const config = PAGE_CONFIG[location.pathname] || PAGE_CONFIG['/']
    setContext({ page: location.pathname, pageTitle: config.title })
    setWelcomeMessage(config.welcome)
    setQuickActions(config.quickActions)
  }, [location.pathname])
}
```

**覆盖页面**：全部 18+ 页面一次性覆盖。

#### 3.4.2 欢迎语动态生成层（P0）

**方案**：在 `aiCopilotStore` 中增加 `welcomeMessage` 状态，`MessageHistory` 根据该状态渲染页面特定欢迎语。

```tsx
// aiCopilotStore.ts 扩展
interface AICopilotState {
  // ... 现有状态
  welcomeMessage: string | null
  setWelcomeMessage: (msg: string | null) => void
}

// MessageHistory.tsx 改造
export function MessageHistory() {
  const { messages, status, welcomeMessage } = useAICopilotStore()
  // ...
  if (messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center p-4">
        <div className="text-center space-y-2">
          <Bot className="w-5 h-5 text-primary" />
          <p className="text-sm text-muted-foreground">
            {welcomeMessage || '有什么可以帮你的？'}
          </p>
        </div>
      </div>
    )
  }
}
```

#### 3.4.3 QuickActionBar 页面化（P1）

**方案**：`quickActions` 从全局硬编码改为按页面配置，在 `useCopilotPageSync` 中同步更新。

#### 3.4.4 LLM 连接降级策略（P0）

**方案 A：Mock 模式开关（立即生效）**

将 `USE_MOCK` 改为环境变量控制，开发环境默认启用 Mock：

```ts
// .env.development
VITE_ENABLE_COPILOT_MOCK=true

// useSSEStream.ts
const USE_MOCK = import.meta.env.VITE_ENABLE_COPILOT_MOCK === 'true'

// Mock 实现：本地模拟对话回复
async function mockSendMessage(content: string): Promise<SSEMessage[]> {
  await delay(800)
  return [{
    id: `msg_${Date.now()}`,
    role: 'assistant',
    content: `我收到了你的消息："${content}"。（当前处于 Mock 模式，后端 LLM 服务尚未连接。）`,
    timestamp: new Date().toISOString(),
  }]
}
```

**方案 B：本地轻量级 LLM 代理（中长期）**

集成 `window.ai`（Chrome 内置 AI）或本地 ollama，作为后端不可用时的降级方案。

#### 3.4.5 Action Cards 前端兜底（P1）

**方案**：在 `useCopilotPageSync` 中，根据页面状态本地生成默认 Action Cards，不依赖后端 API。

```ts
const DEFAULT_PAGE_ACTIONS: Record<string, PageActionCard[]> = {
  '/': [
    { id: 'dash-batch-schedule', type: 'suggestion', title: '批量排期', description: '为多个素人账号统一安排内容生产计划', actions: [{ id: 'schedule', label: '开始排期', variant: 'primary' }] },
    { id: 'dash-go-review', type: 'suggestion', title: '审核待办', description: '查看待审内容', actions: [{ id: 'review', label: '去审核', variant: 'primary' }] },
  ],
  '/generate': [
    { id: 'gen-batch', type: 'suggestion', title: '批量生成', description: '为指定素人账号批量生成内容', actions: [{ id: 'generate', label: '选择账号', variant: 'primary' }] },
  ],
  // ...
}
```

#### 3.4.6 工作区功能按钮 → Copilot Action Cards 联动映射（P0）

**问题本质**：v4.0 Mode C 规范要求工作区禁止所有业务操作按钮，全部迁移至 Copilot Action Cards。但当前代码中，工作区按钮虽已被移除（见 `TaskHubPage.tsx` 中 "Mode C: 工作区禁止...操作按钮"注释），**Copilot 中并未提供对应的替代 Action Cards**，导致用户"无按钮可点、无 Card 可用"的双盲状态。

**设计真源**：`docs/前端设计/Copilot-Workspace-交互模式规范_v2.0.md` §三、§八

**映射矩阵**（工作区已移除的按钮 → Copilot 应提供的 Action Cards）：

| 页面 | 工作区已移除的按钮 | Copilot 应提供的 Action Cards | 触发条件 |
|------|------------------|------------------------------|---------|
| **工作台 `/`** | `[+ 新建任务]` | ➕ **批量排期**：选择多个素人账号 + 主题，一键排期 | 默认态 |
| | `[一键发布]`（ContentCard） | 📤 **批量发布**：选中可发布内容后提供 | 选中可发布卡片 |
| | `[AI 分析]`（MetricCard Hover） | 📊 **生成 AI 战报**：矩阵整体数据总结 | 点击指标卡片 |
| **内容生产 `/generate`** | `[+ 新建内容]`（看板列头） | ➕ **批量生成**：选择素人账号 + 平台 + 主题 | 默认态 |
| | `[保存]` `[发布]`（编辑器） | 💾 **保存草稿** / 🚀 **提交审核** | 检测到编辑变更后 |
| | `[重新生成]` | 🔄 **重新生成**（含风格/长度/Agent 选择） | 编辑完成后 |
| | `[下一步]` `[确认创建]`（向导） | ✅ **确认创建**（汇总 4 步配置，一键确认） | 向导配置完成后 |
| **审核发布 `/review`** | `[通过]` `[打回]` `[驳回]` | ✅ **审核决策**（通过/打回/驳回 + 原因输入） | 选中待审内容 |
| | `[生成封面]` | 🎨 **生成封面**（输入描述，AI 生成） | 详情页默认态 |
| | `[批量通过]` | 📋 **批量审核**（选中多条后提供） | 列表页多选后 |
| **数据报表 `/analytics`** | `[导出报表]` | 📋 **导出战报**（自然语言总结 + 数据导出） | 默认态 |
| | `[查看趋势]` | 📈 **预测未来 7 天趋势** | 选中异常指标后 |
| **账号矩阵 `/accounts`** | `[+ 添加账号]` | ➕ **添加素人账号**（平台 + 账号信息） | 默认态 |
| | `[修复健康度]` | 🛠️ **修复健康度**（具体修复步骤 Card） | 选中低健康度账号 |
| | `[生成发布计划]` | 📅 **生成发布计划**（AI 排期） | 默认态 |
| **Agent 舰队 `/agents`** | `[部署]` `[暂停]` `[重启]` | 🚀 **部署 Agent** / 🔄 **重启 Agent** | 默认态/选中异常 Agent |
| | `[修改配置]` | ⚙️ **修改配置** | 选中 Agent 后 |
| **素材库 `/assets`** | `[上传]` `[AI 打标签]` | 📤 **上传素材** / 🏷️ **AI 批量打标签** | 默认态/选中素材后 |

**关键设计原则**：

1. **选中即触发**：用户在工作区点击卡片/行/元素后，Copilot 立即感知并推送相关 Action Cards（通过 `setContext({ selectedItems, selectedContent })`）
2. **状态流转**：Action Card 执行后，Copilot 自动推送下一步建议（如"审核通过 → 发布确认 Card"）
3. **快捷动作联动**：QuickActionBar 根据当前选中的对象动态更新（如选中待审内容后显示"通过/打回/驳回"快捷动作）

**实现检查清单**：

- [ ] 每个页面的工作区按钮已移除（Mode C 合规）
- [ ] 每个页面在 Copilot 中提供至少 2 个默认 Action Cards
- [ ] 选中工作区元素后，Copilot 上下文更新并推送相关 Cards
- [ ] Action Card 执行后，Copilot 推送下一步建议（状态流转）

### 3.5 实现优先级

| 优先级 | 任务 | 影响 | 工作量 | 依赖 |
|--------|------|------|--------|------|
| P0 | 统一 Copilot 上下文注入机制 | 解决 14 个页面无上下文问题 | 2h | 无 |
| P0 | Mock 模式开关 + 模拟对话 | 让 Copilot 在开发环境可用 | 1h | 无 |
| P0 | 欢迎语动态生成 | 提升用户体验 | 1h | 上下文注入 |
| P1 | Action Cards 前端兜底 | 减少后端依赖 | 2h | 上下文注入 |
| P1 | QuickActionBar 页面化 | 提升相关性 | 1h | 上下文注入 |
| P2 | 各页面精细化的 Action Cards | 提升功能深度 | 4h | 前端兜底 |

---

## 四、综合评估与建议

### 4.1 两项问题的关联性

布局问题与功能联动问题并非孤立：

- **布局修复是功能联动的先决条件**：如果 Copilot 面板遮挡画布，即使用户能与 Copilot 对话，也无法看到 Copilot 建议操作后的页面变化。
- **功能联动是布局的价值所在**：如果 Copilot 不能根据页面提供建议，面板只是一个空壳，布局再精美也无意义。

### 4.2 推荐实施路径

```
Phase 1（本周，2 天）
├── 布局修复（Flex 改造）
├── 统一 Copilot 上下文注入
├── Mock 模式开关
└── 欢迎语动态生成

Phase 2（下周，3 天）
├── Action Cards 前端兜底
├── QuickActionBar 页面化
├── 各页面精细化的 Copilot 联动
└── 后端 API 联调

Phase 3（后续）
├── LLM 后端就绪后关闭 Mock
├── 用户行为数据收集
└── Copilot 效果评估与迭代
```

### 4.3 质量门禁

- [ ] 布局修复后，所有页面在 Copilot 展开/收起时，Main Canvas 内容完整可见
- [ ] 布局修复后，Header 不被 Copilot 遮挡
- [ ] 功能修复后，18+ 页面均有 Copilot 上下文注入
- [ ] 功能修复后，开发环境下 Copilot 对话可用（Mock 模式）
- [ ] 功能修复后，每个页面有页面特定欢迎语

---

## 五、附录：代码审计清单

### 5.1 需修改的文件

| # | 文件 | 问题 | 修改类型 |
|---|------|------|---------|
| 1 | `WorkspaceLayout.tsx` | 布局结构 | 重构 |
| 2 | `AICopilotPanel.tsx` | 移除 fixed 定位 | 重构 |
| 3 | `Header.tsx` | 添加 Copilot 切换按钮 | 新增 |
| 4 | `App.tsx` / `AppRoutes.tsx` | 统一上下文注入 | 新增 |
| 5 | `aiCopilotStore.ts` | 增加 welcomeMessage / quickActions 动态化 | 扩展 |
| 6 | `MessageHistory.tsx` | 欢迎语动态渲染 | 修改 |
| 7 | `QuickActionBar.tsx` | 从 store 读取动态 actions | 修改 |
| 8 | `useSSEStream.ts` | Mock 模式开关 | 扩展 |
| 9 | `DashboardPage.tsx` | 移除手动 useDashboardContext（改统一注入） | 简化 |
| 10 | `ReviewPublishCenterPage.tsx` | 移除手动 Copilot 注入（改统一注入） | 简化 |
| 11 | `ReviewPublishDetailPage.tsx` | 移除手动 Copilot 注入（改统一注入） | 简化 |
| 12 | `LabPage.tsx` | 移除手动 Copilot 注入（改统一注入） | 简化 |
| 13 | `PlaygroundPage.tsx` | 移除手动 Copilot 注入（改统一注入） | 简化 |
| 14 | `TaskHubPage.tsx` / `TaskHubCreatePage.tsx` / `ContentForgePage.tsx` | 新增 Copilot 注入 | 新增 |
| 15 | `DataAnalystPage.tsx` / `AccountPoolPage.tsx` / `AssetPoolPage.tsx` | 新增 Copilot 注入 | 新增 |
| 16 | `AgentOrchestraPage.tsx` / `LlmCockpitPage.tsx` | 新增 Copilot 注入 | 新增 |
| 17 | `SettingsPage.tsx` / `PlatformRulesPage.tsx` / `ProxyConfigPage.tsx` | 新增 Copilot 注入 | 新增 |
| 18 | `.env.development` | 添加 Mock 开关 | 新增 |

### 5.2 新增文件

| 文件 | 用途 |
|------|------|
| `hooks/useCopilotPageSync.ts` | 统一页面上下文同步 Hook |
| `lib/copilotPageConfig.ts` | 页面 → 欢迎语/快捷动作/Action Cards 映射配置 |
| `lib/mockSSE.ts` | Mock 模式下的 SSE 模拟实现 |

---

*评审人: Kimi Code CLI*  
*评审日期: 2026-06-05*  
*修订日期: 2026-06-05*  
*版本: v1.1（修订版：欢迎语运营化 + 工作区按钮-Action Cards 联动映射补充）*
