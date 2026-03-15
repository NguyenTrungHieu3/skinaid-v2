import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func, true, false
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.auth.models.roles import Role
from app.modules.auth.models.user import User
from app.modules.auth.models.user_roles import UserRole
from app.modules.profile.models.user_profile import UserProfile
from app.shared.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository[User]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> Optional[User]:
        return await self.get_one(
            User.email == email,
            User.is_deleted == false(),
        )

    async def get_by_username(self, user_name: str) -> Optional[User]:
        statement = (
            select(User)
            .where(User.user_name == user_name, User.is_deleted == false())
            .options(
                selectinload(User.user_roles).selectinload(UserRole.role),
            )
        )
        result = await self.db.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_id_with_details(
        self,
        user_id: uuid.UUID,
    ) -> Optional[User]:
        """
        Lấy user theo ID, kèm profile + roles.

        Eager load 3 relationship: profile, user_roles, role.
        Thay thế raw SQL + _helpers.load_user_roles().
        """
        statement = (
            select(User)
            .where(User.user_id == user_id, User.is_deleted == false())
            .options(
                selectinload(User.profile),
                selectinload(User.user_roles).selectinload(UserRole.role),
            )
        )
        result = await self.db.execute(statement)
        return result.scalar_one_or_none()

    async def email_exists(self, email: str) -> bool:
        """Kiểm tra email đã tồn tại chưa (bao gồm cả user đã xóa)."""
        user = await self.get_one(User.email == email)
        return user is not None

    async def username_exists(self, user_name: str) -> bool:
        """Kiểm tra username đã tồn tại chưa (bao gồm cả user đã xóa)."""
        user = await self.get_one(User.user_name == user_name)
        return user is not None

    async def create_with_profile(
        self,
        user: User,
        profile: UserProfile,
        default_role_name: str = "user",
    ) -> User:
        from sqlalchemy.orm import selectinload
        
        self.db.add(user)
        await self.db.flush()

        profile.user_id = user.user_id
        self.db.add(profile)
        await self.db.flush()

        role = await self._get_active_role_by_name(default_role_name)
        if role:
            user_role = UserRole(
                user_id=user.user_id,
                role_id=role.role_id,
            )
            self.db.add(user_role)
            await self.db.flush()
        else:
            logger.warning(
                "Không tìm thấy role '%s' để gán cho user %s",
                default_role_name,
                user.user_id,
            )

        # Refresh with eager loading of relationships
        await self.db.refresh(user, ["profile", "user_roles"])
        
        # Explicitly load roles with selectinload to avoid lazy loading in async context
        from sqlmodel import select
        stmt = select(UserRole).options(
            selectinload(UserRole.role)
        ).where(UserRole.user_id == user.user_id)
        result = await self.db.execute(stmt)
        user_roles = result.scalars().all()
        
        # Attach loaded roles to user object
        user.user_roles = user_roles
        
        return user

    async def increment_token_version(
        self,
        user_id: uuid.UUID,
    ) -> Optional[tuple[int, int]]:
        user = await self.get_one(
            User.user_id == user_id,
            User.is_deleted == False,
        )
        if not user:
            return None

        old_version = user.token_version
        user.token_version = old_version + 1
        user.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        await self.db.flush()

        return old_version, user.token_version

    async def get_token_version(
        self,
        user_id: uuid.UUID,
    ) -> Optional[int]:
        user = await self.get_one(
            User.user_id == user_id,
            User.is_deleted == False,
        )
        return user.token_version if user else None

    async def update_last_activity(self, user_id: uuid.UUID) -> None:
        user = await self.get_one(
            User.user_id == user_id,
            User.is_deleted == False,
        )
        if user:
            user.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
            await self.db.flush()

    async def _get_active_role_by_name(
        self,
        role_name: str,
    ) -> Optional[Role]:
        statement = select(Role).where(
            Role.role_name == role_name,
            Role.is_active == True,
        )
        result = await self.db.execute(statement)
        return result.scalar_one_or_none()
