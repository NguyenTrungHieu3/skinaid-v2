from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session as get_db
from app.modules.audit.audit_repository import AuditRepository
from app.modules.audit.services.audit_service import AuditService
from app.modules.audit.services.statistics_service import StatisticsService


DbSession = Annotated[AsyncSession, Depends(get_db)]


def get_audit_repository(db: DbSession) -> AuditRepository:
    return AuditRepository(db)


AuditRepo = Annotated[AuditRepository, Depends(get_audit_repository)]


def get_audit_service(repo: AuditRepo) -> AuditService:
    return AuditService(repo)


AuditSvc = Annotated[AuditService, Depends(get_audit_service)]


def get_statistics_service(db: DbSession) -> StatisticsService:
    return StatisticsService(db)


StatisticsSvc = Annotated[StatisticsService, Depends(get_statistics_service)]
