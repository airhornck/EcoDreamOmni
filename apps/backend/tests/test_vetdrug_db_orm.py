"""VetDrugDB Function ORM tests — W14 Red-Green.

Aligned with PRD V3.1 §VetDrugDB / TASK_V2.7.1 FUNC-3.
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone, timedelta

from src.services import vetdrug_db_function as vdf

pytestmark = pytest.mark.asyncio(loop_scope="function")


@pytest_asyncio.fixture
async def db_session(db, skip_if_no_db):
    return db


# =============================================================================
# VD-1: 批文录入 + 格式校验
# =============================================================================

async def test_create_drug_with_valid_approval_number(db_session: AsyncSession):
    """🔴 批文号格式强制校验 — 兽药字xxxxxxxxx."""
    drug = await vdf.create_drug(
        db=db_session,
        approval_number="兽药字220125001",
        product_name="宠安宁驱虫滴剂",
        generic_name="非泼罗尼溶液",
        manufacturer="某某兽药有限公司",
        indications="用于犬、猫体外驱虫",
        category="化学药品",
        drug_type="非处方药",
        created_by="operator",
    )
    assert drug.id is not None
    assert drug.approval_number == "兽药字220125001"


async def test_create_drug_invalid_approval_number(db_session: AsyncSession):
    """🔴 无效批文号100%拦截."""
    with pytest.raises(ValueError, match="Invalid approval_number"):
        await vdf.create_drug(
            db=db_session,
            approval_number="INVALID_NUMBER",
            product_name="假药",
        )


async def test_create_drug_missing_approval_number(db_session: AsyncSession):
    """🔴 缺失批文号100%拦截."""
    with pytest.raises(ValueError, match="Invalid approval_number"):
        await vdf.create_drug(
            db=db_session,
            approval_number="",
            product_name="假药",
        )


async def test_create_drug_licensed_format(db_session: AsyncSession):
    """🔴 兽药临字格式也接受."""
    drug = await vdf.create_drug(
        db=db_session,
        approval_number="兽药临字2300123456",
        product_name="试验药品",
    )
    assert drug.approval_number == "兽药临字2300123456"


# =============================================================================
# VD-2: 宣称校验
# =============================================================================

async def test_verify_claims_valid(db_session: AsyncSession):
    """🔴 宣称与批文一致性校验 — 通过."""
    drug = await vdf.create_drug(
        db=db_session,
        approval_number="兽药字220125002",
        product_name="驱虫药B",
        indications="驱杀跳蚤、蜱虫",
    )
    result = await vdf.verify_claims(
        db=db_session,
        approval_number="兽药字220125002",
        claimed_indications=["驱杀跳蚤"],
        claimed_effects=[],
    )
    assert result["valid"] is True
    assert len(result["violations"]) == 0


async def test_verify_claims_invalid(db_session: AsyncSession):
    """🔴 宣称与批文一致性校验 — 拦截超范围宣称."""
    drug = await vdf.create_drug(
        db=db_session,
        approval_number="兽药字220125003",
        product_name="驱虫药C",
        indications="驱杀跳蚤",
    )
    result = await vdf.verify_claims(
        db=db_session,
        approval_number="兽药字220125003",
        claimed_indications=["驱杀跳蚤", "治疗皮肤病", "根治耳螨"],
        claimed_effects=[],
    )
    assert result["valid"] is False
    assert len(result["violations"]) >= 2


async def test_verify_claims_not_found(db_session: AsyncSession):
    """🔴 查询不存在的批文号."""
    result = await vdf.verify_claims(
        db=db_session,
        approval_number="兽药字999999999",
        claimed_indications=["驱虫"],
        claimed_effects=[],
    )
    assert result["valid"] is False
    assert "not found" in result["violations"][0]


async def test_verify_claims_expired_status(db_session: AsyncSession):
    """🔴 过期批文拦截."""
    drug = await vdf.create_drug(
        db=db_session,
        approval_number="兽药字220125004",
        product_name="过期药",
        indications="驱虫",
        status="EXPIRED",
    )
    result = await vdf.verify_claims(
        db=db_session,
        approval_number="兽药字220125004",
        claimed_indications=["驱虫"],
        claimed_effects=[],
    )
    assert result["valid"] is False
    assert "EXPIRED" in result["violations"][0]


# =============================================================================
# VD-3: 到期预警
# =============================================================================

async def test_expiry_warning(db_session: AsyncSession):
    """🔴 提前90天到期预警."""
    soon = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    await vdf.create_drug(
        db=db_session,
        approval_number="兽药字220125005",
        product_name="即将到期药",
        expiry_date=soon,
    )
    warnings = await vdf.get_expiry_warnings(db_session, days_ahead=90)
    assert len(warnings) >= 1
    assert any(d.approval_number == "兽药字220125005" for d in warnings)


async def test_no_expiry_warning_for_distant(db_session: AsyncSession):
    """🔴 远期到期不预警."""
    far = (datetime.now(timezone.utc) + timedelta(days=200)).isoformat()
    await vdf.create_drug(
        db=db_session,
        approval_number="兽药字220125006",
        product_name="远期药",
        expiry_date=far,
    )
    warnings = await vdf.get_expiry_warnings(db_session, days_ahead=90)
    assert not any(d.approval_number == "兽药字220125006" for d in warnings)


# =============================================================================
# VD-4: CRUD
# =============================================================================

async def test_drug_crud(db_session: AsyncSession):
    """🔴 完整CRUD."""
    drug = await vdf.create_drug(
        db=db_session,
        approval_number="兽药字220125007",
        product_name="CRUD药",
    )
    # Read
    found = await vdf.get_drug(db_session, str(drug.id))
    assert found is not None

    # Update (approval_number不可改)
    updated = await vdf.update_drug(
        db_session, str(drug.id), product_name="CRUD药V2"
    )
    assert updated is not None
    assert updated.product_name == "CRUD药V2"
    assert updated.approval_number == "兽药字220125007"

    # Delete
    deleted = await vdf.delete_drug(db_session, str(drug.id))
    assert deleted is True
    assert await vdf.get_drug(db_session, str(drug.id)) is None


async def test_list_drugs(db_session: AsyncSession):
    """🔴 列表查询."""
    await vdf.clear_vet_drug_db(db_session)
    for i in range(3):
        await vdf.create_drug(
            db=db_session,
            approval_number=f"兽药字2201251{i:02d}",
            product_name=f"药{i}",
            category="化学药品",
        )
    result = await vdf.list_drugs(db_session, category="化学药品")
    assert result["total"] == 3


async def test_clear_vet_drug_db(db_session: AsyncSession):
    """🔴 清空."""
    await vdf.create_drug(
        db=db_session,
        approval_number="兽药字220125999",
        product_name="清空的药",
    )
    await vdf.clear_vet_drug_db(db_session)
    result = await vdf.list_drugs(db_session)
    assert result["total"] == 0
