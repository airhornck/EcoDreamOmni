# 03-后端Service层

> **版本**: v4.0
> **生成日期**: 2026-06-03
> **关联文档**: `01-数据库模型层.md`, `02-后端API路由层.md`

---

## 一、Service 分类总览

`src/services/` 共 75 个文件，按职责分为 6 大类：

```
├── 认证与权限 (3)
│   ├── auth_service.py
│   ├── auth_function.py
│   └── rbac.py
├── Agent 治理 (6)
│   ├── agent_hub.py
│   ├── agent_orchestra.py
│   ├── agent_cockpit.py
│   ├── agent_metrics.py
│   ├── agent_watch.py
│   └── harness.py
├── Skill 与 Function (8)
│   ├── skill_hub.py
│   ├── skill_smith.py
│   ├── content_insight.py
│   ├── api_platform.py
│   ├── browser_pool.py
│   ├── brand_knowledge_function.py
│   ├── asset_pool_function.py
│   └── celery_tasks_function.py
├── Pipeline 与编排 (4)
│   ├── workflow_engine.py      ← P4 核心改造
│   ├── pipeline.py
│   ├── task_hub.py
│   └── celery_tasks.py
├── 内容生产 (8)
│   ├── content_series.py
│   ├── image_forge.py
│   ├── persona_story.py
│   ├── publisher.py
│   ├── human_in_loop.py
│   ├── review_publish.py
│   ├── comment_hub.py
│   └── data_analyst.py         ← P3 降级
├── 系统与工具 (20+)
│   ├── audit_logger.py
│   ├── alert_stream.py
│   ├── llm_hub.py              ← P5-1 改造
│   ├── checkpoint.py           ← P4 新增（core/）
│   ├── event_bus.py            ← P5-2 新增（core/）
│   ├── settings.py
│   ├── proxy.py
│   ├── cron_hub.py
│   ├── vetdrug.py
│   ├── timeline.py
│   ├── platform_rule_function.py
│   └── ...
```

---

## 二、v4.0 核心 Service 变更

### 2.1 workflow_engine.py（P4）

| 函数/类 | 变更 | 说明 |
|---------|------|------|
| `CompiledDAG` | **新增** | DAG 编译结果 dataclass |
| `compile_dag()` | **新增** | Kahn 拓扑排序 + 环检测 |
| `NodeType.SKILL` | **新增** | Skill 节点类型枚举 |
| `WorkflowNode` | 扩展 | 新增 `depends_on`, `skill_id` |
| `WorkflowExecution` | 扩展 | 新增 `completed_nodes`, `failed_nodes`, `resumed_count` |
| `execute_next_node()` | 重构 | 内部调用 DAG 拓扑调度 |
| `resume_execution()` | **新增** | 从 Checkpoint 恢复状态 |
| `pause_execution()` | **新增** | 暂停执行并保存 Checkpoint |
| `_run_skill_node()` | **新增** | keyword_inject / brand_knowledge_inject 路由 |

### 2.2 llm_hub.py（P5-1）

| 函数/类 | 变更 | 说明 |
|---------|------|------|
| `LLMRouter.route()` | **新增** | 按模态自动路由决策 |
| `get_provider_region()` | **新增** | 供应商区域判断（国内/海外） |
| `modality_support` | 打通 | register/update/list 全链路支持 |
| `_model_to_dict()` | 扩展 | 序列化 modality_support |

### 2.3 event_bus.py（P5-2）

| 函数/类 | 说明 |
|---------|------|
| `EventBus` | Redis Streams + 内存 fallback |
| `publish()` | XADD / 内存追加 |
| `consume()` | XREADGROUP / 内存 FIFO |
| `ack()` | XACK / 内存移除 |
| `create_consumer_group()` | XGROUP CREATE MKSTREAM |

### 2.4 checkpoint.py（P4）

| 函数/类 | 说明 |
|---------|------|
| `CheckpointManager` | 分层存储管理器 |
| `save_sync()` / `load_sync()` | 同步接口 |
| `save()` / `load()` | 异步接口 |
| `_offload()` | 大 Payload (>1MB) 本地文件存储 |

### 2.5 DataAnalyst 降级（P3）

| 原设计 | 新设计 | 文件 |
|--------|--------|------|
| `DataAnalyst` Agent | `engagement_collect` Function | `services/data_analyst.py` |
| `DataAnalyst` Agent | `battle_report_generate` Skill | `services/data_analyst.py` |

---

## 三、Service 调用关系（关键路径）

```
ContentProduction Flow:
  task_hub.create_task()
    └── workflow_engine.start_execution()
          ├── compile_dag()                    # P4
          ├── execute_next_node()
          │     ├── _run_agent_node()          # Agent 调用
          │     ├── _run_skill_node()          # P4 Skill 路由
          │     └── CheckpointManager.save()   # P4 双写
          └── resume_execution()               # P4 断点续跑
                └── CheckpointManager.load_all_sync()

LLM Routing Flow:
  llm_hub_api.route()
    └── LLMRouter.route()
          ├── list_models()       # 筛选 modality
          ├── get_provider_region() # 国内/海外判断
          └── log_usage()         # 记录路由决策
```

---

## 四、Function 层规范（v4.0 架构红线）

> **Agent 禁 DB** — 所有 Agent/Skill 必须通过 Function API 访问数据库。

| Function 文件 | 对应 Service | 说明 |
|--------------|-------------|------|
| `auth_function.py` | `auth_service.py` | 用户认证 |
| `asset_pool_function.py` | `asset_pool.py` | 素材库 CRUD |
| `brand_knowledge_function.py` | `brand_knowledge.py` | 品牌知识库 |
| `celery_tasks_function.py` | `celery_tasks.py` | 定时任务 |
| `platform_rule_function.py` | `platform_rules.py` | 平台规则 |

---

*完整 Service 列表参见 `apps/backend/src/services/` 目录*
