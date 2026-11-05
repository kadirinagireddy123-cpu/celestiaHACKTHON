"""TTS Controller (converted from ttsController.js)."""
import sys
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

try:
    from ..services.tts_service import TTSRequest, TTSResponse, generate_speech
except (ImportError, ValueError):
    from src.services.tts_service import TTSRequest, TTSResponse, generate_speech

from datetime import datetime, timezone
from fastapi import HTTPException, status

async def handle_tts(payload: TTSRequest) -> TTSResponse:
    if not payload.text or not payload.text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required field: 'text' (string to synthesize).",
        )

    result = generate_speech(
        text=payload.text.strip(),
        language=payload.language,
        voice=payload.voice or "neutral",
    )

    return TTSResponse(
        success=True,
        timestamp=datetime.now(timezone.utc).isoformat(),
        data=result,
    )

handleTTS = handle_tts
