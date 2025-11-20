from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.database import get_async_session
from app.modules.auth.services.token_cleanup_service import TokenCleanupService
import logging

logger = logging.getLogger(__name__)

async def run_token_cleanup():
    """
    Scheduled task: Cleanup expired tokens
    Chạy định kỳ (ví dụ: mỗi giờ)
    """
    logger.info("Bắt đầu scheduled token cleanup")
    
    async for session in get_async_session():
        try:
            result = await TokenCleanupService.cleanup_all(session)
            logger.info(f"Token cleanup hoàn tất: {result}")
        except Exception as e:
            logger.error(f"Token cleanup thất bại: {str(e)}", exc_info=True)
        finally:
            await session.close()