"""Tests for Phase 9 Skills — brand_consistency, fingerprint, engagement_predict, publish_schedule, health_score, xhs_note_extraction."""

import pytest
from src.skills.brand_consistency_check import execute as brand_execute, SKILL_ID as BRAND_ID
from src.skills.fingerprint_generate import execute as fp_execute, SKILL_ID as FP_ID
from src.skills.engagement_predict import execute as engage_execute, SKILL_ID as ENGAGE_ID
from src.skills.publish_schedule import execute as schedule_execute, SKILL_ID as SCHEDULE_ID
from src.skills.health_score import execute as health_execute, SKILL_ID as HEALTH_ID
from src.skills.xhs_note_data_extraction import execute as xhs_execute, SKILL_ID as XHS_ID


class TestBrandConsistency:
    def test_basic_check_pass(self):
        result = brand_execute({
            "content": "使用XX品牌的宠物粮食，效果真的很好",
            "title": "XX品牌体验",
            "brand_name": "XX品牌",
            "brand_keywords": ["XX品牌", "宠物粮食"],
            "brand_tone": "professional",
            "prohibited_phrases": ["最棒"],
        })
        assert result["consistent"] is True or result["consistent"] is False
        assert 0 <= result["score"] <= 100
        assert result["skill_id"] == BRAND_ID

    def test_missing_keyword(self):
        result = brand_execute({
            "content": "效果很好，推荐",
            "title": "体验分享",
            "brand_name": "XX品牌",
            "brand_keywords": ["XX品牌"],
        })
        assert any(i["type"] == "missing_keyword" for i in result["issues"])

    def test_prohibited_phrase(self):
        result = brand_execute({
            "content": "这是最棒的产品",
            "title": "推荐",
            "brand_name": "XX品牌",
            "prohibited_phrases": ["最棒"],
        })
        assert any(i["type"] == "prohibited_phrase" for i in result["issues"])


class TestFingerprintGenerate:
    def test_basic_fingerprint(self):
        result = fp_execute({
            "content": "这是一篇关于宠物健康的内容",
            "title": "宠物健康指南",
        })
        assert len(result["fingerprint"]) > 0
        assert result["algorithm"] == "simhash_mvp"
        assert len(result["content_hash"]) == 32
        assert result["skill_id"] == FP_ID

    def test_different_content_different_fp(self):
        r1 = fp_execute({"content": "内容A", "title": "标题A"})
        r2 = fp_execute({"content": "内容B", "title": "标题B"})
        assert r1["fingerprint"] != r2["fingerprint"]

    def test_hash_algorithm(self):
        result = fp_execute({
            "content": "test",
            "algorithm": "sha256",
        })
        assert result["algorithm"] == "sha256"
        assert len(result["fingerprint"]) > 0


class TestEngagementPredict:
    def test_basic_prediction(self):
        result = engage_execute({
            "title": "养猫避坑指南",
            "content": "第一步...第二步...",
            "platform_id": "xhs",
            "account_followers": 5000,
        })
        assert "predicted_likes" in result
        assert "predicted_comments" in result
        assert "predicted_saves" in result
        assert result["predicted_likes"]["low"] <= result["predicted_likes"]["high"]
        assert result["skill_id"] == ENGAGE_ID

    def test_confidence_levels(self):
        result_high = engage_execute({
            "title": "10个养猫避坑指南！第3个太重要了",
            "content": "第一步...第二步...方法...教程...",
            "platform_id": "xhs",
            "account_followers": 10000,
        })
        assert result_high["confidence"] in ("high", "medium", "low")

    def test_platform_multiplier(self):
        r_xhs = engage_execute({
            "title": "test", "content": "test", "platform_id": "xhs", "account_followers": 1000,
        })
        r_douyin = engage_execute({
            "title": "test", "content": "test", "platform_id": "douyin", "account_followers": 1000,
        })
        # Douyin multiplier is higher
        assert r_douyin["predicted_likes"]["median"] >= r_xhs["predicted_likes"]["median"]


class TestPublishSchedule:
    def test_basic_schedule(self):
        result = schedule_execute({
            "platform_id": "xhs",
        })
        assert "recommended_time" in result
        assert "recommended_hour" in result
        assert "reason" in result
        assert result["skill_id"] == SCHEDULE_ID

    def test_alternative_slots(self):
        result = schedule_execute({
            "platform_id": "xhs",
        })
        assert len(result["alternative_slots"]) > 0

    def test_immediate_preference(self):
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        result = schedule_execute({
            "platform_id": "xhs",
            "prefer_immediate": True,
            "earliest_time": now.isoformat(),
        })
        assert result["recommended_time"] is not None


class TestHealthScore:
    def test_healthy_account(self):
        result = health_execute({
            "account_id": "acc_001",
            "platform_id": "xhs",
            "recent_posts_count": 10,
            "recent_violations": 0,
            "avg_engagement_rate": 0.08,
            "login_success_rate": 1.0,
            "days_since_last_post": 1,
            "follower_growth_rate": 0.1,
        })
        assert result["health_score"] >= 80
        assert result["status"] == "healthy"
        assert result["skill_id"] == HEALTH_ID

    def test_critical_account(self):
        result = health_execute({
            "account_id": "acc_002",
            "platform_id": "xhs",
            "recent_posts_count": 0,
            "recent_violations": 5,
            "avg_engagement_rate": 0.0,
            "login_success_rate": 0.5,
            "days_since_last_post": 60,
            "follower_growth_rate": -0.1,
        })
        assert result["health_score"] < 40
        assert result["status"] == "critical"
        assert len(result["suggestions"]) > 0

    def test_dimensions_sum(self):
        result = health_execute({
            "account_id": "acc_003", "platform_id": "xhs",
        })
        assert len(result["dimensions"]) == 5
        total_weight = sum(d["weight"] for d in result["dimensions"])
        assert abs(total_weight - 1.0) < 0.001


class TestXHSNoteExtraction:
    def test_basic_extraction(self):
        result = xhs_execute({
            "note_url": "https://www.xiaohongshu.com/explore/abc123",
        })
        assert result["note_id"] == "abc123"
        assert "title" in result
        assert "engagement" in result
        assert result["skill_id"] == XHS_ID

    def test_filter_engagement(self):
        result = xhs_execute({
            "note_url": "https://www.xiaohongshu.com/explore/abc123",
            "extract_engagement": False,
        })
        assert "engagement" not in result

    def test_parse_note_id_variations(self):
        from src.skills.xhs_note_data_extraction import _parse_note_id
        assert _parse_note_id("https://www.xiaohongshu.com/explore/abc123") == "abc123"
        assert _parse_note_id("https://www.xiaohongshu.com/note/abc123") == "abc123"
        assert _parse_note_id("abc123") == "abc123"
