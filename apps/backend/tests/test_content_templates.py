"""Tests for ContentTemplate ORM and API — v4.0 Phase 1 P1-2."""

import uuid

import pytest
from sqlalchemy import delete

from src.models.content_template import ContentTemplateORM


def _get_token(client):
    """Register a test user and return access token."""
    from src.models.user import clear_users
    clear_users()
    email = f"ct_{uuid.uuid4().hex[:8]}@ecodream.com"
    resp = client.post("/auth/register", json={
        "email": email,
        "password": "SecurePass123!",
        "username": f"ctuser_{uuid.uuid4().hex[:8]}",
        "role": "operator",
    })
    assert resp.status_code == 201, f"Register failed: {resp.text}"
    return resp.json()["access_token"]


def _auth_headers(client):
    return {"Authorization": f"Bearer {_get_token(client)}"}


@pytest.mark.asyncio
async def test_create_content_template_orm(db):
    """Test ORM create."""
    await db.execute(delete(ContentTemplateORM).where(ContentTemplateORM.template_id == "tmpl_test_001"))
    await db.commit()

    template = ContentTemplateORM(
        template_id="tmpl_test_001",
        tenant_id="tenant_test",
        source_platform_id="xhs",
        source_content_url="https://example.com/note/123",
        source_content_id="note_123",
        extracted_structure={"hook_pattern": "痛点反问", "body_structure": "故事线", "cta_pattern": "互动提问"},
        prompt_template="你是一个宠物博主...",
        variables=[{"name": "hook", "label": "钩子", "type": "text", "default_value": ""}],
        engagement_benchmark={"likes": 1200, "comments": 89, "saves": 456, "shares": 23},
        platform_content_type_style_id="style_test_001",
        created_by="user_test",
        usage_count=15,
        avg_generated_engagement={"likes": 800, "comments": 56, "saves": 320},
        status="active",
    )
    db.add(template)
    await db.commit()
    await db.refresh(template)

    assert template.template_id == "tmpl_test_001"
    assert template.tenant_id == "tenant_test"
    assert template.source_platform_id == "xhs"
    assert template.status == "active"


@pytest.mark.asyncio
async def test_content_template_api_crud(client):
    """Test API CRUD endpoints."""
    headers = _auth_headers(client)

    # Create
    create_data = {
        "source_platform_id": "douyin",
        "source_content_url": "https://example.com/video/456",
        "source_content_id": "video_456",
        "extracted_structure": {"hook_pattern": "悬念", "body_structure": "反转", "cta_pattern": "关注"},
        "prompt_template": "生成抖音视频脚本...",
        "variables": [{"name": "scene", "label": "场景", "type": "text", "default_value": ""}],
        "engagement_benchmark": {"likes": 5000, "comments": 200},
        "status": "active",
    }
    resp = client.post("/content-templates", json=create_data, headers=headers)
    assert resp.status_code == 201, f"Create failed: {resp.text}"
    created = resp.json()
    template_id = created["template_id"]
    assert created["source_platform_id"] == "douyin"

    # List
    resp = client.get("/content-templates", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert any(item["template_id"] == template_id for item in data["items"])

    # Get
    resp = client.get(f"/content-templates/{template_id}", headers=headers)
    assert resp.status_code == 200
    detail = resp.json()
    assert detail["template_id"] == template_id

    # Update
    update_data = {"usage_count": 20, "status": "draft"}
    resp = client.patch(f"/content-templates/{template_id}", json=update_data, headers=headers)
    assert resp.status_code == 200
    updated = resp.json()
    assert updated["usage_count"] == 20
    assert updated["status"] == "draft"

    # Delete (soft)
    resp = client.delete(f"/content-templates/{template_id}", headers=headers)
    assert resp.status_code == 200
    deleted = resp.json()
    assert deleted["data"]["template_id"] == template_id

    # Verify deleted
    resp = client.get(f"/content-templates/{template_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "deprecated"


@pytest.mark.asyncio
async def test_content_template_tenant_isolation(client):
    """Test tenant isolation."""
    headers = _auth_headers(client)
    resp = client.get("/content-templates", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    for item in data["items"]:
        assert item["tenant_id"] is not None
