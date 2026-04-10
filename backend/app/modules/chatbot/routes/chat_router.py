from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.core.dependencies.access_control import require_auth
from app.modules.chatbot.dependencies import ChatSvcDep
from app.modules.chatbot.schemas.chat_schemas import (
    ChatMessageResponse,
    CreateSessionRequest,
    CreateSessionResponse,
    SendMessageRequest,
    SessionDetailResponse,
    SessionSummaryResponse,
)
from app.modules.users.models import User
from app.shared.response import SuccessResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/sessions",
    response_model=SuccessResponse[CreateSessionResponse],
    summary="Tạo phiên chat mới",
    description=(
        "Tạo session mới. Nếu truyền `analysis_id` → **Wound Advisor** (lưu DB). "
        "Nếu không → **App Guide** (lưu Redis 24h)."
    ),
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
    summary="Gửi tin nhắn và nhận phản hồi AI",
    description="Gửi tin nhắn trong phiên chat. AI sẽ trả lời dựa trên mode (Wound Advisor / App Guide).",
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
    "/sessions/{session_id}",
    response_model=SuccessResponse[SessionDetailResponse],
    summary="Chi tiết phiên chat + lịch sử tin nhắn",
)
async def get_session_detail(
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


@router.get(
    "/sessions",
    response_model=SuccessResponse[list[SessionSummaryResponse]],
    summary="Danh sách phiên chat",
    description="Mặc định chỉ trả Wound Advisor sessions (DB). Thêm `include_general=true` để bao gồm App Guide.",
)
async def list_sessions(
    chat_svc: ChatSvcDep,
    current_user: User = Depends(require_auth),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    include_general: bool = Query(False),
) -> SuccessResponse:
    summaries, total = await chat_svc.list_sessions(
        user_id=current_user.user_id,
        skip=skip,
        limit=limit,
        include_general=include_general,
    )
    return SuccessResponse(
        message="Lấy danh sách phiên chat thành công",
        data=summaries,
        extra={"total": total, "skip": skip, "limit": limit},
    )


@router.delete(
    "/sessions/{session_id}",
    response_model=SuccessResponse,
    summary="Kết thúc phiên chat",
    description="Wound Advisor → soft close (giữ lịch sử). App Guide → xoá khỏi Redis.",
)
async def delete_session(
    session_id: UUID,
    chat_svc: ChatSvcDep,
    current_user: User = Depends(require_auth),
) -> SuccessResponse:
    await chat_svc.delete_session(
        user_id=current_user.user_id,
        session_id=session_id,
    )
    return SuccessResponse(message="Đã kết thúc phiên chat")
