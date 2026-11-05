"""Info Controller (converted from infoController.js)."""
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

try:
    from ..config.env import config
    from ..config.languages import SUPPORTED_LANGUAGES
except (ImportError, ValueError):
    from src.config.env import config
    from src.config.languages import SUPPORTED_LANGUAGES

_START_TIME = time.time()

def get_health():
    uptime_seconds = int(time.time() - _START_TIME)
    return {
        "status": "ok",
        "product": "Drishti: Voice & Vision AI Backend (Python)",
        "team": "Tech Trojan",
        "version": "1.0.0",
        "uptime": f"{uptime_seconds}s",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "aiConfig": {
            "isDemoMode": config.is_demo_mode,
            "apiKeyConfigured": bool(config.GEMINI_API_KEY),
            "primaryModel": config.PRIMARY_MODEL,
            "fallbackModel": config.FALLBACK_MODEL,
            "ttsModel": config.TTS_MODEL,
        },
        "limits": {
            "maxBodySize": config.MAX_BODY_SIZE,
        },
        "environment": config.NODE_ENV,
    }

def get_languages():
    return {
        "success": True,
        "total": len(SUPPORTED_LANGUAGES),
        "languages": SUPPORTED_LANGUAGES,
    }

def get_modes():
    return {
        "success": True,
        "modes": [
            {
                "id": "safety",
                "title": "Obstacle & Safety Navigation",
                "description": "Real-time hazard detection, clock-position alerts, distance estimation, and clear-path guidance.",
            },
            {
                "id": "read",
                "title": "OCR Text & Label Reading",
                "description": "Read signs, medicine labels, door numbers, warnings, and menus.",
            },
            {
                "id": "currency",
                "title": "Banknote Recognition",
                "description": "Instant identification of banknote denominations (e.g. ₹500, ₹100, ₹50) with tactile notes.",
            },
            {
                "id": "all",
                "title": "Comprehensive Mode",
                "description": "Simultaneous obstacle detection, text recognition, and scene understanding.",
            },
        ],
    }

getHealth = get_health
getLanguages = get_languages
getModes = get_modes
