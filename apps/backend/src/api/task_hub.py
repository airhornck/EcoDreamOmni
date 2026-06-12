"""TaskHub API — Phase 2 / PRD V2.6 §10.3.

Routes:
  POST /task-hub/tasks                  # Create task
  GET  /task-hub/tasks                  # List tasks
  GET  /task-hub/tasks/{id}             # Get task
  PATCH /task-hub/tasks/{id}            # Update task
  DELETE /task-hub/tasks/{id}           # Delete task
  POST /task-hub/tasks/{id}/transition  # Generic state transition
  POST /task-hub/tasks/{id}/start       # Start (QUEUED -> RUNNING)
  POST /task-hub/tasks/{id}/pause       # Pause
  POST /task-hub/tasks/{id}/resume      # Resume
  POST /task-hub/tasks/{id}/complete    # Complete
  POST /task-hub/tasks/{id}/fail        # Fail
  POST /task-hub/tasks/{id}/cancel      # Cancel
  POST /task-hub/tasks/{id}/retry       # Retry (FAILED -> QUEUED)
  POST /task-hub/tasks/{id}/human-decision  # Approve/Reject/Revise
  POST /task-hub/batch                  # Create batch tasks
  GET  /task-hub/batch/{parent_id}/progress # Batch progress
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.dependencies import get_current_user
from src.core.rbac import can_modify_task, can_review_task, task_list_created_by_filter
from src.models.user import User
from src.services import task_hub

router = APIRouter(prefix="/task-hub", tags=["task-hub"])


def _require_ownership(task: task_hub.Task, user: User) -> None:
    if not can_modify_task(user, task):
        raise HTTPException(status_code=403, detail="Forbidden: not the task owner")


# ─── Schemas ───

class CreateTaskRequest(BaseModel):
    name: str
    # v4.0 Agent-First: agent_id 替代 workflow_template_id
    agent_id: Optional[str] = None
    workflow_template_id: Optional[str] = None  # deprecated, 兼容存量
    workflow_version: int = 1
    account_id: str
    persona_id: str
    platform: str = "xhs"
    content_format: Optional[str] = None
    priority: int = 50
    prompt_variables: Optional[Dict[str, Any]] = None
    parent_task_id: Optional[str] = None
    scheduled_at: Optional[str] = None
    cron_schedule: Optional[str] = None  # e.g. "0 9 * * 1"
    cron_date_start: Optional[str] = None  # YYYY-MM-DD
    cron_date_end: Optional[str] = None    # YYYY-MM-DD
    created_by: str = ""
    # 新增字段，对齐前端契约
    persona_story_id: Optional[str] = None
    node_id: Optional[str] = None
    content_series_id: Optional[str] = None
    new_series_name: Optional[str] = None
    content_strategy: Optional[Dict[str, Any]] = None
    methodology_stage_id: Optional[str] = None
    timeline_event_id: Optional[str] = None


class TaskResponse(BaseModel):
    id: str
    name: str
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None
    workflow_template_id: Optional[str] = None
    workflow_template_name: Optional[str] = None
    workflow_version: int
    account_id: str
    account_name: Optional[str] = None
    persona_id: str
    persona_name: Optional[str] = None
    persona_story_id: Optional[str] = None
    story_name: Optional[str] = None
    node_id: Optional[str] = None
    content_series_id: Optional[str] = None
    content_series_name: Optional[str] = None
    prompt_variables: Dict[str, Any]
    status: str
    current_node_index: int
    current_step_label: Optional[str] = None
    estimated_completion_at: Optional[str] = None
    parent_task_id: Optional[str]
    priority: int
    scheduled_at: Optional[str]
    created_by: str
    created_at: str
    updated_at: str
    completed_at: Optional[str]
    platform: str = "xhs"
    review_decision: Optional[str] = None
    reviewed_at: Optional[str] = None
    reviewer: Optional[str] = None
    review_reason: Optional[str] = None
    publish_confirmed_at: Optional[str] = None
    publish_confirmer: Optional[str] = None
    cron_job_id: Optional[str] = None
    trace_id: Optional[str] = None
    execution_id: Optional[str] = None
    content_strategy: Optional[Dict[str, Any]] = None
    methodology_stage_id: Optional[str] = None
    timeline_event_id: Optional[str] = None
    # 富化字段（当前阶段先返回 None，后续 Phase 完善 JOIN 查询）
    account_name: Optional[str] = None
    persona_name: Optional[str] = None
    story_name: Optional[str] = None
    workflow_template_name: Optional[str] = None
    current_step_label: Optional[str] = None
    estimated_completion_at: Optional[str] = None


class UpdateTaskRequest(BaseModel):
    name: Optional[str] = None
    prompt_variables: Optional[Dict[str, Any]] = None
    priority: Optional[int] = None
    scheduled_at: Optional[str] = None


# ─── v4.0 Copilot-Driven 响应扩展 (Step 2 冻结) ───

class CopilotSuggestedAction(BaseModel):
    type: str
    label: str
    reason: str


class CopilotSummary(BaseModel):
    kanban_stats: Dict[str, int]
    recommended_focus: str
    ai_insight: str
    suggested_actions: List[CopilotSuggestedAction]


class CopilotEditorSuggestion(BaseModel):
    type: str
    confidence: float
    reason: str
    suggested_title: Optional[str] = None
    suggested_tags: Optional[List[str]] = None


class CopilotContext(BaseModel):
    editor_suggestions: List[CopilotEditorSuggestion]
    save_status: str
    recommended_next: str
    generation_progress: Optional[Dict[str, Any]] = None


class CopilotFollowup(BaseModel):
    message: str
    suggested_cards: List[Dict[str, Any]]


class TaskListResponse(BaseModel):
    items: List[TaskResponse]
    copilot_summary: CopilotSummary


class TaskDetailResponse(BaseModel):
    task: TaskResponse
    copilot_context: CopilotContext


class TaskCreateResponse(BaseModel):
    task: TaskResponse
    copilot_followup: CopilotFollowup


class TransitionRequest(BaseModel):
    status: str


class HumanDecisionRequest(BaseModel):
    decision: str = Field(..., description="APPROVE / REJECT / REVISE")
    operator: Optional[str] = None
    feedback: Optional[str] = None


class BatchAssignment(BaseModel):
    account_id: str
    persona_id: str
    prompt_variables: Optional[Dict[str, Any]] = None
    priority: int = 50
    scheduled_at: Optional[str] = None


class CreateBatchRequest(BaseModel):
    name_prefix: str
    agent_id: Optional[str] = None
    workflow_template_id: Optional[str] = None
    workflow_version: int = 1
    assignments: List[BatchAssignment]
    created_by: Optional[str] = None


class BatchProgressResponse(BaseModel):
    total: int
    completed: int
    failed: int
    progress_pct: float


# ─── Helpers ───

def _to_task_response(t: task_hub.Task) -> TaskResponse:
    return TaskResponse(
        id=t.id,
        name=t.name,
        agent_id=t.agent_id,
        agent_name=t.agent_name,
        workflow_template_id=t.workflow_template_id,
        workflow_template_name=t.workflow_template_name,
        workflow_version=t.workflow_version,
        account_id=t.account_id,
        account_name=t.account_name,
        persona_id=t.persona_id,
        persona_name=t.persona_name,
        persona_story_id=t.persona_story_id,
        story_name=t.story_name,
        node_id=t.node_id,
        content_series_id=t.content_series_id,
        content_series_name=t.content_series_name,
        prompt_variables=t.prompt_variables,
        status=t.status.value,
        current_node_index=t.current_node_index,
        current_step_label=t.current_step_label,
        estimated_completion_at=t.estimated_completion_at,
        parent_task_id=t.parent_task_id,
        priority=t.priority,
        scheduled_at=t.scheduled_at,
        created_by=t.created_by,
        created_at=t.created_at,
        updated_at=t.updated_at,
        completed_at=t.completed_at,
        platform=t.platform,
        review_decision=t.review_decision,
        reviewed_at=t.reviewed_at,
        reviewer=t.reviewer,
        review_reason=t.review_reason,
        publish_confirmed_at=t.publish_confirmed_at,
        publish_confirmer=t.publish_confirmer,
        cron_job_id=t.cron_job_id,
        trace_id=t.trace_id,
        execution_id=t.execution_id,
    )


# ─── Tasks ───

@router.post("/tasks", status_code=201, response_model=TaskCreateResponse)
async def create_task(
    req: CreateTaskRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # v4.0 Agent-First: resolve workflow_template from agent if not provided
    workflow_template_id = req.workflow_template_id
    agent_id = req.agent_id
    agent_config_snapshot = None

    if agent_id and not workflow_template_id:
        from src.services import agent_function as af
        agent_info = await af.get_agent_by_id(db, agent_id)
        if not agent_info:
            raise HTTPException(status_code=400, detail=f"Agent not found: {agent_id}")
        if agent_info.status != "ACTIVE":
            raise HTTPException(status_code=400, detail=f"Agent {agent_id} is not ACTIVE")
        workflow_template_id = agent_info.config.get("default_workflow_template_id") if agent_info.config else None
        agent_config_snapshot = agent_info.config

    t = await task_hub.create_task(
        db=db,
        name=req.name,
        workflow_template_id=workflow_template_id,
        workflow_version=req.workflow_version,
        account_id=req.account_id,
        persona_id=req.persona_id,
        prompt_variables=req.prompt_variables,
        parent_task_id=req.parent_task_id,
        priority=req.priority,
        scheduled_at=req.scheduled_at,
        cron_schedule=req.cron_schedule,
        cron_date_start=req.cron_date_start,
        cron_date_end=req.cron_date_end,
        created_by=user.id,
        platform=req.platform,
        content_format=req.content_format,
        persona_story_id=req.persona_story_id,
        node_id=req.node_id,
        content_series_id=req.content_series_id,
        new_series_name=req.new_series_name,
        agent_id=agent_id,
        agent_config_snapshot=agent_config_snapshot,
        content_strategy=req.content_strategy,
        methodology_stage_id=req.methodology_stage_id,
        timeline_event_id=req.timeline_event_id,
    )
    # v4.0: Build copilot_followup for content creation
    followup = CopilotFollowup(
        message=f"任务已创建！推荐 Agent「{t.agent_name or '默认 Agent'}」。要现在生成内容吗？",
        suggested_cards=[
            {
                "type": "action",
                "title": "立即生成内容",
                "description": f"使用 {t.agent_name or '默认 Agent'} 生成内容",
                "actions": [
                    {
                        "id": "generate_now",
                        "label": "🚀 立即生成",
                        "variant": "primary",
                        "api": {
                            "method": "POST",
                            "endpoint": f"/api/task-hub/tasks/{t.id}/generate",
                            "payload": {},
                        },
                    },
                    {
                        "id": "configure_first",
                        "label": "⚙️ 先配置",
                        "variant": "secondary",
                        "api": {
                            "method": "GET",
                            "endpoint": f"/api/task-hub/tasks/{t.id}",
                            "payload": {},
                        },
                    },
                ],
            }
        ],
    )
    return TaskCreateResponse(task=_to_task_response(t), copilot_followup=followup)


@router.post("/tasks/with-workflow", status_code=201, response_model=TaskResponse)
async def create_task_with_workflow(
    req: CreateTaskRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create task and immediately start workflow execution."""
    workflow_template_id = req.workflow_template_id
    agent_id = req.agent_id
    agent_config_snapshot = None

    if agent_id and not workflow_template_id:
        from src.services import agent_function as af
        agent_info = await af.get_agent_by_id(db, agent_id)
        if not agent_info:
            raise HTTPException(status_code=400, detail=f"Agent not found: {agent_id}")
        if agent_info.status != "ACTIVE":
            raise HTTPException(status_code=400, detail=f"Agent {agent_id} is not ACTIVE")
        workflow_template_id = agent_info.config.get("default_workflow_template_id") if agent_info.config else None
        agent_config_snapshot = agent_info.config

    t = await task_hub.create_task(
        db=db,
        name=req.name,
        workflow_template_id=workflow_template_id,
        workflow_version=req.workflow_version,
        account_id=req.account_id,
        persona_id=req.persona_id,
        prompt_variables=req.prompt_variables,
        parent_task_id=req.parent_task_id,
        priority=req.priority,
        scheduled_at=req.scheduled_at,
        created_by=user.id,
        platform=req.platform,
        content_format=req.content_format,
        persona_story_id=req.persona_story_id,
        node_id=req.node_id,
        content_series_id=req.content_series_id,
        new_series_name=req.new_series_name,
        agent_id=agent_id,
        agent_config_snapshot=agent_config_snapshot,
    )
    # Start workflow and drive to first human gate or completion
    t = await task_hub.start_workflow(db, t.id)
    return _to_task_response(t)


@router.post("/tasks/{task_id}/start-workflow", response_model=TaskResponse)
async def start_task_workflow(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Start workflow for an existing task."""
    t = await task_hub.get_task(db, task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    _require_ownership(t, user)
    try:
        t = await task_hub.start_workflow(db, task_id)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return _to_task_response(t)


@router.get("/tasks", response_model=TaskListResponse)
async def list_tasks(
    status: Optional[str] = None,
    account_id: Optional[str] = None,
    parent_task_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    created_by = task_list_created_by_filter(user)
    tasks = await task_hub.list_tasks(db, status, account_id, parent_task_id, created_by=created_by)
    # v4.0: Build kanban stats and copilot_summary
    stats = {"draft": 0, "reviewing": 0, "approved": 0, "published": 0}
    for t in tasks:
        s = t.status.value if hasattr(t.status, "value") else str(t.status)
        if s in stats:
            stats[s] = stats.get(s, 0) + 1
        elif s in ("HUMAN_WAIT", "human_wait"):
            stats["reviewing"] = stats.get("reviewing", 0) + 1
        elif s in ("APPROVED_WAITING_PUBLISH", "approved_waiting_publish"):
            stats["approved"] = stats.get("approved", 0) + 1
        elif s in ("COMPLETED", "completed"):
            stats["published"] = stats.get("published", 0) + 1
        else:
            stats["draft"] = stats.get("draft", 0) + 1
    recommended = "draft"
    if stats["reviewing"] > 3:
        recommended = "reviewing"
    elif stats["approved"] > 5:
        recommended = "approved"
    summary = CopilotSummary(
        kanban_stats=stats,
        recommended_focus=recommended,
        ai_insight=f"草稿区堆积 {stats['draft']} 个任务，建议优先处理过期任务",
        suggested_actions=[
            CopilotSuggestedAction(
                type="create_task",
                label="新建内容",
                reason=f"今日发布进度仅 {min(stats['published'] * 10, 100)}%，建议补充内容",
            ),
        ],
    )
    return TaskListResponse(items=[_to_task_response(t) for t in tasks], copilot_summary=summary)


@router.get("/tasks/{task_id}", response_model=TaskDetailResponse)
async def get_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    t = await task_hub.get_task(db, task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    _require_ownership(t, user)
    # v4.0: Build copilot_context for editor page
    ctx = CopilotContext(
        editor_suggestions=[
            CopilotEditorSuggestion(
                type="title_optimization",
                confidence=0.89,
                reason="加入数字可提升 CTR 15%",
                suggested_title="猫咪驱虫避坑指南，这3个误区90%的人都不知道",
            ),
        ],
        save_status="unsaved_changes",
        recommended_next="save_draft",
        generation_progress=None,
    )
    return TaskDetailResponse(task=_to_task_response(t), copilot_context=ctx)


@router.patch("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    req: UpdateTaskRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    t = await task_hub.get_task(db, task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    _require_ownership(t, user)
    data = req.model_dump(exclude_unset=True)
    updated = await task_hub.update_task(db, task_id, **data)
    return _to_task_response(updated)


@router.delete("/tasks/{task_id}", status_code=204)
async def delete_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    t = await task_hub.get_task(db, task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    _require_ownership(t, user)
    ok = await task_hub.delete_task(db, task_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Task not found")
    return None


# ─── State Transitions ───

@router.post("/tasks/{task_id}/transition", response_model=TaskResponse)
async def transition_task(
    task_id: str,
    req: TransitionRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    t = await task_hub.get_task(db, task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    _require_ownership(t, user)
    try:
        t = await task_hub.transition_task(db, task_id, req.status)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    return _to_task_response(t)


@router.post("/tasks/{task_id}/configure", response_model=TaskResponse)
async def configure(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    t = await task_hub.get_task(db, task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    _require_ownership(t, user)
    t = await task_hub.configure(db, task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    return _to_task_response(t)


@router.post("/tasks/{task_id}/queue", response_model=TaskResponse)
async def queue(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    t = await task_hub.get_task(db, task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    _require_ownership(t, user)
    t = await task_hub.queue(db, task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    return _to_task_response(t)


@router.post("/tasks/{task_id}/start", response_model=TaskResponse)
async def start(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    t = await task_hub.get_task(db, task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    _require_ownership(t, user)
    t = await task_hub.start(db, task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    return _to_task_response(t)


@router.post("/tasks/{task_id}/pause", response_model=TaskResponse)
async def pause(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    t = await task_hub.get_task(db, task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    _require_ownership(t, user)
    t = await task_hub.pause(db, task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    return _to_task_response(t)


@router.post("/tasks/{task_id}/resume", response_model=TaskResponse)
async def resume(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    t = await task_hub.get_task(db, task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    _require_ownership(t, user)
    t = await task_hub.resume(db, task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    return _to_task_response(t)


@router.post("/tasks/{task_id}/complete", response_model=TaskResponse)
async def complete(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    t = await task_hub.get_task(db, task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    _require_ownership(t, user)
    t = await task_hub.complete(db, task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    return _to_task_response(t)


@router.post("/tasks/{task_id}/fail", response_model=TaskResponse)
async def fail(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    t = await task_hub.get_task(db, task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    _require_ownership(t, user)
    t = await task_hub.fail(db, task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    return _to_task_response(t)


@router.post("/tasks/{task_id}/cancel", response_model=TaskResponse)
async def cancel(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    t = await task_hub.get_task(db, task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    _require_ownership(t, user)
    t = await task_hub.cancel(db, task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    return _to_task_response(t)


@router.post("/tasks/{task_id}/retry", response_model=TaskResponse)
async def retry(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    t = await task_hub.get_task(db, task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    _require_ownership(t, user)
    try:
        t = await task_hub.retry(db, task_id)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    return _to_task_response(t)


# ─── Human-in-the-Loop ───

@router.post("/tasks/{task_id}/human-decision", response_model=TaskResponse)
async def human_decision(
    task_id: str,
    req: HumanDecisionRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    t = await task_hub.get_task(db, task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    if not can_review_task(user, t):
        raise HTTPException(status_code=403, detail="Forbidden: not authorized to review this task")
    if req.decision.upper() == "APPROVE":
        from src.services import human_in_loop as hil
        result = await hil.approve_task(db, task_id, operator=user.id)
        if not result:
            raise HTTPException(status_code=404, detail="Task not found")
        t = await task_hub.get_task(db, task_id)
        return _to_task_response(t)
    try:
        t = await task_hub.submit_human_decision(db, task_id, req.decision, user.id, req.feedback)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    return _to_task_response(t)


# ─── Batch ───

@router.post("/batch", status_code=201, response_model=List[TaskResponse])
async def create_batch(
    req: CreateBatchRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    batch = await task_hub.create_batch(
        db=db,
        name_prefix=req.name_prefix,
        workflow_template_id=req.workflow_template_id,
        workflow_version=req.workflow_version,
        assignments=[a.model_dump() for a in req.assignments],
        created_by=user.id,
        agent_id=req.agent_id,
    )
    return [_to_task_response(t) for t in batch]


@router.get("/batch/{parent_task_id}/progress", response_model=BatchProgressResponse)
async def batch_progress(
    parent_task_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    t = await task_hub.get_task(db, parent_task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    _require_ownership(t, user)
    progress = await task_hub.get_batch_progress(db, parent_task_id)
    return BatchProgressResponse(
        total=progress["total"],
        completed=progress["completed"],
        failed=progress["failed"],
        progress_pct=progress["progress_pct"],
    )
