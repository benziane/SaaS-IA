"""
Configuration management using Pydantic Settings
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "SaaS-IA MVP"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = ""

    # Redis
    REDIS_URL: str = ""

    # JWT Authentication
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # AI APIs
    ASSEMBLYAI_API_KEY: str = "MOCK"
    
    # AI Providers (inspired by WeLAB)
    GEMINI_API_KEY: str = ""
    CLAUDE_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3002,http://localhost:8004"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins string to list"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


# Global settings instance
settings = Settings()

