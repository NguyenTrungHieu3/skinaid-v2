from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Cookie, Header, Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlmodel.ext.asyncio.session import AsyncSession
from uuid import UUID
from typing import Optional, List

from app.core.dependencies import allow_guest, get_db
from app.modules.auth.models.user import User
from app.modules.ai.controllers.ai_controller import AIController
from app.modules.audit.services.audit_service import AuditService
from app.shared.schemas.response import SuccessResponse, ErrorResponse
from app.modules.guest.services.guest_service import GuestService

router = APIRouter(prefix="/ai")


def handle_controller_response(result):
    """
    Xử lý response từ controller.
    Nếu là ErrorResponse, trả về JSONResponse với status_code đúng.
    """
    if isinstance(result, ErrorResponse):
        return JSONResponse(
            status_code=result.status_code,
            content=jsonable_encoder(result)
        )
    return jsonable_encoder(result)

import logging
logger = logging.getLogger(__name__)

async def get_session_id(
    session_id: Optional[str] = Cookie(None, alias="session_id"),
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
) -> Optional[UUID]:
    session_str = session_id or x_session_id
    
    logger.info(f"[GET_SESSION_ID] Cookie session_id: {session_id}")
    logger.info(f"[GET_SESSION_ID] Header X-Session-ID: {x_session_id}")
    logger.info(f"[GET_SESSION_ID] Using session_str: {session_str}")

    if session_str:
        try:
            parsed_session = UUID(session_str)
            logger.info(f"[GET_SESSION_ID] Parsed session UUID: {parsed_session}")
            return parsed_session
        except ValueError:
            raise HTTPException(status_code=400, detail="Định dạng session_id không hợp lệ")

    logger.warning("[GET_SESSION_ID] No session_id provided!")
    return None

@router.post("/analyze")
async def analyze_wound_image(
    request: Request,
    file: UploadFile = File(..., description="Ảnh vết thương (JPEG/PNG, tối đa 5MB)"),
    current_user: Optional[User] = Depends(allow_guest),
    session_id: Optional[UUID] = Depends(get_session_id),
    db: AsyncSession = Depends(get_db)
):
    controller = AIController(db)

    user_id = current_user.user_id if current_user else None
    if not user_id and not session_id:
        guest_service = GuestService(db)
        session_data = await guest_service.create_guest_session(
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("User-Agent")
        )
        session_id = session_data["session_id"]

    result = await controller.analyze_image(
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
            resource_id=str(result.data.analysis_id) if hasattr(result.data, 'analysis_id') else None,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("User-Agent"),
            is_guest=user_id is None,
            guest_session_id=session_id if user_id is None else None,
            details={"file_name": file.filename, "content_type": file.content_type}
        )
    else:
        await audit_service.log_event(
            action="upload_image",
            user_id=user_id,
            success=False,
            error_message=result.message if isinstance(result, ErrorResponse) else "Upload thất bại",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("User-Agent"),
            is_guest=user_id is None,
            guest_session_id=session_id if user_id is None else None
        )

    return handle_controller_response(result)

@router.get("/history")
async def get_analysis_history(
    limit: int = 50,
    offset: int = 0,
    current_user: Optional[User] = Depends(allow_guest),
    session_id: Optional[UUID] = Depends(get_session_id),
    db: AsyncSession = Depends(get_db)
):
    controller = AIController(db)

    user_id = current_user.user_id if current_user else None

    if not user_id and not session_id:
        raise HTTPException(
            status_code=401,
            detail="Yêu cầu xác thực hoặc session_id phải được cung cấp"
        )

    result = await controller.get_analysis_history(
        user_id=user_id,
        session_id=session_id,
        limit=limit,
        offset=offset
    )

    return handle_controller_response(result)

@router.get("/analysis/{analysis_id}")
async def get_analysis_detail(
    analysis_id: UUID,
    current_user: Optional[User] = Depends(allow_guest),
    session_id: Optional[UUID] = Depends(get_session_id),
    db: AsyncSession = Depends(get_db)
):
    controller = AIController(db)

    user_id = current_user.user_id if current_user else None

    result = await controller.get_analysis_detail(
        analysis_id=analysis_id,
        user_id=user_id,
        session_id=session_id
    )

    return handle_controller_response(result)

@router.delete("/analysis/{analysis_id}")
async def delete_analysis(
    request: Request,
    analysis_id: UUID,
    current_user: Optional[User] = Depends(allow_guest),
    session_id: Optional[UUID] = Depends(get_session_id),
    db: AsyncSession = Depends(get_db)
):
    controller = AIController(db)

    user_id = current_user.user_id if current_user else None

    result = await controller.delete_analysis(
        analysis_id=analysis_id,
        user_id=user_id,
        session_id=session_id
    )
    
    audit_service = AuditService(db)
    await audit_service.log_event(
        action="delete_analysis",
        user_id=user_id,
        success=isinstance(result, SuccessResponse),
        resource_type="wound_analysis",
        resource_id=str(analysis_id),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
        is_guest=user_id is None,
        guest_session_id=session_id if user_id is None else None,
        error_message=result.message if isinstance(result, ErrorResponse) else None
    )

    return handle_controller_response(result)

@router.post("/analyze/batch")
async def analyze_multiple_wound_images(
    files: List[UploadFile] = File(
        ...,
        description="Danh sách ảnh vết thương (JPEG/PNG, mỗi ảnh max 5MB, tối đa 10 ảnh)"
    ),
    current_user: Optional[User] = Depends(allow_guest),
    session_id: Optional[UUID] = Depends(get_session_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Phân tích nhiều ảnh vết thương cùng lúc
    """
    controller = AIController(db)
    
    user_id = current_user.user_id if current_user else None
    
    if not user_id and not session_id:
        # Auto-create guest session for unauthenticated users
        guest_service = GuestService(db)
        session_data = await guest_service.create_guest_session(
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("User-Agent")
        )
        session_id = session_data["session_id"]
    
    result = await controller.analyze_multiple_images(
        files=files,
        user_id=user_id,
        session_id=session_id,
        max_files=5 
    )
    
    return handle_controller_response(result)