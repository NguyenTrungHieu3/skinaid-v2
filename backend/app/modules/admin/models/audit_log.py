"""
Admin Audit Log Model
"""

from sqlmodel import SQLModel, Field
from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional, Dict, Any
from pydantic import BaseModel


class AdminAuditLog(SQLModel, table=True):
    """Model cho bảng admin audit logs"""
    
    __tablename__ = "admin_audit_logs"
    
    # Primary key
    log_id: UUID = Field(default_factory=uuid4, primary_key=True)
    
    # Who performed the action
    admin_user_id: UUID = Field(foreign_key="users.user_id")
    admin_email: str = Field(max_length=255)
    admin_role: str = Field(max_length=50)
    
    # What action was performed
    action: str = Field(max_length=100)  # CREATE_USER, UPDATE_USER, DELETE_USER, etc.
    resource_type: str = Field(max_length=100)  # user, first_aid_guide, etc.
    resource_id: Optional[str] = Field(default=None, max_length=255)
    
    # Action details
    description: Optional[str] = None
    changes: Optional[Dict[str, Any]] = Field(default=None, sa_column_kwargs={"type_": "JSONB"})
    metadata: Optional[Dict[str, Any]] = Field(default=None, sa_column_kwargs={"type_": "JSONB"})
    
    # HTTP request details
    http_method: Optional[str] = Field(default=None, max_length=10)
    endpoint: Optional[str] = Field(default=None, max_length=500)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    # Status and timing
    status: str = Field(default="success", max_length=50)
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AuditLogCreate(BaseModel):
    """Schema để tạo audit log"""
    
    admin_user_id: UUID
    admin_email: str
    admin_role: str
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    description: Optional[str] = None
    changes: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    http_method: Optional[str] = None
    endpoint: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    status: str = "success"
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None


class AuditLogResponse(BaseModel):
    """Schema cho phản hồi audit log"""
    
    log_id: UUID
    admin_email: str
    admin_role: str
    action: str
    resource_type: str
    resource_id: Optional[str]
    description: Optional[str]
    changes: Optional[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]]
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True
