"""Tests for src.services.rag_service — P0-2 v4.0 alignment.

Validates:
  - RAGService.index() — generates embedding and persists to ORM
  - RAGService.search() — pgvector semantic search with mocked DB
  - RAGService.index_batch() — batch indexing
  - RAGService.search_by_entry_id() — similarity by existing entry
  - Tenant isolation on all queries

Note: Tests mock AsyncSession and embedding to avoid requiring PostgreSQL.
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.services.rag_service import RAGService


# ─── Helpers ───

def _make_mock_entry(entry_id, embedding=None, tenant_id="t1"):
    entry = MagicMock()
    entry.id = entry_id
    entry.embedding = embedding
    entry.tenant_id = tenant_id
    return entry


def _make_mock_session():
    """Create a mock AsyncSession with chainable execute()."""
    session = AsyncMock()
    return session


# ─── Index ───

@pytest.mark.asyncio
async def test_index_success():
    entry_id = uuid4()
    mock_entry = _make_mock_entry(entry_id)

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_entry

    session = MagicMock()
    session.execute = AsyncMock(return_value=mock_result)
    session.commit = AsyncMock()

    with patch("src.services.rag_service.encode", new=AsyncMock(return_value=[0.1, 0.2, 0.3])):
        rag = RAGService(session)
        result = await rag.index(entry_id, "test content", tenant_id="t1")

    assert result is True
    assert mock_entry.embedding == [0.1, 0.2, 0.3]
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_index_embedding_failure():
    entry_id = uuid4()
    session = MagicMock()

    with patch("src.services.rag_service.encode", new=AsyncMock(return_value=None)):
        rag = RAGService(session)
        result = await rag.index(entry_id, "test content")

    assert result is False
    session.execute.assert_not_called()


@pytest.mark.asyncio
async def test_index_entry_not_found():
    entry_id = uuid4()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None

    session = MagicMock()
    session.execute = AsyncMock(return_value=mock_result)

    with patch("src.services.rag_service.encode", new=AsyncMock(return_value=[0.1, 0.2])):
        rag = RAGService(session)
        result = await rag.index(entry_id, "test content", tenant_id="t1")

    assert result is False


# ─── Index Batch ───

@pytest.mark.asyncio
async def test_index_batch_partial_success():
    id1, id2 = uuid4(), uuid4()
    entry1 = _make_mock_entry(id1)
    entry2 = _make_mock_entry(id2)

    call_count = [0]

    def _mock_execute(*args, **kwargs):
        call_count[0] += 1
        mock_result = MagicMock()
        if call_count[0] == 1:
            mock_result.scalar_one_or_none.return_value = entry1
        elif call_count[0] == 2:
            mock_result.scalar_one_or_none.return_value = entry2
        else:
            mock_result.scalar_one_or_none.return_value = None
        return mock_result

    session = MagicMock()
    session.execute = AsyncMock(side_effect=_mock_execute)
    session.commit = AsyncMock()

    with patch("src.services.rag_service.encode_batch", new=AsyncMock(return_value=[[0.1], None])):
        rag = RAGService(session)
        results = await rag.index_batch(
            [{"entry_id": id1, "content": "a"}, {"entry_id": id2, "content": "b"}],
            tenant_id="t1",
        )

    assert results[str(id1)] is True
    assert results[str(id2)] is False
    assert entry1.embedding == [0.1]


# ─── Search ───

@pytest.mark.asyncio
async def test_search_no_embedding():
    session = MagicMock()
    with patch("src.services.rag_service.encode", new=AsyncMock(return_value=None)):
        rag = RAGService(session)
        results = await rag.search("query")
        assert results == []


@pytest.mark.asyncio
async def test_search_with_results():
    entry_id = uuid4()
    mock_entry = _make_mock_entry(entry_id, embedding=[0.1, 0.2, 0.3], tenant_id="t1")

    mock_raw_result = MagicMock()
    mock_raw_result.fetchall.return_value = [(entry_id, 0.95)]

    mock_entry_result = MagicMock()
    mock_entry_result.scalars.return_value.all.return_value = [mock_entry]

    call_count = [0]

    def _mock_execute(*args, **kwargs):
        call_count[0] += 1
        if call_count[0] == 1:
            return mock_raw_result
        return mock_entry_result

    session = MagicMock()
    session.execute = AsyncMock(side_effect=_mock_execute)

    with patch("src.services.rag_service.encode", new=AsyncMock(return_value=[0.1, 0.2, 0.3])):
        with patch("src.services.rag_service.get_dimension", return_value=3):
            rag = RAGService(session)
            results = await rag.search("query", top_k=5, tenant_id="t1")

    assert len(results) == 1
    assert results[0]["similarity"] == 0.95


@pytest.mark.asyncio
async def test_search_tenant_isolation():
    """Verify tenant_id is included in SQL params."""
    session = MagicMock()
    mock_raw = MagicMock()
    mock_raw.fetchall.return_value = []
    session.execute = AsyncMock(return_value=mock_raw)

    with patch("src.services.rag_service.encode", new=AsyncMock(return_value=[0.1])):
        with patch("src.services.rag_service.get_dimension", return_value=1):
            rag = RAGService(session)
            await rag.search("query", tenant_id="tenant_abc")

    # Verify execute was called with tenant_id in params
    call_args = session.execute.call_args_list
    assert len(call_args) > 0
    _, kwargs = call_args[0]
    params = kwargs.get("parameters", kwargs.get("params", {}))
    # If params not in kwargs, check positional args
    if not params and len(call_args[0][0]) > 1:
        params = call_args[0][0][1]
    assert params.get("tenant_id") == "tenant_abc"


# ─── Search by Entry ID ───

@pytest.mark.asyncio
async def test_search_by_entry_id_success():
    source_id = uuid4()
    similar_id = uuid4()
    source_entry = _make_mock_entry(source_id, embedding=[0.1, 0.2], tenant_id="t1")
    similar_entry = _make_mock_entry(similar_id, embedding=[0.15, 0.25], tenant_id="t1")

    mock_source_result = MagicMock()
    mock_source_result.scalar_one_or_none.return_value = source_entry

    mock_raw_result = MagicMock()
    mock_raw_result.fetchall.return_value = [(similar_id, 0.98)]

    mock_similar_result = MagicMock()
    mock_similar_result.scalars.return_value.all.return_value = [similar_entry]

    call_count = [0]

    def _mock_execute(*args, **kwargs):
        call_count[0] += 1
        if call_count[0] == 1:
            return mock_source_result
        if call_count[0] == 2:
            return mock_raw_result
        return mock_similar_result

    session = MagicMock()
    session.execute = AsyncMock(side_effect=_mock_execute)

    with patch("src.services.rag_service.get_dimension", return_value=2):
        rag = RAGService(session)
        results = await rag.search_by_entry_id(source_id, top_k=5, tenant_id="t1")

    assert len(results) == 1
    assert results[0]["similarity"] == 0.98


@pytest.mark.asyncio
async def test_search_by_entry_id_no_embedding():
    entry_id = uuid4()
    mock_entry = _make_mock_entry(entry_id, embedding=None)

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_entry

    session = MagicMock()
    session.execute = AsyncMock(return_value=mock_result)

    rag = RAGService(session)
    results = await rag.search_by_entry_id(entry_id)
    assert results == []
