"""Middleware: auth, rate limiting, request logging, daily budget cap.

Kept simple and dependency-light. The integrating back-end is expected to
replace each of these with their own production-grade equivalents (e.g.
Cloud Armor + Redis-backed rate limiter + structured logs to Cloud Logging).
"""
from __future__ import annotations

import logging
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from threading import Lock
from typing import Awaitable, Callable

from fastapi import HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from .config import get_settings

logger = logging.getLogger("mrs_iarma.api")


# ----------------------------------------------------------------------------
# Auth — shared API key in X-API-Key header
# ----------------------------------------------------------------------------


async def verify_api_key(request: Request) -> None:
    """Reject the request if the X-API-Key header is missing/wrong.

    Skipped entirely when settings.api_key is empty (local dev convenience).
    """
    settings = get_settings()
    if not settings.api_key:
        return
    provided = request.headers.get("X-API-Key")
    if not provided or provided != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid X-API-Key header.",
        )


# ----------------------------------------------------------------------------
# Rate limiting — per-IP, sliding window, in-memory
# ----------------------------------------------------------------------------


class InMemoryRateLimiter:
    """Sliding-window rate limiter keyed by client IP.

    NOTE: in-memory state, single-process only. In production with multiple
    workers / replicas, the integrating back-end should swap this for a
    Redis-backed limiter (slowapi + Redis, or Memorystore for GCP).
    """

    def __init__(self) -> None:
        self._per_minute: dict[str, deque[float]] = defaultdict(deque)
        self._per_hour: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, ip: str) -> tuple[bool, str | None]:
        s = get_settings()
        now = time.time()
        with self._lock:
            if s.rate_limit_per_minute > 0:
                window = self._per_minute[ip]
                while window and window[0] < now - 60:
                    window.popleft()
                if len(window) >= s.rate_limit_per_minute:
                    return False, f"Rate limit exceeded: max {s.rate_limit_per_minute} requests per minute."
                window.append(now)
            if s.rate_limit_per_hour > 0:
                window = self._per_hour[ip]
                while window and window[0] < now - 3600:
                    window.popleft()
                if len(window) >= s.rate_limit_per_hour:
                    return False, f"Rate limit exceeded: max {s.rate_limit_per_hour} requests per hour."
                window.append(now)
        return True, None


_rate_limiter = InMemoryRateLimiter()


def check_rate_limit(request: Request) -> None:
    ip = request.client.host if request.client else "unknown"
    ok, msg = _rate_limiter.check(ip)
    if not ok:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=msg)


# ----------------------------------------------------------------------------
# Daily budget cap — protect against runaway costs on a public service
# ----------------------------------------------------------------------------


class DailyBudgetTracker:
    """Counts evaluations per UTC day; raises 503 when daily cap is hit."""

    def __init__(self) -> None:
        self._count = 0
        self._day = self._today()
        self._lock = Lock()

    @staticmethod
    def _today() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    def consume(self) -> None:
        s = get_settings()
        if s.daily_evaluation_cap <= 0:
            return
        with self._lock:
            today = self._today()
            if today != self._day:
                self._day = today
                self._count = 0
            if self._count >= s.daily_evaluation_cap:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=(
                        f"Daily evaluation cap ({s.daily_evaluation_cap}) reached. "
                        "Service will reset at UTC midnight."
                    ),
                )
            self._count += 1


_budget = DailyBudgetTracker()


def check_daily_budget() -> None:
    _budget.consume()


# ----------------------------------------------------------------------------
# Access log — structured JSON log per request (Cloud Logging friendly)
# ----------------------------------------------------------------------------


class AccessLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        started = time.time()
        ip = request.client.host if request.client else "unknown"
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception as exc:
            status_code = 500
            logger.exception(
                "request_failed",
                extra={
                    "request_method": request.method,
                    "request_path": request.url.path,
                    "request_ip": ip,
                    "error": str(exc),
                },
            )
            raise
        finally:
            elapsed_ms = int((time.time() - started) * 1000)
            logger.info(
                "request",
                extra={
                    "request_method": request.method,
                    "request_path": request.url.path,
                    "request_ip": ip,
                    "status_code": status_code,  # type: ignore[possibly-undefined]
                    "elapsed_ms": elapsed_ms,
                },
            )


# ----------------------------------------------------------------------------
# CORS — small helper to wire CORS from settings
# ----------------------------------------------------------------------------


def attach_cors(app) -> None:  # type: ignore[no-untyped-def]
    s = get_settings()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=s.allowed_origins_list,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "X-API-Key"],
    )
