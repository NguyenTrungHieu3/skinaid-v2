from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.redis import init_redis, close_redis
from app.core.scheduler import start_scheduler, shutdown_scheduler
from app.core.startup import run_startup_checks
from app.modules.rag.services.qdrant_service import qdrant_service
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

    print("Connecting to Redis...")
    await init_redis()
    print("Redis ready")

    print("Running seed data...")
    await run_seed_data()
    print("Seed data complete")

    print("Starting scheduler...")
    start_scheduler()
    print("Scheduler ready (cleanup: 3:00 AM daily)")

    print("Initializing Qdrant (RAG vector store)...")
    await qdrant_service.initialize()
    print("Qdrant ready")

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

    print("Closing Redis connection...")
    await close_redis()
    print("Redis connection closed")

    print("Closing Qdrant connection...")
    await qdrant_service.close()
    print("Qdrant connection closed")

    print("=" * 50)
    print("Server stopped")
    print("=" * 50)