"""PoolPredictor Exploration Engine — W18.

Exploration-phase models for engagement prediction:
  - RandomForestRegressor (bootstrap quantiles for intervals)
  - QuantileRegressor (sklearn, for direct interval estimation)
  - ModelArena: A/B assignment framework + interval quality evaluation

Constraints:
  - N_min = 5 for fitted mode (retained from baseline)
  - Small-sample gate: skip deep nets, use tree/linear only
  - Phase 2+ can add XGBoost when data volume permits
"""

import numpy as np
from typing import Dict, List, Optional

from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import QuantileRegressor
from sklearn.model_selection import train_test_split


N_MIN_FITTED = 5


# ─── Random Forest with Bootstrap Intervals ───

class RFIntervalPredictor:
    """RandomForest with bootstrap quantile intervals.

    Trains a forest; interval derived from tree-output distribution.
    More robust than single Bayesian LR for non-linear feature interactions.
    """

    def __init__(self, n_estimators: int = 100, max_depth: int = 8, random_state: int = 42):
        self.model = RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=random_state,
            n_jobs=-1,
        )
        self.is_fitted = False
        self.n_features = 18
        self.train_mae = 0.0
        self.train_mape = 0.0

    def fit(self, X: np.ndarray, y: np.ndarray) -> "RFIntervalPredictor":
        n, d = X.shape
        if d != self.n_features:
            raise ValueError(f"Expected {self.n_features} features, got {d}")
        if n < N_MIN_FITTED:
            raise ValueError(f"Need at least {N_MIN_FITTED} samples, got {n}")
        self.model.fit(X, y)
        self.is_fitted = True
        preds = self.model.predict(X)
        self.train_mae = float(np.mean(np.abs(preds - y)))
        self.train_mape = float(np.mean(np.abs((preds - y) / (y + 1e-6))))
        return self

    def predict(self, x: np.ndarray, quantiles: List[float] = None) -> Dict:
        if not self.is_fitted:
            raise RuntimeError("Model not fitted")
        if x.ndim == 1:
            x = x.reshape(1, -1)

        # Collect predictions from all trees
        tree_preds = np.array([tree.predict(x) for tree in self.model.estimators_])
        # tree_preds shape: (n_estimators, n_samples)
        mean = float(np.mean(tree_preds))
        std = float(np.std(tree_preds))

        if quantiles is None:
            quantiles = [0.025, 0.5, 0.975]
        qs = [float(np.quantile(tree_preds, q)) for q in quantiles]

        return {
            "mean": round(mean, 2),
            "std": round(std, 2),
            "interval_95": [round(qs[0], 2), round(qs[-1], 2)],
            "median": round(qs[1], 2),
            "interval_width": round(qs[-1] - qs[0], 2),
            "model_type": "random_forest",
        }


# ─── Quantile Regressor (sklearn) ───

class QuantileIntervalPredictor:
    """QuantileRegressor for direct lower/median/upper estimation.

    Fits three models: alpha=0.025, 0.5, 0.975.
    """

    def __init__(self, alpha: float = 1.0, solver_options: Optional[Dict] = None):
        self.models: Dict[str, QuantileRegressor] = {}
        self.alphas = {"lower": 0.025, "median": 0.5, "upper": 0.975}
        self.regularization = alpha
        self.solver_options = solver_options or {}
        self.is_fitted = False
        self.n_features = 18

    def fit(self, X: np.ndarray, y: np.ndarray) -> "QuantileIntervalPredictor":
        n, d = X.shape
        if d != self.n_features:
            raise ValueError(f"Expected {self.n_features} features, got {d}")
        if n < N_MIN_FITTED:
            raise ValueError(f"Need at least {N_MIN_FITTED} samples, got {n}")
        for name, quantile in self.alphas.items():
            self.models[name] = QuantileRegressor(
                quantile=quantile,
                alpha=self.regularization,
                solver="highs",
                solver_options=self.solver_options,
            )
            self.models[name].fit(X, y)
        self.is_fitted = True
        return self

    def predict(self, x: np.ndarray) -> Dict:
        if not self.is_fitted:
            raise RuntimeError("Model not fitted")
        if x.ndim == 1:
            x = x.reshape(1, -1)

        preds = {name: float(model.predict(x)[0]) for name, model in self.models.items()}
        width = preds["upper"] - preds["lower"]
        mean_approx = (preds["lower"] + preds["upper"]) / 2.0

        return {
            "mean": round(mean_approx, 2),
            "std": round(width / 3.92, 2),  # approximate std from 95% width
            "interval_95": [round(preds["lower"], 2), round(preds["upper"], 2)],
            "median": round(preds["median"], 2),
            "interval_width": round(width, 2),
            "model_type": "quantile_regressor",
        }


# ─── Model Arena (A/B framework) ───

class ModelArena:
    """A/B assignment + interval quality tracking for exploration models.

    Assignment strategies:
      - "control": always use baseline (Bayesian LR)
      - "explore": always use exploration model
      - "ab_50_50": 50/50 random assignment
      - "ab_ucb": UCB-based assignment (favor better model)
    """

    def __init__(self, strategy: str = "ab_50_50", random_state: int = 42):
        self.strategy = strategy
        self.rng = np.random.RandomState(random_state)
        self.assignments: List[Dict] = []
        self.quality_log: Dict[str, List[Dict]] = {
            "bayesian": [],
            "random_forest": [],
            "quantile_regressor": [],
        }

    def assign_model(self, request_id: str = "") -> str:
        """Return model name for this request."""
        if self.strategy == "control":
            model = "bayesian"
        elif self.strategy == "explore":
            model = self.rng.choice(["random_forest", "quantile_regressor"])
        elif self.strategy == "ab_50_50":
            model = self.rng.choice(["bayesian", "random_forest"])
        elif self.strategy == "ab_ucb":
            model = self._ucb_select()
        else:
            model = "bayesian"
        self.assignments.append({"request_id": request_id, "model": model})
        return model

    def _ucb_select(self) -> str:
        """UCB1-style selection favoring better-calibrated intervals."""
        best_model = "bayesian"
        best_score = -float("inf")
        total_n = sum(len(self.quality_log[m]) for m in self.quality_log)
        for model, logs in self.quality_log.items():
            n = max(1, len(logs))
            avg_quality = np.mean([log["quality_score"] for log in logs]) if logs else 0.5
            # UCB bonus
            bonus = np.sqrt(2 * np.log(max(1, total_n)) / n)
            score = avg_quality + bonus
            if score > best_score:
                best_score = score
                best_model = model
        return best_model

    def record_quality(self, model: str, predicted_interval: List[float], actual: float) -> Dict:
        """Record interval prediction quality for a model.

        Quality = coverage - 0.5 * normalized_width
        Higher is better (max ~1.0).
        """
        lo, hi = predicted_interval
        covered = lo <= actual <= hi
        width = hi - lo
        # Normalize width by typical engagement scale (~100)
        norm_width = width / 100.0
        quality = (1.0 if covered else 0.0) - 0.5 * norm_width
        record = {
            "covered": covered,
            "width": width,
            "actual": actual,
            "quality_score": round(quality, 4),
        }
        self.quality_log[model].append(record)
        return record

    def get_comparison_report(self) -> Dict:
        """Compare all models on coverage and interval width."""
        report = {}
        for model, logs in self.quality_log.items():
            if not logs:
                continue
            report[model] = {
                "n_predictions": len(logs),
                "coverage_rate": round(sum(1 for log in logs if log["covered"]) / len(logs), 4),
                "mean_width": round(np.mean([log["width"] for log in logs]), 2),
                "mean_quality": round(np.mean([log["quality_score"] for log in logs]), 4),
            }
        return report


# ─── Global exploration state ───

_rf_model: Optional[RFIntervalPredictor] = None
_qr_model: Optional[QuantileIntervalPredictor] = None
_arena: Optional[ModelArena] = None


def get_arena(strategy: str = "ab_50_50") -> ModelArena:
    global _arena
    if _arena is None:
        _arena = ModelArena(strategy=strategy)
    return _arena


def train_exploration_models(X: np.ndarray, y: np.ndarray) -> Dict:
    """Train RF and QR models on provided data.

    Returns training metrics for both.
    """
    global _rf_model, _qr_model
    n = len(X)
    if n < N_MIN_FITTED:
        return {
            "success": False,
            "error": f"Insufficient data: {n} < {N_MIN_FITTED}",
        }

    # Train/val split
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

    # Random Forest
    _rf_model = RFIntervalPredictor()
    _rf_model.fit(X_train, y_train)
    rf_val_preds = []
    for xi in X_val:
        p = _rf_model.predict(xi)
        rf_val_preds.append(p["mean"])
    rf_val_preds = np.array(rf_val_preds)
    rf_mae = float(np.mean(np.abs(rf_val_preds - y_val)))
    rf_mape = float(np.mean(np.abs((rf_val_preds - y_val) / (y_val + 1e-6))))

    # Quantile Regressor
    _qr_model = QuantileIntervalPredictor()
    _qr_model.fit(X_train, y_train)
    qr_val_preds = []
    for xi in X_val:
        p = _qr_model.predict(xi)
        qr_val_preds.append(p["mean"])
    qr_val_preds = np.array(qr_val_preds)
    qr_mae = float(np.mean(np.abs(qr_val_preds - y_val)))
    qr_mape = float(np.mean(np.abs((qr_val_preds - y_val) / (y_val + 1e-6))))

    return {
        "success": True,
        "random_forest": {
            "val_mae": round(rf_mae, 2),
            "val_mape": round(rf_mape, 4),
            "train_mae": round(_rf_model.train_mae, 2),
            "train_mape": round(_rf_model.train_mape, 4),
        },
        "quantile_regressor": {
            "val_mae": round(qr_mae, 2),
            "val_mape": round(qr_mape, 4),
        },
        "validation_samples": len(X_val),
    }


def predict_with_model(
    features: np.ndarray,
    model_name: str = "bayesian",
) -> Dict:
    """Predict using a specific model.

    Falls back to bayesian if exploration model not trained.
    """
    if model_name == "random_forest" and _rf_model is not None and _rf_model.is_fitted:
        return _rf_model.predict(features)
    if model_name == "quantile_regressor" and _qr_model is not None and _qr_model.is_fitted:
        return _qr_model.predict(features)
    # Fallback to bayesian via prediction_engine
    from src.services.prediction_engine import get_or_create_model
    bayes = get_or_create_model()
    return bayes.predict(features)


def generate_synthetic_data(n_samples: int = 500, seed: int = 42) -> tuple:
    """Generate synthetic training data for exploration."""
    rng = np.random.RandomState(seed)
    X = rng.randn(n_samples, 18)
    true_beta = np.array([
        2.0, 1.5, 1.0, 3.0, 2.0, 1.0, 0.5, 2.5,
        1.5, 1.0, 0.8, 0.8, 0.5, 1.0, 0.5, 0.3, 0.3, 4.0
    ])
    # Add non-linear interaction for RF to exploit
    interaction = 0.5 * X[:, 0] * X[:, 3] + 0.3 * X[:, 1] * X[:, 7]
    noise = rng.normal(0, 8, n_samples)
    y = X @ true_beta + interaction + 30 + noise
    y = np.clip(y, 5, 150)
    return X, y
