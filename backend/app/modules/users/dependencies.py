from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.modules.audit.audit_repository import AuditRepository
from app.modules.audit.services.audit_service import AuditService
from app.modules.auth.repository.token_repository import TokenRepository
from app.modules.users.repository.profile_repository import ProfileRepository
from app.modules.users.repository.user_repository import UserRepository
from app.modules.users.services.profile_service import ProfileService
from app.modules.users.services.user_service import UserService


DbSession = Annotated[AsyncSession, Depends(get_db)]


def get_profile_repository(db: DbSession) -> ProfileRepository:
    return ProfileRepository(db)


def get_profile_service(
    repository: ProfileRepository = Depends(get_profile_repository),
) -> ProfileService:
    return ProfileService(repository)


ProfileRepo = Annotated[ProfileRepository, Depends(get_profile_repository)]
ProfileSvc  = Annotated[ProfileService,    Depends(get_profile_service)]


def get_user_repository(db: DbSession) -> UserRepository:
    return UserRepository(db)


def get_token_repository(db: DbSession) -> TokenRepository:
    return TokenRepository(db)


def get_user_audit_service(db: DbSession) -> AuditService:
    return AuditService(AuditRepository(db))


def get_user_service(
    db: DbSession,
    repository: UserRepository = Depends(get_user_repository),
    token_repository: TokenRepository = Depends(get_token_repository),
    audit_service: AuditService = Depends(get_user_audit_service),
) -> UserService:
    return UserService(
        db=db,
        repository=repository,
        token_repository=token_repository,
        audit_service=audit_service,
    )


UserRepo = Annotated[UserRepository, Depends(get_user_repository)]
UserSvc  = Annotated[UserService,    Depends(get_user_service)]
