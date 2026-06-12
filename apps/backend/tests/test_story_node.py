"""StoryNode Service ORM tests — PRD V2.7.2 §11.

节点CRUD、排序、内容绑定.
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
async def sample_story(db_session: AsyncSession):
    story = await pss.create_story(
        db=db_session, persona_id="p1", name="节点测试剧本"
    )
    return story


# =============================================================================
# SN-1: 节点CRUD
# =============================================================================

async def test_create_and_list_nodes(db_session: AsyncSession, sample_story):
    """🔴 创建节点并列表查询."""
    sid = str(sample_story.id)
    n1 = await pss.create_node(
        db=db_session,
        story_id=sid,
        sequence_index=0,
        theme="第一集：接猫回家",
        emotion_tone="low",
        key_event="从宠物店接回三个月大的橘猫",
        prev_recap=None,
        next_teaser="明天带它做体检",
    )
    n2 = await pss.create_node(
        db=db_session,
        story_id=sid,
        sequence_index=1,
        theme="第二集：首次体检",
        emotion_tone="medium",
        key_event="去宠物医院做新猫入户体检",
        prev_recap="昨天刚接回家",
        next_teaser="一周后打疫苗",
    )

    nodes = await pss.list_nodes(db_session, sid)
    assert len(nodes) == 2
    assert nodes[0].sequence_index == 0
    assert nodes[0].theme == "第一集：接猫回家"
    assert nodes[1].emotion_tone == "medium"
    assert nodes[1].prev_recap == "昨天刚接回家"


async def test_update_node(db_session: AsyncSession, sample_story):
    """🔴 更新节点字段."""
    sid = str(sample_story.id)
    node = await pss.create_node(
        db=db_session, story_id=sid, sequence_index=0,
        theme="旧主题", emotion_tone="low", key_event="旧事件"
    )
    updated = await pss.update_node(
        db_session, str(node.id), theme="新主题", emotion_tone="high"
    )
    assert updated is not None
    assert updated.theme == "新主题"
    assert updated.emotion_tone == "high"
    assert updated.key_event == "旧事件"


async def test_delete_node(db_session: AsyncSession, sample_story):
    """🔴 删除节点."""
    sid = str(sample_story.id)
    node = await pss.create_node(
        db=db_session, story_id=sid, sequence_index=0,
        theme="将被删", emotion_tone="low", key_event="..."
    )
    nid = str(node.id)
    success = await pss.delete_node(db_session, nid)
    assert success is True
    assert await pss.get_node(db_session, nid) is None


# =============================================================================
# SN-2: 节点排序
# =============================================================================

async def test_reorder_nodes(db_session: AsyncSession, sample_story):
    """🔴 重新排序节点."""
    sid = str(sample_story.id)
    n1 = await pss.create_node(
        db=db_session, story_id=sid, sequence_index=0,
        theme="A", emotion_tone="low", key_event="..."
    )
    n2 = await pss.create_node(
        db=db_session, story_id=sid, sequence_index=1,
        theme="B", emotion_tone="medium", key_event="..."
    )
    n3 = await pss.create_node(
        db=db_session, story_id=sid, sequence_index=2,
        theme="C", emotion_tone="high", key_event="..."
    )

    # 逆序
    nodes = await pss.reorder_nodes(
        db_session, sid, [str(n3.id), str(n2.id), str(n1.id)]
    )
    assert nodes[0].theme == "C"
    assert nodes[0].sequence_index == 0
    assert nodes[1].theme == "B"
    assert nodes[1].sequence_index == 1
    assert nodes[2].theme == "A"
    assert nodes[2].sequence_index == 2


# =============================================================================
# SN-3: 内容绑定
# =============================================================================

async def test_bind_content_to_node(db_session: AsyncSession, sample_story):
    """🔴 将内容草稿绑定到节点."""
    sid = str(sample_story.id)
    node = await pss.create_node(
        db=db_session, story_id=sid, sequence_index=0,
        theme="绑定测试", emotion_tone="low", key_event="..."
    )
    updated = await pss.bind_content_to_node(
        db_session, str(node.id), "draft_12345"
    )
    assert updated is not None
    assert updated.content_draft_id == "draft_12345"
