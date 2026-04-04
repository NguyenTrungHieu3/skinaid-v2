from sqlmodel import SQLModel, Field
from sqlalchemy import Column, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from typing import Optional
from datetime import datetime, timezone
from uuid import uuid4, UUID


class DeviceSession(SQLModel, table=True):
    __tablename__ = "device_sessions"
    __table_args__ = (
        UniqueConstraint("user_id", "device_id", name="device_sessions_user_device_key"),
    )

    session_id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: Optional[UUID] = Field(default=None, foreign_key="users.user_id", index=True)
    device_id: str = Field(max_length=100, index=True)

    platform: str = Field(max_length=20)
    app_version: Optional[str] = Field(default=None, max_length=50)
    os_version: Optional[str] = Field(default=None, max_length=50)
    device_model: Optional[str] = Field(default=None, max_length=100)
    device_name: Optional[str] = Field(default=None, max_length=255)

    push_token: Optional[str] = Field(default=None)
    push_enabled: bool = Field(default=True)
    last_notification_at: Optional[datetime] = Field(default=None)

    cached_sources: Optional[dict] = Field(default=None, sa_column=Column(JSONB, nullable=True))
    cache_size_mb: Optional[float] = Field(default=None)
    cache_version: Optional[str] = Field(default=None, max_length=50)
    last_sync_at: Optional[datetime] = Field(default=None)

    pending_syncs: Optional[dict] = Field(default=None, sa_column=Column(JSONB, nullable=True))

    sync_status: str = Field(default="synced", max_length=20)

    rate_limit_remaining: Optional[int] = Field(default=100)
    rate_limit_reset_at: Optional[datetime] = Field(default=None)

    is_trusted: bool = Field(default=False)
    last_trusted_at: Optional[datetime] = Field(default=None)

    is_active: bool = Field(default=True)
    last_activity_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
