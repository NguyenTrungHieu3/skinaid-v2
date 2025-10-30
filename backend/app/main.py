import sys
import os
if os.name == 'nt': 
    sys.stdout.reconfigure(encoding='utf-8')

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from app.core.database import init_db
from app.core.config import settings
from app.api.v1.api import router as api_v1_router
import logging
import os

logger = logging.getLogger(__name__)

@asynccontextmanager
async def life_span(app: FastAPI):
    print("Máy chủ khởi động !!!")
    debug_email_config_in_server()
    await init_db()
    yield
    print("Máy chủ đã dừng !!!")


def debug_email_config_in_server():
    """Debug function to check email configuration in server"""
    try:
        from app.utils.email_service import email_service

        print("=== EMAIL CONFIG DEBUG ===")
        print(f"SMTP Server: {email_service.smtp_server}")
        print(f"SMTP Port: {email_service.smtp_port}")
        print(f"Sender Email: {email_service.sender_email}")
        print(f"Password Configured: {'Yes' if email_service.sender_password else 'No'}")

        import smtplib
        try:
            with smtplib.SMTP(email_service.smtp_server, email_service.smtp_port) as server:
                server.starttls()
                print("SMTP connection test: SUCCESS")
        except Exception as e:
            print(f"SMTP connection test: FAILED - {str(e)}")

        print("=== EMAIL CONFIG DEBUG END ===")

    except ImportError as e:
        print(f"Email service not available: {str(e)}")
    except Exception as e:
        print(f"Email config debug error: {str(e)}")


app = FastAPI(
    title=settings.APP_NAME, 
    version=settings.VERSION, 
    lifespan=life_span,
)

origins = [
    "http://localhost:3000",  
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"Yêu cầu đến: {request.method} {request.url}")
    response = await call_next(request)
    print(f"Trạng thái phản hồi: {response.status_code} cho {request.method} {request.url}")
    return response

app.include_router(api_v1_router, prefix=settings.API_V1_STR)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "message": "API đang chạy"
    }