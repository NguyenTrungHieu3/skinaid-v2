from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from uuid import UUID


class ChatMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="User's message to chatbot")
    session_id: Optional[str] = Field(None, description="Optional session ID for conversation continuity")


class ChatMessageResponse(BaseModel):
    reply: str = Field(..., description="Chatbot's reply message")
    session_id: str = Field(..., description="Session ID for this conversation")
    validated: bool = Field(False, description="Whether the response has been validated")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")


class ChatMessage(BaseModel):
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    message: str = Field(..., description="Message content")
    timestamp: datetime = Field(..., description="Message timestamp")


class ChatHistoryResponse(BaseModel):
    session_id: UUID = Field(..., description="Session ID")
    messages: List[ChatMessage] = Field(default_factory=list, description="List of chat messages")
    total: int = Field(0, description="Total number of messages")
