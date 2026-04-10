from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.modules.users.profile_repository import ProfileRepository
from app.modules.users.profile_service import ProfileService


DbSession = Annotated[AsyncSession, Depends(get_db)]


def get_profile_repository(db: DbSession) -> ProfileRepository:
    return ProfileRepository(db)


def get_profile_service(
    repository: ProfileRepository = Depends(get_profile_repository),
) -> ProfileService:
    return ProfileService(repository)


ProfileRepo = Annotated[ProfileRepository, Depends(get_profile_repository)]
ProfileSvc  = Annotated[ProfileService,    Depends(get_profile_service)]
