import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.core.cors import setup_cors
from app.core.events import lifespan

# Khởi tạo FastAPI app với lifespan
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description=settings.APP_DESCRIPTION,
    lifespan=lifespan,
)

# Setup CORS
setup_cors(app)

from app.api.v1.api import router as api_router
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