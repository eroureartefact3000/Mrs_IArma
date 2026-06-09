"""Voyage AI embedding wrapper.

Voyage-3-large is the highest-quality general embedding model from Anthropic's
recommended partner. Output dimension: 1024. Embeddings are unit-normalised, so
cosine similarity reduces to a dot product on the index matrix.
"""
import os
import time
from typing import Callable, Sequence, TypeVar

import voyageai
from dotenv import load_dotenv

load_dotenv()

MODEL = "voyage-3-large"
DIM = 1024

# Free tier (no payment method) is 3 RPM + 10K TPM. Once a payment method is on
# file (still free for the first 200M tokens), normal limits kick in. We default
# to free-tier-safe pacing; the build script can override via env.
_FREE_TIER_BATCH = 32           # ~32 × 150 tokens ≈ 4.8K tokens per call, well under 10K TPM
_FREE_TIER_SLEEP = 22.0         # 3 RPM ↔ 1 call per 20 s, +2 s safety


def get_client() -> voyageai.Client:
    api_key = os.environ.get("VOYAGE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "VOYAGE_API_KEY is not set. Sign up at voyageai.com and add the key to .env."
        )
    return voyageai.Client(api_key=api_key)


T = TypeVar("T")


def _with_rate_limit_retry(fn: Callable[[], T], max_retries: int = 4, base_sleep: float = 22.0) -> T:
    """Run fn() and retry on Voyage RateLimitError with exponential-ish backoff.

    Free tier limits are 3 RPM / 10K TPM. The default 22 s sleep matches the
    1-req-per-20-s implied by 3 RPM, with backoff for repeated hits.
    """
    last_err: Exception | None = None
    for attempt in range(max_retries):
        try:
            return fn()
        except voyageai.error.RateLimitError as e:
            last_err = e
            if attempt == max_retries - 1:
                break
            sleep_for = base_sleep * (attempt + 1)
            print(f"  ⚠️  rate limited; sleeping {sleep_for:.0f}s before retry {attempt + 2}/{max_retries}…")
            time.sleep(sleep_for)
    raise last_err  # type: ignore[misc]


def embed_documents(
    texts: Sequence[str],
    batch_size: int | None = None,
    throttle_seconds: float | None = None,
) -> list[list[float]]:
    """Embed a list of documents with optional throttling for free-tier rate limits.

    Args:
        texts: documents to embed.
        batch_size: docs per Voyage request. Defaults to a free-tier-safe value.
        throttle_seconds: sleep between batches. None or 0 → no throttling.
    """
    if batch_size is None:
        batch_size = _FREE_TIER_BATCH
    if throttle_seconds is None:
        throttle_seconds = _FREE_TIER_SLEEP

    client = get_client()
    out: list[list[float]] = []
    total_batches = (len(texts) + batch_size - 1) // batch_size

    for batch_idx, start in enumerate(range(0, len(texts), batch_size)):
        if batch_idx > 0 and throttle_seconds:
            time.sleep(throttle_seconds)
        chunk = list(texts[start : start + batch_size])
        result = _with_rate_limit_retry(
            lambda: client.embed(chunk, model=MODEL, input_type="document")
        )
        out.extend(result.embeddings)
        print(f"  batch {batch_idx + 1}/{total_batches}  ({len(out)}/{len(texts)} docs embedded)")
    return out


def embed_query(text: str) -> list[float]:
    """Embed a single query. input_type='query' is asymmetric to 'document'."""
    client = get_client()
    result = _with_rate_limit_retry(
        lambda: client.embed([text], model=MODEL, input_type="query")
    )
    return result.embeddings[0]
