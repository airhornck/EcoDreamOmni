"""
W11 TrendScout Red-Green tests.
Tests for trend report generation and persona clone drafts.
"""

from src.models.user import clear_users
from src.services.auth_service import register_user
from src.services.trend_scout_service import clear_trend_scout



def get_auth_token(client, role: str = "operator"):
    import uuid
    clear_users()
    clear_trend_scout()
    email = f"trend_{uuid.uuid4().hex[:8]}@ecodream.com"
    response = client.post("/auth/register", json={
        "email": email,
        "password": "SecurePass123!",
        "username": f"trenduser_{uuid.uuid4().hex[:8]}",
        "role": "operator",
    })
    assert response.status_code == 201, f"Register failed: {response.text}"
    return response.json()["access_token"]
def test_create_trend_report(client):
    token = get_auth_token(client)
    response = client.post(
        "/trend-scout/reports",
        json={"query": "猫咪驱虫", "stage_filter": "AWARENESS"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201, f"Got {response.status_code}: {response.text}"
    data = response.json()
    assert data["query"] == "猫咪驱虫"
    assert data["stage_filter"] == "AWARENESS"
    assert len(data["results"]) >= 1
    assert "platform_risk_signals" in data
    assert data["source"] == "mock"
    assert data["tenant_id"] is None


def test_create_report_with_source_and_tenant(client):
    token = get_auth_token(client)
    response = client.post(
        "/trend-scout/reports",
        json={"query": "狗狗训练", "stage_filter": "INTEREST", "source": "mock", "tenant_id": "tenant_42"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["source"] == "mock"
    assert data["tenant_id"] == "tenant_42"


def test_create_report_import_items(client):
    token = get_auth_token(client)
    items = [
        {
            "note_id": "import_1",
            "title": "Imported title 1",
            "title_structure": "痛点+解决方案",
            "ces_estimate": 90,
            "traffic_pool": "L5",
            "stage": "DECISION",
            "tags": ["import", "test"],
            "post_time": "10:00",
            "post_day": "周一",
            "persona_signals": {"pet_type": "dog", "voice": "专业"},
        },
        {
            "note_id": "import_2",
            "title": "Imported title 2",
            "title_structure": "数字+对比",
            "ces_estimate": 75,
            "traffic_pool": "L4",
            "stage": "INTEREST",
            "tags": ["import", "compare"],
            "post_time": "14:00",
            "post_day": "周二",
            "persona_signals": {"pet_type": "cat", "voice": "轻松"},
        },
    ]
    response = client.post(
        "/trend-scout/reports",
        json={"query": "导入测试", "stage_filter": "ALL", "items": items, "source": "import", "tenant_id": "t1"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201, f"Got {response.status_code}: {response.text}"
    data = response.json()
    assert data["source"] == "import"
    assert data["tenant_id"] == "t1"
    assert len(data["results"]) == 2
    assert data["results"][0]["note_id"] == "import_1"
    assert data["results"][1]["note_id"] == "import_2"
    assert data["payload_json"] is not None
    assert data["payload_json"]["item_count"] == 2


def test_create_report_requires_auth(client):
    response = client.post("/trend-scout/reports", json={"query": "x"})
    assert response.status_code == 401


def test_list_trend_reports(client):
    token = get_auth_token(client)
    client.post("/trend-scout/reports", json={"query": "Q1"}, headers={"Authorization": f"Bearer {token}"})
    client.post("/trend-scout/reports", json={"query": "Q2"}, headers={"Authorization": f"Bearer {token}"})
    client.post("/trend-scout/reports", json={"query": "Q3"}, headers={"Authorization": f"Bearer {token}"})
    response = client.get("/trend-scout/reports", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["reports"]) >= 3


def test_list_trend_reports_pagination(client):
    token = get_auth_token(client)
    # create 3 reports
    for i in range(3):
        client.post("/trend-scout/reports", json={"query": f"Pag{i}"}, headers={"Authorization": f"Bearer {token}"})
    # skip 1, limit 1
    response = client.get("/trend-scout/reports?skip=1&limit=1", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["reports"]) == 1
    # skip 0, limit 2
    response = client.get("/trend-scout/reports?skip=0&limit=2", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["reports"]) == 2


def test_get_trend_report_detail(client):
    token = get_auth_token(client)
    create_resp = client.post("/trend-scout/reports", json={"query": "Detail"}, headers={"Authorization": f"Bearer {token}"})
    report_id = create_resp.json()["id"]
    response = client.get(f"/trend-scout/reports/{report_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "Detail"
    assert data["source"] == "mock"
    assert "payload_json" in data


def test_create_persona_draft(client):
    token = get_auth_token(client)
    response = client.post(
        "/trend-scout/persona-draft",
        json={"points": ["驱虫避坑", "肠胃调理", "疫苗攻略"]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "draft"
    assert "identity_core" in data
    assert "content_voice" in data
    assert "warnings" in data
    assert len(data["warnings"]) >= 1
    assert "LLM unavailable" in data["warnings"][0]
    preferred = data["content_preferences"]["preferred_topics"]
    assert len(preferred) == 2
    assert preferred[0]["topic"] == "驱虫避坑"
