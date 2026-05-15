from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from typing import Optional
from datetime import datetime, timezone
from uuid import uuid4, UUID


class Notification(SQLModel, table=True):
    __tablename__ = "notifications"

    notification_id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: Optional[UUID] = Field(default=None, foreign_key="users.user_id", index=True)
    device_id: Optional[str] = Field(default=None, max_length=100)

    title: str = Field(max_length=255)
    body: str
    notification_type: str = Field(max_length=50)

    data: Optional[dict] = Field(default=None, sa_column=Column(JSONB, nullable=True))
    action_url: Optional[str] = Field(default=None)
    image_url: Optional[str] = Field(default=None)

    priority: str = Field(default="normal", max_length=20)
    severity: str = Field(default="info", max_length=20)
    scheduled_at: Optional[datetime] = Field(default=None)
    sent_at: Optional[datetime] = Field(default=None)
    delivered_at: Optional[datetime] = Field(default=None)
    read_at: Optional[datetime] = Field(default=None)

    status: str = Field(default="pending", max_length=20, index=True)
    failure_reason: Optional[str] = Field(default=None, max_length=255)
    retry_count: int = Field(default=0, ge=0)
    max_retries: int = Field(default=3)

    provider: Optional[str] = Field(default=None, max_length=20)
    provider_message_id: Optional[str] = Field(default=None, max_length=255)
    provider_response: Optional[dict] = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
