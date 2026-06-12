"""Tests for Meta-Orchestrator — v4.0 Phase 2 P2-2."""

import pytest

from src.harness.meta_orchestrator import (
    BlackboardEntry,
    DynamicRouter,
    IntentClassifier,
    IntentResult,
    IntentType,
    MetaOrchestrator,
    OrchestrationMode,
    RouteResult,
    StateCoordinator,
    TaskDecomposer,
)


class TestIntentClassifier:
    def test_classify_content_creation(self):
        ic = IntentClassifier()
        result = ic.classify("帮我写一篇关于猫咪的文案")
        assert result.intent == IntentType.CONTENT_CREATION
        assert result.confidence > 0.5
        assert "draft" in result.sub_intents

    def test_classify_data_analysis(self):
        ic = IntentClassifier()
        result = ic.classify("分析一下最近的互动数据")
        assert result.intent == IntentType.DATA_ANALYSIS
        assert "battle_report" in result.sub_intents

    def test_classify_account_management(self):
        ic = IntentClassifier()
        result = ic.classify("帮我排期发布")
        assert result.intent == IntentType.ACCOUNT_MANAGEMENT

    def test_classify_system_query(self):
        ic = IntentClassifier()
        result = ic.classify("这个怎么用")
        assert result.intent == IntentType.SYSTEM_QUERY

    def test_classify_unknown(self):
        ic = IntentClassifier()
        result = ic.classify("xyz abc 123")
        assert result.intent == IntentType.UNKNOWN
        assert result.confidence == 0.0


class TestTaskDecomposer:
    def test_decompose_content_creation(self):
        td = TaskDecomposer()
        result = td.decompose(IntentType.CONTENT_CREATION)
        assert len(result.todos) >= 3
        assert result.todos[0].skill_id == "research"
        assert result.todos[1].skill_id == "draft_writer"
        assert result.sop_template_id == "sop_content_v1"

    def test_decompose_data_analysis(self):
        td = TaskDecomposer()
        result = td.decompose(IntentType.DATA_ANALYSIS)
        assert any(t.skill_id == "engagement_collect" for t in result.todos)

    def test_decompose_custom_sop(self):
        td = TaskDecomposer()
        result = td.decompose(IntentType.CONTENT_CREATION, sop_template_id="sop_content_v1")
        assert result.sop_template_id == "sop_content_v1"


class TestDynamicRouter:
    def test_route_direct_for_system_query(self):
        dr = DynamicRouter()
        result = dr.route(IntentType.SYSTEM_QUERY, todo_count=1)
        assert result.mode == OrchestrationMode.DIRECT

    def test_route_direct_for_single_todo(self):
        dr = DynamicRouter()
        result = dr.route(IntentType.CONTENT_CREATION, todo_count=1)
        assert result.mode == OrchestrationMode.DIRECT

    def test_route_pipeline_default(self):
        dr = DynamicRouter()
        result = dr.route(IntentType.CONTENT_CREATION, todo_count=3)
        assert result.mode == OrchestrationMode.PIPELINE

    def test_route_swarm_for_many_todos(self):
        dr = DynamicRouter()
        result = dr.route(IntentType.CONTENT_CREATION, todo_count=6)
        assert result.mode == OrchestrationMode.SWARM

    def test_route_dynamic_for_high_priority(self):
        dr = DynamicRouter()
        result = dr.route(IntentType.CONTENT_CREATION, todo_count=3, priority="high")
        assert result.mode == OrchestrationMode.DYNAMIC


class TestStateCoordinator:
    def test_create_session(self):
        sc = StateCoordinator()
        sid = sc.create_session()
        assert sid.startswith("sess_")

    def test_write_and_read(self):
        sc = StateCoordinator()
        sid = sc.create_session()
        sc.write(sid, "intent", "content_creation", agent_id="test")
        entry = sc.read(sid, "intent")
        assert entry is not None
        assert entry.value == "content_creation"
        assert entry.updated_by == "test"

    def test_register_agent(self):
        sc = StateCoordinator()
        sid = sc.create_session()
        sc.register_agent(sid, "agt_1")
        sc.register_agent(sid, "agt_2")
        assert sc.get_agents(sid) == ["agt_1", "agt_2"]

    def test_snapshot(self):
        sc = StateCoordinator()
        sid = sc.create_session()
        sc.write(sid, "mode", "PIPELINE")
        sc.register_agent(sid, "agt_1")
        snap = sc.snapshot(sid)
        assert snap["session_id"] == sid
        assert "mode" in snap["entries"]
        assert "agt_1" in snap["agents"]


class TestMetaOrchestrator:
    def test_orchestrate_full_pipeline(self):
        mo = MetaOrchestrator()
        result = mo.orchestrate("帮我写一篇关于狗狗的小红书笔记")

        assert result.session_id.startswith("sess_")
        assert result.intent.intent == IntentType.CONTENT_CREATION
        assert len(result.decomposition.todos) > 0
        assert result.route.mode == OrchestrationMode.PIPELINE
        assert "intent" in result.blackboard["entries"]

    def test_orchestrate_with_existing_session(self):
        mo = MetaOrchestrator()
        r1 = mo.orchestrate("分析数据")
        sid = r1.session_id

        r2 = mo.orchestrate("继续", session_id=sid)
        assert r2.session_id == sid
        assert len(r2.blackboard["entries"]) >= 3  # intent + todos + mode

    def test_orchestrate_system_query(self):
        mo = MetaOrchestrator()
        result = mo.orchestrate("这个系统怎么用")
        assert result.intent.intent == IntentType.SYSTEM_QUERY
        assert result.route.mode == OrchestrationMode.DIRECT
