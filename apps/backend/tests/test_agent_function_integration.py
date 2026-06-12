"""
W15 Agent-Function Integration Tests.

验证Agent服务能正确调用Function层API获取数据：
- ComplianceGuard → BrandKnowledge / PlatformRule
- ContentForge → BrandKnowledge
- TrendScout → TimelineLibrary
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import clear_users
from src.services.auth_service import register_user
from src.services.compliance_engine import clear_evidence
import src.services.brand_knowledge_function as bkf
import src.services.platform_rule_function as prf
import src.services.timeline_library_function as tlf

pytestmark = pytest.mark.asyncio(loop_scope="function")


def _get_auth_token(client) -> str:
    import uuid
    email = f"agent_{uuid.uuid4().hex[:8]}@ecodream.com"
    clear_users()
    clear_evidence()
    response = client.post("/auth/register", json={
        "email": email,
        "password": "SecurePass123!",
        "username": f"agentfuncuser_{uuid.uuid4().hex[:8]}",
        "role": "operator",
    })
    assert response.status_code == 201, f"Register failed: {response.text}"
    return response.json()["access_token"]


# =============================================================================
# INTEGRATION-1: ComplianceGuard → BrandKnowledge
# =============================================================================


async def test_compliance_brand_knowledge_integration(db: AsyncSession, client, skip_if_no_db):
    """🔴 合规检查能检测到BrandKnowledge中的禁用宣称."""
    # Clean setup
    await bkf.clear_brand_knowledge(db)
    await db.commit()

    # Seed BrandKnowledge with prohibited claims
    await bkf.create_entry(
        db=db,
        entry_type="product_sku",
        name="宠安宁®驱虫滴剂",
        content="每月一次体外驱虫",
        product_id="PROD_CA_001",
        approval_number="兽药字220125001",
        brand_name="宠安宁",
        prohibited_claims=["100%有效", "根治", "立即见效"],
        created_by="operator_test",
    )
    await db.commit()

    token = _get_auth_token(client)

    # Content that contains a prohibited claim
    response = client.post(
        "/compliance/check",
        json={
            "text": "这款宠安宁驱虫滴剂100%有效，根治寄生虫问题！",
            "content_id": "draft_bk_001",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, f"Got {response.status_code}: {response.text}"
    data = response.json()

    # Must contain a BrandKnowledge-sourced violation
    bk_violations = [v for v in data["violations"] if v["rule_id"] == "FUNC-BRAND-KNOWLEDGE"]
    assert len(bk_violations) >= 1, f"Expected FUNC-BRAND-KNOWLEDGE violation, got: {data['violations']}"
    assert "100%有效" in bk_violations[0]["matched"] or "根治" in bk_violations[0]["matched"]
    assert "品牌" in bk_violations[0]["category"]

    # Cleanup
    await bkf.clear_brand_knowledge(db)
    await db.commit()


# =============================================================================
# INTEGRATION-2: ComplianceGuard → PlatformRule
# =============================================================================


async def test_compliance_platform_rule_integration(db: AsyncSession, client, skip_if_no_db):
    """🔴 合规检查能调用PlatformRule动态规则评估."""
    # Clean setup
    await prf.clear_platform_rules(db)
    await db.commit()

    # Seed a dynamic platform rule (L4)
    await prf.create_rule(
        db=db,
        platform="xiaohongshu",
        layer="l4",
        name="测试禁用词",
        condition_json={"type": "keyword_regex", "pattern": "测试违规词", "scope": "body"},
        action="block",
        priority=10,
        enabled=True,
        created_by="operator_test",
    )
    await db.commit()

    token = _get_auth_token(client)

    response = client.post(
        "/compliance/check",
        json={"text": "这个内容包含测试违规词，应该被拦截", "content_id": "draft_pr_001"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()

    pr_violations = [v for v in data["violations"] if v["rule_id"].startswith("FUNC-PLATFORM-RULE-")]
    assert len(pr_violations) >= 1, f"Expected FUNC-PLATFORM-RULE violation, got: {data['violations']}"
    assert "平台规则" in pr_violations[0]["category"]

    # Cleanup
    await prf.clear_platform_rules(db)
    await db.commit()


# =============================================================================
# INTEGRATION-3: ContentForge → BrandKnowledge
# =============================================================================


async def test_content_forge_brand_knowledge_integration(db: AsyncSession, client, skip_if_no_db):
    """🔴 内容生成能注入BrandKnowledge知识引用."""
    # Clean setup
    await bkf.clear_brand_knowledge(db)
    await db.commit()

    # Seed knowledge about "猫咪驱虫"
    entry = await bkf.create_entry(
        db=db,
        entry_type="faq",
        name="猫咪驱虫FAQ",
        content="猫咪驱虫是每月必须做的护理工作",
        product_id="PROD_FAQ_001",
        brand_name="瑞德医生",
        created_by="operator_test",
    )
    await db.commit()
    entry_id = str(entry.id)

    token = _get_auth_token(client)

    response = client.post(
        "/content-generate",
        json={"topic": "猫咪驱虫", "platform": "xhs", "persona_id": None},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, f"Got {response.status_code}: {response.text}"
    data = response.json()

    assert "brand_knowledge_refs" in data
    # Should reference the seeded knowledge entry
    assert entry_id in data["brand_knowledge_refs"], (
        f"Expected {entry_id} in brand_knowledge_refs, got {data['brand_knowledge_refs']}"
    )

    # Cleanup
    await bkf.clear_brand_knowledge(db)
    await db.commit()


# =============================================================================
# INTEGRATION-4: TrendScout → TimelineLibrary
# =============================================================================


async def test_trend_scout_timeline_integration(db: AsyncSession, client, skip_if_no_db):
    """🔴 趋势报告能包含TimelineLibrary季节事件."""
    from datetime import date, timedelta

    # Clean setup
    await tlf.clear_timeline_library(db)
    await db.commit()

    today = date.today()
    # Create an event that covers today
    event = await tlf.create_event(
        db=db,
        name="春季驱虫季",
        event_type="seasonal",
        start_date=(today - timedelta(days=5)).isoformat(),
        end_date=(today + timedelta(days=10)).isoformat(),
        description="春季是宠物驱虫的关键时期",
        created_by="operator_test",
    )
    await db.commit()
    event_id = str(event.id)

    token = _get_auth_token(client)

    response = client.post(
        "/trend-scout/reports",
        json={"query": "春季驱虫攻略", "stage_filter": "AWARE"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201, f"Got {response.status_code}: {response.text}"
    data = response.json()

    assert "timeline_events" in data
    assert len(data["timeline_events"]) >= 1, (
        f"Expected timeline_events, got {data.get('timeline_events')}"
    )
    event_ids = [e["id"] for e in data["timeline_events"]]
    assert event_id in event_ids, f"Expected {event_id} in timeline_events"
    assert data["timeline_events"][0]["name"] == "春季驱虫季"

    # Cleanup
    await tlf.clear_timeline_library(db)
    await db.commit()


# =============================================================================
# INTEGRATION-5: Graceful degradation when Function layer is empty
# =============================================================================


async def test_compliance_no_false_positives_when_empty(db: AsyncSession, client, skip_if_no_db):
    """🔴 Function层为空时，合规检查不产生误报."""
    await bkf.clear_brand_knowledge(db)
    await prf.clear_platform_rules(db)
    await db.commit()

    token = _get_auth_token(client)

    # Normal content with no violations
    response = client.post(
        "/compliance/check",
        json={"text": "春天到了，记得给猫咪勤梳毛，保持环境清洁", "content_id": "clean_001"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()

    # Should not have any Function-layer sourced violations
    func_violations = [
        v for v in data["violations"]
        if v["rule_id"].startswith("FUNC-")
    ]
    assert len(func_violations) == 0, (
        f"Expected no Function violations when DB empty, got: {func_violations}"
    )


async def test_content_forge_empty_brand_knowledge(db: AsyncSession, client, skip_if_no_db):
    """🔴 BrandKnowledge为空时，内容生成返回空引用."""
    await bkf.clear_brand_knowledge(db)
    await db.commit()

    token = _get_auth_token(client)

    response = client.post(
        "/content-generate",
        json={"topic": "未知话题测试", "platform": "xhs"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()

    assert "brand_knowledge_refs" in data
    assert data["brand_knowledge_refs"] == []
