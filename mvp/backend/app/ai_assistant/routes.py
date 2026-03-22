"""AI Assistant API Routes - Grade S++"""

import json

from fastapi import APIRouter, Depends, HTTPException, Request, status, Body
from fastapi.responses import StreamingResponse
from typing import List, Dict, Optional
import structlog

from app.ai_assistant.schemas import (
    TextProcessingRequest,
    TextProcessingResponse,
    ProviderInfo
)
from app.ai_assistant.service import AIAssistantService
from app.ai_assistant.classification.content_classifier import ContentClassifier
from app.ai_assistant.classification.model_selector import ModelSelector
from app.ai_assistant.classification.enums import SelectionStrategy
from app.auth import get_current_user
from app.models.user import User

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.get("/providers", response_model=List[ProviderInfo])
async def list_providers(
    current_user: User = Depends(get_current_user)
):
    """
    List all available AI providers.
    
    Returns:
        List[ProviderInfo]: List of available providers with metadata
    """
    try:
        providers = AIAssistantService.list_providers()
        logger.info(
            "providers_listed",
            user_id=str(current_user.id),
            provider_count=len(providers)
        )
        return providers
    except Exception as e:
        logger.error(
            "providers_list_error",
            user_id=str(current_user.id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list providers: {str(e)}"
        )


@router.post("/process-text", response_model=TextProcessingResponse)
async def process_text(
    request: TextProcessingRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Process text using AI (correction, formatting, improvement).
    
    Args:
        request: Text processing request
        current_user: Authenticated user
    
    Returns:
        TextProcessingResponse: Processed text with metadata
    """
    try:
        logger.info(
            "text_processing_request",
            user_id=str(current_user.id),
            task=request.task,
            provider=request.provider,
            text_length=len(request.text)
        )
        
        result = await AIAssistantService.process_text(
            text=request.text,
            task=request.task,
            provider_name=request.provider,
            language=request.language
        )
        
        logger.info(
            "text_processing_complete",
            user_id=str(current_user.id),
            task=request.task,
            provider=request.provider,
            original_length=len(result["original_text"]),
            processed_length=len(result["processed_text"])
        )
        
        return result
        
    except ValueError as e:
        logger.error(
            "text_processing_validation_error",
            user_id=str(current_user.id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(
            "text_processing_error",
            user_id=str(current_user.id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Text processing failed: {str(e)}"
        )


@router.post("/stream")
async def stream_text(
    request_body: TextProcessingRequest,
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Stream text processing results via Server-Sent Events.

    Accepts the same input as /process-text but returns a streaming response.
    Uses the AI Router pipeline (classification, model selection, prompt
    selection) and streams tokens as they arrive from the selected provider.

    SSE event format:
        data: {"token": "chunk_text", "provider": "gemini"}
        data: {"done": true, "provider": "gemini", "tokens_streamed": 123}
        data: {"error": "message"}

    Args:
        request_body: Text processing request (same schema as /process-text)
        request: FastAPI request object (used for disconnect detection)
        current_user: Authenticated user

    Returns:
        StreamingResponse: SSE stream with media_type text/event-stream
    """
    logger.info(
        "stream_request_received",
        user_id=str(current_user.id),
        task=request_body.task,
        text_length=len(request_body.text)
    )

    async def event_generator():
        tokens_streamed = 0
        provider_name = "unknown"

        try:
            is_first = True
            async for chunk in AIAssistantService.stream_text(
                text=request_body.text,
                task=request_body.task,
                target_language=request_body.language,
                strategy=SelectionStrategy.BALANCED
            ):
                # Check for client disconnect
                if await request.is_disconnected():
                    logger.info(
                        "stream_client_disconnected",
                        user_id=str(current_user.id),
                        tokens_streamed=tokens_streamed
                    )
                    return

                if is_first and "provider" in chunk:
                    # First yield is metadata
                    provider_name = chunk["provider"]
                    is_first = False
                    continue

                if "token" in chunk:
                    tokens_streamed += 1
                    event_data = json.dumps(
                        {"token": chunk["token"], "provider": provider_name},
                        ensure_ascii=False
                    )
                    yield f"data: {event_data}\n\n"

            # Final event
            done_data = json.dumps({
                "done": True,
                "provider": provider_name,
                "tokens_streamed": tokens_streamed
            })
            yield f"data: {done_data}\n\n"

            logger.info(
                "stream_complete",
                user_id=str(current_user.id),
                provider=provider_name,
                tokens_streamed=tokens_streamed
            )

        except Exception as e:
            logger.error(
                "stream_error",
                user_id=str(current_user.id),
                error=str(e),
                error_type=type(e).__name__
            )
            error_data = json.dumps(
                {"error": str(e)},
                ensure_ascii=False
            )
            yield f"data: {error_data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.get("/health")
async def health_check():
    """
    Health check endpoint for AI Assistant module.
    
    Returns:
        dict: Health status
    """
    try:
        providers = AIAssistantService.list_providers()
        available_count = sum(1 for p in providers if p["available"])
        
        return {
            "status": "healthy",
            "module": "ai_assistant",
            "providers_total": len(providers),
            "providers_available": available_count
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "module": "ai_assistant",
            "error": str(e)
        }


@router.post("/classify-content")
async def classify_content(
    text: str = Body(..., embed=True),
    language: Optional[str] = Body("french", embed=True),
    metadata: Optional[Dict] = Body(None, embed=True),
    current_user: User = Depends(get_current_user)
) -> Dict:
    """
    🆕 Classify content using AI Router (debug endpoint).
    
    Analyzes text to determine domain, tone, sensitivity, and recommended model.
    Useful for testing and debugging the classification system.
    
    Args:
        text: Text to classify
        language: Language code (french, english, arabic)
        metadata: Optional metadata (title, source, etc.)
    
    Returns:
        {
            "classification": {
                "domains": {...},
                "primary_domain": "religious",
                "tone": "popular",
                "sensitivity": {...},
                ...
            },
            "recommended_model": {
                "model": "groq",
                "strategy": "balanced",
                "reason": "...",
                ...
            },
            "strategy_comparison": {
                "conservative": {...},
                "balanced": {...},
                "cost_optimized": {...}
            }
        }
    
    Example:
        POST /api/ai-assistant/classify-content
        {
            "text": "Le Prophète (paix soit sur lui) a dit...",
            "language": "french",
            "metadata": {"title": "Rappel sur la patience"}
        }
    """
    try:
        # 1. Classify content
        classification = ContentClassifier.classify(
            text=text,
            language=language,
            metadata=metadata
        )
        
        # 2. Get recommended model (balanced strategy)
        recommended_model = ModelSelector.select_model(
            classification=classification,
            strategy=SelectionStrategy.BALANCED
        )
        
        # 3. Compare all strategies
        strategy_comparison = ModelSelector.compare_strategies(classification)
        
        logger.info(
            "content_classified_via_api",
            user_id=str(current_user.id),
            domain=classification["primary_domain"],
            confidence=classification["confidence"],
            recommended_model=recommended_model["model"]
        )
        
        return {
            "classification": classification,
            "recommended_model": recommended_model,
            "strategy_comparison": strategy_comparison
        }
        
    except Exception as e:
        logger.error(
            "classification_error",
            user_id=str(current_user.id),
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Classification failed: {str(e)}"
        )


@router.post("/classify-batch")
async def classify_batch(
    texts: List[str] = Body(..., embed=True),
    language: Optional[str] = Body("french", embed=True),
    current_user: User = Depends(get_current_user)
) -> Dict:
    """
    🆕 Classify multiple texts in batch.
    
    Useful for analyzing multiple transcriptions or documents at once.
    
    Args:
        texts: List of texts to classify
        language: Language code
    
    Returns:
        {
            "results": [
                {"text_index": 0, "classification": {...}, "recommended_model": {...}},
                {"text_index": 1, "classification": {...}, "recommended_model": {...}},
                ...
            ],
            "summary": {
                "total_texts": 10,
                "domains_detected": {"religious": 5, "scientific": 3, "general": 2},
                "average_confidence": 0.78
            }
        }
    """
    try:
        results = []
        domain_counts = {}
        total_confidence = 0.0
        
        for i, text in enumerate(texts):
            classification = ContentClassifier.classify(text, language)
            recommended_model = ModelSelector.select_model(
                classification=classification,
                strategy=SelectionStrategy.BALANCED
            )
            
            results.append({
                "text_index": i,
                "classification": classification,
                "recommended_model": recommended_model
            })
            
            # Update stats
            domain = classification["primary_domain"]
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
            total_confidence += classification["confidence"]
        
        summary = {
            "total_texts": len(texts),
            "domains_detected": domain_counts,
            "average_confidence": round(total_confidence / len(texts), 3) if texts else 0.0
        }
        
        logger.info(
            "batch_classification_complete",
            user_id=str(current_user.id),
            total_texts=len(texts),
            domains=domain_counts
        )
        
        return {
            "results": results,
            "summary": summary
        }
        
    except Exception as e:
        logger.error(
            "batch_classification_error",
            user_id=str(current_user.id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch classification failed: {str(e)}"
        )

