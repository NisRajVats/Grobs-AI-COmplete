"""
Core Configuration Module - GrobsAI Backend
"""
import os
from typing import Optional, List
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "GrobsAI Backend"
    APP_VERSION: str = "1.0.0"
    APP_URL: str = "http://localhost:5173"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # API
    API_V1_PREFIX: str = "/api"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    SQLALCHEMY_DATABASE_URL: str = "sqlite:///./grobs.db"
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10

    # Security
    SECRET_KEY: Optional[str] = None
    REFRESH_SECRET_KEY: Optional[str] = None
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174"]

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # File Storage
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_FILE_TYPES: List[str] = ["application/pdf"]
    SKIP_LLM_PARSING: bool = False

    # Cloud Storage
    STORAGE_PROVIDER: str = "local"
    AWS_S3_BUCKET: Optional[str] = None
    AWS_REGION: Optional[str] = None
    GCS_BUCKET: Optional[str] = None

    # LLM Providers
    LLM_PROVIDER: str = "google"
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    HUGGINGFACE_API_KEY: Optional[str] = None

    # LLM Models
    OPENAI_MODEL: str = "gpt-4o"
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"
    GEMINI_MODEL: str = "gemini-2.0-flash"

    # Embedding
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_PROVIDER: str = "huggingface"

    # Job APIs
    ADZUNA_APP_ID: Optional[str] = None
    ADZUNA_API_KEY: Optional[str] = None
    JOOBLE_API_KEY: Optional[str] = None
    THEIRSTACK_API_KEY: Optional[str] = None

    # Vector Database
    VECTOR_DB_PROVIDER: str = "chroma"
    PINECONE_API_KEY: Optional[str] = None
    PINECONE_ENVIRONMENT: Optional[str] = None
    WEAVIATE_URL: Optional[str] = None
    WEAVIATE_API_KEY: Optional[str] = None
    CHROMA_PERSIST_DIR: str = "./chroma_db"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    CELERY_TASK_TRACK_STARTED: bool = True
    CELERY_TASK_TIME_LIMIT: int = 3600  # 1 hour

    # Email
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: str = "noreply@grobsai.com"
    SMTP_FROM_NAME: str = "GrobsAI"

    # Stripe
    STRIPE_API_KEY: Optional[str] = None
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None

    # Encryption
    RESUME_ENCRYPTION_KEY: Optional[str] = None
    ENCRYPTION_KEY: Optional[str] = None

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./backend.log"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Monitoring
    SENTRY_DSN: Optional[str] = None

    model_config = {
        "env_file": os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        "case_sensitive": True,
        "extra": "ignore"
    }


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()


def config(key: str, default=None):
    return getattr(settings, key, default)
