from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict, Any
import uuid

from app.modules.guest.controllers.guest_controller import GuestController
from app.modules.guest.schemas.guest_schemas import (
    GuestSessionResponse,
    GuestUploadResponse,
    GuestAnalysisResponse,
    GuestStatisticsResponse
)
from app.api.v1.deps import get_db, allow_guest
from app.shared.schemas.response import SuccessResponse, ErrorResponse

router = APIRouter(prefix="/guest", tags=["Guest Management"])

def str_to_uuid(uuid_str: str) -> uuid.UUID:
    """Convert string to UUID with validation."""
    try:
        return uuid.UUID(uuid_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

@router.post("/session", response_model=SuccessResponse[GuestSessionResponse])
async def create_guest_session(
    ip_address: Optional[str] = Query(None, description="IP address của guest"),
    user_agent: Optional[str] = Query(None, description="User agent"),
    db: AsyncSession = Depends(get_db)
):
    """
    Tạo guest session mới cho anonymous users.
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
    """
    controller = GuestController(db)
    return await controller.get_guest_session(str_to_uuid(session_id))

@router.post("/upload", response_model=SuccessResponse[GuestUploadResponse])
async def create_guest_upload(
    session_id: str,
    file_path: str,
    file_name: str,
    file_size: int,
    mime_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Tạo guest upload record.
    """
    controller = GuestController(db)
    return await controller.create_guest_upload(
        str_to_uuid(session_id), file_path, file_name, file_size, mime_type
    )

@router.post("/analysis", response_model=SuccessResponse[GuestAnalysisResponse])
async def create_guest_analysis(
    session_id: str,
    upload_id: Optional[str] = None,
    wound_type: Optional[str] = None,
    severity: Optional[str] = None,
    confidence: Optional[float] = None,
    result_json: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Tạo guest analysis record.
    """
    controller = GuestController(db)
    return await controller.create_guest_analysis(
        str_to_uuid(session_id),
        str_to_uuid(upload_id) if upload_id else None,
        wound_type,
        severity,
        confidence,
        result_json
    )

@router.get("/uploads/{session_id}", response_model=SuccessResponse[List[GuestUploadResponse]])
async def get_guest_uploads(
    session_id: str,
    limit: int = Query(20, description="Số lượng tối đa", le=100, ge=1),
    offset: int = Query(0, description="Số bản ghi bỏ qua", ge=0),
    db: AsyncSession = Depends(get_db)
):
    """
    Lấy danh sách uploads của guest session.
    """
    controller = GuestController(db)
    return await controller.get_guest_uploads(str_to_uuid(session_id), limit, offset)

@router.get("/analyses/{session_id}", response_model=SuccessResponse[List[GuestAnalysisResponse]])
async def get_guest_analyses(
    session_id: str,
    limit: int = Query(20, description="Số lượng tối đa", le=100, ge=1),
    offset: int = Query(0, description="Số bản ghi bỏ qua", ge=0),
    db: AsyncSession = Depends(get_db)
):
    """
    Lấy danh sách analyses của guest session.
    """
    controller = GuestController(db)
    return await controller.get_guest_analyses(str_to_uuid(session_id), limit, offset)

@router.get("/statistics", response_model=SuccessResponse[GuestStatisticsResponse])
async def get_guest_statistics(
    db: AsyncSession = Depends(get_db)
):
    """
    Lấy thống kê về guest activities.
    """
    controller = GuestController(db)
    return await controller.get_guest_statistics()