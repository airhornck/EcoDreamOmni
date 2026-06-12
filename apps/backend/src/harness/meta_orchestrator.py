"""Meta-Orchestrator — v4.0 Phase 2 P2-2.

只决策不执行。包含：
- IntentClassifier: 意图分类（LLM + 规则混合）
- TaskDecomposer: 任务分解（SOP 模板匹配）
- DynamicRouter: 动态路由（选择编排模式）
- StateCoordinator: Blackboard 共享状态

架构红线:
- §2.1 Agent 禁 DB: 不直接操作数据库
- §2.5 LLMHub 路由: LLM 调用通过 LLM Hub（MVP 规则回退）
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


# ═══════════════════════════════════════════════════════
# 1. Intent Classification
# ═══════════════════════════════════════════════════════

class IntentType(str, Enum):
    CONTENT_CREATION = "content_creation"
    DATA_ANALYSIS = "data_analysis"
    ACCOUNT_MANAGEMENT = "account_management"
    SYSTEM_QUERY = "system_query"
    UNKNOWN = "unknown"


@dataclass
class IntentResult:
    intent: IntentType
    confidence: float
    sub_intents: List[str] = field(default_factory=list)
    raw_analysis: str = ""


class IntentClassifier:
    """Hybrid intent classifier: rule-based primary, LLM fallback."""

    _RULES: List[tuple] = [
        # (keywords, intent, sub_intents)
        ("写 生成 创作 文案 笔记 脚本 内容".split(), IntentType.CONTENT_CREATION, ["draft", "image"]),
        ("分析 数据 战报 报告 趋势 统计 诊断".split(), IntentType.DATA_ANALYSIS, ["battle_report", "trend"]),
        ("发布 排期 账号 登录 注册 配置 管理".split(), IntentType.ACCOUNT_MANAGEMENT, ["publish", "schedule"]),
        ("怎么 如何 帮助 什么 查询 状态".split(), IntentType.SYSTEM_QUERY, ["help", "status"]),
    ]

    def classify(self, query: str, context: Optional[Dict[str, Any]] = None) -> IntentResult:
        query_lower = query.lower()
        scores: Dict[IntentType, float] = {intent: 0.0 for intent in IntentType}

        for keywords, intent, sub_intents in self._RULES:
            matched = sum(1 for kw in keywords if kw in query_lower)
            if matched > 0:
                scores[intent] = matched / len(keywords)

        best_intent = max(scores, key=lambda k: scores[k])
        best_score = scores[best_intent]

        if best_score == 0.0:
            return IntentResult(
                intent=IntentType.UNKNOWN,
                confidence=0.0,
                raw_analysis="未能匹配到已知意图",
            )

        # Find sub_intents for the best match
        sub_intents = []
        for keywords, intent, subs in self._RULES:
            if intent == best_intent:
                sub_intents = subs
                break

        confidence = min(1.0, best_score * 2.0)  # scale up
        return IntentResult(
            intent=best_intent,
            confidence=round(confidence, 2),
            sub_intents=sub_intents,
            raw_analysis=f"Rule-based match: {best_intent.value} (score={best_score:.2f})",
        )


# ═══════════════════════════════════════════════════════
# 2. Task Decomposition (SOP Templates)
# ═══════════════════════════════════════════════════════

@dataclass
class TodoItem:
    id: str
    description: str
    skill_id: str
    depends_on: List[str] = field(default_factory=list)
    estimated_duration_ms: int = 5000


@dataclass
class DecomposeResult:
    todos: List[TodoItem]
    estimated_duration_ms: int
    sop_template_id: str


_SOP_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "sop_content_v1": {
        "todos": [
            {"description": "研究主题关键词", "skill_id": "research", "depends_on": []},
            {"description": "生成文案草稿", "skill_id": "draft_writer", "depends_on": ["td_1"]},
            {"description": "合规检查", "skill_id": "compliance_check", "depends_on": ["td_2"]},
            {"description": "生成配图建议", "skill_id": "image_suggester", "depends_on": ["td_2"]},
        ],
    },
    "sop_analysis_v1": {
        "todos": [
            {"description": "收集互动数据", "skill_id": "engagement_collect", "depends_on": []},
            {"description": "生成战报", "skill_id": "battle_report_generate", "depends_on": ["td_1"]},
        ],
    },
    "sop_account_v1": {
        "todos": [
            {"description": "检查账号健康", "skill_id": "account_health", "depends_on": []},
            {"description": "创建发布计划", "skill_id": "publish_scheduler", "depends_on": ["td_1"]},
        ],
    },
}

_INTENT_TO_SOP: Dict[IntentType, str] = {
    IntentType.CONTENT_CREATION: "sop_content_v1",
    IntentType.DATA_ANALYSIS: "sop_analysis_v1",
    IntentType.ACCOUNT_MANAGEMENT: "sop_account_v1",
}


class TaskDecomposer:
    """Decompose intent into executable todos using SOP templates."""

    def decompose(
        self,
        intent: IntentType,
        context: Optional[Dict[str, Any]] = None,
        sop_template_id: Optional[str] = None,
    ) -> DecomposeResult:
        template_id = sop_template_id or _INTENT_TO_SOP.get(intent, "sop_content_v1")
        template = _SOP_TEMPLATES.get(template_id, _SOP_TEMPLATES["sop_content_v1"])

        todos = []
        total_duration = 0
        for i, td in enumerate(template["todos"], start=1):
            todo_id = f"td_{i}"
            todos.append(TodoItem(
                id=todo_id,
                description=td["description"],
                skill_id=td["skill_id"],
                depends_on=td.get("depends_on", []),
                estimated_duration_ms=td.get("estimated_duration_ms", 5000),
            ))
            total_duration += td.get("estimated_duration_ms", 5000)

        return DecomposeResult(
            todos=todos,
            estimated_duration_ms=total_duration,
            sop_template_id=template_id,
        )


# ═══════════════════════════════════════════════════════
# 3. Dynamic Router
# ═══════════════════════════════════════════════════════

class OrchestrationMode(str, Enum):
    PIPELINE = "PIPELINE"
    SWARM = "SWARM"
    DYNAMIC = "DYNAMIC"
    DIRECT = "DIRECT"


@dataclass
class RouteResult:
    mode: OrchestrationMode
    reason: str
    allowed_modes: List[str] = field(default_factory=list)


class DynamicRouter:
    """Select orchestration mode based on task characteristics."""

    def route(
        self,
        intent: IntentType,
        todo_count: int,
        priority: str = "normal",
        requires_realtime: bool = False,
    ) -> RouteResult:
        allowed = [m.value for m in OrchestrationMode]

        # Direct mode: simple system query or single todo
        if intent == IntentType.SYSTEM_QUERY or todo_count <= 1:
            return RouteResult(
                mode=OrchestrationMode.DIRECT,
                reason="简单查询或单任务，适合直达模式",
                allowed_modes=allowed,
            )

        # Swarm mode: many independent todos
        if todo_count >= 5 and not requires_realtime:
            return RouteResult(
                mode=OrchestrationMode.SWARM,
                reason="大量独立子任务，适合蜂群并行模式",
                allowed_modes=allowed,
            )

        # Dynamic mode: high priority or realtime requirements
        if priority == "high" or requires_realtime:
            return RouteResult(
                mode=OrchestrationMode.DYNAMIC,
                reason="高优先级或实时需求，需要动态调整",
                allowed_modes=allowed,
            )

        # Default: Pipeline
        return RouteResult(
            mode=OrchestrationMode.PIPELINE,
            reason="顺序依赖任务，适合 Pipeline 模式",
            allowed_modes=allowed,
        )


# ═══════════════════════════════════════════════════════
# 4. State Coordinator (Blackboard)
# ═══════════════════════════════════════════════════════

@dataclass
class BlackboardEntry:
    key: str
    value: Any
    updated_at: str
    updated_by: str


class StateCoordinator:
    """Blackboard pattern for shared state across agents."""

    def __init__(self):
        self._boards: Dict[str, Dict[str, BlackboardEntry]] = {}
        self._agents: Dict[str, List[str]] = {}  # session_id -> agent_ids

    def create_session(self, session_id: Optional[str] = None) -> str:
        sid = session_id or f"sess_{secrets.token_urlsafe(8)}"
        self._boards[sid] = {}
        self._agents[sid] = []
        return sid

    def write(
        self,
        session_id: str,
        key: str,
        value: Any,
        agent_id: str = "orchestrator",
    ) -> None:
        if session_id not in self._boards:
            self.create_session(session_id)
        self._boards[session_id][key] = BlackboardEntry(
            key=key,
            value=value,
            updated_at=datetime.now(timezone.utc).isoformat(),
            updated_by=agent_id,
        )

    def read(self, session_id: str, key: str) -> Optional[BlackboardEntry]:
        return self._boards.get(session_id, {}).get(key)

    def read_all(self, session_id: str) -> Dict[str, BlackboardEntry]:
        return dict(self._boards.get(session_id, {}))

    def register_agent(self, session_id: str, agent_id: str) -> None:
        if session_id not in self._agents:
            self._agents[session_id] = []
        if agent_id not in self._agents[session_id]:
            self._agents[session_id].append(agent_id)

    def get_agents(self, session_id: str) -> List[str]:
        return list(self._agents.get(session_id, []))

    def snapshot(self, session_id: str) -> Dict[str, Any]:
        entries = {
            k: {"value": v.value, "updated_at": v.updated_at}
            for k, v in self._boards.get(session_id, {}).items()
        }
        return {
            "session_id": session_id,
            "entries": entries,
            "agents": self.get_agents(session_id),
        }


# ═══════════════════════════════════════════════════════
# 5. MetaOrchestrator — Main Entry
# ═══════════════════════════════════════════════════════

@dataclass
class OrchestrateResult:
    session_id: str
    intent: IntentResult
    decomposition: DecomposeResult
    route: RouteResult
    blackboard: Dict[str, Any]


class MetaOrchestrator:
    """Meta-Orchestrator facade — compose all sub-components."""

    def __init__(self):
        self.classifier = IntentClassifier()
        self.decomposer = TaskDecomposer()
        self.router = DynamicRouter()
        self.coordinator = StateCoordinator()

    def orchestrate(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> OrchestrateResult:
        """Full orchestration pipeline: classify → decompose → route → coordinate."""
        ctx = context or {}

        # 1. Classify intent
        intent_result = self.classifier.classify(query, ctx)

        # 2. Create or reuse session
        sid = session_id or self.coordinator.create_session()

        # 3. Write intent to blackboard
        self.coordinator.write(sid, "intent", {
            "type": intent_result.intent.value,
            "confidence": intent_result.confidence,
            "sub_intents": intent_result.sub_intents,
        })

        # 4. Decompose into todos
        decompose_result = self.decomposer.decompose(
            intent=intent_result.intent,
            context=ctx,
        )
        self.coordinator.write(sid, "todos", [
            {"id": t.id, "description": t.description, "skill_id": t.skill_id}
            for t in decompose_result.todos
        ])

        # 5. Route
        route_result = self.router.route(
            intent=intent_result.intent,
            todo_count=len(decompose_result.todos),
            priority=ctx.get("priority", "normal"),
            requires_realtime=ctx.get("requires_realtime", False),
        )
        self.coordinator.write(sid, "mode", route_result.mode.value)

        return OrchestrateResult(
            session_id=sid,
            intent=intent_result,
            decomposition=decompose_result,
            route=route_result,
            blackboard=self.coordinator.snapshot(sid),
        )
