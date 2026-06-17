"""PoolPredictor Exploration API — W18.

Routes:
  POST /pool-predictor/explore/train        — Train exploration models
  POST /pool-predictor/explore/predict      — Predict with specific model
  GET  /pool-predictor/explore/compare      — Model comparison report
  POST /pool-predictor/explore/ab-assign    — Get A/B model assignment
  POST /pool-predictor/explore/feedback     — Record actual vs predicted feedback
"""

from typing import Any, Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.services import exploration_engine as ee
from src.services.prediction_engine import build_feature_vector

router = APIRouter(prefix="/pool-predictor/explore", tags=["pool-predictor-explore"])


# ─── Schemas ───

class TrainRequest(BaseModel):
    n_samples: int = Field(default=500, ge=50, le=5000)
    seed: int = 42


class PredictRequest(BaseModel):
    model_name: str = Field(default="bayesian", description="bayesian | random_forest | quantile_regressor")
    platform: str = "xhs"
    lifecycle_phase: str = "cold_start"
    content_type: str = "note"
    word_count: int = 300
    has_image: bool = False
    has_video: bool = False
    publish_hour: int = 12
    topic_heat: float = 50.0
    title_has_number: bool = False
    title_has_emoji: bool = False
    title_is_question: bool = False
    title_is_exclamation: bool = False
    paragraph_count: int = 3
    info_density: float = 0.5
    sentiment_score: float = 0.0
    tag_count: int = 3
    tag_heat_mean: float = 50.0
    account_avg_ces: float = 30.0


class ABAssignRequest(BaseModel):
    strategy: str = Field(default="ab_50_50", description="control | explore | ab_50_50 | ab_ucb")
    request_id: str = ""


class FeedbackRequest(BaseModel):
    model_name: str
    predicted_lower: float
    predicted_upper: float
    actual: float


# ─── Routes ───

@router.post("/train")
def train_exploration(req: TrainRequest) -> Dict[str, Any]:
    """Train RF and QR exploration models on synthetic data."""
    X, y = ee.generate_synthetic_data(n_samples=req.n_samples, seed=req.seed)
    result = ee.train_exploration_models(X, y)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/predict")
def predict_with_model(req: PredictRequest) -> Dict[str, Any]:
    """Predict engagement using a specific model."""
    features = build_feature_vector(
        platform=req.platform,
        lifecycle_phase=req.lifecycle_phase,
        content_type=req.content_type,
        word_count=req.word_count,
        has_image=req.has_image,
        has_video=req.has_video,
        publish_hour=req.publish_hour,
        topic_heat=req.topic_heat,
        title_has_number=req.title_has_number,
        title_has_emoji=req.title_has_emoji,
        title_is_question=req.title_is_question,
        title_is_exclamation=req.title_is_exclamation,
        paragraph_count=req.paragraph_count,
        info_density=req.info_density,
        sentiment_score=req.sentiment_score,
        tag_count=req.tag_count,
        tag_heat_mean=req.tag_heat_mean,
        account_avg_ces=req.account_avg_ces,
    )
    pred = ee.predict_with_model(features, model_name=req.model_name)
    return {
        "model_name": req.model_name,
        "prediction": pred,
        "features_used": 18,
    }


@router.get("/compare")
def compare_models() -> Dict[str, Any]:
    """Get model comparison report from A/B quality logs."""
    arena = ee.get_arena()
    return arena.get_comparison_report()


@router.post("/ab-assign")
def ab_assign(req: ABAssignRequest) -> Dict[str, Any]:
    """Get A/B model assignment for a request."""
    arena = ee.get_arena(strategy=req.strategy)
    model = arena.assign_model(request_id=req.request_id)
    return {
        "request_id": req.request_id,
        "strategy": req.strategy,
        "assigned_model": model,
    }


@router.post("/feedback")
def record_feedback(req: FeedbackRequest) -> Dict[str, Any]:
    """Record actual engagement vs predicted interval for quality tracking."""
    arena = ee.get_arena()
    record = arena.record_quality(
        model=req.model_name,
        predicted_interval=[req.predicted_lower, req.predicted_upper],
        actual=req.actual,
    )
    return {
        "model_name": req.model_name,
        "recorded": True,
        "quality": record,
    }
