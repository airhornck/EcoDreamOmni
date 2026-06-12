# Python stub for PoolPredictor types aligned with detailed design §5.1
# Used for frontend/backend type contract verification.

from typing import TypedDict, Literal, Optional

class MetricInterval(TypedDict):
    lower: float
    median: float
    upper: float

class PredictionResponse(TypedDict):
    prediction_id: str
    account_id: str
    topic: str
    likes: MetricInterval
    comments: MetricInterval
    saves: MetricInterval
    interval_mode: Literal["prior", "fitted"]
    confidence: float
    feature_version: str
    features: dict[str, float]
    latency_ms: Optional[float]

class PredictionRequest(TypedDict, total=False):
    account_id: str
    content_type: Literal["note", "video", "carousel"]
    topic: str
    lifecycle_phase: Literal["cold_start", "growth", "mature", "dormant"]
    platform: Literal["xhs", "douyin", "wechat_channels"]
    word_count: int
    has_image: bool
    has_video: bool
    publish_hour: int
    n_posts_effective: int
