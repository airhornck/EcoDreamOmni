"""Tests for content_generate Skill — Phase 8 P8-2."""

import pytest

from src.skills.content_generate import execute, SKILL_ID, VERSION, REQUIRES_LLM


class TestContentGenerateSkill:
    def test_skill_metadata(self):
        assert SKILL_ID == "content_generate"
        assert VERSION == "1.0.0"
        assert REQUIRES_LLM is True

    def test_basic_generation(self):
        result = execute({
            "topic": "驱虫药选择",
            "persona_name": "省钱狗爸",
            "platform_id": "xhs",
        })
        assert result["title"]
        assert result["content"]
        assert result["word_count"] > 0
        assert isinstance(result["hashtags"], list)
        assert result["generation_method"] == "template_mvp"

    def test_prompt_layers_present(self):
        result = execute({
            "topic": "疫苗接种",
            "persona_name": "专业兽医小王",
            "persona_tone": "professional",
            "brand_knowledge": ["猫三联每年接种一次", "狂犬疫苗必打"],
            "keywords": ["疫苗", "接种", "猫三联"],
            "platform_id": "xhs",
        })
        layers = result["prompt_layers"]
        assert "layer_1_platform_format" in layers
        assert "layer_2_structure_template" in layers
        assert "layer_3_brand_knowledge" in layers
        assert "layer_4_keywords" in layers
        assert "layer_5_persona" in layers
        assert "layer_6_style_dna" in layers

    def test_different_tones(self):
        for tone in ["casual", "professional", "humorous", "empathetic"]:
            result = execute({
                "topic": "猫粮选择",
                "persona_name": "测试",
                "persona_tone": tone,
                "platform_id": "xhs",
            })
            assert result["content"]
            assert result["word_count"] > 0

    def test_different_platforms(self):
        for platform in ["xhs", "douyin", "bilibili", "wechat_official"]:
            result = execute({
                "topic": "养猫心得",
                "persona_name": "猫奴阿明",
                "platform_id": platform,
            })
            assert result["title"]
            assert result["content"]

    def test_hashtag_limits(self):
        result = execute({
            "topic": "猫咪驱虫",
            "persona_name": "测试",
            "keywords": ["驱虫", "疫苗", "猫粮", "护理", "健康"],
            "platform_id": "douyin",
        })
        assert len(result["hashtags"]) <= 5  # douyin limit

    def test_word_count_target(self):
        result = execute({
            "topic": "长文测试",
            "persona_name": "测试",
            "word_count_target": 800,
            "platform_id": "wechat_official",
        })
        assert result["word_count"] > 0

    def test_output_schema(self):
        result = execute({
            "topic": "测试",
            "persona_name": "测试",
        })
        assert "title" in result
        assert "content" in result
        assert "hashtags" in result
        assert "word_count" in result
        assert "prompt_layers" in result
        assert "generation_method" in result
        assert "skill_id" in result
