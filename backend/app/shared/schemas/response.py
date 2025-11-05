from pydantic import BaseModel, Field
from typing import Optional, Any, Dict, Generic, TypeVar, List
from datetime import datetime, timezone
from fastapi import status

T = TypeVar('T')

class SuccessResponse(BaseModel, Generic[T]):
    success: bool = Field(default=True, description="Luôn là True cho thành công")
    message: str = Field(..., description="Thông báo thành công")
    data: Optional[T] = Field(None, description="Dữ liệu trả về")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status_code: int = Field(default=status.HTTP_200_OK, description="HTTP status code")

class ErrorResponse(BaseModel):
    success: bool = Field(default=False, description="Luôn là False cho lỗi")
    message: str = Field(..., description="Thông báo lỗi")
    error_code: Optional[str] = Field(None, description="Mã lỗi để gỡ lỗi")
    error_details: Optional[Dict[str, Any]] = Field(None, description="Chi tiết lỗi bổ sung")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status_code: int = Field(default=status.HTTP_400_BAD_REQUEST, description="HTTP status code")

