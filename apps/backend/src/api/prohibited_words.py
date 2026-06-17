"""ProhibitedWord API — independent word library for compliance."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.dependencies import get_current_user
from src.models.user import User
from src.services import prohibited_word_function as pwf

router = APIRouter(prefix="/prohibited-words", tags=["prohibited-words"])


# ─── Request/Response Models ───

class WordCreate(BaseModel):
    word: str = Field(..., min_length=1, max_length=255)
    category: str = "general"
    severity: str = "L2"
    platform: str = "universal"
    match_type: str = "exact"
    description: Optional[str] = None


class WordOut(BaseModel):
    id: str
    word: str
    category: str
    severity: str
    platform: str
    match_type: str
    is_enabled: bool
    description: Optional[str]
    created_at: Optional[str]


class WordListResponse(BaseModel):
    items: List[WordOut]
    total: int
    limit: int
    offset: int


class DetectRequest(BaseModel):
    text: str = Field(..., min_length=1)
    platform: str = "universal"


class DetectResponse(BaseModel):
    matched: List[WordOut]
    count: int


class GuidelineCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    category: str
    rules_json: str = "{}"
    platform: str = "universal"
    description: Optional[str] = None


class GuidelineOut(BaseModel):
    id: str
    name: str
    category: str
    rules_json: str
    platform: str
    description: Optional[str]
    is_enabled: bool
    created_at: Optional[str]


# ─── Routes: ProhibitedWord ───

@router.post("", status_code=201, response_model=WordOut)
async def create_word(
    data: WordCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    w = await pwf.create_word(
        db=db,
        word=data.word,
        category=data.category,
        severity=data.severity,
        platform=data.platform,
        match_type=data.match_type,
        description=data.description,
        created_by=user.email if hasattr(user, "email") else "system",
    )
    return WordOut(**pwf.word_to_dict(w))


@router.get("", response_model=WordListResponse)
async def list_words(
    platform: Optional[str] = None,
    category: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 200,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await pwf.list_words(
        db=db, platform=platform, category=category, severity=severity,
        limit=limit, offset=offset,
    )
    return WordListResponse(
        items=[WordOut(**w) for w in result["items"]],
        total=result["total"],
        limit=result["limit"],
        offset=result["offset"],
    )


@router.post("/detect", response_model=DetectResponse)
async def detect_words(
    req: DetectRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    matches = await pwf.detect_words(db=db, text=req.text, platform=req.platform)
    return DetectResponse(matched=[WordOut(**w) for w in matches], count=len(matches))


@router.post("/seed-defaults")
async def seed_defaults(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await pwf.seed_default_words(
        db=db, created_by=user.email if hasattr(user, "email") else "system"
    )
    return {"seeded": result["created"], "skipped": result["skipped"]}


@router.delete("/{word_id}", status_code=204)
async def delete_word(
    word_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ok = await pwf.delete_word(db=db, word_id=word_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Word not found")
    return None


# ─── Routes: ContentGuideline ───

@router.post("/guidelines", status_code=201, response_model=GuidelineOut)
async def create_guideline(
    data: GuidelineCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    g = await pwf.create_guideline(
        db=db,
        name=data.name,
        category=data.category,
        rules_json=data.rules_json,
        platform=data.platform,
        description=data.description,
        created_by=user.email if hasattr(user, "email") else "system",
    )
    return GuidelineOut(**pwf.guideline_to_dict(g))


@router.get("/guidelines", response_model=List[GuidelineOut])
async def list_guidelines(
    platform: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await pwf.list_guidelines(
        db=db, platform=platform, category=category, limit=limit, offset=offset,
    )
    return [GuidelineOut(**g) for g in result["items"]]
