"""Multilingual dictionary and metadata for Drishti."""
from typing import Dict, Any, List

SUPPORTED_LANGUAGES: List[Dict[str, Any]] = [
    {"code": "en", "bcp47": "en-US", "name": "English", "native": "English", "rtl": False},
    {"code": "hi", "bcp47": "hi-IN", "name": "Hindi", "native": "हिन्दी", "rtl": False},
    {"code": "kn", "bcp47": "kn-IN", "name": "Kannada", "native": "ಕನ್ನಡ", "rtl": False},
    {"code": "te", "bcp47": "te-IN", "name": "Telugu", "native": "తెలుగు", "rtl": False},
    {"code": "ta", "bcp47": "ta-IN", "name": "Tamil", "native": "தமிழ்", "rtl": False},
    {"code": "mr", "bcp47": "mr-IN", "name": "Marathi", "native": "मराठी", "rtl": False},
    {"code": "bn", "bcp47": "bn-IN", "name": "Bengali", "native": "বাংলা", "rtl": False},
    {"code": "gu", "bcp47": "gu-IN", "name": "Gujarati", "native": "ગુજરાતી", "rtl": False},
    {"code": "ml", "bcp47": "ml-IN", "name": "Malayalam", "native": "മലയാളം", "rtl": False},
    {"code": "es", "bcp47": "es-ES", "name": "Spanish", "native": "Español", "rtl": False},
    {"code": "fr", "bcp47": "fr-FR", "name": "French", "native": "Français", "rtl": False},
    {"code": "de", "bcp47": "de-DE", "name": "German", "native": "Deutsch", "rtl": False},
    {"code": "ja", "bcp47": "ja-JP", "name": "Japanese", "native": "日本語", "rtl": False},
]

def get_language_metadata(code: str = "en") -> Dict[str, Any]:
    norm = (code or "en").lower().split("-")[0]
    for lang in SUPPORTED_LANGUAGES:
        if lang["code"] == norm:
            return lang
    return {
        "code": "en",
        "bcp47": "en-US",
        "name": "English",
        "native": "English",
        "rtl": False,
    }

