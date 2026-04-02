from typing import Optional, List, Dict, Any
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from .database import get_db
from .token import extract_token, decode_and_verify_token
from .oauth2 import oauth2_scheme, oauth2_scheme_optional
from .user import (
    get_user_by_id,
    check_email_verified,
    check_user_has_role,
    check_user_has_permission
)
from app.modules.users.models import User


async def get_token(token: str = Depends(oauth2_scheme)) -> str:
    return token


async def get_current_user(
    token: str = Depends(get_token),
    db: AsyncSession = Depends(get_db)
) -> User:
    payload = await decode_and_verify_token(token, db, token_type="access")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if user.last_active_at is None or (now - user.last_active_at).total_seconds() > 300:
        user.last_active_at = now
        db.add(user)
        await db.commit()

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    return current_user


async def get_current_verified_user(
    current_user: User = Depends(get_current_user)
) -> Optional[Dict[str, Any]]:
    await check_email_verified(current_user, required=True)

    return {
        "user_id": str(current_user.user_id),
        "email": current_user.email,
        "is_verified": current_user.is_verified,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at,
        "updated_at": current_user.updated_at
    }


def allow_access(
    require_auth: bool = False,
    require_verified: bool = False,
    allow_guest_only: bool = False,
):
    async def dependency(
        token: Optional[str] = Depends(oauth2_scheme_optional),
        db: AsyncSession = Depends(get_db),
    ) -> Optional[User]:

        if allow_guest_only and token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Authenticated users cannot access this route",
            )

        if not token:
            if require_auth:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return None

        try:
            payload = await decode_and_verify_token(token, db, token_type="access")
        except HTTPException:
            if require_auth:
                raise
            return None

        user_id = payload.get("sub")
        if not user_id:
            if require_auth:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return None

        user = await get_user_by_id(db, user_id)
        if not user:
            if require_auth:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found or inactive",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return None

        if require_verified:
            await check_email_verified(user, required=True)

        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if user.last_active_at is None or (now - user.last_active_at).total_seconds() > 300:
            user.last_active_at = now
            db.add(user)
            await db.commit()

        return user

    return dependency


def require_role(allowed_roles: List[str], require_verified: bool = True):
    async def dependency(
        user: User = Depends(allow_access(require_auth=True, require_verified=require_verified)),
        db: AsyncSession = Depends(get_db),
    ) -> User:

        for role in allowed_roles:
            if await check_user_has_role(db, str(user.user_id), role):
                return user

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"One of these roles required: {', '.join(allowed_roles)}",
        )

    return dependency


def require_permission(permission_name: str, require_verified: bool = True):
    async def dependency(
        user: User = Depends(allow_access(require_auth=True, require_verified=require_verified)),
        db: AsyncSession = Depends(get_db),
    ) -> User:

        if not await check_user_has_permission(db, str(user.user_id), permission_name):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission_name}' required",
            )

        return user

    return dependency


def require_any_permissions(allowed_permissions: List[str], require_verified: bool = True):
    async def dependency(
        user: User = Depends(allow_access(require_auth=True, require_verified=require_verified)),
        db: AsyncSession = Depends(get_db),
    ) -> User:

        for perm in allowed_permissions:
            if await check_user_has_permission(db, str(user.user_id), perm):
                return user

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"At least one of these permissions required: {', '.join(allowed_permissions)}",
        )

    return dependency


def require_all_permissions(required_permissions: List[str], require_verified: bool = True):
    async def dependency(
        user: User = Depends(allow_access(require_auth=True, require_verified=require_verified)),
        db: AsyncSession = Depends(get_db),
    ) -> User:

        for perm in required_permissions:
            if not await check_user_has_permission(db, str(user.user_id), perm):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission '{perm}' required",
                )

        return user

    return dependency


allow_guest = allow_access(require_auth=False, require_verified=False)
require_auth = allow_access(require_auth=True, require_verified=False)
require_verified = allow_access(require_auth=True, require_verified=True)
guest_only = allow_access(allow_guest_only=True)

require_admin = require_role(["admin"])
require_user = require_role(["user"])
require_admin_or_moderator = require_role(["admin", "moderator"])

require_upload = require_permission("upload_image")
require_ai_analyze = require_permission("ai_analyze")
require_manage_users = require_permission("manage_users")
require_manage_firstaid = require_permission("manage_firstaid")
require_read_all_history = require_permission("read_all_history")
require_read_logs = require_permission("read_logs")