from fastapi import APIRouter, Depends, UploadFile, File, Form, Request, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Union, List
import logging

from app.shared.schemas.response import SuccessResponse, ErrorResponse
from app.modules.upload.controllers.upload_controllers import UploadController
from app.modules.upload.schemas.upload import WoundImageDetail
from app.modules.upload.schemas.validation import UploadValidationCreate, UploadValidationResponse
from app.api.v1.deps import get_db, get_current_active_user
from app.modules.auth.models.user import User
from app.utils.constants.error_codes import FILE_UPLOAD_FAILED

router = APIRouter(prefix="/upload", tags=["Image Upload"])

logger = logging.getLogger(__name__)

async def get_upload_controller(db: AsyncSession = Depends(get_db)) -> UploadController:
    return UploadController(db)

@router.post(
    "/image",
    summary="Upload wound image",
    description="Upload a wound image"
)
async def upload_image(
    request: Request,
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    controller: UploadController = Depends(get_upload_controller),
    current_user: User = Depends(get_current_active_user)
):
    try:
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        result = await controller.upload_image(
            user_id=str(current_user.user_id),
            file=file,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return result
    except Exception as e:
        logger.error(f"Error uploading image: {str(e)}")
        return ErrorResponse(
            message="Failed to upload image",
            error_code=FILE_UPLOAD_FAILED,
            error_details=None
        )


@router.get(
    "/image/{image_id}",
    response_model=Union[SuccessResponse[WoundImageDetail], ErrorResponse],
    summary="Get wound image details",
    description="Retrieve wound image details"
)
async def get_image_analysis(
    image_id: str,
    controller: UploadController = Depends(get_upload_controller),
    current_user: User = Depends(get_current_active_user)
):
    try:
        result = await controller.get_image_analysis(image_id, str(current_user.user_id))  # Using user_id as woundhistory_id for now
        return result
    except Exception as e:
        logger.error(f"Error getting image analysis: {str(e)}")
        return ErrorResponse(
            message="Failed to retrieve image analysis",
            error_code="IMAGE_NOT_FOUND",
            error_details=None
        )


@router.get(
    "/images",
    summary="Get user's wound images",
    description="Retrieve all wound images uploaded by the current user"
)
async def get_user_images(
    limit: int = 20,
    offset: int = 0,
    controller: UploadController = Depends(get_upload_controller),
    current_user: User = Depends(get_current_active_user)
):
    try:
        result = await controller.get_user_images(
            user_id=str(current_user.user_id), 
            limit=limit,
            offset=offset
        )
        return result
    except Exception as e:
        logger.error(f"Error getting user images: {str(e)}")
        return ErrorResponse(
            message="Failed to retrieve user images",
            error_code="IMAGES_RETRIEVAL_FAILED",
            error_details=None
        )

@router.post(
    "/validation/record",
    response_model=SuccessResponse[UploadValidationResponse],
    summary="Tạo bản ghi validation",
    description="Tạo bản ghi validation mới để theo dõi quá trình xác thực file"
)
async def create_validation_record(
    validation_data: UploadValidationCreate,
    request: Request,
    controller: UploadController = Depends(get_upload_controller),
    current_user: User = Depends(get_current_active_user)
):
    """
    Tạo bản ghi validation mới

    - **validation_data**: Thông tin validation cần ghi nhận
    - **request**: Request object để lấy IP và User-Agent
    - **current_user**: User hiện tại đang đăng nhập
    """
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")

    return await controller.create_validation_record(
        validation_data=validation_data,
        current_user=current_user,
        ip_address=ip_address,
        user_agent=user_agent
    )


@router.get(
    "/validation/my-records",
    response_model=SuccessResponse[List[UploadValidationResponse]],
    summary="Lấy danh sách validation records của tôi",
    description="Lấy danh sách tất cả validation records của user hiện tại"
)
async def get_my_validation_records(
    limit: int = Query(20, description="Số lượng records tối đa", le=100),
    offset: int = Query(0, description="Số records bỏ qua", ge=0),
    controller: UploadController = Depends(get_upload_controller),
    current_user: User = Depends(get_current_active_user)
):
    """
    Lấy danh sách validation records của user hiện tại

    - **limit**: Số lượng records tối đa (default: 20, max: 100)
    - **offset**: Số records bỏ qua (default: 0)
    - **current_user**: User hiện tại đang đăng nhập
    """
    return await controller.get_user_validations(
        current_user=current_user,
        limit=limit,
        offset=offset
    )