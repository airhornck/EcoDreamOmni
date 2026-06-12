"""PoolPredictor: engagement interval prediction aligned with detailed design §5.1.

MVP:
- interval_mode = prior | fitted
- likes / comments / saves as {lower, median, upper}
- feature_version tracking
- P95 latency target <500ms (synchronous path)

Phase 2+ (W18): QuantileRegressor / XGBoost + SHAP, gated by N_min.
"""

import time
import numpy as np
from typing import Dict, List, Optional, Tuple


FEATURE_VERSION = "v1.0-mvp-bayesian"
N_MIN_FITTED = 5  # minimum effective posts to switch from prior to fitted


# ─── Feature Engineering (18-dim per spec) ───

def build_feature_vector(
    platform: str = "xhs",
    lifecycle_phase: str = "cold_start",
    content_type: str = "note",
    word_count: int = 300,
    has_image: bool = False,
    has_video: bool = False,
    publish_hour: int = 12,
    topic_heat: float = 50.0,
    # v2 features
    title_has_number: bool = False,
    title_has_emoji: bool = False,
    title_is_question: bool = False,
    title_is_exclamation: bool = False,
    paragraph_count: int = 3,
    info_density: float = 0.5,
    sentiment_score: float = 0.0,
    tag_count: int = 3,
    tag_heat_mean: float = 50.0,
    account_avg_ces: float = 30.0,
    **kwargs,
) -> np.ndarray:
    """Build 18-dimensional feature vector for engagement prediction."""
    platform_map = {"xhs": 0, "xiaohongshu": 0, "douyin": 1, "weixin": 2, "wechat_channels": 2}
    lifecycle_map = {"cold_start": 0, "new": 0, "warm": 1, "growth": 1, "active": 2, "mature": 3, "dormant": 4}
    content_map = {"text": 0, "note": 0, "image": 1, "carousel": 1, "video": 2, "mixed": 3}

    return np.array([
        platform_map.get(platform, 0),
        lifecycle_map.get(lifecycle_phase, 0),
        content_map.get(content_type, 0),
        float(np.log1p(word_count)),
        float(has_image),
        float(has_video),
        float(publish_hour) / 23.0,
        float(topic_heat) / 100.0,
        float(title_has_number),
        float(title_has_emoji),
        float(title_is_question),
        float(title_is_exclamation),
        float(paragraph_count) / 10.0,
        float(info_density),
        float(sentiment_score),
        float(tag_count) / 10.0,
        float(tag_heat_mean) / 100.0,
        float(account_avg_ces) / 100.0,
    ], dtype=np.float64)


def build_feature_dict(features: np.ndarray) -> Dict:
    """Convert feature array back to dict for API compatibility."""
    labels = [
        "platform_encoded", "lifecycle_encoded", "content_type_encoded",
        "word_count_log", "has_image", "has_video", "publish_hour_norm",
        "topic_heat_norm", "title_has_number", "title_has_emoji",
        "title_is_question", "title_is_exclamation", "paragraph_count_norm",
        "info_density", "sentiment_score", "tag_count_norm",
        "tag_heat_mean_norm", "account_avg_ces_norm",
    ]
    return {label: float(features[i]) for i, label in enumerate(labels)}


# ─── Bayesian Linear Regression ───

class BayesianLinearRegression:
    """Conjugate Bayesian linear regression with Normal-Inverse-Gamma prior."""

    def __init__(self, n_features: int = 18, noise_var: float = 100.0):
        self.n_features = n_features
        self.mu0 = np.zeros(n_features)
        self.Sigma0 = np.eye(n_features) * noise_var
        self.a0 = 2.0
        self.b0 = 2.0
        self.mu_n = self.mu0.copy()
        self.Sigma_n = self.Sigma0.copy()
        self.a_n = self.a0
        self.b_n = self.b0
        self.n_obs = 0
        self.is_fitted = False

    def fit(self, X: np.ndarray, y: np.ndarray) -> "BayesianLinearRegression":
        n, d = X.shape
        if d != self.n_features:
            raise ValueError(f"Expected {self.n_features} features, got {d}")
        Sigma0_inv = np.linalg.inv(self.Sigma0)
        XtX = X.T @ X
        self.Sigma_n = np.linalg.inv(Sigma0_inv + XtX)
        self.mu_n = self.Sigma_n @ (Sigma0_inv @ self.mu0 + X.T @ y)
        yTy = y.T @ y
        mu0_S0_mu0 = self.mu0.T @ Sigma0_inv @ self.mu0
        mu_n_Sn_mu_n = self.mu_n.T @ np.linalg.inv(self.Sigma_n) @ self.mu_n
        self.a_n = self.a0 + n / 2.0
        self.b_n = self.b0 + 0.5 * (yTy + mu0_S0_mu0 - mu_n_Sn_mu_n)
        self.n_obs += n
        self.is_fitted = True
        return self

    def predict(self, x: np.ndarray) -> Dict:
        if x.ndim == 1:
            x = x.reshape(1, -1)
        mean = float((x @ self.mu_n).flatten()[0])
        if self.a_n > 1:
            expected_sigma2 = self.b_n / (self.a_n - 1)
        else:
            expected_sigma2 = self.b_n / self.a_n
        var = float((x @ self.Sigma_n @ x.T).flatten()[0]) + expected_sigma2
        std = float(np.sqrt(max(var, 0.01)))
        width = 1.96 * std
        return {
            "mean": round(mean, 2),
            "std": round(std, 2),
            "interval_95": [round(mean - width, 2), round(mean + width, 2)],
            "interval_width": round(width * 2, 2),
        }

    def get_params(self) -> Dict:
        return {
            "mu": self.mu_n.tolist(),
            "Sigma_diag": np.diag(self.Sigma_n).tolist(),
            "a": self.a_n,
            "b": self.b_n,
            "n_obs": self.n_obs,
        }


# ─── Global Model ───
_model: Optional[BayesianLinearRegression] = None


def get_or_create_model() -> BayesianLinearRegression:
    global _model
    if _model is None:
        _model = BayesianLinearRegression(n_features=18)
        train_baseline_model()
    return _model


def train_baseline_model(model_type: str = "") -> Dict:
    """Train baseline Bayesian model on synthetic data."""
    global _model
    np.random.seed(42)
    n_samples = 200
    X = np.random.randn(n_samples, 18)
    true_beta = np.array([
        2.0, 1.5, 1.0, 3.0, 2.0, 1.0, 0.5, 2.5,
        1.5, 1.0, 0.8, 0.8, 0.5, 1.0, 0.5, 0.3, 0.3, 4.0
    ])
    noise = np.random.normal(0, 8, n_samples)
    y = X @ true_beta + 30 + noise
    y = np.clip(y, 5, 150)

    split = int(0.8 * n_samples)
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]

    _model = BayesianLinearRegression(n_features=18)
    _model.fit(X_train, y_train)

    preds = []
    for xi in X_test:
        p = _model.predict(xi)
        preds.append(p["mean"])
    preds = np.array(preds)

    mae = float(np.mean(np.abs(preds - y_test)))
    mape = float(np.mean(np.abs((preds - y_test) / (y_test + 1e-6))))
    within_interval = 0
    for xi, yi in zip(X_test, y_test):
        p = _model.predict(xi)
        lo, hi = p["interval_95"]
        if lo <= yi <= hi:
            within_interval += 1
    coverage = within_interval / len(y_test)

    # Compute pseudo-R2 for compatibility
    ss_res = float(np.sum((y_test - preds) ** 2))
    ss_tot = float(np.sum((y_test - np.mean(y_test)) ** 2))
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0

    return {
        "model_type": "bayesian_linear_regression",
        "training_samples": split,
        "r2_score": round(r2, 4),
        "mean_absolute_error": round(mae, 2),
        "mape": round(mape, 4),
        "coverage_95": round(coverage, 2),
        "model_params": _model.get_params(),
    }


def get_model_metrics() -> Dict:
    """Return current model metrics."""
    global _model
    if _model is None or not _model.is_fitted:
        metrics = train_baseline_model()
    else:
        metrics = {
            "model_type": "bayesian_linear_regression",
            "training_samples": _model.n_obs,
            "r2_score": 0.0,
            "mean_absolute_error": 0.0,
            "is_trained": _model.is_fitted,
        }
    metrics.setdefault("is_trained", True)
    return metrics


def _compute_interval_mode(lifecycle_phase: str, n_posts_effective: int = 0) -> str:
    """Determine interval mode per detailed design §5.1.

    - prior: N_posts_effective < N_min or config forces prior
    - fitted: sufficient data available
    """
    if lifecycle_phase in ("cold_start", "new"):
        return "prior"
    if n_posts_effective < N_MIN_FITTED:
        return "prior"
    return "fitted"


def _metric_interval(mean: float, std: float, prior_mode: bool = False) -> Dict:
    """Build {lower, median, upper} interval for a single metric.

    In prior mode the interval is widened to reflect higher uncertainty.
    """
    multiplier = 2.5 if prior_mode else 1.96
    lower = max(0.0, round(mean - multiplier * std, 2))
    median = round(mean, 2)
    upper = round(mean + multiplier * std, 2)
    return {"lower": lower, "median": median, "upper": upper}


def predict_engagement(
    platform: str = "xhs",
    lifecycle_phase: str = "cold_start",
    content_type: str = "note",
    word_count: int = 300,
    has_image: bool = False,
    has_video: bool = False,
    publish_hour: int = 12,
    topic_heat: float = 50.0,
    title_has_number: bool = False,
    title_has_emoji: bool = False,
    title_is_question: bool = False,
    title_is_exclamation: bool = False,
    paragraph_count: int = 3,
    info_density: float = 0.5,
    sentiment_score: float = 0.0,
    tag_count: int = 3,
    tag_heat_mean: float = 50.0,
    account_avg_ces: float = 30.0,
    n_posts_effective: int = 0,
    **kwargs,
) -> Dict:
    """Predict engagement with interval structure aligned to detailed design §5.1.

    Returns likes/comments/saves as {lower, median, upper} with interval_mode.
    """
    start_ts = time.perf_counter()

    features = build_feature_vector(
        platform=platform, lifecycle_phase=lifecycle_phase, content_type=content_type,
        word_count=word_count, has_image=has_image, has_video=has_video,
        publish_hour=publish_hour, topic_heat=topic_heat,
        title_has_number=title_has_number, title_has_emoji=title_has_emoji,
        title_is_question=title_is_question, title_is_exclamation=title_is_exclamation,
        paragraph_count=paragraph_count, info_density=info_density,
        sentiment_score=sentiment_score, tag_count=tag_count,
        tag_heat_mean=tag_heat_mean, account_avg_ces=account_avg_ces,
    )

    model = get_or_create_model()
    pred = model.predict(features)

    mean = pred["mean"]
    std = pred["std"]

    interval_mode = _compute_interval_mode(lifecycle_phase, n_posts_effective)
    prior_mode = interval_mode == "prior"

    # Derive sub-metric distributions from the composite CES prediction.
    # Likes dominate engagement; comments and saves are smaller fractions.
    likes_mean = max(0.0, mean * 0.6)
    likes_std = std * 0.35
    comments_mean = max(0.0, mean * 0.15)
    comments_std = std * 0.15
    saves_mean = max(0.0, mean * 0.1)
    saves_std = std * 0.10

    likes = _metric_interval(likes_mean, likes_std, prior_mode)
    comments = _metric_interval(comments_mean, comments_std, prior_mode)
    saves = _metric_interval(saves_mean, saves_std, prior_mode)

    # Heuristic confidence: higher std -> lower confidence; prior_mode caps confidence.
    raw_confidence = max(0.0, 1.0 - std / 50.0)
    confidence = round(min(raw_confidence, 0.65 if prior_mode else 0.95), 4)

    latency_ms = round((time.perf_counter() - start_ts) * 1000, 2)

    return {
        "likes": likes,
        "comments": comments,
        "saves": saves,
        "interval_mode": interval_mode,
        "confidence": confidence,
        "feature_version": FEATURE_VERSION,
        "features": build_feature_dict(features),
        "latency_ms": latency_ms,
    }


# ─── Thompson Sampling (retained for Phase 2+) ───

def thompson_sample(strategies: List[Dict], prior_discount: float = 0.3) -> Dict:
    """Select best strategy using Thompson Sampling."""
    if not strategies:
        raise ValueError("No strategies provided")
    samples = []
    for s in strategies:
        mean = s.get("mean_reward", 0)
        std = s.get("std_reward", 10)
        sample = np.random.normal(mean, std)
        if s.get("is_risky", False):
            sample *= prior_discount
        samples.append(sample)
    best_idx = int(np.argmax(samples))
    return {
        "selected_strategy": strategies[best_idx],
        "selected_index": best_idx,
        "sampled_values": [round(v, 2) for v in samples],
    }


# ─── Cold-start Prior (retained for backward compatibility) ───

def initialize_prior_from_cluster(cluster_avg_ces: float) -> Dict:
    """Initialize prior for cold-start account from cluster aggregate."""
    alpha_0 = 1.0 + cluster_avg_ces / 50.0
    beta_0 = 1.0 + max(0, 4 - cluster_avg_ces / 50.0)
    return {
        "alpha": round(alpha_0, 2),
        "beta": round(beta_0, 2),
        "cluster_avg_ces": cluster_avg_ces,
        "message": "Cold-start prior initialized from cluster aggregate",
    }


def clear_model() -> None:
    global _model
    _model = None
