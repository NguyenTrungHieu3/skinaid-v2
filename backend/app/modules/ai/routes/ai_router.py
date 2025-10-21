from fastapi import APIRouter, UploadFile, File, Depends, Query
from typing import Union, Dict, Any
from app.modules.ai.controllers.ai_controller import AIController
from app.modules.ai.schemas.wound_analysis_schemas import WoundAnalysisResponse
from app.shared.schemas.response import SuccessResponse, ErrorResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.deps import get_current_active_user, get_db

router = APIRouter(prefix="/ai", tags=["AI Processing"])

@router.get("/health")
async def check_ai_health(db: AsyncSession = Depends(get_db)):
    """Kiểm tra trạng thái AI models"""
    controller = AIController(db)
    return await controller.check_health()

@router.post("/analyze", response_model=Union[SuccessResponse[WoundAnalysisResponse], ErrorResponse])
async def analyze_image(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Phân tích hình ảnh vết thương bằng AI
    """
    controller = AIController(db)
    return await controller.analyze_image(file, str(current_user.user_id))

@router.get("/history", response_model=Union[SuccessResponse[Dict[str, Any]], ErrorResponse])
async def get_analysis_history(
    limit: int = Query(20, description="Số lượng records tối đa", le=100),
    offset: int = Query(0, description="Số records bỏ qua", ge=0),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Lấy lịch sử phân tích của user với thống kê chi tiết
    """
    controller = AIController(db)
    return await controller.get_analysis_history(str(current_user.user_id))