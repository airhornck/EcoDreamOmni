"""Embedding service — unified interface for text-to-vector generation.

Supports multiple backends:
  1. API-based (OpenAI / DeepSeek) — 1536-dim, requires API key
  2. Local BGE-M3 — 768-dim, requires `sentence-transformers` package

Backend selection priority:
  1. Explicit `backend` parameter
  2. `EMBEDDING_BACKEND` env var
  3. Auto-detect: BGE-M3 if package available, else API fallback

P0-2 v4.0 alignment:
  - BGE-M3 as preferred local embedding (768-dim)
  - API embedding as fallback (1536-dim)
  - Unified async interface regardless of backend
"""

import os
from abc import ABC, abstractmethod
from typing import List, Optional

import httpx

from src.core.config import settings

DEFAULT_DIM_API = 1536
DEFAULT_DIM_LOCAL = 768
DEFAULT_BGE_MODEL = "BAAI/bge-m3"
TIMEOUT = 30


class EmbeddingBackend(ABC):
    """Abstract embedding backend."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        ...

    @abstractmethod
    async def encode(self, text: str) -> Optional[List[float]]:
        ...

    @abstractmethod
    async def encode_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        ...


class APIEmbeddingBackend(EmbeddingBackend):
    """OpenAI / DeepSeek API embedding backend."""

    def __init__(self, model: Optional[str] = None):
        self.api_key = getattr(settings, "OPENAI_API_KEY", "") or os.environ.get("OPENAI_API_KEY", "")
        self.base_url = "https://api.openai.com/v1"
        self.model = model or "text-embedding-3-small"

        if not self.api_key:
            self.api_key = getattr(settings, "DEEPSEEK_API_KEY", "") or os.environ.get("DEEPSEEK_API_KEY", "")
            self.base_url = "https://api.deepseek.com/v1"
            self.model = model or "deepseek-embedding"

    @property
    def dimension(self) -> int:
        return DEFAULT_DIM_API

    def _is_available(self) -> bool:
        return bool(self.api_key)

    async def encode(self, text: str) -> Optional[List[float]]:
        if not self._is_available():
            return None
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                response = await client.post(
                    f"{self.base_url}/embeddings",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={"input": text, "model": self.model, "encoding_format": "float"},
                )
                response.raise_for_status()
                return response.json()["data"][0]["embedding"]
        except Exception:
            return None

    async def encode_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        if not self._is_available():
            return [None] * len(texts)
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                response = await client.post(
                    f"{self.base_url}/embeddings",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={"input": texts, "model": self.model, "encoding_format": "float"},
                )
                response.raise_for_status()
                data = response.json()["data"]
                embeddings = sorted(data, key=lambda x: x["index"])
                return [e["embedding"] for e in embeddings]
        except Exception:
            return [None] * len(texts)


class BGEEmbeddingBackend(EmbeddingBackend):
    """Local BGE-M3 embedding backend (768-dim).

    Requires: pip install sentence-transformers
    """

    _model = None

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or DEFAULT_BGE_MODEL
        self._ensure_model()

    def _ensure_model(self):
        if BGEEmbeddingBackend._model is None:
            try:
                from sentence_transformers import SentenceTransformer

                BGEEmbeddingBackend._model = SentenceTransformer(self.model_name)
            except ImportError:
                BGEEmbeddingBackend._model = None

    @property
    def dimension(self) -> int:
        return DEFAULT_DIM_LOCAL

    def _is_available(self) -> bool:
        return BGEEmbeddingBackend._model is not None

    async def encode(self, text: str) -> Optional[List[float]]:
        if not self._is_available():
            return None
        # SentenceTransformer encode is synchronous; run in thread pool
        import asyncio

        loop = asyncio.get_event_loop()
        emb = await loop.run_in_executor(None, BGEEmbeddingBackend._model.encode, text)
        return emb.tolist()

    async def encode_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        if not self._is_available():
            return [None] * len(texts)
        import asyncio

        loop = asyncio.get_event_loop()
        embs = await loop.run_in_executor(None, BGEEmbeddingBackend._model.encode, texts)
        return [e.tolist() for e in embs]


# ─── Singleton factory ───

_embedding_backend: Optional[EmbeddingBackend] = None


def get_embedding_backend(preferred: Optional[str] = None) -> EmbeddingBackend:
    """Get or create the embedding backend singleton.

    Args:
        preferred: "bge" | "api" | None (auto-detect)
    """
    global _embedding_backend
    if _embedding_backend is not None:
        return _embedding_backend

    backend_pref = preferred or os.environ.get("EMBEDDING_BACKEND", "auto")

    if backend_pref == "bge":
        _embedding_backend = BGEEmbeddingBackend()
    elif backend_pref == "api":
        _embedding_backend = APIEmbeddingBackend()
    else:
        # Auto-detect: try BGE first, fallback to API
        bge = BGEEmbeddingBackend()
        if bge._is_available():
            _embedding_backend = bge
        else:
            _embedding_backend = APIEmbeddingBackend()

    return _embedding_backend


def reset_embedding_backend() -> None:
    """Reset singleton (mainly for testing)."""
    global _embedding_backend
    _embedding_backend = None


# ─── Convenience wrappers ───

async def encode(text: str, backend: Optional[str] = None) -> Optional[List[float]]:
    """Generate embedding for a single text."""
    return await get_embedding_backend(backend).encode(text)


async def encode_batch(texts: List[str], backend: Optional[str] = None) -> List[Optional[List[float]]]:
    """Generate embeddings for a batch of texts."""
    return await get_embedding_backend(backend).encode_batch(texts)


def get_dimension(backend: Optional[str] = None) -> int:
    """Return the dimension of the current backend."""
    return get_embedding_backend(backend).dimension
