from __future__ import annotations

from typing import Any

from app.shared.exceptions.base import AppException, InternalError


class LLMException(AppException):
    """Base exception cho toàn bộ module LLM."""

    status_code: int = 500
    error_code: str = "LLM_ERROR"

    def __init__(
        self,
        message: str = "Đã xảy ra lỗi LLM",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, details=details)


class LLMServiceUnavailableError(LLMException):
    """OpenAI API không khả dụng — timeout hoặc service down (HTTP 503)."""

    status_code: int = 503
    error_code: str = "LLM_UNAVAILABLE"

    def __init__(
        self,
        message: str = "Dịch vụ LLM tạm thời không khả dụng, vui lòng thử lại sau",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, details=details)


class LLMRateLimitError(LLMException):
    """OpenAI rate limit bị chạm — đã retry nhưng vẫn fail (HTTP 429)."""

    status_code: int = 429
    error_code: str = "LLM_RATE_LIMIT"

    def __init__(
        self,
        message: str = "Đã vượt quá giới hạn yêu cầu LLM, vui lòng thử lại sau ít phút",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, details=details)


class LLMInvalidResponseError(InternalError):
    """LLM trả về response không hợp lệ hoặc rỗng (HTTP 500)."""

    error_code: str = "LLM_INVALID_RESPONSE"

    def __init__(
        self,
        message: str = "LLM trả về kết quả không hợp lệ",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, details=details)


class LLMContextBuildError(InternalError):
    """Lỗi khi build prompt context từ DB guide hoặc RAG chunks (HTTP 500)."""

    error_code: str = "LLM_CONTEXT_ERROR"

    def __init__(
        self,
        message: str = "Không thể xây dựng context cho LLM synthesis",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, details=details)
