import logging
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Cookie, Header, Request, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional, List

from app.core.dependencies import allow_guest, get_db
from app.modules.auth.models.user import User

from app.modules.ai.services.wound_analysis_service import WoundAnalysisService
from app.modules.ai.services.image_processing_service import ImageProcessingService
from app.modules.audit.services.audit_service import AuditService
from app.modules.guest.service import GuestService

from app.shared.response import SuccessResponse, ErrorResponse
from app.modules.ai.schemas.wound_analysis_schemas import (
    WoundAnalysisResponse,
    WoundAnalysisListResponse,
    WoundAnalysisDetailResponse,
    BatchAnalysisResponse
)
from app.modules.ai.mappers.response_mapper import ResponseMapper
from app.utils.constants import error_codes as ErrorCode, messages as Message
from app.modules.ai.exceptions import WoundAnalysisNotFoundError

router = APIRouter(prefix="/ai", tags=["AI Analysis"])
logger = logging.getLogger(__name__)


def get_wound_analysis_service(db: AsyncSession = Depends(get_db)) -> WoundAnalysisService:
    return WoundAnalysisService(db)


def get_image_processing_service(db: AsyncSession = Depends(get_db)) -> ImageProcessingService:
    return ImageProcessingService(db)


def handle_service_response(result):
    """
    Handle response from service.
    If it's ErrorResponse, return JSONResponse with correct status code.
    """
    if isinstance(result, ErrorResponse):
        return JSONResponse(
            status_code=result.status_code,
            content=jsonable_encoder(result)
        )
    return result


async def get_session_id(
    session_id: Optional[str] = Cookie(None, alias="session_id"),
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
) -> Optional[UUID]:
    session_str = session_id or x_session_id

    if session_str:
        try:
            return UUID(session_str)
        except ValueError:
            raise HTTPException(
                status_code=400, detail="Invalid session_id format")

    return None


@router.post("/analyze")
async def analyze_wound_image(
    request: Request,
    file: UploadFile = File(...,
                            description="Wound image (JPEG/PNG, max 5MB)"),
    current_user: Optional[User] = Depends(allow_guest),
    session_id: Optional[UUID] = Depends(get_session_id),
    db: AsyncSession = Depends(get_db),
    image_service: ImageProcessingService = Depends(
        get_image_processing_service)
):
    user_id = current_user.user_id if current_user else None

    # Auto-create guest session if needed
    if not user_id and not session_id:
        guest_service = GuestService(db)
        session_data = await guest_service.create_guest_session(
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("User-Agent")
        )
        session_id = session_data["session_id"]

    logger.info(f"[ANALYZE] Starting - user: {user_id}, session: {session_id}")

    result = await image_service.process_single_image(
        file=file,
        user_id=user_id,
        session_id=session_id
    )

    # Audit logging
    audit_service = AuditService(db)
    if isinstance(result, SuccessResponse):
        await audit_service.log_event(
            action="upload_image",
            user_id=user_id,
            success=True,
            resource_type="wound_analysis",
            resource_id=str(result.data.analysis_id) if hasattr(
                result.data, 'analysis_id') else None,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("User-Agent"),
            is_guest=user_id is None,
            guest_session_id=session_id if user_id is None else None,
            details={"file_name": file.filename,
                     "content_type": file.content_type}
        )
    else:
        await audit_service.log_event(
            action="upload_image",
            user_id=user_id,
            success=False,
            error_message=result.message if isinstance(
                result, ErrorResponse) else "Upload failed",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("User-Agent"),
            is_guest=user_id is None,
            guest_session_id=session_id if user_id is None else None
        )

    return handle_service_response(result)


@router.get("/history")
async def get_analysis_history(
    limit: int = 50,
    offset: int = 0,
    current_user: Optional[User] = Depends(allow_guest),
    session_id: Optional[UUID] = Depends(get_session_id),
    analysis_service: WoundAnalysisService = Depends(
        get_wound_analysis_service)
):
    user_id = current_user.user_id if current_user else None

    if not user_id and not session_id:
        raise HTTPException(
            status_code=401,
            detail="Authentication or session_id required"
        )

    logger.info(f"[GET_HISTORY] user: {user_id}, session: {session_id}")

    try:
        analyses = await analysis_service.get_history(
            user_id=user_id,
            session_id=session_id,
            limit=limit,
            offset=offset
        )

        response_mapper = ResponseMapper()
        events = [response_mapper.map_wound_analysis(
            a, include_detections=False) for a in analyses]

        response_data = WoundAnalysisListResponse(
            # Note: Pagination total not implemented in service yet, using list length
            total=len(analyses),
            limit=limit,
            offset=offset,
            events=events
        )

        return SuccessResponse(
            message=Message.AI_HISTORY_SUCCESS_MSG,
            data=response_data,
            total=len(analyses)
        )
    except Exception as e:
        logger.error(f"[GET_HISTORY] Error: {e}", exc_info=True)
        return ErrorResponse(
            message=Message.AI_HISTORY_ERROR_MSG,
            error_code=ErrorCode.AI_HISTORY_ERROR,
            error_details={"error": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/analysis/{analysis_id}")
async def get_analysis_detail(
    analysis_id: UUID,
    current_user: Optional[User] = Depends(allow_guest),
    session_id: Optional[UUID] = Depends(get_session_id),
    analysis_service: WoundAnalysisService = Depends(
        get_wound_analysis_service)
):
    user_id = current_user.user_id if current_user else None

    logger.info(f"[GET_DETAIL] {analysis_id}")

    try:
        analysis = await analysis_service.get_by_id(analysis_id)

        if not analysis:
            return ErrorResponse(
                message=Message.AI_ANALYSIS_NOT_FOUND_MSG,
                error_code=ErrorCode.AI_ANALYSIS_NOT_FOUND,
                error_details={"analysis_id": str(analysis_id)},
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Access Check
        if analysis.user_id:
            if not user_id or user_id != analysis.user_id:
                return ErrorResponse(
                    message=Message.AI_ACCESS_DENIED_MSG,
                    error_code=ErrorCode.AI_ACCESS_DENIED,
                    status_code=status.HTTP_403_FORBIDDEN
                )
        elif analysis.session_id:
            if not session_id or session_id != analysis.session_id:
                return ErrorResponse(
                    message=Message.AI_ACCESS_DENIED_MSG,
                    error_code=ErrorCode.AI_ACCESS_DENIED,
                    status_code=status.HTTP_403_FORBIDDEN
                )

        response_mapper = ResponseMapper()
        response_data = response_mapper.map_wound_analysis(
            analysis, include_detections=True)

        return SuccessResponse(
            message=Message.AI_DETAIL_SUCCESS_MSG,
            data=response_data
        )

    except Exception as e:
        logger.error(f"[GET_DETAIL] Error: {e}", exc_info=True)
        return ErrorResponse(
            message=Message.AI_DETAIL_ERROR_MSG,
            error_code=ErrorCode.AI_DETAIL_ERROR,
            error_details={"error": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.delete("/analysis/{analysis_id}")
async def delete_analysis(
    request: Request,
    analysis_id: UUID,
    current_user: Optional[User] = Depends(allow_guest),
    session_id: Optional[UUID] = Depends(get_session_id),
    analysis_service: WoundAnalysisService = Depends(
        get_wound_analysis_service),
    db: AsyncSession = Depends(get_db)
):
    user_id = current_user.user_id if current_user else None

    logger.info(f"[DELETE_ANALYSIS] {analysis_id}")

    try:
        analysis = await analysis_service.get_by_id(analysis_id)

        if not analysis:
            return ErrorResponse(
                message=Message.AI_ANALYSIS_NOT_FOUND_MSG,
                error_code=ErrorCode.AI_ANALYSIS_NOT_FOUND,
                error_details={"analysis_id": str(analysis_id)},
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Access Check
        if analysis.user_id:
            if not user_id or user_id != analysis.user_id:
                return ErrorResponse(
                    message=Message.AI_ACCESS_DENIED_MSG,
                    error_code=ErrorCode.AI_ACCESS_DENIED,
                    status_code=status.HTTP_403_FORBIDDEN
                )
        elif analysis.session_id:
            if not session_id or session_id != analysis.session_id:
                return ErrorResponse(
                    message=Message.AI_ACCESS_DENIED_MSG,
                    error_code=ErrorCode.AI_ACCESS_DENIED,
                    status_code=status.HTTP_403_FORBIDDEN
                )

        await analysis_service.soft_delete_analysis(analysis_id)

        result = SuccessResponse(
            message=Message.AI_DELETE_SUCCESS_MSG,
            data={"analysis_id": str(analysis_id), "deleted": True}
        )

        # Audit log
        audit_service = AuditService(db)
        await audit_service.log_event(
            action="delete_analysis",
            user_id=user_id,
            success=True,
            resource_type="wound_analysis",
            resource_id=str(analysis_id),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("User-Agent"),
            is_guest=user_id is None,
            guest_session_id=session_id if user_id is None else None
        )

        return handle_service_response(result)

    except Exception as e:
        logger.error(f"[DELETE_ANALYSIS] Error: {e}", exc_info=True)
        return ErrorResponse(
            message=Message.AI_DELETE_ERROR_MSG,
            error_code=ErrorCode.AI_DELETE_ERROR,
            error_details={"error": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/analyze/batch")
async def analyze_multiple_wound_images(
    request: Request,
    files: List[UploadFile] = File(
        ...,
        description="List of wound images (JPEG/PNG, max 5MB, max 5 images)"
    ),
    current_user: Optional[User] = Depends(allow_guest),
    session_id: Optional[UUID] = Depends(get_session_id),
    db: AsyncSession = Depends(get_db),
    image_service: ImageProcessingService = Depends(
        get_image_processing_service)
):
    """
    Analyze multiple wound images in batch
    """
    user_id = current_user.user_id if current_user else None

    if len(files) == 0:
        return ErrorResponse(
            message="Please provide at least one file",
            error_code=ErrorCode.AI_INVALID_FILE,
            status_code=status.HTTP_400_BAD_REQUEST
        )

    max_files = 5
    if len(files) > max_files:
        return ErrorResponse(
            message=f"File count exceeds limit ({max_files} files)",
            error_code=ErrorCode.AI_INVALID_FILE,
            error_details={"max_files": max_files, "provided": len(files)},
            status_code=status.HTTP_400_BAD_REQUEST
        )

    if not user_id and not session_id:
        # Auto-create guest session for unauthenticated users
        guest_service = GuestService(db)
        session_data = await guest_service.create_guest_session(
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("User-Agent")
        )
        session_id = session_data["session_id"]

    result = await image_service.process_batch_images(
        files=files,
        user_id=user_id,
        session_id=session_id
    )

    return SuccessResponse(
        message=f"Analyzed {result.successful}/{result.total_files} images successfully",
        data=result
    )
