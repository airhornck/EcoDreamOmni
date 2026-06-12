"""Core Pydantic schemas — v4.0 unified API contract layer.

All API responses must use BaseResponse or its subclasses.
All error handling must use ErrorCode from src.core.errors.

P0-3 v4.0 alignment:统一响应格式、分页结构、错误响应规范。
"""

from src.core.schemas.base import BaseResponse, PaginatedResponse, PaginationMeta, ErrorDetail

__all__ = [
    "BaseResponse",
    "PaginatedResponse",
    "PaginationMeta",
    "ErrorDetail",
]
