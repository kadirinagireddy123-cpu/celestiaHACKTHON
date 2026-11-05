"""Main Entrypoint for Drishti Python Backend."""
import sys
import uvicorn
from pathlib import Path

# Ensure the backend directory is on the path so 'src' and 'server' resolve
_BACKEND_DIR = Path(__file__).resolve().parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from server import print_banner          # noqa: E402  (server.py is in this dir)
from src.config.env import config        # noqa: E402

if __name__ == "__main__":
    print_banner()
    uvicorn.run(
        "src.app:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.NODE_ENV == "development",
        log_level="info",
    )
