"""
PersonaPool Red-Green tests.
Tests for persona CRUD, clone, and matcher.
"""

from src.models.user import clear_users
from src.services.persona_pool import clear_persona_pool



def get_auth_token(client, role: str = "operator"):
    import uuid
    clear_users()
    clear_persona_pool()
    email = f"persona_{uuid.uuid4().hex[:8]}@ecodream.com"
    response = client.post("/auth/register", json={
        "email": email,
        "password": "SecurePass123!",
        "username": f"personauser_{uuid.uuid4().hex[:8]}",
        "role": "operator",
    })
    assert response.status_code == 201, f"Register failed: {response.text}"
    return response.json()["access_token"]
def test_create_persona(client):
    token = get_auth_token(client)
    response = client.post(
        "/personas",
        json={
            "name": "奶茶妈",
            "status": "active",
            "identity_core": {"nickname_pattern": "奶茶和它的铲屎官", "bio": "租房养猫3年", "gender": "female"},
            "pet_profile": {"pet_type": "cat", "breed": "英短", "age": 3},
            "owner_profile": {"owner_type": "租房年轻女性", "housing": "租房一居室"},
            "content_voice": {"tone": "亲切吐槽风", "formality_level": "very_casual"},
            "life_scenes": [{"scene_name": "日常护理", "description": "梳毛、剪指甲"}],
            "success_patterns": [{"pattern_name": "避坑清单", "avg_ces": 45}],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201, f"Got {response.status_code}: {response.text}"
    data = response.json()
    assert data["name"] == "奶茶妈"
    assert data["status"] == "active"
    assert data["identity_core"]["gender"] == "female"
    assert data["pet_profile"]["breed"] == "英短"
    assert data["content_voice"]["tone"] == "亲切吐槽风"
    assert len(data["life_scenes"]) == 1


def test_list_personas(client):
    token = get_auth_token(client)
    client.post("/personas", json={"name": "P1"}, headers={"Authorization": f"Bearer {token}"})
    client.post("/personas", json={"name": "P2"}, headers={"Authorization": f"Bearer {token}"})
    response = client.get("/personas", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["personas"]) >= 2


def test_get_persona_detail(client):
    token = get_auth_token(client)
    create_resp = client.post("/personas", json={"name": "Detail"}, headers={"Authorization": f"Bearer {token}"})
    persona_id = create_resp.json()["id"]
    response = client.get(f"/personas/{persona_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["name"] == "Detail"


def test_update_persona(client):
    token = get_auth_token(client)
    create_resp = client.post("/personas", json={"name": "OldName"}, headers={"Authorization": f"Bearer {token}"})
    persona_id = create_resp.json()["id"]
    response = client.patch(
        f"/personas/{persona_id}",
        json={"name": "NewName", "status": "archived"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "NewName"
    assert data["status"] == "archived"


def test_clone_persona(client):
    token = get_auth_token(client)
    source = client.post("/personas", json={"name": "Original"}, headers={"Authorization": f"Bearer {token}"})
    source_id = source.json()["id"]
    response = client.post(
        "/personas/clone",
        json={"source_id": source_id, "name": "Cloned"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Cloned"
    assert data["status"] == "draft"
    assert data["id"] != source_id


def test_delete_persona(client):
    token = get_auth_token(client)
    create_resp = client.post("/personas", json={"name": "ToDelete"}, headers={"Authorization": f"Bearer {token}"})
    persona_id = create_resp.json()["id"]
    del_resp = client.delete(f"/personas/{persona_id}", headers={"Authorization": f"Bearer {token}"})
    assert del_resp.status_code == 204
    get_resp = client.get(f"/personas/{persona_id}", headers={"Authorization": f"Bearer {token}"})
    assert get_resp.status_code == 404


def test_match_personas(client):
    token = get_auth_token(client)
    client.post(
        "/personas",
        json={
            "name": "CatMom",
            "pet_profile": {"pet_type": "cat"},
            "owner_profile": {"owner_type": "租房年轻女性", "income_level": "medium"},
            "usage_stats": {"use_count": 10, "avg_ces": 40},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    response = client.post(
        "/personas/match",
        json={"pet_type": "cat", "owner_type": "租房年轻女性", "budget_level": "medium"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["recommendations"]) >= 1
    assert data["recommendations"][0]["match_score"] > 0


def test_create_persona_requires_auth(client):
    response = client.post("/personas", json={"name": "x"})
    assert response.status_code == 401
