from app.shared.exceptions import AppException


class AIError(AppException):
    """Base error for AI module."""

    status_code: int = 500
    error_code: str = "AI_ERROR"


class WoundAnalysisNotFoundError(AIError):
    """Raised when wound analysis is not found."""

    status_code: int = 404
    error_code: str = "WOUND_ANALYSIS_NOT_FOUND"

    def __init__(self, message: str = "Wound analysis not found", details=None):
        super().__init__(message=message, details=details)


class AIProcessFailedError(AIError):
    """Raised when AI processing fails."""

    status_code: int = 500
    error_code: str = "AI_PROCESS_FAILED"

    def __init__(self, message: str = "AI processing failed", details=None):
        super().__init__(message=message, details=details)


class ImageDownloadError(AIError):
    """Raised when image download fails."""

    status_code: int = 400
    error_code: str = "IMAGE_DOWNLOAD_FAILED"

    def __init__(self, message: str = "Failed to download image", details=None):
        super().__init__(message=message, details=details)
