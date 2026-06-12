# Sprint：MVP 补全 W11–W14 + 预测契约（PRD V2.3 / 详细设计 v1.0）

> 原子任务分解，遵循 Red-Green TDD（见根目录 `AGENTS.md`）。
> **详细设计真源**：[`docs/详细设计_EcoDreamOmni_v1.md`](./详细设计_EcoDreamOmni_v1.md)（含架构—稳定性—可实现性评审结论）
> **上下文包**：[`docs/AI_Context_Packages.md`](./AI_Context_Packages.md)

---

## 已完成基线（W1–W10，勿回退）

- [x] W1–W10 主干：Auth、Dashboard、PlatformAccount、AccountPool、ContentForge、Compliance、Publisher、PoolPredictor（初版）、E2E 等（以 CI 与开发计划勾选为准）

---

## P0：PoolPredictor 契约（对齐详细设计 §5.1 / PRD §2.4）— ✅ 已完成

- [x] **PRED-1 Red**：扩展 `apps/backend/tests/test_pool_predictor.py`，断言响应含 `likes/comments/saves` 各区间的 `lower/median/upper` 及 `interval_mode`、`confidence`
- [x] **PRED-2 Green**：实现 `prediction_engine.py` 中 `interval_mode=prior|fitted`；缺失特征默认值与降权
- [x] **PRED-3 Blue**：`pool_predictor` API schema 与 OpenAPI 文档一致；禁止 `l0_l5` 默认字段；新增 `Idempotency-Key` 幂等支持

**验收**：pytest 全绿；P95 目标见详细设计 §5.1（不含 LLM）

---

## W11：TrendScout（详细设计 §5.2 / CP-TREND）— ✅ 已完成

- [x] **W11-1 Red**：`test_trend_scout.py` — `POST /trend-scout/reports`（Mock + 导入 items）、列表分页、详情、`stage_filter`
- [x] **W11-2 Green**：`trend_scout_service.py` + 持久化 + `source=mock|import` + `tenant_id` + `payload_json`
- [x] **W11-3**：`POST /trend-scout/persona-draft` 返回草案（LLM 不可用时降级模板 + `warnings[]`）
- [x] **W11-4**：前端入口（可选）：Dashboard 智能选题跳转或最小列表页

**禁止**：默认全站真实爬虫（PRD §2.1）

---

## W12：MarketingMethodology（详细设计 §5.3 / CP-METH）— ✅ 已完成

- [x] **W12-1 Red**：`test_methodology.py` — `GET .../template`、`POST .../evaluate` 缺失字段列表
- [x] **W12-2 Green**：`methodology_service.py` + AIPL 四阶段种子数据（fixture）
- [x] **W12-3**：`content_forge` 请求体支持可选 `stage_id`，注入模板版本号（可审计字段 `template_version`）
- [x] **W12-4（可选）**：与前端 Zod schema 字段对齐（`packages/shared` 或生成类型）

---

## W13：DataAnalyst（详细设计 §5.4 / CP-DATA）— ✅ 已完成

- [x] **W13-1 Red**：`test_data_analyst.py` — CSV 导入解析、`prediction_comparison`、`N_min` 门禁下 `coverage_kpi_applicable`
- [x] **W13-2 Green**：`data_analyst_service.py` + CSV 解析（pandas/csv 双回退）；幂等键策略（见详细设计 §3.2）
- [x] **W13-3**：`POST /data-analyst/calibrate` 写入 `calibration_jobs` 队列占位（**禁止**同步重训）；状态 `pending|running|done|failed`
- [x] **W13-4**：`GET /data-analyst/dashboard` 昨日战报聚合；空态引导导入；`coverage_applicable` 标志
- [x] **W13-5**：`GET /data-analyst/attribution/{content_id}` 归因查询

**禁止**：全矩阵无人值守回流为 MVP SLA（PRD §2.3）

---

## W14：PlatformRule L3/L4 + 证据链 + Publisher（详细设计 §5.5–§5.7）— ✅ 已完成

- [x] **W14-1 Red**：`test_platform_rules.py` — L3/L4 CRUD、`layer` 过滤、版本递增策略（update 归档旧版本）
- [x] **W14-2 Green**：`platform_rule_service.py` + 字段对齐 §5.5（`condition_json`, `action` enum, `priority`, `enabled`, `version`, `effective_from`, `created_by`）
- [x] **W14-3**：`GET /platform-rules/attribution/{content_id}` 违规归因
- [x] **W14-4**：`compliance_audit` 追加写；**不可变**更新策略（新行 + `superseded_by`）
- [x] **W14-5**：Publisher 调度前读取 L3 日限/间隔（`evaluate_l3`）；频率阶梯配置驱动（cold_start/growth/mature）；拒绝或延迟须写 `publish_skipped_reason`
- [x] **W14-6**：Dashboard 流量预演面板：`interval_mode` 文案、禁止 L0–L5（PRD §3.1）

---

## W15：SkillHub（详细设计 §5.8 / CP-SKILL）— ✅ 已完成

- [x] **W15-1 Red**：`test_skill_hub.py` — CRUD、四层加载顺序、hermes 导入
- [x] **W15-2 Green**：`skill_hub.py` 四层引擎（L1/L2/L3/L4）、Tool Registry 雏形、safe-eval
- [x] **W15-3**：8 个 L1 Built-in Skill 种子（content-generate、compliance-check、fingerprint-gen、health-score、engagement-predict、publish-schedule、qr-login、session-check）
- [x] **W15-4**：`POST /skill-hub/import/hermes` YAML frontmatter 解析 → L2 Skill
- [x] **W15-5**：Agent-Skill Binding（`skill_binding.py`）

---

## W16：SkillSmith（详细设计 §5.9 / CP-EVO）— ✅ 已完成

- [x] **W16-1 Red**：`test_skill_smith.py` — 性能记录、进化触发、L4 生成
- [x] **W16-2 Green**：`skill_smith.py` — 3 类触发条件（成功率 ≥80%、CES > 40 连续、MAPE < 20%）
- [x] **W16-3**：Evolved Skill 自动生成 `run(ctx)` 代码模板，注册为 L4
- [x] **W16-4**：Human-in-the-loop 审核闸占位（`status=pending_review`）

---

## Phase 1.5：Agent Harness H1–H6 — ✅ 已完成

- [x] **H1**：ReAct 循环（Think → Act → Observe）+ Tool Registry 统一接口（`harness/core.py`、`harness/tool_registry.py`）
- [x] **H2**：三层记忆（短期 / 工作 / 长期，租户隔离）（`harness/memory.py`）
- [x] **H3**：Gather-Act-Verify 验证循环（`harness/verification.py`）
- [x] **H4**：Planning 引擎 — 任务分解 + todo 增量执行（`harness/planning.py`）
- [x] **H5**：Subagent 编排 — Initializer + Coding 双模式（`harness/subagent.py`）
- [x] **H6**：Context Manager（压缩 / 窗口 / pin）+ State Graph（检查点 / 回滚）（`harness/context.py`、`harness/state.py`）
- [x] **H-API**：`api/harness.py` FastAPI 路由（sessions / subagents / plans / checkpoints / context / tools）
- [x] **H-Tests**：`tests/test_harness.py` 42 个用例全绿

---

## W17：IP 信誉系统（文档2 §4.2.2 / §4.4.3）— ✅ 已完成

- [x] **W17-1 Red**：`test_ip_reputation.py` — CRUD、熔断、切换、推荐
- [x] **W17-2 Green**：`ip_reputation.py` — 信誉评分(0-100)、7天测试期、动态熔断、备用IP切换
- [x] **W17-3**：异常类型映射（验证码24h/限流48h/登录失败72h/账号警告7d）
- [x] **W17-4**：单IP最多绑定2个活跃账号；自动淘汰（trust_score ≤ 20 → retired）
- [x] **W17-5**：`api/ip_reputation.py` 完整路由（register/anomaly/circuit/switch/recommend）

---

## W18：PoolPredictor 探索期（详细设计 §5.1 / PRD §2.4）— ✅ 已完成

- [x] **W18-1 Red**：`test_exploration_engine.py` — RF/QR fit+predict、Arena A/B、质量评估
- [x] **W18-2 Green**：`exploration_engine.py` — RandomForest 分位数区间、QuantileRegressor、ModelArena
- [x] **W18-3**：A/B 分配策略（control / explore / ab_50_50 / ab_ucb）
- [x] **W18-4**：区间质量评估（coverage - 0.5×normalized_width）
- [x] **W18-5**：`api/pool_predictor_explore.py` 路由（train/predict/compare/ab-assign/feedback）
- [x] **W18-6**：N_min=5 小样本门禁（不足时返回 error，禁止深度网）

---

## W19：ContentInsight（文档2 §8.11）— ✅ 已完成

- [x] **W19-1 Red**：`test_content_insight.py` — 标签提取、聚合、推荐生成
- [x] **W19-2 Green**：`content_insight.py` — 规则化内容标签、时段/地域/人设分析
- [x] **W19-3**：标签表现关联分析（CES 排序、低表现预警）
- [x] **W19-4**：策略建议生成（标签/时段/分层/格式 四维度）
- [x] **W19-5**：`api/content_insight.py` 路由（analyze/tags/extract/tags/compare/time-slots/recommendations）
- [x] **W19-6**：SHAP 为可选（Phase 2+ 数据量足够时引入）

---

## W20：多平台适配（抖音/视频号）— ✅ 已完成

- [x] **W20-1 Red**：`test_platform_adapters.py` — XHS/抖音/视频号格式与校验
- [x] **W20-2 Green**：`platform_adapters.py` — 平台适配器抽象（format + validate + specs）
- [x] **W20-3**：三平台格式差异：标题长度(20/55/30)、图片上限(18/0/9)、视频时长(600/180/300)
- [x] **W20-4**：hashtag 内联插入、封面自动选取、必填字段校验
- [x] **W20-5**：`api/platform_adapters.py` 路由（platforms/specs/format/validate）

---

## W21：矩阵运营增强 — ✅ 已完成

- [x] **W21-1 Red**：`test_matrix_ops.py` — 分组、批量分配、调度、健康度
- [x] **W21-2 Green**：`matrix_ops.py` — 账号分组（按生命周期+城市）、Brief 批量分发、错峰调度
- [x] **W21-3**：自动分组（auto_group_accounts，≥2 账号才成组）
- [x] **W21-4**：分组健康度聚合（avg_health_score、active/warming/blocked 计数）
- [x] **W21-5**：`api/matrix_ops.py` 路由（groups/auto/assignments/schedules/health）

---

## W22：性能压测 — ✅ 已完成

- [x] **W22-1 Red**：`test_load.py` — 50 账号并发预测/合规/洞察延迟测试
- [x] **W22-2 Green**：PoolPredictor P95 < 500ms、Compliance P95 < 200ms、ContentInsight P95 < 1000ms
- [x] **W22-3**：混合负载测试（预测+合规并发）P95 < 2000ms
- [x] **W22-4**：Jieba 预热机制（避免首次加载污染延迟指标）
- [x] **W22-5**：ThreadPoolExecutor 50 并发零失败

---

## Phase 3：规模化（W23–W30）— ✅ 已完成

### W23：多租户隔离
- [x] **W23-1**：Tenant 模型（CRUD + slug 唯一索引 + 状态管理）
- [x] **W23-2**：TenantContextMiddleware（JWT/Header/Slug 三层提取）
- [x] **W23-3**：平台白名单（`allowed_platforms`）+ 账号容量门禁（`max_accounts`）
- [x] **W23-4**：租户配置覆盖（`config` JSON 动态读写）
- [x] **W23-5**：`api/tenants.py` + `api/tenants/context/whoami`

### W24：分组 Orchestrator
- [x] **W24-1**：Shard 分片调度（`create_group_schedule` 错峰分配）
- [x] **W24-2**：组级健康检查（失败率 < 30% 判定 healthy）
- [x] **W24-3**：`api/orchestrator.py` 路由（schedule/shards/execute/health）

### W25：API 开放平台
- [x] **W25-1**：API Key 生成与吊销（`edo_` 前缀 + 权限列表 + 过期时间）
- [x] **W25-2**：Webhook 注册（URL + 事件订阅 + secret）
- [x] **W25-3**：Token-bucket 限流（租户×端点级别，滑动窗口）
- [x] **W25-4**：`api/api_platform.py` 完整路由

### W26：监控告警
- [x] **W26-1**：Prometheus text format `/metrics` 端点（counter/histogram/gauge）
- [x] **W26-2**：详细健康检查 `/health/detailed`（组件级状态）
- [x] **W26-3**：Metrics API 可编程注入（`inc_counter`/`observe_histogram`/`set_gauge`）

### W27：安全审计
- [x] **W27-1**：审计日志 append-only（actor/resource/before/after 全字段）
- [x] **W27-2**：多维度查询（tenant/event/actor/resource/time 组合过滤）
- [x] **W27-3**：不可变策略（零更新、零删除接口）
- [x] **W27-4**：`api/audit.py` 路由（logs/query/stats）

### W28：负载测试（100 并发）
- [x] **W28-1**：`test_load_100.py` — 100 ThreadPoolExecutor 并发
- [x] **W28-2**：Predict P95 < 600ms、Compliance P95 < 300ms
- [x] **W28-3**：混合负载 P95 < 3000ms
- [x] **W28-4**：降级策略验证（限流桶耗尽后拒绝新请求）

### W29：文档完善
- [x] **W29-1**：OpenAPI 自动导出脚本（`scripts/export_openapi.py`）
- [x] **W29-2**：160 路由完整导出（JSON/YAML 双格式）

### W30：生产发布
- [x] **W30-1**：Docker Compose 配置（PostgreSQL 16 + Redis 7 + Backend + Frontend + Nginx）
- [x] **W30-2**：多阶段 Dockerfile（builder + production，python:3.11-slim）
- [x] **W30-3**：requirements.txt 补全（新增 scikit-learn）
- [x] **W30-4**：健康检查探针（HTTP + pg_isready + redis-cli ping）

---

## 技术债（非本 Sprint 阻塞，登记）

- [x] `meta_learner` 与 PRD 废弃清单冲突：按详细设计 **§5.10** 冻结或 feature_flag 默认关 ✅ 已完成

---

## 当前会话约定

- **一次会话一个原子任务**：从本节勾选一项，完成后更新本文件与 PR。
- **完成后**：在 `开发计划_素人号矩阵AI平台_v2.md` 对应 W11–W14 勾选框同步（人工或下一任务）。

---

## 测试总览

- 后端：**`490 passed, 1 warning`**（pytest）
- 前端：`50 passed`（vitest）

---

## Phase 2 基础设施补全（详细设计 v2.0 新增模块）

> 按依赖拓扑顺序推进：LLM Hub → CronHub → Prompt Registry → Workflow Engine → TaskHub → Human-in-the-Loop

### LLM Hub（详细设计 §5 / PRD V2.5 §8）— ✅ 已完成
- [x] **LLM-1 Red**：`test_llm_hub.py` — 模型注册、三层配置合并、路由决策、预算检查、熔断、合规预检
- [x] **LLM-2 Green**：`services/llm_hub.py` — 模型注册表、三层配置（Skill>Agent>Global）、路由决策（合规降级+预算+熔断+Fallback链）、成本计算
- [x] **LLM-3**：`api/llm_hub.py` — 15 个路由（models/config-layers/route/budgets/circuits/decisions）
- [x] **LLM-4**：注册路由 + 全量回归 411 passed 零失败

### CronHub（详细设计 §6 / PRD V2.5 §9）— ✅ 已完成
- [x] **CRON-1 Red**：`test_cron_hub.py` — Job 注册/Cron 解析/分布式锁/执行器/重试/DLQ
- [x] **CRON-2 Green**：`services/cron_hub.py` — Job Registry、croniter 调度引擎、Execution Runner、Retry & DLQ
- [x] **CRON-3**：`api/cron_hub.py` — 14 个路由
- [x] **CRON-4**：注册路由 + 回归验证

### Prompt Registry（详细设计 §9 / PRD V2.6 §10.5）— ✅ 已完成
- [x] **PROMPT-1 Red**：`test_prompt_registry.py` — 模板注册/变量白名单校验/版本激活/渲染/Dry Run
- [x] **PROMPT-2 Green**：`services/prompt_registry.py` — Jinja2 安全渲染、变量白名单、版本化快照
- [x] **PROMPT-3**：`api/prompt_registry.py` — 10 个路由
- [x] **PROMPT-4**：注册路由 + 回归验证

### Workflow Engine（详细设计 §8 / PRD V2.6 §10.4）— ✅ 已完成
- [x] **WF-1 Red**：`test_workflow_engine.py` — 模板创建/串行执行/上下文传递/失败策略/版本回滚/节点跳过
- [x] **WF-2 Green**：`services/workflow_engine.py` — 串行 Pipeline、4 个预设模板、上下文传递
- [x] **WF-3**：`api/workflow_engine.py` — 10 个路由
- [x] **WF-4**：注册路由 + 回归验证

### TaskHub（详细设计 §7 / PRD V2.6 §10.3）— ✅ 已完成
- [x] **TASK-1 Red**：`test_task_hub.py` — 创建/状态机转换/取消/重试/批量任务
- [x] **TASK-2 Green**：`services/task_hub.py` — 状态机、批量任务、人工审核接口
- [x] **TASK-3**：`api/task_hub.py` — 10 个路由
- [x] **TASK-4**：注册路由 + 回归验证

### Human-in-the-Loop（详细设计 §10 / PRD V2.6 §10.6）— ✅ 已完成
- [x] **HITL-1 Red**：`test_human_in_loop.py` — 审核通过/驳回/打回修改/双人复核
- [x] **HITL-2 Green**：`services/human_in_loop.py` — 审核台、差异记录、反馈闭环
- [x] **HITL-3**：`api/human_in_loop.py` — 7 个路由
- [x] **HITL-4**：注册路由 + 回归验证
