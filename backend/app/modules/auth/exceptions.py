from app.shared.exceptions.base import (
    BadRequestError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
)


class UserNotFoundError(NotFoundError):

    error_code = "AUTH_USER_NOT_FOUND"

    def __init__(self, identifier: str = "") -> None:
        detail = f" ({identifier})" if identifier else ""
        super().__init__(
            message=f"User not found{detail}",
            details={"user_id": identifier} if identifier else None,
        )


class EmailExistsError(ConflictError):

    error_code = "AUTH_EMAIL_EXISTS"

    def __init__(self, email: str = "") -> None:
        super().__init__(
            message="Email already registered",
            details={"email": email} if email else None,
        )


class UsernameExistsError(ConflictError):

    error_code = "AUTH_USERNAME_EXISTS"

    def __init__(self, user_name: str = "") -> None:
        super().__init__(
            message="Username already taken",
            details={"user_name": user_name} if user_name else None,
        )


class InvalidCredentialsError(UnauthorizedError):

    error_code = "AUTH_INVALID_CREDENTIALS"

    def __init__(self) -> None:
        super().__init__(
            message="Invalid username or password",
        )


class AccountInactiveError(ForbiddenError):

    error_code = "AUTH_ACCOUNT_INACTIVE"

    def __init__(self) -> None:
        super().__init__(message="Account has been deactivated")


class AccountUnverifiedError(ForbiddenError):

    error_code = "AUTH_ACCOUNT_UNVERIFIED"

    def __init__(self) -> None:
        super().__init__(message="Account verification required")


class InvalidTokenError(UnauthorizedError):

    error_code = "AUTH_INVALID_TOKEN"

    def __init__(self, message: str = "Invalid token") -> None:
        super().__init__(message=message)


class TokenRevokedError(UnauthorizedError):

    error_code = "AUTH_TOKEN_REVOKED"

    def __init__(self) -> None:
        super().__init__(message="Token has been revoked")


class TokenReuseError(UnauthorizedError):

    error_code = "AUTH_TOKEN_REUSE"

    def __init__(self) -> None:
        super().__init__(
            message="Token reuse detected. All sessions have been revoked for security.",
        )


class WeakPasswordError(BadRequestError):

    error_code = "AUTH_WEAK_PASSWORD"

    def __init__(self, reason: str = "") -> None:
        message = "Password does not meet security requirements"
        if reason:
            message = reason
        super().__init__(message=message)


class InvalidCurrentPasswordError(BadRequestError):

    error_code = "AUTH_INVALID_CURRENT_PASSWORD"

    def __init__(self) -> None:
        super().__init__(message="Current password is incorrect")


class InvalidResetTokenError(BadRequestError):

    error_code = "AUTH_INVALID_RESET_TOKEN"

    def __init__(self) -> None:
        super().__init__(
            message="Password reset token is invalid or expired",
        )
