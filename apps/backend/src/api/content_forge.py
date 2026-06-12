"""ContentForge API routes: drafts, generation, persona pool.

W15: Integrated with BrandKnowledge Function layer for RAG injection.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db, get_db_optional
from src.core.dependencies import get_current_user
from src.models.user import User
from src.services.content_forge_service import (
    create_content_draft,
    generate_with_persona,
    get_content_draft,
    list_content_drafts,
    remove_content_draft,
    update_content_draft,
)
import src.services.brand_knowledge_function as bkf
from src.services import task_hub as th
from src.services.account_pool_service import get_account

router = APIRouter(tags=["content-forge"])


# ─── Request/Response Models ───


class CreateDraftRequest(BaseModel):
    title: str
    content_type: str = Field(default="note", description="note, video, carousel")
    platform: str = Field(default="xhs", description="xhs, douyin, wechat_channels")
    account_id: str = ""
    body: str
    tags: Optional[List[str]] = None
    status: str = "draft"
    cover_image_url: Optional[str] = None


class UpdateDraftRequest(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = None
    cover_image_url: Optional[str] = None


class ContentDraftResponse(BaseModel):
    id: str
    title: str
    content_type: str
    platform: str
    account_id: str
    body: str
    tags: List[str]
    status: str
    cover_image_url: Optional[str] = None
    created_at: str
    updated_at: str
    published_at: Optional[str] = None


class DraftListResponse(BaseModel):
    drafts: List[ContentDraftResponse]
    total: int


class GenerateContentRequest(BaseModel):
    topic: str
    platform: str = "xhs"
    persona_id: Optional[str] = None
    stage_id: Optional[str] = None


class GeneratedContentResponse(BaseModel):
    title: str
    body: str
    tags: List[str]
    platform: str
    content_type: str
    persona_id: str
    _persona_used: str
    template_version: Optional[str] = None
    brand_knowledge_refs: List[str] = []


class PersonaResponse(BaseModel):
    id: str
    name: str
    voice_style: str
    catchphrases: List[str]
    formality: str
    emoji_frequency: str
    avg_sentence_length: int
    description: str


class PersonaListResponse(BaseModel):
    personas: List[PersonaResponse]


# ─── Helpers ───


def _draft_to_response(d: ContentDraftResponse) -> ContentDraftResponse:
    return ContentDraftResponse(
        id=d.id,
        title=d.title,
        content_type=d.content_type,
        platform=d.platform,
        account_id=d.account_id,
        body=d.body,
        tags=d.tags,
        status=d.status,
        cover_image_url=d.cover_image_url,
        created_at=d.created_at,
        updated_at=d.updated_at,
        published_at=d.published_at,
    )


# ─── Draft Routes ───


@router.post("/content-drafts", status_code=status.HTTP_201_CREATED, response_model=ContentDraftResponse)
def create_draft(req: CreateDraftRequest, user: User = Depends(get_current_user)):
    draft = create_content_draft(
        title=req.title,
        content_type=req.content_type,
        platform=req.platform,
        account_id=req.account_id,
        body=req.body,
        tags=req.tags,
        status=req.status,
        cover_image_url=req.cover_image_url,
    )
    return _draft_to_response(draft)


@router.get("/content-drafts", response_model=DraftListResponse)
def list_drafts(user: User = Depends(get_current_user)):
    drafts = list_content_drafts()
    return DraftListResponse(drafts=[_draft_to_response(d) for d in drafts], total=len(drafts))


@router.get("/content-drafts/{draft_id}", response_model=ContentDraftResponse)
def get_draft(draft_id: str, user: User = Depends(get_current_user)):
    draft = get_content_draft(draft_id)
    if draft is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")
    return _draft_to_response(draft)


@router.patch("/content-drafts/{draft_id}", response_model=ContentDraftResponse)
def update_draft(draft_id: str, req: UpdateDraftRequest, user: User = Depends(get_current_user)):
    kwargs = req.model_dump(exclude_unset=True)
    draft = update_content_draft(draft_id, **kwargs)
    if draft is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")
    return _draft_to_response(draft)


@router.delete("/content-drafts/{draft_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_draft(draft_id: str, user: User = Depends(get_current_user)):
    removed = remove_content_draft(draft_id)
    if not removed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")
    return None


# ─── Generation Routes ───


@router.post("/content-generate", response_model=GeneratedContentResponse)
async def generate_content(
    req: GenerateContentRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_optional),
):
    # W15: LLM Hub model resolution (global default)
    llm_config = None
    if db is not None:
        try:
            from src.services import llm_hub as lhs
            resolved = await lhs.resolve_model_for_node(db, "content_generation")
            if resolved["source"] != "none":
                model_info = await lhs.get_model(db, resolved["model_id"])
                if model_info:
                    llm_config = {
                        "provider": model_info["provider"],
                        "model_name": model_info["model_name"],
                        "api_key": lhs.decrypt_api_key(model_info["api_key_encrypted"]),
                        "endpoint_url": model_info.get("endpoint_base_url") or lhs._default_endpoint(model_info["provider"]),
                        "temperature": resolved["temperature"],
                    }
        except Exception:
            pass  # Fallback to env-based DeepSeek

    # W15: BrandKnowledge RAG injection — retrieve BEFORE generation
    brand_knowledge_entries = []
    brand_knowledge_refs = []
    if db is not None:
        try:
            bk_entries = await bkf.search_by_content(db, req.topic, limit=5)
            for entry in bk_entries:
                brand_knowledge_refs.append(str(entry.id))
                brand_knowledge_entries.append(bkf.entry_to_dict(entry))
        except Exception:
            # Graceful degradation if BK unavailable
            pass

    result = generate_with_persona(
        topic=req.topic,
        platform=req.platform,
        persona_id=req.persona_id,
        stage_id=req.stage_id,
        llm_config=llm_config,
        brand_knowledge_entries=brand_knowledge_entries,
    )

    result["brand_knowledge_refs"] = brand_knowledge_refs
    return GeneratedContentResponse(**result)


# ─── Submit for Review (bridges ContentForge → TaskHub) ───

class SubmitForReviewResponse(BaseModel):
    draft_id: str
    task_id: str
    status: str
    message: str


@router.post("/content-drafts/{draft_id}/submit-for-review", response_model=SubmitForReviewResponse)
async def submit_for_review(
    draft_id: str,
    persona_id: Optional[str] = None,
    workflow_template_id: str = "content_creation_standard",
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Submit a content draft for review.

    This endpoint bridges ContentForge and TaskHub by:
    1. Updating the draft status to 'reviewing'
    2. Creating a TaskHub task linked to the draft
    3. Starting the workflow execution (drives to HUMAN_WAIT)
    """
    draft = get_content_draft(draft_id)
    if draft is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")

    # 1. Update draft status
    update_content_draft(draft_id, status="reviewing")

    # 2. Resolve persona_id from account if not provided
    resolved_persona_id = persona_id
    if not resolved_persona_id and draft.account_id:
        acct = get_account(draft.account_id)
        if acct:
            resolved_persona_id = acct.persona
    if not resolved_persona_id:
        resolved_persona_id = "default_persona"

    # 3. Create TaskHub task
    task = await th.create_task(
        db=db,
        name=f"审核: {draft.title}",
        workflow_template_id=workflow_template_id,
        workflow_version=1,
        account_id=draft.account_id or "unknown",
        persona_id=resolved_persona_id,
        platform=draft.platform,
        prompt_variables={
            "draft_id": draft_id,
            "content_preview": draft.body[:500] if draft.body else "",
            "title": draft.title,
            "tags": draft.tags,
            "cover_image_url": draft.cover_image_url,
        },
        created_by=user.username if user else "operator",
    )

    # 4. Start workflow (drives to HUMAN_WAIT or COMPLETED)
    await th.start_workflow(db, task.id)

    return SubmitForReviewResponse(
        draft_id=draft_id,
        task_id=task.id,
        status=task.status.value,
        message="草稿已提交审核，任务已进入工作流",
    )


# ─── Six-Layer Prompt Decomposition ───

class PromptDecomposeRequest(BaseModel):
    topic: str
    platform: str = "xhs"
    persona_id: Optional[str] = None


class PromptLayer(BaseModel):
    key: str
    label: str
    description: str
    content: str


class PromptDecomposeResponse(BaseModel):
    topic: str
    platform: str
    layers: List[PromptLayer]


@router.post("/content-prompt-decompose", response_model=PromptDecomposeResponse)
async def decompose_prompt(
    req: PromptDecomposeRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_optional),
):
    """Decompose the content generation prompt into six visualizable layers."""
    from src.services.content_generator import decompose_six_layer_prompt
    import src.services.brand_knowledge_function as bkf

    # Resolve persona
    persona = None
    if req.persona_id:
        from src.services.content_forge_service import get_persona_detail
        p = get_persona_detail(req.persona_id)
        if p:
            persona = {
                "name": p.name,
                "voice_style": p.voice_style,
                "catchphrases": p.catchphrases,
                "formality": p.formality,
            }

    # Retrieve brand knowledge for RAG context
    brand_knowledge_entries = []
    if db is not None:
        try:
            bk_entries = await bkf.search_by_content(db, req.topic, limit=5)
            brand_knowledge_entries = [bkf.entry_to_dict(e) for e in bk_entries]
        except Exception:
            pass

    layers = decompose_six_layer_prompt(
        topic=req.topic,
        platform=req.platform,
        persona=persona,
        brand_knowledge_entries=brand_knowledge_entries,
    )

    layer_meta = [
        ("platform_format", "平台格式规范", "平台特定的格式、字数、禁忌与必须项"),
        ("structure_template", "结构模板", "输出结构要求：标题、正文分段、标签等"),
        ("brand_knowledge", "品牌知识注入", "RAG 检索到的品牌知识库条目与合规约束"),
        ("keyword_injection", "关键词/话题注入", "核心话题、创作要求与故事线上下文"),
        ("persona_layer", "人格/人设层", "创作者人设、身份定位与口头禅"),
        ("style_layer", "风格层", "语气风格、叙事视角、情感温度与互动策略"),
    ]

    return PromptDecomposeResponse(
        topic=req.topic,
        platform=req.platform,
        layers=[
            PromptLayer(key=k, label=label, description=desc, content=layers[k])
            for k, label, desc in layer_meta
        ],
    )
