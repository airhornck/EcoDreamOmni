"""SkillSmith API — evolved skill auto-generation endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict

from src.api.auth import get_current_user
from src.services import skill_smith

router = APIRouter(prefix="/skill-smith", tags=["skill-smith"])


class PerformanceRecord(BaseModel):
    skill_id: str
    account_id: str
    success: bool
    ces: float = 0.0
    mape: float = 1.0


class EvolveRequest(BaseModel):
    account_id: str
    condition_type: str


class TriggerOut(BaseModel):
    trigger_id: str
    skill_id: str
    account_id: str
    condition_type: str
    threshold: float
    current_value: float
    triggered_at: str
    status: str

    model_config = ConfigDict(from_attributes=True)


@router.post("/record-performance", status_code=201)
def record_performance(data: PerformanceRecord, user=Depends(get_current_user)):
    skill_smith.record_performance(
        skill_id=data.skill_id,
        account_id=data.account_id,
        success=data.success,
        ces=data.ces,
        mape=data.mape,
    )
    return {"status": "recorded"}


@router.get("/opportunities/{skill_id}")
def get_opportunities(skill_id: str, account_id: str, user=Depends(get_current_user)):
    opportunities = skill_smith.check_evolution_opportunities(skill_id, account_id)
    return {"opportunities": opportunities}


@router.post("/evolve/{skill_id}", status_code=201)
def evolve_skill(skill_id: str, data: EvolveRequest, user=Depends(get_current_user)):
    result = skill_smith.generate_evolved_skill(skill_id, data.account_id, data.condition_type)
    if not result:
        raise HTTPException(status_code=400, detail="Cannot evolve skill: insufficient performance data or source skill not found")
    return result


@router.get("/triggers")
def list_triggers(status: Optional[str] = None, user=Depends(get_current_user)):
    triggers = skill_smith.list_evolution_triggers(status=status)
    return {
        "triggers": [
            TriggerOut(
                trigger_id=t.trigger_id,
                skill_id=t.skill_id,
                account_id=t.account_id,
                condition_type=t.condition_type,
                threshold=t.threshold,
                current_value=t.current_value,
                triggered_at=t.triggered_at,
                status=t.status,
            )
            for t in triggers
        ]
    }
