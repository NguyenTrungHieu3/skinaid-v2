from fastapi import UploadFile, status
from sqlmodel.ext.asyncio.session import AsyncSession
from uuid import UUID
from typing import Optional, Union, List
from app.shared.validators.file_validator import FileValidator
from app.shared.services.file_service import FileService
from app.shared.mappers.response_mapper import ResponseMapper
from app.shared.schemas.response import SuccessResponse, ErrorResponse
from app.modules.ai.models.wound_analysis import WoundAnalysis
from app.modules.ai.models.wound_detection import WoundDetection
from app.modules.ai.services.wound_ai_service import WoundAIService
from app.modules.ai.services.wound_analysis_service import WoundAnalysisService
from app.modules.ai.schemas.wound_analysis_schemas import (
    WoundAnalysisResponse,
    WoundAnalysisListResponse,
    WoundAnalysisDetailResponse
)
from app.modules.firstaid.services.first_aid_service import FirstAidService
from app.utils.constants import error_codes as ErrorCode
from app.utils.constants import messages as Message
from app.utils.exceptions.base_exceptions import AppBaseException
import logging
logger = logging.getLogger(__name__)
class AIController:
    """
    Controller for AI wound analysis operations.
    
    Responsibilities:
        - Handle HTTP requests for wound analysis
        - Validate file uploads
        - Coordinate AI analysis workflow
        - Format responses
    """
    
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.validator = FileValidator()
        self.file_service = FileService()
        self.ai_service = WoundAIService()
        self.analysis_service = WoundAnalysisService(db)
        self.first_aid_service = FirstAidService(db)
        self.response_mapper = ResponseMapper()
    async def analyze_image(
        self,
        file: UploadFile,
        user_id: Optional[UUID] = None,
        session_id: Optional[UUID] = None
    ) -> Union[SuccessResponse[WoundAnalysisResponse], ErrorResponse]:
        """
        Analyze wound image using AI
        """
        try:
            logger.info(f"[ANALYZE_IMAGE] Starting analysis - user: {user_id}, session: {session_id}")
            
            # Validate identifiers
            if user_id is None and session_id is None:
                logger.warning("[ANALYZE_IMAGE] Missing identifier")
                return ErrorResponse(
                    message=Message.AI_MISSING_IDENTIFIER_MSG,
                    error_code=ErrorCode.AI_MISSING_IDENTIFIER,
                    error_details={
                        "required": "user_id or session_id",
                        "provided": None
                    },
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            if user_id is not None and session_id is not None:
                logger.warning("[ANALYZE_IMAGE] Multiple identifiers provided")
                return ErrorResponse(
                    message=Message.AI_MULTIPLE_IDENTIFIERS_MSG,
                    error_code=ErrorCode.AI_MULTIPLE_IDENTIFIERS,
                    error_details={
                        "error": "Provide either user_id or session_id, not both"
                    },
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            # Validate file
            validation = await self.validator.validate_upload_file(file)
            if not validation['valid']:
                logger.warning(f"[ANALYZE_IMAGE] File validation failed: {validation['error']}")
                return ErrorResponse(
                    message=Message.AI_INVALID_FILE_MSG,
                    error_code=ErrorCode.AI_INVALID_FILE,
                    error_details={"validation_error": validation['error']},
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            # Save file
            subfolder = f"user/{user_id}" if user_id else f"guest/{session_id}"
            save_result = await self.file_service.save_file(
                file_content=validation['content'],
                filename=file.filename,
                subfolder=subfolder
            )
            # Analyze with AI
            ai_result = await self.ai_service.analyze_wound(
                image_path=save_result['file_path']
            )
            # Create WoundAnalysis record
            analysis = WoundAnalysis.create_analysis(
                user_id=user_id,
                session_id=session_id,
                image_url=save_result['file_url'],
                file_name=save_result['filename'],
                file_size=validation['size'],
                total_detections=len(ai_result.get('detections', [])),
                processing_time_ms=ai_result.get('processing_time_ms', 0)
            )
            self.db.add(analysis)
            await self.db.flush()
            # Create WoundDetection records
            for idx, detection in enumerate(ai_result.get('detections', [])):
                # Get first aid guide for this detection
                guide = await self.first_aid_service.get_first_aid_guide(
                    wound_type=detection['wound_type'],
                    severity=detection['severity'],
                    sub_type=detection.get('sub_type')
                )
                # Extract guide ID and snapshot
                guide_id = guide.get('firstaidguide_id') if guide else None
                snapshot = self.analysis_service.extract_snapshot(guide)
                wound_detection = WoundDetection(
                    analysis_id=analysis.analysis_id,
                    wound_type=detection['wound_type'],
                    severity=detection['severity'],
                    sub_type=detection.get('sub_type'),
                    confidence_score=detection['confidence'],
                    bounding_box=detection.get('bounding_box'),
                    detection_index=idx,
                    firstaidguide_id=guide_id,
                    firstaid_snapshot=snapshot
                )
                self.db.add(wound_detection)
            await self.db.commit()
            await self.db.refresh(analysis, ['wound_detections'])
            # Format response
            response_data = self.response_mapper.map_wound_analysis_basic(analysis)
            
            logger.info(f"[ANALYZE_IMAGE] Success: {analysis.analysis_id}")
            
            return SuccessResponse(
                message=Message.AI_ANALYSIS_SUCCESS_MSG,
                data=response_data,
                status_code=status.HTTP_201_CREATED
            )
        except AppBaseException as e:
            logger.error(f"[ANALYZE_IMAGE] AppBaseException: {e.message}")
            return ErrorResponse(
                message=e.message,
                error_code=e.error_code or ErrorCode.AI_ANALYSIS_ERROR,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"[ANALYZE_IMAGE] Unexpected error", exc_info=True)
            return ErrorResponse(
                message=Message.INTERNAL_ERROR_MSG,
                error_code=ErrorCode.INTERNAL_ERROR,
                error_details={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    async def get_analysis_history(
        self,
        user_id: Optional[UUID] = None,
        session_id: Optional[UUID] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Union[SuccessResponse[WoundAnalysisListResponse], ErrorResponse]:
        """
        Get analysis history for user or guest session
        """
        try:
            logger.info(f"[GET_HISTORY] Fetching history - user: {user_id}, session: {session_id}")
            
            analyses = await self.analysis_service.get_history(
                user_id=user_id,
                session_id=session_id,
                limit=limit,
                offset=offset
            )
            response_data = WoundAnalysisListResponse(
                total=len(analyses),
                limit=limit,
                offset=offset,
                analyses=[
                    self.response_mapper.map_wound_analysis(a, include_detections=False)
                    for a in analyses
                ]
            )
            logger.info(f"[GET_HISTORY] Success: found {len(analyses)} analyses")
            
            return SuccessResponse(
                message=Message.AI_HISTORY_SUCCESS_MSG,
                data=response_data
            )
        except Exception as e:
            logger.error(f"[GET_HISTORY] Unexpected error", exc_info=True)
            return ErrorResponse(
                message=Message.AI_HISTORY_ERROR_MSG,
                error_code=ErrorCode.AI_HISTORY_ERROR,
                error_details={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    async def get_analysis_detail(
        self,
        analysis_id: UUID,
        user_id: Optional[UUID] = None,
        session_id: Optional[UUID] = None
    ) -> Union[SuccessResponse[WoundAnalysisDetailResponse], ErrorResponse]:
        """
        Get detailed analysis by ID
        """
        try:
            logger.info(f"[GET_DETAIL] Fetching analysis: {analysis_id}")
            
            analysis = await self.analysis_service.get_by_id(analysis_id)
            if not analysis:
                logger.warning(f"[GET_DETAIL] Analysis not found: {analysis_id}")
                return ErrorResponse(
                    message=Message.AI_ANALYSIS_NOT_FOUND_MSG,
                    error_code=ErrorCode.AI_ANALYSIS_NOT_FOUND,
                    error_details={"analysis_id": str(analysis_id)},
                    status_code=status.HTTP_404_NOT_FOUND
                )
            # Authorization check
            if user_id is not None:
                request_user_id = UUID(user_id) if isinstance(user_id, str) else user_id
                if analysis.user_id and analysis.user_id != request_user_id:
                    logger.warning(f"[GET_DETAIL] Access denied for user: {user_id}")
                    return ErrorResponse(
                        message=Message.AI_ACCESS_DENIED_MSG,
                        error_code=ErrorCode.AI_ACCESS_DENIED,
                        error_details={"analysis_id": str(analysis_id)},
                        status_code=status.HTTP_403_FORBIDDEN
                    )
            if session_id is not None:
                request_session_id = UUID(session_id) if isinstance(session_id, str) else session_id
                if analysis.session_id and analysis.session_id != request_session_id:
                    logger.warning(f"[GET_DETAIL] Access denied for session: {session_id}")
                    return ErrorResponse(
                        message=Message.AI_ACCESS_DENIED_MSG,
                        error_code=ErrorCode.AI_ACCESS_DENIED,
                        error_details={"analysis_id": str(analysis_id)},
                        status_code=status.HTTP_403_FORBIDDEN
                    )
            response_data = self.response_mapper.map_wound_analysis(
                analysis,
                include_detections=True
            )
            logger.info(f"[GET_DETAIL] Success: {analysis_id}")
            
            return SuccessResponse(
                message=Message.AI_DETAIL_SUCCESS_MSG,
                data=response_data
            )
        except Exception as e:
            logger.error(f"[GET_DETAIL] Unexpected error", exc_info=True)
            return ErrorResponse(
                message=Message.AI_DETAIL_ERROR_MSG,
                error_code=ErrorCode.AI_DETAIL_ERROR,
                error_details={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    async def delete_analysis(
        self,
        analysis_id: UUID,
        user_id: Optional[UUID] = None,
        session_id: Optional[UUID] = None
    ) -> Union[SuccessResponse[dict], ErrorResponse]:
        """
        Soft delete a wound analysis
        """
        try:
            logger.info(f"[DELETE_ANALYSIS] Deleting analysis: {analysis_id}")
            
            analysis = await self.analysis_service.get_by_id(analysis_id)
            if not analysis:
                logger.warning(f"[DELETE_ANALYSIS] Analysis not found: {analysis_id}")
                return ErrorResponse(
                    message=Message.AI_ANALYSIS_NOT_FOUND_MSG,
                    error_code=ErrorCode.AI_ANALYSIS_NOT_FOUND,
                    error_details={"analysis_id": str(analysis_id)},
                    status_code=status.HTTP_404_NOT_FOUND
                )
            # Authorization check
            if user_id is not None:
                request_user_id = UUID(user_id) if isinstance(user_id, str) else user_id
                if analysis.user_id and analysis.user_id != request_user_id:
                    logger.warning(f"[DELETE_ANALYSIS] Access denied for user: {user_id}")
                    return ErrorResponse(
                        message=Message.AI_ACCESS_DENIED_MSG,
                        error_code=ErrorCode.AI_ACCESS_DENIED,
                        error_details={"analysis_id": str(analysis_id)},
                        status_code=status.HTTP_403_FORBIDDEN
                    )
            if session_id is not None:
                request_session_id = UUID(session_id) if isinstance(session_id, str) else session_id
                if analysis.session_id and analysis.session_id != request_session_id:
                    logger.warning(f"[DELETE_ANALYSIS] Access denied for session: {session_id}")
                    return ErrorResponse(
                        message=Message.AI_ACCESS_DENIED_MSG,
                        error_code=ErrorCode.AI_ACCESS_DENIED,
                        error_details={"analysis_id": str(analysis_id)},
                        status_code=status.HTTP_403_FORBIDDEN
                    )
            # Soft delete
            await self.analysis_service.soft_delete_analysis(analysis_id)
            logger.info(f"[DELETE_ANALYSIS] Success: {analysis_id}")
            
            return SuccessResponse(
                message=Message.AI_DELETE_SUCCESS_MSG,
                data={
                    "analysis_id": str(analysis_id),
                    "deleted": True
                }
            )
        except Exception as e:
            logger.error(f"[DELETE_ANALYSIS] Unexpected error", exc_info=True)
            return ErrorResponse(
                message=Message.AI_DELETE_ERROR_MSG,
                error_code=ErrorCode.AI_DELETE_ERROR,
                error_details={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )