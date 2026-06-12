# AI Copilot 专项评审报告 — 布局缺陷与功能联动缺失

> **评审日期**: 2026-06-05  
> **修订日期**: 2026-06-05  
> **评审范围**: EcoDream Omni v4.0 前端 AI Copilot 面板（布局层 + 功能层）  
> **评审维度**: 前端架构 / UI/UX 设计 / LLM 集成 / 页面联动  
> **评审结论**: 🔴 **2 项 P0 阻断性问题**，需立即修复  
> **报告状态**: ✅ **已采纳（按专家评审条件修正后实施）**  
> **专家评审报告**: `docs/变更记录_v4.0/2026-06-05/AI_Copilot布局与功能修复_专家评审报告.md`  
> **综合评分**: 3.3/5（≥3.0，有条件采纳）

---

## 修订记录

| 版本 | 日期 | 修订内容 | 修订依据 |
|------|------|---------|---------|
| v1.0 | 2026-06-05 | 初始评审报告 | 代码审计 |
| **v1.1** | 2026-06-05 | **1. 功能联动脉入后端驱动模式（替代前端硬编码兜底）**<br>**2. 取消 Mock 模式和 Action Cards 前端兜底**<br>**3. 增加 HTML 预览前置要求**<br>**4. 调整工作量评估（增加 Phase 3 质量门禁）**<br>**5. 澄清后端状态（Phase 10 已就绪）** | 专家评审报告（架构×前端×后端×产品 4维度） |

---

## 一、报告摘要

| # | 问题 | 严重级别 | 影响范围 | 状态 |
|---|------|---------|---------|------|
| 1 | **布局缺陷**: AI Copilot 顶到视口顶部（遮挡 Header），左侧画布被遮挡，无抽拉效果 | 🔴 P0 | 所有页面 | 待修复 |
| 2 | **功能联动缺失**: 仅 6/20+ 页面注入 Copilot 上下文；无页面欢迎语；QuickActions 全局硬编码；Action Cards 纯后端驱动但失败时无兜底 | 🔴 P0 | 核心产品体验 | 待修复 |

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

#### 方案 A：Flex 布局改造（推荐，已获专家评审采纳）

将 `AICopilotPanel` 从 `fixed` 改为文档流内的 `flex` 子项，通过 CSS Flex + transition 实现抽拉效果。

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
        transition-all duration-300 ease-in-out">
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
   - 右侧添加 Copilot 展开/收起按钮（使用设计系统 `--bg-ai-glow` hover 态）
   - 按钮状态与 `isOpen` 联动

### 2.6 HTML 预览前置要求（专家评审新增）

根据通用提示词 §5，全局布局变更必须通过 HTML 预览审核：

1. **生成 HTML 预览**：`apps/frontend/demo/page-preview/copilot-layout.html`
2. **自检查清单**：
   - □ Mode C 合规：无业务按钮
   - □ 颜色合规：仅使用设计系统 Token（`#FFFFFF`, `#1F1F1F`, `#7C3AED`）
   - □ 布局合规：三栏布局（IconNav 48px | Canvas | Copilot 320px）
   - □ 交互合规：抽拉动画平滑，Header 始终完整可见
3. **提交审核**：将 HTML 文件路径告知用户，等待审核通过
4. **审核通过后**：方可同步到 React 代码

---

## 三、问题二：AI Copilot 功能联动与 LLM 驱动能力缺失（P0）

### 3.1 现状全景分析

#### 3.1.1 页面上下文覆盖率

| 页面 | 路由 | Copilot 上下文注入 | Action Cards | 状态 |
|------|------|-------------------|-------------|------|
| 工作台 | `/` | ✅ `useDashboardContext` | ✅ 后端获取 | 后端已就绪 |
| 审核发布列表 | `/review` | ✅ 手动注入 | ✅ 后端获取 | 后端已就绪 |
| 审核发布详情 | `/review/:taskId` | ✅ 手动注入 | ✅ 后端获取 | 后端已就绪 |
| 实验室 | `/lab` | ✅ 手动注入 | ❌ 无 | 仅上下文 |
| 关键词库 | `/keywords` | ✅ 手动注入 | ✅ 前端硬编码 | 需接入后端 |
| 模板库 | `/templates` | ✅ 手动注入 | ✅ 前端硬编码 | 需接入后端 |
| 内容生产 | `/generate` | ❌ **无** | ❌ 无 | **完全缺失** |
| 内容生产创建 | `/generate/create` | ❌ **无** | ❌ 无 | **完全缺失** |
| 编辑器 | `/generate/editor/:taskId` | ❌ **无** | ❌ 无 | **完全缺失** |
| 数据报表 | `/analytics` | ❌ **无** | ❌ 无 | **完全缺失** |
| 账号矩阵 | `/accounts` | ❌ **无** | ❌ 无 | **完全缺失** |
| 素材库 | `/assets` | ❌ **无** | ❌ 无 | **完全缺失** |
| Agent 舰队 | `/agents` | ❌ **无** | ❌ 无 | **完全缺失** |
| 模型中心 | `/models` | ❌ **无** | ❌ 无 | **完全缺失** |
| 设置 | `/settings` | ❌ **无** | ❌ 无 | **完全缺失** |
| 工作流 | `/workflows` | ❌ **无** | ❌ 无 | **完全缺失** |
| 平台规则 | `/rules` | ❌ **无** | ❌ 无 | **完全缺失** |
| 实验室其他能力 | `/lab/*` | ⚠️ 仅基础 | ❌ 无 | 不完整 |

**覆盖率**: 6/18 页面（33%），严重不达标。

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
- 无上下文感知的操作建议
- `QuickActionBar` 快捷动作是全局硬编码的，不随页面变化

#### 3.1.3 LLM 连接状态（Phase 10 已澄清）

> **【v1.1 修订】** 原评审报告判断「后端未启动」有误。经需求方澄清：当前处于 **Phase 10**，后端 Copilot 网关已就绪，`localhost:8001 ECONNREFUSED` 为开发环境配置问题，非后端缺失。

**SSE 连接配置**（`useSSEStream.ts`）：

```ts
export function useSSEStream(endpoint = '/api/v1/ai/conversations/stream')
```

**Phase 10 后端已就绪 API**：

| API | 状态 | 说明 |
|-----|------|------|
| `POST /api/ai/copilot/context` | ✅ 已就绪 | 上下文上报 |
| `GET /api/ai/copilot/action-cards` | ✅ 已就绪 | Action Cards 获取 |
| `POST /api/ai/copilot/execute` | ✅ 已就绪 | 通用 Action 执行 |
| `WS /ws/copilot` | ✅ 已就绪 | 实时推送通道 |
| `POST /api/v1/ai/conversations/stream` | ✅ 已就绪 | SSE 流式对话 |

**开发环境配置**：
- 前端通过 Vite Proxy 连接真实后端
- 不再启用 Mock 模式（需求方明确使用真实 LLM）

### 3.2 具体缺陷

#### 缺陷 A：页面上下文覆盖率严重不足（18 页面仅 6 个注入）

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

#### 缺陷 D：Action Cards 后端驱动但前端无降级

**Dashboard 的 Action Cards 获取**（`useDashboardContext.ts`）：
```ts
apiClient<{ cards: unknown[] }>("/api/ai/copilot/action-cards?page=/")
  .then((res) => { ... setPageActionCards(cards) })
  .catch(() => { setPageActionCards([]) }) // ← 失败时直接清空
```

**问题**：
- 后端失败时，Action Cards 直接为空
- 当前代码中没有接入后端 Copilot 网关的统一方式
- 各页面各自实现，标准不统一

### 3.3 根因分析

```
架构设计缺失
  ├── 无统一 Copilot 上下文注入机制
  │     └── 每个页面手动注入 → 遗漏率高（18 页面仅 6 个）
  │
  ├── 无页面状态 → 欢迎语/快捷动作/Action Cards 的映射层
  │     └── MessageHistory / QuickActionBar 全局硬编码
  │     └── 工作区按钮已移除（Mode C），但 Copilot Action Cards 未补齐 → 双盲状态
  │
  └── 前端未统一接入后端 Copilot 网关
        ├── 各页面各自调用 API，无统一 Hook
        ├── 欢迎语/快捷动作/Action Cards 应来自后端，而非前端硬编码
        └── 后端已就绪（Phase 10），前端未及时接入
```

### 3.4 修复方案（v1.1 修订版，接入后端驱动模式）

#### 3.4.1 统一 Copilot 上下文注入机制（P0）

**【v1.1 修订】** 原方案建议前端硬编码 `PAGE_CONFIG` 映射。经专家评审，修正为 **统一 Hook 调用后端 Copilot 上下文网关**。

```tsx
// hooks/useCopilotPageSync.ts
import { useLocation } from 'react-router-dom'
import { useEffect } from 'react'
import { useAICopilotStore } from '../stores/aiCopilotStore'
import { apiClient } from '../lib/api'

export function useCopilotPageSync() {
  const location = useLocation()
  const { setContext, setWelcomeMessage, setQuickActions, setPageActionCards, setPageActionHandler } = useAICopilotStore()

  useEffect(() => {
    const page = location.pathname

    // 1. 上报上下文到后端
    apiClient.post('/api/ai/copilot/context', {
      page,
      page_title: document.title,
      timestamp: new Date().toISOString(),
    }).catch(() => { /* 静默失败，不影响页面功能 */ })

    // 2. 设置基础上下文（前端本地）
    setContext({ page })

    // 3. 获取后端推荐的 Action Cards
    apiClient<{ data: { cards: PageActionCard[], ai_insights: string[], suggested_actions: string[] } }>(
      `/api/ai/copilot/action-cards?page=${encodeURIComponent(page)}`
    )
      .then((res) => {
        setPageActionCards(res.data.cards || [])
        setWelcomeMessage(res.data.ai_insights?.[0] || null)
        setQuickActions(res.data.suggested_actions || [])
      })
      .catch(() => {
        // 后端失败时保留空状态，不硬编码兜底
        setPageActionCards([])
        setWelcomeMessage(null)
        setQuickActions([])
      })

    // Cleanup: 切换页面时清空旧状态
    return () => {
      setPageActionCards([])
      setWelcomeMessage(null)
      setQuickActions([])
    }
  }, [location.pathname])
}
```

**接入位置**：在 `WorkspaceLayout.tsx` 或 `AppRoutes.tsx` 中全局挂载，一次性覆盖全部路由。

**覆盖页面**：全部 18+ 页面一次性覆盖。

#### 3.4.2 欢迎语动态生成层（P0）

**【v1.1 修订】** 欢迎语不再前端硬编码，而是从后端 `action-cards` 接口的 `ai_insights` 字段获取。

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
          <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center mx-auto">
            <Bot className="w-5 h-5 text-primary" />
          </div>
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

**【v1.1 修订】** `quickActions` 从全局硬编码改为从后端 `suggested_actions` 字段动态获取，在 `useCopilotPageSync` 中同步更新。

#### 3.4.4 Action Cards 统一接入后端（P0）

**【v1.1 修订】** 取消前端硬编码兜底方案。Action Cards 统一由后端 `GET /api/ai/copilot/action-cards` 驱动。

前端职责：
1. 页面切换时上报上下文（`POST /api/ai/copilot/context`）
2. 获取并渲染后端返回的 Action Cards（`GET /api/ai/copilot/action-cards`）
3. 用户点击 Action Card 后，调用后端执行网关（`POST /api/ai/copilot/execute`）
4. 处理后端返回的 `copilot_followup` 字段，展示下一步建议

#### 3.4.5 工作区功能按钮 → Copilot Action Cards 联动映射（P0）

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

1. **选中即触发**：用户在工作区点击卡片/行/元素后，Copilot 立即感知并推送相关 Action Cards（通过 `setContext({ selectedItems, selectedContent })` + 重新调用 `action-cards` 接口）
2. **状态流转**：Action Card 执行后，后端通过 `copilot_followup` 推送下一步建议
3. **快捷动作联动**：QuickActionBar 根据当前选中的对象动态更新（后端 `suggested_actions` 字段驱动）

**实现检查清单**：

- [ ] 每个页面的工作区按钮已移除（Mode C 合规）
- [ ] 每个页面在 Copilot 中提供至少 2 个默认 Action Cards（后端驱动）
- [ ] 选中工作区元素后，Copilot 上下文更新并推送相关 Cards
- [ ] Action Card 执行后，后端推送 `copilot_followup` 下一步建议

### 3.5 实现优先级（v1.1 修订版）

| 优先级 | 任务 | 影响 | 工作量 | 依赖 |
|--------|------|------|--------|------|
| P0 | Flex 布局改造 | 解决遮挡问题 | 1天 | 无 |
| P0 | HTML 预览审核 | 质量门禁 | 0.5天 | 布局改造 |
| P0 | 统一 Copilot 上下文注入 Hook | 解决 12 个页面无上下文问题 | 1天 | 后端网关已就绪 |
| P0 | 接入后端 `action-cards` 接口 | Action Cards 动态化 | 1天 | 后端网关已就绪 |
| P0 | 欢迎语/快捷动作接入后端数据 | 提升用户体验 | 0.5天 | action-cards 接口 |
| P1 | 各页面移除手动注入（改统一 Hook） | 代码简化 | 1天 | 统一注入 Hook |
| P1 | 工作区按钮→Action Cards 映射补全 | Mode C 合规 | 2天 | 后端接口 |
| P2 | WebSocket 实时推送 | 实时 Card 推送 | 2天 | 后端 WS 通道 |

---

## 四、综合评估与建议

### 4.1 两项问题的关联性

布局问题与功能联动问题并非孤立：

- **布局修复是功能联动的先决条件**：如果 Copilot 面板遮挡画布，即使用户能与 Copilot 对话，也无法看到 Copilot 建议操作后的页面变化。
- **功能联动是布局的价值所在**：如果 Copilot 不能根据页面提供建议，面板只是一个空壳，布局再精美也无意义。

### 4.2 推荐实施路径（v1.1 修订版）

```
Phase 1（2天）— 布局修复 + 统一注入基础
├── Flex布局改造（WorkspaceLayout + AICopilotPanel + Header）
├── HTML预览生成与审核
├── useCopilotPageSync Hook（调用后端 context + action-cards API）
└── aiCopilotStore 扩展（welcomeMessage / quickActions 动态状态）

Phase 2（3天）— 功能联动 + 后端驱动
├── 各页面移除手动注入（改统一 Hook）
├── 欢迎语/快捷动作接入后端数据
├── 工作区按钮→Copilot Action Cards 映射补全
└── 后端 API 联调（context / action-cards / execute）

Phase 3（2天）— 质量门禁 + 优化
├── 18+页面上下文覆盖率验证
├── E2E测试（布局+功能联动）
├── 文档更新（数据词典 + 变更记录 + PRD偏差报告）
└── TypeScript类型检查 + Lint + 构建通过
```

### 4.3 质量门禁

- [ ] 布局修复后，所有页面在 Copilot 展开/收起时，Main Canvas 内容完整可见
- [ ] 布局修复后，Header 不被 Copilot 遮挡
- [ ] 功能修复后，18+ 页面均有 Copilot 上下文注入（通过统一 Hook）
- [ ] 功能修复后，欢迎语和快捷动作随页面变化（后端驱动）
- [ ] 功能修复后，每个页面有后端提供的默认 Action Cards
- [ ] HTML 预览审核通过
- [ ] TypeScript 类型检查 0 errors
- [ ] 构建通过

---

## 五、附录：代码审计清单

### 5.1 需修改的文件

| # | 文件 | 问题 | 修改类型 |
|---|------|------|---------|
| 1 | `WorkspaceLayout.tsx` | 布局结构 | 重构 |
| 2 | `AICopilotPanel.tsx` | 移除 fixed 定位 | 重构 |
| 3 | `Header.tsx` | 添加 Copilot 切换按钮 | 新增 |
| 4 | `App.tsx` / `AppRoutes.tsx` | 挂载统一上下文注入 Hook | 新增 |
| 5 | `aiCopilotStore.ts` | 增加 welcomeMessage / quickActions 动态化 | 扩展 |
| 6 | `MessageHistory.tsx` | 欢迎语动态渲染 | 修改 |
| 7 | `QuickActionBar.tsx` | 从 store 读取动态 actions | 修改 |
| 8 | `useSSEStream.ts` | 无需修改（直接对接真实后端） | — |
| 9 | `DashboardPage.tsx` | 移除手动 useDashboardContext（改统一注入） | 简化 |
| 10 | `ReviewPublishCenterPage.tsx` | 移除手动 Copilot 注入（改统一注入） | 简化 |
| 11 | `ReviewPublishDetailPage.tsx` | 移除手动 Copilot 注入（改统一注入） | 简化 |
| 12 | `LabPage.tsx` | 移除手动 Copilot 注入（改统一注入） | 简化 |
| 13 | `PlaygroundPage.tsx` | 移除手动 Copilot 注入（改统一注入） | 简化 |
| 14 | `KeywordLibraryPage.tsx` | 移除手动 Copilot 注入（改统一注入） | 简化 |
| 15 | `TemplateLibraryPage.tsx` | 移除手动 Copilot 注入（改统一注入） | 简化 |
| 16 | `TaskHubPage.tsx` / `TaskHubCreatePage.tsx` / `ContentForgePage.tsx` | 新增 Copilot 注入 | 新增 |
| 17 | `DataAnalystPage.tsx` / `AccountPoolPage.tsx` / `AssetPoolPage.tsx` | 新增 Copilot 注入 | 新增 |
| 18 | `AgentOrchestraPage.tsx` / `LlmCockpitPage.tsx` | 新增 Copilot 注入 | 新增 |
| 19 | `SettingsPage.tsx` / `PlatformRulesPage.tsx` / `ProxyConfigPage.tsx` | 新增 Copilot 注入 | 新增 |

### 5.2 新增文件

| 文件 | 用途 |
|------|------|
| `hooks/useCopilotPageSync.ts` | 统一页面上下文同步 Hook（调用后端 API） |
| `demo/page-preview/copilot-layout.html` | HTML 预览审核文件 |

### 5.3 取消的文件（v1.1 不再需）

| 文件 | 原用途 | 取消理由 |
|------|--------|---------|
| `lib/copilotPageConfig.ts` | 前端硬编码页面配置 | 改为后端驱动 |
| `lib/mockSSE.ts` | Mock 模式 SSE 模拟 | 需求方明确使用真实 LLM |

---

## 六、专家评审意见摘要

> 详见：`docs/变更记录_v4.0/2026-06-05/AI_Copilot布局与功能修复_专家评审报告.md`

| 维度 | 评分 | 核心意见 |
|------|------|---------|
| 架构 | 3.3/5 | 布局方案直接采纳；功能联动脉入后端驱动模式，不前端硬编码 |
| 前端 | 3.5/5 | Flex改造技术可行；欢迎语/快捷动作/Action Cards应走后端数据 |
| 后端 | 3.0/5 | 后端Copilot网关已就绪（Phase 10）；原报告误判为未就绪 |
| 产品 | 3.5/5 | 问题识别精准；映射矩阵与设计规范v2.0 §八完全一致 |
| **综合** | **3.3/5** | **≥3.0，有条件采纳** |

** unanimously 共识**：
1. 布局修复方案（Flex改造）直接采纳
2. 功能联动脉入后端驱动模式（替代前端硬编码兜底）
3. Mock模式取消，直接对接真实后端
4. 工作区按钮→Copilot Action Cards映射是Mode C核心要求

---

*评审人: Kimi Code CLI*  
*评审日期: 2026-06-05*  
*修订日期: 2026-06-05*  
*版本: v1.1（评审后修订版：接入后端驱动模式 / 取消Mock / 增加HTML预览要求）*
