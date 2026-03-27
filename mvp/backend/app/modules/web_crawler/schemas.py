"""
Web crawler schemas — v5 (full crawl4ai feature surface).
"""

from typing import Any, Optional

from pydantic import BaseModel, Field, HttpUrl


class AuthConfig(BaseModel):
    """Authentication configuration for crawling protected pages."""
    cookies: Optional[dict[str, str]] = Field(
        default=None,
        description="Cookies to send with the request (e.g. session cookies)",
    )
    headers: Optional[dict[str, str]] = Field(
        default=None,
        description="Custom headers (e.g. Authorization: Bearer xxx)",
    )
    login_url: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="URL of the login page for auto-login",
    )
    login_js: Optional[str] = Field(
        default=None,
        max_length=5000,
        description="JavaScript to execute on login page (fill form + submit)",
    )
    wait_after_login_ms: int = Field(
        default=3000,
        ge=500,
        le=15000,
        description="Milliseconds to wait after login before crawling",
    )


class GeolocationConfig(BaseModel):
    """Geographic location to emulate in the browser (Playwright geolocation API)."""
    latitude: float = Field(
        ...,
        ge=-90.0,
        le=90.0,
        description="Latitude in decimal degrees (-90 to 90)",
    )
    longitude: float = Field(
        ...,
        ge=-180.0,
        le=180.0,
        description="Longitude in decimal degrees (-180 to 180)",
    )
    accuracy: float = Field(
        default=0.0,
        ge=0.0,
        le=10000.0,
        description="Accuracy radius in meters (default 0.0)",
    )


class ScrapeRequest(BaseModel):
    # ---- Core ----
    url: str = Field(..., min_length=1, max_length=2000)
    extract_images: bool = Field(default=True)
    screenshot: bool = Field(default=False)
    max_images: int = Field(default=20, ge=1, le=100)
    use_fit_markdown: bool = Field(
        default=True,
        description="Noise-filtered markdown via PruningContentFilter (better for RAG)",
    )
    topic: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Topic hint — switches content filter to BM25 for topic-aware extraction",
    )
    # ---- Page interaction ----
    wait_for: Optional[str] = Field(
        default=None,
        max_length=500,
        description="CSS selector or JS condition to wait for before capturing (prefix 'css:' or 'js:')",
    )
    wait_for_timeout: Optional[int] = Field(
        default=None,
        ge=500,
        le=60000,
        description="Timeout in ms for the wait_for condition (defaults to page_timeout)",
    )
    js_code: Optional[str] = Field(
        default=None,
        max_length=5000,
        description="JavaScript to execute after page load and wait conditions",
    )
    js_code_before_wait: Optional[str] = Field(
        default=None,
        max_length=5000,
        description="JavaScript to execute BEFORE the wait_for condition (e.g. trigger a click)",
    )
    max_retries: int = Field(
        default=0,
        ge=0,
        le=5,
        description="Number of retry attempts on anti-bot detection or transient failures",
    )
    auth: Optional[AuthConfig] = Field(default=None)

    # ---- Rendering ----
    scan_full_page: bool = Field(
        default=False,
        description="Auto-scroll to trigger lazy loading and infinite scroll",
    )
    process_iframes: bool = Field(
        default=False,
        description="Extract and inline content from iframes",
    )
    flatten_shadow_dom: bool = Field(
        default=False,
        description="Flatten Web Components / Shadow DOM before extraction",
    )
    remove_overlay_elements: bool = Field(
        default=False,
        description="Remove cookie banners, popups, and overlay elements",
    )
    remove_consent_popups: bool = Field(
        default=False,
        description="Remove GDPR/cookie consent banners from known CMP providers",
    )
    simulate_user: bool = Field(
        default=False,
        description="Simulate human mouse movements to bypass bot detection",
    )
    virtual_scroll_selector: Optional[str] = Field(
        default=None,
        max_length=200,
        description="CSS selector for virtual/windowed scroll container",
    )
    adjust_viewport_to_content: bool = Field(
        default=False,
        description="Resize viewport height to match full page content before capture",
    )

    # ---- Reliability ----
    page_timeout: int = Field(
        default=30000,
        ge=5000,
        le=120000,
        description="Page load timeout in milliseconds",
    )
    check_robots_txt: bool = Field(
        default=False,
        description="Respect robots.txt crawling rules",
    )

    # ---- Content filtering ----
    word_count_threshold: int = Field(
        default=10,
        ge=1,
        le=200,
        description="Minimum word count to keep a content block",
    )
    css_selector: Optional[str] = Field(
        default=None,
        max_length=500,
        description="CSS selector to scope extraction to a specific region of the page",
    )
    target_elements: Optional[list[str]] = Field(
        default=None,
        description="List of CSS selectors to target for extraction (overrides global content)",
    )
    only_text: bool = Field(
        default=False,
        description="Extract plain text only, stripping all HTML/Markdown formatting",
    )
    parser_type: str = Field(
        default="lxml",
        pattern="^(lxml|html.parser)$",
        description="HTML parser backend: lxml (fast) or html.parser (pure Python)",
    )
    delay_before_return_html: float = Field(
        default=0.1,
        ge=0.0,
        le=10.0,
        description="Seconds to pause after page loads before capturing HTML (lets dynamic content settle)",
    )
    excluded_tags: list[str] = Field(
        default=[],
        description="HTML tags to strip before extraction (e.g. ['nav','footer','script'])",
    )
    excluded_selector: Optional[str] = Field(
        default=None,
        max_length=500,
        description="CSS selector — matching elements are removed before extraction",
    )
    table_extraction: bool = Field(
        default=False,
        description="Force-include all tables regardless of quality score (legacy flag, use table_extraction_mode)",
    )
    table_extraction_mode: str = Field(
        default="default",
        pattern="^(default|none|llm)$",
        description="Table extraction mode: default (built-in) | none (skip tables) | llm (AI-powered with chunking)",
    )

    # ---- Links ----
    score_links: bool = Field(
        default=False,
        description="Score and rank extracted links by relevance",
    )
    extract_external_links: bool = Field(
        default=False,
        description="Include external links in the response",
    )
    exclude_social_media_links: bool = Field(
        default=False,
        description="Strip social media links from output",
    )
    exclude_domains: list[str] = Field(
        default=[],
        description="List of domains to exclude from link extraction results",
    )

    # ---- Media ----
    extract_audio: bool = Field(default=False, description="Extract audio media metadata")
    extract_video: bool = Field(default=False, description="Extract video media metadata")
    image_score_threshold: int = Field(
        default=2,
        ge=0,
        le=10,
        description="Minimum relevance score for images to be included (0 = include all)",
    )

    # ---- Output formats ----
    pdf: bool = Field(default=False, description="Capture page as PDF (returned as base64)")
    capture_mhtml: bool = Field(
        default=False,
        description="Capture full-page MHTML single-file snapshot",
    )
    capture_network_requests: bool = Field(
        default=False,
        description="Record all network request URLs made during page load",
    )
    log_console: bool = Field(
        default=False,
        description="Log browser console output (warnings, errors) to server logs",
    )
    capture_console_messages: bool = Field(
        default=False,
        description="Capture browser console messages in the response",
    )
    fetch_ssl_certificate: bool = Field(
        default=False,
        description="Include SSL/TLS certificate details in the response",
    )

    # ---- Browser identity ----
    proxy_url: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Proxy URL e.g. http://user:pass@host:port",
    )
    user_agent: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Custom User-Agent string (use 'random' for rotation)",
    )

    # ---- Browser config ----
    enable_stealth: bool = Field(
        default=False,
        description="Activate bot-detection bypass (removes webdriver flag, modifies fingerprints)",
    )
    browser_type: str = Field(
        default="chromium",
        pattern="^(chromium|firefox|webkit|undetected)$",
        description="Browser engine: chromium (default) | firefox | webkit | undetected (v0.8.5 anti-bot)",
    )
    javascript_enabled: bool = Field(
        default=True,
        description="Enable JavaScript execution (disable for faster text-only crawls)",
    )
    avoid_ads: bool = Field(
        default=False,
        description="Block ad/tracker domains automatically",
    )
    session_id: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Session ID to reuse browser state across requests (multi-step workflows)",
    )
    geolocation: Optional[GeolocationConfig] = Field(
        default=None,
        description="Emulate browser GPS location (latitude, longitude, accuracy) for geo-restricted content",
    )

    # ---- Cache ----
    cache_mode: str = Field(
        default="bypass",
        pattern="^(enabled|disabled|bypass|read_only|write_only)$",
        description="Cache behavior: bypass (default) | enabled | disabled | read_only | write_only",
    )

    # ---- Markdown display ----
    ignore_links: bool = Field(
        default=False,
        description="Remove all hyperlinks from the markdown output",
    )
    body_width: int = Field(
        default=0,
        ge=0,
        le=200,
        description="Wrap markdown text at N characters (0 = no wrapping)",
    )

    # ---- Link preview ----
    link_preview_query: Optional[str] = Field(
        default=None,
        max_length=200,
        description="BM25 query to score and rank discovered links by relevance",
    )
    link_preview_max_links: int = Field(
        default=0,
        ge=0,
        le=500,
        description="Max links to head-fetch and score (0 = disabled)",
    )


# ---------------------------------------------------------------------------
# Media types
# ---------------------------------------------------------------------------

class ImageData(BaseModel):
    src: str
    alt: str = ""
    score: float = 0.0
    description: Optional[str] = None


class AudioData(BaseModel):
    src: str
    alt: str = ""
    type: Optional[str] = None


class VideoData(BaseModel):
    src: str
    alt: str = ""
    poster: Optional[str] = None
    type: Optional[str] = None


class TableData(BaseModel):
    headers: list[str] = []
    rows: list[list[str]] = []
    caption: Optional[str] = None


# ---------------------------------------------------------------------------
# Scrape response
# ---------------------------------------------------------------------------

class ScrapeResponse(BaseModel):
    url: str
    title: str = ""
    markdown: str = ""
    fit_markdown: str = ""
    text_length: int = 0
    images: list[ImageData] = []
    image_count: int = 0
    audio: list[AudioData] = []
    video: list[VideoData] = []
    screenshot_base64: Optional[str] = None
    pdf_base64: Optional[str] = None
    mhtml: Optional[str] = None
    links_internal: list[str] = []
    links_external: list[str] = []
    tables: list[TableData] = []
    network_requests: list[str] = []
    console_messages: list[dict] = []
    ssl_certificate: Optional[dict] = None
    status_code: Optional[int] = None
    redirected_url: Optional[str] = None
    scraper: str = "crawl4ai"
    success: bool = True
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Vision scrape
# ---------------------------------------------------------------------------

class ScrapeWithVisionRequest(BaseModel):
    url: str = Field(..., min_length=1, max_length=2000)
    max_images: int = Field(default=10, ge=1, le=50)
    vision_prompt: str = Field(
        default="Describe this image concisely: what it shows, any text visible, and its purpose on the webpage.",
        max_length=500,
    )
    auth: Optional[AuthConfig] = Field(default=None)


class ScrapeWithVisionResponse(BaseModel):
    url: str
    title: str = ""
    markdown: str = ""
    images: list[ImageData] = []
    vision_provider: str = ""
    success: bool = True
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Index to knowledge base
# ---------------------------------------------------------------------------

class IndexRequest(BaseModel):
    url: str = Field(..., min_length=1, max_length=2000)
    crawl_subpages: bool = Field(default=False)
    max_pages: int = Field(default=5, ge=1, le=20)
    include_images: bool = Field(default=True)
    topic: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Topic hint — enables BM25 content filtering for higher-quality KB chunks",
    )
    auth: Optional[AuthConfig] = Field(default=None)


class IndexResponse(BaseModel):
    url: str
    pages_crawled: int = 0
    chunks_indexed: int = 0
    images_found: int = 0
    success: bool = True
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Structured CSS extraction
# ---------------------------------------------------------------------------

class ExtractField(BaseModel):
    name: str = Field(..., max_length=100, description="Output field name")
    selector: str = Field(..., max_length=500, description="CSS selector relative to base_selector")
    type: str = Field(
        default="text",
        pattern="^(text|attribute|html|link)$",
        description="Extraction type: text, attribute, html, or link",
    )
    attribute: Optional[str] = Field(
        default=None,
        max_length=100,
        description="HTML attribute name (required when type=attribute)",
    )


class ExtractRequest(BaseModel):
    url: str = Field(..., min_length=1, max_length=2000)
    base_selector: str = Field(
        ...,
        max_length=500,
        description="CSS selector for repeated container elements (e.g. '.product-card')",
    )
    fields: list[ExtractField] = Field(..., min_length=1, max_length=20)
    auth: Optional[AuthConfig] = Field(default=None)


class ExtractResponse(BaseModel):
    url: str
    items: list[dict] = []
    item_count: int = 0
    success: bool = True
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# LLM-powered extraction
# ---------------------------------------------------------------------------

class LLMExtractRequest(BaseModel):
    url: str = Field(..., min_length=1, max_length=2000)
    instruction: str = Field(
        ...,
        min_length=5,
        max_length=2000,
        description="Natural language instruction (e.g. 'Extract all product names and prices')",
    )
    schema_def: Optional[dict] = Field(
        default=None,
        description="Optional JSON Schema for structured output; omit for free-form block extraction",
    )
    provider: str = Field(
        default="gemini",
        pattern="^(gemini|claude|groq)$",
        description="AI provider: gemini | claude | groq",
    )
    auth: Optional[AuthConfig] = Field(default=None)


class LLMExtractResponse(BaseModel):
    url: str
    data: Optional[Any] = None
    provider: str = ""
    success: bool = True
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Batch scraping
# ---------------------------------------------------------------------------

class BatchScrapeRequest(BaseModel):
    urls: list[str] = Field(..., min_length=1, max_length=10, description="Up to 10 URLs to crawl in parallel")
    use_fit_markdown: bool = Field(default=True)
    extract_images: bool = Field(default=False)


class BatchScrapeResult(BaseModel):
    url: str
    title: str = ""
    markdown: str = ""
    success: bool = True
    error: Optional[str] = None


class BatchScrapeResponse(BaseModel):
    total: int = 0
    succeeded: int = 0
    failed: int = 0
    results: list[BatchScrapeResult] = []


# ---------------------------------------------------------------------------
# Deep crawl (BFS / DFS / Best-First)
# ---------------------------------------------------------------------------

class DeepCrawlRequest(BaseModel):
    url: str = Field(..., min_length=1, max_length=2000)
    strategy: str = Field(
        default="bfs",
        pattern="^(bfs|dfs|best_first)$",
        description="Crawl strategy: bfs (breadth-first) | dfs (depth-first) | best_first (score-guided)",
    )
    max_depth: int = Field(default=2, ge=1, le=5, description="Maximum crawl depth from seed URL")
    max_pages: int = Field(default=10, ge=1, le=50, description="Maximum total pages to crawl")
    score_threshold: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Minimum relevance score for best_first strategy",
    )
    include_external: bool = Field(
        default=False,
        description="Follow links to external domains",
    )
    use_fit_markdown: bool = Field(default=True)
    topic: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Topic hint for BM25 content filtering",
    )
    # ---- URL filtering ----
    keyword_scorer_keywords: Optional[list[str]] = Field(
        default=None,
        description="Keywords for BestFirst scoring — URLs/content matching these rank higher",
    )
    url_patterns: Optional[list[str]] = Field(
        default=None,
        description="URL patterns (glob-style) to include during deep crawl (e.g. ['*docs*', '*guide*'])",
    )
    allowed_domains: Optional[list[str]] = Field(
        default=None,
        description="Whitelist of domains to follow during deep crawl",
    )
    blocked_domains: Optional[list[str]] = Field(
        default=None,
        description="Blacklist of domains to skip during deep crawl",
    )
    # ---- Advanced filters ----
    content_type_filter: Optional[list[str]] = Field(
        default=None,
        description="Allowed MIME types (e.g. ['text/html', 'application/pdf'])",
    )
    content_relevance_query: Optional[str] = Field(
        default=None,
        max_length=200,
        description="BM25 query — only follow pages whose <head> content matches",
    )
    content_relevance_threshold: float = Field(
        default=2.0,
        ge=0.0,
        le=20.0,
        description="BM25 raw score threshold for ContentRelevanceFilter (typical range 1–5)",
    )
    seo_filter: bool = Field(
        default=False,
        description="Filter out low-SEO pages (noindex, missing title, etc.)",
    )
    seo_filter_threshold: float = Field(
        default=0.65,
        ge=0.0,
        le=1.0,
        description="Weighted SEO score threshold (0–1) for SEOFilter",
    )
    # ---- Resume ----
    resume_state: Optional[dict] = Field(
        default=None,
        description="State dict from a previous deep crawl (export_state) to resume from",
    )


class DeepCrawlPageResult(BaseModel):
    url: str
    title: str = ""
    markdown: str = ""
    depth: int = 0
    score: Optional[float] = None
    success: bool = True
    error: Optional[str] = None


class DeepCrawlResponse(BaseModel):
    url: str
    strategy: str = "bfs"
    pages: list[DeepCrawlPageResult] = []
    total_pages: int = 0
    succeeded: int = 0
    failed: int = 0
    export_state: Optional[dict] = None
    success: bool = True
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# URL seeding (sitemap discovery)
# ---------------------------------------------------------------------------

class SeedRequest(BaseModel):
    domain: str = Field(
        ...,
        min_length=1,
        max_length=253,
        description="Domain to discover URLs for (e.g. 'docs.example.com')",
    )
    source: str = Field(
        default="sitemap",
        pattern="^(sitemap|crawl|sitemaps)$",
        description="URL discovery method: sitemap (parse XML sitemap) | crawl (follow links) | sitemaps (all sitemaps)",
    )
    max_urls: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum number of URLs to return",
    )
    pattern: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Glob-style URL pattern filter (e.g. '*example.com/blog/*')",
    )
    query: Optional[str] = Field(
        default=None,
        max_length=200,
        description="BM25 relevance query — only return URLs whose <head> matches (requires extract_head=true)",
    )
    score_threshold: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=20.0,
        description="Minimum BM25 score to include a URL (requires query)",
    )
    extract_head: bool = Field(
        default=False,
        description="Fetch <head> metadata for each URL (required for BM25 query scoring)",
    )


class SeedResponse(BaseModel):
    domain: str
    urls: list[str] = []
    total: int = 0
    success: bool = True
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Regex extraction (zero-LLM, 21 built-in patterns)
# ---------------------------------------------------------------------------

class RegexExtractRequest(BaseModel):
    url: str = Field(..., min_length=1, max_length=2000)
    patterns: list[str] = Field(
        default=[],
        description=(
            "Built-in pattern names to activate. Combine freely. "
            "Values: email, phone_intl, phone_us, url, ipv4, ipv6, uuid, currency, "
            "percentage, number, date_iso, date_us, time_24h, postal_us, postal_uk, "
            "hex_color, twitter_handle, hashtag, mac_addr, iban, credit_card, all"
        ),
    )
    custom_patterns: dict[str, str] = Field(
        default={},
        description="Custom regex patterns as {label: regex_pattern} (e.g. {'sku': 'SKU-\\\\d{6}'})",
    )
    auth: Optional[AuthConfig] = Field(default=None)


class RegexMatch(BaseModel):
    label: str
    value: str
    span: list[int]


class RegexExtractResponse(BaseModel):
    url: str
    matches: list[RegexMatch] = []
    match_count: int = 0
    success: bool = True
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# XPath extraction
# ---------------------------------------------------------------------------

class XPathExtractRequest(BaseModel):
    url: str = Field(..., min_length=1, max_length=2000)
    base_selector: str = Field(
        ...,
        max_length=500,
        description="XPath expression for repeated container elements (e.g. '//div[@class=\"product\"]')",
    )
    fields: list[ExtractField] = Field(..., min_length=1, max_length=20)
    auth: Optional[AuthConfig] = Field(default=None)


# XPathExtractResponse shares ExtractResponse (same shape: url, items, item_count, success, error)


# ---------------------------------------------------------------------------
# Auto-generate CSS/XPath schema via LLM
# ---------------------------------------------------------------------------

class GenerateSchemaRequest(BaseModel):
    url: str = Field(..., min_length=1, max_length=2000)
    query: str = Field(
        ...,
        min_length=5,
        max_length=500,
        description="Natural language description of what to extract (e.g. 'product names and prices')",
    )
    schema_type: str = Field(
        default="CSS",
        pattern="^(CSS|XPath)$",
        description="Selector type for the generated schema: CSS (default) | XPath",
    )
    provider: str = Field(
        default="gemini",
        pattern="^(gemini|claude|groq)$",
        description="AI provider to use for schema generation",
    )


class GenerateSchemaResponse(BaseModel):
    url: str
    schema_def: Optional[dict] = None
    schema_type: str = "CSS"
    success: bool = True
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Process raw HTML (no browser fetch)
# ---------------------------------------------------------------------------

class ProcessHtmlRequest(BaseModel):
    html: str = Field(
        ...,
        min_length=1,
        max_length=5_000_000,
        description="Raw HTML string to process through crawl4ai's pipeline",
    )
    url: str = Field(
        default="https://example.com",
        max_length=2000,
        description="URL context used for resolving relative links",
    )
    use_fit_markdown: bool = Field(
        default=True,
        description="Apply PruningContentFilter for noise-free markdown",
    )
    topic: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Topic hint — switches filter to BM25 for topic-aware extraction",
    )
    css_selector: Optional[str] = Field(
        default=None,
        max_length=500,
        description="CSS selector to scope extraction to a specific region",
    )
    word_count_threshold: int = Field(
        default=10,
        ge=1,
        le=200,
        description="Minimum word count to keep a content block",
    )


class ProcessHtmlResponse(BaseModel):
    url: str
    markdown: str = ""
    fit_markdown: str = ""
    text_length: int = 0
    links_internal: list[str] = []
    links_external: list[str] = []
    success: bool = True
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# HTTP-only fast scrape (no browser, uses HTTPCrawlerConfig)
# ---------------------------------------------------------------------------

class FastScrapeRequest(BaseModel):
    url: str = Field(..., min_length=1, max_length=2000)
    css_selector: Optional[str] = Field(
        default=None,
        max_length=500,
        description="CSS selector to scope extraction (optional)",
    )
    word_count_threshold: int = Field(
        default=10,
        ge=1,
        le=200,
        description="Minimum word count for content blocks",
    )
    use_fit_markdown: bool = Field(
        default=True,
        description="Apply PruningContentFilter for cleaner markdown",
    )
    headers: dict[str, str] = Field(
        default={},
        description="Custom HTTP headers (e.g. Authorization: Bearer xxx)",
    )
    follow_redirects: bool = Field(
        default=True,
        description="Follow HTTP redirects",
    )


class FastScrapeResponse(BaseModel):
    url: str
    title: str = ""
    markdown: str = ""
    fit_markdown: str = ""
    text_length: int = 0
    links_internal: list[str] = []
    links_external: list[str] = []
    status_code: Optional[int] = None
    scraper: str = "crawl4ai_http"
    success: bool = True
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Adaptive crawl (AdaptiveCrawler — self-tuning, stops when confident)
# ---------------------------------------------------------------------------

class AdaptiveCrawlRequest(BaseModel):
    url: str = Field(..., min_length=1, max_length=2000)
    query: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Topic query to guide the adaptive crawl (BM25/semantic scoring)",
    )
    max_pages: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum pages to crawl before stopping",
    )
    max_depth: int = Field(
        default=5,
        ge=1,
        le=15,
        description="Maximum link depth from the seed URL",
    )
    strategy: str = Field(
        default="statistical",
        pattern="^(statistical|embedding)$",
        description="Adaptive strategy: statistical (BM25/TF-IDF, fast) | embedding (semantic, slower)",
    )
    confidence_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Stop crawling when confidence reaches this threshold",
    )


class AdaptiveCrawlPageResult(BaseModel):
    url: str
    title: str = ""
    markdown: str = ""
    depth: int = 0
    score: Optional[float] = None
    success: bool = True
    error: Optional[str] = None


class AdaptiveCrawlResponse(BaseModel):
    url: str
    query: str = ""
    pages: list[AdaptiveCrawlPageResult] = []
    total_pages: int = 0
    succeeded: int = 0
    failed: int = 0
    confidence: Optional[float] = None
    is_sufficient: Optional[bool] = None
    success: bool = True
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# CrawlerHub — pre-built site-profile crawlers
# ---------------------------------------------------------------------------

class HubCrawlRequest(BaseModel):
    url: str = Field(..., min_length=1, max_length=2000)
    site_profile: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description=(
            "Named site profile for CrawlerHub (e.g. 'wikipedia', 'reddit', 'github', 'arxiv'). "
            "Provides pre-tuned configs for known sites."
        ),
    )
    use_fit_markdown: bool = Field(
        default=True,
        description="Apply PruningContentFilter for cleaner markdown output",
    )


class HubCrawlResponse(BaseModel):
    url: str
    site_profile: str = ""
    data: Optional[dict] = None
    success: bool = True
    error: Optional[str] = None
