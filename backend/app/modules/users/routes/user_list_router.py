from fastapi import APIRouter, Depends, Query
from typing import Optional

from app.shared.response import SuccessResponse
from app.modules.users.dependencies import UserSvc
from app.modules.users.schemas.api import (
    UserListResponse,
    UserStatsResponse
)
from app.core.dependencies import require_admin
from app.modules.users.models.user import User

router = APIRouter(prefix="/admin/users")


@router.get(
    "",
    response_model=SuccessResponse[UserListResponse],
    summary="Lấy danh sách người dùng",
    description="Lấy danh sách người dùng có phân trang với các bộ lọc tùy chọn"
)
async def get_users(
    service: UserSvc,
    _: User = Depends(require_admin),
    page: int = Query(1, ge=1, description="Số trang (bắt đầu từ 1)"),
    limit: int = Query(10, ge=1, le=100, description="Số lượng người dùng mỗi trang"),
    search: Optional[str] = Query(None, description="Tìm kiếm theo email hoặc tên hiển thị"),
    role: Optional[str] = Query(None, description="Lọc theo vai trò (user, moderator, admin)"),
    status: Optional[str] = Query(None, description="Lọc theo trạng thái (active, inactive)"),
):
    """Lấy danh sách người dùng có phân trang với các bộ lọc."""
    users, pagination = await service.get_users(
        page=page,
        limit=limit,
        search=search,
        role=role,
        status=status
    )
    return SuccessResponse(
        message="Lấy danh sách người dùng thành công",
        data=UserListResponse(users=users, pagination=pagination)
    )


@router.get(
    "/stats",
    response_model=SuccessResponse[UserStatsResponse],
    summary="Lấy thống kê người dùng",
    description="Lấy thống kê tổng quan về người dùng"
)
async def get_user_stats(
    service: UserSvc,
    _: User = Depends(require_admin),
):
    """Lấy thống kê tổng quan về người dùng."""
    stats = await service.get_user_stats()
    return SuccessResponse(
        message="Lấy thống kê người dùng thành công",
        data=stats
    )


@router.get(
    "/health/check",
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
            "version": "1.1.0"
        }
    )
