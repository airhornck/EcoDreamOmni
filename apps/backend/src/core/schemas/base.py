"""Base Pydantic schemas for unified API responses.

Aligned with docs/契约与数据/01-API接口契约.md §一 (通用响应格式).
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class PaginationMeta(BaseModel):
    """Pagination metadata."""

    page: int = Field(..., ge=1, description="当前页码")
    page_size: int = Field(..., ge=1, description="每页数量")
    total: int = Field(..., ge=0, description="总记录数")
    total_pages: int = Field(..., ge=0, description="总页数")


class ErrorDetail(BaseModel):
    """Field-level error detail."""

    field: Optional[str] = Field(None, description="错误字段名")
    message: str = Field(..., description="错误描述")


class BaseResponse(BaseModel):
    """Unified API response wrapper.

    All API endpoints (except SSE/WebSocket) must return this structure.
    """

    code: str = Field(..., description="业务错误码，如 OK / VALIDATION_ERROR")
    message: str = Field(..., description="用户可读消息（中文）")
    data: Optional[Any] = Field(None, description="业务数据，失败时可为 null")
    trace_id: str = Field(..., description="链路追踪 ID（UUID v4）")
    timestamp: str = Field(..., description="ISO 8601 格式时间戳")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "code": "OK",
                "message": "操作成功",
                "data": {"id": "abc123"},
                "trace_id": "req_abc123def456",
                "timestamp": "2026-06-02T10:30:00Z",
            }
        }
    )


class PaginatedResponse(BaseResponse):
    """Paginated response wrapper.

    Overrides `data` to be a list and adds pagination metadata.
    """

    data: List[Any] = Field(default_factory=list, description="数据列表")
    pagination: PaginationMeta = Field(..., description="分页元数据")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "code": "OK",
                "message": "查询成功",
                "data": [],
                "pagination": {
                    "page": 1,
                    "page_size": 20,
                    "total": 156,
                    "total_pages": 8,
                },
                "trace_id": "req_abc123def456",
                "timestamp": "2026-06-02T10:30:00Z",
            }
        }
    )


class ErrorResponse(BaseResponse):
    """Error response with optional field-level details.

    HTTP status code is conveyed via the actual HTTP response status,
    while `code` provides the business-level error classification.
    """

    data: Optional[Dict[str, Any]] = Field(None, description="附加错误数据")
    field_errors: Optional[List[ErrorDetail]] = Field(None, description="字段级校验错误")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "code": "VALIDATION_ERROR",
                "message": "标题不能为空，且长度不超过20字",
                "data": None,
                "field_errors": [
                    {"field": "title", "message": "标题不能为空"},
                ],
                "trace_id": "req_abc123def456",
                "timestamp": "2026-06-02T10:30:00Z",
            }
        }
    )
