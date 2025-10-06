from fastapi import HTTPException, status
from app.utils.constants.error_codes import * 


class AppBaseException(Exception): 
    """
    Base class for custom exceptions in the service/business logic layer.

    - Dùng trong service (business logic), KHÔNG trực tiếp trả về response cho client.
    - Thường được raise trong các tình huống domain-specific, ví dụ:
        + UserAlreadyExistsException
        + InvalidCredentialsException
        + WeakPasswordError
    - Controller layer sẽ bắt (catch) các exception này và chuyển đổi sang AppHTTPException
      hoặc HTTPException để trả về cho client.
    """

    def __init__(self, message: str, error_code: str = None): 
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class AppHTTPException(HTTPException): 
    """
    Wrapper class cho FastAPI HTTPException, dùng ở API/controller layer.

    - Extend từ FastAPI.HTTPException để có thể raise trực tiếp trong endpoint.
    - Cho phép gắn thêm `error_code` chuẩn hóa từ hệ thống (ví dụ: AUTH_INVALID_CREDENTIALS).
    - Khi raise, FastAPI sẽ tự động build response JSON với:
        + status_code: mã HTTP (401, 403, 404, 500, ...)
        + detail: thông điệp chi tiết
        + headers: thêm metadata (ví dụ WWW-Authenticate cho Bearer token)
        + error_code: mã lỗi nội bộ để FE/Client mapping.

    Ví dụ:
        raise AppHTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            error_code=AUTH_INVALID_TOKEN
        )
    """

    def __init__(self, status_code: int, detail: str, headers: dict = None, error_code: str = None):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = error_code
