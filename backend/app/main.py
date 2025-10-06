import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

print(f"Current directory: {current_dir}")
print(f"Parent directory: {parent_dir}")
print(f"Python path: {sys.path}")

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager 

from app.core.database import init_db
from app.core.config import settings
from app.api.v1.api import router as api_v1_router
import logging
import os

# Set up logging
logger = logging.getLogger(__name__)

def debug_email_config_in_server():
    """Debug email configuration when running in server context"""
    logger.info("=== EMAIL CONFIGURATION DEBUG ===")
    logger.info(f"TESTING environment variable: '{os.getenv('TESTING')}'")
    logger.info(f"SMTP_USERNAME from env: '{os.getenv('SMTP_USERNAME')}'")
    logger.info(f"SMTP_USERNAME from settings: '{settings.SMTP_USERNAME}'")
    logger.info(f"SMTP_PASSWORD length from env: {len(os.getenv('SMTP_PASSWORD', '')) if os.getenv('SMTP_PASSWORD') else 0}")
    logger.info(f"SMTP_PASSWORD length from settings: {len(settings.SMTP_PASSWORD) if settings.SMTP_PASSWORD else 0}")
    logger.info(f"SMTP_SERVER from env: '{os.getenv('SMTP_SERVER')}'")
    logger.info(f"SMTP_SERVER from settings: '{settings.SMTP_SERVER}'")
    logger.info(f"SMTP_PORT from env: '{os.getenv('SMTP_PORT')}'")
    logger.info(f"SMTP_PORT from settings: '{settings.SMTP_PORT}'")
    
    # Check the condition used in auth_service
    use_mock = os.getenv("TESTING") == "true"
    logger.info(f"Will use mock email service: {use_mock}")
    
    if use_mock:
        logger.info("USING MOCK EMAIL SERVICE")
    else:
        logger.info("USING REAL EMAIL SERVICE")
        
        # Try to import and test real email service
        try:
            from app.utils.email_service import EmailService
            email_service = EmailService()
            logger.info(f"EmailService created successfully")
            logger.info(f"email_service.smtp_server: {email_service.smtp_server}")
            logger.info(f"email_service.smtp_port: {email_service.smtp_port}")
            logger.info(f"email_service.sender_email: {email_service.sender_email}")
            logger.info(f"email_service.sender_password length: {len(email_service.sender_password)}")
        except Exception as e:
            logger.error(f"Failed to create EmailService: {e}")

@asynccontextmanager 
async def life_span(app: FastAPI): 
    print("Server start !!!")
    debug_email_config_in_server()
    await init_db()
    yield 
    print("Server is stopped !!!")


app = FastAPI(
    title=settings.APP_NAME, 
    version=settings.VERSION, 
    lifespan=life_span,
)

# ===== CORS middleware =====
origins = [
    "http://localhost:3000",  # React frontend
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # hoặc ["*"] tạm thời cho tất cả
    allow_credentials=True,
    allow_methods=["*"],     # OPTIONS + GET/POST/PUT/DELETE đều ok
    allow_headers=["*"],     # Content-Type, Authorization, ...
)

# ===== Log tất cả request =====
@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"➡️ Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    print(f"⬅️ Response status: {response.status_code} for {request.method} {request.url}")
    return response

# ===== Include API router =====
app.include_router(api_v1_router, prefix=settings.API_V1_STR)

# ===== Root endpoint =====
@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "message": "API is running"
    }