from fastapi import APIRouter, Depends, UploadFile, File, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.upload.controllers.upload_controller import UploadController
from app.modules.upload.schemas.upload_schemas import (
    UploadParams,
    UploadResponse,
    ValidationResult
)
from app.api.v1.deps import get_current_user
from app.shared.schemas.response import SuccessResponse

router = APIRouter()


def get_upload_controller(db: AsyncSession = Depends(get_db)) -> UploadController:
    """Khởi tạo và trả về instance của UploadController sử dụng kết nối cơ sở dữ liệu hiện tại."""
    return UploadController(db)


@router.post(
    "/file",
    response_model=SuccessResponse[UploadResponse],
    summary="Upload file",
    description="Upload file với xử lý ảnh tự động. Yêu cầu đăng nhập."
)
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    params: UploadParams = Depends(),
    controller: UploadController = Depends(get_upload_controller),
    current_user = Depends(get_current_user)
) -> SuccessResponse[UploadResponse]:
    """
    Upload tệp (yêu cầu xác thực).

    - Định dạng hỗ trợ: JPEG, PNG
    - Kích thước tối đa: 5MB
    - Tự động resize, xoay đúng hướng, nén tối ưu
    """
    content = await file.read()
    
    return await controller.upload_file(
        file_content=content,
        file_name=file.filename,
        mime_type=file.content_type or "application/octet-stream",
        request=request,
        user_id=str(current_user.user_id),
        purpose=params.purpose,
        quality=params.quality
    )


@router.post(
    "/guest",
    response_model=SuccessResponse[UploadResponse],
    summary="Guest upload",
    description="Upload file cho guest (không cần đăng nhập)."
)
async def guest_upload(
    request: Request,
    file: UploadFile = File(...),
    controller: UploadController = Depends(get_upload_controller)
) -> SuccessResponse[UploadResponse]:
    """
    Upload tệp cho khách (không yêu cầu đăng nhập).

    - Xử lý tương tự như upload đã đăng nhập
    - Tệp có thể bị xóa sau 24 giờ
    """
    content = await file.read()
    
    return await controller.upload_file(
        file_content=content,
        file_name=file.filename,
        mime_type=file.content_type or "application/octet-stream",
        request=request,
        user_id=None,
        purpose="general"
    )


@router.post(
    "/validate",
    response_model=SuccessResponse[ValidationResult],
    summary="Validate file",
    description="Kiểm tra file hợp lệ không, không upload."
)
async def validate_file(
    file: UploadFile = File(...),
    controller: UploadController = Depends(get_upload_controller)
) -> SuccessResponse[ValidationResult]:
    """
    Xác thực tệp mà không thực hiện upload.

    Trả về kết quả xác thực bao gồm danh sách lỗi và cảnh báo (nếu có).
    """
    content = await file.read()
    
    return await controller.validate_file(
        file_content=content,
        file_name=file.filename,
        mime_type=file.content_type or "application/octet-stream"
    )


@router.get(
    "/health",
    summary="Health check"
)
async def health_check():
    """Endpoint kiểm tra tình trạng hoạt động của dịch vụ upload."""
    return {
        "service": "upload",
        "status": "healthy"
    }