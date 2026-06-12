"""Tests for image_generate Skill — Phase 8 P8-2."""

import pytest

from src.skills.image_generate import execute, SKILL_ID, VERSION


class TestImageGenerateSkill:
    def test_skill_metadata(self):
        assert SKILL_ID == "image_generate"
        assert VERSION == "1.0.0"

    def test_basic_txt2img(self):
        result = execute({"prompt": "一只可爱的橘猫在阳光下睡觉", "platform_id": "xhs"})
        assert result["image_url"]
        assert result["status"] == "placeholder"
        assert result["placeholder"] is True

    def test_platform_dimensions(self):
        for platform in ["xhs", "douyin", "bilibili", "wechat_official"]:
            result = execute({"prompt": "test", "platform_id": platform})
            dims = result["image_dimensions"]
            assert dims["width"] > 0
            assert dims["height"] > 0

    def test_aspect_ratio_override(self):
        result = execute({"prompt": "test", "platform_id": "xhs", "aspect_ratio": "16:9"})
        assert result["image_dimensions"]["aspect_ratio"] == "16:9"

    def test_image_style_prefix(self):
        for style in ["realistic", "illustration", "minimal", "cartoon"]:
            result = execute({"prompt": "猫咪", "platform_id": "xhs", "image_style": style})
            params = result["generation_params"]
            assert params["image_style"] == style
            assert len(params["enhanced_prompt"]) > len(params["original_prompt"])

    def test_img2img_mode(self):
        result = execute({
            "prompt": "把这只猫变成水彩风格",
            "platform_id": "xhs",
            "reference_image_url": "https://example.com/cat.jpg",
        })
        assert result["generation_params"]["mode"] == "img2img"

    def test_output_schema(self):
        result = execute({"prompt": "test", "platform_id": "xhs"})
        assert "image_url" in result
        assert "image_dimensions" in result
        assert "skill_id" in result
