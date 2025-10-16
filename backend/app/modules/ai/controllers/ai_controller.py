from sqlalchemy.ext.asyncio import AsyncSession
from typing import Union
import logging
import tempfile
import os

from app.shared.schemas.response import SuccessResponse, ErrorResponse
from app.modules.ai.schemas.ai_schemas import AIAnalysisResult, AIDetectionResult, BoundingBox
from app.modules.ai.models.ai_analysis import AIModelInfo
from app.modules.ai.services.ai_processing_service import AIProcessingService
from app.utils.exceptions.base_exceptions import AppBaseException
from app.utils.constants.error_codes import USER_INVALID_DATA

logger = logging.getLogger(__name__)

class AIController:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_service = AIProcessingService()

    def _transform_bbox_format(self, detections):
        """
        Transform bbox từ List[float] sang BoundingBox object

        Args:
            detections: List các detection từ AI service

        Returns:
            List các detection với bbox đã được transform
        """
        transformed_detections = []

        for detection in detections:
            bbox_data = detection.get("bbox", [])
            if isinstance(bbox_data, list) and len(bbox_data) >= 4:
                x, y, width, height = bbox_data[:4]
                bbox_obj = BoundingBox(
                    x=float(x),
                    y=float(y),
                    width=float(width),
                    height=float(height)
                )
            else:
                bbox_obj = BoundingBox(x=0, y=0, width=0, height=0)

            transformed_detection = {
                "class_name": detection.get("class_name", ""),
                "confidence": detection.get("confidence", 0.0),
                "bbox": bbox_obj,
                "severity": detection.get("severity", "unknown"),
                "severity_confidence": detection.get("severity_confidence", 0.0)
            }
            transformed_detections.append(transformed_detection)

        return transformed_detections

    async def analyze_image(self, file) -> Union[SuccessResponse[AIAnalysisResult], ErrorResponse]:
        """
        Phân tích hình ảnh vết thương bằng AI

        Args:
            file: UploadFile chứa hình ảnh

        Returns:
            SuccessResponse với kết quả phân tích hoặc ErrorResponse
        """
        temp_file_path = None
        try:
            # Validate file type
            allowed_types = ["image/jpeg", "image/png", "image/jpg"]
            if file.content_type not in allowed_types:
                return ErrorResponse(
                    message=f"Invalid file type: {file.content_type}. Only JPEG/PNG allowed.",
                    error_code="INVALID_FILE_TYPE",
                    error_details={"content_type": file.content_type, "allowed_types": allowed_types}
                )

            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
                temp_file_path = temp_file.name
                content = await file.read()
                temp_file.write(content)
                temp_file.flush()
                os.fsync(temp_file.fileno())

            # Call AI service
            result = await self.ai_service.analyze_image(temp_file_path)

            if not result.get("success", False):
                error_msg = result.get("error", "Unknown AI processing error")
                error_code = result.get("error_code", "AI_PROCESSING_ERROR")
                return ErrorResponse(
                    message=f"AI service analysis failed: {error_msg}",
                    error_code=error_code,
                    error_details={"ai_error": error_msg}
                )

            # Transform bbox format từ List[float] sang BoundingBox object
            if "detections" in result:
                result["detections"] = self._transform_bbox_format(result["detections"])

            analysis_result = AIAnalysisResult(**result)

            return SuccessResponse(
                message="Phân tích hình ảnh thành công",
                data=analysis_result
            )

        except AppBaseException as e:
            return ErrorResponse(
                message=e.message,
                error_code=e.error_code,
                error_details={"validation_error": str(e)}
            )

        except Exception as e:
            logger.error(f"Unexpected error during AI analysis: {e}", exc_info=True)
            return ErrorResponse(
                message="Có lỗi xảy ra trong quá trình phân tích AI",
                error_code="INTERNAL_ERROR",
                error_details={"error": str(e)}
            )

        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except Exception as e:
                    logger.warning(f"Failed to delete temporary file {temp_file_path}: {e}")

    async def check_health(self) -> Union[SuccessResponse[dict], ErrorResponse]:
        """
        Kiểm tra trạng thái dịch vụ AI

        Returns:
            SuccessResponse với trạng thái hoặc ErrorResponse
        """
        try:
            is_healthy = await self.ai_service.check_ai_service_health()

            health_data = {
                "status": "healthy" if is_healthy else "unhealthy",
                "service": "AI",
                "timestamp": None  
            }

            return SuccessResponse(
                message="AI service health check completed",
                data=health_data
            )

        except Exception as e:
            logger.error(f"Error checking AI service health: {e}")
            return ErrorResponse(
                message="Không thể kiểm tra trạng thái AI service",
                error_code="HEALTH_CHECK_ERROR",
                error_details={"error": str(e)}
            )

    async def get_model_info(self) -> Union[SuccessResponse[AIModelInfo], ErrorResponse]:
        """
        Lấy thông tin mô hình AI

        Returns:
            SuccessResponse với thông tin mô hình hoặc ErrorResponse
        """
        try:
            model_info = await self.ai_service.get_model_info()

            return SuccessResponse(
                message="Lấy thông tin mô hình thành công",
                data=model_info
            )

        except Exception as e:
            logger.error(f"Error getting AI model info: {e}")
            return ErrorResponse(
                message="Không thể lấy thông tin mô hình AI",
                error_code="MODEL_INFO_ERROR",
                error_details={"error": str(e)}
            )