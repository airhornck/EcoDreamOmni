"""Strategy Element API — v4.0 Strategy Element Architecture.

Endpoints:
  GET  /api/strategy-elements                  # 列表 + 过滤
  POST /api/strategy-elements                  # 创建
  GET  /api/strategy-elements/recommend        # 智能推荐
  GET  /api/strategy-elements/{id}             # 详情
  PUT  /api/strategy-elements/{id}             # 更新
  DELETE /api/strategy-elements/{id}           # 删除
  POST /api/strategy-elements/{id}/render      # 预览渲染
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.dependencies import get_current_user
from src.models.strategy_element import (
    ElementSource,
    ElementStatus,
    ElementType,
    StrategyElementORM,
)

router = APIRouter(prefix="/strategy-elements", tags=["strategy-elements"])


# ═══════════════════════════════════════════════════════════════════
# Schemas
# ═══════════════════════════════════════════════════════════════════


class TemplateVariable(BaseModel):
    name: str
    label: str
    type: str = "text"
    default_value: Optional[str] = None


class StrategyElementCreate(BaseModel):
    element_id: Optional[str] = None
    element_type: str
    element_subtype: Optional[str] = None
    name: str
    description: Optional[str] = None
    content: Dict[str, Any]
    render_template: str
    variables: List[TemplateVariable] = []
    source: str = "manual"
    source_content_id: Optional[str] = None
    source_element_ids: List[str] = []
    platform: Optional[str] = None
    content_format: Optional[str] = None
    methodology_stage_id: Optional[str] = None
    category: Optional[str] = None


class StrategyElementUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    content: Optional[Dict[str, Any]] = None
    render_template: Optional[str] = None
    variables: Optional[List[TemplateVariable]] = None
    platform: Optional[str] = None
    content_format: Optional[str] = None
    methodology_stage_id: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None


class StrategyElementOut(BaseModel):
    element_id: str
    element_type: str
    element_subtype: Optional[str]
    name: str
    description: Optional[str]
    content: Dict[str, Any]
    render_template: str
    variables: List[Dict[str, Any]]
    source: str
    source_content_id: Optional[str]
    platform: Optional[str]
    content_format: Optional[str]
    methodology_stage_id: Optional[str]
    category: Optional[str]
    usage_count: int
    avg_engagement: Dict[str, Any]
    effectiveness_score: float
    status: str
    created_by: str
    created_at: str
    updated_at: str


class StrategyElementRecommendRequest(BaseModel):
    topic: str
    platform: str = "xhs"
    methodology_stage_id: Optional[str] = None
    element_types: Optional[List[str]] = None
    limit: int = Field(default=6, ge=1, le=20)


class StrategyElementRenderRequest(BaseModel):
    variables: Dict[str, str] = {}
    topic: Optional[str] = None
    platform: Optional[str] = None


class StrategyElementRenderResponse(BaseModel):
    element_id: str
    element_type: str
    rendered_fragment: str
    target_layer: str


# ═══════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════


def _generate_element_id() -> str:
    import secrets

    return f"elem_{secrets.token_hex(6)}"


def _orm_to_out(orm: StrategyElementORM) -> Dict[str, Any]:
    return {
        "element_id": orm.element_id,
        "element_type": orm.element_type,
        "element_subtype": orm.element_subtype,
        "name": orm.name,
        "description": orm.description,
        "content": orm.content or {},
        "render_template": orm.render_template,
        "variables": orm.variables or [],
        "source": orm.source,
        "source_content_id": orm.source_content_id,
        "platform": orm.platform,
        "content_format": orm.content_format,
        "methodology_stage_id": orm.methodology_stage_id,
        "category": orm.category,
        "usage_count": orm.usage_count or 0,
        "avg_engagement": orm.avg_engagement or {},
        "effectiveness_score": orm.effectiveness_score or 0.0,
        "status": orm.status,
        "created_by": orm.created_by,
        "created_at": orm.created_at.isoformat() if orm.created_at else None,
        "updated_at": orm.updated_at.isoformat() if orm.updated_at else None,
    }


# ═══════════════════════════════════════════════════════════════════
# Routes
# ═══════════════════════════════════════════════════════════════════


@router.get("", response_model=List[StrategyElementOut])
async def list_strategy_elements(
    element_type: Optional[str] = Query(None),
    platform: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    methodology_stage_id: Optional[str] = Query(None),
    status: Optional[str] = Query("active"),
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    sort_by: Optional[str] = Query("usage_count"),
    sort_order: Optional[str] = Query("desc"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user),
):
    """List strategy elements with filtering and sorting."""
    tenant_id = getattr(current_user, "tenant_id", None) or "default"

    stmt = select(StrategyElementORM).where(StrategyElementORM.tenant_id == tenant_id)

    if element_type:
        stmt = stmt.where(StrategyElementORM.element_type == element_type)
    if platform:
        stmt = stmt.where(StrategyElementORM.platform == platform)
    if source:
        stmt = stmt.where(StrategyElementORM.source == source)
    if methodology_stage_id:
        stmt = stmt.where(StrategyElementORM.methodology_stage_id == methodology_stage_id)
    if status:
        stmt = stmt.where(StrategyElementORM.status == status)
    if category:
        stmt = stmt.where(StrategyElementORM.category == category)
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(
            (StrategyElementORM.name.ilike(pattern))
            | (StrategyElementORM.description.ilike(pattern))
            | (StrategyElementORM.element_id.ilike(pattern))
        )

    if sort_by == "usage_count":
        stmt = stmt.order_by(desc(StrategyElementORM.usage_count))
    elif sort_by == "effectiveness_score":
        stmt = stmt.order_by(desc(StrategyElementORM.effectiveness_score))
    elif sort_by == "created_at":
        stmt = stmt.order_by(desc(StrategyElementORM.created_at))
    else:
        stmt = stmt.order_by(desc(StrategyElementORM.usage_count))

    stmt = stmt.offset(offset).limit(limit)

    result = await db.execute(stmt)
    items = result.scalars().all()
    return [_orm_to_out(item) for item in items]


@router.post("", response_model=StrategyElementOut, status_code=201)
async def create_strategy_element(
    data: StrategyElementCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user),
):
    """Create a new strategy element."""
    tenant_id = getattr(current_user, "tenant_id", None) or "default"
    element_id = data.element_id or _generate_element_id()

    orm = StrategyElementORM(
        element_id=element_id,
        tenant_id=tenant_id,
        element_type=data.element_type,
        element_subtype=data.element_subtype,
        name=data.name,
        description=data.description,
        content=data.content,
        render_template=data.render_template,
        variables=[v.model_dump() for v in data.variables],
        source=data.source,
        source_content_id=data.source_content_id,
        source_element_ids=data.source_element_ids,
        platform=data.platform,
        content_format=data.content_format,
        methodology_stage_id=data.methodology_stage_id,
        category=data.category,
        created_by=getattr(current_user, "id", "system"),
    )
    db.add(orm)
    await db.commit()
    await db.refresh(orm)
    return _orm_to_out(orm)


@router.get("/recommend", response_model=List[StrategyElementOut])
async def recommend_strategy_elements(
    topic: str = Query(...),
    platform: str = Query("xhs"),
    methodology_stage_id: Optional[str] = Query(None),
    element_types: Optional[List[str]] = Query(None),
    limit: int = Query(6, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user),
):
    """Recommend strategy elements based on topic, platform, and methodology stage.

    Scoring:
      - platform exact match: +10
      - methodology_stage exact match: +5
      - topic keyword overlap: +1 per keyword
      - effectiveness_score: +0.1 per point
      - usage_count: +0.01 per use
    """
    tenant_id = getattr(current_user, "tenant_id", None) or "default"

    stmt = select(StrategyElementORM).where(
        StrategyElementORM.tenant_id == tenant_id,
        StrategyElementORM.status == "active",
    )

    if platform:
        stmt = stmt.where(
            (StrategyElementORM.platform == platform) | (StrategyElementORM.platform.is_(None))
        )
    if element_types:
        stmt = stmt.where(StrategyElementORM.element_type.in_(element_types))

    result = await db.execute(stmt)
    candidates = result.scalars().all()

    topic_words = set(w.lower() for w in topic.split() if len(w) > 1)

    scored = []
    for elem in candidates:
        score = 0.0
        if elem.platform == platform:
            score += 10
        if methodology_stage_id and elem.methodology_stage_id == methodology_stage_id:
            score += 5

        # Topic overlap in name/description/content
        text_to_match = " ".join(
            filter(
                None,
                [
                    elem.name,
                    elem.description or "",
                    str(elem.content) if elem.content else "",
                ],
            )
        ).lower()
        matches = sum(1 for w in topic_words if w in text_to_match)
        score += matches

        score += (elem.effectiveness_score or 0) * 0.1
        score += (elem.usage_count or 0) * 0.01

        scored.append((score, elem))

    # Group by element_type and take top-1 per type, then global top-N
    scored.sort(key=lambda x: -x[0])

    type_seen = set()
    diversified = []
    for score, elem in scored:
        if elem.element_type not in type_seen:
            diversified.append(elem)
            type_seen.add(elem.element_type)
        if len(diversified) >= limit:
            break

    return [_orm_to_out(item) for item in diversified]


@router.get("/{element_id}", response_model=StrategyElementOut)
async def get_strategy_element(
    element_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user),
):
    """Get a single strategy element by ID."""
    tenant_id = getattr(current_user, "tenant_id", None) or "default"

    result = await db.execute(
        select(StrategyElementORM).where(
            StrategyElementORM.tenant_id == tenant_id,
            StrategyElementORM.element_id == element_id,
        )
    )
    orm = result.scalar_one_or_none()
    if not orm:
        raise HTTPException(status_code=404, detail="Strategy element not found")
    return _orm_to_out(orm)


@router.put("/{element_id}", response_model=StrategyElementOut)
async def update_strategy_element(
    element_id: str,
    data: StrategyElementUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user),
):
    """Update a strategy element."""
    tenant_id = getattr(current_user, "tenant_id", None) or "default"

    result = await db.execute(
        select(StrategyElementORM).where(
            StrategyElementORM.tenant_id == tenant_id,
            StrategyElementORM.element_id == element_id,
        )
    )
    orm = result.scalar_one_or_none()
    if not orm:
        raise HTTPException(status_code=404, detail="Strategy element not found")

    update_data = data.model_dump(exclude_unset=True)
    if "variables" in update_data and update_data["variables"] is not None:
        update_data["variables"] = [v.model_dump() for v in update_data["variables"]]

    for key, value in update_data.items():
        setattr(orm, key, value)

    await db.commit()
    await db.refresh(orm)
    return _orm_to_out(orm)


@router.delete("/{element_id}", status_code=204)
async def delete_strategy_element(
    element_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user),
):
    """Soft-delete a strategy element by marking it deprecated."""
    tenant_id = getattr(current_user, "tenant_id", None) or "default"

    result = await db.execute(
        select(StrategyElementORM).where(
            StrategyElementORM.tenant_id == tenant_id,
            StrategyElementORM.element_id == element_id,
        )
    )
    orm = result.scalar_one_or_none()
    if not orm:
        raise HTTPException(status_code=404, detail="Strategy element not found")

    orm.status = "deprecated"
    await db.commit()
    return None


@router.post("/{element_id}/render", response_model=StrategyElementRenderResponse)
async def render_strategy_element(
    element_id: str,
    req: StrategyElementRenderRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user),
):
    """Render a strategy element into a prompt fragment."""
    tenant_id = getattr(current_user, "tenant_id", None) or "default"

    result = await db.execute(
        select(StrategyElementORM).where(
            StrategyElementORM.tenant_id == tenant_id,
            StrategyElementORM.element_id == element_id,
        )
    )
    orm = result.scalar_one_or_none()
    if not orm:
        raise HTTPException(status_code=404, detail="Strategy element not found")

    from src.services.element_renderers import get_renderer

    renderer = get_renderer(orm.element_type)
    fragment = renderer.render(
        element=orm,
        variables=req.variables,
        topic=req.topic or "",
        platform=req.platform or orm.platform or "xhs",
    )

    return StrategyElementRenderResponse(
        element_id=orm.element_id,
        element_type=orm.element_type,
        rendered_fragment=fragment,
        target_layer=renderer.target_layer,
    )
