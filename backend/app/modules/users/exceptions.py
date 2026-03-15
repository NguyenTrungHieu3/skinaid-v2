from app.shared.exceptions.base import NotFoundError, BadRequestError

class UserManagementNotFoundError(NotFoundError):
    def __init__(self, message: str = 'User not found'):
        super().__init__(message=message)

class UserActionFailedError(BadRequestError):
    def __init__(self, message: str = 'User action failed'):
        super().__init__(message=message)
