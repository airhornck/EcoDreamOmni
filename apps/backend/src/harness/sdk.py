"""Agent SDK — v4.0 Phase 2 P2-1a.

统一 Agent 基础设施调用层：重试 / 熔断 / 限流 / 认证 / 日志 / 追踪 / 事件 / 健康。

使用方式:
    sdk = AgentSDK(tenant_id="t1", agent_id="agt_xxx")
    result = await sdk.invoke_with_guard(
        skill_id="skill_001",
        context={"input": "hello"},
    )

架构红线:
- §2.1 Agent 禁 DB: SDK 不直接操作数据库，只调用 Function API
- §2.2 EventBus 优先: 状态变更通过 Redis Streams 发布
- §2.5 LLMHub 路由: SDK 内部 LLM 调用走 LLM Hub
"""

from __future__ import annotations

import asyncio
import functools
import secrets
import time
from contextlib import asynccontextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional, TypeVar

import structlog
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
# ─── Redis 可选导入（未安装/未连接时回退内存实现） ───
try:
    import redis.asyncio as aioredis

    _HAS_REDIS = True
except ImportError:
    aioredis = None  # type: ignore
    _HAS_REDIS = False

from src.core.security import decode_token

T = TypeVar("T")

# ─── ContextVar for distributed tracing ───
_trace_ctx: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)


def get_current_trace_id() -> Optional[str]:
    return _trace_ctx.get()


def set_current_trace_id(trace_id: str) -> None:
    _trace_ctx.set(trace_id)


# ═══════════════════════════════════════════════════════
# 1. Retry Policy
# ═══════════════════════════════════════════════════════

RETRYABLE_EXCEPTIONS = (ConnectionError, TimeoutError, asyncio.TimeoutError)


@dataclass
class RetryConfig:
    max_retries: int = 3
    backoff_factor: float = 2.0
    max_wait: float = 60.0
    retryable_exceptions: tuple = RETRYABLE_EXCEPTIONS


async def _sleep_backoff(attempt: int, factor: float, max_wait: float) -> None:
    wait = min(factor * (2**attempt), max_wait)
    await asyncio.sleep(wait)


def with_retry(config: Optional[RetryConfig] = None):
    """Decorator: exponential backoff retry for async functions."""
    cfg = config or RetryConfig()

    def decorator(fn: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs) -> T:  # type: ignore
            last_exc: Optional[Exception] = None
            for attempt in range(cfg.max_retries + 1):
                try:
                    return await fn(*args, **kwargs)
                except cfg.retryable_exceptions as exc:
                    last_exc = exc
                    if attempt < cfg.max_retries:
                        await _sleep_backoff(attempt, cfg.backoff_factor, cfg.max_wait)
                    else:
                        raise last_exc
            assert last_exc is not None
            raise last_exc  # pragma: no cover

        return wrapper

    return decorator


# ═══════════════════════════════════════════════════════
# 2. Async Circuit Breaker
# ═══════════════════════════════════════════════════════

@dataclass
class CircuitBreakerConfig:
    fail_max: int = 5
    reset_timeout: float = 30.0


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open."""


class AsyncCircuitBreaker:
    """Lightweight async circuit breaker (states: closed / open / half-open)."""

    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.cfg = config or CircuitBreakerConfig()
        self._state = "closed"  # closed | open | half-open
        self._failures = 0
        self._successes = 0
        self._last_failure_time: Optional[float] = None
        self._total_success = 0
        self._total_failure = 0

    @property
    def state(self) -> str:
        return self._state

    def _trip(self) -> None:
        self._state = "open"
        self._last_failure_time = time.time()

    def _reset(self) -> None:
        self._state = "closed"
        self._failures = 0
        self._successes = 0
        self._last_failure_time = None

    def _try_half_open(self) -> bool:
        if self._state == "open" and self._last_failure_time:
            if time.time() - self._last_failure_time >= self.cfg.reset_timeout:
                self._state = "half-open"
                self._failures = 0
                self._successes = 0
                return True
        return False

    async def call(self, fn: Callable[..., Awaitable[T]], *args, **kwargs) -> T:
        if self._state == "open":
            if not self._try_half_open():
                raise CircuitBreakerError(f"Circuit '{self.name}' is OPEN")

        try:
            result = await fn(*args, **kwargs)
            self._successes += 1
            self._total_success += 1
            if self._state == "half-open" and self._successes >= 1:
                self._reset()
            return result
        except Exception as exc:
            self._failures += 1
            self._total_failure += 1
            if self._state in ("closed", "half-open") and self._failures >= self.cfg.fail_max:
                self._trip()
            raise exc

    def metrics(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "state": self._state,
            "total_success": self._total_success,
            "total_failure": self._total_failure,
            "fail_max": self.cfg.fail_max,
            "reset_timeout": self.cfg.reset_timeout,
        }


# Backward-compatible alias
CircuitBreakerWrapper = AsyncCircuitBreaker


# ═══════════════════════════════════════════════════════
# 3. Token Bucket Rate Limiter
# ═══════════════════════════════════════════════════════

@dataclass
class RateLimitConfig:
    rate: float = 10.0  # tokens per second
    capacity: float = 100.0  # max burst
    key_prefix: str = "ratelimit"


class RateLimiter:
    """Token bucket rate limiter with Redis or in-memory fallback."""

    def __init__(self, config: Optional[RateLimitConfig] = None, redis_client=None):
        self.cfg = config or RateLimitConfig()
        self._redis = redis_client
        self._local_buckets: Dict[str, Dict[str, float]] = {}  # fallback

    def _key(self, tenant_id: str, agent_id: str, model: str = "default") -> str:
        return f"{self.cfg.key_prefix}:{tenant_id}:{agent_id}:{model}"

    async def acquire(
        self,
        tenant_id: str,
        agent_id: str,
        model: str = "default",
        tokens: float = 1.0,
    ) -> bool:
        key = self._key(tenant_id, agent_id, model)
        if self._redis:
            return await self._acquire_redis(key, tokens)
        return self._acquire_local(key, tokens)

    async def _acquire_redis(self, key: str, tokens: float) -> bool:
        now = time.time()
        pipe = self._redis.pipeline()
        pipe.hmget(key, ["tokens", "last_update"])
        results = await pipe.execute()
        bucket_info = results[0]

        current_tokens = float(bucket_info[0]) if bucket_info and bucket_info[0] else self.cfg.capacity
        last_update = float(bucket_info[1]) if bucket_info and bucket_info[1] else now

        elapsed = now - last_update
        new_tokens = min(self.cfg.capacity, current_tokens + elapsed * self.cfg.rate)

        if new_tokens >= tokens:
            new_tokens -= tokens
            await self._redis.hset(key, mapping={"tokens": str(new_tokens), "last_update": str(now)})
            await self._redis.expire(key, 300)
            return True
        return False

    def _acquire_local(self, key: str, tokens: float) -> bool:
        now = time.time()
        bucket = self._local_buckets.get(key, {"tokens": self.cfg.capacity, "last_update": now})
        elapsed = now - bucket["last_update"]
        bucket["tokens"] = min(self.cfg.capacity, bucket["tokens"] + elapsed * self.cfg.rate)
        bucket["last_update"] = now

        if bucket["tokens"] >= tokens:
            bucket["tokens"] -= tokens
            self._local_buckets[key] = bucket
            return True
        return False

    def metrics(self, tenant_id: str, agent_id: str, model: str = "default") -> Dict[str, Any]:
        key = self._key(tenant_id, agent_id, model)
        bucket = self._local_buckets.get(key, {"tokens": self.cfg.capacity})
        return {
            "key": key,
            "tokens_remaining": bucket.get("tokens", self.cfg.capacity),
            "capacity": self.cfg.capacity,
            "rate": self.cfg.rate,
        }


# ═══════════════════════════════════════════════════════
# 4. Auth Client (JWT auto-refresh)
# ═══════════════════════════════════════════════════════

@dataclass
class AuthConfig:
    access_token: str = ""
    refresh_token: str = ""
    auto_refresh: bool = True
    refresh_margin_seconds: int = 300  # refresh 5 min before expiry


class AuthClient:
    """Lightweight JWT wrapper with expiry checking."""

    def __init__(self, config: AuthConfig):
        self.cfg = config
        self._lock = asyncio.Lock()

    def is_token_expired(self) -> bool:
        if not self.cfg.access_token:
            return True
        payload = decode_token(self.cfg.access_token)
        if not payload:
            return True
        exp = payload.get("exp")
        if not exp:
            return False
        return time.time() > (exp - self.cfg.refresh_margin_seconds)

    async def get_valid_token(self) -> str:
        async with self._lock:
            if self.is_token_expired() and self.cfg.auto_refresh and self.cfg.refresh_token:
                # MVP: refresh not implemented; production would call auth service
                pass
            return self.cfg.access_token


# ═══════════════════════════════════════════════════════
# 5. Structured Logger
# ═══════════════════════════════════════════════════════


def _build_logger(tenant_id: str, agent_id: str) -> Any:
    return structlog.get_logger(
        tenant_id=tenant_id,
        agent_id=agent_id,
    )


# ═══════════════════════════════════════════════════════
# 6. OpenTelemetry Tracer
# ═══════════════════════════════════════════════════════

_tracer = trace.get_tracer("agent-sdk")


@asynccontextmanager
async def sdk_span(name: str, attributes: Optional[Dict[str, Any]] = None):
    with _tracer.start_as_current_span(name) as span:
        if attributes:
            for k, v in attributes.items():
                span.set_attribute(k, v)
        try:
            yield span
            span.set_status(Status(StatusCode.OK))
        except Exception as exc:
            span.set_status(Status(StatusCode.ERROR, str(exc)))
            span.record_exception(exc)
            raise


# ═══════════════════════════════════════════════════════
# 7. Event Client (Redis Streams)
# ═══════════════════════════════════════════════════════

@dataclass
class EventConfig:
    stream_name: str = "agent.lifecycle"
    max_len: int = 10000


class EventClient:
    """Publish agent lifecycle events to Redis Streams."""

    def __init__(self, config: Optional[EventConfig] = None, redis_client=None):
        self.cfg = config or EventConfig()
        self._redis = redis_client
        self._local_events: List[Dict[str, Any]] = []  # fallback

    async def publish(
        self,
        event_type: str,
        tenant_id: str,
        agent_id: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> bool:
        msg = {
            "event_type": event_type,
            "tenant_id": tenant_id,
            "agent_id": agent_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "trace_id": get_current_trace_id() or secrets.token_hex(8),
            "payload": payload or {},
        }
        if self._redis:
            try:
                await self._redis.xadd(
                    self.cfg.stream_name,
                    {"data": str(msg)},
                    maxlen=self.cfg.max_len,
                    approximate=True,
                )
                return True
            except Exception:
                return False
        self._local_events.append(msg)
        return True

    def get_local_events(self) -> List[Dict[str, Any]]:
        return list(self._local_events)


# ═══════════════════════════════════════════════════════
# 8. Health Client
# ═══════════════════════════════════════════════════════

@dataclass
class HealthConfig:
    heartbeat_interval: float = 30.0
    timeout: float = 5.0


class HealthClient:
    """Agent health reporting."""

    def __init__(self, config: Optional[HealthConfig] = None):
        self.cfg = config or HealthConfig()
        self._last_heartbeat: Optional[str] = None
        self._consecutive_failures = 0
        self._consecutive_successes = 0

    def report_heartbeat(self, status: str = "healthy") -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        self._last_heartbeat = now
        if status == "healthy":
            self._consecutive_successes += 1
            self._consecutive_failures = 0
        else:
            self._consecutive_failures += 1
            self._consecutive_successes = 0
        return {
            "status": status,
            "timestamp": now,
            "consecutive_successes": self._consecutive_successes,
            "consecutive_failures": self._consecutive_failures,
        }

    def metrics(self) -> Dict[str, Any]:
        return {
            "last_heartbeat": self._last_heartbeat,
            "consecutive_successes": self._consecutive_successes,
            "consecutive_failures": self._consecutive_failures,
            "heartbeat_interval": self.cfg.heartbeat_interval,
        }


# ═══════════════════════════════════════════════════════
# AgentSDK — Main Entry
# ═══════════════════════════════════════════════════════

@dataclass
class AgentSDKConfig:
    retry: Optional[RetryConfig] = None
    circuit_breaker: Optional[CircuitBreakerConfig] = None
    rate_limit: Optional[RateLimitConfig] = None
    auth: Optional[AuthConfig] = None
    event: Optional[EventConfig] = None
    health: Optional[HealthConfig] = None
    redis_url: Optional[str] = None


class AgentSDK:
    """Unified Agent SDK — v4.0 Phase 2.

    Provides retry, circuit breaker, rate limiting, auth, logging,
    tracing, event publishing, and health reporting.
    """

    def __init__(
        self,
        tenant_id: str,
        agent_id: str,
        config: Optional[AgentSDKConfig] = None,
    ):
        self.tenant_id = tenant_id
        self.agent_id = agent_id
        self.cfg = config or AgentSDKConfig()

        # Lazy redis init
        self._redis: Any = None
        self._redis_connected = False

        # Sub-components
        self.retry_cfg = self.cfg.retry or RetryConfig()
        self.circuit = CircuitBreakerWrapper(
            name=f"cb:{tenant_id}:{agent_id}",
            config=self.cfg.circuit_breaker,
        )
        self.rate_limiter = RateLimiter(
            config=self.cfg.rate_limit,
            redis_client=None,  # lazy connect
        )
        self.auth = AuthClient(self.cfg.auth or AuthConfig())
        self.logger = _build_logger(tenant_id, agent_id)
        self.event = EventClient(
            config=self.cfg.event,
            redis_client=None,  # lazy connect
        )
        self.health = HealthClient(self.cfg.health)

    async def connect(self) -> bool:
        """Connect to Redis if URL provided."""
        if self._redis_connected:
            return True
        if self.cfg.redis_url and _HAS_REDIS and aioredis:
            try:
                self._redis = await aioredis.from_url(self.cfg.redis_url)
                await self._redis.ping()
                self._redis_connected = True
                self.rate_limiter._redis = self._redis
                self.event._redis = self._redis
                self.logger.info("redis_connected", url=self.cfg.redis_url)
                return True
            except Exception as exc:
                self.logger.warning("redis_connect_failed", error=str(exc))
                return False
        return False

    async def disconnect(self) -> None:
        if self._redis:
            await self._redis.close()
            self._redis = None
            self._redis_connected = False

    # ─── High-level guarded invocation ───

    async def invoke_with_guard(
        self,
        skill_id: str,
        context: Dict[str, Any],
        model: str = "default",
    ) -> Dict[str, Any]:
        """Invoke a skill with retry + circuit breaker + rate limit + trace.

        Pipeline:
            1. Rate limit check
            2. Trace span start
            3. Circuit breaker call
            4. Retry wrapper inside
            5. Trace span end
        """
        trace_id = get_current_trace_id() or secrets.token_hex(8)
        set_current_trace_id(trace_id)

        # 1. Rate limit
        allowed = await self.rate_limiter.acquire(self.tenant_id, self.agent_id, model)
        if not allowed:
            self.logger.warning("rate_limit_exceeded", skill_id=skill_id, model=model)
            return {"success": False, "error": "rate_limit_exceeded", "retry_after": 1}

        # 2-5. Trace + Circuit + Retry
        async with sdk_span(
            "agent.invoke",
            {
                "tenant_id": self.tenant_id,
                "agent_id": self.agent_id,
                "skill_id": skill_id,
                "model": model,
            },
        ):
            try:
                result = await self.circuit.call(
                    self._do_invoke,
                    skill_id,
                    context,
                )
                self.logger.info(
                    "invoke_success",
                    skill_id=skill_id,
                    elapsed_ms=result.get("elapsed_ms"),
                )
                return result
            except Exception as exc:
                self.logger.error("invoke_failed", skill_id=skill_id, error=str(exc))
                return {"success": False, "error": str(exc), "error_type": type(exc).__name__}

    @with_retry()
    async def _do_invoke(
        self,
        skill_id: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Actual invocation — to be overridden or routed to SkillHub."""
        start = time.time()
        # MVP: placeholder — production routes through SkillHub
        elapsed_ms = int((time.time() - start) * 1000)
        return {
            "success": True,
            "skill_id": skill_id,
            "result": {"placeholder": True},
            "elapsed_ms": elapsed_ms,
        }

    # ─── Event publishing ───

    async def publish_event(
        self,
        event_type: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> bool:
        return await self.event.publish(
            event_type=event_type,
            tenant_id=self.tenant_id,
            agent_id=self.agent_id,
            payload=payload,
        )

    # ─── Heartbeat ───

    def heartbeat(self, status: str = "healthy") -> Dict[str, Any]:
        return self.health.report_heartbeat(status)

    # ─── Metrics ───

    def metrics(self) -> Dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "agent_id": self.agent_id,
            "circuit_breaker": self.circuit.metrics(),
            "rate_limiter": self.rate_limiter.metrics(self.tenant_id, self.agent_id),
            "health": self.health.metrics(),
            "redis_connected": self._redis_connected,
        }
