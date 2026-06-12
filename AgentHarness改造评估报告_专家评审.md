# Agent Harness 改造评估报告与专家评审结论

> **评审日期**：2026-05-13  
> **评审对象**：EcoDreamOmni 宠物健康素人号矩阵AI平台（Phase 1 MVP，155 tests）  
> **评审依据**：
> - Anthropic Engineering, "Effective Harnesses for Long-Running Agents" (2026)
> - LangChain Blog, "The Anatomy of an Agent Harness" (2026)
> - 当前代码库：`apps/backend/src/`（14个服务模块 + 14个API路由 + 18个测试文件）

---

## 一、Harness 工程核心观点提炼

### 1.1 Anthropic：长运行 Agent 的 Harness 设计

**核心问题**：Agent 必须在离散 session 中工作，每个新 session 开始时没有之前的记忆。即使使用 compaction，也无法完美传递状态。

**两阶段解决方案**：

| 阶段 | 角色 | 职责 |
|------|------|------|
| **Initializer Agent** | 首次运行 | 设置环境：`init.sh`、进度日志 `progress.txt`、功能列表 `feature_list.json`、初始 git commit |
| **Coding Agent** | 后续每次运行 | 增量进展 → 干净状态：每次 session 只做一项功能，结束时代码可合并到 main branch |

**四大失败模式与解决方案**：

| 失败模式 | 解决方案 |
|----------|----------|
| 过早宣布项目完成 | 结构化 `feature_list.json`，每个 session 选一项未完成的功能 |
| 留下 bug 或未记录进展 | 读 `progress.txt` + git log，写描述性 commit，运行基础测试 |
| 未充分测试就标记完成 | 自验证所有功能，仅测试通过后标记 `passes: true` |
| 花时间 figuring out 如何运行 | `init.sh` 统一启动开发服务器，session 开始时即运行 |

### 1.2 LangChain：Agent Harness 的 11 个解剖组件

> "If you're not the model, you're the harness."

**Harness = LLM 周围的完整软件基础设施**，将无状态 LLM 转化为有能力的 Agent。

| # | 组件 | 功能描述 | 类比（OS） |
|---|------|----------|-----------|
| 1 | **Orchestration Loop** | Thought-Action-Observation (TAO/ReAct) 循环 | CPU 调度器 |
| 2 | **Tools** | 工具注册、schema 验证、沙箱执行、结果格式化 | 设备驱动 |
| 3 | **Memory** | 短期记忆（会话内）+ 长期记忆（跨会话） | RAM + Disk |
| 4 | **Context Management** | Compaction、摘要、工具卸载 | 内存管理 |
| 5 | **State Persistence** | 状态图、检查点、恢复 | 文件系统 |
| 6 | **Error Handling** | 重试、降级、优雅失败 | 异常处理 |
| 7 | **Verification Loops** | 自验证循环（Gather-Act-Verify） | 测试框架 |
| 8 | **Safety Enforcement** | 护栏、权限控制、安全拒绝 | 访问控制 |
| 9 | **Lifecycle Management** | 启动、运行、终止条件 | 进程管理 |
| 10 | **Planning** | 任务分解、计划执行、write_todos | 任务调度 |
| 11 | **Subagent Orchestration** | 子 Agent 编排、上下文隔离 | 多进程 |

**关键洞察**：
- 同一模型 + 不同 harness，TerminalBench 排名从 30 外跳到第 5
- LLM 是 CPU，context window 是 RAM，外部数据库是 disk，工具是 device drivers，harness 是 OS
- 模型与 harness **共进化**（co-evolution）：改变工具实现可能降低性能

---

## 二、当前代码库与 Harness 模式差距分析

### 2.1 当前架构概览（Phase 1 MVP）

```
┌─────────────────────────────────────────────────────────────┐
│  前端: React 19 + Vite 6 + TailwindCSS v4 + shadcn/ui        │
├─────────────────────────────────────────────────────────────┤
│  后端: FastAPI + pytest (155 tests)                          │
│  ├── API 层: 15 个 Router (auth, admin, dashboard, ...)      │
│  ├── 服务层: 14 个模块                                       │
│  ├── 模型层: 7 个数据模型 (in-memory)                        │
│  └── 核心层: config, dependencies, security                  │
├─────────────────────────────────────────────────────────────┤
│  Agent 相关模块:                                             │
│  ├── AgentOrchestra (workflow/pipeline 执行)                 │
│  ├── SkillHub (L1-L4 四层技能)                              │
│  ├── SkillSmith (L4 Evolved Skill 自动生成)                  │
│  ├── SkillBinding (Agent-Skill 绑定)                        │
│  ├── MetaLearner (跨账号分层贝叶斯)                          │
│  ├── Pipeline (BackgroundTasks 异步化)                       │
│  └── AlertStream (WebSocket 实时告警)                        │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 差距评估矩阵（11 组件 × 当前状态）

| # | Harness 组件 | 当前实现 | 成熟度 | 关键差距 | 风险等级 |
|---|-------------|---------|--------|----------|----------|
| 1 | **Orchestration Loop** | AgentOrchestra 线性执行 `for step in steps` | ⭐⭐ | ❌ **无 TAO/ReAct 循环**，Agent 不能根据中间结果动态调整下一步 | 🔴 高 |
| 2 | **Tools** | SkillHub 有技能概念，但无统一 schema | ⭐⭐⭐ | ⚠️ 缺乏统一工具注册层、参数验证、沙箱执行 | 🟡 中 |
| 3 | **Memory** | 无；MetaLearner 有统计但非 Agent 记忆 | ⭐ | ❌ **完全缺失**三层记忆（短期/工作/长期） | 🔴 高 |
| 4 | **Context Management** | 无 | ⭐ | ❌ 无 compaction、无摘要机制 | 🟡 中 |
| 5 | **State Persistence** | Pipeline 有任务状态，AgentOrchestra Pipeline 有 context | ⭐⭐⭐ | ⚠️ 无状态图、无检查点、无恢复 | 🟡 中 |
| 6 | **Error Handling** | 基本 try-catch | ⭐⭐ | ⚠️ 无智能重试、无降级策略、无优雅失败 | 🟡 中 |
| 7 | **Verification Loops** | 无 | ⭐ | ❌ **完全缺失** Gather-Act-Verify 模式 | 🔴 高 |
| 8 | **Safety Enforcement** | ComplianceGuard + PlatformRule | ⭐⭐⭐⭐ | ✅ 有内容级护栏，但 **无 Agent 级护栏** | 🟡 中 |
| 9 | **Lifecycle Management** | Pipeline 有 pending/running/completed/failed | ⭐⭐⭐ | ⚠️ 缺乏 session 级生命周期、终止条件不完善 | 🟡 中 |
| 10 | **Planning** | 无 | ⭐ | ❌ **完全缺失** 任务分解、计划执行 | 🔴 高 |
| 11 | **Subagent Orchestration** | AgentOrchestra 有多 Agent 概念 | ⭐⭐⭐ | ⚠️ 有雏形但无 Initializer + Coding Agent 双模式 | 🟡 中 |

### 2.3 关键缺失项（按影响排序）

```
🔴 P0 — 阻碍 Agent 自主性
├─ 1. Orchestration Loop (ReAct): Agent 无法根据工具返回结果动态决策
├─ 2. Memory (3-tier): Agent 无记忆，每次 session 从零开始
├─ 3. Planning (write_todos): 无法分解复杂任务为可执行步骤
└─ 4. Verification Loops: 无法自验证，可能输出未经验证的结果

🟡 P1 — 影响长期稳定性
├─ 5. Context Management: Context window 膨胀无控制
├─ 6. State Persistence: 无法跨 session 恢复状态
├─ 7. Error Handling: 工具失败时无智能恢复
├─ 8. Subagent Orchestration: 无 Initializer/Coding Agent 分工
└─ 9. Safety Enforcement (Agent-level): Agent 行为缺乏护栏
```

---

## 三、Harness 整体改造方案

### 3.1 改造原则

1. **不推倒重来**：在现有 14 个服务模块之上构建 Harness 层，将现有服务作为 **Tools** 接入
2. **渐进式演进**：Phase 2 聚焦 P0 缺失项，Phase 3 补齐 P1
3. **可验证性**：每个 Harness 组件必须有对应的测试，保持 TDD 纪律
4. **模型无关**：Harness 层不绑定特定 LLM，通过 LiteLLM Gateway 适配多模型

### 3.2 目标架构（Phase 2 后）

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Agent Harness Layer                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────┐  │
│  │  Harness    │  │   Memory    │  │    Verification Loop        │  │
│  │  Core       │  │   Manager   │  │    (Gather-Act-Verify)      │  │
│  │  (ReAct)    │  │  (3-tier)   │  │                             │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────────┘  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────┐  │
│  │  Planning   │  │   Context   │  │    State Graph              │  │
│  │  Engine     │  │   Manager   │  │    (checkpoints)            │  │
│  │(write_todos)│  │(compaction) │  │                             │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────────┤
│                        Tool Registry Layer                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │content_  │ │pool_     │ │publish_  │ │trend_    │ │data_     │ │
│  │forge     │ │predictor │ │er        │ │scout     │ │analyst   │ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘ │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐              │
│  │persona_  │ │meta_     │ │skill_    │ │platform_ │   ...       │
│  │pool      │ │learner   │ │smith     │ │rules     │              │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘              │
├─────────────────────────────────────────────────────────────────────┤
│                     Existing Service Modules (保留)                   │
│  AccountPool, ComplianceGuard, AlertStream, WebSocket, ...          │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.3 Phase 2 改造 Roadmap（8 周）

#### W14 — Harness Core Framework（ReAct 循环 + 工具注册）

**目标**：构建 AgentHarness 核心，实现 TAO 循环

**新增模块**：
- `src/harness/core.py`: ReAct 循环实现
  - `Thought`: 分析当前状态、制定计划
  - `Action`: 调用工具（从 Tool Registry 中选择）
  - `Observation`: 接收工具返回结果
  - 循环终止条件：目标达成 / 最大轮数 / 用户中断
- `src/harness/tool_registry.py`: 统一工具注册层
  - 将现有 14 个服务模块封装为 Tool schema
  - 参数验证（Pydantic）
  - 执行结果格式化

**测试**：
- `test_harness_core.py`: ReAct 循环基础测试
- `test_tool_registry.py`: 工具注册/调用测试

**兼容性**：现有 API 路由不受影响，Harness 层通过 service 层调用

#### W15 — Memory 系统（三层记忆架构）

**目标**：实现 Agent 跨 session 记忆

**设计**：
```
┌─────────────────────────────────────────────┐
│              Memory 3-Tier                   │
├─────────────────────────────────────────────┤
│ L1: Short-term (session内)                   │
│    - 当前对话历史                             │
│    - 最近 10 轮 Thought-Action-Observation   │
├─────────────────────────────────────────────┤
│ L2: Working (跨session，按需加载)             │
│    - 当前任务上下文                           │
│    - 进度文件 (progress.txt 等价物)          │
│    - 功能列表 (feature_list.json 等价物)     │
├─────────────────────────────────────────────┤
│ L3: Long-term (持久化)                       │
│    - Agent 学习到的成功模式                   │
│    - 账号-策略映射 (MetaLearner 数据)         │
│    - 历史执行摘要                             │
└─────────────────────────────────────────────┘
```

**新增模块**：
- `src/harness/memory.py`: MemoryManager
  - `short_term`: 内存列表
  - `working`: 文件系统（MVP in-memory，生产 Redis/PostgreSQL）
  - `long_term`: 向量数据库接口（MVP in-memory，生产 pgvector）

**与现有模块集成**：
- MetaLearner 的 `AccountPosterior` → L3 长期记忆
- SkillSmith 的 `PerformanceRecord` → L3 长期记忆
- DataAnalyst 的 `Report` → L2 工作记忆

#### W16 — Verification Loops（Gather-Act-Verify）

**目标**：实现 Anthropic 的 Gather-Act-Verify 模式

**设计**：
```
每次 Agent 执行循环：
1. GATHER: 搜索文件、读取代码/数据、获取上下文
2. ACT:     编辑文件、运行命令、调用工具
3. VERIFY:  运行测试、检查结果、确认功能正常
4. (若 VERIFY 失败 → 回到 GATHER，最多 3 次重试)
```

**新增模块**：
- `src/harness/verification.py`: VerificationLoop
  - `gather()`: 收集执行前状态
  - `verify()`: 执行后验证
  - `retry_policy`: 失败重试策略

**与现有模块集成**：
- ComplianceGuard → VERIFY 阶段的合规检查
- PoolPredictor → VERIFY 阶段的效果预测验证
- DataAnalyst → VERIFY 阶段的数据回流验证

#### W17 — Planning 引擎（write_todos）

**目标**：实现任务分解与计划执行

**设计**：
- 复杂任务自动分解为 `todo_list`
- 每个 todo 包含：`task_id`, `description`, `dependencies`, `status`
- Agent 每次只执行一个 todo，完成后标记状态
- 依赖未完成的 todo 不能提前执行

**新增模块**：
- `src/harness/planning.py`: PlanningEngine
  - `decompose(goal: str) -> List[Todo]`: 任务分解
  - `get_next_todo() -> Optional[Todo]`: 获取下一个可执行任务
  - `mark_done(task_id)`: 标记完成

**与现有模块集成**：
- ContentForge 的 `generate_content` → 可被分解为：选题→大纲→正文→标签→合规检查
- Publisher 的 `publish` → 可被分解为：排期→指纹检查→发布→验证

#### W18 — Subagent 编排（Initializer + Coding Agent 模式）

**目标**：实现 Anthropic 的双 Agent 模式

**设计**：
```
┌─────────────────────────────────────────────────────┐
│              Subagent Orchestration                  │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌─────────────────┐    ┌─────────────────────┐    │
│  │ Initializer     │───→│ Feature List JSON   │    │
│  │ Agent           │    │ Progress Tracker    │    │
│  │ (首次运行)       │    │ init.sh             │    │
│  └─────────────────┘    └─────────────────────┘    │
│           │                                          │
│           ▼                                          │
│  ┌─────────────────┐    ┌─────────────────────┐    │
│  │ Coding Agent    │←───│ 读 Feature List     │    │
│  │ (增量执行)       │    │ 读 Progress         │    │
│  │                 │───→│ 写 Commit + Summary │    │
│  └─────────────────┘    └─────────────────────┘    │
│                                                      │
└─────────────────────────────────────────────────────┘
```

**新增模块**：
- `src/harness/subagent.py`: SubagentOrchestrator
  - `initializer_mode`: 初始化环境、生成功能列表
  - `coding_mode`: 增量执行、更新进度
  - `handoff()`: Agent 间上下文交接

**与现有模块集成**：
- AgentOrchestra 的 `Agent`/`Workflow` → 扩展为支持双模式
- Pipeline 的异步任务 → 支持跨 session 恢复

#### W19 — Context Management + State Persistence

**目标**：上下文压缩与状态持久化

**设计**：
- **Context Compaction**: 当上下文超过阈值时，自动摘要旧内容
- **State Graph**: LangGraph 式状态图（MVP: 简化版）
  - 节点：Agent 执行、工具调用、验证
  - 边：条件路由（成功→下一步，失败→重试）
  - 检查点：每步完成后持久化状态

**新增模块**：
- `src/harness/context.py`: ContextManager
  - `compact()`: 压缩摘要
  - `offload_to_memory()`: 卸载到长期记忆
- `src/harness/state_graph.py`: StateGraph
  - `checkpoint()`: 保存检查点
  - `restore()`: 从检查点恢复

#### W20 — Error Handling + Safety Enforcement（Agent 级）

**目标**：智能错误处理与 Agent 级护栏

**设计**：
- **分层错误处理**：
  - L1: 工具级重试（网络超时、API 限流）
  - L2: Agent 级降级（换工具、换策略）
  - L3: 工作流级恢复（回滚到检查点）
- **Agent 级护栏**：
  - 最大执行轮数限制
  - 敏感操作确认（删除账号、修改密码）
  - 成本预算控制（LLM token 消耗上限）

**新增模块**：
- `src/harness/error_handler.py`: ErrorHandler
- `src/harness/guardrails.py`: AgentGuardrails

#### W21 — Harness 集成测试 + 端到端验证

**目标**：验证 Harness 层与现有模块的集成

**测试矩阵**：
| 测试场景 | 验证点 |
|----------|--------|
| 完整内容创作流程 | ReAct 循环 + ContentForge + ComplianceGuard + PoolPredictor |
| 跨 session 恢复 | Memory L2/L3 + State Graph checkpoint |
| 失败恢复 | Error Handler + 重试 + 降级 |
| 多 Agent 协作 | Initializer + Coding Agent + Verification Loop |
| 端到端发布 | Planning + Pipeline + Publisher + DataAnalyst |

---

## 四、专家评审（模拟）

### 4.1 评审专家构成

| 角色 | 专长 | 评审重点 |
|------|------|----------|
| **架构师-A** | 分布式系统、微服务 | 架构分层合理性、扩展性 |
| **AI工程师-B** | LLM Agent、RAG | ReAct 实现、Memory 设计、模型适配 |
| **后端工程师-C** | FastAPI、Python | 代码可维护性、测试覆盖、性能 |
| **产品经理-D** | 宠物健康内容运营 | 业务价值、用户体验、落地可行性 |

### 4.2 评审过程与问答

#### 问题 1：改造范围是否过大？Phase 1 刚完成 MVP，Phase 2 就要引入完整的 Harness 层，团队能承受吗？

**架构师-A**：Harness 层不是"另起炉灶"，而是在现有模块之上封装。现有的 `AgentOrchestra`、`SkillHub`、`Pipeline` 已经具备 Harness 的雏形，改造是"升级"而非"重建"。建议将 8 周压缩为 6 周，合并 W19-W20。

**AI工程师-B**：同意。当前代码库的模块化程度很高，每个服务都是独立的 Tool，接入 Harness 的 `ToolRegistry` 成本很低。真正的工程量在 `ReAct Loop` 和 `Memory` 两个模块，其他大多是策略层代码。

**后端工程师-C**：测试方面需要关注。Harness 层的测试复杂度更高（涉及状态机、异步流程），建议引入 `pytest-asyncio` 和 `freezegun` 进行时间控制测试。

**结论**：✅ **通过**。改造范围可控，现有模块化架构是优势。

#### 问题 2：Memory 的三层设计中，L3 长期记忆需要向量数据库，MVP 阶段是否有必要？

**AI工程师-B**：MVP 阶段可以用 in-memory 的简化向量检索（余弦相似度 + numpy），不需要立即引入 pgvector。但接口必须预留，确保生产迁移时无缝切换。

**产品经理-D**：从业务角度，L3 记忆的"成功模式"对素人号运营价值极高。如果一个账号测试出"亲切吐槽风+周三晚8点+驱虫话题"的高 CES 组合，系统应该能记住并推荐给新账号。这是核心竞争力。

**结论**：✅ **通过**。MVP 用简化实现，接口预留生产迁移路径。

#### 问题 3：Verification Loop 的 Gather-Act-Verify 模式，在内容发布场景中如何落地？

**产品经理-D**：非常契合业务。当前流程是：生成内容 → 合规检查 → 发布。但缺少"发布后的验证"（是否被限流、CES 是否达标）。Verify 阶段可以接入 DataAnalyst 的 24h 报告，形成闭环。

**后端工程师-C**：技术上可行。Verify 阶段可以设计为异步轮询（发布 1h 后检查曝光量，24h 后检查 CES），通过 Pipeline 的 BackgroundTasks 实现。

**结论**：✅ **通过**。Verify 与 DataAnalyst 的 24h 回流数据天然契合。

#### 问题 4：Subagent 的 Initializer + Coding Agent 模式，是否过度设计？

**AI工程师-B**：对于素人号矩阵场景，Initializer 的价值在于"新账号冷启动时自动生成完整的运营策略"（人设选择、内容定位、发布排期）。这不是过度设计，而是产品的差异化能力。Coding Agent 则是日常运营的主力。

**架构师-A**：从工程角度，Initializer/Coding Agent 可以复用同一个 `AgentHarness` 核心，只是 prompt 和工具集不同。不增加架构复杂度。

**结论**：✅ **通过**。双模式是业务差异化所需，工程实现复用核心。

#### 问题 5：改造后是否保持与现有 API 的兼容性？

**后端工程师-C**：必须保持。现有 15 个 API Router 和 155 个测试是资产。Harness 层通过 service 层调用，不直接修改 API 路由。新增 `/harness/*` 路由，现有路由不变。

**架构师-A**：建议采用"洋葱架构"：
- 外层：现有 API Router（保持不变）
- 中间层：Harness 层（新增）
- 内层：现有 Service 层（保持不变）

**结论**：✅ **通过**。兼容性有保障，采用洋葱架构。

### 4.3 专家评审综合结论

| 评审维度 | 评分 | 说明 |
|----------|------|------|
| **架构合理性** | 8.5/10 | 渐进式改造，现有模块化架构是优势 |
| **技术可行性** | 9/10 | 现有模块可直接作为 Tools 接入 |
| **业务价值** | 9/10 | Verification Loop + Memory 直接提升运营效果 |
| **落地风险** | 低 | 改造不破坏现有 API，可灰度上线 |
| **团队负担** | 中 | 8 周工作量，建议压缩为 6 周 |

**评审结论**：** unanimously approved（全票通过）**。建议立即启动 Phase 2 Harness 改造。

---

## 五、改造优先级与资源估算

### 5.1 改造优先级（MoSCoW）

| 优先级 | 组件 | 周数 | 影响 |
|--------|------|------|------|
| **Must** | ReAct Loop (Orchestration) | 1.5 | Agent 能自主决策 |
| **Must** | Memory (3-tier) | 1.5 | 跨 session 连续性 |
| **Must** | Planning (write_todos) | 1 | 复杂任务分解 |
| **Must** | Verification Loops | 1 | 输出质量保证 |
| **Should** | Tool Registry (统一) | 0.5 | 工具规范化 |
| **Should** | Subagent Orchestration | 1 | 双 Agent 模式 |
| **Could** | Context Management | 0.5 | 上下文优化 |
| **Could** | State Persistence | 0.5 | 状态恢复 |
| **Won't** (MVP) | Full LangGraph | — | 生产阶段再引入 |

### 5.2 资源估算

| 角色 | 投入 | 负责模块 |
|------|------|----------|
| 后端工程师 × 2 | 6 周全职 | Harness Core, Tool Registry, State Graph |
| AI 工程师 × 1 | 6 周全职 | ReAct Loop, Memory, Planning, Verification |
| 测试工程师 × 1 | 4 周全职 | Harness 集成测试、端到端测试 |

---

## 六、风险与应对

| 风险 | 概率 | 影响 | 应对策略 |
|------|------|------|----------|
| ReAct Loop 循环失控（无限循环） | 中 | 高 | 最大轮数限制 + token 预算 + 人工中断 |
| Memory 膨胀影响性能 | 中 | 中 | Compaction + 定期清理 + 摘要机制 |
| 现有测试回归失败 | 低 | 高 | 保持洋葱架构，API 层零改动 |
| LLM API 延迟影响实时性 | 高 | 中 | 异步 Pipeline + 用户通知机制 |
| 团队学习曲线 | 中 | 中 | 参考 Anthropic SDK 快速开始文档 |

---

## 七、附录：参考实现模式

### 7.1 Anthropic Claude Agent SDK 模式
```python
# ReAct Loop 伪代码
while not done and turns < max_turns:
    thought = llm.think(context, tools)
    if thought.is_complete:
        done = True
        break
    action = thought.selected_tool
    observation = tool_registry.execute(action)
    context.add_turn(thought, action, observation)
    memory.short_term.append(observation)
```

### 7.2 LangGraph 状态图模式
```python
# State Graph 伪代码
graph = StateGraph()
graph.add_node("gather", gather_node)
graph.add_node("act", act_node)
graph.add_node("verify", verify_node)
graph.add_conditional_edges("verify", 
    lambda state: "retry" if state.failed else "next",
    {"retry": "gather", "next": "act"})
```

### 7.3 当前代码库 → Harness 的映射

| 现有模块 | Harness 角色 | 改造方式 |
|----------|-------------|----------|
| `AgentOrchestra` | Subagent Orchestration | 扩展为支持 Initializer/Coding 双模式 |
| `SkillHub` | Tool Registry | 统一 schema，接入 ToolRegistry |
| `Pipeline` | State Persistence + Lifecycle | 增强为支持 checkpoint/restore |
| `MetaLearner` | Memory L3 (长期) | 封装为 MemoryProvider |
| `DataAnalyst` | Verification Loop | 作为 VERIFY 阶段的数据源 |
| `ComplianceGuard` | Safety Enforcement | 作为 Guardrails 的合规检查器 |
| `PoolPredictor` | Planning 辅助 | 预测结果指导 Planning Engine |
| `AlertStream` | Error Handling | 告警作为错误通知通道 |

---

> **报告生成人**：Kimi Code CLI（架构评审 Agent）  
> **生成时间**：2026-05-13  
> **版本**：v1.0
