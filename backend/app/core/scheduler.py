# app/core/scheduler.py (NEW FILE)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.core.database import async_session_maker
from app.core.tasks.cleanup_tokens import (
    cleanup_expired_tokens,
    cleanup_old_verification_tokens
)
import logging

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


# app/core/scheduler.py

async def daily_cleanup_job():
    """Scheduled job: Cleanup mỗi ngày lúc 3:00 AM"""
    logger.info("[Scheduler] Starting daily cleanup job...")
    
    async with async_session_maker() as db:
        try:
            from app.core.tasks.cleanup_tokens import cleanup_all
            
            # Run full cleanup
            results = await cleanup_all(db)
            
            logger.info(
                f"[Scheduler] Daily cleanup completed: "
                f"{results['blacklist_tokens']} blacklist tokens, "
                f"{results['verification_tokens']} verification tokens, "
                f"{results['token_families']} token families"
            )
            
        except Exception as e:
            logger.error(f"[Scheduler] Cleanup job failed: {str(e)}", exc_info=True)


def start_scheduler():
    """
    Khởi động background scheduler
    """
    try:
        scheduler.add_job(
            daily_cleanup_job,
            CronTrigger(hour=3, minute=0),  # 3:00 AM daily
            id="daily_cleanup",
            name="Daily Token Cleanup",
            replace_existing=True
        )
        
        # Start scheduler
        scheduler.start()
        logger.info("[Scheduler] cheduler started successfully")
        logger.info("[Scheduler] Daily cleanup scheduled at 3:00 AM")
        
    except Exception as e:
        logger.error(f"[Scheduler] Failed to start scheduler: {str(e)}", exc_info=True)


def shutdown_scheduler():
    """
    Dừng scheduler một cách graceful
    """
    try:
        if scheduler.running:
            scheduler.shutdown(wait=True)
            logger.info("[Scheduler] Scheduler shutdown successfully")
        else:
            logger.warning("[Scheduler] Scheduler was not running")
            
    except Exception as e:
        logger.error(f"[Scheduler] Error during scheduler shutdown: {str(e)}", exc_info=True)

async def trigger_cleanup_now():
    """
    Manually trigger cleanup (for testing/admin purposes)
    """
    logger.info("[Scheduler] Manual cleanup triggered")
    await daily_cleanup_job()