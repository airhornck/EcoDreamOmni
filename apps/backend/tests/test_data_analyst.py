"""
W13 DataAnalyst Red-Green tests.
Tests for 24h data回流, MAPE, dashboard, calibration, CSV upload, attribution.
"""

from src.models.user import clear_users
from src.services.auth_service import register_user
from src.services.data_analyst_service import clear_data_analyst



def get_auth_token(client, role: str = "operator"):
    import uuid
    clear_users()
    clear_data_analyst()
    email = f"da_{uuid.uuid4().hex[:8]}@ecodream.com"
    response = client.post("/auth/register", json={
        "email": email,
        "password": "SecurePass123!",
        "username": f"dauser_{uuid.uuid4().hex[:8]}",
        "role": "operator",
    })
    assert response.status_code == 201, f"Register failed: {response.text}"
    return response.json()["access_token"]
def test_create_data_report(client):
    token = get_auth_token(client)
    response = client.post(
        "/data-analyst/reports",
        json={
            "account_id": "acc_001",
            "content_id": "c_001",
            "predicted_ces": 42.0,
            "predicted_pool": "L3",
            "period": "24h",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201, f"Got {response.status_code}: {response.text}"
    data = response.json()
    assert data["account_id"] == "acc_001"
    assert "actual_metrics" in data
    assert "prediction_comparison" in data
    assert "attribution" in data
    assert "model_calibration" in data


def test_create_data_report_csv(client):
    token = get_auth_token(client)
    csv_content = (
        "content_id,actual_likes,actual_comments,actual_saves\n"
        "c_csv_001,100,20,5\n"
        "c_csv_002,200,40,10\n"
    )
    response = client.post(
        "/data-analyst/reports",
        data={"account_id": "acc_csv", "predicted_ces": 150.0},
        files={"file": ("test.csv", csv_content, "text/csv")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201, f"Got {response.status_code}: {response.text}"
    data = response.json()
    assert "count" in data
    assert data["count"] == 2
    assert "reports" in data
    assert len(data["reports"]) == 2
    for report in data["reports"]:
        assert "actual_metrics" in report
        assert "prediction_comparison" in report
        assert "mape" in report["prediction_comparison"]


def test_get_data_report(client):
    token = get_auth_token(client)
    create_resp = client.post(
        "/data-analyst/reports",
        json={"account_id": "acc_002", "content_id": "c_002", "predicted_ces": 50.0},
        headers={"Authorization": f"Bearer {token}"},
    )
    report_id = create_resp.json()["id"]
    response = client.get(f"/data-analyst/reports/{report_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == report_id
    assert "mape" in data["prediction_comparison"]


def test_dashboard_summary(client):
    token = get_auth_token(client)
    # Seed some reports
    for i in range(3):
        client.post(
            "/data-analyst/reports",
            json={"account_id": f"acc_{i}", "content_id": f"c_{i}", "predicted_ces": 40.0 + i * 5},
            headers={"Authorization": f"Bearer {token}"},
        )
    response = client.get("/data-analyst/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["published_count"] >= 3
    assert data["avg_ces"] > 0
    assert "has_data" in data
    assert "coverage_applicable" in data


def test_dashboard_empty_state(client):
    token = get_auth_token(client)
    response = client.get("/data-analyst/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["has_data"] is False
    assert "guide" in data
    assert "coverage_applicable" in data
    assert data["coverage_applicable"] is False


def test_attribution(client):
    token = get_auth_token(client)
    client.post(
        "/data-analyst/reports",
        json={"account_id": "acc_att", "content_id": "c_att", "predicted_ces": 45.0},
        headers={"Authorization": f"Bearer {token}"},
    )
    response = client.get("/data-analyst/attribution/c_att", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["content_id"] == "c_att"
    assert "prediction_comparison" in data
    assert "top_features" in data
    assert len(data["top_features"]) > 0


def test_attribution_not_found(client):
    token = get_auth_token(client)
    response = client.get("/data-analyst/attribution/nonexistent", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404


def test_calibrate(client):
    token = get_auth_token(client)
    response = client.post("/data-analyst/calibrate", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 201
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "pending"
    assert "message" in data


def test_calibration_check(client):
    token = get_auth_token(client)
    # Create a report with large prediction error (>25% MAPE)
    client.post(
        "/data-analyst/reports",
        json={"account_id": "acc_big", "content_id": "c_big", "predicted_ces": 10.0},
        headers={"Authorization": f"Bearer {token}"},
    )
    response = client.get("/data-analyst/calibration-check", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert "needs_calibration" in data
    assert "count" in data
