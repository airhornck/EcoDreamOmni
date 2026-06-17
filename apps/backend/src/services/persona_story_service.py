"""PersonaStory Service — ORM持久化版本 (PRD V2.7.2 §11).

剧本管理、节点编排、情感曲线、内容绑定.
与 AssetPool / BrandKnowledge / TimelineLibrary 并列的第六大基础功能.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from sqlalchemy import select, func, delete, asc
from sqlalchemy.orm import selectinload

from src.models.persona_story_orm import PersonaStoryORM, StoryNodeORM


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ─── Story helpers ───


def story_to_dict(story: PersonaStoryORM) -> Dict[str, Any]:
    return {
        "id": str(story.id),
        "persona_id": story.persona_id,
        "name": story.name,
        "description": story.description,
        "emotion_curve_template": story.emotion_curve_template,
        "status": story.status,
        "created_at": story.created_at.isoformat() if story.created_at else None,
        "updated_at": story.updated_at.isoformat() if story.updated_at else None,
    }


def node_to_dict(node: StoryNodeORM) -> Dict[str, Any]:
    return {
        "id": str(node.id),
        "story_id": str(node.story_id),
        "sequence_index": node.sequence_index,
        "theme": node.theme,
        "emotion_tone": node.emotion_tone,
        "key_event": node.key_event,
        "prev_recap": node.prev_recap,
        "next_teaser": node.next_teaser,
        "content_draft_id": node.content_draft_id,
        "created_at": node.created_at.isoformat() if node.created_at else None,
        "updated_at": node.updated_at.isoformat() if node.updated_at else None,
    }


# ─── Story CRUD ───


async def create_story(
    db: Any,
    persona_id: str,
    name: str,
    description: Optional[str] = None,
    emotion_curve_template: str = "gradual_growth",
    status: str = "draft",
) -> PersonaStoryORM:
    story = PersonaStoryORM(
        persona_id=persona_id,
        name=name,
        description=description,
        emotion_curve_template=emotion_curve_template,
        status=status,
    )
    db.add(story)
    await db.flush()
    await db.commit()
    await db.refresh(story)
    return story


async def get_story(
    db: Any, story_id: str
) -> Optional[PersonaStoryORM]:
    result = await db.execute(
        select(PersonaStoryORM)
        .options(selectinload(PersonaStoryORM.nodes))
        .where(PersonaStoryORM.id == story_id)
    )
    return result.scalar_one_or_none()


async def list_stories(
    db: Any,
    persona_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> Dict[str, Any]:
    query = select(PersonaStoryORM)
    if persona_id:
        query = query.where(PersonaStoryORM.persona_id == persona_id)
    if status:
        query = query.where(PersonaStoryORM.status == status)

    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar() or 0

    query = (
        query.order_by(asc(PersonaStoryORM.created_at))
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(query)
    items = result.scalars().all()

    return {"items": list(items), "total": total, "limit": limit, "offset": offset}


async def update_story(
    db: Any, story_id: str, **kwargs
) -> Optional[PersonaStoryORM]:
    story = await get_story(db, story_id)
    if not story:
        return None

    for key, value in kwargs.items():
        if key not in {"id", "created_at"} and hasattr(story, key):
            setattr(story, key, value)

    story.updated_at = _now()
    await db.flush()
    await db.commit()
    await db.refresh(story)
    return story


async def delete_story(db: Any, story_id: str) -> bool:
    story = await get_story(db, story_id)
    if not story:
        return False
    await db.delete(story)
    await db.flush()
    await db.commit()
    return True


async def clone_story(
    db: Any, story_id: str, new_name: str
) -> Optional[PersonaStoryORM]:
    """克隆剧本（含全部节点，重置状态为 draft，清空 content_draft_id）."""
    old_story = await get_story(db, story_id)
    if not old_story:
        return None

    new_story = PersonaStoryORM(
        persona_id=old_story.persona_id,
        name=new_name,
        description=old_story.description,
        emotion_curve_template=old_story.emotion_curve_template,
        status="draft",
    )
    db.add(new_story)
    await db.flush()
    await db.commit()
    await db.refresh(new_story)

    # Clone nodes
    for node in old_story.nodes:
        new_node = StoryNodeORM(
            story_id=new_story.id,
            sequence_index=node.sequence_index,
            theme=node.theme,
            emotion_tone=node.emotion_tone,
            key_event=node.key_event,
            prev_recap=node.prev_recap,
            next_teaser=node.next_teaser,
            content_draft_id=None,
        )
        db.add(new_node)

    await db.flush()
    await db.commit()
    await db.refresh(new_story)
    return new_story


async def update_status(
    db: Any, story_id: str, status: str
) -> Optional[PersonaStoryORM]:
    return await update_story(db, story_id, status=status)


# ─── Node CRUD ───


async def create_node(
    db: Any,
    story_id: str,
    sequence_index: int,
    theme: str,
    emotion_tone: str,
    key_event: str,
    prev_recap: Optional[str] = None,
    next_teaser: Optional[str] = None,
    content_draft_id: Optional[str] = None,
) -> StoryNodeORM:
    node = StoryNodeORM(
        story_id=story_id,
        sequence_index=sequence_index,
        theme=theme,
        emotion_tone=emotion_tone,
        key_event=key_event,
        prev_recap=prev_recap,
        next_teaser=next_teaser,
        content_draft_id=content_draft_id,
    )
    db.add(node)
    await db.flush()
    await db.commit()
    await db.refresh(node)
    return node


async def get_node(
    db: Any, node_id: str
) -> Optional[StoryNodeORM]:
    result = await db.execute(
        select(StoryNodeORM).where(StoryNodeORM.id == node_id)
    )
    return result.scalar_one_or_none()


async def list_nodes(
    db: Any, story_id: str
) -> List[StoryNodeORM]:
    result = await db.execute(
        select(StoryNodeORM)
        .where(StoryNodeORM.story_id == story_id)
        .order_by(asc(StoryNodeORM.sequence_index))
    )
    return list(result.scalars().all())


async def update_node(
    db: Any, node_id: str, **kwargs
) -> Optional[StoryNodeORM]:
    node = await get_node(db, node_id)
    if not node:
        return None

    for key, value in kwargs.items():
        if key not in {"id", "created_at", "story_id"} and hasattr(node, key):
            setattr(node, key, value)

    node.updated_at = _now()
    await db.flush()
    await db.commit()
    await db.refresh(node)
    return node


async def delete_node(db: Any, node_id: str) -> bool:
    node = await get_node(db, node_id)
    if not node:
        return False
    await db.delete(node)
    await db.flush()
    await db.commit()
    return True


async def reorder_nodes(
    db: Any, story_id: str, node_order: List[str]
) -> List[StoryNodeORM]:
    """按 node_order（节点ID列表）重新设置 sequence_index.
    
    使用逐节点临时索引避免 (story_id, sequence_index) 唯一约束冲突.
    """

    nodes = await list_nodes(db, story_id)
    node_map = {str(n.id): n for n in nodes}

    # Phase 1: 为所有待重排节点分配不冲突的临时大索引
    temp_offset = 10_000_000
    for idx, node_id in enumerate(node_order):
        node = node_map.get(node_id)
        if node:
            node.sequence_index = temp_offset + idx
    await db.flush()
    await db.commit()

    # Phase 2: 分配最终索引
    for idx, node_id in enumerate(node_order):
        node = node_map.get(node_id)
        if node:
            node.sequence_index = idx
    await db.flush()
    await db.commit()

    return await list_nodes(db, story_id)


# ─── Story context & next available node ───


async def get_story_context(
    db: Any,
    story_id: str,
    current_node_index: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    """获取剧本上下文，用于 ContentForge 生成时的系列化注入.

    Returns:
        {
            "current_node": {...},
            "prev_node_summary": str,
            "next_node_teaser": str,
            "series_theme": str,
            "emotional_arc": str,
        }
    """
    story = await get_story(db, story_id)
    if not story:
        return None

    nodes = await list_nodes(db, story_id)
    if not nodes:
        return {
            "current_node": None,
            "prev_node_summary": "",
            "next_node_teaser": "",
            "series_theme": story.name,
            "emotional_arc": f"剧本《{story.name}》暂无节点",
        }

    # Determine current node
    if current_node_index is not None:
        current = next(
            (n for n in nodes if n.sequence_index == current_node_index), None
        )
    else:
        current = nodes[0]

    if current is None:
        current = nodes[0]

    # Prev / next
    sorted_nodes = sorted(nodes, key=lambda n: n.sequence_index)
    current_idx_in_sorted = next(
        (i for i, n in enumerate(sorted_nodes) if n.id == current.id), 0
    )

    prev_node = (
        sorted_nodes[current_idx_in_sorted - 1]
        if current_idx_in_sorted > 0
        else None
    )
    next_node = (
        sorted_nodes[current_idx_in_sorted + 1]
        if current_idx_in_sorted < len(sorted_nodes) - 1
        else None
    )

    # Emotional arc description
    template = story.emotion_curve_template
    current_idx_in_sorted / max(len(sorted_nodes) - 1, 1)
    if template == "gradual_growth":
        arc_desc = f"渐进上升曲线 — 第 {current_idx_in_sorted + 1}/{len(sorted_nodes)} 节点（情感逐步累积）"
    elif template == "wave":
        arc_desc = f"波浪曲线 — 第 {current_idx_in_sorted + 1}/{len(sorted_nodes)} 节点（起伏交替）"
    elif template == "climax_first":
        arc_desc = f"高潮前置 — 第 {current_idx_in_sorted + 1}/{len(sorted_nodes)} 节点（首集爆发后回落）"
    else:
        arc_desc = f"平稳曲线 — 第 {current_idx_in_sorted + 1}/{len(sorted_nodes)} 节点（情感稳定输出）"

    return {
        "current_node": node_to_dict(current),
        "prev_node_summary": prev_node.key_event if prev_node else "（系列开篇）",
        "next_node_teaser": next_node.theme if next_node else "（已至结尾）",
        "series_theme": story.name,
        "emotional_arc": arc_desc,
    }


async def get_next_available_node(
    db: Any, story_id: str
) -> Optional[StoryNodeORM]:
    """返回该 story 中第一个 content_draft_id 为 NULL 的节点."""
    result = await db.execute(
        select(StoryNodeORM)
        .where(StoryNodeORM.story_id == story_id)
        .where(StoryNodeORM.content_draft_id.is_(None))
        .order_by(asc(StoryNodeORM.sequence_index))
        .limit(1)
    )
    return result.scalar_one_or_none()


async def bind_content_to_node(
    db: Any, node_id: str, content_draft_id: str
) -> Optional[StoryNodeORM]:
    """将内容草稿绑定到剧本节点."""
    return await update_node(db, node_id, content_draft_id=content_draft_id)


# ─── Clear helpers for tests ───


async def clear_persona_stories(db: Any) -> None:
    await db.execute(delete(StoryNodeORM))
    await db.execute(delete(PersonaStoryORM))
    await db.commit()
