"""PoolPredictor service: prediction requests, batch processing, model management.

Aligned with detailed design §5.1:
- interval_mode prior|fitted
- likes/comments/saves as {lower, median, upper}
- feature_version tracking
"""

from typing import Dict, List, Optional

from src.services.prediction_engine import predict_engagement, train_baseline_model, get_model_metrics

# In-memory prediction log (MVP)
_prediction_db: Dict[str, Dict] = {}


def create_prediction(
    account_id: str,
    content_type: str,
    topic: str,
    lifecycle_phase: str,
    platform: str,
    word_count: int = 300,
    has_image: bool = False,
    has_video: bool = False,
    publish_hour: int = 12,
    n_posts_effective: int = 0,
) -> Dict:
    """Create a prediction request and store the result."""
    result = predict_engagement(
        lifecycle_phase=lifecycle_phase,
        content_type=content_type,
        platform=platform,
        word_count=word_count,
        has_image=has_image,
        has_video=has_video,
        publish_hour=publish_hour,
        topic=topic,
        n_posts_effective=n_posts_effective,
    )

    pred_id = f"pred_{len(_prediction_db) + 1:04d}"
    record = {
        "prediction_id": pred_id,
        "account_id": account_id,
        "topic": topic,
        **result,
    }
    _prediction_db[pred_id] = record
    return record


def get_prediction(prediction_id: str) -> Optional[Dict]:
    return _prediction_db.get(prediction_id)


def batch_predict(items: List[Dict]) -> List[Dict]:
    """Process multiple prediction requests."""
    results = []
    for item in items:
        result = create_prediction(
            account_id=item.get("account_id", ""),
            content_type=item.get("content_type", "note"),
            topic=item.get("topic", ""),
            lifecycle_phase=item.get("lifecycle_phase", "cold_start"),
            platform=item.get("platform", "xhs"),
            word_count=item.get("word_count", 300),
            has_image=item.get("has_image", False),
            has_video=item.get("has_video", False),
            publish_hour=item.get("publish_hour", 12),
            n_posts_effective=item.get("n_posts_effective", 0),
        )
        results.append(result)
    return results


def train_model(model_type: str = "") -> Dict:
    return train_baseline_model()


def model_metrics() -> Dict:
    return get_model_metrics()


def clear_predictions() -> None:
    _prediction_db.clear()
