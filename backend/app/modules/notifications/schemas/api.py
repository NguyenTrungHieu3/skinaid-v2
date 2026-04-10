from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
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
    user_id: UUID
    title: str = Field(max_length=255)
    body: str
    notification_type: str = Field(max_length=50)
    data: Optional[Dict[str, Any]] = None
    action_url: Optional[str] = None
    image_url: Optional[str] = None
    priority: str = Field(default="normal", max_length=20)
