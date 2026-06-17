"""ProhibitedWord Function — independent word library for compliance.

Aligned with PRD V3.1 §Compliance.
"""

import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func

from src.models.prohibited_word_orm import ProhibitedWordORM, ContentGuidelineORM


def _now() -> datetime:
    return datetime.now(timezone.utc)


def word_to_dict(word: ProhibitedWordORM) -> Dict[str, Any]:
    return {
        "id": str(word.id),
        "word": word.word,
        "category": word.category,
        "severity": word.severity,
        "platform": word.platform,
        "match_type": word.match_type,
        "is_enabled": word.is_enabled,
        "description": word.description,
        "tenant_id": word.tenant_id,
        "created_by": word.created_by,
        "updated_by": word.updated_by,
        "created_at": word.created_at.isoformat() if word.created_at else None,
        "updated_at": word.updated_at.isoformat() if word.updated_at else None,
    }


def guideline_to_dict(g: ContentGuidelineORM) -> Dict[str, Any]:
    return {
        "id": str(g.id),
        "name": g.name,
        "category": g.category,
        "description": g.description,
        "rules_json": g.rules_json,
        "platform": g.platform,
        "is_enabled": g.is_enabled,
        "tenant_id": g.tenant_id,
        "created_by": g.created_by,
        "updated_by": g.updated_by,
        "created_at": g.created_at.isoformat() if g.created_at else None,
        "updated_at": g.updated_at.isoformat() if g.updated_at else None,
    }


# ─── CRUD: ProhibitedWord ───

async def create_word(
    db: AsyncSession,
    word: str,
    category: str = "general",
    severity: str = "L2",
    platform: str = "universal",
    match_type: str = "exact",
    is_enabled: bool = True,
    description: Optional[str] = None,
    tenant_id: Optional[str] = None,
    created_by: str = "system",
) -> ProhibitedWordORM:
    w = ProhibitedWordORM(
        word=word,
        category=category,
        severity=severity,
        platform=platform,
        match_type=match_type,
        is_enabled=is_enabled,
        description=description,
        tenant_id=tenant_id,
        created_by=created_by,
    )
    db.add(w)
    await db.commit()
    await db.refresh(w)
    return w


async def get_word(db: AsyncSession, word_id: str) -> Optional[ProhibitedWordORM]:
    result = await db.execute(select(ProhibitedWordORM).where(ProhibitedWordORM.id == word_id))
    return result.scalar_one_or_none()


async def list_words(
    db: AsyncSession,
    platform: Optional[str] = None,
    category: Optional[str] = None,
    severity: Optional[str] = None,
    is_enabled: Optional[bool] = True,
    tenant_id: Optional[str] = None,
    limit: int = 200,
    offset: int = 0,
) -> Dict[str, Any]:
    query = select(ProhibitedWordORM)
    if platform:
        query = query.where(ProhibitedWordORM.platform == platform)
    if category:
        query = query.where(ProhibitedWordORM.category == category)
    if severity:
        query = query.where(ProhibitedWordORM.severity == severity)
    if is_enabled is not None:
        query = query.where(ProhibitedWordORM.is_enabled == is_enabled)
    if tenant_id is not None:
        query = query.where(ProhibitedWordORM.tenant_id == tenant_id)

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar() or 0

    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()
    return {"items": [word_to_dict(w) for w in items], "total": total, "limit": limit, "offset": offset}


async def update_word(db: AsyncSession, word_id: str, **kwargs) -> Optional[ProhibitedWordORM]:
    result = await db.execute(select(ProhibitedWordORM).where(ProhibitedWordORM.id == word_id))
    w = result.scalar_one_or_none()
    if not w:
        return None
    for key, value in kwargs.items():
        if hasattr(w, key):
            setattr(w, key, value)
    w.updated_at = _now()
    await db.commit()
    await db.refresh(w)
    return w


async def delete_word(db: AsyncSession, word_id: str) -> bool:
    result = await db.execute(select(ProhibitedWordORM).where(ProhibitedWordORM.id == word_id))
    w = result.scalar_one_or_none()
    if not w:
        return False
    await db.delete(w)
    await db.commit()
    return True


async def clear_words(db: AsyncSession) -> None:
    await db.execute(delete(ProhibitedWordORM))
    await db.commit()


# ─── Detection ───

async def detect_words(
    db: AsyncSession,
    text: str,
    platform: str = "universal",
    tenant_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Detect prohibited words in text. Returns list of matched word records."""
    query = select(ProhibitedWordORM).where(
        ProhibitedWordORM.is_enabled
    ).where(
        (ProhibitedWordORM.platform == platform) | (ProhibitedWordORM.platform == "universal")
    )
    if tenant_id is not None:
        query = query.where(ProhibitedWordORM.tenant_id == tenant_id)

    result = await db.execute(query)
    words = result.scalars().all()

    matches = []
    text_lower = text.lower()
    for w in words:
        if w.match_type == "exact":
            if w.word.lower() in text_lower:
                matches.append(word_to_dict(w))
        elif w.match_type == "regex":
            if re.search(w.word, text, re.IGNORECASE):
                matches.append(word_to_dict(w))
        elif w.match_type == "fuzzy":
            # MVP: simple substring for fuzzy
            if w.word.lower() in text_lower:
                matches.append(word_to_dict(w))
    return matches


# ─── Seed default words ───

_DEFAULT_WORDS = [
    # L1: Prescription drugs (migrated from compliance_engine.py)
    {"word": "阿莫西林", "category": "prescription", "severity": "L1", "platform": "universal"},
    {"word": "布洛芬", "category": "prescription", "severity": "L1", "platform": "universal"},
    {"word": "对乙酰氨基酚", "category": "prescription", "severity": "L1", "platform": "universal"},
    {"word": "头孢", "category": "prescription", "severity": "L1", "platform": "universal"},
    {"word": "青霉素", "category": "prescription", "severity": "L1", "platform": "universal"},
    {"word": "红霉素", "category": "prescription", "severity": "L1", "platform": "universal"},
    {"word": "甲硝唑", "category": "prescription", "severity": "L1", "platform": "universal"},
    {"word": "庆大霉素", "category": "prescription", "severity": "L1", "platform": "universal"},
    {"word": "土霉素", "category": "prescription", "severity": "L1", "platform": "universal"},
    {"word": "诺氟沙星", "category": "prescription", "severity": "L1", "platform": "universal"},
    {"word": "氧氟沙星", "category": "prescription", "severity": "L1", "platform": "universal"},
    {"word": "环丙沙星", "category": "prescription", "severity": "L1", "platform": "universal"},
    {"word": "地塞米松", "category": "prescription", "severity": "L1", "platform": "universal"},
    {"word": "泼尼松", "category": "prescription", "severity": "L1", "platform": "universal"},
    {"word": "强的松", "category": "prescription", "severity": "L1", "platform": "universal"},
    {"word": "胰岛素", "category": "prescription", "severity": "L1", "platform": "universal"},
    {"word": "安定", "category": "prescription", "severity": "L1", "platform": "universal"},
    {"word": "阿司匹林", "category": "prescription", "severity": "L1", "platform": "universal"},
    {"word": "处方药", "category": "prescription", "severity": "L1", "platform": "universal"},
    {"word": "处方药物", "category": "prescription", "severity": "L1", "platform": "universal"},
    {"word": "人用药物", "category": "prescription", "severity": "L1", "platform": "universal"},
    {"word": "人用药", "category": "prescription", "severity": "L1", "platform": "universal"},
    # L2: Inducement (from comment_hub.py patterns)
    {"word": "加微信", "category": "inducement", "severity": "L2", "platform": "universal"},
    {"word": "扫码", "category": "inducement", "severity": "L2", "platform": "universal"},
    {"word": "点击链接", "category": "inducement", "severity": "L2", "platform": "universal"},
    {"word": "私信我", "category": "inducement", "severity": "L2", "platform": "universal"},
    {"word": "加我", "category": "inducement", "severity": "L2", "platform": "universal"},
    # L3: General sensitive
    {"word": "绝对化用语", "category": "sensitive", "severity": "L3", "platform": "universal"},
]


async def seed_default_words(
    db: AsyncSession,
    created_by: str = "system",
    tenant_id: Optional[str] = None,
) -> Dict[str, int]:
    """Seed default prohibited words. Idempotent by word+platform+tenant."""
    created = 0
    skipped = 0
    for data in _DEFAULT_WORDS:
        result = await db.execute(
            select(ProhibitedWordORM)
            .where(ProhibitedWordORM.word == data["word"])
            .where(ProhibitedWordORM.platform == data["platform"])
            .where(ProhibitedWordORM.tenant_id == tenant_id)
        )
        existing = result.scalar_one_or_none()
        if existing:
            skipped += 1
            continue
        w = ProhibitedWordORM(
            word=data["word"],
            category=data["category"],
            severity=data["severity"],
            platform=data["platform"],
            match_type="exact",
            is_enabled=True,
            tenant_id=tenant_id,
            created_by=created_by,
        )
        db.add(w)
        created += 1
    await db.commit()
    return {"created": created, "skipped": skipped}


# ─── CRUD: ContentGuideline ───

async def create_guideline(
    db: AsyncSession,
    name: str,
    category: str,
    rules_json: str = "{}",
    platform: str = "universal",
    description: Optional[str] = None,
    is_enabled: bool = True,
    tenant_id: Optional[str] = None,
    created_by: str = "system",
) -> ContentGuidelineORM:
    g = ContentGuidelineORM(
        name=name,
        category=category,
        rules_json=rules_json,
        platform=platform,
        description=description,
        is_enabled=is_enabled,
        tenant_id=tenant_id,
        created_by=created_by,
    )
    db.add(g)
    await db.commit()
    await db.refresh(g)
    return g


async def list_guidelines(
    db: AsyncSession,
    platform: Optional[str] = None,
    category: Optional[str] = None,
    is_enabled: Optional[bool] = True,
    limit: int = 50,
    offset: int = 0,
) -> Dict[str, Any]:
    query = select(ContentGuidelineORM)
    if platform:
        query = query.where(ContentGuidelineORM.platform == platform)
    if category:
        query = query.where(ContentGuidelineORM.category == category)
    if is_enabled is not None:
        query = query.where(ContentGuidelineORM.is_enabled == is_enabled)

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar() or 0

    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()
    return {"items": [guideline_to_dict(g) for g in items], "total": total, "limit": limit, "offset": offset}
