from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, timedelta, timezone
import uuid


class GuestSession(SQLModel, table=True):
    __tablename__ = "guest_sessions"
    
    session_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True
    )
    
    ip_address: Optional[str] = Field(default=None, max_length=45)
    user_agent: Optional[str] = None
    
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
    expires_at: datetime = Field(
        default_factory=lambda: (
            datetime.now(timezone.utc) + timedelta(hours=1)
        ).replace(tzinfo=None)
    )
    last_activity_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
    
    upload_count: int = Field(default=0, ge=0)
    analysis_count: int = Field(default=0, ge=0)
    
    is_active: bool = Field(default=True)
    is_converted_to_user: bool = Field(default=False)
    converted_user_id: Optional[str] = Field(
        default=None,
        foreign_key="users.user_id"
    )
    
    @property
    def is_expired(self) -> bool:
        """Check if session has expired"""
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        return now > self.expires_at
    
    @property
    def can_upload(self) -> bool:
        """Check if session can upload more files"""
        from app.shared.role_permission_enum import GUEST_LIMITS
        return (
            not self.is_expired and 
            self.is_active and 
            self.upload_count < GUEST_LIMITS["max_uploads_per_session"]
        )
    
    @property
    def can_analyze(self) -> bool:
        """Check if session can request more analyses"""
        from app.shared.role_permission_enum import GUEST_LIMITS
        return (
            not self.is_expired and 
            self.is_active and 
            self.analysis_count < GUEST_LIMITS["max_analyses_per_session"]
        )
    
    @property
    def remaining_uploads(self) -> int:
        """Get remaining upload quota"""
        from app.shared.role_permission_enum import GUEST_LIMITS
        max_uploads = GUEST_LIMITS["max_uploads_per_session"]
        return max(0, max_uploads - self.upload_count)
    
    @property
    def remaining_analyses(self) -> int:
        """Get remaining analysis quota"""
        from app.shared.role_permission_enum import GUEST_LIMITS
        max_analyses = GUEST_LIMITS["max_analyses_per_session"]
        return max(0, max_analyses - self.analysis_count)