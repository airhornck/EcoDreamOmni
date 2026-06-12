"""LLM Hub Scope Config tests — PRD V2.7.2 §8."""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from src.services import llm_hub as lhs

pytestmark = pytest.mark.asyncio(loop_scope="function")


@pytest_asyncio.fixture
async def db_session(db, skip_if_no_db):
    await lhs.clear_llm_hub_data(db)
    yield db


async def _register_models(db: AsyncSession):
    m1 = await lhs.register_model(
        db, provider="deepseek", model_name="deepseek-chat", api_key="sk-a"
    )
    m2 = await lhs.register_model(
        db, provider="openai", model_name="gpt-4o", api_key="sk-b"
    )
    return m1["id"], m2["id"]


async def test_global_default(db_session: AsyncSession):
    mid1, mid2 = await _register_models(db_session)

    cfg = await lhs.set_global_default(db_session, model_id=mid1, temperature=0.7, timeout=30)
    assert cfg["scope_type"] == "global"
    assert cfg["temperature"] == 0.7

    resolved = await lhs.resolve_model_for_node(db_session, node_id="AnyAgent")
    assert resolved["source"] == "global_default"
    assert resolved["model_id"] == mid1


async def test_node_override_and_remove(db_session: AsyncSession):
    mid1, mid2 = await _register_models(db_session)
    await lhs.set_global_default(db_session, model_id=mid1)

    cfg = await lhs.set_node_override(
        db_session, node_id="ContentForge", model_id=mid2, temperature=0.3
    )
    assert cfg["scope_type"] == "node"
    assert cfg["node_id"] == "ContentForge"

    resolved = await lhs.resolve_model_for_node(db_session, node_id="ContentForge")
    assert resolved["source"] == "override"
    assert resolved["model_id"] == mid2

    ok = await lhs.remove_node_override(db_session, node_id="ContentForge")
    assert ok is True

    resolved2 = await lhs.resolve_model_for_node(db_session, node_id="ContentForge")
    assert resolved2["source"] == "global_default"


async def test_list_scope_configs(db_session: AsyncSession):
    mid1, mid2 = await _register_models(db_session)
    await lhs.set_global_default(db_session, model_id=mid1)
    await lhs.set_node_override(db_session, node_id="PoolPredictor", model_id=mid2)

    configs = await lhs.list_scope_configs(db_session)
    assert len(configs) == 2
    sources = {c["source"] for c in configs}
    assert "global_default" in sources
    assert "override" in sources
