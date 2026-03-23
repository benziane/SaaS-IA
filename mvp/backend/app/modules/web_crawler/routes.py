"""
Web crawler API routes.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth import get_current_user
from app.database import get_session
from app.models.user import User
from app.modules.billing.middleware import require_ai_call_quota
from app.modules.billing.service import BillingService
from app.modules.web_crawler.schemas import (
    IndexRequest,
    IndexResponse,
    ScrapeRequest,
    ScrapeResponse,
    ScrapeWithVisionRequest,
    ScrapeWithVisionResponse,
    ImageData,
)
from app.modules.web_crawler.service import WebCrawlerService
from app.rate_limit import limiter

router = APIRouter()


@router.post("/scrape", response_model=ScrapeResponse)
@limiter.limit("10/minute")
async def scrape_url(
    request: Request,
    body: ScrapeRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Scrape a URL and extract text (markdown) and images.

    Returns clean markdown content and image metadata.

    Rate limit: 10 requests/minute
    """
    auth_dict = body.auth.model_dump() if body.auth else None
    result = await WebCrawlerService.scrape(
        url=body.url,
        extract_images=body.extract_images,
        screenshot=body.screenshot,
        max_images=body.max_images,
        auth=auth_dict,
    )

    return ScrapeResponse(
        url=result["url"],
        title=result.get("title", ""),
        markdown=result.get("markdown", ""),
        text_length=result.get("text_length", 0),
        images=[ImageData(**img) for img in result.get("images", [])],
        image_count=result.get("image_count", 0),
        screenshot_base64=result.get("screenshot_base64"),
        success=result.get("success", False),
        error=result.get("error"),
    )


@router.post("/scrape-vision", response_model=ScrapeWithVisionResponse)
@limiter.limit("3/minute")
async def scrape_with_vision(
    request: Request,
    body: ScrapeWithVisionRequest,
    current_user: User = Depends(require_ai_call_quota),
    session: AsyncSession = Depends(get_session),
):
    """
    Scrape a URL and analyze each image with AI Vision (Gemini).

    Returns markdown content plus AI-generated image descriptions.

    Rate limit: 3 requests/minute (uses AI Vision API)
    """
    auth_dict = body.auth.model_dump() if body.auth else None
    result = await WebCrawlerService.scrape_with_vision(
        url=body.url,
        max_images=body.max_images,
        vision_prompt=body.vision_prompt,
        user_id=current_user.id,
        auth=auth_dict,
    )

    # Consume AI quota (1 per image analyzed + 1 base)
    image_count = len(result.get("images", []))
    await BillingService.consume_quota(
        current_user.id, "ai_call", max(image_count, 1), session
    )

    return ScrapeWithVisionResponse(
        url=result["url"],
        title=result.get("title", ""),
        markdown=result.get("markdown", ""),
        images=[ImageData(**img) for img in result.get("images", [])],
        vision_provider=result.get("vision_provider", ""),
        success=result.get("success", False),
        error=result.get("error"),
    )


@router.post("/index", response_model=IndexResponse)
@limiter.limit("3/minute")
async def index_url(
    request: Request,
    body: IndexRequest,
    current_user: User = Depends(require_ai_call_quota),
    session: AsyncSession = Depends(get_session),
):
    """
    Crawl a URL and index content into the Knowledge Base.

    Optionally crawls subpages (up to max_pages).

    Rate limit: 3 requests/minute
    """
    auth_dict = body.auth.model_dump() if body.auth else None
    result = await WebCrawlerService.index_to_knowledge_base(
        url=body.url,
        user_id=current_user.id,
        crawl_subpages=body.crawl_subpages,
        max_pages=body.max_pages,
        include_images=body.include_images,
        session=session,
        auth=auth_dict,
    )

    # Consume quota
    await BillingService.consume_quota(
        current_user.id, "ai_call", max(result.get("pages_crawled", 1), 1), session
    )

    return IndexResponse(
        url=result["url"],
        pages_crawled=result.get("pages_crawled", 0),
        chunks_indexed=result.get("chunks_indexed", 0),
        images_found=result.get("images_found", 0),
        success=result.get("success", False),
        error=result.get("error"),
    )
