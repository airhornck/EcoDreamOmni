"""
W13 Real-time Alert Stream Red-Green tests.
Tests for WebSocket alert pushing and alert generator.
"""

import pytest
import asyncio
from src.models.user import clear_users
from src.services.auth_service import register_user
from src.services.alert_stream import get_manager, generate_alert, clear_alerts, broadcast_alert



def get_auth_token(client, role: str = "operator"):
    import uuid
    clear_users()
    email = f"ws_{uuid.uuid4().hex[:8]}@ecodream.com"
    response = client.post("/auth/register", json={
        "email": email,
        "password": "SecurePass123!",
        "username": f"wsuser_{uuid.uuid4().hex[:8]}",
        "role": role,
    })
    assert response.status_code == 201, f"Register failed: {response.text}"
    return response.json()["access_token"]
@pytest.fixture(autouse=True)
def clean_alerts():
    clear_alerts()


# ─── WebSocket Connection ───


@pytest.mark.asyncio
async def test_websocket_connect_and_receive_alert(client):
    """Red: Should connect to /ws/alerts and receive a broadcasted alert."""
    token = get_auth_token(client)
    manager = get_manager()
    with client.websocket_connect(f"/ws/alerts?token={token}") as websocket:
        alert = generate_alert(level="warning", title="测试告警", message="WebSocket 实时推送测试")
        await manager.broadcast(alert)
        data = websocket.receive_json()
        assert data["level"] == "warning"
        assert data["title"] == "测试告警"


@pytest.mark.asyncio
async def test_websocket_requires_auth():
    """Red: Should reject unauthenticated WebSocket connections."""
    with pytest.raises(Exception):
        with client.websocket_connect("/ws/alerts") as websocket:
            websocket.receive_json()


@pytest.mark.asyncio
async def test_alert_broadcast_to_multiple_clients(client):
    """Red: Should broadcast alerts to all connected clients."""
    token = get_auth_token(client)
    manager = get_manager()
    with client.websocket_connect(f"/ws/alerts?token={token}") as ws1:
        with client.websocket_connect(f"/ws/alerts?token={token}") as ws2:
            alert = generate_alert(level="emergency", title="全局告警", message="所有客户端应收到")
            await manager.broadcast(alert)
            d1 = ws1.receive_json()
            d2 = ws2.receive_json()
            assert d1["title"] == "全局告警"
            assert d2["title"] == "全局告警"


# ─── Alert Generator ───


@pytest.mark.asyncio
async def test_alert_generator_creates_alert(client):
    """Red: Alert generator should produce an alert and broadcast it."""
    token = get_auth_token(client)
    manager = get_manager()
    with client.websocket_connect(f"/ws/alerts?token={token}") as websocket:
        alert = generate_alert(level="warning", title="生成器测试", message="由生成器触发")
        await manager.broadcast(alert)
        data = websocket.receive_json()
        assert data["level"] == "warning"
        assert data["title"] == "生成器测试"


def test_alert_history_api_includes_generated(client):
    """Red Alerts pushed via stream should be queryable via REST."""
    token = get_auth_token(client)
    generate_alert(level="info", title="历史测试", message="应存入历史")
    response = client.get("/api/alerts", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert any(a["title"] == "历史测试" for a in data.get("alerts", []))
