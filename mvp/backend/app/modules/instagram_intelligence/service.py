"""Instagram intelligence service."""

import asyncio
import os
import tempfile
from typing import Optional

import structlog

logger = structlog.get_logger()

# Auto-detection: Playwright (preferred) → instagrapi → instaloader → mock
HAS_PLAYWRIGHT = False
HAS_INSTAGRAPI = False
HAS_INSTALOADER = False
HAS_PADDLEOCR = False
HAS_SURYA = False
HAS_EASYOCR = False

try:
    from playwright.async_api import async_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    pass

try:
    from instagrapi import Client as InstagrapiClient
    HAS_INSTAGRAPI = True
except ImportError:
    pass

try:
    import instaloader
    HAS_INSTALOADER = True
except ImportError:
    pass

try:
    from paddleocr import PaddleOCR as _PaddleOCR
    HAS_PADDLEOCR = True
except ImportError:
    pass

try:
    from surya.ocr import run_ocr as _surya_run_ocr
    HAS_SURYA = True
except ImportError:
    pass

try:
    import easyocr as _easyocr_mod
    HAS_EASYOCR = True
except ImportError:
    pass


def _get_instagram_settings():
    """Load Instagram credentials from settings (lazy import to avoid circular)."""
    try:
        from app.config import settings
        return {
            "username": settings.INSTAGRAM_USERNAME,
            "password": settings.INSTAGRAM_PASSWORD,
            "app_id": settings.INSTAGRAM_APP_ID,
            "app_secret": settings.INSTAGRAM_APP_SECRET,
            "access_token": settings.INSTAGRAM_ACCESS_TOKEN,
        }
    except Exception:
        return {}


class InstagramIntelligenceService:
    """Download public Instagram Reels, transcribe, score sentiment, store vectors.

    Auth priority:
      1. Meta Basic Display API (INSTAGRAM_ACCESS_TOKEN)
      2. instaloader session login (INSTAGRAM_USERNAME + INSTAGRAM_PASSWORD)
      3. instaloader anonymous (public profiles only, may be rate-limited by Instagram)
      4. mock mode (no library available)
    """

    def __init__(self, session=None):
        self.session = session
        self._creds = _get_instagram_settings()

    def _get_instaloader(self) -> "instaloader.Instaloader":
        """Return an authenticated Instaloader instance if credentials available."""
        L = instaloader.Instaloader(
            download_videos=False,
            download_video_thumbnails=False,
            download_comments=False,
            save_metadata=False,
            quiet=True,
        )
        username = self._creds.get("username", "")
        password = self._creds.get("password", "")
        if username and password:
            try:
                L.login(username, password)
                logger.info("instagram_instaloader_logged_in", username=username)
            except Exception as e:
                logger.warning("instagram_login_failed", error=str(e))
        return L

    async def validate_profile(self, username: str) -> dict:
        """Check if an Instagram profile exists and is public."""
        username = username.lstrip("@").strip()

        if HAS_INSTAGRAPI:
            return await asyncio.get_event_loop().run_in_executor(
                None, self._validate_instagrapi, username
            )
        if HAS_INSTALOADER:
            return await asyncio.get_event_loop().run_in_executor(
                None, self._validate_instaloader, username
            )

        return {
            "valid": False,
            "username": username,
            "exists": False,
            "is_private": False,
            "error": "No Instagram library available. Install instagrapi or instaloader.",
        }

    def _validate_instagrapi(self, username: str) -> dict:
        try:
            cl = InstagrapiClient()
            user_id = cl.user_id_from_username(username)
            info = cl.user_info(user_id)
            return {
                "valid": not info.is_private,
                "username": username,
                "exists": True,
                "is_private": info.is_private,
                "error": "Profile is private" if info.is_private else None,
            }
        except Exception as e:
            return {"valid": False, "username": username, "exists": False, "is_private": False, "error": str(e)[:200]}

    def _validate_instaloader(self, username: str) -> dict:
        try:
            L = self._get_instaloader()
            profile = instaloader.Profile.from_username(L.context, username)
            return {
                "valid": not profile.is_private,
                "username": username,
                "exists": True,
                "is_private": profile.is_private,
                "error": "Profile is private" if profile.is_private else None,
            }
        except instaloader.exceptions.ProfileNotExistsException:
            return {"valid": False, "username": username, "exists": False, "is_private": False, "error": "Profile not found"}
        except Exception as e:
            return {"valid": False, "username": username, "exists": False, "is_private": False, "error": str(e)[:200]}

    async def analyze_profile(
        self,
        username: str,
        max_reels: int = 10,
        transcribe: bool = True,
        language: str = "auto",
    ) -> dict:
        """Fetch public profile info + analyze up to max_reels Reels."""
        username = username.lstrip("@").strip()
        logger.info("instagram_analyze_profile", username=username, max_reels=max_reels)

        # Option 1: Meta Basic Display API
        if self._creds.get("access_token"):
            profile_data = await self._fetch_profile_meta_api(username, max_reels)
        elif HAS_PLAYWRIGHT:
            profile_data = await self._fetch_profile_playwright(username, max_reels)
        elif HAS_INSTAGRAPI:
            profile_data = await asyncio.get_event_loop().run_in_executor(
                None, self._fetch_profile_instagrapi, username, max_reels
            )
        elif HAS_INSTALOADER:
            profile_data = await asyncio.get_event_loop().run_in_executor(
                None, self._fetch_profile_instaloader, username, max_reels
            )
        else:
            profile_data = self._mock_profile(username, max_reels)

        reels = profile_data.get("reels", [])

        if transcribe and reels:
            reels = await self._transcribe_reels(reels, language)

        reels = await self._score_sentiment(reels)

        scores = [r["sentiment_score"] for r in reels if r.get("sentiment_score") is not None]
        avg_score = round(sum(scores) / len(scores), 3) if scores else None
        topics = self._extract_topics(reels)

        return {
            "username": username,
            "full_name": profile_data.get("full_name", ""),
            "bio": profile_data.get("bio", ""),
            "followers": profile_data.get("followers", 0),
            "following": profile_data.get("following", 0),
            "post_count": profile_data.get("post_count", 0),
            "reels_analyzed": len(reels),
            "reels": reels,
            "avg_sentiment_score": avg_score,
            "top_topics": topics,
        }

    async def analyze_reel(self, reel_url: str, transcribe: bool = True, language: str = "auto") -> dict:
        """Analyze a single Reel by URL."""
        logger.info("instagram_analyze_reel", url=reel_url)

        if self._creds.get("access_token"):
            reel_data = await self._fetch_reel_meta_api(reel_url)
        elif HAS_PLAYWRIGHT:
            reel_data = await self._fetch_reel_playwright(reel_url)
        elif HAS_INSTAGRAPI:
            reel_data = await asyncio.get_event_loop().run_in_executor(
                None, self._fetch_reel_instagrapi, reel_url
            )
        elif HAS_INSTALOADER:
            reel_data = await asyncio.get_event_loop().run_in_executor(
                None, self._fetch_reel_instaloader, reel_url
            )
        else:
            reel_data = self._mock_reel(reel_url)

        reels = [reel_data]
        if transcribe:
            reels = await self._transcribe_reels(reels, language)
        reels = await self._score_sentiment(reels)
        return reels[0]

    # ── instagrapi fetch helpers ──────────────────────────────────────────────

    def _fetch_profile_instagrapi(self, username: str, max_reels: int) -> dict:
        try:
            cl = InstagrapiClient()
            user_id = cl.user_id_from_username(username)
            info = cl.user_info(user_id)
            clips = cl.user_clips(user_id, amount=max_reels)
            reels = [self._reel_from_instagrapi(m, username) for m in clips]
            return {
                "full_name": info.full_name or "",
                "bio": info.biography or "",
                "followers": info.follower_count or 0,
                "following": info.following_count or 0,
                "post_count": info.media_count or 0,
                "reels": reels,
            }
        except Exception as e:
            logger.warning("instagram_instagrapi_error", error=str(e))
            return self._mock_profile(username, max_reels)

    def _fetch_reel_instagrapi(self, reel_url: str) -> dict:
        try:
            cl = InstagrapiClient()
            media_pk = cl.media_pk_from_url(reel_url)
            media = cl.media_info(media_pk)
            username = media.user.username if media.user else "unknown"
            return self._reel_from_instagrapi(media, username)
        except Exception as e:
            logger.warning("instagram_instagrapi_reel_error", error=str(e))
            return self._mock_reel(reel_url)

    def _reel_from_instagrapi(self, media, username: str) -> dict:
        return {
            "reel_id": str(media.pk),
            "username": username,
            "caption": (media.caption_text or "")[:500],
            "likes": media.like_count or 0,
            "comments": media.comment_count or 0,
            "views": media.view_count or 0,
            "duration_seconds": float(media.video_duration or 0),
            "thumbnail_url": str(media.thumbnail_url) if media.thumbnail_url else None,
            "reel_url": f"https://www.instagram.com/reel/{media.code}/",
            "video_url": str(media.video_url) if media.video_url else None,
            "transcript": None,
            "transcript_language": None,
            "sentiment_label": None,
            "sentiment_score": None,
            "provider": "instagrapi",
        }

    # ── instaloader fetch helpers ─────────────────────────────────────────────

    # ── Playwright scraper ────────────────────────────────────────────────────

    async def _fetch_profile_playwright(self, username: str, max_reels: int) -> dict:
        """Scrape Instagram profile + reels via headless Chromium."""
        try:
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(
                    headless=True,
                    args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"],
                )
                ctx = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                    viewport={"width": 1280, "height": 800},
                    locale="en-US",
                )
                page = await ctx.new_page()

                # Login if credentials available
                creds_username = self._creds.get("username", "")
                creds_password = self._creds.get("password", "")
                if creds_username and creds_password:
                    await self._playwright_login(page, creds_username, creds_password)

                # Navigate to profile
                await page.goto(f"https://www.instagram.com/{username}/", wait_until="networkidle", timeout=30000)
                await page.wait_for_timeout(2000)

                # Extract profile info via JSON-LD or page content
                profile_data = await page.evaluate("""() => {
                    const getMeta = (prop) => {
                        const el = document.querySelector(`meta[property='${prop}']`) ||
                                   document.querySelector(`meta[name='${prop}']`);
                        return el ? el.getAttribute('content') : '';
                    };
                    const desc = getMeta('og:description') || '';
                    const title = getMeta('og:title') || document.title || '';
                    // Parse followers from description: "1.2M Followers, 500 Following, 1,234 Posts"
                    const followerMatch = desc.match(/([\d,.]+[KMB]?)\s+Followers/i);
                    const followingMatch = desc.match(/([\d,.]+[KMB]?)\s+Following/i);
                    const postsMatch = desc.match(/([\d,.]+[KMB]?)\s+Posts/i);
                    const parseNum = (s) => {
                        if (!s) return 0;
                        s = s.replace(/,/g, '');
                        if (s.endsWith('M')) return Math.round(parseFloat(s) * 1000000);
                        if (s.endsWith('K')) return Math.round(parseFloat(s) * 1000);
                        if (s.endsWith('B')) return Math.round(parseFloat(s) * 1000000000);
                        return parseInt(s) || 0;
                    };
                    return {
                        full_name: title.replace(' • Instagram', '').replace(' (@' + window.location.pathname.replace(/\\//g, '') + ')', '').trim(),
                        bio: getMeta('og:description') || '',
                        followers: parseNum(followerMatch ? followerMatch[1] : '0'),
                        following: parseNum(followingMatch ? followingMatch[1] : '0'),
                        post_count: parseNum(postsMatch ? postsMatch[1] : '0'),
                    };
                }""")

                # Extract reel links
                reel_links = await page.evaluate("""() => {
                    const links = Array.from(document.querySelectorAll('a[href*="/reel/"]'));
                    return [...new Set(links.map(a => a.href))].slice(0, 20);
                }""")

                await browser.close()

                # Fetch each reel
                reels = []
                for reel_url in reel_links[:max_reels]:
                    try:
                        reel = await self._fetch_reel_playwright(reel_url)
                        reels.append(reel)
                    except Exception as e:
                        logger.warning("playwright_reel_error", url=reel_url, error=str(e))

                return {
                    "full_name": profile_data.get("full_name", ""),
                    "bio": profile_data.get("bio", ""),
                    "followers": profile_data.get("followers", 0),
                    "following": profile_data.get("following", 0),
                    "post_count": profile_data.get("post_count", 0),
                    "reels": reels,
                }
        except Exception as e:
            logger.warning("playwright_profile_error", username=username, error=str(e))
            return self._mock_profile(username, max_reels)

    async def _fetch_reel_playwright(self, reel_url: str) -> dict:
        """Scrape a single Reel page via Playwright — intercepts CDN video URL."""
        try:
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(
                    headless=True,
                    args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"],
                )
                ctx = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                    locale="en-US",
                )
                page = await ctx.new_page()

                # Intercept CDN video requests
                cdn_video_url = []
                def on_response(response):
                    url = response.url
                    if ("cdninstagram.com" in url or "fbcdn.net" in url) and (
                        ".mp4" in url or "video" in url.lower()
                    ) and "jpg" not in url:
                        if url not in cdn_video_url:
                            cdn_video_url.append(url)

                page.on("response", on_response)

                creds_username = self._creds.get("username", "")
                creds_password = self._creds.get("password", "")
                if creds_username and creds_password:
                    await self._playwright_login(page, creds_username, creds_password)

                await page.goto(reel_url, wait_until="networkidle", timeout=30000)
                await page.wait_for_timeout(3000)

                data = await page.evaluate("""() => {
                    const getMeta = (prop) => {
                        const el = document.querySelector(`meta[property='${prop}']`) ||
                                   document.querySelector(`meta[name='${prop}']`);
                        return el ? el.getAttribute('content') : '';
                    };
                    const desc = getMeta('og:description') || '';
                    const parseNum = (s) => {
                        if (!s) return 0;
                        s = s.replace(/,/g, '');
                        if (s.endsWith('M')) return Math.round(parseFloat(s) * 1000000);
                        if (s.endsWith('K')) return Math.round(parseFloat(s) * 1000);
                        return parseInt(s) || 0;
                    };
                    const likesMatch = desc.match(/([\d,.]+[KMB]?) likes/i);
                    const imgEl = document.querySelector('meta[property="og:image"]');
                    // Try to get video src from source element (higher quality than blob)
                    const sourceEl = document.querySelector('video source');
                    const videoEl = document.querySelector('video');
                    return {
                        caption: desc,
                        likes: parseNum(likesMatch ? likesMatch[1] : '0'),
                        thumbnail_url: imgEl ? imgEl.getAttribute('content') : '',
                        video_src: (sourceEl ? sourceEl.src : '') || (videoEl ? videoEl.currentSrc : ''),
                    };
                }""")

                shortcode = reel_url.rstrip("/").split("/")[-1]

                # Pick best video URL: intercepted CDN > page source
                best_video_url = None
                if cdn_video_url:
                    best_video_url = cdn_video_url[0]
                    logger.info("playwright_cdn_video_intercepted", url=best_video_url[:80])
                elif data.get("video_src") and not data["video_src"].startswith("blob:"):
                    best_video_url = data["video_src"]

                thumbnail_url = data.get("thumbnail_url") or None

                await browser.close()

                return {
                    "reel_id": shortcode,
                    "username": "",
                    "caption": data.get("caption", "")[:500],
                    "likes": data.get("likes", 0),
                    "comments": 0,
                    "views": 0,
                    "duration_seconds": 0,
                    "thumbnail_url": thumbnail_url,
                    "reel_url": reel_url,
                    "video_url": best_video_url,
                    "transcript": None,
                    "transcript_language": None,
                    "sentiment_label": None,
                    "sentiment_score": None,
                    "provider": "playwright",
                }
        except Exception as e:
            logger.warning("playwright_reel_fetch_error", url=reel_url, error=str(e))
            return self._mock_reel(reel_url)

    async def _playwright_login(self, page, username: str, password: str) -> None:
        """Login to Instagram via Playwright if not already logged in."""
        try:
            await page.goto("https://www.instagram.com/accounts/login/", wait_until="networkidle", timeout=20000)
            await page.wait_for_timeout(1500)
            # Check if already on login page
            if not await page.is_visible('input[name="username"]'):
                return
            await page.fill('input[name="username"]', username)
            await page.fill('input[name="password"]', password)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(3000)
            logger.info("playwright_login_attempted", username=username)
        except Exception as e:
            logger.warning("playwright_login_error", error=str(e))

    # ── Meta Basic Display API ────────────────────────────────────────────────

    async def _fetch_profile_meta_api(self, username: str, max_reels: int) -> dict:
        """Fetch profile + reels via Meta Graph API using access_token."""
        import httpx
        token = self._creds["access_token"]
        base = "https://graph.instagram.com/v19.0"
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # Get user info
                r = await client.get(f"{base}/me", params={
                    "fields": "id,username,name,biography,followers_count,follows_count,media_count",
                    "access_token": token,
                })
                r.raise_for_status()
                user = r.json()

                # Get media list
                r2 = await client.get(f"{base}/me/media", params={
                    "fields": "id,media_type,media_url,thumbnail_url,caption,like_count,comments_count,timestamp,permalink",
                    "access_token": token,
                    "limit": max_reels * 3,
                })
                r2.raise_for_status()
                media_list = r2.json().get("data", [])

                reels = []
                for m in media_list:
                    if m.get("media_type") == "VIDEO" and len(reels) < max_reels:
                        reels.append({
                            "reel_id": m["id"],
                            "username": user.get("username", username),
                            "caption": (m.get("caption") or "")[:500],
                            "likes": m.get("like_count", 0),
                            "comments": m.get("comments_count", 0),
                            "views": 0,
                            "duration_seconds": 0,
                            "thumbnail_url": m.get("thumbnail_url"),
                            "reel_url": m.get("permalink", ""),
                            "video_url": m.get("media_url"),
                            "transcript": None,
                            "transcript_language": None,
                            "sentiment_label": None,
                            "sentiment_score": None,
                            "provider": "meta_api",
                        })

                return {
                    "full_name": user.get("name", ""),
                    "bio": user.get("biography", ""),
                    "followers": user.get("followers_count", 0),
                    "following": user.get("follows_count", 0),
                    "post_count": user.get("media_count", 0),
                    "reels": reels,
                }
        except Exception as e:
            logger.warning("instagram_meta_api_error", error=str(e))
            return self._mock_profile(username, max_reels)

    async def _fetch_reel_meta_api(self, reel_url: str) -> dict:
        """Fetch a single reel via Meta Graph API from permalink."""
        import httpx
        token = self._creds["access_token"]
        base = "https://graph.instagram.com/v19.0"
        try:
            # Extract media ID from URL if possible, else search recent media
            async with httpx.AsyncClient(timeout=30) as client:
                r = await client.get(f"{base}/me/media", params={
                    "fields": "id,media_type,media_url,thumbnail_url,caption,like_count,comments_count,permalink",
                    "access_token": token,
                    "limit": 50,
                })
                r.raise_for_status()
                for m in r.json().get("data", []):
                    if m.get("media_type") == "VIDEO" and reel_url in m.get("permalink", ""):
                        return {
                            "reel_id": m["id"],
                            "username": "",
                            "caption": (m.get("caption") or "")[:500],
                            "likes": m.get("like_count", 0),
                            "comments": m.get("comments_count", 0),
                            "views": 0,
                            "duration_seconds": 0,
                            "thumbnail_url": m.get("thumbnail_url"),
                            "reel_url": m.get("permalink", reel_url),
                            "video_url": m.get("media_url"),
                            "transcript": None,
                            "transcript_language": None,
                            "sentiment_label": None,
                            "sentiment_score": None,
                            "provider": "meta_api",
                        }
        except Exception as e:
            logger.warning("instagram_meta_api_reel_error", error=str(e))
        return self._mock_reel(reel_url)

    def _fetch_profile_instaloader(self, username: str, max_reels: int) -> dict:
        try:
            L = self._get_instaloader()
            profile = instaloader.Profile.from_username(L.context, username)
            reels = []
            for post in profile.get_posts():
                if post.is_video:
                    reels.append(self._reel_from_instaloader(post, username))
                    if len(reels) >= max_reels:
                        break
            return {
                "full_name": profile.full_name or "",
                "bio": profile.biography or "",
                "followers": profile.followers or 0,
                "following": profile.followees or 0,
                "post_count": profile.mediacount or 0,
                "reels": reels,
            }
        except Exception as e:
            logger.warning("instagram_instaloader_error", error=str(e))
            return self._mock_profile(username, max_reels)

    def _fetch_reel_instaloader(self, reel_url: str) -> dict:
        try:
            L = self._get_instaloader()
            shortcode = reel_url.rstrip("/").split("/")[-1]
            post = instaloader.Post.from_shortcode(L.context, shortcode)
            return self._reel_from_instaloader(post, post.owner_username)
        except Exception as e:
            logger.warning("instagram_instaloader_reel_error", error=str(e))
            return self._mock_reel(reel_url)

    def _reel_from_instaloader(self, post, username: str) -> dict:
        return {
            "reel_id": post.shortcode,
            "username": username,
            "caption": (post.caption or "")[:500],
            "likes": post.likes or 0,
            "comments": post.comments or 0,
            "views": post.video_view_count or 0,
            "duration_seconds": float(post.video_duration or 0),
            "thumbnail_url": post.url,
            "reel_url": f"https://www.instagram.com/p/{post.shortcode}/",
            "video_url": post.video_url if post.is_video else None,
            "transcript": None,
            "transcript_language": None,
            "sentiment_label": None,
            "sentiment_score": None,
            "provider": "instaloader",
        }

    # ── transcription ─────────────────────────────────────────────────────────

    async def _transcribe_reels(self, reels: list[dict], language: str) -> list[dict]:
        """Download audio for each reel and transcribe with Whisper via yt-dlp."""
        for reel in reels:
            # Use the original reel page URL for yt-dlp (CDN URLs require browser session)
            source_url = reel.get("reel_url") or reel.get("video_url")
            if not source_url:
                continue
            try:
                transcript, lang = await self._transcribe_video_url(source_url, language)
                reel["transcript"] = transcript
                reel["transcript_language"] = lang
            except Exception as e:
                logger.warning("instagram_transcribe_error", reel_id=reel.get("reel_id"), error=str(e))
        return reels

    async def _transcribe_video_url(self, reel_url: str, language: str) -> tuple[str, str]:
        """Download video via yt-dlp (handles Instagram DASH streams) and transcribe."""
        tmp_dir = tempfile.mkdtemp()
        tmp_path = os.path.join(tmp_dir, "reel.%(ext)s")

        try:
            text, lang = await asyncio.get_event_loop().run_in_executor(
                None, self._ytdlp_download_and_transcribe, reel_url, tmp_path, tmp_dir, language
            )
            return text, lang
        finally:
            import shutil
            try:
                shutil.rmtree(tmp_dir, ignore_errors=True)
            except OSError:
                pass

    def _ytdlp_download_and_transcribe(self, reel_url: str, tmp_path: str, tmp_dir: str, language: str) -> tuple[str, str]:
        """Download via yt-dlp and transcribe with faster-whisper (sync, runs in executor)."""
        try:
            import yt_dlp
        except ImportError:
            logger.warning("yt_dlp_not_available")
            return "", language or "en"

        ydl_opts = {
            "outtmpl": tmp_path,
            "format": "best",
            "quiet": True,
            "no_warnings": True,
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120",
            },
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([reel_url])
        except Exception as e:
            logger.warning("instagram_ytdlp_download_error", error=str(e))
            return "", language or "en"

        import glob
        files = glob.glob(os.path.join(tmp_dir, "*"))
        if not files:
            logger.warning("instagram_ytdlp_no_file")
            return "", language or "en"

        downloaded_path = files[0]
        logger.info("instagram_ytdlp_downloaded", size=os.path.getsize(downloaded_path))
        return self._whisper_transcribe_sync(downloaded_path, language)

    def _whisper_transcribe_sync(self, audio_path: str, language: str) -> tuple[str, str]:
        """Run faster-whisper synchronously in a thread executor."""
        try:
            from faster_whisper import WhisperModel
            model = WhisperModel("tiny", device="cpu", compute_type="int8")
            lang_arg = None if language in ("auto", "", None) else language
            segments_gen, info = model.transcribe(audio_path, language=lang_arg, beam_size=2)
            segments = list(segments_gen)  # materialize generator
            text = " ".join(seg.text.strip() for seg in segments).strip()
            detected_lang = info.language if info else (language or "en")
            logger.info("instagram_whisper_done", lang=detected_lang, chars=len(text))
            return text, detected_lang
        except ImportError:
            logger.warning("faster_whisper_not_available")
            return "", language or "en"
        except Exception as e:
            logger.warning("instagram_whisper_error", error=str(e))
            return "", language or "en"

    # ── sentiment scoring ─────────────────────────────────────────────────────

    async def _score_sentiment(self, reels: list[dict]) -> list[dict]:
        """Score each reel's transcript (or caption) with RoBERTa sentiment."""
        try:
            from app.modules.sentiment.service import SentimentService

            svc = SentimentService()
            for reel in reels:
                text = reel.get("transcript") or reel.get("caption") or ""
                if not text.strip():
                    continue
                result = await svc.analyze_text(text[:512])
                reel["sentiment_label"] = result.get("overall_sentiment") or result.get("label")
                reel["sentiment_score"] = result.get("overall_score") or result.get("score")
        except Exception as e:
            logger.warning("instagram_sentiment_error", error=str(e))
        return reels

    # ── topic extraction ──────────────────────────────────────────────────────

    def _extract_topics(self, reels: list[dict]) -> list[str]:
        """Extract top hashtags / keywords from captions."""
        import re
        from collections import Counter

        tags: list[str] = []
        for reel in reels:
            caption = reel.get("caption", "")
            tags.extend(re.findall(r"#(\w+)", caption.lower()))
            transcript = reel.get("transcript", "") or ""
            words = [w.lower() for w in re.findall(r"\b\w{5,}\b", transcript)]
            tags.extend(words[:10])

        counts = Counter(tags)
        return [t for t, _ in counts.most_common(10)]

    async def save_reel(self, reel: dict, user_id) -> None:
        """Save reel to database if session available."""
        if not self.session:
            return
        try:
            from app.models.instagram_intelligence import InstagramReel
            from uuid import uuid4
            from datetime import datetime, UTC

            db_reel = InstagramReel(
                id=uuid4(),
                user_id=user_id,
                username=reel.get("username", ""),
                reel_id=reel.get("reel_id", ""),
                reel_url=reel.get("reel_url", ""),
                caption=reel.get("caption", "")[:2200],
                likes=reel.get("likes", 0),
                comments=reel.get("comments", 0),
                views=reel.get("views", 0),
                duration_seconds=reel.get("duration_seconds", 0),
                thumbnail_url=reel.get("thumbnail_url"),
                transcript=reel.get("transcript"),
                transcript_language=reel.get("transcript_language"),
                sentiment_label=reel.get("sentiment_label"),
                sentiment_score=reel.get("sentiment_score"),
                provider=reel.get("provider", "instaloader"),
                created_at=datetime.now(UTC).replace(tzinfo=None),
            )
            self.session.add(db_reel)
            await self.session.commit()
            logger.info("instagram_reel_saved", reel_id=db_reel.id, username=reel.get("username"))
        except Exception as e:
            logger.warning("instagram_save_error", error=str(e))

    # ── carousel download ─────────────────────────────────────────────────────

    async def download_carousel(self, post_url: str) -> dict:
        """Download all slides from an Instagram carousel/sidecar post.

        Fallback chain:
          1. instaloader get_sidecar_nodes() — anonymous, no login needed
          2. Playwright DOM scraping — headless browser, intercepts img tags
        Returns dict with slides list [{index, url, is_video, bytes}] + metadata.
        """
        # Extract shortcode robustly from /p/<code>/ or /reel/<code>/
        import re as _re
        m = _re.search(r"/(?:p|reel)/([A-Za-z0-9_-]+)", post_url)
        shortcode = m.group(1) if m else post_url.rstrip("/").split("/")[-1].split("?")[0]
        logger.info("instagram_carousel_download", shortcode=shortcode)

        # ── Strategy 1: instaloader ───────────────────────────────────────────
        if HAS_INSTALOADER:
            try:
                result = await asyncio.get_event_loop().run_in_executor(
                    None, self._carousel_instaloader, shortcode
                )
                if result and result.get("slides"):
                    logger.info("instagram_carousel_instaloader_ok", count=len(result["slides"]))
                    return result
                logger.warning("instagram_carousel_instaloader_empty")
            except Exception as e:
                logger.warning("instagram_carousel_instaloader_failed", error=str(e))

        # ── Strategy 2: Playwright DOM scraping ───────────────────────────────
        if HAS_PLAYWRIGHT:
            try:
                result = await self._carousel_playwright(post_url)
                if result and result.get("slides"):
                    logger.info("instagram_carousel_playwright_ok", count=len(result["slides"]))
                    return result
                logger.warning("instagram_carousel_playwright_empty")
            except Exception as e:
                logger.warning("instagram_carousel_playwright_failed", error=str(e))

        return {"shortcode": shortcode, "post_url": post_url, "slides": [], "provider": "none", "error": "All strategies failed"}

    def _carousel_instaloader(self, shortcode: str) -> dict:
        """Strategy 1 — instaloader get_sidecar_nodes() (sync, runs in executor)."""
        import instaloader
        import urllib.request

        L = instaloader.Instaloader(
            quiet=True,
            download_pictures=False,
            download_videos=False,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
        )

        post = instaloader.Post.from_shortcode(L.context, shortcode)
        nodes = list(post.get_sidecar_nodes())

        # If no sidecar nodes, might be a single image/video post
        if not nodes:
            # Single media
            slides = [{
                "index": 1,
                "url": post.url,
                "is_video": post.is_video,
                "video_url": post.video_url if post.is_video else None,
            }]
        else:
            slides = [
                {
                    "index": i + 1,
                    "url": node.display_url,
                    "is_video": node.is_video,
                    "video_url": node.video_url if node.is_video else None,
                }
                for i, node in enumerate(nodes)
            ]

        return {
            "shortcode": shortcode,
            "post_url": f"https://www.instagram.com/p/{shortcode}/",
            "username": post.owner_username,
            "caption": (post.caption or "")[:500],
            "likes": post.likes or 0,
            "media_type": post.typename,
            "slide_count": len(slides),
            "slides": slides,
            "provider": "instaloader",
        }

    async def _carousel_playwright(self, post_url: str) -> dict:
        """Strategy 2 — Playwright headless DOM scraping for carousel images."""
        import httpx

        shortcode = post_url.rstrip("/").split("/")[-1].split("?")[0]

        JS_COLLECT = """
        () => {
            var result = [];
            var imgs = document.querySelectorAll("img");
            for (var i = 0; i < imgs.length; i++) {
                var src = imgs[i].src;
                var srcset = imgs[i].srcset || "";
                if (src && (src.indexOf("cdninstagram") > -1 || src.indexOf("fbcdn") > -1)) {
                    result.push(src);
                }
                if (srcset) {
                    var parts = srcset.split(",");
                    for (var j = 0; j < parts.length; j++) {
                        var u = parts[j].trim().split(" ")[0];
                        if (u && (u.indexOf("cdninstagram") > -1 || u.indexOf("fbcdn") > -1)) {
                            result.push(u);
                        }
                    }
                }
            }
            return result;
        }
        """

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"],
            )
            ctx = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122",
                viewport={"width": 1280, "height": 900},
            )
            page = await ctx.new_page()
            await page.goto(post_url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(2)

            # Accept cookie banner
            for label in ["Autoriser tous les cookies", "Allow all cookies", "Tout accepter", "Allow essential and optional cookies"]:
                try:
                    await page.click(f'button:has-text("{label}")', timeout=2000)
                    await asyncio.sleep(2)
                    break
                except Exception:
                    pass

            await asyncio.sleep(3)

            # Get caption/meta
            meta_title = await page.evaluate(
                "() => { var el = document.querySelector('meta[property=\"og:title\"]'); return el ? el.content : ''; }"
            )
            meta_desc = await page.evaluate(
                "() => { var el = document.querySelector('meta[property=\"og:description\"]'); return el ? el.content : ''; }"
            )

            seen = set()
            all_urls = []

            def collect(imgs):
                for img in imgs:
                    if img not in seen and "t51." in img:
                        seen.add(img)
                        all_urls.append(img)

            collect(await page.evaluate(JS_COLLECT))

            # Navigate through carousel slides
            for _ in range(15):
                try:
                    next_btn = await page.query_selector(
                        'button[aria-label*="Next"], button[aria-label*="Suivant"], button[aria-label*="next"]'
                    )
                    if next_btn:
                        await next_btn.click()
                    else:
                        await page.keyboard.press("ArrowRight")
                    await asyncio.sleep(1.5)
                    before = len(all_urls)
                    collect(await page.evaluate(JS_COLLECT))
                    if len(all_urls) == before:
                        break
                except Exception:
                    break

            await browser.close()

        # Filter out profile pics (t51.2885 = profile, t51.82787 = post media)
        post_images = [u for u in all_urls if "t51.82787" in u or "t51.75761" in u]
        if not post_images:
            post_images = [u for u in all_urls if "t51." in u]

        slides = [
            {"index": i + 1, "url": u, "is_video": False, "video_url": None}
            for i, u in enumerate(post_images)
        ]

        return {
            "shortcode": shortcode,
            "post_url": post_url,
            "username": "",
            "caption": meta_desc[:500] if meta_desc else "",
            "likes": 0,
            "media_type": "GraphSidecar",
            "slide_count": len(slides),
            "slides": slides,
            "provider": "playwright",
        }

    async def download_carousel_files(self, post_url: str, out_dir: str) -> dict:
        """Download carousel slides to a local directory. Returns paths."""
        import httpx, shutil

        carousel = await self.download_carousel(post_url)
        slides = carousel.get("slides", [])
        if not slides:
            return carousel

        os.makedirs(out_dir, exist_ok=True)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122",
            "Referer": "https://www.instagram.com/",
        }

        saved = []
        async with httpx.AsyncClient(timeout=30, follow_redirects=True, headers=headers) as client:
            for slide in slides:
                url = slide.get("video_url") or slide.get("url")
                if not url:
                    continue
                ext = "mp4" if slide.get("is_video") else "jpg"
                path = os.path.join(out_dir, f"slide_{slide['index']:02d}.{ext}")
                try:
                    resp = await client.get(url)
                    if resp.status_code == 200 and len(resp.content) > 5000:
                        with open(path, "wb") as f:
                            f.write(resp.content)
                        saved.append({"index": slide["index"], "path": path, "size": len(resp.content)})
                        logger.info("instagram_slide_saved", path=path, size=len(resp.content))
                except Exception as e:
                    logger.warning("instagram_slide_download_error", slide=slide["index"], error=str(e))

        carousel["saved_files"] = saved
        carousel["out_dir"] = out_dir
        return carousel

    # ── carousel OCR / vision ─────────────────────────────────────────────────

    async def transcribe_carousel_images(
        self,
        image_paths: list[str],
        mode: str = "claude_vision",
    ) -> list[dict]:
        """Extract text and structure from carousel slide images.

        mode:
          - "local_ocr"     : PaddleOCR → Surya → EasyOCR (best available, no API key)
          - "claude_vision" : Claude Haiku vision (best for infographics/schemas)
          - "both"          : run both in parallel, return combined result
        """
        if mode == "local_ocr":
            return await asyncio.get_event_loop().run_in_executor(
                None, self._ocr_slides_local, image_paths
            )
        if mode == "claude_vision":
            return await self._ocr_slides_claude(image_paths)
        if mode == "both":
            ocr_task = asyncio.get_event_loop().run_in_executor(
                None, self._ocr_slides_local, image_paths
            )
            vision_task = self._ocr_slides_claude(image_paths)
            ocr_results, vision_results = await asyncio.gather(ocr_task, vision_task, return_exceptions=True)
            combined = []
            for i, path in enumerate(image_paths):
                combined.append({
                    "index": i + 1,
                    "path": path,
                    "local_ocr": ocr_results[i]["text"] if not isinstance(ocr_results, Exception) else None,
                    "claude_vision": vision_results[i]["text"] if not isinstance(vision_results, Exception) else None,
                })
            return combined
        raise ValueError(f"Unknown mode: {mode}")

    def _ocr_slides_local(self, image_paths: list[str]) -> list[dict]:
        """Local OCR dispatcher: PaddleOCR → Surya → EasyOCR (best available)."""
        if HAS_PADDLEOCR:
            logger.info("local_ocr_engine", engine="paddleocr")
            return self._ocr_slides_paddleocr(image_paths)
        if HAS_SURYA:
            logger.info("local_ocr_engine", engine="surya")
            return self._ocr_slides_surya(image_paths)
        if HAS_EASYOCR:
            logger.info("local_ocr_engine", engine="easyocr")
            return self._ocr_slides_easyocr(image_paths)
        logger.warning("no_local_ocr_engine_available")
        return [{"index": i + 1, "path": p, "text": "", "method": "local_ocr", "error": "no OCR engine installed"} for i, p in enumerate(image_paths)]

    def _ocr_slides_paddleocr(self, image_paths: list[str]) -> list[dict]:
        """PaddleOCR extraction — fastest local engine (~2s/img CPU)."""
        import os as _os
        _os.environ.setdefault("FLAGS_use_mkldnn", "0")
        try:
            ocr = _PaddleOCR(use_angle_cls=True, lang="en", use_gpu=False, show_log=False)
        except Exception as e:
            logger.warning("paddleocr_init_failed", error=str(e))
            return self._ocr_slides_easyocr(image_paths) if HAS_EASYOCR else [
                {"index": i + 1, "path": p, "text": "", "method": "local_ocr", "error": str(e)}
                for i, p in enumerate(image_paths)
            ]

        results = []
        for i, path in enumerate(image_paths):
            try:
                result = ocr.ocr(path, cls=True)
                lines = [line[1][0] for line in result[0]] if result and result[0] else []
                text = "\n".join(lines)
                results.append({"index": i + 1, "path": path, "text": text, "method": "paddleocr"})
                logger.info("paddleocr_slide_done", index=i + 1, chars=len(text))
            except Exception as e:
                logger.warning("paddleocr_slide_error", index=i + 1, error=str(e))
                results.append({"index": i + 1, "path": path, "text": "", "method": "paddleocr", "error": str(e)})
        return results

    def _ocr_slides_surya(self, image_paths: list[str]) -> list[dict]:
        """Surya OCR extraction — best layout accuracy (~13s/img CPU)."""
        try:
            from surya.model.detection.model import load_model as _load_det, load_processor as _load_det_proc
            from surya.model.recognition.model import load_model as _load_rec
            from surya.model.recognition.processor import load_processor as _load_rec_proc
            det_model = _load_det()
            det_proc = _load_det_proc()
            rec_model = _load_rec()
            rec_proc = _load_rec_proc()
        except Exception as e:
            logger.warning("surya_init_failed", error=str(e))
            return [{"index": i + 1, "path": p, "text": "", "method": "surya", "error": str(e)} for i, p in enumerate(image_paths)]

        from PIL import Image as _Image
        results = []
        for i, path in enumerate(image_paths):
            try:
                img = _Image.open(path).convert("RGB")
                preds = _surya_run_ocr([img], [["en"]], det_model, det_proc, rec_model, rec_proc)
                lines = [line.text for line in preds[0].text_lines]
                text = "\n".join(lines)
                results.append({"index": i + 1, "path": path, "text": text, "method": "surya"})
                logger.info("surya_slide_done", index=i + 1, chars=len(text))
            except Exception as e:
                logger.warning("surya_slide_error", index=i + 1, error=str(e))
                results.append({"index": i + 1, "path": path, "text": "", "method": "surya", "error": str(e)})
        return results

    def _ocr_slides_easyocr(self, image_paths: list[str]) -> list[dict]:
        """EasyOCR extraction — fallback local engine."""
        if not HAS_EASYOCR:
            logger.warning("easyocr_not_available")
            return [{"index": i + 1, "path": p, "text": "", "method": "local_ocr"} for i, p in enumerate(image_paths)]

        reader = _easyocr_mod.Reader(["en"], gpu=False, verbose=False)
        results = []
        for i, path in enumerate(image_paths):
            try:
                lines = reader.readtext(path, detail=0, paragraph=True)
                text = "\n".join(lines)
                results.append({"index": i + 1, "path": path, "text": text, "method": "easyocr"})
                logger.info("easyocr_slide_done", index=i + 1, chars=len(text))
            except Exception as e:
                logger.warning("easyocr_slide_error", index=i + 1, error=str(e))
                results.append({"index": i + 1, "path": path, "text": "", "method": "easyocr", "error": str(e)})
        return results

    async def _ocr_slides_claude(self, image_paths: list[str]) -> list[dict]:
        """Claude Haiku vision extraction — best for infographics and schemas."""
        import base64

        try:
            import anthropic as _anthropic
        except ImportError:
            logger.warning("anthropic_sdk_not_available")
            return [{"index": i + 1, "path": p, "text": "", "method": "claude_vision"} for i, p in enumerate(image_paths)]

        api_key = ""
        try:
            from app.config import settings
            api_key = getattr(settings, "CLAUDE_API_KEY", "") or getattr(settings, "ANTHROPIC_API_KEY", "")
        except Exception:
            pass
        if not api_key:
            import os
            api_key = os.environ.get("CLAUDE_API_KEY") or os.environ.get("ANTHROPIC_API_KEY", "")

        if not api_key:
            logger.warning("claude_vision_no_api_key")
            return [{"index": i + 1, "path": p, "text": "", "method": "claude_vision", "error": "no api key"} for i, p in enumerate(image_paths)]

        client = _anthropic.Anthropic(api_key=api_key)
        prompt = (
            "Extract ALL text from this image exactly as written, preserving structure. "
            "If there are diagrams, comparison tables, bullet lists or schemas, describe their "
            "structure clearly. Format in clean markdown. Be thorough but concise."
        )

        results = []
        for i, path in enumerate(image_paths):
            try:
                with open(path, "rb") as f:
                    img_b64 = base64.standard_b64encode(f.read()).decode("utf-8")
                ext = os.path.splitext(path)[1].lower().lstrip(".")
                media_type = f"image/{'jpeg' if ext in ('jpg','jpeg') else ext}"

                response = client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=800,
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": img_b64}},
                            {"type": "text", "text": prompt},
                        ],
                    }],
                )
                text = response.content[0].text
                results.append({"index": i + 1, "path": path, "text": text, "method": "claude_vision"})
                logger.info("claude_vision_slide_done", index=i + 1, chars=len(text))
            except Exception as e:
                logger.warning("claude_vision_slide_error", index=i + 1, error=str(e))
                results.append({"index": i + 1, "path": path, "text": "", "method": "claude_vision", "error": str(e)})
        return results

    # ── mock mode (no library available) ─────────────────────────────────────

    def _mock_profile(self, username: str, max_reels: int) -> dict:
        return {
            "full_name": f"{username} (mock)",
            "bio": "Mock profile — install instagrapi or instaloader for real data",
            "followers": 0,
            "following": 0,
            "post_count": 0,
            "reels": [self._mock_reel(f"https://www.instagram.com/reel/mock{i}/") for i in range(min(max_reels, 2))],
        }

    def _mock_reel(self, url: str) -> dict:
        shortcode = url.rstrip("/").split("/")[-1]
        return {
            "reel_id": shortcode,
            "username": "mock_user",
            "caption": "Mock reel — no Instagram library installed #mock #demo",
            "likes": 0,
            "comments": 0,
            "views": 0,
            "duration_seconds": 30.0,
            "thumbnail_url": None,
            "reel_url": url,
            "video_url": None,
            "transcript": None,
            "transcript_language": None,
            "sentiment_label": None,
            "sentiment_score": None,
            "provider": "mock",
        }
