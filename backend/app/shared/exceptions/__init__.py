from app.shared.exceptions.base import (
    AppException,
    BadRequestError,
    ConflictError,
    ForbiddenError,
    InternalError,
    NotFoundError,
    ServiceUnavailableError,
    UnauthorizedError,
    ValidationError,
)
from app.shared.exceptions.handler import (
    app_exception_handler,
    generic_exception_handler,
)

__all__ = [
    # Base exceptions
    "AppException",
    "NotFoundError",
    "BadRequestError",
    "ValidationError",
    "ConflictError",
    "UnauthorizedError",
    "ForbiddenError",
    "InternalError",
    "ServiceUnavailableError",
    # Handlers
    "app_exception_handler",
    "generic_exception_handler",
]
