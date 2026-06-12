# 02-后端API路由层

> **版本**: v4.0
> **生成日期**: 2026-06-03
> **关联文档**: `docs/契约与数据/01-API接口契约.md`

---

## 一、API 路由总览

后端 `src/api/` 目录共 59 个路由文件，注册路由 200+ 条。

### 按模块分组

| 模块 | 路由文件 | 端点数 | v4.0 变更 |
|------|---------|--------|----------|
| **认证** | `auth.py` | 4 | — |
| **任务中心** | `task_hub.py` | 18 | — |
| **Pipeline** | `pipeline.py`, `workflow_engine.py` | 12 | **P4 DAG + Checkpoint** |
| **审核发布** | `human_in_loop.py`, `review_publish.py`, `publisher.py` | 16 | — |
| **合规** | `compliance.py` | 6 | — |
| **LLM Hub** | `llm_hub.py` | 8 | **P5 路由 + modality_support** |
| **实验室** | `playground.py` | 11 | **P6 新增**（含关键词 CRUD + 变更日志） |
| **MCP Gateway** | `mcp_gateway.py` | 3 | **P5 预留（501）** |
| **Event Bus** | — | — | P5 核心模块，无 HTTP API |
| **Checkpoint** | — | — | P4 核心模块，Service 层调用 |
| **Agent 治理** | `agent_orchestra.py`, `agent_cockpit.py`, `agent_metrics.py`, `agent_watch.py` | 16 | — |
| **Skill** | `skill_hub.py`, `skill_smith.py` | 8 | — |
| **数据** | `data_analyst.py`, `dashboard.py`, `engagement_tracking.py` | 10 | — |
| **内容** | `content_series.py`, `image_forge.py`, `persona_story.py` | 12 | — |
| **系统** | `settings.py`, `proxy.py`, `cron_hub.py`, `vetdrug.py`, `timeline.py` | 20 | — |
| **其他** | `asset_pool.py`, `brand_knowledge.py`, `comment_hub.py`, `platform_rules.py`, `platform_schema.py`, `review_publish.py`, `alert_stream.py`, `websocket.py`, `ip_reputation.py`, `pool_predictor.py`, `pool_predictor_explore.py`, `api_platform.py`, `browser_pool.py`, `harness.py`, `meta_orchestrator.py`, `prompt_registry.py`, `workflows.py`, `prohibited_words.py` | 60+ | — |

---

## 二、v4.0 新增/变更端点

### 2.1 LLM Hub 路由（P5-1）

| Method | 路径 | 说明 | 状态 |
|--------|------|------|------|
| POST | `/llm-hub/models` | 注册模型 | ✅ |
| PATCH | `/llm-hub/models/{id}` | 更新模型（含 modality_support） | ✅ |
| GET | `/llm-hub/models` | 列表（含 modality_support） | ✅ |
| **POST** | **`/llm-hub/route`** | **按模态路由决策** | **P5-1 新增** |

### 2.2 MCP Gateway（P5-3 预留）

| Method | 路径 | 状态码 | 说明 |
|--------|------|--------|------|
| POST | `/mcp-gateway/servers` | 501 | 注册 MCP Server |
| GET | `/mcp-gateway/servers/{id}/tools` | 501 | Tool Discovery |
| POST | `/mcp-gateway/tools/call` | 501 | Tool 调用 |

### 2.3 实验室（P6-3 新增）

| Method | 路径 | 说明 | 状态 |
|--------|------|------|------|
| POST | `/lab/parse` | 爆款结构解析 | ✅ 骨架 |
| GET | `/lab/templates` | 模板列表 | ✅ 骨架 |
| POST | `/lab/generate` | 一键生成 | ✅ 骨架 |

### 2.4 Pipeline / Workflow Engine（P4）

| Method | 路径 | 变更 |
|--------|------|------|
| POST | `/workflow-engine/templates` | 新增 `depends_on` / `skill_id` |
| POST | `/pipeline/tasks` | 内部调用 DAG 编译 |
| GET | `/workflow-engine/executions/{id}` | 返回 `completed_nodes` / `resumed_count` |
| POST | `/workflow-engine/executions/{id}/resume` | **P4 新增：断点续跑** |

---

## 三、API → Service 映射

| API 层 | Service 层 | 说明 |
|--------|-----------|------|
| `api/llm_hub.py` | `services/llm_hub.py` | LLM 模型管理 + 路由 |
| `api/workflow_engine.py` | `services/workflow_engine.py` | Pipeline 执行引擎 |
| `api/checkpoint.py` | `core/checkpoint.py` | Checkpoint 存储（无独立 API） |
| `api/lab.py` | `services/lab_service.py`（Phase 2） | 爆款复刻 |
| `api/mcp_gateway.py` | `services/mcp_gateway.py`（Phase 2） | MCP 网关 |
| `api/event_bus.py` | `core/event_bus.py` | 事件总线（无 HTTP API） |

---

*详细请求/响应 Schema 参见 `docs/契约与数据/01-API接口契约.md`*
