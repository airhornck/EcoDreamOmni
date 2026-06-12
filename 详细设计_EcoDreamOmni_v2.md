# EcoDreamOmni 详细设计文档 v2.0

> **文档性质**：工程设计级详细设计，面向后端/前端/算法开发团队  
> **对齐基线**：PRD V3.1（V2.7.1基础功能对齐版）《EcoDream_Omni_PRD_v2_对齐核心方案.md》§V2.7.1 V3.1；开发计划 v2.7.1-V3.1对齐版  
> **开源策略**：开源承担通用能力，自研只做编排、特征与业务策略层  
> **工程纪律**：Simon Willison 红绿灯 TDD — 每个模块必须有失败测试→最小实现→测试通过的完整证据链  

---

## 目录

1. 架构总览与新增模块位置
2. AgentHub — Agent 管理与配置中心
3. AgentWatch — Agent 活跃监控与异常检测
4. AgentMetrics — Agent 统计与质量分析
5. LLM Hub — 大模型统一管理与配置中心
6. CronHub — 定时任务调度中心
7. TaskHub — 任务中心
8. Workflow Engine — 工作流编排引擎
9. Prompt Registry — Prompt 全生命周期管理
10. Human-in-the-Loop — 人工审核台
11. 数据模型总览
12. 接口设计汇总
13. 测试策略
14. 开源集成清单与边界

---

## 一、架构总览与新增模块位置

### 1.1 系统架构图（V2.6 增补版）

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SaaS 运营驾驶舱（React + Vite + Storybook）         │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐  │
│  │任务看板 │ │流量预演 │ │账号健康 │ │ 人设库  │ │规则中心 │ │数据报表 │  │
│  │Agent    │ │LLM      │ │Cron     │ │Prompt   │ │Workflow │ │         │  │
│  │Cockpit  │ │Cockpit  │ │Cockpit  │ │Registry │ │Cockpit  │ │         │  │
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
│              │         │ AgentHub       │         │   Jaeger / Prometheus │
│              │         │ AgentWatch     │         │   (可观测性后端)       │
│              │         │ AgentMetrics   │         │                       │
│              │         │ LLM Hub        │         │   Langfuse (可选)     │
│              │         │ CronHub        │         │   (Prompt 追踪)        │
│              │         │ TaskHub        │         │                       │
│              │         │ Workflow Eng.  │         │                       │
│              │         │ Prompt Reg.    │         │                       │
│              │         │ Human-in-Loop  │         │                       │
└───────────────┘         └───────────────┘         └───────────────────────┘
```

### 1.2 新增模块与开源组件映射

| 新增模块 | 开源底座 | 自研业务层 | 数据存储 |
|---------|---------|-----------|---------|
| **AgentHub** | — | 注册发现、配置版本化、RBAC、依赖声明 | PostgreSQL |
| **AgentWatch** | **OpenTelemetry Python**（Trace/Metrics 采集）+ **Jaeger**（Trace 后端）+ **Prometheus Client**（指标暴露）| 心跳规则引擎、异常检测、分级告警 | PostgreSQL + Redis |
| **AgentMetrics** | **Prometheus Client**（指标生成）+ **DeepEval**（质量评分）+ **Langfuse**（效果追踪）| 统计聚合、成本归因、人机干预记录 | PostgreSQL |
| **LLM Hub** | **LiteLLM** Router（底层路由）+ **pybreaker**（熔断器）+ **stamina**（重试）| 三层配置合并、成本治理、合规预检 | PostgreSQL + Redis |
| **CronHub** | **Celery Beat**（调度引擎）+ **croniter**（Cron 解析）+ **stamina**（重试）| Job Registry、Schedule Engine、DLQ | PostgreSQL + Redis |
| **TaskHub** | **transitions**（状态机）+ **Celery**（队列）| 任务生命周期、批量任务、人工审核接口 | PostgreSQL + Redis |
| **Workflow Engine** | **transitions**（状态流转）+ **Celery**（节点执行）| 串行模板、上下文传递、失败策略 | PostgreSQL + Redis |
| **Prompt Registry** | **Langfuse**（Prompt 版本化）+ **Jinja2** SandboxedEnvironment | 变量白名单、效果追踪、安全约束 | PostgreSQL |
| **Human-in-the-Loop** | — | 审核台、决策流、双人复核、反馈闭环 | PostgreSQL |

---

## 二、AgentHub — Agent 管理与配置中心

### 2.1 设计目标

- 所有业务 Agent 的统一注册发现入口
- 配置版本化快照（禁止无版本热改）
- 多环境隔离（dev/staging/prod）
- RBAC 权限与审批流（敏感 Agent 双人复核）
- 依赖声明与自动降级探测

### 2.2 开源/自研边界

| 能力 | 开源组件 | 自研部分 |
|------|---------|---------|
| 数据库 ORM | SQLAlchemy 2.0 | 表结构设计、迁移脚本 |
| 配置校验 | Pydantic | AgentConfigSnapshot 模型、校验规则 |
| 权限 RBAC | 自研（基于现有 JWT+RBAC） | AgentPermission 模型、角色矩阵 |
| 版本化存储 | PostgreSQL JSONB | 版本号自增、checksum、三态管理 |
| 依赖健康探测 | HTTP 客户端 + Redis | 探测逻辑、状态聚合、降级策略 |

### 2.3 核心数据模型

```python
# models/agent_hub.py
from sqlalchemy import Column, String, Integer, DateTime, JSON, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import enum

class AgentStatus(str, enum.Enum):
    REGISTERED = "REGISTERED"
    ACTIVE = "ACTIVE"
    DEGRADED = "DEGRADED"
    PAUSED = "PAUSED"
    OFFLINE = "OFFLINE"

class ConfigStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"
    ROLLED_BACK = "ROLLED_BACK"

class ApprovalStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class AgentRegistration(Base):
    __tablename__ = "agent_registrations"
    
    id = Column(String(64), primary_key=True)           # agent_id
    name = Column(String(128), nullable=False)
    role = Column(String(64), nullable=False)           # TREND_SCOUT / CONTENT_FORGE / ...
    description = Column(String(512))
    owner = Column(String(128), nullable=False)         # 邮箱/企微ID
    status = Column(Enum(AgentStatus), default=AgentStatus.REGISTERED)
    current_config_version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AgentConfigSnapshot(Base):
    __tablename__ = "agent_config_snapshots"
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    agent_id = Column(String(64), ForeignKey("agent_registrations.id"), nullable=False)
    version = Column(Integer, nullable=False)
    env = Column(String(16), default="prod")            # dev / staging / prod
    config_payload = Column(JSONB, nullable=False)      # {prompt_template_id, llm_route, timeout, ...}
    checksum = Column(String(64), nullable=False)       # SHA-256
    created_by = Column(String(128), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(Enum(ConfigStatus), default=ConfigStatus.DRAFT)
    approval_status = Column(Enum(ApprovalStatus), default=ApprovalStatus.PENDING)
    
    __table_args__ = (
        # 每个 Agent 每个环境同一时间只有一个 ACTIVE 版本
        # 通过应用层保证，数据库层加部分索引辅助
    )

class AgentDependency(Base):
    __tablename__ = "agent_dependencies"
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    agent_id = Column(String(64), ForeignKey("agent_registrations.id"), nullable=False)
    dep_type = Column(String(16), nullable=False)       # LLM / TOOL / DATA_SOURCE
    dep_name = Column(String(64), nullable=False)
    dep_status = Column(String(16), default="UNKNOWN")  # HEALTHY / DEGRADED / DOWN / UNKNOWN
    last_check = Column(DateTime)
    failover_config = Column(JSONB, default=dict)       # 降级策略

class AgentPermission(Base):
    __tablename__ = "agent_permissions"
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    agent_id = Column(String(64), ForeignKey("agent_registrations.id"), nullable=False)
    principal = Column(String(128), nullable=False)     # user / service_account
    principal_type = Column(String(16), nullable=False) # USER / SERVICE
    actions = Column(JSONB, default=list)               # ["READ", "INVOKE", "CONFIG", "DELETE"]
    granted_by = Column(String(128), nullable=False)
    granted_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
```

### 2.4 核心服务层设计

```python
# services/agent_hub.py
class AgentHubService:
    """AgentHub 核心服务：注册、配置版本化、权限、依赖探测"""
    
    def register_agent(self, dto: AgentRegisterDTO) -> AgentRegistration:
        """🔴 测试：注册后状态为 REGISTERED，自动生成 v1 配置快照"""
        ...
    
    def create_config_version(self, agent_id: str, payload: dict, 
                              env: str, created_by: str) -> AgentConfigSnapshot:
        """🔴 测试：版本号自增、SHA-256 checksum 正确、敏感 Agent 须审批"""
        ...
    
    def activate_config_version(self, agent_id: str, version: int, env: str) -> None:
        """🔴 测试：激活后原 ACTIVE 版本自动变为 ARCHIVED"""
        ...
    
    def rollback_config(self, agent_id: str, target_version: int, env: str) -> None:
        """🔴 测试：回滚后 target_version 变为 ACTIVE，原 ACTIVE 变为 ROLLED_BACK"""
        ...
    
    def check_dependencies(self, agent_id: str) -> list[AgentDependency]:
        """🔴 测试：探测 LLM/Tool/Data 依赖健康状态，更新 agent_registrations.status"""
        ...
    
    def validate_invocation_permission(self, agent_id: str, 
                                       principal: str, action: str) -> bool:
        """🔴 测试：Orchestrator 调度前调用，无权限抛出 403"""
        ...
```

### 2.5 与现有模块集成点

| 对接模块 | 集成方式 | 说明 |
|---------|---------|------|
| **Orchestrator** | 调度前查询 AgentHub 状态 | Agent 为 DEGRADED/OFFLINE 时拒绝调度 |
| **AgentWatch** | 依赖状态变化通知 | 依赖降级时 AgentWatch 触发告警 |
| **LLM Hub** | Agent 配置含 `llm_config_snapshot` | Agent 回滚时 LLM 配置同步回滚 |
| **Prompt Registry** | Agent 配置含 `prompt_template_versions` | Agent 回滚时 Prompt 版本同步回滚 |
| **Workflow Engine** | Workflow 节点调度前检查 Agent 状态 | 确保目标 Agent ACTIVE 且配置版本匹配 |

---

## 三、AgentWatch — Agent 活跃监控与异常检测

### 3.1 设计目标

- 心跳健康检查（30s 周期，3 周期缺失判定 UNHEALTHY）
- 实时状态看板（空闲/运行中/故障/熔断 + 队列堆积数）
- 链路追踪（OpenTelemetry trace_id + span，MVP 仅采集存储）
- 规则引擎异常检测（循环检测、超时检测、工具失败检测）
- 分级告警（P0 即时电话/短信、P1 企业微信、P2 邮件日报）

### 3.2 开源/自研边界

| 能力 | 开源组件 | 自研部分 |
|------|---------|---------|
| Trace/Metrics 采集 | **OpenTelemetry Python SDK** + contrib 探针 | trace_id 与 content_id 关联、业务语义层 |
| Trace 后端存储/查询 | **Jaeger**（all-in-one Docker）| — |
| 指标暴露 | **Prometheus Python Client** | Agent 任务完成率、队列深度、延迟等自定义指标 |
| 告警通道 | 企业微信/钉钉/邮件 SDK | 告警分级路由、P0 值班电话绑定 |
| 规则引擎 | 自研（基于 Redis + 时间窗口）| 循环检测、超时检测、工具失败检测、成本异常 |

### 3.3 OpenTelemetry 集成设计

```python
# core/telemetry.py
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.instrumentation.celery import CeleryInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

def setup_telemetry(service_name: str, jaeger_endpoint: str):
    """初始化 OpenTelemetry SDK：Trace + Metrics"""
    # Trace Provider
    trace_provider = TracerProvider()
    trace.set_tracer_provider(trace_provider)
    
    otlp_exporter = OTLPSpanExporter(endpoint=jaeger_endpoint, insecure=True)
    span_processor = BatchSpanProcessor(otlp_exporter)
    trace_provider.add_span_processor(span_processor)
    
    # Metrics Provider
    metric_exporter = OTLPMetricExporter(endpoint=jaeger_endpoint, insecure=True)
    metric_reader = PeriodicExportingMetricReader(metric_exporter, export_interval_millis=60000)
    metrics_provider = MeterProvider(metric_readers=[metric_reader])
    metrics.set_meter_provider(metrics_provider)
    
    # 自动探针
    CeleryInstrumentor().instrument()
    RedisInstrumentor().instrument()
    FastAPIInstrumentor().instrument()
    
    return trace.get_tracer(service_name), metrics.get_meter(service_name)
```

### 3.4 核心服务层设计

```python
# services/agent_watch.py
class AgentWatchService:
    """AgentWatch 核心服务：心跳、状态、链路追踪、异常检测、告警"""
    
    def record_heartbeat(self, heartbeat: AgentHeartbeatDTO) -> None:
        """🔴 测试：心跳写入 Redis TTL 7d，缺失 3 周期标记 UNHEALTHY"""
        ...
    
    def get_agent_status(self, agent_id: str) -> AgentStatusDTO:
        """🔴 测试：返回当前状态、当前任务、队列深度、最后心跳时间"""
        ...
    
    def create_trace(self, content_id: str, pipeline_type: str) -> str:
        """🔴 测试：生成 trace_id，写入 Jaeger，MVP 仅要求采集存储"""
        ...
    
    def record_span(self, trace_id: str, parent_span_id: str | None,
                    agent_id: str, input_summary: str, output_summary: str,
                    token_count: int, model_version: str, 
                    duration_ms: int, status: str) -> str:
        """🔴 测试：span 含输入/输出摘要（前 200 字符），禁止存储完整 prompt 中的密钥"""
        ...
    
    def evaluate_alert_rules(self) -> list[AgentAlert]:
        """🔴 测试：循环检测（5min 内同一 content_id ≥3 次）、超时检测、工具失败检测"""
        ...
    
    def send_alert(self, alert: AgentAlert) -> None:
        """🔴 测试：P0→电话/短信+值班群；P1→企业微信；P2→邮件日报"""
        ...
```

### 3.5 告警规则配置（运营可配置）

```python
# models/agent_watch.py
class AlertRule(Base):
    __tablename__ = "agent_watch_alert_rules"
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String(128), nullable=False)
    severity = Column(String(8), nullable=False)        # P0 / P1 / P2
    alert_type = Column(String(32), nullable=False)     # LOOP / TIMEOUT / TOOL_DEGRADED / COST_ANOMALY / HEALTH_CHECK_FAIL
    agent_id = Column(String(64), nullable=True)        # null 表示全 Agent
    condition_config = Column(JSONB, nullable=False)    # {"window_minutes": 5, "threshold_count": 3, ...}
    enabled = Column(Boolean, default=True)
    created_by = Column(String(128))
    created_at = Column(DateTime, default=datetime.utcnow)
```

---

## 四、AgentMetrics — Agent 统计与质量分析

### 4.1 设计目标

- 任务完成率统计（成功且无人工干预 / 总调用次数）
- Token 消耗与成本归因（按 Agent / 按日维度，MVP）
- 延迟分布（p50 / p95 / p99）
- 质量评分（Rubric-based + LLM-as-Judge，MVP 仅 ContentForge / ComplianceGuard）
- 人机干预率记录
- 漂移检测（Phase 2，需 7 天基线）

### 4.2 开源/自研边界

| 能力 | 开源组件 | 自研部分 |
|------|---------|---------|
| 指标采集 | **Prometheus Python Client**（Counter/Histogram/Gauge）| 业务指标定义、标签设计 |
| 质量评分 | **DeepEval**（LLM-as-Judge）| Rubric 定义、评分维度、权重配置 |
| Prompt 效果追踪 | **Langfuse**（Prompt 版本与 Trace 关联）| 性能看板数据聚合 |
| 成本计算 | 自研（结合 LLM Gateway usage + 单价表）| 按 Agent/日维度汇总，容忍 5% 误差 |

### 4.3 Prometheus 指标设计

```python
# metrics/agent_metrics.py
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry

AGENT_METRICS_REGISTRY = CollectorRegistry()

# 任务计数
agent_invocations_total = Counter(
    "agent_invocations_total",
    "Total Agent invocations",
    ["agent_id", "agent_role", "status"],  # status: success/failure/timeout
    registry=AGENT_METRICS_REGISTRY
)

# Token 消耗
agent_tokens_total = Counter(
    "agent_tokens_total",
    "Total tokens consumed by Agent",
    ["agent_id", "model", "token_type"],   # token_type: input/output
    registry=AGENT_METRICS_REGISTRY
)

# 延迟分布
agent_latency_seconds = Histogram(
    "agent_latency_seconds",
    "Agent execution latency",
    ["agent_id", "agent_role"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0],
    registry=AGENT_METRICS_REGISTRY
)

# 队列深度
agent_queue_depth = Gauge(
    "agent_queue_depth",
    "Current queue depth per Agent",
    ["agent_id"],
    registry=AGENT_METRICS_REGISTRY
)

# 人机干预计数
agent_human_interventions_total = Counter(
    "agent_human_interventions_total",
    "Total human interventions",
    ["agent_id", "intervention_type"],
    registry=AGENT_METRICS_REGISTRY
)
```

### 4.4 DeepEval 质量评分集成

```python
# services/agent_metrics_quality.py
from deepeval import evaluate
from deepeval.metrics import GEval, HallucinationMetric, AnswerRelevancyMetric
from deepeval.test_case import LLMTestCase

class AgentQualityEvaluator:
    """基于 DeepEval 的 Agent 输出质量评分器"""
    
    CONTENT_FORGE_RUBRICS = [
        GEval(
            name="结构完整性",
            criteria="评估内容是否包含 hook、body、cta、disclaimer 四个部分",
            evaluation_params=[LLMTestCase.INPUT, LLMTestCase.ACTUAL_OUTPUT]
        ),
        GEval(
            name="口语化程度",
            criteria="评估内容是否自然口语化，避免过度营销语气",
            evaluation_params=[LLMTestCase.INPUT, LLMTestCase.ACTUAL_OUTPUT]
        ),
        GEval(
            name="合规标签命中",
            criteria="评估内容是否包含必要的合规标签和免责声明",
            evaluation_params=[LLMTestCase.INPUT, LLMTestCase.ACTUAL_OUTPUT]
        ),
    ]
    
    def evaluate_content_forge(self, content_id: str, 
                               input_prompt: str, output_content: str) -> dict:
        """🔴 测试：返回结构完整性/口语化/合规命中三维评分 + 加权总分"""
        test_case = LLMTestCase(input=input_prompt, actual_output=output_content)
        results = evaluate([test_case], self.CONTENT_FORGE_RUBRICS)
        return self._aggregate_scores(results)
    
    def evaluate_compliance_guard(self, content_id: str,
                                   content: str, verdict: str, 
                                   human_labels: list[str] | None = None) -> dict:
        """🔴 测试：计算误杀率/漏杀率（需人工抽样标注）"""
        ...
```

### 4.5 核心数据模型

```python
# models/agent_metrics.py
class AgentDailyMetrics(Base):
    __tablename__ = "agent_daily_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    agent_id = Column(String(64), ForeignKey("agent_registrations.id"), nullable=False)
    date = Column(Date, nullable=False)
    total_invocations = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    timeout_count = Column(Integer, default=0)
    human_intervention_count = Column(Integer, default=0)
    task_completion_rate = Column(Float)
    human_intervention_rate = Column(Float)
    avg_latency_ms = Column(Float)
    p95_latency_ms = Column(Float)
    p99_latency_ms = Column(Float)
    total_input_tokens = Column(Integer, default=0)
    total_output_tokens = Column(Integer, default=0)
    estimated_cost_usd = Column(Float)
    quality_score_avg = Column(Float)
    
    __table_args__ = (
        # 按 agent_id + date 唯一
    )

class AgentQualityScore(Base):
    __tablename__ = "agent_quality_scores"
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    agent_id = Column(String(64), nullable=False)
    content_id = Column(String(64), nullable=True)
    trace_id = Column(String(64), nullable=False)
    evaluator = Column(String(32), nullable=False)      # LLM_JUDGE / RULE_ENGINE / HUMAN
    rubric_version = Column(String(32), nullable=False)
    dimensions = Column(JSONB, default=list)            # [{"dimension": "结构完整性", "score": 85, "weight": 0.3}, ...]
    overall_score = Column(Float)
    evaluated_at = Column(DateTime, default=datetime.utcnow)
    evaluated_by = Column(String(128), nullable=True)   # 人工评分时记录

class HumanIntervention(Base):
    __tablename__ = "human_interventions"
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    agent_id = Column(String(64), nullable=False)
    content_id = Column(String(64), nullable=False)
    trace_id = Column(String(64), nullable=False)
    intervention_type = Column(String(32), nullable=False)  # MODIFY_OUTPUT / SKIP_AGENT / FORCE_RETRY / OVERRIDE_DECISION
    reason = Column(String(512))
    operator = Column(String(128), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    before_snapshot = Column(Text, nullable=True)
    after_snapshot = Column(Text, nullable=True)
```

---

## 五、LLM Hub — 大模型统一管理与配置中心

### 5.1 设计目标

- 国产/国外模型统一注册（DeepSeek、Qwen、GPT-4o、Claude 等）
- 三层配置粒度：Global Default → Agent 级 → Skill 级
- 路由策略：固定路由 / 加权随机 / 故障转移
- 成本治理：预算配额、成本告警、日/月限额、自动降模
- 熔断与降级：错误率熔断、延迟熔断、手动熔断、恢复探测

### 5.2 开源/自研边界

| 能力 | 开源组件 | 自研部分 |
|------|---------|---------|
| LLM 统一调用 | **LiteLLM** Router SDK | 三层配置合并逻辑、合规预检、预算检查 |
| 熔断器 | **pybreaker** | 错误率/延迟熔断规则、与 AgentWatch 告警联动 |
| 重试策略 | **stamina** | 指数退避 + jitter，按模型差异化阈值 |
| 成本计算 | 自研（单价表 × Token 数）| 多币种换算、预算配额管理、告警触发 |
| 合规分级 | 自研 | T0/T1/T2 数据出境校验、敏感数据拦截 |

### 5.3 pybreaker + stamina 集成示例

```python
# services/llm_hub/circuit_breaker.py
from pybreaker import CircuitBreaker
from stamina import retry
import stamina
import redis

class LLMCircuitBreakerManager:
    """LLM 专用熔断器管理器：基于 pybreaker，支持 Redis 分布式状态"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self._breakers: dict[str, CircuitBreaker] = {}
    
    def get_breaker(self, model_id: str) -> CircuitBreaker:
        """为每个模型维护独立熔断器"""
        if model_id not in self._breakers:
            self._breakers[model_id] = CircuitBreaker(
                fail_max=5,           # 连续失败 5 次熔断
                reset_timeout=600,    # 熔断 10 分钟后尝试恢复
                expected_exception=(Exception,),  # 可按模型细化
                listeners=[self._breaker_event_listener]
            )
        return self._breakers[model_id]
    
    def _breaker_event_listener(self, event):
        """熔断器状态变化 → 写入 AgentWatch 告警"""
        ...

class LLMRouteExecutor:
    """LLM 路由执行器：stamina 重试 + pybreaker 熔断 + LiteLLM 调用"""
    
    @retry(
        on=Exception,
        attempts=3,
        timeout=None,
        backoff=stamina.ExponentialBackoff(initial_delay=1.0, max_delay=8.0)
    )
    async def execute_with_fallback(self, agent_id: str, skill_id: str | None,
                                    messages: list, data_sensitivity: str) -> dict:
        """完整路由决策流程"""
        # 1. 配置层合并: Skill > Agent > Global
        config = self._resolve_config(agent_id, skill_id)
        
        # 2. 合规预检: T2 模型禁止处理敏感数据
        model_id = config.default_model
        if data_sensitivity == "HIGH" and self._get_model_tier(model_id) == "T2":
            model_id = config.fallback_chain[0]  # 强制降级到 T0/T1
        
        # 3. 预算检查
        if self._budget_exceeded(agent_id, model_id):
            raise BudgetExceededError("预算已耗尽")
        
        # 4. 熔断检查
        breaker = self.breaker_manager.get_breaker(model_id)
        
        # 5. 执行调用（在熔断器保护下）
        try:
            result = breaker(
                lambda: self.litellm_router.completion(model=model_id, messages=messages)
            )
            self._record_success(model_id, agent_id, result)
            return result
        except Exception as e:
            self._record_failure(model_id, agent_id, e)
            # 尝试 fallback chain
            for fallback_model in config.fallback_chain:
                try:
                    result = self.litellm_router.completion(
                        model=fallback_model, messages=messages
                    )
                    self._record_fallback(model_id, fallback_model, agent_id, result)
                    return result
                except Exception:
                    continue
            raise LLMRouteExhaustedError("主模型与降级链全部失败")
```

### 5.4 核心数据模型

```python
# models/llm_hub.py
class LLMModel(Base):
    __tablename__ = "llm_models"
    
    id = Column(String(64), primary_key=True)           # 统一标识，如 "deepseek-chat"
    name = Column(String(128), nullable=False)
    provider = Column(String(32), nullable=False)       # deepseek / openai / anthropic / ...
    provider_model_id = Column(String(64), nullable=False)
    capabilities = Column(JSONB, default=list)          # ["text", "multimodal", "json_mode"]
    compliance_tier = Column(String(4), nullable=False) # T0 / T1 / T2
    max_tokens = Column(Integer)
    max_input_tokens = Column(Integer)
    supports_streaming = Column(Boolean, default=False)
    cost_per_1k_input = Column(Float)
    cost_per_1k_output = Column(Float)
    cost_currency = Column(String(4), default="USD")
    status = Column(String(16), default="ACTIVE")       # ACTIVE / DEGRADED / DEPRECATED / BETA
    endpoint_base_url = Column(String(256), nullable=True)
    api_key_ref = Column(String(128), nullable=False)   # Vault 中的引用，禁止明文
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class LLMConfigLayer(Base):
    __tablename__ = "llm_config_layers"
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    layer = Column(String(16), nullable=False)          # GLOBAL / AGENT / SKILL
    target_id = Column(String(64), nullable=True)       # agent_id 或 skill_id；GLOBAL 为 null
    default_model = Column(String(64), ForeignKey("llm_models.id"))
    fallback_chain = Column(JSONB, default=list)
    timeout_seconds = Column(Integer, default=60)
    max_retries = Column(Integer, default=2)
    temperature = Column(Float, default=0.5)
    top_p = Column(Float, nullable=True)
    max_tokens = Column(Integer, nullable=True)
    route_strategy = Column(String(32), default="PINNED")  # PINNED / WEIGHTED_RANDOM / FAILOVER
    route_weights = Column(JSONB, nullable=True)
    allowed_models = Column(JSONB, default=list)
    forbidden_models = Column(JSONB, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class LLMRouteDecision(Base):
    __tablename__ = "llm_route_decisions"
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    trace_id = Column(String(64), nullable=False)
    content_id = Column(String(64), nullable=True)
    agent_id = Column(String(64), nullable=False)
    skill_id = Column(String(64), nullable=True)
    requested_model = Column(String(64), nullable=False)
    resolved_model = Column(String(64), nullable=False)
    route_strategy = Column(String(32), nullable=False)
    fallback_level = Column(Integer, default=0)
    reason = Column(String(32), nullable=False)         # DEFAULT / AGENT_OVERRIDE / SKILL_OVERRIDE / FALLBACK / COST_LIMIT
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    cost_usd = Column(Float, default=0.0)
    latency_ms = Column(Integer)
    status = Column(String(16), nullable=False)         # SUCCESS / ERROR / TIMEOUT / FALLBACK
    created_at = Column(DateTime, default=datetime.utcnow)

class CircuitBreakerState(Base):
    __tablename__ = "circuit_breaker_states"
    
    model_id = Column(String(64), primary_key=True)
    state = Column(String(16), default="CLOSED")        # CLOSED / OPEN / HALF_OPEN
    failure_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    last_failure_at = Column(DateTime, nullable=True)
    last_success_at = Column(DateTime, nullable=True)
    opened_at = Column(DateTime, nullable=True)
    half_open_at = Column(DateTime, nullable=True)
    trip_reason = Column(String(64), nullable=True)
    auto_recovery = Column(Boolean, default=True)
```

---

## 六、CronHub — 定时任务调度中心

### 6.1 设计目标

- Job 模板注册（系统预设 + 自定义）
- Cron 表达式解析与调度（标准 Unix Cron + 扩展语法）
- 分布式锁防止重复执行
- 失败重试（指数退避）与死信队列（DLQ）
- 执行历史与审计（热库 30 天 + 冷存 180 天）

### 6.2 开源/自研边界

| 能力 | 开源组件 | 自研部分 |
|------|---------|---------|
| 调度引擎 | **Celery Beat** | CronHub 作为上层管理面，动态 reload Beat schedule |
| Cron 解析 | **croniter** | 下次执行时间计算、时区处理、表达式校验 |
| 分布式锁 | Redis `SET NX` | 锁过期时间为 Job 超时的 2 倍 |
| 重试策略 | **stamina**（函数级）+ Celery（队列级）| 指数退避参数、失败分级判断 |
| 死信队列 | Celery DLQ | 死信入队、人工介入界面、批量操作 |

### 6.3 croniter 集成设计

```python
# services/cron_hub/schedule_engine.py
from croniter import croniter
from datetime import datetime
import pytz

class ScheduleEngine:
    """CronHub 调度引擎：基于 croniter 的 Cron 解析与触发计算"""
    
    def validate_cron(self, expression: str) -> bool:
        """🔴 测试：有效 Cron 返回 True，无效返回 False"""
        try:
            croniter(expression)
            return True
        except (ValueError, KeyError):
            return False
    
    def get_next_run(self, expression: str, timezone: str = "Asia/Shanghai") -> datetime:
        """🔴 测试：返回指定时区的下次执行时间"""
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)
        itr = croniter(expression, now)
        return itr.get_next(datetime)
    
    def get_run_times_in_range(self, expression: str, 
                               start: datetime, end: datetime,
                               timezone: str = "Asia/Shanghai") -> list[datetime]:
        """🔴 测试：返回时间范围内所有执行时间点"""
        tz = pytz.timezone(timezone)
        itr = croniter(expression, start)
        runs = []
        while True:
            nxt = itr.get_next(datetime)
            if nxt > end:
                break
            runs.append(nxt.astimezone(tz))
        return runs
```

### 6.4 核心数据模型

```python
# models/cron_hub.py
class CronJob(Base):
    __tablename__ = "cron_jobs"
    
    id = Column(String(64), primary_key=True)
    name = Column(String(128), nullable=False)
    description = Column(String(512))
    job_type = Column(String(16), default="CUSTOM")     # SYSTEM / CUSTOM
    source_template = Column(String(64), nullable=True)
    target_type = Column(String(16), nullable=False)    # AGENT / API / SCRIPT
    target_id = Column(String(64), nullable=False)      # agent_id 或 API endpoint
    target_params = Column(JSONB, default=dict)
    schedule = Column(String(64), nullable=False)       # Cron 表达式
    timezone = Column(String(32), default="Asia/Shanghai")
    concurrency_policy = Column(String(16), default="SKIP")  # SKIP / QUEUE / ALLOW
    retry_policy = Column(JSONB, default=lambda: {"max_retries": 3, "backoff_type": "exponential", "initial_delay_sec": 60})
    timeout_seconds = Column(Integer, default=300)
    dry_run_supported = Column(Boolean, default=False)
    status = Column(String(16), default="ACTIVE")       # ACTIVE / PAUSED / ARCHIVED
    owner = Column(String(128), nullable=False)
    current_version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class JobExecution(Base):
    __tablename__ = "job_executions"
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    job_id = Column(String(64), ForeignKey("cron_jobs.id"), nullable=False)
    version = Column(Integer, nullable=False)
    execution_type = Column(String(16), nullable=False) # SCHEDULED / MANUAL / DRY_RUN / RETRY
    scheduled_at = Column(DateTime, nullable=False)
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    status = Column(String(16), nullable=False)         # PENDING / RUNNING / SUCCESS / FAILED / TIMEOUT / SKIPPED / CANCELLED
    output_summary = Column(String(200), nullable=True)
    error_message = Column(Text, nullable=True)
    error_type = Column(String(32), nullable=True)      # RETRYABLE / NON_RETRYABLE / AGENT_DEGRADED
    retry_count = Column(Integer, default=0)
    trace_id = Column(String(64), nullable=False)
    triggered_by = Column(String(128), nullable=True)   # 手动触发时记录
    created_at = Column(DateTime, default=datetime.utcnow)

class DeadLetterJob(Base):
    __tablename__ = "dead_letter_jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    job_id = Column(String(64), nullable=False)
    execution_id = Column(UUID(as_uuid=True), nullable=False)
    failed_at = Column(DateTime, default=datetime.utcnow)
    error_message = Column(Text, nullable=False)
    error_type = Column(String(32), nullable=False)
    retry_exhausted = Column(Boolean, default=True)
    context_snapshot = Column(JSONB, default=dict)
    status = Column(String(32), default="PENDING_REVIEW")  # PENDING_REVIEW / RETRIED / IGNORED / MANUAL_EXECUTED
    reviewed_by = Column(String(128), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

---

## 七、TaskHub — 任务中心

### 7.1 设计目标

- 任务创建：账号池 + 人设 + 工作流模板 + Prompt 变量
- 任务状态机（DRAFT → CONFIGURING → QUEUED → RUNNING → PAUSED → COMPLETED / FAILED / CANCELLED / HUMAN_WAIT）
- 批量任务（parent_task_id 关联子任务）
- 定时任务绑定（CronHub 集成）
- 人工审核接口（通过/驳回/打回修改）

### 7.2 开源/自研边界

| 能力 | 开源组件 | 自研部分 |
|------|---------|---------|
| 状态机 | **transitions** | Task 状态流转定义、状态迁移守卫、回调钩子 |
| 任务队列 | **Celery** | 账号独立队列、优先级排序、全局队列管理 |
| 批量任务 | 自研 | 子任务生成、进度聚合、父任务状态推导 |

### 7.3 transitions 状态机设计

```python
# services/task_hub/state_machine.py
from transitions import Machine

class TaskStateMachine:
    """Task 状态机：基于 transitions 库"""
    
    STATES = [
        "DRAFT", "CONFIGURING", "QUEUED", "RUNNING", 
        "PAUSED", "HUMAN_WAIT", "COMPLETED", "FAILED", "CANCELLED"
    ]
    
    TRANSITIONS = [
        {"trigger": "configure", "source": "DRAFT", "dest": "CONFIGURING"},
        {"trigger": "queue", "source": "CONFIGURING", "dest": "QUEUED"},
        {"trigger": "start", "source": "QUEUED", "dest": "RUNNING"},
        {"trigger": "pause", "source": "RUNNING", "dest": "PAUSED"},
        {"trigger": "resume", "source": "PAUSED", "dest": "RUNNING"},
        {"trigger": "wait_human", "source": "RUNNING", "dest": "HUMAN_WAIT"},
        {"trigger": "approve", "source": "HUMAN_WAIT", "dest": "RUNNING"},
        {"trigger": "reject", "source": "HUMAN_WAIT", "dest": "FAILED"},
        {"trigger": "complete", "source": "RUNNING", "dest": "COMPLETED"},
        {"trigger": "fail", "source": ["RUNNING", "QUEUED"], "dest": "FAILED"},
        {"trigger": "cancel", "source": ["DRAFT", "CONFIGURING", "QUEUED", "RUNNING", "PAUSED", "HUMAN_WAIT"], "dest": "CANCELLED"},
        {"trigger": "retry", "source": "FAILED", "dest": "QUEUED"},
    ]
    
    def __init__(self, task_id: str):
        self.task_id = task_id
        self.machine = Machine(
            model=self,
            states=self.STATES,
            transitions=self.TRANSITIONS,
            initial="DRAFT",
            after_state_change=self._persist_state
        )
    
    def _persist_state(self, event):
        """状态变化后持久化到数据库 + 写入 AgentWatch trace"""
        ...
    
    def on_enter_RUNNING(self):
        """进入 RUNNING 时：触发 Workflow Engine 执行下一节点"""
        ...
    
    def on_enter_HUMAN_WAIT(self):
        """进入 HUMAN_WAIT 时：通知审核台，启动超时计时器（默认 24h）"""
        ...
    
    def on_enter_FAILED(self):
        """进入 FAILED 时：记录失败原因，触发 AgentWatch 告警"""
        ...
```

### 7.4 核心数据模型

```python
# models/task_hub.py
class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(String(64), primary_key=True)
    name = Column(String(256), nullable=False)
    workflow_template_id = Column(String(64), nullable=False)
    workflow_version = Column(Integer, nullable=False)
    account_id = Column(String(64), ForeignKey("accounts.id"), nullable=False)
    persona_id = Column(String(64), ForeignKey("personas.id"), nullable=False)
    prompt_variables = Column(JSONB, default=dict)
    status = Column(String(16), default="DRAFT")
    current_node_index = Column(Integer, default=0)
    parent_task_id = Column(String(64), ForeignKey("tasks.id"), nullable=True)
    priority = Column(Integer, default=50)              # 0-100，账号健康分映射
    scheduled_at = Column(DateTime, nullable=True)
    created_by = Column(String(128), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

class TaskNodeExecution(Base):
    __tablename__ = "task_node_executions"
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    task_id = Column(String(64), ForeignKey("tasks.id"), nullable=False)
    node_id = Column(String(64), nullable=False)
    node_type = Column(String(16), nullable=False)      # AGENT / HUMAN_APPROVAL / TIMER
    agent_id = Column(String(64), nullable=True)
    prompt_template_id = Column(String(64), nullable=True)
    status = Column(String(16), default="PENDING")      # PENDING / RUNNING / SUCCESS / FAILED / SKIPPED / TIMEOUT / HUMAN_WAIT
    input_context = Column(JSONB, default=dict)         # 输入上下文摘要（前 500 字符）
    output_context = Column(JSONB, default=dict)        # 输出上下文摘要（前 500 字符）
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    trace_id = Column(String(64), nullable=False)
    human_decision = Column(String(16), nullable=True)  # APPROVE / REJECT / REVISE
    human_feedback = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

---

## 八、Workflow Engine — 工作流编排引擎

### 8.1 设计目标

- MVP 仅限串行 Pipeline（禁止 DAG 分支、并行节点、条件跳转）
- 预设工作流模板（content_creation_standard / content_creation_light / trend_scout_only / data_analysis_only）
- 节点类型：agent / human_approval / timer
- 上下文传递：Redis `workflow_context:{task_id}`
- 失败策略：fail_fast / continue / retry_then_fail

### 8.2 开源/自研边界

| 能力 | 开源组件 | 自研部分 |
|------|---------|---------|
| Pipeline 状态流转 | **transitions** | WorkflowTemplate / WorkflowExecution 状态机 |
| 节点执行 | **Celery** | Agent 调用编排、上下文注入、结果回写 |
| 上下文存储 | Redis | Context Store 封装、摘要生成、S3/OSS 大文本引用 |

### 8.3 预设工作流模板

```python
# config/workflow_presets.py
CONTENT_CREATION_STANDARD = {
    "id": "content_creation_standard",
    "name": "标准内容生产工作流",
    "description": "选题→结构分析→框架生成→正文生成→合规审核→互动预演→人工审核→发布",
    "nodes": [
        {"node_index": 0, "node_type": "AGENT", "agent_id": "trend-scout", "node_name": "热点侦察", "fail_strategy": "FAIL_FAST"},
        {"node_index": 1, "node_type": "AGENT", "agent_id": "marketing-methodology", "node_name": "结构分析", "fail_strategy": "FAIL_FAST"},
        {"node_index": 2, "node_type": "AGENT", "agent_id": "content-forge", "node_name": "框架生成", "prompt_template_id": "cf-outline", "fail_strategy": "FAIL_FAST"},
        {"node_index": 3, "node_type": "AGENT", "agent_id": "content-forge", "node_name": "正文生成", "prompt_template_id": "cf-body", "fail_strategy": "FAIL_FAST"},
        {"node_index": 4, "node_type": "AGENT", "agent_id": "compliance-guard", "node_name": "合规审核", "fail_strategy": "FAIL_FAST"},
        {"node_index": 5, "node_type": "AGENT", "agent_id": "pool-predictor", "node_name": "互动预演", "fail_strategy": "CONTINUE"},  # 非阻塞
        {"node_index": 6, "node_type": "HUMAN_APPROVAL", "node_name": "人工审核", "human_config": {"review_type": "CONTENT_PUBLISH", "timeout_hours": 24, "required_role": "content_reviewer"}},
        {"node_index": 7, "node_type": "AGENT", "agent_id": "publisher", "node_name": "发布", "fail_strategy": "FAIL_FAST"},
    ]
}

# 红线：任何含 Publisher 的工作流模板必须包含 human_approval 节点，且不可删除
```

### 8.4 上下文传递设计

```python
# services/workflow_engine/context_store.py
import json
import redis

class WorkflowContextStore:
    """工作流上下文存储：Redis + S3/OSS 大文本引用"""
    
    CONTEXT_TTL_SECONDS = 30 * 24 * 3600  # 30 天
    MAX_INLINE_SIZE = 500                 # 字符，超过则存 S3
    
    def __init__(self, redis_client: redis.Redis, s3_client):
        self.redis = redis_client
        self.s3 = s3_client
    
    def write_node_output(self, task_id: str, node_index: int, 
                          output_data: dict) -> None:
        """写入节点输出到上下文"""
        key = f"workflow_context:{task_id}"
        
        # 大文本处理
        for field, value in output_data.items():
            if isinstance(value, str) and len(value) > self.MAX_INLINE_SIZE:
                # 存 S3，Context 中存引用
                s3_key = f"workflow-contexts/{task_id}/node_{node_index}/{field}.txt"
                self.s3.put_object(Bucket="ecodream-ctx", Key=s3_key, Body=value.encode())
                output_data[field] = {"__ref__": s3_key, "__preview__": value[:self.MAX_INLINE_SIZE]}
        
        # 写入 Redis Hash
        self.redis.hset(key, f"node_{node_index}", json.dumps(output_data))
        self.redis.expire(key, self.CONTEXT_TTL_SECONDS)
    
    def read_node_output(self, task_id: str, node_index: int) -> dict:
        """读取节点输出"""
        key = f"workflow_context:{task_id}"
        data = self.redis.hget(key, f"node_{node_index}")
        return json.loads(data) if data else {}
    
    def get_full_context(self, task_id: str) -> dict:
        """获取完整上下文（用于调试/审计）"""
        key = f"workflow_context:{task_id}"
        raw = self.redis.hgetall(key)
        return {k.decode(): json.loads(v) for k, v in raw.items()}
```

### 8.5 核心数据模型

```python
# models/workflow_engine.py
class WorkflowTemplate(Base):
    __tablename__ = "workflow_templates"
    
    id = Column(String(64), primary_key=True)
    name = Column(String(128), nullable=False)
    description = Column(String(512))
    source_preset = Column(String(64), nullable=True)
    version = Column(Integer, default=1)
    status = Column(String(16), default="DRAFT")        # DRAFT / ACTIVE / DEPRECATED
    owner = Column(String(128), nullable=False)
    nodes = Column(JSONB, default=list)                 # List[WorkflowNode]
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    approval_status = Column(String(16), default="PENDING")  # PENDING / APPROVED

class WorkflowNode(Base):
    """内嵌在 WorkflowTemplate.nodes JSONB 中的节点定义"""
    # 见 8.3 预设模板中的字段定义
    pass  # SQLAlchemy JSONB 直接存储，不单独建表

class WorkflowExecution(Base):
    __tablename__ = "workflow_executions"
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    task_id = Column(String(64), ForeignKey("tasks.id"), nullable=False)
    template_id = Column(String(64), ForeignKey("workflow_templates.id"), nullable=False)
    template_version = Column(Integer, nullable=False)
    status = Column(String(16), default="RUNNING")      # RUNNING / PAUSED / COMPLETED / FAILED / CANCELLED
    current_node_index = Column(Integer, default=0)
    context_ref = Column(String(128), nullable=False)   # Redis key: workflow_context:{task_id}
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

---

## 九、Prompt Registry — Prompt 全生命周期管理

### 9.1 设计目标

- Prompt 模板注册（Jinja2 变量语法，严格白名单）
- 版本化与环境隔离（DRAFT / ACTIVE / ARCHIVED，dev/staging/prod）
- 变量白名单校验（未注册变量拒绝保存）
- 效果追踪（任务完成率、人工干预率、质量评分）
- 安全约束：XSS 过滤、Prompt 注入检测

### 9.2 开源/自研边界

| 能力 | 开源组件 | 自研部分 |
|------|---------|---------|
| Prompt 版本化管理 | **Langfuse**（Prompt Management API）| 与 AgentHub 配置回滚联动、变量白名单校验 |
| 模板渲染 | **Jinja2** SandboxedEnvironment | 变量白名单注入、渲染前安全检查 |
| 效果追踪 | **Langfuse**（Prompt 版本与 Trace 关联）| 性能看板聚合、A/B 测试框架（Phase 2） |
| 安全检测 | 自研（正则 + AST 提取）| Prompt 注入关键词黑名单、变量长度限制 |

### 9.3 Jinja2 安全渲染设计

```python
# services/prompt_registry/security.py
from jinja2.sandbox import SandboxedEnvironment
from jinja2.meta import find_undeclared_variables
import re

class SecurePromptRenderer:
    """Prompt 安全渲染器：沙箱 + 白名单 + 注入检测"""
    
    INJECTION_BLACKLIST = [
        r"ignore\s+previous\s+instructions",
        r"system\s+override",
        r"ignore\s+above",
        r"disregard\s+.*prompt",
        r"__\w+__",            # SSTI 特征
        r"\{\{.*\}\}.*\{\{.*\}\}",  # 嵌套变量（简化检测）
    ]
    
    MAX_VARIABLE_LENGTH = 100
    
    def __init__(self, registered_variables: set[str]):
        self.registered_variables = registered_variables
        self.env = SandboxedEnvironment()
    
    def validate_template(self, template_content: str) -> tuple[bool, str]:
        """🔴 测试：未注册变量返回 (False, 错误信息)；含注入模式返回 (False, 安全告警)"""
        # 1. AST 提取变量
        ast = self.env.parse(template_content)
        undeclared = find_undeclared_variables(ast)
        
        unknown = undeclared - self.registered_variables
        if unknown:
            return False, f"未注册变量: {', '.join(unknown)}"
        
        # 2. 注入检测
        for pattern in self.INJECTION_BLACKLIST:
            if re.search(pattern, template_content, re.IGNORECASE):
                return False, f"检测到潜在 Prompt 注入模式: {pattern}"
        
        return True, "OK"
    
    def render(self, template_content: str, variables: dict) -> str:
        """🔴 测试：渲染前校验变量类型与长度，超长发截断告警"""
        # 校验变量
        for name, value in variables.items():
            if name not in self.registered_variables:
                raise ValueError(f"未注册变量: {name}")
            if isinstance(value, str) and len(value) > self.MAX_VARIABLE_LENGTH:
                variables[name] = value[:self.MAX_VARIABLE_LENGTH]
                # 记录告警日志
        
        template = self.env.from_string(template_content)
        return template.render(**variables)
```

### 9.4 Langfuse 集成设计

```python
# services/prompt_registry/langfuse_adapter.py
from langfuse import Langfuse

class PromptRegistryLangfuseAdapter:
    """Prompt Registry 的 Langfuse 适配层"""
    
    def __init__(self, langfuse: Langfuse):
        self.langfuse = langfuse
    
    def create_prompt_version(self, agent_id: str, name: str, 
                              template_content: str, variables: list[str],
                              env: str = "prod") -> str:
        """🔴 测试：创建 Prompt 版本，返回 Langfuse prompt_id"""
        prompt = self.langfuse.create_prompt(
            name=f"{agent_id}/{name}",
            prompt=template_content,
            config={
                "variables": variables,
                "env": env,
                "agent_id": agent_id,
            },
            is_active=False  # 默认草稿，需手动激活
        )
        return prompt.id
    
    def activate_version(self, prompt_id: str, label: str = "production") -> None:
        """🔴 测试：激活指定版本，原 production label 自动转移"""
        self.langfuse.prompt(prompt_id).update_label(label)
    
    def get_active_prompt(self, agent_id: str, name: str, 
                          env: str = "prod") -> dict:
        """🔴 测试：获取当前生效的 Prompt 版本"""
        prompt = self.langfuse.get_prompt(
            name=f"{agent_id}/{name}",
            label="production",
            cache_ttl_seconds=60
        )
        return {
            "prompt_id": prompt.id,
            "version": prompt.version,
            "content": prompt.prompt,
            "config": prompt.config,
        }
    
    def record_prompt_performance(self, prompt_id: str, trace_id: str,
                                   score: float, metadata: dict) -> None:
        """记录 Prompt 版本的效果评分（与 Langfuse Score 关联）"""
        self.langfuse.score(
            trace_id=trace_id,
            name="prompt_quality",
            value=score,
            comment=json.dumps(metadata)
        )
```

### 9.5 核心数据模型

```python
# models/prompt_registry.py
class PromptTemplate(Base):
    __tablename__ = "prompt_templates"
    
    id = Column(String(64), primary_key=True)
    name = Column(String(256), nullable=False)
    agent_id = Column(String(64), ForeignKey("agent_registrations.id"), nullable=False)
    version = Column(Integer, default=1)
    env = Column(String(16), default="prod")            # dev / staging / prod
    template_content = Column(Text, nullable=False)     # Jinja2 模板
    variables = Column(JSONB, default=list)             # 白名单变量列表
    system_fingerprint = Column(String(64), nullable=False)  # SHA-256
    status = Column(String(16), default="DRAFT")        # DRAFT / ACTIVE / ARCHIVED
    approval_status = Column(String(16), default="PENDING")
    performance_score = Column(Float, nullable=True)
    langfuse_prompt_id = Column(String(64), nullable=True)  # 关联 Langfuse
    created_by = Column(String(128), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PromptVariable(Base):
    __tablename__ = "prompt_variables"
    
    name = Column(String(64), primary_key=True)
    description = Column(String(256), nullable=False)
    type = Column(String(16), default="STRING")         # STRING / NUMBER / ENUM / JSON
    allowed_values = Column(JSONB, nullable=True)       # ENUM 类型可选值
    max_length = Column(Integer, default=100)
    required = Column(Boolean, default=True)
    default_value = Column(String(256), nullable=True)
    validation_regex = Column(String(256), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class PromptPerformance(Base):
    __tablename__ = "prompt_performances"
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    template_id = Column(String(64), ForeignKey("prompt_templates.id"), nullable=False)
    version = Column(Integer, nullable=False)
    date = Column(Date, nullable=False)
    invocations = Column(Integer, default=0)
    avg_quality_score = Column(Float)
    avg_token_cost = Column(Float)
    human_intervention_rate = Column(Float)
    task_completion_rate = Column(Float)
    fail_rate = Column(Float)
```

---

## 十、Human-in-the-Loop — 人工审核台

### 10.1 设计目标

- 审核台视图：内容预览 + Agent 输出摘要 + Prompt 变量
- 审核决策：通过（立即/定时发布）、驳回（须填理由）、打回修改（指定节点）
- 双人复核（Publisher 发布确认须双人复核）
- 反馈闭环：人工修改差异写入 human_intervention 表

### 10.2 开源/自研边界

| 能力 | 开源组件 | 自研部分 |
|------|---------|---------|
| 审核台 UI | React + shadcn/ui | 内容预览、Agent 摘要卡片、操作按钮 |
| 权限校验 | 现有 RBAC | Human-in-the-Loop 专用权限（APPROVE_CONTENT / PUBLISH_CONTENT） |
| 反馈闭环 | 自研 | 差异计算、NLP 聚类（Phase 2）、驳回理由分布 |

### 10.3 核心服务层设计

```python
# services/human_in_loop.py
class HumanInLoopService:
    """人工审核台核心服务"""
    
    def get_pending_tasks(self, reviewer_role: str | None = None,
                          account_id: str | None = None) -> list[PendingTaskDTO]:
        """🔴 测试：返回待审核任务列表，按优先级/时间排序"""
        ...
    
    def get_review_detail(self, task_id: str) -> ReviewDetailDTO:
        """🔴 测试：返回内容预览 + Agent 输出摘要 + Prompt 变量 + 链路追踪入口"""
        ...
    
    def approve(self, task_id: str, operator: str,
                publish_mode: str = "immediate", scheduled_at: datetime | None = None) -> None:
        """🔴 测试：审核通过，任务状态 HUMAN_WAIT → RUNNING，Publisher 节点执行"""
        ...
    
    def reject(self, task_id: str, operator: str, reason: str) -> None:
        """🔴 测试：审核驳回，任务状态 HUMAN_WAIT → FAILED，记录驳回理由"""
        ...
    
    def revise(self, task_id: str, operator: str, 
               target_node_index: int, revised_variables: dict) -> None:
        """🔴 测试：打回修改，重置 current_node_index，修改变量后重新执行下游"""
        ...
    
    def require_dual_approval(self, task_id: str) -> bool:
        """🔴 测试：Publisher 节点前强制双人复核"""
        ...
    
    def record_intervention(self, task_id: str, intervention_type: str,
                            operator: str, before: str, after: str, reason: str) -> None:
        """记录人机干预差异，汇入 AgentMetrics"""
        ...
```

### 10.4 核心数据模型

```python
# models/human_in_loop.py
class ReviewRecord(Base):
    __tablename__ = "review_records"
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    task_id = Column(String(64), ForeignKey("tasks.id"), nullable=False)
    reviewer = Column(String(128), nullable=False)
    decision = Column(String(16), nullable=False)       # APPROVE / REJECT / REVISE
    reason = Column(String(512), nullable=True)
    target_node_index = Column(Integer, nullable=True)  # REVISE 时指定
    revised_variables = Column(JSONB, nullable=True)
    publish_mode = Column(String(16), nullable=True)    # immediate / scheduled
    scheduled_at = Column(DateTime, nullable=True)
    is_dual_approval = Column(Boolean, default=False)
    dual_approver = Column(String(128), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

---

## 十一、数据模型总览

### 11.1 新增表清单

| 表名 | 所属模块 | 核心用途 | 数据量预估 |
|------|---------|---------|-----------|
| `agent_registrations` | AgentHub | Agent 注册信息 | 小（<100 条） |
| `agent_config_snapshots` | AgentHub | 配置版本化快照 | 中（每 Agent 10+ 版本） |
| `agent_dependencies` | AgentHub | 依赖声明 | 小（<500 条） |
| `agent_permissions` | AgentHub | RBAC 权限矩阵 | 小（<1000 条） |
| `agent_heartbeats` | AgentWatch | 心跳记录（Redis 为主，DB 归档） | 大（TTL 7d） |
| `agent_traces` | AgentWatch | 链路追踪（MVP 仅采集，详数据在 Jaeger） | 中 |
| `agent_spans` | AgentWatch | Span 详情 | 中 |
| `agent_alerts` | AgentWatch | 告警记录 | 中 |
| `agent_watch_alert_rules` | AgentWatch | 告警规则配置 | 小（<50 条） |
| `agent_daily_metrics` | AgentMetrics | 日维度统计 | 中（每 Agent × 每天 1 条） |
| `agent_quality_scores` | AgentMetrics | 质量评分记录 | 中 |
| `human_interventions` | AgentMetrics | 人机干预记录 | 中 |
| `llm_models` | LLM Hub | 模型注册表 | 小（<20 条） |
| `llm_config_layers` | LLM Hub | 三层配置 | 中 |
| `llm_route_decisions` | LLM Hub | 路由决策审计日志 | 大（每次调用 1 条，热库 30d + 冷存 180d） |
| `circuit_breaker_states` | LLM Hub | 熔断器状态 | 小（<20 条） |
| `llm_budgets` | LLM Hub | 预算配额 | 小（<50 条） |
| `cron_jobs` | CronHub | 定时任务定义 | 小（<30 条） |
| `job_executions` | CronHub | 执行历史 | 大（热库 30d + 冷存 180d） |
| `dead_letter_jobs` | CronHub | 死信队列 | 中 |
| `tasks` | TaskHub | 任务主表 | 大（按内容生产频率增长） |
| `task_node_executions` | TaskHub + Workflow Engine | 节点执行记录 | 大 |
| `workflow_templates` | Workflow Engine | 工作流模板 | 小（<20 条） |
| `workflow_executions` | Workflow Engine | 工作流执行实例 | 大 |
| `prompt_templates` | Prompt Registry | Prompt 模板 | 中（每 Agent 5–20 个） |
| `prompt_variables` | Prompt Registry | 全局变量白名单 | 小（<50 条） |
| `prompt_performances` | Prompt Registry | Prompt 效果统计 | 中 |
| `review_records` | Human-in-the-Loop | 审核记录 | 中 |

---

## 十二、接口设计汇总

### 12.1 新增 API 路由总表

| 模块 | 路由前缀 | 接口数 | 关键接口 |
|------|---------|--------|---------|
| **AgentHub** | `/agent-hub` | 14 | 注册/配置版本化/激活/回滚/权限/审批 |
| **AgentWatch** | `/agent-watch` | 10 | 心跳/状态/链路/告警/规则配置 |
| **AgentMetrics** | `/agent-metrics` | 10 | 统计看板/质量评分/成本归因/干预记录 |
| **LLM Hub** | `/llm-hub` | 18 | 模型注册/三层配置/路由/成本/熔断 |
| **CronHub** | `/cron-hub` | 14 | Job 管理/执行历史/死信/调度器健康 |
| **TaskHub** | `/task-hub` | 10 | 任务创建/状态机/批量/人工审核接口 |
| **Workflow Engine** | `/workflow-engine` | 10 | 模板管理/节点管理/执行/上下文调试 |
| **Prompt Registry** | `/prompt-registry` | 10 | 模板管理/变量管理/效果追踪/渲染调试 |
| **Human-in-the-Loop** | `/human-in-loop` | 7 | 待审列表/详情/通过/驳回/打回/批量/统计 |

**新增接口总计：约 103 个**

---

## 十三、测试策略

### 13.1 新增模块测试矩阵

| 模块 | 测试文件 | 测试数 | 关键场景 |
|------|----------|--------|---------|
| AgentHub | `test_agent_hub.py` | 6 | 注册/配置版本化/激活/回滚/权限/依赖探测 |
| AgentWatch | `test_agent_watch.py` | 6 | 心跳上报/状态聚合/链路追踪/循环检测/超时检测/告警分级 |
| AgentMetrics | `test_agent_metrics.py` | 5 | 任务完成率计算/成本归因/质量评分/人机干预记录/时序聚合 |
| LLM Hub | `test_llm_hub.py` | 6 | 模型注册/三层配置合并/路由决策/预算检查/熔断/合规预检 |
| CronHub | `test_cron_hub.py` | 6 | Job 注册/Cron 解析/分布式锁/执行器/重试/DLQ |
| TaskHub | `test_task_hub.py` | 5 | 创建/状态机转换/取消/重试/批量任务 |
| Workflow Engine | `test_workflow_engine.py` | 6 | 模板创建/串行执行/上下文传递/失败策略/版本回滚/节点跳过 |
| Prompt Registry | `test_prompt_registry.py` | 5 | 模板注册/变量白名单校验/版本激活/渲染/Dry Run |
| Human-in-the-Loop | `test_human_in_loop.py` | 4 | 审核通过/驳回/打回修改/双人复核 |
| **集成测试** | `test_integration_v26.py` | 6 | Task→Workflow→Agent→Human→Publisher 全链路 / CronHub 触发 / AgentHub 状态检查 / LLM Hub 路由 / 上下文恢复 / Prompt 版本回滚 |

**新增测试总计：约 55 个**

### 13.2 回归策略

- 基线：154 + V2.3–V2.5 新增测试全绿
- 每新增模块，测试数按上表执行，全量回归
- LLM Hub 的 `LLMRouteDecision` 审计日志须保留 >=180 天
- 熔断器状态变化须同步到 AgentWatch 告警表
- 成本计算须与 AgentMetrics 交叉验证，误差 <=3%

---

## 十四、开源集成清单与边界

### 14.1 本次新增开源项目（10 个）

| 项目 | 本地路径 | Stars | 许可证 | 支撑模块 | 自研边界 |
|------|---------|-------|--------|---------|---------|
| **OpenTelemetry Python** | `vendor/observability-tools/opentelemetry-python` | 2k+ | Apache-2.0 | AgentWatch Trace/Metrics 采集 | trace 关联 content_id 业务语义层 |
| **OpenTelemetry Python Contrib** | `vendor/observability-tools/opentelemetry-python-contrib` | 2k+ | Apache-2.0 | 自动探针（Celery/Redis/FastAPI）| — |
| **Prometheus Python Client** | `vendor/observability-tools/prometheus-client-python` | 4.3k+ | Apache-2.0 | AgentMetrics 指标暴露 | 业务指标定义与标签设计 |
| **Jaeger** | `vendor/observability-tools/jaeger` | 22.7k+ | Apache-2.0 | AgentWatch Trace 后端 | — |
| **pybreaker** | `vendor/resilience-libraries/pybreaker` | 655+ | BSD-2/3 | LLM Hub 熔断器 | 事件监听器对接 AgentWatch |
| **stamina** | `vendor/resilience-libraries/stamina` | 1.5k+ | MIT | CronHub/Workflow/LLM 重试 | 条件重试谓词、告警联动 |
| **croniter** | `vendor/workflow-libraries/croniter` | 900+ | MIT | CronHub Cron 解析 | 时区处理、扩展语法封装 |
| **transitions** | `vendor/workflow-libraries/transitions` | 6.5k+ | MIT | TaskHub/Workflow Engine 状态机 | 状态迁移守卫、回调执行 Celery Task |
| **Langfuse** | `vendor/prompt-management/langfuse` | 27k+ | MIT | Prompt Registry 版本化 + 效果追踪 | 与 AgentHub 配置回滚联动 |
| **DeepEval** | `vendor/evaluation-frameworks/deepeval` | 14k+ | Apache-2.0 | AgentMetrics 质量评分 | Rubric 定义、评分维度、权重配置 |

### 14.2 与现有开源项目的关系

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        EcoDreamOmni 开源组件全景（V2.6）                     │
├─────────────────────────────────────────────────────────────────────────────┤
│  AI 框架层                                                                   │
│    hermes-agent（Agent 底座）+ LiteLLM（LLM 路由）+ Langfuse（Prompt 追踪）   │
├─────────────────────────────────────────────────────────────────────────────┤
│  可观测性层（新增）                                                           │
│    OpenTelemetry Python（采集）→ Jaeger（Trace 存储）+ Prometheus（指标 TSDB）│
│    Grafana（可视化，规划）+ Prometheus Python Client（Python 指标暴露）        │
├─────────────────────────────────────────────────────────────────────────────┤
│  韧性治理层（新增）                                                           │
│    pybreaker（熔断器）+ stamina（重试）→ 与 LiteLLM Router 形成防御纵深        │
├─────────────────────────────────────────────────────────────────────────────┤
│  工作流与调度层（新增）                                                        │
│    croniter（Cron 解析）+ transitions（状态机）+ Celery（执行引擎）            │
├─────────────────────────────────────────────────────────────────────────────┤
│  评估层（新增）                                                               │
│    DeepEval（LLM-as-Judge）→ 与 AgentMetrics 质量评分闭环                      │
├─────────────────────────────────────────────────────────────────────────────┤
│  后端框架层                                                                   │
│    FastAPI + SQLAlchemy + Alembic + Celery + Redis + PostgreSQL              │
├─────────────────────────────────────────────────────────────────────────────┤
│  前端层                                                                      │
│    React 19 + Vite 6 + TailwindCSS v4 + shadcn/ui + TanStack + Zustand ...   │
├─────────────────────────────────────────────────────────────────────────────┤
│  浏览器自动化层                                                               │
│    Playwright + rebrowser-patches + puppeteer-extra + owl-light              │
├─────────────────────────────────────────────────────────────────────────────┤
│  ML 层                                                                       │
│    scikit-learn + XGBoost + SHAP + statsmodels + jieba                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 14.3 许可证明细

| 项目 | 许可证 | 商用友好性 | 备注 |
|------|--------|-----------|------|
| OpenTelemetry Python | Apache-2.0 | ✅ 完全自由 | CNCF 项目 |
| Prometheus Python Client | Apache-2.0 | ✅ 完全自由 | CNCF 项目 |
| Jaeger | Apache-2.0 | ✅ 完全自由 | CNCF Graduated |
| pybreaker | BSD-2/3-Clause | ✅ 完全自由 | — |
| stamina | MIT | ✅ 完全自由 | — |
| croniter | MIT | ✅ 完全自由 | Pallets Eco |
| transitions | MIT | ✅ 完全自由 | — |
| Langfuse | MIT | ✅ 完全自由 | 可自托管；ee/ 目录除外 |
| DeepEval | Apache-2.0 | ✅ 完全自由 | 可 100% 离线运行 |

**所有新增项目均为 OSI 认证开源许可证，无商用限制。**

---

> **文档版本**：v2.0  
> **对齐基线**：PRD V3.1（V2.7.1基础功能对齐版）+ 开发计划 v2.7.1-V3.1对齐版  
> **更新日期**：2026-05-15  
> **下次评审**：W14 Sprint 计划会前（开发计划 §3.0）
