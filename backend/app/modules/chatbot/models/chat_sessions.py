from sqlmodel import SQLModel, Field
from sqlalchemy import Column, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, timezone
from uuid import uuid4, UUID


class ChatSession(SQLModel, table=True):
    __tablename__ = "chat_sessions"

    __table_args__ = (
        CheckConstraint(
            "user_id IS NOT NULL OR guest_session_id IS NOT NULL",
            name="chk_chat_session_owner",
        ),
    )

    session_id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID | None = Field(default=None, foreign_key="users.user_id", index=True)
    guest_session_id: UUID | None = Field(
        default=None, foreign_key="guest_sessions.session_id", index=True
    )
    analysis_id: UUID | None = Field(default=None, foreign_key="analyses.analysis_id", index=True)

    system_prompt_version: str | None = Field(default="v2", max_length=20)
    wound_context: dict | None = Field(default=None, sa_column=Column(JSONB, nullable=True))
    user_mood: str | None = Field(default=None, max_length=20)

    status: str = Field(default="active", max_length=20, index=True)
    closure_reason: str | None = Field(default=None, max_length=100)

    message_limit: int = Field(default=50)
    guest_message_limit: int = Field(default=10)
    message_count: int = Field(default=0, ge=0)

    last_message_at: datetime | None = Field(default=None)
    expires_at: datetime | None = Field(default=None)

    total_tokens_used: int = Field(default=0)
    total_cost_usd: float = Field(default=0.0)
    llm_model: str | None = Field(default=None, max_length=50)
    language: str = Field(default="vi", max_length=10)

    user_rating: int | None = Field(default=None)
    user_feedback: str | None = Field(default=None)

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
