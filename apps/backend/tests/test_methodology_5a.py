"""
W15-2 MarketingMethodology 5A — Red phase tests.
Tests for 5A methodology engine (AIPL→5A migration).
"""

import pytest
from src.models.user import clear_users
from src.services.auth_service import register_user
from src.services.methodology_5a_service import clear_5a_methodologies



def get_auth_token(client, role: str = "operator"):
    import uuid
    clear_users()
    clear_5a_methodologies()
    email = f"mm5a_{uuid.uuid4().hex[:8]}@ecodream.com"
    response = client.post("/auth/register", json={
        "email": email,
        "password": "SecurePass123!",
        "username": f"mm5auser_{uuid.uuid4().hex[:8]}",
        "role": "operator",
    })
    assert response.status_code == 201, f"Register failed: {response.text}"
    return response.json()["access_token"]
# ===== 5A阶段定义测试 =====

def test_list_5a_methodologies(client):
    """Test listing 5A methodologies."""
    token = get_auth_token(client)
    response = client.get("/methodologies", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert "methodologies" in data
    frameworks = [m["framework"] for m in data["methodologies"]]
    assert "5A" in frameworks


def test_list_5a_stages(client):
    """Test listing all 5A stages."""
    token = get_auth_token(client)
    response = client.get("/methodologies/stages", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    stages = data["stages"]
    stage_names = [s["stage"] for s in stages]
    assert "AWARE" in stage_names
    assert "APPEAL" in stage_names
    assert "ASK" in stage_names
    assert "ACT" in stage_names
    assert "ADVOCATE" in stage_names


def test_list_stages_by_5a_framework(client):
    """Test listing stages by 5A framework."""
    token = get_auth_token(client)
    response = client.get("/methodologies/5A/stages", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["stages"]) == 5
    for s in data["stages"]:
        assert s["framework"] == "5A"


def test_get_5a_stage_detail(client):
    """Test getting 5A stage detail."""
    token = get_auth_token(client)
    response = client.get("/methodologies/stages/mm_5a_ask", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["stage"] == "ASK"
    assert data["stage_name"] == "问询期"
    assert "content_template" in data
    assert "kpi_targets" in data


def test_get_5a_stage_template(client):
    """Test getting 5A stage content template."""
    token = get_auth_token(client)
    response = client.get("/methodologies/stages/mm_5a_appeal/template", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert "hook" in data
    assert "body" in data
    assert "cta" in data
    assert "disclaimer" in data


# ===== AIPL→5A映射测试 =====

def test_aipl_to_5a_stage_mapping(client):
    """Test AIPL to 5A stage mapping."""
    token = get_auth_token(client)
    mappings = [
        ("AWARENESS", "AWARE"),
        ("INTEREST", "APPEAL"),
        ("PURCHASE", "ACT"),
        ("LOYALTY", "ADVOCATE"),
    ]
    for aipl_stage, expected_5a in mappings:
        response = client.get(f"/methodologies/aipl/{aipl_stage}/to-5a", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        data = response.json()
        assert data["target_stage"] == expected_5a


def test_5a_to_aipl_stage_mapping(client):
    """Test 5A to AIPL stage reverse mapping."""
    token = get_auth_token(client)
    mappings = [
        ("AWARE", "AWARENESS"),
        ("APPEAL", "INTEREST"),
        ("ASK", "INTEREST"),  # ASK aligns with INTEREST in AIPL
        ("ACT", "PURCHASE"),
        ("ADVOCATE", "LOYALTY"),
    ]
    for stage_5a, expected_aipl in mappings:
        response = client.get(f"/methodologies/5a/{stage_5a}/to-aipl", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        data = response.json()
        assert data["target_stage"] == expected_aipl


# ===== 人群定向测试 =====

def test_get_stage_audience_segments(client):
    """Test getting audience segments for a 5A stage."""
    token = get_auth_token(client)
    response = client.get("/methodologies/stages/mm_5a_aware/audience", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert "audience_segments" in data
    assert len(data["audience_segments"]) > 0


def test_get_persona_recommendations_by_stage(client):
    """Test getting persona recommendations for a stage."""
    token = get_auth_token(client)
    response = client.get("/methodologies/stages/mm_5a_act/personas", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert "recommended_personas" in data
    assert isinstance(data["recommended_personas"], list)


# ===== 内容评估测试 =====

def test_evaluate_5a_content(client):
    """Test evaluating content against 5A stage requirements."""
    token = get_auth_token(client)
    response = client.post(
        "/methodologies/stages/mm_5a_ask/evaluate",
        json={
            "body": "姐妹们，我家猫总是拉稀怎么办？有没有什么经验可以分享？求推荐靠谱的宠物医院。"
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "score" in data
    assert "stage_match" in data
    assert "missing_elements" in data
    assert data["stage_match"] == "ASK"


def test_evaluate_5a_content_forbidden_elements(client):
    """Test detecting forbidden elements in 5A content."""
    token = get_auth_token(client)
    # ACT stage forbidden_elements ["疗效保证", "100%有效", "医生同款", "医院专用"]
    response = client.post(
        "/methodologies/stages/mm_5a_act/evaluate",
        json={
            "body": "这个产品100%有效！医生同款专用，疗效保证。购买前请咨询专业人士。"
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["score"] < 60  # Should be low due to forbidden elements
    assert "forbidden_found" in data
    assert len(data["forbidden_found"]) > 0
