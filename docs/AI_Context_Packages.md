# EcoDream Omni · AI 上下文包（Context Packages）

> **文档真源**：`EcoDream_Omni_PRD_v2_对齐核心方案.md`（**V2.3**）、`开发计划_素人号矩阵AI平台_v2.md`（**v2.2**）  
> **详细设计（实施级）**：[`详细设计_EcoDreamOmni_v1.md`](./详细设计_EcoDreamOmni_v1.md) — 架构/接口/数据/评审结论；模块实现前优先阅读对应章节。  
> **用途**：按业务模块复制下列块到 Cursor / 其他 Agent 会话，作为「# 项目上下文」+「# 当前任务」起点；任务 ID 与 [`TASK.md`](./TASK.md) 原子项对齐。  
> **技术栈以仓库为准**（与 PRD 模板示例中的 NestJS 不同）：**前端 React 19 + TypeScript + Vite 6 + Tailwind v4**；**后端 FastAPI + Python 3.11 + SQLAlchemy 2.0 + PostgreSQL 16 + Redis 7**。

---

## 全局 · 项目上下文（所有模块共用）

### # 项目上下文

- **项目名称**：EcoDreamOmni（宠物健康素人号矩阵 AI 内容管理与分发平台）
- **技术栈**：
  - **前端**：React 19 + TypeScript + Vite 6 + TailwindCSS v4 + shadcn/ui；Zustand + TanStack Query；Vitest + RTL
  - **后端**：FastAPI + Uvicorn + Python 3.11 + SQLAlchemy 2.0 + Alembic；pytest；可选 Celery + Redis（预测校准等异步任务，见 PRD §2.3 / §2.6）
  - **数据**：PostgreSQL 16、Redis 7
- **代码规范**：
  - 根目录 `AGENTS.md`：红绿灯 TDD、覆盖率 ≥80%、eslint/ruff/tsc 门禁、提交前缀 `feat|fix|test|refactor|docs|chore`
  - 后端：业务逻辑在 `apps/backend/src/services/`，路由在 `apps/backend/src/api/`，模型在 `apps/backend/src/models/`；API 层不写裸 SQL，经 Service
  - 前端：类型明确，避免 `any`；组件 + 同路径 `.test.tsx`
- **已有代码结构（摘要）**：

```
EcoDreamOmni/
├── AGENTS.md
├── TASK.md
├── EcoDream_Omni_PRD_v2_对齐核心方案.md
├── 开发计划_素人号矩阵AI平台_v2.md
├── docs/
│   ├── 详细设计_EcoDreamOmni_v1.md   # 详细设计 + 评审结论（实施真源）
│   ├── AI_Context_Packages.md
│   └── TASK.md                       # 当前 Sprint 原子任务
│   ├── frontend/src/
│   │   ├── main.tsx, App.tsx
│   │   ├── pages/          # LoginPage, DashboardPage, SkillHubPage, AgentOrchestraPage
│   │   ├── components/     # TaskBoard, ContentLibrary, AccountHealth, AlertStreamBanner
│   │   ├── stores/         # authStore, dashboardStore, skillHubStore, agentOrchestraStore
│   │   └── lib/api.ts
│   └── backend/src/
│       ├── main.py
│       ├── core/           # config, dependencies, security
│       ├── api/            # 各模块路由（auth, account_pool, content_forge, compliance, …）
│       ├── services/       # 业务服务（*_service.py）
│       └── models/         # ORM / 内存模型
├── packages/shared/
└── vendor/                 # 离线开源副本（含 sklearn、LiteLLM 等参考）
```

### # 禁止项（全局）

- **不得**实现或扩展 PRD 已废弃能力：**MetaLearner、记忆联邦、对抗辩论、流量池层级 L0–L5、CES 精确承诺作为主 KPI**（见 PRD §〇、§1.1）。
- **不得**在 MVP 承诺：全矩阵无人值守 24h 爬取真实互动、未做 A/B 的「+x% 互动」因果文案、自动循环改写到预测区间收敛（见 PRD **§2.6**）。
- **不得**修改无关模块测试以满足新需求；新功能须 **先写失败测试**（AGENTS.md）。
- **不得**在 `apps/backend/.venv` 内改依赖源码；ORM 统一 **SQLAlchemy**，禁止在同一业务域引入第二套 ORM。

---

## 模块索引（与开发计划周次 / PRD 章节对应）

| 包 ID | 模块 | 开发计划 | PRD | 详细设计 |
|-------|------|----------|-----|----------|
| CP-AUTH | 认证与租户入口 | W2 | — | §3.1 |
| CP-PLAT-ACCT | 平台账号与 Cookie | W3.5 | — | §3 |
| CP-ACCOUNT | AccountPool / 指纹 / 健康 | W4 | §1.3 | §四 |
| CP-CONTENT | ContentForge + PersonaPool | W5 | §1.3、§2.2（对接） | §5.3 |
| CP-COMPLIANCE | ComplianceGuard | W6 | §1.3、§2.5（L1/L2 基线） | §5.6 |
| CP-PUBLISH | Publisher / 调度 | W7 | §1.3、§2.6 | §5.7 |
| CP-DASH | 驾驶舱聚合 API + 前端 Dashboard | W8 | §1.3、§3 | §5.8 |
| CP-PREDICT | PoolPredictor / prediction_engine | W9、Phase2 W18 | **§2.4**、§2.6 | **§5.1** |
| CP-E2E | Pipeline / E2E | W10 | 全文目标 | §5.9 |
| CP-TREND | TrendScout | **W11** | **§2.1** | §5.2 |
| CP-METH | MarketingMethodology | **W12** | **§2.2**、§2.6 S0–S1 | §5.3 |
| CP-DATA | DataAnalyst | **W13** | **§2.3**、§2.6 B | §5.4 |
| CP-RULES | PlatformRule L3/L4 | **W14** | **§2.5** | §5.5–§5.7 |
| CP-SKILL-HUB | SkillHub | W15 | Phase 2 | —（Phase 2 另版） |
| CP-SKILL-SMITH | SkillSmith | W16 | Phase 2 | — |
| CP-ORCH | Agent Orchestra / Harness 对齐 | §九 H1–H6 | §1.3、§2.6 | §5.9、§六 |

> 上表「详细设计」列内 § 均指 [`docs/详细设计_EcoDreamOmni_v1.md`](./详细设计_EcoDreamOmni_v1.md) 章节编号。

以下每个 **Context Package** 可单独复制使用；**项目上下文**可简写为「见全局节」。

---

## CP-AUTH — 认证与 RBAC

### # 项目上下文

- 项目名称 / 技术栈 / 规范：**见文档顶部「全局 · 项目上下文」**
- **关键路径**：`apps/backend/src/api/auth.py`、`apps/backend/src/services/auth_service.py`、`apps/backend/src/core/security.py`、`apps/backend/src/models/user.py`；前端 `apps/frontend/src/pages/LoginPage.tsx`、`apps/frontend/src/stores/authStore.ts`

### # 当前任务（原子级 · 示例）

- **任务ID**：CP-AUTH-001  
- **目标**：为某敏感管理接口增加基于 `role` 的 FastAPI `Depends` 守卫，与现有 JWT 一致  
- **输入**：已签发的 `access_token`（Bearer）、路由所需角色枚举  
- **输出**：403 或注入 `User` 上下文  
- **约束**：复用 `src/core/dependencies.py` 中既有 `get_current_user` 模式；不新增 ORM

### # 依赖接口（已存在或需定义）

- `get_current_user`（`src/core/dependencies.py`）
- `create_access_token` / `verify_password`（`src/core/security.py`）
- `get_user_by_email`（`src/models/user.py`）

### # 参考示例（Few-shot）

- 风格参考：`apps/backend/src/services/auth_service.py` 中 `authenticate_user`（邮箱+密码 → `Optional[Tuple[User, str, str]]`）
- 路由参考：`apps/backend/src/api/auth.py` 中 Pydantic `BaseModel` 请求体 + `HTTPException` 用法

### # 禁止项

- 不要在 Service 外绕过密码校验直接发 JWT  
- 不要引入 NestJS / TypeORM（与本仓库无关）  
- 不要删除 MFA 相关测试行为除非 TASK 明确要求  

---

## CP-PLAT-ACCT — 平台账号与 Cookie（小红书等）

### # 项目上下文

- **见全局节**  
- **关键路径**：`apps/backend/src/api/platform_account.py`、`apps/backend/src/services/platform_account_service.py`、`apps/backend/src/models/platform_account.py`

### # 当前任务（原子级 · 示例）

- **任务ID**：CP-PLAT-001  
- **目标**：扩展 Session 状态枚举与 Redis 持久化字段文档（代码与 OpenAPI 描述一致）  
- **输入**：现有 `PlatformCookie` 契约（见开发计划 §6.5.2）  
- **输出**：Pydantic 模型 + 单测覆盖新状态迁移  
- **约束**：Cookie 不落日志明文；密钥租户隔离

### # 依赖接口（已存在或需定义）

- `platform_account_service` 中会话 CRUD（以实际 Service 为准）  
- Redis 访问须经统一封装（若已有则复用，勿在 router 直连 redis）

### # 参考示例（Few-shot）

- `apps/backend/src/services/platform_account_service.py` 与对应 `tests/` 中平台账号用例

### # 禁止项

- 禁止在日志打印完整 Cookie  
- 禁止将「连接器成功」写进 MVP SLA（PRD §2.3）

---

## CP-ACCOUNT — AccountPool / 指纹 / 健康分

### # 项目上下文

- **见全局节**  
- **关键路径**：`apps/backend/src/api/account_pool.py`、`apps/backend/src/services/account_pool_service.py`、`account_health.py`、`fingerprint_engine.py`、`apps/backend/src/models/account_pool.py`

### # 当前任务（原子级 · 示例）

- **任务ID**：CP-ACCOUNT-001  
- **目标**：实现 `warming → active` 状态转换的一条规则 + 单元测试（与 PRD 文档2 状态机对齐）  
- **输入**：健康分阈值、冷却期满事件（可模拟）  
- **输出**：更新后状态 + 审计字段  
- **约束**：不破坏现有 CRUD 测试；TDD

### # 依赖接口（已存在或需定义）

- `AccountPool` 模型与 `account_pool_service` 公开方法（以代码为准）

### # 参考示例（Few-shot）

- `apps/backend/tests/test_account_pool.py`

### # 禁止项

- 不要实现「记忆联邦」或 MetaLearner（PRD 全局禁止项）

---

## CP-CONTENT — ContentForge + PersonaPool

### # 项目上下文

- **见全局节**  
- **关键路径**：`api/content_forge.py`、`services/content_forge_service.py`、`services/content_generator.py`；`api/persona_pool.py`、`models/persona.py`、`services/persona_pool_service.py`

### # 当前任务（原子级 · 示例）

- **任务ID**：CP-CONTENT-001  
- **目标**：ContentForge 生成请求接受可选 `methodology_stage_id`，将阶段模板片段注入 prompt（与 **CP-METH** 对齐）  
- **输入**：正文草稿 + `persona_id` + 可选 `stage_id`  
- **输出**：生成文本 + 使用的模板版本号（便于审计）  
- **约束**：无 `stage_id` 时行为与现网一致（回归）

### # 依赖接口（已存在或需定义）

- `methodology_service` 或 HTTP 内部调用（待 **CP-METH** 定义后对接）  
- `persona_pool_service` 取 Voice

### # 参考示例（Few-shot）

- `apps/backend/tests/test_content_forge.py`、`test_persona_pool.py`

### # 禁止项

- 禁止「爬取克隆人设」为默认路径（PRD §2.1）

---

## CP-COMPLIANCE — ComplianceGuard

### # 项目上下文

- **见全局节**  
- **关键路径**：`compliance.py`、`compliance_service.py`、`compliance_engine.py`；jieba 用于分词

### # 当前任务（原子级 · 示例）

- **任务ID**：CP-COMPLIANCE-001  
- **目标**：为 L1 命中写入不可变审计记录结构（字段设计 + 单测），为 **CP-RULES** 证据链打基础  
- **输入**：内容 ID、规则层、命中片段、处置  
- **输出**：持久化或 append-only 存储（按现有 DB 策略）  
- **约束**：保留期需求见产品方案（≥2 年目标），MVP 可先 schema + 写入路径

### # 依赖接口（已存在或需定义）

- `compliance_service.check_*` 系列（以代码为准）

### # 参考示例（Few-shot）

- `apps/backend/tests/test_compliance.py`

### # 禁止项

- 不放宽处方药/诊疗红线（AGENTS.md）

---

## CP-PUBLISH — Publisher / 错峰 / Playwright

### # 项目上下文

- **见全局节**  
- **关键路径**：`publisher.py`、`publisher_service.py`、`publish_scheduler.py`、`playwright_publisher.py`、`models/publish_task.py`

### # 当前任务（原子级 · 示例）

- **任务ID**：CP-PUBLISH-001  
- **目标**：从 **CP-RULES** L3 读取账号日发帖上限，在调度前硬性裁剪队列  
- **输入**：账号 ID、待发布任务列表  
- **输出**：可执行任务子集 + 跳过原因日志  
- **约束**：失败可重试须与「自动化发布成功率」口径一致（PRD §2.6 C）

### # 依赖接口（已存在或需定义）

- `platform_rule_service`（L3 规则查询，待 **CP-RULES**）  
- `publish_scheduler` / `publisher_service` 现有入口

### # 参考示例（Few-shot）

- `apps/backend/tests/test_publisher.py`

### # 禁止项

- 不在无登录态时伪造平台签名发布

---

## CP-DASH — 驾驶舱 API + 前端 Dashboard

### # 项目上下文

- **见全局节**  
- **关键路径**：后端 `dashboard.py`、`dashboard_service.py`；前端 `DashboardPage.tsx`、`TaskBoard.tsx`、`ContentLibrary.tsx`、`AccountHealth.tsx`、`dashboardStore.ts`

### # 当前任务（原子级 · 示例）

- **任务ID**：CP-DASH-001  
- **目标**：对接 **CP-PREDICT** 返回的 `likes/comments/saves` 区间 + `interval_mode` 展示文案（prior vs fitted）  
- **输入**：内容预览 API 响应  
- **输出**：流量预演卡片 UI + 单测快照或 RTL 断言  
- **约束**：禁止展示 L0–L5 为预测结论（PRD §3.1）

### # 依赖接口（已存在或需定义）

- 前端 `lib/api.ts` 中与 dashboard / predictions 相关方法  
- 后端 `pool_predictor` 或聚合接口

### # 参考示例（Few-shot）

- `apps/frontend/src/pages/DashboardPage.test.tsx`、`apps/backend/tests/test_*` 中与 dashboard 相关部分

### # 禁止项

- 不使用「+x% 互动」未验证因果文案（PRD §2.4、§3.1）

---

## CP-PREDICT — PoolPredictor / prediction_engine

### # 项目上下文

- **见全局节**  
- **关键路径**：`pool_predictor.py`、`pool_predictor_service.py`、**`prediction_engine.py`**（核心算法）、`tests/test_pool_predictor.py`

### # 当前任务（原子级 · 示例）

- **任务ID**：CP-PREDICT-001  
- **目标**：在 `prediction_engine` 中为 likes/comments/saves 输出 `lower/median/upper` + `interval_mode`（`prior|fitted`），冷启动走宽先验 + sklearn `QuantileRegressor` 或等价  
- **输入**：特征向量（缺失维默认值并降权，PRD §1.1）  
- **输出**：JSON 可序列化 dict，与现有 `POST /predictions` 契约兼容扩展  
- **约束**：不返回 `l0_l5_distribution`；单测更新断言字段

### # 依赖接口（已存在或需定义）

- `pool_predictor_service.predict_*`（以代码为准）  
- `sklearn`（`vendor/ml-libraries/scikit-learn` 或项目依赖）

### # 参考示例（Few-shot）

- 现有 `prediction_engine.py` 与 `test_pool_predictor.py` 中断言风格

### # 禁止项

- 小样本不强行上 XGBoost/深度网为 MVP 必达（PRD §2.4）  
- 禁止 Thompson 默认开启（PRD §2.4）

---

## CP-E2E — Pipeline / 端到端

### # 项目上下文

- **见全局节**  
- **关键路径**：`api/pipeline.py`、`services/pipeline_service.py`、`tests/test_pipeline.py`、`tests/test_e2e.py`

### # 当前任务（原子级 · 示例）

- **任务ID**：CP-E2E-001  
- **目标**：在 E2E 中增加一步「预测响应含 `interval_mode`」的断言（与 **CP-PREDICT** 同步）  
- **输入**：现有 docker-compose / mock 环境  
- **输出**：绿测  
- **约束**：不拉长 CI 超时阈值除非 TASK 批准

### # 依赖接口（已存在或需定义）

- Pipeline 各阶段服务调用顺序（以 `pipeline_service` 为准）

### # 参考示例（Few-shot）

- `apps/backend/tests/test_e2e.py`

### # 禁止项

- 不在 E2E 中依赖真实外网 LLM（除非已有 mock 开关）

---

## CP-TREND — TrendScout（MVP 补全 W11）

### # 项目上下文

- **见全局节**  
- **关键路径**：`trend_scout.py`、`trend_scout_service.py`、`tests/test_trend_scout.py`  
- **PRD**：§2.1（Mock + 手动导入 + 结构化报告）

### # 当前任务（原子级 · 示例）

- **任务ID**：CP-TREND-001  
- **目标**：`POST /trend-scout/reports` 从 Mock 数据源填充 `TrendReport` / `TrendItem`（PRD 数据模型），支持 `stage_filter`  
- **输入**：query + stage_filter + 可选导入条目列表  
- **输出**：report id + 持久化或内存存储（与现架构一致）  
- **约束**：默认不发起真实站外爬虫

### # 依赖接口（已存在或需定义）

- PRD 所列路由与 dataclass 字段名对齐 OpenAPI

### # 参考示例（Few-shot）

- `apps/backend/tests/test_trend_scout.py`

### # 禁止项

- 禁止默认「爬取克隆对标账号」为产品路径（PRD §2.1）

---

## CP-METH — MarketingMethodology / AIPL（MVP 补全 W12）

### # 项目上下文

- **见全局节**  
- **关键路径**：`methodology.py`、`methodology_service.py`、`tests/test_methodology.py`  
- **PRD**：§2.2；**结构预检 S0**：PRD §2.6（Zod/Pydantic 同源 schema 可与前端共约定）

### # 当前任务（原子级 · 示例）

- **任务ID**：CP-METH-001  
- **目标**：`GET .../stages/{stage_id}/template` 返回 `hook/body/cta/disclaimer` JSON；`POST .../evaluate` 返回缺失字段列表  
- **输入**：阶段 ID、待评估正文  
- **输出**：合规结构评分 + 缺失键数组  
- **约束**：不调用互动预测作为「结构是否合格」的唯一依据（PRD §2.6）

### # 依赖接口（已存在或需定义）

- 与 **CP-CONTENT** 对接：生成前拉模板

### # 参考示例（Few-shot）

- `apps/backend/tests/test_methodology.py`

### # 禁止项

- 不把 CES 作为 MVP 硬门禁 KPI（PRD §2.2）

---

## CP-DATA — DataAnalyst（MVP 补全 W13）

### # 项目上下文

- **见全局节**  
- **关键路径**：`data_analyst.py`、`data_analyst_service.py`、`tests/test_data_analyst.py`  
- **PRD**：§2.3、§2.6 B（导入为主、N_min、异步校准）

### # 当前任务（原子级 · 示例）

- **任务ID**：CP-DATA-001  
- **目标**：实现 `POST /data-analyst/reports` 从 **CSV 导入** 的 `actual_metrics` 与已有预测区间对比，写入 `prediction_comparison` + `within_range`  
- **输入**：content_id、CSV 行或表单字段  
- **输出**：`DataReport` 记录；若样本不足 `N_min` 则标记 `coverage_kpi: not_applicable`  
- **约束**：校准触发仅写队列表或调用占位 Celery task，不做秒级在线学习

### # 依赖接口（已存在或需定义）

- `pool_predictor` 历史预测查询（若无则 mock 接口）  
- Pandas 解析 CSV（依赖项目 pyproject）

### # 参考示例（Few-shot）

- `apps/backend/tests/test_data_analyst.py`

### # 禁止项

- 不承诺 MVP 全矩阵自动回流（PRD §2.3）

---

## CP-RULES — PlatformRule L3/L4（MVP 补全 W14）

### # 项目上下文

- **见全局节**  
- **关键路径**：`platform_rules.py`、`platform_rule_service.py`、`tests/test_platform_rules.py`  
- **PRD**：§2.5；与 **CP-PUBLISH**、**CP-COMPLIANCE** 对齐

### # 当前任务（原子级 · 示例）

- **任务ID**：CP-RULES-001  
- **目标**：`GET/POST/PATCH/DELETE /platform-rules` 支持 `layer=l3|l4` 过滤；L4 支持 JSON 条件 DSL 最小子集  
- **输入**：管理员 JWT、规则 body  
- **输出**：规则 CRUD + OpenAPI 文档  
- **约束**：删除为软删除或版本递增（二选一，与产品一致后写死）

### # 依赖接口（已存在或需定义）

- Admin 角色 `Depends`（可复用 **CP-AUTH** 模式）

### # 参考示例（Few-shot）

- `apps/backend/tests/test_platform_rules.py`

### # 禁止项

- L1 法律红线仍以硬拦截为准，L3/L4 不得弱化 L1（产品方案）

---

## CP-SKILL-HUB — SkillHub（Phase 2 · W15）

### # 项目上下文

- **见全局节**  
- **关键路径**：`api/skill_hub.py`、`services/skill_hub.py`、`services/skill_binding.py`、`tests/test_skill_hub.py`；前端 `SkillHubPage.tsx`、`skillHubStore.ts`

### # 当前任务（原子级 · 示例）

- **任务ID**：CP-SKILL-HUB-001  
- **目标**：Built-in Skill 元数据从 manifest 加载并在 Tool Registry 注册（与开发计划 Harness H1 对齐，渐进）  
- **输入**：Skill 目录或 JSON manifest  
- **输出**：内存/DB 注册表 + 单测

### # 依赖接口（已存在或需定义）

- 与 `agent_orchestra` 后续对接点（仅加接口不破坏现有）

### # 参考示例（Few-shot）

- `apps/backend/tests/test_skill_hub.py`

### # 禁止项

- 不执行未沙箱的第三方 Skill 写文件系统（产品方案 SkillHub 安全节）

---

## CP-SKILL-SMITH — SkillSmith（Phase 2 · W16）

### # 项目上下文

- **见全局节**  
- **关键路径**：`api/skill_smith.py`、`services/skill_smith.py`、`tests/test_skill_smith.py`

### # 当前任务（原子级 · 示例）

- **任务ID**：CP-SKILL-SMITH-001  
- **目标**：从高表现内容标记生成 Evolved Skill **草案** + `pending_review` 状态，不自动全量上线  
- **输入**：DataAnalyst 标记列表（与 **CP-DATA** 契约）  
- **输出**：Skill 草案记录

### # 依赖接口（已存在或需定义）

- `data_analyst_service` 查询接口

### # 参考示例（Few-shot）

- `apps/backend/tests/test_skill_smith.py`

### # 禁止项

- 不替代 MetaLearner 做「跨账号联邦记忆」（全局禁止项）

---

## CP-ORCH — Agent Orchestra / Harness 对齐

### # 项目上下文

- **见全局节**  
- **关键路径**：`api/agent_orchestra.py`、`services/agent_orchestra.py`、`tests/test_agent_orchestra.py`；开发计划 **§九 H1–H6**

### # 当前任务（原子级 · 示例）

- **任务ID**：CP-ORCH-001  
- **目标**：为某一 Pipeline 步骤增加「VERIFY」钩子占位（ComplianceGuard / PoolPredictor），无行为改变、测试先行  
- **输入**：现有 pipeline DAG 定义  
- **输出**：钩子调用顺序 + 单测

### # 依赖接口（已存在或需定义）

- `compliance_service`、`pool_predictor_service` 只读校验接口

### # 参考示例（Few-shot）

- `apps/backend/tests/test_agent_orchestra.py`

### # 禁止项

- 不引入对抗辩论、MetaLearner、记忆联邦（PRD + 开发计划 §1.3）

---

## 使用说明

1. 新建会话时粘贴 **「全局 · 项目上下文」** + 所选模块整节。  
2. 将 **# 当前任务** 中的示例替换为 `TASK.md` 中的原子任务描述。  
3. **Few-shot** 以仓库文件为准，避免粘贴过时大段代码；让 Agent 用 Read 工具打开路径。  
4. 若任务跨模块，主包放实现侧（如 **CP-PREDICT**），在「依赖接口」中列出上游 **CP-METH** / **CP-DATA** 的契约链接或字段表。

---

**文档维护**：随 PRD / 开发计划版本升级同步更新包 ID 与路径；当前对齐 **PRD V2.3**、**开发计划 v2.2**。
