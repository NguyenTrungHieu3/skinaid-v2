from app.shared.exceptions.base import NotFoundError, ForbiddenError


class NotificationNotFoundError(NotFoundError):
    def __init__(self, notification_id: str = None):
        message = (
            f"Không tìm thấy notification với ID {notification_id}"
            if notification_id
            else "Không tìm thấy notification"
        )
        super().__init__(message=message)
        self.error_code = "NOTIFICATION_NOT_FOUND"


class NotificationForbiddenError(ForbiddenError):
    def __init__(self):
        super().__init__(message="Bạn không có quyền thao tác với notification này")
        self.error_code = "NOTIFICATION_FORBIDDEN"
