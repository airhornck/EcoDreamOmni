"""
v2 状态机扩展测试 —— APPROVED_WAITING_PUBLISH 中间状态。

Red-Green TDD for:
  - HUMAN_WAIT → APPROVED_WAITING_PUBLISH 转换
  - APPROVED_WAITING_PUBLISH → RUNNING 转换
  - APPROVED_WAITING_PUBLISH → CANCELLED 转换
  - 无效转换拒绝
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.task_orm import TaskORM
from src.services import task_hub as th
from src.services.task_hub import TaskStatus

pytestmark = pytest.mark.asyncio(loop_scope="function")


@pytest.fixture(autouse=True)
async def clear_db(db: AsyncSession):
    await db.execute(delete(TaskORM))
    await db.commit()
    yield


# ─── 1. APPROVED_WAITING_PUBLISH 状态转换 ───


async def test_human_wait_to_approved_waiting_publish(db: AsyncSession):
    """🔴 HUMAN_WAIT → APPROVED_WAITING_PUBLISH 是合法转换。"""
    t = await th.create_task(db, "T", "wf", 1, "a", "p")
    await th.configure(db, t.id)
    await th.queue(db, t.id)
    await th.start(db, t.id)
    await th.wait_human(db, t.id)
    assert (await th.get_task(db, t.id)).status == TaskStatus.HUMAN_WAIT

    result = await th.transition_task(db, t.id, "approved_waiting_publish")
    assert result.status == TaskStatus.APPROVED_WAITING_PUBLISH


async def test_approved_waiting_publish_to_running(db: AsyncSession):
    """🔴 APPROVED_WAITING_PUBLISH → RUNNING 是合法转换。"""
    t = await th.create_task(db, "T", "wf", 1, "a", "p")
    await th.configure(db, t.id)
    await th.queue(db, t.id)
    await th.start(db, t.id)
    await th.wait_human(db, t.id)
    await th.transition_task(db, t.id, "approved_waiting_publish")

    result = await th.transition_task(db, t.id, "running")
    assert result.status == TaskStatus.RUNNING


async def test_approved_waiting_publish_to_cancelled(db: AsyncSession):
    """🔴 APPROVED_WAITING_PUBLISH → CANCELLED 是合法转换。"""
    t = await th.create_task(db, "T", "wf", 1, "a", "p")
    await th.configure(db, t.id)
    await th.queue(db, t.id)
    await th.start(db, t.id)
    await th.wait_human(db, t.id)
    await th.transition_task(db, t.id, "approved_waiting_publish")

    result = await th.transition_task(db, t.id, "cancelled")
    assert result.status == TaskStatus.CANCELLED


# ─── 2. 无效转换拒绝 ───


async def test_draft_to_approved_waiting_publish_is_invalid(db: AsyncSession):
    """🔴 DRAFT → APPROVED_WAITING_PUBLISH 是非法转换。"""
    t = await th.create_task(db, "T", "wf", 1, "a", "p")
    with pytest.raises(ValueError):
        await th.transition_task(db, t.id, "approved_waiting_publish")


async def test_running_to_approved_waiting_publish_is_invalid(db: AsyncSession):
    """🔴 RUNNING → APPROVED_WAITING_PUBLISH 是非法转换（必须经过 HUMAN_WAIT）。"""
    t = await th.create_task(db, "T", "wf", 1, "a", "p")
    await th.configure(db, t.id)
    await th.queue(db, t.id)
    await th.start(db, t.id)
    with pytest.raises(ValueError):
        await th.transition_task(db, t.id, "approved_waiting_publish")


async def test_approved_waiting_publish_to_human_wait_is_invalid(db: AsyncSession):
    """🔴 APPROVED_WAITING_PUBLISH → HUMAN_WAIT 是非法转换。"""
    t = await th.create_task(db, "T", "wf", 1, "a", "p")
    await th.configure(db, t.id)
    await th.queue(db, t.id)
    await th.start(db, t.id)
    await th.wait_human(db, t.id)
    await th.transition_task(db, t.id, "approved_waiting_publish")
    with pytest.raises(ValueError):
        await th.transition_task(db, t.id, "human_wait")


async def test_approved_waiting_publish_to_completed_is_invalid(db: AsyncSession):
    """🔴 APPROVED_WAITING_PUBLISH → COMPLETED 是非法转换。"""
    t = await th.create_task(db, "T", "wf", 1, "a", "p")
    await th.configure(db, t.id)
    await th.queue(db, t.id)
    await th.start(db, t.id)
    await th.wait_human(db, t.id)
    await th.transition_task(db, t.id, "approved_waiting_publish")
    with pytest.raises(ValueError):
        await th.transition_task(db, t.id, "completed")


# ─── 3. transition_task_with_update 原子操作 ───


async def test_transition_with_update_records_review_fields(db: AsyncSession):
    """🔴 transition_task_with_update 可原子性更新审核字段。"""
    t = await th.create_task(db, "T", "wf", 1, "a", "p")
    await th.configure(db, t.id)
    await th.queue(db, t.id)
    await th.start(db, t.id)
    await th.wait_human(db, t.id)

    result = await th.transition_task_with_update(
        db,
        t.id,
        "approved_waiting_publish",
        review_decision="APPROVE",
        reviewer="alice",
        review_reason="内容合规",
    )
    assert result.status == TaskStatus.APPROVED_WAITING_PUBLISH
    assert result.review_decision == "APPROVE"
    assert result.reviewer == "alice"
    assert result.review_reason == "内容合规"


# ─── 4. 完整 v2 审核-发布链路状态转换 ───


async def test_full_v2_review_publish_lifecycle(db: AsyncSession):
    """🔴 完整链路：DRAFT → ... → HUMAN_WAIT → APPROVED_WAITING_PUBLISH → RUNNING → COMPLETED。"""
    t = await th.create_task(db, "T", "wf", 1, "a", "p")
    await th.configure(db, t.id)
    await th.queue(db, t.id)
    await th.start(db, t.id)
    await th.wait_human(db, t.id)

    # 审核通过（v2 新增中间状态）
    await th.transition_task_with_update(
        db,
        t.id,
        "approved_waiting_publish",
        review_decision="APPROVE",
        reviewer="reviewer_1",
    )
    assert (await th.get_task(db, t.id)).status == TaskStatus.APPROVED_WAITING_PUBLISH

    # 发布确认
    await th.transition_task_with_update(
        db,
        t.id,
        "running",
        publish_confirmer="operator_1",
    )
    assert (await th.get_task(db, t.id)).status == TaskStatus.RUNNING

    # 发布完成
    await th.complete(db, t.id)
    assert (await th.get_task(db, t.id)).status == TaskStatus.COMPLETED
