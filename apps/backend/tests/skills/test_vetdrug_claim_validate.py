"""Tests for vetdrug_claim_validate Skill — Phase 8 P8-1."""


from src.skills.vetdrug_claim_validate import execute, SKILL_ID, VERSION


class TestVetDrugClaimValidateSkill:
    def test_skill_metadata(self):
        assert SKILL_ID == "vetdrug_claim_validate"
        assert VERSION == "1.0.0"

    def test_no_vetdrug_content_passes(self):
        result = execute({"content": "Took my cat to the park today."})
        assert result["valid"] is True
        assert len(result["invalid_claims"]) == 0

    def test_overclaim_blocked(self):
        result = execute({"content": "这款驱虫药100%有效，治愈所有寄生虫，永不复发，绝对安全无副作用。"})
        assert result["valid"] is False
        invalid = result["invalid_claims"]
        assert len(invalid) > 0
        assert any(v["severity"] == "block" for v in invalid)

    def test_valid_approval_number(self):
        result = execute({
            "content": "我家猫用大宠爱驱虫，效果很好。",
            "approval_numbers": ["兽药字220031609"],
        })
        assert result["valid"] is True
        assert len(result["approved_claims"]) > 0

    def test_invalid_approval_number(self):
        result = execute({
            "content": "用了某款新药。",
            "approval_numbers": ["兽药字999999999"],
        })
        assert result["valid"] is False

    def test_claim_not_in_indications(self):
        result = execute({
            "content": "这款药可以治疗感冒和发烧。",
            "approval_numbers": ["兽药字220031609"],
            "vetdrug_claims": ["治疗感冒", "治疗发烧"],
        })
        assert result["valid"] is True
        assert len(result["warnings"]) > 0

    def test_extract_claims_auto(self):
        result = execute({"content": "给猫咪做了体内驱虫和体外驱虫，预防心丝虫。"})
        assert len(result["approved_claims"]) > 0 or len(result["warnings"]) > 0

    def test_output_schema(self):
        result = execute({"content": "test"})
        assert "valid" in result
        assert "invalid_claims" in result
        assert "skill_id" in result
