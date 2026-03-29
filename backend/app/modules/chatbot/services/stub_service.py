from uuid import uuid4, UUID
from typing import List
import logging

from app.modules.chatbot.schemas.chat_schemas import (
    ChatMessageResponse,
    ChatHistoryResponse,
    ChatMessage,
)

logger = logging.getLogger(__name__)


class ChatbotStubService:
    """
    Stub service for chatbot functionality (PBI-26).
    
    Returns mock responses until real chatbot is implemented.
    """
    
    def __init__(self):
        self.default_reply = "Tính năng chatbot sắp ra mắt! Hiện tại mình đang trong giai đoạn phát triển."
    
    async def send_message(self, message: str) -> ChatMessageResponse:
        """
        Return stub chatbot response.
        
        Args:
            message: User's message
            
        Returns:
            ChatMessageResponse with mock reply
        """
        logger.info(f"[CHATBOT STUB] User: {message}")
        
        return ChatMessageResponse(
            reply=self.default_reply,
            session_id=str(uuid4()),
            validated=False,
        )
    
    async def get_history(self, session_id: UUID) -> ChatHistoryResponse:
        """
        Return empty chat history.
        
        Args:
            session_id: Session UUID
            
        Returns:
            ChatHistoryResponse with empty messages list
        """
        logger.info(f"[CHATBOT STUB] Get history for session: {session_id}")
        
        return ChatHistoryResponse(
            session_id=session_id,
            messages=[],
            total=0,
        )
