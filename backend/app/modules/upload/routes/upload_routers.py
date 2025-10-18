from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Union, Dict, Any
import logging

from app.shared.schemas.response import SuccessResponse, ErrorResponse
from app.modules.upload.controllers.upload_controllers import UploadController
from app.api.v1.deps import get_db, get_current_active_user
from app.modules.auth.models.user import User

router = APIRouter(prefix="/upload", tags=["Upload Logs"])

logger = logging.getLogger(__name__)

async def get_upload_controller(db: AsyncSession = Depends(get_db)) -> UploadController:
    return UploadController(db)

@router.get(
    "/logs",
    response_model=Union[SuccessResponse[Dict[str, Any]], ErrorResponse],
    summary="Lấy lịch sử upload logs",
    description="Lấy danh sách upload logs của user hiện tại"
)
async def get_upload_logs(
    limit: int = Query(20, description="Số lượng logs tối đa", le=100),
    offset: int = Query(0, description="Số logs bỏ qua", ge=0),
    controller: UploadController = Depends(get_upload_controller),
    current_user: User = Depends(get_current_active_user)
):
    """Lấy lịch sử upload ảnh của user hiện tại."""
    return await controller.get_upload_logs(
        user_id=str(current_user.user_id),
        limit=limit,
        offset=offset
    )

@router.get(
    "/statistics",
    response_model=Union[SuccessResponse[Dict[str, Any]], ErrorResponse],
    summary="Lấy thống kê upload",
    description="Lấy thống kê upload của user hiện tại"
)
async def get_upload_statistics(
    controller: UploadController = Depends(get_upload_controller),
    current_user: User = Depends(get_current_active_user)
):
    """Lấy thống kê tổng quan về hoạt động upload."""
    return SuccessResponse(
        message="Lấy thống kê upload thành công",
        data=await controller.get_upload_statistics(str(current_user.user_id))
    )