"""PlatformContentTypeStyle API — v4.0 Phase 1 P1-1.

提供 PlatformContentTypeStyle 的 CRUD 接口。

Aligned with docs/契约与数据/01-API接口契约.md §4.1
"""

import secrets
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.api.auth import get_current_user
from src.models.platform_content_type_style import PlatformContentTypeStyleORM

router = APIRouter(prefix="/platform-content-type-styles", tags=["platform-content-type-styles"])


# ─── Pydantic Schemas ───

class TonePreset(BaseModel):
    formality: float = Field(0.5, ge=0.0, le=1.0)
    enthusiasm: float = Field(0.5, ge=0.0, le=1.0)
    urgency: float = Field(0.5, ge=0.0, le=1.0)
    empathy: float = Field(0.5, ge=0.0, le=1.0)


class ContentDNA(BaseModel):
    hook_types: List[str] = []
    structure_patterns: List[str] = []
    tone_presets: List[str] = []


class RecommendedKeywords(BaseModel):
    high_performing: List[str] = []
    trending: List[str] = []
    seasonal: List[str] = []


class StructureTemplate(BaseModel):
    paragraphs: int = 3


class PlatformContentTypeStyleCreate(BaseModel):
    platform_id: str
    content_type: str
    content_dna: Optional[Dict[str, Any]] = None
    default_prompt_fragments: Optional[List[str]] = None
    recommended_keywords: Optional[Dict[str, Any]] = None
    tone_preset: Optional[Dict[str, Any]] = None
    structure_template: Optional[Dict[str, Any]] = None
    status: str = "active"


class PlatformContentTypeStyleUpdate(BaseModel):
    platform_id: Optional[str] = None
    content_type: Optional[str] = None
    content_dna: Optional[Dict[str, Any]] = None
    default_prompt_fragments: Optional[List[str]] = None
    recommended_keywords: Optional[Dict[str, Any]] = None
    tone_preset: Optional[Dict[str, Any]] = None
    structure_template: Optional[Dict[str, Any]] = None
    avg_engagement_rate: Optional[float] = None
    sample_count: Optional[int] = None
    is_ai_generated: Optional[bool] = None
    source_template_ids: Optional[List[str]] = None
    status: Optional[str] = None


class PlatformContentTypeStyleOut(BaseModel):
    style_id: str
    tenant_id: str
    platform_id: str
    content_type: str
    content_dna: Optional[Dict[str, Any]] = None
    default_prompt_fragments: Optional[List[str]] = None
    recommended_keywords: Optional[Dict[str, Any]] = None
    tone_preset: Optional[Dict[str, Any]] = None
    structure_template: Optional[Dict[str, Any]] = None
    avg_engagement_rate: float = 0.0
    sample_count: int = 0
    is_ai_generated: bool = True
    source_template_ids: Optional[List[str]] = None
    status: str = "active"
    created_by: str
    created_at: str
    updated_at: str

    model_config = ConfigDict(from_attributes=True)


class PaginatedStylesOut(BaseModel):
    items: List[PlatformContentTypeStyleOut]
    total: int
    page: int
    page_size: int


# ─── Helpers ───

def _generate_style_id() -> str:
    return f"style_{secrets.token_urlsafe(12)}"


# ─── API Endpoints ───

@router.get("", response_model=PaginatedStylesOut)
async def list_platform_content_type_styles(
    platform_id: Optional[str] = Query(None),
    content_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user),
):
    """列出当前租户的平台内容类型风格（支持分页和过滤）."""
    tenant_id = getattr(current_user, "tenant_id", None) or "default"

    query = select(PlatformContentTypeStyleORM).where(
        PlatformContentTypeStyleORM.tenant_id == tenant_id
    )
    count_query = select(func.count()).select_from(PlatformContentTypeStyleORM).where(
        PlatformContentTypeStyleORM.tenant_id == tenant_id
    )

    if platform_id:
        query = query.where(PlatformContentTypeStyleORM.platform_id == platform_id)
        count_query = count_query.where(PlatformContentTypeStyleORM.platform_id == platform_id)
    if content_type:
        query = query.where(PlatformContentTypeStyleORM.content_type == content_type)
        count_query = count_query.where(PlatformContentTypeStyleORM.content_type == content_type)
    if status:
        query = query.where(PlatformContentTypeStyleORM.status == status)
        count_query = count_query.where(PlatformContentTypeStyleORM.status == status)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()

    return PaginatedStylesOut(
        items=[
            PlatformContentTypeStyleOut(
                style_id=s.style_id,
                tenant_id=s.tenant_id,
                platform_id=s.platform_id,
                content_type=s.content_type,
                content_dna=s.content_dna,
                default_prompt_fragments=s.default_prompt_fragments,
                recommended_keywords=s.recommended_keywords,
                tone_preset=s.tone_preset,
                structure_template=s.structure_template,
                avg_engagement_rate=s.avg_engagement_rate or 0.0,
                sample_count=s.sample_count or 0,
                is_ai_generated=s.is_ai_generated or True,
                source_template_ids=s.source_template_ids,
                status=s.status,
                created_by=s.created_by,
                created_at=s.created_at.isoformat() if s.created_at else "",
                updated_at=s.updated_at.isoformat() if s.updated_at else "",
            )
            for s in items
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=PlatformContentTypeStyleOut, status_code=201)
async def create_platform_content_type_style(
    data: PlatformContentTypeStyleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user),
):
    """创建新的平台内容类型风格."""
    tenant_id = getattr(current_user, "tenant_id", None) or "default"
    user_id = getattr(current_user, "id", "system")

    style = PlatformContentTypeStyleORM(
        style_id=_generate_style_id(),
        tenant_id=tenant_id,
        platform_id=data.platform_id,
        content_type=data.content_type,
        content_dna=data.content_dna or {},
        default_prompt_fragments=data.default_prompt_fragments or [],
        recommended_keywords=data.recommended_keywords or {},
        tone_preset=data.tone_preset or {},
        structure_template=data.structure_template or {},
        status=data.status,
        created_by=user_id,
    )
    db.add(style)
    await db.commit()
    await db.refresh(style)

    return PlatformContentTypeStyleOut(
        style_id=style.style_id,
        tenant_id=style.tenant_id,
        platform_id=style.platform_id,
        content_type=style.content_type,
        content_dna=style.content_dna,
        default_prompt_fragments=style.default_prompt_fragments,
        recommended_keywords=style.recommended_keywords,
        tone_preset=style.tone_preset,
        structure_template=style.structure_template,
        avg_engagement_rate=style.avg_engagement_rate or 0.0,
        sample_count=style.sample_count or 0,
        is_ai_generated=style.is_ai_generated or True,
        source_template_ids=style.source_template_ids,
        status=style.status,
        created_by=style.created_by,
        created_at=style.created_at.isoformat() if style.created_at else "",
        updated_at=style.updated_at.isoformat() if style.updated_at else "",
    )


@router.get("/{style_id}", response_model=PlatformContentTypeStyleOut)
async def get_platform_content_type_style(
    style_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user),
):
    """获取单个风格详情."""
    tenant_id = getattr(current_user, "tenant_id", None) or "default"
    result = await db.execute(
        select(PlatformContentTypeStyleORM).where(
            PlatformContentTypeStyleORM.style_id == style_id,
            PlatformContentTypeStyleORM.tenant_id == tenant_id,
        )
    )
    style = result.scalar_one_or_none()
    if not style:
        raise HTTPException(status_code=404, detail=f"风格未找到: {style_id}")

    return PlatformContentTypeStyleOut(
        style_id=style.style_id,
        tenant_id=style.tenant_id,
        platform_id=style.platform_id,
        content_type=style.content_type,
        content_dna=style.content_dna,
        default_prompt_fragments=style.default_prompt_fragments,
        recommended_keywords=style.recommended_keywords,
        tone_preset=style.tone_preset,
        structure_template=style.structure_template,
        avg_engagement_rate=style.avg_engagement_rate or 0.0,
        sample_count=style.sample_count or 0,
        is_ai_generated=style.is_ai_generated or True,
        source_template_ids=style.source_template_ids,
        status=style.status,
        created_by=style.created_by,
        created_at=style.created_at.isoformat() if style.created_at else "",
        updated_at=style.updated_at.isoformat() if style.updated_at else "",
    )


@router.patch("/{style_id}", response_model=PlatformContentTypeStyleOut)
async def update_platform_content_type_style(
    style_id: str,
    data: PlatformContentTypeStyleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user),
):
    """部分更新风格."""
    tenant_id = getattr(current_user, "tenant_id", None) or "default"
    result = await db.execute(
        select(PlatformContentTypeStyleORM).where(
            PlatformContentTypeStyleORM.style_id == style_id,
            PlatformContentTypeStyleORM.tenant_id == tenant_id,
        )
    )
    style = result.scalar_one_or_none()
    if not style:
        raise HTTPException(status_code=404, detail=f"风格未找到: {style_id}")

    update_fields = data.model_dump(exclude_unset=True)
    for field, value in update_fields.items():
        setattr(style, field, value)

    await db.commit()
    await db.refresh(style)

    return PlatformContentTypeStyleOut(
        style_id=style.style_id,
        tenant_id=style.tenant_id,
        platform_id=style.platform_id,
        content_type=style.content_type,
        content_dna=style.content_dna,
        default_prompt_fragments=style.default_prompt_fragments,
        recommended_keywords=style.recommended_keywords,
        tone_preset=style.tone_preset,
        structure_template=style.structure_template,
        avg_engagement_rate=style.avg_engagement_rate or 0.0,
        sample_count=style.sample_count or 0,
        is_ai_generated=style.is_ai_generated or True,
        source_template_ids=style.source_template_ids,
        status=style.status,
        created_by=style.created_by,
        created_at=style.created_at.isoformat() if style.created_at else "",
        updated_at=style.updated_at.isoformat() if style.updated_at else "",
    )


@router.delete("/{style_id}")
async def delete_platform_content_type_style(
    style_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user),
):
    """软删除风格（status → deprecated）."""
    tenant_id = getattr(current_user, "tenant_id", None) or "default"
    result = await db.execute(
        select(PlatformContentTypeStyleORM).where(
            PlatformContentTypeStyleORM.style_id == style_id,
            PlatformContentTypeStyleORM.tenant_id == tenant_id,
        )
    )
    style = result.scalar_one_or_none()
    if not style:
        raise HTTPException(status_code=404, detail=f"风格未找到: {style_id}")

    style.status = "deprecated"
    await db.commit()
    return {"code": "OK", "message": "风格已删除", "data": {"style_id": style_id}}
