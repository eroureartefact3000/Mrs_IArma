# =============================================================================
# Mrs IArma · The Cannes Oracle
# Multi-stage Dockerfile — production-ready, Cloud Run compatible
#
# Stages:
#   1. frontend-builder — node 20, builds React/Vite bundle into /build/dist
#   2. python-builder   — python 3.11, installs API deps into /opt/venv
#   3. runtime          — python 3.11-slim, copies venv + source + frontend bundle
#
# Result: one image that serves /api/* (FastAPI) AND / (static React bundle).
# =============================================================================

# ---- Stage 1: frontend builder -----------------------------------------------
# node:22-alpine is required because pnpm 11.x (from the v9 lockfile) needs Node 22+.
FROM node:22-alpine AS frontend-builder

ENV CI=true

WORKDIR /build

# Enable corepack so we can use the pinned pnpm version from packageManager.
# pnpm-lock.yaml committed at the repo root → reproducible install.
RUN corepack enable

# Copy manifests first for layer caching.
COPY frontend/package.json frontend/pnpm-lock.yaml ./

# Install with pnpm 11 supply-chain policies relaxed inline. pnpm 11 only
# honors these as --config CLI flags; env vars and .npmrc keys are ignored.
#   minimumReleaseAge=0           → skip the 24h supply-chain quarantine
#   dangerouslyAllowAllBuilds=true → auto-approve postinstall scripts (esbuild)
# Safe here because the lockfile is authoritative.
RUN pnpm install --frozen-lockfile \
    --config.minimumReleaseAge=0 \
    --config.dangerouslyAllowAllBuilds=true

# Copy source and build. Invoke tsc + vite directly (not via `pnpm build`)
# to bypass pnpm's implicit deps-status check, which re-triggers the supply-chain
# policy on every script invocation.
COPY frontend/ ./
RUN ./node_modules/.bin/tsc -b && ./node_modules/.bin/vite build
# The result is at /build/dist (vite outDir = "dist")


# ---- Stage 2: python builder -------------------------------------------------
FROM python:3.11-slim AS python-builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    UV_LINK_MODE=copy

RUN pip install --no-cache-dir uv==0.4.30

WORKDIR /build

# Files needed for hatchling to build the local wheel (which uv pip install .[api] triggers).
# pyproject.toml declares the dep tree; README.md is referenced as the readme; pipeline/
# is the package source.
COPY pyproject.toml README.md ./
COPY pipeline/ ./pipeline/

# Install the "api" extra into a venv
RUN uv venv /opt/venv \
    && VIRTUAL_ENV=/opt/venv uv pip install --no-cache .[api]


# ---- Stage 3: runtime --------------------------------------------------------
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH=/app \
    PORT=8000

# Non-root user
RUN groupadd --system app && useradd --system --gid app --no-create-home app

WORKDIR /app

# Bring the prebuilt virtualenv
COPY --from=python-builder /opt/venv /opt/venv

# Application source
COPY pipeline/ /app/pipeline/
COPY api/ /app/api/
COPY data/ /app/data/
COPY pyproject.toml /app/pyproject.toml
COPY README.md /app/README.md

# Frontend bundle (produced by stage 1). Served by FastAPI at /.
COPY --from=frontend-builder /build/dist /app/frontend/dist

# Legacy vanilla-JS smoke UI kept as a fallback (api/main.py prefers
# frontend/dist when present, falls back to mini_frontend).
COPY mini_frontend/ /app/mini_frontend/

# No editable install needed — PYTHONPATH=/app (set in ENV above) makes
# `import pipeline`, `import api` resolve directly to the copied source.
# This avoids needing pip in the runtime venv (uv venv doesn't include pip).

# Drop privileges
RUN chown -R app:app /app
USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request, sys; r=urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=3); sys.exit(0 if r.status == 200 else 1)" || exit 1

# Uvicorn directly — production deployment should run multiple replicas via the
# orchestrator (Cloud Run autoscaling). Swap in gunicorn + uvicorn workers if
# you want a single-container multi-worker setup.
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips=*"]
