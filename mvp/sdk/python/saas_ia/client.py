"""SaaSIAClient — main entry point for the SaaS-IA Python SDK.

Usage::

    async with SaaSIAClient() as client:
        await client.login("user@example.com", "password")
        transcriptions = await client.transcription.list()
        answer = await client.knowledge.ask("What is ...?")
"""

from __future__ import annotations

from typing import Any

import httpx

from saas_ia.exceptions import SaaSIAError

# Module APIs
from saas_ia.api.transcription import TranscriptionAPI
from saas_ia.api.conversation import ConversationAPI
from saas_ia.api.knowledge import KnowledgeAPI
from saas_ia.api.content_studio import ContentStudioAPI
from saas_ia.api.pipelines import PipelineAPI
from saas_ia.api.agents import AgentAPI
from saas_ia.api.compare import CompareAPI
from saas_ia.api.sentiment import SentimentAPI
from saas_ia.api.image_gen import ImageGenAPI
from saas_ia.api.video_gen import VideoGenAPI
from saas_ia.api.chatbot import ChatbotAPI
from saas_ia.api.marketplace import MarketplaceAPI
from saas_ia.api.data_analyst import DataAnalystAPI
from saas_ia.api.pdf import PDFAPI
from saas_ia.api.social_publisher import SocialPublisherAPI
from saas_ia.api.forms import FormsAPI
from saas_ia.api.code_sandbox import CodeSandboxAPI
from saas_ia.api.presentation_gen import PresentationGenAPI
from saas_ia.api.audio_studio import AudioStudioAPI

DEFAULT_BASE_URL = "http://localhost:8004"
DEFAULT_TIMEOUT = 30.0


class SaaSIAClient:
    """Async client for the SaaS-IA API.

    Parameters
    ----------
    base_url:
        API base URL.  Defaults to ``http://localhost:8004``.
    api_key:
        Optional API key for Public API v1 (``/v1/*``) endpoints.
    timeout:
        HTTP request timeout in seconds.  Defaults to 30.
    """

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        *,
        api_key: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        headers: dict[str, str] = {}
        if api_key:
            headers["X-API-Key"] = api_key

        self._http = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            headers=headers,
            timeout=timeout,
        )

        # Lazily-created module API instances
        self._transcription: TranscriptionAPI | None = None
        self._conversation: ConversationAPI | None = None
        self._knowledge: KnowledgeAPI | None = None
        self._content_studio: ContentStudioAPI | None = None
        self._pipelines: PipelineAPI | None = None
        self._agents: AgentAPI | None = None
        self._compare: CompareAPI | None = None
        self._sentiment: SentimentAPI | None = None
        self._image_gen: ImageGenAPI | None = None
        self._video_gen: VideoGenAPI | None = None
        self._chatbot: ChatbotAPI | None = None
        self._marketplace: MarketplaceAPI | None = None
        self._data_analyst: DataAnalystAPI | None = None
        self._pdf: PDFAPI | None = None
        self._social_publisher: SocialPublisherAPI | None = None
        self._forms: FormsAPI | None = None
        self._code_sandbox: CodeSandboxAPI | None = None
        self._presentation_gen: PresentationGenAPI | None = None
        self._audio_studio: AudioStudioAPI | None = None

    # -- Context manager ----------------------------------------------------

    async def __aenter__(self) -> "SaaSIAClient":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._http.aclose()

    # -- Auth ---------------------------------------------------------------

    async def login(self, email: str, password: str) -> dict[str, Any]:
        """Authenticate with email & password (OAuth2 form).

        The returned JWT is stored internally and used for all subsequent
        requests.

        Returns the full token response including ``access_token`` and
        ``refresh_token``.
        """
        response = await self._http.post(
            "/api/auth/login",
            data={"username": email, "password": password},
        )
        if response.status_code >= 400:
            try:
                detail = response.json().get("detail", response.reason_phrase)
            except Exception:
                detail = response.reason_phrase or str(response.status_code)
            raise SaaSIAError(response.status_code, detail)

        data = response.json()
        self.set_token(data["access_token"])
        return data

    def set_token(self, token: str) -> None:
        """Set a pre-existing JWT token."""
        self._http.headers["Authorization"] = f"Bearer {token}"

    def set_api_key(self, key: str) -> None:
        """Set an API key for Public API v1 endpoints."""
        self._http.headers["X-API-Key"] = key

    async def me(self) -> dict[str, Any]:
        """Get the current user profile."""
        response = await self._http.get("/api/auth/me")
        if response.status_code >= 400:
            try:
                detail = response.json().get("detail", response.reason_phrase)
            except Exception:
                detail = response.reason_phrase or str(response.status_code)
            raise SaaSIAError(response.status_code, detail)
        return response.json()

    # -- Module namespaces --------------------------------------------------

    @property
    def transcription(self) -> TranscriptionAPI:
        """YouTube/audio/video transcription."""
        if self._transcription is None:
            self._transcription = TranscriptionAPI(self._http)
        return self._transcription

    @property
    def conversation(self) -> ConversationAPI:
        """Contextual AI chat with history."""
        if self._conversation is None:
            self._conversation = ConversationAPI(self._http)
        return self._conversation

    @property
    def knowledge(self) -> KnowledgeAPI:
        """Document upload + hybrid search + RAG."""
        if self._knowledge is None:
            self._knowledge = KnowledgeAPI(self._http)
        return self._knowledge

    @property
    def content_studio(self) -> ContentStudioAPI:
        """Multi-format content generation (10 formats)."""
        if self._content_studio is None:
            self._content_studio = ContentStudioAPI(self._http)
        return self._content_studio

    @property
    def pipelines(self) -> PipelineAPI:
        """Sequential AI operation chaining (23 step types)."""
        if self._pipelines is None:
            self._pipelines = PipelineAPI(self._http)
        return self._pipelines

    @property
    def agents(self) -> AgentAPI:
        """Autonomous AI agents (65+ actions)."""
        if self._agents is None:
            self._agents = AgentAPI(self._http)
        return self._agents

    @property
    def compare(self) -> CompareAPI:
        """Multi-provider comparison with voting."""
        if self._compare is None:
            self._compare = CompareAPI(self._http)
        return self._compare

    @property
    def sentiment(self) -> SentimentAPI:
        """Text sentiment analysis (RoBERTa + LLM)."""
        if self._sentiment is None:
            self._sentiment = SentimentAPI(self._http)
        return self._sentiment

    @property
    def image_gen(self) -> ImageGenAPI:
        """AI image generation (10 styles)."""
        if self._image_gen is None:
            self._image_gen = ImageGenAPI(self._http)
        return self._image_gen

    @property
    def video_gen(self) -> VideoGenAPI:
        """Text-to-video generation (6 types)."""
        if self._video_gen is None:
            self._video_gen = VideoGenAPI(self._http)
        return self._video_gen

    @property
    def chatbot(self) -> ChatbotAPI:
        """RAG chatbot builder with embed widget."""
        if self._chatbot is None:
            self._chatbot = ChatbotAPI(self._http)
        return self._chatbot

    @property
    def marketplace(self) -> MarketplaceAPI:
        """Community marketplace (8 categories)."""
        if self._marketplace is None:
            self._marketplace = MarketplaceAPI(self._http)
        return self._marketplace

    @property
    def data_analyst(self) -> DataAnalystAPI:
        """CSV/JSON data analysis with DuckDB + NL queries."""
        if self._data_analyst is None:
            self._data_analyst = DataAnalystAPI(self._http)
        return self._data_analyst

    @property
    def pdf(self) -> PDFAPI:
        """PDF text/table extraction."""
        if self._pdf is None:
            self._pdf = PDFAPI(self._http)
        return self._pdf

    @property
    def social_publisher(self) -> SocialPublisherAPI:
        """Multi-platform social media publishing."""
        if self._social_publisher is None:
            self._social_publisher = SocialPublisherAPI(self._http)
        return self._social_publisher

    @property
    def forms(self) -> FormsAPI:
        """AI-powered conversational forms."""
        if self._forms is None:
            self._forms = FormsAPI(self._http)
        return self._forms

    @property
    def code_sandbox(self) -> CodeSandboxAPI:
        """Secure code execution + AI code tools."""
        if self._code_sandbox is None:
            self._code_sandbox = CodeSandboxAPI(self._http)
        return self._code_sandbox

    @property
    def presentation_gen(self) -> PresentationGenAPI:
        """AI slide generation (5 templates)."""
        if self._presentation_gen is None:
            self._presentation_gen = PresentationGenAPI(self._http)
        return self._presentation_gen

    @property
    def audio_studio(self) -> AudioStudioAPI:
        """Audio editing (pydub + noisereduce)."""
        if self._audio_studio is None:
            self._audio_studio = AudioStudioAPI(self._http)
        return self._audio_studio
