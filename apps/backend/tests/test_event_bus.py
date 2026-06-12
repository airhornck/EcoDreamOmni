"""Tests for Event Bus — Phase 5 P5-2.

Red-Green TDD for:
  - publish / consume / ack 完整链路
  - 消费者组
  - 多条消息 FIFO 顺序
  - Redis fallback 模式
  - 批量消息无丢失
"""

import pytest

from src.core.event_bus import (
    EventBus,
    AGENT_EVENTS,
    PIPELINE_EVENTS,
    SYSTEM_EVENTS,
    WORKBENCH_EVENTS,
    build_message,
    ALL_STREAMS,
)


@pytest.fixture
def bus():
    return EventBus(redis_client=None)


# ─── 1. Basic publish / consume / ack ───


@pytest.mark.asyncio
async def test_publish_and_consume(bus):
    """发布一条消息后能消费到."""
    msg = build_message("agent.heartbeat", "agent_001", {"status": "healthy"})
    msg_id = await bus.publish(AGENT_EVENTS, msg)
    assert msg_id.startswith("mem-")

    await bus.create_consumer_group(AGENT_EVENTS, "g1")
    consumed = await bus.consume(AGENT_EVENTS, "g1", "c1", count=1)
    assert len(consumed) == 1
    assert consumed[0]["data"]["event_type"] == "agent.heartbeat"


@pytest.mark.asyncio
async def test_ack_removes_from_pending(bus):
    """ACK 后消息不再出现在 pending 中."""
    msg = build_message("task.start", "orchestrator", {"task_id": "t1"})
    await bus.publish(PIPELINE_EVENTS, msg)

    await bus.create_consumer_group(PIPELINE_EVENTS, "g1")
    consumed = await bus.consume(PIPELINE_EVENTS, "g1", "c1", count=1)
    assert len(consumed) == 1

    ok = await bus.ack(PIPELINE_EVENTS, "g1", consumed[0]["id"])
    assert ok is True
    assert bus.get_pending_count(PIPELINE_EVENTS, "g1") == 0


@pytest.mark.asyncio
async def test_consume_no_message_returns_empty(bus):
    """空 Stream 消费返回空列表."""
    await bus.create_consumer_group(SYSTEM_EVENTS, "g1")
    consumed = await bus.consume(SYSTEM_EVENTS, "g1", "c1", count=1, block_ms=100)
    assert consumed == []


# ─── 2. FIFO order ───


@pytest.mark.asyncio
async def test_fifo_order_preserved(bus):
    """多条消息保持 FIFO 顺序."""
    for i in range(5):
        msg = build_message("step", "pipeline", {"index": i})
        await bus.publish(PIPELINE_EVENTS, msg)

    await bus.create_consumer_group(PIPELINE_EVENTS, "g1")
    consumed = await bus.consume(PIPELINE_EVENTS, "g1", "c1", count=5)
    indices = [c["data"]["payload"]["index"] for c in consumed]
    assert indices == [0, 1, 2, 3, 4]


# ─── 3. Consumer groups isolation ───


@pytest.mark.asyncio
async def test_multiple_consumer_groups(bus):
    """不同消费者组各自消费消息."""
    msg = build_message("broadcast", "system", {"alert": "low_disk"})
    await bus.publish(SYSTEM_EVENTS, msg)

    await bus.create_consumer_group(SYSTEM_EVENTS, "g1")
    await bus.create_consumer_group(SYSTEM_EVENTS, "g2")

    c1 = await bus.consume(SYSTEM_EVENTS, "g1", "c1", count=1)
    c2 = await bus.consume(SYSTEM_EVENTS, "g2", "c2", count=1)

    assert len(c1) == 1
    assert len(c2) == 1
    assert c1[0]["id"] == c2[0]["id"]


# ─── 4. Batch publish / consume ───


@pytest.mark.asyncio
async def test_1000_messages_no_loss(bus):
    """1000 条消息发布/消费无丢失."""
    for i in range(1000):
        msg = build_message("log", "service", {"seq": i})
        await bus.publish(WORKBENCH_EVENTS, msg)

    await bus.create_consumer_group(WORKBENCH_EVENTS, "g1")
    total_consumed = 0
    while True:
        batch = await bus.consume(WORKBENCH_EVENTS, "g1", "c1", count=100)
        if not batch:
            break
        total_consumed += len(batch)
        for item in batch:
            await bus.ack(WORKBENCH_EVENTS, "g1", item["id"])

    assert total_consumed == 1000


# ─── 5. Build message format ───


def test_build_message_structure():
    """build_message 返回标准格式."""
    msg = build_message("test", "src", {"k": "v"}, trace_id="abc123")
    assert msg["event_type"] == "test"
    assert msg["source"] == "src"
    assert msg["payload"] == {"k": "v"}
    assert msg["trace_id"] == "abc123"
    assert "timestamp" in msg


def test_build_message_generates_trace_id():
    """未提供 trace_id 时自动生成."""
    msg = build_message("test", "src", {})
    assert "trace_id" in msg
    assert len(msg["trace_id"]) == 16


# ─── 6. Stream constants ───


def test_all_streams_defined():
    """ALL_STREAMS 包含全部预定义频道."""
    assert AGENT_EVENTS in ALL_STREAMS
    assert PIPELINE_EVENTS in ALL_STREAMS
    assert SYSTEM_EVENTS in ALL_STREAMS
    assert WORKBENCH_EVENTS in ALL_STREAMS
