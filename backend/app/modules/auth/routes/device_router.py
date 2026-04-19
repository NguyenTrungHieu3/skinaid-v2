from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import get_current_active_user, require_admin
from app.modules.auth.dependencies import DeviceSessionSvc
from app.modules.auth.schemas.device_session import (
    DeviceRegisterRequest,
    DeviceSessionListResponse,
    DeviceSessionResponse,
    DeviceUpdateRequest,
    SyncStatusUpdateRequest,
)
from app.modules.users.models import User
from app.shared.response import SuccessResponse

router = APIRouter(prefix="/devices")


@router.post(
    "/register",
    response_model=SuccessResponse[DeviceSessionResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register or upsert a device session for the current user",
)
async def register_device(
    payload: DeviceRegisterRequest,
    service: DeviceSessionSvc,
    current_user: User = Depends(get_current_active_user),
) -> SuccessResponse:
    entity = await service.register_device(current_user.user_id, payload)
    return SuccessResponse(
        message="Đăng ký thiết bị thành công",
        data=DeviceSessionResponse.model_validate(entity),
    )


@router.get(
    "",
    response_model=SuccessResponse[DeviceSessionListResponse],
    summary="List devices owned by the current user",
)
async def list_devices(
    service: DeviceSessionSvc,
    current_user: User = Depends(get_current_active_user),
    only_active: bool = Query(default=True),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> SuccessResponse:
    items, total = await service.list_user_devices(
        current_user.user_id, only_active=only_active, skip=skip, limit=limit
    )
    return SuccessResponse(
        message="Lấy danh sách thiết bị thành công",
        data=DeviceSessionListResponse(
            items=[DeviceSessionResponse.model_validate(i) for i in items],
            total=total,
        ),
    )


@router.get(
    "/{session_id}",
    response_model=SuccessResponse[DeviceSessionResponse],
    summary="Get one device session",
)
async def get_device(
    session_id: UUID,
    service: DeviceSessionSvc,
    current_user: User = Depends(get_current_active_user),
) -> SuccessResponse:
    entity = await service.get_device(session_id, current_user.user_id)
    return SuccessResponse(
        message="Lấy thông tin thiết bị thành công",
        data=DeviceSessionResponse.model_validate(entity),
    )


@router.patch(
    "/{session_id}",
    response_model=SuccessResponse[DeviceSessionResponse],
    summary="Update device metadata / push token / cache info",
)
async def update_device(
    session_id: UUID,
    payload: DeviceUpdateRequest,
    service: DeviceSessionSvc,
    current_user: User = Depends(get_current_active_user),
) -> SuccessResponse:
    entity = await service.update_device(session_id, current_user.user_id, payload)
    return SuccessResponse(
        message="Cập nhật thiết bị thành công",
        data=DeviceSessionResponse.model_validate(entity),
    )


@router.patch(
    "/{session_id}/sync",
    response_model=SuccessResponse[DeviceSessionResponse],
    summary="Update sync status / pending syncs",
)
async def update_sync(
    session_id: UUID,
    payload: SyncStatusUpdateRequest,
    service: DeviceSessionSvc,
    current_user: User = Depends(get_current_active_user),
) -> SuccessResponse:
    entity = await service.update_sync_status(session_id, current_user.user_id, payload)
    return SuccessResponse(
        message="Cập nhật đồng bộ thành công",
        data=DeviceSessionResponse.model_validate(entity),
    )


@router.post(
    "/{session_id}/trust",
    response_model=SuccessResponse[DeviceSessionResponse],
    summary="Mark device as trusted (admin)",
    dependencies=[Depends(require_admin)],
)
async def trust_device(
    session_id: UUID,
    service: DeviceSessionSvc,
    is_trusted: bool = Query(default=True),
) -> SuccessResponse:
    entity = await service.mark_trusted(session_id, is_trusted=is_trusted)
    return SuccessResponse(
        message="Cập nhật trạng thái tin cậy thành công",
        data=DeviceSessionResponse.model_validate(entity),
    )


@router.post(
    "/{session_id}/revoke",
    response_model=SuccessResponse[DeviceSessionResponse],
    summary="Revoke (deactivate) a device session",
)
async def revoke_device(
    session_id: UUID,
    service: DeviceSessionSvc,
    current_user: User = Depends(get_current_active_user),
) -> SuccessResponse:
    entity = await service.revoke_device(session_id, current_user.user_id)
    return SuccessResponse(
        message="Đã thu hồi thiết bị",
        data=DeviceSessionResponse.model_validate(entity),
    )


@router.delete(
    "/{session_id}",
    response_model=SuccessResponse[dict],
    summary="Delete a device session record",
)
async def delete_device(
    session_id: UUID,
    service: DeviceSessionSvc,
    current_user: User = Depends(get_current_active_user),
) -> SuccessResponse:
    await service.delete_device(session_id, current_user.user_id)
    return SuccessResponse(
        message="Đã xóa thiết bị",
        data={"session_id": str(session_id)},
    )
