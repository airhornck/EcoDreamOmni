"""Tests for src.core.schemas.base — P0-3 v4.0 alignment.

Validates BaseResponse, PaginatedResponse, ErrorResponse structure.
"""

import pytest
from pydantic import ValidationError

from src.core.schemas.base import BaseResponse, PaginatedResponse, PaginationMeta, ErrorDetail


class TestBaseResponse:
    def test_valid_response(self):
        resp = BaseResponse(
            code="OK",
            message="操作成功",
            data={"id": "abc"},
            trace_id="req_123",
            timestamp="2026-06-02T10:30:00Z",
        )
        assert resp.code == "OK"
        assert resp.message == "操作成功"
        assert resp.data == {"id": "abc"}

    def test_data_can_be_none(self):
        resp = BaseResponse(
            code="OK",
            message="操作成功",
            data=None,
            trace_id="req_123",
            timestamp="2026-06-02T10:30:00Z",
        )
        assert resp.data is None

    def test_missing_required_field_raises(self):
        with pytest.raises(ValidationError):
            BaseResponse(
                code="OK",
                message="操作成功",
                # missing trace_id and timestamp
            )


class TestPaginatedResponse:
    def test_valid_paginated(self):
        resp = PaginatedResponse(
            code="OK",
            message="查询成功",
            data=[{"id": 1}, {"id": 2}],
            pagination=PaginationMeta(
                page=1,
                page_size=20,
                total=156,
                total_pages=8,
            ),
            trace_id="req_123",
            timestamp="2026-06-02T10:30:00Z",
        )
        assert len(resp.data) == 2
        assert resp.pagination.total == 156
        assert resp.pagination.total_pages == 8

    def test_pagination_defaults(self):
        meta = PaginationMeta(page=1, page_size=10, total=0, total_pages=0)
        assert meta.page == 1

    def test_page_must_be_positive(self):
        with pytest.raises(ValidationError):
            PaginationMeta(page=0, page_size=10, total=0, total_pages=0)


class TestErrorDetail:
    def test_with_field(self):
        detail = ErrorDetail(field="title", message="标题不能为空")
        assert detail.field == "title"
        assert detail.message == "标题不能为空"

    def test_without_field(self):
        detail = ErrorDetail(message="系统错误")
        assert detail.field is None
