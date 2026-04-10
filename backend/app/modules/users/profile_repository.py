from uuid import uuid4, UUID
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlmodel import select as sqlmodel_select

from app.modules.users.models import User, UserProfile
from app.shared.base_repository import BaseRepository


class ProfileRepository(BaseRepository[UserProfile]):

    def __init__(self, session):
        super().__init__(UserProfile, session)

    async def get_by_user_id(self, user_id: UUID) -> UserProfile | None:
        stmt = sqlmodel_select(UserProfile).where(
            UserProfile.user_id == user_id
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def create_or_update(
        self, user_id: UUID, profile_data: dict[str, Any]
    ) -> UserProfile:
        profile = await self.get_by_user_id(user_id)
        current_time = datetime.now(timezone.utc).replace(tzinfo=None)

        if profile:
            for key, value in profile_data.items():
                if value is not None:
                    setattr(profile, key, value)
            profile.updated_at = current_time
        else:
            profile = UserProfile(
                user_id=user_id,
                created_at=current_time,
                updated_at=current_time,
                **{k: v for k, v in profile_data.items() if v is not None},
            )
            self.db.add(profile)

        await self.db.flush()
        await self.db.refresh(profile)
        return profile

    async def search(
        self,
        full_name: str | None = None,
        gender: str | None = None,
        min_age: int | None = None,
        max_age: int | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> list[UserProfile]:
        stmt = sqlmodel_select(UserProfile)

        if full_name:
            stmt = stmt.where(UserProfile.full_name.ilike(
                f"%{full_name}%"))

        if gender:
            stmt = stmt.where(UserProfile.gender == gender)

        age_col = func.extract('year', func.age(
            func.current_date(), UserProfile.date_of_birth))

        if min_age is not None:
            stmt = stmt.where(age_col >= min_age)

        if max_age is not None:
            stmt = stmt.where(age_col <= max_age)

        stmt = stmt.offset(skip).limit(limit).order_by(
            UserProfile.updated_at.desc())

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_statistics(self) -> dict[str, Any]:
        total_users_stmt = select(func.count()).select_from(User)
        total_result = await self.db.execute(total_users_stmt)
        total_users = total_result.scalar_one()

        with_profile_stmt = select(func.count(UserProfile.user_id))
        profile_result = await self.db.execute(with_profile_stmt)
        users_with_profile = profile_result.scalar_one()

        complete_stmt = select(func.count()).where(
            UserProfile.full_name.is_not(None),
            UserProfile.phone.is_not(None),
            UserProfile.date_of_birth.is_not(None),
            UserProfile.gender.is_not(None),
        )
        complete_result = await self.db.execute(complete_stmt)
        complete_profiles = complete_result.scalar_one()

        gender_stmt = (
            select(UserProfile.gender, func.count(UserProfile.user_id))
            .where(UserProfile.gender.is_not(None))
            .group_by(UserProfile.gender)
        )
        gender_result = await self.db.execute(gender_stmt)
        gender_dist = {row[0]: row[1] for row in gender_result.all()}

        from sqlalchemy import case
        age_col = func.extract('year', func.age(
            func.current_date(), UserProfile.date_of_birth))
        age_group = case(
            (age_col < 18, 'under_18'),
            (age_col.between(18, 25), '18_25'),
            (age_col.between(26, 35), '26_35'),
            (age_col.between(36, 50), '36_50'),
            (age_col > 50, 'over_50'),
            else_='unknown'
        ).label('age_group')

        age_stmt = (
            select(age_group, func.count(UserProfile.user_id))
            .where(UserProfile.date_of_birth.is_not(None))
            .group_by('age_group')
        )
        age_result = await self.db.execute(age_stmt)
        age_dist = {row.age_group: row[1] for row in age_result.all()}

        return {
            "total_users": total_users,
            "users_with_profile": users_with_profile,
            "complete_profiles": complete_profiles,
            "gender_distribution": gender_dist,
            "age_distribution": age_dist,
        }
