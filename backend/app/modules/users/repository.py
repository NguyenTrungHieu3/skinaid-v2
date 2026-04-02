from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy import select, func, or_, desc, false, true
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.base_repository import BaseRepository
from app.modules.users.models import User
from app.modules.auth.models.user_roles import UserRole
from app.modules.auth.models.roles import Role
from app.modules.ai.models.analysis import Analysis

class UserRepository(BaseRepository[User]):
    def __init__(self, db: AsyncSession):
        super().__init__(User, db)

    async def get_users_list(
        self,
        page: int = 1,
        page_size: int = 10,
        search: Optional[str] = None,
        role: Optional[str] = None,
        status: Optional[str] = None
    ) -> Tuple[List[User], int]:
        
        query = select(self.model).where(self.model.is_deleted == false())

        if search:
            search_pattern = f"%{search}%"
            query = query.join(self.model.profile, isouter=True)
            query = query.where(
                or_(
                    self.model.email.ilike(search_pattern),
                    self.model.user_name.ilike(search_pattern),
                    # Assuming profile full_name if it exists
                    func.lower(self.model.profile.property.mapper.class_.full_name).like(search_pattern.lower())
                )
            )

        if status:
            is_active = status.lower() == 'active'
            query = query.where(self.model.is_active == is_active)

        if role:
            query = query.join(
                UserRole, self.model.user_id == UserRole.user_id).join(
                Role, UserRole.role_id == Role.role_id)
            query = query.where(Role.role_name == role.lower())

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.options(
            selectinload(self.model.profile),
            selectinload(self.model.user_roles).selectinload(UserRole.role)
        )

        skip = (page - 1) * page_size
        query = query.offset(skip).limit(page_size).order_by(self.model.created_at.desc())
        
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def get_user_detail(self, user_id: UUID) -> Optional[User]:
        query = select(self.model).where(
            self.model.user_id == user_id,
            self.model.is_deleted == false()
        ).options(
            selectinload(self.model.profile),
            selectinload(self.model.user_roles).selectinload(UserRole.role)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
        
    async def get_user_upload_count(self, user_id: UUID) -> int:
        query = select(func.count(Analysis.analysis_id)).where(Analysis.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalar() or 0
        
    async def get_scan_history(self, user_id: UUID) -> List[Analysis]:
        query = select(Analysis).where(Analysis.user_id == user_id).order_by(desc(Analysis.created_at)).options(selectinload(Analysis.wound_detections)).limit(10)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count_active_admins(self) -> int:
        query = select(func.count(self.model.user_id)).join(
            UserRole, self.model.user_id == UserRole.user_id).join(
            Role, UserRole.role_id == Role.role_id).where(
            Role.role_name == 'admin',
            self.model.is_active == true(),
            self.model.is_deleted == false()
        )
        result = await self.db.execute(query)
        return result.scalar() or 0
