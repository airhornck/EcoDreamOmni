# Sprint 2 完成报告 — WebSocket 实时推送 / Celery 异步生成 / Alembic 迁移

**日期**: 2026-06-05  
**实施范围**: Redis pub/sub 跨进程事件桥接、Celery 内容生成任务、Alembic 迁移修复

---

## 一、实施摘要

| 任务 | 状态 | 关键改动 |
|------|------|----------|
| **Alembic 迁移修复** | ✅ 完成 | `env.py` 添加 `copilot_orm` 导入；`stamp head` 标记当前 DB 状态 |
| **Celery 异步内容生成** | ✅ 完成 | 新增 `regenerate_content` Celery 任务；API 端点真正入队 |
| **WebSocket 实时推送** | ✅ 完成 | Redis pub/sub 跨进程桥接；`content.generation.*` 事件流验证通过 |

---

## 二、Alembic 迁移修复

### 问题
- `alembic_version` 表不存在，所有表通过 `main.py` lifespan 的 `run_sync(ORM.__table__.create)` 创建
- `env.py` 缺少 `copilot_orm` 模型导入，导致 `autogenerate` 无法检测新表

### 修复
**文件**: `alembic/env.py`
```python
from src.models.copilot_orm import (
    CopilotContextSessionORM, AICoverGenerationJobORM, CopilotActionLogORM
)  # noqa: F401
```

**操作**:
```bash
cd apps/backend
python -m alembic stamp head
# → 20260604addc (head)
```

### 结果
- `alembic current` 输出 `20260604addc (head)`
- 数据库中 `copilot_context_sessions`, `ai_cover_generation_jobs`, `copilot_action_logs` 表已存在
- 未来可通过 `alembic revision --autogenerate` 正确检测 schema 变更

---

## 三、Celery 异步内容生成

### 新增任务: `regenerate_content`
**文件**: `src/services/celery_tasks.py`

**任务流程**:
1. 推送 `content.generation.started` 事件 (progress=0)
2. 模拟生成过程，每 1-2 秒推送 `content.generation.progress` (30%, 60%, 90%)
3. 根据 `style_option`/`length_option`/`tone_option` 生成模拟内容
4. 推送 `content.generation.completed` 事件 (progress=100, 包含生成的标题/正文/合规分)
5. 出错时推送 `content.generation.failed` 事件

**参数**:
```python
regenerate_content(
    job_id: str,
    task_id: str,
    user_id: str,
    style_option: str = "casual",      # casual | professional | humorous
    length_option: str = "medium",     # short | medium | long
    tone_option: str = "friendly",     # friendly | serious | playful
    prompt_variables: dict | None = None,
)
```

### API 端点修改
**文件**: `src/api/copilot.py` — `POST /ai/copilot/regenerate-content`

**变更**:
- 从 stub 实现改为真正入队 Celery 任务
- 验证 task 存在性和用户权限
- 调用 `celery_app.send_task("src.services.celery_tasks.regenerate_content", ...)`
- 返回 `ACCEPTED` + `copilot_followup` (进度提示 Card)

---

## 四、WebSocket 实时推送 (Redis pub/sub 桥接)

### 核心问题
Celery Worker 和 FastAPI/Uvicorn 运行在不同进程中，`COPILOT_WS_CONNECTIONS` (内存字典) 无法跨进程共享。Celery 任务推送的事件被静默丢弃。

### 解决方案: Redis pub/sub 跨进程桥接

#### 4.1 Celery Worker 侧 — 发布事件
**文件**: `src/api/copilot.py` — `push_copilot_event()`

```python
async def push_copilot_event(user_id: str, event: str, payload: dict) -> None:
    ws = COPILOT_WS_CONNECTIONS.get(user_id)
    if ws:
        await ws.send_json(message)  # 同进程直接推送
        return
    
    # 跨进程：发布到 Redis pub/sub channel
    redis_client = aioredis.from_url("redis://localhost:6379/0")
    channel = f"copilot:events:{user_id}"
    await redis_client.publish(channel, json.dumps(message))
```

#### 4.2 Uvicorn 侧 — 订阅并转发
**文件**: `src/api/websocket.py` — `copilot_websocket()`

WebSocket 连接时并行启动两个协程：
- `_handle_client_messages()`: 处理客户端发来的消息 (ping, context.update)
- `_redis_listener()`: 订阅 Redis `copilot:events:{user_id}` channel，收到消息后通过 WebSocket 推送给客户端

```python
await asyncio.gather(
    _handle_client_messages(websocket, user_id),
    _redis_listener(websocket, user_id),
    return_exceptions=True,
)
```

### 事件流格式
```json
{
  "event": "content.generation.progress",
  "payload": {
    "job_id": "job_reg_xxx",
    "task_id": "task-uuid",
    "status": "generating",
    "progress": 60,
    "step": "drafting_content"
  },
  "timestamp": "2026-06-05T02:02:10+00:00",
  "trace_id": "ws_abc123"
}
```

### 支持的事件类型
| 事件 | 触发时机 | payload 关键字段 |
|------|---------|-----------------|
| `content.generation.started` | 生成开始 | `progress: 0`, `step: analyzing_requirements` |
| `content.generation.progress` | 进度更新 | `progress: 30/60/90`, `step: ...` |
| `content.generation.completed` | 生成完成 | `progress: 100`, `generated_content`, `compliance_score` |
| `content.generation.failed` | 生成失败 | `error` |
| `cover.generation.progress` | 封面生成中 | `progress`, `step` |
| `cover.generation.completed` | 封面生成完成 | `results` |

---

## 五、端到端验证结果

### 测试场景: WebSocket 实时接收内容生成事件

```
Client ──WebSocket──→ /ws/copilot (Uvicorn)
                         │
                         │ 订阅 Redis: copilot:events:{user_id}
                         │ ◄───────────────┐
Client ──HTTP POST──→ /ai/copilot/regenerate-content
                         │
                         └── Celery Task Enqueued ──→ Celery Worker
                                                          │
                                                          ├── publish Redis
                                                          │   "content.generation.started"
                                                          ├── publish Redis
                                                          │   "content.generation.progress" ×3
                                                          └── publish Redis
                                                              "content.generation.completed"
```

### 实际测试结果
```
Event: content.generation.started   progress=0   step=analyzing_requirements
Event: content.generation.progress  progress=30  step=generating_outline
Event: content.generation.progress  progress=60  step=drafting_content
Event: content.generation.progress  progress=90  step=polishing_and_compliance_check
Event: content.generation.completed progress=100

Total events: 5
SUCCESS: All expected events received!
```

---

## 六、质量门

### 前端
```bash
cd apps/frontend
npx tsc --noEmit --skipLibCheck      # 0 errors ✅
npx eslint src --ext .ts,.tsx         # 0 errors, 7 warnings ✅
```

### 后端
```bash
curl http://localhost:8001/health    # {"status":"ok"} ✅
python -m alembic current             # 20260604addc (head) ✅
python -m celery -A src.celery_app inspect registered
# → regenerate_content, generate_cover 均已注册 ✅
```

### API 端点
| 端点 | 状态 | 说明 |
|------|------|------|
| GET /task-hub/tasks | 200 ✅ | copilot_summary |
| POST /task-hub/tasks | 201 ✅ | copilot_followup |
| GET /task-hub/tasks/{id} | 200 ✅ | copilot_context |
| POST /ai/copilot/regenerate-content | 200 ✅ | Celery 入队 + WebSocket 推送 |
| POST /ai/copilot/save-and-submit | 200 ✅ | 原子操作 + 状态流转 |
| POST /ai/copilot/context | 200 ✅ | 会话持久化 |
| WS /ws/copilot | 101 ✅ | Redis pub/sub 桥接 |

---

## 七、文件变更清单

| 文件 | 变更类型 | 说明 |
|------|---------|------|
| `alembic/env.py` | 修改 | 添加 `copilot_orm` 模型导入 |
| `src/services/celery_tasks.py` | 新增 | `regenerate_content` Celery 任务 |
| `src/api/copilot.py` | 修改 | `push_copilot_event` Redis pub/sub 桥接；`regenerate-content` 真正入队 Celery |
| `src/api/websocket.py` | 修改 | `_redis_listener` 协程；`asyncio.gather` 并行处理客户端消息和 Redis 订阅 |

---

## 八、已知限制

| 项目 | 说明 | 计划 |
|------|------|------|
| Celery Windows pool | Windows 下需使用 `--pool=solo` 避免 billiard 权限错误 | 生产环境使用 Linux + prefork |
| 内容生成 mock | `regenerate_content` 当前生成模拟内容，未接入真实 LLM | Sprint 3 接入 LLM Hub |
| Redis pub/sub 频道清理 | 未实现频道自动过期清理 | 低优先级 |
| WebSocket 多设备 | 同一用户多设备连接时，仅最后一个设备收到事件 | 未来支持多设备推送 |

---

## 九、结论

✅ **Sprint 2 三项任务全部完成：**

1. **Alembic 迁移** — `env.py` 模型导入修复，数据库状态正确标记为 head
2. **Celery 异步生成** — `regenerate_content` 任务实现并注册，API 真正入队
3. **WebSocket 实时推送** — Redis pub/sub 跨进程桥接解决多进程隔离问题，`content.generation.*` 事件流完整验证通过

**系统已具备**：Copilot 驱动的内容生成 → Celery 异步执行 → Redis 事件桥接 → WebSocket 实时推送到前端的完整闭环。
