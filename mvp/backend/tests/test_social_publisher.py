"""
Tests for the Social Publisher module - service, accounts, posts, scheduling, analytics.

All tests mock DB and AI providers. Uses pytest-asyncio.
"""

import json
from datetime import UTC, datetime, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.social_publisher import SocialAccount, SocialPost, PostStatus, SocialPlatform


# ---------------------------------------------------------------------------
# Helper to create a post in the DB
# ---------------------------------------------------------------------------


async def _create_post(
    session,
    user_id,
    content="Test post content",
    platforms=None,
    status=PostStatus.DRAFT,
    schedule_at=None,
):
    if platforms is None:
        platforms = ["twitter", "linkedin"]

    post = SocialPost(
        user_id=user_id,
        content=content,
        platforms_json=json.dumps(platforms),
        status=status,
        schedule_at=schedule_at,
        media_urls_json="[]",
        hashtags_json="[]",
        results_json="{}",
    )
    session.add(post)
    await session.commit()
    await session.refresh(post)
    return post


# ---------------------------------------------------------------------------
# SocialPublisherService tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestSocialPublisherService:
    """Tests for SocialPublisherService business logic."""

    async def test_connect_account(self, session):
        from app.modules.social_publisher.service import SocialPublisherService

        user_id = uuid4()
        account = await SocialPublisherService.connect_account(
            user_id=user_id,
            platform="twitter",
            access_token="oauth_token_12345",
            account_name="@testaccount",
            session=session,
        )

        assert account.platform == "twitter"
        assert account.account_name == "@testaccount"
        assert account.user_id == user_id
        assert account.is_active is True
        # Token should be hashed, not stored as plaintext
        assert account.access_token_hash != "oauth_token_12345"
        assert len(account.access_token_hash) == 64  # SHA-256 hex digest

    async def test_connect_account_invalid_platform(self, session):
        from app.modules.social_publisher.service import SocialPublisherService

        with pytest.raises(ValueError, match="Invalid platform"):
            await SocialPublisherService.connect_account(
                user_id=uuid4(),
                platform="myspace",
                access_token="token",
                account_name="test",
                session=session,
            )

    async def test_list_accounts(self, session):
        from app.modules.social_publisher.service import SocialPublisherService

        user_id = uuid4()

        await SocialPublisherService.connect_account(
            user_id=user_id,
            platform="twitter",
            access_token="tok1",
            account_name="@tw",
            session=session,
        )
        await SocialPublisherService.connect_account(
            user_id=user_id,
            platform="linkedin",
            access_token="tok2",
            account_name="John Doe",
            session=session,
        )

        accounts = await SocialPublisherService.list_accounts(user_id, session)
        assert len(accounts) == 2

    async def test_disconnect_account(self, session):
        from app.modules.social_publisher.service import SocialPublisherService

        user_id = uuid4()
        account = await SocialPublisherService.connect_account(
            user_id=user_id,
            platform="twitter",
            access_token="tok",
            account_name="@test",
            session=session,
        )

        success = await SocialPublisherService.disconnect_account(
            user_id, account.id, session
        )
        assert success is True

        await session.refresh(account)
        assert account.is_active is False

    async def test_create_post_draft(self, session):
        from app.modules.social_publisher.service import SocialPublisherService

        user_id = uuid4()
        post = await SocialPublisherService.create_post(
            user_id=user_id,
            content="Exciting AI update!",
            platforms=["twitter", "linkedin"],
            session=session,
        )

        assert post.content == "Exciting AI update!"
        assert post.status == PostStatus.DRAFT
        assert json.loads(post.platforms_json) == ["twitter", "linkedin"]

    async def test_create_post_with_hashtags(self, session):
        from app.modules.social_publisher.service import SocialPublisherService

        user_id = uuid4()
        post = await SocialPublisherService.create_post(
            user_id=user_id,
            content="Check this out",
            platforms=["twitter"],
            session=session,
            hashtags=["AI", "SaaS"],
        )

        assert "#AI" in post.content
        assert "#SaaS" in post.content

    async def test_create_post_scheduled(self, session):
        from app.modules.social_publisher.service import SocialPublisherService

        user_id = uuid4()
        future_time = datetime.now(UTC) + timedelta(days=1)

        post = await SocialPublisherService.create_post(
            user_id=user_id,
            content="Scheduled post",
            platforms=["linkedin"],
            session=session,
            schedule_at=future_time,
        )

        assert post.status == PostStatus.SCHEDULED
        # SQLite drops timezone info, so compare without tzinfo
        assert post.schedule_at.replace(tzinfo=None) == future_time.replace(tzinfo=None)

    async def test_publish_post_mock(self, session):
        from app.modules.social_publisher.service import SocialPublisherService

        user_id = uuid4()
        post = await _create_post(
            session, user_id, content="Publishing now!", platforms=["twitter"]
        )

        published = await SocialPublisherService.publish_post(
            user_id, post.id, session
        )

        assert published.status == PostStatus.PUBLISHED
        assert published.published_at is not None
        results = json.loads(published.results_json)
        assert "twitter" in results
        assert results["twitter"]["success"] is True

    async def test_publish_post_already_published(self, session):
        from app.modules.social_publisher.service import SocialPublisherService

        user_id = uuid4()
        post = await _create_post(session, user_id)
        post.status = PostStatus.PUBLISHED
        session.add(post)
        await session.commit()
        await session.refresh(post)

        with pytest.raises(ValueError, match="already published"):
            await SocialPublisherService.publish_post(user_id, post.id, session)

    async def test_schedule_post(self, session):
        from app.modules.social_publisher.service import SocialPublisherService

        user_id = uuid4()
        post = await _create_post(session, user_id)
        future = datetime.now(UTC) + timedelta(hours=6)

        scheduled = await SocialPublisherService.schedule_post(
            user_id, post.id, future, session
        )

        assert scheduled is not None
        assert scheduled.status == PostStatus.SCHEDULED
        # SQLite drops timezone info, so compare without tzinfo
        assert scheduled.schedule_at.replace(tzinfo=None) == future.replace(tzinfo=None)

    async def test_schedule_post_already_published(self, session):
        from app.modules.social_publisher.service import SocialPublisherService

        user_id = uuid4()
        post = await _create_post(session, user_id)
        post.status = PostStatus.PUBLISHED
        session.add(post)
        await session.commit()
        await session.refresh(post)

        result = await SocialPublisherService.schedule_post(
            user_id, post.id, datetime.now(UTC) + timedelta(hours=1), session
        )
        assert result is None

    async def test_list_posts_all(self, session):
        from app.modules.social_publisher.service import SocialPublisherService

        user_id = uuid4()
        await _create_post(session, user_id, content="Draft post")
        await _create_post(
            session, user_id,
            content="Scheduled post",
            status=PostStatus.SCHEDULED,
        )

        posts, total = await SocialPublisherService.list_posts(
            user_id, session
        )
        assert total == 2
        assert len(posts) == 2

    async def test_list_posts_filtered_by_status(self, session):
        from app.modules.social_publisher.service import SocialPublisherService

        user_id = uuid4()
        await _create_post(session, user_id, content="Draft")
        await _create_post(
            session, user_id,
            content="Scheduled",
            status=PostStatus.SCHEDULED,
        )

        posts, total = await SocialPublisherService.list_posts(
            user_id, session, status=PostStatus.DRAFT
        )
        assert total == 1
        assert posts[0].content == "Draft"

    async def test_get_analytics(self, session):
        from app.modules.social_publisher.service import SocialPublisherService

        user_id = uuid4()
        post = await _create_post(
            session, user_id,
            platforms=["twitter", "linkedin"],
        )

        analytics = await SocialPublisherService.get_analytics(
            user_id, post.id, session
        )

        assert len(analytics) == 2
        platforms_seen = {a["platform"] for a in analytics}
        assert "twitter" in platforms_seen
        assert "linkedin" in platforms_seen

        for a in analytics:
            assert "impressions" in a
            assert "engagements" in a
            assert "clicks" in a
            assert "shares" in a

    async def test_get_analytics_wrong_user(self, session):
        from app.modules.social_publisher.service import SocialPublisherService

        user_id = uuid4()
        post = await _create_post(session, user_id)

        analytics = await SocialPublisherService.get_analytics(
            uuid4(), post.id, session
        )
        assert analytics == []

    async def test_delete_post_draft(self, session):
        from app.modules.social_publisher.service import SocialPublisherService

        user_id = uuid4()
        post = await _create_post(session, user_id)

        deleted = await SocialPublisherService.delete_post(
            user_id, post.id, session
        )
        assert deleted is True

    async def test_delete_post_published_blocked(self, session):
        from app.modules.social_publisher.service import SocialPublisherService

        user_id = uuid4()
        post = await _create_post(session, user_id)
        post.status = PostStatus.PUBLISHED
        session.add(post)
        await session.commit()
        await session.refresh(post)

        deleted = await SocialPublisherService.delete_post(
            user_id, post.id, session
        )
        assert deleted is False

    async def test_serialize_post(self, session):
        from app.modules.social_publisher.service import SocialPublisherService

        user_id = uuid4()
        post = await _create_post(
            session, user_id,
            content="Serialize me",
            platforms=["instagram"],
        )

        data = SocialPublisherService.serialize_post(post)
        assert data["content"] == "Serialize me"
        assert data["platforms"] == ["instagram"]
        assert data["status"] == PostStatus.DRAFT
        assert isinstance(data["media_urls"], list)
        assert isinstance(data["hashtags"], list)


# ---------------------------------------------------------------------------
# Route-level auth tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestSocialPublisherRoutesAuth:
    """Test that social publisher endpoints require authentication."""

    async def test_connect_account_requires_auth(self, client):
        resp = await client.post("/api/social-publisher/accounts", json={
            "platform": "twitter",
            "access_token": "tok",
            "account_name": "@test",
        })
        assert resp.status_code in (401, 403)

    async def test_list_accounts_requires_auth(self, client):
        resp = await client.get("/api/social-publisher/accounts")
        assert resp.status_code in (401, 403)

    async def test_create_post_requires_auth(self, client):
        resp = await client.post("/api/social-publisher/posts", json={
            "content": "Test post",
            "platforms": ["twitter"],
        })
        assert resp.status_code in (401, 403)

    async def test_list_posts_requires_auth(self, client):
        resp = await client.get("/api/social-publisher/posts")
        assert resp.status_code in (401, 403)

    async def test_publish_post_requires_auth(self, client):
        fake_id = str(uuid4())
        resp = await client.post(f"/api/social-publisher/posts/{fake_id}/publish")
        assert resp.status_code in (401, 403)

    async def test_analytics_requires_auth(self, client):
        fake_id = str(uuid4())
        resp = await client.get(f"/api/social-publisher/posts/{fake_id}/analytics")
        assert resp.status_code in (401, 403)
