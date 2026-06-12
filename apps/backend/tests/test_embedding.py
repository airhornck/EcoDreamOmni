"""Tests for src.core.embedding — P0-2 v4.0 alignment.

Validates:
  - Backend auto-detection and selection
  - APIEmbeddingBackend encode/encode_batch (mocked)
  - BGEEmbeddingBackend encode/encode_batch (mocked or skipped)
  - Dimension reporting
  - Singleton factory behavior
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.embedding import (
    APIEmbeddingBackend,
    BGEEmbeddingBackend,
    get_embedding_backend,
    get_dimension,
    encode,
    encode_batch,
    reset_embedding_backend,
)


@pytest.fixture(autouse=True)
def _reset_backend():
    """Auto-reset singleton before each test."""
    reset_embedding_backend()
    yield
    reset_embedding_backend()


# ─── Backend Dimension ───

def test_api_backend_dimension():
    backend = APIEmbeddingBackend()
    assert backend.dimension == 1536


def test_bge_backend_dimension():
    backend = BGEEmbeddingBackend()
    assert backend.dimension == 768


# ─── API Backend (Mocked) ───

def _make_async_http_client(mock_response):
    """Create an AsyncMock that works as httpx.AsyncClient context manager."""
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.post = AsyncMock(return_value=mock_response)
    return mock_client


@pytest.mark.asyncio
async def test_api_encode_success():
    backend = APIEmbeddingBackend()
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"data": [{"embedding": [0.1, 0.2, 0.3]}]}

    with patch("httpx.AsyncClient", return_value=_make_async_http_client(mock_response)):
        with patch.object(backend, "_is_available", return_value=True):
            result = await backend.encode("hello")
            assert result == [0.1, 0.2, 0.3]


@pytest.mark.asyncio
async def test_api_encode_no_api_key():
    backend = APIEmbeddingBackend()
    with patch.object(backend, "_is_available", return_value=False):
        result = await backend.encode("hello")
        assert result is None


@pytest.mark.asyncio
async def test_api_encode_batch_success():
    backend = APIEmbeddingBackend()
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "data": [
            {"index": 1, "embedding": [0.4, 0.5]},
            {"index": 0, "embedding": [0.1, 0.2]},
        ]
    }

    with patch("httpx.AsyncClient", return_value=_make_async_http_client(mock_response)):
        with patch.object(backend, "_is_available", return_value=True):
            results = await backend.encode_batch(["a", "b"])
            assert len(results) == 2
            assert results[0] == [0.1, 0.2]
            assert results[1] == [0.4, 0.5]


# ─── BGE Backend (Mocked) ───

@pytest.mark.asyncio
async def test_bge_encode_not_available():
    backend = BGEEmbeddingBackend()
    with patch.object(backend, "_is_available", return_value=False):
        result = await backend.encode("hello")
        assert result is None


@pytest.mark.asyncio
async def test_bge_encode_batch_not_available():
    backend = BGEEmbeddingBackend()
    with patch.object(backend, "_is_available", return_value=False):
        results = await backend.encode_batch(["a", "b"])
        assert results == [None, None]


# ─── Factory ───

def test_factory_auto_prefers_bge_when_available():
    with patch.object(BGEEmbeddingBackend, "_is_available", return_value=True):
        backend = get_embedding_backend()
        assert isinstance(backend, BGEEmbeddingBackend)


def test_factory_fallback_to_api_when_bge_unavailable():
    with patch.object(BGEEmbeddingBackend, "_is_available", return_value=False):
        backend = get_embedding_backend()
        assert isinstance(backend, APIEmbeddingBackend)


def test_factory_explicit_api():
    backend = get_embedding_backend(preferred="api")
    assert isinstance(backend, APIEmbeddingBackend)


def test_factory_explicit_bge():
    backend = get_embedding_backend(preferred="bge")
    assert isinstance(backend, BGEEmbeddingBackend)


def test_factory_singleton():
    b1 = get_embedding_backend(preferred="api")
    b2 = get_embedding_backend(preferred="api")
    assert b1 is b2


# ─── Convenience Wrappers ───

@pytest.mark.asyncio
async def test_encode_wrapper():
    mock_backend = MagicMock()
    mock_backend.encode = AsyncMock(return_value=[0.1, 0.2])

    with patch("src.core.embedding.get_embedding_backend", return_value=mock_backend):
        result = await encode("test")
        assert result == [0.1, 0.2]


@pytest.mark.asyncio
async def test_encode_batch_wrapper():
    mock_backend = MagicMock()
    mock_backend.encode_batch = AsyncMock(return_value=[[0.1], [0.2]])

    with patch("src.core.embedding.get_embedding_backend", return_value=mock_backend):
        results = await encode_batch(["a", "b"])
        assert results == [[0.1], [0.2]]


def test_get_dimension_wrapper():
    mock_backend = MagicMock()
    mock_backend.dimension = 768

    with patch("src.core.embedding.get_embedding_backend", return_value=mock_backend):
        assert get_dimension() == 768
