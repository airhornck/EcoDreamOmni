"""Tests for LLM Hub multi-modal routing — Phase 5 P5-1.

Red-Green TDD for:
  - text / image / video / embedding / multimodal 路由
  - domestic preferred → overseas fallback
  - cross_border_risk marking
  - preferred_provider matching
  - no model available error
  - routing decision logged
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

from src.services import llm_hub as lhs
from src.services.llm_hub import LLMRouter, get_provider_region


# ─── Helpers ───


async def _seed_models(session):
    """Seed test models with modality support."""
    m1 = await lhs.register_model(
        session, "deepseek", "deepseek-chat", "key1",
        modality_support={"text": True, "image": False},
    )
    m2 = await lhs.register_model(
        session, "aliyun", "qwen-vl", "key2",
        modality_support={"text": True, "image": True, "video": False},
    )
    m3 = await lhs.register_model(
        session, "openai", "gpt-4o", "key3",
        modality_support={"text": True, "image": True, "video": True},
    )
    return m1, m2, m3


async def _clear_and_seed():
    from src.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        await lhs.clear_llm_hub_data(session)
        await session.commit()
        await _seed_models(session)
        await session.commit()


# ─── All routing tests in a single event loop ───


def test_llm_router_all():
    """合并所有 LLM 路由测试，避免事件循环冲突."""
    from src.core.database import AsyncSessionLocal

    async def _run_all():
        # 清理 + seed
        async with AsyncSessionLocal() as session:
            await lhs.clear_llm_hub_data(session)
            await session.commit()
            await _seed_models(session)
            await session.commit()

        # 1. text → domestic
        async with AsyncSessionLocal() as session:
            decision = await LLMRouter.route(session, "text")
            assert decision["region"] == "domestic"
            assert decision["cross_border_risk"] is False
            assert decision["provider"] in {"deepseek", "aliyun"}

        # 2. image → domestic multimodal
        async with AsyncSessionLocal() as session:
            decision = await LLMRouter.route(session, "image")
            assert decision["provider"] == "aliyun"
            assert decision["cross_border_risk"] is False

        # 3. video → overseas fallback
        async with AsyncSessionLocal() as session:
            decision = await LLMRouter.route(session, "video")
            assert decision["region"] == "overseas"
            assert decision["cross_border_risk"] is True
            assert decision["provider"] == "openai"

        # 4. preferred_provider
        async with AsyncSessionLocal() as session:
            decision = await LLMRouter.route(session, "text", preferred_provider="deepseek")
            assert decision["provider"] == "deepseek"

        # 5. no model raises
        async with AsyncSessionLocal() as session:
            with pytest.raises(ValueError, match="No active model"):
                await LLMRouter.route(session, "audio")

        # 6. route logs decision
        async with AsyncSessionLocal() as session:
            decision = await lhs.route_model_by_modality(
                session, "video", node_id="test_router"
            )
            assert decision["cross_border_risk"] is True
            logs = await lhs.get_usage_logs(session, node_id="test_router", limit=1)
            assert len(logs) == 1
            assert logs[0]["status"] == "ROUTED"
            assert "cross_border_risk=True" in (logs[0].get("error_message") or "")

    asyncio.run(_run_all())


# ─── Provider region classification ───


def test_get_provider_region():
    assert get_provider_region("deepseek") == "domestic"
    assert get_provider_region("openai") == "overseas"
    assert get_provider_region("unknown") == "overseas"
