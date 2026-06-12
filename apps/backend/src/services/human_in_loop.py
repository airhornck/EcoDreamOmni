"""Human-in-the-Loop — Review cockpit, dual approval, intervention records.

W17增强: 弹性审核策略、高风险自动检测、batch-approve批量管控。
Aligned with detailed design §10 / PRD V2.6 §10.6.
"""

import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


from src.services import task_hub


# ─── Enums ───

class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ReviewStrategy(str, Enum):
    SINGLE = "single"
    DUAL = "dual"


# ─── Dataclasses ───

@dataclass
class ReviewRecord:
    id: str
    task_id: str
    reviewer: str
    decision: str  # APPROVE / REJECT / REVISE
    reason: Optional[str]
    target_node_index: Optional[int]
    revised_variables: Optional[Dict[str, Any]]
    publish_mode: Optional[str]  # immediate / scheduled
    scheduled_at: Optional[str]
    is_dual_approval: bool
    dual_approver: Optional[str]
    created_at: str


@dataclass
class PendingReviewDTO:
    task_id: str
    task_name: str
    status: str
    content_preview: str
    agent_summary: str
    prompt_variables: Dict[str, Any]
    priority: int
    waiting_since: str
    requires_dual_approval: bool
    risk_level: RiskLevel = RiskLevel.LOW
    review_strategy: ReviewStrategy = ReviewStrategy.SINGLE


# ─── In-memory stores ───
_review_db: List[ReviewRecord] = []
_task_risk_db: Dict[str, Dict[str, Any]] = {}  # {task_id: {"risk_level": ..., "reason": ...}}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_urlsafe(8)}"


# ─── W17: Risk Detection ───

_L1_KEYWORDS = ["阿莫西林", "头孢", "青霉素", "处方药", "治愈", "根治", "保证有效", "无效退款"]
_L2_KEYWORDS = ["下单", "购买链接", "优惠码", "折扣", "限时", "种草", "必买"]


def detect_content_risk(title: str, body: str, tags: List[str]) -> Dict[str, Any]:
    """Detect content risk level for elastic review strategy.

    Returns:
        {"risk_level": "LOW"|"MEDIUM"|"HIGH", "reasons": [...], "review_strategy": "single"|"dual"}
    """
    text = f"{title} {body}"
    reasons = []
    score = 0

    for kw in _L1_KEYWORDS:
        if kw in text:
            reasons.append(f"包含高风险关键词「{kw}」")
            score += 3

    for kw in _L2_KEYWORDS:
        if kw in text:
            reasons.append(f"包含商业推广关键词「{kw}」")
            score += 1

    if score >= 3:
        risk_level = RiskLevel.HIGH
        strategy = ReviewStrategy.DUAL
    elif score >= 1:
        risk_level = RiskLevel.MEDIUM
        strategy = ReviewStrategy.SINGLE
    else:
        risk_level = RiskLevel.LOW
        strategy = ReviewStrategy.SINGLE

    return {
        "risk_level": risk_level.value,
        "reasons": reasons,
        "review_strategy": strategy.value,
        "requires_forced_individual_review": risk_level == RiskLevel.HIGH,
    }


def get_review_strategy(risk_level: str) -> Dict[str, Any]:
    """Get review strategy based on risk level."""
    mapping = {
        RiskLevel.LOW.value: {"review_strategy": ReviewStrategy.SINGLE.value, "approvers_required": 1},
        RiskLevel.MEDIUM.value: {"review_strategy": ReviewStrategy.SINGLE.value, "approvers_required": 1, "alert": True},
        RiskLevel.HIGH.value: {"review_strategy": ReviewStrategy.DUAL.value, "approvers_required": 2},
    }
    return mapping.get(risk_level, mapping[RiskLevel.LOW.value])


async def mark_task_risk(
    db: Any,
    task_id: str,
    risk_level: str,
    reason: str = "",
) -> Optional[Dict[str, Any]]:
    """Mark a task with risk level (used by review cockpit)."""
    t = await task_hub.get_task(db, task_id)
    if not t:
        return None
    _task_risk_db[task_id] = {"risk_level": risk_level, "reason": reason}
    strategy = get_review_strategy(risk_level)
    return {
        "task_id": task_id,
        "risk_level": risk_level,
        "review_strategy": strategy["review_strategy"],
        "reason": reason,
    }


def get_task_risk(task_id: str) -> Dict[str, Any]:
    """Get risk info for a task."""
    risk = _task_risk_db.get(task_id, {})
    return {
        "risk_level": risk.get("risk_level", RiskLevel.LOW.value),
        "reason": risk.get("reason", ""),
    }


# ─── W17: Batch Approve ───

async def batch_approve(
    db: Any,
    task_ids: List[str],
    reviewer_id: str,
) -> Dict[str, Any]:
    """Batch approve tasks with high-risk individual review enforcement.

    Returns:
        {"approved_count": int, "rejected_count": int, "forced_individual_review_count": int, "forced_individual_review_ids": [...]}
    """
    approved = 0
    rejected = 0
    forced_ids = []

    for task_id in task_ids:
        risk_info = get_task_risk(task_id)
        risk_level = risk_info.get("risk_level", RiskLevel.LOW.value)

        if risk_level == RiskLevel.HIGH.value:
            # High risk: force individual review, skip batch
            forced_ids.append(task_id)
            continue

        t = await task_hub.get_task(db, task_id)
        if not t or t.status != task_hub.TaskStatus.HUMAN_WAIT:
            rejected += 1
            continue

        # Single approval for LOW/MEDIUM (v2: transitions to APPROVED_WAITING_PUBLISH)
        try:
            await approve_task(db, task_id, reviewer_id)
            approved += 1
        except (ValueError, Exception):
            rejected += 1

    return {
        "approved_count": approved,
        "rejected_count": rejected,
        "forced_individual_review_count": len(forced_ids),
        "forced_individual_review_ids": forced_ids,
    }


# ─── Review Cockpit ───

async def get_pending_tasks(
    db: Any,
    reviewer_role: Optional[str] = None,
    account_id: Optional[str] = None,
    created_by: Optional[str] = None,
) -> List[PendingReviewDTO]:
    """Return tasks in HUMAN_WAIT status, ordered by priority / time."""
    tasks = await task_hub.list_tasks(db, status="human_wait", created_by=created_by)
    if account_id:
        tasks = [t for t in tasks if t.account_id == account_id]

    results = []
    for t in tasks:
        # Determine if dual approval required (simplified: tasks with publisher workflow)
        requires_dual = _requires_dual_approval(t.workflow_template_id)
        preview = t.prompt_variables.get("content_preview", "")
        summary = t.prompt_variables.get("agent_summary", "")

        # W17: Apply risk-based strategy
        risk_info = get_task_risk(t.id)
        risk_level = RiskLevel(risk_info.get("risk_level", RiskLevel.LOW.value))
        strategy = ReviewStrategy.DUAL if risk_level == RiskLevel.HIGH else (ReviewStrategy.DUAL if requires_dual else ReviewStrategy.SINGLE)

        results.append(
            PendingReviewDTO(
                task_id=t.id,
                task_name=t.name,
                status=t.status.value,
                content_preview=preview[:200] if isinstance(preview, str) else "",
                agent_summary=summary[:200] if isinstance(summary, str) else "",
                prompt_variables=t.prompt_variables,
                priority=t.priority,
                waiting_since=t.updated_at,
                requires_dual_approval=requires_dual or risk_level == RiskLevel.HIGH,
                risk_level=risk_level,
                review_strategy=strategy,
            )
        )
    # Sort by priority desc, then updated_at asc
    results.sort(key=lambda x: (-x.priority, x.waiting_since))
    return results


async def get_review_detail(
    db: Any,
    task_id: str,
) -> Optional[Dict[str, Any]]:
    t = await task_hub.get_task(db, task_id)
    if not t:
        return None
    history = await get_review_history(db, task_id)
    requires_dual = _requires_dual_approval(t.workflow_template_id)
    return {
        "task_id": t.id,
        "task_name": t.name,
        "status": t.status.value,
        "content_preview": t.prompt_variables.get("content_preview", ""),
        "agent_summary": t.prompt_variables.get("agent_summary", ""),
        "prompt_variables": t.prompt_variables,
        "workflow_template_id": t.workflow_template_id,
        "current_node_index": t.current_node_index,
        "waiting_since": t.updated_at,
        "requires_dual_approval": requires_dual,
        "has_primary_approval": any(r.decision == "APPROVE" for r in history),
        "review_history": [
            {
                "reviewer": r.reviewer,
                "decision": r.decision,
                "reason": r.reason,
                "created_at": r.created_at,
            }
            for r in history
        ],
    }


def _requires_dual_approval(workflow_template_id: Optional[str]) -> bool:
    """Simplified: workflows with 'publish' in template_id require dual approval."""
    if not workflow_template_id:
        return False
    return "publish" in workflow_template_id.lower()


# ─── Review Decisions ───

async def approve_task(
    db: Any,
    task_id: str,
    operator: str,
    publish_mode: Optional[str] = None,
    scheduled_at: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    t = await task_hub.get_task(db, task_id)
    if not t:
        return None
    if t.status != task_hub.TaskStatus.HUMAN_WAIT:
        raise ValueError("Task is not in HUMAN_WAIT status")

    # Check dual approval
    requires_dual = _requires_dual_approval(t.workflow_template_id)
    history = await get_review_history(db, task_id)
    has_primary = any(r.decision == "APPROVE" for r in history)

    if requires_dual and not has_primary:
        # First approval: record but keep in HUMAN_WAIT
        record = ReviewRecord(
            id=_new_id("rev"),
            task_id=task_id,
            reviewer=operator,
            decision="APPROVE",
            reason=None,
            target_node_index=None,
            revised_variables=None,
            publish_mode=publish_mode,
            scheduled_at=scheduled_at,
            is_dual_approval=True,
            dual_approver=None,
            created_at=_now(),
        )
        _review_db.append(record)
        return {
            "task_id": task_id,
            "status": "human_wait",
            "message": "Primary approval recorded; awaiting secondary approval",
            "primary_approver": operator,
        }

    # Final approval — transition to APPROVED_WAITING_PUBLISH (v2)
    record = ReviewRecord(
        id=_new_id("rev"),
        task_id=task_id,
        reviewer=operator,
        decision="APPROVE",
        reason=None,
        target_node_index=None,
        revised_variables=None,
        publish_mode=publish_mode,
        scheduled_at=scheduled_at,
        is_dual_approval=requires_dual,
        dual_approver=history[0].reviewer if history and requires_dual else None,
        created_at=_now(),
    )
    _review_db.append(record)

    # v2: Transition to APPROVED_WAITING_PUBLISH instead of RUNNING
    await task_hub.transition_task_with_update(
        db,
        task_id,
        "approved_waiting_publish",
        review_decision="APPROVE",
        reviewed_at=_now(),
        reviewer=operator,
    )

    # Resume workflow execution to drive publisher node after publish confirmation
    t = await task_hub.get_task(db, task_id)
    if t and t.execution_id:
        await task_hub.resume_workflow_execution(db, t)

    return {
        "task_id": task_id,
        "status": "approved_waiting_publish",
        "message": "审核已通过，请前往审核发布中心确认发布",
        "approver": operator,
    }


async def reject_task(
    db: Any,
    task_id: str,
    operator: str,
    reason: str,
) -> Optional[Dict[str, Any]]:
    t = await task_hub.get_task(db, task_id)
    if not t:
        return None
    if t.status != task_hub.TaskStatus.HUMAN_WAIT:
        raise ValueError("Task is not in HUMAN_WAIT status")

    record = ReviewRecord(
        id=_new_id("rev"),
        task_id=task_id,
        reviewer=operator,
        decision="REJECT",
        reason=reason,
        target_node_index=None,
        revised_variables=None,
        publish_mode=None,
        scheduled_at=None,
        is_dual_approval=False,
        dual_approver=None,
        created_at=_now(),
    )
    _review_db.append(record)

    await task_hub.transition_task_with_update(
        db,
        task_id,
        "failed",
        review_decision="REJECT",
        reviewed_at=_now(),
        reviewer=operator,
        review_reason=reason,
    )

    return {
        "task_id": task_id,
        "status": "REJECTED",
        "reason": reason,
        "reviewer": operator,
    }


async def revise_task(
    db: Any,
    task_id: str,
    operator: str,
    target_node_index: int,
    revised_variables: Dict[str, Any],
    reason: str = "",
) -> Optional[Dict[str, Any]]:
    t = await task_hub.get_task(db, task_id)
    if not t:
        return None
    if t.status != task_hub.TaskStatus.HUMAN_WAIT:
        raise ValueError("Task is not in HUMAN_WAIT status")

    record = ReviewRecord(
        id=_new_id("rev"),
        task_id=task_id,
        reviewer=operator,
        decision="REVISE",
        reason=reason,
        target_node_index=target_node_index,
        revised_variables=revised_variables,
        publish_mode=None,
        scheduled_at=None,
        is_dual_approval=False,
        dual_approver=None,
        created_at=_now(),
    )
    _review_db.append(record)

    # Update task variables and transition to CONFIGURING
    await task_hub.update_task(
        db,
        task_id,
        prompt_variables={**t.prompt_variables, **revised_variables},
        review_decision="REVISE",
        reviewed_at=_now(),
        reviewer=operator,
        review_reason=reason,
    )
    await task_hub.transition_task(db, task_id, "configuring")

    return {
        "task_id": task_id,
        "status": "REVISED",
        "target_node_index": target_node_index,
        "revised_variables": revised_variables,
        "reviewer": operator,
    }


# ─── Review History ───

async def get_review_history(
    db: Any,
    task_id: str,
) -> List[ReviewRecord]:
    return [r for r in _review_db if r.task_id == task_id]


def get_all_reviews(
    reviewer: Optional[str] = None,
    decision: Optional[str] = None,
    limit: int = 100,
) -> List[ReviewRecord]:
    results = _review_db[:]
    if reviewer:
        results = [r for r in results if r.reviewer == reviewer]
    if decision:
        results = [r for r in results if r.decision == decision]
    return results[-limit:]


# ─── Statistics ───

async def get_review_stats(
    db: Any,
) -> Dict[str, Any]:
    total = len(_review_db)
    approved = sum(1 for r in _review_db if r.decision == "APPROVE")
    rejected = sum(1 for r in _review_db if r.decision == "REJECT")
    revised = sum(1 for r in _review_db if r.decision == "REVISE")
    pending = len(await task_hub.list_tasks(db, status="human_wait"))
    return {
        "total_reviews": total,
        "approved": approved,
        "rejected": rejected,
        "revised": revised,
        "pending": pending,
    }


# ─── Clear stores (for testing) ───

def _clear_stores():
    _review_db.clear()
