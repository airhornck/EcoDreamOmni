"""Agent Lifecycle State Machine — v4.0 Phase 2 P2-1b.

Implements the state machine defined in docs/契约与数据/03-核心业务状态流转.md §二.

States: REGISTERED → ACTIVE → DEGRADED / PAUSED / OFFLINE
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class AgentLifecycleState(str, Enum):
    REGISTERED = "registered"
    ACTIVE = "active"
    DEGRADED = "degraded"
    PAUSED = "paused"
    OFFLINE = "offline"


# ─── Illegal transitions (must be intercepted) ───
ILLEGAL_TRANSITIONS: Dict[tuple, str] = {
    (AgentLifecycleState.REGISTERED, AgentLifecycleState.DEGRADED): "未激活不能直接降级",
    (AgentLifecycleState.REGISTERED, AgentLifecycleState.PAUSED): "未激活不能暂停",
    (AgentLifecycleState.REGISTERED, AgentLifecycleState.OFFLINE): "未激活不能离线（应先激活再离线）",
    (AgentLifecycleState.OFFLINE, AgentLifecycleState.ACTIVE): "离线后不能直接激活（需重新注册）",
    (AgentLifecycleState.OFFLINE, AgentLifecycleState.DEGRADED): "离线后不能直接降级",
    (AgentLifecycleState.OFFLINE, AgentLifecycleState.PAUSED): "离线后不能暂停",
    (AgentLifecycleState.PAUSED, AgentLifecycleState.DEGRADED): "暂停中不能降级",
    (AgentLifecycleState.DEGRADED, AgentLifecycleState.PAUSED): "降级中不能暂停（应先恢复再暂停）",
}


class StateTransitionError(Exception):
    """Raised when an illegal state transition is attempted."""


@dataclass
class TransitionRecord:
    from_state: AgentLifecycleState
    to_state: AgentLifecycleState
    trigger: str
    timestamp: str
    reason: str = ""


@dataclass
class StateMachineConfig:
    max_degraded_misses: int = 3  # ACTIVE → DEGRADED
    max_offline_misses: int = 6   # DEGRADED → OFFLINE
    min_recovery_successes: int = 3  # DEGRADED → ACTIVE
    heartbeat_interval_seconds: float = 30.0


class AgentStateMachine:
    """Manage the lifecycle state of a single Agent.

    Usage:
        sm = AgentStateMachine(agent_id="agt_001", tenant_id="t1")
        sm.register()
        sm.activate()
        sm.report_heartbeat(healthy=True)
        ...
    """

    def __init__(
        self,
        agent_id: str,
        tenant_id: str = "default",
        config: Optional[StateMachineConfig] = None,
        on_transition: Optional[Callable[[TransitionRecord], None]] = None,
    ):
        self.agent_id = agent_id
        self.tenant_id = tenant_id
        self.cfg = config or StateMachineConfig()
        self._state = AgentLifecycleState.REGISTERED
        self._history: List[TransitionRecord] = []
        self._consecutive_failures = 0
        self._consecutive_successes = 0
        self._on_transition = on_transition

    # ─── Properties ───

    @property
    def state(self) -> AgentLifecycleState:
        return self._state

    @property
    def can_execute(self) -> bool:
        """Whether the agent can currently execute skills."""
        return self._state == AgentLifecycleState.ACTIVE

    @property
    def can_readonly(self) -> bool:
        """Whether the agent can perform readonly operations."""
        return self._state in (AgentLifecycleState.ACTIVE, AgentLifecycleState.DEGRADED)

    # ─── Core transition logic ───

    def _transition(
        self,
        to_state: AgentLifecycleState,
        trigger: str,
        reason: str = "",
    ) -> None:
        from_state = self._state

        # Check illegal transitions
        key = (from_state, to_state)
        if key in ILLEGAL_TRANSITIONS:
            raise StateTransitionError(
                f"非法状态转换: {from_state.value} → {to_state.value} — {ILLEGAL_TRANSITIONS[key]}"
            )

        self._state = to_state
        record = TransitionRecord(
            from_state=from_state,
            to_state=to_state,
            trigger=trigger,
            timestamp=datetime.now(timezone.utc).isoformat(),
            reason=reason,
        )
        self._history.append(record)

        if self._on_transition:
            self._on_transition(record)

    # ─── Explicit transitions ───

    def register(self) -> None:
        """Initial registration — sets state to REGISTERED."""
        if self._state != AgentLifecycleState.REGISTERED:
            raise StateTransitionError(f"Agent already registered, current state: {self._state.value}")
        self._history.append(TransitionRecord(
            from_state=AgentLifecycleState.REGISTERED,
            to_state=AgentLifecycleState.REGISTERED,
            trigger="register",
            timestamp=datetime.now(timezone.utc).isoformat(),
        ))

    def activate(self, reason: str = "") -> None:
        """Activate the agent (REGISTERED → ACTIVE or DEGRADED → ACTIVE)."""
        if self._state not in (AgentLifecycleState.REGISTERED, AgentLifecycleState.DEGRADED):
            raise StateTransitionError(f"Cannot activate from {self._state.value}")
        self._transition(AgentLifecycleState.ACTIVE, "activate", reason)
        self._consecutive_failures = 0
        self._consecutive_successes = 0

    def degrade(self, reason: str = "") -> None:
        """Manually or automatically degrade (ACTIVE → DEGRADED)."""
        self._transition(AgentLifecycleState.DEGRADED, "degrade", reason)
        self._consecutive_successes = 0

    def pause(self, reason: str = "") -> None:
        """Pause the agent (ACTIVE → PAUSED)."""
        self._transition(AgentLifecycleState.PAUSED, "pause", reason)

    def resume(self, reason: str = "") -> None:
        """Resume from pause (PAUSED → ACTIVE)."""
        self._transition(AgentLifecycleState.ACTIVE, "resume", reason)

    def offline(self, reason: str = "") -> None:
        """Mark agent as offline (any → OFFLINE, except from OFFLINE)."""
        if self._state == AgentLifecycleState.OFFLINE:
            return
        self._transition(AgentLifecycleState.OFFLINE, "offline", reason)

    # ─── Health-based auto transitions ───

    def report_heartbeat(self, healthy: bool = True) -> Dict[str, Any]:
        """Report a heartbeat result. May trigger automatic state transitions.

        Rules:
        - ACTIVE + healthy: increment success counter
        - ACTIVE + unhealthy 3x: auto degrade
        - DEGRADED + healthy 3x: auto activate
        - DEGRADED + unhealthy 6x total: auto offline
        """
        if healthy:
            self._consecutive_successes += 1
            self._consecutive_failures = 0

            if self._state == AgentLifecycleState.DEGRADED:
                if self._consecutive_successes >= self.cfg.min_recovery_successes:
                    self.activate(reason="auto_recovery: consecutive healthy heartbeats")
        else:
            self._consecutive_failures += 1
            self._consecutive_successes = 0

            if self._state == AgentLifecycleState.ACTIVE:
                if self._consecutive_failures >= self.cfg.max_degraded_misses:
                    self.degrade(reason="auto_degrade: consecutive unhealthy heartbeats")
            elif self._state == AgentLifecycleState.DEGRADED:
                if self._consecutive_failures >= self.cfg.max_offline_misses:
                    self.offline(reason="auto_offline: too many unhealthy heartbeats in degraded")

        return {
            "state": self._state.value,
            "consecutive_successes": self._consecutive_successes,
            "consecutive_failures": self._consecutive_failures,
        }

    # ─── Query ───

    def history(self) -> List[TransitionRecord]:
        return list(self._history)

    def metrics(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "tenant_id": self.tenant_id,
            "state": self._state.value,
            "can_execute": self.can_execute,
            "can_readonly": self.can_readonly,
            "consecutive_successes": self._consecutive_successes,
            "consecutive_failures": self._consecutive_failures,
            "transition_count": len(self._history),
        }

    def validate_target_state(self, target: AgentLifecycleState) -> bool:
        """Check if a transition to target state is legal."""
        key = (self._state, target)
        return key not in ILLEGAL_TRANSITIONS
