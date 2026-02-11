from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.modules.firstaid.repository import FirstAidRepository
from app.modules.firstaid.service import FirstAidService


async def get_firstaid_repository(
    db: AsyncSession = Depends(get_db),
) -> FirstAidRepository:
    return FirstAidRepository(db)


async def get_firstaid_service(
    repository: FirstAidRepository = Depends(get_firstaid_repository),
    db: AsyncSession = Depends(get_db),
) -> FirstAidService:
    return FirstAidService(repository, db)


FirstAidRepo = Annotated[FirstAidRepository, Depends(get_firstaid_repository)]
FirstAidSvc = Annotated[FirstAidService, Depends(get_firstaid_service)]
