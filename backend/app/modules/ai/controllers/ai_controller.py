from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile, HTTPException, status
from typing import Union, Dict, Any, Optional
import logging
from datetime import datetime
import uuid

from app.shared.schemas.response import SuccessResponse, ErrorResponse
from app.modules.ai.schemas.wound_analysis_schemas import WoundAnalysisResponse
from app.modules.ai.services.wound_ai_service import WoundAIService
from app.modules.ai.services.wound_analysis_service import WoundAnalysisService
from app.modules.ai.services.detection_processor import DetectionProcessor
from app.modules.ai.services.file_upload_service import FileUploadService
from app.modules.ai.services.response_mapper import ResponseMapper
from app.utils.exceptions.base_exceptions import AppBaseException
from app.api.v1.deps import check_user_has_role

logger = logging.getLogger(__name__)


class AIController:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.analysis_service = WoundAnalysisService(db)

    async def analyze_image(
        self,
        file: UploadFile,
        user_id: Optional[uuid.UUID]
    ) -> Union[SuccessResponse[WoundAnalysisResponse], ErrorResponse]:
        file_path = None

        try:
            # Step 1: File handling (Giữ nguyên)
            display_user_id = user_id or "anonymous"
            file_path, relative_path, image_url = FileUploadService.generate_image_path(
                display_user_id, file.filename
            )
            content = await FileUploadService.save_file(file, file_path)
            validation_error = FileUploadService.validate_file(file, content)
            if validation_error:
                FileUploadService.cleanup_file(file_path)
                return validation_error

            # Step 2: AI analysis (Giữ nguyên, đổi tên biến)
            logger.info(f"[ANALYZE] Starting: {file.filename} (user: {user_id or 'guest'})")
            async with WoundAIService() as ai_service:
                ai_result = await ai_service.analyze_wound_image(file_path)

            if not ai_result.get("success", False):
                # ... (Xử lý lỗi AI - Giữ nguyên)
                FileUploadService.cleanup_file(file_path)
                # Nên raise HTTPException ở đây thay vì return ErrorResponse
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"AI analysis failed: {ai_result.get('error', 'Unknown')}"
                )

            # Extract AI result info (Giữ nguyên)
            ai_model_version = ai_result.get("ai_model_version", "YOLOv11_EfficientNetV2_1.0")
            processing_time_ms = int(ai_result.get("processing_time", 0) * 1000)
            total_detections = ai_result.get("num_detections", 0)
            
            # Đổi tên: Detections thô từ AI/ML
            detections_raw = ai_result.get("detections", []) 

            # Step 3: Xử lý trường hợp không có detection (Sửa đổi để lấy lại detection rỗng)
            if not detections_raw:
                logger.info("[ANALYZE] No valid detections from AI")
                analysis_no_wound = await self.analysis_service.create_no_wound_analysis(
                    user_id=user_id,
                    image_url=image_url,
                    file_name=file.filename,
                    file_size=len(content),
                    ai_model_version=ai_model_version,
                    processing_time_ms=processing_time_ms,
                    total_detections=0 # Đảm bảo là 0
                )
                # Tạo response với analysis và danh sách detections rỗng
                response_no_wound = ResponseMapper.to_wound_analysis_response(
                    analysis_no_wound, [] # Truyền danh sách rỗng
                )
                return SuccessResponse(
                    message="Phân tích hoàn thành - không phát hiện vết thương",
                    data=response_no_wound
                )

            logger.info(f"[ANALYZE] Raw Detections from AI: {len(detections_raw)}")

            # Step 4: Tạo analysis record (Giữ nguyên)
            analysis = await self.analysis_service.create_wound_analysis(
                user_id=user_id,
                image_url=image_url,
                file_name=file.filename,
                file_size=len(content),
                ai_model_version=ai_model_version,
                # Dùng total_detections đã tính từ AI result
                total_detections=total_detections, 
                processing_time_ms=processing_time_ms
            )

            # Lưu detections vào DB (Giữ nguyên)
            # Hàm này sẽ xử lý việc lấy firstaid_snapshot và lưu vào DB
            await self.analysis_service.save_detections(
                analysis.analysis_id, detections_raw
            )

            # ✅✅✅ BƯỚC SỬA QUAN TRỌNG ✅✅✅
            # Lấy lại các bản ghi WoundDetection TỪ DATABASE
            # vì chúng đã được cập nhật với firstaid_snapshot
            saved_detections_models = await self.analysis_service.get_detections_for_analysis(
                analysis.analysis_id
            )
            logger.info(f"[ANALYZE] Fetched {len(saved_detections_models)} detections from DB for response mapping.")


            # Step 5: Map response SỬ DỤNG DỮ LIỆU TỪ DB
            # Truyền analysis model và SAVED detection models vào mapper
            response = ResponseMapper.to_wound_analysis_response(
                analysis, saved_detections_models # <-- Sửa ở đây
            )

            logger.info(
                f"[ANALYZE] Success: {analysis.analysis_id} "
                f"(confidence: {response.average_confidence:.2%})"
            )
            return SuccessResponse(
                message="Phân tích hình ảnh thành công",
                data=response
            )

        except HTTPException:
             raise # Ném lại các lỗi HTTP đã raise (vd: 503 từ AI)
        except AppBaseException as e:
            logger.error(f"[ANALYZE] AppBaseException: {e}")
            FileUploadService.cleanup_file(file_path)
            # Chuyển thành HTTPException để frontend dễ bắt lỗi
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
        except Exception as e:
            logger.error(f"[ANALYZE] Unexpected: {e}", exc_info=True)
            FileUploadService.cleanup_file(file_path)
            # Chuyển thành HTTPException
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Có lỗi xảy ra trong quá trình phân tích")

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
                message="Health check completed",
                data=health_data
            )

        except Exception as e:
            logger.error(f"[HEALTH] Failed: {e}")
            return ErrorResponse(
                message="Không thể kiểm tra trạng thái",
                error_code="HEALTH_CHECK_ERROR",
                error_details={"error": str(e)}
            )

    async def get_analysis_history(
        self,
        user_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0
    ) -> Union[SuccessResponse[dict], ErrorResponse]:
        """
        Endpoint: Get user analysis history.
        """
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
                message="Lấy lịch sử thành công",
                data=response_data
            )

        except Exception as e:
            logger.error(f"[HISTORY] Error: {e}")
            return ErrorResponse(
                message="Không thể lấy lịch sử",
                error_code="HISTORY_ERROR",
                error_details={"error": str(e)}
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
                    message="Analysis not found",
                    error_code="ANALYSIS_NOT_FOUND",
                    error_details={"analysis_id": analysis_id}
                )

            # Check authorization
            if user_id:
                # Authenticated user
                is_admin = await check_user_has_role(self.db, user_id, "admin")
                if str(analysis.user_id) != user_id and not is_admin:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="You can only access your own analyses or all if admin"
                    )
            else:
                # Guest user
                if analysis.user_id is not None:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Guests can only access guest analyses"
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
                message="Lấy chi tiết analysis thành công",
                data=response
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[DETAIL] Error: {e}")
            return ErrorResponse(
                message="Không thể lấy chi tiết analysis",
                error_code="GET_DETAIL_ERROR",
                error_details={"error": str(e)}
            )

    async def delete_analysis(
        self,
        analysis_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> Union[SuccessResponse[Dict[str, str]], ErrorResponse]:
        """
        Endpoint: Soft delete analysis.
        """
        try:
            logger.debug(f"[DELETE] Analysis: {analysis_id}, User: {user_id}")
            
            analysis = await self.analysis_service.get_analysis_by_id(analysis_id)
            
            if not analysis:
                return ErrorResponse(
                    message="Analysis not found",
                    error_code="ANALYSIS_NOT_FOUND",
                    error_details={"analysis_id": analysis_id}
                )
            
            is_admin = await check_user_has_role(self.db, user_id, "admin")

            if str(analysis.user_id) != user_id and not is_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only delete your own analyses"
                )
            
            await self.analysis_service.soft_delete_analysis(analysis_id)
            
            return SuccessResponse(
                message="Xóa analysis thành công",
                data={"analysis_id": analysis_id, "deleted": True}
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[DELETE] Error: {e}")
            return ErrorResponse(
                message="Không thể xóa analysis",
                error_code="DELETE_ERROR",
                error_details={"error": str(e)}
            )