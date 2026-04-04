import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, ValidationError
from typing import List, Union, Optional
from urllib.parse import urlparse


class Settings(BaseSettings):

    # Application
    APP_NAME: str = "SkinAid API"
    VERSION: str = "0.1.0"
    DEBUG: bool = False
    APP_DESCRIPTION: str = "API SkinAid - Phân tích vết thương và trợ lý sơ cứu"
    DOCS_URL: str = "/docs"
    REDOC_URL: str = "/redoc"
    BASE_URL: str = "http://localhost:8000"

    # API
    API_V1_STR: str = "/api/v1"

    # Database
    DATABASE_URL: str

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Email
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""

    # File Upload
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024
    MIN_FILE_SIZE: int = 1024
    UPLOAD_ALLOWED_FORMATS: str = ".jpg,.jpeg,.png"
    MIN_IMAGE_WIDTH: int = 100
    MIN_IMAGE_HEIGHT: int = 100
    MAX_IMAGE_WIDTH: int = 4096
    MAX_IMAGE_HEIGHT: int = 4096
    UPLOAD_DIR: str = "uploads"

    # AI Service
    AI_SERVICE_URL: str = "http://localhost:8001"
    AI_SERVICE_TIMEOUT: int = 30
    AI_MAX_RETRIES: int = 1
    AI_API_KEY: str = ""

    # Map Service
    GEOAPIFY_API_KEY: str = ""

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    QDRANT: str = "http://localhost:6333/"
    RAG_COLLECTION_NAME: str = "skinaid_knowledge_base"
    RAG_EMBEDDING_DIMENSION: int = 3072        

    OPEN_API_KEY: str = ""
    OPEN_EMBEDDING_MODEL: str = "text-embedding-3-large"

    # LLM Synthesis (B5 pipeline)
    LLM_MODEL: str = "gpt-4.1-mini"
    LLM_MAX_TOKENS: int = 2000
    LLM_TEMPERATURE: float = 0.3
    LLM_SYNTHESIS_TOP_K: int = 5

    # Chatbot
    CHATBOT_MAX_MESSAGES: int = 10
    CHATBOT_REDIS_TTL_HOURS: int = 24
    CHATBOT_GUIDE_TEMPERATURE: float = 0.7
    CHATBOT_GUIDE_MAX_TOKENS: int = 500
    CHATBOT_ADVISOR_TEMPERATURE: float = 0.3
    CHATBOT_ADVISOR_MAX_TOKENS: int = 1000

    RAG_DOCS_PATH: str = "docs/RAGDocumentation"
    RAG_SCORE_THRESHOLD: float = 0.5
    RAG_SPARSE_MODEL: str = "Qdrant/bm25"

    # CORS
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, v):
        if isinstance(v, str):
            v = v.strip().lower()
            return v in ("true", "1", "yes", "on")
        return v

    @field_validator("SECRET_KEY", mode="after")
    @classmethod
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v

    @field_validator("DATABASE_URL", mode="after")
    @classmethod
    def validate_database_url(cls, v):
        if not v:
            raise ValueError("DATABASE_URL is required")
        try:
            result = urlparse(v)
            if not all([result.scheme, result.netloc]):
                raise ValueError("Invalid DATABASE_URL format")
        except Exception as e:
            raise ValueError(f"Invalid DATABASE_URL: {e}")
        return v

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @field_validator("CORS_ORIGINS", mode="after")
    @classmethod
    def validate_cors_origins(cls, v: List[str]):
        validated = []
        for origin in v:
            try:
                result = urlparse(origin)
                if not result.scheme or not result.netloc:
                    raise ValueError(f"Invalid CORS origin: {origin}")
                validated.append(origin)
            except Exception as e:
                raise ValueError(f"Invalid CORS origin '{origin}': {e}")
        return validated

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


def load_settings() -> Settings:
    try:
        return Settings()
    except ValidationError as e:
        print("\n" + "=" * 60)
        print("CONFIGURATION ERROR")
        print("=" * 60)
        for error in e.errors():
            field = error.get("loc", [""])[0]
            msg = error.get("msg", "Unknown error")
            print(f"  • {field}: {msg}")
        print("=" * 60)
        print("\nPlease check your .env file and try again.\n")
        os._exit(1)


settings = load_settings()