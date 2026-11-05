"""Text-to-speech service with browser fallback (converted from ttsService.js)."""
import sys
from pathlib import Path
from typing import Optional
import requests
import logging
from pydantic import BaseModel, Field

_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

try:
    from ..config.env import config
    from ..config.languages import get_language_metadata
except (ImportError, ValueError):
    from src.config.env import config
    from src.config.languages import get_language_metadata

logger = logging.getLogger("drishti.tts")

class SpeechConfig(BaseModel):
    text: str
    lang: str
    rate: float = 1.05
    pitch: float = 1.0
    volume: float = 1.0

class TTSResult(BaseModel):
    text: str
    language: str
    bcp47: str
    audioData: Optional[str] = Field(None, description="Base64 encoded audio bytes")
    audioMimeType: Optional[str] = Field(None, description="Audio MIME type")
    useBrowserFallback: bool = Field(True, description="Whether client should use browser SpeechSynthesis")
    source: str = Field("browser_speech_synthesis", description="Synthesis source")
    speechConfig: Optional[SpeechConfig] = Field(None, description="Client speech synthesis parameter tuning")

class TTSRequest(BaseModel):
    text: str = Field(..., description="Text string to synthesize")
    language: str = Field("en", description="Target language code")
    voice: Optional[str] = Field("neutral", description="Voice profile ('neutral', 'female', 'male')")

class TTSResponse(BaseModel):
    success: bool = True
    timestamp: str
    data: TTSResult

def generate_speech(text: str, language: str = "en", voice: str = "neutral") -> TTSResult:
    if not text:
        raise ValueError("Text parameter is required for TTS")

    lang_meta = get_language_metadata(language)

    if config.GEMINI_API_KEY:
        try:
            url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={config.GEMINI_API_KEY}"
            payload = {
                "input": {"text": text},
                "voice": {
                    "languageCode": lang_meta["bcp47"],
                    "ssmlGender": "MALE" if voice == "male" else "FEMALE",
                },
                "audioConfig": {
                    "audioEncoding": "MP3",
                    "speakingRate": 1.05,
                    "pitch": 0.0,
                },
            }
            resp = requests.post(url, json=payload, timeout=4)
            if resp.status_code == 200:
                data = resp.json()
                if "audioContent" in data:
                    return TTSResult(
                        text=text,
                        language=lang_meta["code"],
                        bcp47=lang_meta["bcp47"],
                        audioData=data["audioContent"],
                        audioMimeType="audio/mp3",
                        useBrowserFallback=False,
                        source="gemini_cloud_tts",
                    )
        except Exception as e:
            logger.warning(f"Server TTS failed: {e}. Falling back to browser speech.")

    return TTSResult(
        text=text,
        language=lang_meta["code"],
        bcp47=lang_meta["bcp47"],
        audioData=None,
        audioMimeType=None,
        useBrowserFallback=True,
        source="browser_speech_synthesis",
        speechConfig=SpeechConfig(
            text=text,
            lang=lang_meta["bcp47"],
            rate=1.05,
            pitch=1.0,
            volume=1.0,
        ),
    )
