"""
W12 MarketingMethodology Red-Green tests.
Tests for AIPL stage templates and content evaluation.
"""

from src.models.user import clear_users
from src.services.auth_service import register_user
from src.services.methodology_service import clear_methodologies



def get_auth_token(client, role: str = "operator"):
    import uuid
    clear_users()
    clear_methodologies()
    email = f"mm_{uuid.uuid4().hex[:8]}@ecodream.com"
    response = client.post("/auth/register", json={
        "email": email,
        "password": "SecurePass123!",
        "username": f"mmuser_{uuid.uuid4().hex[:8]}",
        "role": "operator",
    })
    assert response.status_code == 201, f"Register failed: {response.text}"
    return response.json()["access_token"]
def test_list_methodologies(client):
    token = get_auth_token(client)
    response = client.get("/methodologies", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert "methodologies" in data
    assert len(data["methodologies"]) >= 1


def test_list_stages(client):
    token = get_auth_token(client)
    response = client.get("/methodologies/stages", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["stages"]) >= 4  # AWARENESS, INTEREST, PURCHASE, LOYALTY


def test_list_stages_by_framework(client):
    token = get_auth_token(client)
    response = client.get("/methodologies/AIPL/stages", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["stages"]) >= 4
    for s in data["stages"]:
        assert s["framework"] == "AIPL"


def test_get_stage_template(client):
    token = get_auth_token(client)
    response = client.get("/methodologies/stages/mm_aip_interest/template", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert "hook" in data
    assert "body" in data
    assert "cta" in data
    assert "disclaimer" in data
    assert data["hook"]["type"] == "pain_point_resonance"


def test_get_stage_detail(client):
    token = get_auth_token(client)
    response = client.get("/methodologies/stages/mm_aip_interest", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["stage"] == "INTEREST"
    assert data["stage_name"] == "兴趣期"
    assert "content_template" in data
    assert "kpi_targets" in data


def test_evaluate_content(client):
    token = get_auth_token(client)
    response = client.post(
        "/methodologies/stages/mm_aip_interest/evaluate",
        json={
            "body": "姐妹们谁懂啊，我家猫用了XX后好转了。以上仅为个人养宠经验分享，不构成医疗建议。",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "missing_fields" in data
    assert "score" in data
    assert isinstance(data["missing_fields"], list)
    assert isinstance(data["score"], int)


def test_evaluate_content_missing_disclaimer(client):
    token = get_auth_token(client)
    response = client.post(
        "/methodologies/stages/mm_aip_interest/evaluate",
        json={
            "body": "姐妹们谁懂啊，我家猫用了XX后好转了。",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    # Should have lower score due to missing disclaimer and short body/cta
    assert data["score"] < 100
    assert "disclaimer" in data["missing_fields"]
