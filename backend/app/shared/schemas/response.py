
from pydantic import BaseModel, Field
from typing import Optional, Any, Dict, Generic, TypeVar
from datetime import datetime, timezone

T = TypeVar('T')

class SuccessResponse(BaseModel, Generic[T]):
    success: bool = Field(default=True, description="Luôn là True cho success")
    message: str = Field(..., description="Thông báo thành công")
    data: Optional[T] = Field(None, description="Dữ liệu trả về")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ErrorResponse(BaseModel):
    success: bool = Field(default=False, description="Luôn là False cho error")
    message: str = Field(..., description="Thông báo lỗi")
    error_code: Optional[str] = Field(None, description="Mã lỗi để debug")
    error_details: Optional[Dict[str, Any]] = Field(None, description="Chi tiết lỗi thêm")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))