from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.core.dependencies.access_control import require_admin, require_auth
from app.modules.notifications.dependencies import NotificationSvc
from app.modules.notifications.schemas.api import (
    CreateNotificationRequest,
    NotificationListResponse,
    NotificationResponse,
    UnreadCountResponse,
)
from app.modules.users.models import User
from app.shared.response import SuccessResponse

router = APIRouter(prefix="/notifications")


@router.get(
    "",
    response_model=SuccessResponse[NotificationListResponse],
    summary="Danh sách notifications của user",
)
async def list_notifications(
    service: NotificationSvc,
    current_user: User = Depends(require_auth),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    unread_only: bool = Query(default=False),
    notification_type: Optional[str] = Query(default=None),
) -> SuccessResponse:
    data = await service.list_notifications(
        user_id=current_user.user_id,
        skip=skip,
        limit=limit,
        unread_only=unread_only,
        notification_type=notification_type,
    )
    return SuccessResponse(message="Lấy danh sách notifications thành công", data=data)


@router.get(
    "/unread-count",
    response_model=SuccessResponse[UnreadCountResponse],
    summary="Đếm notifications chưa đọc",
)
async def get_unread_count(
    service: NotificationSvc,
    current_user: User = Depends(require_auth),
) -> SuccessResponse:
    data = await service.get_unread_count(user_id=current_user.user_id)
    return SuccessResponse(message="Lấy số notification chưa đọc thành công", data=data)


@router.patch(
    "/read-all",
    response_model=SuccessResponse,
    summary="Đánh dấu tất cả notifications đã đọc",
)
async def mark_all_read(
    service: NotificationSvc,
    current_user: User = Depends(require_auth),
) -> SuccessResponse:
    data = await service.mark_all_read(user_id=current_user.user_id)
    return SuccessResponse(message="Đã đánh dấu tất cả đã đọc", data=data)


@router.patch(
    "/{notification_id}/read",
    response_model=SuccessResponse[NotificationResponse],
    summary="Đánh dấu notification đã đọc",
)
async def mark_read(
    notification_id: UUID,
    service: NotificationSvc,
    current_user: User = Depends(require_auth),
) -> SuccessResponse:
    data = await service.mark_read(
        notification_id=notification_id,
        current_user_id=current_user.user_id,
    )
    return SuccessResponse(message="Đã đánh dấu đã đọc", data=data)


@router.delete(
    "/{notification_id}",
    response_model=SuccessResponse,
    summary="Xóa một notification",
)
async def delete_notification(
    notification_id: UUID,
    service: NotificationSvc,
    current_user: User = Depends(require_auth),
) -> SuccessResponse:
    await service.delete(
        notification_id=notification_id,
        current_user_id=current_user.user_id,
    )
    return SuccessResponse(message="Đã xóa notification")


@router.post(
    "",
    response_model=SuccessResponse[NotificationResponse],
    summary="Tạo notification cho user (admin)",
)
async def create_notification(
    request: CreateNotificationRequest,
    service: NotificationSvc,
    _: User = Depends(require_admin),
) -> SuccessResponse:
    data = await service.create_for_user(request)
    return SuccessResponse(message="Tạo notification thành công", data=data, status_code=201)
