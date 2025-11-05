from typing import Dict, Any, Optional, List, Union
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status
import logging
import uuid

from app.modules.guest.services.guest_service import GuestService
from app.modules.guest.schemas.guest_schemas import (
    GuestSessionResponse,
    GuestUploadResponse,
    GuestAnalysisResponse,
    GuestStatisticsResponse
)
from app.shared.schemas.response import SuccessResponse, ErrorResponse

# Import constants
from app.utils.constants import error_codes as ErrorCode
from app.utils.constants import messages as Message

logger = logging.getLogger(__name__)


class GuestController:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.guest_service = GuestService(db)

    async def create_guest_session(
        self,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Union[SuccessResponse[GuestSessionResponse], ErrorResponse]:
        """Create a new guest session."""
        try:
            logger.info(f"[CREATE_SESSION] Creating guest session - IP: {ip_address}")
            
            session = await self.guest_service.create_guest_session(
                ip_address, user_agent
            )

            if not session:
                logger.error(f"[CREATE_SESSION] Failed to create session - IP: {ip_address}")
                return ErrorResponse(
                    message=Message.GUEST_SESSION_CREATE_ERROR_MSG,
                    error_code=ErrorCode.GUEST_SESSION_CREATE_ERROR,
                    error_details={"ip_address": ip_address},
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            session_response = self._create_session_response(session)
            
            logger.info(
                f"[CREATE_SESSION] Success: {session_response.session_id}"
            )
            
            return SuccessResponse(
                message=Message.GUEST_SESSION_CREATE_SUCCESS_MSG,
                data=session_response,
                status_code=status.HTTP_201_CREATED
            )

        except Exception as e:
            logger.error(f"[CREATE_SESSION] Error: {e}", exc_info=True)
            return ErrorResponse(
                message=Message.GUEST_SESSION_ERROR_MSG,
                error_code=ErrorCode.GUEST_SESSION_ERROR,
                error_details={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_guest_session(
        self,
        session_id: uuid.UUID
    ) -> Union[SuccessResponse[GuestSessionResponse], ErrorResponse]:
        """Get guest session by ID."""
        try:
            logger.info(f"[GET_SESSION] Getting session: {session_id}")
            
            session = await self.guest_service.get_guest_session(session_id)

            if not session:
                logger.warning(f"[GET_SESSION] Session not found: {session_id}")
                return ErrorResponse(
                    message=Message.GUEST_SESSION_NOT_EXISTS_MSG,
                    error_code=ErrorCode.GUEST_SESSION_NOT_FOUND,
                    error_details={"session_id": str(session_id)},
                    status_code=status.HTTP_404_NOT_FOUND
                )

            session_response = self._create_session_response(session)
            
            logger.info(
                f"[GET_SESSION] Success: {session_id} - "
                f"Active: {session_response.is_active}, "
                f"Uploads: {session_response.upload_count}"
            )
            
            return SuccessResponse(
                message=Message.GUEST_SESSION_GET_SUCCESS_MSG,
                data=session_response
            )

        except Exception as e:
            logger.error(f"[GET_SESSION] Error: {e}", exc_info=True)
            return ErrorResponse(
                message=Message.GUEST_SESSION_GET_ERROR_MSG,
                error_code=ErrorCode.GUEST_SESSION_GET_ERROR,
                error_details={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def create_guest_upload(
        self,
        session_id: uuid.UUID,
        file_path: str,
        file_name: str,
        file_size: int,
        mime_type: Optional[str] = None
    ) -> Union[SuccessResponse[GuestUploadResponse], ErrorResponse]:
        """Create a guest upload record."""
        try:
            logger.info(
                f"[CREATE_UPLOAD] Session: {session_id}, "
                f"File: {file_name}, Size: {file_size}"
            )
            
            upload = await self.guest_service.create_guest_upload(
                session_id, file_path, file_name, file_size, mime_type
            )

            if not upload:
                logger.error(
                    f"[CREATE_UPLOAD] Failed - Session: {session_id}"
                )
                return ErrorResponse(
                    message=Message.GUEST_UPLOAD_CREATE_ERROR_MSG,
                    error_code=ErrorCode.GUEST_UPLOAD_CREATE_ERROR,
                    error_details={"session_id": str(session_id)},
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            upload_response = self._create_upload_response(upload)
            
            logger.info(
                f"[CREATE_UPLOAD] Success: {upload_response.upload_id}"
            )
            
            return SuccessResponse(
                message=Message.GUEST_UPLOAD_CREATE_SUCCESS_MSG,
                data=upload_response,
                status_code=status.HTTP_201_CREATED
            )

        except Exception as e:
            logger.error(f"[CREATE_UPLOAD] Error: {e}", exc_info=True)
            return ErrorResponse(
                message=Message.GUEST_UPLOAD_ERROR_MSG,
                error_code=ErrorCode.GUEST_UPLOAD_ERROR,
                error_details={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def create_guest_analysis(
        self,
        session_id: uuid.UUID,
        upload_id: Optional[uuid.UUID] = None,
        wound_type: Optional[str] = None,
        severity: Optional[str] = None,
        confidence: Optional[float] = None,
        result_json: Optional[Dict[str, Any]] = None
    ) -> Union[SuccessResponse[GuestAnalysisResponse], ErrorResponse]:
        """Create a guest analysis record."""
        try:
            logger.info(
                f"[CREATE_ANALYSIS] Session: {session_id}, "
                f"Upload: {upload_id}, Type: {wound_type}, "
                f"Severity: {severity}, Confidence: {confidence}"
            )
            
            analysis = await self.guest_service.create_guest_analysis(
                session_id, upload_id, wound_type, severity, confidence, result_json
            )

            if not analysis:
                logger.error(
                    f"[CREATE_ANALYSIS] Failed - Session: {session_id}"
                )
                return ErrorResponse(
                    message=Message.GUEST_ANALYSIS_CREATE_ERROR_MSG,
                    error_code=ErrorCode.GUEST_ANALYSIS_CREATE_ERROR,
                    error_details={"session_id": str(session_id)},
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            analysis_response = self._create_analysis_response(analysis)
            
            logger.info(
                f"[CREATE_ANALYSIS] Success: {analysis_response.analysis_id}"
            )
            
            return SuccessResponse(
                message=Message.GUEST_ANALYSIS_CREATE_SUCCESS_MSG,
                data=analysis_response,
                status_code=status.HTTP_201_CREATED
            )

        except Exception as e:
            logger.error(f"[CREATE_ANALYSIS] Error: {e}", exc_info=True)
            return ErrorResponse(
                message=Message.GUEST_ANALYSIS_ERROR_MSG,
                error_code=ErrorCode.GUEST_ANALYSIS_ERROR,
                error_details={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_guest_uploads(
        self,
        session_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0
    ) -> Union[SuccessResponse[List[GuestUploadResponse]], ErrorResponse]:
        """Get all uploads for a guest session."""
        try:
            logger.info(
                f"[GET_UPLOADS] Session: {session_id}, "
                f"Limit: {limit}, Offset: {offset}"
            )
            
            uploads = await self.guest_service.get_guest_uploads(
                session_id, limit, offset
            )

            upload_responses = [
                self._create_upload_response(upload) for upload in uploads
            ]

            logger.info(
                f"[GET_UPLOADS] Success: {len(upload_responses)} uploads found"
            )
            
            return SuccessResponse(
                message=Message.GUEST_UPLOADS_FOUND_COUNT_MSG.format(
                    count=len(upload_responses)
                ),
                data=upload_responses
            )

        except Exception as e:
            logger.error(f"[GET_UPLOADS] Error: {e}", exc_info=True)
            return ErrorResponse(
                message=Message.GUEST_UPLOADS_ERROR_MSG,
                error_code=ErrorCode.GUEST_UPLOADS_ERROR,
                error_details={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_guest_analyses(
        self,
        session_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0
    ) -> Union[SuccessResponse[List[GuestAnalysisResponse]], ErrorResponse]:
        """Get all analyses for a guest session."""
        try:
            logger.info(
                f"[GET_ANALYSES] Session: {session_id}, "
                f"Limit: {limit}, Offset: {offset}"
            )
            
            analyses = await self.guest_service.get_guest_analyses(
                session_id, limit, offset
            )

            analysis_responses = [
                self._create_analysis_response(analysis) for analysis in analyses
            ]

            logger.info(
                f"[GET_ANALYSES] Success: {len(analysis_responses)} analyses found"
            )
            
            return SuccessResponse(
                message=Message.GUEST_ANALYSES_FOUND_COUNT_MSG.format(
                    count=len(analysis_responses)
                ),
                data=analysis_responses
            )

        except Exception as e:
            logger.error(f"[GET_ANALYSES] Error: {e}", exc_info=True)
            return ErrorResponse(
                message=Message.GUEST_ANALYSES_ERROR_MSG,
                error_code=ErrorCode.GUEST_ANALYSES_ERROR,
                error_details={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_guest_statistics(
        self
    ) -> Union[SuccessResponse[GuestStatisticsResponse], ErrorResponse]:
        """Get overall guest statistics."""
        try:
            logger.info("[STATISTICS] Getting guest statistics")
            
            stats = await self.guest_service.get_guest_statistics()

            logger.info(
                f"[STATISTICS] Success - "
                f"Total sessions: {stats.get('total_sessions', 0)}, "
                f"Active sessions: {stats.get('active_sessions', 0)}"
            )
            
            return SuccessResponse(
                message=Message.GUEST_STATISTICS_SUCCESS_MSG,
                data=GuestStatisticsResponse(**stats)
            )

        except Exception as e:
            logger.error(f"[STATISTICS] Error: {e}", exc_info=True)
            return ErrorResponse(
                message=Message.GUEST_STATISTICS_ERROR_MSG,
                error_code=ErrorCode.GUEST_STATISTICS_ERROR,
                error_details={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # ============================================
    # Private Helper Methods
    # ============================================

    def _create_session_response(
        self,
        session: Dict[str, Any]
    ) -> GuestSessionResponse:
        """Create GuestSessionResponse from session data."""
        return GuestSessionResponse(
            session_id=uuid.UUID(session.get("session_id")),
            ip_address=session.get("ip_address"),
            user_agent=session.get("user_agent"),
            upload_count=session.get("upload_count", 0),
            analysis_count=session.get("analysis_count", 0),
            is_active=session.get("is_active", True),
            is_converted_to_user=session.get("is_converted_to_user", False),
            converted_user_id=uuid.UUID(session.get("converted_user_id")) if session.get("converted_user_id") else None,
            created_at=session.get("created_at"),
            expires_at=session.get("expires_at"),
            last_activity_at=session.get("last_activity_at"),
            is_expired=session.get("is_expired", False),
            can_upload=session.get("can_upload", True),
            can_analyze=session.get("can_analyze", True),
            remaining_uploads=session.get("remaining_uploads", 0),
            remaining_analyses=session.get("remaining_analyses", 0)
        )

    def _create_upload_response(
        self,
        upload: Dict[str, Any]
    ) -> GuestUploadResponse:
        """Create GuestUploadResponse from upload data."""
        return GuestUploadResponse(
            upload_id=uuid.UUID(upload.get("upload_id")),
            session_id=uuid.UUID(upload.get("session_id")),
            file_path=upload.get("file_path"),
            file_name=upload.get("file_name"),
            file_size=upload.get("file_size", 0),
            mime_type=upload.get("mime_type"),
            created_at=upload.get("created_at"),
            is_deleted=upload.get("is_deleted", False),
            deleted_at=upload.get("deleted_at")
        )

    def _create_analysis_response(
        self,
        analysis: Dict[str, Any]
    ) -> GuestAnalysisResponse:
        """Create GuestAnalysisResponse from analysis data."""
        return GuestAnalysisResponse(
            analysis_id=uuid.UUID(analysis.get("analysis_id")),
            session_id=uuid.UUID(analysis.get("session_id")),
            upload_id=uuid.UUID(analysis.get("upload_id")) if analysis.get("upload_id") else None,
            wound_type=analysis.get("wound_type"),
            severity=analysis.get("severity"),
            confidence=analysis.get("confidence"),
            result_json=analysis.get("result_json"),
            created_at=analysis.get("created_at"),
            is_deleted=analysis.get("is_deleted", False)
        )