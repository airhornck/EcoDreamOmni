"""PersonaStory API routes — PRD V2.7.2 §11.

素人人设剧本管理路由：剧本CRUD、节点编排、情感曲线、内容绑定.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.dependencies import get_current_user
from src.services import persona_story_service as pss

router = APIRouter(prefix="/persona-stories", tags=["persona-stories"])


# ─── Request / Response Models ───


class StoryCreateRequest(BaseModel):
    persona_id: str = Field(..., max_length=64)
    name: str = Field(..., max_length=256)
    description: Optional[str] = None
    emotion_curve_template: str = Field(default="gradual_growth", max_length=32)


class StoryUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, max_length=256)
    description: Optional[str] = None
    emotion_curve_template: Optional[str] = Field(None, max_length=32)


class StoryStatusPatchRequest(BaseModel):
    status: str = Field(..., pattern="^(draft|active|completed|archived)$")


class StoryCloneRequest(BaseModel):
    new_name: str = Field(..., max_length=256)


class StoryOut(BaseModel):
    id: str
    persona_id: str
    name: str
    description: Optional[str] = None
    emotion_curve_template: str
    status: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    # Frontend compatibility
    title: str = ""

    class Config:
        from_attributes = True


class NodeCreateRequest(BaseModel):
    sequence_index: int = Field(..., ge=0)
    theme: str = Field(..., max_length=256)
    emotion_tone: str = Field(..., pattern="^(low|medium|high|burst)$")
    key_event: str
    prev_recap: Optional[str] = None
    next_teaser: Optional[str] = None


class NodeUpdateRequest(BaseModel):
    sequence_index: Optional[int] = Field(None, ge=0)
    theme: Optional[str] = Field(None, max_length=256)
    emotion_tone: Optional[str] = Field(None, pattern="^(low|medium|high|burst)$")
    key_event: Optional[str] = None
    prev_recap: Optional[str] = None
    next_teaser: Optional[str] = None


class NodeOut(BaseModel):
    id: str
    story_id: str
    sequence_index: int
    theme: str
    emotion_tone: str
    key_event: str
    prev_recap: Optional[str] = None
    next_teaser: Optional[str] = None
    content_draft_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    # Frontend compatibility
    title: str = ""
    mood: str = ""

    class Config:
        from_attributes = True


class ReorderRequest(BaseModel):
    node_order: List[str]


class BindContentRequest(BaseModel):
    content_draft_id: str


class StoryContextResponse(BaseModel):
    current_node: Optional[dict] = None
    prev_node_summary: str
    next_node_teaser: str
    series_theme: str
    emotional_arc: str


# ─── Helpers ───


def _story_to_out(story) -> StoryOut:
    return StoryOut(
        id=str(story.id),
        persona_id=story.persona_id,
        name=story.name,
        description=story.description,
        emotion_curve_template=story.emotion_curve_template,
        status=story.status,
        created_at=story.created_at.isoformat() if story.created_at else None,
        updated_at=story.updated_at.isoformat() if story.updated_at else None,
        title=story.name,
    )


def _node_to_out(node) -> NodeOut:
    return NodeOut(
        id=str(node.id),
        story_id=str(node.story_id),
        sequence_index=node.sequence_index,
        theme=node.theme,
        emotion_tone=node.emotion_tone,
        key_event=node.key_event,
        prev_recap=node.prev_recap,
        next_teaser=node.next_teaser,
        content_draft_id=node.content_draft_id,
        created_at=node.created_at.isoformat() if node.created_at else None,
        updated_at=node.updated_at.isoformat() if node.updated_at else None,
        title=node.theme,
        mood=node.emotion_tone,
    )


# ─── Story Routes ───


@router.post("", status_code=status.HTTP_201_CREATED, response_model=StoryOut)
async def create_story_route(
    req: StoryCreateRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    story = await pss.create_story(
        db=db,
        persona_id=req.persona_id,
        name=req.name,
        description=req.description,
        emotion_curve_template=req.emotion_curve_template,
    )
    await db.commit()
    return _story_to_out(story)


@router.get("", response_model=dict)
async def list_stories_route(
    persona_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    result = await pss.list_stories(
        db=db, persona_id=persona_id, status=status, limit=limit, offset=offset
    )
    return {
        "items": [_story_to_out(s) for s in result["items"]],
        "total": result["total"],
        "limit": result["limit"],
        "offset": result["offset"],
    }


@router.get("/{story_id}", response_model=StoryOut)
async def get_story_route(
    story_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    story = await pss.get_story(db, story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    return _story_to_out(story)


@router.put("/{story_id}", response_model=StoryOut)
async def update_story_route(
    story_id: str,
    req: StoryUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    update_data = req.model_dump(exclude_unset=True)
    story = await pss.update_story(db, story_id, **update_data)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    await db.commit()
    return _story_to_out(story)


@router.delete("/{story_id}", status_code=status.HTTP_200_OK)
async def delete_story_route(
    story_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    success = await pss.delete_story(db, story_id)
    if not success:
        raise HTTPException(status_code=404, detail="Story not found")
    await db.commit()
    return {"message": "Story deleted"}


@router.post("/{story_id}/clone", response_model=StoryOut)
async def clone_story_route(
    story_id: str,
    req: StoryCloneRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    story = await pss.clone_story(db, story_id, req.new_name)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    await db.commit()
    return _story_to_out(story)


@router.patch("/{story_id}/status", response_model=StoryOut)
async def update_status_route(
    story_id: str,
    req: StoryStatusPatchRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    story = await pss.update_status(db, story_id, req.status)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    await db.commit()
    return _story_to_out(story)


# ─── Node Routes ───


@router.post("/{story_id}/nodes", status_code=status.HTTP_201_CREATED, response_model=NodeOut)
async def create_node_route(
    story_id: str,
    req: NodeCreateRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    story = await pss.get_story(db, story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    node = await pss.create_node(
        db=db,
        story_id=story_id,
        sequence_index=req.sequence_index,
        theme=req.theme,
        emotion_tone=req.emotion_tone,
        key_event=req.key_event,
        prev_recap=req.prev_recap,
        next_teaser=req.next_teaser,
    )
    await db.commit()
    return _node_to_out(node)


@router.get("/{story_id}/nodes", response_model=List[NodeOut])
async def list_nodes_route(
    story_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    story = await pss.get_story(db, story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    nodes = await pss.list_nodes(db, story_id)
    return [_node_to_out(n) for n in nodes]


@router.post("/{story_id}/nodes/reorder", response_model=List[NodeOut])
async def reorder_nodes_route(
    story_id: str,
    req: ReorderRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    story = await pss.get_story(db, story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    nodes = await pss.reorder_nodes(db, story_id, req.node_order)
    await db.commit()
    return [_node_to_out(n) for n in nodes]


@router.get("/{story_id}/context", response_model=StoryContextResponse)
async def get_story_context_route(
    story_id: str,
    current_node_index: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    context = await pss.get_story_context(db, story_id, current_node_index)
    if context is None:
        raise HTTPException(status_code=404, detail="Story not found")
    return StoryContextResponse(**context)


@router.get("/{story_id}/next-node", response_model=Optional[NodeOut])
async def get_next_available_node_route(
    story_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    story = await pss.get_story(db, story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    node = await pss.get_next_available_node(db, story_id)
    if not node:
        return None
    return _node_to_out(node)


# ─── Standalone Node Routes ───


@router.put("/story-nodes/{node_id}", response_model=NodeOut)
async def update_node_route(
    node_id: str,
    req: NodeUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    update_data = req.model_dump(exclude_unset=True)
    node = await pss.update_node(db, node_id, **update_data)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    await db.commit()
    return _node_to_out(node)


@router.delete("/story-nodes/{node_id}", status_code=status.HTTP_200_OK)
async def delete_node_route(
    node_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    success = await pss.delete_node(db, node_id)
    if not success:
        raise HTTPException(status_code=404, detail="Node not found")
    await db.commit()
    return {"message": "Node deleted"}


@router.post("/story-nodes/{node_id}/bind-content", response_model=NodeOut)
async def bind_content_route(
    node_id: str,
    req: BindContentRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    node = await pss.bind_content_to_node(db, node_id, req.content_draft_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    await db.commit()
    return _node_to_out(node)
