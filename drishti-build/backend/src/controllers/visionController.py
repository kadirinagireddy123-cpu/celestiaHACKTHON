"""Vision Controller (converted from visionController.js)."""
import sys
from pathlib import Path

# Allow direct execution
_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

try:
    from ..schemas.vision_schemas import VisionAssistRequest, VisionAssistResponse
    from ..services.gemini_service import analyze_vision_frame
except (ImportError, ValueError):
    from src.schemas.vision_schemas import VisionAssistRequest, VisionAssistResponse
    from src.services.gemini_service import analyze_vision_frame

from datetime import datetime, timezone
from fastapi import HTTPException, status

async def handle_vision_assist(payload: VisionAssistRequest) -> VisionAssistResponse:
    if not payload.image:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required field: 'image'. Must be a base64 encoded image string or data URL.",
        )

    valid_modes = ["safety", "read", "currency", "all"]
    selected_mode = payload.mode if payload.mode in valid_modes else "safety"

    result = await analyze_vision_frame(
        image=payload.image,
        mode=selected_mode,
        language=payload.language,
        user_prompt=payload.userPrompt or "",
    )

    return VisionAssistResponse(
        success=True,
        timestamp=datetime.now(timezone.utc).isoformat(),
        mode=selected_mode,
        language=payload.language,
        data=result,
    )

handleVisionAssist = handle_vision_assist
