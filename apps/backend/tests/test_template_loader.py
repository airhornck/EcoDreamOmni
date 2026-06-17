"""Tests for template_loader — P8-4."""

from src.core.template_loader import (
    load_all_templates,
    load_template,
    reload_template,
    list_template_ids,
)
from src.services.workflow_engine import NodeType


class TestTemplateLoader:
    def test_load_all_templates(self):
        templates = load_all_templates()
        assert len(templates) >= 8
        # Core templates must exist
        for tid in [
            "content_creation_standard",
            "content_creation_light",
            "trend_scout_only",
            "data_analysis_only",
            "content_creation_note_image",
            "content_creation_video_clone",
            "content_creation_video_original",
            "content_creation_text_article",
        ]:
            assert tid in templates, f"Missing template: {tid}"

    def test_load_template_by_id(self):
        tmpl = load_template("content_creation_standard")
        assert tmpl is not None
        assert tmpl.id == "content_creation_standard"
        assert len(tmpl.nodes) > 0
        assert tmpl.status in ("DRAFT", "ACTIVE")

    def test_load_template_not_found(self):
        assert load_template("nonexistent_xyz") is None

    def test_reload_template(self):
        tmpl = reload_template("content_creation_standard")
        assert tmpl is not None
        assert tmpl.id == "content_creation_standard"

    def test_list_template_ids(self):
        ids = list_template_ids()
        assert "content_creation_standard" in ids
        assert len(ids) >= 8

    def test_template_nodes_parsed(self):
        tmpl = load_template("content_creation_standard")
        assert tmpl is not None
        for node in tmpl.nodes:
            assert node.node_index >= 0
            assert isinstance(node.node_type, NodeType)
            assert node.node_name

    def test_publisher_requires_human_approval(self):
        # The template_loader validates publisher safety
        # Corrupt YAML would raise ValueError during load
        tmpl = load_template("content_creation_standard")
        assert tmpl is not None
        has_publisher = any(
            n.agent_id == "publisher" for n in tmpl.nodes if n.node_type == NodeType.AGENT
        )
        has_human = any(n.node_type == NodeType.HUMAN_APPROVAL for n in tmpl.nodes)
        if has_publisher:
            assert has_human, "Publisher without human_approval should be rejected"

    def test_dry_run_compatibility(self):
        """Ensure loaded templates are compatible with dry_run_execution."""
        from src.services.workflow_engine import dry_run_execution, reload_presets
        reload_presets()
        result = dry_run_execution("content_creation_standard")
        assert result["is_dry_run"] is True
        assert result["validation_passed"] is True
        assert len(result["simulated_nodes"]) > 0
