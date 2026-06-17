"""BrandKnowledge Function ORM tests — W14 Red-Green.

Aligned with PRD V3.1 §BrandKnowledge / TASK_V2.7.1 FUNC-2.
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from src.services import brand_knowledge_function as bkf

pytestmark = pytest.mark.asyncio(loop_scope="function")


@pytest_asyncio.fixture
async def db_session(db, skip_if_no_db):
    return db


# =============================================================================
# BK-1: 知识条目CRUD + 版本化
# =============================================================================

async def test_create_product_entry(db_session: AsyncSession):
    """🔴 创建产品SKU条目 — approval_number必填."""
    entry = await bkf.create_entry(
        db=db_session,
        entry_type="product_sku",
        name="宠安宁®驱虫滴剂",
        content="每月一次体外驱虫，适用于猫咪和狗狗",
        product_id="PROD_001",
        approval_number="兽药字220125001",
        sku_code="SKU_CA_001",
        brand_name="宠安宁",
        prohibited_claims=["100%有效", "根治", "立即见效"],
        required_disclaimers=["请遵医嘱", "兽药广告审查批准文号"],
        created_by="operator_a",
    )
    assert entry.id is not None
    assert entry.entry_type == "product_sku"
    assert entry.approval_number == "兽药字220125001"
    assert entry.is_latest is True
    assert entry.version == 1


async def test_update_creates_new_version(db_session: AsyncSession):
    """🔴 更新自动创建新版本 — 修改双人复核留痕."""
    entry = await bkf.create_entry(
        db=db_session,
        entry_type="faq",
        name="FAQ-001",
        content="旧内容",
        created_by="operator_a",
    )
    v1_id = str(entry.id)

    updated = await bkf.update_entry(
        db=db_session,
        entry_id=v1_id,
        updated_by="operator_b",
        change_reason="补充禁忌症说明（双人复核通过）",
        content="新内容 — 补充禁忌症说明",
    )
    assert updated is not None
    assert updated.version == 2
    assert updated.is_latest is True
    assert updated.parent_id == entry.id

    # 旧版本标记为非最新
    old = await bkf.get_entry(db_session, v1_id)
    assert old is not None
    assert old.is_latest is False


async def test_rollback_to_version(db_session: AsyncSession):
    """🔴 版本回滚功能."""
    entry = await bkf.create_entry(
        db=db_session,
        entry_type="brand_info",
        name="品牌介绍",
        content="v1内容",
        created_by="operator_a",
    )
    v1_id = str(entry.id)

    await bkf.update_entry(
        db=db_session,
        entry_id=v1_id,
        updated_by="operator_b",
        content="v2内容",
    )

    rolled = await bkf.rollback_entry(
        db=db_session,
        entry_id=v1_id,
        changed_by="admin",
        reason="v2内容有误，回滚到v1",
    )
    assert rolled is not None
    assert rolled.version == 3
    assert rolled.content == "v1内容"
    assert "回滚到版本 1" in (rolled.change_reason or "")


async def test_search_by_content(db_session: AsyncSession):
    """🔴 内容检索 — RAG接口MVP（文本模糊匹配）."""
    await bkf.create_entry(
        db=db_session,
        entry_type="category_knowledge",
        name="猫咪驱虫知识",
        content="猫咪需要每月进行体外驱虫，使用含有非泼罗尼成分的滴剂",
        created_by="operator_a",
    )
    results = await bkf.search_by_content(
        db=db_session, query_text="非泼罗尼", entry_type="category_knowledge"
    )
    assert len(results) >= 1
    assert any("非泼罗尼" in r.content for r in results)


async def test_get_prohibited_claims_for_product(db_session: AsyncSession):
    """🔴 RAG结果含prohibited_claims 100%拦截."""
    await bkf.create_entry(
        db=db_session,
        entry_type="product_sku",
        name="产品A",
        content="产品说明",
        product_id="PROD_X",
        prohibited_claims=["绝对有效", "根治一切寄生虫"],
        created_by="operator_a",
    )
    claims = await bkf.get_prohibited_claims_for_product(db_session, "PROD_X")
    assert "绝对有效" in claims
    assert "根治一切寄生虫" in claims


async def test_list_entries_by_brand(db_session: AsyncSession):
    """🔴 按品牌筛选."""
    await bkf.create_entry(
        db=db_session,
        entry_type="product_sku",
        name="产品1",
        content="...",
        brand_name="宠安宁",
        created_by="op",
    )
    await bkf.create_entry(
        db=db_session,
        entry_type="product_sku",
        name="产品2",
        content="...",
        brand_name="宠安宁",
        created_by="op",
    )
    result = await bkf.list_entries(db_session, brand_name="宠安宁")
    assert result["total"] >= 2


async def test_clear_brand_knowledge(db_session: AsyncSession):
    """🔴 清空数据（测试用）."""
    await bkf.create_entry(
        db=db_session, entry_type="faq", name="Q", content="A", created_by="op"
    )
    await bkf.clear_brand_knowledge(db_session)
    result = await bkf.list_entries(db_session)
    assert result["total"] == 0
