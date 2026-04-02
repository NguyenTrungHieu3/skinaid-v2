import logging
from uuid import uuid4, UUID
from typing import Annotated, Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Query, Request, UploadFile

from app.core.dependencies import (
    get_current_active_user,
    get_current_user,
    require_admin,
)
from app.modules.users.models import User
from app.modules.profile.dependencies import get_profile_service
from app.modules.profile.schemas import (
    AvatarDeleteResponse,
    AvatarUploadResponse,
    ProfileStatisticsResponse,
    PublicAvatarResponse,
    UserProfileResponse,
    UserProfileUpdate,
)
from app.modules.profile.service import ProfileService
from app.shared.response import SuccessResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/profile")


@router.put(
    "/update",
    response_model=SuccessResponse[UserProfileResponse],
    summary="Update profile",
)
async def update_profile(
    request: Request,
    profile_data: UserProfileUpdate,
    service: ProfileService = Depends(get_profile_service),
    current_user: User = Depends(get_current_active_user),
) -> SuccessResponse:
    result = await service.update_profile(current_user.user_id, profile_data)

    return SuccessResponse(
        message="Cập nhật hồ sơ thành công",
        data=result,
    )


@router.post(
    "/avatar-upload",
    response_model=SuccessResponse[AvatarUploadResponse],
    summary="Upload avatar",
)
async def upload_avatar(
    file: UploadFile = File(...),
    service: ProfileService = Depends(get_profile_service),
    current_user: User = Depends(get_current_active_user),
) -> SuccessResponse:
    result = await service.upload_avatar(current_user.user_id, file)
    return SuccessResponse(
        message="Upload avatar thành công",
        data=result,
    )


@router.get(
    "/me",
    response_model=SuccessResponse[UserProfileResponse],
    summary="Get current profile",
)
async def get_my_profile(
    service: ProfileService = Depends(get_profile_service),
    current_user: User = Depends(get_current_active_user),
) -> SuccessResponse:
    result = await service.get_profile(current_user.user_id)
    return SuccessResponse(
        message="Lấy thông tin hồ sơ thành công",
        data=result,
    )


@router.get(
    "/statistics",
    response_model=SuccessResponse[ProfileStatisticsResponse],
    summary="Get profile statistics",
)
async def get_profile_statistics(
    service: ProfileService = Depends(get_profile_service),
    _: User = Depends(require_admin),
) -> SuccessResponse:
    result = await service.get_statistics()
    return SuccessResponse(
        message="Lấy thống kê hồ sơ thành công",
        data=result,
    )


@router.get(
    "/search",
    response_model=SuccessResponse[List[UserProfileResponse]],
    summary="Search profiles",
)
async def search_profiles(
    service: ProfileService = Depends(get_profile_service),
    _: User = Depends(require_admin),
    full_name: Optional[str] = Query(None),
    gender: Optional[str] = Query(None),
    min_age: Optional[int] = Query(None, ge=0),
    max_age: Optional[int] = Query(None, ge=0),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> SuccessResponse:
    result = await service.search_profiles(
        full_name=full_name,
        gender=gender,
        min_age=min_age,
        max_age=max_age,
        limit=limit,
        offset=offset,
    )
    return SuccessResponse(
        message="Tìm kiếm hồ sơ thành công",
        data=result,
    )


@router.get(
    "/completion-suggestions",
    response_model=SuccessResponse[Dict[str, Any]],
    summary="Get profile completion suggestions",
)
async def get_completion_suggestions(
    service: ProfileService = Depends(get_profile_service),
    current_user: User = Depends(get_current_active_user),
) -> SuccessResponse:
    result = await service.get_completion_suggestions(current_user.user_id)
    return SuccessResponse(
        message="Lấy gợi ý thành công",
        data=result,
    )


@router.delete(
    "/avatar",
    response_model=SuccessResponse[AvatarDeleteResponse],
    summary="Delete avatar",
)
async def delete_avatar(
    service: ProfileService = Depends(get_profile_service),
    current_user: User = Depends(get_current_active_user),
) -> SuccessResponse:
    result = await service.delete_avatar(current_user.user_id)
    return SuccessResponse(
        message="Xóa avatar thành công",
        data=result,
    )


@router.get(
    "/avatar/{user_id}",
    response_model=SuccessResponse[PublicAvatarResponse],
    summary="Get public avatar",
)
async def get_user_avatar(
    user_id: UUID,
    service: ProfileService = Depends(get_profile_service),
) -> SuccessResponse:
    result = await service.get_public_avatar(user_id)
    return SuccessResponse(
        message="Lấy avatar thành công",
        data=result,
    )
