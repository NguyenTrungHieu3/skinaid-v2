from sqlmodel import SQLModel, Field
from sqlalchemy import UUID
from typing import Optional
from datetime import datetime, timezone
from uuid import uuid4, UUID

class ChatSession(SQLModel, table=True):
    __tablename__ = "chat_sessions"

    session_id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.user_id", index=True)
    analysis_id: Optional[UUID] = Field(default=None, foreign_key="analyses.analysis_id", index=True)
    
    message_count: int = Field(default=0, ge=0)
    last_message_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    status: str = Field(default="active", max_length=20)
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
