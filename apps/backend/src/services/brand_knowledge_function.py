"""BrandKnowledge Function — ORM持久化版本 (W14).

Knowledge base with versioning + pgvector RAG support.
Aligned with PRD V3.1 §BrandKnowledge / TASK_V2.7.1 FUNC-2.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, delete

from src.models.brand_knowledge_orm import BrandKnowledgeEntryORM
from src.services.embedding_service import get_embedding


def _now() -> datetime:
    return datetime.now(timezone.utc)


def entry_to_dict(entry: BrandKnowledgeEntryORM) -> Dict[str, Any]:
    """ORM → dict（兼容API序列化）."""
    return {
        "id": str(entry.id),
        "entry_type": entry.entry_type,
        "name": entry.name,
        "content": entry.content,
        "product_id": entry.product_id,
        "approval_number": entry.approval_number,
        "sku_code": entry.sku_code,
        "brand_name": entry.brand_name,
        "prohibited_claims": entry.prohibited_claims or [],
        "required_disclaimers": entry.required_disclaimers or [],
        "version": entry.version,
        "is_latest": entry.is_latest,
        "parent_id": str(entry.parent_id) if entry.parent_id else None,
        "asset_ids": entry.asset_ids or [],
        "created_by": entry.created_by,
        "updated_by": entry.updated_by,
        "change_reason": entry.change_reason,
        "tenant_id": entry.tenant_id,
        "created_at": entry.created_at.isoformat() if entry.created_at else None,
        "updated_at": entry.updated_at.isoformat() if entry.updated_at else None,
    }


async def create_entry(
    db: AsyncSession,
    entry_type: str,
    name: str,
    content: str,
    product_id: Optional[str] = None,
    approval_number: Optional[str] = None,
    sku_code: Optional[str] = None,
    brand_name: Optional[str] = None,
    prohibited_claims: Optional[List[str]] = None,
    required_disclaimers: Optional[List[str]] = None,
    asset_ids: Optional[List[str]] = None,
    created_by: str = "system",
    tenant_id: Optional[str] = None,
) -> BrandKnowledgeEntryORM:
    """创建知识条目（自动设为最新版本）."""
    entry = BrandKnowledgeEntryORM(
        entry_type=entry_type,
        name=name,
        content=content,
        product_id=product_id,
        approval_number=approval_number,
        sku_code=sku_code,
        brand_name=brand_name,
        prohibited_claims=prohibited_claims or [],
        required_disclaimers=required_disclaimers or [],
        is_latest=True,
        asset_ids=asset_ids or [],
        created_by=created_by,
        tenant_id=tenant_id,
    )
    db.add(entry)
    await db.flush()

    # Generate embedding for RAG (non-blocking on failure)
    try:
        text_for_embedding = f"{name}\n{content}"
        embedding = await get_embedding(text_for_embedding)
        if embedding:
            entry.embedding = embedding
    except Exception:
        pass

    await db.commit()
    await db.refresh(entry)
    return entry


async def get_entry(
    db: AsyncSession, entry_id: str
) -> Optional[BrandKnowledgeEntryORM]:
    result = await db.execute(
        select(BrandKnowledgeEntryORM).where(BrandKnowledgeEntryORM.id == entry_id)
    )
    return result.scalar_one_or_none()


async def get_entry_by_product(
    db: AsyncSession, product_id: str
) -> Optional[BrandKnowledgeEntryORM]:
    result = await db.execute(
        select(BrandKnowledgeEntryORM)
        .where(BrandKnowledgeEntryORM.product_id == product_id)
        .where(BrandKnowledgeEntryORM.is_latest)
        .order_by(desc(BrandKnowledgeEntryORM.version))
        .limit(1)
    )
    return result.scalar_one_or_none()


async def list_entries(
    db: AsyncSession,
    entry_type: Optional[str] = None,
    brand_name: Optional[str] = None,
    is_latest: Optional[bool] = True,
    tenant_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> Dict[str, Any]:
    query = select(BrandKnowledgeEntryORM)
    if entry_type:
        query = query.where(BrandKnowledgeEntryORM.entry_type == entry_type)
    if brand_name:
        query = query.where(BrandKnowledgeEntryORM.brand_name == brand_name)
    if is_latest is not None:
        query = query.where(BrandKnowledgeEntryORM.is_latest == is_latest)
    if tenant_id:
        query = query.where(BrandKnowledgeEntryORM.tenant_id == tenant_id)

    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar() or 0

    query = query.order_by(desc(BrandKnowledgeEntryORM.updated_at)).offset(offset).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()

    return {"items": list(items), "total": total, "limit": limit, "offset": offset}


async def update_entry(
    db: AsyncSession,
    entry_id: str,
    updated_by: str,
    change_reason: Optional[str] = None,
    **kwargs,
) -> Optional[BrandKnowledgeEntryORM]:
    """更新知识条目 — 自动创建新版本（旧版本保留为历史）."""
    old_entry = await get_entry(db, entry_id)
    if not old_entry:
        return None

    # 将旧版本标记为非最新
    old_entry.is_latest = False
    await db.flush()
    await db.commit()

    # 创建新版本
    new_data = {
        "entry_type": kwargs.get("entry_type", old_entry.entry_type),
        "name": kwargs.get("name", old_entry.name),
        "content": kwargs.get("content", old_entry.content),
        "product_id": kwargs.get("product_id", old_entry.product_id),
        "approval_number": kwargs.get("approval_number", old_entry.approval_number),
        "sku_code": kwargs.get("sku_code", old_entry.sku_code),
        "brand_name": kwargs.get("brand_name", old_entry.brand_name),
        "prohibited_claims": kwargs.get("prohibited_claims", old_entry.prohibited_claims),
        "required_disclaimers": kwargs.get("required_disclaimers", old_entry.required_disclaimers),
        "asset_ids": kwargs.get("asset_ids", old_entry.asset_ids),
        "version": old_entry.version + 1,
        "is_latest": True,
        "parent_id": old_entry.id,
        "created_by": old_entry.created_by,
        "updated_by": updated_by,
        "change_reason": change_reason or "内容更新",
        "tenant_id": old_entry.tenant_id,
    }

    new_entry = BrandKnowledgeEntryORM(**new_data)
    db.add(new_entry)
    await db.flush()

    # Re-generate embedding for new version (non-blocking on failure)
    try:
        text_for_embedding = f"{new_data['name']}\n{new_data['content']}"
        embedding = await get_embedding(text_for_embedding)
        if embedding:
            new_entry.embedding = embedding
    except Exception:
        pass

    await db.commit()
    await db.refresh(new_entry)
    return new_entry


async def rollback_entry(
    db: AsyncSession, entry_id: str, changed_by: str, reason: str
) -> Optional[BrandKnowledgeEntryORM]:
    """回滚到指定版本 — 基于parent_id链."""
    target = await get_entry(db, entry_id)
    if not target:
        return None

    # 找到当前最新版本
    result = await db.execute(
        select(BrandKnowledgeEntryORM)
        .where(BrandKnowledgeEntryORM.product_id == target.product_id)
        .where(BrandKnowledgeEntryORM.is_latest)
        .order_by(desc(BrandKnowledgeEntryORM.version))
        .limit(1)
    )
    current_latest = result.scalar_one_or_none()
    if current_latest:
        current_latest.is_latest = False
        await db.flush()
        await db.commit()

    # 创建回滚版本（复制目标版本内容）
    rollback_data = {
        "entry_type": target.entry_type,
        "name": target.name,
        "content": target.content,
        "product_id": target.product_id,
        "approval_number": target.approval_number,
        "sku_code": target.sku_code,
        "brand_name": target.brand_name,
        "prohibited_claims": target.prohibited_claims,
        "required_disclaimers": target.required_disclaimers,
        "asset_ids": target.asset_ids,
        "version": (current_latest.version if current_latest else target.version) + 1,
        "is_latest": True,
        "parent_id": target.id,
        "created_by": target.created_by,
        "updated_by": changed_by,
        "change_reason": f"回滚到版本 {target.version}: {reason}",
        "tenant_id": target.tenant_id,
    }
    new_entry = BrandKnowledgeEntryORM(**rollback_data)
    db.add(new_entry)
    await db.flush()
    await db.commit()
    await db.refresh(new_entry)
    return new_entry


async def delete_entry(db: AsyncSession, entry_id: str) -> bool:
    entry = await get_entry(db, entry_id)
    if not entry:
        return False
    await db.delete(entry)
    await db.flush()
    await db.commit()
    return True


async def search_by_content(
    db: AsyncSession,
    query_text: str,
    entry_type: Optional[str] = None,
    tenant_id: Optional[str] = None,
    limit: int = 10,
    use_vector: bool = True,
) -> List[BrandKnowledgeEntryORM]:
    """文本检索 — 优先pgvector语义检索，回退到name/content模糊匹配."""
    # Try vector search first if requested
    if use_vector:
        try:
            from src.services.embedding_service import get_embedding
            query_embedding = await get_embedding(query_text)
            if query_embedding:
                # pgvector cosine distance search
                from sqlalchemy import text
                # Use raw SQL for pgvector <=> operator
                vector_sql = text("""
                    SELECT id FROM brand_knowledge_entries
                    WHERE is_latest = true
                    AND embedding IS NOT NULL
                    ORDER BY embedding <=> :query_embedding
                    LIMIT :limit
                """)
                result = await db.execute(
                    vector_sql,
                    {
                        "query_embedding": str(query_embedding),
                        "limit": limit,
                    },
                )
                ids = [row[0] for row in result.fetchall()]
                if ids:
                    # Fetch full records
                    entries_result = await db.execute(
                        select(BrandKnowledgeEntryORM).where(
                            BrandKnowledgeEntryORM.id.in_(ids)
                        )
                    )
                    entries = list(entries_result.scalars().all())
                    # Preserve order from vector search
                    entry_map = {e.id: e for e in entries}
                    ordered = [entry_map[i] for i in ids if i in entry_map]
                    # Filter by entry_type/tenant if specified
                    if entry_type:
                        ordered = [e for e in ordered if e.entry_type == entry_type]
                    if tenant_id:
                        ordered = [e for e in ordered if e.tenant_id == tenant_id]
                    return ordered[:limit]
        except Exception:
            # Fall back to text search on any vector error
            pass

    # Fallback: ILIKE text search
    pattern = f"%{query_text}%"
    sql = select(BrandKnowledgeEntryORM).where(
        (BrandKnowledgeEntryORM.name.ilike(pattern))
        | (BrandKnowledgeEntryORM.content.ilike(pattern))
    )
    if entry_type:
        sql = sql.where(BrandKnowledgeEntryORM.entry_type == entry_type)
    if tenant_id:
        sql = sql.where(BrandKnowledgeEntryORM.tenant_id == tenant_id)
    sql = sql.where(BrandKnowledgeEntryORM.is_latest).limit(limit)
    result = await db.execute(sql)
    return list(result.scalars().all())


async def get_prohibited_claims_for_product(
    db: AsyncSession, product_id: str
) -> List[str]:
    """获取指定产品的全部禁用宣称（供ComplianceGuard调用）."""
    entry = await get_entry_by_product(db, product_id)
    if not entry:
        return []
    return list(entry.prohibited_claims or [])


async def clear_brand_knowledge(db: AsyncSession) -> None:
    await db.execute(delete(BrandKnowledgeEntryORM))
    await db.commit()
