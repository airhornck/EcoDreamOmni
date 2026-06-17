"""AI Conversation Streaming API — SSE endpoint for Copilot chat.

Routes:
  POST /api/v1/ai/conversations/stream  # SSE streaming chat

Response format (SSE):
  data: {"content": "片段文本"}
  data: {"action_card": {...}}   # optional, at end
  data: [DONE]
"""

import json
import logging
from typing import Any, AsyncGenerator, Dict, Optional

import httpx
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

from src.core.config import settings
from src.core.database import get_db
from src.core.dependencies import get_current_user
from src.models.user import User
from src.services.llm_hub import decrypt_api_key, resolve_model_for_node

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/ai", tags=["ai-conversation"])


# ─── Schemas ───

class ConversationRequest(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None


# ─── System Prompt Builder ───

_COPILOT_SYSTEM_PROMPT = """你是 EcoDream Omni 的 AI Copilot，一个专业的社交媒体内容运营智能助手。

你的能力包括：
- 内容创作：根据选题或主题生成小红书、抖音、视频号等平台的内容文案
- 审核协助：分析内容合规风险，给出修改建议
- 数据分析：解读运营数据，发现趋势和异常
- 任务执行：协助创建任务、审核内容、管理发布计划

回复要求：
- 使用中文，简洁专业
- 必要时给出可操作的建议
- 如果不确定，直接说明，不要编造"""


def _build_system_prompt(context: Optional[Dict[str, Any]]) -> str:
    page = (context or {}).get("page", "unknown")
    selected = (context or {}).get("selected_items", [])
    parts = [_COPILOT_SYSTEM_PROMPT]
    parts.append(f"\n当前页面: {page}")
    if selected:
        parts.append(f"用户选中内容: {', '.join(str(s) for s in selected)}")
    return "\n".join(parts)


# ─── LLM Config Resolution ───

async def _resolve_llm_config(db: AsyncSession) -> Dict[str, Any]:
    """Resolve LLM config: try LLM Hub first, fallback to env."""
    try:
        hub_result = await resolve_model_for_node(db, "copilot_chat")
        if hub_result.get("source") != "none":
            # Need full model info for api_key and endpoint
            from sqlalchemy import select
            from src.models.llm_hub_orm import LLMModelORM

            model_result = await db.execute(
                select(LLMModelORM).where(
                    LLMModelORM.id == hub_result["model_id"]
                )
            )
            model = model_result.scalar_one_or_none()
            if model:
                return {
                    "provider": model.provider,
                    "model_name": model.model_name,
                    "api_key": decrypt_api_key(model.api_key_encrypted),
                    "endpoint_url": model.endpoint_base_url or _default_endpoint(model.provider),
                    "temperature": hub_result.get("temperature", 0.8),
                }
    except Exception as exc:
        logger.warning("LLM Hub resolution failed, falling back to env: %s", exc)

    # Fallback to env-based DeepSeek
    api_key = settings.DEEPSEEK_API_KEY
    if not api_key:
        raise RuntimeError("No LLM config available: LLM Hub has no model and DEEPSEEK_API_KEY is not set")
    return {
        "provider": "deepseek",
        "model_name": settings.DEFAULT_LLM_MODEL or "deepseek-chat",
        "api_key": api_key,
        "endpoint_url": "https://api.deepseek.com/chat/completions",
        "temperature": 0.8,
    }


def _default_endpoint(provider: str) -> str:
    endpoints = {
        "deepseek": "https://api.deepseek.com/chat/completions",
        "openai": "https://api.openai.com/v1/chat/completions",
        "anthropic": "https://api.anthropic.com/v1/messages",
        "aliyun": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        "zhipu": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        "kimi": "https://api.moonshot.cn/v1/chat/completions",
        "xunfei": "https://spark-api-open.xf-yun.com/v1/chat/completions",
    }
    return endpoints.get(provider, endpoints["deepseek"])


# ─── Stream Generator ───

async def _stream_llm(
    message: str,
    context: Optional[Dict[str, Any]],
    db: AsyncSession,
) -> AsyncGenerator[str, None]:
    config = await _resolve_llm_config(db)
    provider = config["provider"]
    model_name = config["model_name"]
    api_key = config["api_key"]
    endpoint_url = config["endpoint_url"]
    temperature = config["temperature"]

    system_prompt = _build_system_prompt(context)

    if provider == "anthropic":
        payload = {
            "model": model_name,
            "messages": [
                {"role": "user", "content": f"{system_prompt}\n\n{message}"},
            ],
            "temperature": temperature,
            "max_tokens": 2000,
            "stream": True,
        }
    else:
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ],
            "temperature": temperature,
            "max_tokens": 2000,
            "stream": True,
        }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                "POST", endpoint_url, headers=headers, json=payload
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    chunk = line[6:]
                    if chunk == "[DONE]":
                        yield "data: [DONE]\n\n"
                        break
                    try:
                        data = json.loads(chunk)
                        if provider == "anthropic":
                            # Anthropic streaming format
                            delta = data.get("delta", {})
                            text = delta.get("text", "")
                            if text:
                                yield f"data: {json.dumps({'content': text}, ensure_ascii=False)}\n\n"
                        else:
                            # OpenAI-compatible streaming format
                            choices = data.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield f"data: {json.dumps({'content': content}, ensure_ascii=False)}\n\n"
                    except json.JSONDecodeError:
                        continue
    except httpx.HTTPStatusError as exc:
        logger.error("LLM HTTP error: %s - %s", exc.response.status_code, exc.response.text)
        error_msg = f"LLM服务错误: HTTP {exc.response.status_code}"
        try:
            err_data = exc.response.json()
            error_msg = err_data.get("error", {}).get("message", error_msg)
        except Exception:
            pass
        error_content = "\n\n[错误] " + error_msg
        yield f"data: {json.dumps({'content': error_content}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"
    except Exception as exc:
        logger.exception("LLM streaming error")
        error_content = "\n\n[错误] " + str(exc)
        yield f"data: {json.dumps({'content': error_content}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"


# ─── Endpoint ───

@router.post("/conversations/stream")
async def conversation_stream(
    req: ConversationRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """SSE streaming endpoint for AI Copilot chat."""
    return StreamingResponse(
        _stream_llm(req.message, req.context, db),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
