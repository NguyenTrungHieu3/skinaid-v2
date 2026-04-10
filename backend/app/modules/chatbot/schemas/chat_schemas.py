from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ── Request ──────────────────────────────────────────────────────────────────

class CreateSessionRequest(BaseModel):
    analysis_id: Optional[UUID] = Field(
        None,
        description="UUID của kết quả phân tích. Nếu có → Wound Advisor mode. Nếu không → App Guide mode.",
    )


class SendMessageRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Tin nhắn của người dùng",
    )


# ── Response ─────────────────────────────────────────────────────────────────

class CreateSessionResponse(BaseModel):
    session_id: UUID
    analysis_id: Optional[UUID] = None
    session_type: str = Field(description="'wound_advisor' | 'app_guide'")
    max_messages: int = 10
    created_at: datetime


class ChatMessageResponse(BaseModel):
    reply: str
    session_id: UUID
    tokens_used: int = 0
    message_count: int = Field(description="Số tin nhắn user đã gửi (sau lần này)")
    remaining_messages: int = Field(description="Số tin nhắn còn lại")
    created_at: datetime


class MessageItem(BaseModel):
    role: str = Field(description="'user' | 'assistant'")
    content: str
    created_at: datetime


class SessionDetailResponse(BaseModel):
    session_id: UUID
    analysis_id: Optional[UUID] = None
    session_type: str
    messages: List[MessageItem] = []
    message_count: int = 0
    remaining_messages: int = 10
    status: str = "active"
    created_at: datetime


class SessionSummaryResponse(BaseModel):
    session_id: UUID
    analysis_id: Optional[UUID] = None
    session_type: str
    message_count: int = 0
    last_message_at: Optional[datetime] = None
    status: str = "active"
    created_at: datetime
