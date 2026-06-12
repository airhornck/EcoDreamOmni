"""PersonaPool API — persona lifecycle management."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict

from src.api.auth import get_current_user
import src.services.persona_pool as persona_pool_service

router = APIRouter(prefix="/personas", tags=["personas"])


class PersonaCreate(BaseModel):
    name: str
    status: str = "draft"
    identity_core: dict = {}
    pet_profile: dict = {}
    owner_profile: dict = {}
    content_voice: dict = {}
    life_scenes: List[dict] = []
    success_patterns: List[dict] = []
    usage_stats: dict = {}


class PersonaOut(BaseModel):
    id: str
    name: str
    status: str
    identity_core: dict
    pet_profile: dict
    owner_profile: dict
    content_voice: dict
    life_scenes: List[dict]
    success_patterns: List[dict]
    usage_stats: dict
    created_at: str
    updated_at: str
    # Backward-compatible aliases for content_forge
    voice_style: str = ""
    formality: str = ""
    catchphrases: List[str] = []
    # Frontend compatibility fields
    nickname: str = ""
    pet_type: str = ""

    model_config = ConfigDict(from_attributes=True)


class PersonaCloneRequest(BaseModel):
    source_id: str
    name: Optional[str] = None
    overrides: Optional[dict] = None


class PersonaMatchRequest(BaseModel):
    pet_type: str = ""
    owner_type: str = ""
    budget_level: str = ""


def _persona_to_out(persona) -> PersonaOut:
    cv = persona.content_voice or {}
    pp = persona.pet_profile or {}
    return PersonaOut(
        id=persona.id,
        name=persona.name,
        status=persona.status,
        identity_core=persona.identity_core,
        pet_profile=persona.pet_profile,
        owner_profile=persona.owner_profile,
        content_voice=persona.content_voice,
        life_scenes=persona.life_scenes,
        success_patterns=persona.success_patterns,
        usage_stats=persona.usage_stats,
        created_at=persona.created_at,
        updated_at=persona.updated_at,
        voice_style=cv.get("tone", ""),
        formality=cv.get("formality_level", ""),
        catchphrases=cv.get("catchphrases", []),
        nickname=persona.name,
        pet_type=pp.get("pet_type", ""),
    )


@router.post("", status_code=201, response_model=PersonaOut)
def create_persona(data: PersonaCreate, user=Depends(get_current_user)):
    persona = persona_pool_service.create_persona(data.model_dump())
    return _persona_to_out(persona)


@router.get("")
def list_personas(status: Optional[str] = None, user=Depends(get_current_user)):
    personas = persona_pool_service.list_personas(status=status)
    return {"personas": [_persona_to_out(p) for p in personas]}


@router.get("/{persona_id}", response_model=PersonaOut)
def get_persona(persona_id: str, user=Depends(get_current_user)):
    persona = persona_pool_service.get_persona(persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    return _persona_to_out(persona)


@router.patch("/{persona_id}", response_model=PersonaOut)
def update_persona(persona_id: str, data: dict, user=Depends(get_current_user)):
    persona = persona_pool_service.update_persona(persona_id, data)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    return _persona_to_out(persona)


@router.post("/clone", status_code=201, response_model=PersonaOut)
def clone_persona(data: PersonaCloneRequest, user=Depends(get_current_user)):
    overrides = data.overrides or {}
    if data.name:
        overrides["name"] = data.name
    persona = persona_pool_service.clone_persona(data.source_id, overrides)
    if not persona:
        raise HTTPException(status_code=404, detail="Source persona not found")
    return _persona_to_out(persona)


@router.delete("/{persona_id}", status_code=204)
def delete_persona(persona_id: str, user=Depends(get_current_user)):
    if not persona_pool_service.delete_persona(persona_id):
        raise HTTPException(status_code=404, detail="Persona not found")
    return None


@router.post("/match")
def match_personas(data: PersonaMatchRequest, user=Depends(get_current_user)):
    recommendations = persona_pool_service.PersonaMatcher.recommend(data.model_dump())
    return {"recommendations": recommendations}
