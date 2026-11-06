"""Text-to-speech service using gTTS (Google Text-to-Speech) with browser fallback."""
import io
import sys
import base64
import logging
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field

_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

try:
    from ..config.languages import get_language_metadata
except (ImportError, ValueError):
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
    source: str = Field("gtts", description="Synthesis source")
    speechConfig: Optional[SpeechConfig] = Field(None, description="Client speech synthesis parameter tuning")

class TTSRequest(BaseModel):
    text: str = Field(..., description="Text string to synthesize")
    language: str = Field("en", description="Target language code (e.g. 'kn', 'hi', 'te', 'ta', 'en')")
    voice: Optional[str] = Field("neutral", description="Voice profile ('neutral', 'female', 'male')")

class TTSResponse(BaseModel):
    success: bool = True
    timestamp: str
    data: TTSResult

def generate_multilingual_audio(text: str, lang_code: str = "en", filename: str = "output.mp3") -> Optional[str]:
    """
    Generates an audio file in the specified language using gTTS.
    lang_code examples: 'kn' for Kannada, 'hi' for Hindi, 'te' for Telugu, 'en' for English
    """
    try:
        from gtts import gTTS
        tts = gTTS(text=text, lang=lang_code, slow=False)
        tts.save(filename)
        logger.info(f"Generated multilingual audio file saved to {filename}")
        return filename
    except Exception as e:
        logger.warning(f"Error generating speech file: {e}")
        return None

def generate_multilingual_bytes(text: str, lang_code: str = "en") -> Optional[bytes]:
    """
    Generates MP3 audio bytes in memory using gTTS.
    """
    try:
        from gtts import gTTS
        clean_code = (lang_code or "en").lower().split("-")[0]
        tts = gTTS(text=text, lang=clean_code, slow=False)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp.read()
    except Exception as e:
        logger.warning(f"gTTS audio synthesis failed for '{text[:30]}...' in '{lang_code}': {e}")
        return None

def generate_speech(text: str, language: str = "en", voice: str = "neutral") -> TTSResult:
    if not text:
        raise ValueError("Text parameter is required for TTS")

    lang_meta = get_language_metadata(language)
    lang_code = lang_meta.get("code", "en").lower().split("-")[0]

    fallback_speech_config = SpeechConfig(
        text=text,
        lang=lang_meta["bcp47"],
        rate=1.05,
        pitch=1.0,
        volume=1.0,
    )

    # 1. Primary: High-fidelity multilingual gTTS audio
    audio_bytes = generate_multilingual_bytes(text, lang_code=lang_code)
    if audio_bytes:
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        return TTSResult(
            text=text,
            language=lang_meta["code"],
            bcp47=lang_meta["bcp47"],
            audioData=audio_b64,
            audioMimeType="audio/mp3",
            useBrowserFallback=False,
            source="gtts",
            speechConfig=fallback_speech_config,
        )

    # 2. Resilient Fallback: Browser Web Speech API
    logger.info("Falling back to client browser SpeechSynthesis.")
    return TTSResult(
        text=text,
        language=lang_meta["code"],
        bcp47=lang_meta["bcp47"],
        audioData=None,
        audioMimeType=None,
        useBrowserFallback=True,
        source="browser_speech_synthesis",
        speechConfig=fallback_speech_config,
    )
