"""LLM Hub Cost Summary tests — PRD V2.7.2 §8."""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from src.services import llm_hub as lhs

pytestmark = pytest.mark.asyncio(loop_scope="function")


@pytest_asyncio.fixture
async def db_session(db, skip_if_no_db):
    await lhs.clear_llm_hub_data(db)
    await lhs.init_pricing_data(db)
    yield db


async def _register_models(db: AsyncSession):
    m1 = await lhs.register_model(
        db, provider="deepseek", model_name="deepseek-chat", api_key="sk-a"
    )
    m2 = await lhs.register_model(
        db, provider="openai", model_name="gpt-4o", api_key="sk-b"
    )
    return m1["id"], m2["id"]


async def test_cost_calculation_formula(db_session: AsyncSession):
    mid1, _ = await _register_models(db_session)
    # deepseek-chat pricing: input 0.001 / 1k, output 0.002 / 1k, CNY
    # log 1000 input + 500 output
    await lhs.log_usage(
        db=db_session,
        model_id=mid1,
        node_id="NodeA",
        provider_region="domestic",
        input_tokens=1000,
        output_tokens=500,
        latency_ms=100,
        status="success",
    )
    summary = await lhs.get_cost_summary(db_session, period_days=7)
    # cost = 1*0.001 + 0.5*0.002 = 0.002
    assert summary["total_calls"] == 1
    assert summary["total_input_tokens"] == 1000
    assert summary["total_output_tokens"] == 500
    assert summary["estimated_cost_cny"] == pytest.approx(0.002, abs=1e-4)
    assert summary["by_model"][0]["cost_cny"] == pytest.approx(0.002, abs=1e-4)


async def test_cost_summary_aggregation_by_dimensions(db_session: AsyncSession):
    mid1, mid2 = await _register_models(db_session)
    # mid1 = deepseek-chat, mid2 = gpt-4o (USD, 0.035/0.105)
    await lhs.log_usage(
        db=db_session,
        model_id=mid1,
        node_id="NodeA",
        provider_region="domestic",
        input_tokens=1000,
        output_tokens=1000,
        latency_ms=100,
        status="success",
    )
    await lhs.log_usage(
        db=db_session,
        model_id=mid2,
        node_id="NodeB",
        provider_region="overseas",
        input_tokens=2000,
        output_tokens=1000,
        latency_ms=200,
        status="success",
    )
    summary = await lhs.get_cost_summary(db_session, period_days=7)
    assert summary["total_calls"] == 2
    assert len(summary["by_model"]) == 2
    assert len(summary["by_node"]) == 2
    assert len(summary["trend"]) >= 1
    # gpt-4o cost = 2*0.035 + 1*0.105 = 0.175 USD -> 1.26 CNY
    gpt4o = next(m for m in summary["by_model"] if m["model_name"] == "gpt-4o")
    assert gpt4o["cost_cny"] == pytest.approx(1.26, abs=1e-2)
