from __future__ import annotations

from typing import Any

from app.shared.exceptions.base import AppException, NotFoundError, ServiceUnavailableError


class ChatbotException(AppException):
    """Base cho tất cả lỗi chatbot."""

    status_code: int = 500
    error_code: str = "CHATBOT_ERROR"

    def __init__(
        self,
        message: str = "Lỗi chatbot",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, details=details)


class ChatSessionNotFoundError(NotFoundError):
    """Session không tồn tại hoặc không thuộc user."""

    error_code: str = "CHAT_SESSION_NOT_FOUND"

    def __init__(
        self,
        message: str = "Phiên chat không tồn tại",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, details=details)


class ChatMessageLimitError(AppException):
    """Đã đạt giới hạn messages trong session."""

    status_code: int = 429
    error_code: str = "CHAT_MESSAGE_LIMIT_REACHED"

    def __init__(
        self,
        message: str = "Đã đạt giới hạn tin nhắn cho phiên chat này",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, details=details)


class ChatSessionExpiredError(AppException):
    """Redis session đã hết hạn."""

    status_code: int = 410
    error_code: str = "CHAT_SESSION_EXPIRED"

    def __init__(
        self,
        message: str = "Phiên chat đã hết hạn",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, details=details)


class ChatAnalysisNotFoundError(NotFoundError):
    """analysis_id không tồn tại hoặc chưa completed."""

    error_code: str = "CHAT_ANALYSIS_NOT_FOUND"

    def __init__(
        self,
        message: str = "Kết quả phân tích không tồn tại hoặc chưa hoàn thành",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, details=details)


class ChatLLMError(ServiceUnavailableError):
    """LLM service gặp lỗi khi generate reply."""

    error_code: str = "CHAT_LLM_ERROR"

    def __init__(
        self,
        message: str = "Không thể tạo phản hồi từ AI",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, details=details)
