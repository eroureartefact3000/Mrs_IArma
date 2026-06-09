"""Thin wrapper around the Anthropic SDK for vision + JSON workflows."""
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


def call_vision(prompt: str, image_b64: str, media_type: str, max_tokens: int = 2000) -> str:
    """Single-image vision call. Returns the text content of the first block."""
    client = get_client()
    msg = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_b64,
                        },
                    },
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
