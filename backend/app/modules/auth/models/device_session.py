from sqlmodel import SQLModel, Field
from sqlalchemy import Column, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from typing import Optional, Any
from datetime import datetime, timezone
from uuid import uuid4, UUID


class DeviceSession(SQLModel, table=True):
    __tablename__ = "device_sessions"
    __table_args__ = (UniqueConstraint("user_id", "device_id", name="uq_device_sessions_user_device"),)

    session_id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.user_id", index=True, nullable=False)

    device_id: str = Field(max_length=100, nullable=False, index=True)

    # ios | android | web
    platform: str = Field(max_length=20, nullable=False)
    app_version: Optional[str] = Field(default=None, max_length=50)
    os_version: Optional[str] = Field(default=None, max_length=50)
    device_model: Optional[str] = Field(default=None, max_length=100)
    device_name: Optional[str] = Field(default=None, max_length=255)

    push_token: Optional[str] = Field(default=None)
    push_enabled: bool = Field(default=True, nullable=False)
    last_notification_at: Optional[datetime] = None

    cached_sources: Optional[dict[str, Any]] = Field(default=None, sa_column=Column(JSONB, nullable=True))
    cache_size_mb: Optional[float] = None
    cache_version: Optional[str] = Field(default=None, max_length=50)
    last_sync_at: Optional[datetime] = None

    pending_syncs: Optional[dict[str, Any]] = Field(default=None, sa_column=Column(JSONB, nullable=True))
    # synced | pending | conflicting
    sync_status: str = Field(default="synced", max_length=20)

    is_trusted: bool = Field(default=False, nullable=False)
    last_trusted_at: Optional[datetime] = None

    is_active: bool = Field(default=True, nullable=False)
    last_activity_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)
