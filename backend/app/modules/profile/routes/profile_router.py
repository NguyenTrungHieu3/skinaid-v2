from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Union, List, Dict, Any, Optional

from app.shared.schemas.response import SuccessResponse, ErrorResponse
from app.modules.profile.schemas.user_profile_schemas import UserProfileUpdate, UserProfileResponse, ProfileStatisticsResponse,AvatarUploadResponse
from app.modules.profile.controllers.profile_controller import ProfileController
from app.core.dependencies import get_db, get_current_active_user, require_admin
from app.modules.auth.models.user import User
from app.modules.audit.services.audit_service import AuditService
from fastapi import File, UploadFile # Nhớ import File, UploadFile

router = APIRouter(prefix="/profile", tags=["User Profile Management"])

async def get_profile_controller(db: AsyncSession = Depends(get_db)) -> ProfileController:
    return ProfileController(db)

@router.put(
    "/update",
    response_model=Union[SuccessResponse[UserProfileResponse], ErrorResponse],
    summary="Cập nhật thông tin profile",
    description="Cập nhật thông tin cá nhân của user như full_name, phone, address, etc."
)
async def update_profile(
    request: Request,
    profile_data: UserProfileUpdate,
    controller: ProfileController = Depends(get_profile_controller),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Cập nhật thông tin profile cá nhân."""
    result = await controller.update_profile(current_user.user_id, profile_data)
    
    # Audit logging
    audit_service = AuditService(db)
    fields_updated = [k for k, v in profile_data.model_dump(exclude_unset=True).items() if v is not None]
    await audit_service.log_event(
        action="update_profile",
        user_id=current_user.user_id,
        success=isinstance(result, SuccessResponse),
        resource_type="user_profile",
        resource_id=str(current_user.user_id),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
        details={"fields_updated": fields_updated},
        error_message=result.message if isinstance(result, ErrorResponse) else None
    )
    
    return result

@router.post(
    "/avatar-upload",
    response_model=Union[SuccessResponse[AvatarUploadResponse], ErrorResponse],
    summary="Upload ảnh đại diện",
    description="Upload file ảnh và nhận về đường dẫn URL để cập nhật profile"
)
async def upload_avatar(
    file: UploadFile = File(...),
    controller: ProfileController = Depends(get_profile_controller),
    current_user: User = Depends(get_current_active_user), # Yêu cầu đăng nhập mới được up
):
    """
    Upload avatar (Multipart/form-data).
    Trả về URL của ảnh.
    """
    return await controller.upload_avatar(file)

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
    """Lấy thông tin profile cá nhân."""
    return await controller.get_profile(current_user.user_id)

@router.get(
    "/statistics",
    response_model=Union[SuccessResponse[ProfileStatisticsResponse], ErrorResponse],
    summary="Lấy thống kê profile",
    description="Lấy thống kê tổng quan về user profiles trong hệ thống"
)
async def get_profile_statistics(
    controller: ProfileController = Depends(get_profile_controller),
    current_user: User = Depends(require_admin)
):
    return await controller.get_profile_statistics()

@router.get(
    "/search",
    response_model=Union[SuccessResponse[List[UserProfileResponse]], ErrorResponse],
    summary="Tìm kiếm profiles",
    description="Tìm kiếm user profiles với bộ lọc"
)
async def search_profiles(
    full_name: Optional[str] = Query(None, description="Tìm theo tên"),
    gender: Optional[str] = Query(None, description="Lọc theo giới tính"),
    min_age: Optional[int] = Query(None, description="Tuổi tối thiểu", ge=0),
    max_age: Optional[int] = Query(None, description="Tuổi tối đa", ge=0),
    limit: int = Query(20, description="Số lượng tối đa", le=100, ge=1),
    offset: int = Query(0, description="Số bản ghi bỏ qua", ge=0),
    controller: ProfileController = Depends(get_profile_controller),
    current_user: User = Depends(require_admin)
):
    return await controller.search_profiles(
        full_name=full_name,
        gender=gender,
        min_age=min_age,
        max_age=max_age,
        limit=limit,
        offset=offset
    )

@router.get(
    "/completion-suggestions",
    response_model=Union[SuccessResponse[Dict[str, Any]], ErrorResponse],
    summary="Gợi ý hoàn thiện profile",
    description="Lấy gợi ý các trường cần điền để hoàn thiện profile"
)
async def get_completion_suggestions(
    controller: ProfileController = Depends(get_profile_controller),
    current_user: User = Depends(get_current_active_user)
):
    return await controller.get_profile_completion_suggestions(current_user.user_id)
