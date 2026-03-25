"""
Audio Studio service - Podcast/audio editing studio with AI-powered features.

Supports pydub for audio manipulation and noisereduce for noise reduction.
Falls back gracefully when optional dependencies are unavailable.
"""

import asyncio
import json
import os
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Optional
from uuid import UUID, uuid4
from xml.etree.ElementTree import Element, SubElement, tostring

import structlog
from sqlalchemy import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.audio_studio import AudioFile, AudioFileStatus, PodcastEpisode

logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# Optional dependency detection (auto-detect + fallback pattern)
# ---------------------------------------------------------------------------

HAS_PYDUB = False
try:
    from pydub import AudioSegment
    from pydub.silence import detect_silence
    HAS_PYDUB = True
    logger.info("audio_studio_pydub_available")
except ImportError:
    logger.warning("audio_studio_pydub_unavailable", fallback="metadata_mock")

HAS_NOISEREDUCE = False
try:
    import noisereduce  # noqa: F401
    import numpy as np  # noqa: F401
    HAS_NOISEREDUCE = True
    logger.info("audio_studio_noisereduce_available")
except ImportError:
    logger.warning("audio_studio_noisereduce_unavailable", fallback="skip_noise_reduction")

# Base upload directory
UPLOAD_BASE = Path(os.getenv("UPLOAD_DIR", "uploads")) / "audio_studio"


def _ensure_user_dir(user_id: UUID, audio_id: UUID) -> Path:
    """Create and return the upload directory for a specific audio file."""
    d = UPLOAD_BASE / str(user_id) / str(audio_id)
    d.mkdir(parents=True, exist_ok=True)
    return d


class AudioStudioService:
    """Service for podcast/audio editing with AI-powered features."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # -----------------------------------------------------------------------
    # CRUD
    # -----------------------------------------------------------------------

    async def upload_audio(self, user_id: UUID, file_bytes: bytes, original_filename: str) -> AudioFile:
        """Save audio file, extract metadata, and persist record."""
        audio_id = uuid4()
        ext = Path(original_filename).suffix.lower() or ".mp3"
        fmt = ext.lstrip(".")
        filename = f"{audio_id}{ext}"
        dest_dir = _ensure_user_dir(user_id, audio_id)
        file_path = dest_dir / filename

        # Write bytes to disk
        await asyncio.to_thread(file_path.write_bytes, file_bytes)
        file_size_kb = len(file_bytes) // 1024

        # Extract metadata
        duration = 0.0
        sample_rate = 44100
        channels = 1

        if HAS_PYDUB:
            try:
                seg = await asyncio.to_thread(AudioSegment.from_file, str(file_path))
                duration = len(seg) / 1000.0
                sample_rate = seg.frame_rate
                channels = seg.channels
            except Exception as e:
                logger.warning("audio_metadata_extraction_failed", error=str(e))
        else:
            # Rough estimate: file_size / (bitrate / 8)
            duration = max(1.0, len(file_bytes) / 16000)

        record = AudioFile(
            id=audio_id,
            user_id=user_id,
            filename=filename,
            original_filename=original_filename,
            duration_seconds=round(duration, 2),
            sample_rate=sample_rate,
            channels=channels,
            format=fmt,
            file_size_kb=file_size_kb,
            status=AudioFileStatus.READY,
            file_path=str(file_path),
        )
        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)

        logger.info(
            "audio_uploaded",
            audio_id=str(audio_id),
            user_id=str(user_id),
            duration=duration,
            format=fmt,
            size_kb=file_size_kb,
            pydub=HAS_PYDUB,
        )
        return record

    async def list_audio(
        self, user_id: UUID, skip: int = 0, limit: int = 50
    ) -> tuple[list[AudioFile], int]:
        """List audio files for a user with pagination."""
        count_stmt = (
            select(func.count())
            .select_from(AudioFile)
            .where(AudioFile.user_id == user_id, AudioFile.is_deleted == False)  # noqa: E712
        )
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar_one()

        stmt = (
            select(AudioFile)
            .where(AudioFile.user_id == user_id, AudioFile.is_deleted == False)  # noqa: E712
            .order_by(AudioFile.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        items = list(result.scalars().all())
        return items, total

    async def get_audio(self, user_id: UUID, audio_id: UUID) -> Optional[AudioFile]:
        """Get a single audio file by ID, owned by user."""
        record = await self.session.get(AudioFile, audio_id)
        if not record or record.user_id != user_id or record.is_deleted:
            return None
        return record

    async def delete_audio(self, user_id: UUID, audio_id: UUID) -> bool:
        """Soft-delete an audio file."""
        record = await self.session.get(AudioFile, audio_id)
        if not record or record.user_id != user_id:
            return False
        record.is_deleted = True
        record.updated_at = datetime.now(UTC)
        self.session.add(record)
        await self.session.commit()
        logger.info("audio_deleted", audio_id=str(audio_id))
        return True

    # -----------------------------------------------------------------------
    # EDIT (non-destructive)
    # -----------------------------------------------------------------------

    async def edit_audio(
        self, user_id: UUID, audio_id: UUID, operations: list[dict]
    ) -> AudioFile:
        """Apply a sequence of edit operations. Saves result as a new file (non-destructive)."""
        record = await self.get_audio(user_id, audio_id)
        if not record:
            raise ValueError("Audio file not found")

        if not HAS_PYDUB:
            raise RuntimeError("pydub is required for audio editing but is not installed")

        record.status = AudioFileStatus.PROCESSING
        record.updated_at = datetime.now(UTC)
        self.session.add(record)
        await self.session.commit()

        try:
            seg = await asyncio.to_thread(AudioSegment.from_file, record.file_path)

            for op in operations:
                op_type = op.get("type", "")
                params = op.get("params", {})
                seg = await self._apply_operation(seg, op_type, params, user_id)

            # Save edited version as new file alongside original
            edited_id = uuid4()
            ext = Path(record.filename).suffix or ".mp3"
            edited_filename = f"{edited_id}_edited{ext}"
            dest_dir = Path(record.file_path).parent
            edited_path = dest_dir / edited_filename
            fmt = ext.lstrip(".")

            export_format = fmt if fmt != "mp3" else "mp3"
            await asyncio.to_thread(seg.export, str(edited_path), format=export_format)

            # Update record with edited file info
            record.file_path = str(edited_path)
            record.filename = edited_filename
            record.duration_seconds = round(len(seg) / 1000.0, 2)
            record.sample_rate = seg.frame_rate
            record.channels = seg.channels
            record.file_size_kb = os.path.getsize(str(edited_path)) // 1024
            record.status = AudioFileStatus.READY
            record.updated_at = datetime.now(UTC)
            self.session.add(record)
            await self.session.commit()
            await self.session.refresh(record)

            logger.info("audio_edited", audio_id=str(audio_id), operations=len(operations))
            return record

        except Exception as e:
            record.status = AudioFileStatus.FAILED
            record.updated_at = datetime.now(UTC)
            self.session.add(record)
            await self.session.commit()
            logger.error("audio_edit_failed", audio_id=str(audio_id), error=str(e))
            raise

    async def _apply_operation(
        self, seg: "AudioSegment", op_type: str, params: dict, user_id: UUID
    ) -> "AudioSegment":
        """Apply a single edit operation to an AudioSegment."""
        if op_type == "trim":
            start_ms = int(params.get("start", 0) * 1000)
            end_ms = int(params.get("end", len(seg) / 1000) * 1000)
            return seg[start_ms:end_ms]

        elif op_type == "fade_in":
            duration_ms = int(params.get("duration", 2) * 1000)
            return seg.fade_in(duration_ms)

        elif op_type == "fade_out":
            duration_ms = int(params.get("duration", 2) * 1000)
            return seg.fade_out(duration_ms)

        elif op_type == "normalize":
            target_dbfs = params.get("target_dbfs", -20.0)
            change = target_dbfs - seg.dBFS
            return seg.apply_gain(change)

        elif op_type == "noise_reduction":
            if HAS_NOISEREDUCE:
                import noisereduce as nr
                import numpy as np

                samples = np.array(seg.get_array_of_samples(), dtype=np.float32)
                reduced = await asyncio.to_thread(
                    nr.reduce_noise,
                    y=samples,
                    sr=seg.frame_rate,
                    prop_decrease=params.get("prop_decrease", 0.8),
                )
                reduced_int = np.int16(reduced)
                new_seg = seg._spawn(reduced_int.tobytes())
                return new_seg
            else:
                logger.warning("noise_reduction_skipped", reason="noisereduce not installed")
                return seg

        elif op_type == "speed_change":
            factor = params.get("factor", 1.0)
            if factor <= 0:
                factor = 1.0
            # Adjust speed via frame_rate manipulation
            new_frame_rate = int(seg.frame_rate * factor)
            adjusted = seg._spawn(seg.raw_data, overrides={"frame_rate": new_frame_rate})
            return adjusted.set_frame_rate(seg.frame_rate)

        elif op_type == "merge":
            audio_ids = params.get("audio_ids", [])
            for merge_id in audio_ids:
                merge_record = await self.get_audio(user_id, UUID(str(merge_id)))
                if merge_record and os.path.exists(merge_record.file_path):
                    other = await asyncio.to_thread(AudioSegment.from_file, merge_record.file_path)
                    seg = seg + other
            return seg

        else:
            logger.warning("unknown_edit_operation", op_type=op_type)
            return seg

    # -----------------------------------------------------------------------
    # TRANSCRIPTION
    # -----------------------------------------------------------------------

    async def transcribe_audio(self, user_id: UUID, audio_id: UUID) -> AudioFile:
        """Transcribe the audio file using the platform's transcription service."""
        record = await self.get_audio(user_id, audio_id)
        if not record:
            raise ValueError("Audio file not found")

        try:
            from app.modules.transcription.service import TranscriptionService

            result = await TranscriptionService.smart_transcribe(
                video_url=record.file_path,
                language="auto",
                prefer_provider="auto",
            )
            transcript_text = result.get("text", "")
        except Exception as e:
            logger.warning("smart_transcribe_fallback", error=str(e))
            # Fallback: try faster-whisper directly
            try:
                from app.modules.transcription.whisper_local import is_available, transcribe_file
                if is_available():
                    fw_result = await transcribe_file(record.file_path)
                    transcript_text = fw_result.get("text", "")
                else:
                    transcript_text = f"[Transcription unavailable - no providers configured. File: {record.original_filename}]"
            except Exception:
                transcript_text = f"[Transcription unavailable - no providers configured. File: {record.original_filename}]"

        record.transcript = transcript_text
        record.updated_at = datetime.now(UTC)
        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)

        logger.info("audio_transcribed", audio_id=str(audio_id), text_length=len(transcript_text))
        return record

    # -----------------------------------------------------------------------
    # AI: CHAPTERS
    # -----------------------------------------------------------------------

    async def generate_chapters(self, user_id: UUID, audio_id: UUID) -> AudioFile:
        """AI-powered chapter detection from transcript."""
        record = await self.get_audio(user_id, audio_id)
        if not record:
            raise ValueError("Audio file not found")

        if not record.transcript:
            record = await self.transcribe_audio(user_id, audio_id)

        chapters = []
        try:
            from app.ai_assistant.service import AIAssistantService

            prompt = (
                "Analyze the following podcast/audio transcript and generate chapter markers.\n"
                "For each chapter, provide: title, start_time (seconds), end_time (seconds), description.\n"
                f"Total audio duration: {record.duration_seconds} seconds.\n\n"
                f"Transcript:\n{record.transcript[:8000]}\n\n"
                "Respond ONLY with a JSON array of chapter objects with keys: "
                '"title", "start_time", "end_time", "description".'
            )

            result = await AIAssistantService.process_text_with_provider(
                text=prompt,
                task="extract_chapters",
                provider_name="gemini",
                user_id=user_id,
                module="audio_studio",
            )
            raw = result.get("processed_text", "[]")
            chapters = self._parse_json_safe(raw, [])

        except Exception as e:
            logger.warning("ai_chapter_generation_failed", error=str(e))
            # Fallback: simple time-based chapters
            duration = record.duration_seconds
            chunk = max(60, duration / 5)
            t = 0.0
            idx = 1
            while t < duration:
                end = min(t + chunk, duration)
                chapters.append({
                    "title": f"Chapter {idx}",
                    "start_time": round(t, 1),
                    "end_time": round(end, 1),
                    "description": "",
                })
                t = end
                idx += 1

        record.chapters_json = json.dumps(chapters, ensure_ascii=False)
        record.updated_at = datetime.now(UTC)
        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)

        logger.info("chapters_generated", audio_id=str(audio_id), count=len(chapters))
        return record

    # -----------------------------------------------------------------------
    # AI: SHOW NOTES
    # -----------------------------------------------------------------------

    async def generate_show_notes(self, user_id: UUID, audio_id: UUID) -> dict:
        """AI-generated podcast show notes (summary, key points, links, guest info)."""
        record = await self.get_audio(user_id, audio_id)
        if not record:
            raise ValueError("Audio file not found")

        if not record.transcript:
            record = await self.transcribe_audio(user_id, audio_id)

        try:
            from app.ai_assistant.service import AIAssistantService

            prompt = (
                "Generate professional podcast show notes from this transcript.\n"
                "Include:\n"
                "1. Summary (2-3 sentences)\n"
                "2. Key Points (bullet list)\n"
                "3. Notable Quotes\n"
                "4. Resources/Links mentioned\n"
                "5. Guest information (if any)\n\n"
                f"Transcript:\n{record.transcript[:8000]}\n\n"
                'Respond with a JSON object: {"summary": "...", "key_points": [...], '
                '"quotes": [...], "resources": [...], "guests": [...]}'
            )

            result = await AIAssistantService.process_text_with_provider(
                text=prompt,
                task="generate_show_notes",
                provider_name="gemini",
                user_id=user_id,
                module="audio_studio",
            )
            raw = result.get("processed_text", "{}")
            show_notes = self._parse_json_safe(raw, {
                "summary": "Show notes generation failed.",
                "key_points": [],
                "quotes": [],
                "resources": [],
                "guests": [],
            })

        except Exception as e:
            logger.warning("show_notes_generation_failed", error=str(e))
            show_notes = {
                "summary": f"Audio file: {record.original_filename} ({record.duration_seconds}s)",
                "key_points": [],
                "quotes": [],
                "resources": [],
                "guests": [],
            }

        logger.info("show_notes_generated", audio_id=str(audio_id))
        return {"audio_id": str(audio_id), "show_notes": show_notes}

    # -----------------------------------------------------------------------
    # WAVEFORM
    # -----------------------------------------------------------------------

    async def generate_waveform(self, user_id: UUID, audio_id: UUID, points: int = 500) -> list[float]:
        """Generate waveform visualization data (~500 amplitude values)."""
        record = await self.get_audio(user_id, audio_id)
        if not record:
            raise ValueError("Audio file not found")

        if record.waveform_json:
            return json.loads(record.waveform_json)

        waveform: list[float] = []

        if HAS_PYDUB:
            try:
                seg = await asyncio.to_thread(AudioSegment.from_file, record.file_path)
                samples = seg.get_array_of_samples()
                total = len(samples)
                chunk_size = max(1, total // points)

                for i in range(0, total, chunk_size):
                    chunk = samples[i:i + chunk_size]
                    if chunk:
                        peak = max(abs(s) for s in chunk)
                        # Normalize to 0.0-1.0
                        max_val = 2 ** (seg.sample_width * 8 - 1)
                        waveform.append(round(peak / max_val, 4))

                waveform = waveform[:points]
            except Exception as e:
                logger.warning("waveform_generation_failed", error=str(e))
                waveform = [0.5] * points
        else:
            # Mock waveform
            import random
            random.seed(str(audio_id))
            waveform = [round(random.uniform(0.1, 0.9), 4) for _ in range(points)]

        record.waveform_json = json.dumps(waveform)
        record.updated_at = datetime.now(UTC)
        self.session.add(record)
        await self.session.commit()

        logger.info("waveform_generated", audio_id=str(audio_id), points=len(waveform))
        return waveform

    # -----------------------------------------------------------------------
    # SPLIT BY SILENCE
    # -----------------------------------------------------------------------

    async def split_by_silence(
        self, user_id: UUID, audio_id: UUID,
        min_silence_ms: int = 1000, silence_thresh_db: int = -40,
    ) -> list[dict]:
        """Split audio at silence points. Returns list of segments with start/end times."""
        record = await self.get_audio(user_id, audio_id)
        if not record:
            raise ValueError("Audio file not found")

        if not HAS_PYDUB:
            raise RuntimeError("pydub is required for silence detection but is not installed")

        seg = await asyncio.to_thread(AudioSegment.from_file, record.file_path)
        silences = await asyncio.to_thread(
            detect_silence, seg, min_silence_len=min_silence_ms, silence_thresh=silence_thresh_db
        )

        segments = []
        prev_end = 0
        dest_dir = Path(record.file_path).parent / "splits"
        dest_dir.mkdir(parents=True, exist_ok=True)

        for i, (sil_start, sil_end) in enumerate(silences):
            if sil_start > prev_end:
                part = seg[prev_end:sil_start]
                part_filename = f"split_{i:03d}.mp3"
                part_path = dest_dir / part_filename
                await asyncio.to_thread(part.export, str(part_path), format="mp3")
                segments.append({
                    "index": i,
                    "start_seconds": round(prev_end / 1000.0, 2),
                    "end_seconds": round(sil_start / 1000.0, 2),
                    "duration_seconds": round((sil_start - prev_end) / 1000.0, 2),
                    "filename": part_filename,
                })
            prev_end = sil_end

        # Last segment after final silence
        if prev_end < len(seg):
            part = seg[prev_end:]
            part_filename = f"split_{len(silences):03d}.mp3"
            part_path = dest_dir / part_filename
            await asyncio.to_thread(part.export, str(part_path), format="mp3")
            segments.append({
                "index": len(silences),
                "start_seconds": round(prev_end / 1000.0, 2),
                "end_seconds": round(len(seg) / 1000.0, 2),
                "duration_seconds": round((len(seg) - prev_end) / 1000.0, 2),
                "filename": part_filename,
            })

        logger.info("audio_split", audio_id=str(audio_id), segments=len(segments))
        return segments

    # -----------------------------------------------------------------------
    # EXPORT
    # -----------------------------------------------------------------------

    async def export_audio(self, user_id: UUID, audio_id: UUID, target_format: str) -> str:
        """Export audio to a different format (mp3, wav, ogg, flac). Returns file path."""
        record = await self.get_audio(user_id, audio_id)
        if not record:
            raise ValueError("Audio file not found")

        allowed_formats = {"mp3", "wav", "ogg", "flac"}
        if target_format not in allowed_formats:
            raise ValueError(f"Unsupported export format: {target_format}. Use: {allowed_formats}")

        if not HAS_PYDUB:
            raise RuntimeError("pydub is required for audio export but is not installed")

        seg = await asyncio.to_thread(AudioSegment.from_file, record.file_path)

        export_filename = f"{Path(record.filename).stem}.{target_format}"
        export_path = Path(record.file_path).parent / export_filename
        await asyncio.to_thread(seg.export, str(export_path), format=target_format)

        logger.info("audio_exported", audio_id=str(audio_id), format=target_format)
        return str(export_path)

    # -----------------------------------------------------------------------
    # PODCAST EPISODES
    # -----------------------------------------------------------------------

    async def create_podcast_episode(self, user_id: UUID, data: dict) -> PodcastEpisode:
        """Create a podcast episode with metadata."""
        audio_id = UUID(str(data["audio_id"]))
        record = await self.get_audio(user_id, audio_id)
        if not record:
            raise ValueError("Audio file not found")

        episode = PodcastEpisode(
            user_id=user_id,
            audio_id=audio_id,
            title=data["title"],
            description=data.get("description", ""),
            show_notes=data.get("show_notes"),
            publish_date=data.get("publish_date"),
            is_published=bool(data.get("publish_date")),
        )

        # Store chapters on the audio file if provided
        chapters = data.get("chapters", [])
        if chapters:
            record.chapters_json = json.dumps(
                [c.dict() if hasattr(c, "dict") else c for c in chapters],
                ensure_ascii=False,
            )
            self.session.add(record)

        self.session.add(episode)
        await self.session.commit()
        await self.session.refresh(episode)

        logger.info("podcast_episode_created", episode_id=str(episode.id), title=data["title"])
        return episode

    async def list_episodes(self, user_id: UUID, skip: int = 0, limit: int = 50) -> list[PodcastEpisode]:
        """List podcast episodes for a user."""
        stmt = (
            select(PodcastEpisode)
            .where(PodcastEpisode.user_id == user_id)
            .order_by(PodcastEpisode.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # -----------------------------------------------------------------------
    # RSS FEED
    # -----------------------------------------------------------------------

    async def generate_rss_feed(self, user_id: UUID, config: dict) -> str:
        """Generate an RSS/XML podcast feed from published episodes."""
        episodes = await self.list_episodes(user_id)

        rss = Element("rss", version="2.0")
        rss.set("xmlns:itunes", "http://www.itunes.com/dtds/podcast-1.0.dtd")
        channel = SubElement(rss, "channel")

        SubElement(channel, "title").text = config.get("title", "My Podcast")
        SubElement(channel, "description").text = config.get("description", "")
        SubElement(channel, "language").text = config.get("language", "en")
        SubElement(channel, "link").text = config.get("link", "")

        author = config.get("author", "")
        email = config.get("email", "")
        if author:
            SubElement(channel, "itunes:author").text = author
        if email:
            owner = SubElement(channel, "itunes:owner")
            SubElement(owner, "itunes:name").text = author
            SubElement(owner, "itunes:email").text = email

        category = config.get("category", "Technology")
        SubElement(channel, "itunes:category").set("text", category)

        image_url = config.get("image_url")
        if image_url:
            img = SubElement(channel, "itunes:image")
            img.set("href", image_url)

        for ep in episodes:
            if not ep.is_published:
                continue
            item = SubElement(channel, "item")
            SubElement(item, "title").text = ep.title
            SubElement(item, "description").text = ep.description or ""
            if ep.publish_date:
                SubElement(item, "pubDate").text = ep.publish_date.strftime(
                    "%a, %d %b %Y %H:%M:%S +0000"
                )
            SubElement(item, "guid").text = str(ep.id)

            # Enclosure for audio
            audio = await self.session.get(AudioFile, ep.audio_id)
            if audio:
                enc = SubElement(item, "enclosure")
                enc.set("url", f"/api/audio-studio/{audio.id}/export/mp3")
                enc.set("length", str(audio.file_size_kb * 1024))
                enc.set("type", "audio/mpeg")

                SubElement(item, "itunes:duration").text = str(int(audio.duration_seconds))

            if ep.show_notes:
                SubElement(item, "content:encoded").text = ep.show_notes

        xml_str = tostring(rss, encoding="unicode", xml_declaration=True)
        logger.info("rss_feed_generated", user_id=str(user_id), episodes=len(episodes))
        return xml_str

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    @staticmethod
    def _parse_json_safe(text: str, default):
        """Parse JSON from AI output, handling markdown code fences."""
        cleaned = text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            cleaned = "\n".join(lines).strip()
        try:
            return json.loads(cleaned)
        except (json.JSONDecodeError, ValueError):
            return default
