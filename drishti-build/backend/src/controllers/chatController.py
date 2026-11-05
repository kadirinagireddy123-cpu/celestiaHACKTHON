"""Chat Controller (converted from chatController.js)."""
import sys
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

try:
    from ..schemas.chat_schemas import ChatRequest, ChatResponse
    from ..services.gemini_service import chat_with_assistant
except (ImportError, ValueError):
    from src.schemas.chat_schemas import ChatRequest, ChatResponse
    from src.services.gemini_service import chat_with_assistant

from datetime import datetime, timezone
from fastapi import HTTPException, status

async def handle_chat(payload: ChatRequest) -> ChatResponse:
    if not payload.message and not payload.image:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'message' (text) or 'image' must be provided.",
        )

    result = await chat_with_assistant(
        message=payload.message,
        history=payload.history,
        language=payload.language,
        image=payload.image,
    )

    return ChatResponse(
        success=True,
        timestamp=datetime.now(timezone.utc).isoformat(),
        language=payload.language,
        data=result,
    )

handleChat = handle_chat
