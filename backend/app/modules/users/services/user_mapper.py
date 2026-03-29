from typing import List
from datetime import datetime

from app.modules.users.models.user import User
from app.modules.users.schemas.api import UserBasicInfo, UserDetailInfo


class UserMapper:
    """Helper to convert User model to response schemas."""

    @staticmethod
    def extract_roles(user: User) -> List[str]:
        """Extract active roles from user."""
        roles = []
        if user.user_roles:
            for ur in user.user_roles:
                if ur.role and (not ur.expires_at or ur.expires_at > datetime.now()):
                    roles.append(ur.role.role_name)
        return roles

    @staticmethod
    def get_display_name(user: User) -> str:
        """Get user display name."""
        if hasattr(user, 'profile') and user.profile:
            return user.profile.full_name or user.user_name
        return user.user_name

    @staticmethod
    def to_basic_info(user: User, upload_count: int) -> UserBasicInfo:
        """Convert User to UserBasicInfo."""
        return UserBasicInfo(
            user_id=user.user_id,
            email=user.email,
            user_name=user.user_name,
            display_name=UserMapper.get_display_name(user),
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
            roles=UserMapper.extract_roles(user),
            upload_count=upload_count
        )

    @staticmethod
    def to_detail_info(user: User, upload_count: int) -> UserDetailInfo:
        """Convert User to UserDetailInfo."""
        return UserDetailInfo(
            user_id=user.user_id,
            email=user.email,
            user_name=user.user_name,
            display_name=UserMapper.get_display_name(user),
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
            updated_at=user.updated_at,
            roles=UserMapper.extract_roles(user),
            upload_count=upload_count,
            last_login=None
        )
