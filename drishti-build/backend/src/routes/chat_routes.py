"""Chat Routes for Drishti Assistive AI."""
import sys
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

try:
    from ..schemas.chat_schemas import ChatRequest, ChatResponse
    from ..controllers.chatController import handle_chat
except (ImportError, ValueError):
    from src.schemas.chat_schemas import ChatRequest, ChatResponse
    from src.controllers.chatController import handle_chat

from fastapi import APIRouter

router = APIRouter(tags=["Conversational Q&A"])

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest):
    return await handle_chat(payload)
