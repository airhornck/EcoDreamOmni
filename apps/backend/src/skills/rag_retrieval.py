"""RAG Retrieval Skill — v4.0 Phase 8 P8-2.

基于语义查询检索 BrandKnowledge。
MVP: 基于关键词匹配的简化检索，不调用真实 embedding（预留 RAGService 接口）。

架构红线:
- §2.1 Agent 禁 DB: 知识库数据通过 context 注入或由 Function API 提供
- §2.5 LLMHub 路由: requires_llm=False
"""

from typing import Any, Dict

SKILL_ID = "rag_retrieval"
VERSION = "1.0.0"
MODALITY_SUPPORT = {"embedding": True}
REQUIRES_LLM = False
LLM_MODEL_PREFERENCE = ""

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "query": {"type": "string", "description": "检索查询"},
        "top_k": {"type": "integer", "description": "返回结果数量", "default": 5},
        "category": {"type": "string", "description": "知识类别过滤: brand_info/product_sku/faq/prohibited_claim/category_knowledge", "default": ""},
        "brand_name": {"type": "string", "description": "品牌名过滤"},
        "knowledge_entries": {"type": "array", "items": {"type": "object"}, "description": "知识库条目列表（由 Function API 提供）"},
    },
    "required": ["query"],
}

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "results": {"type": "array", "items": {"type": "object"}},
        "total_found": {"type": "integer"},
        "query_time_ms": {"type": "integer"},
        "query": {"type": "string"},
        "method": {"type": "string"},
    },
}


def _keyword_score(query: str, entry: Dict[str, Any]) -> float:
    """Simple keyword matching score for MVP."""
    query_words = set(query.lower().split())
    content = f"{entry.get('name', '')} {entry.get('content', '')} {entry.get('entry_type', '')}"
    content_lower = content.lower()

    if not query_words:
        return 0.0

    matches = sum(1 for qw in query_words if qw in content_lower)
    return matches / len(query_words)


def _category_filter(entry: Dict[str, Any], category: str) -> bool:
    if not category:
        return True
    entry_type = entry.get("entry_type", "")
    return category.lower() in entry_type.lower() or entry_type.lower() in category.lower()


def _brand_filter(entry: Dict[str, Any], brand_name: str) -> bool:
    if not brand_name:
        return True
    entry_brand = entry.get("brand_name", "")
    return brand_name.lower() in entry_brand.lower() or entry_brand.lower() in brand_name.lower()


def execute(context: Dict[str, Any]) -> Dict[str, Any]:
    import time

    start_time = time.time()

    query = context.get("query", "")
    top_k = context.get("top_k", 5)
    category = context.get("category", "")
    brand_name = context.get("brand_name", "")
    knowledge_entries = context.get("knowledge_entries", [])

    if not knowledge_entries:
        # MVP fallback: return empty results with guidance
        return {
            "results": [],
            "total_found": 0,
            "query_time_ms": 0,
            "query": query,
            "method": "keyword_mvp_no_data",
            "note": "未提供知识库数据，请通过 Function API 注入 brand_knowledge_entries",
            "skill_id": SKILL_ID,
            "version": VERSION,
        }

    # Score and filter entries
    scored_entries = []
    for entry in knowledge_entries:
        if not _category_filter(entry, category):
            continue
        if not _brand_filter(entry, brand_name):
            continue
        score = _keyword_score(query, entry)
        if score > 0:
            scored_entries.append({"entry": entry, "score": score})

    # Sort by score descending
    scored_entries.sort(key=lambda x: x["score"], reverse=True)

    # Take top_k
    top_results = scored_entries[:top_k]

    # Format results
    results = []
    for item in top_results:
        entry = item["entry"]
        results.append({
            "id": entry.get("id", ""),
            "name": entry.get("name", ""),
            "entry_type": entry.get("entry_type", ""),
            "brand_name": entry.get("brand_name", ""),
            "content_preview": entry.get("content", "")[:200],
            "score": round(item["score"], 4),
            "relevance": "high" if item["score"] > 0.5 else "medium" if item["score"] > 0.2 else "low",
        })

    query_time_ms = int((time.time() - start_time) * 1000)

    return {
        "results": results,
        "total_found": len(scored_entries),
        "query_time_ms": query_time_ms,
        "query": query,
        "method": "keyword_mvp",
        "skill_id": SKILL_ID,
        "version": VERSION,
    }
