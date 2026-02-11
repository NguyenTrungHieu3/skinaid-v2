"""Scheduled task: Cleanup expired tokens (background scheduler)."""

import logging

from app.core.database import get_session
from app.modules.auth.repository.token_repository import TokenRepository

logger = logging.getLogger(__name__)


async def run_token_cleanup() -> None:
    """
    Scheduled task: Cleanup expired tokens.

    Chạy định kỳ (ví dụ: mỗi giờ).
    """
    logger.info("Bắt đầu scheduled token cleanup")

    async for session in get_session():
        try:
            token_repo = TokenRepository(session)
            result = await token_repo.cleanup_all()
            await session.commit()
            logger.info("Token cleanup hoàn tất: %s", result)
        except Exception as e:
            logger.error(
                "Token cleanup thất bại: %s", str(e), exc_info=True
            )
        finally:
            await session.close()
