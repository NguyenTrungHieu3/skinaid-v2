from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session as get_db
from app.modules.audit.audit_repository import AuditRepository
from app.modules.audit.repository.statistics_repository import StatisticsRepository
from app.modules.audit.services.audit_service import AuditService
from app.modules.audit.services.statistics_service import StatisticsService


DbSession = Annotated[AsyncSession, Depends(get_db)]


def get_audit_repository(db: DbSession) -> AuditRepository:
    return AuditRepository(db)


AuditRepo = Annotated[AuditRepository, Depends(get_audit_repository)]


def get_audit_service(repo: AuditRepo) -> AuditService:
    return AuditService(repo)


AuditSvc = Annotated[AuditService, Depends(get_audit_service)]


def get_statistics_repository(db: DbSession) -> StatisticsRepository:
    return StatisticsRepository(db)


StatisticsRepo = Annotated[StatisticsRepository, Depends(get_statistics_repository)]


def get_statistics_service(repo: StatisticsRepo) -> StatisticsService:
    return StatisticsService(repo)


StatisticsSvc = Annotated[StatisticsService, Depends(get_statistics_service)]
