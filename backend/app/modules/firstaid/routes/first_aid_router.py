from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict, Any
import uuid

from app.modules.firstaid.controllers.first_aid_controller import FirstAidController
from app.modules.firstaid.schemas.first_aid_schemas import (
    FirstAidGuideResponse,
    WoundTypeResponse,
    CreateFirstAidGuideRequest,
    UpdateFirstAidGuideRequest
)
from app.core.dependencies import get_db, require_auth, allow_guest, require_admin
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

@router.post("/guides", response_model=SuccessResponse[FirstAidGuideResponse])
async def create_first_aid_guide(
    guide_request: CreateFirstAidGuideRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_admin)
):
    """
    Tạo hướng dẫn sơ cứu mới (Chỉ Admin).
    """
    controller = FirstAidController(db)
    guide_data = guide_request.dict()
    return await controller.create_first_aid_guide(guide_data, current_user.user_id)

@router.get("/guides/{guide_id}", response_model=SuccessResponse[FirstAidGuideResponse])
async def get_guide_by_id(
    guide_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Lấy hướng dẫn sơ cứu theo ID.
    """
    controller = FirstAidController(db)
    return await controller.get_guide_by_id(guide_id)

@router.put("/guides/{guide_id}", response_model=SuccessResponse[FirstAidGuideResponse])
async def update_first_aid_guide(
    guide_id: uuid.UUID,
    guide_request: UpdateFirstAidGuideRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_admin)
):
    """
    Cập nhật hướng dẫn sơ cứu (Chỉ Admin).
    """
    controller = FirstAidController(db)
    update_data = guide_request.dict(exclude_unset=True)
    return await controller.update_first_aid_guide(guide_id, update_data)

@router.delete("/guides/{guide_id}", response_model=SuccessResponse[Dict[str, Any]])
async def delete_first_aid_guide(
    guide_id: uuid.UUID,
    hard_delete: bool = Query(False, description="True = xóa vĩnh viễn, False = soft delete"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_admin)
):
    """
    Xóa hướng dẫn sơ cứu (Chỉ Admin).
    - hard_delete=False: Soft delete (set is_active=false)
    - hard_delete=True: Hard delete (xóa vĩnh viễn khỏi database)
    """
    controller = FirstAidController(db)
    return await controller.delete_first_aid_guide(guide_id, hard_delete)