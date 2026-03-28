"""
Web crawler API routes — v8.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth import get_current_user
from app.modules.auth_guards.middleware import require_verified_email
from app.database import get_session
from app.models.user import User
from app.modules.billing.middleware import require_ai_call_quota
from app.modules.billing.service import BillingService
from app.modules.web_crawler.schemas import (
    AdaptiveCrawlPageResult,
    AdaptiveCrawlRequest,
    AdaptiveCrawlResponse,
    AudioData,
    BatchScrapeRequest,
    BatchScrapeResponse,
    BatchScrapeResult,
    DeepCrawlPageResult,
    DeepCrawlRequest,
    DeepCrawlResponse,
    ExtractRequest,
    ExtractResponse,
    FastScrapeRequest,
    FastScrapeResponse,
    GenerateSchemaRequest,
    GenerateSchemaResponse,
    HubCrawlRequest,
    HubCrawlResponse,
    ImageData,
    IndexRequest,
    IndexResponse,
    LLMExtractRequest,
    LLMExtractResponse,
    ProcessHtmlRequest,
    ProcessHtmlResponse,
    RegexExtractRequest,
    RegexExtractResponse,
    RegexMatch,
    ScrapeRequest,
    ScrapeResponse,
    ScrapeWithVisionRequest,
    ScrapeWithVisionResponse,
    SeedRequest,
    SeedResponse,
    TableData,
    VideoData,
    XPathExtractRequest,
    C4ACompileRequest,
    C4ACompileResponse,
    C4ACompileFileRequest,
    C4AValidateRequest,
    C4AValidateResponse,
    BrowserProfileCreateRequest,
    BrowserProfileResponse,
    DockerCrawlRequest,
    DockerCrawlResponse,
    DockerCrawlResult,
    PdfScrapeRequest,
    PdfScrapeResponse,
    CosineExtractRequest,
    CosineExtractResponse,
    CosineCluster,
    LxmlExtractRequest,
    LxmlExtractResponse,
    RegexChunkRequest,
    RegexChunkResponse,
)
from app.modules.web_crawler.service import WebCrawlerService
from app.rate_limit import limiter

router = APIRouter()


@router.post("/scrape", response_model=ScrapeResponse)
@limiter.limit("10/minute")
async def scrape_url(
    request: Request,
    body: ScrapeRequest,
    current_user: User = Depends(require_verified_email),
):
    """
    Scrape a URL with the full crawl4ai feature set.

    Supports: fit_markdown, screenshots, PDF/MHTML capture, audio/video/table
    extraction, proxy, custom user-agent, iframe processing, shadow DOM,
    consent popup removal, virtual scroll, network request capture, stealth
    mode, multi-browser (chromium/firefox/webkit), session reuse, cache control,
    link preview scoring, and more.

    Rate limit: 10/minute
    """
    auth_dict = body.auth.model_dump() if body.auth else None
    result = await WebCrawlerService.scrape(
        url=body.url,
        extract_images=body.extract_images,
        screenshot=body.screenshot,
        max_images=body.max_images,
        auth=auth_dict,
        topic=body.topic,
        # Rendering
        scan_full_page=body.scan_full_page,
        process_iframes=body.process_iframes,
        flatten_shadow_dom=body.flatten_shadow_dom,
        remove_overlay_elements=body.remove_overlay_elements,
        simulate_user=body.simulate_user,
        virtual_scroll_selector=body.virtual_scroll_selector,
        # Reliability
        page_timeout=body.page_timeout,
        check_robots_txt=body.check_robots_txt,
        # Content filtering
        word_count_threshold=body.word_count_threshold,
        excluded_tags=body.excluded_tags or None,
        excluded_selector=body.excluded_selector,
        table_extraction=body.table_extraction,
        # Links
        score_links=body.score_links,
        extract_external_links=body.extract_external_links,
        exclude_social_media_links=body.exclude_social_media_links,
        # Media
        extract_audio=body.extract_audio,
        extract_video=body.extract_video,
        # Output
        pdf=body.pdf,
        capture_mhtml=body.capture_mhtml,
        capture_network_requests=body.capture_network_requests,
        # Browser identity
        proxy_url=body.proxy_url,
        user_agent=body.user_agent,
        # Page interaction
        wait_for=body.wait_for,
        wait_for_timeout=body.wait_for_timeout,
        js_code=body.js_code,
        js_code_before_wait=body.js_code_before_wait,
        max_retries=body.max_retries,
        # Content targeting
        css_selector=body.css_selector,
        target_elements=body.target_elements or None,
        only_text=body.only_text,
        parser_type=body.parser_type,
        delay_before_return_html=body.delay_before_return_html,
        adjust_viewport_to_content=body.adjust_viewport_to_content,
        image_score_threshold=body.image_score_threshold,
        exclude_domains=body.exclude_domains or None,
        remove_consent_popups=body.remove_consent_popups,
        log_console=body.log_console,
        capture_console_messages=body.capture_console_messages,
        fetch_ssl_certificate=body.fetch_ssl_certificate,
        # Browser config (v4)
        enable_stealth=body.enable_stealth,
        browser_type=body.browser_type,
        javascript_enabled=body.javascript_enabled,
        avoid_ads=body.avoid_ads,
        session_id=body.session_id,
        # Cache (v4)
        cache_mode=body.cache_mode,
        # Markdown display (v4)
        ignore_links=body.ignore_links,
        body_width=body.body_width,
        # Link preview (v4)
        link_preview_query=body.link_preview_query,
        link_preview_max_links=body.link_preview_max_links,
        # New v5
        geolocation=body.geolocation.model_dump() if body.geolocation else None,
        table_extraction_mode=body.table_extraction_mode,
        # New v7
        content_filter_mode=body.content_filter_mode,
        proxies=[p.model_dump() for p in body.proxies] if body.proxies else None,
        antibot_retry=body.antibot_retry,
    )

    return ScrapeResponse(
        url=result["url"],
        title=result.get("title", ""),
        markdown=result.get("markdown", ""),
        fit_markdown=result.get("fit_markdown", ""),
        text_length=result.get("text_length", 0),
        images=[ImageData(**img) for img in result.get("images", [])],
        image_count=result.get("image_count", 0),
        audio=[AudioData(**a) for a in result.get("audio", [])],
        video=[VideoData(**v) for v in result.get("video", [])],
        screenshot_base64=result.get("screenshot_base64"),
        pdf_base64=result.get("pdf_base64"),
        mhtml=result.get("mhtml"),
        links_internal=result.get("links_internal", []),
        links_external=result.get("links_external", []),
        tables=[TableData(**t) for t in result.get("tables", [])],
        network_requests=result.get("network_requests", []),
        console_messages=result.get("console_messages", []),
        ssl_certificate=result.get("ssl_certificate"),
        status_code=result.get("status_code"),
        redirected_url=result.get("redirected_url"),
        scraper=result.get("scraper", "crawl4ai"),
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

    Rate limit: 3/minute (uses AI Vision API)
    """
    auth_dict = body.auth.model_dump() if body.auth else None
    result = await WebCrawlerService.scrape_with_vision(
        url=body.url,
        max_images=body.max_images,
        vision_prompt=body.vision_prompt,
        user_id=current_user.id,
        auth=auth_dict,
    )

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
    Provide `topic` to enable BM25 content filtering for higher-quality KB chunks.

    Rate limit: 3/minute
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
        topic=body.topic,
    )

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


@router.post("/extract", response_model=ExtractResponse)
@limiter.limit("10/minute")
async def extract_structured(
    request: Request,
    body: ExtractRequest,
    current_user: User = Depends(require_verified_email),
):
    """
    Extract structured data from a page using a CSS selector schema.

    No LLM required — fast, deterministic extraction via CSS selectors.
    Define `base_selector` (the repeated container element) and `fields`
    (what to extract from each container).

    Rate limit: 10/minute
    """
    auth_dict = body.auth.model_dump() if body.auth else None
    fields_list = [f.model_dump() for f in body.fields]
    result = await WebCrawlerService.extract_structured(
        url=body.url,
        base_selector=body.base_selector,
        fields=fields_list,
        auth=auth_dict,
    )

    return ExtractResponse(
        url=result["url"],
        items=result.get("items", []),
        item_count=result.get("item_count", 0),
        success=result.get("success", False),
        error=result.get("error"),
    )


@router.post("/extract-llm", response_model=LLMExtractResponse)
@limiter.limit("5/minute")
async def extract_with_llm(
    request: Request,
    body: LLMExtractRequest,
    current_user: User = Depends(require_ai_call_quota),
    session: AsyncSession = Depends(get_session),
):
    """
    Extract structured data from a page using AI (no CSS schema needed).

    Provide a natural language `instruction` describing what to extract.
    Optionally pass `schema_def` (JSON Schema) to enforce structured output.
    Supports providers: gemini (default), claude, groq.

    Rate limit: 5/minute (uses AI API)
    """
    auth_dict = body.auth.model_dump() if body.auth else None
    result = await WebCrawlerService.extract_with_llm(
        url=body.url,
        instruction=body.instruction,
        schema=body.schema_def,
        provider=body.provider,
        auth=auth_dict,
    )

    await BillingService.consume_quota(current_user.id, "ai_call", 1, session)

    return LLMExtractResponse(
        url=result["url"],
        data=result.get("data"),
        provider=result.get("provider", body.provider),
        success=result.get("success", False),
        error=result.get("error"),
    )


@router.post("/extract-regex", response_model=RegexExtractResponse)
@limiter.limit("10/minute")
async def extract_regex(
    request: Request,
    body: RegexExtractRequest,
    current_user: User = Depends(require_verified_email),
):
    """
    Extract structured data from a page using regex patterns.

    No LLM or CSS required — uses crawl4ai's RegexExtractionStrategy with
    21 built-in named patterns (email, phone_intl, url, ipv4, currency, etc.)
    plus optional custom regex patterns.

    Built-in pattern names: email, phone_intl, phone_us, url, ipv4, ipv6,
    uuid, currency, percentage, number, date_iso, date_us, time_24h,
    postal_us, postal_uk, hex_color, twitter_handle, hashtag, mac_addr,
    iban, credit_card. Use "all" to enable all built-in patterns.

    Rate limit: 10/minute
    """
    auth_dict = body.auth.model_dump() if body.auth else None
    result = await WebCrawlerService.extract_regex(
        url=body.url,
        patterns=body.patterns,
        custom_patterns=body.custom_patterns,
        auth=auth_dict,
    )

    return RegexExtractResponse(
        url=result["url"],
        matches=[RegexMatch(**m) for m in result.get("matches", [])],
        match_count=result.get("match_count", 0),
        success=result.get("success", False),
        error=result.get("error"),
    )


@router.post("/extract-xpath", response_model=ExtractResponse)
@limiter.limit("10/minute")
async def extract_xpath(
    request: Request,
    body: XPathExtractRequest,
    current_user: User = Depends(require_verified_email),
):
    """
    Extract structured data from a page using XPath selectors.

    Alternative to CSS-based extraction — useful when the page structure is
    better expressed in XPath (e.g. deep attribute targeting, relative paths).
    Uses crawl4ai's JsonXPathExtractionStrategy with lxml under the hood.

    Define `base_selector` (XPath to the repeating container) and `fields`
    (XPath relative to each container with optional `transform`).

    Rate limit: 10/minute
    """
    auth_dict = body.auth.model_dump() if body.auth else None
    fields_list = [f.model_dump() for f in body.fields]
    result = await WebCrawlerService.extract_xpath(
        url=body.url,
        base_selector=body.base_selector,
        fields=fields_list,
        auth=auth_dict,
    )

    return ExtractResponse(
        url=result["url"],
        items=result.get("items", []),
        item_count=result.get("item_count", 0),
        success=result.get("success", False),
        error=result.get("error"),
    )


@router.post("/generate-schema", response_model=GenerateSchemaResponse)
@limiter.limit("5/minute")
async def generate_schema(
    request: Request,
    body: GenerateSchemaRequest,
    current_user: User = Depends(require_ai_call_quota),
    session: AsyncSession = Depends(get_session),
):
    """
    Auto-generate a CSS or XPath extraction schema for a URL using AI.

    Fetches the page and uses an LLM to infer the best selector schema
    based on a natural language `query` (e.g. "product listings with price").
    The returned `schema_def` can be used directly in /extract or /extract-xpath.

    Supports providers: gemini (default), claude, groq.

    Rate limit: 5/minute (uses AI API)
    """
    result = await WebCrawlerService.generate_schema(
        url=body.url,
        query=body.query,
        schema_type=body.schema_type,
        provider=body.provider,
    )

    await BillingService.consume_quota(current_user.id, "ai_call", 1, session)

    return GenerateSchemaResponse(
        url=result["url"],
        schema_def=result.get("schema_def"),
        schema_type=result.get("schema_type", body.schema_type),
        success=result.get("success", False),
        error=result.get("error"),
    )


@router.post("/process-html", response_model=ProcessHtmlResponse)
@limiter.limit("20/minute")
async def process_html(
    request: Request,
    body: ProcessHtmlRequest,
    current_user: User = Depends(require_verified_email),
):
    """
    Process raw HTML without a browser fetch.

    Converts already-fetched HTML into markdown, fit_markdown, and link lists
    using crawl4ai's full content pipeline. Useful when you already have HTML
    from your own fetch layer and just want crawl4ai's extraction logic.

    Rate limit: 20/minute
    """
    result = await WebCrawlerService.process_html(
        html=body.html,
        url=body.url,
        use_fit_markdown=body.use_fit_markdown,
        topic=body.topic,
        css_selector=body.css_selector,
        word_count_threshold=body.word_count_threshold,
    )

    return ProcessHtmlResponse(
        url=result["url"],
        markdown=result.get("markdown", ""),
        fit_markdown=result.get("fit_markdown", ""),
        text_length=result.get("text_length", 0),
        links_internal=result.get("links_internal", []),
        links_external=result.get("links_external", []),
        success=result.get("success", False),
        error=result.get("error"),
    )


@router.post("/batch", response_model=BatchScrapeResponse)
@limiter.limit("3/minute")
async def batch_scrape(
    request: Request,
    body: BatchScrapeRequest,
    current_user: User = Depends(require_verified_email),
):
    """
    Scrape up to 10 URLs in parallel using crawl4ai's MemoryAdaptiveDispatcher.

    Handles rate limiting, memory pressure, and exponential backoff automatically.
    Returns fit_markdown by default (set `use_fit_markdown=false` for raw markdown).

    Rate limit: 3/minute
    """
    result = await WebCrawlerService.batch_scrape(
        urls=body.urls,
        use_fit_markdown=body.use_fit_markdown,
        extract_images=body.extract_images,
        dispatcher_config=body.dispatcher.model_dump() if body.dispatcher else None,
        proxies=[p.model_dump() for p in body.proxies] if body.proxies else None,
    )

    return BatchScrapeResponse(
        total=result.get("total", 0),
        succeeded=result.get("succeeded", 0),
        failed=result.get("failed", 0),
        results=[BatchScrapeResult(**r) for r in result.get("results", [])],
        monitor_stats=result.get("monitor_stats"),
    )


@router.post("/deep-crawl", response_model=DeepCrawlResponse)
@limiter.limit("2/minute")
async def deep_crawl(
    request: Request,
    body: DeepCrawlRequest,
    current_user: User = Depends(require_ai_call_quota),
    session: AsyncSession = Depends(get_session),
):
    """
    Deep crawl a site using BFS / DFS / Best-First strategy.

    Automatically discovers and follows internal links from the seed URL.
    Returns content for all crawled pages with depth and relevance score.

    Strategies:
    - `bfs`: Breadth-first (level by level, good for shallow wide crawls)
    - `dfs`: Depth-first (follows chains, good for deep structured sites)
    - `best_first`: Score-guided (follows most relevant links first)

    Advanced filters (v4):
    - `content_type_filter`: Restrict to specific MIME types (e.g. ["text/html"])
    - `content_relevance_query`: BM25 relevance filter — only follow relevant pages
    - `seo_filter`: SEO quality filter — skip low-quality pages
    - `resume_state`: Resume a previous crawl from its exported state

    Rate limit: 2/minute
    """
    result = await WebCrawlerService.deep_crawl(
        url=body.url,
        strategy=body.strategy,
        max_depth=body.max_depth,
        max_pages=body.max_pages,
        score_threshold=body.score_threshold,
        include_external=body.include_external,
        use_fit_markdown=body.use_fit_markdown,
        topic=body.topic,
        keyword_scorer_keywords=body.keyword_scorer_keywords or None,
        url_patterns=body.url_patterns or None,
        allowed_domains=body.allowed_domains or None,
        blocked_domains=body.blocked_domains or None,
        # Advanced filters (v4)
        content_type_filter=body.content_type_filter or None,
        content_relevance_query=body.content_relevance_query,
        content_relevance_threshold=body.content_relevance_threshold,
        seo_filter=body.seo_filter,
        seo_filter_threshold=body.seo_filter_threshold,
        resume_state=body.resume_state,
        # v7
        composite_scorers=body.composite_scorers or None,
        domain_authority_weights=body.domain_authority_weights or None,
        dispatcher_config=body.dispatcher.model_dump() if body.dispatcher else None,
        proxies=[p.model_dump() for p in body.proxies] if body.proxies else None,
    )

    pages_crawled = result.get("total_pages", 1)
    await BillingService.consume_quota(
        current_user.id, "ai_call", max(pages_crawled, 1), session
    )

    return DeepCrawlResponse(
        url=result["url"],
        strategy=result.get("strategy", body.strategy),
        pages=[DeepCrawlPageResult(**p) for p in result.get("pages", [])],
        total_pages=result.get("total_pages", 0),
        succeeded=result.get("succeeded", 0),
        failed=result.get("failed", 0),
        export_state=result.get("export_state"),
        monitor_stats=result.get("monitor_stats"),
        success=result.get("success", False),
        error=result.get("error"),
    )


@router.post("/seed-urls", response_model=SeedResponse)
@limiter.limit("5/minute")
async def seed_urls(
    request: Request,
    body: SeedRequest,
    current_user: User = Depends(require_verified_email),
):
    """
    Discover all URLs for a domain via sitemap or crawl-based seeding.

    Useful for building a URL corpus before batching or indexing.
    Supports sitemap (XML), crawl (follow links), or sitemaps (all sub-sitemaps).

    Advanced options (v4):
    - `pattern`: Glob/regex pattern to filter discovered URLs
    - `query` + `score_threshold`: BM25-score URLs against a topic query
      (auto-enables head extraction for title/description scoring)

    Rate limit: 5/minute
    """
    result = await WebCrawlerService.seed_urls(
        domain=body.domain,
        source=body.source,
        max_urls=body.max_urls,
        pattern=body.pattern,
        query=body.query,
        score_threshold=body.score_threshold,
        extract_head=body.extract_head,
    )

    return SeedResponse(
        domain=result["domain"],
        urls=result.get("urls", []),
        total=result.get("total", 0),
        success=result.get("success", False),
        error=result.get("error"),
    )


# ---------------------------------------------------------------------------
# v5 new endpoints
# ---------------------------------------------------------------------------


@router.post("/scrape-http", response_model=FastScrapeResponse)
@limiter.limit("20/minute")
async def scrape_http(
    request: Request,
    body: FastScrapeRequest,
    current_user: User = Depends(require_verified_email),
):
    """
    Scrape a URL using pure HTTP — no browser, no JavaScript.

    Uses crawl4ai's HTTPCrawlerConfig for 10-20x faster scraping.
    Best for static HTML, server-rendered content, or REST endpoints.

    Rate limit: 20/minute
    """
    result = await WebCrawlerService.scrape_http(
        url=body.url,
        css_selector=body.css_selector,
        word_count_threshold=body.word_count_threshold,
        use_fit_markdown=body.use_fit_markdown,
        headers=body.headers or None,
        follow_redirects=body.follow_redirects,
    )

    return FastScrapeResponse(
        url=result["url"],
        title=result.get("title", ""),
        markdown=result.get("markdown", ""),
        fit_markdown=result.get("fit_markdown", ""),
        text_length=result.get("text_length", 0),
        links_internal=result.get("links_internal", []),
        links_external=result.get("links_external", []),
        status_code=result.get("status_code"),
        scraper=result.get("scraper", "crawl4ai_http"),
        success=result.get("success", False),
        error=result.get("error"),
    )


@router.post("/adaptive-crawl", response_model=AdaptiveCrawlResponse)
@limiter.limit("2/minute")
async def adaptive_crawl(
    request: Request,
    body: AdaptiveCrawlRequest,
    current_user: User = Depends(require_ai_call_quota),
    session: AsyncSession = Depends(get_session),
):
    """
    Crawl a site using AdaptiveCrawler — self-tuning strategy that learns
    relevance as it crawls and stops automatically when confident.

    Strategies:
    - `statistical`: BM25/TF-IDF scoring — fast, no GPU required
    - `embedding`: semantic similarity — more accurate, requires sentence-transformers

    Rate limit: 2/minute
    """
    result = await WebCrawlerService.adaptive_crawl(
        url=body.url,
        query=body.query,
        max_pages=body.max_pages,
        max_depth=body.max_depth,
        strategy=body.strategy,
        confidence_threshold=body.confidence_threshold,
    )

    pages_crawled = result.get("total_pages", 1)
    await BillingService.consume_quota(
        current_user.id, "ai_call", max(pages_crawled, 1), session
    )

    return AdaptiveCrawlResponse(
        url=result["url"],
        query=result.get("query", body.query),
        pages=[AdaptiveCrawlPageResult(**p) for p in result.get("pages", [])],
        total_pages=result.get("total_pages", 0),
        succeeded=result.get("succeeded", 0),
        failed=result.get("failed", 0),
        confidence=result.get("confidence"),
        is_sufficient=result.get("is_sufficient"),
        success=result.get("success", False),
        error=result.get("error"),
    )


@router.post("/hub/crawl", response_model=HubCrawlResponse)
@limiter.limit("10/minute")
async def hub_crawl(
    request: Request,
    body: HubCrawlRequest,
    current_user: User = Depends(require_verified_email),
):
    """
    Crawl a URL using a CrawlerHub site profile.

    CrawlerHub provides pre-tuned configurations for well-known sites
    (e.g. 'wikipedia', 'reddit', 'github', 'arxiv'). Each profile handles
    site-specific rate limits, JavaScript, and selectors automatically.

    Rate limit: 10/minute
    """
    result = await WebCrawlerService.hub_crawl(
        url=body.url,
        site_profile=body.site_profile,
        use_fit_markdown=body.use_fit_markdown,
    )

    return HubCrawlResponse(
        url=result["url"],
        site_profile=result.get("site_profile", body.site_profile),
        data=result.get("data"),
        success=result.get("success", False),
        error=result.get("error"),
    )


@router.post("/c4a/compile", response_model=C4ACompileResponse)
@limiter.limit("20/minute")
async def compile_c4a_script(
    request: Request,
    body: C4ACompileRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Compile C4A-Script DSL to JavaScript.

    C4A-Script is a simple DSL for page interactions (click, type, wait, scroll).
    The compiled JavaScript can be used in `js_code` or `js_code_before_wait`
    fields of the /scrape endpoint.

    Rate limit: 20/minute
    """
    result = WebCrawlerService.compile_c4a(script=body.script)
    return C4ACompileResponse(
        js_code=result.get("js_code", ""),
        success=result.get("success", False),
        error=result.get("error"),
    )


@router.post("/c4a/validate", response_model=C4AValidateResponse)
@limiter.limit("30/minute")
async def validate_c4a_script(
    request: Request,
    body: C4AValidateRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Validate C4A-Script syntax without compiling.

    Returns whether the script is valid and any syntax errors found.

    Rate limit: 30/minute
    """
    result = WebCrawlerService.validate_c4a(script=body.script)
    return C4AValidateResponse(
        valid=result.get("valid", False),
        errors=result.get("errors", []),
    )


@router.post("/c4a/compile-file", response_model=C4ACompileResponse)
@limiter.limit("20/minute")
async def compile_c4a_file(
    request: Request,
    body: C4ACompileFileRequest,
    current_user: User = Depends(get_current_user),
):
    """Compile a C4A-Script file to JavaScript. Rate limit: 20/minute"""
    result = WebCrawlerService.compile_c4a_file(file_path=body.file_path)
    return C4ACompileResponse(
        js_code=result.get("js_code", ""),
        success=result.get("success", False),
        error=result.get("error"),
    )


# ------------------------------------------------------------------
# Browser profiler
# ------------------------------------------------------------------

@router.get("/profiles", response_model=BrowserProfileResponse)
@limiter.limit("10/minute")
async def list_browser_profiles(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """List all persistent browser profiles. Rate limit: 10/minute"""
    result = WebCrawlerService.list_browser_profiles()
    return BrowserProfileResponse(**result)


@router.post("/profiles", response_model=BrowserProfileResponse)
@limiter.limit("5/minute")
async def create_browser_profile(
    request: Request,
    body: BrowserProfileCreateRequest,
    current_user: User = Depends(get_current_user),
):
    """Create a persistent browser profile. Rate limit: 5/minute"""
    result = WebCrawlerService.create_browser_profile(profile_name=body.profile_name)
    return BrowserProfileResponse(**result)


@router.delete("/profiles/{profile_name}", response_model=BrowserProfileResponse)
@limiter.limit("5/minute")
async def delete_browser_profile(
    request: Request,
    profile_name: str,
    current_user: User = Depends(get_current_user),
):
    """Delete a persistent browser profile. Rate limit: 5/minute"""
    result = WebCrawlerService.delete_browser_profile(profile_name=profile_name)
    return BrowserProfileResponse(**result)


# ------------------------------------------------------------------
# Docker remote crawl
# ------------------------------------------------------------------

@router.post("/docker-crawl", response_model=DockerCrawlResponse)
@limiter.limit("3/minute")
async def docker_crawl(
    request: Request,
    body: DockerCrawlRequest,
    current_user: User = Depends(get_current_user),
):
    """Crawl URLs via a remote crawl4ai Docker container. Rate limit: 3/minute"""
    result = await WebCrawlerService.docker_crawl(
        urls=body.urls,
        docker_url=body.docker_url,
        timeout=body.timeout,
    )
    return DockerCrawlResponse(
        total=result.get("total", 0),
        succeeded=result.get("succeeded", 0),
        failed=result.get("failed", 0),
        results=[DockerCrawlResult(**r) for r in result.get("results", [])],
        success=result.get("success", False),
        error=result.get("error"),
    )


# ------------------------------------------------------------------
# PDF scraping
# ------------------------------------------------------------------

@router.post("/scrape-pdf", response_model=PdfScrapeResponse)
@limiter.limit("5/minute")
async def scrape_pdf(
    request: Request,
    body: PdfScrapeRequest,
    current_user: User = Depends(get_current_user),
):
    """Scrape PDF content using crawl4ai's PDFContentScrapingStrategy. Rate limit: 5/minute"""
    result = await WebCrawlerService.scrape_pdf(
        url=body.url,
        extract_images=body.extract_images,
    )
    return PdfScrapeResponse(**result)


# ------------------------------------------------------------------
# Cosine clustering extraction
# ------------------------------------------------------------------

@router.post("/extract-cosine", response_model=CosineExtractResponse)
@limiter.limit("5/minute")
async def extract_cosine(
    request: Request,
    body: CosineExtractRequest,
    current_user: User = Depends(get_current_user),
):
    """Extract content clusters using CosineStrategy (semantic similarity). Rate limit: 5/minute"""
    result = await WebCrawlerService.extract_cosine(
        url=body.url,
        word_count_threshold=body.word_count_threshold,
        max_dist=body.max_dist,
        top_k=body.top_k,
        sim_threshold=body.sim_threshold,
        semantic_filter=body.semantic_filter,
    )
    return CosineExtractResponse(
        url=result["url"],
        clusters=[CosineCluster(**c) for c in result.get("clusters", [])],
        total_clusters=result.get("total_clusters", 0),
        success=result.get("success", False),
        error=result.get("error"),
    )


# ------------------------------------------------------------------
# JSON lxml extraction
# ------------------------------------------------------------------

@router.post("/extract-lxml", response_model=LxmlExtractResponse)
@limiter.limit("5/minute")
async def extract_lxml(
    request: Request,
    body: LxmlExtractRequest,
    current_user: User = Depends(get_current_user),
):
    """Extract structured data using JsonLxmlExtractionStrategy. Rate limit: 5/minute"""
    result = await WebCrawlerService.extract_lxml(
        url=body.url,
        schema=body.schema,
    )
    return LxmlExtractResponse(**result)


# ------------------------------------------------------------------
# Regex chunking
# ------------------------------------------------------------------

@router.post("/chunk-regex", response_model=RegexChunkResponse)
@limiter.limit("20/minute")
async def chunk_regex(
    request: Request,
    body: RegexChunkRequest,
    current_user: User = Depends(get_current_user),
):
    """Split text into chunks using RegexChunking. Rate limit: 20/minute"""
    result = WebCrawlerService.chunk_regex(
        text=body.text,
        patterns=body.patterns,
    )
    return RegexChunkResponse(**result)
