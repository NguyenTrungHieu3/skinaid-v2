from sqlmodel import SQLModel, Field
from sqlalchemy import Column, UUID
from sqlalchemy.dialects.postgresql import JSONB
from typing import Optional
from datetime import datetime, timezone
from uuid import uuid4, UUID

class DeviceSession(SQLModel, table=True):
    __tablename__ = "device_sessions"

    device_session_id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.user_id", index=True)
    
    device_id: str = Field(max_length=255, unique=True, index=True)
    device_name: Optional[str] = Field(default=None, max_length=255)
    push_token: Optional[str] = Field(default=None, max_length=500)
    push_enabled: bool = Field(default=True)
    
    cached_sources: dict = Field(default_factory=dict, sa_column=Column(JSONB))
    cache_size_mb: Optional[float] = None
    
    last_sync_at: Optional[datetime] = None
    sync_status: str = Field(default="synced", max_length=20)
    app_version: Optional[str] = Field(default=None, max_length=50)
    
    rate_limit_reset_at: Optional[datetime] = None
    is_trusted: bool = Field(default=False)
    is_active: bool = Field(default=True)
    
    last_activity_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
