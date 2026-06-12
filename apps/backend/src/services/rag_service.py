"""RAG service — vector indexing and semantic search via pgvector.

P0-2 v4.0 alignment:
  - Async SQLAlchemy operations
  - Tenant isolation on all queries
  - Unified embedding backend (BGE-M3 preferred, API fallback)
  - Cosine similarity search with pgvector <=> operator
"""

from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.embedding import encode, encode_batch, get_dimension
from src.models.brand_knowledge_orm import BrandKnowledgeEntryORM

DEFAULT_TOP_K = 5
SIMILARITY_THRESHOLD = 0.7


class RAGService:
    """RAG retrieval service — index content and search by semantic similarity."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ─── Index ───

    async def index(
        self,
        entry_id: UUID,
        content: str,
        tenant_id: Optional[str] = None,
    ) -> bool:
        """Generate embedding for content and persist to brand_knowledge_entries.

        Returns True if embedding was generated and saved, False otherwise.
        """
        embedding = await encode(content)
        if embedding is None:
            return False

        stmt = (
            select(BrandKnowledgeEntryORM)
            .where(BrandKnowledgeEntryORM.id == entry_id)
        )
        if tenant_id:
            stmt = stmt.where(BrandKnowledgeEntryORM.tenant_id == tenant_id)

        result = await self.db.execute(stmt)
        entry = result.scalar_one_or_none()
        if entry is None:
            return False

        entry.embedding = embedding
        await self.db.commit()
        return True

    async def index_batch(
        self,
        items: List[Dict],
        tenant_id: Optional[str] = None,
    ) -> Dict[str, bool]:
        """Batch index multiple items.

        items: [{"entry_id": UUID, "content": str}, ...]
        Returns: {str(entry_id): True/False, ...}
        """
        texts = [item["content"] for item in items]
        embeddings = await encode_batch(texts)

        results = {}
        for item, emb in zip(items, embeddings):
            entry_id = item["entry_id"]
            if emb is None:
                results[str(entry_id)] = False
                continue

            stmt = (
                select(BrandKnowledgeEntryORM)
                .where(BrandKnowledgeEntryORM.id == entry_id)
            )
            if tenant_id:
                stmt = stmt.where(BrandKnowledgeEntryORM.tenant_id == tenant_id)

            result = await self.db.execute(stmt)
            entry = result.scalar_one_or_none()
            if entry is None:
                results[str(entry_id)] = False
                continue

            entry.embedding = emb
            results[str(entry_id)] = True

        await self.db.commit()
        return results

    # ─── Search ───

    async def search(
        self,
        query: str,
        top_k: int = DEFAULT_TOP_K,
        tenant_id: Optional[str] = None,
        entry_type: Optional[str] = None,
        threshold: float = SIMILARITY_THRESHOLD,
    ) -> List[Dict]:
        """Semantic search via pgvector cosine similarity.

        Returns list of {entry, similarity_score} ordered by relevance.
        """
        query_embedding = await encode(query)
        if query_embedding is None:
            return []

        # pgvector cosine distance: <=> operator (0 = identical, 2 = opposite)
        # similarity = 1 - distance/2
        dim = get_dimension()
        vector_str = ",".join(str(v) for v in query_embedding)

        # Build raw SQL for pgvector ordering — SQLAlchemy doesn't natively support
        # vector operators, so we use text() fragments
        sql = f"""
            SELECT id, 1 - (embedding <=> '[{vector_str}]'::vector({dim})) AS similarity
            FROM brand_knowledge_entries
            WHERE embedding IS NOT NULL
        """
        params = {}
        if tenant_id:
            sql += " AND tenant_id = :tenant_id"
            params["tenant_id"] = tenant_id
        if entry_type:
            sql += " AND entry_type = :entry_type"
            params["entry_type"] = entry_type

        sql += f"""
            AND 1 - (embedding <=> '[{vector_str}]'::vector({dim})) >= :threshold
            ORDER BY embedding <=> '[{vector_str}]'::vector({dim})
            LIMIT :top_k
        """
        params["threshold"] = threshold
        params["top_k"] = top_k

        result = await self.db.execute(text(sql), params)
        rows = result.fetchall()

        # Fetch full entries
        entry_ids = [row[0] for row in rows]
        if not entry_ids:
            return []

        stmt = select(BrandKnowledgeEntryORM).where(BrandKnowledgeEntryORM.id.in_(entry_ids))
        if tenant_id:
            stmt = stmt.where(BrandKnowledgeEntryORM.tenant_id == tenant_id)

        entries_result = await self.db.execute(stmt)
        entries = {e.id: e for e in entries_result.scalars().all()}

        # Preserve similarity order
        output = []
        for row in rows:
            entry_id, similarity = row
            entry = entries.get(entry_id)
            if entry:
                output.append({
                    "entry": entry,
                    "similarity": float(similarity),
                })

        return output

    async def search_by_entry_id(
        self,
        entry_id: UUID,
        top_k: int = DEFAULT_TOP_K,
        tenant_id: Optional[str] = None,
    ) -> List[Dict]:
        """Find semantically similar entries to a given entry (by its own embedding)."""
        stmt = (
            select(BrandKnowledgeEntryORM)
            .where(BrandKnowledgeEntryORM.id == entry_id)
        )
        if tenant_id:
            stmt = stmt.where(BrandKnowledgeEntryORM.tenant_id == tenant_id)

        result = await self.db.execute(stmt)
        entry = result.scalar_one_or_none()
        if entry is None or entry.embedding is None:
            return []

        dim = get_dimension()
        vector_str = ",".join(str(v) for v in entry.embedding)

        sql = f"""
            SELECT id, 1 - (embedding <=> '[{vector_str}]'::vector({dim})) AS similarity
            FROM brand_knowledge_entries
            WHERE embedding IS NOT NULL
              AND id != :entry_id
        """
        params = {"entry_id": str(entry_id)}
        if tenant_id:
            sql += " AND tenant_id = :tenant_id"
            params["tenant_id"] = tenant_id

        sql += f"""
            ORDER BY embedding <=> '[{vector_str}]'::vector({dim})
            LIMIT :top_k
        """
        params["top_k"] = top_k

        result = await self.db.execute(text(sql), params)
        rows = result.fetchall()

        similar_ids = [row[0] for row in rows]
        if not similar_ids:
            return []

        stmt = select(BrandKnowledgeEntryORM).where(BrandKnowledgeEntryORM.id.in_(similar_ids))
        if tenant_id:
            stmt = stmt.where(BrandKnowledgeEntryORM.tenant_id == tenant_id)

        entries_result = await self.db.execute(stmt)
        entries = {e.id: e for e in entries_result.scalars().all()}

        output = []
        for row in rows:
            rid, similarity = row
            e = entries.get(rid)
            if e:
                output.append({"entry": e, "similarity": float(similarity)})

        return output
