"""Image parsing and validation utilities (converted from imageUtils.js)."""
import re
import base64
from typing import Dict, Any

def parse_base64_image(image_input: str) -> Dict[str, Any]:
    if not image_input or not isinstance(image_input, str):
        raise ValueError("Invalid image: must be a base64 encoded string or data URL")

    match = re.match(r"^data:([^;]+);base64,(.+)$", image_input)
    if match:
        mime_type = match.group(1)
        raw_b64 = match.group(2)
    else:
        mime_type = "image/jpeg"
        raw_b64 = re.sub(r"\s+", "", image_input)

    image_bytes = base64.b64decode(raw_b64)
    return {
        "mime_type": mime_type,
        "data": image_bytes,
    }

