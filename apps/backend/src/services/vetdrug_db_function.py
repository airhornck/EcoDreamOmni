"""VetDrugDB Function — ORM持久化版本 (W14).

兽药批文真源：批文录入、宣称校验、到期预警、产品关联.
Aligned with PRD V3.1 §VetDrugDB / TASK_V2.7.1 FUNC-3.
"""

import re
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, delete

from src.models.vet_drug_orm import VetDrugEntryORM


# 批文号格式：兽药字 + 年份(4位) + 企业编号(3位) + 产品编号(4位)
# 示例: 兽药字220125001
_APPROVAL_NUMBER_RE = re.compile(r"^兽药(字|临字)\d{9,}$")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _validate_approval_number(number: str) -> bool:
    """校验批文号格式."""
    if not number:
        return False
    return bool(_APPROVAL_NUMBER_RE.match(number))


def drug_to_dict(drug: VetDrugEntryORM) -> Dict[str, Any]:
    return {
        "id": str(drug.id),
        "approval_number": drug.approval_number,
        "product_name": drug.product_name,
        "generic_name": drug.generic_name,
        "english_name": drug.english_name,
        "manufacturer": drug.manufacturer,
        "manufacturer_address": drug.manufacturer_address,
        "ingredients": drug.ingredients,
        "specifications": drug.specifications,
        "indications": drug.indications,
        "usage_dosage": drug.usage_dosage,
        "contraindications": drug.contraindications,
        "adverse_reactions": drug.adverse_reactions,
        "precautions": drug.precautions,
        "drug_interactions": drug.drug_interactions,
        "storage_conditions": drug.storage_conditions,
        "category": drug.category,
        "drug_type": drug.drug_type,
        "issue_date": drug.issue_date.isoformat() if drug.issue_date else None,
        "expiry_date": drug.expiry_date.isoformat() if drug.expiry_date else None,
        "status": drug.status,
        "applicable_species": drug.applicable_species or [],
        "target_diseases": drug.target_diseases or [],
        "tags": drug.tags or [],
        "brand_knowledge_id": drug.brand_knowledge_id,
        "created_by": drug.created_by,
        "updated_by": drug.updated_by,
        "data_source": drug.data_source,
        "tenant_id": drug.tenant_id,
        "created_at": drug.created_at.isoformat() if drug.created_at else None,
        "updated_at": drug.updated_at.isoformat() if drug.updated_at else None,
    }


async def create_drug(
    db: AsyncSession,
    approval_number: str,
    product_name: str,
    generic_name: Optional[str] = None,
    english_name: Optional[str] = None,
    manufacturer: Optional[str] = None,
    manufacturer_address: Optional[str] = None,
    ingredients: Optional[str] = None,
    specifications: Optional[str] = None,
    indications: Optional[str] = None,
    usage_dosage: Optional[str] = None,
    contraindications: Optional[str] = None,
    adverse_reactions: Optional[str] = None,
    precautions: Optional[str] = None,
    drug_interactions: Optional[str] = None,
    storage_conditions: Optional[str] = None,
    category: Optional[str] = None,
    drug_type: Optional[str] = None,
    issue_date: Optional[str] = None,
    expiry_date: Optional[str] = None,
    applicable_species: Optional[List[str]] = None,
    target_diseases: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
    brand_knowledge_id: Optional[str] = None,
    created_by: Optional[str] = None,
    tenant_id: Optional[str] = None,
    data_source: str = "manual",
    status: str = "ACTIVE",
) -> VetDrugEntryORM:
    """创建兽药批文条目 — 强制校验批文号格式."""
    if not _validate_approval_number(approval_number):
        raise ValueError(
            f"Invalid approval_number format: {approval_number}. Expected: 兽药字/兽药临字 + 10 digits"
        )

    def _parse_dt(s: Optional[str]) -> Optional[datetime]:
        if not s:
            return None
        try:
            return datetime.fromisoformat(s.replace("Z", "+00:00"))
        except ValueError:
            return None

    drug = VetDrugEntryORM(
        approval_number=approval_number,
        product_name=product_name,
        generic_name=generic_name,
        english_name=english_name,
        manufacturer=manufacturer,
        manufacturer_address=manufacturer_address,
        ingredients=ingredients,
        specifications=specifications,
        indications=indications,
        usage_dosage=usage_dosage,
        contraindications=contraindications,
        adverse_reactions=adverse_reactions,
        precautions=precautions,
        drug_interactions=drug_interactions,
        storage_conditions=storage_conditions,
        category=category,
        drug_type=drug_type,
        issue_date=_parse_dt(issue_date),
        expiry_date=_parse_dt(expiry_date),
        applicable_species=applicable_species or [],
        target_diseases=target_diseases or [],
        tags=tags or [],
        brand_knowledge_id=brand_knowledge_id,
        created_by=created_by,
        data_source=data_source,
        status=status,
        tenant_id=tenant_id,
    )
    db.add(drug)
    await db.flush()
    await db.commit()
    await db.refresh(drug)
    return drug


async def get_drug(db: AsyncSession, drug_id: str) -> Optional[VetDrugEntryORM]:
    result = await db.execute(
        select(VetDrugEntryORM).where(VetDrugEntryORM.id == drug_id)
    )
    return result.scalar_one_or_none()


async def get_drug_by_approval_number(
    db: AsyncSession, approval_number: str
) -> Optional[VetDrugEntryORM]:
    result = await db.execute(
        select(VetDrugEntryORM).where(
            VetDrugEntryORM.approval_number == approval_number
        )
    )
    return result.scalar_one_or_none()


async def list_drugs(
    db: AsyncSession,
    product_name: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    tenant_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> Dict[str, Any]:
    query = select(VetDrugEntryORM)
    if product_name:
        query = query.where(VetDrugEntryORM.product_name.ilike(f"%{product_name}%"))
    if category:
        query = query.where(VetDrugEntryORM.category == category)
    if status:
        query = query.where(VetDrugEntryORM.status == status)
    if tenant_id:
        query = query.where(VetDrugEntryORM.tenant_id == tenant_id)

    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar() or 0

    query = query.order_by(desc(VetDrugEntryORM.updated_at)).offset(offset).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()

    return {"items": list(items), "total": total, "limit": limit, "offset": offset}


async def update_drug(
    db: AsyncSession, drug_id: str, **kwargs
) -> Optional[VetDrugEntryORM]:
    drug = await get_drug(db, drug_id)
    if not drug:
        return None

    exclude = {"id", "created_at", "approval_number"}  # 批文号不可修改
    for key, value in kwargs.items():
        if key not in exclude and hasattr(drug, key):
            setattr(drug, key, value)

    drug.updated_at = _now()
    await db.flush()
    await db.commit()
    await db.refresh(drug)
    return drug


async def delete_drug(db: AsyncSession, drug_id: str) -> bool:
    drug = await get_drug(db, drug_id)
    if not drug:
        return False
    await db.delete(drug)
    await db.flush()
    await db.commit()
    return True


async def verify_claims(
    db: AsyncSession,
    approval_number: str,
    claimed_indications: List[str],
    claimed_effects: List[str],
) -> Dict[str, Any]:
    """合规校验：输入内容宣称 → 校验与批文一致性.

    Returns:
        {"valid": bool, "violations": [str], "approved_indications": [str]}
    """
    drug = await get_drug_by_approval_number(db, approval_number)
    if not drug:
        return {
            "valid": False,
            "violations": [f"Approval number {approval_number} not found in database"],
            "approved_indications": [],
        }

    if drug.status != "ACTIVE":
        return {
            "valid": False,
            "violations": [f"Approval status is {drug.status}, not ACTIVE"],
            "approved_indications": drug.indications.split(",") if drug.indications else [],
        }

    approved = drug.indications or ""
    violations = []

    for claim in claimed_indications + claimed_effects:
        if claim and claim not in approved:
            violations.append(f"Claim '{claim}' not in approved indications: {approved}")

    return {
        "valid": len(violations) == 0,
        "violations": violations,
        "approved_indications": approved.split(",") if approved else [],
    }


async def get_expiry_warnings(
    db: AsyncSession,
    days_ahead: int = 90,
    tenant_id: Optional[str] = None,
) -> List[VetDrugEntryORM]:
    """批文到期预警 — 默认提前90天."""
    threshold = _now() + timedelta(days=days_ahead)
    query = (
        select(VetDrugEntryORM)
        .where(VetDrugEntryORM.expiry_date <= threshold)
        .where(VetDrugEntryORM.status == "ACTIVE")
    )
    if tenant_id:
        query = query.where(VetDrugEntryORM.tenant_id == tenant_id)
    query = query.order_by(VetDrugEntryORM.expiry_date)
    result = await db.execute(query)
    return list(result.scalars().all())


async def clear_vet_drug_db(db: AsyncSession) -> None:
    await db.execute(delete(VetDrugEntryORM))
    await db.commit()
