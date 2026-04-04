from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from typing import Optional
from datetime import datetime, timezone
from uuid import uuid4, UUID


class ChatMessage(SQLModel, table=True):
    __tablename__ = "chat_messages"

    message_id: UUID = Field(default_factory=uuid4, primary_key=True)
    session_id: UUID = Field(foreign_key="chat_sessions.session_id", index=True)

    # user | assistant | system
    role: str = Field(max_length=20)
    content: str

    tokens_used: int = Field(default=0, ge=0)
    token_cost_usd: Optional[float] = Field(default=0.0)

    model_used: Optional[str] = Field(default=None, max_length=50)
    temperature: Optional[float] = Field(default=0.7)

    # RAG citations: [{guide_id, url, excerpt}]
    sources: Optional[dict] = Field(default=None, sa_column=Column(JSONB, nullable=True))

    is_helpful: Optional[bool] = Field(default=None)
    flagged: bool = Field(default=False)
    flag_reason: Optional[str] = Field(default=None, max_length=255)

    processing_time_ms: Optional[int] = Field(default=None)

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
