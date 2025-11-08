from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.database import init_db
from app.core.scheduler import start_scheduler, shutdown_scheduler
from app.utils.startup import run_startup_checks
import logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # ========== STARTUP ==========
    print("=" * 50)
    print("Máy chủ đang khởi động...")
    print("=" * 50)
    
    # Run startup checks
    run_startup_checks()
    
    # Initialize database
    print("Đang khởi tạo database...")
    await init_db()
    print("Database đã sẵn sàng")
    
    # Start scheduler
    print("Đang khởi động scheduler...")
    start_scheduler()
    print("Scheduler đã sẵn sàng (cleanup: 3:00 AM daily)")
    
    print("=" * 50)
    print("Máy chủ đã khởi động thành công!")
    print(f"App: {app.title} v{app.version}")
    print(f"API Docs: http://localhost:8000{app.docs_url}")
    print("=" * 50)
    
    yield
    
    # ========== SHUTDOWN ==========
    print("\n" + "=" * 50)
    print("Máy chủ đang dừng...")
    print("=" * 50)
    
    print("Đang dừng scheduler...")
    shutdown_scheduler()
    print("Scheduler đã dừng")
    
    print("=" * 50)
    print("Máy chủ đã dừng hoàn toàn!")
    print("=" * 50)