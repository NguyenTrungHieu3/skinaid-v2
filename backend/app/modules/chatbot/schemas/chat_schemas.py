from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CreateSessionRequest(BaseModel):
    analysis_id: UUID | None = None


class SendMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)


class CreateSessionResponse(BaseModel):
    session_id: UUID
    analysis_id: UUID | None = None
    session_type: str
    max_messages: int = 10
    created_at: datetime


class ChatMessageResponse(BaseModel):
    reply: str
    session_id: UUID
    tokens_used: int = 0
    message_count: int
    remaining_messages: int
    created_at: datetime


class MessageItem(BaseModel):
    role: str
    content: str
    created_at: datetime


class SessionListItem(BaseModel):
    session_id: UUID
    analysis_id: UUID | None = None
    session_type: str
    message_count: int
    last_message_at: datetime
    status: str
    created_at: datetime


class SessionDetailResponse(BaseModel):
    session_id: UUID
    analysis_id: UUID | None = None
    session_type: str
    messages: list[MessageItem]
    message_count: int
    remaining_messages: int
    status: str
    created_at: datetime
