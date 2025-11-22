from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import text
from datetime import datetime, timezone
from typing import Dict
import logging

logger = logging.getLogger(__name__)

class TokenCleanupService:
    
    @staticmethod
    async def cleanup_old_verification_tokens(db: AsyncSession) -> int:
        """Xóa verification tokens đã hết hạn hoặc đã sử dụng"""
        query = text("""
            DELETE FROM verification_tokens
            WHERE expires_at < NOW() OR is_used = true
        """)
        
        result = await db.execute(query)
        await db.commit()
        
        deleted_count = result.rowcount
        logger.info(f"[Cleanup] Đã xóa {deleted_count} verification tokens")
        return deleted_count
    
    @staticmethod
    async def cleanup_expired_tokens(db: AsyncSession) -> int:
        """Xóa token đã hết hạn khỏi blacklist"""
        query = text("""
            DELETE FROM token_blacklist
            WHERE expires_at < NOW()
        """)
        
        result = await db.execute(query)
        await db.commit()
        
        deleted_count = result.rowcount
        logger.info(f"[Cleanup] Đã xóa {deleted_count} expired blacklist tokens")
        return deleted_count
    
    @staticmethod
    async def cleanup_expired_token_families(db: AsyncSession) -> int:
        """Dọn dẹp token families đã hết hạn"""
        query = text("""
            DELETE FROM token_families
            WHERE expires_at < NOW()
        """)
        
        result = await db.execute(query)
        await db.commit()
        
        deleted_count = result.rowcount
        logger.info(f"[Cleanup] Đã xóa {deleted_count} token families")
        return deleted_count
    
    @staticmethod
    async def cleanup_all(db: AsyncSession) -> Dict[str, int]:
        """Dọn dẹp tất cả expired tokens"""
        service = TokenCleanupService()
        
        blacklist_count = await service.cleanup_expired_tokens(db)
        verification_count = await service.cleanup_old_verification_tokens(db)
        families_count = await service.cleanup_expired_token_families(db)
        
        logger.info(
            f"Cleanup hoàn tất: {blacklist_count} blacklist, "
            f"{verification_count} verifications, "
            f"{families_count} families"
        )
        
        return {
            "blacklist_tokens": blacklist_count,
            "verification_tokens": verification_count,
            "token_families": families_count
        }
    
    @staticmethod
    async def get_cleanup_stats(db: AsyncSession) -> Dict:
        """Lấy thống kê các records cần cleanup"""
        blacklist_query = text("""
            SELECT COUNT(*) FROM token_blacklist
            WHERE expires_at < NOW()
        """)
        verification_query = text("""
            SELECT COUNT(*) FROM verification_tokens
            WHERE expires_at < NOW() OR is_used = true
        """)
        
        result = await db.execute(blacklist_query)
        blacklist_count = result.scalar() or 0
        
        result = await db.execute(verification_query)
        verification_count = result.scalar() or 0
        
        return {
            "expired_blacklist_tokens": blacklist_count,
            "expired_verification_tokens": verification_count
        }