"""Environment Configuration for Drishti (converted from env.js)."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Path to backend root .env
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(dotenv_path=BACKEND_DIR / ".env")

class Config:
    PORT: int = int(os.getenv("PORT", "5000"))
    HOST: str = os.getenv("HOST", "0.0.0.0")
    CORS_ORIGIN: list[str] = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGIN", "*").split(",")
        if origin.strip()
    ]
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()
    PRIMARY_MODEL: str = os.getenv("GEMINI_PRIMARY_MODEL", "gemini-3.5-flash")
    FALLBACK_MODEL: str = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-3.5-flash-lite")
    TTS_MODEL: str = os.getenv("GEMINI_TTS_MODEL", "gemini-3.5-flash")
    MAX_BODY_SIZE: str = os.getenv("MAX_BODY_SIZE", "30mb")
    NODE_ENV: str = os.getenv("NODE_ENV", os.getenv("ENV", "development"))

    @property
    def is_demo_mode(self) -> bool:
        return not bool(self.GEMINI_API_KEY)

config = Config()

