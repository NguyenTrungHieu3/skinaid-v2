from pydantic_settings import BaseSettings, SettingsConfigDict 

class Settings(BaseSettings):  

    APP_NAME: str = "Wound Detection API"
    VERSION: str = "0.1.0"
    DEBUG: bool = True

    API_V1_STR: str ="/api/v1"

    DATABASE_URL: str = "postgresql+asyncpg://postgres:123456@localhost:5432/skinaid_db"

    SECRET_KEY: str = "your-secret-key-here-for-testing-purposes-only-make-it-longer-and-more-secure-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = "your-app-email@gmail.com"
    SMTP_PASSWORD: str = "your-app-password"

    UPLOAD_MAX_FILE_SIZE: int = 5 * 1024 * 1024
    UPLOAD_ALLOWED_FORMATS: str = ".jpg,.jpeg,.png"
    UPLOAD_MIN_WIDTH: int = 224
    UPLOAD_MIN_HEIGHT: int = 224
    UPLOAD_DIR: str = "uploads"

    AI_SERVICE_URL: str = "http://localhost:8001"
    AI_SERVICE_TIMEOUT: int = 30
    AI_MAX_RETRIES: int = 1
    AI_API_KEY: str = ""

    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    
    APP_DESCRIPTION: str = "SkinAid API - Wound Analysis & First Aid Assistant"
    DOCS_URL: str = "/docs"
    REDOC_URL: str = "/redoc"

    BASE_URL: str = "http://localhost:8000"

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()