"""
Application configuration management
"""
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, validator


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    # Application
    APP_NAME: str = "YouTube Transcription SaaS"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"

    # API
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # Redis
    REDIS_URL: str
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    # Transcription Services
    TRANSCRIPTION_SERVICE: str = "whisper"
    WHISPER_MODEL: str = "base"
    ASSEMBLYAI_API_KEY: Optional[str] = None
    DEEPGRAM_API_KEY: Optional[str] = None

    # Language Processing
    LANGUAGE_TOOL_ENABLED: bool = True
    SPACY_MODEL: str = "fr_core_news_md"

    # File Storage
    UPLOAD_DIR: str = "/app/uploads"
    MAX_FILE_SIZE: int = 524288000  # 500MB
    ALLOWED_EXTENSIONS: str = "mp3,wav,m4a,mp4,webm"

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: List[str] = ["*"]
    CORS_HEADERS: List[str] = ["*"]

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 10

    # Monitoring
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090

    @validator("CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v

    @validator("ALLOWED_EXTENSIONS", pre=True)
    def assemble_allowed_extensions(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
