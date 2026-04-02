from typing import Optional, List
from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy import select, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.users.models import User
from app.modules.auth.models.user_roles import UserRole
from app.modules.auth.models.roles import Role
from app.modules.auth.models.role_permissions import RolePermission
from app.modules.auth.models.permissions import Permission


async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
    """
    Lấy user từ database theo ID

    Args:
        db: Database session
        user_id: User UUID string

    Returns:
        User object hoặc None nếu không tìm thấy/inactive
    """
    result = await db.execute(
        select(User)
        .where(User.user_id == user_id)
        .where(User.is_active == True)
        .where(User.is_deleted == False)
    )

    return result.scalar_one_or_none()


async def check_email_verified(user: User, required: bool = True) -> None:
    """
    Kiểm tra email đã verified chưa

    Args:
        user: User object
        required: Có bắt buộc verified không

    Raises:
        HTTPException: Nếu email chưa verified mà required=True
    """
    if required and not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required",
        )


async def check_user_has_role(db: AsyncSession, user_id: str, role_name: str) -> bool:
    """
    Kiểm tra user có role cụ thể không

    Args:
        db: Database session
        user_id: User UUID string
        role_name: Tên role cần check

    Returns:
        True nếu user có role
    """
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    result = await db.execute(
        select(UserRole)
        .join(Role, UserRole.role_id == Role.role_id)
        .where(UserRole.user_id == user_id)
        .where(Role.role_name == role_name)
        .where(Role.is_active == True)
        .where(
            (UserRole.expires_at.is_(None)) | (UserRole.expires_at > now)
        )
    )

    return result.scalar_one_or_none() is not None


async def check_user_has_permission(
    db: AsyncSession, user_id: str, permission_name: str
) -> bool:
    """
    Kiểm tra user có permission cụ thể không

    Args:
        db: Database session
        user_id: User UUID string
        permission_name: Tên permission cần check

    Returns:
        True nếu user có permission
    """
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    result = await db.execute(
        select(Permission)
        .join(RolePermission, Permission.permission_id == RolePermission.permission_id)
        .join(UserRole, RolePermission.role_id == UserRole.role_id)
        .where(UserRole.user_id == user_id)
        .where(Permission.permission_name == permission_name)
        .where(
            (UserRole.expires_at.is_(None)) | (UserRole.expires_at > now)
        )
    )

    return result.scalar_one_or_none() is not None


async def get_user_roles(db: AsyncSession, user_id: str) -> List[str]:
    """
    Lấy tất cả roles của user

    Args:
        db: Database session
        user_id: User UUID string

    Returns:
        List tên roles
    """
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    result = await db.execute(
        select(Role.role_name)
        .join(UserRole, Role.role_id == UserRole.role_id)
        .where(UserRole.user_id == user_id)
        .where(Role.is_active == True)
        .where(
            (UserRole.expires_at.is_(None)) | (UserRole.expires_at > now)
        )
        .order_by(Role.role_name)
    )

    rows = result.scalars().all()
    return list(rows)


async def get_user_permissions(db: AsyncSession, user_id: str) -> List[str]:
    """
    Lấy tất cả permissions của user

    Args:
        db: Database session
        user_id: User UUID string

    Returns:
        List tên permissions (unique)
    """
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    result = await db.execute(
        select(distinct(Permission.permission_name))
        .join(RolePermission, Permission.permission_id == RolePermission.permission_id)
        .join(UserRole, RolePermission.role_id == UserRole.role_id)
        .where(UserRole.user_id == user_id)
        .where(
            (UserRole.expires_at.is_(None)) | (UserRole.expires_at > now)
        )
        .order_by(Permission.permission_name)
    )

    rows = result.scalars().all()
    return list(rows)
