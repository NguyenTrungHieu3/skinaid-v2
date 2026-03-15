from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.modules.profile.repository import ProfileRepository
from app.modules.profile.service import ProfileService


def get_profile_repository(
    db: AsyncSession = Depends(get_db),
) -> ProfileRepository:
    return ProfileRepository(db)


def get_profile_service(
    repository: ProfileRepository = Depends(get_profile_repository),
) -> ProfileService:
    return ProfileService(repository)


Repo = Annotated[ProfileRepository, Depends(get_profile_repository)]
Service = Annotated[ProfileService, Depends(get_profile_service)]
