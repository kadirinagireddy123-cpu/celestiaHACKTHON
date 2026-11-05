"""TTS Routes for Drishti Assistive AI."""
import sys
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

try:
    from ..services.tts_service import TTSRequest, TTSResponse
    from ..controllers.ttsController import handle_tts
except (ImportError, ValueError):
    from src.services.tts_service import TTSRequest, TTSResponse
    from src.controllers.ttsController import handle_tts

from fastapi import APIRouter

router = APIRouter(tags=["Text to Speech"])

@router.post("/tts", response_model=TTSResponse)
async def tts_endpoint(payload: TTSRequest):
    return await handle_tts(payload)
