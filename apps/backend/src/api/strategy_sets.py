"""Strategy Set API — v4.0 Strategy Element Architecture.

StrategySet 是 ContentTemplate 的演进形态：
- ContentTemplate = 完整的 prompt_template + variables
- StrategySet = 策略元素组合的快照 + 默认变量值

Endpoints:
  GET  /api/strategy-sets                  # 列表 + 过滤
  POST /api/strategy-sets                  # 创建
  GET  /api/strategy-sets/{id}             # 详情
  PUT  /api/strategy-sets/{id}             # 更新
  DELETE /api/strategy-sets/{id}           # 删除
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.dependencies import get_current_user
from src.models.strategy_set import StrategySetORM

router = APIRouter(prefix="/strategy-sets", tags=["strategy-sets"])


# ═══════════════════════════════════════════════════════════════════
# Schemas
# ═══════════════════════════════════════════════════════════════════


class StrategyElementRef(BaseModel):
    element_id: str
    priority: int = 50
    override_variables: Optional[Dict[str, str]] = None


class StrategySetCreate(BaseModel):
    set_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    element_refs: List[StrategyElementRef]
    default_variables: Dict[str, str] = {}
    source: str = "manual"
    source_content_id: Optional[str] = None
    platform: Optional[str] = None
    content_format: Optional[str] = None
    methodology_stage_id: Optional[str] = None
    category: Optional[str] = None


class StrategySetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    element_refs: Optional[List[StrategyElementRef]] = None
    default_variables: Optional[Dict[str, str]] = None
    platform: Optional[str] = None
    content_format: Optional[str] = None
    methodology_stage_id: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None


class StrategySetOut(BaseModel):
    set_id: str
    name: str
    description: Optional[str]
    element_refs: List[Dict[str, Any]]
    default_variables: Dict[str, Any]
    source: str
    source_content_id: Optional[str]
    platform: Optional[str]
    content_format: Optional[str]
    methodology_stage_id: Optional[str]
    category: Optional[str]
    usage_count: int
    avg_engagement: Dict[str, Any]
    status: str
    created_by: str
    created_at: str
    updated_at: str


# ═══════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════


def _generate_set_id() -> str:
    import secrets

    return f"set_{secrets.token_hex(6)}"


def _orm_to_out(orm: StrategySetORM) -> Dict[str, Any]:
    return {
        "set_id": orm.set_id,
        "name": orm.name,
        "description": orm.description,
        "element_refs": orm.element_refs or [],
        "default_variables": orm.default_variables or {},
        "source": orm.source,
        "source_content_id": orm.source_content_id,
        "platform": orm.platform,
        "content_format": orm.content_format,
        "methodology_stage_id": orm.methodology_stage_id,
        "category": orm.category,
        "usage_count": orm.usage_count or 0,
        "avg_engagement": orm.avg_engagement or {},
        "status": orm.status,
        "created_by": orm.created_by,
        "created_at": orm.created_at.isoformat() if orm.created_at else None,
        "updated_at": orm.updated_at.isoformat() if orm.updated_at else None,
    }


# ═══════════════════════════════════════════════════════════════════
# Routes
# ═══════════════════════════════════════════════════════════════════


@router.get("", response_model=List[StrategySetOut])
async def list_strategy_sets(
    platform: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    methodology_stage_id: Optional[str] = Query(None),
    status: Optional[str] = Query("active"),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user),
):
    """List strategy sets with filtering."""
    tenant_id = getattr(current_user, "tenant_id", None) or "default"

    stmt = select(StrategySetORM).where(StrategySetORM.tenant_id == tenant_id)

    if platform:
        stmt = stmt.where(StrategySetORM.platform == platform)
    if source:
        stmt = stmt.where(StrategySetORM.source == source)
    if methodology_stage_id:
        stmt = stmt.where(StrategySetORM.methodology_stage_id == methodology_stage_id)
    if status:
        stmt = stmt.where(StrategySetORM.status == status)
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(
            (StrategySetORM.name.ilike(pattern))
            | (StrategySetORM.description.ilike(pattern))
            | (StrategySetORM.set_id.ilike(pattern))
        )

    stmt = stmt.order_by(desc(StrategySetORM.usage_count))
    stmt = stmt.offset(offset).limit(limit)

    result = await db.execute(stmt)
    items = result.scalars().all()
    return [_orm_to_out(item) for item in items]


@router.post("", response_model=StrategySetOut, status_code=201)
async def create_strategy_set(
    data: StrategySetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user),
):
    """Create a new strategy set."""
    tenant_id = getattr(current_user, "tenant_id", None) or "default"
    set_id = data.set_id or _generate_set_id()

    orm = StrategySetORM(
        set_id=set_id,
        tenant_id=tenant_id,
        name=data.name,
        description=data.description,
        element_refs=[ref.model_dump(exclude_none=True) for ref in data.element_refs],
        default_variables=data.default_variables,
        source=data.source,
        source_content_id=data.source_content_id,
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


@router.get("/{set_id}", response_model=StrategySetOut)
async def get_strategy_set(
    set_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user),
):
    """Get a single strategy set by ID."""
    tenant_id = getattr(current_user, "tenant_id", None) or "default"

    result = await db.execute(
        select(StrategySetORM).where(
            StrategySetORM.tenant_id == tenant_id,
            StrategySetORM.set_id == set_id,
        )
    )
    orm = result.scalar_one_or_none()
    if not orm:
        raise HTTPException(status_code=404, detail="Strategy set not found")
    return _orm_to_out(orm)


@router.put("/{set_id}", response_model=StrategySetOut)
async def update_strategy_set(
    set_id: str,
    data: StrategySetUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user),
):
    """Update a strategy set."""
    tenant_id = getattr(current_user, "tenant_id", None) or "default"

    result = await db.execute(
        select(StrategySetORM).where(
            StrategySetORM.tenant_id == tenant_id,
            StrategySetORM.set_id == set_id,
        )
    )
    orm = result.scalar_one_or_none()
    if not orm:
        raise HTTPException(status_code=404, detail="Strategy set not found")

    update_data = data.model_dump(exclude_unset=True)
    if "element_refs" in update_data and update_data["element_refs"] is not None:
        update_data["element_refs"] = [
            ref.model_dump(exclude_none=True) for ref in update_data["element_refs"]
        ]

    for key, value in update_data.items():
        setattr(orm, key, value)

    await db.commit()
    await db.refresh(orm)
    return _orm_to_out(orm)


@router.delete("/{set_id}", status_code=204)
async def delete_strategy_set(
    set_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user),
):
    """Soft-delete a strategy set by marking it deprecated."""
    tenant_id = getattr(current_user, "tenant_id", None) or "default"

    result = await db.execute(
        select(StrategySetORM).where(
            StrategySetORM.tenant_id == tenant_id,
            StrategySetORM.set_id == set_id,
        )
    )
    orm = result.scalar_one_or_none()
    if not orm:
        raise HTTPException(status_code=404, detail="Strategy set not found")

    orm.status = "deprecated"
    await db.commit()
    return None
