"""
Auth Dependencies — Dependency Injection chain cho auth module.

Route inject AuthService, AuthService inject repositories.
Session do FastAPI DI cung cấp qua get_db.
"""

from typing import Any
import os
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.modules.auth.repository.token_repository import TokenRepository
from app.modules.auth.repository.user_repository import UserRepository
from app.modules.auth.service import AuthService


def get_user_repository(
    db: AsyncSession = Depends(get_db),
) -> UserRepository:
    """DI: UserRepository."""
    return UserRepository(db)


def get_token_repository(
    db: AsyncSession = Depends(get_db),
) -> TokenRepository:
    """DI: TokenRepository."""
    return TokenRepository(db)


def get_email_service() -> Any:
    """DI: EmailService (Mock or Real based on env)."""
    use_mock = (
        os.getenv("TESTING") == "true"
        or os.getenv("USE_MOCK_EMAIL") == "true"
    )
    if use_mock:
        from app.utils.mock_email_service import (
            mock_email_service as svc,
        )
    else:
        from app.utils.email_service import email_service as svc
    return svc


def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repository),
    token_repo: TokenRepository = Depends(get_token_repository),
    db: AsyncSession = Depends(get_db),
    email_service: Any = Depends(get_email_service),
) -> AuthService:
    """DI: AuthService with repositories injected."""
    return AuthService(
        user_repo=user_repo,
        token_repo=token_repo,
        db=db,
        email_service=email_service,
    )
