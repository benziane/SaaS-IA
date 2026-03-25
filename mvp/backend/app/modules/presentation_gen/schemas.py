"""
Presentation Gen schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# -- Templates --

AVAILABLE_TEMPLATES = [
    {
        "id": "default",
        "name": "Default",
        "description": "Clean and versatile presentation layout",
    },
    {
        "id": "pitch_deck",
        "name": "Pitch Deck",
        "description": "Investor-ready startup pitch with problem/solution/traction flow",
    },
    {
        "id": "report",
        "name": "Report",
        "description": "Data-driven report with charts placeholders and key findings",
    },
    {
        "id": "tutorial",
        "name": "Tutorial",
        "description": "Step-by-step educational presentation with examples",
    },
    {
        "id": "meeting",
        "name": "Meeting",
        "description": "Agenda-driven meeting deck with action items",
    },
    {
        "id": "proposal",
        "name": "Proposal",
        "description": "Business proposal with objectives, approach, timeline, and pricing",
    },
]

VALID_TEMPLATES = {t["id"] for t in AVAILABLE_TEMPLATES}
VALID_STYLES = {"professional", "creative", "minimal", "corporate", "academic", "dark", "colorful"}
VALID_EXPORT_FORMATS = {"html", "markdown", "pdf"}


# -- Slide --

class SlideContent(BaseModel):
    """Single slide content."""
    slide_number: int = Field(..., ge=1)
    title: str = Field(..., min_length=1, max_length=300)
    content: str = Field(..., max_length=5000)
    notes: Optional[str] = Field(None, max_length=2000)
    layout: str = Field(default="title_content", max_length=50)


# -- Presentation requests --

class PresentationCreate(BaseModel):
    """Create a new presentation."""
    title: str = Field(..., min_length=1, max_length=300)
    topic: str = Field(..., min_length=1, max_length=1000)
    num_slides: int = Field(default=10, ge=3, le=50)
    style: str = Field(default="professional", max_length=50)
    template: str = Field(default="default", max_length=50)
    language: str = Field(default="fr", max_length=10)
    source_text: Optional[str] = Field(None, max_length=50000)
    source_url: Optional[str] = Field(None, max_length=2000)

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Introduction a l'IA Generative",
                "topic": "Les fondamentaux de l'IA generative et ses applications en entreprise",
                "num_slides": 12,
                "style": "professional",
                "template": "pitch_deck",
                "language": "fr",
            }
        }


class PresentationFromTranscript(BaseModel):
    """Generate a presentation from an existing transcription."""
    transcript_id: str = Field(..., description="UUID of the transcription to use as source")
    title: Optional[str] = Field(None, max_length=300)
    num_slides: int = Field(default=10, ge=3, le=50)
    style: str = Field(default="professional", max_length=50)
    template: str = Field(default="default", max_length=50)
    language: str = Field(default="fr", max_length=10)

    class Config:
        json_schema_extra = {
            "example": {
                "transcript_id": "550e8400-e29b-41d4-a716-446655440000",
                "num_slides": 10,
                "template": "meeting",
            }
        }


class SlideUpdate(BaseModel):
    """Update a single slide."""
    title: Optional[str] = Field(None, max_length=300)
    content: Optional[str] = Field(None, max_length=5000)
    notes: Optional[str] = Field(None, max_length=2000)
    layout: Optional[str] = Field(None, max_length=50)


class SlideInsert(BaseModel):
    """Insert a new slide after a given position."""
    title: str = Field(..., min_length=1, max_length=300)
    content: str = Field(..., max_length=5000)
    notes: Optional[str] = Field(None, max_length=2000)
    layout: str = Field(default="title_content", max_length=50)


class ExportRequest(BaseModel):
    """Request to export a presentation."""
    format: str = Field(default="html", max_length=20)


# -- Presentation response --

class PresentationRead(BaseModel):
    """Presentation response schema."""
    id: UUID
    user_id: UUID
    title: str
    topic: str
    num_slides: int
    style: str
    template: str
    slides: list[dict]
    status: str
    format: str
    download_url: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
