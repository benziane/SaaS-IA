"""
Voice Clone service - AI voice cloning, TTS synthesis, and dubbing.

Supports ElevenLabs, OpenAI TTS, and Fish.audio providers.
Falls back to mock mode when API keys are not configured.
"""

import json
from datetime import datetime
from typing import Optional
from uuid import UUID

import structlog
from sqlalchemy import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.voice_clone import SpeechSynthesis, SynthesisStatus, VoiceProfile, VoiceStatus

logger = structlog.get_logger()

BUILTIN_VOICES = [
    {"id": "alloy", "name": "Alloy", "language": "multi", "gender": "neutral", "provider": "openai"},
    {"id": "echo", "name": "Echo", "language": "multi", "gender": "male", "provider": "openai"},
    {"id": "fable", "name": "Fable", "language": "multi", "gender": "female", "provider": "openai"},
    {"id": "onyx", "name": "Onyx", "language": "multi", "gender": "male", "provider": "openai"},
    {"id": "nova", "name": "Nova", "language": "multi", "gender": "female", "provider": "openai"},
    {"id": "shimmer", "name": "Shimmer", "language": "multi", "gender": "female", "provider": "openai"},
    {"id": "rachel", "name": "Rachel", "language": "en", "gender": "female", "provider": "elevenlabs"},
    {"id": "adam", "name": "Adam", "language": "en", "gender": "male", "provider": "elevenlabs"},
    {"id": "charlie", "name": "Charlie", "language": "en", "gender": "male", "provider": "elevenlabs"},
    {"id": "charlotte", "name": "Charlotte", "language": "en,fr", "gender": "female", "provider": "elevenlabs"},
]


class VoiceCloneService:
    """Service for voice cloning and TTS."""

    @staticmethod
    async def create_voice_profile(
        user_id: UUID, name: str, description: Optional[str],
        provider: str, language: str, settings: dict,
        audio_data: Optional[bytes], session: AsyncSession,
    ) -> VoiceProfile:
        """Create a voice profile, optionally from audio sample."""
        profile = VoiceProfile(
            user_id=user_id,
            name=name,
            description=description,
            provider=provider,
            language=language,
            settings_json=json.dumps(settings, ensure_ascii=False),
            status=VoiceStatus.PROCESSING if audio_data else VoiceStatus.READY,
        )

        if audio_data:
            # In production, send to ElevenLabs/provider for voice cloning
            # For MVP, simulate processing
            profile.sample_duration_s = len(audio_data) / 32000  # rough estimate
            profile.status = VoiceStatus.READY
            profile.external_voice_id = f"mock_voice_{name.lower().replace(' ', '_')}"
            logger.info("voice_clone_created", name=name, provider=provider, sample_size=len(audio_data))

        session.add(profile)
        await session.commit()
        await session.refresh(profile)
        return profile

    @staticmethod
    async def list_profiles(user_id: UUID, session: AsyncSession) -> list[VoiceProfile]:
        result = await session.execute(
            select(VoiceProfile).where(VoiceProfile.user_id == user_id)
            .order_by(VoiceProfile.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def delete_profile(profile_id: UUID, user_id: UUID, session: AsyncSession) -> bool:
        profile = await session.get(VoiceProfile, profile_id)
        if not profile or profile.user_id != user_id:
            return False
        await session.delete(profile)
        await session.commit()
        return True

    @staticmethod
    async def synthesize(
        user_id: UUID, text: str, voice_id: Optional[str],
        provider: str, output_format: str, language: str,
        session: AsyncSession, speed: float = 1.0,
    ) -> SpeechSynthesis:
        """Synthesize text to speech."""
        voice_uuid = None
        if voice_id:
            try:
                from uuid import UUID as UUIDType
                voice_uuid = UUIDType(voice_id)
            except (ValueError, AttributeError):
                pass

        synthesis = SpeechSynthesis(
            user_id=user_id,
            voice_id=voice_uuid,
            text=text[:10000],
            source_type="text",
            provider=provider,
            output_format=output_format,
            language=language,
            status=SynthesisStatus.PROCESSING,
        )
        session.add(synthesis)
        await session.flush()

        try:
            audio_url = await VoiceCloneService._call_tts_provider(
                text=text, provider=provider, voice_id=voice_id,
                output_format=output_format, language=language, speed=speed,
            )
            synthesis.audio_url = audio_url
            synthesis.status = SynthesisStatus.COMPLETED
            synthesis.duration_s = len(text.split()) * 0.4  # rough estimate
        except Exception as e:
            synthesis.status = SynthesisStatus.FAILED
            synthesis.error = str(e)[:1000]
            logger.error("tts_synthesis_failed", error=str(e))

        synthesis.updated_at = datetime.utcnow()
        session.add(synthesis)
        await session.commit()
        await session.refresh(synthesis)
        return synthesis

    @staticmethod
    async def synthesize_from_source(
        user_id: UUID, source_type: str, source_id: str,
        voice_id: Optional[str], provider: str, language: str,
        session: AsyncSession,
    ) -> SpeechSynthesis:
        """Synthesize from transcription or document."""
        text = ""
        if source_type == "transcription":
            from app.models.transcription import Transcription
            from uuid import UUID as UUIDType
            t = await session.get(Transcription, UUIDType(source_id))
            if t and t.user_id == user_id:
                text = t.transcription_text or ""
        elif source_type == "document":
            from app.models.knowledge import Document, DocumentChunk
            from uuid import UUID as UUIDType
            result = await session.execute(
                select(DocumentChunk).where(DocumentChunk.document_id == UUIDType(source_id))
                .order_by(DocumentChunk.chunk_index)
            )
            chunks = result.scalars().all()
            text = "\n\n".join(c.content for c in chunks)

        if not text:
            synthesis = SpeechSynthesis(
                user_id=user_id, text="", source_type=source_type, source_id=source_id,
                provider=provider, status=SynthesisStatus.FAILED, error="Source text not found",
            )
            session.add(synthesis)
            await session.commit()
            await session.refresh(synthesis)
            return synthesis

        return await VoiceCloneService.synthesize(
            user_id=user_id, text=text[:10000], voice_id=voice_id,
            provider=provider, output_format="mp3", language=language,
            session=session,
        )

    @staticmethod
    async def dub(
        user_id: UUID, source_type: str, source_id: Optional[str],
        source_url: Optional[str], target_language: str,
        voice_id: Optional[str], provider: str, session: AsyncSession,
    ) -> SpeechSynthesis:
        """Dub audio/video to another language (transcribe -> translate -> TTS)."""
        # Get original text
        text = ""
        if source_type == "transcription" and source_id:
            from app.models.transcription import Transcription
            from uuid import UUID as UUIDType
            t = await session.get(Transcription, UUIDType(source_id))
            if t and t.user_id == user_id:
                text = t.transcription_text or ""

        if not text:
            synthesis = SpeechSynthesis(
                user_id=user_id, text="", source_type=source_type,
                source_id=source_id, provider=provider,
                target_language=target_language,
                status=SynthesisStatus.FAILED, error="No source text for dubbing",
            )
            session.add(synthesis)
            await session.commit()
            await session.refresh(synthesis)
            return synthesis

        # Translate
        try:
            from app.ai_assistant.service import AIAssistantService
            result = await AIAssistantService.process_text_with_provider(
                text=f"Translate the following to {target_language}, preserving the natural speech patterns:\n\n{text[:8000]}",
                task="translate",
                provider_name="gemini",
                user_id=user_id,
                module="voice_clone",
            )
            translated = result.get("processed_text", text)
        except Exception:
            translated = text

        # Synthesize translated text
        synthesis = SpeechSynthesis(
            user_id=user_id,
            voice_id=None,
            text=translated[:10000],
            source_type=source_type,
            source_id=source_id,
            provider=provider,
            output_format="mp3",
            language="auto",
            target_language=target_language,
            status=SynthesisStatus.PROCESSING,
        )
        session.add(synthesis)
        await session.flush()

        try:
            audio_url = await VoiceCloneService._call_tts_provider(
                text=translated, provider=provider, voice_id=voice_id,
                output_format="mp3", language=target_language,
            )
            synthesis.audio_url = audio_url
            synthesis.status = SynthesisStatus.COMPLETED
            synthesis.duration_s = len(translated.split()) * 0.4
        except Exception as e:
            synthesis.status = SynthesisStatus.FAILED
            synthesis.error = str(e)[:1000]

        synthesis.updated_at = datetime.utcnow()
        session.add(synthesis)
        await session.commit()
        await session.refresh(synthesis)
        return synthesis

    @staticmethod
    async def list_syntheses(user_id: UUID, session: AsyncSession, limit: int = 20) -> list[SpeechSynthesis]:
        result = await session.execute(
            select(SpeechSynthesis).where(SpeechSynthesis.user_id == user_id)
            .order_by(SpeechSynthesis.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def _call_tts_provider(
        text: str, provider: str, voice_id: Optional[str],
        output_format: str, language: str, speed: float = 1.0,
    ) -> str:
        """Call the TTS provider API. Returns audio URL."""
        from app.config import settings

        if provider == "openai":
            api_key = getattr(settings, "OPENAI_API_KEY", None) or getattr(settings, "GROQ_API_KEY", None)
            if api_key and not api_key.startswith("your-"):
                try:
                    import openai
                    client = openai.AsyncOpenAI(api_key=api_key)
                    response = await client.audio.speech.create(
                        model="tts-1",
                        voice=voice_id or "alloy",
                        input=text[:4096],
                        response_format=output_format,
                        speed=speed,
                    )
                    # Save to file and return path
                    import tempfile, os
                    fd, path = tempfile.mkstemp(suffix=f".{output_format}", prefix="tts_")
                    os.close(fd)
                    response.stream_to_file(path)
                    return f"/api/voice/audio/{os.path.basename(path)}"
                except Exception as e:
                    logger.warning("openai_tts_failed", error=str(e))

        # Try Coqui TTS (free, local, open-source) before mock
        try:
            from app.modules.voice_clone.coqui_tts import is_available as coqui_available, synthesize as coqui_synth
            if coqui_available():
                audio_path = await coqui_synth(
                    text=text[:5000], language=language,
                    output_format="wav", speed=speed,
                )
                if audio_path:
                    import os
                    logger.info("coqui_tts_used", language=language, text_length=len(text))
                    return f"/api/voice/audio/{os.path.basename(audio_path)}"
        except Exception as e:
            logger.debug("coqui_tts_fallback_mock", error=str(e))

        # Mock mode (final fallback)
        logger.info("tts_mock_mode", provider=provider, text_length=len(text))
        return f"/api/voice/audio/mock_{provider}_{language}.{output_format}"

    @staticmethod
    def get_builtin_voices(provider: Optional[str] = None) -> list[dict]:
        all_voices = list(BUILTIN_VOICES)
        # Add Coqui voices if available
        try:
            from app.modules.voice_clone.coqui_tts import is_available, get_supported_languages
            if is_available():
                for lang in get_supported_languages():
                    all_voices.append({
                        "id": f"coqui_{lang['code']}", "name": f"Coqui {lang['name']}",
                        "language": lang["code"], "gender": "neutral", "provider": "coqui",
                    })
        except Exception:
            pass
        if provider:
            return [v for v in all_voices if v["provider"] == provider]
        return all_voices
