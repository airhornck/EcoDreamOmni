"""Agents API — v4.0 Agent-First Architecture.

Routes:
  GET  /agents              # List active agents with filtering
  GET  /agents/recommend    # AI recommend best agent for platform+format
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.services import agent_function as af

router = APIRouter(prefix="/agents", tags=["agents"])


# ─── Schemas ───

class AgentListItem(BaseModel):
    id: str
    name: str
    role: str
    description: str
    avatar_url: Optional[str] = None
    skills: List[str]
    supported_platforms: List[str]
    supported_formats: List[str]
    config: Dict[str, Any]
    success_rate: float
    recent_tasks_1h: int
    status: str
    created_at: str
    updated_at: str


class AgentRecommendAlternative(BaseModel):
    agent_id: str
    name: str
    confidence: float
    reason: str


class AgentRecommendResponse(BaseModel):
    recommended_agent_id: str
    confidence: float
    reason: str
    alternatives: List[AgentRecommendAlternative]
    matched_capabilities: List[str]


# ─── Helpers ───

def _to_agent_list_item(a: af.AgentInfo) -> AgentListItem:
    return AgentListItem(
        id=a.id,
        name=a.name,
        role=a.role,
        description=a.description,
        avatar_url=a.avatar_url,
        skills=a.skills or [],
        supported_platforms=a.supported_platforms or [],
        supported_formats=a.supported_formats or [],
        config=a.config or {},
        success_rate=a.success_rate,
        recent_tasks_1h=a.recent_tasks_1h,
        status=a.status,
        created_at=a.created_at,
        updated_at=a.updated_at,
    )


def _calculate_recommend_score(
    agent: af.AgentInfo,
    platform: str,
    content_format: str,
    persona_id: Optional[str] = None,
    account_id: Optional[str] = None,
) -> float:
    """4-dimension weighted scoring algorithm.
    
    Weights: global_success_rate 40% + persona_history 30% + load_balance 20% + account_history 10%
    MVP: persona/account history not yet persisted; use neutral baseline.
    """
    score = 0.0

    # 1. Global success rate (40%)
    score += (agent.success_rate or 0.0) * 0.40

    # 2. Persona historical preference (30%) — MVP neutral baseline
    # TODO: Phase 3+ persist task_history per persona and calculate real rate
    score += 0.15  # neutral when no history

    # 3. Load balancing (20%) — lower recent_tasks_1h = higher score
    recent = agent.recent_tasks_1h or 0
    max_concurrent = agent.config.get("max_concurrent_tasks", 20) if agent.config else 20
    load_score = max(0.0, 1.0 - (recent / max_concurrent))
    score += load_score * 0.20

    # 4. Account historical preference (10%) — MVP neutral baseline
    score += 0.05  # neutral when no history

    return round(score, 4)


def _build_recommend_reason(agent: af.AgentInfo, score: float) -> str:
    parts = []
    parts.append(f"{agent.name} 最近24小时成功率 {(agent.success_rate or 0) * 100:.0f}%")
    if (agent.recent_tasks_1h or 0) < 5:
        parts.append("当前负载较低，响应更快")
    return "；".join(parts)


# ─── Routes ───

@router.get("", response_model=Dict[str, Any])
async def list_agents(
    platform: Optional[str] = None,
    format: Optional[str] = None,
    status: Optional[str] = "ACTIVE",
    db: AsyncSession = Depends(get_db),
):
    """List agents with optional platform/format filtering."""
    agents = await af.list_agents_from_db(db, status=status, platform=platform, content_format=format)
    # Sort by success_rate desc
    agents.sort(key=lambda a: a.success_rate or 0, reverse=True)
    return {
        "code": "OK",
        "data": [_to_agent_list_item(a).model_dump() for a in agents],
    }


@router.get("/recommend", response_model=Dict[str, Any])
async def recommend_agent(
    platform: str,
    format: str,
    persona_id: Optional[str] = None,
    account_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Recommend the best agent for given platform+format.
    
    Algorithm: weighted scoring (success_rate 40% + persona pref 30% + load 20% + account pref 10%).
    """
    if not platform or not format:
        raise HTTPException(status_code=400, detail="platform and format are required")

    candidates = await af.list_agents_from_db(
        db, status="ACTIVE", platform=platform, content_format=format
    )

    if not candidates:
        # Fallback to generic agent
        generic = await af.get_agent_by_id(db, "content_forge_generic")
        if generic:
            candidates = [generic]
        else:
            raise HTTPException(status_code=404, detail="No suitable agent found")

    scored = []
    for agent in candidates:
        score = _calculate_recommend_score(
            agent, platform, format, persona_id=persona_id, account_id=account_id
        )
        scored.append((agent, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    top_agent, top_score = scored[0]

    alternatives = []
    for agent, score in scored[1:3]:
        alternatives.append(AgentRecommendAlternative(
            agent_id=agent.id,
            name=agent.name,
            confidence=round(score, 2),
            reason=f"成功率 {(agent.success_rate or 0) * 100:.0f}%",
        ))

    matched_caps = []
    if top_agent.skills:
        # Derive required capabilities from platform+format
        required = _derive_required_capabilities(platform, format)
        matched_caps = list(set(top_agent.skills) & set(required))

    return {
        "code": "OK",
        "data": AgentRecommendResponse(
            recommended_agent_id=top_agent.id,
            confidence=round(top_score, 2),
            reason=_build_recommend_reason(top_agent, top_score),
            alternatives=alternatives,
            matched_capabilities=matched_caps,
        ).model_dump(),
    }


def _derive_required_capabilities(platform: str, content_format: str) -> List[str]:
    """Derive required skill capabilities from platform+format."""
    base = ["text_generate_skill", "keyword_inject_skill"]
    if content_format in ("图文",):
        base += ["rag_retrieval_skill", "cover_generate_skill"]
    elif content_format in ("视频", "视频原创"):
        base += ["video_script_skill", "shot_planning_skill"]
    elif content_format == "视频复刻":
        base += ["video_clone_skill", "style_transfer_skill"]
    elif content_format == "仅文字":
        base += ["content_structural_analysis_skill", "rag_retrieval_skill"]
    if platform == "douyin":
        base += ["hook_optimize_skill"]
    elif platform == "bilibili":
        base += ["part_planning_skill"]
    elif platform == "wechat_channels":
        base += ["readability_optimize_skill"]
    return base
