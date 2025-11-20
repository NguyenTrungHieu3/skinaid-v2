from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.modules.auth.tasks.scheduled_cleanup import run_token_cleanup
import logging

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

def start_scheduler():
    
    # Token cleanup - chạy mỗi giờ
    scheduler.add_job(
        run_token_cleanup,
        trigger='cron',
        hour='*',  # Mỗi giờ
        id='token_cleanup',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("Scheduler đã khởi động với token cleanup task")

def shutdown_scheduler():
    """Dừng scheduler"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler đã dừng")