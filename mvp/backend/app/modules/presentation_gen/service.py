"""
Presentation Gen service - AI-powered slide deck generation.

Generates structured presentations from topics, text, or transcriptions.
Supports multiple templates and export formats.
Uses optional marp-cli for PDF/PPTX rendering when available.
"""

import json
from datetime import datetime
from typing import Optional
from uuid import UUID

import structlog

try:
    import subprocess
    _marp_check = subprocess.run(
        ["marp", "--version"], capture_output=True, timeout=5
    )
    HAS_MARP = _marp_check.returncode == 0
except Exception:
    HAS_MARP = False

from sqlalchemy import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.presentation_gen import Presentation, PresentationStatus

logger = structlog.get_logger()

# Template-specific system prompts
TEMPLATE_PROMPTS = {
    "default": "Create a clear, well-structured presentation.",
    "pitch_deck": """Create a startup pitch deck with this flow:
1. Title / Hook
2. Problem statement
3. Solution overview
4. Product demo / screenshots description
5. Market opportunity & size
6. Business model
7. Traction & metrics
8. Team
9. Competitive advantages
10. Financial projections
11. The ask / funding needs
12. Contact & next steps""",
    "report": """Create a data-driven report presentation with:
1. Title & date
2. Executive summary
3. Key metrics / KPIs
4. Detailed findings (2-3 slides)
5. Charts & data descriptions
6. Analysis & insights
7. Recommendations
8. Next steps & timeline""",
    "tutorial": """Create an educational tutorial presentation with:
1. Title & learning objectives
2. Prerequisites / context
3. Step-by-step instructions (3-5 slides)
4. Examples & code snippets if relevant
5. Common pitfalls / FAQ
6. Practice exercises
7. Summary & resources""",
    "meeting": """Create a meeting presentation with:
1. Meeting title, date, attendees placeholder
2. Agenda overview
3. Review of previous action items
4. Discussion topics (2-4 slides)
5. Decisions made
6. Action items & owners
7. Next meeting date""",
    "proposal": """Create a business proposal presentation with:
1. Title & company branding
2. Understanding of client needs
3. Proposed solution / approach
4. Methodology & process
5. Timeline & milestones
6. Team & expertise
7. Case studies / references
8. Pricing & packages
9. Terms & next steps
10. Contact information""",
}


class PresentationGenService:
    """Service for AI-powered presentation generation."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def generate_presentation(
        self,
        user_id: UUID,
        title: str,
        topic: str,
        num_slides: int = 10,
        style: str = "professional",
        template: str = "default",
        language: str = "fr",
        source_text: Optional[str] = None,
        source_url: Optional[str] = None,
    ) -> Presentation:
        """Generate a full presentation using AI."""
        from app.ai_assistant.service import AIAssistantService

        # Resolve source URL content if provided
        resolved_source = source_text or ""
        if source_url and not resolved_source:
            resolved_source = await self._fetch_url_text(source_url)

        # Create the DB record
        presentation = Presentation(
            user_id=user_id,
            title=title,
            topic=topic,
            num_slides=num_slides,
            style=style,
            template=template,
            slides_json="[]",
            status=PresentationStatus.GENERATING,
            format="json",
            source_text=resolved_source[:50000] if resolved_source else None,
        )
        self.session.add(presentation)
        await self.session.flush()

        try:
            slides = await self._generate_slides(
                title=title,
                topic=topic,
                num_slides=num_slides,
                style=style,
                template=template,
                language=language,
                source_text=resolved_source,
                user_id=user_id,
            )

            presentation.slides_json = json.dumps(slides, ensure_ascii=False)
            presentation.num_slides = len(slides)
            presentation.status = PresentationStatus.READY

        except Exception as e:
            presentation.status = PresentationStatus.ERROR
            presentation.slides_json = json.dumps(
                [{"slide_number": 1, "title": "Error", "content": str(e)[:500], "notes": None, "layout": "title_content"}],
                ensure_ascii=False,
            )
            logger.error(
                "presentation_generation_failed",
                presentation_id=str(presentation.id),
                error=str(e),
            )

        presentation.updated_at = datetime.utcnow()
        self.session.add(presentation)
        await self.session.commit()
        await self.session.refresh(presentation)

        logger.info(
            "presentation_generated",
            presentation_id=str(presentation.id),
            num_slides=presentation.num_slides,
            template=template,
            status=presentation.status,
        )
        return presentation

    async def _generate_slides(
        self,
        title: str,
        topic: str,
        num_slides: int,
        style: str,
        template: str,
        language: str,
        source_text: Optional[str],
        user_id: Optional[UUID] = None,
    ) -> list[dict]:
        """Generate slide content using AI provider."""
        from app.ai_assistant.service import AIAssistantService

        template_guidance = TEMPLATE_PROMPTS.get(template, TEMPLATE_PROMPTS["default"])

        lang_instruction = {
            "fr": "Write ALL slide content in French.",
            "en": "Write ALL slide content in English.",
            "es": "Write ALL slide content in Spanish.",
            "de": "Write ALL slide content in German.",
        }.get(language, f"Write ALL slide content in language code: {language}.")

        source_section = ""
        if source_text:
            source_section = f"""

Use the following source material as the basis for the presentation content:
---
{source_text[:12000]}
---"""

        prompt = f"""You are a presentation designer. Generate exactly {num_slides} slides for a presentation.

Title: {title}
Topic: {topic}
Style: {style}
{lang_instruction}

Template guidance:
{template_guidance}
{source_section}

Return ONLY a valid JSON array. Each element must be an object with these exact keys:
- "slide_number": integer starting at 1
- "title": string, the slide title
- "content": string, the slide body content (use markdown formatting: bullet points, bold, etc.)
- "notes": string or null, speaker notes for this slide
- "layout": string, one of "title_slide", "title_content", "two_column", "image_text", "bullets", "quote", "section_header", "blank"

The first slide should use layout "title_slide".
Section transitions should use "section_header".
Most content slides should use "title_content" or "bullets".

Return ONLY the JSON array, no other text."""

        result = await AIAssistantService.process_text_with_provider(
            text=prompt,
            task="presentation_generation",
            provider_name="gemini",
            user_id=user_id,
            module="presentation_gen",
        )

        raw_text = result.get("processed_text", "")
        slides = self._parse_slides_json(raw_text, num_slides)
        return slides

    @staticmethod
    def _parse_slides_json(raw_text: str, expected_count: int) -> list[dict]:
        """Parse AI response into structured slides, with fallback."""
        # Try to extract JSON array from the response
        text = raw_text.strip()

        # Remove markdown code fences if present
        if text.startswith("```"):
            lines = text.split("\n")
            # Remove first line (```json) and last line (```)
            lines = [l for l in lines if not l.strip().startswith("```")]
            text = "\n".join(lines).strip()

        try:
            slides = json.loads(text)
            if isinstance(slides, list):
                # Validate and normalize each slide
                normalized = []
                for i, slide in enumerate(slides):
                    normalized.append({
                        "slide_number": slide.get("slide_number", i + 1),
                        "title": str(slide.get("title", f"Slide {i + 1}")),
                        "content": str(slide.get("content", "")),
                        "notes": slide.get("notes") if slide.get("notes") else None,
                        "layout": str(slide.get("layout", "title_content")),
                    })
                return normalized
        except (json.JSONDecodeError, TypeError):
            pass

        # Fallback: create slides from raw text paragraphs
        logger.warning("presentation_slides_parse_fallback", text_length=len(raw_text))
        paragraphs = [p.strip() for p in raw_text.split("\n\n") if p.strip()]
        slides = []
        for i, para in enumerate(paragraphs[:expected_count]):
            lines = para.split("\n")
            slide_title = lines[0].lstrip("#").strip() if lines else f"Slide {i + 1}"
            slide_content = "\n".join(lines[1:]).strip() if len(lines) > 1 else para
            slides.append({
                "slide_number": i + 1,
                "title": slide_title[:300],
                "content": slide_content[:5000],
                "notes": None,
                "layout": "title_slide" if i == 0 else "title_content",
            })

        # Ensure at least one slide
        if not slides:
            slides = [{
                "slide_number": 1,
                "title": "Presentation",
                "content": raw_text[:5000],
                "notes": None,
                "layout": "title_slide",
            }]

        return slides

    async def list_presentations(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Presentation], int]:
        """List user's presentations with pagination."""
        count_result = await self.session.execute(
            select(func.count())
            .select_from(Presentation)
            .where(Presentation.user_id == user_id)
        )
        total = count_result.scalar_one()

        result = await self.session.execute(
            select(Presentation)
            .where(Presentation.user_id == user_id)
            .order_by(Presentation.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    async def get_presentation(
        self,
        user_id: UUID,
        presentation_id: UUID,
    ) -> Optional[Presentation]:
        """Get a single presentation with slides."""
        presentation = await self.session.get(Presentation, presentation_id)
        if not presentation or presentation.user_id != user_id:
            return None
        return presentation

    async def update_slide(
        self,
        user_id: UUID,
        presentation_id: UUID,
        slide_number: int,
        updates: dict,
    ) -> Optional[Presentation]:
        """Update a single slide by number."""
        presentation = await self.session.get(Presentation, presentation_id)
        if not presentation or presentation.user_id != user_id:
            return None

        slides = json.loads(presentation.slides_json)

        # Find the slide by number
        slide_idx = None
        for i, s in enumerate(slides):
            if s.get("slide_number") == slide_number:
                slide_idx = i
                break

        if slide_idx is None:
            return None

        if "title" in updates and updates["title"] is not None:
            slides[slide_idx]["title"] = updates["title"]
        if "content" in updates and updates["content"] is not None:
            slides[slide_idx]["content"] = updates["content"]
        if "notes" in updates and updates["notes"] is not None:
            slides[slide_idx]["notes"] = updates["notes"]
        if "layout" in updates and updates["layout"] is not None:
            slides[slide_idx]["layout"] = updates["layout"]

        presentation.slides_json = json.dumps(slides, ensure_ascii=False)
        presentation.updated_at = datetime.utcnow()
        self.session.add(presentation)
        await self.session.commit()
        await self.session.refresh(presentation)
        return presentation

    async def add_slide(
        self,
        user_id: UUID,
        presentation_id: UUID,
        after_slide: int,
        slide_data: dict,
    ) -> Optional[Presentation]:
        """Insert a new slide after a given position."""
        presentation = await self.session.get(Presentation, presentation_id)
        if not presentation or presentation.user_id != user_id:
            return None

        slides = json.loads(presentation.slides_json)

        # Determine insertion index
        insert_idx = 0
        for i, s in enumerate(slides):
            if s.get("slide_number") == after_slide:
                insert_idx = i + 1
                break
        else:
            # If after_slide not found, append at end
            insert_idx = len(slides)

        new_slide = {
            "slide_number": after_slide + 1,
            "title": slide_data.get("title", "New Slide"),
            "content": slide_data.get("content", ""),
            "notes": slide_data.get("notes"),
            "layout": slide_data.get("layout", "title_content"),
        }
        slides.insert(insert_idx, new_slide)

        # Re-number all slides
        for i, s in enumerate(slides):
            s["slide_number"] = i + 1

        presentation.slides_json = json.dumps(slides, ensure_ascii=False)
        presentation.num_slides = len(slides)
        presentation.updated_at = datetime.utcnow()
        self.session.add(presentation)
        await self.session.commit()
        await self.session.refresh(presentation)
        return presentation

    async def remove_slide(
        self,
        user_id: UUID,
        presentation_id: UUID,
        slide_number: int,
    ) -> Optional[Presentation]:
        """Remove a slide by number."""
        presentation = await self.session.get(Presentation, presentation_id)
        if not presentation or presentation.user_id != user_id:
            return None

        slides = json.loads(presentation.slides_json)

        # Must keep at least one slide
        if len(slides) <= 1:
            return None

        slides = [s for s in slides if s.get("slide_number") != slide_number]

        # Re-number
        for i, s in enumerate(slides):
            s["slide_number"] = i + 1

        presentation.slides_json = json.dumps(slides, ensure_ascii=False)
        presentation.num_slides = len(slides)
        presentation.updated_at = datetime.utcnow()
        self.session.add(presentation)
        await self.session.commit()
        await self.session.refresh(presentation)
        return presentation

    async def export_presentation(
        self,
        user_id: UUID,
        presentation_id: UUID,
        export_format: str = "html",
    ) -> Optional[dict]:
        """Export presentation to HTML, Markdown, or PDF (mock)."""
        presentation = await self.session.get(Presentation, presentation_id)
        if not presentation or presentation.user_id != user_id:
            return None

        slides = json.loads(presentation.slides_json)

        if export_format == "markdown":
            content = self._export_markdown(presentation.title, slides)
            return {"format": "markdown", "content": content, "filename": f"{presentation.title}.md"}

        if export_format == "html":
            content = self._export_html(presentation.title, presentation.style, slides)
            return {"format": "html", "content": content, "filename": f"{presentation.title}.html"}

        if export_format == "pdf":
            if HAS_MARP:
                content = self._export_marp_markdown(presentation.title, slides)
                return {
                    "format": "pdf",
                    "content": content,
                    "filename": f"{presentation.title}.pdf",
                    "note": "Marp CLI available - use `marp --pdf` to render",
                }
            else:
                return {
                    "format": "pdf",
                    "content": None,
                    "filename": f"{presentation.title}.pdf",
                    "note": "PDF export requires marp-cli. Install with: npm install -g @marp-team/marp-cli",
                }

        return None

    @staticmethod
    def _export_markdown(title: str, slides: list[dict]) -> str:
        """Export slides as Markdown."""
        parts = [f"# {title}\n"]
        for slide in slides:
            parts.append(f"---\n\n## {slide['title']}\n\n{slide['content']}")
            if slide.get("notes"):
                parts.append(f"\n> Speaker notes: {slide['notes']}")
            parts.append("")
        return "\n".join(parts)

    @staticmethod
    def _export_marp_markdown(title: str, slides: list[dict]) -> str:
        """Export slides as Marp-compatible Markdown."""
        parts = [
            "---",
            "marp: true",
            "theme: default",
            f"title: {title}",
            "paginate: true",
            "---\n",
        ]
        for i, slide in enumerate(slides):
            if i > 0:
                parts.append("\n---\n")
            parts.append(f"## {slide['title']}\n")
            parts.append(slide["content"])
            if slide.get("notes"):
                parts.append(f"\n<!--\n{slide['notes']}\n-->")
        return "\n".join(parts)

    @staticmethod
    def _export_html(title: str, style: str, slides: list[dict]) -> str:
        """Export slides as a self-contained HTML presentation."""
        style_colors = {
            "professional": ("#1a1a2e", "#e0e0e0", "#0f3460", "#16213e"),
            "creative": ("#ff6b6b", "#feca57", "#48dbfb", "#ff9ff3"),
            "minimal": ("#ffffff", "#333333", "#f5f5f5", "#e0e0e0"),
            "corporate": ("#003366", "#ffffff", "#004488", "#e8f0fe"),
            "academic": ("#2c3e50", "#ecf0f1", "#3498db", "#f8f9fa"),
            "dark": ("#0d1117", "#c9d1d9", "#161b22", "#21262d"),
            "colorful": ("#6c5ce7", "#fd79a8", "#00cec9", "#fdcb6e"),
        }
        bg, fg, accent, card_bg = style_colors.get(style, style_colors["professional"])

        slides_html = []
        for slide in slides:
            content_html = slide["content"].replace("\n", "<br>")
            slides_html.append(
                f'<section class="slide" data-layout="{slide.get("layout", "title_content")}">'
                f'<h2>{slide["title"]}</h2>'
                f'<div class="slide-content">{content_html}</div>'
                f"</section>"
            )

        joined_slides = "\n".join(slides_html)
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: 'Segoe UI', system-ui, sans-serif; background: {bg}; color: {fg}; }}
.slide {{
  min-height: 100vh; display: flex; flex-direction: column;
  justify-content: center; padding: 4rem 8rem;
  border-bottom: 2px solid {accent};
}}
.slide h2 {{ font-size: 2.5rem; margin-bottom: 2rem; color: {accent}; }}
.slide-content {{ font-size: 1.3rem; line-height: 1.8; }}
.slide[data-layout="title_slide"] {{ text-align: center; }}
.slide[data-layout="title_slide"] h2 {{ font-size: 3.5rem; }}
.slide[data-layout="section_header"] {{ text-align: center; background: {card_bg}; }}
.slide[data-layout="quote"] {{ font-style: italic; text-align: center; }}
</style>
</head>
<body>
{joined_slides}
<script>
document.addEventListener('keydown', e => {{
  const slides = document.querySelectorAll('.slide');
  const current = Math.round(window.scrollY / window.innerHeight);
  if (e.key === 'ArrowRight' || e.key === 'ArrowDown' || e.key === ' ') {{
    e.preventDefault();
    if (current < slides.length - 1) slides[current + 1].scrollIntoView({{ behavior: 'smooth' }});
  }} else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {{
    e.preventDefault();
    if (current > 0) slides[current - 1].scrollIntoView({{ behavior: 'smooth' }});
  }}
}});
</script>
</body>
</html>"""

    @staticmethod
    def get_templates() -> list[dict]:
        """Return available presentation templates."""
        from app.modules.presentation_gen.schemas import AVAILABLE_TEMPLATES
        return AVAILABLE_TEMPLATES

    async def generate_from_transcript(
        self,
        user_id: UUID,
        transcript_id: str,
        title: Optional[str] = None,
        num_slides: int = 10,
        style: str = "professional",
        template: str = "default",
        language: str = "fr",
    ) -> Optional[Presentation]:
        """Generate a presentation from an existing transcription."""
        from app.models.transcription import Transcription
        from uuid import UUID as UUIDType

        tid = UUIDType(transcript_id)
        transcription = await self.session.get(Transcription, tid)
        if not transcription or transcription.user_id != user_id:
            return None

        source_text = transcription.text or ""
        if not source_text:
            return None

        resolved_title = title or f"Presentation - {transcription.video_url[:60]}"

        return await self.generate_presentation(
            user_id=user_id,
            title=resolved_title,
            topic=f"Presentation based on transcription: {resolved_title}",
            num_slides=num_slides,
            style=style,
            template=template,
            language=language,
            source_text=source_text,
        )

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
            logger.warning("presentation_url_fetch_failed", url=url, error=str(e))
        return ""
