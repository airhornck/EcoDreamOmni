"""TimelineLibrary Function ORM tests — W14 Red-Green.

Aligned with PRD V3.1 §TimelineLibrary / TASK_V2.7.1 FUNC-4.
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone, timedelta

from src.services import timeline_library_function as tlf
from src.services import cron_hub as ch

pytestmark = pytest.mark.asyncio(loop_scope="function")


@pytest_asyncio.fixture
async def db_session(db, skip_if_no_db):
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy.pool import NullPool
    from src.models.timeline_library_orm import TimelineEventORM

    # Ensure table exists with latest schema (in case lifespan hasn't run)
    test_engine = create_async_engine(
        "postgresql+asyncpg://ecodream:ecodream@localhost:5432/ecodream",
        poolclass=NullPool,
        echo=False,
    )
    async with test_engine.begin() as conn:
        await conn.run_sync(TimelineEventORM.__table__.create, checkfirst=True)
        await conn.execute(text("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'timeline_events' AND column_name = 'cron_job_id'
                ) THEN
                    ALTER TABLE timeline_events ADD COLUMN cron_job_id VARCHAR(64);
                END IF;
            END $$;
        """))
    await test_engine.dispose()
    ch._clear_stores()
    return db


# =============================================================================
# TL-1: 季节事件CRUD
# =============================================================================

async def test_create_season_event(db_session: AsyncSession):
    """🔴 创建季节事件 — 驱虫季."""
    start = datetime.now(timezone.utc)
    end = start + timedelta(days=30)
    event = await tlf.create_event(
        db=db_session,
        name="春季驱虫季",
        event_type="season",
        start_date=start.isoformat(),
        end_date=end.isoformat(),
        description="每年3-4月，宠物驱虫高峰期",
        recurring=True,
        cron_expression="0 0 1 3 *",  # 每年3月1日
        prohibited_claims=["一次性驱虫终身免疫"],
        is_commercial=False,
    )
    assert event.id is not None
    assert event.event_type == "season"
    assert event.recurring is True


async def test_create_commercial_event_triggers_review(db_session: AsyncSession):
    """🔴 商业主题事件自动标记 — 触发额外审核."""
    start = datetime.now(timezone.utc)
    end = start + timedelta(days=7)
    event = await tlf.create_event(
        db=db_session,
        name="618大促",
        event_type="campaign",
        start_date=start.isoformat(),
        end_date=end.isoformat(),
        is_commercial=True,
    )
    assert event.is_commercial is True


# =============================================================================
# TL-2: 时间范围查询
# =============================================================================

async def test_get_active_events_for_date(db_session: AsyncSession):
    """🔴 按日期查询生效事件."""
    today = datetime.now(timezone.utc)
    await tlf.create_event(
        db=db_session,
        name="当前事件",
        event_type="season",
        start_date=(today - timedelta(days=5)).isoformat(),
        end_date=(today + timedelta(days=5)).isoformat(),
    )
    await tlf.create_event(
        db=db_session,
        name="未来事件",
        event_type="season",
        start_date=(today + timedelta(days=10)).isoformat(),
        end_date=(today + timedelta(days=20)).isoformat(),
    )
    active = await tlf.get_active_events_for_date(db_session, today)
    names = [e.name for e in active]
    assert "当前事件" in names
    assert "未来事件" not in names


async def test_list_events_by_date_range(db_session: AsyncSession):
    """🔴 列表按时间范围筛选."""
    today = datetime.now(timezone.utc)
    await tlf.create_event(
        db=db_session,
        name="范围内",
        event_type="season",
        start_date=(today - timedelta(days=10)).isoformat(),
        end_date=(today + timedelta(days=10)).isoformat(),
    )
    result = await tlf.list_events(
        db=db_session,
        from_date=(today - timedelta(days=5)).isoformat(),
        to_date=(today + timedelta(days=5)).isoformat(),
    )
    assert result["total"] >= 1


# =============================================================================
# TL-3: 商业事件查询
# =============================================================================

async def test_get_commercial_events(db_session: AsyncSession):
    """🔴 查询商业主题事件 — 供审核流程调用."""
    today = datetime.now(timezone.utc)
    await tlf.create_event(
        db=db_session,
        name="双11",
        event_type="campaign",
        start_date=(today - timedelta(days=1)).isoformat(),
        end_date=(today + timedelta(days=10)).isoformat(),
        is_commercial=True,
    )
    commercial = await tlf.get_commercial_events(db_session)
    assert len(commercial) >= 1
    assert any(e.name == "双11" for e in commercial)


# =============================================================================
# TL-4: CronHub集成字段
# =============================================================================

async def test_cron_expression_storage(db_session: AsyncSession):
    """🔴 cron表达式存储 — 与CronHub集成."""
    event = await tlf.create_event(
        db=db_session,
        name="定时事件",
        event_type="custom",
        start_date=datetime.now(timezone.utc).isoformat(),
        end_date=(datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
        cron_expression="0 9 * * 1",  # 每周一9点
    )
    assert event.cron_expression == "0 9 * * 1"


# =============================================================================
# TL-5: CRUD lifecycle
# =============================================================================

async def test_event_update_and_delete(db_session: AsyncSession):
    """🔴 更新与删除."""
    event = await tlf.create_event(
        db=db_session,
        name="可改事件",
        event_type="custom",
        start_date=datetime.now(timezone.utc).isoformat(),
        end_date=(datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
    )
    updated = await tlf.update_event(
        db_session, str(event.id), name="已改名"
    )
    assert updated is not None
    assert updated.name == "已改名"

    deleted = await tlf.delete_event(db_session, str(event.id))
    assert deleted is True


async def test_clear_timeline_library(db_session: AsyncSession):
    """🔴 清空."""
    await tlf.create_event(
        db=db_session,
        name="清空测试",
        event_type="custom",
        start_date=datetime.now(timezone.utc).isoformat(),
        end_date=(datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
    )
    await tlf.clear_timeline_library(db_session)
    result = await tlf.list_events(db_session)
    assert result["total"] == 0


# =============================================================================
# TL-6: CronHub binding
# =============================================================================

async def test_create_event_creates_cron_job(db_session: AsyncSession):
    """🔴 创建带cron表达式的事件应自动创建CronHub job."""
    start = datetime.now(timezone.utc)
    event = await tlf.create_event(
        db=db_session,
        name="每日提醒",
        event_type="custom",
        start_date=start.isoformat(),
        end_date=(start + timedelta(days=1)).isoformat(),
        cron_expression="0 9 * * *",
    )
    assert event.cron_job_id is not None
    assert event.cron_job_id.startswith("job_")
    job = ch.get_job(event.cron_job_id)
    assert job is not None
    assert job.schedule == "0 9 * * *"
    assert job.name == "Timeline:每日提醒"

    # event_to_dict should include cron_job_id
    d = tlf.event_to_dict(event)
    assert d["cron_job_id"] == event.cron_job_id


async def test_update_event_cron_updates_job(db_session: AsyncSession):
    """🔴 更新cron表达式应同步更新CronHub job."""
    start = datetime.now(timezone.utc)
    event = await tlf.create_event(
        db=db_session,
        name="每周提醒",
        event_type="custom",
        start_date=start.isoformat(),
        end_date=(start + timedelta(days=1)).isoformat(),
        cron_expression="0 9 * * 1",
    )
    old_job_id = event.cron_job_id

    updated = await tlf.update_event(
        db_session, str(event.id), cron_expression="0 9 * * 2"
    )
    assert updated is not None
    assert updated.cron_job_id is not None
    assert updated.cron_job_id != old_job_id
    assert ch.get_job(old_job_id) is None  # old job deleted
    assert ch.get_job(updated.cron_job_id).schedule == "0 9 * * 2"


async def test_delete_event_removes_cron_job(db_session: AsyncSession):
    """🔴 删除事件应清理关联的CronHub job."""
    start = datetime.now(timezone.utc)
    event = await tlf.create_event(
        db=db_session,
        name="临时事件",
        event_type="custom",
        start_date=start.isoformat(),
        end_date=(start + timedelta(days=1)).isoformat(),
        cron_expression="0 9 * * *",
    )
    job_id = event.cron_job_id
    assert ch.get_job(job_id) is not None

    await tlf.delete_event(db_session, str(event.id))
    assert ch.get_job(job_id) is None


async def test_create_event_without_cron_no_job(db_session: AsyncSession):
    """🔴 无cron表达式的事件不创建CronHub job."""
    start = datetime.now(timezone.utc)
    event = await tlf.create_event(
        db=db_session,
        name="普通事件",
        event_type="custom",
        start_date=start.isoformat(),
        end_date=(start + timedelta(days=1)).isoformat(),
    )
    assert event.cron_job_id is None
    assert tlf.event_to_dict(event)["cron_job_id"] is None
