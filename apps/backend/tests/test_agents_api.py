"""Tests for Agents API — v4.0 Agent-First Architecture.

Pure unit tests (no DB required) for:
  - Agent recommendation scoring algorithm
  - Agent list filtering (post-filter logic)
  - Required capabilities derivation
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.api.agents import _calculate_recommend_score, _derive_required_capabilities
from src.services.agent_function import AgentInfo


# ─── 1. Recommendation Scoring ───

class TestRecommendScore:
    def test_success_rate_dominates(self):
        """Higher success_rate agent should score higher."""
        agent_high = AgentInfo(
            id="a1", name="High", role="content_generation",
            success_rate=0.95, recent_tasks_1h=0, config={},
        )
        agent_low = AgentInfo(
            id="a2", name="Low", role="content_generation",
            success_rate=0.50, recent_tasks_1h=0, config={},
        )
        score_high = _calculate_recommend_score(agent_high, "xiaohongshu", "图文")
        score_low = _calculate_recommend_score(agent_low, "xiaohongshu", "图文")
        assert score_high > score_low

    def test_load_balancing_penalty(self):
        """Agent with high recent_tasks_1h should score lower."""
        agent_idle = AgentInfo(
            id="a1", name="Idle", role="content_generation",
            success_rate=0.92, recent_tasks_1h=0, config={"max_concurrent_tasks": 20},
        )
        agent_busy = AgentInfo(
            id="a2", name="Busy", role="content_generation",
            success_rate=0.92, recent_tasks_1h=20, config={"max_concurrent_tasks": 20},
        )
        score_idle = _calculate_recommend_score(agent_idle, "xiaohongshu", "图文")
        score_busy = _calculate_recommend_score(agent_busy, "xiaohongshu", "图文")
        assert score_idle > score_busy

    def test_score_range(self):
        """Score should be within reasonable bounds (0~1)."""
        agent = AgentInfo(
            id="a1", name="Test", role="content_generation",
            success_rate=1.0, recent_tasks_1h=0, config={},
        )
        score = _calculate_recommend_score(agent, "xiaohongshu", "图文")
        assert 0.0 <= score <= 1.0


# ─── 2. Required Capabilities Derivation ───

class TestDeriveCapabilities:
    def test_image_format(self):
        caps = _derive_required_capabilities("xiaohongshu", "图文")
        assert "text_generate_skill" in caps
        assert "rag_retrieval_skill" in caps
        assert "cover_generate_skill" in caps

    def test_video_format(self):
        caps = _derive_required_capabilities("douyin", "视频")
        assert "video_script_skill" in caps
        assert "hook_optimize_skill" in caps  # douyin specific

    def test_video_clone_format(self):
        caps = _derive_required_capabilities("douyin", "视频复刻")
        assert "video_clone_skill" in caps
        assert "style_transfer_skill" in caps

    def test_text_only_format(self):
        caps = _derive_required_capabilities("xiaohongshu", "仅文字")
        assert "content_structural_analysis_skill" in caps

    def test_bilibili_video(self):
        caps = _derive_required_capabilities("bilibili", "视频")
        assert "part_planning_skill" in caps

    def test_wechat_text(self):
        caps = _derive_required_capabilities("wechat_channels", "图文")
        assert "readability_optimize_skill" in caps


# ─── 3. AgentInfo Dataclass ───

class TestAgentInfo:
    def test_defaults(self):
        a = AgentInfo(id="test", name="Test", role="content_generation")
        assert a.success_rate == 0.92
        assert a.status == "ACTIVE"
        assert a.skills == []
        assert a.config == {}

    def test_config_access(self):
        a = AgentInfo(
            id="test", name="Test", role="content_generation",
            config={"default_workflow_template_id": "wf_001"},
        )
        assert a.config.get("default_workflow_template_id") == "wf_001"
