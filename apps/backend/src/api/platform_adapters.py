"""Platform Adapter API — W20.

Routes:
  GET  /platform-adapters/platforms          — List supported platforms
  GET  /platform-adapters/specs              — Get all platform specs
  GET  /platform-adapters/{platform}/spec    — Get single platform spec
  POST /platform-adapters/{platform}/format  — Format content for platform
  POST /platform-adapters/{platform}/validate — Validate platform payload
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.services import platform_adapters

router = APIRouter(prefix="/platform-adapters", tags=["platform-adapters"])


# ─── Schemas ───

class FormatRequest(BaseModel):
    title: str
    body: str = ""
    tags: List[str] = []
    images: List[str] = []
    video: Optional[str] = None
    cover_image: Optional[str] = None


class ValidateRequest(BaseModel):
    payload: Dict[str, Any]


# ─── Routes ───

@router.get("/platforms")
def list_platforms() -> Dict[str, Any]:
    return {"platforms": platform_adapters.list_supported_platforms()}


@router.get("/specs")
def get_all_specs() -> Dict[str, Any]:
    return platform_adapters.compare_platform_specs()


@router.get("/{platform}/spec")
def get_platform_spec(platform: str) -> Dict[str, Any]:
    try:
        adapter = platform_adapters.get_adapter(platform)
        return adapter.get_specs()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{platform}/format")
def format_content(platform: str, req: FormatRequest) -> Dict[str, Any]:
    try:
        adapter = platform_adapters.get_adapter(platform)
        payload = adapter.format_content(
            title=req.title,
            body=req.body,
            tags=req.tags,
            images=req.images,
            video=req.video,
            cover_image=req.cover_image,
        )
        return {"platform": platform, "payload": payload}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{platform}/validate")
def validate_payload(platform: str, req: ValidateRequest) -> Dict[str, Any]:
    try:
        adapter = platform_adapters.get_adapter(platform)
        result = adapter.validate_payload(req.payload)
        return {"platform": platform, **result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
