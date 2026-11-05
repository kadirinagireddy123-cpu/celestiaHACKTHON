"""Drishti Voice & Vision AI Backend Server Entrypoint (Python)."""
import uvicorn
from src.config.env import config

def print_banner():
    banner = f"""
==================================================================
        DRISHTI: VOICE & VISION AI ASSISTIVE BACKEND (PYTHON)
               Team Tech Trojan | Celestia Hackathon
==================================================================
  Server Status   : RUNNING on http://{config.HOST}:{config.PORT}
  API Docs        : http://localhost:{config.PORT}/docs
  Health Check    : http://localhost:{config.PORT}/health
  Supported Modes : safety | read | currency | all
  AI Status       : {"DEMO MODE (Simulation active, no API key)" if config.is_demo_mode else "LIVE GEMINI MODE"}
  Primary Model   : {config.PRIMARY_MODEL}
  Fallback Model  : {config.FALLBACK_MODEL}
  Payload Limit   : {config.MAX_BODY_SIZE}
==================================================================
  Direct Endpoints:
    POST /vision-assist - Multimodal frame analysis & obstacle boxes
    POST /chat          - Conversational Q&A with surroundings memory
    POST /tts           - Text to speech synthesis with browser fallback
    GET  /languages     - Multilingual voice list
    GET  /modes         - Supported assistive operational modes
    GET  /health        - System status & diagnostics
==================================================================
"""
    print(banner)

if __name__ == "__main__":
    print_banner()
    uvicorn.run(
        "src.app:app",
        host=config.HOST,
        port=config.PORT,
        reload=True if config.NODE_ENV == "development" else False,
        log_level="info",
    )
