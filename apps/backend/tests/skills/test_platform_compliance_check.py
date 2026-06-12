"""Tests for platform_compliance_check Skill — Phase 8 P8-1."""

import pytest

from src.skills.platform_compliance_check import execute, SKILL_ID, VERSION


class TestPlatformComplianceCheckSkill:
    def test_skill_metadata(self):
        assert SKILL_ID == "platform_compliance_check"
        assert VERSION == "1.0.0"

    def test_clean_content_all_pass(self):
        result = execute({
            "content": "Nice weather today, took my cat outside.",
            "title": "Sunny day",
            "platform_id": "xhs",
        })
        assert result["l1_passed"] is True
        assert result["l2_passed"] is True

    def test_l1_length_violation(self):
        result = execute({
            "content": "a" * 2000,
            "title": "t" * 30,
            "platform_id": "xhs",
        })
        assert len(result["l1_violations"]) > 0

    def test_l2_sensitive_keyword(self):
        result = execute({
            "content": "这款产品永久有效，100%有效保证治愈。",
            "title": "绝对好用",
            "platform_id": "xhs",
        })
        assert result["l2_passed"] is False
        assert any(v["severity"] == "block" for v in result["l2_violations"])

    def test_l1_external_link_blocked(self):
        result = execute({
            "content": "点击这里查看详情 https://example.com",
            "title": "外链测试",
            "platform_id": "xhs",
        })
        assert result["l1_passed"] is False

    def test_platform_specific(self):
        for platform in ["xhs", "douyin", "bilibili", "wechat_official"]:
            result = execute({"content": "test", "title": "test", "platform_id": platform})
            assert result["platform"] == platform

    def test_output_schema(self):
        result = execute({"content": "test", "title": "test", "platform_id": "xhs"})
        assert "l1_passed" in result
        assert "l2_passed" in result
        assert "skill_id" in result
