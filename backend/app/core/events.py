from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.database import init_db
from app.core.scheduler import start_scheduler, shutdown_scheduler
from app.core.startup import run_startup_checks
import logging
import os

logger = logging.getLogger(__name__)


async def run_seed_data():
    try:
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        from seed_data import run_seed
        await run_seed()
    except ImportError as e:
        logger.warning(f"Seed data module not found: {e}")
    except Exception as e:
        logger.error(f"Error running seed data: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("=" * 50)
    print("Starting server...")
    print("=" * 50)

    run_startup_checks()

    print("Initializing database...")
    await init_db()
    print("Database ready")

    print("Running seed data...")
    await run_seed_data()
    print("Seed data complete")

    print("Starting scheduler...")
    start_scheduler()
    print("Scheduler ready (cleanup: 3:00 AM daily)")

    print("=" * 50)
    print("Server started successfully!")
    print(f"App: {app.title} v{app.version}")
    print(f"API Docs: http://localhost:8000{app.docs_url}")
    print("=" * 50)

    yield

    # Shutdown
    print("\n" + "=" * 50)
    print("Stopping server...")
    print("=" * 50)

    print("Stopping scheduler...")
    shutdown_scheduler()
    print("Scheduler stopped")

    print("=" * 50)
    print("Server stopped")
    print("=" * 50)