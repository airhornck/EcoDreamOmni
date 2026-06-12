"""
SkillSmith Red-Green tests.
Tests for evolved skill auto-generation based on performance triggers.
"""

from src.models.user import clear_users
from src.services.auth_service import register_user
from src.services.skill_smith import clear_skill_smith
from src.services.skill_hub import clear_skills



def get_auth_token(client, role: str = "operator"):
    import uuid
    clear_users()
    clear_skills()
    clear_skill_smith()
    email = f"smith_{uuid.uuid4().hex[:8]}@ecodream.com"
    response = client.post("/auth/register", json={
        "email": email,
        "password": "SecurePass123!",
        "username": f"smithuser_{uuid.uuid4().hex[:8]}",
        "role": "operator",
    })
    assert response.status_code == 201, f"Register failed: {response.text}"
    return response.json()["access_token"]
def test_record_performance(client):
    token = get_auth_token(client)
    response = client.post(
        "/skill-smith/record-performance",
        json={"skill_id": "L1-content-generate", "account_id": "acc_001", "success": True, "ces": 45.0, "mape": 0.15},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    assert response.json()["status"] == "recorded"


def test_check_evolution_opportunities_success_rate(client):
    token = get_auth_token(client)
    # Record 5 successes
    for i in range(5):
        client.post(
            "/skill-smith/record-performance",
            json={"skill_id": "L1-content-generate", "account_id": "acc_001", "success": True, "ces": 45.0},
            headers={"Authorization": f"Bearer {token}"},
        )
    response = client.get(
        "/skill-smith/opportunities/L1-content-generate?account_id=acc_001",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["opportunities"]) >= 1
    assert any(o["condition_type"] == "success_rate" for o in data["opportunities"])


def test_check_evolution_opportunities_ces_streak(client):
    token = get_auth_token(client)
    for i in range(3):
        client.post(
            "/skill-smith/record-performance",
            json={"skill_id": "L1-compliance-check", "account_id": "acc_002", "success": True, "ces": 50.0 + i},
            headers={"Authorization": f"Bearer {token}"},
        )
    response = client.get(
        "/skill-smith/opportunities/L1-compliance-check?account_id=acc_002",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert any(o["condition_type"] == "ces_streak" for o in data["opportunities"])


def test_check_evolution_opportunities_mape(client):
    token = get_auth_token(client)
    for i in range(3):
        client.post(
            "/skill-smith/record-performance",
            json={"skill_id": "L1-engagement-predict", "account_id": "acc_003", "success": True, "ces": 30.0, "mape": 0.1},
            headers={"Authorization": f"Bearer {token}"},
        )
    response = client.get(
        "/skill-smith/opportunities/L1-engagement-predict?account_id=acc_003",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert any(o["condition_type"] == "mape_threshold" for o in data["opportunities"])


def test_evolve_skill(client):
    token = get_auth_token(client)
    # Seed performance
    for i in range(5):
        client.post(
            "/skill-smith/record-performance",
            json={"skill_id": "L1-content-generate", "account_id": "acc_001", "success": True, "ces": 45.0},
            headers={"Authorization": f"Bearer {token}"},
        )
    response = client.post(
        "/skill-smith/evolve/L1-content-generate",
        json={"account_id": "acc_001", "condition_type": "success_rate"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201, f"Got {response.status_code}: {response.text}"
    data = response.json()
    assert "evolved_skill_id" in data
    assert data["source_skill_id"] == "L1-content-generate"
    assert data["account_id"] == "acc_001"
    assert data["condition_type"] == "success_rate"


def test_evolve_skill_requires_performance_data(client):
    token = get_auth_token(client)
    response = client.post(
        "/skill-smith/evolve/L1-content-generate",
        json={"account_id": "acc_no_data", "condition_type": "success_rate"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400


def test_list_evolution_triggers(client):
    token = get_auth_token(client)
    for i in range(5):
        client.post(
            "/skill-smith/record-performance",
            json={"skill_id": "L1-content-generate", "account_id": "acc_004", "success": True, "ces": 45.0},
            headers={"Authorization": f"Bearer {token}"},
        )
    client.post(
        "/skill-smith/evolve/L1-content-generate",
        json={"account_id": "acc_004", "condition_type": "success_rate"},
        headers={"Authorization": f"Bearer {token}"},
    )
    response = client.get("/skill-smith/triggers", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["triggers"]) >= 1


def test_record_performance_requires_auth(client):
    response = client.post("/skill-smith/record-performance", json={"skill_id": "x", "account_id": "a", "success": True})
    assert response.status_code == 401
