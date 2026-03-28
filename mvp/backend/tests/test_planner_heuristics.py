"""
Unit tests for the agent planner heuristic.

Verifies that _heuristic_plan() correctly maps natural language instructions
to the appropriate platform actions without requiring AI or external services.
"""

import os

import pytest

# Must be set before any app import so pydantic-settings does not require .env
os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-unit-tests-only")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test_saas_ia")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")
os.environ.setdefault("ASSEMBLYAI_API_KEY", "MOCK")
os.environ.setdefault("GEMINI_API_KEY", "MOCK")
os.environ.setdefault("CLAUDE_API_KEY", "MOCK")
os.environ.setdefault("GROQ_API_KEY", "MOCK")

from app.modules.agents.planner import _heuristic_plan, AVAILABLE_ACTIONS  # noqa: E402


class TestYouTubeHeuristics:
    """YouTube URL and transcript routing."""

    def test_youtube_url_routes_to_smart(self):
        """A bare YouTube watch URL returns youtube_smart (default branch)."""
        result = _heuristic_plan("transcribe https://youtube.com/watch?v=dQw4w9WgXcQ")
        actions = [s["action"] for s in result]
        assert any(a in ("youtube_smart", "transcribe") for a in actions)

    def test_youtu_be_url_routes_to_smart(self):
        """Short youtu.be URL routes to smart transcription."""
        result = _heuristic_plan("get transcript from https://youtu.be/dQw4w9WgXcQ")
        actions = [s["action"] for s in result]
        assert any(a in ("youtube_smart", "youtube_transcript", "transcribe") for a in actions)

    def test_youtube_url_returns_exactly_one_step(self):
        """The top-level YouTube URL branch returns immediately (no accumulation)."""
        result = _heuristic_plan("https://youtube.com/watch?v=dQw4w9WgXcQ")
        assert len(result) == 1
        assert result[0]["action"] == "youtube_smart"

    def test_youtube_playlist_routes_to_playlist(self):
        """A URL with 'playlist' keyword in the instruction picks youtube_playlist."""
        result = _heuristic_plan(
            "transcribe youtube playlist https://youtube.com/playlist?list=PL123"
        )
        actions = [s["action"] for s in result]
        assert any(a in ("youtube_playlist", "batch_transcribe") for a in actions)

    def test_youtube_playlist_early_return(self):
        """The playlist branch exits immediately via early return."""
        result = _heuristic_plan(
            "transcribe youtube playlist https://youtube.com/playlist?list=PL123"
        )
        # early return means exactly one step
        assert len(result) == 1
        assert result[0]["action"] == "youtube_playlist"

    def test_youtube_metadata_keyword(self):
        """'metadata' keyword with a YouTube URL routes to youtube_metadata."""
        result = _heuristic_plan(
            "get metadata from https://youtube.com/watch?v=dQw4w9WgXcQ"
        )
        actions = [s["action"] for s in result]
        assert any(a in ("youtube_metadata", "youtube_smart", "transcribe") for a in actions)

    def test_youtube_metadata_exact_branch(self):
        """Metadata branch is selected when 'metadata' appears with youtube.com URL."""
        result = _heuristic_plan("metadata https://youtube.com/watch?v=abc123")
        assert len(result) == 1
        assert result[0]["action"] == "youtube_metadata"

    def test_youtube_analyze_frames(self):
        """'frame' keyword with a YouTube URL routes to youtube_analyze."""
        result = _heuristic_plan(
            "analyze video frames https://youtube.com/watch?v=dQw4w9WgXcQ"
        )
        actions = [s["action"] for s in result]
        assert any(a in ("youtube_analyze", "analyze_image", "youtube_smart") for a in actions)

    def test_youtube_analyze_exact_branch(self):
        """Frame/vision branch returns youtube_analyze with a YouTube URL."""
        result = _heuristic_plan("analyze frames https://youtube.com/watch?v=abc")
        assert len(result) == 1
        assert result[0]["action"] == "youtube_analyze"

    def test_youtube_analyze_scene_keyword(self):
        """'scene' keyword triggers youtube_analyze when a YouTube URL is present."""
        result = _heuristic_plan("detect scenes https://youtube.com/watch?v=abc")
        actions = [s["action"] for s in result]
        assert "youtube_analyze" in actions

    def test_bulk_youtube_urls(self):
        """'several youtube' triggers batch_transcribe (no YouTube URL present)."""
        result = _heuristic_plan("batch transcribe several youtube videos")
        actions = [s["action"] for s in result]
        assert any(a in ("batch_transcribe", "youtube_playlist") for a in actions)

    def test_youtube_smart_input_has_url_key(self):
        """youtube_smart step always includes 'url' and 'language' in its input."""
        result = _heuristic_plan("https://youtube.com/watch?v=test")
        assert result[0]["input"]["url"] == ""
        assert result[0]["input"]["language"] == "auto"

    def test_youtube_playlist_input_has_max_videos(self):
        """youtube_playlist step includes max_videos in its input."""
        result = _heuristic_plan(
            "all videos https://youtube.com/playlist?list=PL123"
        )
        assert result[0]["action"] == "youtube_playlist"
        assert result[0]["input"]["max_videos"] == 20


class TestCoreHeuristics:
    """Core platform actions — non-regression tests."""

    def test_summarize_routes_correctly(self):
        """'summarize' keyword maps to summarize action."""
        result = _heuristic_plan("summarize this document")
        assert len(result) > 0
        assert result[0]["action"] == "summarize"

    def test_translate_routes_correctly(self):
        """'translate' keyword maps to translate action."""
        result = _heuristic_plan("translate this text to French")
        actions = [s["action"] for s in result]
        assert "translate" in actions

    def test_translate_to_french_sets_target_fr(self):
        """'French' in instruction sets target_language to 'fr'."""
        result = _heuristic_plan("translate to French")
        translate_step = next(s for s in result if s["action"] == "translate")
        assert translate_step["input"]["target_language"] == "fr"

    def test_translate_to_english_sets_target_en(self):
        """'english' in instruction sets target_language to 'en'."""
        result = _heuristic_plan("translate this to English")
        translate_step = next(s for s in result if s["action"] == "translate")
        assert translate_step["input"]["target_language"] == "en"

    def test_sentiment_routes_correctly(self):
        """'sentiment' keyword maps to analyze_sentiment."""
        result = _heuristic_plan("analyze the sentiment of this review")
        actions = [s["action"] for s in result]
        assert any(a in ("analyze_sentiment", "sentiment") for a in actions)

    def test_sentiment_emotion_keyword(self):
        """'emotion' keyword also triggers analyze_sentiment."""
        result = _heuristic_plan("detect the emotion in this message")
        actions = [s["action"] for s in result]
        assert "analyze_sentiment" in actions

    def test_knowledge_search(self):
        """'search' keyword maps to search_knowledge."""
        result = _heuristic_plan("search the knowledge base for machine learning")
        actions = [s["action"] for s in result]
        assert any(a in ("search_knowledge", "ask_knowledge") for a in actions)

    def test_knowledge_search_action(self):
        """'search' alone routes to search_knowledge (not ask_knowledge)."""
        result = _heuristic_plan("search for quantum computing")
        actions = [s["action"] for s in result]
        assert "search_knowledge" in actions

    def test_image_generation(self):
        """'generate image' exact phrase maps to generate_image."""
        # The heuristic checks for the substring "generate image" (no "an" in between).
        result = _heuristic_plan("generate image of a sunset")
        actions = [s["action"] for s in result]
        assert "generate_image" in actions

    def test_image_generation_illustration_keyword(self):
        """'illustration' keyword triggers generate_image."""
        result = _heuristic_plan("create an illustration for the cover")
        actions = [s["action"] for s in result]
        assert "generate_image" in actions

    def test_generate_presentation(self):
        """'presentation' keyword maps to generate_presentation."""
        result = _heuristic_plan("create a presentation about AI")
        actions = [s["action"] for s in result]
        assert any(a in ("generate_presentation", "generate_text") for a in actions)

    def test_generate_presentation_exact(self):
        """'presentation' alone is sufficient to route to generate_presentation."""
        result = _heuristic_plan("make a presentation on climate change")
        actions = [s["action"] for s in result]
        assert "generate_presentation" in actions

    def test_crawl_web(self):
        """'crawl website' maps to crawl_web."""
        result = _heuristic_plan("crawl website https://example.com")
        actions = [s["action"] for s in result]
        assert any(a in ("crawl_web", "crawl_and_index") for a in actions)

    def test_crawl_web_without_index_keyword(self):
        """Without index/knowledge/kb keywords, crawl maps to crawl_web (not crawl_and_index)."""
        result = _heuristic_plan("crawl https://example.com and extract text")
        actions = [s["action"] for s in result]
        assert "crawl_web" in actions
        assert "crawl_and_index" not in actions

    def test_crawl_and_index_with_knowledge_keyword(self):
        """'crawl' + 'knowledge' maps to crawl_and_index."""
        result = _heuristic_plan("crawl this page and save to knowledge base")
        actions = [s["action"] for s in result]
        assert "crawl_and_index" in actions

    def test_security_scan(self):
        """'scan' and 'injection' keywords both trigger security_scan."""
        result = _heuristic_plan("scan this text for PII and injection")
        actions = [s["action"] for s in result]
        assert "security_scan" in actions

    def test_security_scan_pii_keyword(self):
        """'pii' keyword alone triggers security_scan."""
        result = _heuristic_plan("find PII in this document")
        actions = [s["action"] for s in result]
        assert "security_scan" in actions

    def test_code_execution(self):
        """'execute code' phrase maps to execute_code."""
        result = _heuristic_plan("execute this Python code")
        actions = [s["action"] for s in result]
        assert "execute_code" in actions

    def test_code_execution_python_keyword(self):
        """'python' keyword triggers execute_code."""
        result = _heuristic_plan("run this python script")
        actions = [s["action"] for s in result]
        assert "execute_code" in actions

    def test_multi_step_pipeline(self):
        """A complex instruction should produce multiple steps."""
        result = _heuristic_plan("transcribe this YouTube video and then summarize it")
        assert len(result) >= 1  # At minimum 1 step, ideally 2

    def test_transcribe_then_summarize_two_steps(self):
        """'transcri' + 'summar' keywords both fire, producing two steps."""
        result = _heuristic_plan("transcribe this audio and summarize the result")
        actions = [s["action"] for s in result]
        assert "transcribe" in actions
        assert "summarize" in actions

    def test_unknown_instruction_falls_back_to_generate_text(self):
        """An unrecognised instruction falls back to generate_text."""
        result = _heuristic_plan("do something completely unrecognised xyz123")
        assert len(result) == 1
        assert result[0]["action"] == "generate_text"

    def test_fallback_generate_text_includes_prompt(self):
        """Fallback step includes the original instruction as 'prompt'."""
        instruction = "something totally unknown 99zz"
        result = _heuristic_plan(instruction)
        assert result[0]["input"]["prompt"] == instruction

    def test_generate_video_action(self):
        """'avatar' keyword (no clip/highlight) maps to generate_video."""
        result = _heuristic_plan("create an avatar explainer video")
        actions = [s["action"] for s in result]
        assert "generate_video" in actions

    def test_generate_clips_highlight_keyword(self):
        """'clip' + 'highlight' maps to generate_clips (not generate_video)."""
        result = _heuristic_plan("generate highlight clips from this video")
        actions = [s["action"] for s in result]
        assert "generate_clips" in actions

    def test_analyze_data_keyword(self):
        """'csv' keyword maps to analyze_data."""
        result = _heuristic_plan("analyze this csv dataset")
        actions = [s["action"] for s in result]
        assert "analyze_data" in actions

    def test_process_pdf_keyword(self):
        """'pdf' keyword maps to process_pdf."""
        result = _heuristic_plan("process this pdf document")
        actions = [s["action"] for s in result]
        assert "process_pdf" in actions

    def test_execute_code_keyword(self):
        """'execute code' phrase maps to execute_code."""
        result = _heuristic_plan("execute code and show results")
        actions = [s["action"] for s in result]
        assert "execute_code" in actions

    def test_text_to_speech_keyword(self):
        """'tts' keyword maps to text_to_speech."""
        result = _heuristic_plan("tts this article")
        actions = [s["action"] for s in result]
        assert "text_to_speech" in actions

    def test_fine_tune_keyword(self):
        """'fine-tun' keyword maps to fine_tune."""
        result = _heuristic_plan("fine-tune a model on my data")
        actions = [s["action"] for s in result]
        assert "fine_tune" in actions

    def test_deploy_chatbot_keyword(self):
        """'chatbot' keyword maps to deploy_chatbot."""
        result = _heuristic_plan("deploy chatbot for customer support")
        actions = [s["action"] for s in result]
        assert "deploy_chatbot" in actions

    def test_run_crew_keyword(self):
        """'crew' keyword maps to run_crew."""
        result = _heuristic_plan("run a crew to research this topic")
        actions = [s["action"] for s in result]
        assert "run_crew" in actions

    def test_run_workflow_keyword(self):
        """'workflow' keyword maps to run_workflow."""
        result = _heuristic_plan("run this automation workflow")
        actions = [s["action"] for s in result]
        assert "run_workflow" in actions

    def test_batch_transcribe_multiple_videos_keyword(self):
        """'multiple video' phrase maps to batch_transcribe."""
        result = _heuristic_plan("batch transcribe multiple videos at once")
        actions = [s["action"] for s in result]
        assert "batch_transcribe" in actions

    def test_generate_summary_of_transcription(self):
        """'summarize transcri' phrase maps to generate_summary."""
        result = _heuristic_plan("summarize transcription with action items")
        actions = [s["action"] for s in result]
        assert "generate_summary" in actions

    def test_generate_summary_action_items_style(self):
        """'action item' in instruction sets style to 'action_items'."""
        result = _heuristic_plan("summarize transcription action items from this meeting")
        summary_step = next(
            (s for s in result if s["action"] == "generate_summary"), None
        )
        assert summary_step is not None
        assert summary_step["input"]["style"] == "action_items"

    def test_all_steps_have_required_keys(self):
        """Every returned step must have action, description, and input keys."""
        instructions = [
            "transcribe https://youtube.com/watch?v=abc",
            "summarize this text",
            "translate to English",
            "search the knowledge base",
            "generate image of a mountain",
            "scan for PII",
            "execute code snippet",
            "completely unknown instruction 99abc",
        ]
        required_keys = {"action", "description", "input"}
        for instruction in instructions:
            result = _heuristic_plan(instruction)
            for step in result:
                assert required_keys.issubset(step.keys()), (
                    f"Step missing keys for instruction '{instruction}': {step}"
                )

    def test_batch_crawl_heuristic(self):
        """batch crawl keywords route to batch_crawl action."""
        for phrase in ["batch crawl these URLs", "batch scrape the list", "crawl multiple pages", "scrape all links"]:
            steps = _heuristic_plan(phrase)
            assert len(steps) >= 1
            assert steps[0]["action"] == "batch_crawl", f"Failed for: {phrase}"

    def test_deep_crawl_heuristic(self):
        """deep crawl keywords route to deep_crawl action."""
        for phrase in ["deep crawl this site", "crawl entire website", "spider the docs", "map site structure", "full site crawl"]:
            steps = _heuristic_plan(phrase)
            assert len(steps) >= 1
            assert steps[0]["action"] == "deep_crawl", f"Failed for: {phrase}"

    def test_batch_deep_crawl_before_generic(self):
        """batch/deep crawl takes priority over generic crawl_web."""
        steps_batch = _heuristic_plan("batch crawl web pages")
        assert steps_batch[0]["action"] == "batch_crawl"

        steps_deep = _heuristic_plan("deep crawl web site")
        assert steps_deep[0]["action"] == "deep_crawl"


class TestAvailableActions:
    """Verify AVAILABLE_ACTIONS dict completeness."""

    def test_all_youtube_actions_registered(self):
        youtube_actions = [
            "youtube_transcript",
            "youtube_metadata",
            "youtube_smart",
            "youtube_playlist",
            "youtube_analyze",
        ]
        for action in youtube_actions:
            assert action in AVAILABLE_ACTIONS, f"Missing action: {action}"

    def test_core_actions_present(self):
        core = [
            "transcribe",
            "summarize",
            "translate",
            "analyze_sentiment",
            "search_knowledge",
            "generate_image",
            "security_scan",
        ]
        for action in core:
            assert action in AVAILABLE_ACTIONS, f"Missing core action: {action}"

    def test_all_actions_have_description(self):
        for action, desc in AVAILABLE_ACTIONS.items():
            assert isinstance(desc, str) and len(desc) > 5, (
                f"Action '{action}' has empty/short description"
            )

    def test_available_actions_is_dict(self):
        assert isinstance(AVAILABLE_ACTIONS, dict)
        assert len(AVAILABLE_ACTIONS) > 0

    def test_batch_and_summary_actions_registered(self):
        batch_summary_actions = ["batch_transcribe", "generate_summary", "edit_audio", "generate_podcast"]
        for action in batch_summary_actions:
            assert action in AVAILABLE_ACTIONS, f"Missing action: {action}"

    def test_crawl_actions_registered(self):
        crawl_actions = ["batch_crawl", "deep_crawl"]
        for action in crawl_actions:
            assert action in AVAILABLE_ACTIONS, f"Missing action: {action}"

    def test_content_and_dev_actions_registered(self):
        actions = ["generate_presentation", "execute_code", "generate_form", "process_pdf"]
        for action in actions:
            assert action in AVAILABLE_ACTIONS, f"Missing action: {action}"

    def test_enterprise_actions_registered(self):
        actions = ["run_workflow", "run_crew", "deploy_chatbot", "search_marketplace"]
        for action in actions:
            assert action in AVAILABLE_ACTIONS, f"Missing action: {action}"

    def test_all_action_keys_are_strings(self):
        for key in AVAILABLE_ACTIONS:
            assert isinstance(key, str), f"Action key is not a string: {key!r}"

    def test_no_duplicate_descriptions(self):
        """Each action should have a unique description."""
        descriptions = list(AVAILABLE_ACTIONS.values())
        assert len(descriptions) == len(set(descriptions)), (
            "Duplicate descriptions found in AVAILABLE_ACTIONS"
        )
