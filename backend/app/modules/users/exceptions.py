from app.shared.exceptions.base import NotFoundError, BadRequestError


class UserManagementNotFoundError(NotFoundError):
    def __init__(self, message: str = 'User not found'):
        super().__init__(message=message)


class UserActionFailedError(BadRequestError):
    def __init__(self, message: str = 'User action failed'):
        super().__init__(message=message)


class ProfileNotFoundError(NotFoundError):
    error_code: str = "PROFILE_NOT_FOUND"

    def __init__(self, user_id: str | None = None) -> None:
        message = (
            f"Không tìm thấy hồ sơ cho user {user_id}"
            if user_id
            else "Không tìm thấy hồ sơ người dùng"
        )
        super().__init__(message=message)


class InvalidProfileDataError(BadRequestError):
    error_code: str = "PROFILE_INVALID_DATA"

    def __init__(self, message: str = "Dữ liệu hồ sơ không hợp lệ") -> None:
        super().__init__(message=message)


class AvatarUploadError(BadRequestError):
    error_code: str = "PROFILE_AVATAR_UPLOAD_ERROR"

    def __init__(self, message: str = "Lỗi khi upload avatar") -> None:
        super().__init__(message=message)
