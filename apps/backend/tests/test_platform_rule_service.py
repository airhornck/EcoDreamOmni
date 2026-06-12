"""Tests for platform_rule_service — memory fallback path (no DB required)."""

import pytest
import asyncio
from src.services import platform_rule_service
from src.models.account_pool import create_pool_entry, clear_pool_entries


@pytest.fixture(autouse=True)
def clean():
    platform_rule_service.clear_platform_rules()
    clear_pool_entries()
    yield
    platform_rule_service.clear_platform_rules()
    clear_pool_entries()


@pytest.mark.asyncio
async def test_evaluate_l3_allows_by_default():
    """Without any account or DB, evaluate_l3 should allow publishing."""
    result = await platform_rule_service.evaluate_l3("nonexistent_account")
    assert result["allowed"] is True
    assert result["reason"] == ""


@pytest.mark.asyncio
async def test_evaluate_l3_blocks_quota_exceeded():
    """Account with quota_exceeded should be blocked."""
    entry = create_pool_entry(
        platform="xhs",
        account_id="test_quota",
        nickname="Test",
        cookie="cookie",
        persona="p1",
        content_vertical="宠物",
        lifecycle_phase="cold_start",
        fingerprint_profile={
            "user_agent": "ua",
            "viewport": {"width": 1920, "height": 1080},
            "locale": "zh-CN",
            "timezone": "Asia/Shanghai",
        },
    )
    entry.posts_today = 5
    entry.daily_quota = 1

    result = await platform_rule_service.evaluate_l3(entry.id)
    assert result["allowed"] is False
    assert "配额已用尽" in result["reason"]


@pytest.mark.asyncio
async def test_evaluate_l3_memory_rules_fallback():
    """Memory-based L3 rules should still work as fallback."""
    # Create a mature account with no posts
    entry = create_pool_entry(
        platform="xhs",
        account_id="test_mature",
        nickname="Test",
        cookie="cookie",
        persona="p1",
        content_vertical="宠物",
        lifecycle_phase="mature",
        fingerprint_profile={
            "user_agent": "ua",
            "viewport": {"width": 1920, "height": 1080},
            "locale": "zh-CN",
            "timezone": "Asia/Shanghai",
        },
    )
    # No posts, should be allowed
    result = await platform_rule_service.evaluate_l3(entry.id)
    assert result["allowed"] is True


def test_evaluate_content_v2_basic():
    """Memory-based evaluate_content_v2 should still work."""
    result = platform_rule_service.evaluate_content_v2(
        content={"title": "测试", "body": "普通内容", "tags": []}
    )
    assert "pass" in result
    assert "violations" in result


def test_evaluate_content_v2_warns_keyword_regex():
    """L4 keyword_regex rule should trigger warning."""
    result = platform_rule_service.evaluate_content_v2(
        content={"title": "驱虫药推荐", "body": "这个处方很好用", "tags": []}
    )
    # R_L4_002 "关键词临时降权" matches 驱虫药|处方
    assert result["warning_count"] >= 1
    assert any("关键词临时降权" in w.get("name", "") for w in result["warnings"])
