"""Tests for Handoff Protocol and Swarm Mode — Phase 9."""

import pytest
import asyncio
from src.services.handoff import (
    create_handoff,
    get_handoff,
    accept_handoff,
    reject_handoff,
    complete_handoff,
    list_pending_handoffs,
    list_handoffs_by_execution,
    HandoffType,
    HandoffStatus,
)
from src.services.swarm import (
    create_swarm_job,
    get_swarm_job,
    execute_swarm_fan_out,
    aggregate_results,
)


class TestHandoffProtocol:
    def test_create_handoff(self):
        msg = create_handoff(
            handoff_type="delegate",
            from_agent_id="agent_a",
            to_agent_id="agent_b",
            execution_id="exec_001",
            tenant_id="t1",
            task_description="Analyze trends",
        )
        assert msg.handoff_id.startswith("handoff_")
        assert msg.handoff_type == HandoffType.DELEGATE
        assert msg.status == HandoffStatus.PENDING
        assert msg.to_agent_id == "agent_b"

    def test_accept_handoff(self):
        msg = create_handoff(
            handoff_type="collaborate",
            from_agent_id="a1",
            to_agent_id="a2",
            execution_id="exec_002",
        )
        assert accept_handoff(msg.handoff_id) is True
        assert get_handoff(msg.handoff_id).status == HandoffStatus.ACCEPTED

    def test_reject_handoff(self):
        msg = create_handoff(
            handoff_type="escalate",
            from_agent_id="a1",
            to_agent_id="a2",
            execution_id="exec_003",
        )
        assert reject_handoff(msg.handoff_id, "busy") is True
        assert get_handoff(msg.handoff_id).status == HandoffStatus.REJECTED
        assert get_handoff(msg.handoff_id).context_payload["rejection_reason"] == "busy"

    def test_complete_handoff(self):
        msg = create_handoff(
            handoff_type="delegate",
            from_agent_id="a1",
            to_agent_id="a2",
            execution_id="exec_004",
        )
        accept_handoff(msg.handoff_id)
        assert complete_handoff(msg.handoff_id, {"result": "done"}) is True
        completed = get_handoff(msg.handoff_id)
        assert completed.status == HandoffStatus.COMPLETED
        assert completed.context_payload["result"]["result"] == "done"

    def test_list_pending(self):
        # Clear implicit state not possible without full reset; use new agent
        msg = create_handoff(
            handoff_type="delegate",
            from_agent_id="a1",
            to_agent_id="pending_agent_99",
            execution_id="exec_005",
        )
        pending = list_pending_handoffs("pending_agent_99")
        assert any(p.handoff_id == msg.handoff_id for p in pending)

    def test_list_by_execution(self):
        msg1 = create_handoff(
            handoff_type="delegate",
            from_agent_id="a1",
            to_agent_id="a2",
            execution_id="exec_batch_1",
        )
        msg2 = create_handoff(
            handoff_type="return",
            from_agent_id="a2",
            to_agent_id="a1",
            execution_id="exec_batch_1",
        )
        batch = list_handoffs_by_execution("exec_batch_1")
        ids = {m.handoff_id for m in batch}
        assert msg1.handoff_id in ids
        assert msg2.handoff_id in ids

    def test_double_accept_fails(self):
        msg = create_handoff(
            handoff_type="delegate",
            from_agent_id="a1",
            to_agent_id="a2",
            execution_id="exec_006",
        )
        accept_handoff(msg.handoff_id)
        assert accept_handoff(msg.handoff_id) is False


class TestSwarmMode:
    def test_create_swarm_job(self):
        job = create_swarm_job(
            agent_type="trend-scout",
            fleet_id="fleet_001",
            task_inputs=[
                {"query": "cats"},
                {"query": "dogs"},
                {"query": "birds"},
            ],
            tenant_id="t1",
        )
        assert job.job_id.startswith("job_")
        assert len(job.tasks) == 3
        assert job.status == "pending"

    def test_get_swarm_job(self):
        job = create_swarm_job(
            agent_type="content-forge",
            fleet_id="fleet_001",
            task_inputs=[{"topic": "a"}],
        )
        fetched = get_swarm_job(job.job_id)
        assert fetched is not None
        assert fetched.job_id == job.job_id

    @pytest.mark.asyncio
    async def test_execute_swarm_fan_out(self):
        job = create_swarm_job(
            agent_type="mock-agent",
            fleet_id="fleet_001",
            task_inputs=[
                {"value": 1},
                {"value": 2},
                {"value": 3},
            ],
        )

        async def mock_handler(payload):
            await asyncio.sleep(0.01)
            return {"value": payload["value"] * 2, "score": payload["value"]}

        result_job = await execute_swarm_fan_out(job.job_id, mock_handler, max_concurrency=2)
        assert result_job.status in ("running", "aggregating")

    @pytest.mark.asyncio
    async def test_aggregate_merge(self):
        job = create_swarm_job(
            agent_type="mock-agent",
            fleet_id="fleet_001",
            task_inputs=[{"v": 1}, {"v": 2}],
        )

        async def mock_handler(payload):
            return {"v": payload["v"], "score": payload["v"]}

        await execute_swarm_fan_out(job.job_id, mock_handler)
        agg = aggregate_results(job.job_id, strategy="merge")
        assert agg["success"] is True
        assert agg["strategy"] == "merge"
        assert agg["aggregated"]["count"] == 2

    @pytest.mark.asyncio
    async def test_aggregate_best(self):
        job = create_swarm_job(
            agent_type="mock-agent",
            fleet_id="fleet_001",
            task_inputs=[{"v": 1}, {"v": 5}, {"v": 3}],
        )

        async def mock_handler(payload):
            return {"v": payload["v"], "score": payload["v"]}

        await execute_swarm_fan_out(job.job_id, mock_handler)
        agg = aggregate_results(job.job_id, strategy="best")
        assert agg["success"] is True
        assert agg["aggregated"]["best_result"]["score"] == 5

    @pytest.mark.asyncio
    async def test_aggregate_with_failures(self):
        job = create_swarm_job(
            agent_type="mock-agent",
            fleet_id="fleet_001",
            task_inputs=[{"ok": True}, {"ok": False}],
        )

        async def mock_handler(payload):
            if not payload["ok"]:
                raise ValueError("simulated failure")
            return {"ok": True}

        await execute_swarm_fan_out(job.job_id, mock_handler)
        agg = aggregate_results(job.job_id, strategy="merge")
        assert agg["success"] is True
        assert agg["completed_count"] == 1
        assert agg["failed_count"] == 1

    def test_aggregate_job_not_found(self):
        with pytest.raises(ValueError, match="not found"):
            aggregate_results("nonexistent_job", strategy="merge")
