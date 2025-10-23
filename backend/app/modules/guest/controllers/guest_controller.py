from typing import Dict, Any, Optional, List, Union
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.guest.services.guest_service import GuestService
from app.modules.guest.schemas.guest_schemas import (
    GuestSessionResponse,
    GuestUploadResponse,
    GuestAnalysisResponse,
    GuestStatisticsResponse
)
from app.shared.schemas.response import SuccessResponse, ErrorResponse
import logging
import uuid

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

        try:
            session = await self.guest_service.create_guest_session(ip_address, user_agent)

            if not session:
                return ErrorResponse(
                    message="Không thể tạo guest session",
                    error_code="GUEST_SESSION_CREATE_ERROR",
                    error_details={"ip_address": ip_address}
                )

            session_response = self._create_session_response(session)
            return SuccessResponse(
                message="Tạo guest session thành công",
                data=session_response
            )

        except Exception as e:
            logger.error(f"Failed to create guest session: {e}")
            return ErrorResponse(
                message="Không thể tạo guest session",
                error_code="GUEST_SESSION_ERROR",
                error_details={"error": str(e)}
            )

    async def get_guest_session(
        self,
        session_id: uuid.UUID
    ) -> Union[SuccessResponse[GuestSessionResponse], ErrorResponse]:

        try:
            session = await self.guest_service.get_guest_session(session_id)

            if not session:
                return ErrorResponse(
                    message="Guest session không tồn tại",
                    error_code="GUEST_SESSION_NOT_FOUND",
                    error_details={"session_id": str(session_id)}
                )

            session_response = self._create_session_response(session)
            return SuccessResponse(
                message="Lấy guest session thành công",
                data=session_response
            )

        except Exception as e:
            logger.error(f"Failed to get guest session: {e}")
            return ErrorResponse(
                message="Không thể lấy guest session",
                error_code="GUEST_SESSION_ERROR",
                error_details={"error": str(e)}
            )

    async def create_guest_upload(
        self,
        session_id: uuid.UUID,
        file_path: str,
        file_name: str,
        file_size: int,
        mime_type: Optional[str] = None
    ) -> Union[SuccessResponse[GuestUploadResponse], ErrorResponse]:

        try:
            upload = await self.guest_service.create_guest_upload(
                session_id, file_path, file_name, file_size, mime_type
            )

            if not upload:
                return ErrorResponse(
                    message="Không thể tạo guest upload",
                    error_code="GUEST_UPLOAD_CREATE_ERROR",
                    error_details={"session_id": str(session_id)}
                )

            upload_response = self._create_upload_response(upload)
            return SuccessResponse(
                message="Upload file thành công",
                data=upload_response
            )

        except Exception as e:
            logger.error(f"Failed to create guest upload: {e}")
            return ErrorResponse(
                message="Không thể upload file",
                error_code="GUEST_UPLOAD_ERROR",
                error_details={"error": str(e)}
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

        try:
            analysis = await self.guest_service.create_guest_analysis(
                session_id, upload_id, wound_type, severity, confidence, result_json
            )

            if not analysis:
                return ErrorResponse(
                    message="Không thể tạo guest analysis",
                    error_code="GUEST_ANALYSIS_CREATE_ERROR",
                    error_details={"session_id": str(session_id)}
                )

            analysis_response = self._create_analysis_response(analysis)
            return SuccessResponse(
                message="Phân tích thành công",
                data=analysis_response
            )

        except Exception as e:
            logger.error(f"Failed to create guest analysis: {e}")
            return ErrorResponse(
                message="Không thể phân tích",
                error_code="GUEST_ANALYSIS_ERROR",
                error_details={"error": str(e)}
            )

    async def get_guest_uploads(
        self,
        session_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0
    ) -> Union[SuccessResponse[List[GuestUploadResponse]], ErrorResponse]:

        try:
            uploads = await self.guest_service.get_guest_uploads(session_id, limit, offset)

            upload_responses = [
                self._create_upload_response(upload) for upload in uploads
            ]

            return SuccessResponse(
                message=f"Lấy {len(upload_responses)} uploads thành công",
                data=upload_responses
            )

        except Exception as e:
            logger.error(f"Failed to get guest uploads: {e}")
            return ErrorResponse(
                message="Không thể lấy danh sách uploads",
                error_code="GUEST_UPLOADS_ERROR",
                error_details={"error": str(e)}
            )

    async def get_guest_analyses(
        self,
        session_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0
    ) -> Union[SuccessResponse[List[GuestAnalysisResponse]], ErrorResponse]:

        try:
            analyses = await self.guest_service.get_guest_analyses(session_id, limit, offset)

            analysis_responses = [
                self._create_analysis_response(analysis) for analysis in analyses
            ]

            return SuccessResponse(
                message=f"Lấy {len(analysis_responses)} analyses thành công",
                data=analysis_responses
            )

        except Exception as e:
            logger.error(f"Failed to get guest analyses: {e}")
            return ErrorResponse(
                message="Không thể lấy danh sách analyses",
                error_code="GUEST_ANALYSES_ERROR",
                error_details={"error": str(e)}
            )

    async def get_guest_statistics(self) -> Union[SuccessResponse[GuestStatisticsResponse], ErrorResponse]:
        try:
            stats = await self.guest_service.get_guest_statistics()

            return SuccessResponse(
                message="Lấy thống kê guest thành công",
                data=GuestStatisticsResponse(**stats)
            )

        except Exception as e:
            logger.error(f"Failed to get guest statistics: {e}")
            return ErrorResponse(
                message="Không thể lấy thống kê guest",
                error_code="GUEST_STATISTICS_ERROR",
                error_details={"error": str(e)}
            )

    def _create_session_response(self, session: Dict[str, Any]) -> GuestSessionResponse:
        """Tạo GuestSessionResponse từ session data."""
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

    def _create_upload_response(self, upload: Dict[str, Any]) -> GuestUploadResponse:
        """Tạo GuestUploadResponse từ upload data."""
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

    def _create_analysis_response(self, analysis: Dict[str, Any]) -> GuestAnalysisResponse:
        """Tạo GuestAnalysisResponse từ analysis data."""
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