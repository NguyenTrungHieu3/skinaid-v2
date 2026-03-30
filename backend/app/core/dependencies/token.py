from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import text
from datetime import datetime, timezone
from app.core.security.jwt import jwt_handler
from app.core.redis import get_redis


async def extract_token(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return authorization.split(" ")[1]


async def is_token_blacklisted(jti: str) -> bool:
    redis = get_redis()
    return await redis.exists(f"blacklist:{jti}") > 0


async def revoke_token(token: str, user_id: Optional[str] = None) -> bool:
    payload = jwt_handler.decode_token(token, verify_exp=False)

    jti = payload.get("jti")
    if not jti:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token does not contain JTI",
        )

    if await is_token_blacklisted(jti):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token already revoked",
        )

    exp_timestamp = payload.get("exp")
    if exp_timestamp:
        ttl = max(int(exp_timestamp - datetime.now(timezone.utc).timestamp()), 1)
    else:
        ttl = 7 * 24 * 3600

    redis = get_redis()
    await redis.set(f"blacklist:{jti}", 1, ex=ttl)
    return True


async def decode_and_verify_token(
    token: str,
    db: AsyncSession,
    token_type: Optional[str] = None,
    check_blacklist: bool = True,
) -> Dict[str, Any]:
    # 1. Decode
    payload = jwt_handler.decode_token(token, verify_exp=True)

    # 2. Verify type
    if token_type:
        jwt_handler.verify_token_type(payload, token_type)

    # 3. Check token version (logout-all-devices / change-password)
    user_id = payload.get("sub")
    token_version = payload.get("ver", 0)

    if user_id:
        result = await db.execute(
            text("SELECT token_version FROM users WHERE user_id = CAST(:uid AS UUID)"),
            {"uid": user_id},
        )
        row = result.first()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if token_version < row[0]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked. Please login again.",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # 4. Check Redis blacklist (individual revoke)
    if check_blacklist:
        jti = payload.get("jti")
        if jti and await is_token_blacklisted(jti):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )

    return payload
