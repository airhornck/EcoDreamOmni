"""
Agent Orchestra API 测试 — Agent CRUD（含 Update / Delete）。

Red-Green TDD for:
  - PUT /api/agents/{agent_id}   更新 Agent
  - DELETE /api/agents/{agent_id} 删除 Agent
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.services import agent_orchestra as ao


def get_auth_token(client):
    import uuid
    from src.models.user import clear_users
    clear_users()
    ao._agent_db.clear()
    email = f"ao_{uuid.uuid4().hex[:8]}@ecodream.com"
    response = client.post("/auth/register", json={
        "email": email,
        "password": "SecurePass123!",
        "username": f"aouser_{uuid.uuid4().hex[:8]}",
        "role": "operator",
    })
    assert response.status_code == 201, f"Register failed: {response.text}"
    return response.json()["access_token"]


@pytest.fixture(autouse=True)
def clear_db():
    ao._agent_db.clear()
    yield


class TestAgentUpdate:
    """🔴 PUT /agents/{id} 更新 Agent。"""

    def test_update_agent_name_and_role(self, client):
        token = get_auth_token(client)
        agent = ao.create_agent(name="Old Name", role="planner", description="desc")

        response = client.put(
            f"/agents/{agent.id}",
            json={"name": "New Name", "role": "generator", "description": "new desc", "skills": ["sk1"], "config": {}},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name"
        assert data["role"] == "generator"
        assert data["description"] == "new desc"
        assert data["skills"] == ["sk1"]

    def test_update_agent_not_found(self, client):
        token = get_auth_token(client)
        response = client.put(
            "/agents/nonexistent",
            json={"name": "X", "role": "planner", "description": "", "skills": [], "config": {}},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404


class TestAgentDelete:
    """🔴 DELETE /agents/{id} 删除 Agent。"""

    def test_delete_agent(self, client):
        token = get_auth_token(client)
        agent = ao.create_agent(name="ToDelete", role="planner")

        response = client.delete(
            f"/agents/{agent.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 204
        assert ao.get_agent(agent.id) is None

    def test_delete_agent_not_found(self, client):
        token = get_auth_token(client)
        response = client.delete(
            "/agents/nonexistent",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404
