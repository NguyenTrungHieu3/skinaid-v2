import logging
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger(__name__)

_scheduler: Optional[AsyncIOScheduler] = None


def start_scheduler():
    global _scheduler
    try:
        _scheduler = AsyncIOScheduler()
        _scheduler.start()
        logger.info("Scheduler started successfully")
        print("✅ Scheduler started")
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")
        print(f"⚠️  Scheduler warning: {e}")


def shutdown_scheduler():
    global _scheduler
    if _scheduler:
        try:
            _scheduler.shutdown(wait=True)
            logger.info("Scheduler shutdown complete")
            print("✅ Scheduler stopped")
        except Exception as e:
            logger.error(f"Error during scheduler shutdown: {e}")
        finally:
            _scheduler = None


def get_scheduler() -> Optional[AsyncIOScheduler]:
    return _scheduler
