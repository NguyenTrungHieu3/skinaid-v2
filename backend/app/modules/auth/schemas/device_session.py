from datetime import datetime
from typing import Optional, Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


PlatformLiteral = Literal["ios", "android", "web"]
SyncStatusLiteral = Literal["synced", "pending", "conflicting"]


class DeviceRegisterRequest(BaseModel):
    device_id: str = Field(..., min_length=1, max_length=100)
    platform: PlatformLiteral
    app_version: Optional[str] = Field(default=None, max_length=50)
    os_version: Optional[str] = Field(default=None, max_length=50)
    device_model: Optional[str] = Field(default=None, max_length=100)
    device_name: Optional[str] = Field(default=None, max_length=255)
    push_token: Optional[str] = None
    push_enabled: bool = True


class DeviceUpdateRequest(BaseModel):
    device_name: Optional[str] = Field(default=None, max_length=255)
    app_version: Optional[str] = Field(default=None, max_length=50)
    os_version: Optional[str] = Field(default=None, max_length=50)
    push_token: Optional[str] = None
    push_enabled: Optional[bool] = None
    cached_sources: Optional[dict[str, Any]] = None
    cache_size_mb: Optional[float] = None
    cache_version: Optional[str] = Field(default=None, max_length=50)


class SyncStatusUpdateRequest(BaseModel):
    sync_status: SyncStatusLiteral
    pending_syncs: Optional[dict[str, Any]] = None
    last_sync_at: Optional[datetime] = None


class DeviceSessionResponse(BaseModel):
    session_id: UUID
    user_id: UUID
    device_id: str
    platform: str
    app_version: Optional[str] = None
    os_version: Optional[str] = None
    device_model: Optional[str] = None
    device_name: Optional[str] = None
    push_enabled: bool
    push_token: Optional[str] = None
    last_notification_at: Optional[datetime] = None
    cached_sources: Optional[dict[str, Any]] = None
    cache_size_mb: Optional[float] = None
    cache_version: Optional[str] = None
    last_sync_at: Optional[datetime] = None
    pending_syncs: Optional[dict[str, Any]] = None
    sync_status: str
    is_trusted: bool
    last_trusted_at: Optional[datetime] = None
    is_active: bool
    last_activity_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DeviceSessionListResponse(BaseModel):
    items: list[DeviceSessionResponse]
    total: int
