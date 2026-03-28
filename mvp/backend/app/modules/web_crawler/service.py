"""
Web crawler service — v8 (100% crawl4ai feature surface).

Capabilities:
- Singleton browser (avoids 2s Playwright cold-start per request)
- fit_markdown via PruningContentFilter / BM25ContentFilter
- All CrawlerRunConfig rendering options: scan_full_page, process_iframes,
  flatten_shadow_dom, remove_overlay_elements, simulate_user, virtual_scroll
- Reliability: page_timeout, check_robots_txt, word_count_threshold
- Content filtering: excluded_tags, excluded_selector, table_extraction
- Media: images, audio, video extraction
- Links: internal, external, scored, social-media filtered
- Output: PDF (base64), MHTML snapshot, network request capture
- Browser identity: proxy_url, user_agent / rotation
- LLM extraction: LLMExtractionStrategy with gemini/claude/groq
- Deep crawl: BFS / DFS / Best-First strategies via native crawl4ai
- Batch scraping: arun_many() with MemoryAdaptiveDispatcher
- Structured CSS extraction: JsonCssExtractionStrategy
- Auth: cookies, headers, auto-login with isolated session_id
- Jina Reader API fallback when crawl4ai unavailable
- Page interaction: wait_for, wait_for_timeout, js_code, js_code_before_wait, max_retries
- Content targeting: css_selector, target_elements, only_text, parser_type
- Timing: delay_before_return_html, adjust_viewport_to_content
- Media: image_score_threshold
- Privacy: remove_consent_popups
- Console: log_console, capture_console_messages
- Security: fetch_ssl_certificate
- URL seeding: aseed_urls() via AsyncUrlSeeder
- Deep crawl filtering: FilterChain (URLPatternFilter, DomainFilter), KeywordRelevanceScorer
"""

import asyncio
import base64
import re
import secrets
from typing import Optional
from uuid import UUID

import structlog

logger = structlog.get_logger()


# ---------------------------------------------------------------------------
# Singleton browser lifecycle
# ---------------------------------------------------------------------------

_crawler = None
_crawler_lock = asyncio.Lock()


async def get_crawler():
    """Return the singleton AsyncWebCrawler, lazily creating it if needed."""
    global _crawler
    if _crawler is None:
        async with _crawler_lock:
            if _crawler is None:
                from crawl4ai import AsyncWebCrawler, BrowserConfig
                instance = AsyncWebCrawler(config=BrowserConfig(headless=True))
                await instance.start()
                _crawler = instance
    return _crawler


async def init_crawler() -> None:
    """Initialize the singleton browser. Called from lifespan startup."""
    try:
        await get_crawler()
        logger.info("crawl4ai_browser_started")
    except Exception as exc:
        logger.warning("crawl4ai_browser_start_failed", error=str(exc))


async def close_crawler() -> None:
    """Shutdown the singleton browser. Called from lifespan shutdown."""
    global _crawler
    if _crawler is not None:
        try:
            await _crawler.close()
            logger.info("crawl4ai_browser_closed")
        except Exception as exc:
            logger.warning("crawl4ai_browser_close_error", error=str(exc))
        finally:
            _crawler = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_markdown(result) -> tuple[str, str]:
    """Return (raw_markdown, fit_markdown) from a CrawlResult.

    Handles both the modern object API (result.markdown.raw_markdown)
    and the legacy plain-string API.
    """
    if result.markdown is None:
        return "", ""
    if hasattr(result.markdown, "raw_markdown"):
        raw = result.markdown.raw_markdown or ""
        fit = result.markdown.fit_markdown or raw
        return raw, fit
    raw = str(result.markdown)
    return raw, raw


def _build_proxy_config(proxies: list[dict]):
    """Build a RoundRobinProxyStrategy from a list of proxy dicts."""
    try:
        from crawl4ai import ProxyConfig, RoundRobinProxyStrategy
        proxy_objs = [
            ProxyConfig(
                server=p["server"],
                username=p.get("username"),
                password=p.get("password"),
            )
            for p in proxies
        ]
        return RoundRobinProxyStrategy(proxies=proxy_objs)
    except ImportError:
        logger.warning("proxy_rotation_unavailable", reason="crawl4ai ProxyConfig not found")
        return None


def _build_dispatcher(config: dict, monitor=None):
    """Build a MemoryAdaptiveDispatcher from a dispatcher config dict."""
    try:
        from crawl4ai import MemoryAdaptiveDispatcher, RateLimiter
        rate_limiter = RateLimiter(
            base_delay=(
                config.get("rate_limit_base_delay_min", 1.0),
                config.get("rate_limit_base_delay_max", 3.0),
            ),
            max_delay=config.get("rate_limit_max_delay", 60.0),
        )
        return MemoryAdaptiveDispatcher(
            max_session_permit=config.get("max_session_permit", 20),
            memory_threshold_percent=config.get("memory_threshold_percent", 90.0),
            rate_limiter=rate_limiter,
            monitor=monitor,
        )
    except ImportError:
        logger.warning("dispatcher_unavailable", reason="MemoryAdaptiveDispatcher not found")
        return None


def _build_monitor(total_urls: int = 0):
    """Build a CrawlerMonitor (UI disabled for API use)."""
    try:
        from crawl4ai import CrawlerMonitor
        return CrawlerMonitor(urls_total=total_urls, enable_ui=False)
    except ImportError:
        return None


def _get_monitor_stats(monitor) -> dict | None:
    """Extract summary stats from a CrawlerMonitor."""
    if monitor is None:
        return None
    try:
        summary = monitor.get_summary()
        return summary if isinstance(summary, dict) else {"raw": str(summary)}
    except Exception:
        return None


def _build_markdown_generator(
    topic: Optional[str] = None,
    word_count_threshold: int = 10,
    ignore_links: bool = False,
    body_width: int = 0,
    content_filter_mode: str = "pruning",
):
    """Build a DefaultMarkdownGenerator with the appropriate content filter."""
    from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
    from crawl4ai.content_filter_strategy import PruningContentFilter, BM25ContentFilter

    if content_filter_mode == "llm":
        try:
            from crawl4ai.content_filter_strategy import LLMContentFilter
            content_filter = LLMContentFilter()
        except ImportError:
            logger.warning("llm_content_filter_unavailable")
            content_filter = PruningContentFilter(threshold=0.48)
    elif content_filter_mode == "bm25" and topic:
        content_filter = BM25ContentFilter(user_query=topic)
    elif topic:
        content_filter = BM25ContentFilter(user_query=topic)
    else:
        content_filter = PruningContentFilter(threshold=0.48)

    options: dict = {"word_count_threshold": word_count_threshold}
    if ignore_links:
        options["ignore_links"] = True
    if body_width > 0:
        options["body_width"] = body_width
    return DefaultMarkdownGenerator(content_filter=content_filter, options=options)


async def _get_temp_crawler(
    proxy_url: Optional[str] = None,
    user_agent: Optional[str] = None,
    browser_type: str = "chromium",
    enable_stealth: bool = False,
    javascript_enabled: bool = True,
    avoid_ads: bool = False,
):
    """Create a temporary AsyncWebCrawler with custom browser config.

    Caller is responsible for calling .close() on the returned instance.
    """
    from crawl4ai import AsyncWebCrawler, BrowserConfig

    browser_kwargs: dict = {"headless": True}
    if proxy_url:
        browser_kwargs["proxy"] = proxy_url
    if user_agent and user_agent != "random":
        browser_kwargs["user_agent"] = user_agent
    elif user_agent == "random":
        browser_kwargs["user_agent_mode"] = "random"
    if browser_type and browser_type != "chromium":
        browser_kwargs["browser_type"] = browser_type
    if enable_stealth:
        browser_kwargs["enable_stealth"] = True
    if not javascript_enabled:
        browser_kwargs["javascript_enabled"] = False
    if avoid_ads:
        browser_kwargs["avoid_ads"] = True

    instance = AsyncWebCrawler(config=BrowserConfig(**browser_kwargs))
    await instance.start()
    return instance


# ---------------------------------------------------------------------------
# Main service
# ---------------------------------------------------------------------------

class WebCrawlerService:
    """Service for web crawling and content extraction."""

    @staticmethod
    async def scrape(
        url: str,
        # Core
        extract_images: bool = True,
        screenshot: bool = False,
        max_images: int = 20,
        auth: dict = None,
        topic: str = None,
        # Rendering
        scan_full_page: bool = False,
        process_iframes: bool = False,
        flatten_shadow_dom: bool = False,
        remove_overlay_elements: bool = False,
        simulate_user: bool = False,
        virtual_scroll_selector: str = None,
        # Reliability
        page_timeout: int = 30000,
        check_robots_txt: bool = False,
        # Content filtering
        word_count_threshold: int = 10,
        excluded_tags: list = None,
        excluded_selector: str = None,
        table_extraction: bool = False,
        # Links
        score_links: bool = False,
        extract_external_links: bool = False,
        exclude_social_media_links: bool = False,
        # Media
        extract_audio: bool = False,
        extract_video: bool = False,
        # Output
        pdf: bool = False,
        capture_mhtml: bool = False,
        capture_network_requests: bool = False,
        # Browser identity
        proxy_url: str = None,
        user_agent: str = None,
        # Page interaction
        wait_for: str = None,
        wait_for_timeout: int = None,
        js_code: str = None,
        js_code_before_wait: str = None,
        max_retries: int = 0,
        # Content targeting
        css_selector: str = None,
        target_elements: list = None,
        only_text: bool = False,
        parser_type: str = "lxml",
        # Timing
        delay_before_return_html: float = 0.1,
        adjust_viewport_to_content: bool = False,
        # Media
        image_score_threshold: int = 2,
        # Links
        exclude_domains: list = None,
        # Privacy
        remove_consent_popups: bool = False,
        # Console
        log_console: bool = False,
        capture_console_messages: bool = False,
        # SSL
        fetch_ssl_certificate: bool = False,
        # Browser config
        enable_stealth: bool = False,
        browser_type: str = "chromium",
        javascript_enabled: bool = True,
        avoid_ads: bool = False,
        # Session
        session_id: Optional[str] = None,
        # Geolocation
        geolocation: Optional[dict] = None,
        # Cache
        cache_mode: str = "bypass",
        # Markdown display
        ignore_links: bool = False,
        body_width: int = 0,
        # Link preview
        link_preview_query: Optional[str] = None,
        link_preview_max_links: int = 0,
        # Table extraction mode
        table_extraction_mode: str = "default",
        # v7 — content filter, proxy rotation, antibot
        content_filter_mode: str = "pruning",
        proxies: Optional[list] = None,
        antibot_retry: bool = False,
    ) -> dict:
        """
        Scrape a URL with the full crawl4ai feature set.

        Auth modes:
        - cookies: dict of cookies to inject
        - headers: dict of custom headers (e.g. Bearer token)
        - login_url + login_js: auto-login via isolated crawl4ai session
        """
        try:
            from crawl4ai import CrawlerRunConfig, CacheMode

            md_generator = _build_markdown_generator(
                topic, word_count_threshold, ignore_links=ignore_links, body_width=body_width,
                content_filter_mode=content_filter_mode,
            )

            _cache_mode_map = {
                "enabled": CacheMode.ENABLED,
                "disabled": CacheMode.DISABLED,
                "bypass": CacheMode.BYPASS,
                "read_only": CacheMode.READ_ONLY,
                "write_only": CacheMode.WRITE_ONLY,
            }

            config_kwargs: dict = {
                "screenshot": screenshot,
                "cache_mode": _cache_mode_map.get(cache_mode, CacheMode.BYPASS),
                "markdown_generator": md_generator,
                # Rendering
                "scan_full_page": scan_full_page,
                "process_iframes": process_iframes,
                "flatten_shadow_dom": flatten_shadow_dom,
                "remove_overlay_elements": remove_overlay_elements,
                "simulate_user": simulate_user,
                # Reliability
                "page_timeout": page_timeout,
                "check_robots_txt": check_robots_txt,
                # Content
                "word_count_threshold": word_count_threshold,
                # Links
                "score_links": score_links,
                "exclude_social_media_links": exclude_social_media_links,
                # Output
                "pdf": pdf,
                "capture_mhtml": capture_mhtml,
                "capture_network_requests": capture_network_requests,
                # Page interaction
                "max_retries": max_retries,
                "delay_before_return_html": delay_before_return_html,
                # Rendering additions
                "adjust_viewport_to_content": adjust_viewport_to_content,
                "remove_consent_popups": remove_consent_popups,
                # Content
                "only_text": only_text,
                "parser_type": parser_type,
                "image_score_threshold": image_score_threshold,
                # Console
                "log_console": log_console,
                "capture_console_messages": capture_console_messages,
                # SSL
                "fetch_ssl_certificate": fetch_ssl_certificate,
            }

            if excluded_tags:
                config_kwargs["excluded_tags"] = excluded_tags
            if excluded_selector:
                config_kwargs["excluded_selector"] = excluded_selector

            # Table extraction
            if table_extraction_mode == "none":
                try:
                    from crawl4ai.table_extraction import NoTableExtraction
                    config_kwargs["table_extraction"] = NoTableExtraction()
                except ImportError:
                    pass
            elif table_extraction_mode == "llm":
                try:
                    from crawl4ai.table_extraction import LLMTableExtraction
                    config_kwargs["table_extraction"] = LLMTableExtraction()
                except ImportError:
                    logger.warning("llm_table_extraction_unavailable")
            elif table_extraction:
                # Legacy bool — lower threshold to include all tables
                config_kwargs["table_score_threshold"] = 0

            # Geolocation
            if geolocation:
                try:
                    from crawl4ai.async_configs import GeolocationConfig as CrawlGeoConfig
                    config_kwargs["geolocation"] = CrawlGeoConfig(
                        latitude=geolocation["latitude"],
                        longitude=geolocation["longitude"],
                        accuracy=geolocation.get("accuracy", 0.0),
                    )
                except Exception:
                    pass

            # Virtual scroll
            if virtual_scroll_selector:
                try:
                    from crawl4ai import VirtualScrollConfig
                    config_kwargs["virtual_scroll_config"] = VirtualScrollConfig(
                        container_selector=virtual_scroll_selector
                    )
                except Exception:
                    config_kwargs["scan_full_page"] = True  # fallback

            if wait_for:
                config_kwargs["wait_for"] = wait_for
            if wait_for_timeout:
                config_kwargs["wait_for_timeout"] = wait_for_timeout
            if js_code:
                config_kwargs["js_code"] = js_code
            if js_code_before_wait:
                config_kwargs["js_code_before_wait"] = js_code_before_wait
            if css_selector:
                config_kwargs["css_selector"] = css_selector
            if target_elements:
                config_kwargs["target_elements"] = target_elements
            if exclude_domains:
                config_kwargs["exclude_domains"] = exclude_domains

            if session_id:
                config_kwargs["session_id"] = session_id

            if link_preview_query and link_preview_max_links > 0:
                try:
                    from crawl4ai import LinkPreviewConfig
                    config_kwargs["link_preview_config"] = LinkPreviewConfig(
                        query=link_preview_query,
                        max_links=link_preview_max_links,
                        include_internal=True,
                        include_external=False,
                    )
                except Exception:
                    pass

            if auth:
                if auth.get("headers"):
                    config_kwargs["headers"] = auth["headers"]
                if auth.get("cookies"):
                    config_kwargs["cookies"] = [
                        {"name": k, "value": v, "domain": "", "path": "/"}
                        for k, v in auth["cookies"].items()
                    ]

            # Proxy rotation — overrides single proxy_url
            proxy_strategy = None
            if proxies:
                proxy_strategy = _build_proxy_config(proxies)

            # Determine which crawler to use
            needs_temp = bool(
                proxy_url or proxy_strategy or user_agent or enable_stealth
                or browser_type != "chromium" or not javascript_enabled or avoid_ads
            )
            _temp = None
            try:
                if needs_temp:
                    _temp = await _get_temp_crawler(
                        proxy_url=proxy_url if not proxy_strategy else None,
                        user_agent=user_agent,
                        browser_type=browser_type,
                        enable_stealth=enable_stealth,
                        javascript_enabled=javascript_enabled,
                        avoid_ads=avoid_ads,
                    )
                    # Attach proxy rotation if available
                    if proxy_strategy and _temp:
                        try:
                            _temp._config.proxy_config = proxy_strategy
                        except Exception:
                            pass
                    _active = _temp
                else:
                    _active = await get_crawler()

                if auth and auth.get("login_url") and auth.get("login_js"):
                    # Isolated session — no cross-request cookie leakage
                    session_id = f"auth_{secrets.token_hex(8)}"
                    try:
                        login_config = CrawlerRunConfig(
                            session_id=session_id,
                            js_code=auth["login_js"],
                            wait_until="networkidle",
                            page_timeout=page_timeout,
                        )
                        await _active.arun(url=auth["login_url"], config=login_config)
                        await asyncio.sleep(auth.get("wait_after_login_ms", 3000) / 1000)

                        target_config = CrawlerRunConfig(
                            **{**config_kwargs, "session_id": session_id, "wait_until": "networkidle"}
                        )
                        result = await _active.arun(url=url, config=target_config)
                    finally:
                        try:
                            await _active.crawler_strategy.kill_session(session_id)
                        except Exception:
                            pass
                else:
                    config = CrawlerRunConfig(**config_kwargs)
                    result = await _active.arun(url=url, config=config)
            finally:
                if _temp is not None:
                    try:
                        await _temp.close()
                    except Exception:
                        pass

            # Antibot detection + stealth retry
            if antibot_retry and result.success:
                try:
                    from crawl4ai.antibot_detector import is_blocked
                    html = getattr(result, "html", "") or ""
                    blocked, reason = is_blocked(
                        getattr(result, "status_code", None),
                        html,
                        result.error_message,
                    )
                    if blocked and not enable_stealth:
                        logger.info("antibot_blocked_retrying", url=url, reason=reason)
                        stealth_crawler = await _get_temp_crawler(
                            proxy_url=proxy_url,
                            user_agent=user_agent,
                            browser_type=browser_type,
                            enable_stealth=True,
                            javascript_enabled=javascript_enabled,
                            avoid_ads=avoid_ads,
                        )
                        try:
                            retry_config = CrawlerRunConfig(**config_kwargs)
                            result = await stealth_crawler.arun(url=url, config=retry_config)
                        finally:
                            try:
                                await stealth_crawler.close()
                            except Exception:
                                pass
                except ImportError:
                    pass
                except Exception as ab_err:
                    logger.warning("antibot_retry_failed", url=url, error=str(ab_err))

            if not result.success:
                return {
                    "url": url,
                    "success": False,
                    "error": result.error_message or "Failed to crawl URL",
                }

            raw_md, fit_md = _extract_markdown(result)

            # Images
            images = []
            if extract_images and result.media and "images" in result.media:
                for img in result.media["images"][:max_images]:
                    images.append({
                        "src": img.get("src", ""),
                        "alt": img.get("alt", ""),
                        "score": float(img.get("score", 0.0)),
                    })

            # Audio
            audio = []
            if extract_audio and result.media:
                for aud in result.media.get("audio", []):
                    audio.append({
                        "src": aud.get("src", ""),
                        "alt": aud.get("alt", ""),
                        "type": aud.get("type"),
                    })

            # Video
            video = []
            if extract_video and result.media:
                for vid in result.media.get("video", []):
                    video.append({
                        "src": vid.get("src", ""),
                        "alt": vid.get("alt", ""),
                        "poster": vid.get("poster"),
                        "type": vid.get("type"),
                    })

            # Internal links
            internal_links = []
            if result.links and "internal" in result.links:
                for link_info in result.links["internal"]:
                    href = link_info.get("href", "")
                    if href:
                        internal_links.append(href)

            # External links
            external_links = []
            if extract_external_links and result.links and "external" in result.links:
                for link_info in result.links["external"]:
                    href = link_info.get("href", "")
                    if href:
                        external_links.append(href)

            # Tables
            tables = []
            if table_extraction and hasattr(result, "tables") and result.tables:
                for tbl in result.tables:
                    tables.append({
                        "headers": tbl.get("headers", []),
                        "rows": tbl.get("rows", []),
                        "caption": tbl.get("caption"),
                    })

            # Network requests
            net_requests = []
            if capture_network_requests and getattr(result, "network_requests", None):
                for req in result.network_requests:
                    u = req.get("url", "") if isinstance(req, dict) else str(req)
                    if u:
                        net_requests.append(u)

            # PDF
            pdf_b64 = None
            if pdf and getattr(result, "pdf", None):
                raw_pdf = result.pdf
                if isinstance(raw_pdf, bytes):
                    pdf_b64 = base64.b64encode(raw_pdf).decode()
                else:
                    pdf_b64 = str(raw_pdf)

            # MHTML
            mhtml_out = None
            if capture_mhtml and getattr(result, "mhtml", None):
                mhtml_out = result.mhtml

            # Console messages
            console_msgs = []
            if capture_console_messages and getattr(result, "console_messages", None):
                console_msgs = result.console_messages or []

            # SSL certificate
            ssl_cert = None
            if fetch_ssl_certificate and getattr(result, "ssl_certificate", None):
                cert = result.ssl_certificate
                ssl_cert = cert.__dict__ if hasattr(cert, "__dict__") else {"info": str(cert)}

            logger.info("scrape_success", url=url, scraper="crawl4ai")
            return {
                "url": url,
                "title": result.metadata.get("title", "") if result.metadata else "",
                "markdown": raw_md,
                "fit_markdown": fit_md,
                "text_length": len(fit_md or raw_md),
                "images": images,
                "image_count": len(images),
                "audio": audio,
                "video": video,
                "screenshot_base64": result.screenshot if screenshot else None,
                "pdf_base64": pdf_b64,
                "mhtml": mhtml_out,
                "links_internal": internal_links,
                "links_external": external_links,
                "tables": tables,
                "network_requests": net_requests,
                "console_messages": console_msgs,
                "ssl_certificate": ssl_cert,
                "status_code": getattr(result, "status_code", None),
                "redirected_url": getattr(result, "redirected_url", None),
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
        """Scrape via Jina Reader API (free tier, no API key, fallback)."""
        import httpx

        try:
            jina_url = f"https://r.jina.ai/{url}"
            headers = {"Accept": "application/json"}

            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(jina_url, headers=headers)
                resp.raise_for_status()

            data = (
                resp.json().get("data", {})
                if resp.headers.get("content-type", "").startswith("application/json")
                else {}
            )

            if data:
                content = data.get("content", "")
                title = data.get("title", "")
            else:
                content = resp.text
                title = ""

            if not content or not content.strip():
                return {"success": False, "error": "Jina returned empty content"}

            return {
                "url": url,
                "title": title,
                "markdown": content,
                "fit_markdown": content,
                "text_length": len(content),
                "images": [],
                "image_count": 0,
                "audio": [],
                "video": [],
                "screenshot_base64": None,
                "pdf_base64": None,
                "mhtml": None,
                "links_internal": [],
                "links_external": [],
                "tables": [],
                "network_requests": [],
                "console_messages": [],
                "ssl_certificate": None,
                "status_code": None,
                "redirected_url": None,
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
        """Scrape a URL, then analyze each image with AI Vision (Gemini)."""
        scrape_result = await WebCrawlerService.scrape(
            url=url,
            extract_images=True,
            max_images=max_images,
            auth=auth,
        )

        if not scrape_result.get("success"):
            return scrape_result

        analyzed_images = []

        for img_data in scrape_result.get("images", []):
            src = img_data.get("src", "")
            if not src:
                analyzed_images.append(img_data)
                continue
            try:
                description = await WebCrawlerService._analyze_image_url(
                    image_url=src, prompt=vision_prompt
                )
                img_data["description"] = description
            except Exception as e:
                img_data["description"] = f"Analysis failed: {str(e)[:100]}"
            analyzed_images.append(img_data)

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
                pass

        return {
            "url": url,
            "title": scrape_result.get("title", ""),
            "markdown": scrape_result.get("markdown", ""),
            "images": analyzed_images,
            "vision_provider": "gemini",
            "success": True,
        }

    @staticmethod
    async def _analyze_image_url(image_url: str, prompt: str) -> str:
        """Analyze an image URL using Gemini Vision."""
        try:
            import httpx

            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(image_url)
                if resp.status_code != 200:
                    return "Could not download image"
                image_bytes = resp.content
                content_type = resp.headers.get("content-type", "image/jpeg")

            from app.config import settings
            if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "MOCK":
                return "[Vision analysis requires GEMINI_API_KEY]"

            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel("gemini-2.0-flash")
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
        topic: str = None,
    ) -> dict:
        """
        Crawl a URL (and optionally subpages) and index content into the Knowledge Base.

        Uses fit_markdown for cleaner KB chunks.
        Subpage discovery uses crawl4ai native internal links (falls back to regex).
        """
        pages_crawled = 0
        chunks_indexed = 0
        images_found = 0

        try:
            main_result = await WebCrawlerService.scrape(
                url=url,
                extract_images=include_images,
                auth=auth,
                topic=topic,
            )

            if not main_result.get("success"):
                return {
                    "url": url,
                    "success": False,
                    "error": main_result.get("error", "Failed to crawl"),
                }

            content = main_result.get("fit_markdown") or main_result.get("markdown", "")
            title = main_result.get("title", url)

            if include_images:
                for img in main_result.get("images", []):
                    alt = img.get("alt", "")
                    desc = img.get("description", "")
                    if alt or desc:
                        content += f"\n\n[Image: {alt or 'No alt text'}]"
                        if desc:
                            content += f"\n{desc}"
                images_found = len(main_result.get("images", []))

            if content.strip():
                try:
                    from app.modules.knowledge.service import KnowledgeService

                    async def _index(s):
                        return await KnowledgeService.index_text_content(
                            user_id=user_id,
                            filename=f"web_{title[:50]}.md",
                            content=content,
                            content_type="text/markdown",
                            session=s,
                        )

                    if session is not None:
                        indexed = await _index(session)
                    else:
                        from app.database import get_session_context
                        async with get_session_context() as new_session:
                            indexed = await _index(new_session)

                    if indexed:
                        chunks_indexed = indexed.get("total_chunks", 0)
                except Exception as e:
                    logger.warning("knowledge_index_failed", error=str(e))

            pages_crawled = 1

            if crawl_subpages:
                native_links = main_result.get("links_internal", [])
                if native_links:
                    from urllib.parse import urlparse
                    base_domain = urlparse(url).netloc
                    asset_exts = (".png", ".jpg", ".gif", ".css", ".js", ".pdf", ".svg", ".ico")
                    subpage_urls = []
                    seen = set()
                    for href in native_links:
                        parsed = urlparse(href)
                        if (
                            parsed.netloc == base_domain
                            and parsed.scheme in ("http", "https")
                            and not any(parsed.path.endswith(ext) for ext in asset_exts)
                            and href not in seen
                        ):
                            seen.add(href)
                            subpage_urls.append(href)
                            if len(subpage_urls) >= max_pages - 1:
                                break
                else:
                    subpage_urls = WebCrawlerService._extract_links(
                        main_result.get("markdown", ""), url, max_pages - 1
                    )

                for sub_url in subpage_urls:
                    try:
                        sub_result = await WebCrawlerService.scrape(
                            url=sub_url,
                            extract_images=include_images,
                            max_images=5,
                            topic=topic,
                        )

                        if sub_result.get("success"):
                            sub_content = sub_result.get("fit_markdown") or sub_result.get("markdown", "")
                            sub_title = sub_result.get("title", sub_url)

                            if sub_content.strip():
                                try:
                                    from app.modules.knowledge.service import KnowledgeService

                                    async def _index_sub(s):
                                        return await KnowledgeService.index_text_content(
                                            user_id=user_id,
                                            filename=f"web_{sub_title[:50]}.md",
                                            content=sub_content,
                                            content_type="text/markdown",
                                            session=s,
                                        )

                                    if session is not None:
                                        indexed = await _index_sub(session)
                                    else:
                                        from app.database import get_session_context
                                        async with get_session_context() as new_session:
                                            indexed = await _index_sub(new_session)

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
    async def extract_structured(
        url: str,
        base_selector: str,
        fields: list[dict],
        auth: dict = None,
    ) -> dict:
        """
        Extract structured data using a CSS selector schema (no LLM required).

        Returns a list of dicts matching the provided field schema.
        """
        try:
            import json
            from crawl4ai import CrawlerRunConfig, CacheMode
            from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

            schema = {
                "name": "extracted",
                "baseSelector": base_selector,
                "fields": [
                    {
                        "name": f["name"],
                        "selector": f["selector"],
                        "type": f.get("type", "text"),
                        **({"attribute": f["attribute"]} if f.get("attribute") else {}),
                    }
                    for f in fields
                ],
            }

            config_kwargs: dict = {
                "extraction_strategy": JsonCssExtractionStrategy(schema),
                "cache_mode": CacheMode.BYPASS,
            }

            if auth:
                if auth.get("headers"):
                    config_kwargs["headers"] = auth["headers"]
                if auth.get("cookies"):
                    config_kwargs["cookies"] = [
                        {"name": k, "value": v, "domain": "", "path": "/"}
                        for k, v in auth["cookies"].items()
                    ]

            config = CrawlerRunConfig(**config_kwargs)
            crawler = await get_crawler()
            result = await crawler.arun(url=url, config=config)

            if not result.success:
                return {
                    "url": url, "items": [], "item_count": 0,
                    "success": False,
                    "error": result.error_message or "Crawl failed",
                }

            items = []
            if result.extracted_content:
                raw = json.loads(result.extracted_content)
                items = raw if isinstance(raw, list) else [raw]

            logger.info("extract_structured_success", url=url, item_count=len(items))
            return {"url": url, "items": items, "item_count": len(items), "success": True}

        except Exception as e:
            logger.error("extract_structured_failed", url=url, error=str(e))
            return {
                "url": url, "items": [], "item_count": 0,
                "success": False, "error": str(e)[:500],
            }

    @staticmethod
    async def extract_with_llm(
        url: str,
        instruction: str,
        schema: dict = None,
        provider: str = "gemini",
        auth: dict = None,
    ) -> dict:
        """
        Extract structured data using LLM-powered extraction.

        No CSS schema needed — the model follows the natural-language instruction.
        Supports gemini (default), claude, and groq providers.
        """
        try:
            import json
            from crawl4ai import CrawlerRunConfig, CacheMode, LLMConfig
            from crawl4ai.extraction_strategy import LLMExtractionStrategy
            from app.config import settings

            provider_map = {
                "gemini": ("google/gemini-2.0-flash", getattr(settings, "GEMINI_API_KEY", None)),
                "claude": ("anthropic/claude-sonnet-4-5", getattr(settings, "ANTHROPIC_API_KEY", None)),
                "groq": ("groq/llama-3.3-70b-versatile", getattr(settings, "GROQ_API_KEY", None)),
            }

            llm_provider, api_key = provider_map.get(provider, provider_map["gemini"])
            if not api_key or api_key == "MOCK":
                return {
                    "url": url, "data": None, "success": False,
                    "error": f"API key for provider '{provider}' is not configured",
                }

            llm_config = LLMConfig(provider=llm_provider, api_token=api_key)

            strategy_kwargs: dict = {
                "llm_config": llm_config,
                "instruction": instruction,
            }
            if schema:
                strategy_kwargs["schema"] = schema
                strategy_kwargs["extraction_type"] = "schema"
            else:
                strategy_kwargs["extraction_type"] = "block"

            extraction_strategy = LLMExtractionStrategy(**strategy_kwargs)

            config_kwargs: dict = {
                "extraction_strategy": extraction_strategy,
                "cache_mode": CacheMode.BYPASS,
            }

            if auth:
                if auth.get("headers"):
                    config_kwargs["headers"] = auth["headers"]
                if auth.get("cookies"):
                    config_kwargs["cookies"] = [
                        {"name": k, "value": v, "domain": "", "path": "/"}
                        for k, v in auth["cookies"].items()
                    ]

            config = CrawlerRunConfig(**config_kwargs)
            crawler = await get_crawler()
            result = await crawler.arun(url=url, config=config)

            if not result.success:
                return {
                    "url": url, "data": None, "success": False,
                    "error": result.error_message or "Crawl failed",
                }

            data = None
            if result.extracted_content:
                try:
                    data = json.loads(result.extracted_content)
                except Exception:
                    data = result.extracted_content

            logger.info("extract_llm_success", url=url, provider=provider)
            return {"url": url, "data": data, "provider": provider, "success": True}

        except Exception as e:
            logger.error("extract_llm_failed", url=url, error=str(e))
            return {
                "url": url, "data": None, "success": False,
                "error": str(e)[:500],
            }

    @staticmethod
    async def batch_scrape(
        urls: list[str],
        use_fit_markdown: bool = True,
        extract_images: bool = False,
        dispatcher_config: Optional[dict] = None,
        proxies: Optional[list] = None,
    ) -> dict:
        """
        Scrape multiple URLs in parallel using crawl4ai's MemoryAdaptiveDispatcher.

        Handles rate limiting, memory pressure, and exponential backoff automatically.
        When dispatcher_config is provided, uses explicit MemoryAdaptiveDispatcher
        with CrawlerMonitor for stats collection.
        """
        try:
            from crawl4ai import CrawlerRunConfig, CacheMode

            config_kwargs: dict = {"cache_mode": CacheMode.BYPASS}
            if use_fit_markdown:
                config_kwargs["markdown_generator"] = _build_markdown_generator()

            run_config = CrawlerRunConfig(**config_kwargs)
            crawler = await get_crawler()

            # Build explicit dispatcher + monitor if config provided
            monitor = None
            dispatcher = None
            if dispatcher_config:
                monitor = _build_monitor(total_urls=len(urls))
                dispatcher = _build_dispatcher(dispatcher_config, monitor=monitor)

            raw_results = await crawler.arun_many(
                urls=urls, config=run_config,
                dispatcher=dispatcher,
            )

            results = []
            succeeded = 0
            for res in raw_results:
                if res.success:
                    if use_fit_markdown:
                        _, md = _extract_markdown(res)
                    else:
                        md, _ = _extract_markdown(res)
                    results.append({
                        "url": res.url,
                        "title": res.metadata.get("title", "") if res.metadata else "",
                        "markdown": md,
                        "success": True,
                    })
                    succeeded += 1
                else:
                    results.append({
                        "url": res.url, "title": "", "markdown": "",
                        "success": False,
                        "error": res.error_message or "Failed",
                    })

            logger.info("batch_scrape_complete", total=len(urls), succeeded=succeeded)
            return {
                "total": len(urls),
                "succeeded": succeeded,
                "failed": len(urls) - succeeded,
                "results": results,
                "monitor_stats": _get_monitor_stats(monitor),
            }

        except Exception as e:
            logger.error("batch_scrape_failed", error=str(e))
            return {
                "total": len(urls), "succeeded": 0, "failed": len(urls),
                "results": [
                    {"url": u, "title": "", "markdown": "", "success": False, "error": str(e)[:200]}
                    for u in urls
                ],
            }

    @staticmethod
    async def deep_crawl(
        url: str,
        strategy: str = "bfs",
        max_depth: int = 2,
        max_pages: int = 10,
        score_threshold: float = 0.0,
        include_external: bool = False,
        use_fit_markdown: bool = True,
        topic: str = None,
        keyword_scorer_keywords: list = None,
        url_patterns: list = None,
        allowed_domains: list = None,
        blocked_domains: list = None,
        # Advanced filters
        content_type_filter: list = None,
        content_relevance_query: Optional[str] = None,
        content_relevance_threshold: float = 2.0,
        seo_filter: bool = False,
        seo_filter_threshold: float = 0.65,
        # v7 — composite scoring, dispatcher, proxies
        composite_scorers: Optional[list] = None,
        domain_authority_weights: Optional[dict] = None,
        dispatcher_config: Optional[dict] = None,
        proxies: Optional[list] = None,
        # Resume
        resume_state: dict = None,
    ) -> dict:
        """
        Deep crawl a site using BFS / DFS / Best-First strategy.

        Discovers and follows links automatically — no manual link extraction needed.
        Returns a list of page results with url, title, markdown, depth, and score.
        """
        try:
            from crawl4ai import CrawlerRunConfig, CacheMode

            # Import strategies (try top-level first, then subpackage)
            try:
                from crawl4ai import (
                    BFSDeepCrawlStrategy,
                    DFSDeepCrawlStrategy,
                    BestFirstCrawlingStrategy,
                )
            except ImportError:
                from crawl4ai.deep_crawling import (
                    BFSDeepCrawlStrategy,
                    DFSDeepCrawlStrategy,
                    BestFirstCrawlingStrategy,
                )

            # Build optional FilterChain
            filter_chain = None
            all_filters = []
            try:
                from crawl4ai.deep_crawling import (
                    FilterChain, URLPatternFilter, DomainFilter,
                    ContentTypeFilter, ContentRelevanceFilter, SEOFilter,
                )
                if url_patterns:
                    all_filters.append(URLPatternFilter(patterns=url_patterns))
                if allowed_domains or blocked_domains:
                    all_filters.append(DomainFilter(
                        allowed_domains=allowed_domains or None,
                        blocked_domains=blocked_domains or None,
                    ))
                if content_type_filter:
                    all_filters.append(ContentTypeFilter(allowed_types=content_type_filter))
                if content_relevance_query:
                    all_filters.append(ContentRelevanceFilter(
                        query=content_relevance_query,
                        threshold=content_relevance_threshold,
                    ))
                if seo_filter:
                    all_filters.append(SEOFilter(threshold=seo_filter_threshold))
                if all_filters:
                    filter_chain = FilterChain(all_filters)
            except Exception:
                # Fallback: try old import path for basic filters only
                if url_patterns or allowed_domains or blocked_domains:
                    try:
                        from crawl4ai.deep_crawling.filters import FilterChain, URLPatternFilter, DomainFilter
                        fb = []
                        if url_patterns:
                            fb.append(URLPatternFilter(patterns=url_patterns))
                        if allowed_domains or blocked_domains:
                            fb.append(DomainFilter(
                                allowed_domains=allowed_domains or None,
                                blocked_domains=blocked_domains or None,
                            ))
                        if fb:
                            filter_chain = FilterChain(fb)
                    except Exception:
                        pass

            # Build optional scorer(s) for BestFirst
            url_scorer = None
            if strategy == "best_first":
                try:
                    from crawl4ai.deep_crawling.scorers import KeywordRelevanceScorer
                    scorers_list = []

                    if keyword_scorer_keywords:
                        scorers_list.append(
                            KeywordRelevanceScorer(keywords=keyword_scorer_keywords, weight=1.0)
                        )

                    # v7 — composite scorers
                    if composite_scorers:
                        scorer_map = {}
                        try:
                            from crawl4ai import (
                                DomainAuthorityScorer, FreshnessScorer,
                                PathDepthScorer, ContentTypeScorer,
                            )
                            scorer_map = {
                                "domain_authority": lambda: DomainAuthorityScorer(
                                    domain_weights=domain_authority_weights or {},
                                ),
                                "freshness": lambda: FreshnessScorer(),
                                "path_depth": lambda: PathDepthScorer(),
                                "content_type": lambda: ContentTypeScorer(type_weights={}),
                            }
                        except ImportError:
                            logger.warning("composite_scorers_unavailable")

                        for name in composite_scorers:
                            factory = scorer_map.get(name)
                            if factory:
                                scorers_list.append(factory())

                    if len(scorers_list) > 1:
                        from crawl4ai import CompositeScorer
                        url_scorer = CompositeScorer(scorers=scorers_list)
                    elif scorers_list:
                        url_scorer = scorers_list[0]
                except Exception:
                    pass

            exported_state: dict = {}

            async def _on_state_change(state: dict) -> None:
                exported_state.update(state)

            strategy_kwargs: dict = {
                "max_depth": max_depth,
                "max_pages": max_pages,
                "include_external": include_external,
                "on_state_change": _on_state_change,
            }
            if score_threshold > 0:
                strategy_kwargs["score_threshold"] = score_threshold
            if filter_chain:
                strategy_kwargs["filter_chain"] = filter_chain
            if url_scorer and strategy == "best_first":
                strategy_kwargs["url_scorer"] = url_scorer
            if resume_state:
                strategy_kwargs["resume_state"] = resume_state

            strategy_map = {
                "bfs": BFSDeepCrawlStrategy,
                "dfs": DFSDeepCrawlStrategy,
                "best_first": BestFirstCrawlingStrategy,
            }
            crawl_strategy = strategy_map.get(strategy, BFSDeepCrawlStrategy)(**strategy_kwargs)

            config_kwargs: dict = {
                "cache_mode": CacheMode.BYPASS,
                "deep_crawl_strategy": crawl_strategy,
            }
            if use_fit_markdown:
                config_kwargs["markdown_generator"] = _build_markdown_generator(topic)

            config = CrawlerRunConfig(**config_kwargs)
            crawler = await get_crawler()
            raw = await crawler.arun(url=url, config=config)

            # Deep crawl returns List[CrawlResult]
            all_results = raw if isinstance(raw, list) else [raw]

            pages = []
            for res in all_results:
                if res.success:
                    raw_md, fit_md = _extract_markdown(res)
                    md = fit_md if use_fit_markdown else raw_md
                    depth = (
                        getattr(res, "depth", None)
                        or (res.metadata.get("depth", 0) if res.metadata else 0)
                    )
                    score = (
                        getattr(res, "score", None)
                        or (res.metadata.get("score") if res.metadata else None)
                    )
                    pages.append({
                        "url": res.url,
                        "title": res.metadata.get("title", "") if res.metadata else "",
                        "markdown": md,
                        "depth": int(depth) if depth is not None else 0,
                        "score": float(score) if score is not None else None,
                        "success": True,
                    })
                else:
                    pages.append({
                        "url": res.url,
                        "title": "", "markdown": "",
                        "depth": 0, "score": None,
                        "success": False,
                        "error": res.error_message or "Failed",
                    })

            succeeded = sum(1 for p in pages if p["success"])
            logger.info(
                "deep_crawl_complete",
                url=url, strategy=strategy,
                total=len(pages), succeeded=succeeded,
            )
            return {
                "url": url,
                "strategy": strategy,
                "pages": pages,
                "total_pages": len(pages),
                "succeeded": succeeded,
                "failed": len(pages) - succeeded,
                "export_state": exported_state if exported_state else None,
                "monitor_stats": None,
                "success": True,
            }

        except Exception as e:
            logger.error("deep_crawl_failed", url=url, error=str(e))
            return {
                "url": url, "strategy": strategy,
                "pages": [], "total_pages": 0,
                "succeeded": 0, "failed": 0,
                "success": False, "error": str(e)[:500],
            }

    @staticmethod
    async def seed_urls(
        domain: str,
        source: str = "sitemap",
        max_urls: int = 100,
        pattern: Optional[str] = None,
        query: Optional[str] = None,
        score_threshold: Optional[float] = None,
        extract_head: bool = False,
    ) -> dict:
        """
        Discover URLs for a domain using crawl4ai's AsyncUrlSeeder.

        Sources: sitemap (parse XML sitemap), crawl (follow links),
        sitemaps (all sub-sitemaps).
        """
        try:
            from crawl4ai import AsyncUrlSeeder, SeedingConfig

            seed_kwargs: dict = {"source": source}
            if pattern:
                seed_kwargs["pattern"] = pattern
            if query:
                seed_kwargs["query"] = query
                seed_kwargs["extract_head"] = True  # required for BM25 scoring
                seed_kwargs["scoring_method"] = "bm25"
            if score_threshold is not None:
                seed_kwargs["score_threshold"] = score_threshold
            if extract_head and not query:
                seed_kwargs["extract_head"] = True

            config = SeedingConfig(**seed_kwargs)
            async with AsyncUrlSeeder() as seeder:
                urls = await seeder.urls(domain, config)

            # Normalize to list of strings
            if isinstance(urls, dict):
                all_urls = []
                for v in urls.values():
                    all_urls.extend(v if isinstance(v, list) else [str(v)])
                urls = all_urls
            elif not isinstance(urls, list):
                urls = []

            # Cap at max_urls
            urls = [str(u) for u in urls[:max_urls]]

            logger.info("seed_urls_complete", domain=domain, total=len(urls))
            return {
                "domain": domain,
                "urls": urls,
                "total": len(urls),
                "success": True,
            }

        except Exception as e:
            logger.error("seed_urls_failed", domain=domain, error=str(e))
            return {
                "domain": domain,
                "urls": [],
                "total": 0,
                "success": False,
                "error": str(e)[:500],
            }

    @staticmethod
    async def extract_regex(
        url: str,
        patterns: list = None,
        custom_patterns: dict = None,
        auth: dict = None,
    ) -> dict:
        """
        Extract data from a page using regex patterns (zero LLM).

        Built-in patterns: email, phone_intl, phone_us, url, ipv4, ipv6, uuid,
        currency, percentage, number, date_iso, date_us, time_24h, postal_us,
        postal_uk, hex_color, twitter_handle, hashtag, mac_addr, iban, credit_card, all.
        Custom patterns: {label: regex_string}.
        """
        try:
            import json
            from crawl4ai import CrawlerRunConfig, CacheMode
            from crawl4ai.extraction_strategy import RegexExtractionStrategy

            _PATTERN_MAP = {
                "email": "Email", "phone_intl": "PhoneIntl", "phone_us": "PhoneUS",
                "url": "Url", "ipv4": "IPv4", "ipv6": "IPv6", "uuid": "Uuid",
                "currency": "Currency", "percentage": "Percentage", "number": "Number",
                "date_iso": "DateIso", "date_us": "DateUS", "time_24h": "Time24h",
                "postal_us": "PostalUS", "postal_uk": "PostalUK", "hex_color": "HexColor",
                "twitter_handle": "TwitterHandle", "hashtag": "Hashtag",
                "mac_addr": "MacAddr", "iban": "Iban", "credit_card": "CreditCard",
            }

            pattern_flag = getattr(RegexExtractionStrategy, "Nothing", 0)
            for p in (patterns or []):
                if p == "all":
                    pattern_flag = getattr(RegexExtractionStrategy, "All", pattern_flag)
                    break
                attr = _PATTERN_MAP.get(p)
                if attr:
                    flag = getattr(RegexExtractionStrategy, attr, None)
                    if flag is not None:
                        pattern_flag = pattern_flag | flag

            strategy = RegexExtractionStrategy(
                pattern=pattern_flag,
                custom=custom_patterns or None,
            )

            config_kwargs: dict = {
                "extraction_strategy": strategy,
                "cache_mode": CacheMode.BYPASS,
            }
            if auth:
                if auth.get("headers"):
                    config_kwargs["headers"] = auth["headers"]
                if auth.get("cookies"):
                    config_kwargs["cookies"] = [
                        {"name": k, "value": v, "domain": "", "path": "/"}
                        for k, v in auth["cookies"].items()
                    ]

            config = CrawlerRunConfig(**config_kwargs)
            crawler = await get_crawler()
            result = await crawler.arun(url=url, config=config)

            if not result.success:
                return {"url": url, "matches": [], "match_count": 0, "success": False,
                        "error": result.error_message or "Crawl failed"}

            matches = []
            if result.extracted_content:
                raw = json.loads(result.extracted_content)
                matches = raw if isinstance(raw, list) else []

            logger.info("extract_regex_success", url=url, match_count=len(matches))
            return {"url": url, "matches": matches, "match_count": len(matches), "success": True}

        except Exception as e:
            logger.error("extract_regex_failed", url=url, error=str(e))
            return {"url": url, "matches": [], "match_count": 0, "success": False,
                    "error": str(e)[:500]}

    @staticmethod
    async def extract_xpath(
        url: str,
        base_selector: str,
        fields: list,
        auth: dict = None,
    ) -> dict:
        """
        Extract structured data using an XPath selector schema (no LLM required).

        base_selector: XPath expression for container elements (e.g. '//div[@class="product"]').
        fields: same format as CSS extraction — name, selector (XPath), type, attribute.
        """
        try:
            import json
            from crawl4ai import CrawlerRunConfig, CacheMode
            from crawl4ai.extraction_strategy import JsonXPathExtractionStrategy

            schema = {
                "name": "extracted",
                "baseSelector": base_selector,
                "fields": [
                    {
                        "name": f["name"],
                        "selector": f["selector"],
                        "type": f.get("type", "text"),
                        **({"attribute": f["attribute"]} if f.get("attribute") else {}),
                    }
                    for f in fields
                ],
            }

            config_kwargs: dict = {
                "extraction_strategy": JsonXPathExtractionStrategy(schema),
                "cache_mode": CacheMode.BYPASS,
            }
            if auth:
                if auth.get("headers"):
                    config_kwargs["headers"] = auth["headers"]
                if auth.get("cookies"):
                    config_kwargs["cookies"] = [
                        {"name": k, "value": v, "domain": "", "path": "/"}
                        for k, v in auth["cookies"].items()
                    ]

            config = CrawlerRunConfig(**config_kwargs)
            crawler = await get_crawler()
            result = await crawler.arun(url=url, config=config)

            if not result.success:
                return {"url": url, "items": [], "item_count": 0, "success": False,
                        "error": result.error_message or "Crawl failed"}

            items = []
            if result.extracted_content:
                raw = json.loads(result.extracted_content)
                items = raw if isinstance(raw, list) else [raw]

            logger.info("extract_xpath_success", url=url, item_count=len(items))
            return {"url": url, "items": items, "item_count": len(items), "success": True}

        except Exception as e:
            logger.error("extract_xpath_failed", url=url, error=str(e))
            return {"url": url, "items": [], "item_count": 0, "success": False,
                    "error": str(e)[:500]}

    @staticmethod
    async def generate_schema(
        url: str,
        query: str,
        schema_type: str = "CSS",
        provider: str = "gemini",
    ) -> dict:
        """
        Auto-generate a CSS or XPath extraction schema from a URL using LLM.

        The LLM inspects the page HTML and produces a schema ready for /extract or /extract-xpath.
        """
        try:
            from crawl4ai import LLMConfig
            from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
            from app.config import settings

            provider_map = {
                "gemini": ("google/gemini-2.0-flash", getattr(settings, "GEMINI_API_KEY", None)),
                "claude": ("anthropic/claude-sonnet-4-5", getattr(settings, "ANTHROPIC_API_KEY", None)),
                "groq": ("groq/llama-3.3-70b-versatile", getattr(settings, "GROQ_API_KEY", None)),
            }
            llm_provider, api_key = provider_map.get(provider, provider_map["gemini"])
            if not api_key or api_key == "MOCK":
                return {"url": url, "schema_def": None, "schema_type": schema_type,
                        "success": False, "error": f"API key for '{provider}' not configured"}

            llm_config = LLMConfig(provider=llm_provider, api_token=api_key)
            schema = await JsonCssExtractionStrategy.agenerate_schema(
                url=url,
                schema_type=schema_type,
                query=query,
                llm_config=llm_config,
                validate=True,
                max_refinements=2,
            )

            logger.info("generate_schema_success", url=url, schema_type=schema_type)
            return {"url": url, "schema_def": schema, "schema_type": schema_type, "success": True}

        except Exception as e:
            logger.error("generate_schema_failed", url=url, error=str(e))
            return {"url": url, "schema_def": None, "schema_type": schema_type,
                    "success": False, "error": str(e)[:500]}

    @staticmethod
    async def process_html(
        html: str,
        url: str = "https://example.com",
        use_fit_markdown: bool = True,
        topic: Optional[str] = None,
        css_selector: Optional[str] = None,
        word_count_threshold: int = 10,
    ) -> dict:
        """
        Process raw HTML through crawl4ai's pipeline without fetching any URL.

        Useful for processing already-fetched HTML: applies markdown generation,
        content filtering, and link extraction without launching a browser request.
        """
        try:
            from crawl4ai import CrawlerRunConfig, CacheMode

            config_kwargs: dict = {
                "cache_mode": CacheMode.BYPASS,
                "word_count_threshold": word_count_threshold,
            }
            if use_fit_markdown:
                config_kwargs["markdown_generator"] = _build_markdown_generator(
                    topic, word_count_threshold
                )
            if css_selector:
                config_kwargs["css_selector"] = css_selector

            config = CrawlerRunConfig(**config_kwargs)
            crawler = await get_crawler()
            result = await crawler.aprocess_html(
                url=url,
                html=html,
                extracted_content=None,
                config=config,
                screenshot_data=None,
                pdf_data=None,
                verbose=False,
            )

            if not result.success:
                return {"url": url, "markdown": "", "fit_markdown": "",
                        "text_length": 0, "links_internal": [], "links_external": [],
                        "success": False, "error": result.error_message or "Processing failed"}

            raw_md, fit_md = _extract_markdown(result)

            internal_links = []
            if result.links and "internal" in result.links:
                for lk in result.links["internal"]:
                    href = lk.get("href", "")
                    if href:
                        internal_links.append(href)

            external_links = []
            if result.links and "external" in result.links:
                for lk in result.links["external"]:
                    href = lk.get("href", "")
                    if href:
                        external_links.append(href)

            logger.info("process_html_success", url=url)
            return {
                "url": url,
                "markdown": raw_md,
                "fit_markdown": fit_md if use_fit_markdown else "",
                "text_length": len(fit_md or raw_md),
                "links_internal": internal_links,
                "links_external": external_links,
                "success": True,
            }

        except Exception as e:
            logger.error("process_html_failed", url=url, error=str(e))
            return {"url": url, "markdown": "", "fit_markdown": "",
                    "text_length": 0, "links_internal": [], "links_external": [],
                    "success": False, "error": str(e)[:500]}

    @staticmethod
    async def scrape_http(
        url: str,
        css_selector: Optional[str] = None,
        word_count_threshold: int = 10,
        use_fit_markdown: bool = True,
        headers: dict = None,
        follow_redirects: bool = True,
    ) -> dict:
        """
        Scrape a URL using pure HTTP (no browser, no JavaScript).

        Uses HTTPCrawlerConfig — 10-20x faster than browser-based scraping.
        Best for static HTML, server-rendered pages, or authenticated REST endpoints.
        """
        try:
            from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
            from crawl4ai.async_configs import HTTPCrawlerConfig

            http_config = HTTPCrawlerConfig(
                headers=headers or {},
                follow_redirects=follow_redirects,
            )
            # AsyncWebCrawler internally accesses BrowserConfig attributes on the
            # config object. HTTPCrawlerConfig doesn't have them — copy all
            # defaults from a fresh BrowserConfig instance.
            from crawl4ai import BrowserConfig as _BC
            _defaults = _BC(headless=True, verbose=False)
            for _attr in dir(_defaults):
                if _attr.startswith("_") or callable(getattr(_defaults, _attr)):
                    continue
                if not hasattr(http_config, _attr):
                    setattr(http_config, _attr, getattr(_defaults, _attr))

            md_generator = _build_markdown_generator(
                word_count_threshold=word_count_threshold
            ) if use_fit_markdown else None

            config_kwargs: dict = {
                "cache_mode": CacheMode.BYPASS,
                "word_count_threshold": word_count_threshold,
            }
            if md_generator:
                config_kwargs["markdown_generator"] = md_generator
            if css_selector:
                config_kwargs["css_selector"] = css_selector

            run_config = CrawlerRunConfig(**config_kwargs)

            async with AsyncWebCrawler(config=http_config) as crawler:
                result = await crawler.arun(url=url, config=run_config)

            if not result.success:
                return {
                    "url": url,
                    "success": False,
                    "error": result.error_message or "HTTP crawl failed",
                }

            raw_md, fit_md = _extract_markdown(result)

            internal_links, external_links = [], []
            if result.links:
                for lk in result.links.get("internal", []):
                    href = lk.get("href", "")
                    if href:
                        internal_links.append(href)
                for lk in result.links.get("external", []):
                    href = lk.get("href", "")
                    if href:
                        external_links.append(href)

            logger.info("scrape_http_success", url=url)
            return {
                "url": url,
                "title": (result.metadata or {}).get("title", ""),
                "markdown": raw_md,
                "fit_markdown": fit_md if use_fit_markdown else "",
                "text_length": len(fit_md or raw_md),
                "links_internal": internal_links,
                "links_external": external_links,
                "status_code": getattr(result, "status_code", None),
                "scraper": "crawl4ai_http",
                "success": True,
            }

        except ImportError:
            return {
                "url": url,
                "success": False,
                "error": "HTTPCrawlerConfig requires crawl4ai >= 0.4.3",
            }
        except Exception as e:
            logger.error("scrape_http_failed", url=url, error=str(e))
            return {"url": url, "success": False, "error": str(e)[:500]}

    @staticmethod
    async def adaptive_crawl(
        url: str,
        query: str,
        max_pages: int = 20,
        max_depth: int = 5,
        strategy: str = "statistical",
        confidence_threshold: float = 0.7,
    ) -> dict:
        """
        Crawl a site using AdaptiveCrawler — self-tuning strategy that learns
        which pages are relevant and stops when confident.

        strategy: "statistical" (BM25/TF-IDF, no GPU) | "embedding" (semantic, slower)
        """
        try:
            from crawl4ai.adaptive_crawler import AdaptiveCrawler, AdaptiveConfig

            config = AdaptiveConfig(
                max_pages=max_pages,
                max_depth=max_depth,
                strategy=strategy,
                confidence_threshold=confidence_threshold,
            )

            crawler = await get_crawler()
            adaptive = AdaptiveCrawler(crawler=crawler, config=config)
            state = await adaptive.digest(start_url=url, query=query)

            # Extract pages — CrawlState may expose .pages or .results
            raw_pages = (
                getattr(state, "pages", None)
                or getattr(state, "results", None)
                or []
            )

            pages = []
            for res in raw_pages:
                if getattr(res, "success", False):
                    raw_md, fit_md = _extract_markdown(res)
                    meta = getattr(res, "metadata", None) or {}
                    pages.append({
                        "url": getattr(res, "url", ""),
                        "title": meta.get("title", ""),
                        "markdown": fit_md or raw_md,
                        "depth": int(meta.get("depth", 0)),
                        "score": meta.get("score"),
                        "success": True,
                    })
                else:
                    pages.append({
                        "url": getattr(res, "url", ""),
                        "title": "", "markdown": "", "depth": 0, "score": None,
                        "success": False,
                        "error": getattr(res, "error_message", "Failed"),
                    })

            succeeded = sum(1 for p in pages if p.get("success"))
            confidence = None
            is_sufficient = None
            try:
                confidence = float(adaptive.confidence)
                is_sufficient = bool(adaptive.is_sufficient)
            except Exception:
                pass

            logger.info(
                "adaptive_crawl_complete",
                url=url, total=len(pages), succeeded=succeeded,
                confidence=confidence,
            )
            return {
                "url": url,
                "query": query,
                "pages": pages,
                "total_pages": len(pages),
                "succeeded": succeeded,
                "failed": len(pages) - succeeded,
                "confidence": confidence,
                "is_sufficient": is_sufficient,
                "success": True,
            }

        except ImportError:
            return {
                "url": url, "query": query,
                "pages": [], "total_pages": 0, "succeeded": 0, "failed": 0,
                "confidence": None, "is_sufficient": None,
                "success": False,
                "error": "AdaptiveCrawler requires crawl4ai >= 0.7.0",
            }
        except Exception as e:
            logger.error("adaptive_crawl_failed", url=url, error=str(e))
            return {
                "url": url, "query": query,
                "pages": [], "total_pages": 0, "succeeded": 0, "failed": 0,
                "confidence": None, "is_sufficient": None,
                "success": False, "error": str(e)[:500],
            }

    @staticmethod
    async def hub_crawl(
        url: str,
        site_profile: str,
        use_fit_markdown: bool = True,
    ) -> dict:
        """
        Crawl using CrawlerHub — pre-built, site-optimised crawler profiles.

        CrawlerHub.get(site_profile) returns a BaseCrawler subclass whose
        run(url) method returns a JSON string with site-specific structured data.
        """
        try:
            from crawl4ai.hub import CrawlerHub

            crawler_cls = CrawlerHub.get(site_profile)
            if crawler_cls is None:
                return {
                    "url": url,
                    "success": False,
                    "error": f"Unknown site profile: '{site_profile}'. "
                             "Check CrawlerHub for available profiles.",
                }

            import json
            instance = crawler_cls()
            result_json = await instance.run(url=url)
            data = json.loads(result_json) if isinstance(result_json, str) else result_json

            logger.info("hub_crawl_success", url=url, site_profile=site_profile)
            return {
                "url": url,
                "site_profile": site_profile,
                "data": data,
                "success": True,
            }

        except ImportError:
            return {
                "url": url,
                "success": False,
                "error": "CrawlerHub requires crawl4ai >= 0.7.0",
            }
        except Exception as e:
            logger.error("hub_crawl_failed", url=url, site_profile=site_profile, error=str(e))
            return {"url": url, "success": False, "error": str(e)[:500]}

    # ------------------------------------------------------------------
    # v8 — Browser profiler
    # ------------------------------------------------------------------

    @staticmethod
    def list_browser_profiles() -> dict:
        """List all persistent browser profiles."""
        try:
            from crawl4ai import BrowserProfiler
            profiler = BrowserProfiler()
            profiles = profiler.list_profiles()
            return {"profiles": profiles, "success": True}
        except ImportError:
            return {"profiles": [], "success": False, "error": "BrowserProfiler requires crawl4ai >= 0.8.0"}
        except Exception as e:
            return {"profiles": [], "success": False, "error": str(e)[:500]}

    @staticmethod
    def create_browser_profile(profile_name: Optional[str] = None) -> dict:
        """Create a persistent browser profile."""
        try:
            from crawl4ai import BrowserProfiler
            profiler = BrowserProfiler()
            result_name = profiler.create_profile(profile_name=profile_name)
            if result_name:
                path = profiler.get_profile_path(result_name)
                return {"profile_name": result_name, "profile_path": path, "success": True}
            return {"success": False, "error": "Profile creation returned None"}
        except ImportError:
            return {"success": False, "error": "BrowserProfiler requires crawl4ai >= 0.8.0"}
        except Exception as e:
            return {"success": False, "error": str(e)[:500]}

    @staticmethod
    def delete_browser_profile(profile_name: str) -> dict:
        """Delete a persistent browser profile."""
        try:
            from crawl4ai import BrowserProfiler
            profiler = BrowserProfiler()
            deleted = profiler.delete_profile(profile_name)
            return {"success": deleted, "error": None if deleted else f"Profile '{profile_name}' not found"}
        except ImportError:
            return {"success": False, "error": "BrowserProfiler requires crawl4ai >= 0.8.0"}
        except Exception as e:
            return {"success": False, "error": str(e)[:500]}

    # ------------------------------------------------------------------
    # v8 — Docker remote crawl
    # ------------------------------------------------------------------

    @staticmethod
    async def docker_crawl(
        urls: list[str],
        docker_url: str = "http://localhost:8000",
        timeout: float = 30.0,
    ) -> dict:
        """Crawl URLs via a remote crawl4ai Docker container."""
        try:
            from crawl4ai import Crawl4aiDockerClient

            client = Crawl4aiDockerClient(base_url=docker_url, timeout=timeout)
            try:
                raw = await client.crawl(urls=urls)
                all_results = raw if isinstance(raw, list) else [raw]

                results = []
                succeeded = 0
                for res in all_results:
                    if res.success:
                        raw_md, fit_md = _extract_markdown(res)
                        results.append({
                            "url": res.url,
                            "title": (res.metadata or {}).get("title", ""),
                            "markdown": fit_md or raw_md,
                            "success": True,
                        })
                        succeeded += 1
                    else:
                        results.append({
                            "url": res.url, "title": "", "markdown": "",
                            "success": False,
                            "error": res.error_message or "Docker crawl failed",
                        })

                return {
                    "total": len(urls), "succeeded": succeeded,
                    "failed": len(urls) - succeeded,
                    "results": results, "success": True,
                }
            finally:
                try:
                    client.close()
                except Exception:
                    pass

        except ImportError:
            return {
                "total": len(urls), "succeeded": 0, "failed": len(urls),
                "results": [], "success": False,
                "error": "Crawl4aiDockerClient requires crawl4ai >= 0.8.0",
            }
        except Exception as e:
            logger.error("docker_crawl_failed", error=str(e))
            return {
                "total": len(urls), "succeeded": 0, "failed": len(urls),
                "results": [], "success": False, "error": str(e)[:500],
            }

    # ------------------------------------------------------------------
    # v8 — PDF scraping via crawl4ai
    # ------------------------------------------------------------------

    @staticmethod
    async def scrape_pdf(url: str, extract_images: bool = False) -> dict:
        """Scrape PDF content using crawl4ai's PDFContentScrapingStrategy."""
        try:
            from crawl4ai import CrawlerRunConfig, CacheMode, PDFContentScrapingStrategy

            strategy = PDFContentScrapingStrategy(extract_images=extract_images)
            config = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                content_scraping_strategy=strategy,
            )
            crawler = await get_crawler()
            result = await crawler.arun(url=url, config=config)

            if not result.success:
                return {"url": url, "success": False, "error": result.error_message or "PDF scrape failed"}

            raw_md, fit_md = _extract_markdown(result)
            md = fit_md or raw_md
            return {"url": url, "markdown": md, "text_length": len(md), "success": True}

        except ImportError:
            return {"url": url, "success": False, "error": "PDFContentScrapingStrategy requires crawl4ai >= 0.8.0"}
        except Exception as e:
            logger.error("scrape_pdf_failed", url=url, error=str(e))
            return {"url": url, "success": False, "error": str(e)[:500]}

    # ------------------------------------------------------------------
    # v8 — Cosine clustering extraction
    # ------------------------------------------------------------------

    @staticmethod
    async def extract_cosine(
        url: str,
        word_count_threshold: int = 10,
        max_dist: float = 0.2,
        top_k: int = 3,
        sim_threshold: float = 0.3,
        semantic_filter: Optional[str] = None,
    ) -> dict:
        """Extract content clusters using CosineStrategy (semantic similarity)."""
        try:
            from crawl4ai import CrawlerRunConfig, CacheMode, CosineStrategy

            strategy = CosineStrategy(
                word_count_threshold=word_count_threshold,
                max_dist=max_dist,
                top_k=top_k,
                sim_threshold=sim_threshold,
                semantic_filter=semantic_filter,
            )
            config = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                extraction_strategy=strategy,
            )
            crawler = await get_crawler()
            result = await crawler.arun(url=url, config=config)

            if not result.success:
                return {"url": url, "clusters": [], "total_clusters": 0,
                        "success": False, "error": result.error_message or "Cosine extraction failed"}

            import json as _json
            clusters = []
            if result.extracted_content:
                try:
                    raw = _json.loads(result.extracted_content)
                    if isinstance(raw, list):
                        for i, item in enumerate(raw):
                            clusters.append({
                                "index": i,
                                "tags": item.get("tags", []) if isinstance(item, dict) else [],
                                "content": item.get("content", str(item)) if isinstance(item, dict) else str(item),
                            })
                except Exception:
                    clusters = [{"index": 0, "tags": [], "content": result.extracted_content}]

            return {"url": url, "clusters": clusters, "total_clusters": len(clusters), "success": True}

        except ImportError:
            return {"url": url, "clusters": [], "total_clusters": 0,
                    "success": False, "error": "CosineStrategy requires crawl4ai + sentence-transformers"}
        except Exception as e:
            logger.error("extract_cosine_failed", url=url, error=str(e))
            return {"url": url, "clusters": [], "total_clusters": 0, "success": False, "error": str(e)[:500]}

    # ------------------------------------------------------------------
    # v8 — JSON lxml extraction
    # ------------------------------------------------------------------

    @staticmethod
    async def extract_lxml(url: str, schema: dict, auth: dict = None) -> dict:
        """Extract structured data using JsonLxmlExtractionStrategy."""
        try:
            from crawl4ai import CrawlerRunConfig, CacheMode
            from crawl4ai import JsonLxmlExtractionStrategy

            strategy = JsonLxmlExtractionStrategy(schema=schema)
            config_kwargs: dict = {
                "cache_mode": CacheMode.BYPASS,
                "extraction_strategy": strategy,
            }
            if auth and auth.get("headers"):
                config_kwargs["headers"] = auth["headers"]

            config = CrawlerRunConfig(**config_kwargs)
            crawler = await get_crawler()
            result = await crawler.arun(url=url, config=config)

            if not result.success:
                return {"url": url, "data": None, "success": False,
                        "error": result.error_message or "lxml extraction failed"}

            import json as _json
            data = None
            if result.extracted_content:
                try:
                    data = _json.loads(result.extracted_content)
                except Exception:
                    data = result.extracted_content

            return {"url": url, "data": data, "success": True}

        except ImportError:
            return {"url": url, "data": None, "success": False,
                    "error": "JsonLxmlExtractionStrategy requires crawl4ai >= 0.8.0"}
        except Exception as e:
            logger.error("extract_lxml_failed", url=url, error=str(e))
            return {"url": url, "data": None, "success": False, "error": str(e)[:500]}

    # ------------------------------------------------------------------
    # v8 — Regex chunking
    # ------------------------------------------------------------------

    @staticmethod
    def chunk_regex(text: str, patterns: list = None) -> dict:
        """Split text into chunks using RegexChunking."""
        try:
            from crawl4ai import RegexChunking
            chunker = RegexChunking(patterns=patterns)
            chunks = chunker.chunk(text)
            return {"chunks": chunks, "total_chunks": len(chunks), "success": True}
        except ImportError:
            return {"chunks": [], "total_chunks": 0, "success": False,
                    "error": "RegexChunking requires crawl4ai >= 0.8.0"}
        except Exception as e:
            return {"chunks": [], "total_chunks": 0, "success": False, "error": str(e)[:500]}

    # ------------------------------------------------------------------
    # v8 — C4A compile from file
    # ------------------------------------------------------------------

    @staticmethod
    def compile_c4a_file(file_path: str) -> dict:
        """Compile a C4A-Script file to JavaScript."""
        try:
            from crawl4ai import c4a_compile_file
            result = c4a_compile_file(file_path)
            if hasattr(result, "js_code") and result.js_code:
                return {"js_code": result.js_code, "success": True}
            error = getattr(result, "error", None) or "Compilation returned no JS code"
            return {"js_code": "", "success": False, "error": str(error)}
        except ImportError:
            return {"js_code": "", "success": False, "error": "c4a_compile_file requires crawl4ai >= 0.8.0"}
        except Exception as e:
            return {"js_code": "", "success": False, "error": str(e)[:500]}

    # ------------------------------------------------------------------
    # C4A-Script compile / validate
    # ------------------------------------------------------------------

    @staticmethod
    def compile_c4a(script: str) -> dict:
        """Compile C4A-Script DSL to JavaScript."""
        try:
            from crawl4ai import c4a_compile
            result = c4a_compile(script)
            if hasattr(result, "js_code") and result.js_code:
                return {"js_code": result.js_code, "success": True}
            error = getattr(result, "error", None) or "Compilation returned no JS code"
            return {"js_code": "", "success": False, "error": str(error)}
        except ImportError:
            return {"js_code": "", "success": False, "error": "c4a_compile requires crawl4ai >= 0.8.0"}
        except Exception as e:
            return {"js_code": "", "success": False, "error": str(e)[:500]}

    @staticmethod
    def validate_c4a(script: str) -> dict:
        """Validate C4A-Script syntax without compiling."""
        try:
            from crawl4ai import c4a_validate
            result = c4a_validate(script)
            valid = getattr(result, "valid", True)
            errors = getattr(result, "errors", []) or []
            return {"valid": valid, "errors": [str(e) for e in errors]}
        except ImportError:
            return {"valid": False, "errors": ["c4a_validate requires crawl4ai >= 0.8.0"]}
        except Exception as e:
            return {"valid": False, "errors": [str(e)[:500]]}

    @staticmethod
    def _extract_links(markdown: str, base_url: str, max_links: int) -> list[str]:
        """Extract internal links from markdown content (legacy fallback)."""
        from urllib.parse import urljoin, urlparse

        base_domain = urlparse(base_url).netloc
        links = re.findall(r'\[([^\]]*)\]\(([^)]+)\)', markdown)

        urls: set[str] = set()
        for _, href in links:
            full_url = urljoin(base_url, href)
            parsed = urlparse(full_url)
            if parsed.netloc == base_domain and parsed.scheme in ("http", "https"):
                if not any(parsed.path.endswith(ext) for ext in (".png", ".jpg", ".gif", ".css", ".js", ".pdf")):
                    urls.add(full_url)
            if len(urls) >= max_links:
                break

        return list(urls)[:max_links]
