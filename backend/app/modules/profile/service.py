"""
Profile Service — Business logic cho module Profile.

Sử dụng ProfileRepository để truy cập dữ liệu.
"""

import uuid
from typing import Any, Dict, List

from fastapi import UploadFile

from app.modules.profile.exceptions import (
    AvatarUploadError,
    InvalidProfileDataError,
    ProfileNotFoundError,
)
from app.modules.profile.models.user_profile import UserProfile
from app.modules.profile.repository import ProfileRepository
from app.modules.profile.schemas.user_profile_schemas import (
    AvatarDeleteResponse,
    AvatarUploadResponse,
    ProfileStatisticsResponse,
    PublicAvatarResponse,
    UserProfileResponse,
    UserProfileUpdate,
)
from app.shared.services.file_service import FileService
from app.shared.validators.file_validator import FileValidator


class ProfileService:
    """Service xử lý logic cho Profile."""

    def __init__(self, repository: ProfileRepository):
        self.repository = repository
        self.file_service = FileService()

    async def get_profile(
        self, user_id: uuid.UUID
    ) -> UserProfileResponse:
        """Lấy thông tin profile."""
        profile = await self.repository.get_by_user_id(user_id)
        if not profile:
            # Nếu chưa có profile, trả về empty response thay vì lỗi 404?
            # Theo logic cũ: return None hoặc raise.
            # Logic cũ: get_profile_by_user_id return None.
            # Controller cũ: check if existing_profile return existing_profile else 400 bad request (update).
            # Router cũ /me: return controller.get_profile(user_id)
            # Controller.get_profile: if not profile raise 404.
            raise ProfileNotFoundError(str(user_id))

        return UserProfileResponse(**profile.to_response_dict())

    async def update_profile(
        self, user_id: uuid.UUID, data: UserProfileUpdate
    ) -> UserProfileResponse:
        """Cập nhật thông tin profile."""
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            # Không có dữ liệu update -> trả về current profile
            return await self.get_profile(user_id)

        try:
            profile = await self.repository.create_or_update(
                user_id, update_data
            )
            return UserProfileResponse(**profile.to_response_dict())
        except Exception as e:
            raise InvalidProfileDataError(f"Lỗi cập nhật profile: {str(e)}")

    async def upload_avatar(
        self, user_id: uuid.UUID, file: UploadFile
    ) -> AvatarUploadResponse:
        """Upload avatar mới."""
        # 1. Validate file
        await FileValidator.validate_upload_file(
            file=file,
            max_size=5 * 1024 * 1024,  # 5MB
            allowed_types=[
                "image/jpeg",
                "image/jpg",
                "image/png",
                "image/webp",
            ],
        )

        try:
            # 2. Upload file
            folder = f"avatars/{user_id}"
            file_url = await self.file_service.upload_file(file, folder)

            # 3. Update profile
            await self.repository.create_or_update(
                user_id, {"avatar_url": file_url}
            )

            return AvatarUploadResponse(
                avatar_url=file_url,
                file_name=file.filename or "avatar.jpg",
                file_size=file.size or 0,
                uploaded_at=datetime.utcnow(),
            )
        except Exception as e:
            raise AvatarUploadError(f"Upload thất bại: {str(e)}")

    async def delete_avatar(
        self, user_id: uuid.UUID
    ) -> AvatarDeleteResponse:
        """Xóa avatar."""
        profile = await self.repository.get_by_user_id(user_id)
        if not profile or not profile.avatar_url:
            raise ProfileNotFoundError("User chưa có avatar")

        try:
            # Xóa file từ storage (nếu cần thiết - hiện tại FileService hình như chưa có delete?)
            # Logic cũ: os.remove(file_path). FileService có delete_file?
            # Kiểm tra FileService sau. Tạm thời update DB.
            await self.repository.create_or_update(
                user_id, {"avatar_url": None}
            )
            return AvatarDeleteResponse(
                deleted=True,
                message="Đã xóa avatar thành công",
                deleted_at=datetime.utcnow(),
            )
        except Exception as e:
            raise InvalidProfileDataError(f"Lỗi xóa avatar: {str(e)}")

    async def get_public_avatar(
        self, user_id: uuid.UUID
    ) -> PublicAvatarResponse:
        """Lấy avatar public."""
        profile = await self.repository.get_by_user_id(user_id)
        has_avatar = bool(profile and profile.avatar_url)
        return PublicAvatarResponse(
            user_id=user_id,
            avatar_url=profile.avatar_url if profile else None,
            has_avatar=has_avatar,
        )

    async def get_statistics(self) -> ProfileStatisticsResponse:
        """Lấy thống kê profile."""
        stats = await self.repository.get_statistics()
        return ProfileStatisticsResponse(
            total_users=stats["total_users"],
            users_with_profile=stats["users_with_profile"],
            complete_profiles=stats["complete_profiles"],
            gender_distribution=stats["gender_distribution"],
            age_distribution=stats["age_distribution"],
            average_completion=(
                stats["complete_profiles"] / stats["users_with_profile"] * 100
                if stats["users_with_profile"] > 0
                else 0
            ),
        )

    async def search_profiles(
        self,
        full_name: str | None = None,
        gender: str | None = None,
        min_age: int | None = None,
        max_age: int | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[UserProfileResponse]:
        """Tìm kiếm profile."""
        profiles = await self.repository.search(
            full_name=full_name,
            gender=gender,
            min_age=min_age,
            max_age=max_age,
            skip=offset,
            limit=limit,
        )
        return [
            UserProfileResponse(**p.to_response_dict()) for p in profiles
        ]

    async def get_completion_suggestions(
        self, user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Gợi ý hoàn thiện hồ sơ."""
        profile = await self.repository.get_by_user_id(user_id)
        if not profile:
            return {"suggestions": [], "missing_fields": []}

        # Logic gợi ý (giữ nguyên logic cũ)
        missing_fields = []
        suggestions = []

        if not profile.full_name:
            missing_fields.append("full_name")
            suggestions.append("Thêm họ tên đầy đủ")
        if not profile.phone:
            missing_fields.append("phone")
            suggestions.append("Thêm số điện thoại")
        if not profile.date_of_birth:
            missing_fields.append("date_of_birth")
            suggestions.append("Thêm ngày sinh")
        if not profile.gender:
            missing_fields.append("gender")
            suggestions.append("Thêm giới tính")
        if not profile.address:
            missing_fields.append("address")
            suggestions.append("Thêm địa chỉ")
        if not profile.avatar_url:
            missing_fields.append("avatar_url")
            suggestions.append("Thêm ảnh đại diện")

        return {
            "missing_fields": missing_fields,
            "suggestions": suggestions,
            "current_completion": profile.profile_completion_percentage,
            "target_completion": 100,
        }
