from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from app.core.dependencies.access_control import require_auth
from app.modules.chatbot.dependencies import ChatSvcDep
from app.modules.chatbot.schemas.chat_schemas import (
    ChatMessageResponse,
    CreateSessionRequest,
    CreateSessionResponse,
    SendMessageRequest,
    SessionDetailResponse,
    SessionListItem,
)
from app.modules.users.models import User
from app.shared.response import SuccessResponse

router = APIRouter()


@router.post(
    "/sessions",
    response_model=SuccessResponse[CreateSessionResponse],
)
async def create_session(
    request: CreateSessionRequest,
    chat_svc: ChatSvcDep,
    current_user: User = Depends(require_auth),
) -> SuccessResponse:
    result = await chat_svc.create_session(
        user_id=current_user.user_id,
        analysis_id=request.analysis_id,
    )
    return SuccessResponse(
        message="Tạo phiên chat thành công",
        data=result,
    )


@router.post(
    "/sessions/{session_id}/messages",
    response_model=SuccessResponse[ChatMessageResponse],
)
async def send_message(
    session_id: UUID,
    request: SendMessageRequest,
    chat_svc: ChatSvcDep,
    current_user: User = Depends(require_auth),
) -> SuccessResponse:
    result = await chat_svc.send_message(
        user_id=current_user.user_id,
        session_id=session_id,
        message=request.message,
    )
    return SuccessResponse(
        message="Tin nhắn đã được gửi",
        data=result,
    )


@router.get(
    "/sessions",
    response_model=SuccessResponse[list[SessionListItem]],
)
async def list_sessions(
    chat_svc: ChatSvcDep,
    analysis_id: UUID | None = None,
    current_user: User = Depends(require_auth),
) -> SuccessResponse:
    result = await chat_svc.list_sessions(
        user_id=current_user.user_id,
        analysis_id=analysis_id,
    )
    return SuccessResponse(
        message="Lấy danh sách phiên chat thành công",
        data=result,
    )


@router.get(
    "/sessions/{session_id}",
    response_model=SuccessResponse[SessionDetailResponse],
)
async def get_session(
    session_id: UUID,
    chat_svc: ChatSvcDep,
    current_user: User = Depends(require_auth),
) -> SuccessResponse:
    result = await chat_svc.get_session_detail(
        user_id=current_user.user_id,
        session_id=session_id,
    )
    return SuccessResponse(
        message="Lấy chi tiết phiên chat thành công",
        data=result,
    )


@router.delete(
    "/sessions/{session_id}",
    response_model=SuccessResponse[str],
)
async def delete_session(
    session_id: UUID,
    chat_svc: ChatSvcDep,
    current_user: User = Depends(require_auth),
) -> SuccessResponse:
    result = await chat_svc.delete_session(
        user_id=current_user.user_id,
        session_id=session_id,
    )
    return SuccessResponse(
        message="Xóa phiên chat thành công",
        data=result,
    )
