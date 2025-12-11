from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

class GuestSessionBase(BaseModel):
    ip_address: Optional[str] = Field(None, description="Địa chỉ IP của khách")
    user_agent: Optional[str] = Field(None, description="User agent")
    upload_count: int = Field(0, description="Số lần tải lên")
    analysis_count: int = Field(0, description="Số lần phân tích")
    is_active: bool = Field(True, description="Phiên còn hoạt động")
    is_converted_to_user: bool = Field(False, description="Đã chuyển thành người dùng")
    converted_user_id: Optional[uuid.UUID] = Field(None, description="ID người dùng nếu đã chuyển")

class GuestSessionCreate(GuestSessionBase):
    pass

class GuestSessionResponse(GuestSessionBase):
    session_id: uuid.UUID = Field(..., description="ID phiên")
    created_at: datetime = Field(..., description="Thời gian tạo")
    expires_at: datetime = Field(..., description="Thời gian hết hạn")
    last_activity_at: datetime = Field(..., description="Lần hoạt động cuối")

    is_expired: bool = Field(..., description="Phiên đã hết hạn")
    can_upload: bool = Field(..., description="Có thể tải lên")
    can_analyze: bool = Field(..., description="Có thể phân tích")
    remaining_uploads: int = Field(..., description="Số lần tải lên còn lại")
    remaining_analyses: int = Field(..., description="Số lần phân tích còn lại")

class GuestUploadBase(BaseModel):
    file_path: str = Field(..., description="Đường dẫn file")
    file_name: str = Field(..., description="Tên file")
    file_size: int = Field(..., gt=0, description="Kích thước file")
    mime_type: Optional[str] = Field(None, description="Loại MIME")

class GuestUploadCreate(GuestUploadBase):
    pass

class GuestUploadResponse(GuestUploadBase):
    upload_id: uuid.UUID = Field(..., description="ID tải lên")
    session_id: uuid.UUID = Field(..., description="ID phiên")
    created_at: datetime = Field(..., description="Thời gian tải lên")
    is_deleted: bool = Field(False, description="Đã xóa")
    deleted_at: Optional[datetime] = Field(None, description="Thời gian xóa")

class GuestAnalysisBase(BaseModel):
    wound_type: Optional[str] = Field(None, description="Loại vết thương")
    severity: Optional[str] = Field(None, description="Mức độ nghiêm trọng")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Độ tin cậy")
    result_json: Optional[Dict[str, Any]] = Field(None, description="Kết quả phân tích")

class GuestAnalysisCreate(GuestAnalysisBase):
    pass

class GuestAnalysisResponse(GuestAnalysisBase):
    analysis_id: uuid.UUID = Field(..., description="ID phân tích")
    session_id: uuid.UUID = Field(..., description="ID phiên")
    upload_id: Optional[uuid.UUID] = Field(None, description="ID tải lên")
    created_at: datetime = Field(..., description="Thời gian phân tích")
    is_deleted: bool = Field(False, description="Đã xóa")

class GuestStatisticsResponse(BaseModel):
    total_sessions: int = Field(..., description="Tổng số phiên")
    active_sessions: int = Field(..., description="Phiên đang hoạt động")
    total_uploads: int = Field(..., description="Tổng số tải lên")
    total_analyses: int = Field(..., description="Tổng số phân tích")
    converted_users: int = Field(..., description="Số người dùng đã chuyển đổi")
    average_session_duration: float = Field(..., description="Thời gian phiên trung bình (giờ)")