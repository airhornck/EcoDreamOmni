"""Tests for Phase 3 Skills — v4.0 P3-2/P3-3."""

import pytest

from src.skills.content_structural_analysis import execute as structural_execute
from src.skills.content_rewrite import execute as rewrite_execute
from src.skills.title_optimize import execute as title_execute
from src.skills.image_style_transfer import execute as image_execute
from src.skills.video_clone import execute as video_execute
from src.skills.keyword_inject import execute as keyword_execute
from src.skills.persona_story_context import execute as persona_execute


class TestContentStructuralAnalysis:
    def test_standard_structure(self):
        content = "这是钩子\n正文第一段\n正文第二段\n记得点赞收藏！"
        result = structural_execute({"content": content})
        assert result["hook"] == "这是钩子"
        assert "正文" in result["body"]
        assert "点赞收藏" in result["cta"]
        assert result["structure_type"] == "standard"

    def test_short_note(self):
        content = "简短笔记"
        result = structural_execute({"content": content, "platform": "xhs"})
        assert result["structure_type"] == "short_note"

    def test_listicle_detection(self):
        content = "养宠攻略\n· 第一点\n· 第二点\n· 第三点"
        result = structural_execute({"content": content, "platform": "xhs"})
        assert result["structure_type"] == "listicle"


class TestContentRewrite:
    def test_casual_style(self):
        result = rewrite_execute({"content": "您非常优秀", "style": "casual"})
        assert "你" in result["rewritten"]
        assert "超" in result["rewritten"]

    def test_professional_style(self):
        result = rewrite_execute({"content": "超棒", "style": "professional"})
        assert "优秀" in result["rewritten"]

    def test_unknown_style_fallback(self):
        result = rewrite_execute({"content": "hello", "style": "unknown"})
        assert result["rewritten"] == "hello"


class TestTitleOptimize:
    def test_basic_variants(self):
        result = title_execute({"title": "养猫指南", "keywords": ["猫", "养宠"], "platform": "xhs"})
        assert len(result["variants"]) >= 2
        assert any("养猫指南" in v for v in result["variants"])

    def test_douyin_platform(self):
        result = title_execute({"title": "美食探店", "keywords": ["美食"], "platform": "douyin"})
        assert any("#" in v for v in result["variants"])

    def test_no_keywords(self):
        result = title_execute({"title": "测试标题"})
        assert len(result["variants"]) >= 1


class TestImageStyleTransfer:
    def test_warm_style(self):
        result = image_execute({"image_url": "http://test.jpg", "target_style": "warm"})
        assert result["style_params"]["temperature"] == 1.2

    def test_vintage_style(self):
        result = image_execute({"image_url": "http://test.jpg", "target_style": "vintage"})
        assert "grain" in result["style_params"]

    def test_with_brand_colors(self):
        result = image_execute({"image_url": "http://test.jpg", "target_style": "modern", "brand_colors": ["#FF0000"]})
        assert result["style_params"]["brand_color_overlay"] == "#FF0000"


class TestVideoClone:
    def test_douyin_script(self):
        result = video_execute({"topic": "美食教程", "duration_seconds": 60, "platform": "douyin"})
        assert len(result["script_segments"]) == 4  # 60/15
        assert result["music_suggestion"] == "节奏感强的电子音乐"

    def test_xhs_script(self):
        result = video_execute({"topic": "旅行攻略", "duration_seconds": 90, "platform": "xhs"})
        assert len(result["script_segments"]) == 3  # 90/30
        assert result["music_suggestion"] == "轻快治愈系背景音乐"

    def test_shot_list_structure(self):
        result = video_execute({"topic": "测试"})
        assert len(result["shot_list"]) == 3
        assert result["shot_list"][0]["type"] == "opening"


class TestKeywordInject:
    def test_pet_topic(self):
        result = keyword_execute({"content": "关于狗狗", "topic": "宠物", "platform_id": "xhs"})
        assert "养宠攻略" in result["injected_keywords"]
        assert result["injected_count"] >= 1
        assert any("小红书" in f for f in result["prompt_fragments"])

    def test_food_topic(self):
        result = keyword_execute({"content": "好吃的", "topic": "美食"})
        assert "美食探店" in result["injected_keywords"]

    def test_unknown_topic_fallback(self):
        result = keyword_execute({"content": "xyz", "topic": "未知领域"})
        assert result["injected_keywords"] == ["热门推荐", "精选内容", "必看"]


class TestPersonaStoryContext:
    def test_pet_expert(self):
        result = persona_execute({"persona_id": "pet_expert", "topic": "猫咪驱虫"})
        assert "宠物行为专家" in result["persona_intro"]
        assert "猫咪驱虫" in result["story_fragments"][1]

    def test_foodie(self):
        result = persona_execute({"persona_id": "foodie", "topic": "探店"})
        assert "吃货小达人" in result["persona_intro"]

    def test_unknown_persona_fallback(self):
        result = persona_execute({"persona_id": "unknown", "topic": "测试"})
        assert "宠物行为专家" in result["persona_intro"]  # fallback
