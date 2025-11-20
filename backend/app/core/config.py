from pydantic_settings import BaseSettings, SettingsConfigDict 

class Settings(BaseSettings):  

    APP_NAME: str = "Wound Detection API"
    VERSION: str = "0.1.0"
    DEBUG: bool = True

    API_V1_STR: str ="/api/v1"

    DATABASE_URL: str = "postgresql+asyncpg://postgres:123456@localhost:5432/skinaid_db"

    SECRET_KEY: str = "khoa-bi-mat-cua-ban-o-day-chi-danh-cho-muc-dich-kiem-tra-hay-lam-no-dai-hon-va-an-toan-hon-trong-san-xuat"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = "your-app-email@gmail.com"
    SMTP_PASSWORD: str = "your-app-password"

    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024
    MIN_FILE_SIZE: int = 1024
    UPLOAD_ALLOWED_FORMATS: str = ".jpg,.jpeg,.png"
    MIN_IMAGE_WIDTH: int = 100
    MIN_IMAGE_HEIGHT: int = 100
    MAX_IMAGE_WIDTH: int = 4096
    MAX_IMAGE_HEIGHT: int = 4096

    UPLOAD_DIR: str = "uploads"

    AI_SERVICE_URL: str = "http://localhost:8001"
    AI_SERVICE_TIMEOUT: int = 30
    AI_MAX_RETRIES: int = 1
    AI_API_KEY: str = ""

    GEOAPIFY_API_KEY: str = ""

    CORS_ORIGINS: list = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    
    APP_DESCRIPTION: str = "API SkinAid - Phân tích vết thương và trợ lý sơ cứu"
    DOCS_URL: str = "/docs"
    REDOC_URL: str = "/redoc"

    BASE_URL: str = "http://localhost:8000"

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()