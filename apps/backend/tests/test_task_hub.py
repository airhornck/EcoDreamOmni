"""Tests for TaskHub (Phase 2 / PRD V2.6 §10.3).

Red-Green TDD for:
  - Task creation (DB-first with L1 cache)
  - State machine transitions (DRAFT→...→COMPLETED/FAILED/CANCELLED/HUMAN_WAIT)
  - Batch tasks with parent/child
  - Retry logic
  - Human-in-the-loop interface
  - New fields: persona_story_id, node_id, content_series_id
"""

import pytest
import pytest_asyncio
import sys
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.models.task_orm import TaskORM
from src.services import task_hub as th
from src.services.task_hub import TaskStatus, HumanDecision
from src.services import workflow_engine as we

# Load workflow engine presets before tests
we.load_presets()


def _human_approval_index(template_id: str) -> int:
    """Return the node index of the first HUMAN_APPROVAL node in a template."""
    tmpl = we.get_template(template_id)
    for node in tmpl.nodes:
        if node.node_type == we.NodeType.HUMAN_APPROVAL:
            return node.node_index
    raise ValueError(f"No HUMAN_APPROVAL node in template {template_id}")


pytestmark = pytest.mark.asyncio(loop_scope="function")


async def _clear_tasks_db(db: AsyncSession):
    """Clear both PostgreSQL table and in-memory cache."""
    await db.execute(delete(TaskORM))
    await db.commit()
    th._clear_stores()


@pytest_asyncio.fixture(autouse=True)
async def clear_db(db: AsyncSession):
    await _clear_tasks_db(db)
    yield
    await _clear_tasks_db(db)


# ─── 1. Task Creation ───

async def test_create_task(db: AsyncSession):
    t = await th.create_task(
        db=db,
        name="Daily Post",
        workflow_template_id="wf_001",
        workflow_version=1,
        account_id="acc_001",
        persona_id="pers_001",
        prompt_variables={"topic": "cats"},
        created_by="alice",
    )
    assert t.status == TaskStatus.DRAFT
    assert t.prompt_variables["topic"] == "cats"
    # Verify persisted to DB
    fetched = await th.get_task(db, t.id)
    assert fetched is not None
    assert fetched.name == "Daily Post"


async def test_create_task_with_new_fields(db: AsyncSession):
    t = await th.create_task(
        db=db,
        name="Story Post",
        workflow_template_id="wf_001",
        workflow_version=1,
        account_id="acc_001",
        persona_id="pers_001",
        persona_story_id="story_001",
        node_id="node_001",
        content_series_id="series_001",
    )
    assert t.persona_story_id == "story_001"
    assert t.node_id == "node_001"
    assert t.content_series_id == "series_001"
    fetched = await th.get_task(db, t.id)
    assert fetched.persona_story_id == "story_001"


# ─── 2. State Machine Transitions ───

async def test_draft_to_configuring_to_queued(db: AsyncSession):
    t = await th.create_task(db, "T", "wf", 1, "a", "p")
    await th.configure(db, t.id)
    assert (await th.get_task(db, t.id)).status == TaskStatus.CONFIGURING
    await th.queue(db, t.id)
    assert (await th.get_task(db, t.id)).status == TaskStatus.QUEUED


async def test_queued_to_running_to_completed(db: AsyncSession):
    t = await th.create_task(db, "T", "wf", 1, "a", "p")
    await th.configure(db, t.id)
    await th.queue(db, t.id)
    await th.start(db, t.id)
    assert (await th.get_task(db, t.id)).status == TaskStatus.RUNNING
    await th.complete(db, t.id)
    assert (await th.get_task(db, t.id)).status == TaskStatus.COMPLETED
    assert (await th.get_task(db, t.id)).completed_at is not None


async def test_running_to_paused_to_running(db: AsyncSession):
    t = await th.create_task(db, "T", "wf", 1, "a", "p")
    await th.configure(db, t.id)
    await th.queue(db, t.id)
    await th.start(db, t.id)
    await th.pause(db, t.id)
    assert (await th.get_task(db, t.id)).status == TaskStatus.PAUSED
    await th.resume(db, t.id)
    assert (await th.get_task(db, t.id)).status == TaskStatus.RUNNING


async def test_running_to_human_wait_to_approve(db: AsyncSession):
    t = await th.create_task(db, "T", "wf", 1, "a", "p")
    await th.configure(db, t.id)
    await th.queue(db, t.id)
    await th.start(db, t.id)
    await th.wait_human(db, t.id)
    assert (await th.get_task(db, t.id)).status == TaskStatus.HUMAN_WAIT
    await th.approve(db, t.id)
    assert (await th.get_task(db, t.id)).status == TaskStatus.RUNNING


async def test_running_to_human_wait_to_reject(db: AsyncSession):
    t = await th.create_task(db, "T", "wf", 1, "a", "p")
    await th.configure(db, t.id)
    await th.queue(db, t.id)
    await th.start(db, t.id)
    await th.wait_human(db, t.id)
    await th.reject(db, t.id)
    assert (await th.get_task(db, t.id)).status == TaskStatus.FAILED


async def test_invalid_transition_raises(db: AsyncSession):
    t = await th.create_task(db, "T", "wf", 1, "a", "p")
    with pytest.raises(ValueError):
        await th.complete(db, t.id)  # DRAFT -> COMPLETED is invalid


async def test_cancel_from_multiple_states(db: AsyncSession):
    t = await th.create_task(db, "T", "wf", 1, "a", "p")
    await th.cancel(db, t.id)
    assert (await th.get_task(db, t.id)).status == TaskStatus.CANCELLED

    t2 = await th.create_task(db, "T2", "wf", 1, "a", "p")
    await th.configure(db, t2.id)
    await th.queue(db, t2.id)
    await th.start(db, t2.id)
    await th.pause(db, t2.id)
    await th.cancel(db, t2.id)
    assert (await th.get_task(db, t2.id)).status == TaskStatus.CANCELLED


# ─── 3. Retry Logic ───

async def test_retry_resets_node_index(db: AsyncSession):
    t = await th.create_task(db, "T", "wf", 1, "a", "p")
    await th.configure(db, t.id)
    await th.queue(db, t.id)
    await th.start(db, t.id)
    await th.fail(db, t.id)
    assert (await th.get_task(db, t.id)).status == TaskStatus.FAILED
    await th.retry(db, t.id)
    assert (await th.get_task(db, t.id)).status == TaskStatus.QUEUED
    assert (await th.get_task(db, t.id)).current_node_index == 0


# ─── 4. Batch Tasks ───

async def test_create_batch(db: AsyncSession):
    batch = await th.create_batch(
        db=db,
        name_prefix="Holiday Campaign",
        workflow_template_id="wf_001",
        workflow_version=1,
        assignments=[
            {"account_id": "acc_1", "persona_id": "p_1", "priority": 80},
            {"account_id": "acc_2", "persona_id": "p_2", "priority": 60},
        ],
        created_by="alice",
    )
    assert len(batch) == 3  # 1 parent + 2 children
    parent = batch[0]
    assert parent.parent_task_id is None
    children = batch[1:]
    assert all(c.parent_task_id == parent.id for c in children)
    assert children[0].priority == 80


async def test_batch_progress(db: AsyncSession):
    batch = await th.create_batch(
        db=db,
        name_prefix="Test",
        workflow_template_id="wf_001",
        workflow_version=1,
        assignments=[
            {"account_id": "a1", "persona_id": "p1"},
            {"account_id": "a2", "persona_id": "p2"},
        ],
        created_by="alice",
    )
    parent = batch[0]
    child1, child2 = batch[1], batch[2]

    await th.configure(db, child1.id)
    await th.queue(db, child1.id)
    await th.start(db, child1.id)
    await th.complete(db, child1.id)

    await th.configure(db, child2.id)
    await th.queue(db, child2.id)
    await th.start(db, child2.id)
    await th.fail(db, child2.id)

    progress = await th.get_batch_progress(db, parent.id)
    assert progress["total"] == 2
    assert progress["completed"] == 1
    assert progress["failed"] == 1
    assert progress["progress_pct"] == 100.0


# ─── 5. Human-in-the-Loop Interface ───

async def test_submit_human_decision_approve(db: AsyncSession):
    t = await th.create_task(db, "T", "wf", 1, "a", "p")
    await th.configure(db, t.id)
    await th.queue(db, t.id)
    await th.start(db, t.id)
    await th.wait_human(db, t.id)
    result = await th.submit_human_decision(db, t.id, HumanDecision.APPROVE.value, "bob", "Looks good")
    assert result.status == TaskStatus.RUNNING
    decisions = th.get_human_decisions(t.id)
    assert len(decisions) == 1
    assert decisions[0].human_decision == HumanDecision.APPROVE.value


async def test_submit_human_decision_reject(db: AsyncSession):
    t = await th.create_task(db, "T", "wf", 1, "a", "p")
    await th.configure(db, t.id)
    await th.queue(db, t.id)
    await th.start(db, t.id)
    await th.wait_human(db, t.id)
    result = await th.submit_human_decision(db, t.id, HumanDecision.REJECT.value, "bob", "Bad quality")
    assert result.status == TaskStatus.FAILED


async def test_submit_human_decision_revise(db: AsyncSession):
    t = await th.create_task(db, "T", "wf", 1, "a", "p")
    await th.configure(db, t.id)
    await th.queue(db, t.id)
    await th.start(db, t.id)
    await th.wait_human(db, t.id)
    result = await th.submit_human_decision(db, t.id, HumanDecision.REVISE.value, "bob", "Fix typo")
    assert result.status == TaskStatus.CONFIGURING


async def test_human_decision_non_human_wait_raises(db: AsyncSession):
    t = await th.create_task(db, "T", "wf", 1, "a", "p")
    with pytest.raises(ValueError):
        await th.submit_human_decision(db, t.id, HumanDecision.APPROVE.value, "bob")


# ─── 6. Cache warm / list_tasks ───

async def test_list_tasks_with_filter(db: AsyncSession):
    t1 = await th.create_task(db, "T1", "wf", 1, "a1", "p")
    await th.configure(db, t1.id)
    await th.queue(db, t1.id)
    await th.start(db, t1.id)

    t2 = await th.create_task(db, "T2", "wf", 1, "a2", "p")
    await th.configure(db, t2.id)
    await th.queue(db, t2.id)
    await th.start(db, t2.id)

    t3 = await th.create_task(db, "T3", "wf", 1, "a1", "p")

    all_tasks = await th.list_tasks(db)
    assert len(all_tasks) >= 3

    running = await th.list_tasks(db, status="running")
    assert len(running) >= 2
    assert all(t.status == TaskStatus.RUNNING for t in running)

    a1_tasks = await th.list_tasks(db, account_id="a1")
    assert len(a1_tasks) >= 2


async def test_list_tasks_no_filter_after_create(db: AsyncSession):
    """创建任务后立即无过滤列表，应能正确读到新任务（回归测试：响应格式解析）。"""
    t = await th.create_task(db, "NewTask", "wf", 1, "a", "p")
    tasks = await th.list_tasks(db)
    assert len(tasks) >= 1
    ids = [task.id for task in tasks]
    assert t.id in ids


async def test_list_tasks_empty_parent_task_id(db: AsyncSession):
    """parent_task_id 传空字符串时不应过滤掉任何任务（回归测试：过滤条件边界）。"""
    t = await th.create_task(db, "TaskNoParent", "wf", 1, "a", "p")
    tasks = await th.list_tasks(db, parent_task_id="")
    assert len(tasks) >= 1
    ids = [task.id for task in tasks]
    assert t.id in ids


# ─── 7. Update & Delete ───

async def test_update_task(db: AsyncSession):
    t = await th.create_task(db, "T", "wf", 1, "a", "p")
    updated = await th.update_task(db, t.id, name="Updated", priority=99)
    assert updated.name == "Updated"
    assert updated.priority == 99
    fetched = await th.get_task(db, t.id)
    assert fetched.name == "Updated"


async def test_delete_task(db: AsyncSession):
    t = await th.create_task(db, "T", "wf", 1, "a", "p")
    ok = await th.delete_task(db, t.id)
    assert ok is True
    assert await th.get_task(db, t.id) is None


# ─── 8. Workflow Integration ───

async def test_start_workflow_drives_to_human_wait(db: AsyncSession):
    """Start workflow on standard template should drive to HUMAN_WAIT (node 6)."""
    t = await th.create_task(
        db=db,
        name="Workflow Task",
        workflow_template_id="content_creation_standard",
        workflow_version=1,
        account_id="acc_001",
        persona_id="pers_001",
    )
    assert t.status == TaskStatus.DRAFT
    assert t.execution_id is None

    t = await th.start_workflow(db, t.id)
    assert t is not None
    assert t.status == TaskStatus.HUMAN_WAIT
    assert t.execution_id is not None
    assert t.current_node_index == _human_approval_index("content_creation_standard")


async def test_start_workflow_light_template(db: AsyncSession):
    """Light template has HUMAN_APPROVAL at a fixed index."""
    t = await th.create_task(
        db=db,
        name="Light Task",
        workflow_template_id="content_creation_light",
        workflow_version=1,
        account_id="acc_001",
        persona_id="pers_001",
    )
    t = await th.start_workflow(db, t.id)
    assert t.status == TaskStatus.HUMAN_WAIT
    assert t.current_node_index == _human_approval_index("content_creation_light")


async def test_human_decision_approve_resumes_workflow(db: AsyncSession):
    """APPROVE decision should resume workflow and drive to COMPLETED."""
    t = await th.create_task(
        db=db,
        name="Approve Task",
        workflow_template_id="content_creation_light",
        workflow_version=1,
        account_id="acc_001",
        persona_id="pers_001",
    )
    t = await th.start_workflow(db, t.id)
    assert t.status == TaskStatus.HUMAN_WAIT

    result = await th.submit_human_decision(db, t.id, HumanDecision.APPROVE.value, "bob", "Good")
    assert result.status == TaskStatus.COMPLETED


async def test_start_workflow_idempotent(db: AsyncSession):
    """Starting workflow twice should raise error."""
    t = await th.create_task(
        db=db,
        name="Dup Task",
        workflow_template_id="content_creation_light",
        workflow_version=1,
        account_id="acc_001",
        persona_id="pers_001",
    )
    await th.start_workflow(db, t.id)
    with pytest.raises(ValueError):
        await th.start_workflow(db, t.id)


async def test_start_workflow_injects_structured_data(db: AsyncSession):
    """🔴 Workflow execution should inject structured content, topic report, compliance, and prediction into prompt_variables."""
    t = await th.create_task(
        db=db,
        name="Structured Data Task",
        workflow_template_id="content_creation_standard",
        workflow_version=1,
        account_id="acc_001",
        persona_id="pers_001",
    )
    t = await th.start_workflow(db, t.id)
    assert t.status == TaskStatus.HUMAN_WAIT

    pv = t.prompt_variables
    # Structured content
    assert "generated_content" in pv
    assert pv["generated_content"]["title"] is not None
    assert pv["generated_content"]["body"] is not None
    assert pv["generated_content"]["tags"] is not None
    assert pv["generated_content"]["cover_image_url"] is not None

    # Topic report
    assert "topic_report" in pv
    assert pv["topic_report"]["selected_topic"] is not None
    assert len(pv["topic_report"]["topics"]) >= 1

    # Compliance
    assert "compliance_result" in pv
    assert pv["compliance_result"]["level"] == "pass"

    # Prediction
    assert "prediction_result" in pv
    assert "engagement_interval" in pv["prediction_result"]
    assert "likes" in pv["prediction_result"]["engagement_interval"]

    # Quality score
    assert "quality_score" in pv
    assert "overall" in pv["quality_score"]

    # Draft ID
    assert "draft_id" in pv
    assert "content_preview" in pv
