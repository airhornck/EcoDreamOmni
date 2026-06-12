# 综合实施大纲 v3：任务驱动改造与 UI 优化

> 版本：v3.0（合并 v1.0 综合评审 + v2.0 用户问题专项评审 + 用户最终决策）  
> 编制日期：2026-05-24  
> 编制团队：架构专家组 + UE 专家组 + 前端技术专家组 + 后端技术专家组  
> 状态：**所有决策已采纳，进入开发实施阶段**  
> 真源文档：
> - `docs/改造优化方案_任务驱动内容生产_v2.md`
> - `docs/问题分析与优化方案_任务新建UI改造_v1.md`
> - `docs/专家评审报告_任务驱动改造与UI优化综合评审.md`（v1.0）
> - `docs/专家评审报告_用户问题专项评审与信息架构优化_v2.md`

---

## 一、执行摘要

### 1.1 当前状态

| 维度 | 状态 |
|------|------|
| v2 方案 6 个 Phase | 5.5 个已完成代码实现，仅 Wizard 未启动 |
| 问题 1（4 项修复） | ✅ 已全部落地 |
| 用户新增 5 个问题 | 根因已定位，修复方案已确认 |
| 质量门禁（测试/E2E） | 存在缺口，纳入实施路线 |

### 1.2 用户最终决策（6/6 项全部采纳）

| # | 决策项 | 决策 |
|---|--------|------|
| 1 | 立即执行紧急修复（白屏 + 死链） | ✅ 已采纳 |
| 2 | HumanInLoop 合并到 ReviewPublishCenter 后下线 | ✅ 已采纳 |
| 3 | ContentForge 能力迁移后注释（非简单注释） | ✅ 已采纳 |
| 4 | 接受 Wizard 改造方案 | ✅ 已采纳 |
| 5 | 全局增加 ErrorBoundary 防白屏 | ✅ 已采纳 |
| 6 | 接受修订后 6 天完整工期（含测试补全 + E2E） | ✅ 已采纳 |

### 1.3 实施总纲

**总工期：约 6 天，分 4 个批次交付。**

```
批次 1：紧急修复 + 测试补全（1.5 天）
批次 2：功能增强 + 信息架构微调（2 天）
批次 3：Wizard 改造（2 天）
批次 4：E2E 回归验证（0.5 天）
```

---

## 二、已完成项确认（无需重复实施）

### 2.1 v2 方案 Phase-by-Phase 完成度

| Phase | 改造内容 | 完成状态 | 代码证据 |
|-------|----------|----------|----------|
| **Phase 0** | 后端 Task 状态机扩展：`APPROVED_WAITING_PUBLISH` + 新字段 | ✅ 已完成 | `services/task_hub.py:13-76` |
| **Phase 1** | TaskHub 新建任务增强：平台选择 + 注入摘要面板 | ✅ 已完成 | `pages/TaskHubPage.tsx:616-813` |
| **Phase 2** | 任务执行详情 Drawer：Phase 进度条 + 干预入口 | ✅ 已完成 | `pages/TaskHubPage.tsx:871-987` |
| **Phase 3** | ContentForge 任务上下文模式：自动加载配置 | ✅ 已完成 | `pages/ContentForgePage.tsx:134-220` |
| **Phase 4** | HumanInLoop 审核工作台：纯审核决策，移除发布确认 | ✅ 已完成 | `pages/HumanInLoopPage.tsx` |
| **Phase 5** | 审核发布中心：列表 + 详情 Drawer + 发布确认 + CronJob | ✅ 已完成 | `pages/ReviewPublishCenterPage.tsx` (446 行) |
| **Phase 6** | 前端路由串联 + 全局导航 | ✅ 已完成 | `App.tsx:50` + `Sidebar.tsx:76` |

### 2.2 问题 1（4 项修复）验证

| 根因 | 修复措施 | 代码位置 | 状态 |
|------|----------|----------|------|
| `load_presets()` 未调用 | lifespan 启动时调用 | `main.py:118-119` | ✅ |
| account-pool 为空 | 添加种子数据（3 个测试账号） | `main.py:122-139` | ✅ |
| fetchContentSeries 缺失 | Drawer open effect 中补充 | `TaskHubPage.tsx:138` | ✅ |
| disabled={!platform} | 改为显示全部账号 + 提示文案 | `TaskHubPage.tsx:637-653` | ✅ |

### 2.3 后端 API 新增与调整（已完成）

| API / 服务 | 状态 | 说明 |
|-----------|------|------|
| `api/review_publish.py` | ✅ 新增 | 审核结论聚合、详情查询、确认发布（含 CronJob 创建） |
| `services/task_hub.py` | ✅ 修改 | 新增状态、字段、`transition_task_with_update` 原子操作 |
| `services/human_in_loop.py` | ✅ 修改 | `approve_task` 改为进入 `APPROVED_WAITING_PUBLISH` |
| `api/task_hub.py` | ✅ 修改 | TaskResponse 输出新字段；CreateTaskRequest 支持 platform |
| `api/human_in_loop.py` | ✅ 兼容 | ApproveRequest 保留参数但改为可选（向后兼容） |

---

## 三、用户 5 个问题 —— 根因诊断与修复方案

### 3.1 问题 1：Dashboard「新建任务」与 TaskHub「新建任务」指向不一致

**根因**：Dashboard 按钮 `navigate('/content-forge')`，TaskHub 按钮 `openDrawer()`，两者指向不同。

**修复方案**：Dashboard「新建任务」统一指向 `/task-hub`（短期自动打开 Drawer；Wizard 上线后指向 `/task-hub/create`）。

### 3.2 问题 2：暂时注释掉 `/content-forge`

**影响面**：Dashboard 3 个入口、Sidebar 导航、TaskHub Detail Drawer「预览/干预」、ReviewPublishCenter「前往修改」共 7 个死链。

**修复方案**：
1. 隐藏 Sidebar「内容工坊」导航入口
2. 修正 Dashboard 所有指向 ContentForge 的链接
3. 注释 App.tsx 中 `/content-forge` 路由
4. 将 ContentForge 核心编辑能力迁移到 TaskHub 任务详情页（保留干预链路）

### 3.3 问题 3：有了 review-publish-center，compliance/human-in-loop/publisher 是否还有必要

| 页面 | 决策 | 理由 |
|------|------|------|
| **Compliance** | ✅ **保留** | 独立风控扫描工具（L1-L4 + 规则库 + 批量扫描），RPC 只展示结论摘要 |
| **HumanInLoop** | 🔄 **合并到 RPC 后下线** | RPC 已有「审核中」Tab，增加通过/驳回/打回按钮即可一站式完成审核决策+发布确认 |
| **Publisher** | ✅ **保留** | 完整发排系统（日历视图+草稿选择+历史追踪），RPC 只是其子集 |

### 3.4 问题 4：agent-orchestra 未展示 Agent / 是否可编辑

**根因**：
- 页面有 Agent 列表表格，但若后端返回空数据则显示「暂无 Agent」
- **缺少编辑功能**：只有创建和展开查看，无 Update 按钮和表单

**修复方案**：补充 `updateAgent` store 方法 + 编辑表单 UI（复用创建表单结构），调用 `PUT /api/agents/:id`。

### 3.5 问题 5：llm-cockpit 白屏且无法返回

**🚨 根因**：前后端 API 契约断裂。

```
后端 /api/llm-hub/models 返回: {"items": [...], "total": N}
前端 fetchModels: set({ models: data || [] })
结果: models = 对象（不是数组）
组件渲染: models.map() → TypeError → React 崩溃 → 全局白屏
```

**修复方案**：
1. **立即修复（1 行）**：`set({ models: data.items || [] })`
2. **附加修复**：`scopeConfigs` 数据映射（`current_model` → `model_name`）
3. **防御性措施**：全局 ErrorBoundary（约 30 行），防止单页面错误导致全局白屏

---

## 四、UE 专家组：信息架构优化方案

### 4.1 优化后的导航结构（实施后）

```
驾驶舱
└── 运营驾驶舱 /dashboard
    └── 「新建任务」按钮 → /task-hub/create（Wizard）

内容生产
├── 任务中心 /task-hub          ← Wizard 改造后成为统一创建入口
├── 趋势侦察 /trend-scout
└── 互动预演 /predictions       ← 可选：未来移至「风控与发布」

风控与发布
├── 合规审核 /compliance
├── 审核发布中心 /review-publish-center  ← 新增：含审核中/已通过/已驳回/已打回/全部
└── 发布中心 /publisher

数据智能
└── 数据分析 /data-analyst

账号与人设
├── 账号池 /account-pool
└── 人设与剧本 /personas

基础功能
├── 品牌资料库 /brand-knowledge
├── 素材库 /assets
├── 时间线库 /timeline
├── 兽药批文库 /vetdrug
└── 平台规则库 /platform-rules

系统治理
├── Agent 驾驶舱 /agent-orchestra   ← 增强：支持 Agent 编辑
├── 模型管理 /llm-cockpit           ← 修复白屏
├── 技能中枢 /skillhub
├── 工作流编排 /workflow-cockpit
└── 定时调度 /cron-cockpit

系统设置
├── 代理配置 /proxy-config
└── 系统设置 /settings
```

### 4.2 关键交互链路（优化后）

```
Dashboard「新建任务」
  → /task-hub/create（Wizard 4 步骤）
    → Step1: 基础配置（平台/账号/模板/Persona）
    → Step2: 内容设定（系列/Prompt 变量）
    → Step3: 执行策略（立即/定时/Cron）
    → Step4: 确认创建
      → 创建完成 → TaskHub 列表
        → 点击任务 → Detail Drawer（Phase 进度条）
          → Phase 3「内容生成」→ 内联编辑器（原 ContentForge 能力迁移）
            → 编辑内容 → 提交审核 → 自动 transition → HUMAN_WAIT
          → Phase 6「人工审核」→ 跳转 ReviewPublishCenter「审核中」Tab
            → 通过/驳回/打回 → 通过的进入「已通过」Tab
              → 发布确认（立即/定时/Cron）→ 进入 Publisher 执行队列
```

---

## 五、技术专家组：完整实施路线（6 天 / 4 批次）

### 批次 1：紧急修复 + 测试补全（1.5 天）

| 优先级 | 任务 | 工作量 | 交付标准 |
|--------|------|--------|----------|
| 🚨 P0 | LLM Cockpit 白屏修复：`data.items || []` | 1 行 | 页面正常加载，模型列表显示 |
| 🚨 P0 | 全局 ErrorBoundary | 30 行 | 单个页面错误不导致全局白屏 |
| 🚨 P0 | Dashboard「新建任务」指向 `/task-hub` | 2 行 | 点击后打开 TaskHub Drawer |
| 🚨 P0 | 隐藏 Dashboard「新建内容任务」快捷操作 | 1 行 | 用户不可见 |
| 🚨 P0 | 隐藏 Sidebar「内容工坊」导航 | 1 行 | 用户不可见 |
| 🚨 P0 | 注释 App.tsx `/content-forge` 路由 | 2 行 | 路由不可访问 |
| 📋 P0 | 补充 `test_task_status_machine.py` | ~60 行 | `APPROVED_WAITING_PUBLISH` 转换用例通过 |
| 📋 P0 | 补充 `test_review_publish_api.py` | ~80 行 | 列表/详情/确认发布/CronJob 用例通过 |
| 📋 P0 | 补充 `test_human_in_loop_v2.py` | ~40 行 | approve 后状态为 `APPROVED_WAITING_PUBLISH` |
| 📋 P1 | 提取公共 Drawer / SlidePanel 组件 | ~30 行 | TaskHubPage、RPC 复用同一组件 |

### 批次 2：功能增强 + 信息架构微调（2 天）

| 优先级 | 任务 | 工作量 | 交付标准 |
|--------|------|--------|----------|
| 🔄 P1 | HumanInLoop 审核操作迁移到 RPC「审核中」Tab | 0.5 天 | pending 列表卡片可直接通过/驳回/打回 |
| 🔄 P1 | 下线 HumanInLoop（移除页面、路由、Sidebar 导航） | 0.25 天 | `/human-in-the-loop` 不可访问，审核 API 保留 |
| 🔄 P1 | AgentOrchestra 增加编辑功能 | 0.5 天 | 列表有「编辑」按钮，可更新 Agent 信息 |
| 🔄 P1 | LLM Cockpit scope-configs 数据映射修复 | 0.25 天 | 「当前模型」列正常显示 |
| 🔄 P1 | ContentForge 能力迁移到 TaskHub 任务详情 | 0.5 天 | TaskHub Detail Drawer 中可编辑内容并提交审核 |
| 📋 P1 | TaskHub 列表增加「内容干预」快捷图标 | 0.25 天 | RUNNING 且内容生成节点时显示 Hammer 图标 |
| 📋 P2 | 评估「互动预演」分组调整（可选） | — | 信息架构优化，不影响功能 |

### 批次 3：Wizard 改造（2 天）

| 优先级 | 任务 | 工作量 | 交付标准 |
|--------|------|--------|----------|
| 📋 P2 | 新建 `/task-hub/create` 路由 | 0.1 天 | URL 可访问 |
| 📋 P2 | TaskHubCreatePage（Wizard 容器） | 0.3 天 | 含 Stepper 导航 + 状态管理 |
| 📋 P2 | Step1BasicConfig（基础配置） | 0.4 天 | 平台/账号/模板/Persona，级联动效 |
| 📋 P2 | Step2ContentSetting（内容设定） | 0.3 天 | 系列选择 + Prompt 变量动态渲染 |
| 📋 P2 | Step3ExecutionStrategy（执行策略） | 0.3 天 | 立即/定时/Cron，与 CronHub 联动 |
| 📋 P2 | Step4ConfirmCreate（确认创建） | 0.3 天 | 配置摘要只读展示 |
| 📋 P2 | 每步字段校验 + 下一步按钮禁用逻辑 | 0.2 天 | 未填完必填项不可进入下一步 |
| 📋 P2 | 创建完成后自动返回 `/task-hub` | 0.1 天 | 创建成功跳转 |
| 📋 P2 | Dashboard「新建任务」指向 `/task-hub/create` | 0.1 天 | 按钮行为更新 |
| 📋 P1 | Wizard 上线后移除 TaskHubPage Drawer 创建逻辑 | 0.25 天 | TaskHubPage 从 990 行缩减至 ~700 行 |

**Wizard 状态管理方案**：使用本地 `useState`，不新增 Zustand store。创建任务是一次性操作，无需全局共享。

### 批次 4：E2E 回归验证（0.5 天）

| 优先级 | 任务 | 交付标准 |
|--------|------|----------|
| 📋 P0 | 新建任务 → 提交审核 → 审核通过 → 发布确认 全流程走通 | 每个状态转换正确，数据持久化 |
| 📋 P0 | CronJob 创建与 CronCockpit 联动验证 | 循环执行配置后可在 CronCockpit 查看和管理 |
| 📋 P0 | 存量页面回归（Compliance / Publisher / AgentOrchestra / LLM Cockpit） | 无白屏、无死链、功能正常 |

### 总工期汇总

| 批次 | 内容 | 工期 |
|------|------|------|
| 批次 1 | 紧急修复 + 测试补全 | 1.5 天 |
| 批次 2 | 功能增强 + 信息架构微调 | 2.0 天 |
| 批次 3 | Wizard 改造 | 2.0 天 |
| 批次 4 | E2E 回归验证 | 0.5 天 |
| **总计** | | **6.0 天** |

---

## 六、技术风险与缓解措施

| 风险项 | 等级 | 说明 | 缓解措施 |
|--------|------|------|----------|
| `TaskHubPage.tsx` 已达 990 行 | 🟡 中 | 单文件过大，维护成本高 | Wizard 改造移除 Drawer 逻辑后自动瘦身至 ~700 行 |
| 测试覆盖缺口 | 🟡 中 | 新增状态机和 API 无单元测试 | 批次 1 优先补充 3 个测试文件 |
| ContentForge 能力迁移复杂度 | 🟡 中 | 需将内容编辑器嵌入 TaskHub Detail Drawer | 采用内联 iframe 或提取 ContentForge 核心编辑组件复用 |
| HumanInLoop 合并到 RPC | 🟢 低 | 前端 UI 调整，后端 API 不变 | approve/reject/revise API 已存在，仅调整调用方 |
| account-pool 种子数据硬编码 | 🟢 低 | 使用硬编码 demo 账号 | MVP 阶段可接受，后续 Admin 配置化 |
| `publish_mode` API 参数冗余 | 🟢 低 | HITL approve API 仍保留冗余参数 | 标记为 deprecated，下一版本移除 |

---

## 七、代码变更预估

| 模块 | 新增/修改代码预估 | 说明 |
|------|-----------------|------|
| 后端 Task 状态机 | ~20 行 | 已完成，无需变更 |
| 后端 review_publish API | ~120 行 | 已完成，无需变更 |
| 后端 human_in_loop API 调整 | ~10 行 | 已完成，无需变更 |
| 前端 ReviewPublishCenterPage 增强 | ~50 行 | 增加「审核中」Tab 的审核操作按钮 |
| 前端 TaskHubCreatePage + Step 组件 | ~350 行 | Wizard 核心 |
| 前端公共 Drawer 组件提取 | ~30 行 | 复用组件 |
| 前端 Dashboard 修正 | ~5 行 | 死链修复 |
| 前端 LLM Cockpit 修复 | ~5 行 | 白屏 + 数据映射 |
| 前端 ErrorBoundary | ~30 行 | 全局错误边界 |
| 前端 AgentOrchestra 编辑 | ~80 行 | 编辑表单 + Store 方法 |
| 测试 | ~180 行 | 3 个测试文件 |
| **总计** | **~885 行** | 与 v1.0 预估基本持平 |

---

## 八、专家组签字

| 专家组 | 评审结论 | 状态 |
|--------|----------|------|
| **架构专家组** | v2 方案架构合理，APPROVED_WAITING_PUBLISH 中间状态设计正确。用户 5 个问题修复方案无架构风险。Wizard 改造是合理演进路径。 | ✅ 已确认 |
| **后端专家组** | 后端代码实现稳健，状态机有完整保护。测试补全是必要质量门禁。Agent Update API 需在实施中确认存在性，如不存在则同步新增。 | ✅ 已确认 |
| **前端专家组** | LLM Cockpit 白屏根因已定位，修复方案 1 行代码即可。Wizard 改造将显著改善 TaskHubPage 可维护性。公共 Drawer 提取与 Wizard 可同步进行。 | ✅ 已确认 |
| **UE 专家组** | 信息架构优化方向明确：统一入口、合并重复页面（HITL→RPC）、保留独立工具（Compliance/Publisher）。建议优先执行 HumanInLoop 合并。 | ✅ 已确认 |

---

## 九、交付 checklist

批次 1 交付时检查：
- [ ] LLM Cockpit 页面可正常打开，模型列表显示正常
- [ ] 故意制造一个组件渲染错误，验证 ErrorBoundary 捕获且不白屏
- [ ] Dashboard「新建任务」指向 TaskHub，无 404
- [ ] Sidebar 无「内容工坊」入口
- [ ] `pytest` 测试全部通过（含新增的 3 个测试文件）
- [ ] `vitest` 测试全部通过

批次 2 交付时检查：
- [ ] ReviewPublishCenter「审核中」Tab 可直接通过/驳回/打回任务
- [ ] `/human-in-the-loop` 路由不可访问
- [ ] AgentOrchestra 可编辑 Agent 信息
- [ ] TaskHub RUNNING 任务有「内容干预」快捷入口

批次 3 交付时检查：
- [ ] `/task-hub/create` 可访问，4 步骤 Wizard 正常流转
- [ ] 每步校验生效（未填完不可下一步）
- [ ] TaskHubPage 无 Drawer 创建逻辑，「新建任务」跳转 Wizard
- [ ] Wizard 创建完成后自动返回 TaskHub 列表

批次 4 交付时检查：
- [ ] 新建任务 → 提交审核 → 审核通过 → 发布确认（定时/Cron）全流程状态正确
- [ ] CronJob 创建后可在 CronCockpit 查看
- [ ] 存量页面（Compliance/Publisher/AgentOrchestra/LLM Cockpit）功能回归正常

---

> 本文档为开发实施的唯一真源（Single Source of Truth）。任何实施偏差需经专家组评审并更新本文档后方可执行。
