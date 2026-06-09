# =============================================================================
# Mrs IArma · Cannes Lions prediction engine
# Multi-stage Dockerfile — production-ready, Cloud Run compatible
# =============================================================================

# ---- Stage 1: builder ---------------------------------------------------------
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    UV_LINK_MODE=copy

# Install uv for fast resolution + install
RUN pip install --no-cache-dir uv==0.4.30

WORKDIR /build

# Copy lockable definition first for layer caching
COPY pyproject.toml ./

# Install dependencies for the "api" extra into a venv
RUN uv venv /opt/venv \
    && VIRTUAL_ENV=/opt/venv uv pip install --no-cache .[api]

# ---- Stage 2: runtime ---------------------------------------------------------
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    PORT=8000

# Non-root user
RUN groupadd --system app && useradd --system --gid app --no-create-home app

WORKDIR /app

# Bring the prebuilt virtualenv
COPY --from=builder /opt/venv /opt/venv

# Copy the application source. The Python package "pipeline" is also installed
# inside the venv (from the builder stage), but we mount the source so it
# remains the authoritative version in case of an editable install.
COPY pipeline/ /app/pipeline/
COPY api/ /app/api/
COPY mini_frontend/ /app/mini_frontend/
COPY data/ /app/data/
COPY pyproject.toml /app/pyproject.toml
COPY README.md /app/README.md

# Install the local package into the venv so `import pipeline` resolves to
# the copied source (with the bundled data files via the relative paths).
RUN /opt/venv/bin/pip install --no-cache --no-deps -e .

# Drop privileges
RUN chown -R app:app /app
USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request, sys; r=urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=3); sys.exit(0 if r.status == 200 else 1)" || exit 1

# Uvicorn directly — production deployment should run multiple replicas via the
# orchestrator (Cloud Run autoscaling). The integrating team can swap in
# gunicorn + uvicorn workers if they want a single-container multi-worker setup.
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips=*"]
