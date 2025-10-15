from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class ValidationErrorDetail(BaseModel):
    error_code: str = Field(..., description="Mã lỗi xác thực")
    error_message: str = Field(..., description="Thông báo lỗi chi tiết")
    field_name: Optional[str] = Field(None, description="Tên trường dữ liệu có lỗi")

class UploadValidationCreate(BaseModel):
    user_id: Optional[str] = Field(None, description="ID người dùng (nếu có)")
    file_name: Optional[str] = Field(None, description="Tên file")
    file_size: Optional[int] = Field(None, description="Kích thước file")
    file_type: Optional[str] = Field(None, description="Loại file")
    validation_passed: bool = Field(..., description="Kết quả xác thực")
    validation_errors: Optional[Dict[str, Any]] = Field(None, description="Chi tiết lỗi xác thực")
    ip_address: Optional[str] = Field(None, description="Địa chỉ IP")
    user_agent: Optional[str] = Field(None, description="User agent")

class UploadValidationResponse(UploadValidationCreate):
    upload_validations_id: str = Field(..., description="ID bản ghi xác thực")
    request_id: str = Field(..., description="ID yêu cầu")
    attempt_count: int = Field(..., description="Số lần thử")
    created_at: datetime = Field(..., description="Thời gian tạo")
    updated_at: Optional[datetime] = Field(None, description="Thời gian cập nhật cuối cùng")