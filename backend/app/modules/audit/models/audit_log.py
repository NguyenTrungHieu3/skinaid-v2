from sqlmodel import SQLModel, Column, Field, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID as PostgresUUID
from uuid import uuid4, UUID
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import json

class AuditLog(SQLModel, table=True): 
    __tablename__ =  "audit_logs"

    audit_action_id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: Optional[UUID] = Field(
        default=None,
        sa_column=Column(
            PostgresUUID(as_uuid=True),
            ForeignKey("users.user_id", ondelete="SET NULL"),
            index=True,
            nullable=True,
        ),
    )
    action: str = Field(max_length=100, nullable=False, index=True)
    action_category: Optional[str] = Field(default=None, max_length=50, index=True)

    resource_type: Optional[str] = Field(default=None, max_length=50, index=True) 

    resource_id: Optional[str] = Field(default=None, max_length=255, index=True)
    ip_address: Optional[str] = Field(default=None, max_length=45) 
    user_agent: Optional[str] = Field(default=None, max_length=500) 
    success: bool = Field(default=True, nullable=False)
    response_status: Optional[int] = None
    error_code: Optional[str] = Field(default=None, max_length=50)
    error_message:Optional[str] =Field(default=None, max_length=500)
    request_body: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSONB, nullable=True))
    is_guest: bool = Field(default=False, nullable=False)
    guest_session_id: Optional[UUID] = Field(
        default=None,
        sa_column=Column(
            PostgresUUID(as_uuid=True),
            ForeignKey("guest_sessions.session_id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    device_id: Optional[str] = Field(default=None, max_length=100)
    details: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSONB, nullable=True))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)

    def to_dict(self) -> Dict[str, Any]: 
        return {
            "audit_action_id": self.audit_action_id,
            "user_id": self.user_id,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "success": self.success,
            "error_message": self.error_message,
            "is_guest": self.is_guest,
            "guest_session_id": self.guest_session_id,
            "details": self.details,
            "timestamp": self.timestamp
        }

    def __repr__(self):
        return f"<AuditLog(audit_action_id={self.audit_action_id}, action={self.action}, success={self.success})>"

