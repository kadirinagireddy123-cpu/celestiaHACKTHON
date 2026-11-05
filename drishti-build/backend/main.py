"""Main Entrypoint for Drishti Python Backend."""
from server import print_banner
from src.config.env import config
import uvicorn

if __name__ == "__main__":
    print_banner()
    uvicorn.run(
        "src.app:app",
        host=config.HOST,
        port=config.PORT,
        reload=True if config.NODE_ENV == "development" else False,
        log_level="info",
    )
