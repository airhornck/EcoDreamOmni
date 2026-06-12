# Phase 6 变更记录 — 前端层改造（AI Copilot + 实验室 + Inline AI + Agent Flow）

**日期**: 2026-06-03
**Phase**: Phase 6（前端层改造）
**任务**: P6-1 ~ P6-6
**状态**: 已完成

---

## 变更摘要

### P6-1: 全局布局改造（Persistent Three-Panel）

- **新建** `src/components/layout/IconNav.tsx`：48px 固定左侧图标导航（9 个核心页面入口）
- **新建** `src/components/layout/WorkspaceLayout.tsx`：Three-Panel 布局（IconNav 48px + MainCanvas 自适应 + AICopilotPanel 320px）
- **新建** `src/components/ai-copilot/AICopilotPanel.tsx`：P6-1 阶段为占位组件，P6-2 替换为完整实现
- **改造** `src/App.tsx`：新增 `LayoutWrapper`，通过 `localStorage` Feature Flag（`v4_workspace_layout`）切换 AppLayout / WorkspaceLayout，渐进式改造不破坏现有页面

### P6-2: AI Copilot 面板

- **新建** `src/stores/aiCopilotStore.ts`：Zustand store，管理会话状态 / 消息 / Action Cards / 上下文 / 快捷动作
- **新建** `src/hooks/useSSEStream.ts`：SSE 流式响应 hook，支持发送消息 / 接收流式数据 / 解析 Action Card / 中断 / 清空
- **新建** `src/components/ai-copilot/ContextBar.tsx`：上下文条，展示 currentPage / selectedContentId / taskId，支持移除
- **新建** `src/components/ai-copilot/MessageHistory.tsx`：对话历史，自动滚动到底部，用户/助手消息区分样式
- **新建** `src/components/ai-copilot/ActionCardStack.tsx`：Action Card 堆栈，支持 DIFF / CONFIRM / MULTI_SELECT / INFO 四种类型，一键应用/忽略
- **新建** `src/components/ai-copilot/QuickActionBar.tsx`：快捷动作区，预设 4 个常用指令
- **新建** `src/components/ai-copilot/InputBox.tsx`：输入框，支持多行文本 / Enter 发送 / Shift+Enter 换行 / 停止生成按钮
- **替换** `AICopilotPanel.tsx`：整合以上子组件，支持面板展开/收起

### P6-3: 实验室 页面

- **新建** `src/stores/playgroundStore.ts`：Zustand store，管理爆款输入 / 解析结果 / 模板 / 变量 / 生成内容
- **新建** `src/pages/LabPage.tsx`：主页面，6 区域布局（爆款输入全宽 + 3 列工作区 + 底部操作栏）
- **新建** `src/components/playground/ViralInputZone.tsx`：爆款输入区，支持链接粘贴 / 截图上传 / 文本粘贴，Mock 解析 API
- **新建** `src/components/playground/StructureParseZone.tsx`：结构解析展示，Hook 模式 / 正文结构 / CTA 模式 / 语气 / 关键词
- **新建** `src/components/playground/TemplateGenZone.tsx`：模板生成区，下拉选择预设模板，展示 Prompt 模板原文
- **新建** `src/components/playground/VariableReplaceZone.tsx`：变量替换区，动态表单，实时修改变量值
- **新建** `src/components/playground/DiffPreviewZone.tsx`：对比预览区，展示生成标题 / 正文 / 话题标签
- **新建** `src/components/playground/ActionBar.tsx`：底部操作栏，一键生成 / 保存模板 / 应用到向导
- **API 契约补充**：`docs/契约与数据/01-API接口契约.md` §6.2 新增 实验室 端点完整定义

### P6-4: Inline AI 建议

- **新建** `src/stores/inlineAIStore.ts`：Zustand store，管理建议列表 / 已忽略 ID / 选中目标
- **新建** `src/components/inline-ai/InlineSuggestionCard.tsx`：悬浮建议卡片，5 种类型（OPTIMIZE/ADD/REMOVE/WARNING/INFO），Diff 预览，应用/忽略按钮

### P6-5: Agent 流组件

- **新建** `src/stores/agentFlowStore.ts`：Zustand store，管理 Pipeline 执行 / 节点状态 / WebSocket 连接状态
- **新建** `src/components/agent-flow/AgentFlowBar.tsx`：底部内嵌 Agent 执行链路可视化，支持展开/收起详情，WebSocket 实时更新，节点状态色点 + 进度统计

### P6-6: 前端路由更新

- **改造** `src/App.tsx`：新增 `/playground` 路由（lazy-loaded）
- **改造** `src/components/layout/Sidebar.tsx`：内容生产分组新增 实验室 导航入口
- **改造** `src/components/layout/IconNav.tsx`：新增 实验室 图标入口（FlaskConical）

---

## 测试覆盖

| 测试文件 | 测试数 | 状态 |
|----------|--------|------|
| `src/components/layout/__tests__/WorkspaceLayout.test.tsx` | 2 | ✅ 通过 |
| `src/components/layout/__tests__/IconNav.test.tsx` | 3 | ✅ 通过 |
| `src/components/ai-copilot/__tests__/AICopilotPanel.test.tsx` | 3 | ✅ 通过 |
| `src/components/ai-copilot/__tests__/InputBox.test.tsx` | 4 | ✅ 通过 |
| `src/components/playground/__tests__/PlaygroundFlow.test.tsx` | 3 | ✅ 通过 |
| `src/components/inline-ai/__tests__/InlineSuggestionCard.test.tsx` | 4 | ✅ 通过 |
| `src/components/agent-flow/__tests__/AgentFlowBar.test.tsx` | 3 | ✅ 通过 |
| `src/App.test.tsx` | 1 | ✅ 通过 |

**总计**: 新增测试 23 个，全部通过。

---

## 质量门禁

| 门禁项 | 结果 |
|--------|------|
| 前端测试通过 | ✅ 23/23 |
| 前端 Lint 0 errors（新代码） | ✅ 通过 |
| 前端类型检查 0 errors（新代码） | ✅ 通过 |
| 契约文档已同步 | ✅ 01-API接口契约.md §6.2 已补充 |

**已知限制**:
- 前端全局 lint 存在 155 处历史错误（现有 stores 中 `any` 类型），不影响新代码
- 实验室 API 当前为前端 mock 实现，后端正式实现待 Phase 2
- WorkspaceLayout 通过 Feature Flag（`localStorage v4_workspace_layout`）切换，默认保持原 AppLayout

---

## 关联文档更新

- `docs/v4.0_开发Checklist.md` — Phase 6 逐项打勾
- `docs/契约与数据/01-API接口契约.md` — 新增 §6.2 实验室 端点
- 本文档 — 新增
