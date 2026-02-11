"""
Shared response schemas cho toàn bộ ứng dụng.

Cung cấp SuccessResponse dùng chung cho tất cả API endpoints.
ErrorResponse được giữ tạm thời (DEPRECATED) cho đến khi controllers
được refactor sang exception-based error handling.
"""

from datetime import datetime, timezone
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    """Response chuẩn cho các API thành công."""

    success: bool = True
    message: str = "Thành công"
    data: Optional[T] = None
    timestamp: datetime = None
    status_code: int = 200

    def __init__(self, **kwargs):
        if "timestamp" not in kwargs or kwargs["timestamp"] is None:
            kwargs["timestamp"] = datetime.now(timezone.utc)
        super().__init__(**kwargs)


class ErrorResponse(BaseModel):
    """
    ⚠️ DEPRECATED — Sẽ bị xóa khi refactor controllers.

    Dùng shared/exceptions/ thay thế cho error handling.
    Giữ lại tạm thời vì controllers vẫn tự build ErrorResponse.
    """

    success: bool = False
    message: str = "Đã xảy ra lỗi"
    error_code: Optional[str] = None
    error_details: Optional[Any] = None
    timestamp: datetime = None
    status_code: int = 500

    def __init__(self, **kwargs):
        if "timestamp" not in kwargs or kwargs["timestamp"] is None:
            kwargs["timestamp"] = datetime.now(timezone.utc)
        super().__init__(**kwargs)
