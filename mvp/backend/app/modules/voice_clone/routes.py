"""
Voice Clone API routes - Voice cloning, TTS synthesis, and dubbing.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth import get_current_user
from app.modules.auth_guards.middleware import require_verified_email
from app.database import get_session
from app.models.user import User
from app.modules.voice_clone.schemas import (
    BuiltinVoice,
    DubRequest,
    SynthesisRead,
    SynthesizeFromSourceRequest,
    SynthesizeRequest,
    VoiceProfileCreate,
    VoiceProfileRead,
)
from app.modules.voice_clone.service import VoiceCloneService
from app.rate_limit import limiter

router = APIRouter()


@router.post("/profiles", response_model=VoiceProfileRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def create_voice_profile(
    request: Request,
    name: str = Form(...),
    description: Optional[str] = Form(None),
    provider: str = Form(default="elevenlabs"),
    language: str = Form(default="auto"),
    audio_file: Optional[UploadFile] = File(None, description="Audio sample for voice cloning (5-30s)"),
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """Create a voice profile, optionally from audio sample. Rate limit: 5/min"""
    audio_data = None
    if audio_file:
        audio_data = await audio_file.read()
        if len(audio_data) > 50 * 1024 * 1024:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Audio file too large (max 50MB)")

    profile = await VoiceCloneService.create_voice_profile(
        user_id=current_user.id, name=name, description=description,
        provider=provider, language=language, settings={},
        audio_data=audio_data, session=session,
    )
    return profile


@router.get("/profiles", response_model=list[VoiceProfileRead])
@limiter.limit("20/minute")
async def list_profiles(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """List user's voice profiles. Rate limit: 20/min"""
    return await VoiceCloneService.list_profiles(current_user.id, session)


@router.delete("/profiles/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def delete_profile(
    request: Request, profile_id: UUID,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """Delete a voice profile. Rate limit: 10/min"""
    if not await VoiceCloneService.delete_profile(profile_id, current_user.id, session):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")


@router.post("/synthesize", response_model=SynthesisRead)
@limiter.limit("5/minute")
async def synthesize_speech(
    request: Request, body: SynthesizeRequest,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """Synthesize text to speech. Rate limit: 5/min"""
    return await VoiceCloneService.synthesize(
        user_id=current_user.id, text=body.text, voice_id=body.voice_id,
        provider=body.provider, output_format=body.output_format,
        language=body.language, session=session, speed=body.speed,
    )


@router.post("/synthesize-source", response_model=SynthesisRead)
@limiter.limit("3/minute")
async def synthesize_from_source(
    request: Request, body: SynthesizeFromSourceRequest,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """Synthesize from transcription or document. Rate limit: 3/min"""
    return await VoiceCloneService.synthesize_from_source(
        user_id=current_user.id, source_type=body.source_type,
        source_id=body.source_id, voice_id=body.voice_id,
        provider=body.provider, language=body.language, session=session,
    )


@router.post("/dub", response_model=SynthesisRead)
@limiter.limit("2/minute")
async def dub_content(
    request: Request, body: DubRequest,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """Dub content to another language (translate + TTS). Rate limit: 2/min"""
    return await VoiceCloneService.dub(
        user_id=current_user.id, source_type=body.source_type,
        source_id=body.source_id, source_url=body.source_url,
        target_language=body.target_language, voice_id=body.voice_id,
        provider=body.provider, session=session,
    )


@router.get("/syntheses", response_model=list[SynthesisRead])
@limiter.limit("20/minute")
async def list_syntheses(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """List synthesis history. Rate limit: 20/min"""
    return await VoiceCloneService.list_syntheses(current_user.id, session)


@router.get("/voices", response_model=list[BuiltinVoice])
async def list_builtin_voices(provider: Optional[str] = None):
    """List available built-in voices."""
    voices = VoiceCloneService.get_builtin_voices(provider)
    return [BuiltinVoice(**v) for v in voices]
