from __future__ import annotations

from typing import Any

from app.shared.exceptions.base import AppException, NotFoundError, ServiceUnavailableError


class ChatSessionNotFoundError(NotFoundError):
    error_code: str = "CHAT_SESSION_NOT_FOUND"

    def __init__(
        self,
        message: str = "Phiên chat không tồn tại",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, details=details)


class ChatMessageLimitError(AppException):
    status_code: int = 429
    error_code: str = "CHAT_MESSAGE_LIMIT_REACHED"

    def __init__(
        self,
        message: str = "Đã đạt giới hạn tin nhắn cho phiên chat này",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, details=details)


class ChatAnalysisNotFoundError(NotFoundError):
    error_code: str = "CHAT_ANALYSIS_NOT_FOUND"

    def __init__(
        self,
        message: str = "Kết quả phân tích không tồn tại hoặc chưa hoàn thành",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, details=details)


class ChatLLMError(ServiceUnavailableError):
    error_code: str = "CHAT_LLM_ERROR"

    def __init__(
        self,
        message: str = "Không thể tạo phản hồi từ AI",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, details=details)
