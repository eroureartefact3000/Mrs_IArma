"""Media loading for the Anthropic API.

Accepts:
  - Images: jpeg, png, gif, webp (base64). AVIF is converted to JPEG first.
    Images larger than ~5 MB base64 are iteratively downsized until they fit.
  - PDFs: application/pdf, native Claude PDF support (up to 32 MB / 100 pages).
    Multi-page PDFs are sent as-is; Claude reads both embedded text and the
    rendered visuals.

Note: we ignore the file *extension* for IMAGES and use Pillow's detected format
instead. Some Cannes downloads are actually WebP or AVIF saved with a `.jpg`
extension; trusting the extension would send the wrong media_type to the API.
For PDFs the magic header (%PDF-) is checked.
"""
import base64
import io
from pathlib import Path

import pillow_avif  # noqa: F401 - registers AVIF support in Pillow
from PIL import Image

# Anthropic's hard limit for IMAGES is 5 MB on the BASE64-encoded image. Base64
# inflates by 33%, so the raw bytes must stay under 5 MB * 3/4 = 3.75 MB.
# Use 3.5 MB safety margin.
_MAX_IMAGE_BYTES = 3_500_000

# Anthropic's PDF limit is 32 MB raw. The API consumer is the one that gates
# upload size, so we just check we're under the absolute ceiling here.
_MAX_PDF_BYTES = 32 * 1024 * 1024

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


def _is_pdf(path: Path) -> bool:
    """Detect a PDF by its magic header. Trustworthy even if the extension lies."""
    try:
        with open(path, "rb") as f:
            return f.read(5) == b"%PDF-"
    except OSError:
        return False


def load_image_for_api(path: Path) -> tuple[str, str]:
    """Return (base64_data, media_type) for a board file.

    Accepts images (jpeg, png, webp, gif, avif) and PDFs. The function name
    is kept for backward compatibility with the rest of the pipeline.

    Strategy for PDFs:
    - Pass-through as application/pdf if under the 32 MB ceiling.

    Strategy for images:
    - Detect actual format with Pillow (ignoring extension).
    - If API-native and raw bytes fit: send as-is.
    - Otherwise re-encode through Pillow, downscaling if needed.
    """
    if _is_pdf(path):
        raw = path.read_bytes()
        if len(raw) > _MAX_PDF_BYTES:
            raise ValueError(
                f"PDF too large for the API: {len(raw)} bytes (max {_MAX_PDF_BYTES})"
            )
        return base64.standard_b64encode(raw).decode("utf-8"), "application/pdf"

    img = Image.open(path)
    actual_format = (img.format or "").upper()

    # Native format AND raw bytes small enough → send as-is with correct media_type.
    if actual_format in _MT_BY_FORMAT:
        raw = path.read_bytes()
        if len(raw) <= _MAX_IMAGE_BYTES:
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
    if len(data) <= _MAX_IMAGE_BYTES:
        return base64.standard_b64encode(data).decode("utf-8"), media_type

    # Resize ladder.
    for max_dim in _RESIZE_LADDER:
        scaled = img.copy()
        scaled.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
        data = _encode(scaled, media_type)
        if len(data) <= _MAX_IMAGE_BYTES:
            return base64.standard_b64encode(data).decode("utf-8"), media_type

    raise ValueError(f"Could not downsize {path} below {_MAX_IMAGE_BYTES} bytes")
