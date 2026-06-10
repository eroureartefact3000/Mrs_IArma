"""FastAPI entrypoint.

Run locally:
    uv run uvicorn api.main:app --reload

The integrating back-end team is expected to:
    - keep the `pipeline.evaluate_board` core call as the source of truth,
    - rewrap routes / middleware to their internal standards,
    - add: persistence (DB), proper auth (SSO/OAuth), background queueing,
      structured logging to Cloud Logging, OpenTelemetry, etc.
"""
from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .middleware import AccessLogMiddleware, attach_cors
from .routes import router as evaluation_router


def _configure_logging() -> None:
    s = get_settings()
    logging.basicConfig(
        level=s.log_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def create_app() -> FastAPI:
    """Build the FastAPI application. Factory pattern so tests can override config."""
    _configure_logging()
    s = get_settings()

    app = FastAPI(
        title="Mrs IArma · Cannes Lions Prediction Engine",
        version="0.1.0",
        description=(
            "HTTP service wrapping the Mrs IArma prediction engine. "
            "Upload a board image + metadata, get a structured tier prediction. "
            "See INTEGRATION.md for the full integration guide."
        ),
        docs_url="/docs",
        redoc_url=None,
    )

    # Middleware (registration order matters: CORS first, then access log)
    attach_cors(app)
    app.add_middleware(AccessLogMiddleware)

    # Routes
    app.include_router(evaluation_router)

    # Static frontend (served at /). Disable for pure-API deployments where the
    # frontend lives on a separate CDN. Preference order:
    #   1. explicit FRONTEND_DIR env var (absolute or repo-relative path)
    #   2. frontend/dist  → production React build (preferred)
    #   3. mini_frontend  → legacy vanilla-JS smoke UI (fallback)
    if s.serve_frontend:
        repo_root = Path(__file__).resolve().parent.parent
        candidates: list[Path] = []
        if s.frontend_dir:
            explicit = Path(s.frontend_dir)
            candidates.append(explicit if explicit.is_absolute() else (repo_root / explicit))
        candidates.append(repo_root / "frontend" / "dist")
        candidates.append(repo_root / "mini_frontend")

        for candidate in candidates:
            if candidate.exists() and (candidate / "index.html").exists():
                app.mount("/", StaticFiles(directory=candidate, html=True), name="frontend")
                logging.getLogger("mrs_iarma.api").info(
                    "static_frontend_mounted", extra={"path": str(candidate)}
                )
                break

    return app


app = create_app()
