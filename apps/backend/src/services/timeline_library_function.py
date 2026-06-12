"""TimelineLibrary Function — ORM持久化版本 (W14).

季节事件库、产品上市时间线、与CronHub/BrandKnowledge联动.
Aligned with PRD V3.1 §TimelineLibrary / TASK_V2.7.1 FUNC-4.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, delete

from src.models.timeline_library_orm import TimelineEventORM
from src.services import cron_hub


def _now() -> datetime:
    return datetime.now(timezone.utc)


def event_to_dict(event: TimelineEventORM) -> Dict[str, Any]:
    return {
        "id": str(event.id),
        "name": event.name,
        "event_type": event.event_type,
        "description": event.description,
        "start_date": event.start_date.isoformat() if event.start_date else None,
        "end_date": event.end_date.isoformat() if event.end_date else None,
        "recurring": event.recurring,
        "cron_expression": event.cron_expression,
        "cron_job_id": event.cron_job_id,
        "year": event.year,
        "brand_knowledge_ids": event.brand_knowledge_ids or [],
        "product_ids": event.product_ids or [],
        "prohibited_claims": event.prohibited_claims or [],
        "is_commercial": event.is_commercial,
        "status": event.status,
        "priority": event.priority,
        "color_code": event.color_code,
        "created_by": event.created_by,
        "tenant_id": event.tenant_id,
        "created_at": event.created_at.isoformat() if event.created_at else None,
        "updated_at": event.updated_at.isoformat() if event.updated_at else None,
    }


def _parse_dt(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


async def create_event(
    db: AsyncSession,
    name: str,
    event_type: str,
    start_date: str,
    end_date: str,
    description: Optional[str] = None,
    recurring: bool = False,
    cron_expression: Optional[str] = None,
    year: Optional[int] = None,
    brand_knowledge_ids: Optional[List[str]] = None,
    product_ids: Optional[List[str]] = None,
    prohibited_claims: Optional[List[str]] = None,
    is_commercial: bool = False,
    status: str = "ACTIVE",
    priority: int = 0,
    color_code: Optional[str] = None,
    created_by: Optional[str] = None,
    tenant_id: Optional[str] = None,
) -> TimelineEventORM:
    event = TimelineEventORM(
        name=name,
        event_type=event_type,
        description=description,
        start_date=_parse_dt(start_date),
        end_date=_parse_dt(end_date),
        recurring=recurring,
        cron_expression=cron_expression,
        year=year,
        brand_knowledge_ids=brand_knowledge_ids or [],
        product_ids=product_ids or [],
        prohibited_claims=prohibited_claims or [],
        is_commercial=is_commercial,
        status=status,
        priority=priority,
        color_code=color_code,
        created_by=created_by,
        tenant_id=tenant_id,
    )
    db.add(event)
    await db.flush()
    await db.commit()
    await db.refresh(event)

    # Sync to CronHub if cron_expression is provided and valid
    if event.cron_expression and cron_hub.validate_cron(event.cron_expression):
        try:
            job = cron_hub.create_job(
                name=f"Timeline:{event.name}",
                target_type="API",
                target_id="timeline_trigger",
                schedule=event.cron_expression,
                description=f"Auto-created from timeline event {event.id}",
                owner=created_by or "",
            )
            event.cron_job_id = job.id
            await db.commit()
            await db.refresh(event)
        except Exception:
            # Non-blocking: CronHub failure should not prevent timeline creation
            pass

    return event


async def get_event(
    db: AsyncSession, event_id: str
) -> Optional[TimelineEventORM]:
    result = await db.execute(
        select(TimelineEventORM).where(TimelineEventORM.id == event_id)
    )
    return result.scalar_one_or_none()


async def list_events(
    db: AsyncSession,
    event_type: Optional[str] = None,
    status: Optional[str] = "ACTIVE",
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    tenant_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> Dict[str, Any]:
    query = select(TimelineEventORM)
    if event_type:
        query = query.where(TimelineEventORM.event_type == event_type)
    if status:
        query = query.where(TimelineEventORM.status == status)
    if from_date:
        dt = _parse_dt(from_date)
        if dt:
            query = query.where(TimelineEventORM.end_date >= dt)
    if to_date:
        dt = _parse_dt(to_date)
        if dt:
            query = query.where(TimelineEventORM.start_date <= dt)
    if tenant_id:
        query = query.where(TimelineEventORM.tenant_id == tenant_id)

    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar() or 0

    query = (
        query.order_by(desc(TimelineEventORM.start_date))
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(query)
    items = result.scalars().all()

    return {"items": list(items), "total": total, "limit": limit, "offset": offset}


async def update_event(
    db: AsyncSession, event_id: str, **kwargs
) -> Optional[TimelineEventORM]:
    event = await get_event(db, event_id)
    if not event:
        return None

    old_cron = event.cron_expression
    old_job_id = event.cron_job_id

    for key, value in kwargs.items():
        if key in {"start_date", "end_date"} and isinstance(value, str):
            value = _parse_dt(value)
        if key not in {"id", "created_at"} and hasattr(event, key):
            setattr(event, key, value)

    event.updated_at = _now()
    await db.flush()
    await db.commit()

    # Sync CronHub when cron_expression changes
    new_cron = event.cron_expression
    cron_changed = "cron_expression" in kwargs
    if cron_changed:
        if old_job_id:
            try:
                cron_hub.delete_job(old_job_id)
            except Exception:
                pass
            event.cron_job_id = None

        if new_cron and cron_hub.validate_cron(new_cron):
            try:
                job = cron_hub.create_job(
                    name=f"Timeline:{event.name}",
                    target_type="API",
                    target_id="timeline_trigger",
                    schedule=new_cron,
                    description=f"Auto-updated from timeline event {event.id}",
                    owner=event.created_by or "",
                )
                event.cron_job_id = job.id
            except Exception:
                pass

        await db.commit()

    await db.refresh(event)
    return event


async def delete_event(db: AsyncSession, event_id: str) -> bool:
    event = await get_event(db, event_id)
    if not event:
        return False
    if event.cron_job_id:
        try:
            cron_hub.delete_job(event.cron_job_id)
        except Exception:
            pass
    await db.delete(event)
    await db.flush()
    await db.commit()
    return True


async def get_active_events_for_date(
    db: AsyncSession,
    target_date: Optional[datetime] = None,
    tenant_id: Optional[str] = None,
) -> List[TimelineEventORM]:
    """获取指定日期生效的全部事件（含跨季节事件）."""
    if target_date is None:
        target_date = _now()

    query = (
        select(TimelineEventORM)
        .where(TimelineEventORM.start_date <= target_date)
        .where(TimelineEventORM.end_date >= target_date)
        .where(TimelineEventORM.status == "ACTIVE")
    )
    if tenant_id:
        query = query.where(TimelineEventORM.tenant_id == tenant_id)
    query = query.order_by(desc(TimelineEventORM.priority))
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_commercial_events(
    db: AsyncSession,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    tenant_id: Optional[str] = None,
) -> List[TimelineEventORM]:
    """获取商业主题事件 — 供Human-in-the-Loop额外审核流程调用."""
    query = select(TimelineEventORM).where(TimelineEventORM.is_commercial == True)
    if from_date:
        dt = _parse_dt(from_date)
        if dt:
            query = query.where(TimelineEventORM.end_date >= dt)
    if to_date:
        dt = _parse_dt(to_date)
        if dt:
            query = query.where(TimelineEventORM.start_date <= dt)
    if tenant_id:
        query = query.where(TimelineEventORM.tenant_id == tenant_id)
    query = query.where(TimelineEventORM.status == "ACTIVE")
    result = await db.execute(query)
    return list(result.scalars().all())


async def clear_timeline_library(db: AsyncSession) -> None:
    await db.execute(delete(TimelineEventORM))
    await db.commit()
