"""AssetPool Function ORM tests — W14 Red-Green.

Aligned with PRD V3.1 §AssetPool / TASK_V2.7.1 FUNC-1.
Skips automatically when PostgreSQL is unavailable.
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from src.services import asset_pool_function as apf

pytestmark = pytest.mark.asyncio(loop_scope="function")


# ── Fixtures ──

@pytest_asyncio.fixture
async def db_session(db, skip_if_no_db):
    """Yield db session with skip-if-no-db guard."""
    return db


# =============================================================================
# ASSET-1: 三源上传 (Red → Green)
# =============================================================================

async def test_create_asset_operator_upload(db_session: AsyncSession):
    """🔴 运营上传素材 — 占比≥70%基线."""
    asset = await apf.create_asset(
        db=db_session,
        filename="cat_nutrition.jpg",
        file_url="https://cdn.example.com/cat.jpg",
        source_type="OPERATOR_UPLOAD",
        license_type="OWNED",
        copyright_holder="EcoDream Inc",
        tags=["猫咪", "营养"],
        category="cat",
    )
    assert asset.id is not None
    assert asset.source_type == "OPERATOR_UPLOAD"
    assert asset.license_type == "OWNED"
    assert asset.copyright_validated is True
    assert asset.ai_disclosure is False


async def test_create_asset_stock_api(db_session: AsyncSession):
    """🔴 图库API素材 — 版权链完整记录."""
    asset = await apf.create_asset(
        db=db_session,
        filename="vet_stock.jpg",
        file_url="https://stock.example.com/vet.jpg",
        source_type="STOCK_API",
        license_type="LICENSED",
        stock_source="shutterstock",
        stock_id="ss_12345",
        license_expiry="2025-12-31T00:00:00+00:00",
        tags=["兽医", "专业"],
    )
    assert asset.source_type == "STOCK_API"
    assert asset.stock_source == "shutterstock"
    assert asset.license_status in ("VALID", "EXPIRED")


async def test_create_asset_ai_generated(db_session: AsyncSession):
    """🔴 AI生成素材 — 强制附加AI辅助创作标签."""
    asset = await apf.create_asset(
        db=db_session,
        filename="ai_cat.jpg",
        file_url="https://ai.example.com/cat.jpg",
        source_type="AI_GENERATED",
        license_type="AI_GENERATED",
        ai_model="dalle-3",
        ai_prompt="cute cat eating food",
        tags=["AI生成"],
    )
    assert asset.source_type == "AI_GENERATED"
    assert asset.ai_disclosure is True
    assert "AI辅助创作" in (asset.tags or [])
    assert asset.ai_metadata is not None


# =============================================================================
# ASSET-2: 版权校验
# =============================================================================

async def test_copyright_validation_owned_requires_holder(db_session: AsyncSession):
    """🔴 自有版权必须提供copyright_holder."""
    asset = await apf.create_asset(
        db=db_session,
        filename="no_holder.jpg",
        file_url="https://example.com/x.jpg",
        license_type="OWNED",
        copyright_holder=None,
    )
    assert asset.copyright_validated is False


async def test_copyright_validation_licensed_requires_source(db_session: AsyncSession):
    """🔴 授权素材必须提供stock_source."""
    asset = await apf.create_asset(
        db=db_session,
        filename="no_source.jpg",
        file_url="https://example.com/y.jpg",
        license_type="LICENSED",
        stock_source=None,
    )
    assert asset.copyright_validated is False


async def test_license_expiry_status(db_session: AsyncSession):
    """🔴 许可证到期状态自动计算."""
    from datetime import datetime, timezone, timedelta

    past = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
    soon = (datetime.now(timezone.utc) + timedelta(days=15)).isoformat()

    asset_past = await apf.create_asset(
        db=db_session,
        filename="expired.jpg",
        file_url="https://example.com/e.jpg",
        license_type="LICENSED",
        stock_source="getty",
        license_expiry=past,
    )
    assert asset_past.license_status == "EXPIRED"

    asset_soon = await apf.create_asset(
        db=db_session,
        filename="expiring.jpg",
        file_url="https://example.com/s.jpg",
        license_type="LICENSED",
        stock_source="getty",
        license_expiry=soon,
    )
    assert asset_soon.license_status == "EXPIRING_SOON"


# =============================================================================
# ASSET-3: AI标识不可移除
# =============================================================================

async def test_ai_asset_cannot_remove_disclosure(db_session: AsyncSession):
    """🔴 AI生成素材禁止移除AI标签."""
    asset = await apf.create_asset(
        db=db_session,
        filename="ai_test.jpg",
        file_url="https://example.com/ai.jpg",
        source_type="AI_GENERATED",
        license_type="AI_GENERATED",
        ai_model="midjourney",
    )
    updated = await apf.update_asset(
        db=db_session,
        asset_id=str(asset.id),
        tags=["猫咪"],  # 尝试移除AI辅助创作
        ai_disclosure=False,
    )
    assert updated is not None
    assert "AI辅助创作" in (updated.tags or [])
    assert updated.ai_disclosure is True


# =============================================================================
# ASSET-4: 推荐匹配
# =============================================================================

async def test_recommend_assets_match_score(db_session: AsyncSession):
    """🔴 素材-内容匹配推荐."""
    await apf.create_asset(
        db=db_session,
        filename="match_cat.jpg",
        file_url="https://example.com/mc.jpg",
        source_type="OPERATOR_UPLOAD",
        tags=["猫咪", "健康"],
        category="cat",
    )
    result = await apf.recommend_assets(
        db=db_session,
        content_title="猫咪健康饮食指南",
        content_body="",
        content_tags=["猫咪", "健康"],
        target_count=3,
    )
    assert result["total_candidates"] >= 1
    assert result["recommendations"][0]["match_score"] > 0


# =============================================================================
# ASSET-5: 统计
# =============================================================================

async def test_statistics_operator_ratio(db_session: AsyncSession):
    """🔴 运营上传占比统计."""
    await apf.clear_asset_pool(db_session)
    for i in range(3):
        await apf.create_asset(
            db=db_session,
            filename=f"op_{i}.jpg",
            file_url=f"https://example.com/op{i}.jpg",
            source_type="OPERATOR_UPLOAD",
        )
    await apf.create_asset(
        db=db_session,
        filename="ai.jpg",
        file_url="https://example.com/ai.jpg",
        source_type="AI_GENERATED",
        license_type="AI_GENERATED",
        ai_model="dalle",
    )
    stats = await apf.get_statistics(db_session)
    assert stats["total"] == 4
    assert stats["active"] == 4
    assert stats["operator_upload_ratio"] == 75.0


# =============================================================================
# ASSET-6: CRUD lifecycle
# =============================================================================

async def test_asset_crud_lifecycle(db_session: AsyncSession):
    """🔴 完整CRUD生命周期."""
    asset = await apf.create_asset(
        db=db_session,
        filename="lifecycle.jpg",
        file_url="https://example.com/lc.jpg",
    )
    # Read
    found = await apf.get_asset(db_session, str(asset.id))
    assert found is not None
    assert found.filename == "lifecycle.jpg"

    # Update
    updated = await apf.update_asset(
        db_session, str(asset.id), filename="lifecycle_v2.jpg"
    )
    assert updated is not None
    assert updated.filename == "lifecycle_v2.jpg"

    # List
    listed = await apf.list_assets(db_session, limit=10)
    assert listed["total"] >= 1

    # Delete (soft)
    deleted = await apf.delete_asset(db_session, str(asset.id))
    assert deleted is True
    found_after = await apf.get_asset(db_session, str(asset.id))
    assert found_after is not None
    assert found_after.status == "DELETED"


async def test_list_excludes_deleted(db_session: AsyncSession):
    """🔴 列表默认排除已删除."""
    asset = await apf.create_asset(
        db=db_session, filename="del.jpg", file_url="https://example.com/d.jpg"
    )
    await apf.delete_asset(db_session, str(asset.id))
    listed = await apf.list_assets(db_session, status="ACTIVE")
    ids = [str(a.id) for a in listed["items"]]
    assert str(asset.id) not in ids


# =============================================================================
# ASSET-7: kwargs 参数（meta_mime_type 等）应正确保存到数据库
# =============================================================================

async def test_create_asset_preserves_meta_mime_type(db_session: AsyncSession):
    """🔴 create_asset 通过 kwargs 传入的 meta_mime_type 必须持久化到数据库."""
    asset = await apf.create_asset(
        db=db_session,
        filename="cat.png",
        file_url="https://example.com/cat.png",
        meta_mime_type="image/png",
        meta_width=800,
        meta_height=600,
        meta_file_size=102400,
    )
    assert asset.meta_mime_type == "image/png"
    assert asset.meta_width == 800
    assert asset.meta_height == 600
    assert asset.meta_file_size == 102400

    # 重新读取验证持久化
    found = await apf.get_asset(db_session, str(asset.id))
    assert found is not None
    assert found.meta_mime_type == "image/png"
    assert found.meta_width == 800
    assert found.meta_height == 600
    assert found.meta_file_size == 102400


async def test_derived_asset_type_from_meta_mime_type(db_session: AsyncSession):
    """🔴 _derive_asset_type 应优先使用 meta_mime_type 判断类型."""
    from src.api.asset_pool import _derive_asset_type

    asset = await apf.create_asset(
        db=db_session,
        filename="no_extension",
        file_url="https://example.com/no_extension",
        meta_mime_type="image/png",
    )
    assert _derive_asset_type(asset) == "image"

    asset2 = await apf.create_asset(
        db=db_session,
        filename="video_no_ext",
        file_url="https://example.com/video_no_ext",
        meta_mime_type="video/mp4",
    )
    assert _derive_asset_type(asset2) == "video"
