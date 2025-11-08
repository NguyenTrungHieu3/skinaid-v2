from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import text
from datetime import datetime, timezone
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

async def cleanup_old_verification_tokens(db: AsyncSession) -> int: 
    """
    Xóa verification tokens đã hết hạn hoặc đã sử dụng
    """
    query =text ("""
        DELETE FROM verification_tokens
        WHERE expires_at < NOW() OR is_used = true
    """)

    result = await db.execute(query)
    await db.commit()

    deleted_count = result.rowcount 
    logger.info(f"[Cleanup] Deleted {deleted_count} verification tokens")

    return deleted_count

async def cleanup_expired_tokens(db: AsyncSession) -> int: 
    """
    Xóa token đã hết hạn khỏi blacklist
    """
    query = text("""
        DELETE FROM token_blacklist
        WHERE expires_at < NOW() 
    """)

    result = await db.execute(query)
    await db.commit()

    deleted_count = result.rowcount
    logger.info(f"[Cleanup] Deleted {deleted_count} expired blacklist tokens")

    return deleted_count

async def get_blacklist_stats(db: AsyncSession) -> Dict: 
    """
    Lấy thống kê token blacklist
    """

    query = text(""" 
        SELECT 
            COUNT(*) as total_tokens,
            COUNT(*) FILTER (WHERE token_type = 'access') as access_tokens,
            COUNT(*) FILTER (WHERE token_type = 'refresh') as refresh_tokens,
            COUNT(*) FILTER (WHERE expires_at < NOW()) as expired_tokens,
            COUNT(*) FILTER (WHERE expires_at >= NOW()) as active_tokens,
            COUNT(DISTINCT user_id) as unique_users,
            MIN(revoked_at) as oldest_revoked,
            MAX(revoked_at) as newest_revoked,
            AVG(EXTRACT(EPOCH FROM (expires_at - revoked_at))) as avg_ttl_seconds
        FROM token_blacklist    
    """)

    result = await db.execute(query)
    row = result.mappings().first()

    if not row: 
        return {
            "total_tokens": 0,
            "access_tokens": 0,
            "refresh_tokens": 0,
            "expired_tokens": 0,
            "active_tokens": 0,
            "unique_users": 0,
            "oldest_revoked": None,
            "newest_revoked": None,
            "avg_ttl_hours": 0
        }
    
    stats = dict(row)

    if stats.get("avg_ttl_seconds"): 
        stats["avg_ttl_hours"] = round(stats["avg_ttl_seconds"] / 3600, 2)
    else: 
        stats["avg_ttl_hours"] = 0
    
    stats.pop("avg_ttl_seconds", None)
    return stats

async def revoke_all_user_tokens(db: AsyncSession, user_id: str) -> Dict: 
    """
    Revoke tất cả tokens của user bằng cách increment token_version
    Tất cả tokens cũ sẽ tự động invalid khi verify
    """
    query = text("""
        UPDATE users
        SET token_version = token_version + 1,
            updated_at = NOW()
        WHERE user_id = CAST(:user_id AS UUID)
        RETURNING token_version - 1 as old_version, token_version as new_version
    """)

    result = await db.execute(query, {"user_id": user_id})
    row = result.first()
    await db.commit()

    if not row: 
        logger.warning(f"[Revoke] User {user_id} not found")
        return {
            "success": False,
            "user_id": user_id, 
            "message": "User not found"
        }
    
    old_version = row[0]
    new_version = row[1]

    logger.info(f"[Revoke] All tokens for user {user_id}: v{old_version} -> v{new_version}")
    return{
        "success": True,
        "user_id": user_id, 
        "old_version": old_version, 
        "new_version": new_version, 
        "message": f"All tokens revoked. User must login again"
    }

async def get_user_token_version(db: AsyncSession, user_id: str)-> Optional[int]: 
    """
    Lấy token version hiện tại của user
    """
    query = text(""" 
        SELECT token_version
        FROM users
        WHERE user_id = CAST(:user_id AS UUID)
    """)

    result = await db.execute(query, {"user_id": user_id})
    row = result.first()

    return row[0] if row else None 

async def get_cleanup_stats(db:AsyncSession)-> Dict: 
    """
    Lấy thống kê tổng quan về các records cần cleanup
    """

    # Count expired blacklist tokens
    blacklist_query = text("""
        SELECT COUNT(*) FROM token_blacklist
        WHERE expires_at < NOW()
    """)
    result = await db.execute(blacklist_query)
    blacklist_count = result.scalar() or 0 

    # Count expired verification tokens
    verification_query = text("""
        SELECT COUNT(*) FROM verification_tokens 
        WHERE expires_at < NOW() OR is_used = true
    """)
    result = await db.execute(verification_query)
    verification_count = result.scalar() or 0
    
    return {
        "expired_blacklist_tokens": blacklist_count,
        "expired_verification_tokens": verification_count
    }

from app.core.tasks.token_family_service import cleanup_expired_token_families
async def cleanup_all(db: AsyncSession) -> Dict[str, int]:
    """
    Cleanup all expired records
    """
    blacklist_count = await cleanup_expired_tokens(db)
    verification_count = await cleanup_old_verification_tokens(db)
    families_count = await cleanup_expired_token_families(db)
    
    logger.info(
        f"Full cleanup: {blacklist_count} blacklist, "
        f"{verification_count} verifications, "
        f"{families_count} token families"
    )
    
    return {
        "blacklist_tokens": blacklist_count,
        "verification_tokens": verification_count,
        "token_families": families_count
    }



