"""
Notification router — stub endpoints.

Provides basic CRUD-style notification endpoints.
Replace with full implementation when notification delivery is ready.
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional
from uuid import UUID

from app.shared.response import SuccessResponse
from app.core.dependencies import get_current_user
from app.modules.users.models.user import User

router = APIRouter(prefix="/notifications")


@router.get(
    "",
    response_model=SuccessResponse,
    summary="Lấy danh sách thông báo",
    description="Lấy danh sách thông báo của người dùng hiện tại",
)
async def get_notifications(
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False),
):
    """Lấy danh sách thông báo — stub trả về danh sách rỗng."""
    return SuccessResponse(
        message="Lấy danh sách thông báo thành công",
        data={
            "notifications": [],
            "pagination": {
                "total": 0,
                "page": page,
                "limit": limit,
                "total_pages": 0,
            },
            "unread_count": 0,
        },
    )


@router.patch(
    "/{notification_id}/read",
    response_model=SuccessResponse,
    summary="Đánh dấu đã đọc",
)
async def mark_as_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
):
    """Đánh dấu thông báo đã đọc — stub."""
    return SuccessResponse(
        message="Đánh dấu đã đọc thành công",
        data={"notification_id": str(notification_id), "read": True},
    )
