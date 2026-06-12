"""ImageForge API — W16 图片配置引擎路由。"""

from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from src.api.auth import get_current_user
from src.services.image_forge import (
    approve_config,
    create_image_config,
    get_image_config,
    list_image_configs,
    recommend_images,
    reject_config,
    set_layout,
    submit_for_review,
    t2_check,
)

router = APIRouter(prefix="/image-configs", tags=["image-forge"])


# ─── Request/Response Models ───

class ImageConfigCreate(BaseModel):
    content_draft_id: str
    account_id: str
    layout_type: str
    topic: str = ""
    has_product_info: bool = False


class ImageConfigOut(BaseModel):
    id: str
    content_draft_id: str
    account_id: str
    layout_type: str
    topic: str
    has_product_info: bool
    cover_image: Optional[dict]
    body_images: List[dict]
    status: str
    reject_reason: Optional[str] = None
    reviewer_id: Optional[str] = None
    created_at: str


class LayoutUpdate(BaseModel):
    cover_image: Optional[dict]
    body_images: List[dict]


class RecommendationsOut(BaseModel):
    recommended_images: List[dict]


class T2CheckOut(BaseModel):
    allow_t2: bool
    product_info_detected: bool
    reason: str


class ReviewAction(BaseModel):
    reviewer_id: str


class RejectAction(BaseModel):
    reviewer_id: str
    reason: str


# ─── Helpers ───

def _config_to_out(config) -> ImageConfigOut:
    return ImageConfigOut(
        id=config.id,
        content_draft_id=config.content_draft_id,
        account_id=config.account_id,
        layout_type=config.layout_type,
        topic=config.topic,
        has_product_info=config.has_product_info,
        cover_image=config.cover_image,
        body_images=config.body_images,
        status=config.status,
        reject_reason=config.reject_reason,
        reviewer_id=config.reviewer_id,
        created_at=config.created_at,
    )


# ─── Routes ───

@router.post("", status_code=status.HTTP_201_CREATED, response_model=ImageConfigOut)
def create_config(req: ImageConfigCreate, user=Depends(get_current_user)):
    config = create_image_config(
        content_draft_id=req.content_draft_id,
        account_id=req.account_id,
        layout_type=req.layout_type,
        topic=req.topic,
        has_product_info=req.has_product_info,
    )
    return _config_to_out(config)


@router.get("", response_model=Dict[str, List[ImageConfigOut]])
def list_configs(account_id: Optional[str] = None, user=Depends(get_current_user)):
    configs = list_image_configs(account_id=account_id)
    return {"configs": [_config_to_out(c) for c in configs]}


@router.get("/{config_id}", response_model=ImageConfigOut)
def get_config(config_id: str, user=Depends(get_current_user)):
    config = get_image_config(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    return _config_to_out(config)


@router.patch("/{config_id}/layout", response_model=ImageConfigOut)
def update_layout(config_id: str, req: LayoutUpdate, user=Depends(get_current_user)):
    config = set_layout(config_id, req.cover_image, req.body_images)
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    return _config_to_out(config)


@router.get("/{config_id}/recommendations", response_model=RecommendationsOut)
def get_recommendations(config_id: str, user=Depends(get_current_user)):
    config = get_image_config(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    images = recommend_images(config.topic)
    return RecommendationsOut(recommended_images=images)


@router.post("/{config_id}/t2-check", response_model=T2CheckOut)
def run_t2_check(config_id: str, user=Depends(get_current_user)):
    result = t2_check(config_id)
    if not result:
        raise HTTPException(status_code=404, detail="Config not found")
    return T2CheckOut(**result)


@router.post("/{config_id}/submit", response_model=ImageConfigOut)
def submit(config_id: str, user=Depends(get_current_user)):
    config = submit_for_review(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    return _config_to_out(config)


@router.post("/{config_id}/approve", response_model=ImageConfigOut)
def approve(config_id: str, req: ReviewAction, user=Depends(get_current_user)):
    config = approve_config(config_id, req.reviewer_id)
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    return _config_to_out(config)


@router.post("/{config_id}/reject", response_model=ImageConfigOut)
def reject(config_id: str, req: RejectAction, user=Depends(get_current_user)):
    config = reject_config(config_id, req.reviewer_id, req.reason)
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    return _config_to_out(config)
