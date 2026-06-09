"""HTTP routes exposing the prediction engine.

Endpoints:
    POST /api/evaluate     — multipart upload + metadata → BoardEvaluation JSON
    GET  /api/health       — liveness + index loaded check
    GET  /api/categories   — list of supported Cannes Lions categories (Outdoor only for MVP)

The route handlers are intentionally thin: they validate inputs, hand off to
`pipeline.evaluate_board`, and serialize the result. All business logic lives
in the `pipeline` library.
"""
from __future__ import annotations

import logging
import shutil
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import JSONResponse

from pipeline import UserMetadata, evaluate_board

from .config import get_settings
from .middleware import check_daily_budget, check_rate_limit, verify_api_key

logger = logging.getLogger("mrs_iarma.api")
router = APIRouter(prefix="/api", tags=["evaluation"])


# ----------------------------------------------------------------------------
# /api/health — liveness probe (no auth)
# ----------------------------------------------------------------------------


@router.get("/health")
def health() -> dict[str, Any]:
    """Liveness probe. Confirms the service is up and the RAG index is loadable.

    Returns:
        - status: "ok"
        - version: package version
        - index_loaded: whether the Voyage index npy + meta jsonl are present
    """
    from pipeline import __version__
    from pipeline.search import DEFAULT_EMBEDDINGS, DEFAULT_META

    index_present = DEFAULT_EMBEDDINGS.exists() and DEFAULT_META.exists()
    return {
        "status": "ok",
        "version": __version__,
        "index_loaded": index_present,
    }


# ----------------------------------------------------------------------------
# /api/categories — list of supported Cannes Lions categories
# ----------------------------------------------------------------------------


@router.get("/categories")
def categories() -> dict[str, Any]:
    """List of Cannes Lions categories with their enabled state for the UI dropdown.

    Sourced from the engine's category registry — keep that registry as the
    single source of truth. To add a new category, register it in
    `pipeline/category_registry.py`, don't touch this route.
    """
    from pipeline.category_registry import list_categories

    return {
        "categories": [
            {
                "key": c.key,
                "label": c.label,
                "family": c.family,
                "enabled": c.enabled,
            }
            for c in list_categories()
        ]
    }


# ----------------------------------------------------------------------------
# /api/evaluate — POST multipart, runs the full pipeline, returns JSON
# ----------------------------------------------------------------------------


_ALLOWED_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".avif", ".gif"}


def _validate_upload(image: UploadFile) -> None:
    s = get_settings()
    if not image.filename:
        raise HTTPException(400, "Missing image filename.")
    ext = Path(image.filename).suffix.lower()
    if ext not in _ALLOWED_EXTS:
        raise HTTPException(
            400,
            f"Unsupported file extension '{ext}'. Allowed: {sorted(_ALLOWED_EXTS)}.",
        )
    # content-length is best-effort; we also re-check after saving
    if image.size and image.size > s.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, f"File too large. Max {s.max_upload_mb} MB.")


@router.post(
    "/evaluate",
    summary="Evaluate a Cannes Lions board",
    description=(
        "Runs the full pipeline (extraction → RAG → multi-pass judge → malus) "
        "and returns the structured BoardEvaluation. ~45 seconds, ~$2 per call."
    ),
    dependencies=[Depends(verify_api_key)],
)
async def evaluate(
    request: Request,
    image: UploadFile = File(..., description="Board image (jpg/png/webp/avif/gif). Max 25 MB."),
    campaign_name: str = Form(..., min_length=1, max_length=200),
    agency: str = Form(..., min_length=1, max_length=200),
    client: str = Form(..., min_length=1, max_length=200),
    category: str = Form("Outdoor", description="Cannes Lions category. Only 'Outdoor' is functional in MVP."),
    client_internationally_known: bool = Form(True),
) -> JSONResponse:
    """End-to-end evaluation of a board."""
    check_rate_limit(request)
    check_daily_budget()

    # Reject categories that aren't enabled (registry-driven)
    from pipeline.category_registry import (
        CategoryNotEnabled,
        UnknownCategory,
        list_enabled_keys,
        require_enabled_category,
    )

    try:
        require_enabled_category(category)
    except (UnknownCategory, CategoryNotEnabled):
        raise HTTPException(
            status_code=400,
            detail=(
                f"Category '{category}' not yet supported. "
                f"Enabled categories: {sorted(list_enabled_keys())}."
            ),
        )

    _validate_upload(image)

    eval_id = str(uuid.uuid4())
    started = time.time()

    # Persist the upload to a temp file (pipeline takes a Path).
    suffix = Path(image.filename or "board.jpg").suffix.lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        try:
            shutil.copyfileobj(image.file, tmp)
            tmp_path = Path(tmp.name)
        finally:
            image.file.close()

    try:
        # Final size check after copy
        s = get_settings()
        if tmp_path.stat().st_size > s.max_upload_mb * 1024 * 1024:
            raise HTTPException(413, f"File too large. Max {s.max_upload_mb} MB.")

        metadata = UserMetadata(
            campaign_name=campaign_name,
            agency=agency,
            client=client,
            category=category,
            client_internationally_known=client_internationally_known,
        )

        logger.info(
            "evaluation_started",
            extra={"evaluation_id": eval_id, "campaign": campaign_name, "agency": agency},
        )

        result = evaluate_board(
            image_path=tmp_path,
            user_metadata=metadata,
            k_references=s.rag_top_k,
            n_passes=s.judge_passes,
            verbose=False,
        )

        elapsed = time.time() - started
        logger.info(
            "evaluation_completed",
            extra={
                "evaluation_id": eval_id,
                "tier": result.tier_prediction.predicted_tier,
                "elapsed_s": round(elapsed, 1),
            },
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "evaluation_id": eval_id,
                "elapsed_seconds": round(elapsed, 1),
                "tier_prediction": result.tier_prediction.model_dump(),
                # Expose the full BoardEvaluation under `_debug` for advanced clients
                # (internal teams, calibration). Front-end UI only needs tier_prediction.
                "_debug": {
                    "medal_prediction": result.medal_prediction.model_dump(),
                    "base_weighted_score": result.base_weighted_score,
                    "final_weighted_score": result.final_weighted_score,
                    "tier_probabilities": result.tier_probabilities,
                    "malus": result.malus,
                    "references_count": len(result.references),
                },
            },
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("evaluation_failed", extra={"evaluation_id": eval_id})
        raise HTTPException(
            status_code=500,
            detail=f"Evaluation failed: {type(exc).__name__}",
        ) from exc
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass
