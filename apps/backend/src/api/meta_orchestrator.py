"""Meta-Orchestrator API — v4.0 Phase 2 P2-2.

Aligned with docs/契约与数据/01-API接口契约.md §4.3
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.harness.meta_orchestrator import MetaOrchestrator

router = APIRouter(prefix="/orchestrator", tags=["meta-orchestrator"])

_orchestrator = MetaOrchestrator()


# ─── Schemas ───

class ClassifyIntentRequest(BaseModel):
    query: str
    context: Optional[Dict[str, Any]] = None


class ClassifyIntentResponse(BaseModel):
    intent: str
    confidence: float
    sub_intents: List[str] = []
    raw_analysis: str = ""


class DecomposeRequest(BaseModel):
    intent: str
    context: Optional[Dict[str, Any]] = None
    sop_template_id: Optional[str] = None


class TodoItemOut(BaseModel):
    id: str
    description: str
    skill_id: str
    depends_on: List[str] = []


class DecomposeResponse(BaseModel):
    todos: List[TodoItemOut]
    estimated_duration_ms: int
    sop_template_id: str


class RouteRequest(BaseModel):
    intent: str
    todo_count: int = Field(1, ge=1)
    priority: str = "normal"
    requires_realtime: bool = False


class RouteResponse(BaseModel):
    mode: str
    reason: str
    allowed_modes: List[str] = []


class BlackboardEntryOut(BaseModel):
    value: Any
    updated_at: str


class BlackboardResponse(BaseModel):
    session_id: str
    entries: Dict[str, BlackboardEntryOut]
    agents: List[str]


class OrchestrateRequest(BaseModel):
    query: str
    context: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None


class OrchestrateResponse(BaseModel):
    session_id: str
    intent: ClassifyIntentResponse
    todos: List[TodoItemOut]
    route: RouteResponse
    blackboard: Dict[str, Any]


# ─── Routes ───

@router.post("/intent", response_model=ClassifyIntentResponse)
async def classify_intent(req: ClassifyIntentRequest):
    """Classify user intent."""
    result = _orchestrator.classifier.classify(req.query, req.context)
    return ClassifyIntentResponse(
        intent=result.intent.value,
        confidence=result.confidence,
        sub_intents=result.sub_intents,
        raw_analysis=result.raw_analysis,
    )


@router.post("/decompose", response_model=DecomposeResponse)
async def decompose_task(req: DecomposeRequest):
    """Decompose intent into executable todos."""
    from src.harness.meta_orchestrator import IntentType

    intent = IntentType(req.intent)
    result = _orchestrator.decomposer.decompose(
        intent=intent,
        context=req.context,
        sop_template_id=req.sop_template_id,
    )
    return DecomposeResponse(
        todos=[
            TodoItemOut(
                id=t.id,
                description=t.description,
                skill_id=t.skill_id,
                depends_on=t.depends_on,
            )
            for t in result.todos
        ],
        estimated_duration_ms=result.estimated_duration_ms,
        sop_template_id=result.sop_template_id,
    )


@router.post("/route", response_model=RouteResponse)
async def route_task(req: RouteRequest):
    """Select orchestration mode."""
    from src.harness.meta_orchestrator import IntentType

    intent = IntentType(req.intent)
    result = _orchestrator.router.route(
        intent=intent,
        todo_count=req.todo_count,
        priority=req.priority,
        requires_realtime=req.requires_realtime,
    )
    return RouteResponse(
        mode=result.mode.value,
        reason=result.reason,
        allowed_modes=result.allowed_modes,
    )


@router.get("/blackboard/{session_id}", response_model=BlackboardResponse)
async def get_blackboard(session_id: str):
    """Query Blackboard shared state."""
    snapshot = _orchestrator.coordinator.snapshot(session_id)
    entries = {
        k: BlackboardEntryOut(value=v["value"], updated_at=v["updated_at"])
        for k, v in snapshot["entries"].items()
    }
    return BlackboardResponse(
        session_id=snapshot["session_id"],
        entries=entries,
        agents=snapshot["agents"],
    )


@router.post("/orchestrate", response_model=OrchestrateResponse)
async def orchestrate(req: OrchestrateRequest):
    """Full orchestration pipeline: classify → decompose → route → coordinate."""
    result = _orchestrator.orchestrate(
        query=req.query,
        context=req.context,
        session_id=req.session_id,
    )
    return OrchestrateResponse(
        session_id=result.session_id,
        intent=ClassifyIntentResponse(
            intent=result.intent.intent.value,
            confidence=result.intent.confidence,
            sub_intents=result.intent.sub_intents,
            raw_analysis=result.intent.raw_analysis,
        ),
        todos=[
            TodoItemOut(
                id=t.id,
                description=t.description,
                skill_id=t.skill_id,
                depends_on=t.depends_on,
            )
            for t in result.decomposition.todos
        ],
        route=RouteResponse(
            mode=result.route.mode.value,
            reason=result.route.reason,
            allowed_modes=result.route.allowed_modes,
        ),
        blackboard=result.blackboard,
    )
