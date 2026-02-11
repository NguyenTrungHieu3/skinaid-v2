"""
Profile Exceptions — Custom exceptions cho module Profile.
"""

from app.shared.exceptions import (
    BadRequestError,
    NotFoundError,
)


class ProfileNotFoundError(NotFoundError):
    """không tìm thấy hồ sơ người dùng."""

    def __init__(self, user_id: str | None = None) -> None:
        message = (
            f"Không tìm thấy hồ sơ cho user {user_id}"
            if user_id
            else "Không tìm thấy hồ sơ người dùng"
        )
        super().__init__(
            message=message,
            error_code="PROFILE_NOT_FOUND",
        )


class InvalidProfileDataError(BadRequestError):
    """Dữ liệu hồ sơ không hợp lệ."""

    def __init__(self, message: str = "Dữ liệu hồ sơ không hợp lệ") -> None:
        super().__init__(
            message=message,
            error_code="PROFILE_INVALID_DATA",
        )


class AvatarUploadError(BadRequestError):
    """Lỗi khi upload avatar."""

    def __init__(self, message: str = "Lỗi khi upload avatar") -> None:
        super().__init__(
            message=message,
            error_code="PROFILE_AVATAR_UPLOAD_ERROR",
        )
