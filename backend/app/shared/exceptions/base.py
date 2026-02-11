"""
Base exception hierarchy cho toàn bộ SkinAid application.

Tất cả module-specific exceptions kế thừa từ các lớp base này.
Tuân theo /exception-guidelines workflow.
"""

from typing import Any


class AppException(Exception):
    """Exception gốc cho toàn bộ ứng dụng SkinAid."""

    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"

    def __init__(
        self,
        message: str = "Đã xảy ra lỗi nội bộ",
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(AppException):
    """Tài nguyên không tồn tại — 404."""

    status_code: int = 404
    error_code: str = "NOT_FOUND"

    def __init__(
        self,
        message: str = "Tài nguyên không tồn tại",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, details=details)


class BadRequestError(AppException):
    """Dữ liệu đầu vào không hợp lệ — 400."""

    status_code: int = 400
    error_code: str = "BAD_REQUEST"

    def __init__(
        self,
        message: str = "Yêu cầu không hợp lệ",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, details=details)


class ValidationError(AppException):
    """Dữ liệu không vượt qua validation — 422."""

    status_code: int = 422
    error_code: str = "VALIDATION_ERROR"

    def __init__(
        self,
        message: str = "Dữ liệu không hợp lệ",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, details=details)


class ConflictError(AppException):
    """Tài nguyên đã tồn tại hoặc xung đột — 409."""

    status_code: int = 409
    error_code: str = "CONFLICT"

    def __init__(
        self,
        message: str = "Tài nguyên đã tồn tại",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, details=details)


class UnauthorizedError(AppException):
    """Xác thực thất bại — 401."""

    status_code: int = 401
    error_code: str = "UNAUTHORIZED"

    def __init__(
        self,
        message: str = "Xác thực thất bại",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, details=details)


class ForbiddenError(AppException):
    """Không có quyền truy cập — 403."""

    status_code: int = 403
    error_code: str = "FORBIDDEN"

    def __init__(
        self,
        message: str = "Không có quyền truy cập",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, details=details)


class InternalError(AppException):
    """Lỗi nội bộ hệ thống — 500."""

    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"

    def __init__(
        self,
        message: str = "Đã xảy ra lỗi nội bộ",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, details=details)


class ServiceUnavailableError(AppException):
    """Dịch vụ bên ngoài không khả dụng — 503."""

    status_code: int = 503
    error_code: str = "SERVICE_UNAVAILABLE"

    def __init__(
        self,
        message: str = "Dịch vụ tạm thời không khả dụng",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, details=details)
