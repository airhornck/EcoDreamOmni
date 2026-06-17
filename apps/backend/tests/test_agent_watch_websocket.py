"""Tests for AgentWatch WebSocket StreamEvent — P8-6."""

from src.services.agent_watch_websocket import (
    emit_stream_event,
    get_event_buffer,
    clear_event_buffer,
    build_progress_event,
    build_agent_status_event,
    subscribe,
    unsubscribe,
)


class TestAgentWatchWebSocket:
    def test_emit_and_buffer(self):
        clear_event_buffer("exec_001")
        event = emit_stream_event(
            execution_id="exec_001",
            agent_id="agent_a",
            event_type="THINK",
            content="Thinking about trends...",
            tenant_id="t1",
        )
        assert event.event_type == "THINK"
        assert event.agent_id == "agent_a"

        buf = get_event_buffer("exec_001")
        assert len(buf) == 1
        assert buf[0].content == "Thinking about trends..."

    def test_clear_buffer(self):
        emit_stream_event("exec_002", "agent_a", "ACT", "Doing something")
        clear_event_buffer("exec_002")
        assert get_event_buffer("exec_002") == []

    def test_build_progress_event(self):
        event = build_progress_event(
            execution_id="exec_003",
            agent_id="agent_a",
            current_step=3,
            total_steps=10,
            step_description="Generating content",
            tenant_id="t1",
        )
        assert event.event_type == "PROGRESS"
        assert event.payload["progress_percent"] == 30
        assert event.payload["current_step"] == 3

    def test_build_agent_status_event(self):
        event = build_agent_status_event(
            agent_id="agent_b",
            status="HEALTHY",
            tenant_id="t1",
            extra={"execution_id": "exec_004"},
        )
        assert event.event_type == "AGENT_STATUS"
        assert event.payload["status"] == "HEALTHY"

    def test_multiple_events_same_execution(self):
        clear_event_buffer("exec_005")
        for et in ["THINK", "ACT", "OBSERVE", "OUTPUT", "ERROR"]:
            emit_stream_event("exec_005", "agent_c", et, f"event {et}")
        buf = get_event_buffer("exec_005")
        assert len(buf) == 5
        types = [e.event_type for e in buf]
        assert types == ["THINK", "ACT", "OBSERVE", "OUTPUT", "ERROR"]

    def test_subscribe_unsubscribe(self):
        class FakeWS:
            def __init__(self):
                self.sent = []
            async def send_text(self, text):
                self.sent.append(text)

        ws = FakeWS()
        subscribe("tenant_x", ws)
        assert ws in _get_subs("tenant_x")
        unsubscribe("tenant_x", ws)
        assert ws not in _get_subs("tenant_x")


def _get_subs(tenant_id):
    from src.services.agent_watch_websocket import _websocket_subscribers
    return _websocket_subscribers.get(tenant_id, set())
