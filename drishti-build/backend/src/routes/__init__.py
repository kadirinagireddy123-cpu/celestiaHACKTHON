from .vision_routes import router as vision_router
from .chat_routes import router as chat_router
from .tts_routes import router as tts_router
from .info_routes import router as info_router

__all__ = ["vision_router", "chat_router", "tts_router", "info_router"]

