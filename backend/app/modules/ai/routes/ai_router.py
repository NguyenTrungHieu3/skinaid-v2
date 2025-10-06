from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status
from app.modules.ai.services.ai_processing_service import AIProcessingService
from app.modules.ai.schemas.ai_schemas import AIAnalysisResult
import tempfile
import os
import uuid
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ai", tags=["AI Processing"])

@router.get("/health")
async def check_ai_health(): 
    is_healthy = await AIProcessingService.check_ai_service_health()
    return {
        "status": "healthy" if is_healthy else "unhealthy", 
        "services": "AI"
    }

@router.post("/analyze", response_model=AIAnalysisResult)
async def analyze_image(file: UploadFile = File(...)):
    temp_file_path = None
    try:
        allowed_types = ["image/jpeg", "image/png", "image/jpg"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type: {file.content_type}. Only JPEG/PNG allowed."
            )
        
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
            temp_file_path = temp_file.name
            content = await file.read()
            temp_file.write(content)
            temp_file.flush()
            os.fsync(temp_file.fileno())
        
        result = await AIProcessingService.analyze_image(temp_file_path)
        
        if not result.get("success", False):
            error_msg = result.get("error", "Unknown AI processing error")
            error_code = result.get("error_code", "AI_PROCESSING_ERROR")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"AI service analysis failed: {error_msg} (Error code: {error_code})"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during AI analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during AI analysis: {str(e)}"
        )
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception as e:
                logger.warning(f"Failed to delete temporary file {temp_file_path}: {e}")