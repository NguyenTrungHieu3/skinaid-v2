from typing import Optional, List
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import text

from app.core.database import get_session
from app.modules.auth.models.user import User
from app.core.Security.jwt import JWTHandler

jwt = JWTHandler()
get_db = get_session

async def extract_token(authorization: Optional[str]) -> Optional[str]:
    """Tách token từ header Authorization: Bearer <token>"""
    if not authorization:
        return None

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return authorization.split(" ")[1]


def decode_token(token: str) -> Optional[str]:
    """Giải mã JWT → trả về user_id nếu hợp lệ"""
    try:
        payload = jwt.verify_token(token)
        return payload.get("sub")
    except Exception:
        return None


async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
    """Lấy user từ DB (raw SQL)"""
    query = text("""
        SELECT * FROM users
        WHERE user_id = CAST(:user_id AS UUID)
        AND is_active = true
        AND is_deleted = false
    """)

    result = await db.execute(query, {"user_id": user_id})
    user_row = result.mappings().first()

    if user_row is None:
        return None

    return User.model_validate(dict(user_row))


async def check_email_verified(user: User, required: bool = True) -> None:
    """Kiểm tra email đã verified chưa"""
    if required and not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required",
        )


async def check_user_has_role(db: AsyncSession, user_id: str, role_name: str) -> bool:
    """Kiểm tra user có role cụ thể không"""
    query = text("""
        SELECT ur.user_id
        FROM user_roles ur
        JOIN roles r ON ur.role_id = r.role_id
        WHERE ur.user_id = CAST(:user_id AS UUID)
        AND r.role_name = :role_name
        AND r.is_active = true
        AND (ur.expires_at IS NULL OR ur.expires_at > NOW())
    """)
    result = await db.execute(query, {"user_id": user_id, "role_name": role_name})
    return result.first() is not None


async def check_user_has_permission(
    db: AsyncSession, user_id: str, permission_name: str
) -> bool:
    """Kiểm tra user có permission cụ thể không"""
    query = text("""
        SELECT p.permission_id
        FROM permissions p
        JOIN role_permissions rp ON p.permission_id = rp.permission_id
        JOIN user_roles ur ON rp.role_id = ur.role_id
        WHERE ur.user_id = CAST(:user_id AS UUID)
        AND p.permission_name = :permission_name
        AND (ur.expires_at IS NULL OR ur.expires_at > NOW())
    """)
    result = await db.execute(query, {"user_id": user_id, "permission_name": permission_name})
    return result.first() is not None

async def get_token(authorization: Optional[str] = Header(None)) -> str:
    token = await extract_token(authorization)
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token


async def get_current_user(
    token: str = Depends(get_token), db: AsyncSession = Depends(get_db)
) -> User:
    user_id = decode_token(token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    return current_user

def allow_access(
    require_auth: bool = False,
    require_verified: bool = False,
    allow_guest_only: bool = False,
):
    """
        require_auth: Bắt buộc đăng nhập
        require_verified: Bắt buộc xác minh email
        allow_guest_only: Chỉ cho guest (reject nếu có token)
    """
    async def dependency(
        authorization: Optional[str] = Header(None),
        db: AsyncSession = Depends(get_db),
    ) -> Optional[User]:

        token = await extract_token(authorization)

        # Guest-only routes (register, login, etc.)
        if allow_guest_only and token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Authenticated users cannot access this route",
            )

        # No token provided
        if not token:
            if require_auth:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return None

        # Verify token
        user_id = decode_token(token)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Get user
        user = await get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check email verification
        if require_verified:
            await check_email_verified(user, required=True)

        return user

    return dependency


def require_role(allowed_roles: List[str], require_verified: bool = True):
    """
    Yêu cầu user có ít nhất 1 role trong danh sách
    """
    async def dependency(
        user: User = Depends(allow_access(require_auth=True, require_verified=require_verified)),
        db: AsyncSession = Depends(get_db),
    ) -> User:

        for role in allowed_roles:
            if await check_user_has_role(db, user.user_id, role):
                return user

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"One of these roles required: {', '.join(allowed_roles)}",
        )

    return dependency


def require_permission(permission_name: str, require_verified: bool = True):
    """
    Yêu cầu user có 1 permission cụ thể
    """
    async def dependency(
        user: User = Depends(allow_access(require_auth=True, require_verified=require_verified)),
        db: AsyncSession = Depends(get_db),
    ) -> User:

        if not await check_user_has_permission(db, user.user_id, permission_name):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission_name}' required",
            )

        return user

    return dependency


def require_any_permissions(allowed_permissions: List[str], require_verified: bool = True):
    """
    Cho phép nếu user có ÍT NHẤT 1 permission trong danh sách
    """
    async def dependency(
        user: User = Depends(allow_access(require_auth=True, require_verified=require_verified)),
        db: AsyncSession = Depends(get_db),
    ) -> User:

        for perm in allowed_permissions:
            if await check_user_has_permission(db, user.user_id, perm):
                return user

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"At least one of these permissions required: {', '.join(allowed_permissions)}",
        )

    return dependency


def require_all_permissions(required_permissions: List[str], require_verified: bool = True):
    """
    Chỉ cho phép nếu user có TẤT CẢ permissions
    """
    async def dependency(
        user: User = Depends(allow_access(require_auth=True, require_verified=require_verified)),
        db: AsyncSession = Depends(get_db),
    ) -> User:

        for perm in required_permissions:
            if not await check_user_has_permission(db, user.user_id, perm):
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