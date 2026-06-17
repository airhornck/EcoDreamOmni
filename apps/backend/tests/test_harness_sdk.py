"""Tests for Agent SDK — v4.0 Phase 2 P2-1a."""

import asyncio

import pytest

from src.harness.sdk import (
    AgentSDK,
    AgentSDKConfig,
    CircuitBreakerConfig,
    CircuitBreakerWrapper,
    EventClient,
    EventConfig,
    HealthClient,
    RateLimiter,
    RateLimitConfig,
    RetryConfig,
    get_current_trace_id,
    set_current_trace_id,
    with_retry,
)


class TestRetryPolicy:
    @pytest.mark.asyncio
    async def test_with_retry_success(self):
        call_count = 0

        @with_retry(RetryConfig(max_retries=2, backoff_factor=0.1))
        async def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("simulated")
            return "ok"

        result = await flaky()
        assert result == "ok"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_with_retry_exhausted(self):
        call_count = 0

        @with_retry(RetryConfig(max_retries=1, backoff_factor=0.05))
        async def always_fail():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("boom")

        with pytest.raises(ConnectionError):
            await always_fail()
        assert call_count == 2  # initial + 1 retry


class TestCircuitBreaker:
    @pytest.mark.asyncio
    async def test_circuit_closed_on_success(self):
        cb = CircuitBreakerWrapper("test_cb")

        async def ok():
            return "success"

        result = await cb.call(ok)
        assert result == "success"
        assert cb.state == "closed"
        assert cb.metrics()["total_success"] == 1

    @pytest.mark.asyncio
    async def test_circuit_opens_after_failures(self):
        cb = CircuitBreakerWrapper("test_cb", CircuitBreakerConfig(fail_max=2, reset_timeout=1))

        async def fail():
            raise ValueError("fail")

        with pytest.raises(ValueError):
            await cb.call(fail)
        with pytest.raises(ValueError):
            await cb.call(fail)

        # Circuit should be open now
        assert cb.state == "open"
        assert cb.metrics()["total_failure"] == 2


class TestRateLimiter:
    @pytest.mark.asyncio
    async def test_rate_limit_allows_within_capacity(self):
        rl = RateLimiter(RateLimitConfig(rate=100, capacity=10))
        allowed = 0
        for _ in range(10):
            if await rl.acquire("t1", "a1"):
                allowed += 1
        assert allowed == 10

    @pytest.mark.asyncio
    async def test_rate_limit_blocks_over_capacity(self):
        rl = RateLimiter(RateLimitConfig(rate=100, capacity=5))
        allowed = 0
        for _ in range(20):
            if await rl.acquire("t1", "a1"):
                allowed += 1
        assert allowed == 5

    @pytest.mark.asyncio
    async def test_rate_limit_refills_over_time(self):
        rl = RateLimiter(RateLimitConfig(rate=10, capacity=2))
        assert await rl.acquire("t1", "a1") is True
        assert await rl.acquire("t1", "a1") is True
        assert await rl.acquire("t1", "a1") is False
        await asyncio.sleep(0.15)  # wait for ~1.5 tokens
        assert await rl.acquire("t1", "a1") is True


class TestEventClient:
    @pytest.mark.asyncio
    async def test_publish_fallback(self):
        ec = EventClient(EventConfig(stream_name="test.stream"))
        ok = await ec.publish("agent.registered", "t1", "a1", {"foo": "bar"})
        assert ok is True
        events = ec.get_local_events()
        assert len(events) == 1
        assert events[0]["event_type"] == "agent.registered"
        assert events[0]["tenant_id"] == "t1"


class TestHealthClient:
    def test_heartbeat_tracks_consecutive(self):
        hc = HealthClient()
        r1 = hc.report_heartbeat("healthy")
        assert r1["consecutive_successes"] == 1
        r2 = hc.report_heartbeat("unhealthy")
        assert r2["consecutive_failures"] == 1
        assert r2["consecutive_successes"] == 0

    def test_metrics(self):
        hc = HealthClient()
        hc.report_heartbeat("healthy")
        m = hc.metrics()
        assert m["consecutive_successes"] == 1
        assert m["heartbeat_interval"] == 30.0


class TestAgentSDK:
    @pytest.mark.asyncio
    async def test_sdk_initialization(self):
        sdk = AgentSDK(tenant_id="test_t", agent_id="agt_test")
        assert sdk.tenant_id == "test_t"
        assert sdk.agent_id == "agt_test"
        assert sdk._redis_connected is False

    @pytest.mark.asyncio
    async def test_invoke_with_guard_success(self):
        sdk = AgentSDK(
            tenant_id="test_t",
            agent_id="agt_test",
            config=AgentSDKConfig(
                rate_limit=RateLimitConfig(rate=1000, capacity=100),
            ),
        )
        result = await sdk.invoke_with_guard("skill_001", {"input": "hello"})
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_invoke_with_guard_rate_limited(self):
        sdk = AgentSDK(
            tenant_id="test_t",
            agent_id="agt_test",
            config=AgentSDKConfig(
                rate_limit=RateLimitConfig(rate=1, capacity=1),
            ),
        )
        r1 = await sdk.invoke_with_guard("skill_001", {"input": "a"})
        assert r1["success"] is True
        r2 = await sdk.invoke_with_guard("skill_001", {"input": "b"})
        assert r2["success"] is False
        assert r2["error"] == "rate_limit_exceeded"

    @pytest.mark.asyncio
    async def test_publish_event(self):
        sdk = AgentSDK(tenant_id="test_t", agent_id="agt_test")
        ok = await sdk.publish_event("agent.active", {"detail": "started"})
        assert ok is True
        assert len(sdk.event.get_local_events()) == 1

    def test_heartbeat(self):
        sdk = AgentSDK(tenant_id="test_t", agent_id="agt_test")
        result = sdk.heartbeat("healthy")
        assert result["status"] == "healthy"
        assert result["consecutive_successes"] == 1

    def test_metrics(self):
        sdk = AgentSDK(tenant_id="test_t", agent_id="agt_test")
        m = sdk.metrics()
        assert m["tenant_id"] == "test_t"
        assert m["agent_id"] == "agt_test"
        assert "circuit_breaker" in m
        assert "rate_limiter" in m
        assert "health" in m


class TestTraceContext:
    def test_trace_id_contextvar(self):
        assert get_current_trace_id() is None
        set_current_trace_id("abc123")
        assert get_current_trace_id() == "abc123"
