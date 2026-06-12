# PRD 偏差报告 v4.0

> **用途**: 记录 PRD v4.0 定义与代码实际实现之间的偏差，跟踪修复状态。  
> **更新日期**: 2026-06-05  
> **关联文档**: `EcoDream_Omni_PRD_v4_AI_Native_Architecture.md`

---

## 偏差记录表

| # | 偏差项 | PRD 章节 | PRD 预期行为 | 代码实际行为 | 严重级别 | 修复状态 | 修复日期 | 修复版本 |
|---|--------|---------|-------------|-------------|---------|---------|---------|---------|
| 1 | **AI Copilot 布局实现偏离** | §2531, §2542, §3655 | 右侧 320px 持久侧边栏，三栏布局（IconNav \| Canvas \| Copilot），Header 完整可见 | Copilot 使用 `position: fixed right-0 top-0`，遮挡 Header 和 Canvas 右侧 | 🔴 P0 | ✅ 已修复 | 2026-06-05 | v1.1 |
| 2 | **Copilot 上下文注入机制缺失** | §2654 | 所有页面均有 Copilot 上下文注入，Copilot 能感知当前页面 | 仅 6/18 页面手动注入，无统一机制 | 🔴 P0 | ✅ 已修复 | 2026-06-05 | v1.1 |
| 3 | **欢迎语全局硬编码** | §5.3 | 页面特定欢迎语（后端 `ai_insights` 驱动） | 所有页面统一显示 `"有什么可以帮你的？"` | 🟡 P1 | ✅ 已修复 | 2026-06-05 | v1.1 |
| 4 | **快捷动作全局硬编码** | §5.3 | 页面特定快捷动作（后端 `suggested_actions` 驱动） | 4 条固定动作在所有页面显示 | 🟡 P1 | ✅ 已修复 | 2026-06-05 | v1.1 |
| 5 | **Action Cards 前端硬编码** | §6.1 | 后端 `action-cards` 接口统一驱动 | 部分页面前端硬编码 Action Cards | 🟡 P1 | 🔄 迁移中 | — | — |
| 6 | **无抽拉动画** | §2542 | Copilot 展开/收起时 Canvas 宽度平滑过渡 | 无过渡动画，瞬间出现/消失 | 🟡 P1 | ✅ 已修复 | 2026-06-05 | v1.1 |

---

## 偏差 1：AI Copilot 布局实现偏离

**PRD 预期**（§2531, §2542, §3655）：
> "右侧AI Copilot" — 右侧320px持久侧边栏完全对齐2026年工业标准（Cursor/VS Code/Figma）。三栏布局：IconNav 48px | Bento Grid 主画布 | AI Copilot 320px。

**代码实际行为**：
- `AICopilotPanel.tsx` 使用 `position: fixed right-0 top-0 z-30 h-screen w-[320px]`
- 脱离文档流，导致：
  - Header 右侧被遮挡（`top-0` 覆盖 Header 区域）
  - Main Canvas 右侧内容被遮挡（`flex-1` 未减去 320px）
- 收起状态使用悬浮按钮 `fixed right-0 top-1/2`

**修复方案**：
- 改用 CSS Grid 布局：`grid-template-columns: 48px 1fr 320px`
- Header 独立顶行：`grid-row: 1; grid-column: 2 / 4`
- Copilot 仅在 Header 下方：`grid-row: 2; grid-column: 3`
- 收起时 `grid-template-columns: 48px 1fr 0fr`，过渡动画 `0.3s ease`

**修复文件**：
- `src/components/layout/WorkspaceLayout.tsx`
- `src/components/ai-copilot/AICopilotPanel.tsx`
- `src/components/layout/Header.tsx`

---

## 偏差 2：Copilot 上下文注入机制缺失

**PRD 预期**（§2654）：
> 页面职责与 AI Copilot 默认行为映射表 — 每个页面都有明确的 Copilot 上下文和默认 Action Cards。

**代码实际行为**：
- 无统一注入机制
- 仅 6 个页面手动写 `useEffect` + `setContext`
- 12 个页面完全缺失上下文注入
- 用户切换页面时，Copilot 仍显示上一个页面的上下文

**修复方案**：
- 新建 `hooks/useCopilotPageSync.ts` 统一 Hook
- 在 `App.tsx` 的 `LayoutWrapper` 中全局挂载
- 自动覆盖全部路由，无需各页面手动注入
- 调用后端 `POST /api/ai/copilot/context` 上报上下文
- 调用后端 `GET /api/ai/copilot/action-cards` 获取 Action Cards

**修复文件**：
- `src/hooks/useCopilotPageSync.ts`（新增）
- `src/App.tsx`
- 各页面移除手动 `setContext` 调用

---

## 偏差 3：欢迎语全局硬编码

**PRD 预期**（§5.3）：
> AI Copilot 面板设计规范 — 欢迎语应根据页面上下文动态生成。

**代码实际行为**：
- `MessageHistory.tsx` 硬编码 `"有什么可以帮你的？"`
- 所有页面统一显示，无页面特定引导

**修复方案**：
- `aiCopilotStore` 新增 `welcomeMessage` 状态
- `useCopilotPageSync` 从后端 `ai_insights[0]` 获取欢迎语
- `MessageHistory` 从 Store 读取 `welcomeMessage`

**修复文件**：
- `src/stores/aiCopilotStore.ts`
- `src/components/ai-copilot/MessageHistory.tsx`
- `src/hooks/useCopilotPageSync.ts`

---

## 偏差 4：快捷动作全局硬编码

**PRD 预期**（§5.3）：
> 快捷动作区根据页面上下文动态更新。

**代码实际行为**：
- `aiCopilotStore.ts` 初始化硬编码 4 条快捷动作
- 所有页面固定显示

**修复方案**：
- `aiCopilotStore` 新增 `setQuickActions` 方法
- `useCopilotPageSync` 从后端 `suggested_actions` 获取快捷动作

**修复文件**：
- `src/stores/aiCopilotStore.ts`
- `src/hooks/useCopilotPageSync.ts`

---

## 偏差 5：Action Cards 前端硬编码

**PRD 预期**（§6.1）：
> 后端 API 统一规范 — `GET /api/ai/copilot/action-cards` 返回页面级 Action Cards。

**代码实际行为**：
- `KeywordLibraryPage.tsx`、`TemplateLibraryPage.tsx` 等页面前端硬编码 Action Cards
- Dashboard 的 `useDashboardContext` 前端获取并映射 Action Cards

**修复状态**：🔄 **迁移中**
- 统一 Hook `useCopilotPageSync` 已接入后端 `action-cards` 接口
- 页面级硬编码 Action Cards 暂时保留作为兜底
- 待后端接口全面覆盖后，可完全移除前端硬编码

---

## 偏差 6：无抽拉动画

**PRD 预期**（§2542）：
> 三栏布局过渡动画。

**代码实际行为**：
- Copilot 展开/收起时瞬间切换，无过渡效果
- 收起时使用悬浮按钮，占用右侧空间

**修复方案**：
- CSS Grid `grid-template-columns` 添加 `0.3s ease` 过渡
- Copilot Panel 添加 `opacity` 过渡
- 移除悬浮按钮，改为 Header 内 toggle 按钮

**修复文件**：
- `src/components/layout/WorkspaceLayout.tsx`
- `src/components/ai-copilot/AICopilotPanel.tsx`
- `src/components/layout/Header.tsx`

---

*维护: 项目团队 + Kimi Code CLI*  
*版本: v4.0*  
*生效日期: 2026-06-05*
