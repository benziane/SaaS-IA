"""
Content Studio service - Multi-format AI content generation from any source.

Transforms transcriptions, documents, URLs, or raw text into blog articles,
Twitter threads, LinkedIn posts, newsletters, and more.
Includes readability scoring via textstat when available.
"""

import json
from datetime import UTC, datetime
from typing import Optional
from uuid import UUID

import structlog

try:
    import textstat
    HAS_TEXTSTAT = True
except ImportError:
    HAS_TEXTSTAT = False
from sqlalchemy import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.content_studio import (
    ContentFormat,
    ContentProject,
    ContentStatus,
    GeneratedContent,
)

logger = structlog.get_logger()

# Format-specific generation prompts
FORMAT_PROMPTS = {
    ContentFormat.BLOG_ARTICLE: """Write a comprehensive, well-structured blog article based on the following content.
Include:
- An engaging title (H1)
- An introduction hook
- 3-5 main sections with H2 headings
- Key takeaways or bullet points
- A conclusion with call to action
Target length: 800-1500 words. Use markdown formatting.""",

    ContentFormat.TWITTER_THREAD: """Create a viral Twitter/X thread (8-15 tweets) based on the following content.
Rules:
- First tweet must be a strong hook with an emoji
- Each tweet max 280 characters
- Use numbering (1/, 2/, etc.)
- Include relevant hashtags in the last tweet
- End with a CTA (follow, retweet, bookmark)
Format each tweet on a new line separated by ---""",

    ContentFormat.LINKEDIN_POST: """Write a professional LinkedIn post based on the following content.
Structure:
- Strong opening line (hook)
- 3-5 short paragraphs with line breaks
- Use relevant emojis sparingly
- Include a personal insight or lesson
- End with a question to drive engagement
- Add 3-5 relevant hashtags
Target length: 150-300 words.""",

    ContentFormat.NEWSLETTER: """Write an email newsletter based on the following content.
Structure:
- Subject line (compelling, under 60 chars)
- Preview text (under 100 chars)
- Greeting
- Introduction (why this matters)
- Main content with sections
- Key takeaways (bulleted)
- CTA button text
- Sign-off
Use a conversational, friendly tone.""",

    ContentFormat.INSTAGRAM_CAROUSEL: """Create an Instagram carousel post (8-10 slides) based on the following content.
Format for each slide:
- Slide 1: Eye-catching title/hook
- Slides 2-8: One key point per slide (keep text short, max 3 lines)
- Second-to-last slide: Summary/recap
- Last slide: CTA (save, share, follow)
Separate each slide with ---
Also provide a caption with hashtags.""",

    ContentFormat.YOUTUBE_DESCRIPTION: """Write an optimized YouTube video description based on the following content.
Include:
- First 2 lines: compelling summary (shown before "Show more")
- Timestamps/chapters (if applicable)
- Key points covered
- Links section placeholder
- Tags/keywords
- Call to action (subscribe, like, comment)
Target length: 200-500 words.""",

    ContentFormat.SEO_META: """Generate SEO metadata based on the following content.
Provide as JSON:
{
  "meta_title": "under 60 chars, keyword-rich",
  "meta_description": "under 160 chars, compelling",
  "h1": "main heading",
  "keywords": ["list", "of", "10", "relevant", "keywords"],
  "slug": "url-friendly-slug",
  "og_title": "Open Graph title",
  "og_description": "Open Graph description"
}""",

    ContentFormat.PRESS_RELEASE: """Write a professional press release based on the following content.
Structure:
- FOR IMMEDIATE RELEASE header
- Headline (compelling, newsworthy)
- Subheadline
- Dateline (city, date)
- Lead paragraph (who, what, when, where, why)
- Body (2-3 supporting paragraphs)
- Quote from stakeholder
- Boilerplate/About section
- Contact information placeholder
Use formal, journalistic tone.""",

    ContentFormat.EMAIL_CAMPAIGN: """Create an email marketing campaign based on the following content.
Provide 3 email variations:
EMAIL 1 (Awareness):
- Subject line
- Preview text
- Body (short, engaging)
- CTA

EMAIL 2 (Value):
- Subject line
- Preview text
- Body (educational)
- CTA

EMAIL 3 (Conversion):
- Subject line
- Preview text
- Body (urgency)
- CTA

Separate emails with ===.""",

    ContentFormat.PODCAST_NOTES: """Create comprehensive podcast show notes based on the following content.
Include:
- Episode title
- Episode summary (2-3 sentences)
- Key topics discussed (bulleted)
- Notable quotes
- Timestamps (estimated)
- Resources mentioned
- Guest bio (if applicable)
- Subscribe/follow links placeholder""",
}


class ContentStudioService:
    """Service for multi-format AI content generation."""

    @staticmethod
    async def create_project(
        user_id: UUID,
        title: str,
        source_type: str,
        source_text: Optional[str],
        source_id: Optional[str],
        session: AsyncSession,
        language: str = "auto",
        tone: str = "professional",
        target_audience: Optional[str] = None,
        keywords: Optional[list[str]] = None,
    ) -> ContentProject:
        """Create a new content project."""
        # If source is a transcription or document, fetch the text
        resolved_text = source_text or ""

        if source_type == "transcription" and source_id:
            resolved_text = await ContentStudioService._fetch_transcription_text(
                source_id, user_id, session
            )
        elif source_type == "document" and source_id:
            resolved_text = await ContentStudioService._fetch_document_text(
                source_id, user_id, session
            )
        elif source_type == "url" and source_text:
            resolved_text = await ContentStudioService._fetch_url_text(source_text)

        project = ContentProject(
            user_id=user_id,
            title=title,
            source_type=source_type,
            source_id=source_id,
            source_text=resolved_text[:50000],
            language=language,
            tone=tone,
            target_audience=target_audience,
            keywords=json.dumps(keywords or [], ensure_ascii=False),
        )
        session.add(project)
        await session.commit()
        await session.refresh(project)

        logger.info(
            "content_project_created",
            project_id=str(project.id),
            source_type=source_type,
            text_length=len(resolved_text),
        )
        return project

    @staticmethod
    async def generate_contents(
        project_id: UUID,
        user_id: UUID,
        formats: list[str],
        session: AsyncSession,
        provider: Optional[str] = None,
        custom_instructions: Optional[str] = None,
    ) -> list[GeneratedContent]:
        """Generate content in multiple formats for a project."""
        project = await session.get(ContentProject, project_id)
        if not project or project.user_id != user_id:
            return []

        source_text = project.source_text
        if not source_text:
            return []

        generated = []
        for fmt_str in formats:
            try:
                fmt = ContentFormat(fmt_str)
            except ValueError:
                logger.warning("content_studio_unknown_format", format=fmt_str)
                continue

            content_obj = GeneratedContent(
                project_id=project_id,
                user_id=user_id,
                format=fmt,
                status=ContentStatus.GENERATING,
                provider=provider or "gemini",
            )
            session.add(content_obj)
            await session.flush()

            try:
                result = await ContentStudioService._generate_single(
                    source_text=source_text,
                    fmt=fmt,
                    tone=project.tone,
                    target_audience=project.target_audience,
                    keywords=project.keywords,
                    language=project.language,
                    provider=provider,
                    custom_instructions=custom_instructions,
                    user_id=user_id,
                )

                content_obj.content = result.get("content", "")
                content_obj.title = result.get("title", "")
                metadata = result.get("metadata", {})
                if result.get("readability"):
                    metadata["readability"] = result["readability"]
                content_obj.metadata_json = json.dumps(
                    metadata, ensure_ascii=False
                )
                content_obj.word_count = len(content_obj.content.split())
                content_obj.status = ContentStatus.GENERATED
                content_obj.provider = result.get("provider", provider or "gemini")

            except Exception as e:
                content_obj.status = ContentStatus.FAILED
                content_obj.content = f"Generation failed: {str(e)[:500]}"
                logger.error(
                    "content_generation_failed",
                    format=fmt.value,
                    error=str(e),
                )

            session.add(content_obj)
            generated.append(content_obj)

        await session.commit()
        for c in generated:
            await session.refresh(c)

        logger.info(
            "content_generation_complete",
            project_id=str(project_id),
            formats_requested=len(formats),
            formats_generated=sum(1 for c in generated if c.status == ContentStatus.GENERATED),
        )
        return generated

    @staticmethod
    async def _generate_single(
        source_text: str,
        fmt: ContentFormat,
        tone: str,
        target_audience: Optional[str],
        keywords: Optional[str],
        language: str,
        provider: Optional[str],
        custom_instructions: Optional[str],
        user_id: Optional[UUID] = None,
    ) -> dict:
        """Generate a single format using AI."""
        from app.ai_assistant.service import AIAssistantService

        format_prompt = FORMAT_PROMPTS.get(fmt, "Generate content in the requested format.")

        context_parts = [f"Tone: {tone}"]
        if target_audience:
            context_parts.append(f"Target audience: {target_audience}")
        if keywords:
            context_parts.append(f"Keywords to include: {keywords}")
        if language and language != "auto":
            context_parts.append(f"Language: {language}")
        if custom_instructions:
            context_parts.append(f"Additional instructions: {custom_instructions}")

        context = "\n".join(context_parts)

        prompt = f"""{format_prompt}

{context}

Source content:
{source_text[:12000]}"""

        result = await AIAssistantService.process_text_with_provider(
            text=prompt,
            task="content_generation",
            provider_name=provider or "gemini",
            user_id=user_id,
            module="content_studio",
        )

        generated_text = result.get("processed_text", "")

        # Extract title if present (first # heading)
        title = ""
        lines = generated_text.split("\n")
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("# "):
                title = stripped[2:].strip()
                break
            if stripped.startswith("Subject line:") or stripped.startswith("Subject:"):
                title = stripped.split(":", 1)[1].strip()
                break

        # Compute readability metrics on the generated content
        readability = ContentStudioService._compute_readability(generated_text)

        return {
            "content": generated_text,
            "title": title,
            "provider": result.get("provider", provider or "gemini"),
            "readability": readability,
            "metadata": {
                "format": fmt.value,
                "tone": tone,
                "model": result.get("model", ""),
            },
        }

    @staticmethod
    async def list_projects(
        user_id: UUID,
        session: AsyncSession,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[ContentProject], int]:
        """List user's content projects with pagination."""
        count_result = await session.execute(
            select(func.count())
            .select_from(ContentProject)
            .where(ContentProject.user_id == user_id)
        )
        total = count_result.scalar_one()

        result = await session.execute(
            select(ContentProject)
            .where(ContentProject.user_id == user_id)
            .order_by(ContentProject.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    @staticmethod
    async def get_project_contents(
        project_id: UUID,
        user_id: UUID,
        session: AsyncSession,
    ) -> list[GeneratedContent]:
        """Get all generated content for a project."""
        result = await session.execute(
            select(GeneratedContent)
            .where(
                GeneratedContent.project_id == project_id,
                GeneratedContent.user_id == user_id,
            )
            .order_by(GeneratedContent.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def update_content(
        content_id: UUID,
        user_id: UUID,
        updates: dict,
        session: AsyncSession,
    ) -> Optional[GeneratedContent]:
        """Update a generated content piece."""
        content = await session.get(GeneratedContent, content_id)
        if not content or content.user_id != user_id:
            return None

        if "title" in updates and updates["title"] is not None:
            content.title = updates["title"]
        if "content" in updates and updates["content"] is not None:
            content.content = updates["content"]
            content.word_count = len(updates["content"].split())
        if "status" in updates and updates["status"]:
            content.status = updates["status"]
        if "scheduled_at" in updates:
            content.scheduled_at = updates["scheduled_at"]

        content.updated_at = datetime.now(UTC)
        session.add(content)
        await session.commit()
        await session.refresh(content)
        return content

    @staticmethod
    async def regenerate_content(
        content_id: UUID,
        user_id: UUID,
        session: AsyncSession,
        custom_instructions: Optional[str] = None,
        provider: Optional[str] = None,
    ) -> Optional[GeneratedContent]:
        """Regenerate a specific content piece (creates new version)."""
        content = await session.get(GeneratedContent, content_id)
        if not content or content.user_id != user_id:
            return None

        project = await session.get(ContentProject, content.project_id)
        if not project:
            return None

        content.status = ContentStatus.GENERATING
        content.version += 1
        session.add(content)
        await session.flush()

        try:
            result = await ContentStudioService._generate_single(
                source_text=project.source_text,
                fmt=content.format,
                tone=project.tone,
                target_audience=project.target_audience,
                keywords=project.keywords,
                language=project.language,
                provider=provider,
                custom_instructions=custom_instructions,
                user_id=user_id,
            )
            content.content = result.get("content", "")
            content.title = result.get("title", content.title)
            content.word_count = len(content.content.split())
            content.status = ContentStatus.GENERATED
            content.provider = result.get("provider", provider)
            content.metadata_json = json.dumps(
                result.get("metadata", {}), ensure_ascii=False
            )
        except Exception as e:
            content.status = ContentStatus.FAILED
            logger.error("content_regeneration_failed", error=str(e))

        content.updated_at = datetime.now(UTC)
        session.add(content)
        await session.commit()
        await session.refresh(content)
        return content

    @staticmethod
    async def delete_project(
        project_id: UUID,
        user_id: UUID,
        session: AsyncSession,
    ) -> bool:
        """Delete a project and all its generated content."""
        project = await session.get(ContentProject, project_id)
        if not project or project.user_id != user_id:
            return False

        # Delete generated contents
        result = await session.execute(
            select(GeneratedContent).where(
                GeneratedContent.project_id == project_id
            )
        )
        for content in result.scalars().all():
            await session.delete(content)

        await session.delete(project)
        await session.commit()

        logger.info("content_project_deleted", project_id=str(project_id))
        return True

    @staticmethod
    def _compute_readability(text: str) -> dict:
        """
        Compute readability metrics for generated content.

        Uses textstat library when available for comprehensive scoring.
        Falls back to basic word count and estimated reading time otherwise.
        """
        word_count = len(text.split())
        reading_time_minutes = round(word_count / 200, 1)

        if not HAS_TEXTSTAT:
            return {
                "word_count": word_count,
                "reading_time_minutes": reading_time_minutes,
                "source": "basic",
            }

        flesch_score = textstat.flesch_reading_ease(text)

        # Determine difficulty level based on Flesch Reading Ease
        if flesch_score >= 60:
            difficulty_level = "easy"
        elif flesch_score >= 30:
            difficulty_level = "medium"
        else:
            difficulty_level = "hard"

        return {
            "flesch_reading_ease": round(flesch_score, 1),
            "flesch_kincaid_grade": round(textstat.flesch_kincaid_grade(text), 1),
            "gunning_fog": round(textstat.gunning_fog(text), 1),
            "smog_index": round(textstat.smog_index(text), 1),
            "automated_readability_index": round(textstat.automated_readability_index(text), 1),
            "coleman_liau_index": round(textstat.coleman_liau_index(text), 1),
            "word_count": word_count,
            "reading_time_minutes": reading_time_minutes,
            "difficulty_level": difficulty_level,
            "source": "textstat",
        }

    @staticmethod
    async def _fetch_transcription_text(
        transcription_id: str, user_id: UUID, session: AsyncSession
    ) -> str:
        """Fetch transcription text as source."""
        from app.models.transcription import Transcription
        from uuid import UUID as UUIDType

        tid = UUIDType(transcription_id)
        transcription = await session.get(Transcription, tid)
        if transcription and transcription.user_id == user_id:
            return transcription.transcription_text or ""
        return ""

    @staticmethod
    async def _fetch_document_text(
        document_id: str, user_id: UUID, session: AsyncSession
    ) -> str:
        """Fetch document text as source."""
        from app.models.knowledge import Document
        from uuid import UUID as UUIDType

        did = UUIDType(document_id)
        doc = await session.get(Document, did)
        if doc and doc.user_id == user_id:
            # Retrieve chunks
            from app.models.knowledge import DocumentChunk

            result = await session.execute(
                select(DocumentChunk)
                .where(DocumentChunk.document_id == did)
                .order_by(DocumentChunk.chunk_index)
            )
            chunks = result.scalars().all()
            return "\n\n".join(c.content for c in chunks)
        return ""

    @staticmethod
    async def _fetch_url_text(url: str) -> str:
        """Crawl a URL and return extracted text."""
        try:
            from app.modules.web_crawler.service import WebCrawlerService

            result = await WebCrawlerService.scrape(
                url=url, extract_images=False, max_images=0
            )
            if result.get("success"):
                return result.get("markdown", "")
        except Exception as e:
            logger.warning("content_studio_url_fetch_failed", url=url, error=str(e))
        return ""
