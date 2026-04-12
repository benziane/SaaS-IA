"""
Configuration management using Pydantic Settings
"""

import hashlib
from typing import List, Set

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""

    # Application
    APP_NAME: str = "SaaS-IA MVP"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    SQL_ECHO: bool = False

    # Database
    DATABASE_URL: str = ""

    # Redis
    REDIS_URL: str = ""

    # JWT Authentication
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Metrics (HIGH-01: separate token, never reuse SECRET_KEY)
    METRICS_TOKEN: str = ""

    # Trusted reverse-proxy IPs (HIGH-03: only trust X-Forwarded-For from these)
    TRUSTED_PROXIES: str = ""

    # AI APIs
    ASSEMBLYAI_API_KEY: str = "MOCK"
    
    # AI Providers (inspired by WeLAB)
    GEMINI_API_KEY: str = ""
    CLAUDE_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    
    # Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_PRO_MONTHLY: str = ""

    # Social Publisher token encryption key (Fernet-compatible base64 key, or any string)
    SOCIAL_TOKEN_KEY: str = ""

    # Instagram — Option 1: instaloader session login
    INSTAGRAM_USERNAME: str = ""
    INSTAGRAM_PASSWORD: str = ""

    # Instagram — Option 2: Meta Basic Display API
    INSTAGRAM_APP_ID: str = ""
    INSTAGRAM_APP_SECRET: str = ""
    INSTAGRAM_ACCESS_TOKEN: str = ""

    # Email / SMTP (optional — falls back to console logger if not set)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@saas-ia.com"
    SMTP_TLS: bool = True
    FRONTEND_URL: str = "http://localhost:3002"

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
    def debug_enabled(self) -> bool:
        """DEBUG is only effective when ENVIRONMENT is not 'production'."""
        if self.ENVIRONMENT == "production":
            return False
        return self.DEBUG

    @property
    def sql_echo_enabled(self) -> bool:
        """SQL_ECHO is only effective in development with an explicit flag."""
        if self.ENVIRONMENT == "production":
            return False
        return self.SQL_ECHO

    @property
    def dev_mode(self) -> bool:
        """True when ENVIRONMENT=development — enables dev shortcuts (email bypass, seeded users, etc.).
        Always False in production regardless of any other flag."""
        return self.ENVIRONMENT == "development"

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins string to list"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def metrics_token_resolved(self) -> str:
        """Return METRICS_TOKEN, or a deterministic hash derived from SECRET_KEY (never the raw SECRET_KEY)."""
        if self.METRICS_TOKEN:
            return self.METRICS_TOKEN
        return hashlib.sha256(f"metrics:{self.SECRET_KEY}".encode()).hexdigest()

    @property
    def trusted_proxies_set(self) -> Set[str]:
        """Parse comma-separated TRUSTED_PROXIES into a set of IP strings."""
        raw = (self.TRUSTED_PROXIES or "").strip()
        if not raw:
            return set()
        return {ip.strip() for ip in raw.split(",") if ip.strip()}


# Global settings instance
settings = Settings()

