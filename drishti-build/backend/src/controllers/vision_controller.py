"""Snake_case alias to visionController.py."""
import sys
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

try:
    from .visionController import handle_vision_assist, handleVisionAssist
except (ImportError, ValueError):
    from src.controllers.visionController import handle_vision_assist, handleVisionAssist

__all__ = ["handle_vision_assist", "handleVisionAssist"]
