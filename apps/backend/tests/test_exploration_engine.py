"""Tests for PoolPredictor Exploration Engine (W18).

Red-Green TDD for:
  - RFIntervalPredictor fit + predict
  - QuantileIntervalPredictor fit + predict
  - ModelArena A/B assignment + quality tracking
  - train_exploration_models + comparison report
"""

import pytest
import numpy as np
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.services import exploration_engine as ee
from src.services.prediction_engine import build_feature_vector


@pytest.fixture(autouse=True)
def reset_models():
    """Reset global exploration state before each test."""
    ee._rf_model = None
    ee._qr_model = None
    ee._arena = None
    yield


# ─── Synthetic data ───

def test_generate_synthetic_data():
    X, y = ee.generate_synthetic_data(n_samples=100, seed=1)
    assert X.shape == (100, 18)
    assert len(y) == 100
    assert np.all(y >= 5) and np.all(y <= 150)


# ─── RF Interval Predictor ───

def test_rf_fit_predict():
    X, y = ee.generate_synthetic_data(n_samples=100, seed=2)
    rf = ee.RFIntervalPredictor(n_estimators=50, max_depth=6)
    rf.fit(X, y)
    assert rf.is_fitted is True

    pred = rf.predict(X[0])
    assert "mean" in pred
    assert "interval_95" in pred
    lo, hi = pred["interval_95"]
    assert lo <= pred["mean"] <= hi
    assert pred["model_type"] == "random_forest"


def test_rf_insufficient_data():
    rf = ee.RFIntervalPredictor()
    X = np.random.randn(3, 18)
    y = np.random.randn(3)
    with pytest.raises(ValueError, match="Need at least"):
        rf.fit(X, y)


# ─── Quantile Regressor ───

def test_qr_fit_predict():
    X, y = ee.generate_synthetic_data(n_samples=100, seed=3)
    qr = ee.QuantileIntervalPredictor(alpha=0.5)
    qr.fit(X, y)
    assert qr.is_fitted is True

    pred = qr.predict(X[0])
    assert "mean" in pred
    assert "interval_95" in pred
    lo, hi = pred["interval_95"]
    assert lo <= pred["median"] <= hi
    assert pred["model_type"] == "quantile_regressor"


def test_qr_insufficient_data():
    qr = ee.QuantileIntervalPredictor()
    X = np.random.randn(3, 18)
    y = np.random.randn(3)
    with pytest.raises(ValueError, match="Need at least"):
        qr.fit(X, y)


# ─── Model Arena ───

def test_arena_assign_control():
    arena = ee.ModelArena(strategy="control")
    model = arena.assign_model("req-1")
    assert model == "bayesian"


def test_arena_assign_explore():
    arena = ee.ModelArena(strategy="explore")
    model = arena.assign_model("req-1")
    assert model in ("random_forest", "quantile_regressor")


def test_arena_assign_ab_50_50():
    arena = ee.ModelArena(strategy="ab_50_50")
    models = [arena.assign_model(f"req-{i}") for i in range(100)]
    # Should get both bayesian and random_forest
    assert "bayesian" in models or "random_forest" in models


def test_arena_record_quality():
    arena = ee.ModelArena()
    record = arena.record_quality("bayesian", [10.0, 50.0], 30.0)
    assert record["covered"] is True
    assert record["quality_score"] > 0

    record2 = arena.record_quality("bayesian", [10.0, 20.0], 30.0)
    assert record2["covered"] is False


def test_arena_comparison_report():
    arena = ee.ModelArena()
    arena.record_quality("bayesian", [10.0, 50.0], 30.0)
    arena.record_quality("bayesian", [15.0, 45.0], 25.0)
    arena.record_quality("random_forest", [5.0, 60.0], 30.0)
    report = arena.get_comparison_report()
    assert "bayesian" in report
    assert report["bayesian"]["n_predictions"] == 2


def test_arena_ucb_select():
    arena = ee.ModelArena(strategy="ab_ucb")
    # Seed with some quality data
    for _ in range(5):
        arena.record_quality("bayesian", [10, 50], 30)
    for _ in range(3):
        arena.record_quality("random_forest", [10, 50], 30)
    model = arena.assign_model("req-x")
    assert model in ("bayesian", "random_forest", "quantile_regressor")


# ─── Integration: train + predict ───

def test_train_exploration_models():
    X, y = ee.generate_synthetic_data(n_samples=200, seed=4)
    result = ee.train_exploration_models(X, y)
    assert result["success"] is True
    assert "random_forest" in result
    assert "quantile_regressor" in result
    assert ee._rf_model is not None
    assert ee._qr_model is not None


def test_train_insufficient_data():
    X, y = ee.generate_synthetic_data(n_samples=3, seed=5)
    result = ee.train_exploration_models(X, y)
    assert result["success"] is False
    assert "Insufficient" in result["error"]


def test_predict_with_model_fallback():
    """If exploration model not trained, fallback to bayesian."""
    X, y = ee.generate_synthetic_data(n_samples=200, seed=6)
    ee.train_exploration_models(X, y)
    features = build_feature_vector()

    pred_rf = ee.predict_with_model(features, "random_forest")
    assert "mean" in pred_rf

    pred_qr = ee.predict_with_model(features, "quantile_regressor")
    assert "mean" in pred_qr

    pred_fallback = ee.predict_with_model(features, "random_forest")
    assert "mean" in pred_fallback
