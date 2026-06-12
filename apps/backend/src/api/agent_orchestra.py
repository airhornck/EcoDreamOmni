"""Agent Orchestra API — multi-agent orchestration."""

from typing import List, Optional
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


# ─── Workflow Schemas ───

class WorkflowStepIn(BaseModel):
    agent_id: str
    name: str
    input_from: str = "trigger"
    output_to: str = "result"


class WorkflowCreate(BaseModel):
    name: str
    description: str = ""
    steps: List[WorkflowStepIn] = []


class WorkflowStepOut(BaseModel):
    agent_id: str
    name: str
    input_from: str
    output_to: str


class WorkflowOut(BaseModel):
    id: str
    name: str
    description: str
    steps: List[WorkflowStepOut]
    status: str
    created_at: str

    model_config = ConfigDict(from_attributes=True)


# ─── Pipeline Schemas ───

class PipelineCreate(BaseModel):
    workflow_id: str
    context: dict = {}


class PipelineOut(BaseModel):
    id: str
    workflow_id: str
    status: str
    current_step: int
    context: dict
    results: list
    created_at: str
    updated_at: str

    model_config = ConfigDict(from_attributes=True)


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


# ─── Workflow Routes ───

@router.post("/workflows", status_code=201, response_model=WorkflowOut)
def create_workflow(data: WorkflowCreate, user=Depends(get_current_user)):
    steps = [s.model_dump() for s in data.steps]
    wf = agent_orchestra.create_workflow(
        name=data.name,
        description=data.description,
        steps=steps,
    )
    return WorkflowOut(
        id=wf.id,
        name=wf.name,
        description=wf.description,
        steps=[
            WorkflowStepOut(
                agent_id=s.agent_id,
                name=s.name,
                input_from=s.input_from,
                output_to=s.output_to,
            )
            for s in wf.steps
        ],
        status=wf.status,
        created_at=wf.created_at,
    )


@router.get("/workflows")
def list_workflows(user=Depends(get_current_user)):
    wfs = agent_orchestra.list_workflows()
    return {
        "workflows": [
            WorkflowOut(
                id=w.id,
                name=w.name,
                description=w.description,
                steps=[
                    WorkflowStepOut(
                        agent_id=s.agent_id,
                        name=s.name,
                        input_from=s.input_from,
                        output_to=s.output_to,
                    )
                    for s in w.steps
                ],
                status=w.status,
                created_at=w.created_at,
            )
            for w in wfs
        ]
    }


@router.get("/workflows/{workflow_id}", response_model=WorkflowOut)
def get_workflow(workflow_id: str, user=Depends(get_current_user)):
    wf = agent_orchestra.get_workflow(workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return WorkflowOut(
        id=wf.id,
        name=wf.name,
        description=wf.description,
        steps=[
            WorkflowStepOut(
                agent_id=s.agent_id,
                name=s.name,
                input_from=s.input_from,
                output_to=s.output_to,
            )
            for s in wf.steps
        ],
        status=wf.status,
        created_at=wf.created_at,
    )


# ─── Pipeline Routes ───

@router.post("/pipelines", status_code=201, response_model=PipelineOut)
def create_pipeline(data: PipelineCreate, user=Depends(get_current_user)):
    pipe = agent_orchestra.create_pipeline(data.workflow_id, data.context)
    if not pipe:
        raise HTTPException(status_code=404, detail="Workflow not found")
    # MVP: execute synchronously on creation
    pipe = agent_orchestra.execute_pipeline(pipe.id)
    return PipelineOut(
        id=pipe.id,
        workflow_id=pipe.workflow_id,
        status=pipe.status,
        current_step=pipe.current_step,
        context=pipe.context,
        results=pipe.results,
        created_at=pipe.created_at,
        updated_at=pipe.updated_at,
    )


@router.get("/pipelines", response_model=dict)
def list_pipelines(user=Depends(get_current_user)):
    """返回流水线列表."""
    pipes = agent_orchestra.list_pipelines()
    return {
        "pipelines": [
            PipelineOut(
                id=p.id,
                workflow_id=p.workflow_id,
                status=p.status,
                current_step=p.current_step,
                context=p.context,
                results=p.results,
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
            for p in pipes
        ]
    }


@router.get("/pipelines/{pipeline_id}", response_model=PipelineOut)
def get_pipeline(pipeline_id: str, user=Depends(get_current_user)):
    pipe = agent_orchestra.get_pipeline(pipeline_id)
    if not pipe:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return PipelineOut(
        id=pipe.id,
        workflow_id=pipe.workflow_id,
        status=pipe.status,
        current_step=pipe.current_step,
        context=pipe.context,
        results=pipe.results,
        created_at=pipe.created_at,
        updated_at=pipe.updated_at,
    )
