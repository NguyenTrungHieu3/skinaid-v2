from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.modules.guest.repository import GuestRepository
from app.modules.guest.service import GuestService


async def get_guest_repository(
    db: AsyncSession = Depends(get_db),
) -> GuestRepository:
    return GuestRepository(db)


async def get_guest_service(
    repository: GuestRepository = Depends(get_guest_repository),
    db: AsyncSession = Depends(get_db),
) -> GuestService:
    return GuestService(repository, db)


GuestRepo = Annotated[GuestRepository, Depends(get_guest_repository)]
GuestSvc = Annotated[GuestService, Depends(get_guest_service)]
