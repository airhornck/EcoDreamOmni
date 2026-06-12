"""Tests for rag_retrieval Skill — Phase 8 P8-2."""

import pytest

from src.skills.rag_retrieval import execute, SKILL_ID, VERSION


class TestRAGRetrievalSkill:
    def test_skill_metadata(self):
        assert SKILL_ID == "rag_retrieval"
        assert VERSION == "1.0.0"

    def test_no_data_fallback(self):
        result = execute({"query": "cat food"})
        assert result["results"] == []
        assert result["total_found"] == 0
        assert result["method"] == "keyword_mvp_no_data"

    def test_basic_keyword_match(self):
        entries = [
            {"id": "1", "name": "Royal Canin", "content": "Good for kittens", "entry_type": "product_sku", "brand_name": "Royal"},
            {"id": "2", "name": "Orijen", "content": "High protein", "entry_type": "product_sku", "brand_name": "Orijen"},
            {"id": "3", "name": "FAQ1", "content": "New cat tips", "entry_type": "faq", "brand_name": ""},
        ]
        result = execute({"query": "cat food", "knowledge_entries": entries, "top_k": 2})
        assert len(result["results"]) > 0
        assert result["total_found"] > 0
        assert result["method"] == "keyword_mvp"

    def test_category_filter(self):
        entries = [
            {"id": "1", "name": "ProductA", "content": "ContentA", "entry_type": "product_sku"},
            {"id": "2", "name": "FAQ1", "content": "ContentB", "entry_type": "faq"},
        ]
        result = execute({"query": "content", "knowledge_entries": entries, "category": "faq"})
        assert len(result["results"]) == 1
        assert result["results"][0]["entry_type"] == "faq"

    def test_brand_filter(self):
        entries = [
            {"id": "1", "name": "Royal Kitten", "content": "Royal content", "entry_type": "product_sku", "brand_name": "Royal"},
            {"id": "2", "name": "Orijen Adult", "content": "Orijen content", "entry_type": "product_sku", "brand_name": "Orijen"},
        ]
        result = execute({"query": "royal", "knowledge_entries": entries, "brand_name": "Royal"})
        assert len(result["results"]) == 1
        assert result["results"][0]["brand_name"] == "Royal"

    def test_top_k_limit(self):
        entries = [
            {"id": str(i), "name": f"Entry{i}", "content": f"Content{i}", "entry_type": "product_sku"}
            for i in range(10)
        ]
        result = execute({"query": "content", "knowledge_entries": entries, "top_k": 3})
        assert len(result["results"]) <= 3

    def test_relevance_scoring(self):
        entries = [
            {"id": "1", "name": "Exact match", "content": "test query", "entry_type": "faq"},
            {"id": "2", "name": "Partial match", "content": "other content", "entry_type": "faq"},
        ]
        result = execute({"query": "test query", "knowledge_entries": entries})
        if len(result["results"]) >= 2:
            assert result["results"][0]["score"] >= result["results"][1]["score"]

    def test_result_preview_truncation(self):
        entries = [
            {"id": "1", "name": "Long content", "content": "a" * 500, "entry_type": "faq"},
        ]
        result = execute({"query": "long content", "knowledge_entries": entries})
        preview = result["results"][0]["content_preview"]
        assert len(preview) <= 200

    def test_output_schema(self):
        result = execute({
            "query": "test",
            "knowledge_entries": [{"id": "1", "name": "Test", "content": "Test content", "entry_type": "faq"}],
        })
        assert "results" in result
        assert "total_found" in result
        assert "query_time_ms" in result
        assert "query" in result
        assert "method" in result
        assert "skill_id" in result
