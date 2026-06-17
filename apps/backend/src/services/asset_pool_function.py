"""AssetPool Function — ORM持久化版本 (W14).

Aligned with PRD V3.1 §AssetPool / TASK_V2.7.1 FUNC-1.
Migrates in-memory storage to PostgreSQL via SQLAlchemy 2.0 async.

API routes should inject `db: AsyncSession = Depends(get_db)` and await these functions.
For test environments without DB, the legacy in-memory service remains available.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete

from src.models.asset_pool_orm import AssetORM


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _check_license_status(expiry_dt: Optional[datetime]) -> str:
    if not expiry_dt:
        return "VALID"
    now = _now()
    days_until = (expiry_dt - now).days
    if days_until < 0:
        return "EXPIRED"
    elif days_until <= 30:
        return "EXPIRING_SOON"
    return "VALID"


def _generate_thumbnail_url(file_url: str) -> str:
    if "." in file_url:
        base, ext = file_url.rsplit(".", 1)
        return f"{base}_thumb.{ext}"
    return f"{file_url}_thumb"


def _ensure_ai_disclosure(data: Dict[str, Any]) -> Dict[str, Any]:
    if data.get("source_type") == "AI_GENERATED":
        data["ai_disclosure"] = True
        tags = list(data.get("tags") or [])
        if "AI辅助创作" not in tags:
            tags.append("AI辅助创作")
        data["tags"] = tags
    return data


def _validate_copyright(data: Dict[str, Any]) -> bool:
    lt = data.get("license_type")
    if lt == "OWNED":
        return bool(data.get("copyright_holder"))
    if lt == "LICENSED":
        return bool(data.get("stock_source"))
    if lt == "AI_GENERATED":
        return bool(data.get("ai_model"))
    return True


def asset_to_dict(asset: AssetORM) -> Dict[str, Any]:
    """ORM对象 → 字典（兼容API层序列化）."""
    return {
        "id": str(asset.id),
        "filename": asset.filename,
        "file_url": asset.file_url,
        "thumbnail_url": asset.thumbnail_url,
        "source_type": asset.source_type,
        "license_type": asset.license_type,
        "license_status": asset.license_status,
        "copyright_holder": asset.copyright_holder,
        "copyright_year": asset.copyright_year,
        "usage_rights": asset.usage_rights or [],
        "copyright_validated": asset.copyright_validated,
        "license_ref": asset.license_ref,
        "stock_source": asset.stock_source,
        "stock_id": asset.stock_id,
        "license_expiry": asset.license_expiry.isoformat() if asset.license_expiry else None,
        "ai_model": asset.ai_model,
        "ai_prompt": asset.ai_prompt,
        "ai_disclosure": asset.ai_disclosure,
        "ai_metadata": asset.ai_metadata,
        "category": asset.category,
        "tags": asset.tags or [],
        "description": asset.description,
        "series_id": asset.series_id,
        "brand_knowledge_id": asset.brand_knowledge_id,
        "status": asset.status,
        "meta_width": asset.meta_width,
        "meta_height": asset.meta_height,
        "meta_file_size": asset.meta_file_size,
        "meta_mime_type": asset.meta_mime_type,
        "meta_dominant_color": asset.meta_dominant_color,
        "uploaded_by": asset.uploaded_by,
        "tenant_id": asset.tenant_id,
        "created_at": asset.created_at.isoformat() if asset.created_at else None,
        "updated_at": asset.updated_at.isoformat() if asset.updated_at else None,
    }


async def create_asset(
    db: AsyncSession,
    filename: str,
    file_url: str,
    source_type: str = "OPERATOR_UPLOAD",
    license_type: str = "OWNED",
    tags: Optional[List[str]] = None,
    category: Optional[str] = None,
    description: Optional[str] = None,
    copyright_holder: Optional[str] = None,
    copyright_year: Optional[int] = None,
    usage_rights: Optional[List[str]] = None,
    stock_source: Optional[str] = None,
    stock_id: Optional[str] = None,
    license_expiry: Optional[str] = None,
    ai_model: Optional[str] = None,
    ai_prompt: Optional[str] = None,
    series_id: Optional[str] = None,
    brand_knowledge_id: Optional[str] = None,
    uploaded_by: Optional[str] = None,
    tenant_id: Optional[str] = None,
    generate_thumbnail: bool = True,
    **kwargs,
) -> AssetORM:
    _now()

    expiry_dt = None
    if license_expiry:
        try:
            expiry_dt = datetime.fromisoformat(license_expiry.replace("Z", "+00:00"))
        except ValueError:
            pass

    asset_data = {
        "filename": filename,
        "file_url": file_url,
        "source_type": source_type,
        "license_type": license_type,
        "tags": tags or [],
        "category": category,
        "description": description,
        "copyright_holder": copyright_holder,
        "copyright_year": copyright_year,
        "usage_rights": usage_rights or [],
        "stock_source": stock_source,
        "stock_id": stock_id,
        "license_expiry": expiry_dt,
        "ai_model": ai_model,
        "ai_prompt": ai_prompt,
        "series_id": series_id,
        "brand_knowledge_id": brand_knowledge_id,
        "uploaded_by": uploaded_by,
        "tenant_id": tenant_id,
        "status": "ACTIVE",
    }
    asset_data = _ensure_ai_disclosure(asset_data)
    asset_data["copyright_validated"] = _validate_copyright(asset_data)
    asset_data["license_status"] = _check_license_status(expiry_dt)

    if generate_thumbnail:
        asset_data["thumbnail_url"] = _generate_thumbnail_url(file_url)

    if asset_data["source_type"] == "AI_GENERATED":
        asset_data["ai_metadata"] = {"model": ai_model, "prompt": ai_prompt}

    # Merge kwargs (e.g., meta_mime_type, meta_width, meta_height, meta_file_size)
    # so that callers like upload_asset_file can pass extra ORM fields.
    for key, value in kwargs.items():
        if key not in asset_data and hasattr(AssetORM, key):
            asset_data[key] = value

    asset = AssetORM(**asset_data)
    db.add(asset)
    await db.flush()
    await db.commit()
    await db.refresh(asset)
    return asset


async def get_asset(db: AsyncSession, asset_id: str) -> Optional[AssetORM]:
    result = await db.execute(select(AssetORM).where(AssetORM.id == asset_id))
    return result.scalar_one_or_none()


async def list_assets(
    db: AsyncSession,
    source_type: Optional[str] = None,
    license_type: Optional[str] = None,
    category: Optional[str] = None,
    tags: Optional[List[str]] = None,
    status: str = "ACTIVE",
    tenant_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> Dict[str, Any]:
    query = select(AssetORM)
    if status:
        query = query.where(AssetORM.status == status)
    if source_type:
        query = query.where(AssetORM.source_type == source_type)
    if license_type:
        query = query.where(AssetORM.license_type == license_type)
    if category:
        query = query.where(AssetORM.category == category)
    if tenant_id:
        query = query.where(AssetORM.tenant_id == tenant_id)

    # tags 过滤在Python层执行（避免JSONB操作符跨dialect差异）
    result = await db.execute(query)
    items_all = result.scalars().all()
    if tags:
        tag_set = set(tags)
        items_all = [a for a in items_all if tag_set.intersection(set(a.tags or []))]

    total = len(items_all)
    items_all = sorted(items_all, key=lambda a: a.created_at or _now(), reverse=True)
    paginated = items_all[offset:offset + limit]

    return {
        "items": paginated,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


async def update_asset(
    db: AsyncSession, asset_id: str, **kwargs
) -> Optional[AssetORM]:
    asset = await get_asset(db, asset_id)
    if not asset:
        return None

    if asset.source_type == "AI_GENERATED":
        if "tags" in kwargs:
            tags = list(kwargs["tags"])
            if "AI辅助创作" not in tags:
                tags.append("AI辅助创作")
            kwargs["tags"] = tags
        if "ai_disclosure" in kwargs:
            kwargs["ai_disclosure"] = True

    exclude = {"id", "created_at"}
    for key, value in kwargs.items():
        if key not in exclude and hasattr(asset, key):
            setattr(asset, key, value)

    asset.updated_at = _now()
    await db.flush()
    await db.commit()
    await db.refresh(asset)
    return asset


async def delete_asset(db: AsyncSession, asset_id: str) -> bool:
    asset = await get_asset(db, asset_id)
    if not asset:
        return False
    asset.status = "DELETED"
    asset.updated_at = _now()
    await db.flush()
    await db.commit()
    return True


async def get_statistics(
    db: AsyncSession, tenant_id: Optional[str] = None
) -> Dict[str, Any]:
    query = select(AssetORM)
    if tenant_id:
        query = query.where(AssetORM.tenant_id == tenant_id)

    total_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = total_result.scalar() or 0

    active_q = query.where(AssetORM.status == "ACTIVE")
    active_result = await db.execute(
        select(func.count()).select_from(active_q.subquery())
    )
    active = active_result.scalar() or 0

    source_dist: Dict[str, int] = {}
    license_dist: Dict[str, int] = {}
    for st in ("OPERATOR_UPLOAD", "STOCK_API", "AI_GENERATED"):
        q = active_q.where(AssetORM.source_type == st)
        r = await db.execute(select(func.count()).select_from(q.subquery()))
        cnt = r.scalar() or 0
        if cnt:
            source_dist[st] = cnt
    for lt in ("OWNED", "LICENSED", "AI_GENERATED"):
        q = active_q.where(AssetORM.license_type == lt)
        r = await db.execute(select(func.count()).select_from(q.subquery()))
        cnt = r.scalar() or 0
        if cnt:
            license_dist[lt] = cnt

    op_count = source_dist.get("OPERATOR_UPLOAD", 0)
    active_total = sum(source_dist.values())
    op_ratio = (op_count / active_total * 100) if active_total > 0 else 0.0

    return {
        "total": total,
        "active": active,
        "source_distribution": source_dist,
        "license_distribution": license_dist,
        "operator_upload_ratio": round(op_ratio, 2),
    }


def _calculate_match_score(
    asset: AssetORM, content_title: str, content_body: str, content_tags: List[str]
) -> float:
    score = 0.0
    content_text = f"{content_title} {content_body}".lower()
    asset_tags = [t.lower() for t in (asset.tags or [])]

    for tag in asset_tags:
        if tag in content_text:
            score += 20.0
        if tag in [t.lower() for t in content_tags]:
            score += 30.0

    if asset.category and asset.category.lower() in content_text:
        score += 15.0

    if asset.source_type == "AI_GENERATED":
        score *= 0.9
    if asset.license_status == "EXPIRING_SOON":
        score *= 0.8

    return min(100.0, score)


async def recommend_assets(
    db: AsyncSession,
    content_title: str,
    content_body: str = "",
    content_tags: Optional[List[str]] = None,
    series_id: Optional[str] = None,
    target_count: int = 3,
    exclude_asset_ids: Optional[List[str]] = None,
    tenant_id: Optional[str] = None,
) -> Dict[str, Any]:
    content_tags = content_tags or []
    exclude_ids = set(exclude_asset_ids or [])

    query = select(AssetORM).where(AssetORM.status == "ACTIVE")
    if tenant_id:
        query = query.where(AssetORM.tenant_id == tenant_id)

    result = await db.execute(query)
    assets = result.scalars().all()

    scored: List[Dict[str, Any]] = []
    for asset in assets:
        if str(asset.id) in exclude_ids:
            continue
        score = _calculate_match_score(asset, content_title, content_body, content_tags)
        match_reason = "标签匹配"
        if series_id and asset.series_id == series_id:
            score += 25.0
            match_reason = f"系列匹配 ({series_id})"
        if score > 0:
            scored.append(
                {
                    "asset_id": str(asset.id),
                    "match_score": round(score, 1),
                    "match_reason": match_reason,
                }
            )

    scored.sort(key=lambda x: x["match_score"], reverse=True)
    recommendations = scored[:target_count]

    return {
        "recommendations": recommendations,
        "total_candidates": len(scored),
    }


async def clear_asset_pool(db: AsyncSession) -> None:
    await db.execute(delete(AssetORM))
    await db.commit()
