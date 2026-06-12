# Phase 5 变更记录 — 接入层改造（Event Bus + MCP Gateway + LLM Hub 多模态路由）

**日期**: 2026-06-03
**Phase**: Phase 5（接入层改造）
**任务**: P5-1 ~ P5-3
**状态**: 已完成

---

## 变更摘要

### P5-1: LLM Hub 多模态路由

- `src/services/llm_hub.py`:
  - 新增 `route()` 函数：按 `modality` 自动选择最优模型
  - 路由策略：国内首选 → 海外兜底（`cross_border_risk=True`）
  - 路由决策自动写入 `LLMUsageLog`（status=`ROUTED`，provider_region=`overseas`）
  - `register_model` / `update_model` / `list_models` 全面支持 `modality_support` 字段
  - `_model_to_dict()` 序列化 `modality_support`
- `src/api/llm_hub.py`:
  - 新增 `POST /llm-hub/route` 端点
  - `LLMModelCreate` / `LLMModelUpdate` / `LLMModelResponse` Schema 新增 `modality_support`
- `src/services/llm_hub.py` — `get_provider_region()`:
  - `deepseek` / `zhipu` / `qwen` / `baichuan` / `moonshot` → `domestic`
  - `openai` / `anthropic` / `gemini` / `mistral` → `overseas`

### P5-2: Event Bus（Redis Streams + 内存 fallback）

- **新建** `src/core/event_bus.py`:
  - `EventBus` 核心类，`__init__(redis_client=None)`
  - `publish(stream, message)` → Redis `XADD` 或内存追加（带 trace_id / timestamp 自动注入）
  - `consume(stream, group, consumer, count, block_ms)` → Redis `XREADGROUP` 或内存 FIFO
  - `ack(stream, group, message_id)` → Redis `XACK` 或内存移除
  - `create_consumer_group(stream, group)` → Redis `XGROUP CREATE MKSTREAM` 或内存初始化
  - **关键修复**：内存 fallback 模式下 `consume()` 使用 `copy.deepcopy()` 隔离不同消费者组的消息引用，避免组 A ACK 后影响组 B
  - 预定义频道常量：`AGENT_EVENTS` / `PIPELINE_EVENTS` / `SYSTEM_EVENTS` / `WORKBENCH_EVENTS`

### P5-3: MCP Gateway 预留接口

- **新建** `src/api/mcp_gateway.py`:
  - `MCPRegisterServerRequest` / `MCPToolCallRequest` / `MCPResponse` Pydantic Schema
  - `POST /mcp-gateway/servers` → 501
  - `GET /mcp-gateway/servers/{server_id}/tools` → 501
  - `POST /mcp-gateway/tools/call` → 501
  - 统一返回 `MCPResponse(status="not_implemented", error="MCP Gateway 将在 Phase 2 实现")`
- `src/main.py`: 已注册 `mcp_gateway.router`

---

## 测试覆盖

| 测试文件 | 测试数 | 状态 |
|----------|--------|------|
| `tests/test_event_bus.py` | 9 | ✅ 全部通过（含 1000 条消息压力测试） |
| `tests/test_mcp_gateway.py` | 5 | ✅ 全部通过 |
| `tests/test_llm_*.py` | 14 | ✅ 全部通过（含路由 5 模态 × 2 场景 + 模型注册/成本/日志/配置） |

**总计**: 新增/回归测试 28 个，全部通过。

**已知限制**:
- `test_llm_hub.py` 在 Windows + asyncpg + pytest-asyncio 并发运行时偶发 `Event loop is closed`；使用 `pytest -n1` 或单独运行该模块可 100% 通过。

---

## 质量门禁

| 门禁项 | 结果 |
|--------|------|
| pytest 新代码测试通过 | ✅ 28/28 |
| pytest 现有代码回归 | ✅ 43/43 workflow 测试通过（Phase 4 基准） |
| ruff 0 errors（新代码） | ✅ 通过 |
| mypy 0 errors（新代码） | ✅ 通过（现有技术债务 15 处无关） |
| Alembic 迁移 | ✅ 无需新增迁移（P5 无 schema 变更） |

---

## 关联文档更新

- `docs/v4.0_开发Checklist.md` — Phase 5 逐项打勾
- `docs/契约与数据/01-API接口契约.md` — 新增 §五 LLM Hub 路由接口、§六 MCP Gateway 预留接口
- 本文档 — 新增

---

## 已知限制

- MCP Gateway 当前为 501 骨架，Phase 2 正式实现 SSE 连接管理、Tool Discovery、Tool Call
- Redis 容器未运行时 Event Bus 自动 fallback 到内存模式，生产环境需确保 Redis 可用
- LLM 路由测试 Windows 并发偶发事件循环冲突（已标注缓解方案）
