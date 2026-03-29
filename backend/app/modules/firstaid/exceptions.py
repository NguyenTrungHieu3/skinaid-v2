from app.shared.exceptions.base import NotFoundError, ConflictError, BadRequestError


class FirstAidGuideNotFoundError(NotFoundError):
    def __init__(self, guide_id: str = None, message: str = None):
        if not message:
            message = f"Không tìm thấy hướng dẫn sơ cứu{f' với ID {guide_id}' if guide_id else ''}"
        super().__init__(
            message=message,
        )
        self.error_code = "GUIDE_NOT_FOUND"


class GuideAlreadyExistsError(ConflictError):
    def __init__(self, message: str):
        super().__init__(
            message=message,
        )
        self.error_code = "GUIDE_ALREADY_EXISTS"


class InvalidGuideDataError(BadRequestError):
    def __init__(self, message: str):
        super().__init__(
            message=message,
        )
        self.error_code = "INVALID_GUIDE_DATA"
