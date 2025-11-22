from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict, field_validator
from uuid import UUID
from datetime import datetime


class AuditLogResponse(BaseModel):
    audit_action_id: UUID = Field(..., description="ID của bản ghi audit")
    user_id: Optional[UUID] = Field(None, description="ID người dùng thực hiện hành động")
    action: str = Field(..., description="Tên hành động (login, upload, delete...)")
    resource_type: Optional[str] = Field(None, description="Loại tài nguyên (user, file...)")
    resource_id: Optional[str] = Field(None, description="ID của tài nguyên bị tác động")
    ip_address: Optional[str] = Field(None, description="Địa chỉ IP của client")
    user_agent: Optional[str] = Field(None, description="User agent của trình duyệt")
    success: bool = Field(..., description="Hành động thành công hay thất bại")
    error_message: Optional[str] = Field(None, description="Thông báo lỗi nếu thất bại")
    is_guest: bool = Field(..., description="Có phải người dùng khách không")
    guest_session_id: Optional[UUID] = Field(None, description="ID phiên khách nếu là guest")
    details: Optional[Dict[str, Any]] = Field(None, description="Thông tin chi tiết thêm")
    timestamp: datetime = Field(..., description="Thời gian xảy ra hành động")
    user_name: Optional[str] = Field(None, description="Tên người dùng")
    email: Optional[str] = Field(None, description="Email người dùng")
    role_name: Optional[str] = Field(None, description="Vai trò người dùng")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "audit_action_id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "123e4567-e89b-12d3-a456-426614174001",
                "action": "login",
                "resource_type": "user",
                "resource_id": "123e4567-e89b-12d3-a456-426614174001",
                "ip_address": "192.168.1.1",
                "user_agent": "Mozilla/5.0...",
                "success": True,
                "error_message": None,
                "is_guest": False,
                "guest_session_id": None,
                "details": {"login_method": "email"},
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }
    )


class AuditStatsResponse(BaseModel):
    total_logs: int = Field(..., ge=0, description="Tổng số bản ghi audit")
    success_rate: float = Field(..., ge=0, le=100, description="Tỷ lệ thành công (%)")
    action_distribution: Dict[str, int] = Field(..., description="Số lượng mỗi loại hành động")
    recent_activity_24h: int = Field(..., ge=0, description="Số bản ghi trong 24h gần nhất")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_logs": 1000,
                "success_rate": 95.5,
                "action_distribution": {
                    "login": 450,
                    "logout": 400,
                    "user_file_upload": 100,
                    "guest_upload": 50
                },
                "recent_activity_24h": 150
            }
        }
    )


class AuditLogListResponse(BaseModel):
    logs: List[AuditLogResponse] = Field(..., description="Danh sách bản ghi audit")
    total: int = Field(..., ge=0, description="Tổng số bản ghi (tất cả trang)")
    page: int = Field(..., ge=1, description="Trang hiện tại")
    limit: int = Field(..., ge=1, le=100, description="Số bản ghi mỗi trang")
    total_pages: int = Field(..., ge=0, description="Tổng số trang")
    has_more: bool = Field(..., description="Còn trang tiếp theo không")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "logs": [],
                "total": 100,
                "page": 1,
                "limit": 50,
                "total_pages": 2,
                "has_more": True
            }
        }
    )


class AuditLogFilterParams(BaseModel):
    user_id: Optional[UUID] = Field(None,description="Lọc theo user ID")
    action: Optional[str] = Field(None,max_length=100,description="Lọc theo loại hành động")
    resource_type: Optional[str] = Field(None, max_length=50, description="Lọc theo loại tài nguyên")
    success: Optional[bool] = Field(None, description="Lọc theo trạng thái thành công/thất bại")
    is_guest: Optional[bool] = Field(None, description="Lọc theo guest/user")
    search: Optional[str] = Field(None, max_length=255, description="Tìm kiếm trong action, user_name, email, error_message")
    role_name: Optional[str] = Field(None, max_length=50, description="Lọc theo vai trò người dùng (admin, user, ...)")
    start_date: Optional[datetime] = Field(None, description="Lọc từ ngày (ISO 8601: 2025-11-01T00:00:00Z)")
    end_date: Optional[datetime] = Field(None, description="Lọc đến ngày (ISO 8601: 2025-11-11T23:59:59Z)")
    page: int = Field(1, ge=1, description="Số trang (bắt đầu từ 1)")
    limit: int = Field(50, ge=1, le=100, description="Số bản ghi mỗi trang (tối đa 100)")

    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v: Optional[datetime], info) -> Optional[datetime]:
        if v is not None and info.data.get('start_date') is not None:
            start_date = info.data['start_date']
            if v <= start_date:
                raise ValueError('end_date phải sau start_date')
        return v