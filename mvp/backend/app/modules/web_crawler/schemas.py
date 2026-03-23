"""
Web crawler schemas.
"""

from typing import Optional

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


class ScrapeRequest(BaseModel):
    url: str = Field(..., min_length=1, max_length=2000)
    extract_images: bool = Field(default=True)
    screenshot: bool = Field(default=False)
    max_images: int = Field(default=20, ge=1, le=100)
    auth: Optional[AuthConfig] = Field(default=None)


class ImageData(BaseModel):
    src: str
    alt: str = ""
    score: float = 0.0
    description: Optional[str] = None


class ScrapeResponse(BaseModel):
    url: str
    title: str = ""
    markdown: str = ""
    text_length: int = 0
    images: list[ImageData] = []
    image_count: int = 0
    screenshot_base64: Optional[str] = None
    success: bool = True
    error: Optional[str] = None


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


class IndexRequest(BaseModel):
    url: str = Field(..., min_length=1, max_length=2000)
    crawl_subpages: bool = Field(default=False)
    max_pages: int = Field(default=5, ge=1, le=20)
    include_images: bool = Field(default=True)
    auth: Optional[AuthConfig] = Field(default=None)


class IndexResponse(BaseModel):
    url: str
    pages_crawled: int = 0
    chunks_indexed: int = 0
    images_found: int = 0
    success: bool = True
    error: Optional[str] = None
