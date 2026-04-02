from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from datetime import datetime


class AuditLogFilterParams(BaseModel):
    page: int = Field(1, ge=1, description="Trang hiện tại")
    limit: int = Field(20, ge=1, le=100, description="Số lượng logs mỗi trang")
    user_id: Optional[UUID] = Field(None, description="Lọc theo user ID")
    action: Optional[str] = Field(None, description="Lọc theo hành động")
    resource_type: Optional[str] = Field(
        None, description="Lọc theo loại resource")
    success: Optional[bool] = Field(
        None, description="Lọc theo trạng thái thành công/thất bại")
    is_guest: Optional[bool] = Field(
        None, description="Lọc theo khách vãng lai")
    search: Optional[str] = Field(
        None, description="Tìm kiếm trong action, description, email, user_name")
    role_name: Optional[str] = Field(
        None, description="Lọc theo vai trò của user")
    start_date: Optional[datetime] = Field(None, description="Lọc từ ngày")
    end_date: Optional[datetime] = Field(None, description="Lọc đến ngày")
    log_type: Optional[str] = Field(
        None, description="Lọc theo loại log: admin_action / user_activity / system_error")
    level: Optional[str] = Field(
        None, description="Lọc theo mức độ: info / warning / error")


class AuditLogResponse(BaseModel):
    audit_action_id: UUID
    user_id: Optional[UUID] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    success: bool
    error_message: Optional[str] = None
    is_guest: bool
    guest_session_id: Optional[UUID] = None
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None

    # User info (joined)
    username: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AuditLogListResponse(BaseModel):
    logs: List[Dict[str, Any]]
    total: int
    page: int
    limit: int
    total_pages: int
    has_more: bool


class AuditStatsResponse(BaseModel):
    total_logs: int
    success_rate: float
    top_actions: List[Dict[str, Any]]
    daily_activity: List[Dict[str, Any]]
