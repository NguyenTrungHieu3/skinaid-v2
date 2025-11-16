from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile, HTTPException, status
from typing import Union, Dict, Any, Optional
import logging
from datetime import datetime
import uuid

from app.shared.schemas.response import SuccessResponse, ErrorResponse
from fastapi import status as http_status
from app.modules.ai.schemas.wound_analysis_schemas import WoundAnalysisResponse, SimpleAnalysisResponse
from app.modules.ai.services.wound_ai_service import WoundAIService
from app.modules.ai.services.wound_analysis_service import WoundAnalysisService
from app.modules.ai.services.detection_processor import DetectionProcessor
from app.modules.ai.services.file_upload_service import FileUploadService
from app.modules.ai.services.response_mapper import ResponseMapper
from app.utils.exceptions.base_exceptions import AppBaseException
from app.api.v1.deps import check_user_has_role

# Import constants
from app.utils.constants import error_codes as ErrorCode
from app.utils.constants import messages as Message

logger = logging.getLogger(__name__)


class AIController:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.analysis_service = WoundAnalysisService(db)

    async def analyze_image(
        self,
        file: UploadFile,
        user_id: Optional[uuid.UUID]
    ) -> Union[SuccessResponse[SimpleAnalysisResponse], ErrorResponse]:
        file_path = None

        try:
            # Step 1: File handling
            display_user_id = user_id or "anonymous"
            file_path, relative_path, image_url = FileUploadService.generate_image_path(
                display_user_id, file.filename
            )
            content = await FileUploadService.save_file(file, file_path)
            validation_error = FileUploadService.validate_file(file, content)
            if validation_error:
                FileUploadService.cleanup_file(file_path)
                return validation_error

            # Step 2: AI analysis
            logger.info(f"[ANALYZE] Starting: {file.filename} (user: {user_id or 'guest'})")
            async with WoundAIService() as ai_service:
                ai_result = await ai_service.analyze_wound_image(file_path)

            if not ai_result.get("success", False):
                FileUploadService.cleanup_file(file_path)
                error_detail = ai_result.get('error', 'Unknown')
                logger.error(f"[ANALYZE] AI service error: {error_detail}")
                return ErrorResponse(
                    message=Message.AI_SERVICE_UNAVAILABLE_MSG,
                    error_code=ErrorCode.AI_SERVICE_UNAVAILABLE,
                    error_details={"error": error_detail},
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE
                )

            # Extract AI result info
            ai_model_version = ai_result.get("ai_model_version", "YOLOv11_EfficientNetV2_1.0")
            processing_time_ms = int(ai_result.get("processing_time", 0) * 1000)
            total_detections = ai_result.get("num_detections", 0)
            detections_raw = ai_result.get("detections", [])

            # Step 3: Xử lý trường hợp không có detection
            if not detections_raw:
                logger.info("[ANALYZE] No valid detections from AI")
                analysis_no_wound = await self.analysis_service.create_no_wound_analysis(
                    user_id=user_id,
                    image_url=image_url,
                    file_name=file.filename,
                    file_size=len(content),
                    ai_model_version=ai_model_version,
                    processing_time_ms=processing_time_ms,
                    total_detections=0
                )
                response_no_wound = ResponseMapper.to_simple_analysis_response(analysis_no_wound)
                return SuccessResponse(
                    message=Message.ANALYSIS_SUCCESS_NO_WOUND_MSG,
                    data=response_no_wound
                )

            logger.info(f"[ANALYZE] Raw Detections from AI: {len(detections_raw)}")

            # Step 4: Tạo analysis record
            analysis = await self.analysis_service.create_wound_analysis(
                user_id=user_id,
                image_url=image_url,
                file_name=file.filename,
                file_size=len(content),
                ai_model_version=ai_model_version,
                total_detections=total_detections,
                processing_time_ms=processing_time_ms
            )

            # Lưu detections vào DB
            await self.analysis_service.save_detections(
                analysis.analysis_id, detections_raw
            )

            # Lấy lại các bản ghi WoundDetection từ DATABASE
            saved_detections_models = await self.analysis_service.get_detections_for_analysis(
                analysis.analysis_id
            )
            logger.info(f"[ANALYZE] Fetched {len(saved_detections_models)} detections from DB for response mapping.")

            # Step 5: Tạo response
            simple_response = ResponseMapper.to_simple_analysis_response(analysis)

            logger.info(f"[ANALYZE] Success: {analysis.analysis_id}")
            return SuccessResponse(
                message=Message.ANALYSIS_SUCCESS_MSG,
                data=simple_response
            )

        except HTTPException:
            raise  # Re-raise HTTPException từ các service khác
        except AppBaseException as e:
            logger.error(f"[ANALYZE] AppBaseException: {e}")
            FileUploadService.cleanup_file(file_path)
            return ErrorResponse(
                message=e.message,
                error_code=getattr(e, 'error_code', ErrorCode.INTERNAL_ERROR),
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"[ANALYZE] Unexpected: {e}", exc_info=True)
            FileUploadService.cleanup_file(file_path)
            return ErrorResponse(
                message=Message.ANALYSIS_PROCESS_ERROR_MSG,
                error_code=ErrorCode.INTERNAL_ERROR,
                error_details={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def check_health(self) -> Union[SuccessResponse[dict], ErrorResponse]:
        """Endpoint: Health check."""
        try:
            logger.debug("[HEALTH] Checking...")
            
            async with WoundAIService() as ai_service:
                model_health = await ai_service.check_model_health()

            db_healthy = True
            try:
                from sqlmodel import text
                await self.db.execute(text("SELECT 1"))
            except Exception:
                db_healthy = False

            overall_healthy = model_health["overall_health"] and db_healthy
            
            health_data = {
                "status": "healthy" if overall_healthy else "unhealthy",
                "ai_models": model_health,
                "database": "healthy" if db_healthy else "unhealthy",
                "accuracy_threshold": DetectionProcessor.MIN_CONFIDENCE_THRESHOLD,
                "supported_wound_types": model_health["supported_wound_types"],
                "timestamp": datetime.now().isoformat()
            }

            logger.info(f"[HEALTH] {health_data['status']}")
            
            return SuccessResponse(
                message=Message.HEALTH_CHECK_SUCCESS_MSG,
                data=health_data
            )

        except Exception as e:
            logger.error(f"[HEALTH] Failed: {e}")
            return ErrorResponse(
                message=Message.HEALTH_CHECK_ERROR_MSG,
                error_code=ErrorCode.HEALTH_CHECK_ERROR,
                error_details={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_analysis_history(
        self,
        user_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0
    ) -> Union[SuccessResponse[dict], ErrorResponse]:
        """Endpoint: Get user analysis history."""
        try:
            logger.debug(f"[HISTORY] User: {user_id}, limit: {limit}, offset: {offset}")
            
            analyses = await self.analysis_service.get_user_analysis_history(
                user_id=user_id,
                limit=limit,
                offset=offset
            )

            response_data = ResponseMapper.to_analysis_history_response(analyses)

            logger.info(
                f"[HISTORY] Retrieved {len(analyses)} analyses "
                f"(success rate: {response_data['statistics']['success_rate']:.1f}%)"
            )

            return SuccessResponse(
                message=Message.HISTORY_SUCCESS_MSG,
                
                data=response_data
            )

        except Exception as e:
            logger.error(f"[HISTORY] Error: {e}")
            return ErrorResponse(
                message=Message.HISTORY_ERROR_MSG,
                error_code=ErrorCode.HISTORY_ERROR,
                error_details={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_analysis_detail(
        self,
        analysis_id: uuid.UUID,
        user_id: Optional[str]
    ) -> Union[SuccessResponse[WoundAnalysisResponse], ErrorResponse]:
        """
        Endpoint: Get analysis detail.
        Authorization:
        - Authenticated users can view their own analyses or all if admin.
        - Guests can only view guest analyses (user_id is None).
        """
        try:
            logger.debug(f"[DETAIL] Analysis: {analysis_id}, User: {user_id}")

            analysis = await self.analysis_service.get_analysis_by_id(analysis_id)

            if not analysis:
                return ErrorResponse(
                    message=Message.ANALYSIS_NOT_FOUND_MSG,
                    error_code=ErrorCode.ANALYSIS_NOT_FOUND,
                    error_details={"analysis_id": str(analysis_id)},
                    status_code=status.HTTP_404_NOT_FOUND
                )

            # Check authorization
            if user_id:
                # Authenticated user
                is_admin = await check_user_has_role(self.db, user_id, "admin")
                if str(analysis.user_id) != user_id and not is_admin:
                    return ErrorResponse(
                        message=Message.ANALYSIS_ACCESS_DENIED_MSG,
                        error_code=ErrorCode.ANALYSIS_ACCESS_DENIED,
                        status_code=status.HTTP_403_FORBIDDEN
                    )
            else:
                # Guest user
                if analysis.user_id is not None:
                    return ErrorResponse(
                        message=Message.GUEST_ACCESS_DENIED_MSG,
                        error_code=ErrorCode.GUEST_ACCESS_DENIED,
                        status_code=status.HTTP_403_FORBIDDEN
                    )

            # Get detections
            detections = await self.analysis_service.get_detections_for_analysis(
                analysis_id
            )

            response = ResponseMapper.to_wound_analysis_response(
                analysis,
                detections
            )

            return SuccessResponse(
                message=Message.GET_DETAIL_SUCCESS_MSG,
                data=response
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[DETAIL] Error: {e}")
            return ErrorResponse(
                message=Message.GET_DETAIL_ERROR_MSG,
                error_code=ErrorCode.GET_DETAIL_ERROR,
                error_details={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def delete_analysis(
        self,
        analysis_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> Union[SuccessResponse[Dict[str, Any]], ErrorResponse]:
        """Endpoint: Soft delete analysis."""
        try:
            logger.debug(f"[DELETE] Analysis: {analysis_id}, User: {user_id}")
            
            analysis = await self.analysis_service.get_analysis_by_id(analysis_id)
            
            if not analysis:
                return ErrorResponse(
                    message=Message.ANALYSIS_NOT_FOUND_MSG,
                    error_code=ErrorCode.ANALYSIS_NOT_FOUND,
                    error_details={"analysis_id": str(analysis_id)},
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            is_admin = await check_user_has_role(self.db, user_id, "admin")

            if str(analysis.user_id) != user_id and not is_admin:
                return ErrorResponse(
                    message=Message.DELETE_ACCESS_DENIED_MSG,
                    error_code=ErrorCode.DELETE_ACCESS_DENIED,
                    status_code=status.HTTP_403_FORBIDDEN
                )
            
            await self.analysis_service.soft_delete_analysis(analysis_id)
            
            return SuccessResponse(
                message=Message.DELETE_SUCCESS_MSG,
                data={"analysis_id": str(analysis_id), "deleted": True}
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[DELETE] Error: {e}")
            return ErrorResponse(
                message=Message.DELETE_ERROR_MSG,
                error_code=ErrorCode.DELETE_ERROR,
                error_details={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )