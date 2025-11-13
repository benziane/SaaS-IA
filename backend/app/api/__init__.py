"""
API router configuration
"""
from fastapi import APIRouter
from app.api import transcriptions

api_router = APIRouter()

# Include all routers
api_router.include_router(transcriptions.router)

# Health check endpoint
@api_router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "transcription-api"}
