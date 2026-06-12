"""PlatformRule Function ORM tests — W14 Red-Green.

Aligned with PRD V3.1 §PlatformRule / TASK_V2.7.1 FUNC-5.
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from src.services import platform_rule_function as prf

pytestmark = pytest.mark.asyncio(loop_scope="function")


@pytest_asyncio.fixture
async def db_session(db, skip_if_no_db):
    await prf.clear_platform_rules(db)
    # Also clear attribution snapshots since evaluate_content commits independently
    from sqlalchemy import delete
    from src.models.platform_rule_attribution_orm import ContentRuleAttributionORM
    await db.execute(delete(ContentRuleAttributionORM))
    await db.commit()
    return db


# =============================================================================
# PR-1: 规则CRUD + 版本化
# =============================================================================

async def test_create_rule_xiaohongshu(db_session: AsyncSession):
    """🔴 创建小红书平台规则."""
    rule = await prf.create_rule(
        db=db_session,
        platform="xiaohongshu",
        layer="l3",
        name="新号日发限制",
        condition_json={
            "type": "frequency",
            "scope": "account_state",
            "condition": "account_age_days<7 AND daily_post_count>=1",
        },
        action="warn",
        priority=100,
        effective_from="2026-01-01T00:00:00+00:00",
        created_by="system",
    )
    assert rule.id is not None
    assert rule.platform == "xiaohongshu"
    assert rule.layer == "l3"
    assert rule.version == 1


async def test_create_rule_douyin_placeholder(db_session: AsyncSession):
    """🔴 抖音扩展接口预留 — 空实现+测试."""
    rule = await prf.create_rule(
        db=db_session,
        platform="douyin",
        layer="l2",
        name="抖音兽药广告号校验",
        condition_json={
            "type": "keyword_regex",
            "scope": "content",
            "pattern": "广告审查批准文号",
            "case_sensitive": False,
        },
        action="block",
        priority=200,
        created_by="system",
    )
    assert rule.platform == "douyin"


async def test_update_rule_creates_history(db_session: AsyncSession):
    """🔴 更新规则自动留痕 — 版本化."""
    rule = await prf.create_rule(
        db=db_session,
        platform="xiaohongshu",
        layer="l4",
        name="关键词临时降权",
        condition_json={"type": "keyword_regex", "pattern": "(驱虫药)"},
        action="warn",
        created_by="system",
    )
    rule_id = str(rule.id)

    updated = await prf.update_rule(
        db=db_session,
        rule_id=rule_id,
        updated_by="admin",
        change_reason="618期间提高优先级",
        priority=150,
    )
    assert updated is not None
    assert updated.version == 2
    assert updated.priority == 150

    history = await prf.get_rule_history(db_session, rule_id)
    assert len(history) == 1
    assert history[0].version == 1
    assert history[0].priority == 0


async def test_list_rules_by_platform(db_session: AsyncSession):
    """🔴 按平台筛选规则."""
    await prf.create_rule(
        db=db_session,
        platform="xiaohongshu",
        layer="l1",
        name="小红书L1规则",
        condition_json={},
        created_by="system",
    )
    await prf.create_rule(
        db=db_session,
        platform="douyin",
        layer="l1",
        name="抖音L1规则",
        condition_json={},
        created_by="system",
    )
    xs = await prf.list_rules(db_session, platform="xiaohongshu")
    ds = await prf.list_rules(db_session, platform="douyin")
    assert xs["total"] >= 1
    assert ds["total"] >= 1


# =============================================================================
# PR-2: 规则引擎评估
# =============================================================================

async def test_evaluate_content_keyword_block(db_session: AsyncSession):
    """🔴 关键词规则拦截."""
    await prf.create_rule(
        db=db_session,
        platform="xiaohongshu",
        layer="l2",
        name="禁用词拦截",
        condition_json={
            "type": "keyword_regex",
            "pattern": "(处方药|根治)",
            "case_sensitive": False,
        },
        action="block",
        priority=100,
        created_by="system",
    )
    result = await prf.evaluate_content(
        db=db_session,
        content={"title": "这款处方药根治猫藓", "body": "", "tags": []},
        platform="xiaohongshu",
    )
    assert result["pass"] is False
    assert result["violation_count"] >= 1
    assert any("禁用词拦截" in v.get("name", "") for v in result["violations"])


async def test_evaluate_content_frequency_warn(db_session: AsyncSession):
    """🔴 频率规则警告."""
    await prf.create_rule(
        db=db_session,
        platform="xiaohongshu",
        layer="l3",
        name="新号频率",
        condition_json={
            "type": "frequency",
            "scope": "account_state",
            "condition": "daily_post_count>=1 new",
        },
        action="warn",
        created_by="system",
    )
    result = await prf.evaluate_content(
        db=db_session,
        content={"title": "test", "body": "", "tags": []},
        platform="xiaohongshu",
        account_state={"daily_post_count": 2},
    )
    assert result["warning_count"] >= 1


async def test_evaluate_content_pass(db_session: AsyncSession):
    """🔴 无违规内容通过."""
    await prf.create_rule(
        db=db_session,
        platform="xiaohongshu",
        layer="l2",
        name="禁用词",
        condition_json={"type": "keyword_regex", "pattern": "(违禁词A)"},
        action="block",
        created_by="system",
    )
    result = await prf.evaluate_content(
        db=db_session,
        content={"title": "正常内容", "body": "", "tags": []},
        platform="xiaohongshu",
    )
    assert result["pass"] is True
    assert result["violation_count"] == 0


async def test_rule_disabled_not_evaluated(db_session: AsyncSession):
    """🔴 禁用规则不参与评估."""
    rule = await prf.create_rule(
        db=db_session,
        platform="xiaohongshu",
        layer="l2",
        name="禁用规则",
        condition_json={"type": "keyword_regex", "pattern": "(测试)"},
        action="block",
        enabled=True,
        created_by="system",
    )
    # Disable it
    await prf.update_rule(
        db=db_session,
        rule_id=str(rule.id),
        updated_by="admin",
        enabled=False,
    )
    result = await prf.evaluate_content(
        db=db_session,
        content={"title": "测试内容", "body": "", "tags": []},
        platform="xiaohongshu",
    )
    assert result["pass"] is True


# =============================================================================
# PR-3: 生效时间控制
# =============================================================================

async def test_rule_effective_date_filter(db_session: AsyncSession):
    """🔴 未生效规则不参与评估."""
    from datetime import datetime, timezone, timedelta

    future = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    await prf.create_rule(
        db=db_session,
        platform="xiaohongshu",
        layer="l2",
        name="未来规则",
        condition_json={"type": "keyword_regex", "pattern": "(未来)"},
        action="block",
        effective_from=future,
        created_by="system",
    )
    result = await prf.evaluate_content(
        db=db_session,
        content={"title": "未来内容", "body": "", "tags": []},
        platform="xiaohongshu",
    )
    assert result["pass"] is True  # 规则尚未生效


# =============================================================================
# PR-4: 清理
# =============================================================================

async def test_clear_platform_rules(db_session: AsyncSession):
    """🔴 清空规则."""
    await prf.create_rule(
        db=db_session,
        platform="xiaohongshu",
        layer="l1",
        name="清理测试",
        condition_json={},
        created_by="system",
    )
    await prf.clear_platform_rules(db_session)
    result = await prf.list_rules(db_session)
    assert result["total"] == 0


# =============================================================================
# Attribution persistence
# =============================================================================

async def test_attribution_persisted_and_queryable(db_session: AsyncSession):
    """🔴 规则触发后归因记录应持久化并可查询."""
    await prf.create_rule(
        db=db_session,
        platform="xiaohongshu",
        layer="l3_medical",
        name="处方药拦截",
        condition_json={"type": "keyword", "keywords": ["处方药"]},
        action="block",
        created_by="system",
    )
    content_id = "content-attr-001"
    result = await prf.evaluate_content(
        db=db_session,
        content={"title": "这款处方药根治猫藓", "body": "", "tags": [],
                 "content_id": content_id},
        platform="xiaohongshu",
    )
    assert result["pass"] is False
    assert result["violation_count"] == 1

    attrs = await prf.get_attributions_for_content(db_session, content_id)
    assert len(attrs) == 1
    assert attrs[0]["rule_name"] == "处方药拦截"
    assert attrs[0]["action"] == "block"
    assert attrs[0]["matched"] == "处方药"
    assert attrs[0]["layer"] == "l3_medical"

    # Non-existent content returns empty
    empty = await prf.get_attributions_for_content(db_session, "no-such-id")
    assert empty == []
