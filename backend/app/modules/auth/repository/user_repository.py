"""
UserRepository — Truy vấn database cho User entity.

Thay thế toàn bộ raw SQL trong UserService + _helpers.load_user_roles().
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.auth.models.roles import Role
from app.modules.auth.models.user import User
from app.modules.auth.models.user_roles import UserRole
from app.modules.profile.models.user_profile import UserProfile
from app.shared.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository[User]):
    """Repository cho User entity — tất cả truy vấn database liên quan user."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(User, db)

    # ── QUERY ─────────────────────────────────────────────

    async def get_by_email(self, email: str) -> Optional[User]:
        """Lấy user chưa bị xóa theo email."""
        return await self.get_one(
            User.email == email,
            User.is_deleted == False,  # noqa: E712
        )

    async def get_by_username(self, user_name: str) -> Optional[User]:
        """
        Lấy user chưa bị xóa theo username, kèm roles.

        Eager load user_roles → role để tránh N+1 query.
        """
        statement = (
            select(User)
            .where(User.user_name == user_name, User.is_deleted == False)  # noqa: E712
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
            .where(User.user_id == user_id, User.is_deleted == False)  # noqa: E712
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

    # ── CREATE ────────────────────────────────────────────

    async def create_with_profile(
        self,
        user: User,
        profile: UserProfile,
        default_role_name: str = "user",
    ) -> User:
        """
        Tạo user mới kèm profile + gán role mặc định.

        Transaction flow:
        1. Add user → flush (để có user_id FK)
        2. Add profile → flush
        3. Gán role mặc định → flush
        4. Refresh user để load relationships

        Args:
            user: User entity đã khởi tạo (chưa persist)
            profile: UserProfile entity đã khởi tạo
            default_role_name: Tên role mặc định (default: "user")

        Returns:
            User với profile + roles đã load
        """
        # 1. Persist user
        self.db.add(user)
        await self.db.flush()

        # 2. Persist profile (FK = user_id)
        profile.user_id = user.user_id
        self.db.add(profile)
        await self.db.flush()

        # 3. Gán role mặc định
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

        # 4. Refresh để load relationships
        await self.db.refresh(user, ["profile", "user_roles"])
        return user

    # ── UPDATE ────────────────────────────────────────────

    async def increment_token_version(
        self,
        user_id: uuid.UUID,
    ) -> Optional[tuple[int, int]]:
        """
        Tăng token_version (+1) để thu hồi tất cả tokens.

        Returns:
            Tuple (old_version, new_version) hoặc None nếu không tìm thấy user
        """
        user = await self.get_one(
            User.user_id == user_id,
            User.is_deleted == False,  # noqa: E712
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
        """Lấy token_version hiện tại của user."""
        user = await self.get_one(
            User.user_id == user_id,
            User.is_deleted == False,  # noqa: E712
        )
        return user.token_version if user else None

    async def update_last_activity(self, user_id: uuid.UUID) -> None:
        """Cập nhật updated_at (last activity time)."""
        user = await self.get_one(
            User.user_id == user_id,
            User.is_deleted == False,  # noqa: E712
        )
        if user:
            user.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
            await self.db.flush()

    # ── PRIVATE ───────────────────────────────────────────

    async def _get_active_role_by_name(
        self,
        role_name: str,
    ) -> Optional[Role]:
        """Lấy role đang active theo tên."""
        statement = select(Role).where(
            Role.role_name == role_name,
            Role.is_active == True,  # noqa: E712
        )
        result = await self.db.execute(statement)
        return result.scalar_one_or_none()
