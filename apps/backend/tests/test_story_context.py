"""StoryContext & NextAvailableNode tests — PRD V2.7.2 §11.

上下文生成、next_available_node.
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from src.services import persona_story_service as pss

pytestmark = pytest.mark.asyncio(loop_scope="function")


@pytest_asyncio.fixture
async def db_session(db, skip_if_no_db):
    return db


@pytest_asyncio.fixture
async def story_with_nodes(db_session: AsyncSession):
    story = await pss.create_story(
        db=db_session,
        persona_id="p1",
        name="养猫30天",
        emotion_curve_template="gradual_growth",
    )
    sid = str(story.id)
    await pss.create_node(
        db=db_session, story_id=sid, sequence_index=0,
        theme="接猫回家", emotion_tone="low",
        key_event="从宠物店领养橘猫", next_teaser="准备体检"
    )
    await pss.create_node(
        db=db_session, story_id=sid, sequence_index=1,
        theme="首次体检", emotion_tone="medium",
        key_event="宠物医院全面体检", prev_recap="昨天接回家", next_teaser="疫苗日"
    )
    await pss.create_node(
        db=db_session, story_id=sid, sequence_index=2,
        theme="打疫苗", emotion_tone="high",
        key_event="接种猫三联第一针", prev_recap="体检通过"
    )
    return story


# =============================================================================
# SC-1: 上下文生成
# =============================================================================

async def test_get_story_context(db_session: AsyncSession, story_with_nodes):
    """🔴 获取剧本上下文 — 含前情提要与下集预告."""
    sid = str(story_with_nodes.id)
    ctx = await pss.get_story_context(db_session, sid, current_node_index=1)
    assert ctx is not None
    assert ctx["series_theme"] == "养猫30天"
    assert ctx["current_node"]["theme"] == "首次体检"
    assert ctx["prev_node_summary"] == "从宠物店领养橘猫"
    assert ctx["next_node_teaser"] == "打疫苗"
    assert "渐进上升曲线" in ctx["emotional_arc"]


async def test_get_story_context_first_node(db_session: AsyncSession, story_with_nodes):
    """🔴 首节点上下文 — prev 为空提示."""
    sid = str(story_with_nodes.id)
    ctx = await pss.get_story_context(db_session, sid, current_node_index=0)
    assert ctx["prev_node_summary"] == "（系列开篇）"
    assert ctx["next_node_teaser"] == "首次体检"


async def test_get_story_context_last_node(db_session: AsyncSession, story_with_nodes):
    """🔴 尾节点上下文 — next 为空提示."""
    sid = str(story_with_nodes.id)
    ctx = await pss.get_story_context(db_session, sid, current_node_index=2)
    assert ctx["prev_node_summary"] == "宠物医院全面体检"
    assert ctx["next_node_teaser"] == "（已至结尾）"


# =============================================================================
# SC-2: 下一个可用节点
# =============================================================================

async def test_get_next_available_node(db_session: AsyncSession, story_with_nodes):
    """🔴 返回第一个 content_draft_id 为 NULL 的节点."""
    sid = str(story_with_nodes.id)
    node = await pss.get_next_available_node(db_session, sid)
    assert node is not None
    assert node.sequence_index == 0
    assert node.theme == "接猫回家"

    # 绑定第一个节点后，next_available 应变为第二个
    await pss.bind_content_to_node(db_session, str(node.id), "draft_01")
    next_node = await pss.get_next_available_node(db_session, sid)
    assert next_node is not None
    assert next_node.sequence_index == 1
    assert next_node.theme == "首次体检"
