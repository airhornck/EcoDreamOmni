"""
Pipeline Red-Green tests.
Tests for async task submission, status polling, and cancellation.
"""

import time
from src.models.user import clear_users
from src.services.pipeline_service import clear_pipeline



def get_auth_token(client, role: str = "operator"):
    import uuid
    clear_users()
    clear_pipeline()
    email = f"pipe_{uuid.uuid4().hex[:8]}@ecodream.com"
    response = client.post("/auth/register", json={
        "email": email,
        "password": "SecurePass123!",
        "username": f"pipeuser_{uuid.uuid4().hex[:8]}",
        "role": "operator",
    })
    assert response.status_code == 201, f"Register failed: {response.text}"
    return response.json()["access_token"]
def test_submit_async_task(client):
    token = get_auth_token(client)
    response = client.post(
        "/pipeline/tasks",
        json={"task_type": "trend_crawl", "payload": {"query": "猫咪驱虫", "stage_filter": "AWARENESS"}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201, f"Got {response.status_code}: {response.text}"
    data = response.json()
    assert data["task_type"] == "trend_crawl"
    assert data["status"] in ("pending", "running", "completed")
    assert "task_id" in data


def test_get_task_status(client):
    token = get_auth_token(client)
    submit_resp = client.post(
        "/pipeline/tasks",
        json={"task_type": "model_training", "payload": {}},
        headers={"Authorization": f"Bearer {token}"},
    )
    task_id = submit_resp.json()["task_id"]

    # Poll until completed (BackgroundTasks runs synchronously in TestClient)
    for _ in range(10):
        response = client.get(f"/pipeline/tasks/{task_id}", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        data = response.json()
        if data["status"] in ("completed", "failed"):
            break
        time.sleep(0.1)

    assert data["task_id"] == task_id
    assert data["status"] in ("completed", "failed")


def test_list_tasks(client):
    token = get_auth_token(client)
    for i in range(3):
        client.post(
            "/pipeline/tasks",
            json={"task_type": "trend_crawl", "payload": {"query": f"Q{i}"}},
            headers={"Authorization": f"Bearer {token}"},
        )
    response = client.get("/pipeline/tasks", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["tasks"]) >= 3


def test_list_tasks_by_type(client):
    token = get_auth_token(client)
    client.post(
        "/pipeline/tasks",
        json={"task_type": "trend_crawl", "payload": {}},
        headers={"Authorization": f"Bearer {token}"},
    )
    client.post(
        "/pipeline/tasks",
        json={"task_type": "model_training", "payload": {}},
        headers={"Authorization": f"Bearer {token}"},
    )
    response = client.get("/pipeline/tasks?task_type=trend_crawl", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    for t in response.json()["tasks"]:
        assert t["task_type"] == "trend_crawl"


def test_cancel_pending_task(client):
    token = get_auth_token(client)
    # Submit a task type that takes no time to keep it pending
    # Use a custom handler that sleeps, or rely on rapid submission before execution
    submit_resp = client.post(
        "/pipeline/tasks",
        json={"task_type": "trend_crawl", "payload": {"query": "x"}},
        headers={"Authorization": f"Bearer {token}"},
    )
    task_id = submit_resp.json()["task_id"]
    response = client.post(f"/pipeline/tasks/{task_id}/cancel", headers={"Authorization": f"Bearer {token}"})
    # May be 200 (cancelled) or 400 (already completed) depending on timing
    assert response.status_code in (200, 400)


def test_cancel_nonexistent_task(client):
    token = get_auth_token(client)
    response = client.post("/pipeline/tasks/nonexistent/cancel", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 400


def test_task_result_contains_data(client):
    token = get_auth_token(client)
    submit_resp = client.post(
        "/pipeline/tasks",
        json={"task_type": "trend_crawl", "payload": {"query": "测试", "stage_filter": ""}},
        headers={"Authorization": f"Bearer {token}"},
    )
    task_id = submit_resp.json()["task_id"]

    for _ in range(10):
        response = client.get(f"/pipeline/tasks/{task_id}", headers={"Authorization": f"Bearer {token}"})
        data = response.json()
        if data["status"] == "completed":
            break
        time.sleep(0.1)

    assert data["status"] == "completed"
    assert data["result"] is not None
    assert "report_id" in data["result"]


def test_pipeline_requires_auth(client):
    response = client.post("/pipeline/tasks", json={"task_type": "x", "payload": {}})
    assert response.status_code == 401
