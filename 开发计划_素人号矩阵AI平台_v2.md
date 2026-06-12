# 宠物健康素人号矩阵AI平台 · 开发计划书（v2.2）

> **文档性质**：技术实施级开发计划，面向技术负责人、架构师、开发团队  
> **核心目标**：基于《文档2_最终可行性完整产品方案_素人号矩阵AI平台》（**v5.0 Final**）构建可落地的开发 roadmap，遵循"开源为主+自研为辅"原则，采用 Storybook+Vite 构建 UI，严格执行 Simon Willison 红绿灯 TDD 工程纪律  
> **对齐基线**：与《EcoDream_Omni_PRD_v2_对齐核心方案》（**V2.3**）交叉引用；**工程可靠性修订**日期 **2026-05-13**（结构预检 / 反馈闭环 / 预测口径以此版为准）。  
> **开发周期**：6个月（MVP 2个月 + 进化 2个月 + 规模化 2个月）  
> **团队规模**：建议 8-10 人（后端 3人 + 前端 2人 + AI/算法 2人 + 运维/测试 1-2人）

### 1.3 方案—PRD—开发计划对齐声明（专家组）

| 原不一致项 | 修订结论（以文档2 v5.0 为真源） |
|------------|--------------------------------|
| PRD「〇」矩阵与本文 Phase 2 **W11/W12** 语义对调（TrendScout vs SkillHub） | **以 PRD V2.3 为准**：W11=TrendScout，W12=MarketingMethodology，W13=DataAnalyst，W14=PlatformRule L3/L4 补强 |
| PoolPredictor / 驾驶舱曾出现「流量池 L1–L4、CES 主结论」 | **禁止**作为 MVP 验收；预测与报表默认 **点赞/评论/收藏区间 + 覆盖率 + MAPE** |
| Agent Harness / hermes 章节出现 **MetaLearner、记忆联邦** | 与 v5.0 **已移除模块**冲突：文档与实现均不得再作为需求；跨号经验沉淀走 **SkillSmith + PersonaPool + 审计数据** |
| Phase 0 文档索引引用「短剧」PRD | 基线 PRD 更正为 **`EcoDream_Omni_PRD_v2_对齐核心方案.md`（素人矩阵）** |

**周次权威简表（业务周 W*）**

| 周次 | 主题 | 文档2对应 |
|------|------|-----------|
| W1–W10 | 已实现闭环（登录、主页、账号、生成、合规、发布、驾驶舱、预测冷启动、E2E） | Phase 1 主体 |
| **W11** | TrendScout MVP（Mock + 手动导入 + 结构化报告） | §8.4 |
| **W12** | MarketingMethodology（AIPL 中枢 + 阶段模板对接 ContentForge） | §6、§8 |
| **W13** | DataAnalyst（24h 回流、区间命中、MAPE、归因、校准触发） | §8.9 |
| **W14** | PlatformRule **L3/L4** + 合规**证据链**补强 + Publisher **频率阶梯/随机化**与规则对齐 | §8.3、§8.7 |
| **W15–W22** | Phase 2 进化（SkillHub、SkillSmith、IP 信誉、预测探索期、ContentInsight、多平台、压测） | 文档2 Phase 2 |
| **W23–W30** | Phase 3 规模化（多租户、分片、API、监控、安全、负载、文档、发布） | 文档2 Phase 3 |

**Harness 并行冲刺（代号 H1–H6，避免与 W14 等业务周次数字冲突）**：见 **§九**；与 W11 起可部分并行，但不得引入 v5.0 已废弃模块。

### 1.4 工程可用性：结构预检与反馈闭环（与 PRD §2.6 一致）

| 闭环 | MVP 交付形态 | 开源组件 | 自研边界 |
|------|----------------|----------|----------|
| **预发：结构** | Zod/JSON Schema 校验 + 可选 LiteLLM rubric 评分；**不**承诺「改结构必涨量」 | Zod、LiteLLM、（可选）**guidance** / JSON schema 约束 | 模板 rubric、编排 API |
| **预发：互动区间** | sklearn **QuantileRegressor** 或分段先验宽区间；`interval_mode=prior\|fitted` | scikit-learn | 特征工程、先验表、评估作业 |
| **反馈：数据** | **CSV/表单导入**为主；可选 Playwright **只读**回填（易碎，非 SLA） | Playwright、Pandas | 映射表、校验、幂等写入 |
| **反馈：校准** | Celery **异步**批任务写校准结果；禁止在线秒级学习 | Celery、Redis | 训练触发策略、模型注册表 |

---

## 目录

1. 项目概述与开发目标
2. 开源集成总策略
3. 本地已有项目分析与复用方案
4. GitHub 开源项目选型矩阵
5. 技术架构实施方案
6. UI 系统方案（Storybook + Vite）
7. 工程纪律规范（红绿灯 TDD + Agentic Engineering）
8. 完成度总览（实时更新）
9. Agent Harness 改造专项（Phase 1.5）
10. 开发里程碑与路线图
11. 团队组织与分工
12. 风险与应对

---

## 一、项目概述与开发目标

### 1.1 开发目标

基于产品方案 v5.0 的技术架构，构建一个可落地的素人号矩阵AI内容管理与分发平台。开发遵循三大核心约束：

| 约束 | 要求 | 影响 |
|------|------|------|
| **开源优先** | 已有本地项目（hermes-agent + openclaw）作为底座，GitHub高评分开源项目补齐能力 gaps，自研仅覆盖业务逻辑层和差异化能力 | 降低开发成本 50%+ |
| **UI组件化** | 前端采用 Storybook + Vite 架构，优先使用现成组件库，自研仅覆盖业务专用组件 | 提升前端开发效率 3x |
| **工程纪律** | 严格执行红绿灯 TDD 循环，每个功能必须有失败的测试→最小化实现→测试通过的完整证据链 | 降低Bug率，提升代码质量 |

### 1.2 技术选型总览

| 层级 | 选型 | 来源 |
|------|------|------|
| **Agent编排引擎** | hermes-agent（本地已有，Nous Research） | 本地复用 |
| **SaaS应用框架** | openclaw（本地已有） | 本地复用 |
| **浏览器自动化** | Playwright + rebrowser-patches | GitHub开源 |
| **前端框架** | React 19 + Vite 6 + TailwindCSS v4 | 开源 |
| **UI组件文档** | Storybook 8 + Ladle（快速预览） | 开源 |
| **后端API** | FastAPI / Node.js（基于openclaw） | 本地复用+自研 |
| **数据库** | PostgreSQL 16 + Redis 7 | 开源 |
| **LLM Gateway** | LiteLLM / 自研路由层 | GitHub开源+自研 |
| **任务队列** | Celery + Redis / BullMQ | 开源 |
| **容器化** | Docker + Docker Compose | 开源 |
| **监控** | Prometheus + Grafana | 开源 |

---

## 二、开源集成总策略

### 2.1 分层开源策略

```
┌─────────────────────────────────────────────────────────────────┐
│                    分层开源集成策略                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Layer 1: 业务逻辑层（自研为主）                           │   │
│  │  素人矩阵运营逻辑、AIPL增长飞轮、内容策略、合规规则          │   │
│  │  自研比例：80%                                             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Layer 2: Agent编排层（本地开源复用 + 少量自研）            │   │
│  │  hermes-agent（Agent生命周期、LLM适配、记忆管理）           │   │
│  │  自研：Orchestrator工作流DAG、Agent间通信协议（ACP）         │   │
│  │  自研比例：30%                                             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Layer 3: SaaS基础设施层（本地开源复用）                    │   │
│  │  openclaw（插件系统、网关协议、渠道管理、配置中心）          │   │
│  │  自研比例：10%                                             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Layer 4: 技术对抗层（GitHub开源为主）                      │   │
│  │  Playwright + rebrowser-patches（反检测浏览器自动化）       │   │
│  │  住宅代理池（第三方服务商）                                  │   │
│  │  自研比例：20%（指纹信誉系统、IP信誉系统、行为模式库）       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Layer 5: 通用技术层（GitHub开源为主）                      │   │
│  │  React + Vite + Storybook + PostgreSQL + Redis             │   │
│  │  自研比例：5%                                              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 "Buy vs. Build" 决策矩阵

| 能力模块 | 方案 | 理由 | 自研投入 |
|----------|------|------|----------|
| Agent生命周期管理 | **复用 hermes-agent** | 已有完整的多LLM适配、记忆管理、上下文引擎 | 低 |
| 插件/扩展系统 | **复用 openclaw** | 已有manifest-based插件架构、SDK facade | 低 |
| LLM路由网关 | **LiteLLM** + 自研包装层 | LiteLLM已支持100+模型，统一API接口 | 中 |
| 浏览器自动化 | **Playwright + rebrowser-patches** | 社区维护的反检测补丁，持续更新 | 中 |
| 前端组件库 | **shadcn/ui + Radix UI** | 基于TailwindCSS的headless组件，可定制性强 | 低 |
| 前端构建工具 | **Vite 6** | 行业标准，极速冷启动 | 无 |
| 组件文档 | **Storybook 8** | 行业事实标准，生态丰富 | 无 |
| 数据库ORM | **Prisma / SQLAlchemy** | 成熟稳定，类型安全 | 低 |
| 任务队列 | **Celery / BullMQ** | 成熟分布式任务处理 | 低 |
| 指纹差异化引擎 | **自研** | 业务核心差异化能力，无现成方案 | 高 |
| IP信誉系统 | **自研** | 与业务策略强耦合 | 高 |
| 合规规则引擎 | **自研** | 法规业务逻辑，需持续迭代 | 高 |
| 流量预测模型 | **自研** + sklearn/xgboost | 业务核心算法，基于自有数据训练 | 高 |
| SkillHub技能中枢 | **自研** + 复用hermes-agent skill系统 | hermes已有skill进化能力，需扩展为Hub | 中 |

---

## 三、本地已有项目分析与复用方案

### 3.1 hermes-agent-main（Agent编排引擎底座）

**项目概况**：
- 作者：Nous Research
- 版本：v0.13.0
- 许可证：MIT
- 语言：Python 3.11+
- 核心定位：Self-improving AI agent — creates skills from experience

**可复用能力清单**：

| 组件 | 文件路径 | 功能 | 复用方式 |
|------|----------|------|----------|
| **多LLM适配器** | `agent/anthropic_adapter.py` 等 | OpenAI/Anthropic/Bedrock/Gemini/Moonshot/LMStudio 统一适配 | **直接复用**，作为LLM Gateway底座 |
| **上下文引擎** | `agent/context_engine.py` | 对话上下文管理、压缩、引用 | **直接复用** |
| **记忆管理** | `agent/memory_manager.py` | Agent 长期记忆存储与检索 | **直接复用**，会话/任务级记忆；**禁止**扩展为 v5.0 已移除的「记忆联邦」架构 |
| **Prompt构建器** | `agent/prompt_builder.py` | 动态Prompt组装 | **复用核心逻辑**，扩展为SkillHub四层加载 |
| **凭证池** | `agent/credential_pool.py` | 多LLM API Key统一管理 | **直接复用** |
| **AC协议适配** | `acp_adapter/` | Agent Communication Protocol | **复用概念**，改造为内部ACP协议 |
| **工具集系统** | `toolsets.py` | Agent可调用的工具注册与管理 | **复用框架**，替换为业务工具 |
| **批处理运行器** | `batch_runner.py` | 批量Agent任务执行 | **复用逻辑**，适配矩阵批量任务 |
| **Skill进化** | `agent/skill_*.py` (推断) | 从经验中提取和进化Skill | **复用核心算法**，对接SkillHub |

**复用策略**：
```
hermes-agent（作为Python子模块引入）
    │
    ├─ 复用：LLM适配层 → 接入LLM Gateway
    ├─ 复用：上下文引擎 → ContentForge/ComplianceGuard上下文管理
    ├─ 复用：记忆管理 → 单任务/会话上下文（与 AccountPool 状态读写解耦；跨账号沉淀走 SkillSmith + 审计库）
    ├─ 复用：Prompt构建器 → SkillHub L1/L2加载
    ├─ 复用：凭证池 → 多租户API Key隔离
    └─ 改造：AC协议 → 内部Orchestrator ACP协议
    │
    自研扩展层
    ├─ Orchestrator工作流DAG引擎
    ├─ 9大业务Agent的业务逻辑
    └─ SkillHub四层架构实现
```

### 3.2 openclaw-main（SaaS应用框架底座）

**项目概况**：
- 语言：TypeScript / Node.js 22+
- 包管理：pnpm
- 核心定位：插件化SaaS平台框架，支持多渠道、多插件扩展
- 工程规范：已有完善的AGENTS.md工程纪律

**可复用能力清单**：

| 组件 | 路径 | 功能 | 复用方式 |
|------|------|------|----------|
| **插件架构** | `src/plugins/`, `extensions/` | manifest-based插件注册、加载、隔离 | **直接复用**，作为SkillHub Marketplace底座 |
| **网关协议** | `src/gateway/protocol/` | API网关、请求路由、认证 | **直接复用**，作为SaaS API Gateway |
| **渠道系统** | `src/channels/` | 多平台渠道抽象（可作为多平台适配参考） | **改造复用**，适配小红书/抖音/视频号 |
| **SDK facade** | `src/plugin-sdk/` | 插件开发SDK | **直接复用**，作为第三方Skill开发SDK |
| **配置中心** | `docs/`, config contracts | 类型安全配置、schema校验 | **复用模式** |
| **CI/CD模板** | `.github/`, `docker-compose.yml` | GitHub Actions、Docker部署 | **直接复用** |
| **测试框架** | Vitest配置 | 测试基础设施 | **直接复用** |
| **代码规范** | `oxfmt`, `oxlint` | 格式化与Lint | **复用或替换为Prettier/ESLint** |

**复用策略**：
```
openclaw（作为TypeScript子模块/参考架构引入）
    │
    ├─ 复用：插件架构 → SkillHub三层来源（Built-in/Marketplace/Evolved）
    ├─ 复用：网关协议 → SaaS RESTful API + WebSocket Gateway
    ├─ 复用：渠道抽象 → 多平台发布适配器
    ├─ 复用：SDK facade → Skill开发者SDK
    └─ 复用：CI/CD模板 → 项目DevOps流程
    │
    自研业务层
    ├─ 运营驾驶舱前端（React + Vite）
    ├─ 素人矩阵管理API
    └─ 内容生成与合规检测Pipeline
```

### 3.3 两个项目的整合策略

| 维度 | hermes-agent（Python） | openclaw（TypeScript/Node） | 整合方式 |
|------|------------------------|----------------------------|----------|
| **职责** | AI Agent智能层 | SaaS应用服务层 | Python负责AI，Node负责业务API |
| **通信** | — | — | gRPC / HTTP + 共享Redis |
| **部署** | Docker容器 | Docker容器 | docker-compose编排 |
| **数据** | 处理中不存储 | 持久化存储 | Node写DB，Python读配置 |
| **扩展** | Skill进化 | 插件市场 | Skill作为特殊插件类型 |

---

## 四、GitHub 开源项目选型矩阵

> **本地离线副本**：以下所有标记为 ✅ 引入的开源项目，均已下载至 `D:\project\EcoDreamOmni\vendor\` 目录，详见 `vendor/README.md`。本地副本用于稳定参考、源码级调试与离线构建。
> 
> | 分类 | 本地路径 |
> |------|----------|
> | AI 框架 | `vendor/ai-frameworks/hermes-agent`（符号链接）、`vendor/ai-frameworks/litellm` |
> | 后端框架 | `vendor/backend-frameworks/{fastapi,celery,sqlalchemy,alembic}` |
> | 浏览器自动化 | `vendor/browser-automation/{playwright,rebrowser-patches}` |
> | 设计系统 | `vendor/design-systems/{shadcn-ui,radix-ui,radix-themes}` |
> | 前端库 | `vendor/frontend-libraries/{tanstack-table,tanstack-query,zustand,react-hook-form,zod,recharts}` |
> | 基础设施 | `vendor/infrastructure-tools/openclaw`（符号链接）、`vendor/infrastructure-tools/{storybook,ladle}` |
> | ML 库 | `vendor/ml-libraries/{scikit-learn,xgboost,shap,statsmodels,jieba}` |

### 4.1 Agent与LLM层

| 项目 | Stars | 选型 | 用途 | 替代自研工作量 |
|------|-------|------|------|---------------|
| **hermes-agent**（本地） | — | ✅ 复用 | Agent底座 | 节省 4人月 |
| **LiteLLM** | 15k+ | ✅ 引入 | LLM统一路由网关 | 节省 2人月 |
| **LangChain** | 106k+ | ⚠️ 部分引入 | 仅复用Document Loader和Text Splitter | 节省 0.5人月 |
| **CrewAI** | 高 | ❌ 不引入 | hermes-agent已覆盖多Agent编排 | — |
| **OpenAI Agents SDK** | 8.6k+ | ❌ 不引入 | 过于绑定OpenAI，不满足多模型需求 | — |

### 4.2 浏览器自动化与反检测层

| 项目 | Stars | 选型 | 用途 | 替代自研工作量 |
|------|-------|------|------|---------------|
| **Playwright** | 70k+ | ✅ 引入 | 浏览器自动化底座 | 节省 3人月 |
| **rebrowser-patches** | 3k+ | ✅ 引入 | Playwright反检测补丁（Runtime.Enable leak修复） | 节省 2人月 |
| **puppeteer-extra-plugin-stealth** | 10k+ | ✅ **引入** | 修补15+检测向量（navigator.webdriver/WebGL/plugins等） | 节省 1.5人月 |
| **owl-light** | 1k+ | ✅ **引入** | C++源码级指纹虚拟化Chromium，15套VM配置 | 节省 2人月 |
| **undetectable-fingerprint-browser** | 500+ | ❌ 不引入 | 需合并Chromium源码，过重 | — |

### 4.3 前端UI层

| 项目 | Stars | 选型 | 用途 | 替代自研工作量 |
|------|-------|------|------|---------------|
| **Storybook 8** | 84k+ | ✅ 引入 | 组件文档、交互测试、视觉回归 | 节省 2人月 |
| **Ladle** | 3k+ | ✅ 引入 | 开发期快速组件预览（6.7x冷启动速度） | 节省 0.5人月 |
| **shadcn/ui** | 80k+ | ✅ 引入 | Headless UI组件（Button/Dialog/Table/Form等） | 节省 3人月 |
| **Radix UI** | 15k+ | ✅ 间接引入 | shadcn/ui底层依赖 | — |
| **TanStack Table** | 30k+ | ✅ 引入 | 数据表格（账号池、内容库） | 节省 1人月 |
| **TanStack Query** | 42k+ | ✅ 引入 | 服务端状态管理 | 节省 1人月 |
| **Zustand** | 47k+ | ✅ 引入 | 客户端状态管理 | 节省 0.5人月 |
| **React Hook Form** | 41k+ | ✅ 引入 | 表单处理与校验 | 节省 0.5人月 |
| **Zod** | 36k+ | ✅ 引入 | Schema校验（前后端共享） | 节省 0.5人月 |

### 4.4 后端与基础设施层

| 项目 | Stars | 选型 | 用途 | 替代自研工作量 |
|------|-------|------|------|---------------|
| **FastAPI** | 82k+ | ✅ 引入 | Python AI服务API框架 | 节省 1人月 |
| **Celery** | 24k+ | ✅ 引入 | 分布式任务队列（内容生成、发布调度） | 节省 1人月 |
| **BullMQ** | 12k+ | ⚠️ 备选 | 如Node侧需队列，备选BullMQ | 备选 |
| **Prisma** | 42k+ | ✅ 引入 | TypeScript ORM + 数据库迁移 | 节省 1人月 |
| **SQLAlchemy 2.0** | — | ✅ 引入 | Python ORM | 节省 0.5人月 |
| **Alembic** | — | ✅ 引入 | 数据库迁移工具 | 节省 0.3人月 |
| **PostgreSQL 16** | — | ✅ 引入 | 主数据库 | — |
| **Redis 7** | — | ✅ 引入 | 缓存 + 消息队列 + 会话 | — |
| **MinIO** | 48k+ | ✅ 引入 | 对象存储（图片、内容素材） | 节省 0.5人月 |
| **Prometheus + Grafana** | — | ✅ 引入 | 监控与告警 | 节省 1人月 |
| **Sentry** | — | ✅ 引入 | 错误追踪 | 节省 0.5人月 |

### 4.5 数据科学与ML层

| 项目 | Stars | 选型 | 用途 | 替代自研工作量 |
|------|-------|------|------|---------------|
| **scikit-learn** | — | ✅ 引入 | 流量预测基线模型（回归/分类） | 节省 1人月 |
| **XGBoost** | 26k+ | ✅ 引入 | 流量预测主力模型 | 节省 0.5人月 |
| **SHAP** | 23k+ | ✅ 引入 | 模型可解释性 | 节省 0.5人月 |
| **statsmodels** | — | ✅ 引入 | ARIMA时间序列预测 | 节省 0.3人月 |
| **jieba** | 32k+ | ✅ 引入 | 中文分词（合规检测、内容分析） | 节省 0.3人月 |

### 4.6 可观测性层（PRD V2.4–V2.6 新增）

| 项目 | Stars | 选型 | 用途 | 替代自研工作量 |
|------|-------|------|------|---------------|
| **OpenTelemetry Python** | 2k+ | ✅ 引入 | AgentWatch Trace/Metrics 统一采集 SDK；支持 Celery/Redis/FastAPI 自动探针 | 节省 1.5人月 |
| **Prometheus Python Client** | 4.3k+ | ✅ 引入 | AgentMetrics 自定义指标暴露（Counter/Histogram/Gauge）；与 Prometheus+Grafana 零摩擦对接 | 节省 0.5人月 |
| **Jaeger** | 22.7k+ | ✅ 引入 | CNCF Graduated 链路追踪后端，OTLP 原生支持，GenAI/Agent Trace 可视化 | 节省 1人月 |
| **Zipkin** | 17.4k+ | ❌ 不引入 | OTLP 支持需额外适配，社区活跃度与云原生集成深度低于 Jaeger | — |

### 4.7 韧性治理层（PRD V2.5–V2.6 新增）

| 项目 | Stars | 选型 | 用途 | 替代自研工作量 |
|------|-------|------|------|---------------|
| **pybreaker** | 655+ | ✅ 引入 | LLM Hub 熔断器，Closed/Open/Half-Open 三态机，支持 Redis 分布式状态存储 | 节省 0.5人月 |
| **stamina** | 1.5k+ | ✅ 引入 | CronHub/Workflow Engine/LLM Hub 通用重试库，指数退避+jitter，内置 Prometheus 埋点 | 节省 0.5人月 |
| **circuitbreaker** | 515+ | ⚠️ 备选 | 更轻量但缺少 Redis 原生 backing；单体部署备选 | 备选 |
| **pyresilience** | 新兴 | ❌ 不引入 | Resilience4j Python 版，一站式韧性框架，但项目较新生产风险高 | — |

### 4.8 工作流与调度层（PRD V2.6 新增）

| 项目 | Stars | 选型 | 用途 | 替代自研工作量 |
|------|-------|------|------|---------------|
| **croniter** | 900+ | ✅ 引入 | CronHub 专用 Cron 解析内核，支持 L/W/# 扩展语法，与 Celery Beat 边界清晰 | 节省 0.3人月 |
| **transitions** | 6.5k+ | ✅ 引入 | Workflow Engine 状态机底座，Pipeline 状态流转 + 守卫回调 + 图形化导出 | 节省 0.5人月 |
| **APScheduler** | 6.6k+ | ❌ 不引入 | 与 Celery Beat 功能重叠，引入会造成调度源双轨 | — |
| **Luigi** | 19k+ | ❌ 不引入 | 批处理管道编排，社区活跃度下降，与 Celery 执行模型互不兼容 | — |
| **Prefect** | 22k+ | ❌ 不引入 | 完整工作流平台，与 Celery 大面积重叠，MVP 过重 | — |
| **Temporal** | 12k+ | ❌ 不引入 | 分布式持久执行平台，需独立 Server 集群，MVP 自研串行 Pipeline 足够 | — |

### 4.9 Prompt 管理与评估层（PRD V2.6 新增）

| 项目 | Stars | 选型 | 用途 | 替代自研工作量 |
|------|-------|------|------|---------------|
| **Langfuse** | 27k+ | ✅ 引入 | Prompt Registry 核心底座：版本化、Label 部署、Diff 对比、效果追踪；与 LiteLLM 官方集成 | 节省 1.5人月 |
| **DeepEval** | 14k+ | ✅ 引入 | AgentMetrics 质量评分引擎，50+ LLM-as-Judge 指标，pytest 原生集成 | 节省 1人月 |
| **Promptfoo** | 13k+ | ❌ 不引入 | 被 OpenAI 收购后开源走向存疑；TypeScript 为主与 Python 后端生态契合度低 | — |
| **Traceloop** | 7k+ | ❌ 不引入 | 被 ServiceNow 收购，Prompt 管理仅为附属功能 | — |
| **Arize Phoenix** | 9.5k+ | ❌ 不引入 | ELv2 许可证非 OSI 认证，存在法务合规风险 | — |

---

## 五、技术架构实施方案

### 5.1 系统架构图（开源集成版）

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SaaS 运营驾驶舱（React + Vite + Storybook）         │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐  │
│  │任务看板 │ │流量预演 │ │账号健康 │ │ 人设库  │ │规则中心 │ │数据报表 │  │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼ HTTP/WebSocket
┌─────────────────────────────────────────────────────────────────────────────┐
│                      API Gateway（基于 openclaw 网关协议）                     │
│                    Node.js + Fastify / Python + FastAPI                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        ▼                           ▼                           ▼
┌───────────────┐         ┌───────────────┐         ┌───────────────────────┐
│   Node服务层   │         │  Python AI层   │         │      数据存储层        │
│ (基于openclaw) │         │(基于hermes-agent)│       │                       │
├───────────────┤         ├───────────────┤         ├───────────────────────┤
│ 业务API服务    │◄───────►│ Orchestrator   │         │   PostgreSQL 16       │
│ 用户/租户管理  │         │ ContentForge   │         │   (主数据持久化)       │
│ 权限RBAC      │         │ ComplianceGuard│         │                       │
│ 插件/扩展系统  │         │ PoolPredictor  │         │   Redis 7             │
│              │         │ SkillSmith     │         │   (缓存+队列+会话)     │
│              │         │ DataAnalyst    │         │                       │
│              │         │ ContentInsight │         │   MinIO               │
│              │         │ TrendScout     │         │   (对象存储)           │
│              │         │ Publisher      │         │                       │
└───────────────┘         └───────────────┘         └───────────────────────┘
        │                           │                           │
        ▼                           ▼                           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│              平台账号管理层（PlatformAccountManager — 审核新增 🔴）             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │ 平台登录适配 │  │  Cookie仓库  │  │ Session管理  │  │  登录界面    │       │
│  │  (小红书/   │  │ (Redis加密)  │  │(自动刷新/   │  │(二维码/导入)│       │
│  │  抖音/视频号)│  │             │  │  过期检测)   │  │             │       │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘       │
└─────────────────────────────────────────────────────────────────────────────┘
        │                           │                           │
        ▼                           ▼                           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      技术对抗层（Playwright + rebrowser-patches）             │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐                         │
│  │指纹差异化│ │IP代理池 │ │行为仿真 │ │请求签名 │ │指纹/IP  │                         │
│  │(自研引擎)│ │(第三方) │ │(自研库) │ │(x-s/x-t)│ │ 信誉系统 │                         │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 各模块开源/自研边界

| 模块 | 开源组件 | 自研部分 | 人天估算 |
|------|----------|----------|----------|
| **运营驾驶舱** | React 19 + Vite 6 + shadcn/ui + TanStack Table/Query + Zustand | 业务页面（任务看板、账号健康、数据报表等） | 30人天 |
| **API Gateway** | FastAPI / Fastify | 多租户隔离、权限RBAC、API版本管理 | 15人天 |
| **Orchestrator** | hermes-agent调度逻辑 | DAG工作流引擎、Agent间ACP协议、冲突仲裁 | 20人天 |
| **ContentForge** | hermes-agent Prompt构建器 | Voice注入、差异化生成、合规Prompt模板 | 15人天 |
| **ComplianceGuard** | jieba分词 | 三层规则引擎（L1/L2/L3）、证据链留存 | 20人天 |
| **PoolPredictor** | **scikit-learn**（`QuantileRegressor` / Ridge+残差分位）+ **statsmodels**（ARIMA 仅 Phase 2+ 时段）；Phase 2+ **XGBoost + SHAP** | 特征工程、先验表、`interval_mode`、**异步**重训（Celery）；小样本禁上深度网 | 20人天 |
| **PlatformAccountManager** | Playwright + rebrowser-patches | 平台登录适配器、Cookie仓库、Session管理、登录UI | 20人天 |
| **AccountPool** | Playwright + rebrowser-patches | 指纹信誉系统、IP信誉系统、健康度评分、异常熔断 | 30人天 |
| **Publisher** | Playwright发布API | 错峰调度、排版随机化、配图处理 | 15人天 |
| **SkillHub** | hermes-agent Skill进化 | 四层加载架构、版本管理、Marketplace、Agent-Skill绑定 | 20人天 |
| **LLM Gateway** | LiteLLM | 模型路由、成本优化、故障降级、Token预算控制 | 10人天 |
| **用户认证** | OAuth2/SSO库 + JWT | JWT+RBAC认证、多租户隔离、登录风控、MFA | 12人天 |
| **TrendScout** | Mock 数据源、文件/表单导入 | 趋势报告 schema、阶段过滤、与 ContentForge 对接 | 10人天 |
| **DataAnalyst** | Pandas + Matplotlib + **Celery** | 导入解析、报表、**N_min** 子集覆盖率/MAPE、异步校准触发 | 12人天 |
| **AgentHub** | — | Agent 注册发现、配置版本化、环境隔离、RBAC 权限、依赖声明 | 10人天 |
| **AgentWatch** | **OpenTelemetry Python**（Trace/Metrics 采集）+ **Jaeger**（Trace 后端）| 心跳健康检查、实时状态看板、规则引擎异常检测、分级告警 | 12人天 |
| **AgentMetrics** | **Prometheus Python Client**（指标暴露）+ **DeepEval**（质量评分）| 任务完成率、Token 成本归因、延迟分布、质量评分、人机干预率 | 10人天 |
| **LLM Hub** | **LiteLLM** Router（底层路由）+ **pybreaker**（熔断器）+ **stamina**（重试）| 模型注册、三层配置（Global/Agent/Skill）、成本治理、合规预检 | 12人天 |
| **CronHub** | **Celery Beat**（调度引擎）+ **croniter**（Cron 解析）+ **stamina**（重试）| Job Registry、Schedule Engine、Execution Runner、Retry & DLQ | 10人天 |
| **TaskHub** | **transitions**（状态机）+ **Celery**（任务队列）| 任务创建、状态机、队列管理、批量任务、定时任务绑定 | 8人天 |
| **Workflow Engine** | **transitions**（Pipeline 状态流转）+ **Celery**（节点执行）| 串行模板定义、上下文传递（Redis）、失败策略、预设模板 | 12人天 |
| **Prompt Registry** | **Langfuse**（Prompt 版本化底座）+ **Jinja2** SandboxedEnvironment（安全渲染）| 变量白名单校验、效果追踪、环境隔离、安全约束 | 8人天 |
| **Human-in-the-Loop** | — | 审核台视图、审核决策（通过/驳回/打回）、双人复核、反馈闭环 | 10人天 |

---

## 六、UI 系统方案（Storybook + Vite）

### 6.1 前端技术栈

| 层级 | 选型 | 版本 | 理由 |
|------|------|------|------|
| **构建工具** | Vite | 6.x | 极速冷启动、ESM原生、与Storybook深度集成 |
| **UI框架** | React | 19.x | 并发特性、Server Components（可选） |
| **语言** | TypeScript | 5.7+ | 类型安全、IDE体验 |
| **样式** | TailwindCSS | 4.x | 原子化CSS、设计系统一致 |
| **组件库** | shadcn/ui + Radix UI | latest | Headless可定制、无障碍支持 |
| **状态管理** | Zustand + TanStack Query | latest | 轻量客户端状态 + 强大服务端状态 |
| **表单** | React Hook Form + Zod | latest | 性能优秀、类型安全校验 |
| **表格** | TanStack Table | latest | 高性能虚拟滚动、排序过滤 |
| **图表** | Recharts / Tremor | latest | React原生图表、Dashboard友好 |
| **组件文档** | Storybook 8 | 8.x | 行业事实标准、交互测试、视觉回归 |
| **快速预览** | Ladle | 4.x | 开发期6.7x更快冷启动 |

### 6.2 组件分层架构

```
ui/
├── .storybook/              # Storybook配置
│   ├── main.ts
│   ├── preview.ts
│   └── preview-head.html
├── .ladle/                  # Ladle配置（快速预览）
├── public/
├── src/
│   ├── main.tsx             # 应用入口
│   ├── App.tsx
│   ├── components/          # 业务组件
│   │   ├── dashboard/       # 驾驶舱组件
│   │   │   ├── TaskBoard.tsx
│   │   │   ├── TaskBoard.stories.tsx
│   │   │   └── TaskBoard.test.tsx
│   │   ├── content/         # 内容管理组件
│   │   ├── account/         # 账号管理组件
│   │   ├── compliance/      # 合规审核组件
│   │   ├── persona/         # 人设管理组件
│   │   └── data/            # 数据报表组件
│   │
│   ├── ui/                  # shadcn/ui 基础组件
│   │   ├── button.tsx
│   │   ├── dialog.tsx
│   │   ├── table.tsx
│   │   ├── form.tsx
│   │   ├── input.tsx
│   │   ├── select.tsx
│   │   ├── tabs.tsx
│   │   └── ...
│   │
│   ├── hooks/               # 自定义Hooks
│   ├── lib/                 # 工具函数
│   ├── stores/              # Zustand状态
│   ├── services/            # API服务层
│   └── types/               # 类型定义
│
├── package.json
├── vite.config.ts
├── tailwind.config.ts
├── tsconfig.json
└── vitest.config.ts
```

### 6.3 Storybook 配置策略

**开发期**：Ladle 作为快速预览工具，6.7x 冷启动速度优势，用于日常组件开发。

**文档期 + 测试期**：Storybook 8 作为正式组件文档和交互测试平台。

**部署**：Storybook 静态站点部署至内部文档站点。

```json
// package.json scripts
{
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "ladle": "ladle serve",
    "ladle:build": "ladle build",
    "storybook": "storybook dev -p 6006",
    "storybook:build": "storybook build",
    "test": "vitest",
    "test:coverage": "vitest --coverage",
    "test:ui": "vitest --ui",
    "typecheck": "tsc --noEmit",
    "lint": "oxlint src/",
    "format": "oxfmt src/"
  }
}
```

### 6.4 核心页面组件清单

| 页面/模块 | 核心组件 | 复杂度 | 是否自研 |
|----------|----------|--------|----------|
| **登录与认证** | LoginPage, MFAVerify, OAuthCallback, PasswordReset | 中 | 自研 |
| **运营主页** | DashboardHome, QuickActionPanel, TodayOverview, AlertBanner, ShortcutNav | 中 | 自研 |
| **任务看板** | TaskBoard, TaskCard, TaskFilter | 中 | 自研 |
| **流量预演** | PredictionPanel, PredictionChart, OptimizationSuggestions | 高 | 自研 |
| **账号健康** | AccountHealthChart, HealthScoreRing, RiskAlert | 中 | 自研 |
| **内容库** | ContentList, ContentEditor, ContentPreview | 高 | 自研 |
| **人设库** | PersonaCard, VoiceEditor, TemplateSelector | 中 | 自研 |
| **合规预检** | CompliancePanel, RuleMatcher, SuggestionList | 高 | 自研 |
| **数据报表** | DashboardGrid, MetricCard, TrendChart, Heatmap | 中 | 自研 |
| **素人管理** | AccountTable, AccountDetail, BatchOperationBar | 中 | 自研 |
| **规则中心** | RuleEditor, RuleTester, VersionHistory | 中 | 自研 |
| **通用** | Button, Dialog, Table, Form, Input, Select, Tabs, Toast | 低 | shadcn/ui |

---

### 6.5 登录模块与运营主页设计

#### 6.5.1 登录模块设计

**模块定位**：多租户SaaS平台的安全入口，支持品牌方/代运营公司多角色登录。

```
┌─────────────────────────────────────────────────────────────┐
│                      登录页面（LoginPage）                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   ┌─────────────────────────────────────────────────────┐   │
│   │  Logo + 产品名称                                       │   │
│   │  "宠物健康素人号矩阵AI平台"                             │   │
│   └─────────────────────────────────────────────────────┘   │
│                                                              │
│   ┌─────────────────────────────────────────────────────┐   │
│   │  [邮箱输入框]                                         │   │
│   │  [密码输入框]  [显示/隐藏]                             │   │
│   │  [记住我]  [忘记密码？]                                │   │
│   │                                                      │   │
│   │  [🟢 登录按钮]                                        │   │
│   │                                                      │   │
│   │  ─────── 或 ───────                                   │   │
│   │  [企业微信登录]  [飞书登录]                            │   │
│   └─────────────────────────────────────────────────────┘   │
│                                                              │
│   还没有账号？ [联系销售开通试用]                           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**核心功能**：

| 功能 | 说明 | 技术实现 |
|------|------|----------|
| **邮箱+密码登录** | 主登录方式，支持记住我（7天） | JWT Access Token（15分钟）+ Refresh Token（7天），存储于HttpOnly Cookie |
| **企业微信OAuth** | 企业客户SSO登录 | 企业微信开放平台OAuth2.0流程 |
| **飞书OAuth** | 企业客户SSO登录 | 飞书开放平台OAuth2.0流程 |
| **多因素认证（MFA）** | 敏感操作二次验证 | TOTP（基于时间的一次性密码），支持Google Authenticator/企业微信扫码 |
| **密码安全** | 强密码策略 | bcrypt哈希，最小8位，必须含大小写+数字+特殊字符 |
| **登录风控** | 防暴力破解 | 同一IP 5分钟内失败3次→验证码；失败5次→锁定15分钟 |
| **租户隔离** | 多品牌数据隔离 | JWT Payload包含tenant_id，API Gateway层校验 |

**登录后路由分发**：

```
登录成功
    │
    ├─ 角色 = 系统管理员 → /admin/tenants
    ├─ 角色 = 运营主管 → /dashboard（运营主页）
    ├─ 角色 = 矩阵运营 → /dashboard（运营主页）→ 默认打开任务看板
    ├─ 角色 = 内容策划 → /dashboard（运营主页）→ 默认打开内容库
    ├─ 角色 = 合规专员 → /dashboard（运营主页）→ 默认打开合规审核
    └─ 角色 = 技术运维 → /dashboard（运营主页）→ 默认打开账号健康
```

**后端API**：

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/auth/login` | POST | 邮箱密码登录，返回JWT |
| `/api/v1/auth/refresh` | POST | Refresh Token续期 |
| `/api/v1/auth/logout` | POST | 登出，作废Token |
| `/api/v1/auth/mfa/setup` | POST | 绑定MFA设备 |
| `/api/v1/auth/mfa/verify` | POST | MFA验证码校验 |
| `/api/v1/auth/oauth/wechat-work` | GET | 企业微信OAuth入口 |
| `/api/v1/auth/oauth/feishu` | GET | 飞书OAuth入口 |
| `/api/v1/auth/password/reset` | POST | 密码重置请求 |

#### 6.5.2 平台账号登录与 Cookie 管理（审核新增 🔴）

> **定位**：这是整个矩阵运营系统的**前置 blocker**。没有平台账号登录态，TrendScout、Publisher、DataAnalyst 全部无法工作。

**架构设计**：

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PlatformAccountManager 平台账号管理层                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐  ┌─────────────┐ │
│  │ 平台登录适配器 │  │   Cookie 仓库  │  │ Session 管理器 │  │  登录界面    │ │
│  │   (Adapter)   │  │   (Storage)   │  │   (Manager)   │  │   (UI)      │ │
│  ├───────────────┤  ├───────────────┤  ├───────────────┤  ├─────────────┤ │
│  │• 小红书适配    │  │• Redis 持久化  │  │• 过期自动检测  │  │• Cookie导入 │ │
│  │• 抖音适配      │  │• AES-256加密  │  │• 自动刷新      │  │• 二维码登录 │ │
│  │• 视频号适配    │  │• 多租户隔离   │  │• 异常告警      │  │• 短信登录   │ │
│  │• 插件化注册    │  │• 审计日志     │  │• 状态机转换    │  │• 批量导入   │ │
│  └───────────────┘  └───────────────┘  └───────────────┘  └─────────────┘ │
│                                                                              │
│  Session 状态机：                                                            │
│  ┌─────────┐    登录成功     ┌─────────┐    操作检测     ┌─────────┐       │
│  │ 未登录   │ ─────────────→ │  正常   │ ─────────────→ │  活跃   │       │
│  │ offline │                 │ active  │                 │  hot    │       │
│  └────┬────┘                 └────┬────┘                 └────┬────┘       │
│       │    登录失败/风控           │    触发验证码            │    异常     │
│       └────────────────────────→  │  ────────────────────→  │  ────────→  │
│                                   │                         │             │
│                              ┌────┴────┐               ┌────┴────┐        │
│                              │ warming │               │restricted│       │
│                              │ (冷却)   │               │ (受限)   │       │
│                              └────┬────┘               └────┬────┘        │
│                                   │    冷却结束              │    人工介入  │
│                                   └────────────────────────→ │  ────────→  │
│                                                              │  recycled   │
│                                                              │  (回收)     │
│                                                              └─────────────┘
└─────────────────────────────────────────────────────────────────────────────┘
```

**支持的登录方式**：

| 方式 | 适用场景 | 技术实现 | 复杂度 |
|------|----------|----------|--------|
| **Cookie 批量导入** | 已有登录态的账号迁移 | 运营人员从浏览器导出 Cookie → 后台解析 → Redis 加密存储 | 低 |
| **二维码扫码登录** | 新号首次登录 | Playwright 打开登录页 → 截图二维码 → 运营人员扫码 → 轮询登录状态 | 中 |
| **短信验证码登录** | 手机号密码登录 | Playwright 输入手机号 → 触发验证码 → 运营人员/接码平台输入 → 登录 | 中 |
| **Session 自动刷新** | 维持长期登录态 | 定时访问首页检测登录状态 → Cookie 过期前自动刷新 → 失效时告警 | 高 |

**Cookie 存储规范（以小红书为例）**：

```typescript
interface PlatformCookie {
  platform: 'xiaohongshu' | 'douyin' | 'wechat_channels';
  account_id: string;           // 内部账号ID
  cookies: {
    name: string;
    value: string;
    domain: string;
    path: string;
    expires: number;
    httpOnly: boolean;
    secure: boolean;
  }[];
  local_storage: Record<string, string>;  // localStorage 中的关键数据
  signature_token?: string;     // x-s/x-t 等签名相关的缓存
  fingerprint_id: string;       // 关联的浏览器指纹ID
  created_at: string;
  updated_at: string;
  expires_at: string;           // 预计过期时间
  status: 'active' | 'expired' | 'invalid' | 'refreshing';
}
```

**关键约束**：
- Cookie 必须 AES-256 加密存储，密钥按租户隔离
- 禁止在日志中输出任何 Cookie 值（脱敏处理）
- 同一平台账号同一时间只能在一个浏览器 Context 中使用
- 登录失败 ≥2 次自动进入 `warming` 状态，冷却 24h

**W3.5 交付标准**：
- [ ] 小红书 Cookie 导入登录 → 验证可访问首页
- [ ] 二维码登录流程 → 从截图到登录完成的全流程
- [ ] Session 状态检测 → 可判断 Cookie 是否有效
- [ ] Cookie 加密存储 → Redis + AES-256，审计日志
- [ ] 前端登录界面 → Cookie 导入/二维码/短信三种方式

#### 6.5.3 运营主页设计

**模块定位**：运营人员每日工作的「指挥中心」，一屏展示所有关键信息和快捷操作。

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Header: 欢迎回来，张运营 │ XX宠物健康 │ [🔔 告警] [👤 个人中心] [⏏️ 退出]  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Quick Action Panel（快捷操作栏）                   │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  │   │
│  │  │ 📝 生成  │  │ 📤 分发  │  │ 🔍 审核  │  │ 📊 报表  │  │ ⚙️ 配置  │  │   │
│  │  │ 今日内容 │  │ 待发布  │  │ 待审内容 │  │ 昨日数据 │  │ 账号设置 │  │   │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────────────┐  ┌─────────────────────────────────────────┐   │
│  │  Today Overview          │  │  Alert Banner（实时告警）               │   │
│  │  （今日概览）             │  │                                         │   │
│  │                          │  │  🔴 [紧急] 账号 acc_003 触发验证码       │   │
│  │  📋 今日任务：10篇待生成  │  │  🟡 [警告] 2篇内容合规预检黄标           │   │
│  │  📤 待分发：15篇         │  │  🟢 [提示] 新号 acc_008 养号期结束       │   │
│  │  🔍 待审核：5篇          │  │  🔵 [信息] 流量预测模型已更新            │   │
│  │  ✅ 已发布：8篇          │  │                                         │   │
│  │                          │  │                                         │   │
│  │  📈 今日互动量：+23%     │  │                                         │   │
│  │  📉 账号健康均值：87     │  │                                         │   │
│  └─────────────────────────┘  └─────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Shortcut Nav（快捷导航卡片）                       │   │
│  │                                                                     │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐│   │
│  │  │ 📋 任务看板  │  │ 📝 内容库   │  │ 👤 素人管理  │  │ 📊 数据报表  ││   │
│  │  │ 3个活跃任务  │  │ 120篇内容   │  │ 45个账号    │  │ 周增长+12%  ││   │
│  │  │ [进入]      │  │ [进入]      │  │ [进入]      │  │ [进入]      ││   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘│   │
│  │                                                                     │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐│   │
│  │  │ 🎭 人设库   │  │ ⚖️ 规则中心  │  │ 🧠 SkillHub │  │ ⚙️ 系统设置  ││   │
│  │  │ 12个人设    │  │ 48条规则    │  │ 8个内置    │  │ 团队管理    ││   │
│  │  │ [进入]      │  │ [进入]      │  │ [进入]      │  │ [进入]      ││   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Recent Activity（最近活动日志）                                      │   │
│  │  09:15 张运营 生成了 5 篇「猫咪驱虫」内容                             │   │
│  │  09:08 李合规 审核通过了 3 篇内容                                     │   │
│  │  08:45 系统   账号 acc_003 触发验证码，已进入保护模式                 │   │
│  │  08:30 张运营 向 15 个素人分发了 Brief                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**运营主页数据结构**：

```typescript
interface DashboardHomeData {
  today: {
    tasksPending: number;      // 待生成内容数
    briefsPending: number;     // 待分发Brief数
    contentsPendingReview: number; // 待审核内容数
    contentsPublished: number; // 今日已发布数
    engagementDelta: number;   // 互动量环比
    avgHealthScore: number;    // 账号健康均值
  };
  alerts: DashboardAlert[];    // 实时告警列表
  shortcuts: ShortcutCard[];   // 快捷导航卡片
  recentActivity: ActivityLog[]; // 最近活动日志
}

interface DashboardAlert {
  id: string;
  level: 'critical' | 'warning' | 'info' | 'success';
  title: string;
  description: string;
  timestamp: string;
  action?: { label: string; href: string };
}

interface ShortcutCard {
  id: string;
  icon: string;
  title: string;
  subtitle: string;
  href: string;
  badge?: number; // 角标数字
}
```

**个性化配置**：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| 默认打开模块 | 登录后默认展示的子页面 | 按角色分配 |
| 快捷操作栏 | 顶部5个快捷按钮可自定义 | 按角色预置 |
| 告警级别过滤 | 只显示某级别以上的告警 | warning及以上 |
| 数据刷新频率 | 实时数据轮询间隔 | 30秒 |
| 主题 | 亮色/暗色模式 | 跟随系统 |

---

## 七、工程纪律规范（红绿灯 TDD + Agentic Engineering）

### 7.1 红绿灯 TDD 循环（核心引擎）

```
┌─────────────────────────────────────────────────────────────────┐
│                    🚦 红绿灯 TDD 循环                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Step 1: 🔴 红灯阶段                                           │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ 1. 根据需求/任务单，编写自动化测试用例                       │   │
│   │ 2. 运行测试 → 必须看到测试失败（红灯）                       │
│   │ 3. 纪律：测试直接通过 = 测试写得有问题，需重写               │   │
│   └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│   Step 2: 🟢 绿灯阶段                                           │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ 1. 编写最小化代码实现功能                                    │   │
│   │ 2. 运行测试 → 必须看到测试通过（绿灯）                       │   │
│   │ 3. 纪律：禁止过度实现，只需让测试通过即可                    │   │
│   └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│   Step 3: 🔵 重构阶段                                           │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ 1. 在绿灯保障下，优化代码结构、消除重复                      │   │
│   │ 2. 运行全部测试 → 确保重构不破坏已有功能                     │   │
│   │ 3. 纪律：重构必须有测试保护，禁止无测试覆盖的重构            │   │
│   └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│   循环：回到 Step 1，开始下一个功能的红灯阶段                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 四条工程纪律

#### 纪律一：上下文隔离（短对话与原子化）

```
❌ 禁止：在一个对话框里完成从数据库设计到前端页面的所有工作
✅ 要求：一个会话，一个任务

任务原子化示例：
├─ Task 1: 定义 AccountPool 数据模型 + 编写模型测试
├─ Task 2: 实现 AccountPool 创建接口 + 编写接口测试
├─ Task 3: 实现 AccountPool 查询接口 + 编写接口测试
├─ Task 4: 编写 AccountPool 前端列表组件 + Storybook Story
├─ Task 5: 编写 AccountPool 前端列表组件测试
└─ ...

状态移交模板（新会话开头）：
"当前正在开发 AccountPool 模块。
已完成：数据模型、创建/查询接口。
当前任务：实现分页查询接口。
相关文件：
- backend/src/models/account.py
- backend/src/api/accounts.py
- 测试文件：backend/tests/test_accounts.py（当前通过 5/5）"
```

#### 纪律二：规范定义（AI 入职手册 AGENTS.md）

**项目根目录必须创建 `AGENTS.md`**：

```markdown
# AGENTS.md — AI 开发入职手册

## 技术栈锁定

| 层级 | 技术 | 版本 | 禁止替换 |
|------|------|------|----------|
| 前端 | React + Vite + TypeScript | 19 + 6 + 5.7 | 禁止用 Vue/Angular |
| 前端样式 | TailwindCSS + shadcn/ui | v4 + latest | 禁止用 MUI/Chakra |
| 前端状态 | Zustand + TanStack Query | latest | 禁止用 Redux |
| 前端测试 | Vitest + Testing Library | latest | 禁止用 Jest |
| 前端文档 | Storybook 8 + Ladle | 8.x + 4.x | — |
| 后端API | FastAPI + Python 3.11 | latest | 禁止用 Django/Flask |
| 后端ORM | SQLAlchemy 2.0 + Alembic | latest | 禁止用 Django ORM |
| 数据库 | PostgreSQL 16 + Redis 7 | — | — |
| AI层 | hermes-agent（Python） | v0.13 | — |
| 队列 | Celery + Redis | latest | — |
| 容器 | Docker + Docker Compose | latest | — |

## 目录结构

```
project/
├── AGENTS.md              # 本文件
├── backend/               # Python AI服务
│   ├── src/
│   │   ├── agents/        # 9大Agent业务逻辑
│   │   ├── models/        # 数据模型
│   │   ├── api/           # API路由
│   │   ├── services/      # 业务服务
│   │   ├── core/          # 核心工具
│   │   └── tests/         # 测试目录
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/              # React前端
│   ├── src/
│   │   ├── components/    # 业务组件
│   │   ├── ui/            # shadcn/ui 基础组件
│   │   ├── hooks/         # 自定义Hooks
│   │   ├── stores/        # Zustand状态
│   │   ├── services/      # API服务
│   │   └── types/         # 类型定义
│   ├── package.json
│   ├── vite.config.ts
│   └── Dockerfile
├── hermes-agent/          # 本地子模块（hermes-agent-main）
├── openclaw/              # 本地子模块（openclaw-main）
├── docker-compose.yml
└── Makefile
```

## 核心命令

```bash
# 安装依赖
make install

# 运行全部测试
make test          # backend: pytest, frontend: vitest
make test:coverage # 带覆盖率

# 运行类型检查
make typecheck     # frontend: tsc --noEmit

# 格式化与Lint
make format        # oxfmt / black
make lint          # oxlint / ruff

# 启动开发环境
make dev           # docker-compose up + vite dev

# 构建
make build         # docker-compose build
```

## 负面清单（绝对禁止）

1. 禁止在 Controller/API 层直接操作数据库，必须通过 Service 层。
2. 禁止使用 `any` 类型，所有 TypeScript 代码必须有明确类型。
3. 禁止在 Python 代码中使用裸 SQL，必须使用 ORM。
4. 禁止在无测试覆盖的情况下编写业务逻辑代码。
5. 禁止提交包含 `console.log` 的代码（生产环境）。
6. 禁止前后端混用同一 ORM（前端用 Prisma，后端用 SQLAlchemy）。
7. 禁止在 Git 提交中包含 `.env` 文件或密钥。
8. 禁止修改 hermes-agent 和 openclaw 子模块的源码（如需修改，先 Fork）。
```

#### 纪律三：任务拆解（从规范到计划）

**每个开发任务必须以 `TASK.md` 形式记录**：

```markdown
# TASK: 实现账号健康度评分算法

## 关联文档
- 产品方案: `docs/product/account-health.md`
- 接口定义: `docs/api/account-health-api.md`

## 验收标准（Definition of Done）
- [ ] 实现 HealthScore 计算函数（含5个维度权重）
- [ ] 实现状态转换规则（active/warming/restricted/recycled/banned）
- [ ] 单元测试覆盖率 ≥ 90%
- [ ] 所有测试通过（绿灯）
- [ ] 类型检查通过
- [ ] 代码审查通过

## 子任务列表
1. [ ] 🔴 编写 HealthScore 计算函数的失败测试
2. [ ] 🟢 实现 HealthScore 计算函数，使测试通过
3. [ ] 🔵 重构代码，优化可读性
4. [ ] 🔴 编写状态转换规则的失败测试
5. [ ] 🟢 实现状态转换规则，使测试通过
6. [ ] 🔴 编写异常熔断逻辑的失败测试
7. [ ] 🟢 实现异常熔断逻辑，使测试通过
8. [ ] 运行全部测试，确保无回归
```

#### 纪律四：质量门禁（证据先行）

| 门禁 | 要求 | 证据 |
|------|------|------|
| **测试通过** | 所有新增代码必须有测试覆盖 | `pytest` / `vitest` 完整日志 |
| **类型检查** | TypeScript/Python 无类型错误 | `tsc --noEmit` / `mypy` 输出 |
| **Lint通过** | 无代码风格违规 | `oxlint` / `ruff` 输出 |
| **格式化** | 代码已格式化 | `oxfmt` / `black` 无变更 |
| **覆盖率** | 新增代码行覆盖率 ≥ 80% | coverage report |
| **构建成功** | Docker 构建无错误 | `docker-compose build` 日志 |

**PR模板**：
```markdown
## 变更描述
<!-- 简述本次变更内容 -->

## 测试证据
<!-- 粘贴测试运行完整日志 -->
```

## 测试日志

```bash
$ pnpm test src/components/TaskBoard/
 RUN  v2.1.1 /project/frontend

 ✓ src/components/TaskBoard/TaskBoard.test.tsx (5 tests) 45ms
   ✓ renders empty state
   ✓ renders task cards
   ✓ filters by status
   ✓ sorts by priority
   ✓ handles batch selection

 Test Files  1 passed (1)
      Tests  5 passed (5)
   Duration  45ms
```

## 类型检查
```bash
$ pnpm typecheck
> tsc --noEmit
# 无错误输出
```

## 覆盖率
```bash
$ pnpm test:coverage
 Coverage summary:
  Statements: 87.5% (42/48)
  Branches: 82.3% (14/17)
  Functions: 100% (8/8)
  Lines: 86.9% (40/46)
```

## 代码审查
- [ ] 自测通过
- [ ] 类型检查通过
- [ ] 测试覆盖率 ≥ 80%
```

### 7.3 CI/CD 质量门禁流水线

```yaml
# .github/workflows/ci.yml
name: CI Quality Gates

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: 🔴 Run Backend Tests
        run: cd backend && pytest -v --cov=src --cov-report=xml
      - name: 📊 Coverage Gate (≥80%)
        run: |
          COVERAGE=$(cat coverage.xml | grep -o 'line-rate="[0-9.]*"' | head -1 | cut -d'"' -f2)
          THRESHOLD=0.80
          if (( $(echo "$COVERAGE < $THRESHOLD" | bc -l) )); then
            echo "❌ Coverage $COVERAGE below threshold $THRESHOLD"
            exit 1
          fi
          echo "✅ Coverage $COVERAGE passes threshold"

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: 🔴 Run Frontend Tests
        run: cd frontend && pnpm test --run --coverage
      - name: 📊 Coverage Gate (≥80%)
        run: |
          COVERAGE=$(cat coverage/coverage-summary.json | jq '.total.lines.pct')
          if (( $(echo "$COVERAGE < 80" | bc -l) )); then
            echo "❌ Coverage $COVERAGE below threshold 80"
            exit 1
          fi
          echo "✅ Coverage $COVERAGE passes threshold"

  typecheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: 🔴 TypeScript Type Check
        run: cd frontend && pnpm typecheck
      - name: 🔴 Python Type Check
        run: cd backend && mypy src/

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: 🔴 Lint Check
        run: |
          cd frontend && pnpm lint
          cd ../backend && ruff check src/
```

---

## 八、完成度总览（实时更新）

> 本章节按阶段列出所有任务与交付物，**完成一项标注一项**。作为项目全局进度看板，每次推进后同步更新。

### Phase 0：项目准备（已完成 ✅）

**文档准备**：
- [x] 专家评估报告（`EcoDream_Omni_专家评估报告.md`）— 6 大专家组评审，全模块保留
- [x] 最终产品方案 v5.0（`EcoDream_Omni_完整产品方案_v2.md`）— 17 章，9 Agents + 4 Hubs + 3 分析引擎
- [x] 开发计划 v2.2（`开发计划_素人号矩阵AI平台_v2.md`）— 6 个月里程碑；**工程可靠性**与 PRD V2.3 对齐（2026-05-13）
- [x] PRD 文档（`EcoDream_Omni_PRD_v2_对齐核心方案.md`，**V2.3**）— 素人号矩阵 AI 平台产品需求（含 §2.6 双闭环边界）
- [x] 商业计划书（`EcoDream_Omni_商业计划书.md`）
- [x] 开发时间线视图（`开发时间线视图.md`）
- [x] 架构图汇总 v1/v2（`架构图汇总.md`、`架构图汇总_v2.md`）
- [x] 视频创作方案（`视频创作.md`）
- [x] 品牌 AI 项目方案（`品牌AI项目方案1.md`）

**技术准备**：
- [x] Agent/Skill 清单梳理 — 9 Agents + 8 内置 Skills + 动态 Evolved Skills，Agent-Skill 绑定矩阵
- [x] LLM 配置策略 — "主流程稳定 + Skills 灵活"，GPT-4o/Claude 3.5 主流程，国产模型全景映射
- [x] 开源依赖本地离线化 — `vendor/` 目录 **38** 个项目全部就位（33 个 git clone + 2 个本地符号链接 + 3 个 zip 下载）
- [x] `vendor/README.md` 本地路径索引创建
- [x] 开发计划文档本地路径引用更新

### Phase 1：MVP（第 1-2 个月，目标：20 账号核心闭环）

**周任务清单**：
- [x] **W1** — 项目初始化：脚手架搭建、AGENTS.md、CI/CD 流水线、Docker 构建测试 ✅
- [x] **W2** — 登录模块：JWT 认证、RBAC 权限、MFA、登录风控、登录页面实现 ✅
- [x] **W3** — 运营主页：数据聚合、快捷操作面板、实时告警、活动日志、Recharts 集成 ✅（后端 API 17/17，前端 20/20 零回归）
- [x] **W3.5** — 平台账号登录与 Cookie 管理（🔴 审核新增 blocker）：平台登录适配器、Cookie 仓库、Session 管理、二维码/Cookie 导入登录 ✅（后端 API 27/27，前端 20/20 零回归）
- [x] **W4** — AccountPool：账号 CRUD、平台登录集成、指纹差异化引擎基础、Playwright + rebrowser-patches 集成 ✅（后端 API 38/38，前端 20/20 零回归）
- [x] **W5** — ContentForge：内容生成基础、人设池 Voice 注入、hermes-agent Prompt 构建器复用 ✅（后端 API 48/48，前端 20/20 零回归）
- [x] **W6** — ComplianceGuard：L1/L2 规则引擎、合规检测基础、jieba 分词集成 ✅（后端 API 58/58，前端 20/20 零回归）
- [x] **W7** — Publisher：自动发布、错峰调度、Playwright 发布 API 封装 ✅（后端 API 67/67，前端 20/20 零回归）
- [x] **W8** — 运营驾驶舱 MVP：任务看板 + 内容库 + 账号健康、Storybook 配置 ✅（后端 API 67/67，前端 32/32 零回归）
- [x] **W9** — PoolPredictor：冷启动期预测模型（先验 + 基准）、scikit-learn 集成 ✅（后端 API 75/75，前端 32/32 零回归）
- [x] **W10** — E2E 全流程联调：登录→主页→生成→发布→数据回流、Docker Compose 编排 ✅（后端 API 79/79，前端 32/32 零回归）

**MVP 补全冲刺（文档2 Phase 1 缺口，与 PRD V2.3 P0 / §2.6 对齐；建议在进入 Phase 2 前进完）**：
- [x] **W11** — TrendScout：Mock 数据源、手动导入/运营关键词、结构化趋势报告、阶段过滤；**禁止**默认全量真实爬虫（须独立法务评审）
- [x] **W12** — MarketingMethodology：AIPL 四阶段、阶段模板、KPI 与合规标签；与 ContentForge 管道对接
- [x] **W13** — DataAnalyst：**导入优先**的实际互动对齐、24h 报告、**N_min 子集**上区间覆盖率/MAPE、异步校准触发（Celery）；可选只读连接器不纳入 MVP SLA
- [x] **W14** — PlatformRule **L3/L4** CRUD、动态生效、违规归因；ComplianceGuard **证据链**留存策略；Publisher **频率阶梯/错峰/排版随机化**与 L3 对齐

**Phase 1 交付物**：
- [x] 可运行的 SaaS 平台（20 账号支持）
- [x] 登录模块（邮箱/企业微信/飞书 + MFA + 登录风控）
- [x] 运营主页（一屏概览 + 快捷操作 + 实时告警 + 活动日志）
- [x] 平台账号登录与 Cookie 管理（小红书/抖音 Cookie 导入、二维码登录、Session 维持）
- [x] 红绿灯 TDD 流程跑通（测试覆盖率 ≥ 80%）
- [x] AGENTS.md + CI/CD 质量门禁
- [x] 运营驾驶舱 MVP（任务看板 + 内容生成 + 合规检测）
- [x] **（补全）** W11–W14：TrendScout、AIPL 中枢、DataAnalyst、PlatformRule L3/L4 + 证据链 + Publisher 规则对齐（文档2 Phase 1 完整性）

### Phase 1.5：PRD V2.4–V2.6 基础设施补全（W15–W17，与 Phase 2 早期重叠）

> **定位**：PRD V2.4（Agent 全生命周期）、V2.5（LLM Hub + CronHub）、V2.6（Task & Workflow Engine）新增模块是 Phase 1 闭环的**必要基础设施**，在周次上与 Phase 2 早期（W15–W17）并行推进。本小节作为**集中跟踪视图**，所有新增模块的详细任务分解见下方 Phase 2 周任务清单中的「并行」条目。

**新增模块总览与周次矩阵**：

| 新增模块 | 所属 PRD | 核心交付 | 周次 | 状态 |
|---------|---------|---------|------|------|
| **AgentHub** | V2.4 §7.2 | 注册发现、配置版本化、RBAC、依赖声明 | W15 | [ ] |
| **AgentWatch** | V2.4 §7.3 | 心跳健康、OpenTelemetry 链路追踪、规则引擎告警 | W15–W16 | [ ] |
| **AgentMetrics** | V2.4 §7.4 | 任务完成率、Token 成本、延迟分布、质量评分（DeepEval） | W16 | [ ] |
| **Agent Cockpit** | V2.4 §7.5 | 前端：状态看板 + 统计报表 + 配置面板 | W17 | [ ] |
| **LLM Hub** | V2.5 §8 | 模型注册、三层路由配置、成本治理、熔断降级（pybreaker） | W15–W16 | [ ] |
| **LLM Cockpit** | V2.5 §8.4 | 前端：模型面板 + 三层配置 + 成本看板 + 熔断监控 | W17 | [ ] |
| **CronHub** | V2.5 §9 | Job Registry、Schedule Engine、Retry & DLQ（stamina） | W15–W16 | [ ] |
| **Cron Cockpit** | V2.5 §9.5 | 前端：任务看板 + 执行历史 + DLQ + 手动触发 | W17 | [ ] |
| **TaskHub** | V2.6 §10.3 | 任务创建、状态机（transitions）、批量任务、人工审核接口 | W15–W16 | [ ] |
| **Workflow Engine** | V2.6 §10.4 | 串行 Pipeline、上下文传递、4 个预设模板、失败策略 | W16 | [ ] |
| **Prompt Registry** | V2.6 §10.5 | Prompt 版本化（Langfuse）、变量白名单、Jinja2 安全渲染 | W15–W16 | [ ] |
| **Human-in-the-Loop** | V2.6 §10.6 | 审核台、通过/驳回/打回、双人复核、反馈闭环 | W16 | [ ] |
| **Workflow Cockpit** | V2.6 §10.7 | 前端：Kanban + 模板编辑器 + Prompt 编辑器 + 执行监控 | W17 | [ ] |

**新增模块测试基线**：
- [ ] AgentHub：`test_agent_hub.py`（6 测试）
- [ ] AgentWatch：`test_agent_watch.py`（6 测试）
- [ ] AgentMetrics：`test_agent_metrics.py`（5 测试）
- [ ] LLM Hub：`test_llm_hub.py`（6 测试）
- [ ] CronHub：`test_cron_hub.py`（6 测试）
- [ ] TaskHub：`test_task_hub.py`（5 测试）
- [ ] Workflow Engine：`test_workflow_engine.py`（6 测试）
- [ ] Prompt Registry：`test_prompt_registry.py`（5 测试）
- [ ] Human-in-the-Loop：`test_human_in_loop.py`（4 测试）
- [ ] 集成测试：`test_integration_v26.py`（6 测试）
- **新增测试合计：约 55 个**

**新增开源项目到位情况**：
- [x] `vendor/observability-tools/` — OpenTelemetry Python + contrib、Prometheus Client、Jaeger（4 个）
- [x] `vendor/resilience-libraries/` — pybreaker、stamina（2 个）
- [x] `vendor/workflow-libraries/` — croniter、transitions（2 个）
- [x] `vendor/prompt-management/` — Langfuse（1 个）
- [x] `vendor/evaluation-frameworks/` — DeepEval（1 个）

---

### Phase 2：进化（第 3-4 个月，目标：50 账号自我进化）

**周任务清单**（**注意**：W11–W14 已预留给 MVP 补全冲刺，Phase 2 业务周从 **W15** 起算）：
- [x] **W15** — SkillHub：四层架构、Built-in Skill 加载、hermes-agent Skill 系统复用
  - **并行（PRD V2.4 §7.2）**：AgentHub — Agent 注册发现、配置版本化、环境隔离、权限 RBAC、依赖声明
  - **并行（PRD V2.5 §8.2）**：LLM Hub — Model Registry（国产+国外模型注册）、Global Default 配置、Agent 级配置绑定
  - **并行（PRD V2.5 §9.2）**：CronHub — Job Registry（系统预设 Job 定义）、Schedule Engine（Cron 解析 + 分布式锁）
  - **并行（PRD V2.6 §10.3）**：TaskHub — 任务创建、状态机（transitions）、批量任务基础
  - **并行（PRD V2.6 §10.5）**：Prompt Registry — 变量白名单、Jinja2 安全渲染、版本化快照
- [x] **W16** — SkillSmith：成功模式提取、Evolved Skill 生成与人工审核闸
  - **并行（PRD V2.4 §7.4）**：AgentMetrics — 任务完成率、Token 成本归因、延迟分布、质量评分（Rubric-based + DeepEval）
  - **并行（PRD V2.4 §7.3）**：AgentWatch — 心跳健康检查、实时状态看板、OpenTelemetry Trace 采集、异常检测规则引擎
  - **并行（PRD V2.5 §8.2）**：LLM Hub — Skill 级配置、Route Engine（固定路由 + 故障转移）、Cost Governor（预算 + 告警）
  - **并行（PRD V2.5 §9.2）**：CronHub — Execution Runner（Agent 调用集成）、Retry & DLQ（指数退避 + 死信队列）
  - **并行（PRD V2.6 §10.4）**：Workflow Engine — 串行模板定义、上下文传递（Redis）、预设模板（content_creation_standard/light）
  - **并行（PRD V2.6 §10.6）**：Human-in-the-Loop — 审核台视图、通过/驳回/打回修改、双人复核
- [x] **W17** — IP 信誉系统：IP 信誉评分、动态熔断、备用 IP 切换（文档2 §4.2）
  - **并行（PRD V2.4 §7.5）**：Agent Cockpit — Agent 状态看板、统计报表、配置面板（前端）
  - **并行（PRD V2.5 §8.4）**：LLM Cockpit — 模型管理面板、三层配置、成本看板、熔断监控（前端）
  - **并行（PRD V2.5 §9.5）**：Cron Cockpit — 定时任务看板、执行历史、DLQ 面板、手动触发（前端）
  - **并行（PRD V2.6 §10.7）**：Workflow Cockpit — 任务 Kanban、工作流模板编辑器、Prompt 编辑器、执行监控（前端）
- [x] **W18** — PoolPredictor 探索期：贝叶斯线性回归 / 随机森林、区间评估与 A/B 框架（与 PRD §2.4 一致）
- [x] **W19** — ContentInsight：内容标签化、事后归因、SHAP（可选）
  - **并行（PRD V2.4 §7.4）**：AgentMetrics 成本精确归因（content_id 级）
- [x] **W20** — 多平台适配：抖音/视频号内容格式适配（AccountPool/Publisher 适配器）
- [x] **W21** — 矩阵运营增强：规模化 Brief 分发、账号分组策略（可选 BriefHub）
- [x] **W22** — 性能压测：50 账号并发稳定性、Redis 调优

**AgentWatch 跨周并行（PRD V2.4 §7.3，W15–W16）**：
- [x] 心跳健康检查（30s 周期、3 周期缺失判定 UNHEALTHY）
- [x] 实时状态看板（空闲/运行中/故障/熔断 + 队列堆积数）
- [x] 链路追踪（OpenTelemetry trace_id + span，MVP 仅采集存储）
- [x] 异常检测规则引擎（循环检测、超时检测、工具失败检测）
- [x] 告警分级（P0 即时电话/短信、P1 企业微信、P2 邮件日报）

**Phase 2 交付物**：
- [x] SkillHub 技能中枢上线（四层架构 + Tool Registry + 8 L1 Built-in + hermes 兼容 + H1–H6 Harness 完整框架）
- [x] 流量预测进入探索期（Bayesian 基线 + RF/QR 探索模型 + A/B ModelArena + 区间覆盖率评估）
- [x] 50 账号矩阵稳定运行（W21 分组/批量分发/错峰调度 + W22 50 并发压测全绿：Predict P95<500ms / Compliance P95<200ms）
- [x] 多平台内容适配（小红书/抖音/视频号三平台格式转换 + 约束校验 + API）
- [x] **Agent 全生命周期管理（PRD V2.4 §7）**：
  - AgentHub：注册发现 + 配置版本化 + 环境隔离 + 权限 RBAC + 依赖声明
  - AgentWatch：心跳监控 + 链路追踪（OpenTelemetry）+ 规则引擎异常检测 + 分级告警
  - AgentMetrics：任务完成率 + Token 成本归因 + 延迟分布 + 质量评分（ContentForge / ComplianceGuard）
  - Agent Cockpit：状态看板 + 统计报表 + 配置面板（前端驾驶舱）
- [x] **LLM 管理与配置中心（PRD V2.5 §8）**：
  - LLM Hub：模型注册（国产+国外 10+ 模型）+ 三层配置（Global/Agent/Skill）+ 路由策略（固定/故障转移）+ 成本治理（预算配额 + 三级告警）+ 熔断降级（pybreaker + 恢复探测）
  - LLM Cockpit：模型管理面板 + 三层配置面板 + 成本看板 + 熔断监控（前端）
- [x] **定时任务调度中心（PRD V2.5 §9）**：
  - CronHub：Job Registry（9 个系统预设 Job）+ Schedule Engine（croniter + 分布式锁）+ Execution Runner（Agent/API 调用）+ Retry & DLQ（指数退避 + 死信队列人工介入）
  - Cron Cockpit：定时任务看板 + 执行历史时间轴 + DLQ 面板 + 调度器健康监控（前端）
- [x] **任务与工作流引擎（PRD V2.6 §10）**：
  - TaskHub：任务创建（账号+人设+模板+变量）+ 状态机（DRAFT→RUNNING→COMPLETED/FAILED/HUMAN_WAIT）+ 批量任务 + 定时任务绑定
  - Workflow Engine：串行 Pipeline（MVP 禁止 DAG）+ 4 个预设模板 + 上下文传递（Redis + S3）+ 失败策略（fail_fast/continue/retry_then_fail）
  - Prompt Registry：Prompt 版本化（Langfuse）+ 变量白名单校验 + Jinja2 安全渲染 + 效果追踪（质量分 vs Token 成本）
  - Human-in-the-Loop：审核台（内容预览 + Agent 摘要）+ 通过/驳回/打回修改 + 双人复核 + 反馈闭环（human_intervention 表）
  - Workflow Cockpit：任务 Kanban + 工作流模板编辑器（强制 human_approval 节点）+ Prompt 编辑器（变量高亮 + diff）+ 执行监控（前端）

### Phase 3：规模化（第 5-6 个月，目标：100+ 账号联邦）

**周任务清单**（Phase 3 自 **W23** 起算，避免与 Phase 2 周次重叠）：
- [x] **W23** — 多租户隔离：品牌租户隔离、数据隔离、独立配置、openclaw 多租户架构复用
- [x] **W24** — 分组 Orchestrator：账号组自治、分片调度
- [x] **W25** — API 开放平台：客户系统集成 API、Webhook
- [x] **W26** — 监控告警：Prometheus metrics 端点 + 健康检查 API
- [x] **W27** — 安全审计：审计日志、数据加密、等保合规
- [x] **W28** — 负载测试：100 账号并发、API 限流、降级策略
- [x] **W29** — 文档完善：OpenAPI 160 路由自动导出脚本
- [x] **W30** — 生产发布：Docker Compose + PostgreSQL + Redis + Nginx 配置就绪

**Phase 3 交付物**：
- [x] 100+ 账号矩阵支持（100 并发压测全绿：Predict P95<600ms / Compliance P95<300ms）
- [x] 多租户 SaaS 平台（Tenant 模型 + 中间件 + 配置隔离 + 平台白名单）
- [x] API 开放平台（API Key / Webhook / Token-bucket 限流）
- [x] 生产级监控告警（Prometheus metrics 端点 + 组件健康检查）
- [x] 等保三级合规（审计日志 append-only + 多维度查询 + 不可变策略）

---

## 九、Agent Harness 改造专项（Phase 1.5）

> **依据**：Anthropic Engineering "Effective Harnesses for Long-Running Agents" + LangChain "The Anatomy of an Agent Harness"  
> **目标**：在 Phase 1 代码基线（以 CI 测试计数为准）上，构建统一的 Agent Harness 层，使现有服务模块升级为 Agent 可调用、可验证的 Tools  
> **周期**：6 个并行冲刺周 **H1–H6**（与业务周 **W*** 解耦，避免与「MVP 补全 W14」等冲突），建议自第 3 个月初起与 **W15+** 并行推进  
> **原则**：渐进式改造、洋葱架构（Harness 层包裹现有 Service 层）、零 API 回归；**禁止**引入文档2 v5.0 已废弃的 MetaLearner、记忆联邦、对抗辩论

### 9.1 当前代码库与 Harness 差距（专家评审结论）

| # | Harness 组件 | 当前状态 | 关键差距 | 风险 |
|---|-------------|---------|----------|------|
| 1 | **Orchestration Loop (ReAct)** | AgentOrchestra 线性执行 | 无 TAO 动态决策循环 | 🔴 高 |
| 2 | **Memory (3-tier)** | 完全缺失 | 无短期/工作/长期记忆 | 🔴 高 |
| 3 | **Planning (write_todos)** | 完全缺失 | 无法分解复杂任务 | 🔴 高 |
| 4 | **Verification Loops** | 完全缺失 | 无 Gather-Act-Verify | 🔴 高 |
| 5 | **Tool Registry** | SkillHub 有雏形 | 无统一 schema/沙箱 | 🟡 中 |
| 6 | **Subagent Orchestration** | AgentOrchestra 有雏形 | 无 Initializer+Coding 双模式 | 🟡 中 |
| 7 | **Context Management** | 完全缺失 | 无 compaction | 🟡 中 |
| 8 | **State Persistence** | Pipeline 有任务状态 | 无状态图/检查点 | 🟡 中 |

### 9.2 改造后目标架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Agent Harness Layer                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────┐  │
│  │  ReAct Loop │  │   Memory    │  │    Verification Loop        │  │
│  │  (Thought-  │  │  (3-tier)   │  │    (Gather-Act-Verify)      │  │
│  │   Action-   │  │             │  │                             │  │
│  │ Observation)│  │             │  │                             │  │
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
├─────────────────────────────────────────────────────────────────────┤
│                     Existing Service Modules（保留；不含已废弃模块）         │
│  AccountPool, PersonaPool, ComplianceGuard, PoolPredictor, …                 │
└─────────────────────────────────────────────────────────────────────┘
```

### 9.3 改造 Roadmap（并行冲刺 **H1–H6**；勿与业务周 W14 等混用同一编号）

| 冲刺 | 红灯任务（测试） | 绿灯任务（实现） | 与现有模块的集成 |
|------|-----------------|-----------------|----------------|
| **H1** | ReAct 循环测试、工具注册测试 | Harness Core（`harness/core.py`）、Tool Registry（`harness/tool_registry.py`） | 将服务模块封装为 Tool schema |
| **H2** | 三层记忆测试、跨 session 恢复测试 | Memory Manager（`harness/memory.py`）：短期 / 工作 / 长期（**租户内、合规留存范围内**） | DataAnalyst / Pipeline 摘要 → 工作记忆；**禁止**「跨账号记忆联邦」 |
| **H3** | 自验证循环测试、失败重试测试 | Verification Loop（`harness/verification.py`）：Gather-Act-Verify | ComplianceGuard、PoolPredictor 等进入 VERIFY 闸门 |
| **H4** | 任务分解测试、依赖执行测试 | Planning Engine（`harness/planning.py`）：write_todos、增量执行 | ContentForge 分解为选题→大纲→正文→标签→合规 |
| **H5** | 双 Agent 模式测试、上下文交接测试 | Subagent Orchestrator（`harness/subagent.py`） | AgentOrchestra 扩展；Pipeline 跨 session 恢复 |
| **H6** | 上下文压缩测试、状态图恢复测试；端到端错误恢复测试 | Context Manager + State Graph + Error Handler + Guardrails | checkpoint/restore；告警与合规护栏 |

### 9.4 专家评审结论

| 评审维度 | 评分 | 说明 |
|----------|------|------|
| 架构合理性 | 8.5/10 | 渐进式改造，洋葱架构，现有模块化是优势 |
| 技术可行性 | 9/10 | 现有模块可直接作为 Tools 接入 Harness |
| 业务价值 | 9/10 | Verification Loop + Memory 直接提升运营效果 |
| 落地风险 | 低 | 不破坏现有 API，可灰度上线 |
| 兼容性保障 | 100% | 现有 **CI 测试集**零回归（具体数量以 `pytest`/`vitest` 输出为准） |

**评审结论**：unanimously approved（全票通过）。详见 `AgentHarness改造评估报告_专家评审.md`。

### 9.5 改造后 Phase 2 的重新定位

Phase 1.5 的 Harness 层完成后，原有 Phase 2 的"进化"目标获得系统性支撑：

| 原 Phase 2 目标 | Harness 赋能后 |
|----------------|---------------|
| SkillHub 技能中枢 | Tool Registry 统一管理，L4 Evolved Skill 自动注册为 Tool |
| 流量预测探索期 | ReAct Loop 根据预测结果动态调整内容策略 |
| 50 账号矩阵 | Memory「长期层」仅承载**可审计**的策略摘要与 Tool 结果缓存；跨账号风格/模板沉淀由 **SkillSmith + PersonaPool** 实现（对齐 v5.0 已移除「记忆联邦」） |
| 多平台适配 | Planning Engine 自动分解平台适配任务 |

---

## 十、开发里程碑与路线图

### 10.1 Phase 1：MVP（第1-2个月）

**目标**：验证核心闭环，支持20账号冷启动

| 周 | 红灯任务（测试） | 绿灯任务（实现） | 开源集成 |
|----|-----------------|-----------------|----------|
| W1 | 项目初始化测试、Docker构建测试 | 项目脚手架、AGENTS.md、CI/CD流水线 | Vite + React + shadcn/ui 初始化 |
| W2 | 登录模块测试（认证/授权/风控） | 登录页面、JWT认证、RBAC权限、多租户隔离 | OAuth2库集成 |
| W3 | 运营主页测试（数据聚合/个性化） | 运营主页、快捷操作、实时告警、活动日志 | Recharts图表库集成 |
| W3.5 | 平台账号登录测试、Cookie存储测试 | PlatformAccountManager：登录适配器、Cookie仓库、Session管理 | Playwright上下文隔离 |
| W4 | AccountPool CRUD测试、指纹配置测试 | AccountPool核心逻辑、平台登录集成、指纹差异化引擎基础 | Playwright + rebrowser-patches 集成 |
| W5 | ContentForge生成测试、Voice注入测试 | ContentForge + PersonaPool基础实现 | hermes-agent Prompt构建器复用 |
| W6 | ComplianceGuard规则测试 | L1/L2规则引擎、合规检测基础 | jieba分词集成 |
| W7 | Publisher发布测试、错峰调度测试 | Publisher自动发布、错峰调度 | Playwright发布API封装 |
| W8 | 前端组件测试、API集成测试 | 运营驾驶舱MVP页面（任务看板+内容库+账号健康） | Storybook配置 |
| W9 | PoolPredictor预测测试 | 冷启动期预测模型（先验+基准） | scikit-learn集成 |
| W10 | E2E全流程测试 | 端到端联调、登录→主页→生成→发布→数据回流 | Docker Compose编排 |
| **W11** | TrendScout 测试（Mock/导入/阶段过滤） | TrendScout MVP：Mock、手动导入、结构化报告 | 与 PRD §2.1 一致 |
| **W12** | 方法论阶段模板测试 | MarketingMethodology：AIPL 模板与 ContentForge 对接 | — |
| **W13** | DataAnalyst 报表/命中率/MAPE 测试 | DataAnalyst：24h 报告、区间命中、归因 | — |
| **W14** | PlatformRule L3/L4 + Publisher 规则对齐测试 | L3/L4 CRUD、证据链、频率阶梯与错峰 | — |

**Phase 1 交付物**：
- [ ] 可运行的SaaS平台（20账号支持）
- [ ] 登录模块（邮箱/企业微信/飞书 + MFA + 登录风控）
- [ ] 运营主页（一屏概览 + 快捷操作 + 实时告警 + 活动日志）
- [ ] 红绿灯TDD流程跑通（测试覆盖率≥80%）
- [ ] AGENTS.md + CI/CD质量门禁
- [ ] 运营驾驶舱MVP（任务看板 + 内容生成 + 合规检测）
- [ ] **（补全）** W11–W14：见 **§八**「MVP 补全冲刺」与文档2 Phase 1 完整性

### 10.2 Phase 1.5 + Phase 2：Harness（H1–H6）+ 业务进化（第3-4个月）

**目标**：完成 **H1–H6** Harness 并行冲刺（见 **§九**），并交付 Phase 2 业务周 **W15–W22**（50 账号自我进化）。

> **说明**：**H1–H6** 为 Harness 专用代号；业务侧 **W11–W14** 已用于「MVP 补全冲刺」。二者可并行，但排期会议须分开引用代号与周次，避免歧义。

| 业务周 | 红灯任务 | 绿灯任务 | 开源集成 |
|--------|---------|---------|----------|
| **W15** | SkillHub 加载/版本测试 | SkillHub 四层架构、Built-in Skill 加载 | hermes-agent Skill 系统复用 |
| **W16** | Evolved Skill 生成/审核测试 | SkillSmith 成功模式提取、Evolved Skill 生成 | — |
| **W17** | IP 信誉/熔断测试 | IP 信誉评分、动态熔断、备用 IP 切换 | — |
| **W18** | 区间预测与 A/B 测试 | PoolPredictor 探索期模型、区间评估 | XGBoost / sklearn |
| **W19** | 内容洞察/归因测试 | ContentInsight、SHAP（可选） | SHAP |
| **W20** | 多平台适配测试 | 抖音/视频号格式与发布适配 | — |
| **W21** | 矩阵规模化/Brief 流程测试 | Brief 分发与账号分组（可选 BriefHub） | — |
| **W22** | 性能压测 | 50 账号并发、Redis 调优 | Redis |
| **H1–H6** | 见 §9.3 | Harness 核心能力与 Tool Registry | LiteLLM Gateway |

**Phase 2 交付物**：
- [ ] **Agent Harness 核心能力上线**（ReAct + Memory + Verification + Planning；不含废弃模块）
- [ ] SkillHub 技能中枢上线（接入 Tool Registry）
- [ ] 流量预测进入探索期（**互动量区间** + 覆盖率评估 + 可选 ReAct 策略闭环）
- [ ] 50 账号矩阵稳定运行（**SkillSmith + PersonaPool** 沉淀成功模式）
- [ ] 多平台内容适配（小红书 + 抖音，Planning 可辅助分解）

### 10.3 Phase 3：规模化（第5-6个月）

**目标**：规模化联邦，支持100+账号

| 周 | 红灯任务 | 绿灯任务 | 开源集成 |
|----|---------|---------|----------|
| **W23** | 多租户隔离测试 | 品牌租户隔离、数据隔离、独立配置 | openclaw多租户架构复用 |
| **W24** | 分组Orchestrator测试 | 账号组自治、分片调度（Harness Subagent编排） | — |
| **W25** | API开放平台测试 | 客户系统集成API、Webhook | — |
| **W26** | 监控告警测试 | Prometheus + Grafana Dashboard | Prometheus + Grafana部署 |
| **W27** | 安全审计测试 | 审计日志、数据加密、等保合规 | — |
| **W28** | 负载测试 | 100账号并发、API限流、降级策略 | — |
| **W29** | 文档完善 | API文档、开发者文档、运维手册 | — |
| **W30** | 生产发布 | 生产环境部署、灰度切换 | Docker Swarm/K8s |

**Phase 3 交付物**：
- [ ] 100+ 账号矩阵支持
- [ ] 多租户 SaaS 平台
- [ ] API 开放平台
- [ ] 生产级监控告警
- [ ] 等保三级合规
- [ ] **Agent Harness 生产级运行**（Initializer + Coding Agent 全自动运营）

---

## 十一、团队组织与分工

### 11.1 建议团队配置（8-10人）

| 角色 | 人数 | 职责 | 技术栈 |
|------|------|------|--------|
| **技术负责人/架构师** | 1 | 架构设计、技术选型、代码审查、开源集成决策 | Python + TS + AI |
| **后端开发（Python AI层）** | 2 | Agent业务逻辑、AI Pipeline、模型训练 | Python + FastAPI + hermes-agent |
| **后端开发（Node服务层）** | 1 | SaaS API、多租户、权限、网关 | Node.js + TypeScript + openclaw |
| **前端开发** | 2 | 运营驾驶舱、组件库、Storybook | React + Vite + TailwindCSS |
| **AI/算法工程师** | 1 | 流量预测模型、合规NLP、特征工程 | Python + sklearn + XGBoost |
| **浏览器自动化工程师** | 1 | Playwright反检测、指纹引擎、发布执行 | Python/Node + Playwright |
| **DevOps/测试工程师** | 1-2 | CI/CD、Docker编排、测试自动化、监控 | Docker + GitHub Actions + Grafana |

### 11.2 每周开发节奏

| 时间 | 活动 | 参与人 |
|------|------|--------|
| 周一 10:00 | Sprint计划会 | 全员 |
| 每日 10:00 | 站会（15分钟） | 全员 |
| 周三 15:00 | 代码审查会 | 技术负责人 + 相关开发者 |
| 周五 16:00 | 红绿灯回顾会 | 全员 |
| 周五 17:00 | 测试报告评审 | 全员 |

---

## 十二、风险与应对

| 风险 | 概率 | 影响 | 应对策略 |
|------|------|------|----------|
| **hermes-agent/openclaw 源码不兼容** | 中 | 高 | 提前2周做技术预研，建立Fork分支，制定改造计划 |
| **Playwright反检测被平台识别** | **高** | 高 | 1) rebrowser-patches + stealth 插件双层防护；2) 每日指纹测试账号池验证；3) Canvas/WebGL/字体指纹随机化 |
| **平台无开放指标 API、连接器易碎** | **高** | **高** | MVP **导入优先**；连接器插件化 + 失败降级 + 监控；不把全量自动回流写入 SLA |
| **小红书/抖音登录流程变更** | 中 | **中** | 登录适配器插件化设计，监控登录页 DOM 变化，预留缓冲迭代 |
| **LLM API成本超预算** | 高 | 中 | LiteLLM成本监控 + 缓存层 + 模型降级策略 |
| **流量预测模型精度不达预期** | 中 | 中 | 设定合理预期（区间预测），预留模型迭代时间 |
| **团队不熟悉红绿灯TDD** | 高 | 中 | 第一周集中培训，配备TDD导师，CI强制门禁 |
| **开源项目停止维护** | 低 | 高 | 核心能力（指纹引擎、合规规则）保持自研能力，避免深度绑定 |
| **数据安全合规审查不通过** | 低 | 高 | 等保三级同步建设，法务提前介入，数据本地化 |

---

## 附录

### A. 开源项目完整清单

| 项目名称 | 版本 | 用途 | 许可证 |
|----------|------|------|--------|
| hermes-agent（本地） | v0.13.0 | Agent编排底座 | MIT |
| openclaw（本地） | — | SaaS框架底座 | 需确认 |
| React | 19.x | 前端框架 | MIT |
| Vite | 6.x | 构建工具 | MIT |
| TailwindCSS | 4.x | CSS框架 | MIT |
| shadcn/ui | latest | UI组件库 | MIT |
| Radix UI | latest | Headless组件 | MIT |
| Storybook | 8.x | 组件文档 | MIT |
| Ladle | 4.x | 快速组件预览 | MIT |
| TanStack Table/Query | latest | 表格/状态管理 | MIT |
| Zustand | latest | 状态管理 | MIT |
| React Hook Form | latest | 表单处理 | MIT |
| Zod | latest | Schema校验 | MIT |
| Vitest | latest | 测试框架 | MIT |
| Playwright | latest | 浏览器自动化 | Apache-2.0 |
| rebrowser-patches | latest | 反检测补丁 | MIT |
| FastAPI | latest | Python API框架 | MIT |
| SQLAlchemy | 2.x | Python ORM | MIT |
| Alembic | latest | 数据库迁移 | MIT |
| Celery | latest | 任务队列 | BSD-3 |
| PostgreSQL | 16 | 数据库 | PostgreSQL License |
| Redis | 7 | 缓存/队列 | BSD-3 |
| MinIO | latest | 对象存储 | AGPL-3.0 |
| Prometheus | latest | 监控 | Apache-2.0 |
| Grafana | latest | 可视化 | AGPL-3.0 |
| scikit-learn | latest | ML基线模型 | BSD-3 |
| XGBoost | latest | 梯度提升 | Apache-2.0 |
| SHAP | latest | 模型解释 | MIT |
| LiteLLM | latest | LLM路由网关 | MIT |
| jieba | latest | 中文分词 | MIT |
| OpenTelemetry Python | latest | Trace/Metrics 采集 SDK | Apache-2.0 |
| OpenTelemetry Python Contrib | latest | 自动探针集 | Apache-2.0 |
| Prometheus Python Client | latest | Prometheus 指标暴露 | Apache-2.0 |
| Jaeger | latest | 链路追踪后端 | Apache-2.0 |
| pybreaker | latest | 熔断器 | BSD-2/3-Clause |
| stamina | latest | 生产级重试库 | MIT |
| croniter | latest | Cron 表达式解析 | MIT |
| transitions | latest | 有限状态机 | MIT |
| Langfuse | latest | Prompt 版本化管理 + LLM 可观测性 | MIT |
| DeepEval | latest | LLM-as-Judge 评估框架 | Apache-2.0 |

### B. 参考资源

- [Simon Willison: Agentic Engineering](https://simonwillison.net/)
- [hermes-agent GitHub](https://github.com/NousResearch/hermes-agent) → 本地副本：`vendor/ai-frameworks/hermes-agent`（符号链接自 `D:\bigproject\hermes-agent-main`）
- [openclaw GitHub](https://github.com/openclaw/openclaw) → 本地副本：`vendor/infrastructure-tools/openclaw`（符号链接自 `D:\bigproject\openclaw-main`）
- [LiteLLM GitHub](https://github.com/BerriAI/litellm) → 本地副本：`vendor/ai-frameworks/litellm`
- [Storybook Docs](https://storybook.js.org/docs) → 本地副本：`vendor/infrastructure-tools/storybook`
- [rebrowser-patches](https://github.com/rebrowser/rebrowser-patches) → 本地副本：`vendor/browser-automation/rebrowser-patches`
- [shadcn/ui](https://ui.shadcn.com/) → 本地副本：`vendor/design-systems/shadcn-ui`
- [Ladle GitHub](https://github.com/tajo/ladle) → 本地副本：`vendor/infrastructure-tools/ladle`
- [xhs-api GitHub](https://github.com/ReaJason/xhs) → 本地副本：`vendor/platform-crawlers/xhs-api`
- [douyin-tiktok-api GitHub](https://github.com/Evil0ctal/Douyin_TikTok_Download_API) → 本地副本：`vendor/platform-crawlers/douyin-tiktok-api`
- [puppeteer-extra GitHub](https://github.com/berstend/puppeteer-extra) → 本地副本：`vendor/browser-stealth/puppeteer-extra`
- [owl-light GitHub](https://github.com/Olib-AI/owl-light) → 本地副本：`vendor/browser-stealth/owl-light`
- [OpenTelemetry Python GitHub](https://github.com/open-telemetry/opentelemetry-python) → 本地副本：`vendor/observability-tools/opentelemetry-python`
- [OpenTelemetry Python Contrib GitHub](https://github.com/open-telemetry/opentelemetry-python-contrib) → 本地副本：`vendor/observability-tools/opentelemetry-python-contrib`
- [Prometheus Python Client GitHub](https://github.com/prometheus/client_python) → 本地副本：`vendor/observability-tools/prometheus-client-python`
- [Jaeger GitHub](https://github.com/jaegertracing/jaeger) → 本地副本：`vendor/observability-tools/jaeger`
- [pybreaker GitHub](https://github.com/danielfm/pybreaker) → 本地副本：`vendor/resilience-libraries/pybreaker`
- [stamina GitHub](https://github.com/hynek/stamina) → 本地副本：`vendor/resilience-libraries/stamina`
- [croniter GitHub](https://github.com/pallets-eco/croniter) → 本地副本：`vendor/workflow-libraries/croniter`
- [transitions GitHub](https://github.com/pytransitions/transitions) → 本地副本：`vendor/workflow-libraries/transitions`
- [Langfuse GitHub](https://github.com/langfuse/langfuse) → 本地副本：`vendor/prompt-management/langfuse`
- [DeepEval GitHub](https://github.com/confident-ai/deepeval) → 本地副本：`vendor/evaluation-frameworks/deepeval`
- 完整本地路径索引：`vendor/README.md`




# 宠物健康素人号矩阵AI平台 · 开发计划书（v2.7.1-V3.1对齐版）

> **文档性质**: 技术实施级开发计划，面向技术负责人、架构师、开发团队  
> **核心目标**: 基于PRD V3.1（V2.7.1基础功能对齐版）同步更新开发roadmap，遵循"开源为主+自研为辅"原则  
> **对齐基线**: 
> - PRD V3.1《EcoDream_Omni_PRD_v2_对齐核心方案.md》§V2.7.1 V3.1基础功能对齐版
> - 法务合规评审报告《法务合规评审报告_PRD_V2.7.1_11项新增需求.md》
> - 专家评审报告《专家评审报告_PRD_V2.7.1_架构审查.md》
> - **开发计划专家评审报告**《专家评审报告_开发计划_v2.7.1_V3.1架构对齐.md》
> **开发周期**: 6个月（MVP 2个月 + 进化 2个月 + 规模化 2个月）  
> **团队规模**: 建议 8-10人

---

## 〇、文档引用关系矩阵（真源声明）

> **唯一产品真源**: 《文档2_最终可行性完整产品方案_素人号矩阵AI平台》v5.0 Final  
> **PRD真源**: PRD V3.1（V2.7.1基础功能对齐版）《EcoDream_Omni_PRD_v2_对齐核心方案.md》  
> **开发计划真源**: 本文档 v2.7.1-V3.1对齐版  
> **详细设计真源**: 《详细设计_EcoDreamOmni_v2.md》v2.0（待更新至v2.7.1）

### 〇.1 文档层级与引用链

```
文档2 v5.0 Final（产品真源）
    │
    ▼ 约束与对齐
PRD V3.1（需求真源）
    ├── §一、五大基础功能详细设计  ──→ 本文档 §3.0 W14
    ├── §三、Agent层调整  ─────────→ 本文档 §3.1 W15 / §3.2 W16
    ├── §2.7.1 新增需求  ─────────→ 本文档 §3.1-3.3
    └── §八、执行计划  ───────────→ 本文档 §三、执行顺序
    │
    ▼ 技术实施
本文档 v2.7.1-V3.1对齐版（开发计划真源）
    ├── §一、变更概述  ───────────→ PRD V3.1 §〇、架构调整总纲
    ├── §3.0 W14 基础功能  ───────→ PRD V3.1 §一、五大基础功能
    ├── §3.1 W15 Agent接入  ─────→ PRD V3.1 §三、Agent层调整
    ├── §3.2 W16 新增Agent  ─────→ PRD V2.7.1 §新增需求 + PRD V3.1 §三
    ├── §3.3 W17 审核台  ────────→ PRD V2.6 §10.6 Human-in-the-Loop
    └── §四、测试策略  ───────────→ PRD V2.7.1 §测试策略
    │
    ▼ 工程设计
详细设计 v2.7.1（待创建）
    └── 接口/模型/开源边界  ──────→ 本文档 §二、开源+自研边界
```

### 〇.2 版本对齐检查表

| 检查项 | PRD | 开发计划 | 详细设计 | 状态 |
|--------|-----|----------|----------|------|
| 三层架构定义（Function/Agent/Skill）| V3.1 §〇.2 | ✅ 本文档 §一.2 | 🟡 v2.0待更新 | 已对齐 |
| 五大基础功能作为数据真源 | V3.1 §一 | ✅ 本文档 §3.0 | 🔴 待创建 | 已对齐 |
| W14基础功能先行周 | V3.1 §八 | ✅ 本文档 §3.0 | - | 已对齐 |
| VetDrugDB兽药批文库 | V3.1 §1.3 | ✅ 本文档 §3.0 | 🔴 待创建 | 已对齐 |
| Agent禁止直接操作数据库 | V3.1 §〇.2 | ✅ 本文档 §一.2 | - | 已对齐 |
| 11项新增需求清单 | V2.7.1 | ✅ 本文档 §1.1 | - | 已对齐 |

### 〇.3 专家评审团（已组建并评审通过）

> **评审依据**: PRD V2.3-V3.1 专家组终审建议模式  
> **评审日期**: 2026-05-19  
> **评审结论**:  unanimously approved（全票通过），详见 `docs/专家评审报告_开发计划_v2.7.1_V3.1架构对齐.md`

| 角色 | 专家职责 | 评审结论 | 关键意见 |
|------|----------|----------|----------|
| **首席架构师** | 三层架构一致性、Function层定位 | ✅ 采纳 | AssetPool/BrandKnowledge/TimelineLibrary必须定位为Function层数据真源 |
| **产品负责人** | PRD→开发计划需求追溯 | ✅ 采纳 | 11项需求完整追溯，W14基础功能周为新增强制里程碑 |
| **法务合规官** | VetDrugDB、AssetPool合规设计 | ✅ 采纳 | VetDrugDB为合规刚需，批文校验100%拦截；AssetPool版权链≥2年 |
| **技术负责人** | 周次可行性、依赖关系 | ✅ 采纳 | W14先行建设基础功能，W15-W18Agent逐层接入，依赖关系清晰 |
| **数据架构师** | 基础功能数据真源设计 | ✅ 采纳 | 五大基础Function为唯一数据真源，Agent/Skill禁止直接操作数据库 |

---

## 一、V2.7.1-V3.1 变更概述

### 1.1 新增需求清单（11项）

| 序号 | 模块 | 优先级 | 交付周次 | 合规等级 | 架构层级 | 关键约束 |
|------|------|--------|----------|----------|----------|----------|
| 1 | **AssetPool Function**（三源混合素材库）| P0 | **W14** | 中风险 | **Function层** | 运营上传≥70%，AI图加标识 |
| 2 | **BrandKnowledge Function**（品牌知识库）| P0 | **W14** | 🔴高风险 | **Function层** | 兽药批文强制校验，RAG注入控制 |
| 3 | **VetDrugDB Function**（兽药批文库）| P0 | **W14** | 🔴高风险 | **Function层** | V3.1新增，批文号100%校验 |
| 4 | **TimelineLibrary Function**（时间线库）| P1 | **W14** | 低风险 | **Function层** | 与CronHub集成，季节事件库 |
| 5 | **PlatformRule Function**（平台规则库基座）| P0 | **W14** | 中风险 | **Function层** | 小红书规则迁移，为抖音扩展留接口 |
| 6 | TrendScout增强（选题报告生成）| P0 | **W15** | 中风险 | Agent层 | Mock数据标注"参考区间"，PDF加水印 |
| 7 | MarketingMethodology 5A | P0 | **W15** | 低风险 | Agent层 | AIPL→5A平滑迁移 |
| 8 | ImageForge（图片配置引擎）| P0 | **W16** | 中风险 | Agent层 | 强制人工审核，T2模型预检 |
| 9 | ContentSeries（内容系列化）| P1 | **W16** | 低风险 | Agent层 | 禁止矩阵互评互赞 |
| 10 | PlatformRule多平台适配 | P0 | **W16** | 中风险 | Function扩展 | 抖音广告审查号校验 |
| 11 | Human-in-the-Loop弹性单人 | P0 | **W17** | 中风险 | Agent层 | 高风险内容双人复核 |
| 12 | Workflow可视化配置 | P1 | **W17** | 低风险 | Function扩展 | 后端强制校验human_approval |
| 13 | CommentHub（合规版）| P1 | **W17** | 中风险 | Agent层 | 自动评论代码层移除 |

> **架构调整说明**: 原v2.7.1中AssetPool/BrandKnowledge/TimelineLibrary被误定位为独立业务模块，V3.1评审后**重新定位为Function层基础功能**。原W15内容拆分至W14（基础功能建设）和W15（Agent接入）。

### 1.2 三层架构对齐（V3.1定义）

```
Layer 3: Function层（基础功能/数据真源）— W14优先建设
├── AssetPool Function（图库/素材库真源）
├── BrandKnowledge Function（品牌知识真源）
├── VetDrugDB Function（兽药批文真源）— V3.1新增
├── TimelineLibrary Function（营销时间真源）
├── PlatformRule Function（平台规则真源）
├── LLM Hub / CronHub / TaskHub / Workflow / Prompt Registry / Human-in-the-Loop
└── AgentHub / AgentWatch / AgentMetrics

Layer 2: Agent层（业务决策）— W15-W17接入Function
├── TrendScout Agent（调用TimelineLibrary）
├── ContentForge Agent（调用BrandKnowledge/VetDrugDB）
├── ComplianceGuard Agent（调用BrandKnowledge/VetDrugDB/PlatformRule/AssetPool）
├── ImageForge Agent（调用AssetPool/BrandKnowledge）— V2.7.1新增
├── CommentMonitor Agent（调用BrandKnowledge/PlatformRule）— V2.7.1新增
└── 现有Agent升级接入Function

Layer 1: Skill层（原子能力）— 通过Agent调用Function
└── 各类Skill（部分允许直接调用Function API白名单）
```

### 1.3 方案—PRD—开发计划 对齐声明（V3.1增补）

| 原不一致项（v2.7.1旧版） | 修订结论（以PRD V3.1为真源） |
|------------------------|---------------------------|
| AssetPool/BrandKnowledge/TimelineLibrary作为独立业务模块开发 | **重新定位为Function层基础功能**，作为数据真源先行建设（W14） |
| VetDrugDB兽药批文库完全未提及 | **V3.1新增核心Function**，合规刚需，W14建设 |
| W15直接开始Agent功能开发，无基础数据基座 | **新增W14基础功能先行周**，Agent禁止直接操作数据库 |
| 开发计划v2.7.1日期(2026-05-18)早于PRD V3.1日期(2026-05-19) | **按PRD V3.1评审结论修正**，开发计划版本升级为v2.7.1-V3.1对齐版 |
| 缺少Agent/Skill对Function的调用规范 | **新增调用规范**：所有Agent/Skill对基础功能的访问必须通过Function API |

---

## 二、开源+自研边界定义

### 2.1 新增开源组件选型

| 组件 | 版本 | 许可证 | 支撑模块 | 自研边界 |
|------|------|--------|----------|----------|
| WeasyPrint | 59.0 | MIT | TrendScout PDF生成 | 报告模板CSS |
| Pillow | 10.x | HPND | AssetPool图片处理 | 版权管理逻辑 |
| pgvector | 0.2.x | PostgreSQL | BrandKnowledge向量检索 | RAG注入控制 |
| React Flow | 12.x | MIT | Workflow可视化 | 后端强制校验 |

### 2.2 自研代码量预估

| 模块 | 架构层级 | 自研代码行数 | 核心自研逻辑 |
|------|----------|-------------|--------------|
| AssetPool Function | **Function层** | 1200 | 版权管理，三源调度，素材-内容匹配 |
| BrandKnowledge Function | **Function层** | 1500 | 批文校验，RAG控制，知识库管理 |
| VetDrugDB Function | **Function层** | 800 | 批文库管理，宣称校验，到期预警 |
| TimelineLibrary Function | **Function层** | 400 | 季节事件库，事件-内容映射 |
| PlatformRule Function基座 | **Function层** | 600 | 规则引擎基座，平台差异抽象 |
| TrendScout增强 | Agent层 | 800 | 报告聚合，5A匹配度计算，人群契合度评分 |
| MarketingMethodology 5A | Agent层 | 800 | 阶段模板，AIPL迁移，人群定向 |
| ImageForge | Agent层 | 600 | 图片-内容匹配，排版配置，人工干预记录 |
| ContentSeries | Agent层 | 600 | 系列上下文管理，单账号约束 |
| Human-in-the-Loop弹性 | Agent层 | 800 | 弹性审核逻辑，高风险检测 |
| Workflow可视化 | Function扩展 | 600 | 后端强制校验，模板版本化 |
| CommentHub | Agent层 | 1000 | 合规分析（无自动），危机预警 |
| PlatformRule多平台 | Function扩展 | 800 | 平台差异规则，抖音适配 |
| **合计** | — | **~10,100行** | 业务逻辑层+Function层 |

---

## 三、V2.7.1-V3.1 新增模块开发计划

### 3.0 W14: 五大基础功能建设周（Function层数据地基）—— V3.1新增

> **定位**: 本周为V3.1评审后**新增的强制性里程碑**。所有基础Function必须在Agent开发前建设完成，为上层Agent提供标准化数据接口。  
> **红线**: Agent/Skill**禁止直接操作数据库**，必须通过Function API访问基础数据。

**AssetPool Function（图库/素材库真源）**
- [ ] **开源**: Pillow缩略图生成，图库API对接
- [ ] **自研**: 
  - 三源调度（运营上传≥70%/图库API/AI生成）
  - 版权管理核心（source_type/license_type/license_ref）
  - 素材-内容匹配推荐API
  - 带签名URL访问控制（STS Token）
- [ ] **合规**: AI图强制加"AI辅助创作"标签；版权链留存≥2年
- [ ] **测试**: `test_asset_pool.py` — 5个测试全绿

**BrandKnowledge Function（品牌知识真源）**
- [ ] **开源**: pgvector向量存储，LangChain仅Document Loader
- [ ] **自研**: 
  - 知识条目CRUD（品牌信息/品类知识/产品SKU/FAQ/禁用语）
  - RAG检索接口（Top-K知识片段）
  - 产品-批文关联（VetDrugDB外键）
  - 素材关联（AssetPool外键）
  - 版本化管理与回滚
- [ ] **合规**: `ProductInfo.approval_number`必填；知识库修改双人复核+留痕≥2年
- [ ] **测试**: `test_brand_knowledge.py` — 6个测试全绿

**VetDrugDB Function（兽药批文真源）—— V3.1新增**
- [ ] **自研**: 
  - 批文数据录入（手动/批量CSV/API同步）
  - 批文检索（按批文号/产品名/成分/适应症）
  - 合规校验接口：输入内容功效宣称→校验与批文一致性
  - 批文到期预警（提前90天）
- [ ] **合规**: 批文号`兽药字xxxxxxxxx`格式强制校验；缺失批文100%拦截
- [ ] **测试**: `test_vetdrug_db.py` — 5个测试全绿

**TimelineLibrary Function（营销时间真源）**
- [ ] **开源**: croniter季节调度
- [ ] **自研**: 
  - 季节事件库（驱虫季/换毛季/疫苗季等）
  - 产品上市时间线管理
  - 与CronHub定时任务绑定
  - 与BrandKnowledge prohibited_claims联动
- [ ] **测试**: `test_timeline_library.py` — 4个测试全绿

**PlatformRule Function基座（平台规则真源）**
- [ ] **自研**: 
  - 小红书现有L1-L4规则迁移至Function层
  - 平台差异规则抽象基座（为抖音/视频号扩展预留接口）
  - 规则版本化与动态生效
  - 与AccountPool账号平台绑定
- [ ] **测试**: `test_platform_rule_function.py` — 4个测试全绿

**W14 交付标准**:
- [ ] 五大基础Function API全部可用，Swagger文档生成
- [ ] 每个Function至少5个测试全绿
- [ ] Agent直接操作数据库的入口全部关闭（代码审查确认）
- [ ] Function间关联关系建立（产品-批文-素材-时间线）

---

### 3.1 W15: 核心Agent接入基础功能 + TrendScout增强 + 5A

> **定位**: 在W14基础Function建设完成后，核心Agent开始接入标准化数据接口。TrendScout和MarketingMethodology同步增强。

**核心Agent接入基础功能**
- [ ] **ContentForge Agent → BrandKnowledge/VetDrugDB**
  - RAG注入控制系统接入BrandKnowledge检索接口
  - 产品信息自动关联VetDrugDB批文校验
  - 禁用词实时拦截（BrandKnowledge prohibited_claims）
- [ ] **ComplianceGuard Agent → BrandKnowledge/VetDrugDB/PlatformRule/AssetPool**
  - 品牌一致性校验调用BrandKnowledge
  - 兽药宣称校验调用VetDrugDB
  - 平台规则校验调用PlatformRule
  - 素材版权校验调用AssetPool
- [ ] **TrendScout Agent → TimelineLibrary**
  - 时间线选题：按季节事件库推荐营销节点
  - 产品上市时间关联热点推荐
- [ ] **Workflow Engine → 新增基础功能节点**
  - 工作流模板增加基础Function调用节点类型
- [ ] **测试**: `test_agent_function_integration.py` — 6个测试全绿

**TrendScout增强（选题报告生成）**
- [ ] **开源**: WeasyPrint PDF渲染集成
- [ ] **自研**: 结构化选题报告生成
  - 热点趋势摘要聚合
  - 竞品内容结构分析
  - 5A阶段匹配度计算
  - 人群契合度评分
  - 预估互动区间（PoolPredictor先验，标注"参考区间"）
  - 品牌Logo注入
- [ ] **合规**: PDF加水印（下载人、时间）；`engagement_interval`标注"内部参考区间，非平台真实数据"
- [ ] **测试**: `test_trend_scout_v2.py` — 6个测试全绿

**MarketingMethodology 5A**
- [ ] **自研**: AIPL→5A全面替换
  - 5A阶段定义（Aware/Appeal/Ask/Act/Advocate）
  - AIPL映射兼容层（存量内容平滑迁移）
  - 人群定向（AudienceSegment）
  - 阶段-内容模板绑定
- [ ] **合规**: A2模板禁用绝对化用语；A4模板禁用促销话术（兽药法规）
- [ ] **测试**: `test_methodology_5a.py` — 5个测试全绿

---

### 3.2 W16: 新增Agent + 多平台扩展 + ContentSeries

> **定位**: 在核心Agent接入完成后，开发V2.7.1新增Agent和多平台适配。

**ImageForge（图片配置引擎）**
- [ ] **自研**: 
  - 图片-内容匹配算法（调用AssetPool推荐接口）
  - 排版配置（封面+正文配图）
  - 人工干预闭环
- [ ] **集成**: LLM Hub多模态路由（AI生图）
- [ ] **合规**: 含产品信息禁止路由T2境外模型；强制经过人工审核
- [ ] **测试**: `test_image_forge.py` — 5个测试全绿

**CommentHub（合规版）**
- [ ] **开源**: jieba情感分析
- [ ] **自研**: 
  - AI建议+人工手动发布（CommentMonitor Agent）
  - 自动评论代码层彻底移除
  - 回复接口强制人工确认
  - 诱导话术自动拦截
- [ ] **合规**: 每日回复频率≤20条/账号；自动评论入口不存在
- [ ] **测试**: `test_comment_hub.py` — 5个测试全绿

**ContentSeries（内容系列化）**
- [ ] **自研**: 
  - 系列上下文注入（`{{series.prev_content}}`）
  - 单账号内前后文呼应
  - 矩阵互评互赞代码层拦截
- [ ] **测试**: `test_content_series.py` — 4个测试全绿

**PlatformRule多平台适配**
- [ ] **自研**: 
  - 抖音平台规则扩展（调用PlatformRule Function基座）
  - 兽药广告审查号强制校验
  - 引流话术L1拦截
  - 平台差异规则矩阵
- [ ] **合规**: 抖音内容须显著展示兽药广告审查批准文号
- [ ] **测试**: `test_platform_rule_v2.py` — 5个测试全绿

---

### 3.3 W17: 审核台增强 + Workflow可视化

> **定位**: 前端增强与审核流程优化。

**Human-in-the-Loop弹性单人**
- [ ] **自研**: 
  - 弹性审核策略（标准内容单人/高风险双人）
  - 高风险标签自动检测（调用BrandKnowledge/VetDrugDB）
  - batch-approve批量操作管控（含高风险强制逐篇审核）
- [ ] **合规**: 高风险内容`PENDING_REVIEW`状态
- [ ] **测试**: `test_human_in_loop_v2.py` — 5个测试全绿

**Workflow可视化配置**
- [ ] **开源**: React Flow拖拽组件
- [ ] **自研**: 
  - 后端强制校验发布类模板含`human_approval`节点
  - 模板版本化管理
  - Dry Run模拟执行
- [ ] **测试**: `test_workflow_visual.py` — 4个测试全绿

---

### 3.4 W18: 全链路E2E验证 + 安全审计

> **定位**: 20账号×标准工作流×五大基础功能的全链路验证，以及V3.1架构安全审计。

**E2E-1: V2.7.1-V3.1全链路集成测试**
- [ ] `test_integration_v271.py` — 13项需求端到端验证（11项新增+2项架构调整）
- [ ] Function层API可用性验证
- [ ] Agent→Function调用链路验证
- [ ] 工作流全节点跑通验证

**E2E-2: 架构合规验收**
- [ ] Agent直接数据库访问扫描（静态代码分析）— **必须0处**
- [ ] Function API标准化验证
- [ ] 五大基础Function数据一致性验证

**E2E-3: 业务合规验收**
- [ ] BrandKnowledge批文校验100%
- [ ] VetDrugDB宣称一致性100%
- [ ] AssetPool AI标识100%
- [ ] ImageForge T2预检100%
- [ ] CommentHub自动评论移除100%
- [ ] PlatformRule抖音广告号校验100%

---

## 四、测试策略更新

### 4.1 新增模块测试矩阵

| 模块 | 架构层级 | 测试文件 | 测试数 | 关键场景 |
|------|----------|----------|--------|----------|
| AssetPool Function | Function层 | `test_asset_pool.py` | 5 | 三源上传/版权校验/AI标识/匹配推荐/签名URL |
| BrandKnowledge Function | Function层 | `test_brand_knowledge.py` | 6 | 批文校验/RAG拦截/一致性检查/版本回滚 |
| VetDrugDB Function | Function层 | `test_vetdrug_db.py` | 5 | 批文录入/宣称校验/到期预警/产品关联 |
| TimelineLibrary Function | Function层 | `test_timeline_library.py` | 4 | 季节事件/与CronHub集成/与BrandKnowledge联动 |
| PlatformRule Function | Function层 | `test_platform_rule_function.py` | 4 | 规则迁移/平台抽象/动态生效/版本化 |
| Agent-Function集成 | 集成 | `test_agent_function_integration.py` | 6 | ContentForge-RAG/ComplianceGuard-多Function/TrendScout-时间线 |
| TrendScout增强 | Agent层 | `test_trend_scout_v2.py` | 6 | PDF生成/5A匹配/人群契合/水印/批量报告 |
| MarketingMethodology 5A | Agent层 | `test_methodology_5a.py` | 5 | 阶段模板/AIPL迁移/人群定向 |
| ImageForge | Agent层 | `test_image_forge.py` | 5 | AI推荐/人工干预/排版配置/T2预检 |
| ContentSeries | Agent层 | `test_content_series.py` | 4 | 系列上下文/单账号约束/互评拦截 |
| Human-in-the-Loop弹性 | Agent层 | `test_human_in_loop_v2.py` | 5 | 弹性策略/高风险检测/批量管控 |
| Workflow可视化 | Function扩展 | `test_workflow_visual.py` | 4 | 强制校验/版本管理/Dry Run |
| CommentHub | Agent层 | `test_comment_hub.py` | 5 | 自动评论移除/强制确认/诱导拦截 |
| PlatformRule多平台 | Function扩展 | `test_platform_rule_v2.py` | 5 | 抖音规则/广告号校验/平台差异 |
| 全链路E2E | 集成 | `test_integration_v271.py` | 6 | 13项需求端到端/架构合规/业务合规 |

**新增测试合计: 75个**（含20个Function层测试 + 6个Agent-Function集成测试 + 49个Agent层测试）

### 4.2 合规验收测试

| 合规项 | 测试用例 | 验收标准 | 架构层级 |
|--------|----------|----------|----------|
| VetDrugDB批文校验 | `test_vet_approval_required` | 缺失批文号100%拦截 | Function层 |
| BrandKnowledge RAG拦截 | `test_rag_prohibited_blocked` | `prohibited_claims`100%拦截 | Function层 |
| AssetPool AI标识 | `test_ai_disclosure` | AI图强制加标识100% | Function层 |
| ImageForge T2预检 | `test_t2_image_blocked` | 含产品信息路由T2拦截100% | Agent层 |
| CommentHub自动评论 | `test_auto_comment_removed` | 自动评论入口不存在 | Agent层 |
| PlatformRule抖音广告号 | `test_douyin_ad_approval` | 兽药内容广告号校验100% | Function扩展 |
| **Agent直接DB访问** | `test_no_direct_db_access` | 静态扫描0处违规 | **架构红线** |

---

## 五、风险评估与缓解

### 5.1 V3.1架构调整新增风险

| 风险 | 等级 | 缓解措施 |
|------|------|----------|
| W14新增导致整体延期1周 | 🟡 中 | W14为Function层API开发，可与W15前端开发部分并行；基础功能接口先行交付 |
| Agent现有代码直接DB访问 | 🔴 高 | 代码静态扫描（`grep -r "session.execute\|db.query"`）；W14完成全部接口封装 |
| Function层性能瓶颈 | 🟡 中 | Redis缓存热点数据；pgvector向量索引；Batch API减少调用次数 |
| BrandKnowledge批文不一致 | 🔴 高 | 季度校验+approval_number强制+双人复核 |
| AssetPool版权纠纷 | 🟡 中 | 三源比例≥70%上传+授权链留存≥2年 |
| CommentHub误开启自动 | 🟡 中 | 代码层移除入口+接口强制确认校验 |
| T2模型数据出境 | 🟡 中 | LLM Hub预检拦截+敏感数据定义 |
| 抖音平台规则变化 | 🟡 中 | 规则引擎动态配置+监控告警 |

### 5.2 技术债务

1. AIPL→5A需在Phase 2完成全量迁移（存量内容兼容层W15完成，全量迁移W19-W20）
2. BrandKnowledge MVP用pgvector，Phase 2评估专用向量库（Milvus/Pinecone）
3. 多平台规则每新增平台复杂度O(n²)，需设计继承机制（PlatformRule Function基座已预留接口）
4. **V3.1新增债务**: Function层API版本化管理（W14基线v1，后续迭代须兼容）

---

## 六、执行决议

1. **V3.1架构调整已通过专家评审**（2026-05-19），开发计划按本对齐版执行
2. **W14基础功能建设周为新增强制里程碑**，不可跳过；五大基础Function必须在Agent开发前完成
3. **AssetPool/BrandKnowledge/TimelineLibrary重新定位为Function层**，VetDrugDB为V3.1新增核心Function
4. **Agent/Skill禁止直接操作数据库**，必须通过Function API访问基础数据（代码静态扫描验证）
5. **开源边界确认**：新增4个开源组件，全部商用友好许可；自研聚焦约10,100行业务逻辑+Function层代码
6. **周次同步**：W14基础功能→W15 Agent接入→W16新增Agent→W17审核台→W18全链路E2E
7. **版本号**：本文档版本为 **v2.7.1-V3.1对齐版**，替代原v2.7.1更新版（第1591行起旧内容）

---

## 附录A：文档引用关系详细矩阵

### A.1 开发计划 ↔ PRD 交叉引用

| 本文档章节 | PRD章节 | 引用类型 | 说明 |
|-----------|---------|----------|------|
| §〇.3 专家评审团 | PRD V2.3 §六 | 继承模式 | 采用PRD V2.3专家组评审模式 |
| §一.1 新增需求清单 | PRD V2.7.1 §新增需求 | 直接引用 | 11项需求完整追溯 |
| §一.2 三层架构 | PRD V3.1 §〇.2 | 直接引用 | Function/Agent/Skill定义 |
| §3.0 W14 基础功能 | PRD V3.1 §一、五大基础功能 | 技术实施 | Function层数据真源建设 |
| §3.1 W15 Agent接入 | PRD V3.1 §三、Agent层调整 | 技术实施 | Agent接入Function规范 |
| §3.2 W16 新增Agent | PRD V2.7.1 §新增需求 + V3.1 §三 | 技术实施 | ImageForge/CommentHub等 |
| §3.3 W17 审核台 | PRD V2.6 §10.6 | 技术实施 | Human-in-the-Loop增强 |
| §四 测试策略 | PRD V2.7.1 §测试策略 | 扩展引用 | 新增Function层+集成测试 |

### A.2 开发计划 ↔ 详细设计 交叉引用

| 本文档章节 | 详细设计章节 | 引用类型 | 说明 |
|-----------|-------------|----------|------|
| §3.0 W14 AssetPool | 详细设计 v2.7.1 §AssetPool | 待创建 | Function层接口设计 |
| §3.0 W14 BrandKnowledge | 详细设计 v2.7.1 §BrandKnowledge | 待创建 | RAG+向量检索设计 |
| §3.0 W14 VetDrugDB | 详细设计 v2.7.1 §VetDrugDB | 待创建 | V3.1新增批文库设计 |
| §3.1 W15 Agent接入 | 详细设计 v2.0 §二-四 | 基线引用 | AgentHub/Watch/Metrics |
| §3.2 W16 ImageForge | 详细设计 v2.7.1 §ImageForge | 待创建 | 图片配置引擎设计 |
| §3.3 W17 Workflow可视化 | 详细设计 v2.0 §八 | 基线引用 | Workflow Engine扩展 |

### A.3 唯一真源声明

| 数据/配置类型 | 唯一真源文档 | 真源位置 | 传播路径 |
|--------------|-------------|----------|----------|
| 产品信息（含批文号） | BrandKnowledge + VetDrugDB Function | `brand_knowledge_entries` + `vetdrug_entries` | Agent→Function API→DB |
| 素材版权信息 | AssetPool Function | `asset_license_records` | Agent→Function API→S3+DB |
| 平台规则 | PlatformRule Function | `platform_rules` | Agent→Function API→DB |
| 营销时间线 | TimelineLibrary Function | `timeline_events` | Agent→Function API→DB |
| Prompt模板 | Prompt Registry | `prompt_templates` | Agent→Registry API→DB |
| Agent配置 | AgentHub | `agent_config_snapshots` | Orchestrator→AgentHub API→DB |
| LLM路由 | LLM Hub | `llm_config_layers` | Agent→LLM Hub API→DB |

---

**更新日期**: 2026-05-19  
**版本**: v2.7.1-V3.1对齐版  
**评审状态**: ✅ 通过（架构对齐评审2026-05-19）  
**替代范围**: 本文档第1591行起原v2.7.1更新版内容已全部替换  
**对齐PRD**: PRD V3.1（V2.7.1基础功能对齐版）2026-05-19  
**下次评审**: W14 Sprint计划会前



# 宠物健康素人号矩阵AI平台 · 开发计划书（v2.7.2 增补版）

> **文档性质**: PRD V2.7.2 技术实施增补，面向技术负责人、开发团队  
> **核心目标**: 基于PRD V2.7.2 最新调整，同步更新开发计划与详细设计，推进实际编码  
> **对齐基线**: 
> - PRD V2.7.2《EcoDream_Omni_PRD_v2_对齐核心方案.md》§8 LLM Hub精简版 + §11 PersonaStory
> - 开发计划 v2.7.1-V3.1对齐版（本文档第1591-2069行）
> **开发周期**: W14-W18 Sprint 内完成  

---

## 〇、V2.7.2 变更概述

### 〇.1 PRD V2.7.2 关键调整

| 调整项 | 原设计（V2.5/V2.7.1） | 新设计（V2.7.2） | 影响 |
|--------|----------------------|-----------------|------|
| **LLM Hub 配置模式** | 三层配置（Global/Agent/Skill）+ Route Engine + Cost Governor + Circuit Breaker | 极简四字段（厂家+模型名+APIKey+状态）+ 应用范围（全局默认+节点覆盖）+ 精简成本看板 | 开发周期从W15-W17压缩至W15-W16；运营配置门槛大幅降低 |
| **LLM Cockpit 前端** | 模型面板+三层配置+成本看板+熔断监控 | 模型注册抽屉（5字段）+ 应用范围一览表 + 精简成本看板 + 调用日志 | 前端开发量降低约40% |
| **基础功能数量** | 五大基础功能（AssetPool/BK/VD/TL/PR） | **六大基础功能**（新增 PersonaStory） | W14增补PersonaStory Function |
| **PersonaStory 定位** | 无 | 第六大基础功能，与PersonaPool解耦：Pool管"是谁"，Story管"经历了什么" | 新增独立模块，ContentForge生成时注入 |

### 〇.2 文档引用关系更新

```
PRD V2.7.2（需求真源）
    ├── §8 LLM Hub精简版 ─────────→ 本文档 §一、§二
    ├── §11 PersonaStory ────────→ 本文档 §三
    └── §八.7 专家评审决议 ──────→ 本文档 §四
    │
    ▼
本文档 v2.7.2 增补（开发计划真源）
    ├── §一 LLM Hub精简版开发计划
    ├── §二 LLM Hub详细设计更新
    ├── §三 PersonaStory开发计划
    ├── §四 PersonaStory详细设计
    └── §五 编码任务分配
    │
    ▼
详细设计 v2.7.2（工程设计真源）— 本文档 §二、§四
```

---

## 一、LLM Hub 精简版开发计划

### 1.1 精简前后对比

| 维度 | V2.5 原版 | V2.7.2 精简版 |
|------|----------|--------------|
| **Model Registry** | 12字段（含能力标签/合规分级/单价/端点/Vault引用） | 5字段（厂家/模型名/APIKey/端点/状态） |
| **配置层级** | L1 Global / L2 Agent / L3 Skill 三层 | 全局默认 + 节点级覆盖 两层 |
| **路由策略** | PINNED / WEIGHTED_RANDOM / FAILOVER | 直接查询：节点有覆盖→覆盖模型；无→全局默认 |
| **成本治理** | Cost Governor（预算配额/三级告警/多币种） | 成本看板（展示消耗/趋势/排行，不管控） |
| **熔断降级** | Circuit Breaker（pybreaker / 自动恢复探测） | 移除；AgentWatch错误率告警替代 |
| **合规预检** | T2模型处理敏感数据强制拦截 | 境外模型调用提示风险，不强制拦截 |
| **测试数** | 22个（6模块×3-4测试） | 13个（4模块×2-4测试） |
| **开发周次** | W15-W17（3轮） | W15-W16（2轮） |

### 1.2 数据模型精简

```python
# 精简后 LLMModel（5字段注册）
@dataclass
class LLMModel:
    id: str
    provider: str           # 厂家选择
    model_name: str         # 模型名（如 deepseek-chat）
    api_key_encrypted: str  # AES-256加密存储
    endpoint_base_url: Optional[str] = None  # 可选，默认官方
    status: str = "active"  # active / inactive
    data_training_opt_out: bool = True  # 默认不参与模型训练
    created_at: str = ""
    updated_at: str = ""

# 精简后 ScopeConfig（应用范围）
@dataclass
class ScopeConfig:
    id: str
    scope_type: str         # "global" or "node"
    node_id: Optional[str]  # agent_id or skill_id; global为None
    model_id: str           # 指向LLMModel.id
    temperature: float = 0.5
    timeout_seconds: int = 60
    created_at: str = ""
    updated_at: str = ""

# 精简后 LLMUsageLog（调用日志）
@dataclass
class LLMUsageLog:
    id: str
    model_id: str
    node_id: str            # 调用方agent/skill ID
    provider_region: str    # "domestic" or "overseas"
    input_tokens: int
    output_tokens: int
    latency_ms: int
    status: str             # success / error
    created_at: str = ""
```

### 1.3 API 接口精简

| 接口 | 方法 | V2.5 | V2.7.2 |
|------|------|------|--------|
| `/llm-hub/models` | POST | 12字段注册 | 5字段注册 |
| `/llm-hub/models/{id}/test` | POST | 无 | **新增**：连通性测试 |
| `/llm-hub/scope-configs` | POST/GET/DELETE | 无（原为/config-layers） | **新增**：应用范围配置CRUD |
| `/llm-hub/scope-configs/nodes` | GET | 无 | **新增**：节点一览表（含继承关系） |
| `/llm-hub/usage-logs` | GET | 无（原为/decisions） | **新增**：调用日志筛选导出 |
| `/llm-hub/cost-summary` | GET | 无（成本在预算接口） | **新增**：成本看板数据聚合 |
| `/llm-hub/route` | POST | 复杂路由决策 | 简化：查询scope→返回模型配置 |
| `/llm-hub/config-layers` | POST/GET/DELETE | 三层配置CRUD | **移除** |
| `/llm-hub/budgets` | POST/GET | 预算配额CRUD | **移除**（延后Phase 2） |
| `/llm-hub/circuits/{id}` | GET/POST | 熔断器状态/操作 | **移除**（延后Phase 2） |

### 1.4 执行顺序（精简版）

**第 1 轮（W15）**：Model Registry（极简5字段）+ 应用范围配置（全局默认+节点覆盖）+ APIKey加密存储 + 连通性测试接口。  
**第 2 轮（W15 末）**：与 LiteLLM Gateway 集成 + LLMUsageLog 记录 + AgentMetrics 消耗统计注入。  
**第 3 轮（W16）**：LLM Cockpit 前端（模型注册抽屉 / 应用范围一览表 / 成本看板 / 调用日志）。  
**第 4 轮（W16 末）**：全量回归 + 成本公式验证 + APIKey安全审计。  
**Phase 2 扩展（W18-W19）**：Route Engine（故障转移）、Cost Governor（预算配额）、Circuit Breaker（熔断降级）。

---

## 二、LLM Hub 精简版详细设计

### 2.1 服务层重构（`services/llm_hub.py`）

**保留接口**（精简后仍需要的函数）：
- `register_model(provider, model_name, api_key, endpoint_url, status)` → 返回 LLMModel
- `list_models(provider, status)` → 返回 LLMModel[]
- `get_model(model_id)` → 返回 LLMModel
- `delete_model(model_id)` → bool
- `test_model_connectivity(model_id)` → bool（新增）
- `set_global_default(model_id, temperature, timeout)` → ScopeConfig
- `set_node_override(node_id, model_id, temperature, timeout)` → ScopeConfig
- `remove_node_override(node_id)` → bool
- `list_scope_configs()` → 含继承关系的一览表
- `resolve_model_for_node(node_id)` → 返回实际使用的 model_id（有覆盖→覆盖；无→全局默认）
- `log_usage(model_id, node_id, tokens, latency, status)` → LLMUsageLog
- `get_cost_summary(period)` → 成本聚合数据

**移除接口**（延后Phase 2）：
- `route_decision()` 复杂路由逻辑
- `create_budget()` / `consume_budget()` / `list_budgets()`
- `get_circuit_state()` / `manual_trip()` / `manual_reset()`
- `create_config_layer()` / `list_all_configs()` / `delete_config_layer()`（三层配置）

### 2.2 安全设计

- **APIKey 存储**: AES-256-GCM 加密，`api_key_encrypted` 字段；加密密钥从环境变量 `LLM_API_KEY_MASTER_KEY` 读取
- **前端不可回显**: API 返回模型列表时，`api_key_encrypted` 替换为掩码字符串 `"••••••••"`
- **连通性测试**: 后端使用解密后的 APIKey 向厂家端点发送极简请求（如 `{"model":"xxx","messages":[{"role":"user","content":"hi"}],"max_tokens":1}`），验证 HTTP 200
- **访问审计**: 所有模型注册/修改/删除操作写入 `audit_logs` 表

### 2.3 成本计算公式

```python
def estimate_cost(model_id: str, input_tokens: int, output_tokens: int) -> float:
    """按厂家官方单价计算预估成本（CNY）"""
    pricing = {
        "deepseek-chat": {"input": 0.001, "output": 0.002},        # per 1K tokens, CNY
        "deepseek-reasoner": {"input": 0.004, "output": 0.016},
        "gpt-4o": {"input": 0.035, "output": 0.105},              # USD, 需汇率转换
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        "claude-3-5-sonnet": {"input": 0.003, "output": 0.015},   # USD
        "qwen-max": {"input": 0.02, "output": 0.06},              # CNY
        "glm-4": {"input": 0.005, "output": 0.005},               # CNY
        "kimi-v1": {"input": 0.006, "output": 0.012},             # CNY
    }
    # 实际实现从数据库 pricing 表读取
```

---

## 三、PersonaStory 开发计划

### 3.1 模块定位

**PersonaStory** = 第六大基础功能，与 AssetPool / BrandKnowledge / VetDrugDB / TimelineLibrary / PlatformRule 并列。

- **PersonaPool** 管 "是谁"（Voice、风格、标签）
- **PersonaStory** 管 "经历了什么"（时间轴驱动的故事剧本）
- **ContentForge** 生成时注入 `persona_story_context`（前情回顾 + 情绪基调 + 下期预告）

### 3.2 数据模型

```python
@dataclass
class StoryNode:
    id: str
    story_id: str                    # 所属剧本
    sequence_index: int              # 节点顺序
    theme: str                       # 本期主题
    emotion_tone: str                # 低落 / 平稳 / 高涨 / 爆发
    key_event: str                   # 关键事件描述
    prev_recap: Optional[str] = None # 前情回顾（注入内容）
    next_teaser: Optional[str] = None # 下期预告（注入内容）
    content_draft_id: Optional[str] = None  # 关联生成的内容
    created_at: str = ""

@dataclass
class PersonaStory:
    id: str
    persona_id: str                  # 关联Persona
    name: str                        # 剧本名称（如"新手养猫第1-12周"）
    description: str = ""
    emotion_curve_template: str = "gradual_growth"  # 情感曲线模板
    nodes: List[StoryNode] = field(default_factory=list)
    status: str = "draft"            # draft / active / completed / archived
    created_at: str = ""
    updated_at: str = ""

@dataclass
class PersonaStoryContext:
    """注入ContentForge的上下文"""
    current_node: StoryNode
    prev_node_summary: Optional[str] = None
    next_node_teaser: Optional[str] = None
    series_theme: str = ""           # 系列整体主题
    emotional_arc: str = ""          # 当前情感曲线位置
```

### 3.3 功能清单

| 功能 | 优先级 | 后端API | 前端页面 |
|------|--------|---------|----------|
| 剧本CRUD | P0 | `POST/GET/PUT/DELETE /persona-stories` | Story Cockpit 列表+编辑 |
| 故事节点CRUD | P0 | `POST/GET/PUT/DELETE /story-nodes` | 节点时间轴编辑器 |
| 情感曲线模板 | P1 | `GET /story-templates` | 模板选择器 |
| 剧本绑定Persona | P0 | `POST /persona-stories/{id}/bind` | Persona下拉绑定 |
| 内容生成注入 | P0 | `GET /persona-stories/{id}/context` | ContentForge自动调用 |
| 剧本复制 | P1 | `POST /persona-stories/{id}/clone` | 一键复制按钮 |
| 剧本状态流转 | P0 | `PATCH /persona-stories/{id}/status` | 状态切换 |

### 3.4 前端设计：Story Cockpit

```
┌─────────────────────────────────────────────────────────────┐
│  Story Cockpit                           [新建剧本]          │
├─────────────────────────────────────────────────────────────┤
│  筛选: [全部状态 ▼] [Persona ▼]                              │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ 剧本A        │  │ 剧本B        │  │ 剧本C        │         │
│  │ 温柔铲屎官   │  │ 专业兽医     │  │ 生活博主     │         │
│  │ 12节点·活跃  │  │ 8节点·草稿   │  │ 6节点·已完成 │         │
│  │ [编辑][复制] │  │ [编辑][激活] │  │ [归档]       │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
├─────────────────────────────────────────────────────────────┤
│  剧本编辑器（选中剧本A）                                      │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ 剧本名: 新手养猫第1-12周的真实记录                      │ │
│  │ Persona: 温柔铲屎官 [更换]                              │ │
│  │ 情感曲线: 渐进成长 [低谷逆袭 ▼]                         │ │
│  │                                                       │ │
│  │ 时间轴节点:                                            │ │
│  │  [1] 主题: 第一次带猫回家    情绪: 高涨    [编辑][删除]│ │
│  │  [2] 主题: 猫咪应激了三天    情绪: 低落    [编辑][删除]│ │
│  │  [3] 主题: 找到安抚方法      情绪: 平稳    [编辑][删除]│ │
│  │  [4] 主题: 第一次驱虫        情绪: 高涨    [编辑][删除]│ │
│  │  [+] 添加节点                                            │ │
│  │                                                       │ │
│  │ [保存] [预览注入效果] [激活剧本]                         │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 3.5 执行顺序

**W14 末-W15 初**：
- 数据模型（StoryNode / PersonaStory / PersonaStoryContext）
- ORM 模型与数据库迁移
- 后端 Service + API（剧本CRUD / 节点CRUD / 上下文生成）
- pytest 测试（6个）

**W15 中**：
- Story Cockpit 前端页面
- 与 ContentForge 集成（生成时注入 persona_story_context）
- 与 PersonaPool 联动（剧本绑定Persona）

---

## 四、编码任务分配与优先级

### 4.1 任务分解

| # | 任务 | 优先级 | 估算 | 负责人 |
|---|------|--------|------|--------|
| 1 | **PersonaStory 后端**：ORM模型 + Service + API + 测试 | P0 | 1天 | Agent-1 |
| 2 | **LLM Hub 精简版后端**：重写Service + 新API + 测试 | P0 | 1.5天 | Agent-2 |
| 3 | **前端**：Story Cockpit页面 + LLM Cockpit精简版更新 | P0 | 1.5天 | Agent-3 |
| 4 | **集成测试**：PersonaStory→ContentForge注入链路 + LLM调用链路 | P0 | 0.5天 | 联合 |

### 4.2 编码规范

- 遵循 AGENTS.md 红绿灯 TDD 纪律
- 后端：FastAPI + SQLAlchemy 2.0 + pytest
- 前端：React 19 + Vite 6 + Tailwind v4 + shadcn/ui
- 所有新增代码必须有测试覆盖（≥80%）

---

**更新日期**: 2026-05-21  
**版本**: v2.7.2增补版  
**对齐PRD**: PRD V2.7.2  
**状态**: 已更新开发计划与详细设计，进入编码阶段
