from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import text
from datetime import datetime, timezone
import uuid
from app.core.Security.jwt import jwt_handler
from app.modules.auth.models.token_blacklist import TokenBlacklist

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
        # Phiên bản token cũ hơn current version → đã bị thu hồi tất cả
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
    # Giải mã token (không xác thực exp vì có thể token đã hết hạn)
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