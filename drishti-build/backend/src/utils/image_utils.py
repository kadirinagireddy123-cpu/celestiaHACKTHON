"""Image parsing, validation and compression utilities."""
import re
import io
import base64
from typing import Dict, Any

# Target size for fast Gemini inference (small but enough for detection)
_MAX_PIXELS = 640 * 480   # ~0.3 MP ceiling for speed
_JPEG_QUALITY = 70        # balance quality vs payload size

def parse_base64_image(image_input: str, compress: bool = True) -> Dict[str, Any]:
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

    # Compress/resize large images for faster inference
    if compress:
        image_bytes, mime_type = _resize_if_needed(image_bytes, mime_type)

    return {
        "mime_type": mime_type,
        "data": image_bytes,
    }

def _resize_if_needed(image_bytes: bytes, mime_type: str):
    """Resize image to max _MAX_PIXELS while preserving aspect ratio for speed."""
    try:
        from PIL import Image
        with Image.open(io.BytesIO(image_bytes)) as img:
            w, h = img.size
            total = w * h
            if total <= _MAX_PIXELS:
                return image_bytes, mime_type  # already small enough

            # Compute scale so total pixels ~ _MAX_PIXELS
            import math
            scale = math.sqrt(_MAX_PIXELS / total)
            new_w = max(1, int(w * scale))
            new_h = max(1, int(h * scale))

            # Convert to RGB to ensure JPEG compatibility
            if img.mode in ("RGBA", "P", "LA"):
                img = img.convert("RGB")
            img = img.resize((new_w, new_h), Image.LANCZOS)

            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=_JPEG_QUALITY, optimize=True)
            return buf.getvalue(), "image/jpeg"
    except Exception:
        # PIL not available or error – return original unchanged
        return image_bytes, mime_type

