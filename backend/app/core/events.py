from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.database import init_db
from app.core.scheduler import start_scheduler, shutdown_scheduler
from app.utils.startup import run_startup_checks
import logging
import os

logger = logging.getLogger(__name__)


async def run_seed_data():
    """Chạy seed data nếu cần"""
    try:
        # Import seed module
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        from seed_data import run_seed
        await run_seed()
    except ImportError as e:
        logger.warning(f"Không tìm thấy seed_data module: {e}")
    except Exception as e:
        logger.error(f"Lỗi khi chạy seed data: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Quản lý vòng đời ứng dụng"""
    # ========== KHỞI ĐỘNG ==========
    print("=" * 50)
    print("Server đang khởi động...")
    print("=" * 50)
    
    # Chạy các kiểm tra khởi động
    run_startup_checks()
    
    # Khởi tạo database
    print("Đang khởi tạo database...")
    await init_db()
    print("Database đã sẵn sàng")
    
    # Chạy seed data (tạo admin user và firstaid guides)
    print("Đang kiểm tra và seed dữ liệu...")
    await run_seed_data()
    print("Seed data hoàn tất")
    
    # Khởi động scheduler
    print("Đang khởi động scheduler...")
    start_scheduler()
    print("Scheduler đã sẵn sàng (cleanup: 3:00 AM daily)")
    
    print("=" * 50)
    print("Server đã khởi động thành công!")
    print(f"App: {app.title} v{app.version}")
    print(f"API Docs: http://localhost:8000{app.docs_url}")
    print("=" * 50)
    
    yield
    
    # ========== TẮT MÁY ==========
    print("\n" + "=" * 50)
    print("Server đang dừng...")
    print("=" * 50)
    
    print("Đang dừng scheduler...")
    shutdown_scheduler()
    print("Scheduler đã dừng")
    
    print("=" * 50)
    print("Server đã dừng hoàn toàn!")
    print("=" * 50)