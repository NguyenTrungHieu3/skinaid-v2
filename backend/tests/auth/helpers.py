import uuid
from datetime import datetime, timedelta, timezone

from app.core.Security.jwt import JWTHandler
from app.core.Security.password import hash_password
from app.modules.auth.models.roles import Role
from app.modules.auth.models.token_family import TokenFamily
from app.modules.users.models.user import User
from app.modules.auth.models.user_roles import UserRole
from app.modules.auth.models.verification_token import VerificationToken
from app.modules.users.models.user_profile import UserProfile


def utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def build_user(
    *,
    user_name: str,
    email: str,
    password: str,
    is_verified: bool = True,
    is_active: bool = True,
) -> User:
    now = utc_now_naive()
    return User(
        user_name=user_name,
        email=email,
        hashed_password=hash_password(password),
        token_version=0,
        is_active=is_active,
        is_verified=is_verified,
        is_deleted=False,
        created_at=now,
        updated_at=now,
    )


def build_profile(*, user_id: uuid.UUID, full_name: str) -> UserProfile:
    now = utc_now_naive()
    return UserProfile(
        user_id=user_id,
        full_name=full_name,
        created_at=now,
        updated_at=now,
    )


def build_role(role_name: str = "user") -> Role:
    now = utc_now_naive()
    return Role(
        role_name=role_name,
        description=f"{role_name} role",
        is_active=True,
        created_at=now,
        updated_at=now,
    )


def build_user_role(user_id: uuid.UUID, role_id: uuid.UUID) -> UserRole:
    return UserRole(
        user_id=user_id,
        role_id=role_id,
        assigned_at=utc_now_naive(),
    )


def create_token_pair_for_user(user_id: uuid.UUID, token_version: int = 0) -> dict:
    return JWTHandler().create_token_pair(subject=str(user_id), token_version=token_version)


def build_token_family(
    *,
    user_id: uuid.UUID,
    refresh_jti: str,
    access_jti: str,
    expires_in_days: int = 7,
) -> TokenFamily:
    return TokenFamily(
        user_id=user_id,
        refresh_token_jti=refresh_jti,
        access_token_jti=access_jti,
        parent_jti=None,
        is_revoked=False,
        created_at=utc_now_naive(),
        expires_at=utc_now_naive() + timedelta(days=expires_in_days),
    )


def build_password_reset_token(email: str, token: str, expires_in_hours: int = 1) -> VerificationToken:
    now = utc_now_naive()
    return VerificationToken(
        email=email,
        token=token,
        token_type="password_reset",
        expires_at=now + timedelta(hours=expires_in_hours),
        is_used=False,
        created_at=now,
        updated_at=now,
    )
