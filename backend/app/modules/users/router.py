from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID

from app.shared.response import SuccessResponse
from app.modules.users.service import UserService
from app.modules.users.schemas import (
    UserListResponse,
    UserDetailResponse,
    UpdateUserStatusRequest,
    UpdateUserStatusResponse
)
from app.core.dependencies import get_db, require_admin
from app.modules.users.models import User
from app.shared.exceptions import NotFoundError
from app.modules.audit.services.audit_service import AuditService
from app.modules.audit.routes.audit_router import get_audit_service

router = APIRouter(prefix="/admin/users")

def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(db)

@router.get(
    "",
    response_model=UserListResponse,
    summary="Danh sách user"
)
async def get_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(require_admin)
):
    """Lấy danh sách người dùng"""
    return await service.get_users(
        page=page,
        page_size=page_size,
        search=search,
        role=role,
        status=status
    )

@router.get(
    "/{user_id}",
    response_model=UserDetailResponse,
    summary="Chi tiết một user"
)
async def get_user_detail(
    user_id: str,
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(require_admin)
):
    """Lấy thông tin chi tiết đầy đủ của user"""
    user_detail = await service.get_user_detail(UUID(user_id))
    if not user_detail:
        raise NotFoundError(message=f"Không tìm thấy người dùng với ID {user_id}")
    return user_detail

@router.patch(
    "/{user_id}/status",
    response_model=UpdateUserStatusResponse,
    summary="Kích hoạt / Tắt tài khoản"
)
async def update_user_status(
    request: Request,
    user_id: str,
    status_data: UpdateUserStatusRequest,
    service: UserService = Depends(get_user_service),
    current_admin: User = Depends(require_admin),
    audit_service: AuditService = Depends(get_audit_service),
):
    """Cập nhật trạng thái người dùng (active / inactive)"""
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")
    
    return await service.update_user_status(
        user_id=UUID(user_id),
        status_data=status_data,
        current_admin=current_admin,
        audit_service=audit_service,
        ip_address=ip_address,
        user_agent=user_agent
    )
