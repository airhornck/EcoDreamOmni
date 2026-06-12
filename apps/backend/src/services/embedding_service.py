"""Embedding service — lightweight text-to-vector wrapper.

MVP: Uses DeepSeek embedding API (or OpenAI fallback).
Future: Swap for local embedding model (BGE-M3, etc.) via vendor/ml-libraries.
"""

import os
from typing import List, Optional

import httpx

from src.core.config import settings

EMBEDDING_DIM = 1536
DEFAULT_MODEL = "text-embedding-3-small"
TIMEOUT = 30


async def get_embedding(text: str, model: Optional[str] = None) -> Optional[List[float]]:
    """Generate embedding vector for a single text string.

    Returns 1536-dim float list, or None if API unavailable.
    """
    api_key = getattr(settings, "OPENAI_API_KEY", "") or os.environ.get("OPENAI_API_KEY", "")
    base_url = "https://api.openai.com/v1"

    # Fallback to DeepSeek if no OpenAI key
    if not api_key:
        api_key = getattr(settings, "DEEPSEEK_API_KEY", "") or os.environ.get("DEEPSEEK_API_KEY", "")
        base_url = "https://api.deepseek.com/v1"
        model = model or "deepseek-embedding"
    else:
        model = model or DEFAULT_MODEL

    if not api_key:
        return None

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                f"{base_url}/embeddings",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "input": text,
                    "model": model,
                    "encoding_format": "float",
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["data"][0]["embedding"]
    except Exception:
        # Embedding generation failure should NOT block CRUD operations
        return None


async def get_embeddings_batch(texts: List[str], model: Optional[str] = None) -> List[Optional[List[float]]]:
    """Batch embedding generation."""
    api_key = getattr(settings, "OPENAI_API_KEY", "") or os.environ.get("OPENAI_API_KEY", "")
    base_url = "https://api.openai.com/v1"

    if not api_key:
        api_key = getattr(settings, "DEEPSEEK_API_KEY", "") or os.environ.get("DEEPSEEK_API_KEY", "")
        base_url = "https://api.deepseek.com/v1"
        model = model or "deepseek-embedding"
    else:
        model = model or DEFAULT_MODEL

    if not api_key:
        return [None] * len(texts)

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                f"{base_url}/embeddings",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "input": texts,
                    "model": model,
                    "encoding_format": "float",
                },
            )
            response.raise_for_status()
            data = response.json()
            # Sort by index to maintain order
            embeddings = sorted(data["data"], key=lambda x: x["index"])
            return [e["embedding"] for e in embeddings]
    except Exception:
        return [None] * len(texts)
