"""Tests for Skill Hub v4.0 P3-1 Registration & Validation."""

import pytest

from src.services.skill_hub import (
    AgentSkillBinding,
    SkillDefinition,
    _skill_versions,
    bind_to_agent,
    get_agent_skills,
    get_latest_version,
    get_skill_versions,
    register,
    validate_invocation,
)


class TestRegister:
    def test_register_valid_skill(self):
        sd = SkillDefinition(
            skill_id="skill_test_001",
            name="Test Skill",
            description="A test skill",
            version="1.0.0",
            input_schema={"type": "object", "properties": {"topic": {"type": "string"}}},
            output_schema={"type": "object", "properties": {"result": {"type": "string"}}},
        )
        result = register(sd)
        assert result.skill_id == "skill_test_001"
        assert result.name == "Test Skill"
        assert result.version == "1.0.0"

    def test_register_invalid_schema(self):
        sd = SkillDefinition(
            skill_id="skill_test_002",
            name="Bad Schema",
            description="bad",
            input_schema="not_a_dict",
        )
        with pytest.raises(ValueError, match="Schema validation failed"):
            register(sd)

    def test_register_invalid_version(self):
        sd = SkillDefinition(
            skill_id="skill_test_003",
            name="Bad Version",
            description="bad",
            version="not-a-version",
        )
        with pytest.raises(ValueError, match="Invalid semantic version"):
            register(sd)

    def test_register_multiple_versions(self):
        # Register v1.0.0
        register(SkillDefinition(skill_id="skill_multi", name="Multi", description="m", version="1.0.0"))
        # Register v1.1.0
        register(SkillDefinition(skill_id="skill_multi", name="Multi", description="m", version="1.1.0"))
        # Register v2.0.0
        register(SkillDefinition(skill_id="skill_multi", name="Multi", description="m", version="2.0.0"))

        versions = get_skill_versions("skill_multi")
        assert len(versions) == 3
        assert versions[0].version == "2.0.0"  # latest first
        assert versions[1].version == "1.1.0"
        assert versions[2].version == "1.0.0"


class TestBindToAgent:
    def test_bind_and_list(self):
        register(SkillDefinition(skill_id="skill_bind", name="Bindable", description="b"))
        binding = bind_to_agent("skill_bind", "agt_001", priority=5, config={"key": "val"})
        assert binding.agent_id == "agt_001"
        assert binding.skill_id == "skill_bind"
        assert binding.priority == 5

    def test_get_agent_skills(self):
        register(SkillDefinition(skill_id="skill_a", name="Skill A", description="a"))
        register(SkillDefinition(skill_id="skill_b", name="Skill B", description="b"))
        bind_to_agent("skill_a", "agt_002")
        bind_to_agent("skill_b", "agt_002")

        skills = get_agent_skills("agt_002")
        skill_ids = {s.skill_id for s in skills}
        assert "skill_a" in skill_ids
        assert "skill_b" in skill_ids


class TestValidateInvocation:
    def test_validate_success_with_binding(self):
        register(SkillDefinition(
            skill_id="skill_val",
            name="Validatable",
            description="v",
            input_schema={
                "type": "object",
                "properties": {"topic": {"type": "string"}},
                "required": ["topic"],
            },
        ))
        bind_to_agent("skill_val", "agt_003")

        result = validate_invocation("skill_val", "agt_003", {"topic": "cats"})
        assert result["valid"] is True
        assert result["errors"] == []

    def test_validate_missing_permission(self):
        register(SkillDefinition(skill_id="skill_perm", name="Permission", description="p"))
        # No binding for agt_999
        result = validate_invocation("skill_perm", "agt_999", {})
        assert result["valid"] is False
        assert any("not bound" in e for e in result["errors"])

    def test_validate_missing_required_input(self):
        register(SkillDefinition(
            skill_id="skill_req",
            name="Required",
            description="r",
            input_schema={
                "type": "object",
                "properties": {"topic": {"type": "string"}},
                "required": ["topic"],
            },
        ))
        bind_to_agent("skill_req", "agt_004")

        result = validate_invocation("skill_req", "agt_004", {})
        assert result["valid"] is False
        assert any("Missing required input" in e for e in result["errors"])

    def test_validate_wrong_type(self):
        register(SkillDefinition(
            skill_id="skill_type",
            name="TypeCheck",
            description="t",
            input_schema={
                "type": "object",
                "properties": {"count": {"type": "integer"}},
            },
        ))
        bind_to_agent("skill_type", "agt_005")

        result = validate_invocation("skill_type", "agt_005", {"count": "not_a_number"})
        assert result["valid"] is False
        assert any("wrong type" in e for e in result["errors"])


class TestVersionManagement:
    def test_get_latest_version(self):
        register(SkillDefinition(skill_id="skill_latest", name="Latest", description="l", version="1.0.0"))
        register(SkillDefinition(skill_id="skill_latest", name="Latest", description="l", version="1.2.0"))

        latest = get_latest_version("skill_latest")
        assert latest is not None
        assert latest.version == "1.2.0"

    def test_get_latest_nonexistent(self):
        assert get_latest_version("skill_nonexistent") is None

    def test_l1_skills_are_public(self):
        # L1 skills don't require binding
        result = validate_invocation("L1-content-generate", "any_agent", {})
        assert result["valid"] is True
