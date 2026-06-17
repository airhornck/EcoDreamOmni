"""SkillHub API — four-layer skill management + agent binding + Tool Registry.

Aligned with dev-plan W15: hermes-agent skill compatibility + Tool Registry schema.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, List, Optional

from src.services.skill_hub import (
    SkillDefinition,
    register,
    bind_to_agent,
    get_agent_skills,
    validate_invocation,
    get_skill_versions,
    get_latest_version,
)

from fastapi import APIRouter, Depends, HTTPException

from src.api.auth import get_current_user
from src.services import skill_hub, skill_binding

router = APIRouter()


class SkillCreate(BaseModel):
    name: str
    description: str = ""
    level: str = "L2"
    code: str = ""
    tags: List[str] = []
    version: str = "1.0.0"
    metadata: dict = {}
    modality_support: dict = {"text": True}


class SkillUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    level: Optional[str] = None
    code: Optional[str] = None
    tags: Optional[List[str]] = None
    version: Optional[str] = None
    status: Optional[str] = None
    metadata: Optional[dict] = None


class SkillOut(BaseModel):
    id: str
    name: str
    description: str
    level: str
    code: str
    tags: List[str]
    version: str
    status: str
    metadata: dict
    created_at: str
    updated_at: str

    model_config = ConfigDict(from_attributes=True)


class BindingCreate(BaseModel):
    agent_id: str
    skill_id: str
    priority: int = 0
    config: dict = {}


class BindingOut(BaseModel):
    id: str
    agent_id: str
    skill_id: str
    priority: int
    config: dict


class ExecuteRequest(BaseModel):
    context: dict = {}


class ToolSchemaOut(BaseModel):
    skill_id: str
    name: str
    description: str
    input_schema: dict
    output_schema: dict
    requires_tools: List[str]
    requires_toolsets: List[str]


class DependencyCheckOut(BaseModel):
    skill_id: str
    missing_tools: List[str]
    missing_toolsets: List[str]
    satisfied: bool


class HermesSkillImport(BaseModel):
    skill_md: str


# ─── Skill CRUD ───

@router.post("", status_code=201, response_model=SkillOut)
def create_skill(data: SkillCreate, user=Depends(get_current_user)):
    skill = skill_hub.create_skill(
        name=data.name,
        description=data.description,
        level=data.level,
        code=data.code,
        tags=data.tags,
        version=data.version,
        metadata=data.metadata,
        modality_support=data.modality_support,
    )
    return _skill_to_out(skill)


@router.get("")
def list_skills(level: Optional[str] = None, user=Depends(get_current_user)):
    skills = skill_hub.list_skills(level=level)
    return {"skills": [_skill_to_out(s) for s in skills]}


@router.get("/{skill_id}", response_model=SkillOut)
def get_skill(skill_id: str, user=Depends(get_current_user)):
    skill = skill_hub.get_skill(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return _skill_to_out(skill)


@router.patch("/{skill_id}", response_model=SkillOut)
def update_skill(skill_id: str, data: SkillUpdate, user=Depends(get_current_user)):
    kwargs = data.model_dump(exclude_unset=True)
    skill = skill_hub.update_skill(skill_id, **kwargs)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return _skill_to_out(skill)


@router.delete("/{skill_id}", status_code=204)
def delete_skill(skill_id: str, user=Depends(get_current_user)):
    if not skill_hub.delete_skill(skill_id):
        raise HTTPException(status_code=404, detail="Skill not found")
    return None


# ─── Four-Layer Resolution ───

@router.get("/resolve/all")
def resolve_all_skills(user=Depends(get_current_user)):
    """Resolve effective skill set with layer override (L4 > L3 > L2 > L1)."""
    skills = skill_hub.resolve_skills()
    return {"skills": [_skill_to_out(s) for s in skills]}


@router.get("/resolve/agent/{agent_id}")
def resolve_agent_skills(agent_id: str, user=Depends(get_current_user)):
    """Resolve effective skill set for a specific agent (bindings + L1)."""
    skills = skill_hub.resolve_skills_for_agent(agent_id)
    return {"skills": [_skill_to_out(s) for s in skills], "agent_id": agent_id}


# ─── Dependency Check ───

@router.get("/{skill_id}/dependencies", response_model=DependencyCheckOut)
def check_dependencies(skill_id: str, user=Depends(get_current_user)):
    skill = skill_hub.get_skill(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    deps = skill_hub.check_dependencies(skill_id)
    return DependencyCheckOut(
        skill_id=skill_id,
        missing_tools=deps["missing_tools"],
        missing_toolsets=deps["missing_toolsets"],
        satisfied=len(deps["missing_tools"]) == 0 and len(deps["missing_toolsets"]) == 0,
    )


# ─── Agent-Skill Binding ───

agent_binding_router = APIRouter()

@agent_binding_router.post("", status_code=201, response_model=BindingOut)
def create_binding(data: BindingCreate, user=Depends(get_current_user)):
    binding = skill_binding.bind_skill(
        agent_id=data.agent_id,
        skill_id=data.skill_id,
        priority=data.priority,
        config=data.config,
    )
    return BindingOut(
        id=binding.id,
        agent_id=binding.agent_id,
        skill_id=binding.skill_id,
        priority=binding.priority,
        config=binding.config,
    )


@agent_binding_router.get("")
def list_bindings(agent_id: Optional[str] = None, user=Depends(get_current_user)):
    bindings = skill_binding.list_bindings(agent_id=agent_id)
    return {
        "bindings": [
            BindingOut(
                id=b.id,
                agent_id=b.agent_id,
                skill_id=b.skill_id,
                priority=b.priority,
                config=b.config,
            )
            for b in bindings
        ]
    }


# ─── Tool Registry ───

@router.get("/tools/registry")
def list_tool_registry(layer: Optional[str] = None, user=Depends(get_current_user)):
    """List all registered tools with unified schema."""
    schemas = skill_hub.list_tools_by_layer(layer=layer)
    return {
        "tools": [
            ToolSchemaOut(
                skill_id=t.skill_id,
                name=t.name,
                description=t.description,
                input_schema=t.input_schema,
                output_schema=t.output_schema,
                requires_tools=t.requires_tools,
                requires_toolsets=t.requires_toolsets,
            )
            for t in schemas
        ]
    }


@router.get("/tools/registry/{skill_id}", response_model=ToolSchemaOut)
def get_tool_schema(skill_id: str, user=Depends(get_current_user)):
    schema = skill_hub.get_tool_schema(skill_id)
    if not schema:
        raise HTTPException(status_code=404, detail="Tool schema not found")
    return ToolSchemaOut(
        skill_id=schema.skill_id,
        name=schema.name,
        description=schema.description,
        input_schema=schema.input_schema,
        output_schema=schema.output_schema,
        requires_tools=schema.requires_tools,
        requires_toolsets=schema.requires_toolsets,
    )


# ─── Hermes-Agent Import ───

@router.post("/import/hermes", status_code=201, response_model=SkillOut)
def import_hermes_skill(data: HermesSkillImport, user=Depends(get_current_user)):
    skill = skill_hub.import_hermes_skill(data.skill_md)
    if skill is None:
        raise HTTPException(status_code=422, detail="Invalid hermes SKILL.md content")
    return _skill_to_out(skill)


# ─── Skill Execution ───

@router.post("/{skill_id}/execute", response_model=dict)
def execute_skill(skill_id: str, req: ExecuteRequest, user=Depends(get_current_user)):
    result = skill_hub.execute_skill(skill_id, req.context)
    if not result["success"] and result["error"] == "Skill not found":
        raise HTTPException(status_code=404, detail="Skill not found")
    return result


# ─── Helpers ───

def _skill_to_out(skill: skill_hub.Skill) -> SkillOut:
    return SkillOut(
        id=skill.id,
        name=skill.name,
        description=skill.description,
        level=skill.level,
        code=skill.code,
        tags=skill.tags,
        version=skill.version,
        status=skill.status,
        metadata=skill.metadata,
        modality_support=skill.modality_support,
        created_at=skill.created_at,
        updated_at=skill.updated_at,
    )


# ═══════════════════════════════════════════════════════
# P3-1: Skill Hub Registration & Validation v4.0
# ═══════════════════════════════════════════════════════


class RegisterSkillRequest(BaseModel):
    skill_id: str
    name: str
    description: str = ""
    version: str = "1.0.0"
    level: str = "L2"
    input_schema: Dict = Field(default_factory=dict)
    output_schema: Dict = Field(default_factory=dict)
    modality_support: Dict = Field(default_factory=lambda: {"text": True})
    requires_llm: bool = False
    llm_model_preference: str = ""
    required_functions: List[str] = Field(default_factory=list)
    permissions: Dict = Field(default_factory=dict)
    code: str = ""
    metadata: Dict = Field(default_factory=dict)


class RegisterSkillResponse(BaseModel):
    skill_id: str
    name: str
    version: str
    status: str
    message: str


class BindSkillRequest(BaseModel):
    agent_id: str
    priority: int = 0
    config: Dict = Field(default_factory=dict)


class ValidateInvocationRequest(BaseModel):
    agent_id: str
    inputs: Dict = Field(default_factory=dict)


class ValidateInvocationResponse(BaseModel):
    valid: bool
    errors: List[str]


class SkillVersionOut(BaseModel):
    skill_id: str
    name: str
    version: str
    level: str
    description: str


# ─── Routes ───

@router.post("/register", response_model=RegisterSkillResponse, status_code=201)
def register_skill(req: RegisterSkillRequest, user=Depends(get_current_user)):
    """Register a new Skill with JSON Schema validation."""
    definition = SkillDefinition(
        skill_id=req.skill_id,
        name=req.name,
        description=req.description,
        version=req.version,
        level=req.level,
        input_schema=req.input_schema,
        output_schema=req.output_schema,
        modality_support=req.modality_support,
        requires_llm=req.requires_llm,
        llm_model_preference=req.llm_model_preference,
        required_functions=req.required_functions,
        permissions=req.permissions,
        code=req.code,
        metadata=req.metadata,
    )
    result = register(definition)
    return RegisterSkillResponse(
        skill_id=result.skill_id,
        name=result.name,
        version=result.version,
        status=result.status,
        message="Skill registered successfully",
    )


@router.post("/{skill_id}/bind", response_model=dict)
def bind_skill(skill_id: str, req: BindSkillRequest, user=Depends(get_current_user)):
    """Bind a Skill to an Agent."""
    binding = bind_to_agent(
        skill_id=skill_id,
        agent_id=req.agent_id,
        priority=req.priority,
        config=req.config,
        granted_by=getattr(user, "id", "system"),
    )
    return {
        "agent_id": binding.agent_id,
        "skill_id": binding.skill_id,
        "priority": binding.priority,
        "granted_at": binding.granted_at,
    }


@router.get("/agent/{agent_id}/skills")
def list_agent_skills(agent_id: str, user=Depends(get_current_user)):
    """List all skills available to an agent."""
    skills = get_agent_skills(agent_id)
    return {
        "agent_id": agent_id,
        "skills": [
            {
                "skill_id": s.skill_id,
                "name": s.name,
                "version": s.version,
                "level": s.level,
                "description": s.description,
                "modality_support": s.modality_support,
            }
            for s in skills
        ],
    }


@router.post("/{skill_id}/validate", response_model=ValidateInvocationResponse)
def validate_skill(skill_id: str, req: ValidateInvocationRequest, user=Depends(get_current_user)):
    """Validate if an agent can invoke a skill with given inputs."""
    result = validate_invocation(skill_id, req.agent_id, req.inputs)
    return ValidateInvocationResponse(valid=result["valid"], errors=result["errors"])


@router.get("/{skill_id}/versions")
def list_skill_versions(skill_id: str, user=Depends(get_current_user)):
    """List all versions of a skill."""
    versions = get_skill_versions(skill_id)
    return {
        "skill_id": skill_id,
        "versions": [
            {"version": v.version, "level": v.level, "status": v.status}
            for v in versions
        ],
    }


@router.get("/{skill_id}/latest")
def get_latest_skill_version(skill_id: str, user=Depends(get_current_user)):
    """Get the latest version of a skill."""
    latest = get_latest_version(skill_id)
    if not latest:
        raise HTTPException(status_code=404, detail="Skill not found")
    return SkillVersionOut(
        skill_id=latest.skill_id,
        name=latest.name,
        version=latest.version,
        level=latest.level,
        description=latest.description,
    )
