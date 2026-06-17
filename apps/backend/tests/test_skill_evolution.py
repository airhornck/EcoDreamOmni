"""Tests for Skill Evolution — v4.0 Phase 3 P3-4."""


from src.skills.evolution import (
    get_all_scores,
    get_evolution_report,
    get_quality_score,
    record_execution,
)


class TestSkillEvolution:
    def test_record_success(self):
        rec = record_execution(
            skill_id="skill_ev_1",
            agent_id="agt_1",
            tenant_id="t1",
            inputs={"topic": "cats"},
            outputs={"result": "ok"},
            success=True,
            latency_ms=100,
        )
        assert rec.success is True
        assert rec.skill_id == "skill_ev_1"

    def test_quality_score_updates(self):
        record_execution("skill_ev_2", "agt_1", "t1", {}, {}, True, latency_ms=100)
        record_execution("skill_ev_2", "agt_1", "t1", {}, {}, True, latency_ms=200)
        record_execution("skill_ev_2", "agt_1", "t1", {}, {}, False, error="timeout", latency_ms=5000)

        qs = get_quality_score("skill_ev_2")
        assert qs is not None
        assert qs.total_executions == 3
        assert qs.success_count == 2
        assert qs.failure_count == 1
        assert qs.score > 0

    def test_evolution_report(self):
        for i in range(10):
            record_execution("skill_ev_3", "agt_1", "t1", {}, {}, True, latency_ms=100)
        report = get_evolution_report("skill_ev_3")
        assert "skill_id" in report
        assert report["total_executions"] == 10
        assert report["success_rate"] == 1.0
        assert report["recommendation"] == "stable"

    def test_low_score_recommendation(self):
        for i in range(10):
            record_execution("skill_ev_4", "agt_1", "t1", {}, {}, False, error="error", latency_ms=10000)
        report = get_evolution_report("skill_ev_4")
        assert report["recommendation"] == "needs_improvement"
        assert len(report["top_failure_patterns"]) > 0

    def test_positive_samples_capped(self):
        for i in range(150):
            record_execution("skill_ev_5", "agt_1", "t1", {}, {}, True, latency_ms=50)
        qs = get_quality_score("skill_ev_5")
        assert len(qs.positive_samples) == 100  # capped

    def test_get_all_scores(self):
        record_execution("skill_ev_all", "agt_1", "t1", {}, {}, True)
        scores = get_all_scores()
        assert any(s.skill_id == "skill_ev_all" for s in scores)
