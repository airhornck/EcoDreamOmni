"""Tests for Agent Lifecycle State Machine — v4.0 Phase 2 P2-1b."""

import pytest

from src.harness.state_machine import (
    AgentLifecycleState,
    AgentStateMachine,
    ILLEGAL_TRANSITIONS,
    StateMachineConfig,
    StateTransitionError,
)


class TestIllegalTransitions:
    def test_illegal_transitions_dict(self):
        assert len(ILLEGAL_TRANSITIONS) == 8
        assert (AgentLifecycleState.REGISTERED, AgentLifecycleState.OFFLINE) in ILLEGAL_TRANSITIONS

    def test_validate_target_state(self):
        sm = AgentStateMachine("agt_1")
        assert sm.validate_target_state(AgentLifecycleState.ACTIVE) is True
        assert sm.validate_target_state(AgentLifecycleState.DEGRADED) is False  # REGISTERED→DEGRADED illegal


class TestBasicTransitions:
    def test_register(self):
        sm = AgentStateMachine("agt_1")
        sm.register()
        assert sm.state == AgentLifecycleState.REGISTERED

    def test_activate_from_registered(self):
        sm = AgentStateMachine("agt_1")
        sm.activate()
        assert sm.state == AgentLifecycleState.ACTIVE
        assert sm.can_execute is True

    def test_pause_and_resume(self):
        sm = AgentStateMachine("agt_1")
        sm.activate()
        sm.pause()
        assert sm.state == AgentLifecycleState.PAUSED
        assert sm.can_execute is False
        sm.resume()
        assert sm.state == AgentLifecycleState.ACTIVE

    def test_offline(self):
        sm = AgentStateMachine("agt_1")
        sm.activate()
        sm.offline()
        assert sm.state == AgentLifecycleState.OFFLINE
        assert sm.can_execute is False
        assert sm.can_readonly is False


class TestIllegalTransitionBlocking:
    def test_registered_to_degraded_blocked(self):
        sm = AgentStateMachine("agt_1")
        with pytest.raises(StateTransitionError):
            sm.degrade()

    def test_registered_to_paused_blocked(self):
        sm = AgentStateMachine("agt_1")
        with pytest.raises(StateTransitionError):
            sm.pause()

    def test_offline_to_any_blocked(self):
        sm = AgentStateMachine("agt_1")
        sm.activate()
        sm.offline()
        with pytest.raises(StateTransitionError):
            sm.activate()
        with pytest.raises(StateTransitionError):
            sm.pause()
        with pytest.raises(StateTransitionError):
            sm.degrade()

    def test_paused_to_degraded_blocked(self):
        sm = AgentStateMachine("agt_1")
        sm.activate()
        sm.pause()
        with pytest.raises(StateTransitionError):
            sm.degrade()

    def test_degraded_to_paused_blocked(self):
        sm = AgentStateMachine("agt_1")
        sm.activate()
        sm.degrade()
        with pytest.raises(StateTransitionError):
            sm.pause()


class TestAutoTransitions:
    def test_auto_degrade_after_unhealthy_heartbeats(self):
        cfg = StateMachineConfig(max_degraded_misses=3)
        sm = AgentStateMachine("agt_1", config=cfg)
        sm.activate()

        sm.report_heartbeat(healthy=False)
        sm.report_heartbeat(healthy=False)
        assert sm.state == AgentLifecycleState.ACTIVE  # 2 failures, not yet degraded

        sm.report_heartbeat(healthy=False)
        assert sm.state == AgentLifecycleState.DEGRADED  # 3 failures → degraded

    def test_auto_activate_after_recovery(self):
        cfg = StateMachineConfig(max_degraded_misses=2, min_recovery_successes=2)
        sm = AgentStateMachine("agt_1", config=cfg)
        sm.activate()
        sm.report_heartbeat(healthy=False)
        sm.report_heartbeat(healthy=False)
        assert sm.state == AgentLifecycleState.DEGRADED

        sm.report_heartbeat(healthy=True)
        assert sm.state == AgentLifecycleState.DEGRADED  # 1 success, not yet recovered

        sm.report_heartbeat(healthy=True)
        assert sm.state == AgentLifecycleState.ACTIVE  # 2 successes → recovered

    def test_auto_offline_after_degraded_failures(self):
        cfg = StateMachineConfig(max_degraded_misses=2, max_offline_misses=4)
        sm = AgentStateMachine("agt_1", config=cfg)
        sm.activate()

        sm.report_heartbeat(healthy=False)
        sm.report_heartbeat(healthy=False)
        assert sm.state == AgentLifecycleState.DEGRADED

        sm.report_heartbeat(healthy=False)
        sm.report_heartbeat(healthy=False)
        assert sm.state == AgentLifecycleState.OFFLINE  # 4 failures in degraded → offline


class TestHistoryAndMetrics:
    def test_history_tracks_transitions(self):
        sm = AgentStateMachine("agt_1")
        sm.activate()
        sm.pause()
        sm.resume()

        history = sm.history()
        assert len(history) >= 3
        assert history[0].to_state == AgentLifecycleState.ACTIVE
        assert history[1].to_state == AgentLifecycleState.PAUSED
        assert history[2].to_state == AgentLifecycleState.ACTIVE

    def test_metrics(self):
        sm = AgentStateMachine("agt_1")
        sm.activate()
        m = sm.metrics()
        assert m["agent_id"] == "agt_1"
        assert m["state"] == "active"
        assert m["can_execute"] is True
        assert m["transition_count"] >= 1

    def test_on_transition_callback(self):
        calls = []

        def cb(record):
            calls.append(record)

        sm = AgentStateMachine("agt_1", on_transition=cb)
        sm.activate()
        sm.pause()

        assert len(calls) == 2
        assert calls[0].to_state == AgentLifecycleState.ACTIVE
        assert calls[1].to_state == AgentLifecycleState.PAUSED
