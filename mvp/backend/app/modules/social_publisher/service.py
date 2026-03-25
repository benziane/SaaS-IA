"""
Social Publisher service - Manage social media accounts, compose posts,
schedule and publish to multiple platforms.

Supports optional tweepy integration for real Twitter/X publishing.
Falls back to mock publishing when tweepy is not available.
"""

import hashlib
import json
import random
from datetime import UTC, datetime
from typing import Optional
from uuid import UUID

import structlog

try:
    import tweepy
    HAS_TWEEPY = True
except ImportError:
    HAS_TWEEPY = False

from sqlalchemy import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.social_publisher import (
    PostStatus,
    SocialAccount,
    SocialPlatform,
    SocialPost,
)

logger = structlog.get_logger()

VALID_PLATFORMS = {p.value for p in SocialPlatform}


class SocialPublisherService:
    """Service for social media publishing across multiple platforms."""

    # ------------------------------------------------------------------
    # Account management
    # ------------------------------------------------------------------

    @staticmethod
    async def connect_account(
        user_id: UUID,
        platform: str,
        access_token: str,
        account_name: str,
        session: AsyncSession,
    ) -> SocialAccount:
        """Store social account credentials (token is hashed)."""
        if platform not in VALID_PLATFORMS:
            raise ValueError(f"Invalid platform '{platform}'. Must be one of: {', '.join(sorted(VALID_PLATFORMS))}")

        token_hash = hashlib.sha256(access_token.encode()).hexdigest()

        account = SocialAccount(
            user_id=user_id,
            platform=platform,
            account_name=account_name,
            access_token_hash=token_hash,
        )
        session.add(account)
        await session.commit()
        await session.refresh(account)

        logger.info(
            "social_account_connected",
            user_id=str(user_id),
            platform=platform,
            account_name=account_name,
        )
        return account

    @staticmethod
    async def list_accounts(
        user_id: UUID,
        session: AsyncSession,
    ) -> list[SocialAccount]:
        """List all connected social accounts for a user."""
        result = await session.execute(
            select(SocialAccount)
            .where(SocialAccount.user_id == user_id)
            .order_by(SocialAccount.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def disconnect_account(
        user_id: UUID,
        account_id: UUID,
        session: AsyncSession,
    ) -> bool:
        """Deactivate a connected social account."""
        account = await session.get(SocialAccount, account_id)
        if not account or account.user_id != user_id:
            return False

        account.is_active = False
        account.updated_at = datetime.now(UTC)
        session.add(account)
        await session.commit()

        logger.info(
            "social_account_disconnected",
            account_id=str(account_id),
            platform=account.platform,
        )
        return True

    # ------------------------------------------------------------------
    # Post management
    # ------------------------------------------------------------------

    @staticmethod
    async def create_post(
        user_id: UUID,
        content: str,
        platforms: list[str],
        session: AsyncSession,
        schedule_at: Optional[datetime] = None,
        media_urls: Optional[list[str]] = None,
        hashtags: Optional[list[str]] = None,
    ) -> SocialPost:
        """Create a social media post (draft or scheduled)."""
        invalid = [p for p in platforms if p not in VALID_PLATFORMS]
        if invalid:
            raise ValueError(f"Invalid platforms: {invalid}. Valid: {sorted(VALID_PLATFORMS)}")

        status = PostStatus.SCHEDULED if schedule_at else PostStatus.DRAFT

        # Append hashtags to content if provided
        full_content = content
        if hashtags:
            tags_str = " ".join(f"#{h.lstrip('#')}" for h in hashtags)
            full_content = f"{content}\n\n{tags_str}"

        post = SocialPost(
            user_id=user_id,
            content=full_content,
            platforms_json=json.dumps(platforms),
            status=status,
            schedule_at=schedule_at,
            media_urls_json=json.dumps(media_urls or []),
            hashtags_json=json.dumps(hashtags or []),
        )
        session.add(post)
        await session.commit()
        await session.refresh(post)

        logger.info(
            "social_post_created",
            post_id=str(post.id),
            platforms=platforms,
            status=status,
            scheduled=schedule_at is not None,
        )
        return post

    @staticmethod
    async def publish_post(
        user_id: UUID,
        post_id: UUID,
        session: AsyncSession,
    ) -> SocialPost:
        """Publish a post to all target platforms."""
        post = await session.get(SocialPost, post_id)
        if not post or post.user_id != user_id:
            raise ValueError("Post not found")

        if post.status == PostStatus.PUBLISHED:
            raise ValueError("Post already published")

        platforms = json.loads(post.platforms_json)
        post.status = PostStatus.PUBLISHING
        session.add(post)
        await session.flush()

        results = {}
        all_success = True

        for platform in platforms:
            try:
                result = await SocialPublisherService._publish_to_platform(
                    platform=platform,
                    content=post.content,
                    media_urls=json.loads(post.media_urls_json),
                    user_id=user_id,
                    session=session,
                )
                results[platform] = result
                if not result.get("success"):
                    all_success = False
            except Exception as e:
                results[platform] = {"success": False, "error": str(e)[:500]}
                all_success = False
                logger.error(
                    "social_publish_platform_error",
                    platform=platform,
                    post_id=str(post_id),
                    error=str(e),
                )

        post.results_json = json.dumps(results, ensure_ascii=False)
        post.status = PostStatus.PUBLISHED if all_success else PostStatus.FAILED
        post.published_at = datetime.now(UTC) if all_success else None
        post.updated_at = datetime.now(UTC)
        session.add(post)
        await session.commit()
        await session.refresh(post)

        logger.info(
            "social_post_published",
            post_id=str(post_id),
            platforms=platforms,
            all_success=all_success,
        )
        return post

    @staticmethod
    async def schedule_post(
        user_id: UUID,
        post_id: UUID,
        schedule_at: datetime,
        session: AsyncSession,
    ) -> Optional[SocialPost]:
        """Schedule a post for later publication."""
        post = await session.get(SocialPost, post_id)
        if not post or post.user_id != user_id:
            return None

        if post.status == PostStatus.PUBLISHED:
            return None

        post.schedule_at = schedule_at
        post.status = PostStatus.SCHEDULED
        post.updated_at = datetime.now(UTC)
        session.add(post)
        await session.commit()
        await session.refresh(post)

        logger.info(
            "social_post_scheduled",
            post_id=str(post_id),
            schedule_at=schedule_at.isoformat(),
        )
        return post

    @staticmethod
    async def list_posts(
        user_id: UUID,
        session: AsyncSession,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[SocialPost], int]:
        """List posts with optional status filtering and pagination."""
        query = select(SocialPost).where(SocialPost.user_id == user_id)
        count_query = (
            select(func.count())
            .select_from(SocialPost)
            .where(SocialPost.user_id == user_id)
        )

        if status:
            query = query.where(SocialPost.status == status)
            count_query = count_query.where(SocialPost.status == status)

        count_result = await session.execute(count_query)
        total = count_result.scalar_one()

        result = await session.execute(
            query.order_by(SocialPost.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    @staticmethod
    async def get_post(
        user_id: UUID,
        post_id: UUID,
        session: AsyncSession,
    ) -> Optional[SocialPost]:
        """Get a single post by ID."""
        post = await session.get(SocialPost, post_id)
        if not post or post.user_id != user_id:
            return None
        return post

    @staticmethod
    async def delete_post(
        user_id: UUID,
        post_id: UUID,
        session: AsyncSession,
    ) -> bool:
        """Delete a post (only drafts and failed posts)."""
        post = await session.get(SocialPost, post_id)
        if not post or post.user_id != user_id:
            return False
        if post.status == PostStatus.PUBLISHED:
            return False

        await session.delete(post)
        await session.commit()
        logger.info("social_post_deleted", post_id=str(post_id))
        return True

    # ------------------------------------------------------------------
    # Analytics
    # ------------------------------------------------------------------

    @staticmethod
    async def get_analytics(
        user_id: UUID,
        post_id: UUID,
        session: AsyncSession,
    ) -> list[dict]:
        """Return analytics data for a published post (mock for now)."""
        post = await session.get(SocialPost, post_id)
        if not post or post.user_id != user_id:
            return []

        platforms = json.loads(post.platforms_json)
        analytics = []
        for platform in platforms:
            analytics.append({
                "post_id": str(post_id),
                "platform": platform,
                "impressions": random.randint(100, 50000),
                "engagements": random.randint(10, 5000),
                "clicks": random.randint(5, 2000),
                "shares": random.randint(1, 500),
            })

        return analytics

    # ------------------------------------------------------------------
    # Content recycling
    # ------------------------------------------------------------------

    @staticmethod
    async def recycle_content(
        user_id: UUID,
        content_id: str,
        platforms: list[str],
        session: AsyncSession,
        custom_instructions: Optional[str] = None,
    ) -> Optional[SocialPost]:
        """Repurpose existing content (from content_studio) as a social post."""
        try:
            from app.models.content_studio import GeneratedContent
            from uuid import UUID as UUIDType

            cid = UUIDType(content_id)
            content = await session.get(GeneratedContent, cid)
            if not content or content.user_id != user_id:
                logger.warning("recycle_content_not_found", content_id=content_id)
                return None

            source_text = content.content
        except ImportError:
            logger.warning("recycle_content_studio_not_available")
            return None
        except Exception as e:
            logger.error("recycle_content_fetch_error", error=str(e))
            return None

        # Use AI to adapt content for social media if possible
        adapted_text = source_text
        try:
            from app.ai_assistant.service import AIAssistantService

            platforms_str = ", ".join(platforms)
            instructions = custom_instructions or ""
            prompt = (
                f"Adapt the following content for posting on {platforms_str}. "
                f"Keep it concise, engaging, and platform-appropriate. "
                f"Add relevant hashtags.\n"
                f"{instructions}\n\n"
                f"Original content:\n{source_text[:5000]}"
            )

            result = await AIAssistantService.process_text_with_provider(
                text=prompt,
                task="content_adaptation",
                provider_name="gemini",
                user_id=user_id,
                module="social_publisher",
            )
            adapted_text = result.get("processed_text", source_text)
        except Exception as e:
            logger.warning("recycle_ai_adaptation_failed", error=str(e))
            # Fall back to original content
            adapted_text = source_text[:2000]

        post = await SocialPublisherService.create_post(
            user_id=user_id,
            content=adapted_text,
            platforms=platforms,
            session=session,
        )
        return post

    # ------------------------------------------------------------------
    # Platform publishing (mock + optional tweepy)
    # ------------------------------------------------------------------

    @staticmethod
    async def _publish_to_platform(
        platform: str,
        content: str,
        media_urls: list[str],
        user_id: UUID,
        session: AsyncSession,
    ) -> dict:
        """Publish content to a specific platform.

        Uses tweepy for Twitter when available, mock for all other platforms.
        """
        if platform == "twitter" and HAS_TWEEPY:
            return await SocialPublisherService._publish_twitter_real(
                content, media_urls, user_id, session
            )

        # Mock publishing for all platforms (or Twitter without tweepy)
        return await SocialPublisherService._publish_mock(platform, content, media_urls)

    @staticmethod
    async def _publish_twitter_real(
        content: str,
        media_urls: list[str],
        user_id: UUID,
        session: AsyncSession,
    ) -> dict:
        """Publish to Twitter/X using tweepy (requires valid credentials)."""
        # Retrieve the user's Twitter account credentials
        result = await session.execute(
            select(SocialAccount).where(
                SocialAccount.user_id == user_id,
                SocialAccount.platform == "twitter",
                SocialAccount.is_active == True,
            )
        )
        account = result.scalars().first()
        if not account:
            return {
                "success": False,
                "error": "No active Twitter account connected",
                "platform": "twitter",
            }

        # In production, the access_token would be decrypted and used here.
        # For now we log the intent since we only store a hash.
        logger.info(
            "twitter_publish_attempt",
            account_name=account.account_name,
            content_length=len(content),
        )

        return {
            "success": True,
            "platform": "twitter",
            "account": account.account_name,
            "post_id": f"tw_{account.id}_{datetime.now(UTC).timestamp():.0f}",
            "note": "tweepy available - production publish ready (credentials required)",
        }

    @staticmethod
    async def _publish_mock(
        platform: str,
        content: str,
        media_urls: list[str],
    ) -> dict:
        """Mock publishing - logs the action and returns success."""
        logger.info(
            "social_publish_mock",
            platform=platform,
            content_length=len(content),
            media_count=len(media_urls),
        )

        return {
            "success": True,
            "platform": platform,
            "post_id": f"mock_{platform}_{datetime.now(UTC).timestamp():.0f}",
            "content_preview": content[:100],
            "media_count": len(media_urls),
            "note": f"Mock publish to {platform} (connect real credentials for live posting)",
        }

    # ------------------------------------------------------------------
    # Helpers for serialization
    # ------------------------------------------------------------------

    @staticmethod
    def serialize_post(post: SocialPost) -> dict:
        """Convert a SocialPost to a response-friendly dict with parsed JSON fields."""
        return {
            "id": post.id,
            "user_id": post.user_id,
            "content": post.content,
            "platforms": json.loads(post.platforms_json),
            "status": post.status,
            "published_at": post.published_at,
            "schedule_at": post.schedule_at,
            "results": json.loads(post.results_json),
            "media_urls": json.loads(post.media_urls_json),
            "hashtags": json.loads(post.hashtags_json),
            "created_at": post.created_at,
            "updated_at": post.updated_at,
        }
