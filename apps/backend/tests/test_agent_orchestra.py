"""
W12 Agent Orchestra Red-Green tests.
Tests for multi-agent orchestration: agents, workflows, pipelines, context passing.
"""

from src.models.user import clear_users
from src.services.auth_service import register_user



def get_auth_token(client, role: str = "operator"):
    import uuid
    clear_users()
    email = f"orchestra_{uuid.uuid4().hex[:8]}@ecodream.com"
    response = client.post("/auth/register", json={
        "email": email,
        "password": "SecurePass123!",
        "username": f"orchestrauser_{uuid.uuid4().hex[:8]}",
        "role": role,
    })
    assert response.status_code == 201, f"Register failed: {response.text}"
    return response.json()["access_token"]
# ─── Agent CRUD ───


def test_create_agent(client):
    """Red: Should create an agent with role and skills."""
    token = get_auth_token(client)
    payload = {
        "name": "内容策划师",
        "role": "content_planner",
        "description": "负责根据热点话题策划内容方向",
        "skills": [],
        "config": {"max_topics_per_day": 5},
    }
    response = client.post("/agent-orchestra/agents", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 201, f"Got {response.status_code}: {response.text}"
    data = response.json()
    assert data["name"] == "内容策划师"
    assert data["role"] == "content_planner"
    assert "id" in data


def test_create_agent_requires_auth(client):
    response = client.post("/agent-orchestra/agents", json={"name": "x", "role": "test"})
    assert response.status_code == 401


def test_list_agents(client):
    token = get_auth_token(client)
    client.post("/agent-orchestra/agents", json={"name": "AgentA", "role": "planner", "skills": []}, headers={"Authorization": f"Bearer {token}"})
    client.post("/agent-orchestra/agents", json={"name": "AgentB", "role": "generator", "skills": []}, headers={"Authorization": f"Bearer {token}"})
    response = client.get("/agent-orchestra/agents", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["agents"]) >= 2


def test_get_agent_detail(client):
    token = get_auth_token(client)
    create_resp = client.post(
        "/agent-orchestra/agents",
        json={"name": "DetailAgent", "role": "checker", "description": "detail", "skills": []},
        headers={"Authorization": f"Bearer {token}"},
    )
    agent_id = create_resp.json()["id"]
    response = client.get(f"/agent-orchestra/agents/{agent_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["name"] == "DetailAgent"


# ─── Agent-Skill Binding via Orchestra ───


def test_bind_skill_to_agent(client):
    """Red: Should bind a skill to an agent via orchestra API."""
    token = get_auth_token(client)
    # Create a skill first
    skill_resp = client.post(
        "/skills",
        json={"name": "OrchestraSkill", "level": "L2", "version": "1.0.0", "code": "pass"},
        headers={"Authorization": f"Bearer {token}"},
    )
    skill_id = skill_resp.json()["id"]

    # Create an agent
    agent_resp = client.post(
        "/agent-orchestra/agents",
        json={"name": "BindAgent", "role": "executor", "skills": []},
        headers={"Authorization": f"Bearer {token}"},
    )
    agent_id = agent_resp.json()["id"]

    # Bind skill
    bind_resp = client.post(
        f"/agent-orchestra/agents/{agent_id}/skills",
        json={"skill_id": skill_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert bind_resp.status_code == 201
    data = bind_resp.json()
    assert skill_id in data["skills"]


