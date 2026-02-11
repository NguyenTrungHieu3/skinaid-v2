"""
Auth Exceptions — Exception chuyên biệt cho auth module.

Kế thừa từ shared/exceptions/base.py AppException hierarchy.
Mỗi exception tự chứa status_code + error_code → không cần ErrorCode constants.
"""

from app.shared.exceptions.base import (
    BadRequestError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
)


# ── User ──────────────────────────────────────────────────


class UserNotFoundError(NotFoundError):
    """Không tìm thấy user."""

    error_code = "AUTH_USER_NOT_FOUND"

    def __init__(self, identifier: str = "") -> None:
        detail = f" ({identifier})" if identifier else ""
        super().__init__(
            resource="User",
            resource_id=identifier,
            message=f"Không tìm thấy người dùng{detail}",
        )


class EmailExistsError(ConflictError):
    """Email đã được sử dụng."""

    error_code = "AUTH_EMAIL_EXISTS"

    def __init__(self, email: str = "") -> None:
        super().__init__(
            message="Email đã được sử dụng",
            details={"email": email} if email else None,
        )


class UsernameExistsError(ConflictError):
    """Username đã tồn tại."""

    error_code = "AUTH_USERNAME_EXISTS"

    def __init__(self, user_name: str = "") -> None:
        super().__init__(
            message="Tên người dùng đã tồn tại",
            details={"user_name": user_name} if user_name else None,
        )


# ── Authentication ────────────────────────────────────────


class InvalidCredentialsError(UnauthorizedError):
    """Thông tin đăng nhập không hợp lệ."""

    error_code = "AUTH_INVALID_CREDENTIALS"

    def __init__(self) -> None:
        super().__init__(
            message="Tên người dùng hoặc mật khẩu không hợp lệ",
        )


class AccountInactiveError(ForbiddenError):
    """Tài khoản đã bị vô hiệu hóa."""

    error_code = "AUTH_ACCOUNT_INACTIVE"

    def __init__(self) -> None:
        super().__init__(message="Tài khoản đã bị vô hiệu hóa")


class AccountUnverifiedError(ForbiddenError):
    """Tài khoản chưa xác minh."""

    error_code = "AUTH_ACCOUNT_UNVERIFIED"

    def __init__(self) -> None:
        super().__init__(message="Yêu cầu xác minh tài khoản")


# ── Token ─────────────────────────────────────────────────


class InvalidTokenError(UnauthorizedError):
    """Token không hợp lệ."""

    error_code = "AUTH_INVALID_TOKEN"

    def __init__(self, message: str = "Token không hợp lệ") -> None:
        super().__init__(message=message)


class TokenRevokedError(UnauthorizedError):
    """Token đã bị thu hồi."""

    error_code = "AUTH_TOKEN_REVOKED"

    def __init__(self) -> None:
        super().__init__(message="Token đã bị thu hồi")


class TokenReuseError(UnauthorizedError):
    """Phát hiện tái sử dụng token (security threat)."""

    error_code = "AUTH_TOKEN_REUSE"

    def __init__(self) -> None:
        super().__init__(
            message="Phát hiện tái sử dụng token. "
            "Tất cả phiên đã bị vô hiệu hóa vì lý do bảo mật.",
        )


# ── Password ──────────────────────────────────────────────


class WeakPasswordError(BadRequestError):
    """Mật khẩu không đạt yêu cầu bảo mật."""

    error_code = "AUTH_WEAK_PASSWORD"

    def __init__(self, reason: str = "") -> None:
        message = "Mật khẩu không đạt yêu cầu bảo mật"
        if reason:
            message = reason
        super().__init__(message=message)


class InvalidCurrentPasswordError(BadRequestError):
    """Mật khẩu hiện tại không đúng."""

    error_code = "AUTH_INVALID_CURRENT_PASSWORD"

    def __init__(self) -> None:
        super().__init__(message="Mật khẩu hiện tại không đúng")


class InvalidResetTokenError(BadRequestError):
    """Token đặt lại mật khẩu không hợp lệ hoặc đã hết hạn."""

    error_code = "AUTH_INVALID_RESET_TOKEN"

    def __init__(self) -> None:
        super().__init__(
            message="Token đặt lại mật khẩu không hợp lệ hoặc đã hết hạn",
        )
