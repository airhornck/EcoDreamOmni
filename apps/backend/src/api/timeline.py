"""Timeline API — CRUD for timeline events.

Wraps src/services/timeline_library_function.py.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.auth import get_current_user
from src.core.database import get_db
from src.services import timeline_library_function as tlf

router = APIRouter(prefix="/timeline", tags=["timeline"])


class TimelineEventCreate(BaseModel):
    name: str
    event_type: str
    start_date: str
    end_date: str
    description: Optional[str] = None
    recurring: bool = False
    cron_expression: Optional[str] = None
    cron_job_id: Optional[str] = None
    year: Optional[int] = None
    brand_knowledge_ids: List[str] = []
    product_ids: List[str] = []
    prohibited_claims: List[str] = []
    is_commercial: bool = False
    status: str = "ACTIVE"
    priority: int = 0
    color_code: Optional[str] = None


class TimelineEventOut(BaseModel):
    id: str
    name: str
    event_type: str
    description: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    recurring: bool
    cron_expression: Optional[str] = None
    year: Optional[int] = None
    brand_knowledge_ids: List[str] = []
    product_ids: List[str] = []
    prohibited_claims: List[str] = []
    is_commercial: bool
    status: str
    priority: int
    color_code: Optional[str] = None
    created_by: Optional[str] = None
    tenant_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


@router.get("/events")
async def list_events(
    event_type: Optional[str] = None,
    year: Optional[int] = None,
    status: Optional[str] = "ACTIVE",
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    result = await tlf.list_events(
        db, event_type=event_type, status=status, limit=limit, offset=offset
    )
    items = result["items"]

    if year is not None:
        items = [item for item in items if getattr(item, "year", None) == year]
    if search:
        search_lower = search.lower()
        items = [
            item
            for item in items
            if search_lower in getattr(item, "name", "").lower()
            or search_lower in (getattr(item, "description", None) or "").lower()
        ]

    total = len(items)
    return {
        "items": [tlf.event_to_dict(item) for item in items],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.post("/events", status_code=201, response_model=TimelineEventOut)
async def create_event(
    data: TimelineEventCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    event = await tlf.create_event(
        db=db,
        name=data.name,
        event_type=data.event_type,
        start_date=data.start_date,
        end_date=data.end_date,
        description=data.description,
        recurring=data.recurring,
        cron_expression=data.cron_expression,
        year=data.year,
        brand_knowledge_ids=data.brand_knowledge_ids,
        product_ids=data.product_ids,
        prohibited_claims=data.prohibited_claims,
        is_commercial=data.is_commercial,
        status=data.status,
        priority=data.priority,
        color_code=data.color_code,
        created_by=user.email if hasattr(user, "email") else "user",
    )
    await db.commit()
    return TimelineEventOut(**tlf.event_to_dict(event))


@router.get("/events/{event_id}", response_model=TimelineEventOut)
async def get_event(
    event_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    event = await tlf.get_event(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return TimelineEventOut(**tlf.event_to_dict(event))


@router.put("/events/{event_id}", response_model=TimelineEventOut)
async def update_event(
    event_id: str,
    data: dict,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    event = await tlf.update_event(db=db, event_id=event_id, **data)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    await db.commit()
    return TimelineEventOut(**tlf.event_to_dict(event))


@router.delete("/events/{event_id}", status_code=204)
async def delete_event(
    event_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    if not await tlf.delete_event(db, event_id):
        raise HTTPException(status_code=404, detail="Event not found")
    await db.commit()
    return None
