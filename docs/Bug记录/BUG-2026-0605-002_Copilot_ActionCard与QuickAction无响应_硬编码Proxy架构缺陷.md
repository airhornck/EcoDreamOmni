# BUG-2026-0605-002：Copilot Action Card 与 Quick Action 点击无响应

> **发现日期**: 2026-06-05  
> **修复日期**: 2026-06-05（Phase 1）→ 2026-06-12（Phase 2 桥接完成）  
> **严重级别**: 🟠 P1 — 功能性缺陷（Copilot 核心交互不可用）  
> **影响范围**: 前端全局（所有页面）+ 后端 Copilot 网关  
> **修复者**: Kimi Code CLI  
> **关联评审报告**: `docs/评审报告/Copilot升级为MetaAgent_专家评审报告_v4.0.md`  
> **状态**: 🟡 Phase 1 修复中

---

## 一、现象描述

### Bug 1：Action Card 按钮点击无反应

在 AI Copilot 右侧面板中，随着页面切换动态出现的功能卡片（如 Dashboard 的"创建任务"、审核列表的"批量审核"），点击按钮后：
- 没有任何页面跳转
- 没有任何操作执行
- 控制台无报错

### Bug 2：Quick Action 点击无反应

在 AI Copilot 面板底部的"快捷动作"区域，点击预设动作（如"分析最近7天爆款趋势"）后：
- 消息发送到 LLM 流，但 LLM 只返回文本建议
- 没有触发任何实际操作（没有跳转、没有 API 调用）

---

## 二、复现条件

1. 启动前端（`vite dev` 或 Docker `5173`）+ 后端（`8000`）
2. 登录系统，进入任意页面（如 Dashboard `/` 或审核列表 `/review`）
3. 确保 AI Copilot 面板已打开（右侧 320px 面板）
4. 等待 Action Cards 加载（约 1-2 秒）
5. 点击任意 Action Card 的按钮 或 Quick Action 的 chip

**复现率**: 100%（Default Action Cards 均无法响应）

---

## 三、根因分析

### 3.1 直接原因

#### Bug 1 直接原因：pageActionHandler 未注册

| 页面 | 是否注册 handler | 状态 |
|------|----------------|------|
| Dashboard (`/`) | ❌ `useDashboardContext` 定义了 handler，但 `DashboardPage.tsx` 未调用 | 缺失 |
| 审核列表 (`/review`) | ❌ `ReviewPublishCenterPage` 之前 TS 修复时移除了 handler 注册 | 缺失 |
| 审核详情 (`/review/:id`) | ✅ `ReviewPublishDetailPage` 注册了 `handleCopilotAction` | 正常 |
| 模板库 (`/templates`) | ✅ `TemplateLibraryPage` 注册了 handler | 正常 |
| 关键词库 (`/keywords`) | ✅ `KeywordLibraryPage` 注册了 handler | 正常 |

当 `pageActionHandler === null` 时，`PageActionCardArea` 的 `onAction?.()` 返回 `undefined`，UI 无任何反馈。

#### Bug 2 直接原因：Quick Action 没有操作执行链路

```
QuickActionBar.onClick
    → AICopilotPanel.handleSend(actionText)
    → useSSEStream.sendStreamMessage(actionText)
    → POST /api/v1/ai/conversations/stream
    → LLM 返回文本建议
    → 仅渲染到 MessageHistory，不触发任何操作
```

Quick Action 当前只是"把预设文本发给 LLM 聊天"，没有 intent 解析 → 路由 → 执行的链路。

### 3.2 根本原因 — 架构层面

当前 Copilot 架构是**"硬编码 Proxy + 页面注入 Handler"**模式：

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│   前端页面      │      │   copilot.py    │      │   后端服务      │
│                 │      │                 │      │                 │
│ useEffect注册   │─────▶│ if page=="/"    │─────▶│ /api/human-in-  │
│ pageActionHandler│      │   返回cards     │      │ the-loop/...    │
│                 │      │                 │      │                 │
│                 │      │ if card_id==... │─────▶│ /api/ai/generate│
│                 │      │   调用endpoint  │      │ -cover          │
└─────────────────┘      └─────────────────┘      └─────────────────┘
```

**缺陷**：
1. 每新增一个页面，需同时改前端（注册 handler）+ 后端（`copilot.py` 硬编码卡片）
2. `execute_action()` 是 100+ 行的 `if/elif` 硬编码，只覆盖 6 个 endpoint
3. Default Action Cards（如"创建任务""前往审核"）没有 `api` 字段，后端 execute 不识别
4. Quick Actions 完全没有操作路由层

---

## 四、影响评估

| 维度 | 影响 | 说明 |
|------|------|------|
| 用户体验 | 🔴 高 | Copilot 核心交互（Action Cards + Quick Actions）完全不可用，用户只能看不能点 |
| 功能完整性 | 🟠 中 | Copilot 的"驱动工作流"能力失效，退化为纯聊天面板 |
| 数据安全 | 🟢 无 | 不涉及数据操作 |
| 业务连续性 | 🟢 无 | 核心内容生产/审核/发布流程独立运行，不受影响 |
| 核心架构 | 🟠 中 | 暴露 Copilot 架构的可扩展性缺陷，需升级为动态路由 |

---

## 五、修复方案

### 5.1 方案选择

采用专家评审报告推荐的 **方案 B（Copilot → MetaOrchestrator 桥接）**，分 Phase 1 + Phase 2 实施。

### 5.2 Phase 1 — 立即修复 + 基础设施（当前 Sprint）

#### 修改 1：前端页面补全 pageActionHandler 注册

- `ReviewPublishCenterPage.tsx`：补充 `setPageActionHandler`，处理"批量审核""AI 分析"卡片
- `DashboardPage.tsx`：调用 `useDashboardContext(navigate)`，激活 Dashboard handler

#### 修改 2：后端 Default Action Cards 补充 api 字段

- `copilot.py` `_build_default_page_cards()`：为所有 Default Cards 补充 `api` 字段，指向对应的后端 endpoint 或前端路由指令

#### 修改 3：Quick Action 增加 intent 路由

- 方案：在 `useCopilotPageSync.ts` 中，将 `suggested_actions` 映射为 `{action, target}` 结构
- 或在 `conversation.py` 的 LLM system prompt 中增加指令：如果用户消息匹配 Quick Action 关键词，返回 `{"action": "navigate", "target": "..."}`
- **Phase 1 简化方案**：前端 QuickActionBar 点击时，直接根据 action 文本匹配路由表，调用 `navigate()`

#### 修改 4：铺设 CapabilityRegistry 基础设施

- 新增 `src/services/capability_registry.py`
- 定义统一的注册接口：`register_capability(page, actions, handler)`
- 将现有页面的硬编码 handler 迁移到注册表（Phase 1 先定义接口，Phase 2 全面迁移）

#### 修改 5：统一 Agent 数据源

- `AgentOrchestra` 的 agent 定义迁移到 `AgentORM`（DB 持久化）
- 确保 Copilot 的 action-cards 可以从统一的 Agent 数据源获取

### 5.3 Phase 2 — Copilot → MetaOrchestrator 桥接（下一 Sprint）

- 新增 `POST /api/ai/copilot/agent` 接口
- Copilot 所有操作统一走 `MetaOrchestrator.orchestrate()`
- 删除 `copilot.py` 硬编码的 `if/elif execute` 逻辑
- 所有页面/Agent/Skill 注册到 `CapabilityRegistry`

### 5.4 修改文件清单

| 文件路径 | 修改类型 | 修改内容摘要 |
|----------|----------|--------------|
| `apps/frontend/src/pages/ReviewPublishCenterPage.tsx` | 修复 | 补充 `setPageActionHandler` 注册 |
| `apps/frontend/src/pages/DashboardPage.tsx` | 修复 | 调用 `useDashboardContext(navigate)` |
| `apps/frontend/src/hooks/useCopilotPageSync.ts` | 修复 | Quick Action 增加路由映射 |
| `apps/frontend/src/components/ai-copilot/QuickActionBar.tsx` | 修复 | 点击时根据 action 匹配路由 |
| `apps/backend/src/api/copilot.py` | 修复 | Default Cards 补充 `api` 字段 |
| `apps/backend/src/services/capability_registry.py` | 新增 | 统一能力注册表基础设施 |
| `apps/backend/src/services/agent_orchestra.py` | 重构 | Agent 定义迁移到 AgentORM |
| `apps/backend/src/models/agent_orm.py` | 扩展 | 支持 AgentOrchestra 的字段 |

---

## 六、验证步骤

- [ ] 访问 Dashboard `/`，点击"创建任务"卡片，跳转到 `/generate/create`
- [ ] 访问审核列表 `/review`，点击"批量审核"卡片，触发批量审核操作
- [ ] 访问审核详情 `/review/:id`，点击"审核通过"，触发 approve API
- [ ] 点击 Quick Action"分析最近7天爆款趋势"，跳转或触发对应操作
- [ ] 切换页面后，Action Cards 正确更新，旧页面的 handler 不再残留
- [ ] 前端 `tsc --noEmit` 0 errors
- [ ] 前端 `eslint .` 0 errors
- [ ] Docker Build 通过
- [ ] 架构红线审查通过（详见专家评审报告 §4）

---

## 七、预防措施

- [ ] CapabilityRegistry 注册接口需有 TypeScript 类型定义，防止类似字段缺失问题
- [ ] 新增页面时必须调用 `useCopilotContext(navigate)` 或注册 handler
- [ ] 工程纪律补充：Copilot Action Card 必须有对应的 handler 或 api 字段，否则 CI 报错
- [ ] 单元测试：每个页面的 Copilot handler 注册必须有测试覆盖

---

## 八、关联文档

- [x] `docs/文档总纲_v4.0.md` — Bug 记录已索引
- [x] `docs/评审报告/Copilot升级为MetaAgent_专家评审报告_v4.0.md` — 架构调整评审报告
- [ ] `docs/变更记录_v4.0/2026-06-05/` — Phase 1 变更记录（修复后补充）
- [ ] `docs/数据词典_v4.0/` — CapabilityRegistry 模型（Phase 1 实施中补充）
- [ ] `docs/契约与数据/01-API接口契约.md` — `/ai/copilot/agent` 契约（Phase 2 实施前补充）
