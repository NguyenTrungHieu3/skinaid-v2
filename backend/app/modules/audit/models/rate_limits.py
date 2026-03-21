from sqlmodel import SQLModel, Field
from sqlalchemy import UUID
from typing import Optional
from datetime import datetime, timezone
from uuid import uuid4, UUID

class RateLimit(SQLModel, table=True):
    __tablename__ = "rate_limits"

    limit_id: UUID = Field(default_factory=uuid4, primary_key=True)
    ip_address: Optional[str] = Field(default=None, max_length=45, index=True)
    device_id: Optional[str] = Field(default=None, max_length=255, index=True)
    user_id: Optional[UUID] = Field(default=None, foreign_key="users.user_id", index=True)
    
    endpoint: Optional[str] = Field(default=None, max_length=255)
    limit_value: int = Field(ge=0)
    window_seconds: int = Field(ge=0)
    current_count: int = Field(default=0, ge=0)
    
    window_start_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    window_reset_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
