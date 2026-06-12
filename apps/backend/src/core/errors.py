"""Unified error codes — v4.0 API contract.

Aligned with docs/契约与数据/01-API接口契约.md §二 (全局错误码字典).

Usage:
    from src.core.errors import ErrorCode, raise_validation_error

    raise_validation_error(
        code=ErrorCode.VALIDATION_ERROR,
        message="标题不能为空",
        field_errors=[{"field": "title", "message": "标题不能为空"}],
    )
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import HTTPException


class ErrorCode(str, Enum):
    """Business error codes aligned with API contract v4.0."""

    # ─── 2xx Success ───
    OK = "OK"
    CREATED = "CREATED"
    ACCEPTED = "ACCEPTED"

    # ─── 4xx Client Errors ───
    VALIDATION_ERROR = "VALIDATION_ERROR"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    RATE_LIMITED = "RATE_LIMITED"
    PAYLOAD_TOO_LARGE = "PAYLOAD_TOO_LARGE"

    # ─── 5xx Agent/Skill Errors ───
    AGENT_NOT_FOUND = "AGENT_NOT_FOUND"
    AGENT_DEGRADED = "AGENT_DEGRADED"
    AGENT_TIMEOUT = "AGENT_TIMEOUT"
    SKILL_NOT_FOUND = "SKILL_NOT_FOUND"
    SKILL_EXECUTION_ERROR = "SKILL_EXECUTION_ERROR"
    SKILL_NOT_BOUND = "SKILL_NOT_BOUND"

    # ─── 6xx Function Errors ───
    FUNCTION_NOT_FOUND = "FUNCTION_NOT_FOUND"
    FUNCTION_UNAVAILABLE = "FUNCTION_UNAVAILABLE"
    DATA_INTEGRITY_ERROR = "DATA_INTEGRITY_ERROR"

    # ─── 7xx LLM Errors ───
    LLM_MODEL_UNAVAILABLE = "LLM_MODEL_UNAVAILABLE"
    LLM_RATE_LIMITED = "LLM_RATE_LIMITED"
    LLM_CONTENT_FILTERED = "LLM_CONTENT_FILTERED"
    LLM_CONTEXT_OVERFLOW = "LLM_CONTEXT_OVERFLOW"
    LLM_COST_EXCEEDED = "LLM_COST_EXCEEDED"

    # ─── 8xx Workflow/Pipeline Errors ───
    WORKFLOW_NOT_FOUND = "WORKFLOW_NOT_FOUND"
    WORKFLOW_INVALID_STATE = "WORKFLOW_INVALID_STATE"
    WORKFLOW_NODE_FAILED = "WORKFLOW_NODE_FAILED"
    WORKFLOW_NODE_TIMEOUT = "WORKFLOW_NODE_TIMEOUT"
    HUMAN_APPROVAL_TIMEOUT = "HUMAN_APPROVAL_TIMEOUT"
    CHECKPOINT_CORRUPTED = "CHECKPOINT_CORRUPTED"

    # ─── 9xx System Errors ───
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    TIMEOUT = "TIMEOUT"


# ─── HTTP status mapping ───

_ERROR_HTTP_STATUS: Dict[ErrorCode, int] = {
    ErrorCode.OK: 200,
    ErrorCode.CREATED: 201,
    ErrorCode.ACCEPTED: 202,
    ErrorCode.VALIDATION_ERROR: 400,
    ErrorCode.UNAUTHORIZED: 401,
    ErrorCode.FORBIDDEN: 403,
    ErrorCode.NOT_FOUND: 404,
    ErrorCode.CONFLICT: 409,
    ErrorCode.RATE_LIMITED: 429,
    ErrorCode.PAYLOAD_TOO_LARGE: 413,
    ErrorCode.AGENT_NOT_FOUND: 500,
    ErrorCode.AGENT_DEGRADED: 503,
    ErrorCode.AGENT_TIMEOUT: 504,
    ErrorCode.SKILL_NOT_FOUND: 500,
    ErrorCode.SKILL_EXECUTION_ERROR: 500,
    ErrorCode.SKILL_NOT_BOUND: 403,
    ErrorCode.FUNCTION_NOT_FOUND: 500,
    ErrorCode.FUNCTION_UNAVAILABLE: 503,
    ErrorCode.DATA_INTEGRITY_ERROR: 500,
    ErrorCode.LLM_MODEL_UNAVAILABLE: 503,
    ErrorCode.LLM_RATE_LIMITED: 429,
    ErrorCode.LLM_CONTENT_FILTERED: 400,
    ErrorCode.LLM_CONTEXT_OVERFLOW: 400,
    ErrorCode.LLM_COST_EXCEEDED: 429,
    ErrorCode.WORKFLOW_NOT_FOUND: 404,
    ErrorCode.WORKFLOW_INVALID_STATE: 400,
    ErrorCode.WORKFLOW_NODE_FAILED: 500,
    ErrorCode.WORKFLOW_NODE_TIMEOUT: 504,
    ErrorCode.HUMAN_APPROVAL_TIMEOUT: 408,
    ErrorCode.CHECKPOINT_CORRUPTED: 500,
    ErrorCode.INTERNAL_ERROR: 500,
    ErrorCode.SERVICE_UNAVAILABLE: 503,
    ErrorCode.TIMEOUT: 504,
}


def get_http_status(code: ErrorCode) -> int:
    """Get HTTP status code for a business error code."""
    return _ERROR_HTTP_STATUS.get(code, 500)


# ─── Exception helpers ───

class APIException(HTTPException):
    """Structured API exception with business error code."""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        field_errors: Optional[List[Dict[str, str]]] = None,
        trace_id: Optional[str] = None,
    ):
        self.business_code = code
        self.business_message = message
        self.business_data = data
        self.field_errors = field_errors or []
        self.trace_id = trace_id
        super().__init__(
            status_code=get_http_status(code),
            detail={
                "code": code.value,
                "message": message,
                "data": data,
                "field_errors": field_errors,
                "trace_id": trace_id,
            },
        )


def raise_validation_error(
    message: str,
    field_errors: Optional[List[Dict[str, str]]] = None,
    trace_id: Optional[str] = None,
) -> None:
    """Convenience helper for validation errors."""
    raise APIException(
        code=ErrorCode.VALIDATION_ERROR,
        message=message,
        field_errors=field_errors,
        trace_id=trace_id,
    )


def raise_not_found(
    resource: str,
    resource_id: Optional[str] = None,
    trace_id: Optional[str] = None,
) -> None:
    """Convenience helper for not-found errors."""
    msg = f"{resource} 不存在"
    if resource_id:
        msg = f"{resource} {resource_id} 不存在"
    raise APIException(
        code=ErrorCode.NOT_FOUND,
        message=msg,
        trace_id=trace_id,
    )
