"""LLM Hub Usage Logs tests — PRD V2.7.2 §8."""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from src.services import llm_hub as lhs

pytestmark = pytest.mark.asyncio(loop_scope="function")


@pytest_asyncio.fixture
async def db_session(db, skip_if_no_db):
    await lhs.clear_llm_hub_data(db)
    yield db


async def _register_model(db: AsyncSession):
    m = await lhs.register_model(
        db, provider="deepseek", model_name="deepseek-chat", api_key="sk-a"
    )
    return m["id"]


async def test_log_usage_write(db_session: AsyncSession):
    mid = await _register_model(db_session)
    log = await lhs.log_usage(
        db=db_session,
        model_id=mid,
        node_id="ContentForge",
        provider_region="domestic",
        input_tokens=100,
        output_tokens=50,
        latency_ms=120,
        status="success",
    )
    assert log["model_id"] == mid
    assert log["node_id"] == "ContentForge"
    assert log["status"] == "success"


async def test_get_usage_logs_filter(db_session: AsyncSession):
    mid = await _register_model(db_session)
    await lhs.log_usage(
        db=db_session,
        model_id=mid,
        node_id="NodeA",
        provider_region="domestic",
        input_tokens=10,
        output_tokens=5,
        latency_ms=10,
        status="success",
    )
    await lhs.log_usage(
        db=db_session,
        model_id=mid,
        node_id="NodeB",
        provider_region="domestic",
        input_tokens=20,
        output_tokens=10,
        latency_ms=20,
        status="error",
    )

    logs = await lhs.get_usage_logs(db=db_session, node_id="NodeA")
    assert len(logs) == 1
    assert logs[0]["node_id"] == "NodeA"

    logs_all = await lhs.get_usage_logs(db=db_session, limit=100)
    assert len(logs_all) == 2
