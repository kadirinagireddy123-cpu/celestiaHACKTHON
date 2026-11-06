"""Gemini multimodal vision and chat service (converted from geminiService.js)."""
import sys
import json
import re
import logging
from pathlib import Path
from typing import Optional, List, Any

_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

try:
    from ..config.env import config
    from ..schemas.vision_schemas import VisionAssistResult
    from ..schemas.chat_schemas import ChatResult, ChatMessage
    from ..utils.image_utils import parse_base64_image
    from ..utils.prompt_templates import get_vision_system_prompt, get_chat_system_prompt
    from .mock_service import get_mock_vision_assist, get_mock_chat_response
except (ImportError, ValueError):
    from src.config.env import config
    from src.schemas.vision_schemas import VisionAssistResult
    from src.schemas.chat_schemas import ChatResult, ChatMessage
    from src.utils.image_utils import parse_base64_image
    from src.utils.prompt_templates import get_vision_system_prompt, get_chat_system_prompt
    from src.services.mock_service import get_mock_vision_assist, get_mock_chat_response

logger = logging.getLogger("drishti.gemini")

_genai_client = None

def get_client():
    global _genai_client
    if not config.GEMINI_API_KEY:
        return None
    if _genai_client is None:
        try:
            from google import genai
            _genai_client = genai.Client(api_key=config.GEMINI_API_KEY)
        except Exception as e:
            logger.warning(f"Could not initialize google.genai: {e}")
    return _genai_client

def clean_and_parse_json(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```json"):
        cleaned = re.sub(r"^```json\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    elif cleaned.startswith("```"):
        cleaned = re.sub(r"^```\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        cleaned = cleaned[start : end + 1]

    return json.loads(cleaned)

async def analyze_vision_frame(
    image: str,
    mode: str = "safety",
    language: str = "en",
    user_prompt: str = ""
) -> VisionAssistResult:
    if config.is_demo_mode:
        logger.info("Running vision analysis in DEMO MODE (no API key configured).")
        return get_mock_vision_assist(mode, language, user_prompt)

    models_to_try = [
        config.PRIMARY_MODEL,
        config.FALLBACK_MODEL,
        "gemini-flash-lite-latest",
        "gemini-3.1-flash-lite",
    ]
    last_error = None

    try:
        img_info = parse_base64_image(image)
    except Exception as e:
        logger.warning(f"Image parsing failed: {e}. Falling back to mock.")
        return get_mock_vision_assist(mode, language, user_prompt)

    prompt = get_vision_system_prompt(mode, language)
    if user_prompt:
        prompt += f'\nUser question or command: "{user_prompt}"'

    client = get_client()
    if client:
        from google.genai import types
        for model_name in models_to_try:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[
                        prompt,
                        types.Part.from_bytes(data=img_info["data"], mime_type=img_info["mime_type"]),
                    ],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=VisionAssistResult,
                        temperature=0.2,
                    ),
                )
                if response.parsed:
                    result = response.parsed
                else:
                    data = clean_and_parse_json(response.text)
                    result = VisionAssistResult(**data)
                result.isDemoMode = False
                result.modelUsed = model_name
                return result
            except Exception as err:
                logger.warning(f"Model {model_name} failed: {err}. Trying fallback...")
                last_error = err

    logger.error(f"Vision analysis failed with all models: {last_error}. Returning resilient mock.")
    mock = get_mock_vision_assist(mode, language, user_prompt)
    mock.fallbackReason = str(last_error) if last_error else "API Key not set or model error"
    return mock

async def chat_with_assistant(
    message: Optional[str] = None,
    history: Optional[List[ChatMessage]] = None,
    language: str = "en",
    image: Optional[str] = None
) -> ChatResult:
    if config.is_demo_mode:
        logger.info("Chat running in DEMO MODE (no API key configured).")
        return get_mock_chat_response(message or "", language)

    models_to_try = [
        config.PRIMARY_MODEL,
        config.FALLBACK_MODEL,
        "gemini-flash-lite-latest",
        "gemini-3.1-flash-lite",
    ]
    system_instruction = get_chat_system_prompt(language)
    last_error = None

    client = get_client()
    contents = [system_instruction]

    if history:
        for turn in history[-6:]:
            role = "user" if turn.role == "user" else "model"
            contents.append(f"{role.upper()}: {turn.text}")

    current_msg = message or "Describe what is around me."
    if image:
        try:
            from google.genai import types
            img_info = parse_base64_image(image)
            contents.append(types.Part.from_bytes(data=img_info["data"], mime_type=img_info["mime_type"]))
        except Exception as e:
            logger.warning(f"Could not parse chat image: {e}")

    contents.append(f"USER: {current_msg}")

    if client:
        from google.genai import types
        for model_name in models_to_try:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=ChatResult,
                        temperature=0.3,
                    ),
                )
                if response.parsed:
                    result = response.parsed
                else:
                    data = clean_and_parse_json(response.text)
                    result = ChatResult(**data)
                result.isDemoMode = False
                return result
            except Exception as err:
                logger.warning(f"Chat model {model_name} failed: {err}")
                last_error = err

    logger.error(f"Chat failed with all models: {last_error}. Returning resilient mock.")
    mock = get_mock_chat_response(message or "", language)
    mock.fallbackReason = str(last_error) if last_error else "API Key not set or model error"
    return mock
