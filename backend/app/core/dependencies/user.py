from typing import Optional, List
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import text
from app.modules.auth.models.user import User

async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
    """
    Lấy user từ database theo ID
    
    Args:
        db: Database session
        user_id: User UUID string
        
    Returns:
        User object hoặc None nếu không tìm thấy/inactive
    """
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
    query = text("""
        SELECT EXISTS(
            SELECT 1
            FROM user_roles ur
            JOIN roles r ON ur.role_id = r.role_id
            WHERE ur.user_id = CAST(:user_id AS UUID)
            AND r.role_name = :role_name
            AND r.is_active = true
            AND (ur.expires_at IS NULL OR ur.expires_at > NOW())
        ) AS has_role
    """)
    
    result = await db.execute(query, {"user_id": user_id, "role_name": role_name})
    row = result.first()
    
    return row[0] if row else False


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
    query = text("""
        SELECT EXISTS(
            SELECT 1
            FROM permissions p
            JOIN role_permissions rp ON p.permission_id = rp.permission_id
            JOIN user_roles ur ON rp.role_id = ur.role_id
            WHERE ur.user_id = CAST(:user_id AS UUID)
            AND p.permission_name = :permission_name
            AND (ur.expires_at IS NULL OR ur.expires_at > NOW())
        ) AS has_permission
    """)
    
    result = await db.execute(query, {"user_id": user_id, "permission_name": permission_name})
    row = result.first()
    
    return row[0] if row else False


async def get_user_roles(db: AsyncSession, user_id: str) -> List[str]:
    """
    Lấy tất cả roles của user
    
    Args:
        db: Database session
        user_id: User UUID string
        
    Returns:
        List tên roles
    """
    query = text("""
        SELECT r.role_name
        FROM user_roles ur
        JOIN roles r ON ur.role_id = r.role_id
        WHERE ur.user_id = CAST(:user_id AS UUID)
        AND r.is_active = true
        AND (ur.expires_at IS NULL OR ur.expires_at > NOW())
        ORDER BY r.role_name
    """)
    
    result = await db.execute(query, {"user_id": user_id})
    rows = result.fetchall()
    
    return [row[0] for row in rows]


async def get_user_permissions(db: AsyncSession, user_id: str) -> List[str]:
    """
    Lấy tất cả permissions của user
    
    Args:
        db: Database session
        user_id: User UUID string
        
    Returns:
        List tên permissions (unique)
    """
    query = text("""
        SELECT DISTINCT p.permission_name
        FROM permissions p
        JOIN role_permissions rp ON p.permission_id = rp.permission_id
        JOIN user_roles ur ON rp.role_id = ur.role_id
        WHERE ur.user_id = CAST(:user_id AS UUID)
        AND (ur.expires_at IS NULL OR ur.expires_at > NOW())
        ORDER BY p.permission_name
    """)
    
    result = await db.execute(query, {"user_id": user_id})
    rows = result.fetchall()
    
    return [row[0] for row in rows]
