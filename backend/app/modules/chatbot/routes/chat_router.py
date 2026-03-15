from fastapi import APIRouter, Depends
from uuid import UUID
from app.modules.chatbot.services.stub_service import ChatbotStubService
from app.modules.chatbot.schemas.chat_schemas import (
    ChatMessageRequest,
    ChatMessageResponse,
    ChatHistoryResponse,
)
from app.shared.response import SuccessResponse

router = APIRouter(tags=["Chatbot"])


@router.post(
    "/message",
    response_model=SuccessResponse[ChatMessageResponse],
    summary="Send a chatbot message (PBI-26)",
    description="Send a message to the chatbot and receive a reply. **Stub:** Returns mock response until real chatbot is implemented.",
)
async def send_chatbot_message(
    request: ChatMessageRequest,
    stub_service: ChatbotStubService = Depends(),
) -> SuccessResponse:
    """
    Send a message to the chatbot and receive a reply.
    
    **Stub:** Returns mock response until real chatbot is implemented.
    """
    result = await stub_service.send_message(request.message)
    
    return SuccessResponse(
        message="Tin nhắn đã được gửi",
        data=result,
    )


@router.get(
    "/history/{session_id}",
    response_model=SuccessResponse[ChatHistoryResponse],
    summary="Get chat history (PBI-26)",
    description="Get chat history for a session. **Stub:** Returns empty list until real chatbot is implemented.",
)
async def get_chat_history(
    session_id: UUID,
    stub_service: ChatbotStubService = Depends(),
) -> SuccessResponse:
    """
    Get chat history for a session.
    
    **Stub:** Returns empty list until real chatbot is implemented.
    """
    result = await stub_service.get_history(session_id)
    
    return SuccessResponse(
        message="Lấy lịch sử chat thành công",
        data=result,
    )
