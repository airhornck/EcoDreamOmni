"""Unified LLM Client — W15+ integration with LLM Hub.

Replaces raw httpx calls in content_generator and other consumers.
- Resolves model config from LLM Hub
- Handles provider-specific payload formatting
- Auto-logs usage after every call
"""

import time
from typing import Any, Dict, List, Optional

import httpx

from src.core.config import settings
from src.services.llm_hub import decrypt_api_key, log_usage, resolve_model_for_node


class LLMClient:
    """Unified LLM caller with automatic usage logging."""

    async def call(
        self,
        system_prompt: str,
        user_prompt: str,
        db=None,
        node_id: str = "content_generation",
        llm_config: Optional[dict] = None,
        max_tokens: int = 2000,
    ) -> str:
        """Call LLM with unified interface.

        Args:
            system_prompt: System prompt text
            user_prompt: User prompt text
            db: AsyncSession for LLM Hub resolution/logging (optional)
            node_id: Node identifier for scope resolution and logging
            llm_config: Pre-resolved config dict (bypasses LLM Hub resolution)
            max_tokens: Max output tokens

        Returns:
            LLM response content string
        """
        resolved = llm_config
        model_id = "unknown"

        if resolved is None and db is not None:
            hub_result = await resolve_model_for_node(db, node_id)
            if hub_result.get("source") != "none":
                model_info = hub_result.get("model_info")
                if model_info:
                    model_id = str(hub_result.get("model_id", "unknown"))
                    resolved = {
                        "provider": model_info.get("provider", "deepseek"),
                        "model_name": model_info.get("model_name", "deepseek-chat"),
                        "api_key": decrypt_api_key(model_info["api_key_encrypted"]),
                        "endpoint_url": model_info.get("endpoint_base_url") or self._default_endpoint(
                            model_info.get("provider", "deepseek")
                        ),
                        "temperature": hub_result.get("temperature", 0.8),
                    }

        if resolved is None:
            # Fallback to env-based DeepSeek
            api_key = settings.DEEPSEEK_API_KEY
            if not api_key:
                raise RuntimeError("No LLM config available: LLM Hub has no model and DEEPSEEK_API_KEY is not set")
            resolved = {
                "provider": "deepseek",
                "model_name": settings.DEFAULT_LLM_MODEL or "deepseek-chat",
                "api_key": api_key,
                "endpoint_url": "https://api.deepseek.com/chat/completions",
                "temperature": 0.8,
            }
            model_id = "env-deepseek"

        provider = resolved.get("provider", "deepseek")
        model_name = resolved.get("model_name", settings.DEFAULT_LLM_MODEL or "deepseek-chat")
        api_key = resolved["api_key"]
        endpoint_url = resolved.get("endpoint_url", self._default_endpoint(provider))
        temperature = resolved.get("temperature", 0.8)

        payload = self._build_payload(
            provider=provider,
            model_name=model_name,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        start_time = time.perf_counter()
        status = "success"
        error_msg = None
        response_text = ""

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(endpoint_url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                response_text = self._extract_content(provider, data)
        except Exception as e:
            status = "error"
            error_msg = str(e)
            raise
        finally:
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            # Approximate token counts for logging
            input_tokens = len(system_prompt) + len(user_prompt)
            output_tokens = len(response_text)

            if db is not None:
                try:
                    await log_usage(
                        db=db,
                        model_id=model_id,
                        node_id=node_id,
                        provider_region="domestic" if provider in {"deepseek", "aliyun", "baidu", "zhipu", "kimi", "xunfei"} else "overseas",
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        latency_ms=latency_ms,
                        status=status,
                        error=error_msg,
                    )
                except Exception:
                    # Don't let logging failures break the flow
                    pass

        return response_text

    def _default_endpoint(self, provider: str) -> str:
        endpoints = {
            "deepseek": "https://api.deepseek.com/chat/completions",
            "openai": "https://api.openai.com/v1/chat/completions",
            "anthropic": "https://api.anthropic.com/v1/messages",
        }
        return endpoints.get(provider, endpoints["deepseek"])

    def _build_payload(
        self,
        provider: str,
        model_name: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> Dict[str, Any]:
        if provider == "anthropic":
            return {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
        return {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
        }

    def _extract_content(self, provider: str, data: Dict) -> str:
        if provider == "anthropic":
            return data.get("content", [{}])[0].get("text", "")
        return data["choices"][0]["message"]["content"]


# Global client instance
llm_client = LLMClient()
