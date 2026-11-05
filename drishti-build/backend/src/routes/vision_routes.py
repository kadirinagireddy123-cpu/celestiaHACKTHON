"""Vision Routes for Drishti Assistive AI."""
import sys
from pathlib import Path

# Allow direct script execution from VS Code without parent package errors
_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

try:
    from ..schemas.vision_schemas import VisionAssistRequest, VisionAssistResponse
    from ..controllers.visionController import handle_vision_assist
except (ImportError, ValueError):
    from src.schemas.vision_schemas import VisionAssistRequest, VisionAssistResponse
    from src.controllers.visionController import handle_vision_assist

from fastapi import APIRouter

router = APIRouter(tags=["Vision Assist"])

@router.post("/vision-assist", response_model=VisionAssistResponse)
async def vision_assist_endpoint(payload: VisionAssistRequest):
    return await handle_vision_assist(payload)

if __name__ == "__main__":
    import uvicorn
    from src.app import app
    print("Starting Drishti server from vision_routes.py on http://localhost:5000 ...")
    uvicorn.run(app, host="0.0.0.0", port=5000)
