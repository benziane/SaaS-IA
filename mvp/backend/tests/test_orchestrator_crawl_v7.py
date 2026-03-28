"""Tests for web_crawler v7 integration in 3 orchestrators."""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

pytestmark = pytest.mark.anyio


class TestAgentExecutorCrawlV7:
    """Test batch_crawl and deep_crawl handlers in Agent Executor."""

    async def test_batch_crawl_success(self):
        mock_result = {
            "success": True,
            "results": [
                {"success": True, "title": "Page 1", "url": "https://a.com"},
                {"success": True, "title": "Page 2", "url": "https://b.com"},
                {"success": False, "url": "https://c.com", "error": "timeout"},
            ],
        }
        with patch("app.modules.web_crawler.service.WebCrawlerService.batch_scrape", new_callable=AsyncMock, return_value=mock_result):
            from app.modules.agents.executor import _exec_batch_crawl
            result = await _exec_batch_crawl({"urls": ["https://a.com", "https://b.com", "https://c.com"]}, None)
            assert result["action"] == "batch_crawl"
            assert result["successes"] == 2
            assert result["total"] == 3

    async def test_batch_crawl_no_urls(self):
        from app.modules.agents.executor import _exec_batch_crawl
        result = await _exec_batch_crawl({}, None)
        assert "error" in result
        assert "No URLs" in result["error"]

    async def test_batch_crawl_urls_from_previous(self):
        mock_result = {"success": True, "results": [{"success": True, "title": "P1", "url": "https://a.com"}]}
        with patch("app.modules.web_crawler.service.WebCrawlerService.batch_scrape", new_callable=AsyncMock, return_value=mock_result):
            from app.modules.agents.executor import _exec_batch_crawl
            result = await _exec_batch_crawl({}, "https://a.com\nhttps://b.com")
            assert result["action"] == "batch_crawl"

    async def test_deep_crawl_success(self):
        mock_result = {
            "success": True,
            "results": [
                {"title": "Home", "url": "https://example.com"},
                {"title": "About", "url": "https://example.com/about"},
            ],
        }
        with patch("app.modules.web_crawler.service.WebCrawlerService.deep_crawl", new_callable=AsyncMock, return_value=mock_result):
            from app.modules.agents.executor import _exec_deep_crawl
            result = await _exec_deep_crawl({"url": "https://example.com", "max_depth": 2}, None)
            assert result["action"] == "deep_crawl"
            assert result["pages_crawled"] == 2

    async def test_deep_crawl_no_url(self):
        from app.modules.agents.executor import _exec_deep_crawl
        result = await _exec_deep_crawl({}, None)
        assert "error" in result

    async def test_deep_crawl_invalid_url(self):
        from app.modules.agents.executor import _exec_deep_crawl
        result = await _exec_deep_crawl({"url": "not-a-url"}, None)
        assert "error" in result


class TestPlannerCrawlV7:
    """Test batch/deep crawl in AVAILABLE_ACTIONS."""

    def test_batch_crawl_in_actions(self):
        from app.modules.agents.planner import AVAILABLE_ACTIONS
        assert "batch_crawl" in AVAILABLE_ACTIONS

    def test_deep_crawl_in_actions(self):
        from app.modules.agents.planner import AVAILABLE_ACTIONS
        assert "deep_crawl" in AVAILABLE_ACTIONS
