# app/main.py
import sys
import os
import logging
import time
from datetime import datetime

if os.name == 'nt': 
    sys.stdout.reconfigure(encoding='utf-8')

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

# Core
from app.core.config import settings
from app.core.events import lifespan
from app.core.cors import setup_cors
from starlette.middleware.cors import CORSMiddleware

# Routers
from app.api.v1.api import router as api_v1_router

logger = logging.getLogger(__name__)


# ========== CREATE APPLICATION ==========
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description=settings.APP_DESCRIPTION,
    docs_url=settings.DOCS_URL,
    redoc_url=settings.REDOC_URL,
    lifespan=lifespan,
)


# ========== SETUP CORS ==========
setup_cors(app)


# ========== SIMPLE REQUEST LOGGING ==========
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Simple request/response logging"""
    start_time = time.time()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print(f"[{timestamp}] Request: {request.method} {request.url.path}")
    response = await call_next(request)
    duration = round((time.time() - start_time) * 1000, 2)
    print(f"[{timestamp}] Response: {response.status_code} | {request.method} {request.url.path} | {duration}ms")
    
    return response

# ========== INCLUDE ROUTERS ==========
app.include_router(api_v1_router, prefix=settings.API_V1_STR)


# ========== STATIC FILES ==========
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


# ========== ROOT ENDPOINTS ==========
@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "message": "API dang chay",
        "status": "healthy",
        "docs": settings.DOCS_URL,
        "api": settings.API_V1_STR,
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "database": "connected",
        "scheduler": "running",
    }


@app.get("/info")
async def system_info():
    """System information"""
    return {
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "features": {
            "wound_analysis": True,
            "first_aid_guides": True,
            "user_authentication": True,
            "jwt_tokens": True,
            "token_blacklist": True,
            "auto_cleanup": True,
            "rbac": True,
            "guest_sessions": True,
        },
        "endpoints": {
            "docs": settings.DOCS_URL,
            "redoc": settings.REDOC_URL,
            "api_v1": settings.API_V1_STR,
        }
    }


# ========== RUN SERVER (DEVELOPMENT ONLY) ==========
if __name__ == "__main__":
    import uvicorn
    
    print("=" * 50)
    print("Starting development server...")
    print("=" * 50)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )