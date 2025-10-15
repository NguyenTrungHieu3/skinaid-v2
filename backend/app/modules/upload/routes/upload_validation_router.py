from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional, List
import logging

from app.shared.schemas.response import SuccessResponse, ErrorResponse
from app.modules.upload.schemas.validation import (
    UploadValidationCreate,
    UploadValidationResponse
)
from app.modules.upload.controllers.upload_validation_controller import UploadValidationController
from app.api.v1.deps import get_db, get_current_active_user
from app.modules.auth.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/validation", tags=["Upload Validation"])


async def get_validation_controller(db: AsyncSession = Depends(get_db)) -> UploadValidationController:
    """Dependency để inject UploadValidationController"""
    return UploadValidationController(db)


@router.post(
    "/record",
    response_model=SuccessResponse[UploadValidationResponse],
    summary="Tạo bản ghi validation",
    description="Tạo bản ghi validation mới để theo dõi quá trình xác thực file"
)
async def create_validation_record(
    validation_data: UploadValidationCreate,
    request: Request,
    controller: UploadValidationController = Depends(get_validation_controller),
    current_user: User = Depends(get_current_active_user)
):
    """
    Tạo bản ghi validation mới

    - **validation_data**: Thông tin validation cần ghi nhận
    - **request**: Request object để lấy IP và User-Agent
    - **current_user**: User hiện tại đang đăng nhập
    """
    # Lấy thông tin từ request headers
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")

    return await controller.create_validation_record(
        validation_data=validation_data,
        current_user=current_user,
        ip_address=ip_address,
        user_agent=user_agent
    )


@router.get(
    "/record/{validation_id}",
    response_model=SuccessResponse[UploadValidationResponse],
    summary="Lấy thông tin validation theo ID",
    description="Lấy thông tin chi tiết của một validation record"
)
async def get_validation_by_id(
    validation_id: str,
    controller: UploadValidationController = Depends(get_validation_controller),
    current_user: User = Depends(get_current_active_user)
):
    """
    Lấy thông tin validation theo ID

    - **validation_id**: ID của validation record cần lấy
    - **current_user**: User hiện tại đang đăng nhập (chỉ lấy được record của chính mình)
    """
    return await controller.get_validation_by_id(
        validation_id=validation_id,
        current_user=current_user
    )


@router.get(
    "/record/request/{request_id}",
    response_model=SuccessResponse[UploadValidationResponse],
    summary="Lấy thông tin validation theo request ID",
    description="Lấy thông tin validation dựa trên request ID"
)
async def get_validation_by_request_id(
    request_id: str,
    controller: UploadValidationController = Depends(get_validation_controller),
    current_user: User = Depends(get_current_active_user)
):
    """
    Lấy thông tin validation theo request ID

    - **request_id**: ID của request cần tìm
    - **current_user**: User hiện tại đang đăng nhập (chỉ lấy được record của chính mình)
    """
    return await controller.get_validation_by_request_id(
        request_id=request_id,
        current_user=current_user
    )


@router.get(
    "/my-records",
    response_model=SuccessResponse[List[UploadValidationResponse]],
    summary="Lấy danh sách validation records của tôi",
    description="Lấy danh sách tất cả validation records của user hiện tại"
)
async def get_my_validation_records(
    limit: int = Query(20, description="Số lượng records tối đa", le=100),
    offset: int = Query(0, description="Số records bỏ qua", ge=0),
    controller: UploadValidationController = Depends(get_validation_controller),
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


@router.put(
    "/record/{validation_id}/attempt",
    response_model=SuccessResponse[UploadValidationResponse],
    summary="Cập nhật validation attempt",
    description="Cập nhật thông tin một lần thử validation"
)
async def update_validation_attempt(
    validation_id: str,
    validation_passed: bool = Query(..., description="Kết quả validation"),
    controller: UploadValidationController = Depends(get_validation_controller),
    current_user: User = Depends(get_current_active_user)
):
    """
    Cập nhật thông tin validation attempt

    - **validation_id**: ID của validation record cần cập nhật
    - **validation_passed**: Kết quả validation (true/false)
    - **current_user**: User hiện tại đang đăng nhập
    """
    return await controller.update_validation_attempt(
        validation_id=validation_id,
        validation_passed=validation_passed,
        current_user=current_user
    )


@router.get(
    "/stats",
    response_model=SuccessResponse[Dict[str, Any]],
    summary="Lấy thống kê validation",
    description="Lấy thống kê tổng quan về các validation records của user"
)
async def get_validation_stats(
    controller: UploadValidationController = Depends(get_validation_controller),
    current_user: User = Depends(get_current_active_user)
):
    """
    Lấy thống kê validation của user hiện tại

    - **current_user**: User hiện tại đang đăng nhập

    Trả về thống kê bao gồm:
    - Tổng số validation records
    - Số records thành công/thất bại
    - Tỷ lệ thành công
    """
    try:
        # Lấy tất cả validation records của user
        all_records = await controller.get_user_validations(
            current_user=current_user,
            limit=1000  # Lấy tối đa để tính thống kê
        )

        if isinstance(all_records.data, SuccessResponse):
            records = all_records.data.data
        else:
            records = all_records.data

        total_records = len(records)
        successful_records = sum(1 for record in records if record.validation_passed)
        failed_records = total_records - successful_records
        success_rate = (successful_records / total_records * 100) if total_records > 0 else 0

        stats = {
            "total_records": total_records,
            "successful_records": successful_records,
            "failed_records": failed_records,
            "success_rate": round(success_rate, 2)
        }

        return SuccessResponse(
            message="Lấy thống kê validation thành công",
            data=stats
        )

    except Exception as e:
        logger.error(f"Failed to get validation stats for {current_user.user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Không thể lấy thống kê validation"
        )