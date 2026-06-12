# EcoDream Omni v4.0 — Copilot 与工作区交互模式规范 v1.0

> **状态**: 草案（待架构评审）  
> **日期**: 2026-06-04  
> **提出者**: 前端开发（审核发布页面重构过程）  
> **评审人**: 待产品负责人、设计负责人、技术负责人、AI 架构师  
> **影响范围**: 全局 10 页面 + AI Copilot 面板 + 后端 API  

---

## 一、问题定义

### 1.1 当前模式的缺陷

在 v2.7.x → v4.0 迁移过程中，我们遇到了一个根本性的交互设计冲突：

| 冲突点 | 传统模式表现 | AI-Native 期望 |
|--------|-------------|----------------|
| 审核决策 | 详情页右侧放置「通过/打回/驳回」按钮 | 用户期望 AI 给出建议后再决策 |
| 封面生成 | 弹框内提供「AI 生成」Tab，用户输入 Prompt 直接生成 | 缺乏 Copilot 上下文，生成质量低 |
| 内容优化 | 工作区 Inline 建议浮层 | 无法追溯历史建议、无法对比多版本 |
| 批量操作 | 列表页勾选后顶部批量按钮 | Copilot 无法感知批量意图 |

**核心矛盾**: 工作区按钮是「命令式」交互（用户直接操作），而 AI Copilot 是「对话式」交互（用户与 AI 协商）。两者并行时，用户认知负担重，且 AI 无法获得操作上下文。

### 1.2 新范式提案：Copilot-Driven Workflow

> **定义**: 对于特定高价值操作，将发起入口从「工作区按钮」迁移至「Copilot Action Card」，工作区仅负责展示内容和预览效果，Copilot 负责驱动操作流。

**类比**: 飞机驾驶舱中，飞行员（用户）通过操纵杆和仪表（工作区）观察状态，但通过无线电（Copilot）与塔台（AI）协商航线调整。重大决策（起飞/降落/转向）需要塔台确认。

---

## 二、三种交互模式定义

### 2.1 Mode A: Direct（直接操作）— 工作区按钮为主

**适用场景**: 低认知负担、高频、无需 AI 判断的操作

**特征**:
- 工作区提供明确按钮
- Copilot 仅作被动辅助（展示建议，不拦截操作）
- 用户点击即执行，无需二次确认

**示例页面/功能**:
| 页面 | 功能 | 按钮位置 | Copilot 角色 |
|------|------|---------|-------------|
| 工作台 | 新建任务 | PageHeader `[+ 新建任务]` | 点击后 Copilot 自动展开询问主题 |
| 内容生产 | 保存草稿 | 编辑器底部 `[保存]` | 保存成功后 Copilot 提示「要我帮你做合规检查吗？」 |
| 账号矩阵 | 添加账号 | 页面 `[+ 添加账号]` | Copilot 记录新增账号，提示健康度检查 |
| 素材库 | 上传图片 | 拖拽上传区 | 上传后 Copilot 提示「需要 AI 打标签吗？」 |
| 设置 | 修改密码 | 表单 `[确认修改]` | 无 Copilot 介入 |

### 2.2 Mode B: Copilot-Driven（副驾驶驱动）— Copilot Action Card 为主

**适用场景**: 高价值、需要 AI 判断、有状态流转、需要多轮协商的操作

**特征**:
- **工作区移除操作按钮**，仅保留展示/预览/编辑能力
- Copilot 主动提供 **Action Card**（带可执行按钮的卡片）
- 用户通过 Copilot 交互完成操作
- 操作结果实时同步到工作区（预览区更新）
- 支持多轮协商（不满意 → 重新生成/修改条件）

**示例页面/功能**:
| 页面 | 功能 | 工作区变化 | Copilot Action Card |
|------|------|-----------|-------------------|
| **审核发布** | 审核决策 | 右侧栏移除「通过/打回/驳回」按钮，仅保留预览 | 提供三按钮 Action Card，含 AI 建议文案 |
| **审核发布** | 生成封面 | 弹框移除「AI 生成」Tab | 提供「生成封面」Action Card，含提示词输入框 |
| 内容生产 | 重新生成内容 | 编辑器移除「重新生成」按钮 | Copilot 提供「重新生成」Card，可选择风格/长度 |
| 数据报表 | 异常诊断 | 图表仅展示异常标记 | Copilot 主动提供「分析下降原因」Card |
| 账号矩阵 | 健康度修复 | 账号卡片无修复按钮 | Copilot 提供「生成发布计划」Card |

### 2.3 Mode C: Hybrid（混合模式）— 工作区 + Copilot 均可发起

**适用场景**: 中频、用户习惯已养成、需要渐进迁移的操作

**特征**:
- 工作区保留快捷入口（次要）
- Copilot 提供增强版入口（主要）
- 两侧操作结果同步

**示例页面/功能**:
| 页面 | 工作区入口 | Copilot 入口 | 备注 |
|------|-----------|-------------|------|
| 内容生产 | 编辑器内 `[AI 优化]` 浮层 | Copilot 「优化标题」Card | 浮层作为快捷方式保留 |
| 工作台 | ContentCard 上 `[一键发布]` | Copilot 「批量发布」Card | 批量场景走 Copilot |
| 数据报表 | 指标卡片 `[导出报表]` | Copilot 「生成 AI 战报」Card | 导出走工作区，战报走 Copilot |

---

## 三、Copilot Action Card 规范

### 3.1 Action Card 类型定义

```typescript
interface ActionCard {
  id: string
  type: 'decision' | 'generation' | 'optimization' | 'batch' | 'info'
  title: string           // Card 标题
  description?: string    // 说明文案（AI 建议）
  
  // 输入区（可选）
  inputs?: Array<{
    name: string
    label: string
    type: 'text' | 'select' | 'textarea' | 'toggle'
    placeholder?: string
    options?: Array<{ label: string; value: string }>
    defaultValue?: unknown
  }>
  
  // 操作按钮（至少一个）
  actions: Array<{
    id: string
    label: string
    variant: 'primary' | 'secondary' | 'danger' | 'ghost'
    icon?: string
    // 执行后行为
    behavior: {
      type: 'execute' | 'expand' | 'navigate' | 'dismiss'
      // execute: 调用 API
      api?: { method: string; endpoint: string; payload: Record<string, unknown> }
      // expand: 展开更多内容（如生成结果）
      expandContent?: string
      // navigate: 跳转页面
      route?: string
    }
  }>
  
  // 结果展示区（执行后显示）
  result?: {
    type: 'diff' | 'preview' | 'list' | 'chart'
    content: unknown
  }
  
  // 状态
  state: 'pending' | 'executing' | 'completed' | 'failed'
}
```

### 3.2 状态流转图

```
┌─────────────┐     用户进入页面      ┌─────────────┐
│  Copilot    │ ────────────────────→ │  Context    │
│   Idle      │                       │  Analysis   │
└─────────────┘                       └──────┬──────┘
                                             │
                                             ▼
                                    ┌─────────────┐
                                    │  Should     │
                                    │  Suggest?   │
                                    └──────┬──────┘
                                           │
                      ┌────────────────────┼────────────────────┐
                      │ 否                  │ 是                 │
                      ▼                    ▼                    ▼
               ┌─────────────┐     ┌─────────────┐      ┌─────────────┐
               │  等待用户   │     │  Push       │      │  Push       │
               │  输入/选择  │     │  ActionCard │      │  InlineTip  │
               └─────────────┘     └──────┬──────┘      └─────────────┘
                                           │
                      ┌────────────────────┼────────────────────┐
                      │ 用户点击 Action    │ 用户修改条件        │ 用户忽略
                      ▼                    ▼                    ▼
               ┌─────────────┐     ┌─────────────┐      ┌─────────────┐
               │  Executing  │     │  Update     │      │  Dismiss    │
               │  (loading)  │     │  Inputs     │      │  (fade out) │
               └──────┬──────┘     └─────────────┘      └─────────────┘
                      │
        ┌─────────────┼─────────────┐
        │ 成功         │ 失败         │ 需要确认
        ▼             ▼             ▼
 ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
 │  Show Result│ │  Show Error │ │ ConfirmCard │
 │  (diff/     │ │  + Retry    │ │ (是/否)     │
 │  preview)   │ │  Button     │ │             │
 └──────┬──────┘ └─────────────┘ └─────────────┘
        │
        ▼
 ┌─────────────┐
 │  User:      │
 │  [应用]     │ ──→ 同步到工作区 + Toast 成功
 │  [再优化]   │ ──→ 回到 Executing（带反馈）
 │  [忽略]     │ ──→ Dismiss
 └─────────────┘
```

### 3.3 审核发布页面 Action Cards 详细设计

#### Card 1: ReviewDecisionCard（审核决策）

```yaml
type: decision
title: 审核决策
description: |
  合规分 96 分，质量分 88 分，L1-L4 全部通过。
  建议：直接通过，预计可获得 25-60 互动量。
inputs: []
actions:
  - id: approve
    label: ✅ 审核通过
    variant: primary
    behavior:
      type: execute
      api:
        method: POST
        endpoint: /api/human-in-the-loop/tasks/{taskId}/approve
        payload: {}
  - id: revise
    label: 🔄 打回修改
    variant: secondary
    behavior:
      type: expand
      expandContent: revise_reason_input  # 展开原因输入框
  - id: reject
    label: ❌ 驳回
    variant: ghost
    behavior:
      type: expand
      expandContent: reject_reason_input
```

**工作区同步行为**:
- 通过后：工作区预览区显示「已通过」Badge + 绿色边框闪烁一次
- 打回后：工作区标题栏显示「已打回」状态，编辑器保持打开
- 驳回后：工作区淡出，自动返回列表页

#### Card 2: CoverGenerateCard（生成封面）

```yaml
type: generation
title: 🎨 生成封面
description: 让 AI 根据内容主题生成封面图
inputs:
  - name: prompt
    label: 描述
    type: textarea
    placeholder: 描述你想要的封面风格，例如：温馨可爱的橘猫在草地上
actions:
  - id: generate
    label: 生成封面
    variant: primary
    icon: sparkles
    behavior:
      type: execute
      api:
        method: POST
        endpoint: /api/ai/generate-cover
        payload:
          task_id: "{taskId}"
          prompt: "{inputs.prompt}"
          content_summary: "{autoExtracted}"
  - id: random
    label: 随机生成
    variant: ghost
    behavior:
      type: execute
      api:
        method: POST
        endpoint: /api/ai/generate-cover
        payload:
          task_id: "{taskId}"
          prompt: ""
          auto_prompt: true
```

**工作区同步行为**:
- 生成中：Copilot 显示「生成中...」进度，工作区封面区显示骨架屏
- 生成完成：Copilot 展示 2-4 张缩略图，用户点击「使用此图」
- 应用后：工作区封面区立即更新，Copilot 显示「封面已更新」确认

---

## 四、各页面交互模式评估

### 4.1 评估矩阵

| # | 页面 | 当前模式 | 建议模式 | 改动成本 | 优先级 | 备注 |
|---|------|---------|---------|---------|--------|------|
| 1 | **审核发布 /review** | Direct | **Copilot-Driven** | 中 | 🔴 P0 | **本次重构核心** |
| 2 | **内容生产 /generate** | Direct | **Hybrid → Copilot-Driven** | 高 | 🟡 P1 | 重新生成、AI 优化建议走 Copilot |
| 3 | **工作台 /** | Direct | Hybrid | 中 | 🟡 P1 | 批量操作走 Copilot，单卡片操作保留快捷入口 |
| 4 | **数据报表 /analytics** | Direct | **Copilot-Driven** | 中 | 🟢 P2 | 异常诊断、AI 战报走 Copilot |
| 5 | **账号矩阵 /accounts** | Direct | **Copilot-Driven** | 中 | 🟢 P2 | 健康度修复、发布计划走 Copilot |
| 6 | **Agent 舰队 /agents** | Direct | Hybrid | 低 | 🟢 P2 | 一键重启走 Copilot，日志查看保留 |
| 7 | **模型中心 /models** | Direct | Direct | 低 | ⚪ P3 | 成本预警走 Copilot 提示，操作保留 |
| 8 | **素材库 /assets** | Direct | Hybrid | 低 | ⚪ P3 | AI 打标签走 Copilot |
| 9 | **实验室 /lab** | Direct | Hybrid | 低 | ⚪ P3 | 爆款解析走 Copilot |
| 10 | **设置 /settings** | Direct | Direct | 无 | ⚪ P3 | 无需 Copilot 介入 |

### 4.2 改动时序建议

```
Phase 2 (当前) ──→ 审核发布全面 Copilot-Driven
Phase 3 ─────────→ 内容生产 Hybrid 改造（重新生成、AI 优化）
Phase 3 ─────────→ 工作台批量操作 Hybrid 改造
Phase 4 ─────────→ 数据报表、账号矩阵 Copilot-Driven
Phase 4 ─────────→ 其余页面 Hybrid 改造
```

---

## 五、技术实现规范

### 5.1 前端 Store 扩展

```typescript
// stores/aiCopilotStore.ts — 新增 Action Card 管理
interface CopilotActionCardState {
  activeCards: ActionCard[]
  executingCardId: string | null
  
  pushCard: (card: ActionCard) => void
  updateCard: (id: string, patch: Partial<ActionCard>) => void
  dismissCard: (id: string) => void
  executeAction: (cardId: string, actionId: string) => Promise<void>
}

// 页面级 Hook — 每个页面声明自己产生的 Action Cards
// pages/ReviewPublishDetailPage/hooks/useReviewCopilot.ts
export function useReviewCopilot(taskId: string, detail: ReviewDetail) {
  const { pushCard, dismissCard } = useAICopilotStore()
  
  useEffect(() => {
    // 进入详情页时，自动推送审核决策 Card
    if (detail.status === 'human_wait') {
      pushCard({
        id: `review-decision-${taskId}`,
        type: 'decision',
        title: '审核决策',
        description: generateReviewAdvice(detail),  // AI 生成建议文案
        actions: [
          { id: 'approve', label: '✅ 审核通过', variant: 'primary', ... },
          { id: 'revise', label: '🔄 打回修改', variant: 'secondary', ... },
          { id: 'reject', label: '❌ 驳回', variant: 'ghost', ... },
        ],
      })
    }
    
    // 推送封面生成 Card
    pushCard({
      id: `cover-gen-${taskId}`,
      type: 'generation',
      title: '🎨 生成封面',
      ...
    })
    
    return () => {
      dismissCard(`review-decision-${taskId}`)
      dismissCard(`cover-gen-${taskId}`)
    }
  }, [taskId, detail.status])
}
```

### 5.2 工作区 ↔ Copilot 通信协议

```typescript
// 事件总线（替代直接 prop drilling）
// lib/copilot-bridge.ts

interface CopilotBridgeEvent {
  type: 
    | 'WORKSPACE_CONTENT_SELECTED'   // 用户选中工作区内容
    | 'WORKSPACE_CONTENT_UPDATED'    // 工作区内容变更
    | 'COPILOT_ACTION_EXECUTED'      // Copilot 操作执行
    | 'COPILOT_RESULT_APPLIED'       // Copilot 结果应用到工作区
    | 'COPILOT_STREAM_CHUNK'         // SSE 流式输出
  payload: Record<string, unknown>
  source: 'workspace' | 'copilot'
  timestamp: number
}

// 示例：封面生成结果应用到工作区
// Copilot 侧
emitBridgeEvent({
  type: 'COPILOT_RESULT_APPLIED',
  payload: { field: 'cover_image_url', value: 'https://...', taskId: '123' },
  source: 'copilot',
})

// 工作区侧监听
onBridgeEvent('COPILOT_RESULT_APPLIED', (e) => {
  if (e.payload.field === 'cover_image_url') {
    setCoverImage(e.payload.value)  // 实时更新封面预览
    showToast('封面已更新')
  }
})
```

### 5.3 API 契约变更（前端视角）

详见配套文档《后端需求补充_审核发布_Copilot-Driven_2026-06-04.md》。

---

## 六、待决策事项（需评审会议确认）

| # | 议题 | 选项 A | 选项 B | 建议 |
|---|------|--------|--------|------|
| 1 | 审核决策按钮是否在工作区保留快捷入口？ | 完全移除（纯 Copilot-Driven） | 保留弱化入口（Hybrid） | **选项 A**，强制培养 Copilot 习惯 |
| 2 | Copilot 是否主动推送 Action Card？ | 是（进入页面自动推送） | 否（仅用户询问后推送） | **选项 A**，降低用户发现成本 |
| 3 | 封面生成失败后是否允许无限重试？ | 是 | 限流（最多 3 次/分钟） | **选项 B**，防止滥用 |
| 4 | 批量审核是否支持 Copilot 驱动？ | 是（选中多条后 Copilot 汇总建议） | 否（保留顶部批量按钮） | **选项 A**，作为 P1 后续迭代 |
| 5 | 其他页面（内容生产/工作台）是否立即跟进？ | 立即全部重构 | 仅审核发布先行验证 | **选项 B**，小步快跑，验证后再推广 |

---

## 七、附录：参考文档

- `04-全局设计规范_浅色主题_AI工作台.md` §5.3 Copilot 主动建议规则
- `02-AICopilot面板设计.md`（待创建）
- `01-API接口契约.md` §通用响应格式
- 本次重构产物: `demo/page-preview/review.html`

---

*文档版本: v1.0*  
*待评审日期: 2026-06-05*  
*评审通过后更新为 v1.1 并进入实施*
