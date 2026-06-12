"""Tests for ContentInsight (W19).

Red-Green TDD for:
  - Tag extraction
  - Tag performance aggregation
  - Time performance aggregation
  - Tier performance aggregation
  - Strategy recommendation generation
  - Full analysis pipeline
"""

import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.services import content_insight as ci


# ─── Tag extraction ───

def test_extract_tags_basic():
    profile = ci.extract_content_tags(
        content_id="c1",
        title="How to feed your dog 5 tips",
        body="Some content",
        topic="dog nutrition",
        content_type="note",
        word_count=300,
        publish_hour=10,
        has_image=True,
    )
    assert "dog_nutrition" in profile.tags
    assert "note" in profile.tags
    assert "format_image" in profile.tags
    assert "length_medium" in profile.tags
    assert "time_morning" in profile.tags
    assert "title_has_number" in profile.tags
    assert profile.title_features["has_number"] is True
    assert profile.title_features["is_question"] is True  # "how to"


def test_extract_tags_evening():
    profile = ci.extract_content_tags(
        content_id="c2",
        title="Amazing!",
        body="",
        topic="cat health",
        content_type="video",
        word_count=600,
        publish_hour=20,
        has_video=True,
    )
    assert "time_evening" in profile.tags
    assert "format_video" in profile.tags
    assert "length_long" in profile.tags
    assert "title_exclamation" in profile.tags
    assert profile.title_features["is_exclamation"] is True


# ─── Tag performance ───

def test_aggregate_tag_performance():
    profiles = [
        ci.ContentTagProfile("c1", ["dog", "morning"], {}, "note", "medium", "morning"),
        ci.ContentTagProfile("c2", ["dog", "evening"], {}, "note", "medium", "evening"),
        ci.ContentTagProfile("c3", ["cat", "morning"], {}, "note", "medium", "morning"),
    ]
    engagement = {
        "c1": {"likes": 100, "comments": 20, "saves": 10, "ces": 50},
        "c2": {"likes": 80, "comments": 15, "saves": 8, "ces": 40},
        "c3": {"likes": 60, "comments": 10, "saves": 5, "ces": 30},
    }
    perf = ci.aggregate_tag_performance(profiles, engagement, min_contents=2)
    assert len(perf) >= 1
    dog_perf = next((p for p in perf if p.tag == "dog"), None)
    assert dog_perf is not None
    assert dog_perf.content_count == 2
    assert dog_perf.avg_ces == 45.0  # (50 + 40) / 2


def test_aggregate_tag_performance_min_filter():
    profiles = [
        ci.ContentTagProfile("c1", ["rare_tag"], {}, "note", "short", "morning"),
    ]
    engagement = {"c1": {"likes": 10, "comments": 1, "saves": 0, "ces": 5}}
    perf = ci.aggregate_tag_performance(profiles, engagement, min_contents=2)
    assert len(perf) == 0  # Filtered out


# ─── Time performance ───

def test_aggregate_time_performance():
    profiles = [
        ci.ContentTagProfile("c1", ["morning"], {}, "note", "medium", "morning"),
        ci.ContentTagProfile("c2", ["morning"], {}, "note", "medium", "morning"),
        ci.ContentTagProfile("c3", ["evening"], {}, "note", "medium", "evening"),
    ]
    engagement = {
        "c1": {"likes": 100, "ces": 50},
        "c2": {"likes": 80, "ces": 40},
        "c3": {"likes": 60, "ces": 30},
    }
    perf = ci.aggregate_time_performance(profiles, engagement)
    assert len(perf) == 2
    assert perf[0].hour_bucket == "morning"  # Higher avg CES
    assert perf[0].avg_ces == 45.0


# ─── Strategy recommendations ───

def test_generate_recommendations_tag():
    tag_perf = [
        ci.TagPerformance("dog_nutrition", 5, 100, 20, 10, 50.0, ["c1"]),
        ci.TagPerformance("cat_health", 3, 30, 5, 2, 15.0, ["c2"]),
    ]
    time_perf = []
    tier_perf = []
    recs = ci.generate_recommendations(tag_perf, time_perf, tier_perf)
    assert any(r.category == "tag" and "dog_nutrition" in r.insight for r in recs)
    assert any(r.category == "tag" and "underperform" in r.insight for r in recs)


def test_generate_recommendations_timing():
    tag_perf = []
    time_perf = [
        ci.TimePerformance("evening", 10, 60.0, 120.0),
        ci.TimePerformance("morning", 10, 20.0, 40.0),
    ]
    tier_perf = []
    recs = ci.generate_recommendations(tag_perf, time_perf, tier_perf)
    assert any(r.category == "timing" for r in recs)
    assert "evening" in recs[0].insight


def test_generate_recommendations_format():
    tag_perf = [
        ci.TagPerformance("format_video", 5, 100, 20, 10, 55.0, ["c1"]),
        ci.TagPerformance("format_image", 5, 50, 10, 5, 25.0, ["c2"]),
    ]
    recs = ci.generate_recommendations(tag_perf, [], [])
    assert any(r.category == "content_format" for r in recs)


# ─── Full pipeline ───

def test_analyze_content_performance_full():
    contents = [
        {"id": "c1", "title": "Dog nutrition tips", "topic": "dog nutrition", "content_type": "note", "word_count": 300, "publish_hour": 10, "has_image": True},
        {"id": "c2", "title": "Cat health guide", "topic": "cat health", "content_type": "note", "word_count": 400, "publish_hour": 20, "has_image": True},
        {"id": "c3", "title": "Dog food review", "topic": "dog nutrition", "content_type": "note", "word_count": 250, "publish_hour": 10, "has_image": False},
    ]
    accounts = [
        {"id": "a1", "lifecycle_phase": "growth", "posts_week": 5},
        {"id": "a2", "lifecycle_phase": "cold_start", "posts_week": 2},
    ]
    engagement = {
        "c1": {"likes": 100, "comments": 20, "saves": 10, "ces": 50},
        "c2": {"likes": 60, "comments": 10, "saves": 5, "ces": 30},
        "c3": {"likes": 80, "comments": 15, "saves": 8, "ces": 40},
    }

    result = ci.analyze_content_performance(contents, accounts, engagement)
    assert result["total_contents_analyzed"] == 3
    assert result["total_accounts_analyzed"] == 2
    assert len(result["tag_performance"]) > 0
    assert len(result["time_performance"]) > 0
    assert len(result["recommendations"]) > 0

    # Verify dog_nutrition is among top tags
    dog_tag = next((t for t in result["tag_performance"] if t["tag"] == "dog_nutrition"), None)
    assert dog_tag is not None
    assert dog_tag["avg_ces"] == 45.0  # (50 + 40) / 2


def test_analyze_empty():
    result = ci.analyze_content_performance([], [], {})
    assert result["total_contents_analyzed"] == 0
    assert result["tag_performance"] == []
    assert result["recommendations"] == []
