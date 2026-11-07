"""Speech-to-Text transcription route — works on HTTP (MediaRecorder fallback)."""
import sys
import base64
import logging
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

try:
    from ..config.env import config
except (ImportError, ValueError):
    from src.config.env import config

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

logger = logging.getLogger("drishti.transcribe")
router = APIRouter(tags=["Speech to Text"])


class TranscribeRequest(BaseModel):
    audio: str              # base64-encoded audio (webm/ogg/wav/mp4)
    mimeType: str = "audio/webm"
    language: str = "en"   # BCP-47 or simple code like "kn", "hi", "te"


class TranscribeResponse(BaseModel):
    success: bool = True
    transcript: str = ""
    language: str = "en"
    confidence: float = 1.0


# BCP-47 → readable language hint for Gemini
_LANG_HINTS = {
    "en": "English", "hi": "Hindi", "kn": "Kannada", "te": "Telugu",
    "ta": "Tamil",   "mr": "Marathi", "bn": "Bengali", "gu": "Gujarati",
    "ml": "Malayalam","es": "Spanish","fr": "French",  "de": "German",
    "ja": "Japanese",
}


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(payload: TranscribeRequest):
    """
    Accepts base64-encoded audio recorded via MediaRecorder (webm/ogg/wav).
    Uses Gemini multimodal to transcribe the speech.
    Works on plain HTTP — no Web Speech API required.
    """
    if not payload.audio:
        raise HTTPException(status_code=400, detail="No audio data provided.")

    if config.is_demo_mode:
        return TranscribeResponse(transcript="", language=payload.language)

    try:
        audio_bytes = base64.b64decode(payload.audio)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid base64 audio data.")

    lang_code = payload.language.split("-")[0].lower()
    lang_name = _LANG_HINTS.get(lang_code, "English")

    prompt = (
        f"Transcribe the spoken words in this audio clip EXACTLY as heard. "
        f"The speaker is using {lang_name} ({payload.language}). "
        f"Return ONLY the raw transcription text — no punctuation corrections, "
        f"no commentary, no JSON. If the audio is silent or unclear, return an empty string."
    )

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=config.GEMINI_API_KEY)

        mime = payload.mimeType or "audio/webm"
        # Gemini accepts audio/webm, audio/ogg, audio/wav, audio/mp4
        if not mime.startswith("audio/"):
            mime = "audio/webm"

        # Try multimodal models that support audio input
        models_to_try = [
            "gemini-3.5-flash-lite",
            "gemini-flash-lite-latest",
            "gemini-3.1-flash-lite",
        ]

        for model_name in models_to_try:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[
                        prompt,
                        types.Part.from_bytes(data=audio_bytes, mime_type=mime),
                    ],
                    config=types.GenerateContentConfig(
                        temperature=0.0,  # deterministic for transcription
                        max_output_tokens=512,
                    ),
                )
                transcript = (response.text or "").strip()
                logger.info(f"Transcribed [{lang_name}]: '{transcript[:80]}'")
                return TranscribeResponse(
                    transcript=transcript,
                    language=payload.language,
                )
            except Exception as e:
                logger.warning(f"Transcription with {model_name} failed: {e}")
                continue

        return TranscribeResponse(transcript="", language=payload.language)

    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

