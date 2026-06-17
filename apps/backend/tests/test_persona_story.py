"""PersonaStory Service ORM tests — PRD V2.7.2 §11.

剧本CRUD、克隆、状态流转.
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from src.services import persona_story_service as pss

pytestmark = pytest.mark.asyncio(loop_scope="function")


@pytest_asyncio.fixture
async def db_session(db, skip_if_no_db):
    return db


# =============================================================================
# PS-1: 剧本CRUD
# =============================================================================

async def test_create_story(db_session: AsyncSession):
    """🔴 创建剧本 — 默认状态 draft."""
    story = await pss.create_story(
        db=db_session,
        persona_id="persona_cat_mom_01",
        name="新手养猫日记",
        description="记录从0开始养猫30天的真实心路",
        emotion_curve_template="gradual_growth",
    )
    assert story.id is not None
    assert story.persona_id == "persona_cat_mom_01"
    assert story.name == "新手养猫日记"
    assert story.status == "draft"
    assert story.emotion_curve_template == "gradual_growth"


async def test_list_stories_by_persona_and_status(db_session: AsyncSession):
    await pss.clear_persona_stories(db_session)
    """🔴 按 persona_id 与 status 筛选列表."""
    await pss.create_story(
        db=db_session, persona_id="p1", name="剧本A", status="draft"
    )
    await pss.create_story(
        db=db_session, persona_id="p1", name="剧本B", status="active"
    )
    await pss.create_story(
        db=db_session, persona_id="p2", name="剧本C", status="draft"
    )

    r1 = await pss.list_stories(db_session, persona_id="p1")
    assert r1["total"] == 2

    r2 = await pss.list_stories(db_session, status="active")
    assert r2["total"] == 1
    assert r2["items"][0].name == "剧本B"


async def test_update_story(db_session: AsyncSession):
    """🔴 更新剧本字段."""
    story = await pss.create_story(
        db=db_session, persona_id="p1", name="旧名称"
    )
    updated = await pss.update_story(
        db_session, str(story.id), name="新名称", description="补充描述"
    )
    assert updated is not None
    assert updated.name == "新名称"
    assert updated.description == "补充描述"


async def test_delete_story(db_session: AsyncSession):
    """🔴 删除剧本（级联删除节点）."""
    story = await pss.create_story(
        db=db_session, persona_id="p1", name="将被删除"
    )
    sid = str(story.id)
    success = await pss.delete_story(db_session, sid)
    assert success is True
    assert await pss.get_story(db_session, sid) is None


# =============================================================================
# PS-2: 克隆与状态流转
# =============================================================================

async def test_clone_story(db_session: AsyncSession):
    """🔴 克隆剧本 — 含节点，状态重置 draft，content_draft_id 清空."""
    story = await pss.create_story(
        db=db_session, persona_id="p1", name="原剧本", emotion_curve_template="wave"
    )
    sid = str(story.id)

    # 添加节点
    await pss.create_node(
        db_session, sid, 0, "第一集", "low", "接到猫咪", content_draft_id="cd_01"
    )
    await pss.create_node(
        db_session, sid, 1, "第二集", "medium", "第一次驱虫", content_draft_id="cd_02"
    )

    cloned = await pss.clone_story(db_session, sid, "克隆剧本")
    assert cloned is not None
    assert cloned.name == "克隆剧本"
    assert cloned.status == "draft"
    assert str(cloned.id) != sid

    cloned_nodes = await pss.list_nodes(db_session, str(cloned.id))
    assert len(cloned_nodes) == 2
    assert cloned_nodes[0].theme == "第一集"
    assert cloned_nodes[0].content_draft_id is None
    assert cloned_nodes[1].theme == "第二集"
    assert cloned_nodes[1].content_draft_id is None


async def test_status_transition(db_session: AsyncSession):
    """🔴 状态流转: draft → active → completed → archived."""
    story = await pss.create_story(db_session, persona_id="p1", name="状态测试")
    sid = str(story.id)

    for st in ("active", "completed", "archived"):
        updated = await pss.update_status(db_session, sid, st)
        assert updated is not None
        assert updated.status == st


async def test_clear_persona_stories(db_session: AsyncSession):
    """🔴 清空数据（测试用）."""
    await pss.create_story(db_session, persona_id="p1", name="清空测试")
    await pss.clear_persona_stories(db_session)
    result = await pss.list_stories(db_session)
    assert result["total"] == 0
