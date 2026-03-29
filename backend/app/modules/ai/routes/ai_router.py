from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import allow_guest, get_db
from app.modules.ai.dependencies import get_guest_session_id
from app.modules.ai.mappers.response_mapper import ResponseMapper
from app.modules.ai.schemas.wound_analysis_schemas import (
    BatchAnalysisResponse,
    WoundAnalysisDetailResponse,
    WoundAnalysisListResponse,
    WoundAnalysisResponse,
)
from app.modules.ai.services.analysis_orchestration_service import (
    AnalysisOrchestrationService,
)
from app.modules.ai.services.image_processing_service import ImageProcessingService
from app.modules.ai.services.wound_analysis_service import WoundAnalysisService
from app.modules.guest.repository import GuestRepository
from app.modules.guest.service import GuestService
from app.modules.audit.audit_repository import AuditRepository
from app.modules.audit.services.audit_service import AuditService
from app.modules.users.models.user import User
from app.shared.exceptions import (
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
)
from app.shared.response import SuccessResponse
from app.shared.constants import messages as Message

router = APIRouter(prefix="/ai", tags=["AI Analysis"])


def get_wound_analysis_service(
    db: AsyncSession = Depends(get_db),
) -> WoundAnalysisService:
    return WoundAnalysisService(db)


def get_image_processing_service(
    db: AsyncSession = Depends(get_db),
) -> ImageProcessingService:
    return ImageProcessingService(db)


def get_analysis_orchestration_service(
    db: AsyncSession = Depends(get_db),
    image_service: ImageProcessingService = Depends(get_image_processing_service),
) -> AnalysisOrchestrationService:
    guest_repo = GuestRepository(db)
    guest_service = GuestService(guest_repo, db)
    audit_repo = AuditRepository(db)
    audit_service = AuditService(audit_repo)
    return AnalysisOrchestrationService(
        image_service=image_service,
        guest_service=guest_service,
        audit_service=audit_service,
        db=db,
    )


@router.post("/analyze", response_model=SuccessResponse)
async def analyze_wound_image(
    request: Request,
    file: UploadFile = File(..., description="Wound image (JPEG/PNG, max 5MB)"),
    current_user: Optional[User] = Depends(allow_guest),
    guest_session_id: Optional[UUID] = Depends(get_guest_session_id),
    db: AsyncSession = Depends(get_db),
    orchestration_service: AnalysisOrchestrationService = Depends(
        get_analysis_orchestration_service
    ),
):
    """Analyze wound image (user or guest)."""
    user_id = current_user.user_id if current_user else None

    response_data = await orchestration_service.analyze_single_image(
        file=file,
        user_id=user_id,
        guest_session_id=guest_session_id,
        request=request,
    )

    return SuccessResponse(
        message=Message.AI_ANALYSIS_SUCCESS_MSG,
        data=response_data,
    )


@router.get("/history", response_model=SuccessResponse)
async def get_analysis_history(
    limit: int = 50,
    offset: int = 0,
    current_user: Optional[User] = Depends(allow_guest),
    guest_session_id: Optional[UUID] = Depends(get_guest_session_id),
    analysis_service: WoundAnalysisService = Depends(get_wound_analysis_service),
):
    """Get analysis history for user or guest session."""
    user_id = current_user.user_id if current_user else None

    if not user_id and not guest_session_id:
        raise UnauthorizedError(
            message="Authentication or guest_session_id required to view history"
        )

    analyses = await analysis_service.get_history(
        user_id=user_id,
        guest_session_id=guest_session_id,
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
    guest_session_id: Optional[UUID] = Depends(get_guest_session_id),
    analysis_service: WoundAnalysisService = Depends(get_wound_analysis_service),
):
    """Get detailed analysis result by ID."""
    user_id = current_user.user_id if current_user else None

    analysis = await analysis_service.get_by_id(analysis_id)
    if not analysis:
        raise NotFoundError(
            message=Message.AI_ANALYSIS_NOT_FOUND_MSG,
            details={"analysis_id": str(analysis_id)},
        )

    if analysis.user_id:
        if not user_id or user_id != analysis.user_id:
            raise ForbiddenError(message=Message.AI_ACCESS_DENIED_MSG)
    elif analysis.guest_session_id:
        if not guest_session_id or guest_session_id != analysis.guest_session_id:
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
    analysis_id: UUID,
    current_user: Optional[User] = Depends(allow_guest),
    guest_session_id: Optional[UUID] = Depends(get_guest_session_id),
    analysis_service: WoundAnalysisService = Depends(get_wound_analysis_service),
):
    """Soft delete an analysis result."""
    user_id = current_user.user_id if current_user else None

    analysis = await analysis_service.get_by_id(analysis_id)
    if not analysis:
        raise NotFoundError(
            message=Message.AI_ANALYSIS_NOT_FOUND_MSG,
            details={"analysis_id": str(analysis_id)},
        )

    if analysis.user_id:
        if not user_id or user_id != analysis.user_id:
            raise ForbiddenError(message=Message.AI_ACCESS_DENIED_MSG)
    elif analysis.guest_session_id:
        if not guest_session_id or guest_session_id != analysis.guest_session_id:
            raise ForbiddenError(message=Message.AI_ACCESS_DENIED_MSG)

    await analysis_service.soft_delete_analysis(analysis_id)

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
    guest_session_id: Optional[UUID] = Depends(get_guest_session_id),
    orchestration_service: AnalysisOrchestrationService = Depends(
        get_analysis_orchestration_service
    ),
):
    """Analyze multiple wound images (max 5)."""
    user_id = current_user.user_id if current_user else None

    if len(files) == 0:
        from app.shared.exceptions import BadRequestError
        from app.shared.constants import error_codes as ErrorCode

        raise BadRequestError(message="At least one image file is required")

    max_files = 5
    if len(files) > max_files:
        from app.shared.exceptions import BadRequestError

        raise BadRequestError(
            message=f"Number of files exceeds limit ({max_files} files)",
            details={"max_files": max_files, "provided": len(files)},
        )

    result = await orchestration_service.analyze_batch_images(
        files=files,
        user_id=user_id,
        guest_session_id=guest_session_id,
        request=request,
    )

    return SuccessResponse(
        message=f"Successfully analyzed {result.successful}/{result.total_files} images",
        data=result,
    )
