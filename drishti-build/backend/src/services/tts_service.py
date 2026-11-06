"""Text-to-speech service using gTTS (Google Text-to-Speech) with browser fallback."""
import io
import sys
import base64
import logging
from pathlib import Path
from typing import Optional, Dict
from pydantic import BaseModel, Field

_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

try:
    from ..config.languages import get_language_metadata
except (ImportError, ValueError):
    from src.config.languages import get_language_metadata

logger = logging.getLogger("drishti.tts")

# ISO 639-1 language code lookup dictionary
LANGUAGE_CODES: Dict[str, str] = {
    "english": "en",
    "kannada": "kn",
    "hindi": "hi",
    "telugu": "te",
    "tamil": "ta",
    "marathi": "mr",
    "bengali": "bn",
    "gujarati": "gu",
    "malayalam": "ml",
    "spanish": "es",
    "french": "fr",
    "german": "de",
    "japanese": "ja"
}

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
    language: str = Field("en", description="Target language code or name (e.g. 'kannada', 'kn', 'hindi', 'hi', 'en')")
    voice: Optional[str] = Field("neutral", description="Voice profile ('neutral', 'female', 'male')")

class TTSResponse(BaseModel):
    success: bool = True
    timestamp: str
    data: TTSResult

def generate_speech_file(text_to_speak: str, language_name: str = "english", output_file: str = "alert_output.mp3") -> str:
    """
    Converts text to speech in the requested target language and saves to MP3 file.
    
    :param text_to_speak: The translated output string from your model.
    :param language_name: Key corresponding to the selected language (e.g. 'kannada', 'kn', 'japanese', 'ja').
    :param output_file: File path where MP3 should be saved.
    :return: Path to the generated audio file or empty string on failure.
    """
    lang_key = (language_name or "english").lower().strip()
    lang_code = LANGUAGE_CODES.get(lang_key, lang_key.split("-")[0] if len(lang_key) <= 3 else "en")
    
    try:
        from gtts import gTTS
        tts = gTTS(text=text_to_speak, lang=lang_code, slow=False)
        tts.save(output_file)
        logger.info(f"Generated TTS audio file: {output_file} (lang: {lang_code})")
        return output_file
    except Exception as e:
        logger.warning(f"Failed to generate TTS audio: {e}")
        return ""

def generate_multilingual_audio(text: str, lang_code: str = "en", filename: str = "output.mp3") -> Optional[str]:
    """Generates an audio file in the specified language using gTTS."""
    res = generate_speech_file(text_to_speak=text, language_name=lang_code, output_file=filename)
    return res if res else None

def generate_multilingual_bytes(text: str, lang_code: str = "en") -> Optional[bytes]:
    """
    Generates MP3 audio bytes in memory using gTTS.
    """
    try:
        from gtts import gTTS
        clean_key = (lang_code or "en").lower().strip()
        code = LANGUAGE_CODES.get(clean_key, clean_key.split("-")[0])
        tts = gTTS(text=text, lang=code, slow=False)
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

    lang_clean = (language or "en").lower().strip()
    lang_code = LANGUAGE_CODES.get(lang_clean, lang_clean.split("-")[0])
    lang_meta = get_language_metadata(lang_code)

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
            language=lang_code,
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
