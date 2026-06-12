"""ContentInsight API — W19.

Routes:
  POST /content-insight/analyze       — Full content performance analysis
  POST /content-insight/tags/extract  — Extract tags from a single content
  POST /content-insight/tags/compare  — Compare tag performance
  GET  /content-insight/time-slots    — Time slot performance ranking
  GET  /content-insight/recommendations — Active strategy recommendations
"""

from typing import Any, Dict, List
from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.services import content_insight as ci

router = APIRouter(prefix="/content-insight", tags=["content-insight"])


# ─── Schemas ───

class ContentItem(BaseModel):
    id: str
    title: str = ""
    body: str = ""
    topic: str = ""
    content_type: str = "note"
    word_count: int = 300
    publish_hour: int = 12
    has_image: bool = False
    has_video: bool = False


class AccountItem(BaseModel):
    id: str
    lifecycle_phase: str = "cold_start"
    posts_week: int = 0


class EngagementItem(BaseModel):
    likes: float = 0
    comments: float = 0
    saves: float = 0
    ces: float = 0


class AnalyzeRequest(BaseModel):
    contents: List[ContentItem]
    accounts: List[AccountItem] = []
    engagement_data: Dict[str, EngagementItem] = {}  # content_id -> engagement
    engagement_by_account: Dict[str, List[EngagementItem]] = {}  # account_id -> list


class TagExtractRequest(BaseModel):
    content_id: str
    title: str
    body: str = ""
    topic: str = ""
    content_type: str = "note"
    word_count: int = 300
    publish_hour: int = 12
    has_image: bool = False
    has_video: bool = False


class TagCompareRequest(BaseModel):
    tag_profiles: List[Dict[str, Any]]
    engagement_data: Dict[str, EngagementItem]
    min_contents: int = 2


# ─── Routes ───

@router.post("/analyze")
def analyze_content(req: AnalyzeRequest) -> Dict[str, Any]:
    """Run full ContentInsight analysis pipeline."""
    contents = [c.model_dump() for c in req.contents]
    accounts = [a.model_dump() for a in req.accounts]
    engagement = {k: v.model_dump() for k, v in req.engagement_data.items()}
    eng_by_acc = {k: [item.model_dump() for item in v] for k, v in req.engagement_by_account.items()}

    result = ci.analyze_content_performance(contents, accounts, engagement, eng_by_acc)
    return result


@router.post("/tags/extract")
def extract_tags(req: TagExtractRequest) -> Dict[str, Any]:
    """Extract structured tags from a single content item."""
    profile = ci.extract_content_tags(
        content_id=req.content_id,
        title=req.title,
        body=req.body,
        topic=req.topic,
        content_type=req.content_type,
        word_count=req.word_count,
        publish_hour=req.publish_hour,
        has_image=req.has_image,
        has_video=req.has_video,
    )
    return {
        "content_id": profile.content_id,
        "tags": profile.tags,
        "title_features": profile.title_features,
        "content_type": profile.content_type,
        "word_count_bucket": profile.word_count_bucket,
        "publish_hour_bucket": profile.publish_hour_bucket,
    }


@router.post("/tags/compare")
def compare_tags(req: TagCompareRequest) -> Dict[str, Any]:
    """Compare performance across tags."""
    profiles = [
        ci.ContentTagProfile(
            content_id=p["content_id"],
            tags=p.get("tags", []),
            title_features=p.get("title_features", {}),
            content_type=p.get("content_type", "note"),
            word_count_bucket=p.get("word_count_bucket", "medium"),
            publish_hour_bucket=p.get("publish_hour_bucket", "afternoon"),
        )
        for p in req.tag_profiles
    ]
    engagement = {k: v.model_dump() for k, v in req.engagement_data.items()}
    perf = ci.aggregate_tag_performance(profiles, engagement, min_contents=req.min_contents)
    return {
        "tag_performance": [
            {
                "tag": t.tag,
                "content_count": t.content_count,
                "avg_likes": t.avg_likes,
                "avg_comments": t.avg_comments,
                "avg_saves": t.avg_saves,
                "avg_ces": t.avg_ces,
                "top_content_ids": t.top_content_ids,
            }
            for t in perf
        ],
    }


@router.get("/recommendations")
def get_recommendations() -> Dict[str, Any]:
    """Return currently active strategy recommendations (requires prior analysis data)."""
    # MVP: return placeholder; real implementation would cache from last analyze call
    return {
        "recommendations": [],
        "note": "Run POST /content-insight/analyze to generate recommendations",
    }
