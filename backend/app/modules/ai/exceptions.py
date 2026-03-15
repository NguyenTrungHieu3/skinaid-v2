from app.shared.exceptions.base import AppException, NotFoundError, InternalError, BadRequestError


class AIError(InternalError):
    error_code: str = "AI_ERROR"


class WoundAnalysisNotFoundError(NotFoundError):
    error_code: str = "WOUND_ANALYSIS_NOT_FOUND"

    def __init__(self, message: str = "Wound analysis not found", details=None):
        super().__init__(message=message, details=details)


class AIProcessFailedError(InternalError):
    error_code: str = "AI_PROCESS_FAILED"

    def __init__(self, message: str = "AI processing failed", details=None):
        super().__init__(message=message, details=details)


class ImageDownloadError(BadRequestError):
    error_code: str = "IMAGE_DOWNLOAD_FAILED"

    def __init__(self, message: str = "Failed to download image", details=None):
        super().__init__(message=message, details=details)
