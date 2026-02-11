from app.shared.exceptions import NotFoundError, BadRequestError, ConflictError, ForbiddenError


class AdminUserNotFoundError(NotFoundError):
    """Raised when an admin user operation fails to find the user."""

    def __init__(self, message="Admin user not found", details=None):
        super().__init__(message=message, details=details)


class AdminStatsError(BadRequestError):
    """Raised when retrieving statistics fails."""

    def __init__(self, message="Failed to retrieve statistics", details=None):
        super().__init__(message=message, details=details)


class AdminActionFailedError(BadRequestError):
    """Raised when a general admin action fails."""

    def __init__(self, message="Admin action failed", details=None):
        super().__init__(message=message, details=details)
