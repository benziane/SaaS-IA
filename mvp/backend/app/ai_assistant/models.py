"""
Database Models pour AI Assistant - Grade S++

Tables pour stocker configurations des providers AI.
"""
from typing import Optional
from datetime import UTC, datetime
from sqlmodel import SQLModel, Field
from uuid import UUID, uuid4


class AIProviderConfig(SQLModel, table=True):
    """Configuration des providers AI."""
    
    __tablename__ = "ai_provider_configs"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    
    # Provider
    provider_name: str = Field(max_length=50, unique=True, index=True)
    display_name: str = Field(max_length=100)
    
    # Configuration
    enabled: bool = Field(default=True)
    default_model: str = Field(max_length=100)
    max_tokens: int = Field(default=2000)
    temperature: float = Field(default=0.7)
    
    # Limites
    rate_limit_per_minute: int = Field(default=10)
    daily_quota: Optional[int] = None
    
    # Coûts (par 1K tokens)
    cost_per_1k_input: float = Field(default=0.0)
    cost_per_1k_output: float = Field(default=0.0)
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

