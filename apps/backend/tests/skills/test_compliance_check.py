"""Tests for compliance_check Skill — Phase 8 P8-1."""


from src.skills.compliance_check import execute, SKILL_ID, VERSION


class TestComplianceCheckSkill:
    def test_skill_metadata(self):
        assert SKILL_ID == "compliance_check"
        assert VERSION == "1.0.0"

    def test_clean_content_passes(self):
        result = execute({
            "content": "Brushed my cat today, found a lot of shedding.",
            "title": "Cat brushing log",
            "platform_id": "xhs",
        })
        assert result["passed"] is True
        assert result["risk_level"] == "low"
        assert len(result["violations"]) == 0

    def test_sensitive_words_detected(self):
        result = execute({
            "content": "这款猫粮效果最好，绝对是第一选择，顶级品质。",
            "title": "最好的猫粮",
            "platform_id": "xhs",
        })
        assert result["passed"] is True
        assert result["risk_level"] == "medium"
        violations = result["violations"]
        assert any(v["type"] == "sensitive_word" for v in violations)

    def test_length_violation(self):
        result = execute({
            "content": "a" * 2000,
            "title": "超长标题" * 10,
            "hashtags": ["tag"] * 15,
            "platform_id": "xhs",
        })
        assert result["risk_level"] == "low"
        violations = result["violations"]
        assert any(v["type"] == "length_violation" for v in violations)

    def test_vetdrug_claims_flagged(self):
        result = execute({
            "content": "我家猫得了耳螨，用这款药治疗，效果很好，治愈了。",
            "title": "耳螨治疗经验",
            "platform_id": "xhs",
        })
        violations = result["violations"]
        assert any(v["type"] == "vetdrug_claim" for v in violations)

    def test_platform_specific_rules(self):
        for platform in ["xhs", "douyin", "bilibili", "wechat_official"]:
            result = execute({"content": "test", "title": "test", "platform_id": platform})
            assert "check_items" in result
            assert len(result["check_items"]) == 4

    def test_output_schema(self):
        result = execute({"content": "test", "title": "test", "platform_id": "xhs"})
        assert "passed" in result
        assert "risk_level" in result
        assert "violations" in result
        assert "skill_id" in result
