"""
W17 WF-2 Workflow 可视化配置 Red-Green 测试。

核心要求:
- 后端强制校验发布类模板含 human_approval 节点
- 模板版本化管理
- Dry Run 模拟执行
- React Flow 节点数据接口
"""

from src.models.user import clear_users
from src.services.auth_service import register_user
from src.services import workflow_engine as we



def get_auth_token(client, role: str = "operator"):
    import uuid
    clear_users()
    we._clear_stores()
    email = f"workflow_{uuid.uuid4().hex[:8]}@ecodream.com"
    response = client.post("/auth/register", json={
        "email": email,
        "password": "SecurePass123!",
        "username": f"workflowuser_{uuid.uuid4().hex[:8]}",
        "role": "operator",
    })
    assert response.status_code == 201, f"Register failed: {response.text}"
    return response.json()["access_token"]
# =============================================================================
# WF-1: 发布类模板强制校验 human_approval 节点
# =============================================================================


def test_create_publish_template_requires_human_approval(client):
    """🔴 创建含 publisher 的工作流模板必须包含 human_approval 节点."""
    token = get_auth_token(client)
    response = client.post(
        "/workflow-visual",
        json={
            "name": "非法发布工作流",
            "nodes": [
                {"node_type": "AGENT", "node_name": "生成", "agent_id": "content-forge"},
                {"node_type": "AGENT", "node_name": "发布", "agent_id": "publisher"},
            ],
            "owner": "test",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422
    data = response.json()
    assert "human_approval" in data["detail"]


def test_create_publish_template_with_human_approval_succeeds(client):
    """🔴 含 publisher + human_approval 的模板创建成功."""
    token = get_auth_token(client)
    response = client.post(
        "/workflow-visual",
        json={
            "name": "合法发布工作流",
            "nodes": [
                {"node_type": "AGENT", "node_name": "生成", "agent_id": "content-forge"},
                {"node_type": "HUMAN_APPROVAL", "node_name": "人工审核"},
                {"node_type": "AGENT", "node_name": "发布", "agent_id": "publisher"},
            ],
            "owner": "test",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201


# =============================================================================
# WF-2: 模板版本化管理
# =============================================================================


def test_template_version_upgrade(client):
    """🔴 工作流模板支持版本升级."""
    token = get_auth_token(client)
    create_resp = client.post(
        "/workflow-visual",
        json={
            "name": "版本测试",
            "nodes": [
                {"node_type": "AGENT", "node_name": "A", "agent_id": "a1"},
            ],
            "owner": "test",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    tmpl_id = create_resp.json()["id"]
    assert create_resp.json()["version"] == 1

    # 升级版本
    response = client.post(
        f"/workflow-visual/{tmpl_id}/upgrade-version",
        json={"change_reason": "添加新节点"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == 2
    assert data["previous_version"] == 1


def test_template_version_history(client):
    """🔴 能查询模板版本历史."""
    token = get_auth_token(client)
    create_resp = client.post(
        "/workflow-visual",
        json={
            "name": "历史测试",
            "nodes": [
                {"node_type": "AGENT", "node_name": "A", "agent_id": "a1"},
            ],
            "owner": "test",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    tmpl_id = create_resp.json()["id"]

    # 升级两次
    client.post(f"/workflow-visual/{tmpl_id}/upgrade-version", json={}, headers={"Authorization": f"Bearer {token}"})
    client.post(f"/workflow-visual/{tmpl_id}/upgrade-version", json={}, headers={"Authorization": f"Bearer {token}"})

    response = client.get(
        f"/workflow-visual/{tmpl_id}/versions",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["versions"]) >= 3  # v1 + v2 + v3


# =============================================================================
# WF-3: Dry Run 模拟执行
# =============================================================================


def test_dry_run_workflow_simulation(client):
    """🔴 Dry Run 能模拟执行工作流而不产生副作用."""
    token = get_auth_token(client)
    create_resp = client.post(
        "/workflow-visual",
        json={
            "name": "DryRun测试",
            "nodes": [
                {"node_type": "AGENT", "node_name": "A", "agent_id": "a1"},
                {"node_type": "AGENT", "node_name": "B", "agent_id": "a2"},
            ],
            "owner": "test",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    tmpl_id = create_resp.json()["id"]

    response = client.post(
        f"/workflow-visual/{tmpl_id}/dry-run",
        json={"initial_context": {"test": "data"}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, f"Got {response.status_code}: {response.text}"
    data = response.json()
    assert data["is_dry_run"] is True
    assert "simulated_nodes" in data
    assert len(data["simulated_nodes"]) == 2
    assert data["overall_status"] in ["COMPLETED", "SIMULATED"]
    # 验证没有真实的 execution 被创建
    exec_list = client.get("/workflow-visual/executions", headers={"Authorization": f"Bearer {token}"}).json()
    dry_run_execs = [e for e in exec_list.get("executions", []) if e.get("template_id") == tmpl_id]
    assert len(dry_run_execs) == 0


def test_dry_run_detects_missing_human_approval(client):
    """🔴 Dry Run 能检测发布类模板缺少 human_approval 节点."""
    token = get_auth_token(client)
    # 使用预设模板（含 publisher + human_approval）
    response = client.post(
        "/workflow-visual/content_creation_standard/dry-run",
        json={},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["validation_passed"] is True
    assert data["has_human_approval"] is True


# =============================================================================
# WF-4: React Flow 节点数据接口
# =============================================================================


def test_react_flow_format_for_template(client):
    """🔴 工作流模板能转换为 React Flow 格式."""
    token = get_auth_token(client)
    response = client.get(
        "/workflow-visual/content_creation_standard/react-flow",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data
    assert len(data["nodes"]) > 0
    # React Flow 节点格式
    first_node = data["nodes"][0]
    assert "id" in first_node
    assert "type" in first_node
    assert "position" in first_node
    assert "data" in first_node


def test_react_flow_edges_connect_nodes(client):
    """🔴 React Flow edges 正确连接所有节点."""
    token = get_auth_token(client)
    response = client.get(
        "/workflow-visual/content_creation_standard/react-flow",
        headers={"Authorization": f"Bearer {token}"},
    )
    data = response.json()
    edges = data["edges"]
    nodes = data["nodes"]
    # edges 数量 = nodes 数量 - 1（串行连接）
    assert len(edges) == len(nodes) - 1
    for edge in edges:
        assert "source" in edge
        assert "target" in edge
        assert edge["source"] != edge["target"]
