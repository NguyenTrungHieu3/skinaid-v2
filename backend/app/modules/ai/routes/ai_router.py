from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status
from typing import Union
from app.modules.ai.controllers.ai_controller import AIController
from app.modules.ai.schemas.ai_schemas import AIAnalysisResult
from app.shared.schemas.response import SuccessResponse, ErrorResponse
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ai", tags=["AI Processing"])

@router.get("/health")
async def check_ai_health(db: AsyncSession = Depends(get_db)):
    """Kiểm tra trạng thái dịch vụ AI"""
    controller = AIController(db)
    return await controller.check_health()

@router.post("/analyze", response_model=Union[SuccessResponse[AIAnalysisResult], ErrorResponse])
async def analyze_image(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    """Phân tích hình ảnh vết thương bằng AI"""
    controller = AIController(db)
    return await controller.analyze_image(file)

@router.get("/model-info", response_model=Union[SuccessResponse[dict], ErrorResponse])
async def get_model_info(db: AsyncSession = Depends(get_db)):
    """Lấy thông tin mô hình AI"""
    controller = AIController(db)
    return await controller.get_model_info()