"""Image loading for the Anthropic API.

Anthropic accepts jpeg, png, gif, webp (base64). AVIF is converted to JPEG first.
Any image larger than ~5 MB base64 is iteratively downsized until it fits.

Note: we ignore the file *extension* and use Pillow's detected format instead.
Some Cannes downloads are actually WebP or AVIF saved with a `.jpg` extension —
trusting the extension would send wrong media_type to the API.
"""
import base64
import io
from pathlib import Path

import pillow_avif  # noqa: F401 - registers AVIF support in Pillow
from PIL import Image

# Anthropic's hard limit is 5 MB on the BASE64-encoded image. Base64 inflates by
# 33%, so the raw bytes must stay under 5 MB * 3/4 = 3.75 MB. Use 3.5 MB safety.
_MAX_BYTES = 3_500_000
_RESIZE_LADDER = (3000, 2500, 2000, 1500, 1200, 1000)
_JPEG_QUALITY = 92

_MT_BY_FORMAT = {
    "JPEG": "image/jpeg",
    "PNG": "image/png",
    "WEBP": "image/webp",
    "GIF": "image/gif",
}


def _encode(img: Image.Image, media_type: str) -> bytes:
    buf = io.BytesIO()
    if media_type == "image/jpeg":
        img.save(buf, format="JPEG", quality=_JPEG_QUALITY, optimize=True)
    elif media_type == "image/png":
        img.save(buf, format="PNG", optimize=True)
    elif media_type == "image/webp":
        img.save(buf, format="WEBP", quality=_JPEG_QUALITY)
    else:
        raise ValueError(f"Unsupported media type for encode: {media_type}")
    return buf.getvalue()


def load_image_for_api(path: Path) -> tuple[str, str]:
    """Return (base64_data, media_type) for an image file.

    Strategy:
    - Detect actual format with Pillow (ignoring extension).
    - If API-native and raw bytes fit: send as-is.
    - Otherwise re-encode through Pillow, downscaling if needed.
    """
    img = Image.open(path)
    actual_format = (img.format or "").upper()

    # Native format AND raw bytes small enough → send as-is with correct media_type.
    if actual_format in _MT_BY_FORMAT:
        raw = path.read_bytes()
        if len(raw) <= _MAX_BYTES:
            return base64.standard_b64encode(raw).decode("utf-8"), _MT_BY_FORMAT[actual_format]

    # Must re-encode (AVIF, mismatched extension we can't trust, or oversized).
    img = img.convert("RGB")
    # PNGs convert to JPEG for size; AVIF and unknowns default to JPEG; WebP stays WebP.
    if actual_format == "WEBP":
        media_type = "image/webp"
    else:
        media_type = "image/jpeg"

    # Try original resolution after re-encode.
    data = _encode(img, media_type)
    if len(data) <= _MAX_BYTES:
        return base64.standard_b64encode(data).decode("utf-8"), media_type

    # Resize ladder.
    for max_dim in _RESIZE_LADDER:
        scaled = img.copy()
        scaled.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
        data = _encode(scaled, media_type)
        if len(data) <= _MAX_BYTES:
            return base64.standard_b64encode(data).decode("utf-8"), media_type

    raise ValueError(f"Could not downsize {path} below {_MAX_BYTES} bytes")
