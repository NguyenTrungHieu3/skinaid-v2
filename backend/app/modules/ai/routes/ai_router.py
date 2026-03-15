import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import allow_guest, get_db
from app.modules.ai.dependencies import get_session_id
from app.modules.ai.mappers.response_mapper import ResponseMapper
from app.modules.ai.schemas.wound_analysis_schemas import (
    BatchAnalysisResponse,
    WoundAnalysisDetailResponse,
    WoundAnalysisListResponse,
    WoundAnalysisResponse,
)
from app.modules.ai.services.image_processing_service import ImageProcessingService
from app.modules.ai.services.wound_analysis_service import WoundAnalysisService
from app.modules.audit.audit_repository import AuditRepository
from app.modules.audit.services.audit_service import AuditService
from app.modules.auth.models.user import User
from app.modules.guest.service import GuestService
from app.shared.exceptions import (
    AppException,
    BadRequestError,
    ForbiddenError,
    InternalError,
    NotFoundError,
    UnauthorizedError,
)
from app.shared.response import SuccessResponse
from app.shared.constants import error_codes as ErrorCode
from app.shared.constants import messages as Message

router = APIRouter(prefix="/ai", tags=["AI Analysis"])
logger = logging.getLogger(__name__)


def get_wound_analysis_service(
    db: AsyncSession = Depends(get_db),
) -> WoundAnalysisService:
    return WoundAnalysisService(db)


def get_image_processing_service(
    db: AsyncSession = Depends(get_db),
) -> ImageProcessingService:
    return ImageProcessingService(db)


@router.post("/analyze", response_model=SuccessResponse)
async def analyze_wound_image(
    request: Request,
    file: UploadFile = File(..., description="Wound image (JPEG/PNG, max 5MB)"),
    current_user: Optional[User] = Depends(allow_guest),
    session_id: Optional[UUID] = Depends(get_session_id),
    db: AsyncSession = Depends(get_db),
    image_service: ImageProcessingService = Depends(get_image_processing_service),
):
    """Analyze wound image (user or guest)."""
    user_id = current_user.user_id if current_user else None

    if not user_id and not session_id:
        guest_service = GuestService(db)
        session_data = await guest_service.create_guest_session(
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("User-Agent"),
        )
        session_id = session_data["session_id"]

    logger.info(f"[ANALYZE] Starting - user: {user_id}, session: {session_id}")

    audit_repo = AuditRepository(db)
    audit_service = AuditService(audit_repo)

    try:
        result = await image_service.process_single_image(
            file=file,
            user_id=user_id,
            session_id=session_id,
        )

        try:
            await audit_service.log_event(
                action="upload_image",
                user_id=user_id,
                success=True,
                resource_type="wound_analysis",
                resource_id=(
                    str(result.data.analysis_id)
                    if hasattr(result.data, "analysis_id")
                    else None
                ),
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("User-Agent"),
                is_guest=user_id is None,
                guest_session_id=session_id if user_id is None else None,
                details={"file_name": file.filename, "content_type": file.content_type},
            )
        except Exception:
            pass

        return result

    except AppException as e:
        try:
            await audit_service.log_event(
                action="upload_image",
                user_id=user_id,
                success=False,
                error_message=e.message,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("User-Agent"),
                is_guest=user_id is None,
                guest_session_id=session_id if user_id is None else None,
            )
        except Exception:
            pass
        raise


@router.get("/history", response_model=SuccessResponse)
async def get_analysis_history(
    limit: int = 50,
    offset: int = 0,
    current_user: Optional[User] = Depends(allow_guest),
    session_id: Optional[UUID] = Depends(get_session_id),
    analysis_service: WoundAnalysisService = Depends(get_wound_analysis_service),
):
    """Get analysis history for user or guest session."""
    user_id = current_user.user_id if current_user else None

    if not user_id and not session_id:
        raise UnauthorizedError(
            message="Authentication or session_id required to view history"
        )

    logger.info(f"[GET_HISTORY] user: {user_id}, session: {session_id}")

    analyses = await analysis_service.get_history(
        user_id=user_id,
        session_id=session_id,
        limit=limit,
        offset=offset,
    )

    response_mapper = ResponseMapper()
    events = [
        response_mapper.map_wound_analysis(a, include_detections=False)
        for a in analyses
    ]

    response_data = WoundAnalysisListResponse(
        total=len(analyses),
        limit=limit,
        offset=offset,
        events=events,
    )

    return SuccessResponse(
        message=Message.AI_HISTORY_SUCCESS_MSG,
        data=response_data,
    )


@router.get("/analysis/{analysis_id}", response_model=SuccessResponse)
async def get_analysis_detail(
    analysis_id: UUID,
    current_user: Optional[User] = Depends(allow_guest),
    session_id: Optional[UUID] = Depends(get_session_id),
    analysis_service: WoundAnalysisService = Depends(get_wound_analysis_service),
):
    """Get detailed analysis result by ID."""
    user_id = current_user.user_id if current_user else None

    logger.info(f"[GET_DETAIL] {analysis_id}")

    analysis = await analysis_service.get_by_id(analysis_id)
    if not analysis:
        raise NotFoundError(
            message=Message.AI_ANALYSIS_NOT_FOUND_MSG,
            details={"analysis_id": str(analysis_id)},
        )

    if analysis.user_id:
        if not user_id or user_id != analysis.user_id:
            raise ForbiddenError(message=Message.AI_ACCESS_DENIED_MSG)
    elif analysis.session_id:
        if not session_id or session_id != analysis.session_id:
            raise ForbiddenError(message=Message.AI_ACCESS_DENIED_MSG)

    response_mapper = ResponseMapper()
    response_data = response_mapper.map_wound_analysis(
        analysis, include_detections=True
    )

    return SuccessResponse(
        message=Message.AI_DETAIL_SUCCESS_MSG,
        data=response_data,
    )


@router.delete("/analysis/{analysis_id}", response_model=SuccessResponse)
async def delete_analysis(
    request: Request,
    analysis_id: UUID,
    current_user: Optional[User] = Depends(allow_guest),
    session_id: Optional[UUID] = Depends(get_session_id),
    analysis_service: WoundAnalysisService = Depends(get_wound_analysis_service),
    db: AsyncSession = Depends(get_db),
):
    """Soft delete an analysis result."""
    user_id = current_user.user_id if current_user else None

    logger.info(f"[DELETE_ANALYSIS] {analysis_id}")

    analysis = await analysis_service.get_by_id(analysis_id)
    if not analysis:
        raise NotFoundError(
            message=Message.AI_ANALYSIS_NOT_FOUND_MSG,
            details={"analysis_id": str(analysis_id)},
        )

    if analysis.user_id:
        if not user_id or user_id != analysis.user_id:
            raise ForbiddenError(message=Message.AI_ACCESS_DENIED_MSG)
    elif analysis.session_id:
        if not session_id or session_id != analysis.session_id:
            raise ForbiddenError(message=Message.AI_ACCESS_DENIED_MSG)

    await analysis_service.soft_delete_analysis(analysis_id)

    try:
        audit_repo = AuditRepository(db)
        audit_service = AuditService(audit_repo)
        await audit_service.log_event(
            action="delete_analysis",
            user_id=user_id,
            success=True,
            resource_type="wound_analysis",
            resource_id=str(analysis_id),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("User-Agent"),
            is_guest=user_id is None,
            guest_session_id=session_id if user_id is None else None,
        )
    except Exception:
        pass

    return SuccessResponse(
        message=Message.AI_DELETE_SUCCESS_MSG,
        data={"analysis_id": str(analysis_id), "deleted": True},
    )


@router.post("/analyze/batch", response_model=SuccessResponse)
async def analyze_multiple_wound_images(
    request: Request,
    files: List[UploadFile] = File(
        ...,
        description="List of wound images (JPEG/PNG, max 5MB, max 5 images)",
    ),
    current_user: Optional[User] = Depends(allow_guest),
    session_id: Optional[UUID] = Depends(get_session_id),
    db: AsyncSession = Depends(get_db),
    image_service: ImageProcessingService = Depends(get_image_processing_service),
):
    """Analyze multiple wound images (max 5)."""
    user_id = current_user.user_id if current_user else None

    if len(files) == 0:
        raise BadRequestError(message="At least one image file is required")

    max_files = 5
    if len(files) > max_files:
        raise BadRequestError(
            message=f"Number of files exceeds limit ({max_files} files)",
            details={"max_files": max_files, "provided": len(files)},
        )

    if not user_id and not session_id:
        guest_service = GuestService(db)
        session_data = await guest_service.create_guest_session(
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("User-Agent"),
        )
        session_id = session_data["session_id"]

    result = await image_service.process_batch_images(
        files=files,
        user_id=user_id,
        session_id=session_id,
    )

    return SuccessResponse(
        message=f"Successfully analyzed {result.successful}/{result.total_files} images",
        data=result,
    )
