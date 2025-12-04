from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.shared.schemas.response import SuccessResponse
from app.modules.admin.controllers.user_management_controller import UserManagementController
from app.modules.admin.schemas.user_management_schemas import (
    CreateUserRequest,
    UpdateUserRequest,
    UpdateUserStatusRequest,
    UserListResponse,
    UserDetailResponse,
    UserStatsResponse
)
from app.core.dependencies import get_db, require_admin
from app.modules.auth.models.user import User
from app.core.rate_limit import limiter

router = APIRouter(prefix="/admin/users", tags=["Admin - User Management"])


async def get_user_controller(db: AsyncSession = Depends(get_db)) -> UserManagementController:
    """Dependency để lấy user management controller instance"""
    return UserManagementController(db)


@router.get(
    "",
    response_model=SuccessResponse[UserListResponse],
    response_model=SuccessResponse[UserListResponse],
    summary="Lấy danh sách người dùng",
    description="Lấy danh sách người dùng có phân trang với các bộ lọc tùy chọn"
)
async def get_users(
    page: int = Query(1, ge=1, description="Số trang (bắt đầu từ 1)"),
    limit: int = Query(10, ge=1, le=100, description="Số lượng người dùng mỗi trang"),
    search: Optional[str] = Query(None, description="Tìm kiếm theo email hoặc tên hiển thị"),
    role: Optional[str] = Query(None, description="Lọc theo vai trò (user, moderator, admin)"),
    status: Optional[str] = Query(None, description="Lọc theo trạng thái (active, inactive)"),
    controller: UserManagementController = Depends(get_user_controller),
    current_user: User = Depends(require_admin)
):
    """
    Lấy danh sách người dùng có phân trang với các bộ lọc:
    - **page**: Số trang (bắt đầu từ 1)
    - **limit**: Số bản ghi mỗi trang (1-100)
    - **search**: Tìm kiếm trong email và tên hiển thị
    - **role**: Lọc theo vai trò (user, moderator, admin)
    - **status**: Lọc theo trạng thái (active, inactive)
    
    **Yêu cầu quyền admin**
    """
    return await controller.get_users(
        page=page,
        limit=limit,
        search=search,
        role=role,
        status=status
    )


@router.get(
    "/stats",
    response_model=SuccessResponse[UserStatsResponse],
    response_model=SuccessResponse[UserStatsResponse],
    summary="Lấy thống kê người dùng",
    description="Lấy thống kê tổng quan về người dùng"
)
async def get_user_stats(
    controller: UserManagementController = Depends(get_user_controller),
    current_user: User = Depends(require_admin)
):
    """
    Lấy thống kê tổng quan về người dùng:
    - Tổng số người dùng
    - Người dùng đang hoạt động
    - Người dùng đã xác thực
    - Người dùng theo vai trò
    
    **Yêu cầu quyền admin**
    """
    return await controller.get_user_stats()


@router.get(
    "/{user_id}",
    response_model=SuccessResponse[UserDetailResponse],
    response_model=SuccessResponse[UserDetailResponse],
    summary="Lấy chi tiết người dùng",
    description="Lấy thông tin chi tiết về một người dùng cụ thể"
)
async def get_user_detail(
    user_id: str,
    controller: UserManagementController = Depends(get_user_controller),
    current_user: User = Depends(require_admin)
):
    """
    Lấy thông tin chi tiết về một người dùng cụ thể theo ID.
    
    **Yêu cầu quyền admin**
    """
    return await controller.get_user_detail(user_id)


@router.post(
    "",
    response_model=SuccessResponse[UserDetailResponse],
    response_model=SuccessResponse[UserDetailResponse],
    summary="Tạo người dùng mới",
    description="Tạo một tài khoản người dùng mới",
    status_code=201
)
@limiter.limit("100/minute")
async def create_user(
    request: Request,
    user_data: CreateUserRequest,
    controller: UserManagementController = Depends(get_user_controller),
    current_user: User = Depends(require_admin)
):
    """
    Tạo một tài khoản người dùng mới với các thông tin sau:
    - **email**: Địa chỉ email hợp lệ (duy nhất)
    - **display_name**: Tên hiển thị của người dùng (2-100 ký tự)
    - **password**: Mật khẩu (tối thiểu 6 ký tự)
    - **role**: Vai trò người dùng (user, moderator, admin)
    
    Người dùng do admin tạo sẽ được tự động xác thực.
    
    **Giới hạn tốc độ**: 100 yêu cầu mỗi phút
    **Yêu cầu quyền admin**
    """
    return await controller.create_user(user_data)


@router.put(
    "/{user_id}",
    response_model=SuccessResponse[UserDetailResponse],
    response_model=SuccessResponse[UserDetailResponse],
    summary="Cập nhật người dùng",
    description="Cập nhật thông tin người dùng"
)
async def update_user(
    user_id: str,
    user_data: UpdateUserRequest,
    controller: UserManagementController = Depends(get_user_controller),
    current_user: User = Depends(require_admin)
):
    """
    Cập nhật thông tin người dùng. Tất cả các trường đều là tùy chọn:
    - **display_name**: Cập nhật tên hiển thị
    - **email**: Cập nhật email (phải là duy nhất)
    - **role**: Cập nhật vai trò (user, moderator, admin)
    - **is_active**: Cập nhật trạng thái hoạt động
    
    **Yêu cầu quyền admin**
    """
    return await controller.update_user(user_id, user_data)


@router.patch(
    "/{user_id}/status",
    response_model=SuccessResponse[UserDetailResponse],
    response_model=SuccessResponse[UserDetailResponse],
    summary="Cập nhật trạng thái người dùng",
    description="Cập nhật trạng thái hoạt động/không hoạt động của người dùng"
)
async def update_user_status(
    user_id: str,
    status_data: UpdateUserStatusRequest,
    controller: UserManagementController = Depends(get_user_controller),
    current_user: User = Depends(require_admin)
):
    """
    Cập nhật trạng thái hoạt động/không hoạt động của người dùng.
    
    Đặt is_active thành False sẽ vô hiệu hóa tài khoản người dùng.
    
    **Yêu cầu quyền admin**
    """
    return await controller.update_user_status(user_id, status_data)


@router.delete(
    "/{user_id}",
    response_model=SuccessResponse,
    response_model=SuccessResponse,
    summary="Xóa người dùng",
    description="Xóa tài khoản người dùng (soft delete)"
)
async def delete_user(
    user_id: str,
    controller: UserManagementController = Depends(get_user_controller),
    current_user: User = Depends(require_admin)
):
    """
    Xóa tài khoản người dùng (soft delete).
    
    Hành động này đặt trạng thái is_active của người dùng thành False thay vì xóa vĩnh viễn bản ghi.
    
    **Yêu cầu quyền admin**
    """
    return await controller.delete_user(user_id)


@router.post(
    "/{user_id}/resend-verification",
    response_model=SuccessResponse,
    response_model=SuccessResponse,
    summary="Gửi lại email xác thực",
    description="Gửi lại email xác thực cho người dùng chưa xác thực"
)
async def resend_verification_email(
    user_id: str,
    controller: UserManagementController = Depends(get_user_controller),
    current_user: User = Depends(require_admin)
):
    """
    Gửi lại email xác thực cho người dùng.
    
    Endpoint này sẽ:
    - Kiểm tra xem người dùng có tồn tại và chưa được xác thực không
    - Tạo token xác thực mới
    - Gửi email xác thực
    
    **Yêu cầu quyền admin**
    """
    return await controller.resend_verification_email(user_id)


@router.get(
    "/health/check",
    response_model=SuccessResponse[dict],
    response_model=SuccessResponse[dict],
    summary="Kiểm tra sức khỏe dịch vụ quản lý người dùng",
    description="Kiểm tra xem dịch vụ quản lý người dùng có hoạt động tốt không"
)
async def user_management_health_check():
    """Endpoint kiểm tra sức khỏe cho dịch vụ quản lý người dùng"""
    return SuccessResponse(
        message="Dịch vụ quản lý người dùng hoạt động tốt",
        data={
            "status": "healthy",
            "service": "user_management",
            "version": "1.0.0"
        }
    )
