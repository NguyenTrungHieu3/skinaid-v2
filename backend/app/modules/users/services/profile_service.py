from uuid import uuid4, UUID
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import UploadFile

from app.core.config import settings
from app.modules.users.exceptions import (
    AvatarUploadError,
    ProfileNotFoundError,
)
from app.modules.users.models.user_profile import UserProfile
from app.modules.users.repository.profile_repository import ProfileRepository
from app.modules.users.schemas.profile_schemas import (
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
    def __init__(self, repository: ProfileRepository):
        self.repository = repository
        self.file_service = FileService()

    async def get_profile(
        self, user_id: UUID
    ) -> UserProfileResponse:
        profile = await self.repository.get_by_user_id(user_id)
        if not profile:
            raise ProfileNotFoundError(str(user_id))

        return UserProfileResponse(**profile.to_response_dict())

    async def update_profile(
        self, user_id: UUID, data: UserProfileUpdate
    ) -> UserProfileResponse:
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return await self.get_profile(user_id)

        profile = await self.repository.create_or_update(
            user_id, update_data
        )
        return UserProfileResponse(**profile.to_response_dict())

    async def upload_avatar(
        self, user_id: UUID, file: UploadFile
    ) -> AvatarUploadResponse:
        await FileValidator.validate_upload_file(
            file=file,
            max_size=settings.MAX_UPLOAD_SIZE,
            allowed_types=[
                "image/jpeg",
                "image/jpg",
                "image/png",
                "image/webp",
            ],
        )

        file_content = await file.read()
        save_result = await FileService.save_file(
            file_content=file_content,
            filename=file.filename or "avatar.jpg",
            subfolder=f"avatars/{user_id}",
        )
        file_url = save_result["file_url"]

        await self.repository.create_or_update(
            user_id, {"avatar_url": file_url}
        )

        return AvatarUploadResponse(
            avatar_url=file_url,
            file_name=file.filename or "avatar.jpg",
            file_size=len(file_content),
            uploaded_at=datetime.now(timezone.utc),
        )

    async def delete_avatar(
        self, user_id: UUID
    ) -> AvatarDeleteResponse:
        profile = await self.repository.get_by_user_id(user_id)
        if not profile or not profile.avatar_url:
            raise ProfileNotFoundError("User chưa có avatar")

        old_avatar_path = profile.avatar_url.replace("/uploads/", "uploads/")
        await FileService.delete_file(old_avatar_path)

        await self.repository.create_or_update(
            user_id, {"avatar_url": None}
        )
        return AvatarDeleteResponse(
            deleted=True,
            message="Đã xóa avatar thành công",
            deleted_at=datetime.now(timezone.utc),
        )

    async def get_public_avatar(
        self, user_id: UUID
    ) -> PublicAvatarResponse:
        profile = await self.repository.get_by_user_id(user_id)
        has_avatar = bool(profile and profile.avatar_url)
        return PublicAvatarResponse(
            user_id=user_id,
            avatar_url=profile.avatar_url if profile else None,
            has_avatar=has_avatar,
        )

    async def get_statistics(self) -> ProfileStatisticsResponse:
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
        self, user_id: UUID
    ) -> Dict[str, Any]:
        profile = await self.repository.get_by_user_id(user_id)
        if not profile:
            return {"suggestions": [], "missing_fields": []}

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
