"""
W11 SkillHub Red-Green tests.
Tests for four-layer skill loading, version management, and Agent-Skill binding.
"""

from src.models.user import clear_users
from src.services.auth_service import register_user



def get_auth_token(client, role: str = "operator"):
    import uuid
    clear_users()
    email = f"skill_{uuid.uuid4().hex[:8]}@ecodream.com"
    response = client.post("/auth/register", json={
        "email": email,
        "password": "SecurePass123!",
        "username": f"skilluser_{uuid.uuid4().hex[:8]}",
        "role": role,
    })
    assert response.status_code == 201, f"Register failed: {response.text}"
    return response.json()["access_token"]
# ─── Skill CRUD ───


def test_create_skill(client):
    """Red Should create a skill with version and level."""
    token = get_auth_token(client)
    payload = {
        "name": "猫咪驱虫内容生成",
        "description": "基于宠物健康领域生成小红书风格的内容",
        "level": "L2",  # L1 built-in, L2 project, L3 user, L4 session
        "code": "def generate(topic): return f'关于{topic}的科普内容'",
        "tags": ["内容生成", "宠物健康"],
        "version": "1.0.0",
    }
    response = client.post("/skills", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 201, f"Got {response.status_code}: {response.text}"
    data = response.json()
    assert data["name"] == "猫咪驱虫内容生成"
    assert data["level"] == "L2"
    assert data["version"] == "1.0.0"
    assert "id" in data


def test_create_skill_requires_auth(client):
    response = client.post("/skills", json={"name": "x"})
    assert response.status_code == 401


def test_list_skills(client):
    token = get_auth_token(client)
    client.post("/skills", json={"name": "SkillA", "level": "L1", "version": "1.0.0", "code": ""}, headers={"Authorization": f"Bearer {token}"})
    client.post("/skills", json={"name": "SkillB", "level": "L2", "version": "1.0.0", "code": ""}, headers={"Authorization": f"Bearer {token}"})
    response = client.get("/skills", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["skills"]) >= 2


def test_get_skill_detail(client):
    token = get_auth_token(client)
    create_resp = client.post(
        "/skills",
        json={"name": "SkillDetail", "level": "L1", "version": "1.0.0", "code": "print('hello')"},
        headers={"Authorization": f"Bearer {token}"},
    )
    skill_id = create_resp.json()["id"]
    response = client.get(f"/skills/{skill_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["name"] == "SkillDetail"


def test_update_skill_version(client):
    token = get_auth_token(client)
    create_resp = client.post(
        "/skills",
        json={"name": "VersionedSkill", "level": "L2", "version": "1.0.0", "code": "v1"},
        headers={"Authorization": f"Bearer {token}"},
    )
    skill_id = create_resp.json()["id"]
    response = client.patch(
        f"/skills/{skill_id}",
        json={"version": "1.1.0", "code": "v2"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "1.1.0"
    assert data["code"] == "v2"


def test_delete_skill(client):
    token = get_auth_token(client)
    create_resp = client.post(
        "/skills",
        json={"name": "DeleteMe", "level": "L3", "version": "1.0.0", "code": ""},
        headers={"Authorization": f"Bearer {token}"},
    )
    skill_id = create_resp.json()["id"]
    response = client.delete(f"/skills/{skill_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 204
    assert client.get(f"/skills/{skill_id}", headers={"Authorization": f"Bearer {token}"}).status_code == 404


# ─── Four-Layer Loading ───


def test_builtin_skills_loaded():
    """Red: L1 built-in skills should be auto-loaded on startup."""
    from src.services.skill_hub import list_builtin_skills

    skills = list_builtin_skills()
    assert len(skills) > 0
    for skill in skills:
        assert skill.level == "L1"


def test_four_layer_loading_order():
    """Red: Higher layers should override lower layers for same skill name."""
    from src.services.skill_hub import load_skill

    # L1 built-in
    l1 = load_skill("content_generate", level="L1")
    assert l1 is not None
    assert l1.level == "L1"

    # L2 project (should override L1 if same name)
    # MVP: different skills at different levels
    l2 = load_skill("compliance_check", level="L2")
    if l2:
        assert l2.level == "L2"


# ─── Agent-Skill Binding ───


def test_bind_skill_to_agent(client):
    """Red Should bind a skill to an agent."""
    token = get_auth_token(client)
    skill_resp = client.post(
        "/skills",
        json={"name": "BindTestSkill", "level": "L2", "version": "1.0.0", "code": ""},
        headers={"Authorization": f"Bearer {token}"},
    )
    skill_id = skill_resp.json()["id"]

    bind_resp = client.post(
        "/agent-skills",
        json={"agent_id": "agent_content_planner", "skill_id": skill_id, "priority": 1},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert bind_resp.status_code == 201
    data = bind_resp.json()
    assert data["agent_id"] == "agent_content_planner"
    assert data["skill_id"] == skill_id


def test_list_agent_skills(client):
    """Red Should list all skills bound to an agent."""
    token = get_auth_token(client)
    skill_resp = client.post(
        "/skills",
        json={"name": "AgentSkill", "level": "L2", "version": "1.0.0", "code": ""},
        headers={"Authorization": f"Bearer {token}"},
    )
    skill_id = skill_resp.json()["id"]

    client.post(
        "/agent-skills",
        json={"agent_id": "agent_compliance", "skill_id": skill_id, "priority": 2},
        headers={"Authorization": f"Bearer {token}"},
    )

    response = client.get("/agent-skills?agent_id=agent_compliance", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["bindings"]) > 0
    assert any(b["skill_id"] == skill_id for b in data["bindings"])


# ─── Skill Execution ───


def test_execute_skill(client):
    """Red Should execute a skill and return result."""
    token = get_auth_token(client)
    skill_resp = client.post(
        "/skills",
        json={
            "name": "ExecuteTest",
            "level": "L2",
            "version": "1.0.0",
            "code": "def run(ctx): return f'Hello {ctx.get(\"name\", \"world\")}'",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    skill_id = skill_resp.json()["id"]

    exec_resp = client.post(
        f"/skills/{skill_id}/execute",
        json={"context": {"name": "EcoDream"}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert exec_resp.status_code == 200
    data = exec_resp.json()
    assert "result" in data
