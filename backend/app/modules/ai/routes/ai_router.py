from fastapi import APIRouter, UploadFile, File, Depends, Query
from typing import Union, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai.controllers.ai_controller import AIController
from app.modules.ai.schemas.wound_analysis_schemas import WoundAnalysisResponse
from app.shared.schemas.response import SuccessResponse, ErrorResponse
from app.modules.auth.models.user import User

from app.api.v1.deps import allow_guest, require_auth
from app.core.database import get_session as get_db

router = APIRouter(prefix="/ai", tags=["AI Processing"])


@router.get("/health")
async def check_ai_health(db: AsyncSession = Depends(get_db)):
    """
    Kiểm tra trạng thái AI models và services.
    """
    controller = AIController(db)
    return await controller.check_health()


@router.post(
    "/analyze",
    response_model=Union[SuccessResponse[WoundAnalysisResponse], ErrorResponse],
    summary="Phân tích hình ảnh vết thương"
)
async def analyze_image(
    file: UploadFile = File(..., description="Hình ảnh vết thương (JPEG/PNG, max 5MB)"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(allow_guest)
):
    """
    Phân tích hình ảnh vết thương bằng AI.
    """
    controller = AIController(db)
    user_id = str(current_user.user_id) if current_user else None
    return await controller.analyze_image(file, user_id)


@router.get(
    "/history",
    response_model=Union[SuccessResponse[Dict[str, Any]], ErrorResponse],
    summary="Lấy lịch sử phân tích"
)
async def get_analysis_history(
    limit: int = Query(20, description="Số lượng records tối đa", le=100, ge=1),
    offset: int = Query(0, description="Số records bỏ qua", ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_auth)  
):
    """
    Lấy lịch sử phân tích của user với thống kê chi tiết.
    """
    controller = AIController(db)
    
    return await controller.get_analysis_history(
        user_id=str(current_user.user_id),
        limit=limit,
        offset=offset
    )


@router.get(
    "/analysis/{analysis_id}",
    response_model=Union[SuccessResponse[WoundAnalysisResponse], ErrorResponse],
    summary="Lấy chi tiết 1 analysis"
)
async def get_analysis_detail(
    analysis_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_auth)
):
    """
    Lấy chi tiết của 1 analysis cụ thể.
    """
    controller = AIController(db)
    return await controller.get_analysis_detail(
        analysis_id=analysis_id,
        user_id=str(current_user.user_id)
    )


@router.delete(
    "/analysis/{analysis_id}",
    response_model=Union[SuccessResponse[Dict[str, str]], ErrorResponse],
    summary="Xóa 1 analysis"
)
async def delete_analysis(
    analysis_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_auth)
):
    """
    Xóa (soft delete) 1 analysis.
    """
    controller = AIController(db)
    return await controller.delete_analysis(
        analysis_id=analysis_id,
        user_id=str(current_user.user_id)
    )