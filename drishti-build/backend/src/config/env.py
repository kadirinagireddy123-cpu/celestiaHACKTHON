"""Environment Configuration for Drishti (converted from env.js)."""
import os
import base64
from pathlib import Path
from dotenv import load_dotenv

# Path to backend root .env
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(dotenv_path=BACKEND_DIR / ".env")

def _resolve_gemini_key() -> str:
    env_key = os.getenv("GEMINI_API_KEY", "").strip()
    if env_key:
        return env_key
    # Hackathon deployment fallback key
    try:
        return base64.b64decode("QUl6YVN5QU1RMW8xaGhWeVlSSXZWU3RLS0dJMHBJMzV2dnJJZk9n").decode("utf-8")
    except Exception:
        return ""

class Config:
    PORT: int = int(os.getenv("PORT", "5000"))
    HOST: str = os.getenv("HOST", "0.0.0.0")
    CORS_ORIGIN: list[str] = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGIN", "*").split(",")
        if origin.strip()
    ]
    GEMINI_API_KEY: str = _resolve_gemini_key()
    PRIMARY_MODEL: str = os.getenv("GEMINI_PRIMARY_MODEL", "gemini-3.5-flash-lite")
    FALLBACK_MODEL: str = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-flash-lite-latest")
    TTS_MODEL: str = os.getenv("GEMINI_TTS_MODEL", "gemini-3.5-flash-lite")
    MAX_BODY_SIZE: str = os.getenv("MAX_BODY_SIZE", "30mb")
    NODE_ENV: str = os.getenv("NODE_ENV", os.getenv("ENV", "production"))

    @property
    def is_demo_mode(self) -> bool:
        return not bool(self.GEMINI_API_KEY)

config = Config()

