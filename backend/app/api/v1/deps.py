from typing import Optional, List, Dict, Any
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import text
from datetime import datetime, timezone
import uuid

from app.core.database import get_session
from app.modules.auth.models.user import User
from app.modules.auth.models.token_blacklist import TokenBlacklist
from app.core.Security.jwt import jwt_handler

get_db = get_session


# ==================== TOKEN HELPERS ====================

async def extract_token(authorization: Optional[str]) -> Optional[str]:
    """
    Tách token từ header Authorization: Bearer <token>
    
    Returns:
        Token string hoặc None nếu không có header
        
    Raises:
        HTTPException: Nếu format header sai
    """
    if not authorization:
        return None

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return authorization.split(" ")[1]


async def is_token_blacklisted(db: AsyncSession, jti: str) -> bool:
    """
    Kiểm tra token có trong blacklist không
    
    Args:
        db: Database session
        jti: JWT ID
        
    Returns:
        True nếu token đã bị revoke
    """
    query = text("""
        SELECT EXISTS(
            SELECT 1 FROM token_blacklist 
            WHERE jti = :jti
        ) AS is_blacklisted
    """)
    
    result = await db.execute(query, {"jti": jti})
    row = result.first()
    
    return row[0] if row else False


async def decode_and_verify_token(
    token: str,
    db: AsyncSession,
    token_type: Optional[str] = None,
    check_blacklist: bool = True
) -> Dict[str, Any]:
    """
    Decode token và verify đầy đủ (type + blacklist)
    
    Args:
        token: JWT token string
        db: Database session
        token_type: Optional - "access" hoặc "refresh" để validate type
        check_blacklist: Có check blacklist không (default: True)
        
    Returns:
        Token payload đã verified
        
    Raises:
        HTTPException: Nếu token invalid/expired/blacklisted/wrong type
    """
    # 1. Decode token
    payload = jwt_handler.decode_token(token, verify_exp=True)
    
    # 2. Verify token type 
    if token_type:
        jwt_handler.verify_token_type(payload, token_type)
    # 3. check token version ** revoke all detection
    user_id = payload.get("sub")
    token_version = payload.get("ver", 0)

    if user_id: 
        # query kiểm tra token version của user
        version_query = text(""" 
            SELECT token_version
            FROM users
            WHERE user_id = CAST(:user_id AS UUID)
        """)
        result = await db.execute(version_query, {"user_id": user_id})
        row = result.first()

        if not row: 
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        current_version = row[0]
        # Token version cũ hơn current version → đã bị revoke all
        if token_version < current_version: 
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked. Please login again.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
    # 4. Check blacklist **individual token revoke
    if check_blacklist:
        jti = payload.get("jti")
        if jti and await is_token_blacklisted(db, jti):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    return payload


async def revoke_token(
    db: AsyncSession,
    token: str,
    user_id: Optional[str] = None
) -> TokenBlacklist:
    """
    Thu hồi token và thêm vào blacklist
    
    Args:
        db: Database session
        token: JWT token cần revoke
        user_id: Optional user_id (nếu không có sẽ lấy từ token)
        
    Returns:
        TokenBlacklist entry đã tạo
        
    Raises:
        HTTPException: Nếu token invalid hoặc đã bị revoke
    """
    # Decode token (không verify exp vì có thể token đã hết hạn)
    payload = jwt_handler.decode_token(token, verify_exp=False)
    
    jti = payload.get("jti")
    if not jti:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token does not contain JTI"
        )
    
    # Kiểm tra đã bị revoke chưa
    if await is_token_blacklisted(db, jti):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token already revoked"
        )
    
    # Lấy thông tin từ payload
    exp_timestamp = payload.get("exp")
    expires_at = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
    token_type = payload.get("type", "access")
    
    # Lấy user_id từ token nếu không được truyền vào
    if not user_id:
        user_id = payload.get("sub")
    
    # Chuẩn bị dữ liệu cho token_blacklist
    tokenblacklist_id = uuid.uuid4()
    revoked_at = datetime.now(timezone.utc)
    
    # Insert vào database
    query = text("""
        INSERT INTO token_blacklist (
            tokenblacklist_id, 
            jti, 
            user_id, 
            token_type, 
            revoked_at, 
            expires_at
        )
        VALUES (
            CAST(:tokenblacklist_id AS UUID),
            :jti,
            CAST(:user_id AS UUID),
            :token_type,
            :revoked_at,
            :expires_at
        )
    """)
    
    await db.execute(query, {
        "tokenblacklist_id": str(tokenblacklist_id),
        "jti": jti,
        "user_id": user_id,
        "token_type": token_type,
        "revoked_at": revoked_at,
        "expires_at": expires_at
    })
    
    await db.commit()
    
    # Tạo object để return
    blacklist_entry = TokenBlacklist(
        tokenblacklist_id=tokenblacklist_id,
        jti=jti,
        user_id=uuid.UUID(user_id) if user_id else None,
        token_type=token_type,
        revoked_at=revoked_at,
        expires_at=expires_at
    )
    
    return blacklist_entry


# async def revoke_token_returning(
#     db: AsyncSession,
#     token: str,
#     user_id: Optional[str] = None
# ) -> TokenBlacklist:
#     """
#     Thu hồi token và thêm vào blacklist với RETURNING
#     Alternative version sử dụng RETURNING để lấy record vừa insert
    
#     Args:
#         db: Database session
#         token: JWT token cần revoke
#         user_id: Optional user_id
        
#     Returns:
#         TokenBlacklist entry từ database
#     """
#     # Decode token
#     payload = jwt_handler.decode_token(token, verify_exp=False)
    
#     jti = payload.get("jti")
#     if not jti:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Token does not contain JTI"
#         )
    
#     # Kiểm tra đã bị revoke chưa
#     if await is_token_blacklisted(db, jti):
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Token already revoked"
#         )
    
#     # Lấy thông tin từ payload
#     exp_timestamp = payload.get("exp")
#     expires_at = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
#     token_type = payload.get("type", "access")
    
#     if not user_id:
#         user_id = payload.get("sub")
    
#     tokenblacklist_id = uuid.uuid4()
#     revoked_at = datetime.now(timezone.utc)
    
#     # Insert với RETURNING
#     query = text("""
#         INSERT INTO token_blacklist (
#             tokenblacklist_id, 
#             jti, 
#             user_id, 
#             token_type, 
#             revoked_at, 
#             expires_at
#         )
#         VALUES (
#             CAST(:tokenblacklist_id AS UUID),
#             :jti,
#             CAST(:user_id AS UUID),
#             :token_type,
#             :revoked_at,
#             :expires_at
#         )
#         RETURNING *
#     """)
    
#     result = await db.execute(query, {
#         "tokenblacklist_id": str(tokenblacklist_id),
#         "jti": jti,
#         "user_id": user_id,
#         "token_type": token_type,
#         "revoked_at": revoked_at,
#         "expires_at": expires_at
#     })
    
#     await db.commit()
    
#     # Lấy row vừa insert
#     row = result.mappings().first()
#     if not row:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Failed to revoke token"
#         )
    
#     return TokenBlacklist.model_validate(dict(row))


# ==================== USER HELPERS ====================

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


# ==================== BASIC DEPENDENCIES ====================

async def get_token(authorization: Optional[str] = Header(None)) -> str:
    """
    Dependency: Extract token từ Authorization header
    
    Raises:
        HTTPException: Nếu không có header
    """
    token = await extract_token(authorization)
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token


async def get_current_user(
    token: str = Depends(get_token),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency: Lấy user hiện tại từ access token
    
    Returns:
        User object
        
    Raises:
        HTTPException: Nếu token invalid/revoked hoặc user không tồn tại
    """
    # Decode và verify token
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

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    return current_user


async def get_current_verified_user(
    current_user: User = Depends(get_current_user)
) -> Optional[Dict[str, Any]]:
    """
    Dependency: Lấy user hiện tại đã verified dưới dạng dict

    Returns:
        Dict chứa thông tin user hoặc None nếu chưa verified

    Raises:
        HTTPException: Nếu user chưa verified
    """
    await check_email_verified(current_user, required=True)

    return {
        "user_id": str(current_user.user_id),
        "email": current_user.email,
        "is_verified": current_user.is_verified,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at,
        "updated_at": current_user.updated_at
    }


# ==================== FLEXIBLE ACCESS CONTROL ====================

def allow_access(
    require_auth: bool = False,
    require_verified: bool = False,
    allow_guest_only: bool = False,
):
    """
    Factory function tạo flexible access control dependency
    
    Args:
        require_auth: Bắt buộc đăng nhập (reject nếu không có token)
        require_verified: Bắt buộc email verified (cần require_auth=True)
        allow_guest_only: Chỉ cho guest (reject nếu có token hợp lệ)
    
    Returns:
        Dependency function trả về User object hoặc None
        
    Examples:
        # Public route, optional auth
        @app.get("/posts", dependencies=[Depends(allow_access())])
        
        # Require login
        @app.get("/profile", dependencies=[Depends(allow_access(require_auth=True))])
        
        # Require login + verified email
        @app.post("/upload", dependencies=[Depends(allow_access(require_auth=True, require_verified=True))])
        
        # Guest only (register, login)
        @app.post("/register", dependencies=[Depends(allow_access(allow_guest_only=True))])
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

        # Verify token (with blacklist check)
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

        # Get user
        user = await get_user_by_id(db, user_id)
        if not user:
            if require_auth:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found or inactive",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return None

        # Check email verification
        if require_verified:
            await check_email_verified(user, required=True)

        return user

    return dependency


# ==================== ROLE-BASED ACCESS CONTROL ====================

def require_role(allowed_roles: List[str], require_verified: bool = True):
    """
    Factory function: Yêu cầu user có ít nhất 1 role trong danh sách
    
    Args:
        allowed_roles: Danh sách role được phép (OR logic)
        require_verified: Có yêu cầu email verified không
        
    Returns:
        Dependency function trả về User object
        
    Example:
        @app.get("/admin", dependencies=[Depends(require_role(["admin"]))])
        @app.get("/content", dependencies=[Depends(require_role(["admin", "moderator"]))])
    """
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


# ==================== PERMISSION-BASED ACCESS CONTROL ====================

def require_permission(permission_name: str, require_verified: bool = True):
    """
    Factory function: Yêu cầu user có 1 permission cụ thể
    
    Args:
        permission_name: Tên permission cần có
        require_verified: Có yêu cầu email verified không
        
    Returns:
        Dependency function trả về User object
        
    Example:
        @app.post("/upload", dependencies=[Depends(require_permission("upload_image"))])
    """
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
    """
    Factory function: User có ÍT NHẤT 1 permission trong danh sách
    
    Args:
        allowed_permissions: Danh sách permissions (OR logic)
        require_verified: Có yêu cầu email verified không
        
    Returns:
        Dependency function trả về User object
        
    Example:
        @app.post("/moderate", dependencies=[Depends(require_any_permissions(["edit_post", "delete_post"]))])
    """
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
    """
    Factory function: User có TẤT CẢ permissions trong danh sách
    
    Args:
        required_permissions: Danh sách permissions (AND logic)
        require_verified: Có yêu cầu email verified không
        
    Returns:
        Dependency function trả về User object
        
    Example:
        @app.delete("/user/{id}", dependencies=[Depends(require_all_permissions(["manage_users", "delete_users"]))])
    """
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


# ==================== COMMON SHORTCUTS ====================

# Access level shortcuts
allow_guest = allow_access(require_auth=False, require_verified=False)
require_auth = allow_access(require_auth=True, require_verified=False)
require_verified = allow_access(require_auth=True, require_verified=True)
guest_only = allow_access(allow_guest_only=True)

# --- BỔ SUNG DÒNG NÀY ---
# Dependency này sẽ trả về User nếu có token, hoặc None nếu không có token (không báo lỗi 401)
get_optional_user = allow_access(require_auth=False, require_verified=False)

# Role shortcuts
require_admin = require_role(["admin"])
require_user = require_role(["user"])
require_admin_or_moderator = require_role(["admin", "moderator"])

# Permission shortcuts
require_upload = require_permission("upload_image")
require_ai_analyze = require_permission("ai_analyze")
require_manage_users = require_permission("manage_users")
require_manage_firstaid = require_permission("manage_firstaid")
require_read_all_history = require_permission("read_all_history")
require_read_logs = require_permission("read_logs")

