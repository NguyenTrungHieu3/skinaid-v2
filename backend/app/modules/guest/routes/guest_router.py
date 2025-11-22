from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import uuid

from app.modules.guest.controllers.guest_controller import GuestController
from app.modules.guest.schemas.guest_schemas import (
    GuestSessionResponse,
    GuestStatisticsResponse
)
from app.core.dependencies import get_db, require_admin
from app.shared.schemas.response import SuccessResponse
from app.modules.audit.services.audit_service import AuditService

router = APIRouter(prefix="/guest", tags=["Guest Management"])

@router.post("/session", response_model=SuccessResponse[GuestSessionResponse])
async def create_guest_session(
    request: Request,
    ip_address: Optional[str] = Query(None, description="IP address của guest"),
    user_agent: Optional[str] = Query(None, description="User agent"),
    db: AsyncSession = Depends(get_db)
):
    """
    Tạo guest session mới cho anonymous users.
    Session sẽ expire sau 1 giờ.
    """
    # Auto-detect IP and User-Agent if not provided
    if not ip_address and request.client:
        ip_address = request.client.host
    if not user_agent:
        user_agent = request.headers.get("User-Agent")
    
    controller = GuestController(db)
    result = await controller.create_guest_session(ip_address, user_agent)
    
    # Audit logging
    audit_service = AuditService(db)
    if isinstance(result, SuccessResponse):
        await audit_service.log_event(
            action="create_guest_session",
            success=True,
            resource_type="guest_session",
            resource_id=str(result.data.session_id),
            is_guest=True,
            guest_session_id=result.data.session_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    return result

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
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin)  # Admin-only access
):
    """
    Lấy thống kê về guest activities.
    Admin only endpoint.
    """
    controller = GuestController(db)
    return await controller.get_guest_statistics()