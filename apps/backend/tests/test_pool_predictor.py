"""
W9 PoolPredictor Red-Green tests aligned with detailed design §5.1.
Tests for interval prediction structure, feature engineering, and model metrics.
"""

import numpy as np
from src.models.user import clear_users
from src.services.auth_service import register_user



def get_auth_token(client, role: str = "operator"):
    import uuid
    clear_users()
    email = f"pp_{uuid.uuid4().hex[:8]}@ecodream.com"
    response = client.post("/auth/register", json={
        "email": email,
        "password": "SecurePass123!",
        "username": f"ppuser_{uuid.uuid4().hex[:8]}",
        "role": "operator",
    })
    assert response.status_code == 201, f"Register failed: {response.text}"
    return response.json()["access_token"]
# ─── Prediction API ───


def test_submit_prediction_request(client):
    """Red Should submit a prediction request and return interval-structured engagement."""
    token = get_auth_token(client)
    payload = {
        "account_id": "pool_xhs_001",
        "content_type": "note",
        "topic": "猫咪驱虫",
        "lifecycle_phase": "cold_start",
        "platform": "xhs",
        "word_count": 300,
        "has_image": True,
        "has_video": False,
        "publish_hour": 10,
    }
    response = client.post("/predictions", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200, f"Got {response.status_code}: {response.text}"
    data = response.json()
    assert "prediction_id" in data
    assert "likes" in data
    assert "comments" in data
    assert "saves" in data
    assert "interval_mode" in data
    assert data["interval_mode"] in ("prior", "fitted")
    assert "confidence" in data
    assert 0 <= data["confidence"] <= 1
    assert "feature_version" in data
    assert data["feature_version"].startswith("v")
    # Verify interval structure
    for metric in ("likes", "comments", "saves"):
        assert "lower" in data[metric]
        assert "median" in data[metric]
        assert "upper" in data[metric]
        assert data[metric]["lower"] <= data[metric]["median"] <= data[metric]["upper"]


def test_prediction_prior_vs_fitted(client):
    """Red Cold-start should return prior; mature should return fitted."""
    token = get_auth_token(client)
    cold = client.post(
        "/predictions",
        json={"account_id": "a1", "topic": "t", "lifecycle_phase": "cold_start", "platform": "xhs"},
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    assert cold["interval_mode"] == "prior"

    fitted = client.post(
        "/predictions",
        json={"account_id": "a2", "topic": "t", "lifecycle_phase": "mature", "platform": "xhs", "n_posts_effective": 10},
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    assert fitted["interval_mode"] == "fitted"
    # Prior mode should have wider intervals (lower confidence cap)
    assert cold["confidence"] <= fitted["confidence"]


def test_prediction_requires_auth(client):
    response = client.post("/predictions", json={"account_id": "a", "topic": "t"})
    assert response.status_code == 401


def test_get_prediction_result(client):
    """Red Should retrieve a prediction result by ID."""
    token = get_auth_token(client)
    create_resp = client.post(
        "/predictions",
        json={
            "account_id": "pool_xhs_002",
            "content_type": "note",
            "topic": "狗狗疫苗",
            "lifecycle_phase": "growth",
            "platform": "xhs",
            "word_count": 400,
            "has_image": True,
            "has_video": False,
            "publish_hour": 14,
            "n_posts_effective": 10,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    pred_id = create_resp.json()["prediction_id"]

    response = client.get(f"/predictions/{pred_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["prediction_id"] == pred_id
    assert "features" in data
    assert "likes" in data
    assert data["interval_mode"] == "fitted"


def test_batch_prediction(client):
    """Red Should support batch prediction for multiple items."""
    token = get_auth_token(client)
    response = client.post(
        "/predictions/batch",
        json={
            "items": [
                {"account_id": "a1", "content_type": "note", "topic": "A", "lifecycle_phase": "cold_start", "platform": "xhs"},
                {"account_id": "a2", "content_type": "video", "topic": "B", "lifecycle_phase": "mature", "platform": "douyin", "n_posts_effective": 8},
            ]
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 2
    # First should be prior, second fitted
    assert data["results"][0]["interval_mode"] == "prior"
    assert data["results"][1]["interval_mode"] == "fitted"


def test_prediction_idempotency(client):
    """Red Same Idempotency-Key should return cached result."""
    token = get_auth_token(client)
    key = "idem-pp-001"
    payload = {
        "account_id": "idem_a1",
        "content_type": "note",
        "topic": "Idempotency Test",
        "lifecycle_phase": "cold_start",
        "platform": "xhs",
    }
    r1 = client.post("/predictions", json=payload, headers={"Authorization": f"Bearer {token}", "Idempotency-Key": key})
    assert r1.status_code == 200
    r2 = client.post("/predictions", json=payload, headers={"Authorization": f"Bearer {token}", "Idempotency-Key": key})
    assert r2.status_code == 200
    assert r1.json()["prediction_id"] == r2.json()["prediction_id"]


# ─── Feature Engineering ───


def test_feature_vector_generation():
    """Red: Should generate proper 18-dim feature vector from input."""
    from src.services.prediction_engine import build_feature_vector, build_feature_dict

    arr = build_feature_vector(
        lifecycle_phase="cold_start",
        content_type="note",
        platform="xhs",
        word_count=300,
        has_image=True,
        has_video=False,
        publish_hour=10,
    )
    assert len(arr) == 18
    assert arr.dtype == np.float64
    # Verify dict conversion for API compatibility
    features = build_feature_dict(arr)
    assert "lifecycle_encoded" in features
    assert "platform_encoded" in features
    assert "content_type_encoded" in features
    assert features["has_image"] == 1.0
    assert features["has_video"] == 0.0


def test_cold_start_baseline_prediction():
    """Red: Cold start accounts should get prior mode with lower confidence cap."""
    from src.services.prediction_engine import predict_engagement

    cold_start = predict_engagement(
        lifecycle_phase="cold_start",
        content_type="note",
        platform="xhs",
        word_count=200,
        has_image=False,
        has_video=False,
        publish_hour=3,
    )
    mature = predict_engagement(
        lifecycle_phase="mature",
        content_type="note",
        platform="xhs",
        word_count=500,
        has_image=True,
        has_video=False,
        publish_hour=20,
        n_posts_effective=10,
    )
    assert cold_start["interval_mode"] == "prior"
    assert mature["interval_mode"] == "fitted"
    # Prior caps confidence lower than fitted
    assert cold_start["confidence"] <= mature["confidence"]
    # Intervals should be present
    for metric in ("likes", "comments", "saves"):
        assert metric in cold_start
        assert "lower" in cold_start[metric]
        assert "median" in cold_start[metric]
        assert "upper" in cold_start[metric]


# ─── Model Training ───


def test_model_training_and_metrics():
    """Red: Should train a Bayesian baseline model and report metrics."""
    from src.services.prediction_engine import train_baseline_model, get_model_metrics, clear_model

    clear_model()
    result = train_baseline_model()
    metrics = get_model_metrics()
    assert metrics["model_type"] == "bayesian_linear_regression"
    assert "training_samples" in metrics
    assert "r2_score" in metrics
    assert "mean_absolute_error" in metrics
    assert result["training_samples"] > 0
    assert "coverage_95" in result
    assert "mape" in result


def test_model_predicts_reasonable_range():
    """Red: Predictions should be in a reasonable range."""
    from src.services.prediction_engine import predict_engagement

    result = predict_engagement(
        lifecycle_phase="growth",
        content_type="note",
        platform="xhs",
        word_count=350,
        has_image=True,
        has_video=False,
        publish_hour=12,
        n_posts_effective=10,
    )
    assert result["interval_mode"] == "fitted"
    assert 0 <= result["likes"]["median"] <= 10000
    assert 0 <= result["comments"]["median"] <= 1000
    assert 0 <= result["saves"]["median"] <= 5000
    assert result["feature_version"].startswith("v")
