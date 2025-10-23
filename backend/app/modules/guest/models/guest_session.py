from sqlmodel import SQLModel, Field
from sqlalchemy import UUID
from typing import Optional
from datetime import datetime, timedelta, timezone
import uuid

class GuestSession(SQLModel, table=True):
    __tablename__ = "guest_sessions"

    session_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    ip_address: Optional[str] = Field(default=None, max_length=45)
    user_agent: Optional[str] = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    expires_at: datetime = Field(default_factory=lambda: (datetime.now(timezone.utc) + timedelta(hours=1)).replace(tzinfo=None))
    last_activity_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    upload_count: int = Field(default=0, ge=0)
    analysis_count: int = Field(default=0, ge=0)

    is_active: bool = Field(default=True)
    is_converted_to_user: bool = Field(default=False)
    converted_user_id: Optional[uuid.UUID] = Field(default=None, foreign_key="users.user_id")

    @property
    def is_expired(self) -> bool:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        return now > self.expires_at

    @property
    def can_upload(self) -> bool:
        return not self.is_expired and self.is_active and self.upload_count < 5

    @property
    def can_analyze(self) -> bool:
        return not self.is_expired and self.is_active and self.analysis_count < 3

    @property
    def remaining_uploads(self) -> int:
        return max(0, 5 - self.upload_count)

    @property
    def remaining_analyses(self) -> int:
        return max(0, 3 - self.analysis_count)