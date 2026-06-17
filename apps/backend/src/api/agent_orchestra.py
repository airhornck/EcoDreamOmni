"""Agent Orchestra API — multi-agent orchestration."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict

from src.api.auth import get_current_user
from src.services import agent_orchestra


router = APIRouter()


# ─── Agent Schemas ───

class AgentCreate(BaseModel):
    name: str
    role: str
    description: str = ""
    skills: List[str] = []
    config: dict = {}


class AgentOut(BaseModel):
    id: str
    name: str
    role: str
    description: str
    skills: List[str]
    config: dict
    status: str
    created_at: str
    updated_at: str

    model_config = ConfigDict(from_attributes=True)


class BindSkillRequest(BaseModel):
    skill_id: str


# ─── Agent Routes ───

@router.post("/agents", status_code=201, response_model=AgentOut)
def create_agent(data: AgentCreate, user=Depends(get_current_user)):
    agent = agent_orchestra.create_agent(
        name=data.name,
        role=data.role,
        description=data.description,
        skills=data.skills,
        config=data.config,
    )
    return AgentOut(
        id=agent.id,
        name=agent.name,
        role=agent.role,
        description=agent.description,
        skills=agent.skills,
        config=agent.config,
        status=agent.status,
        created_at=agent.created_at,
        updated_at=agent.updated_at,
    )


@router.get("/agents")
def list_agents(user=Depends(get_current_user)):
    agents = agent_orchestra.list_agents()
    return {
        "agents": [
            AgentOut(
                id=a.id,
                name=a.name,
                role=a.role,
                description=a.description,
                skills=a.skills,
                config=a.config,
                status=a.status,
                created_at=a.created_at,
                updated_at=a.updated_at,
            )
            for a in agents
        ]
    }


@router.get("/agents/{agent_id}", response_model=AgentOut)
def get_agent(agent_id: str, user=Depends(get_current_user)):
    agent = agent_orchestra.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return AgentOut(
        id=agent.id,
        name=agent.name,
        role=agent.role,
        description=agent.description,
        skills=agent.skills,
        config=agent.config,
        status=agent.status,
        created_at=agent.created_at,
        updated_at=agent.updated_at,
    )


@router.post("/agents/{agent_id}/skills", status_code=201, response_model=AgentOut)
def bind_skill(agent_id: str, data: BindSkillRequest, user=Depends(get_current_user)):
    agent = agent_orchestra.bind_skill_to_agent(agent_id, data.skill_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return AgentOut(
        id=agent.id,
        name=agent.name,
        role=agent.role,
        description=agent.description,
        skills=agent.skills,
        config=agent.config,
        status=agent.status,
        created_at=agent.created_at,
        updated_at=agent.updated_at,
    )


@router.put("/agents/{agent_id}", response_model=AgentOut)
def update_agent(agent_id: str, data: AgentCreate, user=Depends(get_current_user)):
    agent = agent_orchestra.update_agent(
        agent_id,
        name=data.name,
        role=data.role,
        description=data.description,
        skills=data.skills,
        config=data.config,
    )
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return AgentOut(
        id=agent.id,
        name=agent.name,
        role=agent.role,
        description=agent.description,
        skills=agent.skills,
        config=agent.config,
        status=agent.status,
        created_at=agent.created_at,
        updated_at=agent.updated_at,
    )


@router.delete("/agents/{agent_id}", status_code=204)
def delete_agent(agent_id: str, user=Depends(get_current_user)):
    deleted = agent_orchestra.delete_agent(agent_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Agent not found")
    return None



