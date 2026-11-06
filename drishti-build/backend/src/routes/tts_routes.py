"""TTS Routes for Drishti Assistive AI."""
import sys
from pathlib import Path
from typing import Optional

_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

try:
    from ..services.tts_service import (
        TTSRequest,
        TTSResponse,
        generate_multilingual_bytes,
        generate_multilingual_audio,
    )
    from ..controllers.ttsController import handle_tts
except (ImportError, ValueError):
    from src.services.tts_service import (
        TTSRequest,
        TTSResponse,
        generate_multilingual_bytes,
        generate_multilingual_audio,
    )
    from src.controllers.ttsController import handle_tts

from fastapi import APIRouter, HTTPException, Query, Response

router = APIRouter(tags=["Text to Speech"])

@router.post("/tts", response_model=TTSResponse)
async def tts_endpoint(payload: TTSRequest):
    return await handle_tts(payload)

@router.get("/tts/stream")
@router.post("/tts/stream")
async def tts_stream_endpoint(
    text: str = Query(..., description="Text to speak"),
    language: str = Query("en", description="Language code (e.g. 'kn', 'hi', 'te', 'ta', 'en')")
):
    """
    Directly streams multilingual MP3 audio generated via gTTS.
    Can be used in an <audio src="..."> tag or downloaded.
    """
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")
    
    audio_bytes = generate_multilingual_bytes(text.strip(), lang_code=language)
    if not audio_bytes:
        raise HTTPException(status_code=500, detail="Could not generate speech audio.")
    
    return Response(
        content=audio_bytes,
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": f'inline; filename="drishti_tts_{language}.mp3"',
            "Cache-Control": "public, max-age=3600",
        }
    )
