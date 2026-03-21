from typing import List, Optional, Sequence, Any, Tuple, Dict
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, func, or_, desc, true, false, case
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.base_repository import BaseRepository
from app.modules.users.models.user import User
from app.modules.auth.models.user_roles import UserRole
from app.modules.auth.models.roles import Role


class UserRepository(BaseRepository[User]):
    def __init__(self, db: AsyncSession):
        super().__init__(User, db)

    async def get_users_with_filters(
        self,
        skip: int = 0,
        limit: int = 10,
        search: Optional[str] = None,
        role: Optional[str] = None,
        status: Optional[str] = None
    ) -> Tuple[Sequence[User], int]:
        # Base query
        query = select(self.model).where(self.model.is_deleted == false())

        # Apply search
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    self.model.email.ilike(search_pattern),
                    self.model.user_name.ilike(search_pattern)
                )
            )

        # Apply status filter
        if status:
            is_active = status.lower() == 'active'
            query = query.where(self.model.is_active == is_active)

        # Apply role filter
        if role:
            query = query.join(
                UserRole, self.model.user_id == UserRole.user_id)
            query = query.join(Role, UserRole.role_id == Role.role_id)
            query = query.where(Role.role_name == role.lower())

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Eager load relationships
        query = query.options(
            selectinload(self.model.profile),
            selectinload(self.model.user_roles).selectinload(UserRole.role)
        )

        # Apply pagination and sorting
        query = query.offset(skip).limit(
            limit).order_by(self.model.created_at.desc())

        result = await self.db.execute(query)
        return result.scalars().all(), total

    async def get_user_with_details(self, user_id: UUID) -> Optional[User]:
        query = select(self.model).where(
            self.model.user_id == user_id,
            self.model.is_deleted == false()
        ).options(
            selectinload(self.model.profile),
            selectinload(self.model.user_roles).selectinload(UserRole.role)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_user_stats(self) -> Dict[str, Any]:
        # Total users
        total_query = select(func.count(self.model.user_id)).where(
            self.model.is_deleted == false())
        total_result = await self.db.execute(total_query)
        total_users = total_result.scalar() or 0

        # Active users
        active_query = select(func.count(self.model.user_id)).where(
            self.model.is_active == true(),
            self.model.is_deleted == false()
        )
        active_result = await self.db.execute(active_query)
        active_users = active_result.scalar() or 0

        # Verified users
        verified_query = select(func.count(self.model.user_id)).where(
            self.model.is_verified == true(),
            self.model.is_deleted == false()
        )
        verified_result = await self.db.execute(verified_query)
        verified_users = verified_result.scalar() or 0

        # Users by role
        role_query = (
            select(
                Role.role_name,
                func.count(
                    func.distinct(
                        case(
                            (User.is_deleted == false(), UserRole.user_id),
                            else_=None
                        )
                    )
                ).label("count")
            )
            .select_from(Role)
            .outerjoin(UserRole, Role.role_id == UserRole.role_id)
            .outerjoin(User, UserRole.user_id == User.user_id)
            .group_by(Role.role_name)
        )
        role_result = await self.db.execute(role_query)
        users_by_role = {row.role_name: row.count for row in role_result.all()}

        return {
            "total_users": total_users,
            "active_users": active_users,
            "verified_users": verified_users,
            "users_by_role": users_by_role
        }

    async def get_user_upload_count(self, user_id: UUID) -> int:
        from app.modules.ai.models.analysis import Analysis
        
        query = select(func.count(Analysis.analysis_id)).where(
            Analysis.user_id == user_id
        )
        try:
            result = await self.db.execute(query)
            count = result.scalar()
            return count or 0
        except Exception:
            return 0

    async def get_role_by_name(self, role_name: str) -> Optional[Role]:
        query = select(Role).where(Role.role_name == role_name.lower())
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        return await self.get_one(self.model.email == email)

    async def email_exists(self, email: str) -> bool:
        user = await self.get_by_email(email)
        return user is not None

    async def get_by_username(self, user_name: str) -> Optional[User]:
        return await self.get_one(self.model.user_name == user_name)

    async def username_exists(self, username: str) -> bool:
        user = await self.get_by_username(username)
        return user is not None

    async def remove_all_user_roles(self, user_id: UUID) -> None:
        from sqlalchemy import delete
        query = delete(UserRole).where(UserRole.user_id == user_id)
        await self.db.execute(query)
        await self.db.flush()

    async def create_profile(self, user_id: UUID, full_name: str) -> None:
        from app.modules.users.models.user_profile import UserProfile
        profile = UserProfile(user_id=user_id, full_name=full_name)
        self.db.add(profile)
        await self.db.flush()

    async def assign_role(self, user_id: UUID, role_id: int) -> None:
        user_role = UserRole(user_id=user_id, role_id=role_id)
        self.db.add(user_role)
        await self.db.flush()
