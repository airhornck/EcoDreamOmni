"""Tests for src.core.errors — P0-3 v4.0 alignment.

Validates ErrorCode enum, HTTP status mapping, APIException, convenience helpers.
"""

import pytest
from fastapi import HTTPException

from src.core.errors import (
    ErrorCode,
    get_http_status,
    APIException,
    raise_validation_error,
    raise_not_found,
)


class TestErrorCode:
    def test_all_codes_are_strings(self):
        for code in ErrorCode:
            assert isinstance(code.value, str)
            assert len(code.value) > 0

    def test_success_codes(self):
        assert ErrorCode.OK == "OK"
        assert ErrorCode.CREATED == "CREATED"
        assert ErrorCode.ACCEPTED == "ACCEPTED"

    def test_client_error_codes(self):
        assert ErrorCode.VALIDATION_ERROR == "VALIDATION_ERROR"
        assert ErrorCode.NOT_FOUND == "NOT_FOUND"
        assert ErrorCode.RATE_LIMITED == "RATE_LIMITED"

    def test_agent_error_codes(self):
        assert ErrorCode.AGENT_DEGRADED == "AGENT_DEGRADED"
        assert ErrorCode.SKILL_NOT_FOUND == "SKILL_NOT_FOUND"

    def test_llm_error_codes(self):
        assert ErrorCode.LLM_MODEL_UNAVAILABLE == "LLM_MODEL_UNAVAILABLE"
        assert ErrorCode.LLM_RATE_LIMITED == "LLM_RATE_LIMITED"

    def test_workflow_error_codes(self):
        assert ErrorCode.WORKFLOW_NODE_FAILED == "WORKFLOW_NODE_FAILED"
        assert ErrorCode.CHECKPOINT_CORRUPTED == "CHECKPOINT_CORRUPTED"


class TestHttpStatusMapping:
    @pytest.mark.parametrize(
        "code,expected_status",
        [
            (ErrorCode.OK, 200),
            (ErrorCode.CREATED, 201),
            (ErrorCode.ACCEPTED, 202),
            (ErrorCode.VALIDATION_ERROR, 400),
            (ErrorCode.UNAUTHORIZED, 401),
            (ErrorCode.FORBIDDEN, 403),
            (ErrorCode.NOT_FOUND, 404),
            (ErrorCode.CONFLICT, 409),
            (ErrorCode.RATE_LIMITED, 429),
            (ErrorCode.AGENT_DEGRADED, 503),
            (ErrorCode.LLM_MODEL_UNAVAILABLE, 503),
            (ErrorCode.INTERNAL_ERROR, 500),
        ],
    )
    def test_status_mapping(self, code, expected_status):
        assert get_http_status(code) == expected_status

    def test_unknown_code_defaults_to_500(self):
        # Simulate a code not in the mapping
        class FakeCode:
            pass
        assert get_http_status(FakeCode()) == 500  # type: ignore


class TestAPIException:
    def test_basic_exception(self):
        exc = APIException(
            code=ErrorCode.NOT_FOUND,
            message="资源不存在",
            trace_id="req_123",
        )
        assert exc.status_code == 404
        assert exc.business_code == ErrorCode.NOT_FOUND
        assert exc.business_message == "资源不存在"
        assert exc.detail["code"] == "NOT_FOUND"

    def test_exception_with_field_errors(self):
        exc = APIException(
            code=ErrorCode.VALIDATION_ERROR,
            message="参数校验失败",
            field_errors=[{"field": "title", "message": "不能为空"}],
        )
        assert exc.status_code == 400
        assert exc.field_errors == [{"field": "title", "message": "不能为空"}]

    def test_exception_is_http_exception(self):
        exc = APIException(code=ErrorCode.OK, message="成功")
        assert isinstance(exc, HTTPException)


class TestConvenienceHelpers:
    def test_raise_validation_error(self):
        with pytest.raises(APIException) as exc_info:
            raise_validation_error(
                message="标题不能为空",
                field_errors=[{"field": "title", "message": "不能为空"}],
            )
        assert exc_info.value.business_code == ErrorCode.VALIDATION_ERROR
        assert exc_info.value.status_code == 400

    def test_raise_not_found_without_id(self):
        with pytest.raises(APIException) as exc_info:
            raise_not_found("用户")
        assert exc_info.value.business_code == ErrorCode.NOT_FOUND
        assert "用户 不存在" in exc_info.value.business_message

    def test_raise_not_found_with_id(self):
        with pytest.raises(APIException) as exc_info:
            raise_not_found("用户", resource_id="user_123")
        assert "用户 user_123 不存在" in exc_info.value.business_message
