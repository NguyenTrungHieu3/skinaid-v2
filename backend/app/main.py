import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.v1.api import router as api_router
from app.core.config import settings
from app.core.events import lifespan
from app.middleware.cors import setup_cors
from app.middleware.rate_limit import limiter
from app.shared.exceptions import (
    AppException,
    app_exception_handler,
    generic_exception_handler,
)



app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description=settings.APP_DESCRIPTION,
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

setup_cors(app)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.VERSION,
        "docs_url": "/docs",
        "redoc_url": "/redoc",
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "project": settings.APP_NAME,
        "version": settings.VERSION,
    }


UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(exist_ok=True)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
