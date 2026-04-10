from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai.schemas.wound_analysis_schemas import (
    BatchAnalysisResponse,
    WoundAnalysisResponse,
)
from app.modules.ai.services.image_processing_service import ImageProcessingService
from app.modules.guest.repository import GuestRepository
from app.modules.guest.service import GuestService
from app.modules.guest.schemas.api import CreateGuestSessionRequest
from app.modules.audit.audit_repository import AuditRepository
from app.modules.audit.services.audit_service import AuditService


class AnalysisOrchestrationService:
    def __init__(
        self,
        image_service: ImageProcessingService,
        guest_service: GuestService,
        audit_service: AuditService,
        db: AsyncSession,
    ):
        self.image_service = image_service
        self.guest_service = guest_service
        self.audit_service = audit_service
        self.db = db

    async def _ensure_session(
        self,
        user_id: Optional[UUID],
        guest_session_id: Optional[UUID],
        request: Request,
    ) -> tuple[Optional[UUID], Optional[UUID]]:
        """Create guest session if user_id and guest_session_id are both None,
        or if guest_session_id is stale (not found in DB)."""
        if user_id:
            return user_id, None

        # Validate existing guest_session_id
        if guest_session_id:
            try:
                await self.guest_service.get_session(guest_session_id)
                return user_id, guest_session_id
            except Exception:
                # Session expired or not found — create a new one
                pass

        session_data = await self.guest_service.create_session(
            CreateGuestSessionRequest(
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("User-Agent"),
            )
        )
        return user_id, session_data.session_id

    async def _log_audit(
        self,
        action: str,
        user_id: Optional[UUID],
        guest_session_id: Optional[UUID],
        success: bool,
        request: Request,
        resource_id: Optional[UUID] = None,
        error_message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        log_type: Optional[str] = None,
        level: Optional[str] = None,
        description: Optional[str] = None,
    ) -> None:
        """Log audit event (non-blocking)."""
        try:
            await self.audit_service.log_event(
                action=action,
                user_id=user_id,
                success=success,
                resource_type="wound_analysis",
                resource_id=str(resource_id) if resource_id else None,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("User-Agent"),
                is_guest=user_id is None,
                guest_session_id=guest_session_id if user_id is None else None,
                error_message=error_message,
                details=details,
                log_type=log_type,
                level=level,
                description=description,
            )
        except Exception:
            pass

    async def analyze_single_image(
        self,
        file: UploadFile,
        user_id: Optional[UUID],
        guest_session_id: Optional[UUID],
        request: Request,
    ) -> WoundAnalysisResponse:
        """
        Process single wound image with automatic session management.
        """
        user_id, guest_session_id = await self._ensure_session(
            user_id, guest_session_id, request
        )

        result = await self.image_service.process_single_image(
            file=file,
            user_id=user_id,
            guest_session_id=guest_session_id,
        )

        await self._log_audit(
            action="wound_scan",
            user_id=user_id,
            guest_session_id=guest_session_id,
            success=True,
            request=request,
            resource_id=result.data.analysis_id if hasattr(result.data, "analysis_id") else None,
            details={"file_name": file.filename, "content_type": file.content_type},
            description=f"Wound image scanned: {file.filename}",
        )

        return result.data

    async def analyze_batch_images(
        self,
        files: List[UploadFile],
        user_id: Optional[UUID],
        guest_session_id: Optional[UUID],
        request: Request,
    ) -> BatchAnalysisResponse:
        """
        Process multiple wound images with automatic session management.
        """
        user_id, guest_session_id = await self._ensure_session(
            user_id, guest_session_id, request
        )

        return await self.image_service.process_batch_images(
            files=files,
            user_id=user_id,
            guest_session_id=guest_session_id,
        )
