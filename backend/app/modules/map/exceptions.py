from app.shared.exceptions.base import NotFoundError, InternalError

class LocationNotFoundError(NotFoundError):
    """Raised when a location, route, or address cannot be found"""
    def __init__(self, message: str = "Location not found"):
        super().__init__(message=message)

class MapServiceUnavailableError(InternalError):
    """Raised when the third-party map service is unavailable or encounters an error"""
    def __init__(self, message: str = "Map service is currently unavailable"):
        super().__init__(message=message)
