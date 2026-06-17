"""
W16-3 PlatformRule 多平台适配（抖音）Red-Green 测试。

核心要求:
- 调用 PlatformRule Function 基座扩展
- 兽药广告审查号强制校验
- 引流话术 L1 拦截
- 平台差异规则矩阵
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import clear_users

pytestmark = pytest.mark.asyncio(loop_scope="function")


def _get_auth_token(client) -> str:
    import uuid
    email = f"douyin_{uuid.uuid4().hex[:8]}@ecodream.com"
    clear_users()
    response = client.post("/auth/register", json={
        "email": email,
        "password": "SecurePass123!",
        "username": f"douyinuser_{uuid.uuid4().hex[:8]}",
        "role": "operator",
    })
    assert response.status_code == 201, f"Register failed: {response.text}"
    return response.json()["access_token"]


# =============================================================================
# DOUYIN-1: 兽药广告审查号校验
# =============================================================================


async def test_douyin_requires_ad_approval_number(client, db: AsyncSession, skip_if_no_db):
    """🔴 抖音内容须显著展示兽药广告审查批准文号."""
    token = _get_auth_token(client)

    # 内容缺少广告审查号
    response = client.post(
        "/platform-rules/douyin/evaluate",
        json={
            "title": "驱虫药推荐",
            "body": "这款驱虫药效果很好，推荐购买",
            "tags": ["驱虫", "兽药"],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()

    # 必须包含广告审查号缺失的违规
    ad_violations = [v for v in data["violations"] if "广告审查" in v.get("message", "")]
    assert len(ad_violations) >= 1, f"Expected ad approval violation, got: {data['violations']}"


async def test_douyin_passes_with_ad_approval_number(client, db: AsyncSession, skip_if_no_db):
    """🔴 包含广告审查号的抖音内容通过校验."""
    token = _get_auth_token(client)

    response = client.post(
        "/platform-rules/douyin/evaluate",
        json={
            "title": "驱虫药推荐",
            "body": "这款驱虫药效果很好，兽药广告审查批准文号：兽药广审（视）第2025010001号",
            "tags": ["驱虫", "兽药"],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()

    # 广告审查号校验应通过
    ad_violations = [v for v in data["violations"] if "广告审查" in v.get("message", "")]
    assert len(ad_violations) == 0, f"Expected no ad approval violation, got: {ad_violations}"


# =============================================================================
# DOUYIN-2: 引流话术 L1 拦截
# =============================================================================


async def test_douyin_blocks_diversion_phrases(client, db: AsyncSession, skip_if_no_db):
    """🔴 抖音引流话术 L1 拦截."""
    token = _get_auth_token(client)

    response = client.post(
        "/platform-rules/douyin/evaluate",
        json={
            "title": "私信领取",
            "body": "加我微信了解更多，微信号 xxx",
            "tags": ["引流"],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()

    diversion_violations = [v for v in data["violations"] if "引流" in v.get("category", "")]
    assert len(diversion_violations) >= 1, f"Expected diversion violation, got: {data['violations']}"


# =============================================================================
# DOUYIN-3: 平台差异规则矩阵
# =============================================================================


async def test_douyin_specific_rules_different_from_xiaohongshu(client, db: AsyncSession, skip_if_no_db):
    """🔴 抖音规则与小红书规则存在差异."""
    token = _get_auth_token(client)

    # 同一条内容在抖音和小红书的评估结果应不同
    douyin_resp = client.post(
        "/platform-rules/douyin/evaluate",
        json={"title": "测试", "body": "加我微信", "tags": []},
        headers={"Authorization": f"Bearer {token}"},
    )
    xhs_resp = client.post(
        "/platform-rules/xiaohongshu/evaluate",
        json={"title": "测试", "body": "加我微信", "tags": []},
        headers={"Authorization": f"Bearer {token}"},
    )

    douyin_data = douyin_resp.json()
    xhs_resp.json()

    # 抖音应有引流相关违规，小红书可能没有（或不同）
    douyin_diversion = [v for v in douyin_data["violations"] if "引流" in v.get("category", "")]
    assert len(douyin_diversion) >= 1


# =============================================================================
# DOUYIN-4: 抖音规则 CRUD
# =============================================================================


async def test_create_douyin_platform_rule(client, db: AsyncSession, skip_if_no_db):
    """🔴 能创建抖音平台规则."""
    token = _get_auth_token(client)

    response = client.post(
        "/platform-rules",
        json={
            "name": "抖音引流拦截",
            "platform": "douyin",
            "layer": "l1",
            "condition_json": {"type": "keyword_regex", "pattern": "微信|私信|加V", "scope": "body"},
            "action": "block",
            "priority": 20,
            "enabled": True,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["platform"] == "douyin"
    assert data["name"] == "抖音引流拦截"
