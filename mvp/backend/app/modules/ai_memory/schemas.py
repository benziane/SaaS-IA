"""AI Memory schemas."""
from pydantic import BaseModel
from typing import Optional


class MemoryRead(BaseModel):
    id: str
    memory_type: str
    content: str
    category: Optional[str]
    confidence: float
    source: str
    active: bool
    use_count: int

    class Config:
        from_attributes = True
