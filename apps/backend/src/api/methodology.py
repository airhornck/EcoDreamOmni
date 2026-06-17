"""MarketingMethodology API — AIPL stage templates and content evaluation."""

from src.services import methodology_5a_service

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict

from src.api.auth import get_current_user
from src.services import methodology_service

router = APIRouter(prefix="/methodologies", tags=["methodology"])


class MethodologyOut(BaseModel):
    framework: str
    stages: List[str]


class StageOut(BaseModel):
    id: str
    framework: str
    stage: str
    stage_name: str
    content_template: dict
    kpi_targets: dict
    compliance_tags: List[str]
    forbidden_elements: List[str]
    stage_transition_criteria: dict
    recommended_persona_types: List[str]

    model_config = ConfigDict(from_attributes=True)


class StageTemplateOut(BaseModel):
    hook: dict
    body: dict
    cta: dict
    disclaimer: dict


class StageEvaluateRequest(BaseModel):
    body: str


class StageEvaluateResponse(BaseModel):
    missing_fields: List[str]
    score: int


@router.get("")
def list_methodologies(user=Depends(get_current_user)):
    return {"methodologies": methodology_service.list_methodologies()}


@router.get("/{framework_id}/stages")
def list_stages_by_framework(framework_id: str, user=Depends(get_current_user)):
    stages = methodology_service.list_stages_by_framework(framework_id)
    return {
        "stages": [
            StageOut(
                id=s.id,
                framework=s.framework,
                stage=s.stage,
                stage_name=s.stage_name,
                content_template=s.content_template,
                kpi_targets=s.kpi_targets,
                compliance_tags=s.compliance_tags,
                forbidden_elements=s.forbidden_elements,
                stage_transition_criteria=s.stage_transition_criteria,
                recommended_persona_types=s.recommended_persona_types,
            )
            for s in stages
        ]
    }


@router.get("/stages")
def list_stages(framework: Optional[str] = None, user=Depends(get_current_user)):
    stages = methodology_service.list_stages(framework=framework)
    return {
        "stages": [
            StageOut(
                id=s.id,
                framework=s.framework,
                stage=s.stage,
                stage_name=s.stage_name,
                content_template=s.content_template,
                kpi_targets=s.kpi_targets,
                compliance_tags=s.compliance_tags,
                forbidden_elements=s.forbidden_elements,
                stage_transition_criteria=s.stage_transition_criteria,
                recommended_persona_types=s.recommended_persona_types,
            )
            for s in stages
        ]
    }


@router.get("/stages/{stage_id}/template", response_model=StageTemplateOut)
def get_stage_template(stage_id: str, user=Depends(get_current_user)):
    template = methodology_service.get_stage_template(stage_id)
    if not template:
        raise HTTPException(status_code=404, detail="Stage not found")
    return StageTemplateOut(
        hook=template.get("hook", {}),
        body=template.get("body", {}),
        cta=template.get("cta", {}),
        disclaimer=template.get("disclaimer", {}),
    )


@router.get("/stages/{stage_id}", response_model=StageOut)
def get_stage(stage_id: str, user=Depends(get_current_user)):
    stage = methodology_service.get_stage(stage_id)
    if not stage:
        raise HTTPException(status_code=404, detail="Stage not found")
    return StageOut(
        id=stage.id,
        framework=stage.framework,
        stage=stage.stage,
        stage_name=stage.stage_name,
        content_template=stage.content_template,
        kpi_targets=stage.kpi_targets,
        compliance_tags=stage.compliance_tags,
        forbidden_elements=stage.forbidden_elements,
        stage_transition_criteria=stage.stage_transition_criteria,
        recommended_persona_types=stage.recommended_persona_types,
    )


@router.post("/stages/{stage_id}/evaluate")
def evaluate_content(stage_id: str, data: StageEvaluateRequest, user=Depends(get_current_user)):
    # Try 5A service first, fall back to AIPL service
    result = methodology_5a_service.evaluate_5a_content(stage_id, data.body)
    if result["stage_match"] is None and "stage_not_found" in result.get("missing_elements", []):
        # Try original service
        result = methodology_service.evaluate_content(stage_id, data.body)
        return StageEvaluateResponse(
            missing_fields=result["missing_fields"],
            score=result["score"],
        )
    # Return 5A enhanced response
    return StageEvaluate5AResponse(
        score=result["score"],
        stage_match=result["stage_match"],
        missing_elements=result["missing_elements"],
        forbidden_found=result.get("forbidden_found", []),
    )


# ===== 5A Methodology Extensions =====


class StageEvaluate5AResponse(BaseModel):
    score: int
    stage_match: Optional[str]
    missing_elements: List[str]
    forbidden_found: List[str]


class AudienceSegmentsOut(BaseModel):
    audience_segments: List[dict]


class PersonaRecommendationsOut(BaseModel):
    recommended_personas: List[str]


class StageMappingOut(BaseModel):
    source_stage: str
    target_stage: str
    mapping_description: str


@router.get("/stages/{stage_id}/audience", response_model=AudienceSegmentsOut)
def get_stage_audience_segments(stage_id: str, user=Depends(get_current_user)):
    segments = methodology_5a_service.get_stage_audience_segments(stage_id)
    if segments is None:
        raise HTTPException(status_code=404, detail="Stage not found")
    return AudienceSegmentsOut(audience_segments=segments)


@router.get("/stages/{stage_id}/personas", response_model=PersonaRecommendationsOut)
def get_stage_persona_recommendations(stage_id: str, user=Depends(get_current_user)):
    personas = methodology_5a_service.get_stage_persona_recommendations(stage_id)
    if personas is None:
        raise HTTPException(status_code=404, detail="Stage not found")
    return PersonaRecommendationsOut(recommended_personas=personas)


@router.get("/aipl/{aipl_stage}/to-5a", response_model=StageMappingOut)
def map_aipl_to_5a(aipl_stage: str, user=Depends(get_current_user)):
    result = methodology_5a_service.map_aipl_to_5a(aipl_stage)
    if not result:
        raise HTTPException(status_code=400, detail=f"Invalid AIPL stage: {aipl_stage}")
    five_a_stage, desc = result
    return StageMappingOut(
        source_stage=aipl_stage.upper(),
        target_stage=five_a_stage,
        mapping_description=desc,
    )


@router.get("/5a/{five_a_stage}/to-aipl", response_model=StageMappingOut)
def map_5a_to_aipl(five_a_stage: str, user=Depends(get_current_user)):
    result = methodology_5a_service.map_5a_to_aipl(five_a_stage)
    if not result:
        raise HTTPException(status_code=400, detail=f"Invalid 5A stage: {five_a_stage}")
    aipl_stage, desc = result
    return StageMappingOut(
        source_stage=five_a_stage.upper(),
        target_stage=aipl_stage,
        mapping_description=desc,
    )


