import asyncio
from fastapi import status
from sqlmodel.ext.asyncio.session import AsyncSession
from uuid import UUID
from typing import Optional, Union, List

from app.shared.schemas.response import SuccessResponse, ErrorResponse
from app.modules.ai.services.wound_analysis_service import WoundAnalysisService
from app.modules.ai.services.image_processing_service import ImageProcessingService
from app.modules.ai.schemas.wound_analysis_schemas import (
    WoundAnalysisResponse,
    WoundAnalysisListResponse,
    WoundAnalysisDetailResponse, 
    BatchAnalysisItemResult, 
    BatchAnalysisResponse
)
from app.shared.mappers.response_mapper import ResponseMapper
from app.utils.constants import error_codes as ErrorCode
from app.utils.constants import messages as Message
from app.modules.audit.services.audit_service import AuditService

import logging
logger = logging.getLogger(__name__)
class AIController:
    
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.audit_service = AuditService(db)
        self.image_processor = ImageProcessingService(db)
        self.analysis_service = WoundAnalysisService(db)
        self.response_mapper = ResponseMapper()
    
    async def analyze_image(
        self,
        file,
        user_id: Optional[UUID] = None,
        session_id: Optional[UUID] = None
    ) -> Union[SuccessResponse[WoundAnalysisResponse], ErrorResponse]:
        """
        Phân tích một ảnh vết thương.
        """
        logger.info(f"[ANALYZE_IMAGE] Starting analysis - user: {user_id}, session: {session_id}")
        
        # Xác thực danh tính
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
        
        return await self.image_processor.process_single_image(
            file=file,
            user_id=user_id,
            session_id=session_id
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
                events=[
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
            # Kiểm tra quyền truy cập
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
            # Kiểm tra quyền truy cập
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
            # Xóa mềm
            await self.analysis_service.soft_delete_analysis(analysis_id)
            
            await self.audit_service.log_event(
                action="wound_analysis_deleted",
                user_id=user_id or analysis.user_id,
                resource_type="wound_analysis",
                resource_id=str(analysis_id),
                is_guest=(session_id is not None),
                guest_session_id=session_id,
                success=True
            )
            
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

    async def analyze_multiple_images(
        self,
        files: List,
        user_id: Optional[UUID] = None,
        session_id: Optional[UUID] = None,
        max_files: int = 5
    ) -> Union[SuccessResponse[BatchAnalysisResponse], ErrorResponse]:
        """
        Phân tích nhiều ảnh vết thương cùng lúc
        """
        logger.info(
            f"[BATCH_ANALYZE] Starting - "
            f"files: {len(files)}, user: {user_id}, session: {session_id}"
        )
        
        if len(files) == 0:
            return ErrorResponse(
                message="Vui lòng cung cấp ít nhất một file",
                error_code=ErrorCode.AI_INVALID_FILE,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        if len(files) > max_files:
            return ErrorResponse(
                message=f"Số lượng file vượt quá giới hạn ({max_files} files)",
                error_code=ErrorCode.AI_INVALID_FILE,
                error_details={
                    "max_files": max_files,
                    "provided": len(files)
                },
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        if user_id is None and session_id is None:
            return ErrorResponse(
                message=Message.AI_MISSING_IDENTIFIER_MSG,
                error_code=ErrorCode.AI_MISSING_IDENTIFIER,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        if user_id is not None and session_id is not None:
            return ErrorResponse(
                message=Message.AI_MULTIPLE_IDENTIFIERS_MSG,
                error_code=ErrorCode.AI_MULTIPLE_IDENTIFIERS,
                status_code=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            batch_response = await self.image_processor.process_batch_images(
                files=files,
                user_id=user_id,
                session_id=session_id
            )
            
            return SuccessResponse(
                message=f"Đã phân tích {batch_response.successful}/{batch_response.total_files} ảnh thành công",
                data=batch_response,
                status_code=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(f"[BATCH_ANALYZE] Unexpected error", exc_info=True)
            return ErrorResponse(
                message=Message.INTERNAL_ERROR_MSG,
                error_code=ErrorCode.INTERNAL_ERROR,
                error_details={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )