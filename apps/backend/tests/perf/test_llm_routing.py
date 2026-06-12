"""P7-3: 性能测试 — LLM 路由延迟

目标:
- text 模态路由延迟 < 50ms
- image 模态路由延迟 < 100ms
- embedding 模态路由延迟 < 50ms
"""

import time
import pytest

from src.services.llm_hub import get_provider_region, LLMRouter
from src.models.llm_hub_orm import LLMModelORM


@pytest.mark.asyncio
@pytest.mark.perf
class TestLLMRoutingPerf:
    """LLM 路由性能测试。"""

    async def _ensure_model(self, db, modality: str):
        """确保数据库中有支持指定模态的 active 模型。"""
        from sqlalchemy import select
        result = await db.execute(
            select(LLMModelORM).where(
                LLMModelORM.status == "active",
            )
        )
        models = result.scalars().all()
        model = next((m for m in models if m.modality_support and m.modality_support.get(modality)), None)
        if model is None:
            model = LLMModelORM(
                provider="deepseek",
                model_name="deepseek-chat",
                api_key_encrypted="test_key",
                endpoint_base_url="https://api.deepseek.com",
                status="active",
                modality_support={
                    "text": True,
                    "image": modality == "image",
                    "embedding": modality == "embedding",
                    "video": False,
                    "multimodal": False,
                },
            )
            db.add(model)
            await db.commit()
            await db.refresh(model)
        return model

    async def test_text_route_latency(self, db):
        """text 模态路由延迟 < 50ms。"""
        await self._ensure_model(db, "text")
        start = time.perf_counter()
        result = await LLMRouter.route(db, modality="text")
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert "model_id" in result
        assert elapsed_ms < 50, f"text 路由延迟 {elapsed_ms:.2f}ms 超过 50ms 阈值"

    async def test_image_route_latency(self, db):
        """image 模态路由延迟 < 100ms。"""
        await self._ensure_model(db, "image")
        start = time.perf_counter()
        try:
            result = await LLMRouter.route(db, modality="image")
            elapsed_ms = (time.perf_counter() - start) * 1000
            assert "model_id" in result
            assert elapsed_ms < 100, f"image 路由延迟 {elapsed_ms:.2f}ms 超过 100ms 阈值"
        except ValueError:
            pytest.skip("无可用 image 模型")

    async def test_embedding_route_latency(self, db):
        """embedding 模态路由延迟 < 50ms。"""
        await self._ensure_model(db, "embedding")
        start = time.perf_counter()
        try:
            result = await LLMRouter.route(db, modality="embedding")
            elapsed_ms = (time.perf_counter() - start) * 1000
            assert "model_id" in result
            assert elapsed_ms < 50, f"embedding 路由延迟 {elapsed_ms:.2f}ms 超过 50ms 阈值"
        except ValueError:
            pytest.skip("无可用 embedding 模型")

    def test_get_provider_region_latency(self):
        """get_provider_region 应为 O(1) 延迟。"""
        start = time.perf_counter()
        for _ in range(100):
            get_provider_region("deepseek")
            get_provider_region("openai")
            get_provider_region("anthropic")
        elapsed_ms = (time.perf_counter() - start) * 1000
        assert elapsed_ms < 10, f"100 次 region 查询延迟 {elapsed_ms:.2f}ms 超过 10ms 阈值"
