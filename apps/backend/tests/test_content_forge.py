"""
W5 ContentForge Red-Green tests.
Tests for content generation, Voice injection, and persona pool.
"""

from src.models.user import clear_users
from src.services.persona_pool import clear_persona_pool



def get_auth_token(client, role: str = "operator"):
    import uuid
    clear_users()
    clear_persona_pool()
    email = f"cf_{uuid.uuid4().hex[:8]}@ecodream.com"
    response = client.post("/auth/register", json={
        "email": email,
        "password": "SecurePass123!",
        "username": f"cfuser_{uuid.uuid4().hex[:8]}",
        "role": "content_planner",
    })
    assert response.status_code == 201, f"Register failed: {response.text}"
    return response.json()["access_token"]
# ─── Content Draft CRUD ───


def test_create_content_draft(client):
    token = get_auth_token(client)
    payload = {
        "title": "猫咪驱虫指南",
        "content_type": "note",
        "platform": "xhs",
        "account_id": "pool_xhs_001",
        "body": "春天到了，给毛孩子驱虫很重要...",
        "tags": ["宠物健康", "猫咪驱虫"],
        "status": "draft",
    }
    response = client.post("/content-drafts", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 201, f"Got {response.status_code}: {response.text}"
    data = response.json()
    assert data["title"] == "猫咪驱虫指南"
    assert data["content_type"] == "note"
    assert data["platform"] == "xhs"
    assert data["status"] == "draft"
    assert "id" in data


def test_create_draft_requires_auth(client):
    response = client.post("/content-drafts", json={"title": "x", "content_type": "note"})
    assert response.status_code == 401


def test_list_content_drafts(client):
    from src.models.content_draft import clear_drafts
    clear_drafts()
    token = get_auth_token(client)
    client.post(
        "/content-drafts",
        json={"title": "A", "content_type": "note", "platform": "xhs", "account_id": "a1", "body": "...", "status": "draft"},
        headers={"Authorization": f"Bearer {token}"},
    )
    client.post(
        "/content-drafts",
        json={"title": "B", "content_type": "video", "platform": "douyin", "account_id": "a2", "body": "...", "status": "published"},
        headers={"Authorization": f"Bearer {token}"},
    )
    response = client.get("/content-drafts", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["drafts"]) == 2


def test_get_draft_detail(client):
    token = get_auth_token(client)
    create_resp = client.post(
        "/content-drafts",
        json={"title": "详情测试", "content_type": "note", "platform": "xhs", "account_id": "a1", "body": "正文", "status": "draft"},
        headers={"Authorization": f"Bearer {token}"},
    )
    draft_id = create_resp.json()["id"]
    response = client.get(f"/content-drafts/{draft_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "详情测试"
    assert data["body"] == "正文"


def test_update_draft_status(client):
    token = get_auth_token(client)
    create_resp = client.post(
        "/content-drafts",
        json={"title": "更新测试", "content_type": "note", "platform": "xhs", "account_id": "a1", "body": "旧正文", "status": "draft"},
        headers={"Authorization": f"Bearer {token}"},
    )
    draft_id = create_resp.json()["id"]
    response = client.patch(
        f"/content-drafts/{draft_id}",
        json={"body": "新正文", "status": "reviewing"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["body"] == "新正文"
    assert data["status"] == "reviewing"


def test_delete_draft(client):
    token = get_auth_token(client)
    create_resp = client.post(
        "/content-drafts",
        json={"title": "删除测试", "content_type": "note", "platform": "xhs", "account_id": "a1", "body": "...", "status": "draft"},
        headers={"Authorization": f"Bearer {token}"},
    )
    draft_id = create_resp.json()["id"]
    response = client.delete(f"/content-drafts/{draft_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 204
    assert client.get(f"/content-drafts/{draft_id}", headers={"Authorization": f"Bearer {token}"}).status_code == 404


# ─── Voice / Persona ───


def test_generate_content_with_voice():
    """Red: Content generation should inject persona voice into output."""
    from src.services.content_generator import generate_content

    result = generate_content(
        topic="猫咪驱虫",
        platform="xhs",
        persona={
            "name": "温柔铲屎官",
            "voice_style": "亲切、口语化、爱用emoji",
            "catchphrases": ["喵~", "毛孩子"],
            "formality": "casual",
        },
    )
    assert "title" in result
    assert "body" in result
    assert "tags" in result
    assert isinstance(result["tags"], list)
    # Voice injection should affect tone (MVP: mock verifies persona was passed)
    assert result["_persona_used"] == "温柔铲屎官"


def test_voice_injection_changes_tone():
    """Red: Different personas should produce different tones."""
    from src.services.content_generator import generate_content

    result_casual = generate_content(
        topic="驱虫",
        platform="xhs",
        persona={"name": " casual", "voice_style": "口语化", "formality": "casual"},
    )
    result_professional = generate_content(
        topic="驱虫",
        platform="xhs",
        persona={"name": "专业兽医", "voice_style": "严谨、科普", "formality": "formal"},
    )
    # MVP: different personas should produce different content
    assert result_professional["body"] != result_casual["body"]


# ─── ContentForge Stage Integration ───


def test_generate_content_with_stage_id(client):
    """Red Content generation should accept optional stage_id and inject template_version."""
    token = get_auth_token(client)
    response = client.post(
        "/content-generate",
        json={"topic": "猫咪驱虫", "platform": "xhs", "persona_id": None, "stage_id": "mm_aip_interest"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "template_version" in data
    assert data["template_version"] == "mm_aip_interest"


# ─── Persona Pool ───


def test_persona_pool_list(client):
    """Red Should list available personas in the pool."""
    token = get_auth_token(client)
    # Seed a persona
    client.post(
        "/personas",
        json={
            "name": "温柔铲屎官",
            "content_voice": {"tone": "亲切、口语化、爱用emoji", "formality_level": "casual", "catchphrases": ["喵~", "毛孩子"]},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    response = client.get("/personas", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert "personas" in data
    assert len(data["personas"]) > 0
    for p in data["personas"]:
        assert "id" in p
        assert "name" in p
        assert "voice_style" in p
        assert "formality" in p


def test_persona_pool_get_detail(client):
    token = get_auth_token(client)
    create_resp = client.post(
        "/personas",
        json={
            "name": "专业兽医",
            "content_voice": {"tone": "严谨、科普、数据支撑", "formality_level": "formal", "catchphrases": ["研究表明"]},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    persona_id = create_resp.json()["id"]
    detail = client.get(f"/personas/{persona_id}", headers={"Authorization": f"Bearer {token}"})
    assert detail.status_code == 200
    data = detail.json()
    assert data["id"] == persona_id
    assert "name" in data
    assert "voice_style" in data
