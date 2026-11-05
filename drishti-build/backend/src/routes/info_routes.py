"""Info Routes for Drishti Assistive AI."""
import sys
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

try:
    from ..controllers.infoController import get_health, get_languages, get_modes
except (ImportError, ValueError):
    from src.controllers.infoController import get_health, get_languages, get_modes

from fastapi import APIRouter

router = APIRouter(tags=["Info & Diagnostics"])

@router.get("/health")
def health_endpoint():
    return get_health()

@router.get("/languages")
def languages_endpoint():
    return get_languages()

@router.get("/modes")
def modes_endpoint():
    return get_modes()
