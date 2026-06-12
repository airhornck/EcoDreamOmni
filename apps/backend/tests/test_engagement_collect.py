"""Tests for Engagement Collect Function — v4.0 Phase 1 P1-3."""

import pytest
from sqlalchemy import delete

from src.functions.engagement_collect import (
    collect_engagement_for_task,
    get_engagement_summary,
)
from src.models.note_engagement_orm import NoteEngagementORM
from src.models.publish_task_orm import PublishTaskORM


@pytest.mark.asyncio
async def test_collect_engagement_for_task(db):
    """Test collecting engagement for a single task."""
    # Clean up
    await db.execute(delete(NoteEngagementORM).where(NoteEngagementORM.publish_task_id == "pt_test_001"))
    await db.execute(delete(PublishTaskORM).where(PublishTaskORM.id == "pt_test_001"))
    await db.commit()

    # Need a publish task first
    task = PublishTaskORM(
        id="pt_test_001",
        draft_id="draft_001",
        account_id="acc_001",
        platform="xhs",
        status="published",
        platform_post_id="note_abc123",
    )
    db.add(task)
    await db.commit()

    result = await collect_engagement_for_task(
        db=db,
        publish_task_id="pt_test_001",
        platform_post_id="note_abc123",
        account_id="acc_001",
    )

    assert result is not None
    assert result.publish_task_id == "pt_test_001"
    assert result.account_id == "acc_001"
    assert result.fetch_status == "success"
    assert result.likes is not None
    assert result.likes >= 0


@pytest.mark.asyncio
async def test_get_engagement_summary_empty(db):
    """Test summary with no data."""
    # Clean up all test engagement data
    await db.execute(delete(NoteEngagementORM))
    await db.commit()

    summary = await get_engagement_summary(db, days=30)
    assert summary["has_data"] is False
    assert summary["total_records"] == 0


@pytest.mark.asyncio
async def test_get_engagement_summary_with_data(db):
    """Test summary with data."""
    # Clean up first
    await db.execute(delete(NoteEngagementORM))
    await db.commit()

    # Insert mock engagement data
    for i in range(3):
        eng = NoteEngagementORM(
            id=f"ne_test_{i}",
            publish_task_id=f"pt_{i}",
            account_id="acc_001",
            platform_post_id=f"note_{i}",
            likes=100 + i * 50,
            comments=20 + i * 10,
            saves=30 + i * 15,
            shares=5 + i,
            views=1000 + i * 500,
            fetch_status="success",
        )
        db.add(eng)
    await db.commit()

    summary = await get_engagement_summary(db, account_id="acc_001", days=30)
    assert summary["has_data"] is True
    assert summary["total_records"] == 3
    assert summary["avg_likes"] > 0
