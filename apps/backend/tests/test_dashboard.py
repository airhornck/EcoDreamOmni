"""
Dashboard module Red-Green tests.
Tests for the operations homepage data APIs.
"""

from src.models.user import clear_users



def get_auth_token(client, role: str = "operator"):
    import uuid
    clear_users()
    email = f"dash_{uuid.uuid4().hex[:8]}@ecodream.com"
    response = client.post("/auth/register", json={
        "email": email,
        "password": "SecurePass123!",
        "username": f"dashuser_{uuid.uuid4().hex[:8]}",
        "role": "operator",
    })
    assert response.status_code == 201, f"Register failed: {response.text}"
    return response.json()["access_token"]
# ───────────────────────────────────────────────
# Red: /dashboard/overview
# ───────────────────────────────────────────────

def test_overview_returns_today_stats(client):
    """Red Dashboard overview should return today's key metrics."""
    token = get_auth_token(client)
    response = client.get("/dashboard/overview", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200, f"Got {response.status_code}: {response.text}"
    data = response.json()
    assert "today" in data
    today = data["today"]
    assert isinstance(today["tasksPending"], int)
    assert isinstance(today["briefsPending"], int)
    assert isinstance(today["contentsPendingReview"], int)
    assert isinstance(today["contentsPublished"], int)
    assert isinstance(today["engagementDelta"], (int, float))
    assert isinstance(today["avgHealthScore"], (int, float))


def test_overview_requires_auth(client):
    """Red Overview endpoint should require authentication."""
    response = client.get("/dashboard/overview")
    assert response.status_code == 401


# ───────────────────────────────────────────────
# Red: /dashboard/quick-actions
# ───────────────────────────────────────────────

def test_quick_actions_returns_actions(client):
    """Red Quick actions should return actionable items for the user."""
    token = get_auth_token(client)
    response = client.get("/dashboard/quick-actions", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200, f"Got {response.status_code}: {response.text}"
    data = response.json()
    assert "actions" in data
    actions = data["actions"]
    assert len(actions) > 0
    for action in actions:
        assert "id" in action
        assert "label" in action
        assert "icon" in action
        assert "href" in action
        assert "badge" in action


# ───────────────────────────────────────────────
# Red: /dashboard/alerts
# ───────────────────────────────────────────────

def test_alerts_returns_alert_list(client):
    """Red Alerts should return real-time alert banners."""
    token = get_auth_token(client)
    response = client.get("/dashboard/alerts", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200, f"Got {response.status_code}: {response.text}"
    data = response.json()
    assert "alerts" in data
    alerts = data["alerts"]
    for alert in alerts:
        assert "id" in alert
        assert "level" in alert  # emergency / warning / info / success
        assert "title" in alert
        assert "message" in alert
        assert "timestamp" in alert


def test_alerts_can_filter_by_level(client):
    """Red Alerts endpoint should support filtering by severity level."""
    token = get_auth_token(client)
    response = client.get("/dashboard/alerts?level=warning", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    for alert in data["alerts"]:
        assert alert["level"] == "warning"


# ───────────────────────────────────────────────
# Red: /dashboard/activity-log
# ───────────────────────────────────────────────

def test_activity_log_returns_entries(client):
    """Red Activity log should return chronological operation records."""
    token = get_auth_token(client)
    response = client.get("/dashboard/activity-log", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200, f"Got {response.status_code}: {response.text}"
    data = response.json()
    assert "entries" in data
    entries = data["entries"]
    for entry in entries:
        assert "id" in entry
        assert "actor" in entry
        assert "action" in entry
        assert "target" in entry
        assert "timestamp" in entry


def test_activity_log_supports_pagination(client):
    """Red Activity log should support limit/offset pagination."""
    token = get_auth_token(client)
    response = client.get("/dashboard/activity-log?limit=5&offset=0", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["entries"]) <= 5
    assert "total" in data
