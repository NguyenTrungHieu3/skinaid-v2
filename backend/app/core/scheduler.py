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


async def cleanup_expired_guest_sessions():
    logger.info("Cleanup task: Expired guest sessions (stub)")
    print("🧹 Running cleanup: Expired guest sessions (stub)")


async def cleanup_expired_tokens():
    logger.info("Cleanup task: Expired tokens (stub)")
    print("🧹 Running cleanup: Expired tokens (stub)")


async def cleanup_old_chat_sessions():
    logger.info("Cleanup task: Old chat sessions (stub)")
    print("🧹 Running cleanup: Old chat sessions (stub)")
