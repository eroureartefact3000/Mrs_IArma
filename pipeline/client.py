"""Thin wrapper around the Anthropic SDK for vision + JSON workflows.

The model is multimodal: it accepts either an image block (jpeg/png/webp/gif)
or a document block (application/pdf). The dispatcher here picks the right
block type from the media_type, so callers don't need to know.
"""
import json
import os
import re

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

MODEL = "claude-opus-4-7"


def get_client() -> Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. Copy .env.example to .env and fill it in."
        )
    return Anthropic(api_key=api_key)


def build_media_block(media_b64: str, media_type: str) -> dict:
    """Return the content block for either an image or a PDF, based on media_type.

    PDFs use type='document', images use type='image'. The SDK accepts both
    inside the messages.content array.
    """
    block_type = "document" if media_type == "application/pdf" else "image"
    return {
        "type": block_type,
        "source": {
            "type": "base64",
            "media_type": media_type,
            "data": media_b64,
        },
    }


def call_vision(prompt: str, image_b64: str, media_type: str, max_tokens: int = 2000) -> str:
    """Single-media vision call. Returns the text content of the first block.

    The argument name is `image_b64` for backward compatibility; it now also
    accepts a base64-encoded PDF when media_type is 'application/pdf'.
    """
    client = get_client()
    msg = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        messages=[
            {
                "role": "user",
                "content": [
                    build_media_block(image_b64, media_type),
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    )
    return msg.content[0].text


_JSON_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


def extract_json(text: str) -> dict:
    """Robustly extract a JSON object from a model response."""
    text = text.strip()
    fence_match = _JSON_FENCE.search(text)
    if fence_match:
        text = fence_match.group(1).strip()
    # Fall back: locate the outermost { ... }
    if not text.startswith("{"):
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            text = text[start : end + 1]
    return json.loads(text)
