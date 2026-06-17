"""
W13 PlatformRule Engine Red-Green tests.
Tests for L3/L4 dynamic rules, CRUD, violation attribution, and version history.
"""

from src.models.user import clear_users
from tests.conftest import sync_clear_platform_rules



def get_auth_token(client, role: str = "operator"):
    import uuid
    clear_users()
    sync_clear_platform_rules()
    email = f"pr_{uuid.uuid4().hex[:8]}@ecodream.com"
    response = client.post("/auth/register", json={
        "email": email,
        "password": "SecurePass123!",
        "username": f"pruser_{uuid.uuid4().hex[:8]}",
        "role": "operator",
    })
    assert response.status_code == 201, f"Register failed: {response.text}"
    return response.json()["access_token"]
def test_list_platform_rules(client):
    token = get_auth_token(client)
    response = client.get("/platform-rules", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert "rules" in data
    assert len(data["rules"]) >= 1


def test_list_rules_by_layer(client):
    token = get_auth_token(client)
    response = client.get("/platform-rules?layer=l3", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    for r in data["rules"]:
        assert r["layer"] == "l3"


def test_create_platform_rule(client):
    token = get_auth_token(client)
    response = client.post(
        "/platform-rules",
        json={
            "name": "测试动态规则",
            "layer": "l4",
            "condition_json": {"type": "keyword_regex", "pattern": "测试", "scope": "title"},
            "action": "warn",
            "priority": 10,
            "enabled": True,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "测试动态规则"
    assert data["layer"] == "l4"
    assert data["action"] == "warn"
    assert data["version"] == 1


def test_evaluate_content_with_rules(client):
    token = get_auth_token(client)
    response = client.post(
        "/platform-rules/evaluate",
        json={
            "title": "猫咪驱虫药推荐",
            "body": "我家猫用了这个药治愈了",
            "tags": ["驱虫", "推荐"],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "pass_v" in data
    assert "violations" in data
    assert "warnings" in data
    assert "suggestions" in data


def test_delete_platform_rule(client):
    token = get_auth_token(client)
    create_resp = client.post(
        "/platform-rules",
        json={
            "name": "ToDelete",
            "layer": "l4",
            "condition_json": {},
            "action": "warn",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    rule_id = create_resp.json()["id"]
    del_resp = client.delete(f"/platform-rules/{rule_id}", headers={"Authorization": f"Bearer {token}"})
    assert del_resp.status_code == 204
    get_resp = client.get(f"/platform-rules/{rule_id}", headers={"Authorization": f"Bearer {token}"})
    assert get_resp.status_code == 404


def test_get_rule_attribution(client):
    token = get_auth_token(client)
    response = client.get(
        "/platform-rules/attribution/draft_001",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["content_id"] == "draft_001"
    assert "attribution" in data


def test_update_rule_increments_version(client):
    token = get_auth_token(client)
    create_resp = client.post(
        "/platform-rules",
        json={
            "name": "VersionTest",
            "layer": "l3",
            "condition_json": {},
            "action": "block",
            "priority": 5,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    rule_id = create_resp.json()["id"]
    assert create_resp.json()["version"] == 1

    patch_resp = client.patch(
        f"/platform-rules/{rule_id}",
        json={"name": "VersionTestUpdated", "priority": 10},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert patch_resp.status_code == 200
    data = patch_resp.json()
    assert data["version"] == 2
    assert data["name"] == "VersionTestUpdated"
    assert data["priority"] == 10
