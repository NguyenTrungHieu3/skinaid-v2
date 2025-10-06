from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Union
import uuid

from app.shared.schemas.response import SuccessResponse, ErrorResponse
from app.modules.profile.schemas.user_profile import UserProfileUpdate, UserProfileResponse
from app.modules.profile.controllers.profile_controllers import ProfileController
from app.api.v1.deps import get_db, get_current_active_user
from app.modules.auth.models.user import User

router = APIRouter(prefix="/profile", tags=["User Profile"])

async def get_profile_controller(db: AsyncSession = Depends(get_db)) -> ProfileController:
    return ProfileController(db)

@router.put(
    "/update",
    response_model=Union[SuccessResponse[UserProfileResponse], ErrorResponse],
    summary="Cập nhật thông tin profile",
    description="Cập nhật thông tin cá nhân của user như full_name, phone, address, etc."
)
async def update_profile(
    profile_data: UserProfileUpdate,
    controller: ProfileController = Depends(get_profile_controller),
    current_user: User = Depends(get_current_active_user)
):
    return await controller.update_profile(str(current_user.id), profile_data)

@router.get(
    "/me",
    response_model=Union[SuccessResponse[UserProfileResponse], ErrorResponse],
    summary="Lấy thông tin profile hiện tại",
    description="Lấy thông tin profile của user đang đăng nhập"
)
async def get_my_profile(
    controller: ProfileController = Depends(get_profile_controller),
    current_user: User = Depends(get_current_active_user)
):
    return await controller.get_profile(str(current_user.id))
