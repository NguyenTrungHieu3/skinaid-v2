from app.shared.exceptions.base import AppException


class GuestSessionNotFoundError(AppException):
    def __init__(self, session_id: str = None):
        message = f"Không tìm thấy phiên khách{f' với ID {session_id}' if session_id else ''}"
        super().__init__(
            message=message,
            error_code="GUEST_SESSION_NOT_FOUND",
            status_code=404,
        )


class AnalysisClaimError(AppException):
    def __init__(self, message: str = "Không thể nhận phân tích này"):
        super().__init__(
            message=message,
            error_code="ANALYSIS_CLAIM_FAILED",
            status_code=400,
        )
