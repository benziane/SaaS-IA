"""
Web crawler service using crawl4ai with Jina Reader API fallback.

Provides web scraping with text and image extraction,
AI vision analysis, and knowledge base indexing.
Scraping priority: crawl4ai (full browser) → Jina Reader (free API).
"""

import base64
import re
from typing import Optional
from uuid import UUID

import structlog

logger = structlog.get_logger()


class WebCrawlerService:
    """Service for web crawling and content extraction."""

    @staticmethod
    async def scrape(
        url: str,
        extract_images: bool = True,
        screenshot: bool = False,
        max_images: int = 20,
        auth: dict = None,
    ) -> dict:
        """
        Scrape a URL and extract text (markdown) and images.

        Auth modes:
        - cookies: dict of cookies to inject
        - headers: dict of custom headers (e.g. Bearer token)
        - login_url + login_js: auto-login via JS execution before crawling
        """
        try:
            from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig

            # Build config with auth
            config_kwargs = {"screenshot": screenshot}
            browser_kwargs = {"headless": True}

            if auth:
                # Custom headers (Bearer tokens, API keys)
                if auth.get("headers"):
                    config_kwargs["headers"] = auth["headers"]

                # Cookies injection
                if auth.get("cookies"):
                    cookie_list = [
                        {"name": k, "value": v, "domain": "", "path": "/"}
                        for k, v in auth["cookies"].items()
                    ]
                    config_kwargs["cookies"] = cookie_list

                # JavaScript execution for login
                if auth.get("login_js"):
                    config_kwargs["js_code"] = auth["login_js"]
                    config_kwargs["wait_until"] = "networkidle"

            config = CrawlerRunConfig(**config_kwargs)
            browser_config = BrowserConfig(**browser_kwargs)

            async with AsyncWebCrawler(config=browser_config) as crawler:
                # If login_url is provided, first navigate to login page and execute JS
                if auth and auth.get("login_url") and auth.get("login_js"):
                    login_config = CrawlerRunConfig(
                        js_code=auth["login_js"],
                        wait_until="networkidle",
                    )
                    await crawler.arun(url=auth["login_url"], config=login_config)
                    # Wait for auth to settle
                    import asyncio
                    await asyncio.sleep(auth.get("wait_after_login_ms", 3000) / 1000)

                    # Now crawl the target URL (session cookies are preserved)
                    target_config = CrawlerRunConfig(
                        screenshot=screenshot,
                        wait_until="networkidle",
                    )
                    result = await crawler.arun(url=url, config=target_config)
                else:
                    result = await crawler.arun(url=url, config=config)

                if not result.success:
                    return {
                        "url": url,
                        "success": False,
                        "error": result.error_message or "Failed to crawl URL",
                    }

                # Extract images
                images = []
                if extract_images and result.media and "images" in result.media:
                    for img in result.media["images"][:max_images]:
                        images.append({
                            "src": img.get("src", ""),
                            "alt": img.get("alt", ""),
                            "score": float(img.get("score", 0.0)),
                        })

                logger.info("scrape_success", url=url, scraper="crawl4ai")
                return {
                    "url": url,
                    "title": result.metadata.get("title", "") if result.metadata else "",
                    "markdown": result.markdown or "",
                    "text_length": len(result.markdown or ""),
                    "images": images,
                    "image_count": len(images),
                    "screenshot_base64": result.screenshot if screenshot else None,
                    "success": True,
                    "scraper": "crawl4ai",
                }

        except ImportError:
            logger.warning("crawl4ai_not_installed", msg="falling back to Jina Reader")
        except Exception as e:
            logger.warning("crawl4ai_failed", url=url, error=str(e), msg="falling back to Jina Reader")

        # Fallback: Jina Reader API
        try:
            jina_result = await WebCrawlerService._scrape_with_jina(url)
            if jina_result.get("success"):
                logger.info("scrape_success", url=url, scraper="jina_reader")
                return jina_result
            else:
                logger.error("jina_fallback_failed", url=url, error=jina_result.get("error"))
                return {
                    "url": url,
                    "success": False,
                    "error": f"All scrapers failed. Jina: {jina_result.get('error', 'unknown')}",
                }
        except Exception as e:
            logger.error("all_scrapers_failed", url=url, error=str(e))
            return {
                "url": url,
                "success": False,
                "error": f"All scrapers failed: {str(e)[:500]}",
            }

    @staticmethod
    async def _scrape_with_jina(url: str) -> dict:
        """
        Scrape a URL using Jina Reader API (free tier, no API key).

        Returns clean markdown content via https://r.jina.ai/{url}.
        """
        import httpx

        try:
            jina_url = f"https://r.jina.ai/{url}"
            headers = {"Accept": "application/json"}

            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(jina_url, headers=headers)
                resp.raise_for_status()

            data = resp.json().get("data", {}) if resp.headers.get("content-type", "").startswith("application/json") else {}

            if data:
                content = data.get("content", "")
                title = data.get("title", "")
            else:
                # Fallback: plain text response
                content = resp.text
                title = ""

            if not content or not content.strip():
                return {"success": False, "error": "Jina returned empty content"}

            return {
                "url": url,
                "title": title,
                "markdown": content,
                "text_length": len(content),
                "images": [],
                "image_count": 0,
                "screenshot_base64": None,
                "success": True,
                "scraper": "jina_reader",
            }

        except Exception as e:
            logger.error("jina_scrape_failed", url=url, error=str(e))
            return {
                "url": url,
                "success": False,
                "error": f"Jina Reader failed: {str(e)[:300]}",
            }

    @staticmethod
    async def scrape_with_vision(
        url: str,
        max_images: int = 10,
        vision_prompt: str = "Describe this image concisely.",
        user_id: Optional[UUID] = None,
        auth: dict = None,
    ) -> dict:
        """
        Scrape a URL, then analyze each image with AI Vision.
        """
        # First scrape
        scrape_result = await WebCrawlerService.scrape(
            url=url,
            extract_images=True,
            max_images=max_images,
            auth=auth,
        )

        if not scrape_result.get("success"):
            return scrape_result

        # Analyze images with Gemini Vision
        analyzed_images = []
        vision_provider = "gemini"

        for img_data in scrape_result.get("images", []):
            src = img_data.get("src", "")
            if not src:
                analyzed_images.append(img_data)
                continue

            try:
                description = await WebCrawlerService._analyze_image_url(
                    image_url=src,
                    prompt=vision_prompt,
                )
                img_data["description"] = description
            except Exception as e:
                img_data["description"] = f"Analysis failed: {str(e)[:100]}"

            analyzed_images.append(img_data)

        # Track AI cost for vision analysis
        if analyzed_images:
            try:
                from app.modules.cost_tracker.tracker import track_ai_usage
                await track_ai_usage(
                    user_id=user_id,
                    provider="gemini",
                    model="gemini-2.0-flash",
                    module="web_crawler",
                    action="vision_analysis",
                    input_tokens=0,
                    output_tokens=0,
                    latency_ms=0,
                    success=True,
                )
            except Exception:
                pass  # Cost tracking should never break main flow

        return {
            "url": url,
            "title": scrape_result.get("title", ""),
            "markdown": scrape_result.get("markdown", ""),
            "images": analyzed_images,
            "vision_provider": vision_provider,
            "success": True,
        }

    @staticmethod
    async def _analyze_image_url(image_url: str, prompt: str) -> str:
        """Analyze an image URL using Gemini Vision."""
        try:
            import httpx

            # Download image
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(image_url)
                if resp.status_code != 200:
                    return "Could not download image"

                image_bytes = resp.content
                content_type = resp.headers.get("content-type", "image/jpeg")

            # Use Gemini Vision
            from app.config import settings
            if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "MOCK":
                return "[Vision analysis requires GEMINI_API_KEY]"

            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)

            model = genai.GenerativeModel("gemini-2.0-flash")

            # Create image part
            image_part = {
                "mime_type": content_type.split(";")[0],
                "data": base64.b64encode(image_bytes).decode("utf-8"),
            }

            response = model.generate_content([prompt, image_part])
            return response.text if response.text else "No description generated"

        except Exception as e:
            return f"Vision error: {str(e)[:200]}"

    @staticmethod
    async def index_to_knowledge_base(
        url: str,
        user_id: UUID,
        crawl_subpages: bool = False,
        max_pages: int = 5,
        include_images: bool = True,
        session=None,
        auth: dict = None,
    ) -> dict:
        """
        Crawl a URL (and optionally subpages) and index content
        into the Knowledge Base.
        """
        pages_crawled = 0
        chunks_indexed = 0
        images_found = 0

        try:
            # Scrape main page
            main_result = await WebCrawlerService.scrape(
                url=url,
                extract_images=include_images,
                auth=auth,
            )

            if not main_result.get("success"):
                return {
                    "url": url,
                    "success": False,
                    "error": main_result.get("error", "Failed to crawl"),
                }

            # Prepare content for indexing
            content = main_result.get("markdown", "")
            title = main_result.get("title", url)

            if include_images:
                # Append image descriptions to content
                for img in main_result.get("images", []):
                    alt = img.get("alt", "")
                    src = img.get("src", "")
                    desc = img.get("description", "")
                    if alt or desc:
                        content += f"\n\n[Image: {alt or 'No alt text'}]"
                        if desc:
                            content += f"\n{desc}"
                images_found = len(main_result.get("images", []))

            # Index in knowledge base
            if content.strip() and session:
                try:
                    from app.modules.knowledge.service import KnowledgeService
                    indexed = await KnowledgeService.index_text_content(
                        user_id=user_id,
                        filename=f"web_{title[:50]}.md",
                        content=content,
                        content_type="text/markdown",
                        session=session,
                    )
                    if indexed:
                        chunks_indexed = indexed.get("total_chunks", 0)
                except Exception as e:
                    logger.warning("knowledge_index_failed", error=str(e))
                    # Fallback: just report we crawled but couldn't index
                    chunks_indexed = 0

            pages_crawled = 1

            # Crawl subpages if requested
            if crawl_subpages:
                subpage_urls = WebCrawlerService._extract_links(
                    content, url, max_pages - 1
                )

                for sub_url in subpage_urls:
                    try:
                        sub_result = await WebCrawlerService.scrape(
                            url=sub_url,
                            extract_images=include_images,
                            max_images=5,
                        )

                        if sub_result.get("success") and sub_result.get("markdown"):
                            sub_content = sub_result["markdown"]
                            sub_title = sub_result.get("title", sub_url)

                            if session:
                                try:
                                    from app.modules.knowledge.service import KnowledgeService
                                    indexed = await KnowledgeService.index_text_content(
                                        user_id=user_id,
                                        filename=f"web_{sub_title[:50]}.md",
                                        content=sub_content,
                                        content_type="text/markdown",
                                        session=session,
                                    )
                                    if indexed:
                                        chunks_indexed += indexed.get("total_chunks", 0)
                                except Exception:
                                    pass

                            pages_crawled += 1
                            images_found += len(sub_result.get("images", []))

                    except Exception as e:
                        logger.warning("subpage_crawl_failed", url=sub_url, error=str(e))

            return {
                "url": url,
                "pages_crawled": pages_crawled,
                "chunks_indexed": chunks_indexed,
                "images_found": images_found,
                "success": True,
            }

        except Exception as e:
            logger.error("index_failed", url=url, error=str(e))
            return {
                "url": url,
                "pages_crawled": pages_crawled,
                "chunks_indexed": chunks_indexed,
                "images_found": images_found,
                "success": False,
                "error": str(e)[:500],
            }

    @staticmethod
    def _extract_links(markdown: str, base_url: str, max_links: int) -> list[str]:
        """Extract internal links from markdown content."""
        from urllib.parse import urljoin, urlparse

        base_domain = urlparse(base_url).netloc
        links = re.findall(r'\[([^\]]*)\]\(([^)]+)\)', markdown)

        urls = set()
        for _, href in links:
            full_url = urljoin(base_url, href)
            parsed = urlparse(full_url)

            # Only same-domain HTTP(S) links
            if parsed.netloc == base_domain and parsed.scheme in ("http", "https"):
                # Skip anchors, images, assets
                if not any(parsed.path.endswith(ext) for ext in (".png", ".jpg", ".gif", ".css", ".js", ".pdf")):
                    urls.add(full_url)

            if len(urls) >= max_links:
                break

        return list(urls)[:max_links]
