from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class NotificationResponse(BaseModel):
    notification_id: UUID
    user_id: Optional[UUID]
    device_id: Optional[str]

    title: str
    body: str
    notification_type: str

    data: Optional[Dict[str, Any]]
    action_url: Optional[str]
    image_url: Optional[str]

    priority: str
    severity: str
    scheduled_at: Optional[datetime]
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    read_at: Optional[datetime]

    status: str
    failure_reason: Optional[str]
    retry_count: int
    max_retries: int

    provider: Optional[str]
    provider_message_id: Optional[str]

    created_at: datetime
    updated_at: datetime

    is_read: bool = False

    @model_validator(mode="after")
    def compute_is_read(self) -> "NotificationResponse":
        self.is_read = self.read_at is not None
        return self

    model_config = {"from_attributes": True}


class NotificationListResponse(BaseModel):
    items: List[NotificationResponse]
    total: int
    unread_count: int


class UnreadCountResponse(BaseModel):
    unread_count: int


class CreateNotificationRequest(BaseModel):
    """
    Tạo thông báo cho người dùng.

    - recipient_type="specific" (mặc định): gửi đến user_id cụ thể.
    - recipient_type="all": gửi đến toàn bộ user đang active;
      không cần truyền user_id.
    """
    recipient_type: Literal["specific", "all"] = Field(
        default="specific",
        description='"specific" → gửi 1 user, "all" → broadcast toàn bộ user active',
    )
    user_id: Optional[UUID] = Field(
        default=None,
        description="Bắt buộc khi recipient_type='specific'",
    )
    title: str = Field(max_length=255)
    body: str
    notification_type: str = Field(max_length=50)
    data: Optional[Dict[str, Any]] = None
    action_url: Optional[str] = None
    image_url: Optional[str] = None
    priority: str = Field(default="normal", max_length=20)
    severity: str = Field(default="info", max_length=20)

    @model_validator(mode="after")
    def _check_user_id_required(self) -> "CreateNotificationRequest":
        if self.recipient_type == "specific" and self.user_id is None:
            raise ValueError("user_id là bắt buộc khi recipient_type='specific'")
        return self


class BroadcastNotificationResponse(BaseModel):
    """Trả về khi recipient_type='all'."""
    sent_count: int
    recipient_type: str = "all"
    title: str
    notification_type: str

