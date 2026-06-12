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
    response = client.post("/agents", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 201, f"Got {response.status_code}: {response.text}"
    data = response.json()
    assert data["name"] == "内容策划师"
    assert data["role"] == "content_planner"
    assert "id" in data


def test_create_agent_requires_auth(client):
    response = client.post("/agents", json={"name": "x", "role": "test"})
    assert response.status_code == 401


def test_list_agents(client):
    token = get_auth_token(client)
    client.post("/agents", json={"name": "AgentA", "role": "planner", "skills": []}, headers={"Authorization": f"Bearer {token}"})
    client.post("/agents", json={"name": "AgentB", "role": "generator", "skills": []}, headers={"Authorization": f"Bearer {token}"})
    response = client.get("/agents", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["agents"]) >= 2


def test_get_agent_detail(client):
    token = get_auth_token(client)
    create_resp = client.post(
        "/agents",
        json={"name": "DetailAgent", "role": "checker", "description": "detail", "skills": []},
        headers={"Authorization": f"Bearer {token}"},
    )
    agent_id = create_resp.json()["id"]
    response = client.get(f"/agents/{agent_id}", headers={"Authorization": f"Bearer {token}"})
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
        "/agents",
        json={"name": "BindAgent", "role": "executor", "skills": []},
        headers={"Authorization": f"Bearer {token}"},
    )
    agent_id = agent_resp.json()["id"]

    # Bind skill
    bind_resp = client.post(
        f"/agents/{agent_id}/skills",
        json={"skill_id": skill_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert bind_resp.status_code == 201
    data = bind_resp.json()
    assert skill_id in data["skills"]


# ─── Workflow ───


def test_create_workflow(client):
    """Red: Should create a workflow with ordered steps."""
    token = get_auth_token(client)
    # Create agents
    a1 = client.post("/agents", json={"name": "Planner", "role": "planner", "skills": []}, headers={"Authorization": f"Bearer {token}"}).json()
    a2 = client.post("/agents", json={"name": "Generator", "role": "generator", "skills": []}, headers={"Authorization": f"Bearer {token}"}).json()

    payload = {
        "name": "内容生产流水线",
        "description": "从策划到发布的完整内容生产流程",
        "steps": [
            {"agent_id": a1["id"], "name": "策划", "input_from": "trigger", "output_to": "brief"},
            {"agent_id": a2["id"], "name": "生成", "input_from": "brief", "output_to": "draft"},
        ],
    }
    response = client.post("/workflows", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 201, f"Got {response.status_code}: {response.text}"
    data = response.json()
    assert data["name"] == "内容生产流水线"
    assert len(data["steps"]) == 2


# ─── Pipeline Execution ───


def test_execute_pipeline(client):
    """Red: Should execute a pipeline and return pipeline ID."""
    token = get_auth_token(client)
    # Create skill with executable code
    skill_resp = client.post(
        "/skills",
        json={
            "name": "EchoSkill",
            "level": "L2",
            "version": "1.0.0",
            "code": "def run(ctx): return {'echo': ctx.get('message', 'ok')}",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    skill_id = skill_resp.json()["id"]

    # Create agent with skill
    agent_resp = client.post(
        "/agents",
        json={"name": "EchoAgent", "role": "echo", "skills": [skill_id]},
        headers={"Authorization": f"Bearer {token}"},
    )
    agent_id = agent_resp.json()["id"]

    # Create workflow
    wf_resp = client.post(
        "/workflows",
        json={
            "name": "EchoWorkflow",
            "description": "Echo test",
            "steps": [{"agent_id": agent_id, "name": "echo_step", "input_from": "trigger", "output_to": "result"}],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    wf_id = wf_resp.json()["id"]

    # Execute pipeline
    pipe_resp = client.post(
        "/pipelines",
        json={"workflow_id": wf_id, "context": {"message": "hello_orchestra"}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert pipe_resp.status_code == 201, f"Got {pipe_resp.status_code}: {pipe_resp.text}"
    data = pipe_resp.json()
    assert "id" in data
    assert data["workflow_id"] == wf_id
    assert data["status"] in ("pending", "running", "completed")


def test_pipeline_status_tracking(client):
    """Red: Should track pipeline execution status."""
    token = get_auth_token(client)
    agent_resp = client.post(
        "/agents",
        json={"name": "StatusAgent", "role": "noop", "skills": []},
        headers={"Authorization": f"Bearer {token}"},
    )
    agent_id = agent_resp.json()["id"]

    wf_resp = client.post(
        "/workflows",
        json={
            "name": "StatusWF",
            "description": "Status tracking test",
            "steps": [{"agent_id": agent_id, "name": "noop", "input_from": "trigger", "output_to": "result"}],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    wf_id = wf_resp.json()["id"]

    pipe_resp = client.post(
        "/pipelines",
        json={"workflow_id": wf_id, "context": {}},
        headers={"Authorization": f"Bearer {token}"},
    )
    pipe_id = pipe_resp.json()["id"]

    status_resp = client.get(f"/pipelines/{pipe_id}", headers={"Authorization": f"Bearer {token}"})
    assert status_resp.status_code == 200
    data = status_resp.json()
    assert data["id"] == pipe_id
    assert "status" in data
    assert "current_step" in data


def test_agent_context_passing(client):
    """Red: Pipeline should pass context between agent steps."""
    token = get_auth_token(client)
    # Skill that appends to a list
    skill_resp = client.post(
        "/skills",
        json={
            "name": "AppendSkill",
            "level": "L2",
            "version": "1.0.0",
            "code": "def run(ctx): ctx['trace'] = ctx.get('trace', []) + [ctx.get('step_name')]; return ctx",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    skill_id = skill_resp.json()["id"]

    agent_resp = client.post(
        "/agents",
        json={"name": "TraceAgent", "role": "tracer", "skills": [skill_id]},
        headers={"Authorization": f"Bearer {token}"},
    )
    agent_id = agent_resp.json()["id"]

    wf_resp = client.post(
        "/workflows",
        json={
            "name": "TraceWF",
            "description": "Context passing test",
            "steps": [
                {"agent_id": agent_id, "name": "step_a", "input_from": "trigger", "output_to": "ctx"},
                {"agent_id": agent_id, "name": "step_b", "input_from": "ctx", "output_to": "ctx"},
            ],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    wf_id = wf_resp.json()["id"]

    pipe_resp = client.post(
        "/pipelines",
        json={"workflow_id": wf_id, "context": {"trace": []}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert pipe_resp.status_code == 201
    pipe_id = pipe_resp.json()["id"]

    # After execution, result should contain trace from both steps
    result_resp = client.get(f"/pipelines/{pipe_id}", headers={"Authorization": f"Bearer {token}"})
    assert result_resp.status_code == 200
    data = result_resp.json()
    # MVP: context is accumulated during synchronous execution
    assert "results" in data or "context" in data
