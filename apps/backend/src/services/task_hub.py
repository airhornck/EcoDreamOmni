"""TaskHub — Task creation, state machine, batch tasks, human-in-the-loop interface.

Aligned with detailed design §7 / PRD V2.6 §10.3.

v2.2 refactor: Agent-Function protocol compliance.
- All DB operations delegated to task_function.py (Function layer).
- Agent layer focuses on orchestration, state machine, workflow integration.
- Architecture rule: Agent NEVER imports ORM models or uses db sessions directly.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


# ── Function layer imports ──
from src.services.task_function import (
    Task,
    TaskStatus,
    HumanDecision,
    TaskNodeExecution,
    _new_id,
    _now,
    get_task_cache,
    list_task_cache,
    clear_task_cache,
    load_tasks_into_cache,
    create_task_in_db,
    get_task_from_db,
    list_tasks_from_db,
    update_task_in_db,
    transition_task_in_db,
    delete_task_from_db,
)
from src.services import content_series
from src.services.content_forge_service import generate_with_persona
from src.services.compliance_engine import check_compliance
import src.services.persona_story_service as pss
from src.services.prompt_composition_engine import PromptCompositionEngine, ContentStrategy


# Re-export domain types for API layer
__all__ = [
    "Task",
    "TaskStatus",
    "HumanDecision",
    "TaskNodeExecution",
    "create_task",
    "get_task",
    "list_tasks",
    "update_task",
    "transition_task",
    "transition_task_with_update",
    "delete_task",
    "configure",
    "queue",
    "start",
    "pause",
    "resume",
    "wait_human",
    "approve",
    "reject",
    "complete",
    "fail",
    "batch_create_tasks",
    "start_workflow",
    "submit_human_decision",
    "get_human_decisions",
    "load_tasks_into_cache",
    "resume_workflow_execution",
    "simulate_node_output",
    "_clear_stores",
]


# ─── Task CRUD (delegated to Function layer) ───

async def create_task(
    db: Any,
    name: str,
    workflow_template_id: Optional[str] = None,
    workflow_version: int = 1,
    account_id: str = "",
    persona_id: str = "",
    *,
    prompt_variables: Optional[Dict[str, Any]] = None,
    parent_task_id: Optional[str] = None,
    priority: int = 50,
    scheduled_at: Optional[str] = None,
    cron_schedule: Optional[str] = None,
    cron_date_start: Optional[str] = None,
    cron_date_end: Optional[str] = None,
    created_by: str = "",
    platform: str = "xhs",
    content_format: Optional[str] = None,
    persona_story_id: Optional[str] = None,
    node_id: Optional[str] = None,
    content_series_id: Optional[str] = None,
    new_series_name: Optional[str] = None,
    trace_id: Optional[str] = None,
    execution_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    agent_config_snapshot: Optional[Dict[str, Any]] = None,
    content_strategy: Optional[Dict[str, Any]] = None,
    methodology_stage_id: Optional[str] = None,
    timeline_event_id: Optional[str] = None,
) -> Task:
    """Create a new task."""
    resolved_series_id = content_series_id
    if new_series_name and not content_series_id:
        series = content_series.create_series(
            name=new_series_name,
            account_id=account_id,
            stage_sequence=[],
        )
        resolved_series_id = series.id

    pv = dict(prompt_variables or {})
    if scheduled_at:
        pv["scheduled_at"] = scheduled_at
    if cron_schedule:
        pv["cron_schedule"] = cron_schedule
    if cron_date_start:
        pv["cron_date_start"] = cron_date_start
    if cron_date_end:
        pv["cron_date_end"] = cron_date_end

    task_id = _new_id("task")
    now = _now()
    task = Task(
        id=task_id,
        name=name,
        workflow_template_id=workflow_template_id,
        workflow_version=workflow_version,
        account_id=account_id,
        persona_id=persona_id,
        persona_story_id=persona_story_id,
        node_id=node_id,
        content_series_id=resolved_series_id,
        prompt_variables=pv,
        status=TaskStatus.DRAFT,
        current_node_index=0,
        parent_task_id=parent_task_id,
        priority=priority,
        scheduled_at=scheduled_at,
        created_by=created_by,
        platform=platform,
        content_format=content_format,
        trace_id=trace_id,
        execution_id=execution_id,
        created_at=now,
        updated_at=now,
        agent_id=agent_id,
        agent_config_snapshot=agent_config_snapshot or {},
        content_strategy=content_strategy,
        methodology_stage_id=methodology_stage_id,
        timeline_event_id=timeline_event_id,
    )
    return await create_task_in_db(db, task)


async def get_batch_progress(db: Any, parent_task_id: str) -> Dict[str, Any]:
    """Get progress statistics for a batch of tasks sharing the same parent."""
    tasks = await list_tasks(db, parent_task_id=parent_task_id)
    total = len(tasks)
    if total == 0:
        return {"total": 0, "completed": 0, "failed": 0, "progress_pct": 0.0}
    completed = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)
    failed = sum(1 for t in tasks if t.status == TaskStatus.FAILED)
    progress_pct = ((completed + failed) / total) * 100.0
    return {
        "total": total,
        "completed": completed,
        "failed": failed,
        "progress_pct": progress_pct,
    }


async def get_task(db: Any, task_id: str) -> Optional[Task]:
    """Get task with L1 cache."""
    cached = get_task_cache(task_id)
    if cached:
        return cached
    return await get_task_from_db(db, task_id)


async def list_tasks(
    db: Any,
    status: Optional[str] = None,
    account_id: Optional[str] = None,
    parent_task_id: Optional[str] = None,
    created_by: Optional[str] = None,
) -> List[Task]:
    cache = list_task_cache()
    if cache and not any((status, account_id, parent_task_id, created_by)):
        return cache
    return await list_tasks_from_db(db, status=status, account_id=account_id, parent_task_id=parent_task_id, created_by=created_by)


async def update_task(db: Any, task_id: str, **kwargs) -> Optional[Task]:
    task = get_task_cache(task_id)
    if not task:
        task = await get_task_from_db(db, task_id)
    if not task:
        return None

    for key, value in kwargs.items():
        if hasattr(task, key) and key != "status":
            setattr(task, key, value)
    task.updated_at = _now()
    return await update_task_in_db(db, task_id, task)


async def transition_task(db: Any, task_id: str, new_status: str) -> Optional[Task]:
    return await transition_task_in_db(db, task_id, new_status)


async def transition_task_with_update(
    db: Any, task_id: str, new_status: str, **kwargs
) -> Optional[Task]:
    task = await transition_task(db, task_id, new_status)
    if task:
        task = await update_task(db, task_id, **kwargs)
    return task


async def delete_task(db: Any, task_id: str) -> bool:
    return await delete_task_from_db(db, task_id)


# ─── State Machine shortcuts ───

async def configure(db: Any, task_id: str) -> Optional[Task]:
    return await transition_task(db, task_id, "configuring")


async def queue(db: Any, task_id: str) -> Optional[Task]:
    return await transition_task(db, task_id, "queued")


async def start(db: Any, task_id: str) -> Optional[Task]:
    return await transition_task(db, task_id, "running")


async def pause(db: Any, task_id: str) -> Optional[Task]:
    return await transition_task(db, task_id, "paused")


async def resume(db: Any, task_id: str) -> Optional[Task]:
    return await transition_task(db, task_id, "running")


async def wait_human(db: Any, task_id: str) -> Optional[Task]:
    return await transition_task(db, task_id, "human_wait")


async def approve(db: Any, task_id: str) -> Optional[Task]:
    return await transition_task(db, task_id, "running")


async def reject(db: Any, task_id: str) -> Optional[Task]:
    return await transition_task(db, task_id, "failed")


async def complete(db: Any, task_id: str) -> Optional[Task]:
    return await transition_task(db, task_id, "completed")


async def fail(db: Any, task_id: str) -> Optional[Task]:
    return await transition_task(db, task_id, "failed")


async def cancel(db: Any, task_id: str) -> Optional[Task]:
    return await transition_task(db, task_id, "cancelled")


async def retry(db: Any, task_id: str) -> Optional[Task]:
    """Retry a failed task: reset to queued and clear node index."""
    task = await transition_task(db, task_id, "queued")
    if task:
        task = await update_task(db, task_id, current_node_index=0)
    return task


# ─── Batch operations ───

async def batch_create_tasks(
    db: Any,
    tasks_data: Optional[List[Dict[str, Any]]] = None,
    created_by: str = "",
    name_prefix: Optional[str] = None,
    workflow_template_id: Optional[str] = None,
    workflow_version: int = 1,
    assignments: Optional[List[Dict[str, Any]]] = None,
    agent_id: Optional[str] = None,
) -> List[Task]:
    """Create multiple tasks in a single batch.

    Supports two calling styles:
    1. Legacy: tasks_data list of task dicts
    2. Batch campaign: name_prefix + assignments (creates parent + children)
    """
    # Legacy mode: tasks_data provided directly
    if tasks_data:
        created = []
        for data in tasks_data:
            task = await create_task(
                db=db,
                name=data["name"],
                workflow_template_id=data.get("workflow_template_id", "default"),
                workflow_version=data.get("workflow_version", 1),
                account_id=data.get("account_id", ""),
                persona_id=data.get("persona_id", ""),
                prompt_variables=data.get("prompt_variables", {}),
                parent_task_id=data.get("parent_task_id"),
                priority=data.get("priority", 50),
                scheduled_at=data.get("scheduled_at"),
                created_by=created_by,
                platform=data.get("platform", "xhs"),
                content_format=data.get("content_format"),
                persona_story_id=data.get("persona_story_id"),
                node_id=data.get("node_id"),
                content_series_id=data.get("content_series_id"),
                new_series_name=data.get("new_series_name"),
                agent_id=data.get("agent_id", agent_id),
            )
            created.append(task)
        return created

    # Campaign mode: parent + child tasks from assignments
    if name_prefix and assignments:
        created = []
        parent = await create_task(
            db=db,
            name=f"{name_prefix} (Parent)",
            workflow_template_id=workflow_template_id or "default",
            workflow_version=workflow_version,
            account_id="",
            persona_id="",
            created_by=created_by,
            agent_id=agent_id,
        )
        created.append(parent)
        for assign in assignments:
            child = await create_task(
                db=db,
                name=f"{name_prefix} - {assign.get('account_id', '')}",
                workflow_template_id=workflow_template_id or "default",
                workflow_version=workflow_version,
                account_id=assign.get("account_id", ""),
                persona_id=assign.get("persona_id", ""),
                priority=assign.get("priority", 50),
                parent_task_id=parent.id,
                created_by=created_by,
                agent_id=agent_id,
            )
            created.append(child)
        return created

    return []


# Alias for backward compatibility
create_batch = batch_create_tasks


# ─── Human-in-the-Loop bridge ───

async def submit_human_decision(
    db: Any,
    task_id: str,
    decision: str,
    operator: str,
    feedback: str = "",
) -> Optional[Task]:
    """Submit a human approval decision and drive the task forward."""
    task = await get_task(db, task_id)
    if not task:
        return None

    if task.status != TaskStatus.HUMAN_WAIT:
        raise ValueError(f"Task is not in HUMAN_WAIT status: {task.status.value}")

    if decision == "APPROVE":
        task = await transition_task_with_update(
            db, task_id, "running",
            review_decision="APPROVE", reviewer=operator,
            review_reason=feedback,
        )
    elif decision == "REJECT":
        task = await transition_task_with_update(
            db, task_id, "failed",
            review_decision="REJECT", reviewer=operator,
            review_reason=feedback,
        )
    elif decision == "REVISE":
        task = await transition_task_with_update(
            db, task_id, "configuring",
            review_decision="REVISE", reviewer=operator,
            review_reason=feedback,
        )
    else:
        raise ValueError(f"Unknown decision: {decision}")

    # Record human decision in node execution log (for audit trail)
    if task:
        from src.services.task_function import _node_exec_db
        _node_exec_db.append(
            TaskNodeExecution(
                id=_new_id("exec"),
                task_id=task_id,
                node_id="human_approval",
                node_type="HUMAN_APPROVAL",
                agent_id=None,
                prompt_template_id=None,
                status="completed",
                input_context={},
                output_context={"decision": decision, "feedback": feedback},
                started_at=_now(),
                ended_at=_now(),
                duration_ms=0,
                error_message=None,
                trace_id=task.trace_id or "",
                human_decision=decision,
                human_feedback=feedback,
                created_at=_now(),
            )
        )

    # For APPROVE, resume workflow execution to drive to completion
    if decision == "APPROVE" and task and task.execution_id:
        task = await resume_workflow_execution(db, task)

    return task


async def resume_workflow_execution(db: Any, task: Task) -> Task:
    """Resume a paused workflow execution after human approval."""
    from src.services import workflow_engine as we

    if not task.execution_id:
        return task

    execution = we.get_execution(task.execution_id)
    if not execution or execution.status != we.WorkflowStatus.PAUSED:
        return task

    # Resume execution
    we.resume_execution(execution.id)

    # Merge user-modified content from prompt_variables back into execution context
    # so that publisher nodes see the latest edits (cover, title, body, tags, etc.)
    pv = task.prompt_variables or {}
    if "generated_content" in pv:
        execution.context["generated_content"] = pv["generated_content"]
    if "cover_image_url" in pv:
        execution.context["cover_image_url"] = pv["cover_image_url"]
    if "title" in pv:
        execution.context["title"] = pv["title"]
    if "body" in pv:
        execution.context["body"] = pv["body"]
    if "tags" in pv:
        execution.context["tags"] = pv["tags"]

    if task.status != TaskStatus.RUNNING:
        task = await transition_task(db, task.id, "running")

    # Complete the current HUMAN_APPROVAL node first
    result = we.execute_next_node(execution.id, node_output={"human_decision": "APPROVE"})
    await update_task(db, task.id, current_node_index=execution.current_node_index)

    # Drive execution until completion, failure, or next human gate
    while True:
        execution = we.get_execution(execution.id)
        if execution.status in (we.WorkflowStatus.COMPLETED, we.WorkflowStatus.FAILED, we.WorkflowStatus.CANCELLED):
            break
        if execution.status == we.WorkflowStatus.PAUSED:
            break

        tmpl = we.get_template(execution.template_id)
        if not tmpl:
            break

        if execution.current_node_index >= len(tmpl.nodes):
            break

        node = tmpl.nodes[execution.current_node_index]

        # If next node is human approval, pause and wait
        if node.node_type == we.NodeType.HUMAN_APPROVAL:
            we.pause_execution(execution.id)
            task = await transition_task(db, task.id, "human_wait")
            break

        # Execute next node
        node_output = await simulate_node_output(node, task, execution_context=execution.context, db=db)
        result = we.execute_next_node(execution.id, node_output=node_output)
        await update_task(db, task.id, current_node_index=execution.current_node_index)

        if result.get("done"):
            if result.get("status") == "COMPLETED":
                task = await transition_task(db, task.id, "completed")
            elif result.get("status") == "FAILED":
                task = await transition_task(db, task.id, "failed")
            break

    return task


def get_human_decisions(task_id: str) -> List[TaskNodeExecution]:
    # Node execution history is in-memory only for MVP
    # This should be migrated to a Function-layer call when node_exec is persisted
    from src.services.task_function import _node_exec_db
    return [n for n in _node_exec_db if n.task_id == task_id and n.human_decision is not None]


# ─── Workflow Integration ───

async def simulate_node_output(
    node, task, execution_context: Optional[Dict[str, Any]] = None, db=None
) -> Dict[str, Any]:
    """Generate output for workflow nodes.

    REAL: trend-scout uses XhsClient to fetch real topic suggestions.
    REAL: marketing-methodology uses LLM to generate content structure.
    REAL: content-forge (cf-outline/cf-body) calls generate_with_persona via real LLM.
    REAL: compliance-guard calls check_compliance on generated text.
    REAL: pool-predictor uses LLM for engagement estimation (marked as reference).
    """
    logger = logging.getLogger(__name__)
    agent_id = node.agent_id or ""
    template_id = node.prompt_template_id or ""
    platform = task.platform or "xhs"
    task_name = task.name or "内容任务"
    execution_context = execution_context or {}

    # Base content derived from task name for realism
    base_topic = task_name.replace("任务", "").replace("内容", "").strip() or "宠物养护"

    # ── Helper: resolve LLM config from LLM Hub ──
    async def _resolve_llm_config() -> Optional[dict]:
        if db is None:
            return None
        try:
            from src.services import llm_hub as lhs
            resolved = await lhs.resolve_model_for_node(db, "content_generation")
            if resolved.get("source") != "none":
                model_info = await lhs.get_model(db, resolved["model_id"])
                if model_info:
                    return {
                        "provider": model_info["provider"],
                        "model_name": model_info["model_name"],
                        "api_key": lhs.decrypt_api_key(model_info["api_key_encrypted"]),
                        "endpoint_url": model_info.get("endpoint_base_url") or lhs._default_endpoint(model_info["provider"]),
                        "temperature": resolved.get("temperature", 0.8),
                    }
        except Exception:
            pass
        return None

    if agent_id == "trend-scout":
        report_id = _new_id("report")
        topics = []
        source = "mock"

        # Try real XHS topic fetch
        try:
            from src.services.xhs_publisher import _get_xhs_client
            from src.models.account_pool import get_pool_entry

            account = get_pool_entry(task.account_id) if task.account_id else None
            cookie = account.cookie if account and account.cookie else None
            user_agent = ""
            if account and account.fingerprint_profile:
                user_agent = account.fingerprint_profile.user_agent or ""

            if cookie:
                client = _get_xhs_client(cookie=cookie, user_agent=user_agent)
                suggest_results = client.get_suggest_topic(base_topic)
                if suggest_results:
                    for idx, t in enumerate(suggest_results[:5]):
                        topics.append({
                            "id": f"topic-{idx:03d}",
                            "title": t.get("name", base_topic),
                            "source_report": report_id,
                            "estimated_engagement": 200 + idx * 50,
                            "tags": [base_topic, t.get("name", "")],
                            "status": "adopted" if idx == 0 else "candidate",
                        })
                    source = "xhs_api"
        except Exception as exc:
            logger = logging.getLogger(__name__)
            logger.warning("TrendScout real fetch failed, falling back to mock: %s", exc)

        # Fallback to mock if real fetch yielded no topics
        if not topics:
            topics = [
                {
                    "id": "topic-001",
                    "title": base_topic,
                    "source_report": report_id,
                    "estimated_engagement": 350,
                    "tags": [base_topic, "宠物健康", "养宠日常"],
                    "status": "adopted",
                },
                {
                    "id": "topic-002",
                    "title": f"{base_topic}避坑指南",
                    "source_report": report_id,
                    "estimated_engagement": 280,
                    "tags": [base_topic, "避坑", "新手"],
                    "status": "candidate",
                },
            ]

        return {
            "topic_report": {
                "report_id": report_id,
                "selected_topic": base_topic,
                "topics": topics,
                "5a_stage": "AWARENESS",
                "audience_fit_score": 82,
            },
            "agent_summary": f"TrendScout: 从{source}获取 {len(topics)} 个话题建议",
        }

    if agent_id == "marketing-methodology":
        outline = {
            "title": f"🔥{base_topic}攻略，铲屎官必看！",
            "sections": ["环境降温", "饮食补水", "避坑指南", "急救方法"],
        }

        # ★ v4.0: 优先使用 task.methodology_stage_id 确定阶段
        methodology_stage_id = task.methodology_stage_id
        if methodology_stage_id:
            try:
                from src.services import methodology_service as ms
                stage = ms.get_stage(methodology_stage_id)
                if stage and hasattr(stage, "structure_template"):
                    outline = stage.structure_template
            except Exception:
                pass

        # Try LLM-driven structure generation (fallback when no stage_id)
        if not methodology_stage_id:
            try:
                from src.services.content_generator import call_llm
                llm_config = await _resolve_llm_config()
                system_prompt = f"""你是一位{platform}平台的内容策略专家。
基于选题「{base_topic}」，生成一个吸引人的内容结构大纲。
要求：
1. 标题符合平台调性，带emoji，有吸引力
2. 内容结构 3-5 个部分，每部分有清晰的小标题
3. 输出 JSON 格式：{{"title": "", "sections": ["", ""]}}"""
                raw = call_llm(system_prompt, f"请为「{base_topic}」生成{platform}平台的内容结构大纲", llm_config=llm_config)
                import json
                llm_outline = json.loads(raw)
                if llm_outline.get("title") and llm_outline.get("sections"):
                    outline = llm_outline
            except Exception as exc:
                logger = logging.getLogger(__name__)
                logger.warning("MarketingMethodology LLM failed, using fallback: %s", exc)

        return {
            "outline": outline,
            "methodology_stage_id": methodology_stage_id,
            "agent_summary": f"MarketingMethodology: 生成「{base_topic}」内容框架 ({len(outline.get('sections', []))} 节)",
        }

    if agent_id == "pool-predictor":
        prediction_result = {
            "predicted_score": 85,
            "predicted_views": 12000,
            "tags": [base_topic, "宠物健康"],
            "engagement_interval": {
                "likes": {"min": 800, "max": 1500, "confidence": "medium"},
                "comments": {"min": 50, "max": 120, "confidence": "medium"},
                "collects": {"min": 30, "max": 80, "confidence": "medium"},
            },
            "disclaimer": "基于经验模型的参考区间，非平台真实数据",
        }
        quality_score = {
            "overall": 87,
            "readability": 90,
            "engagement_potential": 85,
            "compliance_score": 95,
        }

        # Try LLM-driven prediction
        try:
            from src.services.content_generator import call_llm
            llm_config = await _resolve_llm_config()
            content_preview = execution_context.get("content", "")[:500]
            system_prompt = """你是一位小红书运营数据分析师。基于内容质量和平台特性，给出互动预测区间。
重要：必须标注这是"基于经验的参考区间，非平台真实数据"。
输出 JSON 格式：
{
  "engagement_interval": {
    "likes": {"min": 0, "max": 0, "confidence": "low|medium|high"},
    "comments": {"min": 0, "max": 0, "confidence": "low|medium|high"},
    "collects": {"min": 0, "max": 0, "confidence": "low|medium|high"}
  },
  "viral_probability": 0.0,
  "best_publish_time": "HH:MM-HH:MM"
}"""
            raw = call_llm(system_prompt, f"内容预览：{content_preview}\n\n选题：{base_topic}\n平台：{platform}", llm_config=llm_config)
            import json
            llm_prediction = json.loads(raw)
            if llm_prediction.get("engagement_interval"):
                prediction_result["engagement_interval"] = llm_prediction["engagement_interval"]
            if "viral_probability" in llm_prediction:
                prediction_result["viral_probability"] = llm_prediction["viral_probability"]
            if "best_publish_time" in llm_prediction:
                prediction_result["best_publish_time"] = llm_prediction["best_publish_time"]
        except Exception as exc:
            logger = logging.getLogger(__name__)
            logger.warning("PoolPredictor LLM failed, using fallback: %s", exc)

        return {
            "prediction_result": prediction_result,
            "quality_score": quality_score,
            "agent_summary": f"PoolPredictor: 「{base_topic}」参考预测 (质量分 {quality_score['overall']})",
        }

    if agent_id == "publisher":
        # Consume daily quota for the assigned account
        if task.account_id:
            from src.models.account_pool import _ensure_daily_reset, get_pool_entry

            account = get_pool_entry(task.account_id)
            if account:
                _ensure_daily_reset(account)
                if not account.quota_exceeded:
                    account.posts_today += 1
                    account.updated_at = datetime.now(timezone.utc).isoformat()

        # ── REAL PUBLISH via XhsClient ──
        real_publish_result = {
            "published": False,
            "url": "",
            "platform": platform,
            "platform_post_id": "",
            "error": "",
        }
        if platform == "xhs" or platform == "xiaohongshu":
            try:
                from src.services.xhs_publisher import publish_to_xhs

                gc = execution_context.get("generated_content", {})
                content = {
                    "title": gc.get("title", task.name),
                    "body": gc.get("body", ""),
                    "tags": gc.get("tags", []),
                    "images": gc.get("images", []),
                    "cover_image_url": gc.get("cover_image_url", ""),
                }
                if not content["body"]:
                    body = execution_context.get("content", "")
                    content["body"] = body
                result = publish_to_xhs(task.account_id, content)
                real_publish_result["published"] = result.get("success", False)
                real_publish_result["url"] = result.get("published_url", "")
                real_publish_result["platform_post_id"] = result.get("platform_post_id", "")
                real_publish_result["error"] = result.get("error", "")
                # ── P0 Fix: Persist publish result to task for audit trail ──
                if result.get("success"):
                    logger.info("XHS publish success: note_id=%s url=%s", result.get("platform_post_id"), result.get("published_url"))
                    # Update task with publish audit fields
                    await update_task(
                        db, task.id,
                        published_url=result.get("published_url"),
                        platform_post_id=result.get("platform_post_id"),
                        published_at=_now(),
                        publish_error="",
                    )
                    # ── 24h engagement data recovery (Celery delayed task) ──
                    platform_post_id = result.get("platform_post_id")
                    if platform_post_id and task.account_id:
                        try:
                            from src.celery_app import celery_app
                            import random
                            jitter = random.randint(0, 300)
                            celery_app.send_task(
                                "src.services.celery_tasks.fetch_note_engagement",
                                kwargs={
                                    "publish_task_id": task.id,
                                    "account_id": task.account_id,
                                    "platform_post_id": platform_post_id,
                                },
                                countdown=86400 + jitter,
                            )
                            logger.info("Scheduled engagement fetch for note %s in ~24h", platform_post_id)
                        except Exception as sched_exc:
                            logger.warning("Failed to schedule engagement fetch: %s", sched_exc)
                else:
                    logger.warning("XHS publish failed: %s", result.get("error"))
                    await update_task(
                        db, task.id,
                        publish_error=result.get("error", "Unknown publish error"),
                    )
            except Exception as e:
                logger.exception("XHS publish error")
                real_publish_result["error"] = str(e)
        else:
            real_publish_result["error"] = f"Platform {platform} real publisher not implemented"

        return {
            "publish_result": real_publish_result,
            "agent_summary": f"Publisher: {'发布成功' if real_publish_result['published'] else '发布失败'}「{base_topic}」到 {platform}",
        }

    # ── Helper: assign a preset cover image based on topic ──
    def _preset_cover_image(topic: str) -> str:
        """Return a deterministic Unsplash cover URL for the given topic."""
        keyword = topic.replace(" ", ",").replace("，", ",")
        return f"https://images.unsplash.com/photo-1543852786-1cf6624b9987?auto=format&fit=crop&w=800&q=80&keywords=pet,{keyword}"

    if agent_id == "content-forge" and template_id == "cf-outline":
        # ── REAL LLM CALL for detailed outline generation ──
        from src.services.content_generator import generate_outline

        llm_config = await _resolve_llm_config()
        try:
            outline = generate_outline(
                topic=base_topic,
                platform=platform,
                persona={"name": task.persona_id},  # simplified persona ref
                llm_config=llm_config,
            )
            return {
                "outline": outline,
                "agent_summary": f"ContentForge: 生成「{base_topic}」详细框架 ({len(outline.get('sections', []))} 节)",
            }
        except Exception as e:
            return {
                "outline": {
                    "title": f"{base_topic}攻略",
                    "sections": [
                        {"heading": "✨ 核心要点", "points": ["背景介绍"], "word_count": 100},
                    ],
                },
                "agent_summary": f"ContentForge: 框架生成失败，使用fallback ({str(e)[:50]})",
                "_error": str(e),
            }

    if agent_id == "content-forge" and template_id == "cf-body":
        # ── REAL LLM CALL with BrandKnowledge RAG + PersonaStory injection ──
        # Phase 2: content_format-aware generation
        content_format = task.content_format or "图文"
        preset_cover = _preset_cover_image(base_topic)
        brand_knowledge_entries = []
        if db is not None:
            try:
                from src.services import brand_knowledge_function as bkf
                bk_entries = await bkf.search_by_content(db, base_topic, limit=5)
                brand_knowledge_entries = [bkf.entry_to_dict(e) for e in bk_entries]
            except Exception:
                pass

        # PersonaStory context injection
        story_context = None
        if db is not None and task.persona_story_id:
            try:
                node_index = task.current_node_index
                if task.node_id:
                    node_result = await pss.get_node(db, task.node_id)
                    if node_result:
                        node_index = node_result.sequence_index
                ctx = await pss.get_story_context(db, task.persona_story_id, current_node_index=node_index)
                if ctx:
                    story_context = {
                        "series_theme": ctx.get("series_theme", ""),
                        "emotional_arc": ctx.get("emotional_arc", ""),
                        "current_node": ctx.get("current_node", {}),
                        "prev_recap": ctx.get("prev_node_summary", ""),
                        "next_teaser": ctx.get("next_node_teaser", ""),
                    }
                    current_node = ctx.get("current_node", {})
                    if current_node and current_node.get("theme"):
                        base_topic = current_node["theme"]
            except Exception:
                pass

        # LLM Hub config resolution
        llm_config = None
        if db is not None:
            try:
                from src.services import llm_hub as lhs
                resolved = await lhs.resolve_model_for_node(db, "content_generation")
                if resolved["source"] != "none":
                    model_info = await lhs.get_model(db, resolved["model_id"])
                    if model_info:
                        llm_config = {
                            "provider": model_info["provider"],
                            "model_name": model_info["model_name"],
                            "api_key": lhs.decrypt_api_key(model_info["api_key_encrypted"]),
                            "endpoint_url": model_info.get("endpoint_base_url") or lhs._default_endpoint(model_info["provider"]),
                            "temperature": resolved["temperature"],
                        }
            except Exception:
                pass

        # Determine content_type and format-specific fields from content_format
        content_type_map = {
            "图文": "note",
            "视频": "video",
            "视频复刻": "video_clone",
            "视频原创": "video_original",
            "仅文字": "text_only",
            "长文章": "article",
        }
        content_type = content_type_map.get(content_format, "note")

        # ★ v4.0 Strategy Element Architecture: Compose prompt from content_strategy
        composed_prompt_str = None
        strategy_keywords: List[str] = []
        if task.content_strategy:
            try:
                strategy = ContentStrategy(
                    elements=task.content_strategy.get("elements", []),
                    variables=task.content_strategy.get("variables", {}),
                    custom_fragments=task.content_strategy.get("custom_fragments", []),
                    persona_id=task.persona_id,
                    persona_story_id=task.persona_story_id,
                    node_id=task.node_id,
                    content_series_id=task.content_series_id,
                    timeline_event_id=task.timeline_event_id,
                    methodology_stage_id=task.methodology_stage_id,
                )
                engine = PromptCompositionEngine()
                composed = engine.compose(strategy, topic=base_topic, platform=platform, token_budget=8000)
                composed_prompt_str = composed.full_prompt
                # Extract keywords from strategy variables for叠加模式
                strategy_keywords = [
                    kw.strip()
                    for kw in strategy.variables.get("keywords", "").split(",")
                    if kw.strip()
                ]
            except Exception as exc:
                logger.warning("PromptCompositionEngine failed, falling back to legacy prompt building: %s", exc)

        # keyword_inject 叠加模式：workflow 注入的 keywords + 策略变量中的 keywords 合并去重
        workflow_keywords = execution_context.get("injected_keywords", [])
        if isinstance(workflow_keywords, list):
            merged_keywords = list(dict.fromkeys(strategy_keywords + workflow_keywords))
        else:
            merged_keywords = strategy_keywords

        try:
            new_content = generate_with_persona(
                topic=base_topic,
                platform=platform,
                persona_id=task.persona_id,
                brand_knowledge_entries=brand_knowledge_entries,
                story_context=story_context,
                keywords=merged_keywords if merged_keywords else None,
                llm_config=llm_config,
                composed_prompt=composed_prompt_str,
            )
            body_text = new_content.get("body", "").strip()
            title = new_content.get("title", f"🔥{base_topic}攻略！").strip()
            tags = new_content.get("tags", [base_topic, "宠物健康", "养宠日常"])
            cover_image_url = execution_context.get("cover_image_url") or task.prompt_variables.get("cover_image_url") or preset_cover
            draft_id = _new_id("draft")

            generated_content: Dict[str, Any] = {
                "title": title,
                "body": body_text,
                "tags": tags,
                "platform": platform,
                "content_type": content_type,
                "content_format": content_format,
                "cover_image_url": cover_image_url,
            }

            # Format-specific fields
            if content_format in ("视频", "视频复刻", "视频原创"):
                generated_content["video_script"] = new_content.get("video_script", "")
                generated_content["video_duration"] = new_content.get("video_duration", "30s-60s")
                generated_content["video_shots"] = new_content.get("video_shots", [])
            elif content_format == "长文章":
                generated_content["article_outline"] = new_content.get("article_outline", [])
                generated_content["word_count"] = len(body_text)
            elif content_format == "仅文字":
                generated_content["word_count"] = len(body_text)

            return {
                "generated_content": generated_content,
                "content_preview": body_text[:200],
                "draft_id": draft_id,
                "agent_summary": f"ContentForge: 生成「{base_topic}」{content_format} ({len(body_text)} 字)",
            }
        except Exception as e:
            # Graceful degradation
            generated_content_fallback: Dict[str, Any] = {
                "title": f"🔥{base_topic}攻略！",
                "body": f"{base_topic}是每位宠物家长都需要关注的话题...",
                "tags": [base_topic, "宠物健康"],
                "platform": platform,
                "content_type": content_type,
                "content_format": content_format,
                "cover_image_url": preset_cover,
            }
            if content_format in ("视频", "视频复刻", "视频原创"):
                generated_content_fallback["video_script"] = ""
                generated_content_fallback["video_duration"] = "30s-60s"
            elif content_format == "长文章":
                generated_content_fallback["article_outline"] = []
                generated_content_fallback["word_count"] = 0

            return {
                "generated_content": generated_content_fallback,
                "content_preview": f"{base_topic}是每位宠物家长都需要关注的话题...",
                "draft_id": _new_id("draft"),
                "agent_summary": f"ContentForge: LLM调用失败，使用fallback ({str(e)[:50]})",
                "_error": str(e),
            }

    if agent_id == "compliance-guard":
        content = execution_context.get("content", "")
        # Primary: ORM-based platform rules (L1-L4)
        orm_result = {"pass": True, "violations": [], "warnings": [], "suggestions": []}
        if db is not None:
            try:
                from src.services import platform_rule_function as prf

                orm_result = await prf.evaluate_content(
                    db=db,
                    content={
                        "title": task.prompt_variables.get("title", ""),
                        "body": content,
                        "tags": task.prompt_variables.get("tags", []),
                        "content_id": task.id,
                    },
                    platform=task.platform or "xiaohongshu",
                )
            except Exception:
                pass  # fallback to legacy check_compliance

        # Fallback: legacy hardcoded compliance engine
        legacy_result = check_compliance(content, content_id=task.id)

        # Merge ORM + legacy into unified format (backward-compatible)
        merged_violations = list(legacy_result.get("violations", []))
        merged_suggestions = list(legacy_result.get("suggestions", []))

        for v in orm_result.get("violations", []):
            merged_violations.append({
                "rule_id": v.get("rule_id", ""),
                "level": "L1" if v.get("layer", "").startswith("l1") else "L2",
                "category": v.get("name", ""),
                "matched": v.get("matched", ""),
                "message": f"触发规则: {v.get('name', '')}",
                "suggestion": "请根据规则要求修改内容",
            })
        for w in orm_result.get("warnings", []):
            merged_violations.append({
                "rule_id": w.get("rule_id", ""),
                "level": "L2",
                "category": w.get("name", ""),
                "matched": w.get("matched", ""),
                "message": f"触发规则: {w.get('name', '')}",
                "suggestion": "请根据规则要求修改内容",
            })
        for s in orm_result.get("suggestions", []):
            merged_suggestions.append(f"建议: {s.get('name', '')}")

        level = "reject" if any(v.get("level", "").startswith("L1") for v in merged_violations) else (
            "warning" if merged_violations else "pass"
        )

        result = {
            "evidence_id": legacy_result.get("evidence_id", ""),
            "content_id": task.id,
            "level": level,
            "violations": merged_violations,
            "suggestions": merged_suggestions,
            "checked_at": legacy_result.get("checked_at", ""),
            "_orm_evaluated": True,
        }
        risk_score = 100 if level == "reject" else (50 if level == "warning" else 0)
        return {
            "compliance_result": result,
            "agent_summary": f"ComplianceGuard: 扫描完成，风险分 {risk_score} ({len(merged_violations)} 违规)",
        }

    # Default fallback for unrecognized agents
    return {
        "output": f"Simulated output for {agent_id}/{template_id}",
        "agent_summary": f"Simulated: {agent_id}({template_id})",
    }


async def start_workflow(db: Any, task_id: str) -> Optional[Task]:
    """Start a workflow execution for an existing task and drive it to first human gate or completion.
    
    This is the bridge between TaskHub (task lifecycle) and WorkflowEngine (execution plan).
    """
    task = await get_task(db, task_id)
    if not task:
        return None
    if task.execution_id:
        raise ValueError("该任务已启动过工作流，请勿重复启动")

    from src.services import workflow_engine as we

    # v4.0 Agent-First: resolve workflow_template_id from agent if needed
    workflow_template_id = task.workflow_template_id
    if not workflow_template_id and task.agent_id:
        from src.services import agent_function as af
        agent_info = await af.get_agent_by_id(db, task.agent_id)
        if agent_info and agent_info.config:
            workflow_template_id = agent_info.config.get("default_workflow_template_id")
    if not workflow_template_id:
        raise ValueError("任务缺少 workflow_template_id 且无法从 agent 解析")

    # Transition task through state machine: DRAFT -> CONFIGURING -> QUEUED -> RUNNING
    await transition_task(db, task_id, "configuring")
    await transition_task(db, task_id, "queued")
    await transition_task(db, task_id, "running")

    # Start workflow execution
    execution = we.start_execution(task_id, workflow_template_id, prompt_variables=task.prompt_variables)

    # Inject strategy elements (including safety constraints) into execution context
    # so that compliance nodes can read structured constraints directly.
    prompt_vars = task.prompt_variables or {}
    strategy_element_ids = prompt_vars.get("strategy_element_ids") or []
    safety_constraint_ids = prompt_vars.get("safety_constraint_element_ids") or []
    if strategy_element_ids or safety_constraint_ids:
        try:
            from sqlalchemy import select
            from src.models.strategy_element import StrategyElementORM

            all_ids = list(set(strategy_element_ids + safety_constraint_ids))
            stmt = select(StrategyElementORM).where(StrategyElementORM.element_id.in_(all_ids))
            result = await db.execute(stmt)
            elements = result.scalars().all()
            strategy_elements_data = []
            safety_constraints_data = []
            for el in elements:
                item = {
                    "element_id": el.element_id,
                    "element_type": el.element_type,
                    "name": el.name,
                    "content": el.content or {},
                    "platform": el.platform,
                    "content_format": el.content_format,
                }
                strategy_elements_data.append(item)
                if el.element_type == "safety_constraint":
                    safety_constraints_data.append(item)
            execution.context["strategy_elements"] = strategy_elements_data
            execution.context["safety_constraints"] = safety_constraints_data
        except Exception as exc:
            logging.getLogger(__name__).warning("Failed to inject strategy elements into workflow context: %s", exc)

    task = await update_task(db, task_id, execution_id=execution.id)

    # Drive execution until human approval, completion, or failure
    while True:
        execution = we.get_execution(execution.id)
        if execution.status in (we.WorkflowStatus.COMPLETED, we.WorkflowStatus.FAILED, we.WorkflowStatus.CANCELLED):
            break
        if execution.status == we.WorkflowStatus.PAUSED:
            break

        tmpl = we.get_template(execution.template_id)
        if not tmpl:
            break

        if execution.current_node_index >= len(tmpl.nodes):
            break

        node = tmpl.nodes[execution.current_node_index]

        # If next node is human approval, pause workflow and set TaskHub to HUMAN_WAIT
        if node.node_type == we.NodeType.HUMAN_APPROVAL:
            we.pause_execution(execution.id)
            # Merge workflow context into prompt_variables for review-publish-center
            merged_vars = {**(task.prompt_variables or {}), **(execution.context or {})}
            if "content_preview" not in merged_vars:
                merged_vars["content_preview"] = execution.context.get("content", "") or execution.context.get("output", "") or ""
            # Also ensure structured content is preserved
            if "generated_content" in execution.context and "generated_content" not in merged_vars:
                merged_vars["generated_content"] = execution.context["generated_content"]
            if "topic_report" in execution.context and "topic_report" not in merged_vars:
                merged_vars["topic_report"] = execution.context["topic_report"]
            if "compliance_result" in execution.context and "compliance_result" not in merged_vars:
                merged_vars["compliance_result"] = execution.context["compliance_result"]
            if "prediction_result" in execution.context and "prediction_result" not in merged_vars:
                merged_vars["prediction_result"] = execution.context["prediction_result"]
            if "quality_score" in execution.context and "quality_score" not in merged_vars:
                merged_vars["quality_score"] = execution.context["quality_score"]
            if "cover_image_url" in execution.context and "cover_image_url" not in merged_vars:
                merged_vars["cover_image_url"] = execution.context["cover_image_url"]
            if "draft_id" in execution.context and "draft_id" not in merged_vars:
                merged_vars["draft_id"] = execution.context["draft_id"]
            task = await update_task(db, task_id, prompt_variables=merged_vars)
            task = await transition_task(db, task_id, "human_wait")
            break

        # Execute next node (content-forge & compliance-guard call real services)
        node_output = await simulate_node_output(node, task, execution_context=execution.context, db=db)
        result = we.execute_next_node(execution.id, node_output=node_output)
        await update_task(db, task_id, current_node_index=execution.current_node_index)

        if result.get("done"):
            if result.get("status") == "COMPLETED":
                task = await transition_task(db, task_id, "completed")
            elif result.get("status") == "FAILED":
                task = await transition_task(db, task_id, "failed")
            break

    return task


# ─── Clear stores (for testing) ───

def _clear_stores():
    clear_task_cache()
    from src.services.task_function import _node_exec_db
    _node_exec_db.clear()
