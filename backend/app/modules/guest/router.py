from uuid import uuid4, UUID
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request, status

from app.core.dependencies import get_db, require_admin, require_user
from app.modules.users.models.user import User
from app.modules.guest.dependencies import get_guest_service
from app.modules.guest.schemas.api import (
    CreateGuestSessionRequest,
    GuestSessionResponse,
    GuestStatsResponse,
)
from app.modules.guest.service import GuestService
from app.shared.response import SuccessResponse


router = APIRouter(prefix="/guest", tags=["Guest Management"])


@router.post(
    "/session",
    response_model=SuccessResponse[GuestSessionResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Tạo phiên khách",
)
async def create_guest_session(
    request: Request,
    ip_address: Optional[str] = Query(
        None, description="IP address của guest"),
    user_agent: Optional[str] = Query(None, description="User agent"),
    service: GuestService = Depends(get_guest_service),
) -> SuccessResponse:
    if not ip_address and request.client:
        ip_address = request.client.host
    if not user_agent:
        user_agent = request.headers.get("User-Agent")

    req_dto = CreateGuestSessionRequest(
        ip_address=ip_address, user_agent=user_agent)
    session = await service.create_session(req_dto)

    return SuccessResponse(
        message="Tạo phiên khách thành công",
        data=GuestSessionResponse.model_validate(session)
    )


@router.get(
    "/session/{session_id}",
    response_model=SuccessResponse[GuestSessionResponse],
    summary="Lấy chi tiết phiên khách",
)
async def get_guest_session(
    session_id: UUID,
    service: GuestService = Depends(get_guest_service),
) -> SuccessResponse:
    session = await service.get_session(session_id)
    return SuccessResponse(
        message="Lấy thông tin phiên thành công",
        data=GuestSessionResponse.model_validate(session)
    )


@router.get(
    "/statistics",
    response_model=SuccessResponse[GuestStatsResponse],
    summary="Thống kê Guest (Admin)",
)
async def get_guest_statistics(
    service: GuestService = Depends(get_guest_service),
    current_user: User = Depends(require_admin),
) -> SuccessResponse:
    stats = await service.get_stats()
    return SuccessResponse(
        message="Lấy thống kê thành công",
        data=stats
    )


@router.post(
    "/claim/{analysis_id}",
    response_model=SuccessResponse,
    summary="Nhận analysis từ Guest Session",
)
async def claim_analysis(
    analysis_id: UUID,
    service: GuestService = Depends(get_guest_service),
    current_user: User = Depends(require_user),
) -> SuccessResponse:
    await service.claim_analysis(analysis_id, current_user.user_id)
    return SuccessResponse(message="Nhận phân tích thành công")
