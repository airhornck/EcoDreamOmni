"""Tests for Battle Report Generate Skill — v4.0 Phase 1 P1-3."""

import pytest
from sqlalchemy import delete

from src.skills.battle_report_generate import (
    generate_battle_report,
    generate_battle_report_for_content,
)
from src.models.note_engagement_orm import NoteEngagementORM
from src.models.publish_task_orm import PublishTaskORM


@pytest.mark.asyncio
async def test_generate_battle_report_empty(db):
    """Test battle report with no data."""
    # Clean up
    await db.execute(delete(NoteEngagementORM))
    await db.commit()

    report = await generate_battle_report(db, period_days=7)
    assert report.report_id.startswith("br_")
    assert "暂无互动数据" in report.summary
    assert len(report.recommendations) > 0


@pytest.mark.asyncio
async def test_generate_battle_report_with_data(db):
    """Test battle report with engagement data."""
    # Clean up
    await db.execute(delete(NoteEngagementORM))
    await db.commit()

    # Insert mock engagement data
    for i in range(5):
        eng = NoteEngagementORM(
            id=f"ne_br_{i}",
            publish_task_id=f"pt_br_{i}",
            account_id="acc_br",
            platform_post_id=f"note_br_{i}",
            likes=200 + i * 100,
            comments=30 + i * 20,
            saves=50 + i * 30,
            shares=10 + i * 5,
            views=2000 + i * 1000,
            fetch_status="success",
        )
        db.add(eng)
    await db.commit()

    report = await generate_battle_report(db, account_id="acc_br", period_days=7)
    assert report.report_id.startswith("br_")
    assert "近7日共发布" in report.summary
    assert len(report.highlights) > 0
    assert len(report.recommendations) > 0
    assert report.raw_data["record_count"] == 5


@pytest.mark.asyncio
async def test_generate_battle_report_for_content(db):
    """Test battle report for specific content."""
    # Clean up ALL records with same draft_id / publish_task_id to avoid stale data
    await db.execute(delete(NoteEngagementORM).where(NoteEngagementORM.publish_task_id == "pt_content_001"))
    await db.execute(delete(PublishTaskORM).where(PublishTaskORM.draft_id == "draft_content_001"))
    await db.commit()

    # Create publish task
    task = PublishTaskORM(
        id="pt_content_001",
        draft_id="draft_content_001",
        account_id="acc_001",
        platform="xhs",
        status="published",
        platform_post_id="note_content_001",
    )
    db.add(task)

    # Create engagement
    eng = NoteEngagementORM(
        id="ne_content_001",
        publish_task_id="pt_content_001",
        account_id="acc_001",
        platform_post_id="note_content_001",
        likes=500,
        comments=80,
        saves=120,
        shares=20,
        views=5000,
        fetch_status="success",
    )
    db.add(eng)
    await db.commit()

    report = await generate_battle_report_for_content(db, content_id="draft_content_001")
    assert report is not None
    assert report.report_id.startswith("br_")
    assert "draft_content_001" in report.title


@pytest.mark.asyncio
async def test_generate_battle_report_for_content_not_found(db):
    """Test battle report for non-existent content."""
    report = await generate_battle_report_for_content(db, content_id="nonexistent")
    assert report is None
