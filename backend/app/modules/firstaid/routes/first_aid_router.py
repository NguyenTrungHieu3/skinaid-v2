from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict, Any

from app.modules.firstaid.controllers.first_aid_controller import FirstAidController
from app.modules.firstaid.schemas.first_aid_schemas import (
    FirstAidGuideResponse,
    WoundTypeResponse
)
from app.api.v1.deps import get_db, require_auth, allow_guest
from app.shared.schemas.response import SuccessResponse, ErrorResponse

router = APIRouter(prefix="/first-aid")

@router.get("/guide/{wound_type}/{severity}", response_model=SuccessResponse[FirstAidGuideResponse])
async def get_first_aid_guide(
    wound_type: str,
    severity: str,
    sub_type: Optional[str] = Query(None, description="Loại phụ (chỉ dành cho burn: blister, skintear)"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_auth)
):
    """
    Lấy hướng dẫn sơ cứu cho loại và mức độ vết thương cụ thể.
    """
    controller = FirstAidController(db)
    return await controller.get_first_aid_guide(wound_type, severity, sub_type)

@router.get("/wound-types", response_model=SuccessResponse[List[WoundTypeResponse]])
async def get_available_wound_types(
    db: AsyncSession = Depends(get_db)
):
    """
    Lấy danh sách các loại vết thương có hướng dẫn sơ cứu.
    """
    controller = FirstAidController(db)
    return await controller.get_available_wound_types()

@router.get("/search", response_model=SuccessResponse[List[FirstAidGuideResponse]])
async def search_first_aid_guides(
    wound_type: Optional[str] = Query(None, description="Lọc theo loại vết thương"),
    severity: Optional[str] = Query(None, description="Lọc theo mức độ"),
    limit: int = Query(20, description="Số lượng tối đa", le=100, ge=1),
    offset: int = Query(0, description="Số bản ghi bỏ qua", ge=0),
    db: AsyncSession = Depends(get_db)
):
    """
    Tìm kiếm hướng dẫn sơ cứu với bộ lọc.
    """
    controller = FirstAidController(db)
    return await controller.search_first_aid_guides(wound_type, severity, limit, offset)

@router.get("/statistics", response_model=SuccessResponse[Dict[str, Any]])
async def get_first_aid_statistics(
    db: AsyncSession = Depends(get_db)
):
    """
    Lấy thống kê về first aid knowledge base.
    """
    controller = FirstAidController(db)
    return await controller.get_statistics()

@router.get("/validate/{wound_type}/{severity}", response_model=SuccessResponse[Dict[str, Any]])
async def validate_guide_availability(
    wound_type: str,
    severity: str,
    sub_type: Optional[str] = Query(None, description="Loại phụ (chỉ dành cho burn: blister, skintear)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Kiểm tra tính khả dụng của hướng dẫn sơ cứu.
    """
    controller = FirstAidController(db)
    return await controller.validate_guide_availability(wound_type, severity, sub_type)