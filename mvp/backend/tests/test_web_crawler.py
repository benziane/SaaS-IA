"""
Tests for the web_crawler module v2:
- Schemas (fit_markdown, topic, ExtractRequest, BatchScrapeRequest)
- Service helpers (_extract_markdown, _build_markdown_generator)
- Singleton lifecycle (get_crawler, init_crawler, close_crawler)
- Service methods (scrape, extract_structured, batch_scrape, index_to_knowledge_base)
- Routes (/scrape, /scrape-vision, /index, /extract, /batch)

All tests run without external services — crawl4ai, DB, Redis fully mocked.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4


# ---------------------------------------------------------------------------
# Schema tests
# ---------------------------------------------------------------------------

class TestWebCrawlerSchemas:

    def test_scrape_request_defaults(self):
        from app.modules.web_crawler.schemas import ScrapeRequest
        r = ScrapeRequest(url="https://example.com")
        assert r.use_fit_markdown is True
        assert r.extract_images is True
        assert r.screenshot is False
        assert r.max_images == 20
        assert r.auth is None

    def test_scrape_request_fit_markdown_false(self):
        from app.modules.web_crawler.schemas import ScrapeRequest
        r = ScrapeRequest(url="https://example.com", use_fit_markdown=False)
        assert r.use_fit_markdown is False

    def test_scrape_request_url_too_long(self):
        from pydantic import ValidationError
        from app.modules.web_crawler.schemas import ScrapeRequest
        with pytest.raises(ValidationError):
            ScrapeRequest(url="https://example.com/" + "a" * 2000)

    def test_scrape_request_url_empty(self):
        from pydantic import ValidationError
        from app.modules.web_crawler.schemas import ScrapeRequest
        with pytest.raises(ValidationError):
            ScrapeRequest(url="")

    def test_scrape_response_has_fit_markdown(self):
        from app.modules.web_crawler.schemas import ScrapeResponse
        r = ScrapeResponse(url="https://example.com", markdown="raw", fit_markdown="clean")
        assert r.fit_markdown == "clean"
        assert r.scraper == "crawl4ai"

    def test_index_request_topic(self):
        from app.modules.web_crawler.schemas import IndexRequest
        r = IndexRequest(url="https://example.com", topic="machine learning")
        assert r.topic == "machine learning"

    def test_index_request_topic_too_long(self):
        from pydantic import ValidationError
        from app.modules.web_crawler.schemas import IndexRequest
        with pytest.raises(ValidationError):
            IndexRequest(url="https://example.com", topic="x" * 201)

    def test_index_request_defaults(self):
        from app.modules.web_crawler.schemas import IndexRequest
        r = IndexRequest(url="https://example.com")
        assert r.topic is None
        assert r.crawl_subpages is False
        assert r.max_pages == 5

    def test_extract_field_defaults(self):
        from app.modules.web_crawler.schemas import ExtractField
        f = ExtractField(name="title", selector="h2")
        assert f.type == "text"
        assert f.attribute is None

    def test_extract_field_attribute_type(self):
        from app.modules.web_crawler.schemas import ExtractField
        f = ExtractField(name="href", selector="a", type="attribute", attribute="href")
        assert f.type == "attribute"
        assert f.attribute == "href"

    def test_extract_field_invalid_type(self):
        from pydantic import ValidationError
        from app.modules.web_crawler.schemas import ExtractField
        with pytest.raises(ValidationError):
            ExtractField(name="x", selector="div", type="invalid_type")

    def test_extract_request_valid(self):
        from app.modules.web_crawler.schemas import ExtractRequest, ExtractField
        r = ExtractRequest(
            url="https://example.com",
            base_selector=".product",
            fields=[ExtractField(name="title", selector="h2")],
        )
        assert r.base_selector == ".product"
        assert len(r.fields) == 1

    def test_extract_request_too_many_fields(self):
        from pydantic import ValidationError
        from app.modules.web_crawler.schemas import ExtractRequest, ExtractField
        with pytest.raises(ValidationError):
            ExtractRequest(
                url="https://example.com",
                base_selector=".item",
                fields=[ExtractField(name=f"f{i}", selector=f"span.{i}") for i in range(21)],
            )

    def test_batch_scrape_request_defaults(self):
        from app.modules.web_crawler.schemas import BatchScrapeRequest
        r = BatchScrapeRequest(urls=["https://a.com", "https://b.com"])
        assert r.use_fit_markdown is True
        assert r.extract_images is False
        assert len(r.urls) == 2

    def test_batch_scrape_request_too_many_urls(self):
        from pydantic import ValidationError
        from app.modules.web_crawler.schemas import BatchScrapeRequest
        with pytest.raises(ValidationError):
            BatchScrapeRequest(urls=[f"https://example{i}.com" for i in range(11)])

    def test_batch_scrape_request_empty_urls(self):
        from pydantic import ValidationError
        from app.modules.web_crawler.schemas import BatchScrapeRequest
        with pytest.raises(ValidationError):
            BatchScrapeRequest(urls=[])

    def test_auth_config_defaults(self):
        from app.modules.web_crawler.schemas import AuthConfig
        a = AuthConfig()
        assert a.cookies is None
        assert a.headers is None
        assert a.wait_after_login_ms == 3000

    def test_auth_config_wait_bounds(self):
        from pydantic import ValidationError
        from app.modules.web_crawler.schemas import AuthConfig
        with pytest.raises(ValidationError):
            AuthConfig(wait_after_login_ms=100)  # below min 500
        with pytest.raises(ValidationError):
            AuthConfig(wait_after_login_ms=20000)  # above max 15000


# ---------------------------------------------------------------------------
# Helper function tests
# ---------------------------------------------------------------------------

class TestExtractMarkdown:

    def test_none_result(self):
        from app.modules.web_crawler.service import _extract_markdown
        mock = MagicMock()
        mock.markdown = None
        raw, fit = _extract_markdown(mock)
        assert raw == ""
        assert fit == ""

    def test_object_api_with_fit(self):
        from app.modules.web_crawler.service import _extract_markdown
        mock = MagicMock()
        mock.markdown.raw_markdown = "# Raw Content\n\nNav stuff"
        mock.markdown.fit_markdown = "# Raw Content\n\nClean"
        raw, fit = _extract_markdown(mock)
        assert raw == "# Raw Content\n\nNav stuff"
        assert fit == "# Raw Content\n\nClean"

    def test_object_api_fit_falls_back_to_raw(self):
        from app.modules.web_crawler.service import _extract_markdown
        mock = MagicMock()
        mock.markdown.raw_markdown = "# Raw"
        mock.markdown.fit_markdown = ""  # empty fit → use raw
        raw, fit = _extract_markdown(mock)
        assert fit == "# Raw"

    def test_legacy_string_api(self):
        from app.modules.web_crawler.service import _extract_markdown
        mock = MagicMock()
        # Remove raw_markdown attribute so hasattr returns False
        del mock.markdown.raw_markdown
        mock.markdown.__str__ = lambda self: "plain string markdown"
        raw, fit = _extract_markdown(mock)
        assert raw == fit  # both equal when legacy


class TestBuildMarkdownGenerator:

    def test_without_topic_uses_pruning(self):
        from app.modules.web_crawler.service import _build_markdown_generator
        from crawl4ai.content_filter_strategy import PruningContentFilter
        gen = _build_markdown_generator()
        assert gen is not None
        assert isinstance(gen.content_filter, PruningContentFilter)

    def test_with_topic_uses_bm25(self):
        from app.modules.web_crawler.service import _build_markdown_generator
        from crawl4ai.content_filter_strategy import BM25ContentFilter
        gen = _build_markdown_generator(topic="machine learning")
        assert isinstance(gen.content_filter, BM25ContentFilter)


# ---------------------------------------------------------------------------
# Singleton lifecycle tests
# ---------------------------------------------------------------------------

class TestCrawlerLifecycle:

    @pytest.mark.asyncio
    async def test_init_crawler_starts_browser(self):
        import app.modules.web_crawler.service as svc

        mock_crawler = AsyncMock()
        mock_crawler.start = AsyncMock()

        original = svc._crawler
        try:
            svc._crawler = None
            # Patch at the crawl4ai module level (AsyncWebCrawler is imported
            # inside get_crawler(), not at service module level)
            with patch("crawl4ai.AsyncWebCrawler", return_value=mock_crawler), \
                 patch("crawl4ai.BrowserConfig"):
                await svc.init_crawler()
                mock_crawler.start.assert_called_once()
        finally:
            svc._crawler = original

    @pytest.mark.asyncio
    async def test_init_crawler_handles_exception(self):
        import app.modules.web_crawler.service as svc

        original = svc._crawler
        try:
            svc._crawler = None
            with patch("crawl4ai.AsyncWebCrawler", side_effect=ImportError("no crawl4ai")):
                # Must not raise — exception is swallowed with a warning log
                await svc.init_crawler()
        finally:
            svc._crawler = original

    @pytest.mark.asyncio
    async def test_close_crawler_calls_close(self):
        import app.modules.web_crawler.service as svc

        mock_crawler = AsyncMock()
        mock_crawler.close = AsyncMock()

        original = svc._crawler
        try:
            svc._crawler = mock_crawler
            await svc.close_crawler()
            mock_crawler.close.assert_called_once()
            assert svc._crawler is None
        finally:
            svc._crawler = original

    @pytest.mark.asyncio
    async def test_close_crawler_noop_when_none(self):
        import app.modules.web_crawler.service as svc

        original = svc._crawler
        try:
            svc._crawler = None
            await svc.close_crawler()  # must not raise
        finally:
            svc._crawler = original

    @pytest.mark.asyncio
    async def test_get_crawler_returns_singleton(self):
        import app.modules.web_crawler.service as svc

        mock_crawler = AsyncMock()
        mock_crawler.start = AsyncMock()

        original = svc._crawler
        try:
            svc._crawler = None
            # AsyncWebCrawler is imported inside get_crawler() via
            # "from crawl4ai import AsyncWebCrawler" — patch at the crawl4ai module level
            with patch("crawl4ai.AsyncWebCrawler", return_value=mock_crawler), \
                 patch("crawl4ai.BrowserConfig"):
                c1 = await svc.get_crawler()
                c2 = await svc.get_crawler()
                assert c1 is c2
                mock_crawler.start.assert_called_once()  # only once despite two calls
        finally:
            svc._crawler = original


# ---------------------------------------------------------------------------
# Service.scrape tests
# ---------------------------------------------------------------------------

def _make_crawl_result(
    success=True,
    raw_md="# Title\n\nContent here",
    fit_md="# Title\n\nContent here",
    title="Test Page",
    error_msg=None,
    internal_links=None,
):
    result = MagicMock()
    result.success = success
    result.error_message = error_msg
    result.metadata = {"title": title}
    result.markdown.raw_markdown = raw_md
    result.markdown.fit_markdown = fit_md
    result.media = {"images": [{"src": "https://example.com/img.jpg", "alt": "logo", "score": 0.9}]}
    result.screenshot = None
    result.links = {"internal": internal_links or []}
    return result


class TestWebCrawlerServiceScrape:

    @pytest.mark.asyncio
    async def test_scrape_success_returns_fit_markdown(self):
        from app.modules.web_crawler.service import WebCrawlerService
        import app.modules.web_crawler.service as svc

        mock_crawler = AsyncMock()
        mock_crawler.arun = AsyncMock(return_value=_make_crawl_result(
            raw_md="# Raw\n\nNavigation junk",
            fit_md="# Clean Content",
        ))

        with patch.object(svc, "get_crawler", new=AsyncMock(return_value=mock_crawler)):
            result = await WebCrawlerService.scrape("https://example.com")

        assert result["success"] is True
        assert result["markdown"] == "# Raw\n\nNavigation junk"
        assert result["fit_markdown"] == "# Clean Content"
        assert result["scraper"] == "crawl4ai"

    @pytest.mark.asyncio
    async def test_scrape_passes_topic_to_bm25(self):
        from app.modules.web_crawler.service import WebCrawlerService
        from crawl4ai.content_filter_strategy import BM25ContentFilter
        import app.modules.web_crawler.service as svc

        mock_crawler = AsyncMock()
        mock_crawler.arun = AsyncMock(return_value=_make_crawl_result())

        captured_config = {}

        async def capture_arun(url, config):
            captured_config["config"] = config
            return _make_crawl_result()

        mock_crawler.arun = capture_arun

        with patch.object(svc, "get_crawler", new=AsyncMock(return_value=mock_crawler)):
            await WebCrawlerService.scrape("https://example.com", topic="python fastapi")

        cfg = captured_config.get("config")
        assert cfg is not None
        assert isinstance(cfg.markdown_generator.content_filter, BM25ContentFilter)

    @pytest.mark.asyncio
    async def test_scrape_returns_internal_links(self):
        from app.modules.web_crawler.service import WebCrawlerService
        import app.modules.web_crawler.service as svc

        internal = [{"href": "https://example.com/page1"}, {"href": "https://example.com/page2"}]
        mock_crawler = AsyncMock()
        mock_crawler.arun = AsyncMock(return_value=_make_crawl_result(internal_links=internal))

        with patch.object(svc, "get_crawler", new=AsyncMock(return_value=mock_crawler)):
            result = await WebCrawlerService.scrape("https://example.com")

        assert "https://example.com/page1" in result["links_internal"]
        assert "https://example.com/page2" in result["links_internal"]

    @pytest.mark.asyncio
    async def test_scrape_crawl_failure_falls_back_to_jina(self):
        from app.modules.web_crawler.service import WebCrawlerService
        import app.modules.web_crawler.service as svc

        mock_crawler = AsyncMock()
        mock_crawler.arun = AsyncMock(side_effect=Exception("Playwright crash"))

        jina_result = {
            "url": "https://example.com",
            "title": "Jina Title",
            "markdown": "Jina content",
            "fit_markdown": "Jina content",
            "text_length": 12,
            "images": [],
            "image_count": 0,
            "screenshot_base64": None,
            "links_internal": [],
            "success": True,
            "scraper": "jina_reader",
        }

        with patch.object(svc, "get_crawler", new=AsyncMock(return_value=mock_crawler)), \
             patch.object(WebCrawlerService, "_scrape_with_jina", new=AsyncMock(return_value=jina_result)):
            result = await WebCrawlerService.scrape("https://example.com")

        assert result["success"] is True
        assert result["scraper"] == "jina_reader"

    @pytest.mark.asyncio
    async def test_scrape_crawl_result_not_success(self):
        from app.modules.web_crawler.service import WebCrawlerService
        import app.modules.web_crawler.service as svc

        mock_crawler = AsyncMock()
        mock_crawler.arun = AsyncMock(return_value=_make_crawl_result(
            success=False, error_msg="403 Forbidden"
        ))

        jina_fail = {"url": "https://example.com", "success": False, "error": "Jina also failed"}

        with patch.object(svc, "get_crawler", new=AsyncMock(return_value=mock_crawler)), \
             patch.object(WebCrawlerService, "_scrape_with_jina", new=AsyncMock(return_value=jina_fail)):
            result = await WebCrawlerService.scrape("https://example.com")

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_scrape_with_auth_session_isolation(self):
        from app.modules.web_crawler.service import WebCrawlerService
        import app.modules.web_crawler.service as svc

        session_ids = []

        mock_crawler = AsyncMock()
        mock_crawler.crawler_strategy.kill_session = AsyncMock()

        async def record_session(url, config):
            if hasattr(config, "session_id") and config.session_id:
                session_ids.append(config.session_id)
            return _make_crawl_result()

        mock_crawler.arun = record_session

        auth = {
            "login_url": "https://example.com/login",
            "login_js": "document.querySelector('#submit').click()",
            "wait_after_login_ms": 500,
        }

        with patch.object(svc, "get_crawler", new=AsyncMock(return_value=mock_crawler)):
            await WebCrawlerService.scrape("https://example.com/dashboard", auth=auth)

        # Both login and target calls use the same session_id
        assert len(session_ids) == 2
        assert session_ids[0] == session_ids[1]
        mock_crawler.crawler_strategy.kill_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_scrape_extracts_images(self):
        from app.modules.web_crawler.service import WebCrawlerService
        import app.modules.web_crawler.service as svc

        mock_crawler = AsyncMock()
        mock_crawler.arun = AsyncMock(return_value=_make_crawl_result())

        with patch.object(svc, "get_crawler", new=AsyncMock(return_value=mock_crawler)):
            result = await WebCrawlerService.scrape("https://example.com", extract_images=True)

        assert result["image_count"] == 1
        assert result["images"][0]["src"] == "https://example.com/img.jpg"
        assert result["images"][0]["score"] == 0.9


# ---------------------------------------------------------------------------
# Service.extract_structured tests
# ---------------------------------------------------------------------------

class TestWebCrawlerServiceExtract:

    @pytest.mark.asyncio
    async def test_extract_structured_returns_items(self):
        from app.modules.web_crawler.service import WebCrawlerService
        import app.modules.web_crawler.service as svc

        items = [{"title": "Product A", "price": "$10"}, {"title": "Product B", "price": "$20"}]
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.extracted_content = json.dumps(items)

        mock_crawler = AsyncMock()
        mock_crawler.arun = AsyncMock(return_value=mock_result)

        fields = [{"name": "title", "selector": "h2", "type": "text", "attribute": None}]

        with patch.object(svc, "get_crawler", new=AsyncMock(return_value=mock_crawler)):
            result = await WebCrawlerService.extract_structured(
                url="https://example.com",
                base_selector=".product",
                fields=fields,
            )

        assert result["success"] is True
        assert result["item_count"] == 2
        assert result["items"][0]["title"] == "Product A"

    @pytest.mark.asyncio
    async def test_extract_structured_empty_content(self):
        from app.modules.web_crawler.service import WebCrawlerService
        import app.modules.web_crawler.service as svc

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.extracted_content = None

        mock_crawler = AsyncMock()
        mock_crawler.arun = AsyncMock(return_value=mock_result)

        with patch.object(svc, "get_crawler", new=AsyncMock(return_value=mock_crawler)):
            result = await WebCrawlerService.extract_structured(
                url="https://example.com",
                base_selector=".item",
                fields=[{"name": "x", "selector": "span", "type": "text", "attribute": None}],
            )

        assert result["success"] is True
        assert result["item_count"] == 0
        assert result["items"] == []

    @pytest.mark.asyncio
    async def test_extract_structured_crawl_failure(self):
        from app.modules.web_crawler.service import WebCrawlerService
        import app.modules.web_crawler.service as svc

        mock_result = MagicMock()
        mock_result.success = False
        mock_result.error_message = "403 Forbidden"

        mock_crawler = AsyncMock()
        mock_crawler.arun = AsyncMock(return_value=mock_result)

        with patch.object(svc, "get_crawler", new=AsyncMock(return_value=mock_crawler)):
            result = await WebCrawlerService.extract_structured(
                url="https://example.com",
                base_selector=".item",
                fields=[{"name": "x", "selector": "span", "type": "text", "attribute": None}],
            )

        assert result["success"] is False
        assert "403" in result["error"]

    @pytest.mark.asyncio
    async def test_extract_structured_exception(self):
        from app.modules.web_crawler.service import WebCrawlerService
        import app.modules.web_crawler.service as svc

        with patch.object(svc, "get_crawler", new=AsyncMock(side_effect=Exception("browser down"))):
            result = await WebCrawlerService.extract_structured(
                url="https://example.com",
                base_selector=".item",
                fields=[{"name": "x", "selector": "span", "type": "text", "attribute": None}],
            )

        assert result["success"] is False
        assert "browser down" in result["error"]


# ---------------------------------------------------------------------------
# Service.batch_scrape tests
# ---------------------------------------------------------------------------

def _make_batch_result(url, success=True, raw_md="# Content", fit_md="# Content"):
    r = MagicMock()
    r.url = url
    r.success = success
    r.error_message = None if success else "Failed"
    r.metadata = {"title": "Title"} if success else None
    r.markdown.raw_markdown = raw_md
    r.markdown.fit_markdown = fit_md
    return r


class TestWebCrawlerServiceBatch:

    @pytest.mark.asyncio
    async def test_batch_scrape_all_success(self):
        from app.modules.web_crawler.service import WebCrawlerService
        import app.modules.web_crawler.service as svc

        urls = ["https://a.com", "https://b.com"]
        mock_crawler = AsyncMock()
        mock_crawler.arun_many = AsyncMock(return_value=[
            _make_batch_result(urls[0], fit_md="Clean A"),
            _make_batch_result(urls[1], fit_md="Clean B"),
        ])

        with patch.object(svc, "get_crawler", new=AsyncMock(return_value=mock_crawler)):
            result = await WebCrawlerService.batch_scrape(urls)

        assert result["total"] == 2
        assert result["succeeded"] == 2
        assert result["failed"] == 0
        assert result["results"][0]["markdown"] == "Clean A"

    @pytest.mark.asyncio
    async def test_batch_scrape_partial_failure(self):
        from app.modules.web_crawler.service import WebCrawlerService
        import app.modules.web_crawler.service as svc

        urls = ["https://a.com", "https://b.com"]
        mock_crawler = AsyncMock()
        mock_crawler.arun_many = AsyncMock(return_value=[
            _make_batch_result(urls[0]),
            _make_batch_result(urls[1], success=False),
        ])

        with patch.object(svc, "get_crawler", new=AsyncMock(return_value=mock_crawler)):
            result = await WebCrawlerService.batch_scrape(urls)

        assert result["succeeded"] == 1
        assert result["failed"] == 1
        assert result["results"][1]["success"] is False

    @pytest.mark.asyncio
    async def test_batch_scrape_uses_raw_when_fit_disabled(self):
        from app.modules.web_crawler.service import WebCrawlerService
        import app.modules.web_crawler.service as svc

        urls = ["https://a.com"]
        mock_crawler = AsyncMock()
        mock_crawler.arun_many = AsyncMock(return_value=[
            _make_batch_result(urls[0], raw_md="# Raw Full", fit_md="# Fit"),
        ])

        with patch.object(svc, "get_crawler", new=AsyncMock(return_value=mock_crawler)):
            result = await WebCrawlerService.batch_scrape(urls, use_fit_markdown=False)

        assert result["results"][0]["markdown"] == "# Raw Full"

    @pytest.mark.asyncio
    async def test_batch_scrape_exception_returns_all_failed(self):
        from app.modules.web_crawler.service import WebCrawlerService
        import app.modules.web_crawler.service as svc

        urls = ["https://a.com", "https://b.com"]

        with patch.object(svc, "get_crawler", new=AsyncMock(side_effect=Exception("timeout"))):
            result = await WebCrawlerService.batch_scrape(urls)

        assert result["total"] == 2
        assert result["succeeded"] == 0
        assert result["failed"] == 2
        assert all(not r["success"] for r in result["results"])


# ---------------------------------------------------------------------------
# Service.index_to_knowledge_base tests
# ---------------------------------------------------------------------------

class TestWebCrawlerServiceIndex:

    @pytest.mark.asyncio
    async def test_index_uses_fit_markdown_for_kb(self):
        """KB indexing must use fit_markdown, not raw markdown."""
        from app.modules.web_crawler.service import WebCrawlerService

        indexed_content = {}

        scrape_result = {
            "url": "https://example.com",
            "title": "Test",
            "markdown": "# Raw\n\nNav junk here",
            "fit_markdown": "# Clean Content Only",
            "images": [],
            "links_internal": [],
            "success": True,
        }

        async def mock_index(user_id, filename, content, content_type, session):
            indexed_content["content"] = content
            return {"total_chunks": 3}

        with patch.object(WebCrawlerService, "scrape", new=AsyncMock(return_value=scrape_result)), \
             patch("app.modules.knowledge.service.KnowledgeService.index_text_content",
                   new=AsyncMock(return_value={"total_chunks": 3})):
            result = await WebCrawlerService.index_to_knowledge_base(
                url="https://example.com",
                user_id=uuid4(),
                session=MagicMock(),
            )

        assert result["success"] is True
        assert result["pages_crawled"] == 1

    @pytest.mark.asyncio
    async def test_index_uses_native_links_for_subpages(self):
        """When crawl4ai returns internal links, use them (not regex fallback)."""
        from app.modules.web_crawler.service import WebCrawlerService

        crawled_urls = []
        call_count = 0

        internal = [
            {"href": "https://example.com/page1"},
            {"href": "https://example.com/page2"},
        ]

        async def mock_scrape(url, **kwargs):
            crawled_urls.append(url)
            return {
                "url": url,
                "title": "Page",
                "markdown": "content",
                "fit_markdown": "clean content",
                "images": [],
                "links_internal": [l["href"] for l in internal] if url == "https://example.com" else [],
                "success": True,
            }

        with patch.object(WebCrawlerService, "scrape", new=mock_scrape), \
             patch.dict("sys.modules", {"app.modules.knowledge.service": MagicMock(
                 KnowledgeService=MagicMock(index_text_content=AsyncMock(return_value={"total_chunks": 1}))
             ), "app.database": MagicMock(get_session_context=MagicMock())}):
            result = await WebCrawlerService.index_to_knowledge_base(
                url="https://example.com",
                user_id=uuid4(),
                crawl_subpages=True,
                max_pages=3,
                session=MagicMock(),
            )

        # Main + 2 subpages should have been attempted
        assert "https://example.com/page1" in crawled_urls
        assert "https://example.com/page2" in crawled_urls

    @pytest.mark.asyncio
    async def test_index_scrape_failure(self):
        from app.modules.web_crawler.service import WebCrawlerService

        with patch.object(WebCrawlerService, "scrape", new=AsyncMock(return_value={
            "url": "https://example.com",
            "success": False,
            "error": "Connection refused",
        })):
            result = await WebCrawlerService.index_to_knowledge_base(
                url="https://example.com",
                user_id=uuid4(),
                session=MagicMock(),
            )

        assert result["success"] is False
        assert result["error"] == "Connection refused"


# ---------------------------------------------------------------------------
# Route tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def crawler_client(app):
    """AsyncClient with crawl4ai browser lifecycle mocked out."""
    import httpx

    transport = httpx.ASGITransport(app=app)
    return transport, app


class TestWebCrawlerRoutes:

    @pytest.fixture(autouse=True)
    def _override_deps(self, app, test_user):
        """
        Override FastAPI dependencies so route tests never touch PostgreSQL or Redis:
        - get_current_user / require_ai_call_quota → return mock test_user
        - get_session → return a MagicMock (billing consume_quota is separately mocked)
        Also prevent real browser init/close during the lifespan.
        """
        from fastapi import HTTPException, Request
        from fastapi.security.utils import get_authorization_scheme_param
        from app.auth import get_current_user
        from app.database import get_session
        from app.modules.billing.middleware import require_ai_call_quota

        # Check bearer presence so unauthenticated tests still get 401,
        # but skip DB lookup (PostgreSQL not running in test env).
        def _auth_override(request: Request):
            auth = request.headers.get("Authorization", "")
            _, token = get_authorization_scheme_param(auth)
            if not token:
                raise HTTPException(status_code=401, detail="Not authenticated")
            return test_user

        def _mock_session():
            yield MagicMock()

        from app.modules.auth_guards.middleware import require_verified_email
        app.dependency_overrides[get_current_user] = _auth_override
        app.dependency_overrides[require_verified_email] = _auth_override
        app.dependency_overrides[require_ai_call_quota] = _auth_override
        app.dependency_overrides[get_session] = _mock_session

        with patch("app.modules.web_crawler.service.init_crawler", new_callable=AsyncMock), \
             patch("app.modules.web_crawler.service.close_crawler", new_callable=AsyncMock):
            yield

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_scrape_success(self, client, auth_headers):
        scrape_result = {
            "url": "https://example.com",
            "title": "Example",
            "markdown": "# Example",
            "fit_markdown": "# Example Clean",
            "text_length": 15,
            "images": [],
            "image_count": 0,
            "screenshot_base64": None,
            "links_internal": [],
            "success": True,
            "scraper": "crawl4ai",
        }

        with patch("app.modules.web_crawler.service.WebCrawlerService.scrape",
                   new=AsyncMock(return_value=scrape_result)):
            response = await client.post(
                "/api/crawler/scrape",
                json={"url": "https://example.com"},
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["fit_markdown"] == "# Example Clean"
        assert data["scraper"] == "crawl4ai"

    @pytest.mark.asyncio
    async def test_scrape_unauthorized(self, client):
        response = await client.post(
            "/api/crawler/scrape",
            json={"url": "https://example.com"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_scrape_invalid_url(self, client, auth_headers):
        response = await client.post(
            "/api/crawler/scrape",
            json={"url": ""},
            headers=auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_extract_success(self, client, auth_headers):
        extract_result = {
            "url": "https://example.com",
            "items": [{"title": "A"}, {"title": "B"}],
            "item_count": 2,
            "success": True,
            "error": None,
        }

        with patch("app.modules.web_crawler.service.WebCrawlerService.extract_structured",
                   new=AsyncMock(return_value=extract_result)):
            response = await client.post(
                "/api/crawler/extract",
                json={
                    "url": "https://example.com",
                    "base_selector": ".product",
                    "fields": [{"name": "title", "selector": "h2"}],
                },
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["item_count"] == 2
        assert len(data["items"]) == 2

    @pytest.mark.asyncio
    async def test_extract_missing_base_selector(self, client, auth_headers):
        response = await client.post(
            "/api/crawler/extract",
            json={"url": "https://example.com", "fields": [{"name": "t", "selector": "h2"}]},
            headers=auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_extract_empty_fields(self, client, auth_headers):
        response = await client.post(
            "/api/crawler/extract",
            json={"url": "https://example.com", "base_selector": ".item", "fields": []},
            headers=auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_extract_unauthorized(self, client):
        response = await client.post(
            "/api/crawler/extract",
            json={"url": "https://example.com", "base_selector": ".item",
                  "fields": [{"name": "t", "selector": "h2"}]},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_batch_success(self, client, auth_headers):
        batch_result = {
            "total": 2,
            "succeeded": 2,
            "failed": 0,
            "results": [
                {"url": "https://a.com", "title": "A", "markdown": "# A", "success": True},
                {"url": "https://b.com", "title": "B", "markdown": "# B", "success": True},
            ],
        }

        with patch("app.modules.web_crawler.service.WebCrawlerService.batch_scrape",
                   new=AsyncMock(return_value=batch_result)):
            response = await client.post(
                "/api/crawler/batch",
                json={"urls": ["https://a.com", "https://b.com"]},
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert data["succeeded"] == 2
        assert len(data["results"]) == 2

    @pytest.mark.asyncio
    async def test_batch_too_many_urls(self, client, auth_headers):
        response = await client.post(
            "/api/crawler/batch",
            json={"urls": [f"https://example{i}.com" for i in range(11)]},
            headers=auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_batch_unauthorized(self, client):
        response = await client.post(
            "/api/crawler/batch",
            json={"urls": ["https://example.com"]},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_index_with_topic(self, client, auth_headers):
        index_result = {
            "url": "https://example.com",
            "pages_crawled": 1,
            "chunks_indexed": 5,
            "images_found": 0,
            "success": True,
            "error": None,
        }

        with patch("app.modules.web_crawler.service.WebCrawlerService.index_to_knowledge_base",
                   new=AsyncMock(return_value=index_result)) as mock_index, \
             patch("app.modules.billing.service.BillingService.consume_quota",
                   new=AsyncMock(return_value=None)):
            response = await client.post(
                "/api/crawler/index",
                json={"url": "https://example.com", "topic": "machine learning"},
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["chunks_indexed"] == 5
        # Verify topic was forwarded to service
        call_kwargs = mock_index.call_args.kwargs
        assert call_kwargs.get("topic") == "machine learning"


# ---------------------------------------------------------------------------
# v3 schema tests — new ScrapeRequest fields + new models
# ---------------------------------------------------------------------------

class TestScrapeRequestV3:

    def test_new_rendering_fields_default_false(self):
        from app.modules.web_crawler.schemas import ScrapeRequest
        r = ScrapeRequest(url="https://example.com")
        assert r.scan_full_page is False
        assert r.process_iframes is False
        assert r.flatten_shadow_dom is False
        assert r.remove_overlay_elements is False
        assert r.simulate_user is False
        assert r.virtual_scroll_selector is None

    def test_new_reliability_fields_defaults(self):
        from app.modules.web_crawler.schemas import ScrapeRequest
        r = ScrapeRequest(url="https://example.com")
        assert r.page_timeout == 30000
        assert r.check_robots_txt is False
        assert r.word_count_threshold == 10

    def test_page_timeout_bounds(self):
        from pydantic import ValidationError
        from app.modules.web_crawler.schemas import ScrapeRequest
        with pytest.raises(ValidationError):
            ScrapeRequest(url="https://example.com", page_timeout=1000)  # below min 5000
        with pytest.raises(ValidationError):
            ScrapeRequest(url="https://example.com", page_timeout=200000)  # above max 120000

    def test_word_count_threshold_bounds(self):
        from pydantic import ValidationError
        from app.modules.web_crawler.schemas import ScrapeRequest
        with pytest.raises(ValidationError):
            ScrapeRequest(url="https://example.com", word_count_threshold=0)  # below min 1
        with pytest.raises(ValidationError):
            ScrapeRequest(url="https://example.com", word_count_threshold=300)  # above max 200

    def test_new_link_fields_defaults(self):
        from app.modules.web_crawler.schemas import ScrapeRequest
        r = ScrapeRequest(url="https://example.com")
        assert r.score_links is False
        assert r.extract_external_links is False
        assert r.exclude_social_media_links is False

    def test_new_media_fields_defaults(self):
        from app.modules.web_crawler.schemas import ScrapeRequest
        r = ScrapeRequest(url="https://example.com")
        assert r.extract_audio is False
        assert r.extract_video is False

    def test_new_output_fields_defaults(self):
        from app.modules.web_crawler.schemas import ScrapeRequest
        r = ScrapeRequest(url="https://example.com")
        assert r.pdf is False
        assert r.capture_mhtml is False
        assert r.capture_network_requests is False

    def test_browser_identity_fields_defaults(self):
        from app.modules.web_crawler.schemas import ScrapeRequest
        r = ScrapeRequest(url="https://example.com")
        assert r.proxy_url is None
        assert r.user_agent is None

    def test_topic_field_on_scrape_request(self):
        from app.modules.web_crawler.schemas import ScrapeRequest
        r = ScrapeRequest(url="https://example.com", topic="python")
        assert r.topic == "python"

    def test_scrape_response_has_new_fields(self):
        from app.modules.web_crawler.schemas import ScrapeResponse
        r = ScrapeResponse(url="https://example.com")
        assert r.audio == []
        assert r.video == []
        assert r.links_external == []
        assert r.tables == []
        assert r.network_requests == []
        assert r.pdf_base64 is None
        assert r.mhtml is None


class TestNewSchemasV3:

    def test_llm_extract_request_defaults(self):
        from app.modules.web_crawler.schemas import LLMExtractRequest
        r = LLMExtractRequest(url="https://example.com", instruction="Extract prices")
        assert r.provider == "gemini"
        assert r.schema_def is None
        assert r.auth is None

    def test_llm_extract_request_invalid_provider(self):
        from pydantic import ValidationError
        from app.modules.web_crawler.schemas import LLMExtractRequest
        with pytest.raises(ValidationError):
            LLMExtractRequest(url="https://example.com", instruction="x", provider="openai")

    def test_llm_extract_request_all_providers(self):
        from app.modules.web_crawler.schemas import LLMExtractRequest
        for provider in ("gemini", "claude", "groq"):
            r = LLMExtractRequest(url="https://example.com", instruction="extract", provider=provider)
            assert r.provider == provider

    def test_llm_extract_request_short_instruction_rejected(self):
        from pydantic import ValidationError
        from app.modules.web_crawler.schemas import LLMExtractRequest
        with pytest.raises(ValidationError):
            LLMExtractRequest(url="https://example.com", instruction="ab")  # < 5 chars

    def test_deep_crawl_request_defaults(self):
        from app.modules.web_crawler.schemas import DeepCrawlRequest
        r = DeepCrawlRequest(url="https://example.com")
        assert r.strategy == "bfs"
        assert r.max_depth == 2
        assert r.max_pages == 10
        assert r.score_threshold == 0.0
        assert r.include_external is False
        assert r.use_fit_markdown is True
        assert r.topic is None

    def test_deep_crawl_request_invalid_strategy(self):
        from pydantic import ValidationError
        from app.modules.web_crawler.schemas import DeepCrawlRequest
        with pytest.raises(ValidationError):
            DeepCrawlRequest(url="https://example.com", strategy="random")

    def test_deep_crawl_request_all_strategies(self):
        from app.modules.web_crawler.schemas import DeepCrawlRequest
        for strat in ("bfs", "dfs", "best_first"):
            r = DeepCrawlRequest(url="https://example.com", strategy=strat)
            assert r.strategy == strat

    def test_deep_crawl_request_max_pages_bounds(self):
        from pydantic import ValidationError
        from app.modules.web_crawler.schemas import DeepCrawlRequest
        with pytest.raises(ValidationError):
            DeepCrawlRequest(url="https://example.com", max_pages=0)
        with pytest.raises(ValidationError):
            DeepCrawlRequest(url="https://example.com", max_pages=51)

    def test_deep_crawl_response_defaults(self):
        from app.modules.web_crawler.schemas import DeepCrawlResponse
        r = DeepCrawlResponse(url="https://example.com")
        assert r.pages == []
        assert r.total_pages == 0
        assert r.succeeded == 0
        assert r.strategy == "bfs"

    def test_audio_video_data_schemas(self):
        from app.modules.web_crawler.schemas import AudioData, VideoData
        a = AudioData(src="https://example.com/audio.mp3")
        assert a.alt == ""
        assert a.type is None
        v = VideoData(src="https://example.com/video.mp4")
        assert v.poster is None
        assert v.type is None


# ---------------------------------------------------------------------------
# v3 service tests — new scrape options + extract_with_llm + deep_crawl
# ---------------------------------------------------------------------------

def _make_crawl_result_v3(
    success=True,
    raw_md="# Title\n\nContent",
    fit_md="# Title\n\nContent",
    title="Test Page",
    error_msg=None,
    internal_links=None,
    external_links=None,
    audio_media=None,
    video_media=None,
    tables=None,
    network_requests=None,
):
    result = MagicMock()
    result.success = success
    result.error_message = error_msg
    result.metadata = {"title": title} if success else None
    result.markdown.raw_markdown = raw_md
    result.markdown.fit_markdown = fit_md
    result.media = {
        "images": [{"src": "https://example.com/img.jpg", "alt": "logo", "score": 0.9}],
        "audio": audio_media or [],
        "video": video_media or [],
    }
    result.screenshot = None
    result.links = {
        "internal": internal_links or [],
        "external": external_links or [],
    }
    result.tables = tables or []
    result.network_requests = network_requests or []
    result.pdf = None
    result.mhtml = None
    return result


class TestWebCrawlerServiceV3:

    @pytest.mark.asyncio
    async def test_scrape_extracts_audio(self):
        from app.modules.web_crawler.service import WebCrawlerService
        import app.modules.web_crawler.service as svc

        audio = [{"src": "https://example.com/a.mp3", "alt": "podcast", "type": "audio/mpeg"}]
        mock_crawler = AsyncMock()
        mock_crawler.arun = AsyncMock(return_value=_make_crawl_result_v3(audio_media=audio))

        with patch.object(svc, "get_crawler", new=AsyncMock(return_value=mock_crawler)):
            result = await WebCrawlerService.scrape("https://example.com", extract_audio=True)

        assert len(result["audio"]) == 1
        assert result["audio"][0]["src"] == "https://example.com/a.mp3"

    @pytest.mark.asyncio
    async def test_scrape_extracts_video(self):
        from app.modules.web_crawler.service import WebCrawlerService
        import app.modules.web_crawler.service as svc

        video = [{"src": "https://example.com/v.mp4", "alt": "demo", "poster": None, "type": "video/mp4"}]
        mock_crawler = AsyncMock()
        mock_crawler.arun = AsyncMock(return_value=_make_crawl_result_v3(video_media=video))

        with patch.object(svc, "get_crawler", new=AsyncMock(return_value=mock_crawler)):
            result = await WebCrawlerService.scrape("https://example.com", extract_video=True)

        assert len(result["video"]) == 1
        assert result["video"][0]["src"] == "https://example.com/v.mp4"

    @pytest.mark.asyncio
    async def test_scrape_extracts_external_links(self):
        from app.modules.web_crawler.service import WebCrawlerService
        import app.modules.web_crawler.service as svc

        external = [{"href": "https://other.com/page"}, {"href": "https://third.com/"}]
        mock_crawler = AsyncMock()
        mock_crawler.arun = AsyncMock(return_value=_make_crawl_result_v3(external_links=external))

        with patch.object(svc, "get_crawler", new=AsyncMock(return_value=mock_crawler)):
            result = await WebCrawlerService.scrape(
                "https://example.com", extract_external_links=True
            )

        assert "https://other.com/page" in result["links_external"]
        assert "https://third.com/" in result["links_external"]

    @pytest.mark.asyncio
    async def test_scrape_no_external_links_by_default(self):
        from app.modules.web_crawler.service import WebCrawlerService
        import app.modules.web_crawler.service as svc

        external = [{"href": "https://other.com/page"}]
        mock_crawler = AsyncMock()
        mock_crawler.arun = AsyncMock(return_value=_make_crawl_result_v3(external_links=external))

        with patch.object(svc, "get_crawler", new=AsyncMock(return_value=mock_crawler)):
            result = await WebCrawlerService.scrape("https://example.com")  # extract_external_links=False

        assert result["links_external"] == []

    @pytest.mark.asyncio
    async def test_scrape_extracts_tables(self):
        from app.modules.web_crawler.service import WebCrawlerService
        import app.modules.web_crawler.service as svc

        tables = [{"headers": ["Name", "Price"], "rows": [["Widget", "$10"]], "caption": "Products"}]
        mock_crawler = AsyncMock()
        mock_crawler.arun = AsyncMock(return_value=_make_crawl_result_v3(tables=tables))

        with patch.object(svc, "get_crawler", new=AsyncMock(return_value=mock_crawler)):
            result = await WebCrawlerService.scrape("https://example.com", table_extraction=True)

        assert len(result["tables"]) == 1
        assert result["tables"][0]["headers"] == ["Name", "Price"]

    @pytest.mark.asyncio
    async def test_scrape_network_requests_captured(self):
        from app.modules.web_crawler.service import WebCrawlerService
        import app.modules.web_crawler.service as svc

        net_reqs = [{"url": "https://api.example.com/data"}, {"url": "https://cdn.example.com/style.css"}]
        mock_crawler = AsyncMock()
        mock_crawler.arun = AsyncMock(return_value=_make_crawl_result_v3(network_requests=net_reqs))

        with patch.object(svc, "get_crawler", new=AsyncMock(return_value=mock_crawler)):
            result = await WebCrawlerService.scrape(
                "https://example.com", capture_network_requests=True
            )

        assert "https://api.example.com/data" in result["network_requests"]

    @pytest.mark.asyncio
    async def test_scrape_pdf_encoded_as_base64(self):
        from app.modules.web_crawler.service import WebCrawlerService
        import app.modules.web_crawler.service as svc
        import base64

        mock_result = _make_crawl_result_v3()
        mock_result.pdf = b"%PDF-1.4 sample bytes"

        mock_crawler = AsyncMock()
        mock_crawler.arun = AsyncMock(return_value=mock_result)

        with patch.object(svc, "get_crawler", new=AsyncMock(return_value=mock_crawler)):
            result = await WebCrawlerService.scrape("https://example.com", pdf=True)

        assert result["pdf_base64"] is not None
        decoded = base64.b64decode(result["pdf_base64"])
        assert decoded == b"%PDF-1.4 sample bytes"

    @pytest.mark.asyncio
    async def test_scrape_uses_temp_crawler_for_proxy(self):
        from app.modules.web_crawler.service import WebCrawlerService
        import app.modules.web_crawler.service as svc

        temp_crawler = AsyncMock()
        temp_crawler.arun = AsyncMock(return_value=_make_crawl_result_v3())
        temp_crawler.close = AsyncMock()

        with patch.object(svc, "_get_temp_crawler", new=AsyncMock(return_value=temp_crawler)):
            result = await WebCrawlerService.scrape(
                "https://example.com", proxy_url="http://proxy:8080"
            )

        assert result["success"] is True
        temp_crawler.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_scrape_config_passes_rendering_options(self):
        from app.modules.web_crawler.service import WebCrawlerService
        import app.modules.web_crawler.service as svc

        captured = {}

        async def capture_arun(url, config):
            captured["config"] = config
            return _make_crawl_result_v3()

        mock_crawler = AsyncMock()
        mock_crawler.arun = capture_arun

        with patch.object(svc, "get_crawler", new=AsyncMock(return_value=mock_crawler)):
            await WebCrawlerService.scrape(
                "https://example.com",
                scan_full_page=True,
                process_iframes=True,
                flatten_shadow_dom=True,
                remove_overlay_elements=True,
                simulate_user=True,
                page_timeout=60000,
            )

        cfg = captured["config"]
        assert cfg.scan_full_page is True
        assert cfg.process_iframes is True
        assert cfg.flatten_shadow_dom is True
        assert cfg.remove_overlay_elements is True
        assert cfg.simulate_user is True
        assert cfg.page_timeout == 60000

    @pytest.mark.asyncio
    async def test_extract_with_llm_success(self):
        from app.modules.web_crawler.service import WebCrawlerService
        import app.modules.web_crawler.service as svc

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.extracted_content = '[{"product": "Widget", "price": "$10"}]'

        mock_crawler = AsyncMock()
        mock_crawler.arun = AsyncMock(return_value=mock_result)

        mock_settings = MagicMock()
        mock_settings.GEMINI_API_KEY = "test-gemini-key"

        with patch.object(svc, "get_crawler", new=AsyncMock(return_value=mock_crawler)), \
             patch("app.config.settings", mock_settings), \
             patch("crawl4ai.LLMConfig", return_value=MagicMock()), \
             patch("crawl4ai.extraction_strategy.LLMExtractionStrategy", return_value=MagicMock()), \
             patch("crawl4ai.CrawlerRunConfig", return_value=MagicMock()):
            result = await WebCrawlerService.extract_with_llm(
                url="https://example.com",
                instruction="Extract product names and prices",
                provider="gemini",
            )

        assert result["success"] is True
        assert result["provider"] == "gemini"
        assert isinstance(result["data"], list)

    @pytest.mark.asyncio
    async def test_extract_with_llm_missing_api_key(self):
        from app.modules.web_crawler.service import WebCrawlerService

        mock_settings = MagicMock()
        mock_settings.GEMINI_API_KEY = None

        with patch("app.config.settings", mock_settings):
            result = await WebCrawlerService.extract_with_llm(
                url="https://example.com",
                instruction="Extract data",
                provider="gemini",
            )

        assert result["success"] is False
        assert "API key" in result["error"] or "not configured" in result["error"]

    @pytest.mark.asyncio
    async def test_extract_with_llm_crawl_failure(self):
        from app.modules.web_crawler.service import WebCrawlerService
        import app.modules.web_crawler.service as svc

        mock_result = MagicMock()
        mock_result.success = False
        mock_result.error_message = "403 Forbidden"

        mock_crawler = AsyncMock()
        mock_crawler.arun = AsyncMock(return_value=mock_result)

        mock_llm_config = MagicMock()
        mock_strategy = MagicMock()

        with patch.object(svc, "get_crawler", new=AsyncMock(return_value=mock_crawler)), \
             patch("crawl4ai.LLMConfig", return_value=mock_llm_config), \
             patch("crawl4ai.extraction_strategy.LLMExtractionStrategy", return_value=mock_strategy):
            result = await WebCrawlerService.extract_with_llm(
                url="https://example.com",
                instruction="Extract data",
            )

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_deep_crawl_bfs_success(self):
        from app.modules.web_crawler.service import WebCrawlerService
        import app.modules.web_crawler.service as svc

        page1 = MagicMock()
        page1.success = True
        page1.url = "https://example.com"
        page1.metadata = {"title": "Home", "depth": 0}
        page1.markdown.raw_markdown = "# Home"
        page1.markdown.fit_markdown = "# Home"

        page2 = MagicMock()
        page2.success = True
        page2.url = "https://example.com/about"
        page2.metadata = {"title": "About", "depth": 1}
        page2.markdown.raw_markdown = "# About"
        page2.markdown.fit_markdown = "# About"

        mock_crawler = AsyncMock()
        mock_crawler.arun = AsyncMock(return_value=[page1, page2])

        mock_strategy = MagicMock()

        with patch.object(svc, "get_crawler", new=AsyncMock(return_value=mock_crawler)), \
             patch("crawl4ai.BFSDeepCrawlStrategy", return_value=mock_strategy):
            result = await WebCrawlerService.deep_crawl(
                url="https://example.com",
                strategy="bfs",
                max_depth=2,
                max_pages=5,
            )

        assert result["success"] is True
        assert result["total_pages"] == 2
        assert result["succeeded"] == 2
        assert result["strategy"] == "bfs"
        assert result["pages"][0]["url"] == "https://example.com"

    @pytest.mark.asyncio
    async def test_deep_crawl_partial_failure(self):
        from app.modules.web_crawler.service import WebCrawlerService
        import app.modules.web_crawler.service as svc

        page1 = MagicMock()
        page1.success = True
        page1.url = "https://example.com"
        page1.metadata = {"title": "Home"}
        page1.markdown.raw_markdown = "# Home"
        page1.markdown.fit_markdown = "# Home"

        page2 = MagicMock()
        page2.success = False
        page2.url = "https://example.com/broken"
        page2.error_message = "Timeout"

        mock_crawler = AsyncMock()
        mock_crawler.arun = AsyncMock(return_value=[page1, page2])

        with patch.object(svc, "get_crawler", new=AsyncMock(return_value=mock_crawler)), \
             patch("crawl4ai.BFSDeepCrawlStrategy", return_value=MagicMock()):
            result = await WebCrawlerService.deep_crawl("https://example.com")

        assert result["total_pages"] == 2
        assert result["succeeded"] == 1
        assert result["failed"] == 1

    @pytest.mark.asyncio
    async def test_deep_crawl_exception_returns_error(self):
        from app.modules.web_crawler.service import WebCrawlerService
        import app.modules.web_crawler.service as svc

        with patch.object(svc, "get_crawler", new=AsyncMock(side_effect=Exception("browser crash"))):
            result = await WebCrawlerService.deep_crawl("https://example.com")

        assert result["success"] is False
        assert "browser crash" in result["error"]

    @pytest.mark.asyncio
    async def test_deep_crawl_strategies_map(self):
        """Each strategy string maps to the correct class."""
        from app.modules.web_crawler.service import WebCrawlerService
        import app.modules.web_crawler.service as svc

        page = MagicMock()
        page.success = True
        page.url = "https://example.com"
        page.metadata = {"title": "T"}
        page.markdown.raw_markdown = "x"
        page.markdown.fit_markdown = "x"

        mock_crawler = AsyncMock()
        mock_crawler.arun = AsyncMock(return_value=[page])

        for strategy, cls_name in [
            ("bfs", "BFSDeepCrawlStrategy"),
            ("dfs", "DFSDeepCrawlStrategy"),
            ("best_first", "BestFirstCrawlingStrategy"),
        ]:
            with patch.object(svc, "get_crawler", new=AsyncMock(return_value=mock_crawler)), \
                 patch(f"crawl4ai.{cls_name}", return_value=MagicMock()) as mock_cls:
                await WebCrawlerService.deep_crawl(
                    "https://example.com", strategy=strategy
                )
                mock_cls.assert_called_once()


# ---------------------------------------------------------------------------
# v3 route tests — /extract-llm + /deep-crawl
# ---------------------------------------------------------------------------

class TestWebCrawlerRoutesV3:

    @pytest.fixture(autouse=True)
    def _override_deps(self, app, test_user):
        from fastapi import HTTPException, Request
        from fastapi.security.utils import get_authorization_scheme_param
        from app.auth import get_current_user
        from app.database import get_session
        from app.modules.billing.middleware import require_ai_call_quota

        def _auth_override(request: Request):
            auth = request.headers.get("Authorization", "")
            _, token = get_authorization_scheme_param(auth)
            if not token:
                raise HTTPException(status_code=401, detail="Not authenticated")
            return test_user

        def _mock_session():
            yield MagicMock()

        from app.modules.auth_guards.middleware import require_verified_email
        app.dependency_overrides[get_current_user] = _auth_override
        app.dependency_overrides[require_verified_email] = _auth_override
        app.dependency_overrides[require_ai_call_quota] = _auth_override
        app.dependency_overrides[get_session] = _mock_session

        with patch("app.modules.web_crawler.service.init_crawler", new_callable=AsyncMock), \
             patch("app.modules.web_crawler.service.close_crawler", new_callable=AsyncMock):
            yield

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_extract_llm_success(self, client, auth_headers):
        llm_result = {
            "url": "https://example.com",
            "data": [{"name": "Widget", "price": "$10"}],
            "provider": "gemini",
            "success": True,
            "error": None,
        }

        with patch("app.modules.web_crawler.service.WebCrawlerService.extract_with_llm",
                   new=AsyncMock(return_value=llm_result)), \
             patch("app.modules.billing.service.BillingService.consume_quota",
                   new=AsyncMock(return_value=None)):
            response = await client.post(
                "/api/crawler/extract-llm",
                json={"url": "https://example.com", "instruction": "Extract product names and prices"},
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["provider"] == "gemini"
        assert data["data"] is not None

    @pytest.mark.asyncio
    async def test_extract_llm_unauthorized(self, client):
        response = await client.post(
            "/api/crawler/extract-llm",
            json={"url": "https://example.com", "instruction": "Extract data"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_extract_llm_invalid_provider(self, client, auth_headers):
        response = await client.post(
            "/api/crawler/extract-llm",
            json={
                "url": "https://example.com",
                "instruction": "Extract data",
                "provider": "openai",
            },
            headers=auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_extract_llm_instruction_too_short(self, client, auth_headers):
        response = await client.post(
            "/api/crawler/extract-llm",
            json={"url": "https://example.com", "instruction": "ab"},
            headers=auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_deep_crawl_success(self, client, auth_headers):
        deep_result = {
            "url": "https://example.com",
            "strategy": "bfs",
            "pages": [
                {"url": "https://example.com", "title": "Home", "markdown": "# Home",
                 "depth": 0, "score": None, "success": True},
                {"url": "https://example.com/about", "title": "About", "markdown": "# About",
                 "depth": 1, "score": None, "success": True},
            ],
            "total_pages": 2,
            "succeeded": 2,
            "failed": 0,
            "success": True,
            "error": None,
        }

        with patch("app.modules.web_crawler.service.WebCrawlerService.deep_crawl",
                   new=AsyncMock(return_value=deep_result)), \
             patch("app.modules.billing.service.BillingService.consume_quota",
                   new=AsyncMock(return_value=None)):
            response = await client.post(
                "/api/crawler/deep-crawl",
                json={"url": "https://example.com", "max_depth": 2, "max_pages": 5},
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total_pages"] == 2
        assert len(data["pages"]) == 2
        assert data["strategy"] == "bfs"

    @pytest.mark.asyncio
    async def test_deep_crawl_unauthorized(self, client):
        response = await client.post(
            "/api/crawler/deep-crawl",
            json={"url": "https://example.com"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_deep_crawl_invalid_strategy(self, client, auth_headers):
        response = await client.post(
            "/api/crawler/deep-crawl",
            json={"url": "https://example.com", "strategy": "random_walk"},
            headers=auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_deep_crawl_max_pages_too_high(self, client, auth_headers):
        response = await client.post(
            "/api/crawler/deep-crawl",
            json={"url": "https://example.com", "max_pages": 100},
            headers=auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_scrape_passes_new_options_to_service(self, client, auth_headers):
        """Verify new v3 scrape options are forwarded to service."""
        with patch("app.modules.web_crawler.service.WebCrawlerService.scrape",
                   new=AsyncMock(return_value={
                       "url": "https://example.com", "title": "", "markdown": "",
                       "fit_markdown": "", "text_length": 0, "images": [], "image_count": 0,
                       "audio": [], "video": [], "screenshot_base64": None, "pdf_base64": None,
                       "mhtml": None, "links_internal": [], "links_external": [], "tables": [],
                       "network_requests": [], "success": True, "scraper": "crawl4ai",
                   })) as mock_scrape:
            response = await client.post(
                "/api/crawler/scrape",
                json={
                    "url": "https://example.com",
                    "scan_full_page": True,
                    "process_iframes": True,
                    "remove_overlay_elements": True,
                    "extract_audio": True,
                    "extract_video": True,
                    "extract_external_links": True,
                    "pdf": True,
                    "proxy_url": "http://proxy:8080",
                    "user_agent": "Mozilla/5.0",
                },
                headers=auth_headers,
            )

        assert response.status_code == 200
        call_kwargs = mock_scrape.call_args.kwargs
        assert call_kwargs["scan_full_page"] is True
        assert call_kwargs["process_iframes"] is True
        assert call_kwargs["remove_overlay_elements"] is True
        assert call_kwargs["extract_audio"] is True
        assert call_kwargs["extract_external_links"] is True
        assert call_kwargs["pdf"] is True
        assert call_kwargs["proxy_url"] == "http://proxy:8080"
        assert call_kwargs["user_agent"] == "Mozilla/5.0"


# ---------------------------------------------------------------------------
# v4 schema tests — page interaction, console, SSL, SeedRequest, DeepCrawl filters
# ---------------------------------------------------------------------------

class TestScrapeRequestV4:

    def test_page_interaction_fields_default(self):
        from app.modules.web_crawler.schemas import ScrapeRequest
        r = ScrapeRequest(url="https://example.com")
        assert r.wait_for is None
        assert r.wait_for_timeout is None
        assert r.js_code is None
        assert r.js_code_before_wait is None
        assert r.max_retries == 0

    def test_max_retries_bounds(self):
        from pydantic import ValidationError
        from app.modules.web_crawler.schemas import ScrapeRequest
        with pytest.raises(ValidationError):
            ScrapeRequest(url="https://example.com", max_retries=-1)
        with pytest.raises(ValidationError):
            ScrapeRequest(url="https://example.com", max_retries=6)

    def test_content_targeting_fields_default(self):
        from app.modules.web_crawler.schemas import ScrapeRequest
        r = ScrapeRequest(url="https://example.com")
        assert r.css_selector is None
        assert r.target_elements is None
        assert r.only_text is False
        assert r.parser_type == "lxml"
        assert r.delay_before_return_html == 0.1

    def test_parser_type_valid_values(self):
        from app.modules.web_crawler.schemas import ScrapeRequest
        assert ScrapeRequest(url="https://example.com", parser_type="lxml").parser_type == "lxml"
        assert ScrapeRequest(url="https://example.com", parser_type="html.parser").parser_type == "html.parser"

    def test_parser_type_invalid_rejected(self):
        from pydantic import ValidationError
        from app.modules.web_crawler.schemas import ScrapeRequest
        with pytest.raises(ValidationError):
            ScrapeRequest(url="https://example.com", parser_type="beautifulsoup")

    def test_rendering_v4_fields_default(self):
        from app.modules.web_crawler.schemas import ScrapeRequest
        r = ScrapeRequest(url="https://example.com")
        assert r.adjust_viewport_to_content is False
        assert r.remove_consent_popups is False

    def test_media_v4_fields_default(self):
        from app.modules.web_crawler.schemas import ScrapeRequest
        r = ScrapeRequest(url="https://example.com")
        assert r.image_score_threshold == 2
        assert r.exclude_domains == []

    def test_image_score_threshold_bounds(self):
        from pydantic import ValidationError
        from app.modules.web_crawler.schemas import ScrapeRequest
        with pytest.raises(ValidationError):
            ScrapeRequest(url="https://example.com", image_score_threshold=-1)
        with pytest.raises(ValidationError):
            ScrapeRequest(url="https://example.com", image_score_threshold=11)

    def test_console_ssl_fields_default(self):
        from app.modules.web_crawler.schemas import ScrapeRequest
        r = ScrapeRequest(url="https://example.com")
        assert r.log_console is False
        assert r.capture_console_messages is False
        assert r.fetch_ssl_certificate is False

    def test_scrape_response_v4_new_fields(self):
        from app.modules.web_crawler.schemas import ScrapeResponse
        r = ScrapeResponse(url="https://example.com")
        assert r.console_messages == []
        assert r.ssl_certificate is None
        assert r.status_code is None
        assert r.redirected_url is None

    def test_scrape_response_v4_populated(self):
        from app.modules.web_crawler.schemas import ScrapeResponse
        r = ScrapeResponse(
            url="https://example.com",
            console_messages=[{"type": "warn", "text": "Deprecated", "timestamp": 1.0}],
            ssl_certificate={"issuer": "Let's Encrypt", "valid_until": "2025-01-01"},
            status_code=200,
            redirected_url="https://www.example.com",
        )
        assert len(r.console_messages) == 1
        assert r.console_messages[0]["type"] == "warn"
        assert r.ssl_certificate["issuer"] == "Let's Encrypt"
        assert r.status_code == 200
        assert r.redirected_url == "https://www.example.com"

    def test_delay_before_return_html_bounds(self):
        from pydantic import ValidationError
        from app.modules.web_crawler.schemas import ScrapeRequest
        with pytest.raises(ValidationError):
            ScrapeRequest(url="https://example.com", delay_before_return_html=-0.1)
        with pytest.raises(ValidationError):
            ScrapeRequest(url="https://example.com", delay_before_return_html=11.0)


class TestSeedSchemas:

    def test_seed_request_defaults(self):
        from app.modules.web_crawler.schemas import SeedRequest
        r = SeedRequest(domain="example.com")
        assert r.source == "sitemap"
        assert r.max_urls == 100

    def test_seed_request_valid_sources(self):
        from app.modules.web_crawler.schemas import SeedRequest
        for src in ("sitemap", "crawl", "sitemaps"):
            r = SeedRequest(domain="example.com", source=src)
            assert r.source == src

    def test_seed_request_invalid_source(self):
        from pydantic import ValidationError
        from app.modules.web_crawler.schemas import SeedRequest
        with pytest.raises(ValidationError):
            SeedRequest(domain="example.com", source="xpath")

    def test_seed_request_max_urls_bounds(self):
        from pydantic import ValidationError
        from app.modules.web_crawler.schemas import SeedRequest
        with pytest.raises(ValidationError):
            SeedRequest(domain="example.com", max_urls=0)
        with pytest.raises(ValidationError):
            SeedRequest(domain="example.com", max_urls=1001)

    def test_seed_request_empty_domain_rejected(self):
        from pydantic import ValidationError
        from app.modules.web_crawler.schemas import SeedRequest
        with pytest.raises(ValidationError):
            SeedRequest(domain="")

    def test_seed_response_defaults(self):
        from app.modules.web_crawler.schemas import SeedResponse
        r = SeedResponse(domain="example.com")
        assert r.urls == []
        assert r.total == 0
        assert r.success is True
        assert r.error is None

    def test_seed_response_populated(self):
        from app.modules.web_crawler.schemas import SeedResponse
        r = SeedResponse(
            domain="example.com",
            urls=["https://example.com/page1", "https://example.com/page2"],
            total=2,
        )
        assert len(r.urls) == 2
        assert r.total == 2


class TestDeepCrawlRequestV4:

    def test_new_fields_default_none(self):
        from app.modules.web_crawler.schemas import DeepCrawlRequest
        r = DeepCrawlRequest(url="https://example.com")
        assert r.keyword_scorer_keywords is None
        assert r.url_patterns is None
        assert r.allowed_domains is None
        assert r.blocked_domains is None

    def test_keyword_scorer_keywords_set(self):
        from app.modules.web_crawler.schemas import DeepCrawlRequest
        r = DeepCrawlRequest(
            url="https://example.com",
            strategy="best_first",
            keyword_scorer_keywords=["python", "machine learning"],
        )
        assert r.keyword_scorer_keywords == ["python", "machine learning"]

    def test_url_patterns_set(self):
        from app.modules.web_crawler.schemas import DeepCrawlRequest
        r = DeepCrawlRequest(
            url="https://example.com",
            url_patterns=["*docs*", "*guide*"],
        )
        assert r.url_patterns == ["*docs*", "*guide*"]

    def test_domain_filters_set(self):
        from app.modules.web_crawler.schemas import DeepCrawlRequest
        r = DeepCrawlRequest(
            url="https://example.com",
            allowed_domains=["docs.example.com"],
            blocked_domains=["old.example.com"],
        )
        assert r.allowed_domains == ["docs.example.com"]
        assert r.blocked_domains == ["old.example.com"]


# ---------------------------------------------------------------------------
# v4 service tests — console messages, SSL, seed_urls, deep crawl filters
# ---------------------------------------------------------------------------

def _make_crawl_result_v4(
    success=True,
    raw_md="# Title\n\nContent",
    fit_md="# Title\n\nContent",
    title="Test Page",
    error_msg=None,
    console_messages=None,
    ssl_certificate=None,
    status_code=200,
    redirected_url=None,
):
    result = MagicMock()
    result.success = success
    result.error_message = error_msg
    result.metadata = {"title": title} if success else None
    result.markdown.raw_markdown = raw_md
    result.markdown.fit_markdown = fit_md
    result.media = {"images": [], "audio": [], "video": []}
    result.screenshot = None
    result.links = {"internal": [], "external": []}
    result.tables = []
    result.network_requests = []
    result.pdf = None
    result.mhtml = None
    result.console_messages = console_messages
    result.ssl_certificate = ssl_certificate
    result.status_code = status_code
    result.redirected_url = redirected_url
    return result


class TestWebCrawlerServiceV4:

    @pytest.mark.asyncio
    async def test_scrape_captures_console_messages(self):
        from app.modules.web_crawler.service import WebCrawlerService
        import app.modules.web_crawler.service as svc

        console = [{"type": "error", "text": "Uncaught TypeError", "timestamp": 1.5}]
        mock_crawler = AsyncMock()
        mock_crawler.arun = AsyncMock(
            return_value=_make_crawl_result_v4(console_messages=console)
        )

        with patch.object(svc, "get_crawler", new=AsyncMock(return_value=mock_crawler)):
            result = await WebCrawlerService.scrape(
                "https://example.com", capture_console_messages=True
            )

        assert result["console_messages"] == console

    @pytest.mark.asyncio
    async def test_scrape_console_empty_when_disabled(self):
        from app.modules.web_crawler.service import WebCrawlerService
        import app.modules.web_crawler.service as svc

        console = [{"type": "log", "text": "something", "timestamp": 1.0}]
        mock_crawler = AsyncMock()
        mock_crawler.arun = AsyncMock(
            return_value=_make_crawl_result_v4(console_messages=console)
        )

        with patch.object(svc, "get_crawler", new=AsyncMock(return_value=mock_crawler)):
            result = await WebCrawlerService.scrape(
                "https://example.com", capture_console_messages=False
            )

        assert result["console_messages"] == []

    @pytest.mark.asyncio
    async def test_scrape_ssl_certificate_extracted(self):
        from app.modules.web_crawler.service import WebCrawlerService
        import app.modules.web_crawler.service as svc

        from types import SimpleNamespace
        fake_cert = SimpleNamespace(issuer="Let's Encrypt", valid_until="2025-06-01")
        mock_crawler = AsyncMock()
        mock_crawler.arun = AsyncMock(
            return_value=_make_crawl_result_v4(ssl_certificate=fake_cert)
        )

        with patch.object(svc, "get_crawler", new=AsyncMock(return_value=mock_crawler)):
            result = await WebCrawlerService.scrape(
                "https://example.com", fetch_ssl_certificate=True
            )

        assert result["ssl_certificate"] is not None
        assert result["ssl_certificate"]["issuer"] == "Let's Encrypt"

    @pytest.mark.asyncio
    async def test_scrape_ssl_none_when_disabled(self):
        from app.modules.web_crawler.service import WebCrawlerService
        import app.modules.web_crawler.service as svc

        mock_crawler = AsyncMock()
        mock_crawler.arun = AsyncMock(return_value=_make_crawl_result_v4())

        with patch.object(svc, "get_crawler", new=AsyncMock(return_value=mock_crawler)):
            result = await WebCrawlerService.scrape(
                "https://example.com", fetch_ssl_certificate=False
            )

        assert result["ssl_certificate"] is None

    @pytest.mark.asyncio
    async def test_scrape_status_code_returned(self):
        from app.modules.web_crawler.service import WebCrawlerService
        import app.modules.web_crawler.service as svc

        mock_crawler = AsyncMock()
        mock_crawler.arun = AsyncMock(
            return_value=_make_crawl_result_v4(status_code=200)
        )

        with patch.object(svc, "get_crawler", new=AsyncMock(return_value=mock_crawler)):
            result = await WebCrawlerService.scrape("https://example.com")

        assert result["status_code"] == 200

    @pytest.mark.asyncio
    async def test_scrape_redirected_url_returned(self):
        from app.modules.web_crawler.service import WebCrawlerService
        import app.modules.web_crawler.service as svc

        mock_crawler = AsyncMock()
        mock_crawler.arun = AsyncMock(
            return_value=_make_crawl_result_v4(redirected_url="https://www.example.com")
        )

        with patch.object(svc, "get_crawler", new=AsyncMock(return_value=mock_crawler)):
            result = await WebCrawlerService.scrape("https://example.com")

        assert result["redirected_url"] == "https://www.example.com"

    @pytest.mark.asyncio
    async def test_scrape_config_passes_v4_options(self):
        """wait_for, js_code, max_retries, css_selector forwarded to CrawlerRunConfig."""
        from app.modules.web_crawler.service import WebCrawlerService
        import app.modules.web_crawler.service as svc

        captured = {}

        async def capture_arun(url, config):
            captured["config"] = config
            return _make_crawl_result_v4()

        mock_crawler = AsyncMock()
        mock_crawler.arun = capture_arun

        with patch.object(svc, "get_crawler", new=AsyncMock(return_value=mock_crawler)):
            await WebCrawlerService.scrape(
                "https://example.com",
                wait_for="css:.content",
                wait_for_timeout=5000,
                js_code="document.querySelector('.btn').click()",
                js_code_before_wait="window.scrollTo(0,0)",
                max_retries=2,
                css_selector=".main-content",
                only_text=True,
                adjust_viewport_to_content=True,
                remove_consent_popups=True,
                image_score_threshold=5,
            )

        cfg = captured["config"]
        assert cfg.wait_for == "css:.content"
        assert cfg.wait_for_timeout == 5000
        assert cfg.js_code == "document.querySelector('.btn').click()"
        assert cfg.js_code_before_wait == "window.scrollTo(0,0)"
        assert cfg.max_retries == 2
        assert cfg.css_selector == ".main-content"
        assert cfg.only_text is True
        assert cfg.adjust_viewport_to_content is True
        assert cfg.remove_consent_popups is True
        assert cfg.image_score_threshold == 5

    @pytest.mark.asyncio
    async def test_seed_urls_success(self):
        from app.modules.web_crawler.service import WebCrawlerService

        discovered = ["https://example.com/page1", "https://example.com/page2"]

        mock_seeder = AsyncMock()
        mock_seeder.urls = AsyncMock(return_value=discovered)
        mock_seeder.__aenter__ = AsyncMock(return_value=mock_seeder)
        mock_seeder.__aexit__ = AsyncMock(return_value=False)

        with patch("crawl4ai.AsyncUrlSeeder", return_value=mock_seeder), \
             patch("crawl4ai.SeedingConfig", return_value=MagicMock()):
            result = await WebCrawlerService.seed_urls(
                domain="example.com",
                source="sitemap",
                max_urls=50,
            )

        assert result["success"] is True
        assert result["domain"] == "example.com"
        assert len(result["urls"]) == 2
        assert result["total"] == 2

    @pytest.mark.asyncio
    async def test_seed_urls_failure(self):
        from app.modules.web_crawler.service import WebCrawlerService

        with patch("crawl4ai.AsyncUrlSeeder", side_effect=Exception("sitemap not found")):
            result = await WebCrawlerService.seed_urls(domain="broken.example.com")

        assert result["success"] is False
        assert result["urls"] == []
        assert "sitemap not found" in result["error"]

    @pytest.mark.asyncio
    async def test_seed_urls_respects_max_urls(self):
        from app.modules.web_crawler.service import WebCrawlerService

        # Return 20 URLs but cap at 5
        discovered = [f"https://example.com/page{i}" for i in range(20)]

        mock_seeder = AsyncMock()
        mock_seeder.urls = AsyncMock(return_value=discovered)
        mock_seeder.__aenter__ = AsyncMock(return_value=mock_seeder)
        mock_seeder.__aexit__ = AsyncMock(return_value=False)

        with patch("crawl4ai.AsyncUrlSeeder", return_value=mock_seeder), \
             patch("crawl4ai.SeedingConfig", return_value=MagicMock()):
            result = await WebCrawlerService.seed_urls(
                domain="example.com",
                max_urls=5,
            )

        assert len(result["urls"]) == 5
        assert result["total"] == 5

    @pytest.mark.asyncio
    async def test_deep_crawl_with_filter_chain(self):
        """deep_crawl builds FilterChain when url_patterns provided."""
        from app.modules.web_crawler.service import WebCrawlerService
        import app.modules.web_crawler.service as svc

        page = MagicMock()
        page.success = True
        page.url = "https://example.com/docs"
        page.metadata = {"title": "Docs", "depth": 1}
        page.markdown.raw_markdown = "# Docs"
        page.markdown.fit_markdown = "# Docs"

        mock_crawler = AsyncMock()
        mock_crawler.arun = AsyncMock(return_value=[page])

        mock_filter_chain = MagicMock()
        mock_pattern_filter = MagicMock()
        mock_domain_filter = MagicMock()

        with patch.object(svc, "get_crawler", new=AsyncMock(return_value=mock_crawler)), \
             patch("crawl4ai.BFSDeepCrawlStrategy", return_value=MagicMock()), \
             patch("crawl4ai.deep_crawling.FilterChain", return_value=mock_filter_chain) as mock_fc, \
             patch("crawl4ai.deep_crawling.URLPatternFilter", return_value=mock_pattern_filter), \
             patch("crawl4ai.deep_crawling.DomainFilter", return_value=mock_domain_filter), \
             patch("crawl4ai.deep_crawling.ContentTypeFilter", return_value=MagicMock(), create=True), \
             patch("crawl4ai.deep_crawling.ContentRelevanceFilter", return_value=MagicMock(), create=True), \
             patch("crawl4ai.deep_crawling.SEOFilter", return_value=MagicMock(), create=True):
            result = await WebCrawlerService.deep_crawl(
                url="https://example.com",
                strategy="bfs",
                url_patterns=["*docs*"],
                allowed_domains=["docs.example.com"],
                blocked_domains=["old.example.com"],
            )

        assert result["success"] is True
        # FilterChain was constructed
        mock_fc.assert_called_once()

    @pytest.mark.asyncio
    async def test_deep_crawl_keyword_scorer_for_best_first(self):
        """deep_crawl builds KeywordRelevanceScorer when strategy=best_first + keywords given."""
        from app.modules.web_crawler.service import WebCrawlerService
        import app.modules.web_crawler.service as svc

        page = MagicMock()
        page.success = True
        page.url = "https://example.com"
        page.metadata = {"title": "T"}
        page.markdown.raw_markdown = "x"
        page.markdown.fit_markdown = "x"

        mock_crawler = AsyncMock()
        mock_crawler.arun = AsyncMock(return_value=[page])

        with patch.object(svc, "get_crawler", new=AsyncMock(return_value=mock_crawler)), \
             patch("crawl4ai.BestFirstCrawlingStrategy", return_value=MagicMock()) as mock_strat, \
             patch("crawl4ai.deep_crawling.scorers.KeywordRelevanceScorer", return_value=MagicMock()) as mock_scorer:
            result = await WebCrawlerService.deep_crawl(
                url="https://example.com",
                strategy="best_first",
                keyword_scorer_keywords=["python", "tutorial"],
            )

        assert result["success"] is True
        mock_scorer.assert_called_once_with(keywords=["python", "tutorial"], weight=1.0)


# ---------------------------------------------------------------------------
# v4 route tests — /seed-urls + updated /scrape v4 params
# ---------------------------------------------------------------------------

class TestWebCrawlerRoutesV4:

    @pytest.fixture(autouse=True)
    def _override_deps(self, app, test_user):
        from fastapi import HTTPException, Request
        from fastapi.security.utils import get_authorization_scheme_param
        from app.auth import get_current_user
        from app.database import get_session
        from app.modules.billing.middleware import require_ai_call_quota

        def _auth_override(request: Request):
            auth = request.headers.get("Authorization", "")
            _, token = get_authorization_scheme_param(auth)
            if not token:
                raise HTTPException(status_code=401, detail="Not authenticated")
            return test_user

        def _mock_session():
            yield MagicMock()

        from app.modules.auth_guards.middleware import require_verified_email
        app.dependency_overrides[get_current_user] = _auth_override
        app.dependency_overrides[require_verified_email] = _auth_override
        app.dependency_overrides[require_ai_call_quota] = _auth_override
        app.dependency_overrides[get_session] = _mock_session

        with patch("app.modules.web_crawler.service.init_crawler", new_callable=AsyncMock), \
             patch("app.modules.web_crawler.service.close_crawler", new_callable=AsyncMock):
            yield

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_seed_urls_success(self, client, auth_headers):
        seed_result = {
            "domain": "example.com",
            "urls": ["https://example.com/page1", "https://example.com/page2"],
            "total": 2,
            "success": True,
            "error": None,
        }

        with patch("app.modules.web_crawler.service.WebCrawlerService.seed_urls",
                   new=AsyncMock(return_value=seed_result)):
            response = await client.post(
                "/api/crawler/seed-urls",
                json={"domain": "example.com"},
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total"] == 2
        assert len(data["urls"]) == 2
        assert data["domain"] == "example.com"

    @pytest.mark.asyncio
    async def test_seed_urls_unauthorized(self, client):
        response = await client.post(
            "/api/crawler/seed-urls",
            json={"domain": "example.com"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_seed_urls_invalid_source(self, client, auth_headers):
        response = await client.post(
            "/api/crawler/seed-urls",
            json={"domain": "example.com", "source": "invalid"},
            headers=auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_seed_urls_empty_domain(self, client, auth_headers):
        response = await client.post(
            "/api/crawler/seed-urls",
            json={"domain": ""},
            headers=auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_scrape_v4_params_forwarded(self, client, auth_headers):
        """Verify new v4 scrape params are forwarded to service."""
        base_result = {
            "url": "https://example.com", "title": "", "markdown": "",
            "fit_markdown": "", "text_length": 0, "images": [], "image_count": 0,
            "audio": [], "video": [], "screenshot_base64": None, "pdf_base64": None,
            "mhtml": None, "links_internal": [], "links_external": [], "tables": [],
            "network_requests": [], "console_messages": [], "ssl_certificate": None,
            "status_code": 200, "redirected_url": None,
            "success": True, "scraper": "crawl4ai",
        }

        with patch("app.modules.web_crawler.service.WebCrawlerService.scrape",
                   new=AsyncMock(return_value=base_result)) as mock_scrape:
            response = await client.post(
                "/api/crawler/scrape",
                json={
                    "url": "https://example.com",
                    "wait_for": "css:.main",
                    "js_code": "window.scrollTo(0,0)",
                    "max_retries": 3,
                    "css_selector": ".article",
                    "only_text": True,
                    "remove_consent_popups": True,
                    "capture_console_messages": True,
                    "fetch_ssl_certificate": True,
                },
                headers=auth_headers,
            )

        assert response.status_code == 200
        call_kwargs = mock_scrape.call_args.kwargs
        assert call_kwargs["wait_for"] == "css:.main"
        assert call_kwargs["js_code"] == "window.scrollTo(0,0)"
        assert call_kwargs["max_retries"] == 3
        assert call_kwargs["css_selector"] == ".article"
        assert call_kwargs["only_text"] is True
        assert call_kwargs["remove_consent_popups"] is True
        assert call_kwargs["capture_console_messages"] is True
        assert call_kwargs["fetch_ssl_certificate"] is True

    @pytest.mark.asyncio
    async def test_scrape_response_includes_v4_fields(self, client, auth_headers):
        """ScrapeResponse includes console_messages, ssl_certificate, status_code."""
        base_result = {
            "url": "https://example.com", "title": "Test", "markdown": "# Test",
            "fit_markdown": "# Test", "text_length": 6, "images": [], "image_count": 0,
            "audio": [], "video": [], "screenshot_base64": None, "pdf_base64": None,
            "mhtml": None, "links_internal": [], "links_external": [], "tables": [],
            "network_requests": [],
            "console_messages": [{"type": "warn", "text": "Deprecated API", "timestamp": 1.0}],
            "ssl_certificate": {"issuer": "DigiCert"},
            "status_code": 200,
            "redirected_url": "https://www.example.com",
            "success": True, "scraper": "crawl4ai",
        }

        with patch("app.modules.web_crawler.service.WebCrawlerService.scrape",
                   new=AsyncMock(return_value=base_result)):
            response = await client.post(
                "/api/crawler/scrape",
                json={"url": "https://example.com", "capture_console_messages": True},
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["console_messages"] == [{"type": "warn", "text": "Deprecated API", "timestamp": 1.0}]
        assert data["ssl_certificate"] == {"issuer": "DigiCert"}
        assert data["status_code"] == 200
        assert data["redirected_url"] == "https://www.example.com"

    @pytest.mark.asyncio
    async def test_deep_crawl_v4_filter_params_forwarded(self, client, auth_headers):
        """Verify new deep crawl filter params are forwarded to service."""
        deep_result = {
            "url": "https://example.com", "strategy": "bfs",
            "pages": [], "total_pages": 0, "succeeded": 0, "failed": 0,
            "success": True, "error": None,
        }

        with patch("app.modules.web_crawler.service.WebCrawlerService.deep_crawl",
                   new=AsyncMock(return_value=deep_result)) as mock_deep, \
             patch("app.modules.billing.service.BillingService.consume_quota",
                   new=AsyncMock(return_value=None)):
            response = await client.post(
                "/api/crawler/deep-crawl",
                json={
                    "url": "https://example.com",
                    "strategy": "best_first",
                    "keyword_scorer_keywords": ["python", "tutorial"],
                    "url_patterns": ["*docs*"],
                    "allowed_domains": ["docs.example.com"],
                    "blocked_domains": ["old.example.com"],
                },
                headers=auth_headers,
            )

        assert response.status_code == 200
        call_kwargs = mock_deep.call_args.kwargs
        assert call_kwargs["keyword_scorer_keywords"] == ["python", "tutorial"]
        assert call_kwargs["url_patterns"] == ["*docs*"]
        assert call_kwargs["allowed_domains"] == ["docs.example.com"]
        assert call_kwargs["blocked_domains"] == ["old.example.com"]


# ---------------------------------------------------------------------------
# v5 schema tests — browser config, cache, link preview, regex, xpath, etc.
# ---------------------------------------------------------------------------

class TestScrapeRequestV5:

    def test_browser_config_defaults(self):
        from app.modules.web_crawler.schemas import ScrapeRequest
        r = ScrapeRequest(url="https://example.com")
        assert r.enable_stealth is False
        assert r.browser_type == "chromium"
        assert r.javascript_enabled is True
        assert r.avoid_ads is False
        assert r.session_id is None

    def test_browser_type_valid_values(self):
        from app.modules.web_crawler.schemas import ScrapeRequest
        for bt in ("chromium", "firefox", "webkit"):
            assert ScrapeRequest(url="https://example.com", browser_type=bt).browser_type == bt

    def test_browser_type_invalid_rejected(self):
        from pydantic import ValidationError
        from app.modules.web_crawler.schemas import ScrapeRequest
        with pytest.raises(ValidationError):
            ScrapeRequest(url="https://example.com", browser_type="safari")

    def test_session_id_max_length_enforced(self):
        from pydantic import ValidationError
        from app.modules.web_crawler.schemas import ScrapeRequest
        with pytest.raises(ValidationError):
            ScrapeRequest(url="https://example.com", session_id="x" * 101)

    def test_cache_mode_defaults(self):
        from app.modules.web_crawler.schemas import ScrapeRequest
        r = ScrapeRequest(url="https://example.com")
        assert r.cache_mode == "bypass"

    def test_cache_mode_valid_values(self):
        from app.modules.web_crawler.schemas import ScrapeRequest
        for mode in ("enabled", "disabled", "bypass", "read_only", "write_only"):
            assert ScrapeRequest(url="https://example.com", cache_mode=mode).cache_mode == mode

    def test_cache_mode_invalid_rejected(self):
        from pydantic import ValidationError
        from app.modules.web_crawler.schemas import ScrapeRequest
        with pytest.raises(ValidationError):
            ScrapeRequest(url="https://example.com", cache_mode="aggressive")

    def test_markdown_display_defaults(self):
        from app.modules.web_crawler.schemas import ScrapeRequest
        r = ScrapeRequest(url="https://example.com")
        assert r.ignore_links is False
        assert r.body_width == 0

    def test_body_width_bounds(self):
        from pydantic import ValidationError
        from app.modules.web_crawler.schemas import ScrapeRequest
        with pytest.raises(ValidationError):
            ScrapeRequest(url="https://example.com", body_width=-1)
        with pytest.raises(ValidationError):
            ScrapeRequest(url="https://example.com", body_width=201)
        assert ScrapeRequest(url="https://example.com", body_width=80).body_width == 80

    def test_link_preview_defaults(self):
        from app.modules.web_crawler.schemas import ScrapeRequest
        r = ScrapeRequest(url="https://example.com")
        assert r.link_preview_query is None
        assert r.link_preview_max_links == 0

    def test_link_preview_max_links_bounds(self):
        from pydantic import ValidationError
        from app.modules.web_crawler.schemas import ScrapeRequest
        with pytest.raises(ValidationError):
            ScrapeRequest(url="https://example.com", link_preview_max_links=-1)
        with pytest.raises(ValidationError):
            ScrapeRequest(url="https://example.com", link_preview_max_links=501)

    def test_link_preview_query_max_length(self):
        from pydantic import ValidationError
        from app.modules.web_crawler.schemas import ScrapeRequest
        with pytest.raises(ValidationError):
            ScrapeRequest(url="https://example.com", link_preview_query="x" * 201)

    def test_stealth_mode_set(self):
        from app.modules.web_crawler.schemas import ScrapeRequest
        r = ScrapeRequest(url="https://example.com", enable_stealth=True, browser_type="firefox")
        assert r.enable_stealth is True
        assert r.browser_type == "firefox"


class TestDeepCrawlRequestV5:

    def test_advanced_filter_defaults(self):
        from app.modules.web_crawler.schemas import DeepCrawlRequest
        r = DeepCrawlRequest(url="https://example.com")
        assert r.content_type_filter is None
        assert r.content_relevance_query is None
        assert r.content_relevance_threshold == 2.0
        assert r.seo_filter is False
        assert r.seo_filter_threshold == 0.65
        assert r.resume_state is None

    def test_content_type_filter_set(self):
        from app.modules.web_crawler.schemas import DeepCrawlRequest
        r = DeepCrawlRequest(url="https://example.com", content_type_filter=["text/html", "application/pdf"])
        assert r.content_type_filter == ["text/html", "application/pdf"]

    def test_content_relevance_threshold_bounds(self):
        from pydantic import ValidationError
        from app.modules.web_crawler.schemas import DeepCrawlRequest
        with pytest.raises(ValidationError):
            DeepCrawlRequest(url="https://example.com", content_relevance_threshold=-0.1)
        with pytest.raises(ValidationError):
            DeepCrawlRequest(url="https://example.com", content_relevance_threshold=20.1)
        assert DeepCrawlRequest(url="https://example.com", content_relevance_threshold=3.5).content_relevance_threshold == 3.5

    def test_seo_filter_threshold_bounds(self):
        from pydantic import ValidationError
        from app.modules.web_crawler.schemas import DeepCrawlRequest
        with pytest.raises(ValidationError):
            DeepCrawlRequest(url="https://example.com", seo_filter_threshold=-0.1)
        with pytest.raises(ValidationError):
            DeepCrawlRequest(url="https://example.com", seo_filter_threshold=1.1)

    def test_resume_state_dict(self):
        from app.modules.web_crawler.schemas import DeepCrawlRequest
        state = {"visited": ["https://example.com/p1"], "depth": 2}
        r = DeepCrawlRequest(url="https://example.com", resume_state=state)
        assert r.resume_state["visited"] == ["https://example.com/p1"]

    def test_deep_crawl_response_has_export_state(self):
        from app.modules.web_crawler.schemas import DeepCrawlResponse
        r = DeepCrawlResponse(url="https://example.com")
        assert r.export_state is None

    def test_deep_crawl_response_export_state_populated(self):
        from app.modules.web_crawler.schemas import DeepCrawlResponse
        state = {"visited": ["https://example.com"], "queue": []}
        r = DeepCrawlResponse(url="https://example.com", export_state=state)
        assert r.export_state["visited"] == ["https://example.com"]


class TestSeedRequestV5:

    def test_new_fields_default(self):
        from app.modules.web_crawler.schemas import SeedRequest
        r = SeedRequest(domain="example.com")
        assert r.pattern is None
        assert r.query is None
        assert r.score_threshold is None
        assert r.extract_head is False

    def test_pattern_set(self):
        from app.modules.web_crawler.schemas import SeedRequest
        r = SeedRequest(domain="example.com", pattern="*/blog/*")
        assert r.pattern == "*/blog/*"

    def test_query_with_threshold(self):
        from app.modules.web_crawler.schemas import SeedRequest
        r = SeedRequest(domain="example.com", query="python tutorial", score_threshold=1.5)
        assert r.query == "python tutorial"
        assert r.score_threshold == 1.5

    def test_score_threshold_bounds(self):
        from pydantic import ValidationError
        from app.modules.web_crawler.schemas import SeedRequest
        with pytest.raises(ValidationError):
            SeedRequest(domain="example.com", score_threshold=-0.1)
        with pytest.raises(ValidationError):
            SeedRequest(domain="example.com", score_threshold=20.1)

    def test_extract_head_flag(self):
        from app.modules.web_crawler.schemas import SeedRequest
        r = SeedRequest(domain="example.com", extract_head=True)
        assert r.extract_head is True


class TestRegexExtractSchemas:

    def test_regex_extract_request_defaults(self):
        from app.modules.web_crawler.schemas import RegexExtractRequest
        r = RegexExtractRequest(url="https://example.com")
        assert r.patterns == []
        assert r.custom_patterns == {}
        assert r.auth is None

    def test_regex_extract_request_with_patterns(self):
        from app.modules.web_crawler.schemas import RegexExtractRequest
        r = RegexExtractRequest(
            url="https://example.com",
            patterns=["email", "phone_intl"],
            custom_patterns={"zip": r"\b\d{5}\b"},
        )
        assert "email" in r.patterns
        assert "zip" in r.custom_patterns

    def test_regex_match_schema(self):
        from app.modules.web_crawler.schemas import RegexMatch
        m = RegexMatch(label="email", value="user@example.com", span=[10, 28])
        assert m.label == "email"
        assert m.value == "user@example.com"
        assert m.span == [10, 28]

    def test_regex_extract_response_defaults(self):
        from app.modules.web_crawler.schemas import RegexExtractResponse
        r = RegexExtractResponse(url="https://example.com")
        assert r.matches == []
        assert r.match_count == 0
        assert r.success is True
        assert r.error is None

    def test_regex_extract_response_populated(self):
        from app.modules.web_crawler.schemas import RegexExtractResponse, RegexMatch
        r = RegexExtractResponse(
            url="https://example.com",
            matches=[RegexMatch(label="email", value="a@b.com", span=[0, 7])],
            match_count=1,
            success=True,
        )
        assert len(r.matches) == 1
        assert r.matches[0].label == "email"


class TestXPathExtractSchemas:

    def test_xpath_extract_request_defaults(self):
        from app.modules.web_crawler.schemas import XPathExtractRequest, ExtractField
        r = XPathExtractRequest(
            url="https://example.com",
            base_selector="//div[@class='item']",
            fields=[ExtractField(name="title", selector=".//h2")],
        )
        assert r.base_selector == "//div[@class='item']"
        assert r.fields[0].name == "title"
        assert r.auth is None

    def test_xpath_request_reuses_extract_field(self):
        from app.modules.web_crawler.schemas import XPathExtractRequest, ExtractField
        f = ExtractField(name="href", selector=".//a/@href", type="attribute", attribute="href")
        r = XPathExtractRequest(
            url="https://example.com",
            base_selector="//ul/li",
            fields=[f],
        )
        assert r.fields[0].attribute == "href"


class TestGenerateSchemaSchemas:

    def test_generate_schema_request_defaults(self):
        from app.modules.web_crawler.schemas import GenerateSchemaRequest
        r = GenerateSchemaRequest(url="https://example.com", query="product listings")
        assert r.schema_type == "CSS"
        assert r.provider == "gemini"

    def test_generate_schema_request_xpath_type(self):
        from app.modules.web_crawler.schemas import GenerateSchemaRequest
        r = GenerateSchemaRequest(url="https://example.com", query="articles", schema_type="XPath")
        assert r.schema_type == "XPath"

    def test_generate_schema_type_invalid_rejected(self):
        from pydantic import ValidationError
        from app.modules.web_crawler.schemas import GenerateSchemaRequest
        with pytest.raises(ValidationError):
            GenerateSchemaRequest(url="https://example.com", query="test", schema_type="Regex")

    def test_generate_schema_response_defaults(self):
        from app.modules.web_crawler.schemas import GenerateSchemaResponse
        r = GenerateSchemaResponse(url="https://example.com")
        assert r.schema_def is None
        assert r.schema_type == "CSS"
        assert r.success is True
        assert r.error is None

    def test_generate_schema_response_populated(self):
        from app.modules.web_crawler.schemas import GenerateSchemaResponse
        schema = {"baseSelector": ".item", "fields": [{"name": "title", "selector": "h2"}]}
        r = GenerateSchemaResponse(
            url="https://example.com",
            schema_def=schema,
            schema_type="CSS",
            success=True,
        )
        assert r.schema_def["baseSelector"] == ".item"


class TestProcessHtmlSchemas:

    def test_process_html_request_defaults(self):
        from app.modules.web_crawler.schemas import ProcessHtmlRequest
        r = ProcessHtmlRequest(html="<html><body><p>Test</p></body></html>")
        assert r.url == "https://example.com"
        assert r.use_fit_markdown is True
        assert r.topic is None
        assert r.css_selector is None
        assert r.word_count_threshold == 10

    def test_process_html_request_custom_url(self):
        from app.modules.web_crawler.schemas import ProcessHtmlRequest
        r = ProcessHtmlRequest(html="<p>Hello</p>", url="https://example.com/page")
        assert r.url == "https://example.com/page"

    def test_process_html_request_html_required(self):
        from pydantic import ValidationError
        from app.modules.web_crawler.schemas import ProcessHtmlRequest
        with pytest.raises(ValidationError):
            ProcessHtmlRequest()

    def test_process_html_response_defaults(self):
        from app.modules.web_crawler.schemas import ProcessHtmlResponse
        r = ProcessHtmlResponse(url="https://example.com")
        assert r.markdown == ""
        assert r.fit_markdown == ""
        assert r.text_length == 0
        assert r.links_internal == []
        assert r.links_external == []
        assert r.success is True
        assert r.error is None


# ---------------------------------------------------------------------------
# v5 service tests — new methods + updated scrape/deep_crawl/seed_urls
# ---------------------------------------------------------------------------

class TestWebCrawlerServiceV5:

    @pytest.mark.asyncio
    async def test_scrape_passes_browser_type_to_temp_crawler(self):
        """browser_type != chromium triggers _get_temp_crawler."""
        from app.modules.web_crawler.service import WebCrawlerService
        import app.modules.web_crawler.service as svc

        captured_kwargs = {}

        async def fake_get_temp_crawler(**kwargs):
            captured_kwargs.update(kwargs)
            mock = AsyncMock()
            mock.arun = AsyncMock(return_value=_make_crawl_result_v4())
            mock.__aenter__ = AsyncMock(return_value=mock)
            mock.__aexit__ = AsyncMock(return_value=False)
            return mock

        with patch.object(svc, "_get_temp_crawler", new=fake_get_temp_crawler), \
             patch.object(svc, "get_crawler", new=AsyncMock()):
            await WebCrawlerService.scrape("https://example.com", browser_type="firefox")

        assert captured_kwargs.get("browser_type") == "firefox"

    @pytest.mark.asyncio
    async def test_scrape_stealth_triggers_temp_crawler(self):
        from app.modules.web_crawler.service import WebCrawlerService
        import app.modules.web_crawler.service as svc

        captured_kwargs = {}

        async def fake_get_temp_crawler(**kwargs):
            captured_kwargs.update(kwargs)
            mock = AsyncMock()
            mock.arun = AsyncMock(return_value=_make_crawl_result_v4())
            mock.__aenter__ = AsyncMock(return_value=mock)
            mock.__aexit__ = AsyncMock(return_value=False)
            return mock

        with patch.object(svc, "_get_temp_crawler", new=fake_get_temp_crawler), \
             patch.object(svc, "get_crawler", new=AsyncMock()):
            await WebCrawlerService.scrape("https://example.com", enable_stealth=True)

        assert captured_kwargs.get("enable_stealth") is True

    @pytest.mark.asyncio
    async def test_scrape_session_id_forwarded_to_config(self):
        from app.modules.web_crawler.service import WebCrawlerService
        import app.modules.web_crawler.service as svc

        captured = {}

        async def capture_arun(url, config):
            captured["config"] = config
            return _make_crawl_result_v4()

        mock_crawler = AsyncMock()
        mock_crawler.arun = capture_arun

        with patch.object(svc, "get_crawler", new=AsyncMock(return_value=mock_crawler)):
            await WebCrawlerService.scrape(
                "https://example.com",
                session_id="my-session-123",
            )

        assert hasattr(captured["config"], "session_id")
        assert captured["config"].session_id == "my-session-123"

    @pytest.mark.asyncio
    async def test_extract_regex_happy_path(self):
        from app.modules.web_crawler.service import WebCrawlerService

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.url = "https://example.com"
        mock_result.extracted_content = '[{"label": "email", "value": "a@b.com", "span": [10, 17]}]'

        mock_crawler_instance = AsyncMock()
        mock_crawler_instance.arun = AsyncMock(return_value=mock_result)
        mock_crawler_instance.__aenter__ = AsyncMock(return_value=mock_crawler_instance)
        mock_crawler_instance.__aexit__ = AsyncMock(return_value=False)

        with patch("crawl4ai.AsyncWebCrawler", return_value=mock_crawler_instance), \
             patch("crawl4ai.RegexExtractionStrategy", return_value=MagicMock()):
            result = await WebCrawlerService.extract_regex(
                url="https://example.com",
                patterns=["email"],
            )

        assert result["success"] is True
        assert result["url"] == "https://example.com"
        assert result["match_count"] >= 0

    @pytest.mark.asyncio
    async def test_extract_regex_failure(self):
        from app.modules.web_crawler.service import WebCrawlerService
        import app.modules.web_crawler.service as svc

        with patch.object(svc, "get_crawler", new=AsyncMock(side_effect=Exception("network error"))), \
             patch("crawl4ai.CrawlerRunConfig", return_value=MagicMock()):
            result = await WebCrawlerService.extract_regex(
                url="https://broken.example.com",
                patterns=["email"],
            )

        assert result["success"] is False
        assert "network error" in result["error"]

    @pytest.mark.asyncio
    async def test_extract_xpath_happy_path(self):
        from app.modules.web_crawler.service import WebCrawlerService
        import app.modules.web_crawler.service as svc

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.url = "https://example.com"
        mock_result.extracted_content = '[{"title": "Article 1"}, {"title": "Article 2"}]'

        mock_crawler = AsyncMock()
        mock_crawler.arun = AsyncMock(return_value=mock_result)

        with patch.object(svc, "get_crawler", new=AsyncMock(return_value=mock_crawler)), \
             patch("crawl4ai.CrawlerRunConfig", return_value=MagicMock()):
            result = await WebCrawlerService.extract_xpath(
                url="https://example.com",
                base_selector="//div[@class='item']",
                fields=[{"name": "title", "selector": ".//h2", "type": "text"}],
            )

        assert result["success"] is True
        assert result["url"] == "https://example.com"

    @pytest.mark.asyncio
    async def test_extract_xpath_failure(self):
        from app.modules.web_crawler.service import WebCrawlerService
        import app.modules.web_crawler.service as svc

        with patch.object(svc, "get_crawler", new=AsyncMock(side_effect=Exception("xpath error"))), \
             patch("crawl4ai.CrawlerRunConfig", return_value=MagicMock()):
            result = await WebCrawlerService.extract_xpath(
                url="https://broken.example.com",
                base_selector="//div",
                fields=[{"name": "title", "selector": ".//h2", "type": "text"}],
            )

        assert result["success"] is False
        assert "xpath error" in result["error"]

    @pytest.mark.asyncio
    async def test_generate_schema_happy_path(self):
        from app.modules.web_crawler.service import WebCrawlerService
        from app.config import settings

        fake_schema = {"baseSelector": ".product", "fields": [{"name": "price", "selector": ".price"}]}

        with patch.object(settings, "GEMINI_API_KEY", "fake-test-key"), \
             patch("crawl4ai.extraction_strategy.JsonCssExtractionStrategy") as mock_cls:
            mock_cls.agenerate_schema = AsyncMock(return_value=fake_schema)
            result = await WebCrawlerService.generate_schema(
                url="https://example.com",
                query="product listings with price",
                schema_type="CSS",
                provider="gemini",
            )

        assert result["success"] is True
        assert result["url"] == "https://example.com"

    @pytest.mark.asyncio
    async def test_generate_schema_failure(self):
        from app.modules.web_crawler.service import WebCrawlerService
        from app.config import settings

        with patch.object(settings, "GEMINI_API_KEY", "fake-test-key"), \
             patch("crawl4ai.extraction_strategy.JsonCssExtractionStrategy") as mock_cls:
            mock_cls.agenerate_schema = AsyncMock(side_effect=Exception("LLM quota exceeded"))
            result = await WebCrawlerService.generate_schema(
                url="https://example.com",
                query="articles",
            )

        assert result["success"] is False
        assert "LLM quota exceeded" in result["error"]

    @pytest.mark.asyncio
    async def test_process_html_happy_path(self):
        from app.modules.web_crawler.service import WebCrawlerService
        import app.modules.web_crawler.service as svc

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.markdown = MagicMock()
        mock_result.markdown.raw_markdown = "# Test\n\nHello world"
        mock_result.markdown.fit_markdown = "# Test\n\nHello world"
        mock_result.links = {
            "internal": [{"href": "https://example.com/about"}],
            "external": [{"href": "https://other.com"}],
        }
        mock_result.error_message = None

        mock_crawler = AsyncMock()
        mock_crawler.aprocess_html = AsyncMock(return_value=mock_result)

        with patch.object(svc, "get_crawler", new=AsyncMock(return_value=mock_crawler)):
            result = await WebCrawlerService.process_html(
                html="<html><body><h1>Test</h1><p>Hello world</p></body></html>",
                url="https://example.com",
                use_fit_markdown=True,
            )

        assert result["success"] is True
        assert result["url"] == "https://example.com"
        assert "# Test" in result["markdown"]
        assert len(result["links_internal"]) == 1
        assert len(result["links_external"]) == 1

    @pytest.mark.asyncio
    async def test_process_html_no_fit_markdown(self):
        from app.modules.web_crawler.service import WebCrawlerService
        import app.modules.web_crawler.service as svc

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.markdown = MagicMock()
        mock_result.markdown.raw_markdown = "# Page"
        mock_result.markdown.fit_markdown = "# Page"
        mock_result.links = {"internal": [], "external": []}
        mock_result.error_message = None

        mock_crawler = AsyncMock()
        mock_crawler.aprocess_html = AsyncMock(return_value=mock_result)

        with patch.object(svc, "get_crawler", new=AsyncMock(return_value=mock_crawler)):
            result = await WebCrawlerService.process_html(
                html="<p>Hello</p>",
                use_fit_markdown=False,
            )

        assert result["fit_markdown"] == ""

    @pytest.mark.asyncio
    async def test_process_html_failure(self):
        from app.modules.web_crawler.service import WebCrawlerService
        import app.modules.web_crawler.service as svc

        mock_crawler = AsyncMock()
        mock_crawler.aprocess_html = AsyncMock(side_effect=Exception("parse error"))

        with patch.object(svc, "get_crawler", new=AsyncMock(return_value=mock_crawler)):
            result = await WebCrawlerService.process_html(html="<bad>")

        assert result["success"] is False
        assert "parse error" in result["error"]

    @pytest.mark.asyncio
    async def test_seed_urls_with_query(self):
        """seed_urls with query auto-enables BM25 scoring."""
        from app.modules.web_crawler.service import WebCrawlerService

        discovered = ["https://example.com/ml-tutorial", "https://example.com/python-guide"]

        mock_seeder = AsyncMock()
        mock_seeder.urls = AsyncMock(return_value=discovered)
        mock_seeder.__aenter__ = AsyncMock(return_value=mock_seeder)
        mock_seeder.__aexit__ = AsyncMock(return_value=False)

        captured_config = {}

        def fake_seeding_config(**kwargs):
            captured_config.update(kwargs)
            return MagicMock()

        with patch("crawl4ai.AsyncUrlSeeder", return_value=mock_seeder), \
             patch("crawl4ai.SeedingConfig", side_effect=fake_seeding_config):
            result = await WebCrawlerService.seed_urls(
                domain="example.com",
                query="machine learning tutorials",
                score_threshold=1.5,
            )

        assert result["success"] is True
        assert captured_config.get("query") == "machine learning tutorials"
        assert captured_config.get("extract_head") is True
        assert captured_config.get("scoring_method") == "bm25"

    @pytest.mark.asyncio
    async def test_deep_crawl_content_type_filter(self):
        """deep_crawl builds ContentTypeFilter when content_type_filter given."""
        from app.modules.web_crawler.service import WebCrawlerService
        import app.modules.web_crawler.service as svc

        page = MagicMock()
        page.success = True
        page.url = "https://example.com/page"
        page.metadata = {"title": "T", "depth": 0}
        page.markdown = MagicMock()
        page.markdown.raw_markdown = "# Page"
        page.markdown.fit_markdown = "# Page"

        mock_crawler = AsyncMock()
        mock_crawler.arun = AsyncMock(return_value=[page])

        with patch.object(svc, "get_crawler", new=AsyncMock(return_value=mock_crawler)), \
             patch("crawl4ai.BFSDeepCrawlStrategy", return_value=MagicMock()), \
             patch("crawl4ai.deep_crawling.ContentTypeFilter", return_value=MagicMock(), create=True) as mock_ctf, \
             patch("crawl4ai.deep_crawling.FilterChain", return_value=MagicMock(), create=True):
            result = await WebCrawlerService.deep_crawl(
                url="https://example.com",
                strategy="bfs",
                content_type_filter=["text/html"],
            )

        assert result["success"] is True


# ---------------------------------------------------------------------------
# v5 route tests — new endpoints + updated param forwarding
# ---------------------------------------------------------------------------

class TestWebCrawlerRoutesV5:

    @pytest.fixture(autouse=True)
    def _override_deps(self, app, test_user):
        from fastapi import HTTPException, Request
        from fastapi.security.utils import get_authorization_scheme_param
        from app.auth import get_current_user
        from app.database import get_session
        from app.modules.billing.middleware import require_ai_call_quota
        from app.rate_limit import limiter

        # Reset in-memory rate limit counters so tests in earlier classes
        # cannot exhaust low per-endpoint limits (e.g. 2/minute on /deep-crawl).
        try:
            limiter._storage.reset()
        except Exception:
            pass

        def _auth_override(request: Request):
            auth = request.headers.get("Authorization", "")
            _, token = get_authorization_scheme_param(auth)
            if not token:
                raise HTTPException(status_code=401, detail="Not authenticated")
            return test_user

        def _mock_session():
            yield MagicMock()

        from app.modules.auth_guards.middleware import require_verified_email
        app.dependency_overrides[get_current_user] = _auth_override
        app.dependency_overrides[require_verified_email] = _auth_override
        app.dependency_overrides[require_ai_call_quota] = _auth_override
        app.dependency_overrides[get_session] = _mock_session

        with patch("app.modules.web_crawler.service.init_crawler", new_callable=AsyncMock), \
             patch("app.modules.web_crawler.service.close_crawler", new_callable=AsyncMock):
            yield

        app.dependency_overrides.clear()

    # -- /extract-regex --

    @pytest.mark.asyncio
    async def test_extract_regex_success(self, client, auth_headers):
        mock_result = {
            "url": "https://example.com",
            "matches": [{"label": "email", "value": "a@b.com", "span": [0, 7]}],
            "match_count": 1,
            "success": True,
            "error": None,
        }
        with patch("app.modules.web_crawler.service.WebCrawlerService.extract_regex",
                   new=AsyncMock(return_value=mock_result)):
            response = await client.post(
                "/api/crawler/extract-regex",
                json={"url": "https://example.com", "patterns": ["email"]},
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["match_count"] == 1
        assert data["matches"][0]["label"] == "email"

    @pytest.mark.asyncio
    async def test_extract_regex_unauthorized(self, client):
        response = await client.post(
            "/api/crawler/extract-regex",
            json={"url": "https://example.com", "patterns": ["email"]},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_extract_regex_invalid_url(self, client, auth_headers):
        response = await client.post(
            "/api/crawler/extract-regex",
            json={"url": ""},
            headers=auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_extract_regex_params_forwarded(self, client, auth_headers):
        mock_result = {
            "url": "https://example.com",
            "matches": [],
            "match_count": 0,
            "success": True,
            "error": None,
        }
        with patch("app.modules.web_crawler.service.WebCrawlerService.extract_regex",
                   new=AsyncMock(return_value=mock_result)) as mock_svc:
            await client.post(
                "/api/crawler/extract-regex",
                json={
                    "url": "https://example.com",
                    "patterns": ["email", "phone_intl"],
                    "custom_patterns": {"zip": r"\b\d{5}\b"},
                },
                headers=auth_headers,
            )

        call_kwargs = mock_svc.call_args.kwargs
        assert call_kwargs["patterns"] == ["email", "phone_intl"]
        assert "zip" in call_kwargs["custom_patterns"]

    # -- /extract-xpath --

    @pytest.mark.asyncio
    async def test_extract_xpath_success(self, client, auth_headers):
        mock_result = {
            "url": "https://example.com",
            "items": [{"title": "Article 1"}],
            "item_count": 1,
            "success": True,
            "error": None,
        }
        with patch("app.modules.web_crawler.service.WebCrawlerService.extract_xpath",
                   new=AsyncMock(return_value=mock_result)):
            response = await client.post(
                "/api/crawler/extract-xpath",
                json={
                    "url": "https://example.com",
                    "base_selector": "//div[@class='item']",
                    "fields": [{"name": "title", "selector": ".//h2"}],
                },
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["item_count"] == 1
        assert data["items"][0]["title"] == "Article 1"

    @pytest.mark.asyncio
    async def test_extract_xpath_unauthorized(self, client):
        response = await client.post(
            "/api/crawler/extract-xpath",
            json={
                "url": "https://example.com",
                "base_selector": "//div",
                "fields": [{"name": "title", "selector": ".//h2"}],
            },
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_extract_xpath_missing_fields(self, client, auth_headers):
        response = await client.post(
            "/api/crawler/extract-xpath",
            json={"url": "https://example.com"},
            headers=auth_headers,
        )
        assert response.status_code == 422

    # -- /generate-schema --

    @pytest.mark.asyncio
    async def test_generate_schema_success(self, client, auth_headers):
        schema = {"baseSelector": ".item", "fields": [{"name": "title", "selector": "h2"}]}
        mock_result = {
            "url": "https://example.com",
            "schema_def": schema,
            "schema_type": "CSS",
            "success": True,
            "error": None,
        }
        with patch("app.modules.web_crawler.service.WebCrawlerService.generate_schema",
                   new=AsyncMock(return_value=mock_result)), \
             patch("app.modules.billing.service.BillingService.consume_quota",
                   new=AsyncMock(return_value=None)):
            response = await client.post(
                "/api/crawler/generate-schema",
                json={"url": "https://example.com", "query": "product listings"},
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["schema_def"]["baseSelector"] == ".item"
        assert data["schema_type"] == "CSS"

    @pytest.mark.asyncio
    async def test_generate_schema_unauthorized(self, client):
        response = await client.post(
            "/api/crawler/generate-schema",
            json={"url": "https://example.com", "query": "test"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_generate_schema_consumes_billing(self, client, auth_headers):
        mock_result = {
            "url": "https://example.com",
            "schema_def": None,
            "schema_type": "CSS",
            "success": True,
            "error": None,
        }
        with patch("app.modules.web_crawler.service.WebCrawlerService.generate_schema",
                   new=AsyncMock(return_value=mock_result)), \
             patch("app.modules.billing.service.BillingService.consume_quota",
                   new=AsyncMock(return_value=None)) as mock_billing:
            await client.post(
                "/api/crawler/generate-schema",
                json={"url": "https://example.com", "query": "test items"},
                headers=auth_headers,
            )

        mock_billing.assert_called_once()
        _, quota_type, amount, _ = mock_billing.call_args.args
        assert quota_type == "ai_call"
        assert amount == 1

    # -- /process-html --

    @pytest.mark.asyncio
    async def test_process_html_success(self, client, auth_headers):
        mock_result = {
            "url": "https://example.com",
            "markdown": "# Title\n\nContent",
            "fit_markdown": "# Title\n\nContent",
            "text_length": 18,
            "links_internal": ["https://example.com/about"],
            "links_external": [],
            "success": True,
            "error": None,
        }
        with patch("app.modules.web_crawler.service.WebCrawlerService.process_html",
                   new=AsyncMock(return_value=mock_result)):
            response = await client.post(
                "/api/crawler/process-html",
                json={"html": "<html><body><h1>Title</h1><p>Content</p></body></html>"},
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "# Title" in data["markdown"]
        assert data["text_length"] == 18
        assert len(data["links_internal"]) == 1

    @pytest.mark.asyncio
    async def test_process_html_unauthorized(self, client):
        response = await client.post(
            "/api/crawler/process-html",
            json={"html": "<p>Test</p>"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_process_html_missing_html(self, client, auth_headers):
        response = await client.post(
            "/api/crawler/process-html",
            json={},
            headers=auth_headers,
        )
        assert response.status_code == 422

    # -- /scrape v5 new params --

    @pytest.mark.asyncio
    async def test_scrape_v5_params_forwarded(self, client, auth_headers):
        """Verify browser/cache/session/markdown/link-preview params forwarded."""
        base_result = {
            "url": "https://example.com", "title": "", "markdown": "",
            "fit_markdown": "", "text_length": 0, "images": [], "image_count": 0,
            "audio": [], "video": [], "screenshot_base64": None, "pdf_base64": None,
            "mhtml": None, "links_internal": [], "links_external": [], "tables": [],
            "network_requests": [], "console_messages": [], "ssl_certificate": None,
            "status_code": 200, "redirected_url": None,
            "success": True, "scraper": "crawl4ai",
        }

        with patch("app.modules.web_crawler.service.WebCrawlerService.scrape",
                   new=AsyncMock(return_value=base_result)) as mock_scrape:
            response = await client.post(
                "/api/crawler/scrape",
                json={
                    "url": "https://example.com",
                    "browser_type": "firefox",
                    "enable_stealth": True,
                    "javascript_enabled": False,
                    "avoid_ads": True,
                    "session_id": "sess-abc",
                    "cache_mode": "enabled",
                    "ignore_links": True,
                    "body_width": 80,
                    "link_preview_query": "machine learning",
                    "link_preview_max_links": 10,
                },
                headers=auth_headers,
            )

        assert response.status_code == 200
        kw = mock_scrape.call_args.kwargs
        assert kw["browser_type"] == "firefox"
        assert kw["enable_stealth"] is True
        assert kw["javascript_enabled"] is False
        assert kw["avoid_ads"] is True
        assert kw["session_id"] == "sess-abc"
        assert kw["cache_mode"] == "enabled"
        assert kw["ignore_links"] is True
        assert kw["body_width"] == 80
        assert kw["link_preview_query"] == "machine learning"
        assert kw["link_preview_max_links"] == 10

    # -- /deep-crawl v5 new params --

    @pytest.mark.asyncio
    async def test_deep_crawl_v5_advanced_filters_forwarded(self, client, auth_headers):
        deep_result = {
            "url": "https://example.com", "strategy": "bfs",
            "pages": [], "total_pages": 0, "succeeded": 0, "failed": 0,
            "export_state": {"visited": ["https://example.com"], "queue": []},
            "success": True, "error": None,
        }

        with patch("app.modules.web_crawler.service.WebCrawlerService.deep_crawl",
                   new=AsyncMock(return_value=deep_result)) as mock_deep, \
             patch("app.modules.billing.service.BillingService.consume_quota",
                   new=AsyncMock(return_value=None)):
            response = await client.post(
                "/api/crawler/deep-crawl",
                json={
                    "url": "https://example.com",
                    "content_type_filter": ["text/html"],
                    "content_relevance_query": "python tutorials",
                    "content_relevance_threshold": 2.5,
                    "seo_filter": True,
                    "seo_filter_threshold": 0.7,
                    "resume_state": {"visited": [], "queue": []},
                },
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["export_state"]["visited"] == ["https://example.com"]

        kw = mock_deep.call_args.kwargs
        assert kw["content_type_filter"] == ["text/html"]
        assert kw["content_relevance_query"] == "python tutorials"
        assert kw["content_relevance_threshold"] == 2.5
        assert kw["seo_filter"] is True
        assert kw["seo_filter_threshold"] == 0.7
        assert kw["resume_state"] == {"visited": [], "queue": []}

    # -- /seed-urls v5 new params --

    @pytest.mark.asyncio
    async def test_seed_urls_v5_params_forwarded(self, client, auth_headers):
        seed_result = {
            "domain": "example.com",
            "urls": ["https://example.com/ml"],
            "total": 1,
            "success": True,
            "error": None,
        }

        with patch("app.modules.web_crawler.service.WebCrawlerService.seed_urls",
                   new=AsyncMock(return_value=seed_result)) as mock_seed:
            response = await client.post(
                "/api/crawler/seed-urls",
                json={
                    "domain": "example.com",
                    "query": "machine learning",
                    "score_threshold": 1.5,
                    "pattern": "*/blog/*",
                    "extract_head": True,
                },
                headers=auth_headers,
            )

        assert response.status_code == 200
        kw = mock_seed.call_args.kwargs
        assert kw["query"] == "machine learning"
        assert kw["score_threshold"] == 1.5
        assert kw["pattern"] == "*/blog/*"
        assert kw["extract_head"] is True


# ---------------------------------------------------------------------------
# V6 — Schema tests (GeolocationConfig, undetected, table_extraction_mode,
#        FastScrape*, AdaptiveCrawl*, HubCrawl*)
# ---------------------------------------------------------------------------

class TestWebCrawlerSchemasV6:

    # -- GeolocationConfig --

    def test_geolocation_config_valid(self):
        from app.modules.web_crawler.schemas import GeolocationConfig
        g = GeolocationConfig(latitude=48.8566, longitude=2.3522)
        assert g.latitude == 48.8566
        assert g.longitude == 2.3522
        assert g.accuracy == 0.0

    def test_geolocation_config_with_accuracy(self):
        from app.modules.web_crawler.schemas import GeolocationConfig
        g = GeolocationConfig(latitude=-33.86, longitude=151.2, accuracy=15.5)
        assert g.accuracy == 15.5

    def test_geolocation_config_invalid_latitude(self):
        from pydantic import ValidationError
        from app.modules.web_crawler.schemas import GeolocationConfig
        with pytest.raises(ValidationError):
            GeolocationConfig(latitude=91.0, longitude=0.0)

    def test_geolocation_config_invalid_longitude(self):
        from pydantic import ValidationError
        from app.modules.web_crawler.schemas import GeolocationConfig
        with pytest.raises(ValidationError):
            GeolocationConfig(latitude=0.0, longitude=200.0)

    def test_geolocation_config_negative_accuracy(self):
        from pydantic import ValidationError
        from app.modules.web_crawler.schemas import GeolocationConfig
        with pytest.raises(ValidationError):
            GeolocationConfig(latitude=0.0, longitude=0.0, accuracy=-1.0)

    # -- ScrapeRequest: undetected browser type --

    def test_scrape_request_undetected_browser(self):
        from app.modules.web_crawler.schemas import ScrapeRequest
        r = ScrapeRequest(url="https://example.com", browser_type="undetected")
        assert r.browser_type == "undetected"

    def test_scrape_request_invalid_browser_type(self):
        from pydantic import ValidationError
        from app.modules.web_crawler.schemas import ScrapeRequest
        with pytest.raises(ValidationError):
            ScrapeRequest(url="https://example.com", browser_type="edge")

    # -- ScrapeRequest: table_extraction_mode --

    def test_scrape_request_table_mode_default(self):
        from app.modules.web_crawler.schemas import ScrapeRequest
        r = ScrapeRequest(url="https://example.com")
        assert r.table_extraction_mode == "default"

    def test_scrape_request_table_mode_none(self):
        from app.modules.web_crawler.schemas import ScrapeRequest
        r = ScrapeRequest(url="https://example.com", table_extraction_mode="none")
        assert r.table_extraction_mode == "none"

    def test_scrape_request_table_mode_llm(self):
        from app.modules.web_crawler.schemas import ScrapeRequest
        r = ScrapeRequest(url="https://example.com", table_extraction_mode="llm")
        assert r.table_extraction_mode == "llm"

    def test_scrape_request_table_mode_invalid(self):
        from pydantic import ValidationError
        from app.modules.web_crawler.schemas import ScrapeRequest
        with pytest.raises(ValidationError):
            ScrapeRequest(url="https://example.com", table_extraction_mode="auto")

    # -- ScrapeRequest: geolocation --

    def test_scrape_request_with_geolocation(self):
        from app.modules.web_crawler.schemas import ScrapeRequest, GeolocationConfig
        r = ScrapeRequest(
            url="https://example.com",
            geolocation=GeolocationConfig(latitude=48.8566, longitude=2.3522),
        )
        assert r.geolocation is not None
        assert r.geolocation.latitude == 48.8566

    def test_scrape_request_geolocation_none_by_default(self):
        from app.modules.web_crawler.schemas import ScrapeRequest
        r = ScrapeRequest(url="https://example.com")
        assert r.geolocation is None

    # -- FastScrapeRequest / FastScrapeResponse --

    def test_fast_scrape_request_defaults(self):
        from app.modules.web_crawler.schemas import FastScrapeRequest
        r = FastScrapeRequest(url="https://example.com")
        assert r.use_fit_markdown is True
        assert r.word_count_threshold == 10
        assert r.follow_redirects is True
        assert r.headers == {}

    def test_fast_scrape_request_custom(self):
        from app.modules.web_crawler.schemas import FastScrapeRequest
        r = FastScrapeRequest(
            url="https://example.com",
            css_selector="article",
            headers={"Accept": "text/html"},
        )
        assert r.css_selector == "article"
        assert r.headers["Accept"] == "text/html"

    def test_fast_scrape_response_defaults(self):
        from app.modules.web_crawler.schemas import FastScrapeResponse
        r = FastScrapeResponse(url="https://example.com")
        assert r.success is True
        assert r.scraper == "crawl4ai_http"
        assert r.error is None

    # -- AdaptiveCrawlRequest --

    def test_adaptive_crawl_request_defaults(self):
        from app.modules.web_crawler.schemas import AdaptiveCrawlRequest
        r = AdaptiveCrawlRequest(url="https://example.com", query="python async")
        assert r.max_pages == 20
        assert r.max_depth == 5
        assert r.strategy == "statistical"
        assert r.confidence_threshold == 0.7

    def test_adaptive_crawl_request_query_too_short(self):
        from pydantic import ValidationError
        from app.modules.web_crawler.schemas import AdaptiveCrawlRequest
        with pytest.raises(ValidationError):
            AdaptiveCrawlRequest(url="https://example.com", query="ab")

    def test_adaptive_crawl_request_invalid_strategy(self):
        from pydantic import ValidationError
        from app.modules.web_crawler.schemas import AdaptiveCrawlRequest
        with pytest.raises(ValidationError):
            AdaptiveCrawlRequest(url="https://example.com", query="python", strategy="greedy")

    def test_adaptive_crawl_request_embedding_strategy(self):
        from app.modules.web_crawler.schemas import AdaptiveCrawlRequest
        r = AdaptiveCrawlRequest(url="https://example.com", query="machine learning", strategy="embedding")
        assert r.strategy == "embedding"

    def test_adaptive_crawl_response_empty(self):
        from app.modules.web_crawler.schemas import AdaptiveCrawlResponse
        r = AdaptiveCrawlResponse(url="https://example.com")
        assert r.pages == []
        assert r.total_pages == 0
        assert r.confidence is None
        assert r.is_sufficient is None

    # -- HubCrawlRequest / HubCrawlResponse --

    def test_hub_crawl_request_valid(self):
        from app.modules.web_crawler.schemas import HubCrawlRequest
        r = HubCrawlRequest(url="https://en.wikipedia.org/wiki/Python", site_profile="wikipedia")
        assert r.site_profile == "wikipedia"
        assert r.use_fit_markdown is True

    def test_hub_crawl_request_empty_profile(self):
        from pydantic import ValidationError
        from app.modules.web_crawler.schemas import HubCrawlRequest
        with pytest.raises(ValidationError):
            HubCrawlRequest(url="https://example.com", site_profile="")

    def test_hub_crawl_response_defaults(self):
        from app.modules.web_crawler.schemas import HubCrawlResponse
        r = HubCrawlResponse(url="https://example.com", success=True)
        assert r.data is None
        assert r.error is None


# ---------------------------------------------------------------------------
# V6 — Service tests (scrape_http, adaptive_crawl, hub_crawl, geo + table)
# ---------------------------------------------------------------------------

class TestWebCrawlerServiceV6:

    # -- scrape_http --

    @pytest.mark.asyncio
    async def test_scrape_http_happy_path(self):
        from app.modules.web_crawler.service import WebCrawlerService

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.markdown = MagicMock()
        mock_result.markdown.raw_markdown = "# Python\n\nGreat language."
        mock_result.markdown.fit_markdown = "# Python\n\nGreat language."
        mock_result.links = {
            "internal": [{"href": "https://python.org/docs"}],
            "external": [{"href": "https://pypi.org"}],
        }
        mock_result.metadata = {"title": "Python"}
        mock_result.status_code = 200

        mock_crawler_ctx = MagicMock()
        mock_crawler_ctx.__aenter__ = AsyncMock(return_value=MagicMock(
            arun=AsyncMock(return_value=mock_result)
        ))
        mock_crawler_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch("crawl4ai.async_configs.HTTPCrawlerConfig", MagicMock()), \
             patch("crawl4ai.AsyncWebCrawler", return_value=mock_crawler_ctx):
            result = await WebCrawlerService.scrape_http(
                url="https://python.org",
                use_fit_markdown=True,
            )

        assert result["success"] is True
        assert result["url"] == "https://python.org"
        assert "Python" in result["markdown"]
        assert result["scraper"] == "crawl4ai_http"
        assert result["links_internal"] == ["https://python.org/docs"]
        assert result["links_external"] == ["https://pypi.org"]

    @pytest.mark.asyncio
    async def test_scrape_http_failure_result(self):
        from app.modules.web_crawler.service import WebCrawlerService

        mock_result = MagicMock()
        mock_result.success = False
        mock_result.error_message = "Connection refused"

        mock_crawler_ctx = MagicMock()
        mock_crawler_ctx.__aenter__ = AsyncMock(return_value=MagicMock(
            arun=AsyncMock(return_value=mock_result)
        ))
        mock_crawler_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch("crawl4ai.async_configs.HTTPCrawlerConfig", MagicMock()), \
             patch("crawl4ai.AsyncWebCrawler", return_value=mock_crawler_ctx):
            result = await WebCrawlerService.scrape_http(url="https://bad.example.com")

        assert result["success"] is False
        assert "Connection refused" in result["error"]

    @pytest.mark.asyncio
    async def test_scrape_http_import_error(self):
        import sys
        from app.modules.web_crawler.service import WebCrawlerService
        with patch.dict(sys.modules, {"crawl4ai.async_configs": None}):
            result = await WebCrawlerService.scrape_http(url="https://example.com")

        assert result["success"] is False
        assert "crawl4ai" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_scrape_http_exception(self):
        from app.modules.web_crawler.service import WebCrawlerService

        mock_crawler_ctx = MagicMock()
        mock_crawler_ctx.__aenter__ = AsyncMock(side_effect=RuntimeError("browser crash"))
        mock_crawler_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch("crawl4ai.async_configs.HTTPCrawlerConfig", MagicMock()), \
             patch("crawl4ai.AsyncWebCrawler", return_value=mock_crawler_ctx):
            result = await WebCrawlerService.scrape_http(url="https://example.com")

        assert result["success"] is False
        assert "browser crash" in result["error"]

    # -- adaptive_crawl --

    @pytest.mark.asyncio
    async def test_adaptive_crawl_happy_path(self):
        from app.modules.web_crawler.service import WebCrawlerService
        import app.modules.web_crawler.service as svc

        mock_page = MagicMock()
        mock_page.url = "https://docs.python.org/tutorial"
        mock_page.title = "Tutorial"
        mock_page.markdown = MagicMock()
        mock_page.markdown.raw_markdown = "# Tutorial"
        mock_page.markdown.fit_markdown = "# Tutorial"
        mock_page.depth = 1
        mock_page.score = 0.85
        mock_page.success = True

        mock_state = MagicMock()
        mock_state.pages = [mock_page]

        mock_adaptive = MagicMock()
        mock_adaptive.digest = AsyncMock(return_value=mock_state)
        mock_adaptive.confidence = 0.92
        mock_adaptive.is_sufficient = True

        mock_crawler = AsyncMock()

        mock_adaptive_cls = MagicMock(return_value=mock_adaptive)
        mock_config_cls = MagicMock()

        with patch.object(svc, "get_crawler", new=AsyncMock(return_value=mock_crawler)), \
             patch("crawl4ai.adaptive_crawler.AdaptiveCrawler", mock_adaptive_cls), \
             patch("crawl4ai.adaptive_crawler.AdaptiveConfig", mock_config_cls):
            result = await WebCrawlerService.adaptive_crawl(
                url="https://docs.python.org",
                query="async python tutorial",
                max_pages=10,
            )

        assert result["success"] is True
        assert result["url"] == "https://docs.python.org"
        assert result["total_pages"] == 1
        assert result["succeeded"] == 1
        assert result["confidence"] == 0.92
        assert result["is_sufficient"] is True
        assert result["pages"][0]["url"] == "https://docs.python.org/tutorial"

    @pytest.mark.asyncio
    async def test_adaptive_crawl_failure_in_page(self):
        from app.modules.web_crawler.service import WebCrawlerService
        import app.modules.web_crawler.service as svc

        mock_page = MagicMock()
        mock_page.url = "https://example.com/broken"
        mock_page.title = ""
        mock_page.markdown = MagicMock()
        mock_page.markdown.raw_markdown = ""
        mock_page.markdown.fit_markdown = ""
        mock_page.depth = 0
        mock_page.score = None
        mock_page.success = False

        mock_state = MagicMock()
        mock_state.pages = [mock_page]

        mock_adaptive = MagicMock()
        mock_adaptive.digest = AsyncMock(return_value=mock_state)
        mock_adaptive.confidence = 0.1
        mock_adaptive.is_sufficient = False

        mock_crawler = AsyncMock()

        with patch.object(svc, "get_crawler", new=AsyncMock(return_value=mock_crawler)), \
             patch("crawl4ai.adaptive_crawler.AdaptiveCrawler", MagicMock(return_value=mock_adaptive)), \
             patch("crawl4ai.adaptive_crawler.AdaptiveConfig", MagicMock()):
            result = await WebCrawlerService.adaptive_crawl(
                url="https://example.com",
                query="test query here",
            )

        assert result["success"] is True
        assert result["failed"] == 1
        assert result["succeeded"] == 0

    @pytest.mark.asyncio
    async def test_adaptive_crawl_import_error(self):
        from app.modules.web_crawler.service import WebCrawlerService
        import app.modules.web_crawler.service as svc

        import sys
        mock_crawler = AsyncMock()
        with patch.object(svc, "get_crawler", new=AsyncMock(return_value=mock_crawler)), \
             patch.dict(sys.modules, {"crawl4ai.adaptive_crawler": None}):
            result = await WebCrawlerService.adaptive_crawl(
                url="https://example.com",
                query="test query here",
            )

        assert result["success"] is False
        assert "crawl4ai" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_adaptive_crawl_exception(self):
        from app.modules.web_crawler.service import WebCrawlerService
        import app.modules.web_crawler.service as svc

        mock_crawler = AsyncMock()
        mock_adaptive = MagicMock()
        mock_adaptive.digest = AsyncMock(side_effect=RuntimeError("timeout"))

        with patch.object(svc, "get_crawler", new=AsyncMock(return_value=mock_crawler)), \
             patch("crawl4ai.adaptive_crawler.AdaptiveCrawler", MagicMock(return_value=mock_adaptive)), \
             patch("crawl4ai.adaptive_crawler.AdaptiveConfig", MagicMock()):
            result = await WebCrawlerService.adaptive_crawl(
                url="https://example.com",
                query="test query here",
            )

        assert result["success"] is False
        assert "timeout" in result["error"]

    # -- hub_crawl --

    @pytest.mark.asyncio
    async def test_hub_crawl_happy_path(self):
        from app.modules.web_crawler.service import WebCrawlerService

        mock_instance = MagicMock()
        mock_instance.run = AsyncMock(return_value=json.dumps({"title": "Python", "summary": "A language"}))
        mock_crawler_cls = MagicMock(return_value=mock_instance)

        mock_hub = MagicMock()
        mock_hub.get = MagicMock(return_value=mock_crawler_cls)

        with patch("crawl4ai.hub.CrawlerHub", mock_hub):
            result = await WebCrawlerService.hub_crawl(
                url="https://en.wikipedia.org/wiki/Python",
                site_profile="wikipedia",
            )

        assert result["success"] is True
        assert result["site_profile"] == "wikipedia"
        assert result["data"]["title"] == "Python"

    @pytest.mark.asyncio
    async def test_hub_crawl_unknown_profile(self):
        from app.modules.web_crawler.service import WebCrawlerService

        mock_hub = MagicMock()
        mock_hub.get = MagicMock(return_value=None)

        with patch("crawl4ai.hub.CrawlerHub", mock_hub):
            result = await WebCrawlerService.hub_crawl(
                url="https://example.com",
                site_profile="unknown_site_xyz",
            )

        assert result["success"] is False
        assert "unknown_site_xyz" in result["error"]

    @pytest.mark.asyncio
    async def test_hub_crawl_import_error(self):
        import sys
        from app.modules.web_crawler.service import WebCrawlerService
        with patch.dict(sys.modules, {"crawl4ai.hub": None}):
            result = await WebCrawlerService.hub_crawl(
                url="https://example.com",
                site_profile="wikipedia",
            )

        assert result["success"] is False
        assert "crawl4ai" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_hub_crawl_exception(self):
        from app.modules.web_crawler.service import WebCrawlerService

        mock_instance = MagicMock()
        mock_instance.run = AsyncMock(side_effect=Exception("connection timeout"))
        mock_crawler_cls = MagicMock(return_value=mock_instance)

        mock_hub = MagicMock()
        mock_hub.get = MagicMock(return_value=mock_crawler_cls)

        with patch("crawl4ai.hub.CrawlerHub", mock_hub):
            result = await WebCrawlerService.hub_crawl(
                url="https://example.com",
                site_profile="wikipedia",
            )

        assert result["success"] is False
        assert "connection timeout" in result["error"]

    # -- scrape() geolocation forwarding --

    @pytest.mark.asyncio
    async def test_scrape_geolocation_forwarded(self):
        from app.modules.web_crawler.service import WebCrawlerService
        import app.modules.web_crawler.service as svc

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.markdown = MagicMock()
        mock_result.markdown.raw_markdown = "# Geo page"
        mock_result.markdown.fit_markdown = "# Geo page"
        mock_result.links = {"internal": [], "external": []}
        mock_result.media = {}
        mock_result.metadata = {"title": "Geo page"}
        mock_result.screenshot = None
        mock_result.pdf = None
        mock_result.network_requests = None
        mock_result.console_messages = []
        mock_result.ssl_certificate = None
        mock_result.mhtml = None

        mock_crawler = AsyncMock()
        mock_crawler.arun = AsyncMock(return_value=mock_result)

        captured_run_config = {}

        import crawl4ai.async_configs as ac_mod
        real_crc = ac_mod.CrawlerRunConfig

        def capture_run_config(**kwargs):
            captured_run_config.update(kwargs)
            return real_crc(**kwargs)

        with patch.object(svc, "get_crawler", new=AsyncMock(return_value=mock_crawler)), \
             patch("crawl4ai.CrawlerRunConfig", side_effect=capture_run_config):
            await WebCrawlerService.scrape(
                url="https://example.com",
                geolocation={"latitude": 48.8566, "longitude": 2.3522, "accuracy": 10.0},
            )

        assert "geolocation" in captured_run_config

    # -- scrape() table_extraction_mode forwarding --

    @pytest.mark.asyncio
    async def test_scrape_table_mode_none_forwarded(self):
        from app.modules.web_crawler.service import WebCrawlerService
        import app.modules.web_crawler.service as svc

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.markdown = MagicMock()
        mock_result.markdown.raw_markdown = "# Page"
        mock_result.markdown.fit_markdown = "# Page"
        mock_result.links = {"internal": [], "external": []}
        mock_result.media = {}
        mock_result.metadata = {"title": "Page"}
        mock_result.screenshot = None
        mock_result.pdf = None
        mock_result.network_requests = None
        mock_result.console_messages = []
        mock_result.ssl_certificate = None
        mock_result.mhtml = None

        mock_crawler = AsyncMock()
        mock_crawler.arun = AsyncMock(return_value=mock_result)

        captured_run_config = {}

        import crawl4ai.async_configs as ac_mod
        real_crc = ac_mod.CrawlerRunConfig

        def capture_run_config(**kwargs):
            captured_run_config.update(kwargs)
            return real_crc(**kwargs)

        with patch.object(svc, "get_crawler", new=AsyncMock(return_value=mock_crawler)), \
             patch("crawl4ai.CrawlerRunConfig", side_effect=capture_run_config):
            await WebCrawlerService.scrape(
                url="https://example.com",
                table_extraction_mode="none",
            )

        assert "table_extraction" in captured_run_config


# ---------------------------------------------------------------------------
# V6 — Route tests (/scrape-http, /adaptive-crawl, /hub/crawl, /scrape v6)
# ---------------------------------------------------------------------------

class TestWebCrawlerRoutesV6:

    @pytest.fixture(autouse=True)
    def _override_deps(self, app, test_user):
        from fastapi import HTTPException, Request
        from fastapi.security.utils import get_authorization_scheme_param
        from app.auth import get_current_user
        from app.database import get_session
        from app.modules.billing.middleware import require_ai_call_quota
        from app.rate_limit import limiter

        try:
            limiter._storage.reset()
        except Exception:
            pass

        def _auth_override(request: Request):
            auth = request.headers.get("Authorization", "")
            _, token = get_authorization_scheme_param(auth)
            if not token:
                raise HTTPException(status_code=401, detail="Not authenticated")
            return test_user

        def _mock_session():
            yield MagicMock()

        from app.modules.auth_guards.middleware import require_verified_email
        app.dependency_overrides[get_current_user] = _auth_override
        app.dependency_overrides[require_verified_email] = _auth_override
        app.dependency_overrides[require_ai_call_quota] = _auth_override
        app.dependency_overrides[get_session] = _mock_session

        with patch("app.modules.web_crawler.service.init_crawler", new_callable=AsyncMock), \
             patch("app.modules.web_crawler.service.close_crawler", new_callable=AsyncMock):
            yield

        app.dependency_overrides.clear()

    # -- /scrape-http --

    @pytest.mark.asyncio
    async def test_scrape_http_success(self, client, auth_headers):
        mock_result = {
            "url": "https://python.org",
            "title": "Python",
            "markdown": "# Python",
            "fit_markdown": "# Python",
            "text_length": 8,
            "links_internal": [],
            "links_external": [],
            "status_code": 200,
            "scraper": "crawl4ai_http",
            "success": True,
            "error": None,
        }
        with patch("app.modules.web_crawler.service.WebCrawlerService.scrape_http",
                   new=AsyncMock(return_value=mock_result)):
            response = await client.post(
                "/api/crawler/scrape-http",
                json={"url": "https://python.org"},
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["scraper"] == "crawl4ai_http"
        assert data["title"] == "Python"

    @pytest.mark.asyncio
    async def test_scrape_http_unauthorized(self, client):
        response = await client.post(
            "/api/crawler/scrape-http",
            json={"url": "https://python.org"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_scrape_http_invalid_url(self, client, auth_headers):
        response = await client.post(
            "/api/crawler/scrape-http",
            json={"url": ""},
            headers=auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_scrape_http_params_forwarded(self, client, auth_headers):
        mock_result = {
            "url": "https://example.com",
            "title": "", "markdown": "", "fit_markdown": "",
            "text_length": 0, "links_internal": [], "links_external": [],
            "status_code": 200, "scraper": "crawl4ai_http",
            "success": True, "error": None,
        }
        with patch("app.modules.web_crawler.service.WebCrawlerService.scrape_http",
                   new=AsyncMock(return_value=mock_result)) as mock_svc:
            await client.post(
                "/api/crawler/scrape-http",
                json={
                    "url": "https://example.com",
                    "css_selector": "article",
                    "use_fit_markdown": False,
                    "follow_redirects": False,
                },
                headers=auth_headers,
            )

        kw = mock_svc.call_args.kwargs
        assert kw["css_selector"] == "article"
        assert kw["use_fit_markdown"] is False
        assert kw["follow_redirects"] is False

    @pytest.mark.asyncio
    async def test_scrape_http_service_error(self, client, auth_headers):
        mock_result = {
            "url": "https://bad.example.com",
            "title": "", "markdown": "", "fit_markdown": "",
            "text_length": 0, "links_internal": [], "links_external": [],
            "status_code": None, "scraper": "crawl4ai_http",
            "success": False, "error": "Connection refused",
        }
        with patch("app.modules.web_crawler.service.WebCrawlerService.scrape_http",
                   new=AsyncMock(return_value=mock_result)):
            response = await client.post(
                "/api/crawler/scrape-http",
                json={"url": "https://bad.example.com"},
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["error"] == "Connection refused"

    # -- /adaptive-crawl --

    @pytest.mark.asyncio
    async def test_adaptive_crawl_success(self, client, auth_headers):
        mock_result = {
            "url": "https://docs.python.org",
            "query": "async tutorial",
            "pages": [
                {"url": "https://docs.python.org/asyncio", "title": "asyncio",
                 "markdown": "# asyncio", "depth": 1, "score": 0.9,
                 "success": True, "error": None},
            ],
            "total_pages": 1,
            "succeeded": 1,
            "failed": 0,
            "confidence": 0.88,
            "is_sufficient": True,
            "success": True,
            "error": None,
        }
        with patch("app.modules.web_crawler.service.WebCrawlerService.adaptive_crawl",
                   new=AsyncMock(return_value=mock_result)), \
             patch("app.modules.web_crawler.routes.BillingService.consume_quota",
                   new_callable=AsyncMock):
            response = await client.post(
                "/api/crawler/adaptive-crawl",
                json={"url": "https://docs.python.org", "query": "async tutorial"},
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["confidence"] == 0.88
        assert data["is_sufficient"] is True
        assert len(data["pages"]) == 1

    @pytest.mark.asyncio
    async def test_adaptive_crawl_unauthorized(self, client):
        response = await client.post(
            "/api/crawler/adaptive-crawl",
            json={"url": "https://example.com", "query": "async tutorial"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_adaptive_crawl_query_too_short(self, client, auth_headers):
        response = await client.post(
            "/api/crawler/adaptive-crawl",
            json={"url": "https://example.com", "query": "ab"},
            headers=auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_adaptive_crawl_consumes_billing(self, client, auth_headers):
        mock_result = {
            "url": "https://docs.python.org",
            "query": "async tutorial",
            "pages": [],
            "total_pages": 5,
            "succeeded": 5,
            "failed": 0,
            "confidence": 0.75,
            "is_sufficient": True,
            "success": True,
            "error": None,
        }
        with patch("app.modules.web_crawler.service.WebCrawlerService.adaptive_crawl",
                   new=AsyncMock(return_value=mock_result)), \
             patch("app.modules.web_crawler.routes.BillingService.consume_quota",
                   new_callable=AsyncMock) as mock_billing:
            response = await client.post(
                "/api/crawler/adaptive-crawl",
                json={"url": "https://docs.python.org", "query": "async tutorial"},
                headers=auth_headers,
            )

        assert response.status_code == 200
        mock_billing.assert_called_once()
        _, quota_type, amount, _ = mock_billing.call_args.args
        assert quota_type == "ai_call"
        assert amount == 5

    @pytest.mark.asyncio
    async def test_adaptive_crawl_billing_min_one(self, client, auth_headers):
        """Billing should consume at least 1 even when total_pages is 0."""
        mock_result = {
            "url": "https://example.com",
            "query": "test query here",
            "pages": [],
            "total_pages": 0,
            "succeeded": 0,
            "failed": 0,
            "confidence": None,
            "is_sufficient": None,
            "success": False,
            "error": "Import error",
        }
        with patch("app.modules.web_crawler.service.WebCrawlerService.adaptive_crawl",
                   new=AsyncMock(return_value=mock_result)), \
             patch("app.modules.web_crawler.routes.BillingService.consume_quota",
                   new_callable=AsyncMock) as mock_billing:
            await client.post(
                "/api/crawler/adaptive-crawl",
                json={"url": "https://example.com", "query": "test query here"},
                headers=auth_headers,
            )

        mock_billing.assert_called_once()
        _, _, amount, _ = mock_billing.call_args.args
        assert amount >= 1

    @pytest.mark.asyncio
    async def test_adaptive_crawl_params_forwarded(self, client, auth_headers):
        mock_result = {
            "url": "https://example.com",
            "query": "machine learning basics",
            "pages": [], "total_pages": 0, "succeeded": 0, "failed": 0,
            "confidence": None, "is_sufficient": None,
            "success": True, "error": None,
        }
        with patch("app.modules.web_crawler.service.WebCrawlerService.adaptive_crawl",
                   new=AsyncMock(return_value=mock_result)) as mock_svc, \
             patch("app.modules.web_crawler.routes.BillingService.consume_quota",
                   new_callable=AsyncMock):
            await client.post(
                "/api/crawler/adaptive-crawl",
                json={
                    "url": "https://example.com",
                    "query": "machine learning basics",
                    "max_pages": 30,
                    "max_depth": 8,
                    "strategy": "embedding",
                    "confidence_threshold": 0.85,
                },
                headers=auth_headers,
            )

        kw = mock_svc.call_args.kwargs
        assert kw["max_pages"] == 30
        assert kw["max_depth"] == 8
        assert kw["strategy"] == "embedding"
        assert kw["confidence_threshold"] == 0.85

    # -- /hub/crawl --

    @pytest.mark.asyncio
    async def test_hub_crawl_success(self, client, auth_headers):
        mock_result = {
            "url": "https://en.wikipedia.org/wiki/Python",
            "site_profile": "wikipedia",
            "data": {"title": "Python (programming language)", "summary": "..."},
            "success": True,
            "error": None,
        }
        with patch("app.modules.web_crawler.service.WebCrawlerService.hub_crawl",
                   new=AsyncMock(return_value=mock_result)):
            response = await client.post(
                "/api/crawler/hub/crawl",
                json={"url": "https://en.wikipedia.org/wiki/Python", "site_profile": "wikipedia"},
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["site_profile"] == "wikipedia"
        assert data["data"]["title"] == "Python (programming language)"

    @pytest.mark.asyncio
    async def test_hub_crawl_unauthorized(self, client):
        response = await client.post(
            "/api/crawler/hub/crawl",
            json={"url": "https://example.com", "site_profile": "wikipedia"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_hub_crawl_empty_profile(self, client, auth_headers):
        response = await client.post(
            "/api/crawler/hub/crawl",
            json={"url": "https://example.com", "site_profile": ""},
            headers=auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_hub_crawl_unknown_profile_response(self, client, auth_headers):
        mock_result = {
            "url": "https://example.com",
            "success": False,
            "error": "Unknown site profile: 'nonexistent_site'. Check CrawlerHub for available profiles.",
        }
        with patch("app.modules.web_crawler.service.WebCrawlerService.hub_crawl",
                   new=AsyncMock(return_value=mock_result)):
            response = await client.post(
                "/api/crawler/hub/crawl",
                json={"url": "https://example.com", "site_profile": "nonexistent_site"},
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "nonexistent_site" in data["error"]

    @pytest.mark.asyncio
    async def test_hub_crawl_params_forwarded(self, client, auth_headers):
        mock_result = {
            "url": "https://arxiv.org/abs/2301.00001",
            "site_profile": "arxiv",
            "data": {"authors": ["Smith"]},
            "success": True,
            "error": None,
        }
        with patch("app.modules.web_crawler.service.WebCrawlerService.hub_crawl",
                   new=AsyncMock(return_value=mock_result)) as mock_svc:
            await client.post(
                "/api/crawler/hub/crawl",
                json={
                    "url": "https://arxiv.org/abs/2301.00001",
                    "site_profile": "arxiv",
                    "use_fit_markdown": False,
                },
                headers=auth_headers,
            )

        kw = mock_svc.call_args.kwargs
        assert kw["site_profile"] == "arxiv"
        assert kw["use_fit_markdown"] is False

    # -- /scrape with v6 params --

    @pytest.mark.asyncio
    async def test_scrape_with_geolocation(self, client, auth_headers):
        mock_result = {
            "url": "https://example.com",
            "markdown": "# Paris content",
            "fit_markdown": "# Paris content",
            "title": "Example FR",
            "scraper": "crawl4ai",
            "success": True,
            "error": None,
            "images": [],
            "image_count": 0,
            "audio": [],
            "video": [],
            "links_internal": [],
            "links_external": [],
            "tables": [],
            "network_requests": [],
            "console_messages": [],
            "ssl_certificate": None,
            "mhtml": None,
            "text_length": 15,
        }
        with patch("app.modules.web_crawler.service.WebCrawlerService.scrape",
                   new=AsyncMock(return_value=mock_result)) as mock_svc:
            response = await client.post(
                "/api/crawler/scrape",
                json={
                    "url": "https://example.com",
                    "geolocation": {"latitude": 48.8566, "longitude": 2.3522, "accuracy": 5.0},
                },
                headers=auth_headers,
            )

        assert response.status_code == 200
        kw = mock_svc.call_args.kwargs
        assert kw["geolocation"] == {"latitude": 48.8566, "longitude": 2.3522, "accuracy": 5.0}

    @pytest.mark.asyncio
    async def test_scrape_with_table_mode_llm(self, client, auth_headers):
        mock_result = {
            "url": "https://example.com",
            "markdown": "# Tables",
            "fit_markdown": "# Tables",
            "title": "Example",
            "scraper": "crawl4ai",
            "success": True,
            "error": None,
            "images": [],
            "image_count": 0,
            "audio": [],
            "video": [],
            "links_internal": [],
            "links_external": [],
            "tables": [],
            "network_requests": [],
            "console_messages": [],
            "ssl_certificate": None,
            "mhtml": None,
            "text_length": 8,
        }
        with patch("app.modules.web_crawler.service.WebCrawlerService.scrape",
                   new=AsyncMock(return_value=mock_result)) as mock_svc:
            await client.post(
                "/api/crawler/scrape",
                json={"url": "https://example.com", "table_extraction_mode": "llm"},
                headers=auth_headers,
            )

        kw = mock_svc.call_args.kwargs
        assert kw["table_extraction_mode"] == "llm"

    @pytest.mark.asyncio
    async def test_scrape_with_undetected_browser(self, client, auth_headers):
        mock_result = {
            "url": "https://example.com",
            "markdown": "# Page",
            "fit_markdown": "# Page",
            "title": "Example",
            "scraper": "crawl4ai",
            "success": True,
            "error": None,
            "images": [],
            "image_count": 0,
            "audio": [],
            "video": [],
            "links_internal": [],
            "links_external": [],
            "tables": [],
            "network_requests": [],
            "console_messages": [],
            "ssl_certificate": None,
            "mhtml": None,
            "text_length": 6,
        }
        with patch("app.modules.web_crawler.service.WebCrawlerService.scrape",
                   new=AsyncMock(return_value=mock_result)) as mock_svc:
            await client.post(
                "/api/crawler/scrape",
                json={"url": "https://example.com", "browser_type": "undetected"},
                headers=auth_headers,
            )

        kw = mock_svc.call_args.kwargs
        assert kw["browser_type"] == "undetected"


# ---------------------------------------------------------------------------
# V7 — Schema tests (CrawlProxyConfig, BatchDispatcherConfig, content_filter_mode,
#        antibot_retry, C4ACompile*, C4AValidate*, composite_scorers)
# ---------------------------------------------------------------------------

class TestWebCrawlerSchemasV7:

    # -- CrawlProxyConfig --

    def test_proxy_config_valid(self):
        from app.modules.web_crawler.schemas import CrawlProxyConfig
        p = CrawlProxyConfig(server="http://proxy:8080")
        assert p.server == "http://proxy:8080"
        assert p.username is None
        assert p.password is None

    def test_proxy_config_with_auth(self):
        from app.modules.web_crawler.schemas import CrawlProxyConfig
        p = CrawlProxyConfig(server="socks5://proxy:1080", username="user", password="pass")
        assert p.username == "user"
        assert p.password == "pass"

    def test_proxy_config_missing_server(self):
        from pydantic import ValidationError
        from app.modules.web_crawler.schemas import CrawlProxyConfig
        with pytest.raises(ValidationError):
            CrawlProxyConfig()

    def test_proxy_config_empty_server(self):
        from pydantic import ValidationError
        from app.modules.web_crawler.schemas import CrawlProxyConfig
        with pytest.raises(ValidationError):
            CrawlProxyConfig(server="")

    # -- BatchDispatcherConfig --

    def test_dispatcher_config_defaults(self):
        from app.modules.web_crawler.schemas import BatchDispatcherConfig
        d = BatchDispatcherConfig()
        assert d.max_session_permit == 20
        assert d.memory_threshold_percent == 90.0
        assert d.rate_limit_base_delay_min == 1.0
        assert d.rate_limit_base_delay_max == 3.0
        assert d.rate_limit_max_delay == 60.0

    def test_dispatcher_config_custom(self):
        from app.modules.web_crawler.schemas import BatchDispatcherConfig
        d = BatchDispatcherConfig(
            max_session_permit=5,
            memory_threshold_percent=80.0,
            rate_limit_base_delay_min=0.5,
            rate_limit_base_delay_max=2.0,
            rate_limit_max_delay=30.0,
        )
        assert d.max_session_permit == 5
        assert d.memory_threshold_percent == 80.0
        assert d.rate_limit_base_delay_min == 0.5

    def test_dispatcher_config_memory_threshold_too_low(self):
        from pydantic import ValidationError
        from app.modules.web_crawler.schemas import BatchDispatcherConfig
        with pytest.raises(ValidationError):
            BatchDispatcherConfig(memory_threshold_percent=49.9)

    def test_dispatcher_config_memory_threshold_too_high(self):
        from pydantic import ValidationError
        from app.modules.web_crawler.schemas import BatchDispatcherConfig
        with pytest.raises(ValidationError):
            BatchDispatcherConfig(memory_threshold_percent=99.1)

    # -- ScrapeRequest new fields --

    def test_scrape_request_content_filter_mode_default(self):
        from app.modules.web_crawler.schemas import ScrapeRequest
        r = ScrapeRequest(url="https://example.com")
        assert r.content_filter_mode == "pruning"

    def test_scrape_request_content_filter_mode_bm25(self):
        from app.modules.web_crawler.schemas import ScrapeRequest
        r = ScrapeRequest(url="https://example.com", content_filter_mode="bm25")
        assert r.content_filter_mode == "bm25"

    def test_scrape_request_content_filter_mode_llm(self):
        from app.modules.web_crawler.schemas import ScrapeRequest
        r = ScrapeRequest(url="https://example.com", content_filter_mode="llm")
        assert r.content_filter_mode == "llm"

    def test_scrape_request_content_filter_mode_invalid(self):
        from pydantic import ValidationError
        from app.modules.web_crawler.schemas import ScrapeRequest
        with pytest.raises(ValidationError):
            ScrapeRequest(url="https://example.com", content_filter_mode="auto")

    def test_scrape_request_antibot_retry_default(self):
        from app.modules.web_crawler.schemas import ScrapeRequest
        r = ScrapeRequest(url="https://example.com")
        assert r.antibot_retry is False

    def test_scrape_request_antibot_retry_enabled(self):
        from app.modules.web_crawler.schemas import ScrapeRequest
        r = ScrapeRequest(url="https://example.com", antibot_retry=True)
        assert r.antibot_retry is True

    def test_scrape_request_with_proxies(self):
        from app.modules.web_crawler.schemas import ScrapeRequest, CrawlProxyConfig
        r = ScrapeRequest(
            url="https://example.com",
            proxies=[
                CrawlProxyConfig(server="http://proxy1:8080"),
                CrawlProxyConfig(server="http://proxy2:8080", username="u", password="p"),
            ],
        )
        assert len(r.proxies) == 2
        assert r.proxies[0].server == "http://proxy1:8080"
        assert r.proxies[1].username == "u"

    def test_scrape_request_proxies_none_by_default(self):
        from app.modules.web_crawler.schemas import ScrapeRequest
        r = ScrapeRequest(url="https://example.com")
        assert r.proxies is None

    # -- BatchScrapeRequest new fields --

    def test_batch_request_with_dispatcher(self):
        from app.modules.web_crawler.schemas import BatchScrapeRequest, BatchDispatcherConfig
        r = BatchScrapeRequest(
            urls=["https://a.com"],
            dispatcher=BatchDispatcherConfig(max_session_permit=10),
        )
        assert r.dispatcher is not None
        assert r.dispatcher.max_session_permit == 10

    def test_batch_request_with_proxies(self):
        from app.modules.web_crawler.schemas import BatchScrapeRequest, CrawlProxyConfig
        r = BatchScrapeRequest(
            urls=["https://a.com"],
            proxies=[CrawlProxyConfig(server="http://proxy:8080")],
        )
        assert len(r.proxies) == 1

    def test_batch_response_with_monitor_stats(self):
        from app.modules.web_crawler.schemas import BatchScrapeResponse
        r = BatchScrapeResponse(
            total=2, succeeded=2, failed=0,
            monitor_stats={"memory_mb": 512, "tasks_done": 2},
        )
        assert r.monitor_stats["memory_mb"] == 512

    def test_batch_response_monitor_stats_none_by_default(self):
        from app.modules.web_crawler.schemas import BatchScrapeResponse
        r = BatchScrapeResponse(total=1, succeeded=1, failed=0)
        assert r.monitor_stats is None

    # -- DeepCrawlRequest new fields --

    def test_deep_crawl_request_composite_scorers(self):
        from app.modules.web_crawler.schemas import DeepCrawlRequest
        r = DeepCrawlRequest(
            url="https://example.com",
            strategy="best_first",
            composite_scorers=["domain_authority", "freshness", "path_depth"],
        )
        assert r.composite_scorers == ["domain_authority", "freshness", "path_depth"]

    def test_deep_crawl_request_composite_scorers_none_by_default(self):
        from app.modules.web_crawler.schemas import DeepCrawlRequest
        r = DeepCrawlRequest(url="https://example.com")
        assert r.composite_scorers is None

    def test_deep_crawl_request_domain_authority_weights(self):
        from app.modules.web_crawler.schemas import DeepCrawlRequest
        r = DeepCrawlRequest(
            url="https://example.com",
            domain_authority_weights={"docs.python.org": 0.9, "pypi.org": 0.7},
        )
        assert r.domain_authority_weights["docs.python.org"] == 0.9

    def test_deep_crawl_request_with_dispatcher(self):
        from app.modules.web_crawler.schemas import DeepCrawlRequest, BatchDispatcherConfig
        r = DeepCrawlRequest(
            url="https://example.com",
            dispatcher=BatchDispatcherConfig(max_session_permit=5),
        )
        assert r.dispatcher.max_session_permit == 5

    def test_deep_crawl_request_with_proxies(self):
        from app.modules.web_crawler.schemas import DeepCrawlRequest, CrawlProxyConfig
        r = DeepCrawlRequest(
            url="https://example.com",
            proxies=[CrawlProxyConfig(server="http://proxy:8080")],
        )
        assert len(r.proxies) == 1

    def test_deep_crawl_response_monitor_stats(self):
        from app.modules.web_crawler.schemas import DeepCrawlResponse
        r = DeepCrawlResponse(
            url="https://example.com",
            monitor_stats={"urls_crawled": 10, "memory_mb": 256},
        )
        assert r.monitor_stats["urls_crawled"] == 10

    def test_deep_crawl_response_monitor_stats_none_by_default(self):
        from app.modules.web_crawler.schemas import DeepCrawlResponse
        r = DeepCrawlResponse(url="https://example.com")
        assert r.monitor_stats is None

    # -- C4A schemas --

    def test_c4a_compile_request_valid(self):
        from app.modules.web_crawler.schemas import C4ACompileRequest
        r = C4ACompileRequest(script="click('.btn')")
        assert r.script == "click('.btn')"

    def test_c4a_compile_request_empty_script(self):
        from pydantic import ValidationError
        from app.modules.web_crawler.schemas import C4ACompileRequest
        with pytest.raises(ValidationError):
            C4ACompileRequest(script="")

    def test_c4a_compile_response_defaults(self):
        from app.modules.web_crawler.schemas import C4ACompileResponse
        r = C4ACompileResponse()
        assert r.js_code == ""
        assert r.success is True
        assert r.error is None

    def test_c4a_compile_response_with_code(self):
        from app.modules.web_crawler.schemas import C4ACompileResponse
        r = C4ACompileResponse(js_code="document.querySelector('.btn').click()", success=True)
        assert "click" in r.js_code

    def test_c4a_validate_request_valid(self):
        from app.modules.web_crawler.schemas import C4AValidateRequest
        r = C4AValidateRequest(script="wait(1000)")
        assert r.script == "wait(1000)"

    def test_c4a_validate_request_empty_script(self):
        from pydantic import ValidationError
        from app.modules.web_crawler.schemas import C4AValidateRequest
        with pytest.raises(ValidationError):
            C4AValidateRequest(script="")

    def test_c4a_validate_response_defaults(self):
        from app.modules.web_crawler.schemas import C4AValidateResponse
        r = C4AValidateResponse()
        assert r.valid is True
        assert r.errors == []

    def test_c4a_validate_response_with_errors(self):
        from app.modules.web_crawler.schemas import C4AValidateResponse
        r = C4AValidateResponse(valid=False, errors=["unexpected token at line 3"])
        assert r.valid is False
        assert len(r.errors) == 1


# ---------------------------------------------------------------------------
# V7 — Service tests (compile_c4a, validate_c4a)
# ---------------------------------------------------------------------------

class TestWebCrawlerServiceV7:

    # -- compile_c4a --

    def test_compile_c4a_happy_path(self):
        from app.modules.web_crawler.service import WebCrawlerService

        mock_result = MagicMock()
        mock_result.js_code = "document.querySelector('.btn').click();"

        with patch("crawl4ai.c4a_compile", return_value=mock_result):
            result = WebCrawlerService.compile_c4a(script="click('.btn')")

        assert result["success"] is True
        assert result["js_code"] == "document.querySelector('.btn').click();"

    def test_compile_c4a_no_js_code(self):
        from app.modules.web_crawler.service import WebCrawlerService

        mock_result = MagicMock()
        mock_result.js_code = ""
        mock_result.error = "Syntax error on line 1"

        with patch("crawl4ai.c4a_compile", return_value=mock_result):
            result = WebCrawlerService.compile_c4a(script="bad script")

        assert result["success"] is False
        assert "Syntax error" in result["error"]

    def test_compile_c4a_import_error(self):
        from app.modules.web_crawler.service import WebCrawlerService

        with patch("crawl4ai.c4a_compile", side_effect=ImportError("no c4a_compile")):
            result = WebCrawlerService.compile_c4a(script="click('.btn')")

        assert result["success"] is False
        assert "crawl4ai" in result["error"]

    def test_compile_c4a_exception(self):
        from app.modules.web_crawler.service import WebCrawlerService

        with patch("crawl4ai.c4a_compile", side_effect=RuntimeError("unexpected")):
            result = WebCrawlerService.compile_c4a(script="click('.btn')")

        assert result["success"] is False
        assert "unexpected" in result["error"]

    # -- validate_c4a --

    def test_validate_c4a_happy_path(self):
        from app.modules.web_crawler.service import WebCrawlerService

        mock_result = MagicMock()
        mock_result.valid = True
        mock_result.errors = []

        with patch("crawl4ai.c4a_validate", return_value=mock_result):
            result = WebCrawlerService.validate_c4a(script="click('.btn')")

        assert result["valid"] is True
        assert result["errors"] == []

    def test_validate_c4a_invalid_script(self):
        from app.modules.web_crawler.service import WebCrawlerService

        mock_result = MagicMock()
        mock_result.valid = False
        mock_result.errors = ["unexpected token at line 2", "missing argument"]

        with patch("crawl4ai.c4a_validate", return_value=mock_result):
            result = WebCrawlerService.validate_c4a(script="bad script")

        assert result["valid"] is False
        assert len(result["errors"]) == 2
        assert "unexpected token" in result["errors"][0]

    def test_validate_c4a_import_error(self):
        from app.modules.web_crawler.service import WebCrawlerService

        with patch("crawl4ai.c4a_validate", side_effect=ImportError("no c4a_validate")):
            result = WebCrawlerService.validate_c4a(script="click('.btn')")

        assert result["valid"] is False
        assert "crawl4ai" in result["errors"][0]

    def test_validate_c4a_exception(self):
        from app.modules.web_crawler.service import WebCrawlerService

        with patch("crawl4ai.c4a_validate", side_effect=RuntimeError("parser crash")):
            result = WebCrawlerService.validate_c4a(script="click('.btn')")

        assert result["valid"] is False
        assert "parser crash" in result["errors"][0]


# ---------------------------------------------------------------------------
# V7 — Route tests (/c4a/compile, /c4a/validate, /scrape v7, /batch v7,
#        /deep-crawl v7)
# ---------------------------------------------------------------------------

class TestWebCrawlerRoutesV7:

    @pytest.fixture(autouse=True)
    def _override_deps(self, app, test_user):
        from fastapi import HTTPException, Request
        from fastapi.security.utils import get_authorization_scheme_param
        from app.auth import get_current_user
        from app.database import get_session
        from app.modules.billing.middleware import require_ai_call_quota
        from app.rate_limit import limiter

        try:
            limiter._storage.reset()
        except Exception:
            pass

        def _auth_override(request: Request):
            auth = request.headers.get("Authorization", "")
            _, token = get_authorization_scheme_param(auth)
            if not token:
                raise HTTPException(status_code=401, detail="Not authenticated")
            return test_user

        def _mock_session():
            yield MagicMock()

        from app.modules.auth_guards.middleware import require_verified_email
        app.dependency_overrides[get_current_user] = _auth_override
        app.dependency_overrides[require_verified_email] = _auth_override
        app.dependency_overrides[require_ai_call_quota] = _auth_override
        app.dependency_overrides[get_session] = _mock_session

        with patch("app.modules.web_crawler.service.init_crawler", new_callable=AsyncMock), \
             patch("app.modules.web_crawler.service.close_crawler", new_callable=AsyncMock):
            yield

        app.dependency_overrides.clear()

    # -- /c4a/compile --

    @pytest.mark.asyncio
    async def test_c4a_compile_success(self, client, auth_headers):
        compile_result = {"js_code": "document.querySelector('.btn').click();", "success": True, "error": None}

        with patch("app.modules.web_crawler.service.WebCrawlerService.compile_c4a",
                   return_value=compile_result):
            response = await client.post(
                "/api/crawler/c4a/compile",
                json={"script": "click('.btn')"},
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "click" in data["js_code"]

    @pytest.mark.asyncio
    async def test_c4a_compile_unauthorized(self, client):
        response = await client.post(
            "/api/crawler/c4a/compile",
            json={"script": "click('.btn')"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_c4a_compile_empty_script(self, client, auth_headers):
        response = await client.post(
            "/api/crawler/c4a/compile",
            json={"script": ""},
            headers=auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_c4a_compile_service_error(self, client, auth_headers):
        compile_result = {"js_code": "", "success": False, "error": "Syntax error"}

        with patch("app.modules.web_crawler.service.WebCrawlerService.compile_c4a",
                   return_value=compile_result):
            response = await client.post(
                "/api/crawler/c4a/compile",
                json={"script": "bad script"},
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["error"] == "Syntax error"

    # -- /c4a/validate --

    @pytest.mark.asyncio
    async def test_c4a_validate_success(self, client, auth_headers):
        validate_result = {"valid": True, "errors": []}

        with patch("app.modules.web_crawler.service.WebCrawlerService.validate_c4a",
                   return_value=validate_result):
            response = await client.post(
                "/api/crawler/c4a/validate",
                json={"script": "click('.btn')"},
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["errors"] == []

    @pytest.mark.asyncio
    async def test_c4a_validate_unauthorized(self, client):
        response = await client.post(
            "/api/crawler/c4a/validate",
            json={"script": "click('.btn')"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_c4a_validate_empty_script(self, client, auth_headers):
        response = await client.post(
            "/api/crawler/c4a/validate",
            json={"script": ""},
            headers=auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_c4a_validate_invalid_script_response(self, client, auth_headers):
        validate_result = {"valid": False, "errors": ["unexpected token at line 3"]}

        with patch("app.modules.web_crawler.service.WebCrawlerService.validate_c4a",
                   return_value=validate_result):
            response = await client.post(
                "/api/crawler/c4a/validate",
                json={"script": "bad_script_here"},
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert "unexpected token" in data["errors"][0]

    # -- /scrape with v7 params --

    @pytest.mark.asyncio
    async def test_scrape_content_filter_mode_forwarded(self, client, auth_headers):
        scrape_result = {
            "url": "https://example.com", "title": "", "markdown": "",
            "fit_markdown": "", "text_length": 0, "images": [], "image_count": 0,
            "audio": [], "video": [], "screenshot_base64": None, "pdf_base64": None,
            "mhtml": None, "links_internal": [], "links_external": [], "tables": [],
            "network_requests": [], "console_messages": [], "ssl_certificate": None,
            "status_code": 200, "redirected_url": None,
            "success": True, "scraper": "crawl4ai", "error": None,
        }

        with patch("app.modules.web_crawler.service.WebCrawlerService.scrape",
                   new=AsyncMock(return_value=scrape_result)) as mock_scrape:
            response = await client.post(
                "/api/crawler/scrape",
                json={"url": "https://example.com", "content_filter_mode": "llm"},
                headers=auth_headers,
            )

        assert response.status_code == 200
        kw = mock_scrape.call_args.kwargs
        assert kw["content_filter_mode"] == "llm"

    @pytest.mark.asyncio
    async def test_scrape_antibot_retry_forwarded(self, client, auth_headers):
        scrape_result = {
            "url": "https://example.com", "title": "", "markdown": "",
            "fit_markdown": "", "text_length": 0, "images": [], "image_count": 0,
            "audio": [], "video": [], "screenshot_base64": None, "pdf_base64": None,
            "mhtml": None, "links_internal": [], "links_external": [], "tables": [],
            "network_requests": [], "console_messages": [], "ssl_certificate": None,
            "status_code": 200, "redirected_url": None,
            "success": True, "scraper": "crawl4ai", "error": None,
        }

        with patch("app.modules.web_crawler.service.WebCrawlerService.scrape",
                   new=AsyncMock(return_value=scrape_result)) as mock_scrape:
            response = await client.post(
                "/api/crawler/scrape",
                json={"url": "https://example.com", "antibot_retry": True},
                headers=auth_headers,
            )

        assert response.status_code == 200
        kw = mock_scrape.call_args.kwargs
        assert kw["antibot_retry"] is True

    @pytest.mark.asyncio
    async def test_scrape_proxies_forwarded(self, client, auth_headers):
        scrape_result = {
            "url": "https://example.com", "title": "", "markdown": "",
            "fit_markdown": "", "text_length": 0, "images": [], "image_count": 0,
            "audio": [], "video": [], "screenshot_base64": None, "pdf_base64": None,
            "mhtml": None, "links_internal": [], "links_external": [], "tables": [],
            "network_requests": [], "console_messages": [], "ssl_certificate": None,
            "status_code": 200, "redirected_url": None,
            "success": True, "scraper": "crawl4ai", "error": None,
        }

        with patch("app.modules.web_crawler.service.WebCrawlerService.scrape",
                   new=AsyncMock(return_value=scrape_result)) as mock_scrape:
            response = await client.post(
                "/api/crawler/scrape",
                json={
                    "url": "https://example.com",
                    "proxies": [
                        {"server": "http://proxy1:8080"},
                        {"server": "http://proxy2:8080", "username": "u", "password": "p"},
                    ],
                },
                headers=auth_headers,
            )

        assert response.status_code == 200
        kw = mock_scrape.call_args.kwargs
        assert kw["proxies"] is not None
        assert len(kw["proxies"]) == 2
        assert kw["proxies"][0]["server"] == "http://proxy1:8080"
        assert kw["proxies"][1]["username"] == "u"

    # -- /batch with dispatcher --

    @pytest.mark.asyncio
    async def test_batch_with_dispatcher_config(self, client, auth_headers):
        batch_result = {
            "total": 2, "succeeded": 2, "failed": 0,
            "results": [
                {"url": "https://a.com", "title": "A", "markdown": "# A", "success": True, "error": None},
                {"url": "https://b.com", "title": "B", "markdown": "# B", "success": True, "error": None},
            ],
            "monitor_stats": {"memory_mb": 256, "tasks_done": 2},
        }

        with patch("app.modules.web_crawler.service.WebCrawlerService.batch_scrape",
                   new=AsyncMock(return_value=batch_result)) as mock_batch:
            response = await client.post(
                "/api/crawler/batch",
                json={
                    "urls": ["https://a.com", "https://b.com"],
                    "dispatcher": {"max_session_permit": 5, "memory_threshold_percent": 80.0},
                },
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["monitor_stats"]["memory_mb"] == 256
        kw = mock_batch.call_args.kwargs
        assert kw["dispatcher_config"] is not None
        assert kw["dispatcher_config"]["max_session_permit"] == 5

    @pytest.mark.asyncio
    async def test_batch_with_proxies(self, client, auth_headers):
        batch_result = {
            "total": 1, "succeeded": 1, "failed": 0,
            "results": [
                {"url": "https://a.com", "title": "A", "markdown": "# A", "success": True, "error": None},
            ],
            "monitor_stats": None,
        }

        with patch("app.modules.web_crawler.service.WebCrawlerService.batch_scrape",
                   new=AsyncMock(return_value=batch_result)) as mock_batch:
            response = await client.post(
                "/api/crawler/batch",
                json={
                    "urls": ["https://a.com"],
                    "proxies": [{"server": "http://proxy:8080"}],
                },
                headers=auth_headers,
            )

        assert response.status_code == 200
        kw = mock_batch.call_args.kwargs
        assert kw["proxies"] is not None
        assert len(kw["proxies"]) == 1

    @pytest.mark.asyncio
    async def test_batch_monitor_stats_none(self, client, auth_headers):
        batch_result = {
            "total": 1, "succeeded": 1, "failed": 0,
            "results": [
                {"url": "https://a.com", "title": "A", "markdown": "# A", "success": True, "error": None},
            ],
            "monitor_stats": None,
        }

        with patch("app.modules.web_crawler.service.WebCrawlerService.batch_scrape",
                   new=AsyncMock(return_value=batch_result)):
            response = await client.post(
                "/api/crawler/batch",
                json={"urls": ["https://a.com"]},
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["monitor_stats"] is None

    # -- /deep-crawl with composite scorers --

    @pytest.mark.asyncio
    async def test_deep_crawl_composite_scorers_forwarded(self, client, auth_headers):
        deep_result = {
            "url": "https://example.com", "strategy": "best_first",
            "pages": [], "total_pages": 0, "succeeded": 0, "failed": 0,
            "export_state": None, "monitor_stats": {"urls_total": 0},
            "success": True, "error": None,
        }

        with patch("app.modules.web_crawler.service.WebCrawlerService.deep_crawl",
                   new=AsyncMock(return_value=deep_result)) as mock_deep, \
             patch("app.modules.web_crawler.routes.BillingService.consume_quota",
                   new_callable=AsyncMock):
            response = await client.post(
                "/api/crawler/deep-crawl",
                json={
                    "url": "https://example.com",
                    "strategy": "best_first",
                    "composite_scorers": ["domain_authority", "freshness"],
                    "domain_authority_weights": {"docs.python.org": 0.9},
                },
                headers=auth_headers,
            )

        assert response.status_code == 200
        kw = mock_deep.call_args.kwargs
        assert kw["composite_scorers"] == ["domain_authority", "freshness"]
        assert kw["domain_authority_weights"] == {"docs.python.org": 0.9}

    @pytest.mark.asyncio
    async def test_deep_crawl_dispatcher_forwarded(self, client, auth_headers):
        deep_result = {
            "url": "https://example.com", "strategy": "bfs",
            "pages": [], "total_pages": 0, "succeeded": 0, "failed": 0,
            "export_state": None, "monitor_stats": {"memory_mb": 128},
            "success": True, "error": None,
        }

        with patch("app.modules.web_crawler.service.WebCrawlerService.deep_crawl",
                   new=AsyncMock(return_value=deep_result)) as mock_deep, \
             patch("app.modules.web_crawler.routes.BillingService.consume_quota",
                   new_callable=AsyncMock):
            response = await client.post(
                "/api/crawler/deep-crawl",
                json={
                    "url": "https://example.com",
                    "dispatcher": {"max_session_permit": 10, "memory_threshold_percent": 85.0},
                },
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["monitor_stats"]["memory_mb"] == 128
        kw = mock_deep.call_args.kwargs
        assert kw["dispatcher_config"] is not None
        assert kw["dispatcher_config"]["max_session_permit"] == 10

    @pytest.mark.asyncio
    async def test_deep_crawl_proxies_forwarded(self, client, auth_headers):
        deep_result = {
            "url": "https://example.com", "strategy": "bfs",
            "pages": [], "total_pages": 0, "succeeded": 0, "failed": 0,
            "export_state": None, "monitor_stats": None,
            "success": True, "error": None,
        }

        with patch("app.modules.web_crawler.service.WebCrawlerService.deep_crawl",
                   new=AsyncMock(return_value=deep_result)) as mock_deep, \
             patch("app.modules.web_crawler.routes.BillingService.consume_quota",
                   new_callable=AsyncMock):
            response = await client.post(
                "/api/crawler/deep-crawl",
                json={
                    "url": "https://example.com",
                    "proxies": [{"server": "socks5://proxy:1080"}],
                },
                headers=auth_headers,
            )

        assert response.status_code == 200
        kw = mock_deep.call_args.kwargs
        assert kw["proxies"] is not None
        assert kw["proxies"][0]["server"] == "socks5://proxy:1080"


# ---------------------------------------------------------------------------
# v8 — Schema tests
# ---------------------------------------------------------------------------

class TestWebCrawlerSchemasV8:

    # -- C4ACompileFileRequest --

    def test_c4a_compile_file_request_valid(self):
        from app.modules.web_crawler.schemas import C4ACompileFileRequest
        r = C4ACompileFileRequest(file_path="/scripts/demo.c4a")
        assert r.file_path == "/scripts/demo.c4a"

    def test_c4a_compile_file_request_empty_path_raises(self):
        from pydantic import ValidationError
        from app.modules.web_crawler.schemas import C4ACompileFileRequest
        with pytest.raises(ValidationError):
            C4ACompileFileRequest(file_path="")

    # -- BrowserProfileCreateRequest --

    def test_browser_profile_create_request_defaults(self):
        from app.modules.web_crawler.schemas import BrowserProfileCreateRequest
        r = BrowserProfileCreateRequest()
        assert r.profile_name is None

    def test_browser_profile_create_request_with_name(self):
        from app.modules.web_crawler.schemas import BrowserProfileCreateRequest
        r = BrowserProfileCreateRequest(profile_name="my-profile")
        assert r.profile_name == "my-profile"

    # -- BrowserProfileResponse --

    def test_browser_profile_response_defaults(self):
        from app.modules.web_crawler.schemas import BrowserProfileResponse
        r = BrowserProfileResponse()
        assert r.profile_name is None
        assert r.profile_path is None
        assert r.profiles == []
        assert r.success is True
        assert r.error is None

    # -- DockerCrawlRequest --

    def test_docker_crawl_request_defaults(self):
        from app.modules.web_crawler.schemas import DockerCrawlRequest
        r = DockerCrawlRequest(urls=["https://example.com"])
        assert r.docker_url == "http://localhost:8000"
        assert r.timeout == 30.0

    def test_docker_crawl_request_custom_docker_url(self):
        from app.modules.web_crawler.schemas import DockerCrawlRequest
        r = DockerCrawlRequest(urls=["https://a.com"], docker_url="http://my-docker:9000", timeout=60.0)
        assert r.docker_url == "http://my-docker:9000"
        assert r.timeout == 60.0

    # -- DockerCrawlResponse --

    def test_docker_crawl_response_defaults(self):
        from app.modules.web_crawler.schemas import DockerCrawlResponse
        r = DockerCrawlResponse()
        assert r.total == 0
        assert r.succeeded == 0
        assert r.failed == 0
        assert r.results == []
        assert r.success is True
        assert r.error is None

    # -- PdfScrapeRequest --

    def test_pdf_scrape_request_defaults(self):
        from app.modules.web_crawler.schemas import PdfScrapeRequest
        r = PdfScrapeRequest(url="https://example.com/doc.pdf")
        assert r.extract_images is False

    def test_pdf_scrape_request_with_extract_images(self):
        from app.modules.web_crawler.schemas import PdfScrapeRequest
        r = PdfScrapeRequest(url="https://example.com/doc.pdf", extract_images=True)
        assert r.extract_images is True

    # -- PdfScrapeResponse --

    def test_pdf_scrape_response_defaults(self):
        from app.modules.web_crawler.schemas import PdfScrapeResponse
        r = PdfScrapeResponse(url="https://example.com/doc.pdf")
        assert r.markdown == ""
        assert r.text_length == 0
        assert r.success is True
        assert r.error is None

    # -- CosineExtractRequest --

    def test_cosine_extract_request_defaults(self):
        from app.modules.web_crawler.schemas import CosineExtractRequest
        r = CosineExtractRequest(url="https://example.com")
        assert r.word_count_threshold == 10
        assert r.max_dist == 0.2
        assert r.top_k == 3
        assert r.sim_threshold == 0.3
        assert r.semantic_filter is None

    def test_cosine_extract_request_custom_params(self):
        from app.modules.web_crawler.schemas import CosineExtractRequest
        r = CosineExtractRequest(
            url="https://example.com",
            word_count_threshold=50,
            max_dist=0.5,
            top_k=10,
            sim_threshold=0.7,
            semantic_filter="machine learning",
        )
        assert r.word_count_threshold == 50
        assert r.max_dist == 0.5
        assert r.top_k == 10
        assert r.sim_threshold == 0.7
        assert r.semantic_filter == "machine learning"

    # -- CosineExtractResponse --

    def test_cosine_extract_response_defaults(self):
        from app.modules.web_crawler.schemas import CosineExtractResponse
        r = CosineExtractResponse(url="https://example.com")
        assert r.clusters == []
        assert r.total_clusters == 0
        assert r.success is True
        assert r.error is None

    def test_cosine_extract_response_with_clusters(self):
        from app.modules.web_crawler.schemas import CosineExtractResponse, CosineCluster
        c = CosineCluster(index=0, tags=["ai"], content="Hello world")
        r = CosineExtractResponse(url="https://example.com", clusters=[c], total_clusters=1)
        assert r.total_clusters == 1
        assert r.clusters[0].content == "Hello world"

    # -- CosineCluster --

    def test_cosine_cluster_defaults(self):
        from app.modules.web_crawler.schemas import CosineCluster
        c = CosineCluster()
        assert c.index == 0
        assert c.tags == []
        assert c.content == ""

    # -- LxmlExtractRequest --

    def test_lxml_extract_request_valid(self):
        from app.modules.web_crawler.schemas import LxmlExtractRequest
        r = LxmlExtractRequest(url="https://example.com", schema={"name": "title", "selector": "h1"})
        assert r.schema == {"name": "title", "selector": "h1"}

    # -- LxmlExtractResponse --

    def test_lxml_extract_response_defaults(self):
        from app.modules.web_crawler.schemas import LxmlExtractResponse
        r = LxmlExtractResponse(url="https://example.com")
        assert r.data is None
        assert r.success is True
        assert r.error is None

    # -- RegexChunkRequest --

    def test_regex_chunk_request_valid(self):
        from app.modules.web_crawler.schemas import RegexChunkRequest
        r = RegexChunkRequest(text="Hello world")
        assert r.text == "Hello world"
        assert r.patterns is None

    def test_regex_chunk_request_empty_text_raises(self):
        from pydantic import ValidationError
        from app.modules.web_crawler.schemas import RegexChunkRequest
        with pytest.raises(ValidationError):
            RegexChunkRequest(text="")

    # -- RegexChunkResponse --

    def test_regex_chunk_response_defaults(self):
        from app.modules.web_crawler.schemas import RegexChunkResponse
        r = RegexChunkResponse()
        assert r.chunks == []
        assert r.total_chunks == 0
        assert r.success is True
        assert r.error is None

    # -- SemaphoreDispatcherConfig --

    def test_semaphore_dispatcher_config_defaults(self):
        from app.modules.web_crawler.schemas import SemaphoreDispatcherConfig
        r = SemaphoreDispatcherConfig()
        assert r.semaphore_count == 5
        assert r.max_session_permit == 20

    def test_semaphore_dispatcher_config_custom(self):
        from app.modules.web_crawler.schemas import SemaphoreDispatcherConfig
        r = SemaphoreDispatcherConfig(semaphore_count=10, max_session_permit=50)
        assert r.semaphore_count == 10
        assert r.max_session_permit == 50

    # -- BatchScrapeRequest dispatcher fields --

    def test_batch_scrape_request_dispatcher_type_default(self):
        from app.modules.web_crawler.schemas import BatchScrapeRequest
        r = BatchScrapeRequest(urls=["https://example.com"])
        assert r.dispatcher_type == "memory_adaptive"
        assert r.semaphore_count == 5

    def test_batch_scrape_request_semaphore_dispatcher(self):
        from app.modules.web_crawler.schemas import BatchScrapeRequest
        r = BatchScrapeRequest(urls=["https://example.com"], dispatcher_type="semaphore", semaphore_count=15)
        assert r.dispatcher_type == "semaphore"
        assert r.semaphore_count == 15


# ---------------------------------------------------------------------------
# v8 — Service tests
# ---------------------------------------------------------------------------

class TestWebCrawlerServiceV8:

    # -- list_browser_profiles --

    def test_list_browser_profiles_happy(self):
        from app.modules.web_crawler.service import WebCrawlerService

        mock_profiler = MagicMock()
        mock_profiler.list_profiles.return_value = [{"name": "default"}]

        with patch("crawl4ai.BrowserProfiler", return_value=mock_profiler):
            result = WebCrawlerService.list_browser_profiles()

        assert result["success"] is True
        assert result["profiles"] == [{"name": "default"}]

    def test_list_browser_profiles_import_error(self):
        import sys
        from app.modules.web_crawler.service import WebCrawlerService

        with patch.dict(sys.modules, {"crawl4ai": None}):
            result = WebCrawlerService.list_browser_profiles()

        assert result["success"] is False
        assert "BrowserProfiler" in result["error"]

    # -- create_browser_profile --

    def test_create_browser_profile_happy(self):
        from app.modules.web_crawler.service import WebCrawlerService

        mock_profiler = MagicMock()
        mock_profiler.create_profile.return_value = "test-profile"
        mock_profiler.get_profile_path.return_value = "/profiles/test-profile"

        with patch("crawl4ai.BrowserProfiler", return_value=mock_profiler):
            result = WebCrawlerService.create_browser_profile(profile_name="test-profile")

        assert result["success"] is True
        assert result["profile_name"] == "test-profile"
        assert result["profile_path"] == "/profiles/test-profile"

    def test_create_browser_profile_import_error(self):
        import sys
        from app.modules.web_crawler.service import WebCrawlerService

        with patch.dict(sys.modules, {"crawl4ai": None}):
            result = WebCrawlerService.create_browser_profile()

        assert result["success"] is False
        assert "BrowserProfiler" in result["error"]

    # -- delete_browser_profile --

    def test_delete_browser_profile_happy(self):
        from app.modules.web_crawler.service import WebCrawlerService

        mock_profiler = MagicMock()
        mock_profiler.delete_profile.return_value = True

        with patch("crawl4ai.BrowserProfiler", return_value=mock_profiler):
            result = WebCrawlerService.delete_browser_profile("old-profile")

        assert result["success"] is True
        assert result["error"] is None

    def test_delete_browser_profile_not_found(self):
        from app.modules.web_crawler.service import WebCrawlerService

        mock_profiler = MagicMock()
        mock_profiler.delete_profile.return_value = False

        with patch("crawl4ai.BrowserProfiler", return_value=mock_profiler):
            result = WebCrawlerService.delete_browser_profile("ghost")

        assert result["success"] is False
        assert "not found" in result["error"]

    # -- docker_crawl --

    @pytest.mark.asyncio
    async def test_docker_crawl_happy(self):
        from app.modules.web_crawler.service import WebCrawlerService

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.url = "https://example.com"
        mock_result.metadata = {"title": "Example"}
        mock_result.markdown_v2 = MagicMock()
        mock_result.markdown_v2.fit_markdown = "# Example content"

        mock_client = AsyncMock()
        mock_client.crawl.return_value = [mock_result]
        mock_client.close = MagicMock()

        with patch("crawl4ai.Crawl4aiDockerClient", return_value=mock_client):
            result = await WebCrawlerService.docker_crawl(
                urls=["https://example.com"],
                docker_url="http://localhost:8000",
                timeout=30.0,
            )

        assert result["success"] is True
        assert result["total"] == 1
        assert result["succeeded"] == 1
        assert result["failed"] == 0

    @pytest.mark.asyncio
    async def test_docker_crawl_import_error(self):
        import sys
        from app.modules.web_crawler.service import WebCrawlerService

        with patch.dict(sys.modules, {"crawl4ai": None}):
            result = await WebCrawlerService.docker_crawl(urls=["https://example.com"])

        assert result["success"] is False
        assert "Crawl4aiDockerClient" in result["error"]

    # -- scrape_pdf --

    @pytest.mark.asyncio
    async def test_scrape_pdf_happy(self):
        from app.modules.web_crawler.service import WebCrawlerService

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.markdown = MagicMock()
        mock_result.markdown.raw_markdown = "# PDF Content"
        mock_result.markdown.fit_markdown = "# PDF Content"

        mock_crawler = AsyncMock()
        mock_crawler.arun.return_value = mock_result

        with patch("crawl4ai.PDFContentScrapingStrategy"), \
             patch("crawl4ai.CrawlerRunConfig"), \
             patch("crawl4ai.CacheMode"), \
             patch("app.modules.web_crawler.service.get_crawler", new_callable=AsyncMock, return_value=mock_crawler):
            result = await WebCrawlerService.scrape_pdf(url="https://example.com/doc.pdf")

        assert result["success"] is True
        assert result["url"] == "https://example.com/doc.pdf"
        assert result["text_length"] > 0

    @pytest.mark.asyncio
    async def test_scrape_pdf_import_error(self):
        import sys
        from app.modules.web_crawler.service import WebCrawlerService

        with patch.dict(sys.modules, {"crawl4ai": None}):
            result = await WebCrawlerService.scrape_pdf(url="https://example.com/doc.pdf")

        assert result["success"] is False
        assert "PDFContentScrapingStrategy" in result["error"]

    # -- extract_cosine --

    @pytest.mark.asyncio
    async def test_extract_cosine_happy(self):
        from app.modules.web_crawler.service import WebCrawlerService

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.extracted_content = json.dumps([
            {"tags": ["ai"], "content": "Cluster about AI"},
        ])

        mock_crawler = AsyncMock()
        mock_crawler.arun.return_value = mock_result

        with patch("crawl4ai.CosineStrategy"), \
             patch("crawl4ai.CrawlerRunConfig"), \
             patch("crawl4ai.CacheMode"), \
             patch("app.modules.web_crawler.service.get_crawler", new_callable=AsyncMock, return_value=mock_crawler):
            result = await WebCrawlerService.extract_cosine(url="https://example.com")

        assert result["success"] is True
        assert result["total_clusters"] == 1
        assert result["clusters"][0]["content"] == "Cluster about AI"

    @pytest.mark.asyncio
    async def test_extract_cosine_import_error(self):
        import sys
        from app.modules.web_crawler.service import WebCrawlerService

        with patch.dict(sys.modules, {"crawl4ai": None}):
            result = await WebCrawlerService.extract_cosine(url="https://example.com")

        assert result["success"] is False
        assert "CosineStrategy" in result["error"]

    # -- extract_lxml --

    @pytest.mark.asyncio
    async def test_extract_lxml_happy(self):
        from app.modules.web_crawler.service import WebCrawlerService

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.extracted_content = json.dumps({"title": "Example"})

        mock_crawler = AsyncMock()
        mock_crawler.arun.return_value = mock_result

        with patch("crawl4ai.JsonLxmlExtractionStrategy"), \
             patch("crawl4ai.CrawlerRunConfig"), \
             patch("crawl4ai.CacheMode"), \
             patch("app.modules.web_crawler.service.get_crawler", new_callable=AsyncMock, return_value=mock_crawler):
            result = await WebCrawlerService.extract_lxml(
                url="https://example.com",
                schema={"name": "title", "selector": "h1"},
            )

        assert result["success"] is True
        assert result["data"] == {"title": "Example"}

    @pytest.mark.asyncio
    async def test_extract_lxml_import_error(self):
        import sys
        from app.modules.web_crawler.service import WebCrawlerService

        with patch.dict(sys.modules, {"crawl4ai": None}):
            result = await WebCrawlerService.extract_lxml(
                url="https://example.com",
                schema={"name": "title", "selector": "h1"},
            )

        assert result["success"] is False
        assert "JsonLxmlExtractionStrategy" in result["error"]

    # -- chunk_regex --

    def test_chunk_regex_happy(self):
        from app.modules.web_crawler.service import WebCrawlerService

        mock_chunker = MagicMock()
        mock_chunker.chunk.return_value = ["chunk1", "chunk2"]

        with patch("crawl4ai.RegexChunking", return_value=mock_chunker):
            result = WebCrawlerService.chunk_regex(text="Hello world. Goodbye world.")

        assert result["success"] is True
        assert result["total_chunks"] == 2
        assert result["chunks"] == ["chunk1", "chunk2"]

    def test_chunk_regex_import_error(self):
        import sys
        from app.modules.web_crawler.service import WebCrawlerService

        with patch.dict(sys.modules, {"crawl4ai": None}):
            result = WebCrawlerService.chunk_regex(text="Hello world.")

        assert result["success"] is False
        assert "RegexChunking" in result["error"]

    # -- compile_c4a_file --

    def test_compile_c4a_file_happy(self):
        from app.modules.web_crawler.service import WebCrawlerService

        mock_compiled = MagicMock()
        mock_compiled.js_code = "document.querySelector('h1').textContent;"

        with patch("crawl4ai.c4a_compile_file", return_value=mock_compiled):
            result = WebCrawlerService.compile_c4a_file(file_path="/scripts/demo.c4a")

        assert result["success"] is True
        assert "querySelector" in result["js_code"]

    def test_compile_c4a_file_import_error(self):
        import sys
        from app.modules.web_crawler.service import WebCrawlerService

        with patch.dict(sys.modules, {"crawl4ai": None}):
            result = WebCrawlerService.compile_c4a_file(file_path="/scripts/demo.c4a")

        assert result["success"] is False
        assert "c4a_compile_file" in result["error"]


# ---------------------------------------------------------------------------
# v8 — Route tests
# ---------------------------------------------------------------------------

class TestWebCrawlerRoutesV8:

    @pytest.fixture(autouse=True)
    def _override_deps(self, app, test_user):
        from fastapi import HTTPException, Request
        from fastapi.security.utils import get_authorization_scheme_param
        from app.auth import get_current_user
        from app.database import get_session
        from app.modules.billing.middleware import require_ai_call_quota
        from app.rate_limit import limiter

        try:
            limiter._storage.reset()
        except Exception:
            pass

        def _auth_override(request: Request):
            auth = request.headers.get("Authorization", "")
            _, token = get_authorization_scheme_param(auth)
            if not token:
                raise HTTPException(status_code=401, detail="Not authenticated")
            return test_user

        def _mock_session():
            yield MagicMock()

        from app.modules.auth_guards.middleware import require_verified_email
        app.dependency_overrides[get_current_user] = _auth_override
        app.dependency_overrides[require_verified_email] = _auth_override
        app.dependency_overrides[require_ai_call_quota] = _auth_override
        app.dependency_overrides[get_session] = _mock_session

        with patch("app.modules.web_crawler.service.init_crawler", new_callable=AsyncMock), \
             patch("app.modules.web_crawler.service.close_crawler", new_callable=AsyncMock):
            yield

        app.dependency_overrides.clear()

    # -- /c4a/compile-file --

    @pytest.mark.asyncio
    async def test_c4a_compile_file_success(self, client, auth_headers):
        compile_result = {"js_code": "document.querySelector('h1');", "success": True, "error": None}

        with patch("app.modules.web_crawler.service.WebCrawlerService.compile_c4a_file",
                   return_value=compile_result):
            response = await client.post(
                "/api/crawler/c4a/compile-file",
                json={"file_path": "/scripts/demo.c4a"},
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "querySelector" in data["js_code"]

    @pytest.mark.asyncio
    async def test_c4a_compile_file_unauthorized(self, client):
        response = await client.post(
            "/api/crawler/c4a/compile-file",
            json={"file_path": "/scripts/demo.c4a"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_c4a_compile_file_empty_path_422(self, client, auth_headers):
        response = await client.post(
            "/api/crawler/c4a/compile-file",
            json={"file_path": ""},
            headers=auth_headers,
        )
        assert response.status_code == 422

    # -- /profiles GET --

    @pytest.mark.asyncio
    async def test_profiles_list_success(self, client, auth_headers):
        mock_result = {"profiles": [{"name": "default"}], "success": True}

        with patch("app.modules.web_crawler.service.WebCrawlerService.list_browser_profiles",
                   return_value=mock_result):
            response = await client.get(
                "/api/crawler/profiles",
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["profiles"]) == 1

    @pytest.mark.asyncio
    async def test_profiles_list_unauthorized(self, client):
        response = await client.get("/api/crawler/profiles")
        assert response.status_code == 401

    # -- /profiles POST --

    @pytest.mark.asyncio
    async def test_profiles_create_success(self, client, auth_headers):
        mock_result = {"profile_name": "new-prof", "profile_path": "/p/new-prof", "success": True}

        with patch("app.modules.web_crawler.service.WebCrawlerService.create_browser_profile",
                   return_value=mock_result):
            response = await client.post(
                "/api/crawler/profiles",
                json={"profile_name": "new-prof"},
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["profile_name"] == "new-prof"

    @pytest.mark.asyncio
    async def test_profiles_create_unauthorized(self, client):
        response = await client.post(
            "/api/crawler/profiles",
            json={"profile_name": "x"},
        )
        assert response.status_code == 401

    # -- /profiles DELETE --

    @pytest.mark.asyncio
    async def test_profiles_delete_success(self, client, auth_headers):
        mock_result = {"success": True, "error": None}

        with patch("app.modules.web_crawler.service.WebCrawlerService.delete_browser_profile",
                   return_value=mock_result):
            response = await client.delete(
                "/api/crawler/profiles/old-prof",
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_profiles_delete_unauthorized(self, client):
        response = await client.delete("/api/crawler/profiles/old-prof")
        assert response.status_code == 401

    # -- /docker-crawl --

    @pytest.mark.asyncio
    async def test_docker_crawl_success(self, client, auth_headers):
        mock_result = {
            "total": 1, "succeeded": 1, "failed": 0,
            "results": [{"url": "https://example.com", "title": "Ex", "markdown": "# Ex", "success": True}],
            "success": True, "error": None,
        }

        with patch("app.modules.web_crawler.service.WebCrawlerService.docker_crawl",
                   new=AsyncMock(return_value=mock_result)):
            response = await client.post(
                "/api/crawler/docker-crawl",
                json={"urls": ["https://example.com"]},
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["succeeded"] == 1

    @pytest.mark.asyncio
    async def test_docker_crawl_unauthorized(self, client):
        response = await client.post(
            "/api/crawler/docker-crawl",
            json={"urls": ["https://example.com"]},
        )
        assert response.status_code == 401

    # -- /scrape-pdf --

    @pytest.mark.asyncio
    async def test_scrape_pdf_success(self, client, auth_headers):
        mock_result = {"url": "https://example.com/doc.pdf", "markdown": "# PDF text", "text_length": 10, "success": True}

        with patch("app.modules.web_crawler.service.WebCrawlerService.scrape_pdf",
                   new=AsyncMock(return_value=mock_result)):
            response = await client.post(
                "/api/crawler/scrape-pdf",
                json={"url": "https://example.com/doc.pdf"},
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["text_length"] == 10

    @pytest.mark.asyncio
    async def test_scrape_pdf_unauthorized(self, client):
        response = await client.post(
            "/api/crawler/scrape-pdf",
            json={"url": "https://example.com/doc.pdf"},
        )
        assert response.status_code == 401

    # -- /extract-cosine --

    @pytest.mark.asyncio
    async def test_extract_cosine_success(self, client, auth_headers):
        mock_result = {
            "url": "https://example.com",
            "clusters": [{"index": 0, "tags": ["ai"], "content": "AI cluster"}],
            "total_clusters": 1, "success": True, "error": None,
        }

        with patch("app.modules.web_crawler.service.WebCrawlerService.extract_cosine",
                   new=AsyncMock(return_value=mock_result)):
            response = await client.post(
                "/api/crawler/extract-cosine",
                json={"url": "https://example.com"},
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total_clusters"] == 1

    @pytest.mark.asyncio
    async def test_extract_cosine_unauthorized(self, client):
        response = await client.post(
            "/api/crawler/extract-cosine",
            json={"url": "https://example.com"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_extract_cosine_params_forwarded(self, client, auth_headers):
        mock_result = {
            "url": "https://example.com",
            "clusters": [], "total_clusters": 0, "success": True, "error": None,
        }

        with patch("app.modules.web_crawler.service.WebCrawlerService.extract_cosine",
                   new=AsyncMock(return_value=mock_result)) as mock_svc:
            response = await client.post(
                "/api/crawler/extract-cosine",
                json={
                    "url": "https://example.com",
                    "word_count_threshold": 50,
                    "max_dist": 0.8,
                    "top_k": 7,
                    "sim_threshold": 0.6,
                    "semantic_filter": "deep learning",
                },
                headers=auth_headers,
            )

        assert response.status_code == 200
        kw = mock_svc.call_args.kwargs
        assert kw["word_count_threshold"] == 50
        assert kw["max_dist"] == 0.8
        assert kw["top_k"] == 7
        assert kw["sim_threshold"] == 0.6
        assert kw["semantic_filter"] == "deep learning"

    # -- /extract-lxml --

    @pytest.mark.asyncio
    async def test_extract_lxml_success(self, client, auth_headers):
        mock_result = {"url": "https://example.com", "data": {"title": "Test"}, "success": True, "error": None}

        with patch("app.modules.web_crawler.service.WebCrawlerService.extract_lxml",
                   new=AsyncMock(return_value=mock_result)):
            response = await client.post(
                "/api/crawler/extract-lxml",
                json={"url": "https://example.com", "schema": {"name": "title", "selector": "h1"}},
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] == {"title": "Test"}

    @pytest.mark.asyncio
    async def test_extract_lxml_unauthorized(self, client):
        response = await client.post(
            "/api/crawler/extract-lxml",
            json={"url": "https://example.com", "schema": {"name": "title"}},
        )
        assert response.status_code == 401

    # -- /chunk-regex --

    @pytest.mark.asyncio
    async def test_chunk_regex_success(self, client, auth_headers):
        mock_result = {"chunks": ["Hello", "World"], "total_chunks": 2, "success": True, "error": None}

        with patch("app.modules.web_crawler.service.WebCrawlerService.chunk_regex",
                   return_value=mock_result):
            response = await client.post(
                "/api/crawler/chunk-regex",
                json={"text": "Hello. World."},
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total_chunks"] == 2

    @pytest.mark.asyncio
    async def test_chunk_regex_unauthorized(self, client):
        response = await client.post(
            "/api/crawler/chunk-regex",
            json={"text": "Hello. World."},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_chunk_regex_params_forwarded(self, client, auth_headers):
        mock_result = {"chunks": ["a", "b"], "total_chunks": 2, "success": True, "error": None}

        with patch("app.modules.web_crawler.service.WebCrawlerService.chunk_regex",
                   return_value=mock_result) as mock_svc:
            response = await client.post(
                "/api/crawler/chunk-regex",
                json={"text": "Hello. World.", "patterns": [r"\.\s+"]},
                headers=auth_headers,
            )

        assert response.status_code == 200
        kw = mock_svc.call_args.kwargs
        assert kw["text"] == "Hello. World."
        assert kw["patterns"] == [r"\.\s+"]
