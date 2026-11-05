"""Main Entrypoint for Drishti Python Backend."""
import os
import sys
import uvicorn
from pathlib import Path
from dotenv import load_dotenv

# Add backend dir to path so 'src' package resolves at runtime
_BACKEND_DIR = Path(__file__).resolve().parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

# Load .env from the backend directory
load_dotenv(_BACKEND_DIR / ".env")

HOST      = os.getenv("HOST", "0.0.0.0")
PORT      = int(os.getenv("PORT", "5000"))
NODE_ENV  = os.getenv("NODE_ENV", os.getenv("ENV", "development"))
MODEL     = os.getenv("GEMINI_PRIMARY_MODEL", "gemini-3.5-flash")
API_KEY   = os.getenv("GEMINI_API_KEY", "")

def print_banner() -> None:
    mode_label = "DEMO MODE (no API key)" if not API_KEY else "LIVE GEMINI MODE"
    print(f"""
==================================================================
        DRISHTI: VOICE & VISION AI ASSISTIVE BACKEND (PYTHON)
               Team Tech Trojan | Celestia Hackathon
==================================================================
  Server   : http://{HOST}:{PORT}
  Docs     : http://localhost:{PORT}/docs
  Health   : http://localhost:{PORT}/health
  AI Mode  : {mode_label}
  Model    : {MODEL}
==================================================================
""")

if __name__ == "__main__":
    print_banner()
    uvicorn.run(
        "src.app:app",
        host=HOST,
        port=PORT,
        reload=NODE_ENV == "development",
        log_level="info",
    )
