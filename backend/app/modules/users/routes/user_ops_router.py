from fastapi import APIRouter, Depends, Request, status
from uuid import UUID

from app.shared.response import SuccessResponse
from app.modules.users.dependencies import UserSvc, get_user_service
from app.modules.users.services.user_service import UserService
from app.modules.users.schemas.api import (
    CreateUserRequest,
    UpdateUserRequest,
    UpdateUserStatusRequest,
    UserDetailResponse
)
from app.core.dependencies import require_admin
from app.modules.users.models.user import User
from app.middleware.rate_limit import limiter

router = APIRouter(prefix="/admin/users")


@router.post(
    "",
    response_model=SuccessResponse[UserDetailResponse],
    summary="Tạo người dùng mới",
    description="Tạo một tài khoản người dùng mới",
    status_code=201
)
@limiter.limit("100/minute")
async def create_user(
    request: Request,
    user_data: CreateUserRequest,
    service: UserService = Depends(get_user_service),  # explicit — required by limiter decorator
    current_user: User = Depends(require_admin)
):
    """
    Tạo một tài khoản người dùng mới.
    Người dùng do admin tạo sẽ được tự động xác thực.
    """
    user_detail = await service.create_user(
        user_data=user_data,
        current_admin=current_user,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent")
    )
    return SuccessResponse(
        message="Tạo người dùng thành công",
        data=UserDetailResponse(user=user_detail)
    )


@router.get(
    "/{user_id}",
    response_model=SuccessResponse[UserDetailResponse],
    summary="Lấy chi tiết người dùng",
    description="Lấy thông tin chi tiết về một người dùng cụ thể"
)
async def get_user_detail(
    user_id: str,
    service: UserSvc,
    current_user: User = Depends(require_admin)
):
    """Lấy thông tin chi tiết về một người dùng cụ thể theo ID."""
    user_detail = await service.get_user_detail(UUID(user_id))
    if not user_detail:
        from app.shared.exceptions import NotFoundError
        raise NotFoundError(
            message=f"Không tìm thấy người dùng với ID {user_id}")

    return SuccessResponse(
        message="Lấy chi tiết người dùng thành công",
        data=UserDetailResponse(user=user_detail)
    )


@router.put(
    "/{user_id}",
    response_model=SuccessResponse[UserDetailResponse],
    summary="Cập nhật người dùng",
    description="Cập nhật thông tin người dùng"
)
async def update_user(
    request: Request,
    user_id: str,
    user_data: UpdateUserRequest,
    service: UserSvc,
    current_user: User = Depends(require_admin)
):
    """Cập nhật thông tin người dùng."""
    user_detail = await service.update_user(
        user_id=UUID(user_id),
        user_data=user_data,
        current_admin=current_user,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent")
    )
    return SuccessResponse(
        message="Cập nhật người dùng thành công",
        data=UserDetailResponse(user=user_detail)
    )


@router.patch(
    "/{user_id}/status",
    response_model=SuccessResponse[UserDetailResponse],
    summary="Cập nhật trạng thái người dùng",
    description="Cập nhật trạng thái hoạt động/không hoạt động của người dùng"
)
async def update_user_status(
    request: Request,
    user_id: str,
    status_data: UpdateUserStatusRequest,
    service: UserSvc,
    current_user: User = Depends(require_admin)
):
    """Cập nhật trạng thái hoạt động/không hoạt động của người dùng."""
    user_detail = await service.update_user_status(
        user_id=UUID(user_id),
        is_active=status_data.is_active,
        current_admin=current_user,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent")
    )

    vn_status_text = "kích hoạt" if status_data.is_active else "vô hiệu hóa"
    return SuccessResponse(
        message=f"Người dùng đã được {vn_status_text} thành công",
        data=UserDetailResponse(user=user_detail)
    )


@router.delete(
    "/{user_id}",
    response_model=SuccessResponse,
    summary="Xóa người dùng",
    description="Xóa tài khoản người dùng (soft delete)"
)
async def delete_user(
    request: Request,
    user_id: str,
    service: UserSvc,
    current_user: User = Depends(require_admin)
):
    """Xóa tài khoản người dùng (soft delete)."""
    await service.delete_user(
        user_id=UUID(user_id),
        current_admin=current_user,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent")
    )
    return SuccessResponse(
        message="Xóa người dùng thành công",
        data={"user_id": user_id}
    )


@router.post(
    "/{user_id}/resend-verification",
    response_model=SuccessResponse,
    summary="Gửi lại email xác thực",
    description="Gửi lại email xác thực cho người dùng chưa xác thực"
)
async def resend_verification_email(
    request: Request,
    user_id: str,
    service: UserSvc,
    current_user: User = Depends(require_admin)
):
    """Gửi lại email xác thực cho người dùng."""
    await service.resend_verification_email(
        user_id=UUID(user_id),
        current_admin=current_user,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent")
    )
    return SuccessResponse(
        message="Gửi email xác thực thành công",
        data={"user_id": user_id}
    )
