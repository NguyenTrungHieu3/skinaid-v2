from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import uuid

from app.modules.guest.controllers.guest_controller import GuestController
from app.modules.guest.schemas.guest_schemas import (
    GuestSessionResponse,
    GuestStatisticsResponse
)
from app.api.v1.deps import get_db
from app.shared.schemas.response import SuccessResponse

router = APIRouter(prefix="/guest", tags=["Guest Management"])

@router.post("/session", response_model=SuccessResponse[GuestSessionResponse])
async def create_guest_session(
    ip_address: Optional[str] = Query(None, description="IP address của guest"),
    user_agent: Optional[str] = Query(None, description="User agent"),
    db: AsyncSession = Depends(get_db)
):
    """
    Tạo guest session mới cho anonymous users.
    Session sẽ expire sau 1 giờ.
    """
    controller = GuestController(db)
    return await controller.create_guest_session(ip_address, user_agent)

@router.get("/session/{session_id}", response_model=SuccessResponse[GuestSessionResponse])
async def get_guest_session(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Lấy thông tin guest session theo ID.
    Bao gồm upload/analysis counts và limits.
    """
    controller = GuestController(db)
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Định dạng session ID không hợp lệ")
    
    return await controller.get_guest_session(session_uuid)

@router.get("/statistics", response_model=SuccessResponse[GuestStatisticsResponse])
async def get_guest_statistics(
    db: AsyncSession = Depends(get_db)
):
    """
    Lấy thống kê về guest activities.
    Admin only endpoint.
    """
    controller = GuestController(db)
    return await controller.get_guest_statistics()