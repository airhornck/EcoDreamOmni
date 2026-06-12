# 问题分析报告：Task-Hub 任务在 Review-Publish-Center 不可见

> **问题现象**：在 `http://localhost:5173/task-hub` 的"任务列表"中可以看到任务，但在 `http://localhost:5173/review-publish-center` 中看不到这些任务产出的内容。
>
> **报告日期**：2026-05-25
> **分析方式**：组织 4 个专家组（前端页面/状态层、后端 API 层、数据流链路层、数据库模型层）并行代码审查

---

## 1. 问题摘要

经专家组联合分析，该问题**不是单一 bug，而是由前端大小写不匹配、数据流链路断裂、后端过滤条件遗漏、双轨审批语义冲突等多重因素叠加导致**。

| 严重程度 | 问题 | 位置 | 影响 |
|---------|------|------|------|
| 🔴 Critical | 前端 pending 标签页状态字符串大小写不匹配 | `ReviewPublishCenterPage.tsx:75` | **"审核中"标签页永远为空**，即使后端有 `human_wait` 状态任务 |
| 🔴 Critical | TaskHub 创建的任务无法进入工作流 | `TaskHubPage.tsx:356` + `taskHubStore.ts` | **任务永远停留在 `configuring`**，无法到达 `HUMAN_WAIT` |
| 🔴 Critical | 双轨审批语义冲突：`submit_human_decision` 与 `human_in_loop.approve_task` 行为不一致 | `task_hub.py:549` / `human_in_loop.py` | 审批后任务状态错误地变为 `running`，**永久从 review-publish-center 消失** |
| 🔴 High | review-publish-center 过滤条件遗漏 `approved_waiting_publish` | `review_publish.py:112-113` | **已审核通过待发布的任务被过滤掉** |
| 🔴 High | `task_hub.approve()` 语义错误 | `task_hub.py:462-463` | 方法名是 approve，实际行为是转为 `running` |
| 🟡 Medium | `prompt_variables` 缺少 `content_preview` 和 `draft_id` | `workflow_engine.py` / `task_hub.py` | review-publish-center **内容预览为空**，confirm-publish **报 422** |
| 🟡 Medium | ContentDraft 和 PublishTask 是内存存储 | `content_draft.py` / `publish_task.py` | **重启后数据全部丢失** |
| 🟡 Medium | 前端审核通过提示语状态判断大小写不匹配 | `ReviewPublishCenterPage.tsx:140` | 审核通过后不显示"请前往已通过标签确认发布"引导 |
| 🟡 Low | 后端测试拼写错误 | `test_review_publish_api.py:158` | `"APROVED_WAITING_PUBLISH"` 少了 P |
| 🟡 Low | URL 参数 `task_id` 传递后未被消费 | `ReviewPublishCenterPage.tsx` | TaskHubPage 导航带的参数被完全忽略 |

---

## 2. 专家组分工与审查范围

| 专家组 | 职责 | 审查文件 |
|--------|------|---------|
| 前端页面/状态层 | 审查 ReviewPublishCenterPage、reviewPublishStore 的交互与数据解析 | `ReviewPublishCenterPage.tsx`, `reviewPublishStore.ts`, `reviewPublishStore.test.ts` |
| 后端 API 层 | 审查 review_publish、human_in_loop、task_hub API 路由与状态机 | `api/review_publish.py`, `api/human_in_loop.py`, `api/task_hub.py`, 测试文件 |
| 数据流链路层 | 追踪从 task-hub 创建到 review-publish-center 展示的完整数据流 | `App.tsx`, `TaskHubPage.tsx`, `main.py`, `task_hub.py`, `content_forge.py`, `workflow_engine.py` |
| 数据库模型层 | 审查 TaskORM、ContentDraft、PublishTask 的持久化设计与关联关系 | `models/task_orm.py`, `models/content_draft.py`, `models/publish_task.py`, Alembic 迁移文件 |

---

## 3. 根因分析（Root Cause Analysis）

### 3.1 致命根因 A：前端 pending 标签页状态字符串大小写不匹配

#### 代码证据

**前端**（`apps/frontend/src/pages/ReviewPublishCenterPage.tsx` 第 73-75 行）：
```tsx
const filtered = conclusions.filter((c) => {
  if (activeTab === 'all') return true
  if (activeTab === 'approved') return c.review_decision === 'APPROVE'
  if (activeTab === 'rejected') return c.review_decision === 'REJECT'
  if (activeTab === 'revised') return c.review_decision === 'REVISE'
  if (activeTab === 'pending') return c.status === 'HUMAN_WAIT'  // ← BUG
  return true
})
```

**后端**（`apps/backend/src/api/review_publish.py` 第 123-131 行）：
```python
if status_filter == "pending":
    if t.status != task_hub.TaskStatus.HUMAN_WAIT:
        continue
```

后端返回的 JSON 中 `status` 字段值为 **小写** `"human_wait"`：
```python
# review_publish.py 第 146 行
status=t.status.value,  # TaskStatus.HUMAN_WAIT.value == "human_wait"
```

**结论**：前端检查的是大写 `'HUMAN_WAIT'`，后端返回的是小写 `'human_wait'`，两者永远不相等，**"审核中"标签页永远为空**。

> **旁证**：`TaskHubPage.tsx` 第 896 行已做过兼容处理：
> ```tsx
> (selectedTask.status === 'HUMAN_WAIT' || selectedTask.status === 'human_wait')
> ```
> 说明开发者意识到了大小写不一致，但未在 `ReviewPublishCenterPage` 中修复。

---

### 3.2 致命根因 B：TaskHub 创建的任务无法进入工作流（链路断裂）

#### 代码证据

**前端 TaskHubPage**（`apps/frontend/src/pages/TaskHubPage.tsx` 第 354-362 行）：
```tsx
{task.status === 'draft' && (
  <button onClick={() => configureTask(task.id)} title="启动">
    <Play className="w-4 h-4 text-primary" />
  </button>
)}
```

**前端 taskHubStore**（`apps/frontend/src/stores/taskHubStore.ts` 第 266-278 行）：
```ts
configureTask: async (id) => {
  const res = await fetch(`/api/task-hub/tasks/${id}/configure`, { method: 'POST', ... })
  ...
  await get().fetchTasks()
  return true
}
```

**后端 configure**（`apps/backend/src/services/task_hub.py` 第 438-439 行）：
```python
async def configure(db: AsyncSession, task_id: str) -> Optional[Task]:
    return await transition_task(db, task_id, "configuring")
```

**后端 start_workflow**（`apps/backend/src/api/task_hub.py` 第 234-244 行）：
```python
@router.post("/tasks/{task_id}/start-workflow", response_model=TaskResponse)
async def start_task_workflow(task_id: str, db: AsyncSession = Depends(get_db)):
    t = await task_hub.start_workflow(db, task_id)
    ...
```

**问题**：
1. 用户点击"启动" → 任务状态从 `draft` → `configuring`
2. **没有后续步骤**调用 `start_workflow` 来启动工作流
3. 任务永远停留在 `configuring`，**永远无法到达 `HUMAN_WAIT`**
4. review-publish-center 的入口过滤条件是 `review_decision != null OR status == HUMAN_WAIT`
5. 因此这些任务**被过滤掉，不可见**

#### 对比：唯一能走通的链路

**ContentForge 提交审核**（`apps/backend/src/api/content_forge.py` 第 235-293 行）：
```python
# 1. 创建 Task
# 2. 自动调用 th.start_workflow(db, task.id)
# 3. 工作流执行到 HUMAN_APPROVAL 节点 → transition_task("human_wait")
```

**结论**：当前只有 `ContentForge → 提交审核` 这条路径能完整走通。`TaskHub` 直接创建的任务是一个**死胡同**。

---

### 3.3 致命根因 C：双轨审批语义冲突

#### 代码证据

**路径 A（正确）**：`human_in_loop.approve_task()`
```python
# human_in_loop.py 第 331-363 行
await task_hub.transition_task_with_update(
    db, task_id, "approved_waiting_publish",
    review_decision="APPROVE", reviewed_at=_now(), reviewer=operator
)
```
- 最终状态：`APPROVED_WAITING_PUBLISH`
- 设置 `review_decision="APPROVE"`
- ✅ review-publish-center **可见**

**路径 B（错误）**：`task_hub.submit_human_decision()`
```python
# task_hub.py 第 584-585 行
if decision == HumanDecision.APPROVE.value:
    task = await approve(db, task_id)  # ← 调用 approve()
```

```python
# task_hub.py 第 462-463 行
async def approve(db: AsyncSession, task_id: str) -> Optional[Task]:
    return await transition_task(db, task_id, "running")
```

- 最终状态：`RUNNING`
- **不设置 `review_decision`**
- ❌ review-publish-center **不可见**（不满足入口过滤条件）

**问题**：如果任何代码（前端或其他集成方）误用了 `/tasks/{id}/human-decision` 做 approve，这条任务就从 review-publish-center 的视野中**永久消失**。

---

### 3.4 高优先级根因 D：review-publish-center 过滤条件遗漏 `approved_waiting_publish`

#### 代码证据

**review_publish.py 第 112-113 行**：
```python
for t in all_tasks:
    if not (t.review_decision or t.status == task_hub.TaskStatus.HUMAN_WAIT):
        continue
```

**问题场景**：
- 任务处于 `approved_waiting_publish` 状态
- 但 `review_decision` 为 `None`（例如直接调用 `transition_task` 而非 `human_in_loop.approve_task`）
- 该任务被过滤掉，review-publish-center **不可见**

**正确逻辑**应包含 `approved_waiting_publish`：
```python
if not (t.review_decision or t.status in {
    task_hub.TaskStatus.HUMAN_WAIT,
    task_hub.TaskStatus.APPROVED_WAITING_PUBLISH,
}):
    continue
```

---

### 3.5 高优先级根因 E：`task_hub.approve()` 语义错误

#### 代码证据

```python
# task_hub.py 第 462-463 行
async def approve(db: AsyncSession, task_id: str) -> Optional[Task]:
    return await transition_task(db, task_id, "running")
```

**问题**：
- 方法名叫 `approve`，用户自然期望它将任务标记为"已审核通过"
- 实际行为却是转为 `running`（运行中）
- 这与 v2 架构设计（审核通过后应进入 `approved_waiting_publish` 等待发布确认）相矛盾
- `human_in_loop.approve_task()` 的行为才是正确的

---

### 3.6 其他关联问题

#### 3.6.1 `prompt_variables` 缺少 `content_preview` 和 `draft_id`

- `review_publish.py` 第 135 行：`preview = t.prompt_variables.get("content_preview", "")`
- `review_publish.py` 第 225 行：`draft_id = _get_draft_id(t.prompt_variables)`
- 只有 `content_forge.py` 的 `submit-for-review` 路径会写入这两个字段
- TaskHub 直接创建的任务，`prompt_variables` 中没有这些内容
- **后果**：review-publish-center 内容预览为空；confirm-publish 报 **422** `"Task has no associated draft_id"`

#### 3.6.2 ContentDraft 和 PublishTask 是内存存储

- `content_draft.py`：`_draft_db: Dict[str, ContentDraft] = {}`
- `publish_task.py`：`_task_db: Dict[str, PublishTask] = {}`
- **没有任何 Alembic 迁移文件**
- 服务器重启后数据全部丢失

#### 3.6.3 前端审核通过提示语状态判断大小写不匹配

```tsx
// ReviewPublishCenterPage.tsx 第 140 行
decision === 'approve' && result.status === 'APPROVED_WAITING_PUBLISH'
  ? '审核已通过，请前往「已通过」标签确认发布'
  : '审核已通过'
```
- `result.status` 实际是 `"approved_waiting_publish"`（小写）
- 提示语永远不显示引导信息

#### 3.6.4 测试拼写错误

```python
# test_review_publish_api.py 第 158 行
assert data["status"] == "APROVED_WAITING_PUBLISH" or data["status"] == "approved_waiting_publish"
```
- `"APROVED_WAITING_PUBLISH"` 少了字母 P
- 因后面有 `or`，测试仍能通过

---

## 4. 影响范围评估

| 维度 | 影响 |
|------|------|
| **功能可用性** | review-publish-center 核心功能严重受损："审核中"标签页永远为空；TaskHub 创建的任务无法进入审核流程；确认发布时报 422 |
| **用户体验** | 用户在 task-hub 创建任务后，无法在任何地方找到对应的审核/发布入口；审核通过后看不到发布确认引导 |
| **数据完整性** | ContentDraft 和 PublishTask 为内存存储，重启后数据丢失；Task 与 Draft 之间只有松散的 JSON 字典关联，无数据库外键约束 |
| **业务链路** | 当前只有 `ContentForge → 提交审核` 路径可走通；`TaskHub → 启动` 路径完全断裂，形成死胡同 |
| **测试覆盖** | `test_hitl_rpc_integration.py` 存在 async/await 缺失，完全无法运行；`reviewPublishStore.test.ts` 未覆盖 `fetchConclusions` |

---

## 5. 修复建议（按优先级排序）

### 5.1 立即修复（P0）

**修复 1：前端 pending 标签页大小写匹配**

```tsx
// ReviewPublishCenterPage.tsx 第 75 行
// 修改前
if (activeTab === 'pending') return c.status === 'HUMAN_WAIT'
// 修改后
if (activeTab === 'pending') return c.status === 'human_wait'
```

**修复 2：TaskHub "启动"按钮改为启动工作流**

```tsx
// TaskHubPage.tsx 第 356 行
// 修改前：onClick={() => configureTask(task.id)}
// 修改后：onClick={() => startWorkflow(task.id)}
```

需要在 `taskHubStore.ts` 中新增 `startWorkflow` 方法：
```ts
startWorkflow: async (id) => {
  const res = await fetch(`/api/task-hub/tasks/${id}/start-workflow`, {
    method: 'POST', headers: authHeaders(),
  })
  ...
}
```

**修复 3：统一审批入口，消除双轨冲突**

方案 A（推荐）：删除/重构 `task_hub.submit_human_decision` 的 approve 分支，使其调用 `human_in_loop.approve_task`：
```python
# task_hub.py 第 584-585 行
if decision == HumanDecision.APPROVE.value:
    from src.services import human_in_loop as hil
    return await hil.approve_task(db, task_id, reviewer="system")
```

方案 B：将 `task_hub.approve()` 的语义修正为转向 `approved_waiting_publish`：
```python
async def approve(db: AsyncSession, task_id: str) -> Optional[Task]:
    return await transition_task_with_update(
        db, task_id, "approved_waiting_publish",
        review_decision="APPROVE", reviewed_at=_now()
    )
```

**修复 4：review-publish-center 过滤条件补充 `approved_waiting_publish`**

```python
# review_publish.py 第 112-113 行
if not (t.review_decision or t.status in {
    task_hub.TaskStatus.HUMAN_WAIT,
    task_hub.TaskStatus.APPROVED_WAITING_PUBLISH,
}):
    continue
```

### 5.2 短期修复（P1）

1. **修正前端审核通过提示语**：`'APPROVED_WAITING_PUBLISH'` → `'approved_waiting_publish'`
2. **修正后端测试拼写错误**：`"APROVED_WAITING_PUBLISH"` → `"approved_waiting_publish"`
3. **修正 `test_hitl_rpc_integration.py`**：将 `_create_human_wait_task` 改为 `async def` 并添加 `await`
4. **补充 `reviewPublishStore.test.ts`**：添加 `fetchConclusions` 的测试用例
5. **限制 TaskHubPage "完成"按钮**：不应允许手动将任务标记为 `completed` 来绕过审核流程

### 5.3 中期修复（P2）

1. **Workflow 节点产出回写 `prompt_variables`**：工作流执行到 `HUMAN_WAIT` 时，将当前节点输出自动写入 `prompt_variables["content_preview"]` 和 `"draft_id"`
2. **为 ContentDraft 和 PublishTask 创建数据库表**：添加 Alembic 迁移文件，将内存存储改为 PostgreSQL 持久化
3. **在 TaskORM 中添加 `draft_id` 字段**：作为显式外键（或索引字段），替代松散的 JSON 字典关联
4. **将 `human_in_loop` 的 `_review_db` 持久化**：创建 `review_records` 数据库表

### 5.4 长期优化（P3）

1. **统一 API 响应格式**：明确前后端状态字符串的大小写契约（建议全小写 + 前端统一适配）
2. **消除内存缓存依赖**：当前 `_task_db`、`_draft_db`、`_publish_task_db` 均为进程级内存，多进程/多副本部署下会导致数据不一致
3. **URL 参数消费**：在 `ReviewPublishCenterPage` 中读取 `task_id` query 参数，自动过滤或展开对应任务

---

## 6. 验证步骤

修复后，建议按以下步骤验证：

1. 启动前后端服务：`docker-compose up -d --build`
2. 访问 `http://localhost:5173/task-hub/create`，创建任务
3. 在 `http://localhost:5173/task-hub` 中点击"启动"按钮
4. **断言**：任务状态变为 `human_wait`（可通过刷新列表或查看详情确认）
5. 访问 `http://localhost:5173/review-publish-center`，切换到"审核中"标签
6. **断言**：能看到该任务，且内容预览不为空
7. 点击"通过"审核
8. **断言**：提示语显示"请前往「已通过」标签确认发布"
9. 切换到"已通过"标签，点击"确认发布"
10. **断言**：发布成功，任务状态流转正常

---

## 7. 附录：关键代码路径索引

| 文件 | 路径 | 相关行号 | 说明 |
|------|------|---------|------|
| 前端审核页 | `apps/frontend/src/pages/ReviewPublishCenterPage.tsx` | 66-77, 131-151 | 数据加载、过滤、审核决策 |
| 前端 Store | `apps/frontend/src/stores/reviewPublishStore.ts` | 70-83, 108-127 | fetchConclusions、decideTask |
| 前端任务页 | `apps/frontend/src/pages/TaskHubPage.tsx` | 354-362, 895-933 | 启动按钮、状态操作、跳转逻辑 |
| 前端 Store | `apps/frontend/src/stores/taskHubStore.ts` | 266-278 | configureTask |
| 后端 API | `apps/backend/src/api/review_publish.py` | 99-165, 213-280 | 列表查询、确认发布 |
| 后端服务 | `apps/backend/src/services/task_hub.py` | 438-439, 462-463, 549-585 | configure、approve、submit_human_decision |
| 后端服务 | `apps/backend/src/services/human_in_loop.py` | 289-363 | approve_task |
| 后端 API | `apps/backend/src/api/task_hub.py` | 234-244, 296-302 | start-workflow、start |
| 后端服务 | `apps/backend/src/services/workflow_engine.py` | 633-689 | start_workflow |
| 后端 API | `apps/backend/src/api/content_forge.py` | 235-293 | submit-for-review |
| 数据模型 | `apps/backend/src/models/task_orm.py` | 51-56, 61-99 | status 字段、prompt_variables |
| 后端测试 | `apps/backend/tests/test_review_publish_api.py` | 158 | 拼写错误 |
| 后端测试 | `apps/backend/tests/test_hitl_rpc_integration.py` | 37-44 | async 缺失 |
| 路由配置 | `apps/frontend/src/App.tsx` | 46 | `/review-publish-center` 路由 |

---

*报告由 EcoDreamOmni 专家组联合评审生成。遵循 AGENTS.md 中"证据优先"原则，所有结论均基于代码逐行分析得出。*
