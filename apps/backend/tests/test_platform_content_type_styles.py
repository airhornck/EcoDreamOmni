"""Tests for PlatformContentTypeStyle ORM and API — v4.0 Phase 1 P1-1."""

import uuid

import pytest
from sqlalchemy import delete

from src.models.platform_content_type_style import PlatformContentTypeStyleORM


def _get_token(client):
    """Register a test user and return access token."""
    from src.models.user import clear_users
    clear_users()
    email = f"pcs_{uuid.uuid4().hex[:8]}@ecodream.com"
    resp = client.post("/auth/register", json={
        "email": email,
        "password": "SecurePass123!",
        "username": f"pcsuser_{uuid.uuid4().hex[:8]}",
        "role": "operator",
    })
    assert resp.status_code == 201, f"Register failed: {resp.text}"
    return resp.json()["access_token"]


def _auth_headers(client):
    return {"Authorization": f"Bearer {_get_token(client)}"}


@pytest.mark.asyncio
async def test_create_platform_content_type_style_orm(db):
    """Test ORM create."""
    # Clean up first
    await db.execute(delete(PlatformContentTypeStyleORM).where(PlatformContentTypeStyleORM.style_id == "style_test_001"))
    await db.commit()

    style = PlatformContentTypeStyleORM(
        style_id="style_test_001",
        tenant_id="tenant_test",
        platform_id="xhs",
        content_type="note_image",
        content_dna={"hook_types": ["反差"]},
        default_prompt_fragments=["语气亲切"],
        recommended_keywords={"high_performing": ["养宠攻略"]},
        tone_preset={"formality": 0.3, "enthusiasm": 0.8},
        structure_template={"paragraphs": 3},
        avg_engagement_rate=0.0856,
        sample_count=128,
        is_ai_generated=True,
        source_template_ids=["tmpl_001"],
        status="active",
        created_by="user_test",
    )
    db.add(style)
    await db.commit()
    await db.refresh(style)

    assert style.style_id == "style_test_001"
    assert style.tenant_id == "tenant_test"
    assert style.platform_id == "xhs"
    assert style.content_type == "note_image"
    assert style.status == "active"


@pytest.mark.asyncio
async def test_platform_content_type_style_api_crud(client):
    """Test API CRUD endpoints."""
    headers = _auth_headers(client)

    # Create
    create_data = {
        "platform_id": "xhs",
        "content_type": "note_video",
        "content_dna": {"hook_types": ["悬念"]},
        "default_prompt_fragments": ["开场抓人"],
        "recommended_keywords": {"trending": ["热门话题"]},
        "tone_preset": {"formality": 0.5, "enthusiasm": 0.9},
        "structure_template": {"paragraphs": 5},
        "status": "active",
    }
    resp = client.post("/platform-content-type-styles", json=create_data, headers=headers)
    assert resp.status_code == 201, f"Create failed: {resp.text}"
    created = resp.json()
    style_id = created["style_id"]
    assert created["platform_id"] == "xhs"
    assert created["content_type"] == "note_video"

    # List
    resp = client.get("/platform-content-type-styles", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert any(item["style_id"] == style_id for item in data["items"])

    # Get
    resp = client.get(f"/platform-content-type-styles/{style_id}", headers=headers)
    assert resp.status_code == 200
    detail = resp.json()
    assert detail["style_id"] == style_id

    # Update
    update_data = {"status": "draft", "sample_count": 10}
    resp = client.patch(f"/platform-content-type-styles/{style_id}", json=update_data, headers=headers)
    assert resp.status_code == 200
    updated = resp.json()
    assert updated["status"] == "draft"
    assert updated["sample_count"] == 10

    # Delete (soft)
    resp = client.delete(f"/platform-content-type-styles/{style_id}", headers=headers)
    assert resp.status_code == 200
    deleted = resp.json()
    assert deleted["data"]["style_id"] == style_id

    # Verify deleted
    resp = client.get(f"/platform-content-type-styles/{style_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "deprecated"


@pytest.mark.asyncio
async def test_platform_content_type_style_tenant_isolation(client):
    """Test tenant isolation — must filter by tenant_id."""
    headers = _auth_headers(client)
    resp = client.get("/platform-content-type-styles", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    for item in data["items"]:
        assert item["tenant_id"] is not None
