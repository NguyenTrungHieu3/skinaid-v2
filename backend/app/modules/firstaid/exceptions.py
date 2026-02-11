from app.shared.exceptions.base import AppException


class FirstAidGuideNotFoundError(AppException):
    def __init__(self, guide_id: str = None, message: str = None):
        if not message:
            message = f"Không tìm thấy hướng dẫn sơ cứu{f' với ID {guide_id}' if guide_id else ''}"
        super().__init__(
            message=message,
            error_code="GUIDE_NOT_FOUND",
            status_code=404,
        )


class GuideAlreadyExistsError(AppException):
    def __init__(self, message: str):
        super().__init__(
            message=message,
            error_code="GUIDE_ALREADY_EXISTS",
            status_code=409,
        )


class InvalidGuideDataError(AppException):
    def __init__(self, message: str):
        super().__init__(
            message=message,
            error_code="INVALID_GUIDE_DATA",
            status_code=400,
        )
