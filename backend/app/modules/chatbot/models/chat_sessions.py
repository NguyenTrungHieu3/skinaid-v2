from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from typing import Optional
from datetime import datetime, timezone
from uuid import uuid4, UUID


class ChatSession(SQLModel, table=True):
    __tablename__ = "chat_sessions"

    session_id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.user_id", index=True)
    analysis_id: Optional[UUID] = Field(default=None, foreign_key="analyses.analysis_id", index=True)

    system_prompt_version: Optional[str] = Field(default="v2", max_length=20)
    wound_context: Optional[dict] = Field(default=None, sa_column=Column(JSONB, nullable=True))
    # anxious | calm | urgent
    user_mood: Optional[str] = Field(default=None, max_length=20)

    # active | closed | expired | escalated
    status: str = Field(default="active", max_length=20, index=True)
    closure_reason: Optional[str] = Field(default=None, max_length=100)

    message_limit: int = Field(default=50)
    message_count: int = Field(default=0, ge=0)

    last_message_at: Optional[datetime] = Field(default=None)
    expires_at: Optional[datetime] = Field(default=None)

    total_tokens_used: int = Field(default=0)
    total_cost_usd: Optional[float] = Field(default=0.0)
    llm_model: Optional[str] = Field(default=None, max_length=50)
    language: str = Field(default="vi", max_length=10)

    user_rating: Optional[int] = Field(default=None)
    user_feedback: Optional[str] = Field(default=None)

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
