"""ContentTemplate API — v4.0 Phase 1 P1-2.

提供 ContentTemplate 的 CRUD 接口。

Aligned with docs/契约与数据/01-API接口契约.md §4.2
"""

import secrets
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.api.auth import get_current_user
from src.models.content_template import ContentTemplateORM

router = APIRouter(prefix="/content-templates", tags=["content-templates"])


# ─── Pydantic Schemas ───

class TemplateVariable(BaseModel):
    name: str
    label: str
    type: str = "text"
    default_value: Optional[str] = None


class ExtractedStructure(BaseModel):
    hook_pattern: str = ""
    body_structure: str = ""
    cta_pattern: str = ""


class EngagementBenchmark(BaseModel):
    likes: int = 0
    comments: int = 0
    saves: int = 0
    shares: int = 0


class ContentTemplateCreate(BaseModel):
    source_platform_id: str
    source_content_url: Optional[str] = None
    source_content_id: Optional[str] = None
    extracted_structure: Dict[str, Any]
    prompt_template: str
    variables: List[Dict[str, Any]]
    engagement_benchmark: Optional[Dict[str, Any]] = None
    platform_content_type_style_id: Optional[str] = None
    status: str = "active"


class ContentTemplateUpdate(BaseModel):
    source_platform_id: Optional[str] = None
    source_content_url: Optional[str] = None
    source_content_id: Optional[str] = None
    extracted_structure: Optional[Dict[str, Any]] = None
    prompt_template: Optional[str] = None
    variables: Optional[List[Dict[str, Any]]] = None
    engagement_benchmark: Optional[Dict[str, Any]] = None
    platform_content_type_style_id: Optional[str] = None
    usage_count: Optional[int] = None
    avg_generated_engagement: Optional[Dict[str, Any]] = None
    status: Optional[str] = None


class ContentTemplateOut(BaseModel):
    template_id: str
    tenant_id: str
    source_platform_id: str
    source_content_url: Optional[str] = None
    source_content_id: Optional[str] = None
    extracted_structure: Dict[str, Any]
    prompt_template: str
    variables: List[Dict[str, Any]]
    engagement_benchmark: Optional[Dict[str, Any]] = None
    platform_content_type_style_id: Optional[str] = None
    created_by: str
    usage_count: int = 0
    avg_generated_engagement: Optional[Dict[str, Any]] = None
    status: str = "active"
    created_at: str
    updated_at: str

    model_config = ConfigDict(from_attributes=True)


class PaginatedTemplatesOut(BaseModel):
    items: List[ContentTemplateOut]
    total: int
    page: int
    page_size: int


# ─── Helpers ───

def _generate_template_id() -> str:
    return f"tmpl_{secrets.token_urlsafe(12)}"


# ─── API Endpoints ───

@router.get("", response_model=PaginatedTemplatesOut)
async def list_content_templates(
    platform_content_type_style_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    structure_type: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user),
):
    """列出当前租户的内容模板（支持分页和过滤）."""
    tenant_id = getattr(current_user, "tenant_id", None) or "default"

    query = select(ContentTemplateORM).where(ContentTemplateORM.tenant_id == tenant_id)
    count_query = select(func.count()).select_from(ContentTemplateORM).where(
        ContentTemplateORM.tenant_id == tenant_id
    )

    if platform_content_type_style_id:
        query = query.where(
            ContentTemplateORM.platform_content_type_style_id == platform_content_type_style_id
        )
        count_query = count_query.where(
            ContentTemplateORM.platform_content_type_style_id == platform_content_type_style_id
        )
    if status:
        query = query.where(ContentTemplateORM.status == status)
        count_query = count_query.where(ContentTemplateORM.status == status)
    if structure_type:
        query = query.where(
            ContentTemplateORM.extracted_structure["structure_type"].as_string()
            == structure_type
        )
        count_query = count_query.where(
            ContentTemplateORM.extracted_structure["structure_type"].as_string()
            == structure_type
        )
    if source:
        query = query.where(ContentTemplateORM.source == source)
        count_query = count_query.where(ContentTemplateORM.source == source)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()

    return PaginatedTemplatesOut(
        items=[
            ContentTemplateOut(
                template_id=t.template_id,
                tenant_id=t.tenant_id,
                source_platform_id=t.source_platform_id,
                source_content_url=t.source_content_url,
                source_content_id=t.source_content_id,
                extracted_structure=t.extracted_structure or {},
                prompt_template=t.prompt_template,
                variables=t.variables or [],
                engagement_benchmark=t.engagement_benchmark,
                platform_content_type_style_id=t.platform_content_type_style_id,
                created_by=t.created_by,
                usage_count=t.usage_count or 0,
                avg_generated_engagement=t.avg_generated_engagement,
                status=t.status,
                created_at=t.created_at.isoformat() if t.created_at else "",
                updated_at=t.updated_at.isoformat() if t.updated_at else "",
            )
            for t in items
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/recommend", response_model=List[ContentTemplateOut])
async def recommend_content_templates(
    topic: str,
    platform: str = Query("xhs"),
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user),
):
    """根据 topic 关键词推荐 Top3 最相关模板（MVP：简单字符串包含匹配）."""
    tenant_id = getattr(current_user, "tenant_id", None) or "default"

    result = await db.execute(
        select(ContentTemplateORM).where(
            ContentTemplateORM.tenant_id == tenant_id,
            ContentTemplateORM.source_platform_id == platform,
            ContentTemplateORM.status == "active",
        )
    )
    templates = result.scalars().all()

    topic_lower = topic.lower()
    scored: List[tuple[int, ContentTemplateORM]] = []
    for t in templates:
        score = 0
        prompt_lower = t.prompt_template.lower()
        if topic_lower in prompt_lower:
            score += 1
        scored.append((score, t))

    # 按匹配分降序，再按使用次数降序作为次级排序
    scored.sort(key=lambda x: (-x[0], -(x[1].usage_count or 0)))
    top3 = [t for _, t in scored[:3]]

    return [
        ContentTemplateOut(
            template_id=t.template_id,
            tenant_id=t.tenant_id,
            source_platform_id=t.source_platform_id,
            source_content_url=t.source_content_url,
            source_content_id=t.source_content_id,
            extracted_structure=t.extracted_structure or {},
            prompt_template=t.prompt_template,
            variables=t.variables or [],
            engagement_benchmark=t.engagement_benchmark,
            platform_content_type_style_id=t.platform_content_type_style_id,
            created_by=t.created_by,
            usage_count=t.usage_count or 0,
            avg_generated_engagement=t.avg_generated_engagement,
            status=t.status,
            created_at=t.created_at.isoformat() if t.created_at else "",
            updated_at=t.updated_at.isoformat() if t.updated_at else "",
        )
        for t in top3
    ]


@router.post("", response_model=ContentTemplateOut, status_code=201)
async def create_content_template(
    data: ContentTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user),
):
    """创建新的内容模板."""
    tenant_id = getattr(current_user, "tenant_id", None) or "default"
    user_id = getattr(current_user, "id", "system")

    template = ContentTemplateORM(
        template_id=_generate_template_id(),
        tenant_id=tenant_id,
        source_platform_id=data.source_platform_id,
        source_content_url=data.source_content_url,
        source_content_id=data.source_content_id,
        extracted_structure=data.extracted_structure,
        prompt_template=data.prompt_template,
        variables=data.variables,
        engagement_benchmark=data.engagement_benchmark or {},
        platform_content_type_style_id=data.platform_content_type_style_id,
        status=data.status,
        created_by=user_id,
    )
    db.add(template)
    await db.commit()
    await db.refresh(template)

    return ContentTemplateOut(
        template_id=template.template_id,
        tenant_id=template.tenant_id,
        source_platform_id=template.source_platform_id,
        source_content_url=template.source_content_url,
        source_content_id=template.source_content_id,
        extracted_structure=template.extracted_structure or {},
        prompt_template=template.prompt_template,
        variables=template.variables or [],
        engagement_benchmark=template.engagement_benchmark,
        platform_content_type_style_id=template.platform_content_type_style_id,
        created_by=template.created_by,
        usage_count=template.usage_count or 0,
        avg_generated_engagement=template.avg_generated_engagement,
        status=template.status,
        created_at=template.created_at.isoformat() if template.created_at else "",
        updated_at=template.updated_at.isoformat() if template.updated_at else "",
    )


@router.get("/{template_id}", response_model=ContentTemplateOut)
async def get_content_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user),
):
    """获取单个模板详情."""
    tenant_id = getattr(current_user, "tenant_id", None) or "default"
    result = await db.execute(
        select(ContentTemplateORM).where(
            ContentTemplateORM.template_id == template_id,
            ContentTemplateORM.tenant_id == tenant_id,
        )
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail=f"模板未找到: {template_id}")

    return ContentTemplateOut(
        template_id=template.template_id,
        tenant_id=template.tenant_id,
        source_platform_id=template.source_platform_id,
        source_content_url=template.source_content_url,
        source_content_id=template.source_content_id,
        extracted_structure=template.extracted_structure or {},
        prompt_template=template.prompt_template,
        variables=template.variables or [],
        engagement_benchmark=template.engagement_benchmark,
        platform_content_type_style_id=template.platform_content_type_style_id,
        created_by=template.created_by,
        usage_count=template.usage_count or 0,
        avg_generated_engagement=template.avg_generated_engagement,
        status=template.status,
        created_at=template.created_at.isoformat() if template.created_at else "",
        updated_at=template.updated_at.isoformat() if template.updated_at else "",
    )


@router.patch("/{template_id}", response_model=ContentTemplateOut)
async def update_content_template(
    template_id: str,
    data: ContentTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user),
):
    """部分更新模板."""
    tenant_id = getattr(current_user, "tenant_id", None) or "default"
    result = await db.execute(
        select(ContentTemplateORM).where(
            ContentTemplateORM.template_id == template_id,
            ContentTemplateORM.tenant_id == tenant_id,
        )
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail=f"模板未找到: {template_id}")

    update_fields = data.model_dump(exclude_unset=True)
    for field, value in update_fields.items():
        setattr(template, field, value)

    await db.commit()
    await db.refresh(template)

    return ContentTemplateOut(
        template_id=template.template_id,
        tenant_id=template.tenant_id,
        source_platform_id=template.source_platform_id,
        source_content_url=template.source_content_url,
        source_content_id=template.source_content_id,
        extracted_structure=template.extracted_structure or {},
        prompt_template=template.prompt_template,
        variables=template.variables or [],
        engagement_benchmark=template.engagement_benchmark,
        platform_content_type_style_id=template.platform_content_type_style_id,
        created_by=template.created_by,
        usage_count=template.usage_count or 0,
        avg_generated_engagement=template.avg_generated_engagement,
        status=template.status,
        created_at=template.created_at.isoformat() if template.created_at else "",
        updated_at=template.updated_at.isoformat() if template.updated_at else "",
    )


@router.delete("/{template_id}")
async def delete_content_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(get_current_user),
):
    """软删除模板（status → deprecated）."""
    tenant_id = getattr(current_user, "tenant_id", None) or "default"
    result = await db.execute(
        select(ContentTemplateORM).where(
            ContentTemplateORM.template_id == template_id,
            ContentTemplateORM.tenant_id == tenant_id,
        )
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail=f"模板未找到: {template_id}")

    template.status = "deprecated"
    await db.commit()
    return {"code": "OK", "message": "模板已删除", "data": {"template_id": template_id}}
