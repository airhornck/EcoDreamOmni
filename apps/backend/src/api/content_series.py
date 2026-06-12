"""ContentSeries API — W16 内容系列化路由。"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from src.api.auth import get_current_user
from src.services.content_series import (
    add_content_to_series,
    check_engagement_allowed,
    create_series,
    get_series,
    get_series_context,
    list_series,
)

router = APIRouter(prefix="/content-series", tags=["content-series"])


# ─── Request/Response Models ───


class SeriesCreateRequest(BaseModel):
    name: str
    account_id: str
    stage_sequence: List[str]


class SeriesAddContentRequest(BaseModel):
    content_draft_id: str
    stage: str


class SeriesOut(BaseModel):
    id: str
    name: str
    account_id: str
    stage_sequence: List[str]
    contents: List[dict]
    status: str


class SeriesContextResponse(BaseModel):
    series_id: str
    series_name: str
    account_id: str
    current_stage: str
    current_index: int
    total_contents: int
    prev_content: Optional[dict]
    next_content: Optional[dict]
    prev_summary: str
    stage_sequence: List[str]


class EngagementCheckRequest(BaseModel):
    account_ids: List[str]
    action: str


class EngagementCheckResponse(BaseModel):
    allowed: bool
    reason: str


# ─── Helpers ───


def _series_to_out(series) -> SeriesOut:
    return SeriesOut(
        id=series.id,
        name=series.name,
        account_id=series.account_id,
        stage_sequence=series.stage_sequence,
        contents=list(series.contents),
        status=series.status,
    )


# ─── Routes ───


@router.post("", status_code=status.HTTP_201_CREATED, response_model=SeriesOut)
def create_series_route(
    req: SeriesCreateRequest,
    user=Depends(get_current_user),
):
    series = create_series(
        name=req.name,
        account_id=req.account_id,
        stage_sequence=req.stage_sequence,
    )
    return _series_to_out(series)


@router.get("", response_model=dict)
def list_series_route(
    account_id: Optional[str] = None,
    user=Depends(get_current_user),
):
    series_list = list_series(account_id=account_id)
    return {"series": [_series_to_out(s) for s in series_list]}


@router.get("/{series_id}", response_model=SeriesOut)
def get_series_route(
    series_id: str,
    user=Depends(get_current_user),
):
    series = get_series(series_id)
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")
    return _series_to_out(series)


@router.post("/{series_id}/contents", response_model=SeriesOut)
def add_content_to_series_route(
    series_id: str,
    req: SeriesAddContentRequest,
    user=Depends(get_current_user),
):
    series = add_content_to_series(
        series_id=series_id,
        content_draft_id=req.content_draft_id,
        stage=req.stage,
    )
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")
    return _series_to_out(series)


@router.get("/{series_id}/context", response_model=SeriesContextResponse)
def get_series_context_route(
    series_id: str,
    content_draft_id: str,
    user=Depends(get_current_user),
):
    context = get_series_context(series_id, content_draft_id)
    if not context:
        raise HTTPException(status_code=404, detail="Series or content not found")
    return SeriesContextResponse(**context)


@router.post("/engagement-check", response_model=EngagementCheckResponse)
def engagement_check_route(
    req: EngagementCheckRequest,
    user=Depends(get_current_user),
):
    result = check_engagement_allowed(
        account_ids=req.account_ids,
        action=req.action,
    )
    return EngagementCheckResponse(**result)
