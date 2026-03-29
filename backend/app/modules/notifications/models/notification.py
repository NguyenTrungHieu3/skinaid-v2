from sqlmodel import SQLModel, Field
from sqlalchemy import Column, UUID
from sqlalchemy.dialects.postgresql import JSONB
from typing import Optional
from datetime import datetime, timezone
from uuid import uuid4, UUID

class Notification(SQLModel, table=True):
    __tablename__ = "notifications"

    notification_id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.user_id", index=True)
    
    title: str = Field(max_length=255)
    body: str
    notification_type: str = Field(max_length=50) # 'alert', 'reminder', 'system'
    data: dict = Field(default_factory=dict, sa_column=Column(JSONB))
    priority: str = Field(default="normal", max_length=20) # 'high', 'normal', 'low'
    
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    
    status: str = Field(default="pending", max_length=20) # 'pending', 'sent', 'failed'
    retry_count: int = Field(default=0, ge=0)
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
