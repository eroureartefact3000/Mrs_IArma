"""Smoke tests for the FastAPI service.

Like the pipeline smoke tests, these don't hit external APIs. The /api/evaluate
endpoint is covered structurally (input validation, bad category rejected,
auth enforcement) — the full LLM call is exercised manually via curl or
`scripts/evaluate_board.py` since it is paid.
"""
from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _ensure_env_keys(monkeypatch):
    """Set dummy API keys so config doesn't reject app boot during tests."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", os.environ.get("ANTHROPIC_API_KEY", "sk-ant-dummy"))
    monkeypatch.setenv("VOYAGE_API_KEY", os.environ.get("VOYAGE_API_KEY", "pa-dummy"))
    # Reset cached settings to pick up env changes
    from api.config import get_settings

    get_settings.cache_clear()


@pytest.fixture
def client():
    from api.main import create_app

    return TestClient(create_app())


# ----------------------------------------------------------------------------
# /api/health
# ----------------------------------------------------------------------------


def test_health_returns_ok(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert data["index_loaded"] is True  # committed in data/


# ----------------------------------------------------------------------------
# /api/categories
# ----------------------------------------------------------------------------


def test_categories_returns_all_thirty_enabled(client):
    r = client.get("/api/categories")
    assert r.status_code == 200
    cats = r.json()["categories"]
    # Each category must carry the registry-driven shape
    for c in cats:
        assert {"key", "label", "family", "enabled"} <= set(c.keys())
    enabled = [c for c in cats if c["enabled"]]
    assert len(enabled) == 30, "all 30 Cannes Lions 2026 categories must be enabled"
    keys = {c["key"] for c in enabled}
    for canonical in ("Outdoor", "PR", "Film", "Health & Wellness", "Titanium"):
        assert canonical in keys


# ----------------------------------------------------------------------------
# /api/evaluate — input validation (no LLM calls)
# ----------------------------------------------------------------------------


def test_evaluate_rejects_missing_fields(client):
    """Missing required form fields → 422."""
    r = client.post("/api/evaluate", files={"image": ("x.jpg", b"fake", "image/jpeg")})
    assert r.status_code == 422


def test_evaluate_rejects_unknown_category(client):
    """A category that isn't in the registry must be rejected upstream with 400."""
    r = client.post(
        "/api/evaluate",
        data={
            "campaign_name": "Test",
            "agency": "Test",
            "client": "Test",
            "category": "NotARealCannesCategory",
            "client_internationally_known": "true",
        },
        files={"image": ("x.jpg", b"fake", "image/jpeg")},
    )
    assert r.status_code == 400
    assert "not yet supported" in r.json()["detail"]


def test_evaluate_rejects_bad_extension(client):
    """File extension must be in the whitelist."""
    r = client.post(
        "/api/evaluate",
        data={
            "campaign_name": "Test",
            "agency": "Test",
            "client": "Test",
            "category": "Outdoor",
            "client_internationally_known": "true",
        },
        files={"image": ("x.txt", b"fake", "text/plain")},
    )
    assert r.status_code == 400
    assert "Unsupported file extension" in r.json()["detail"]


# ----------------------------------------------------------------------------
# Auth gate
# ----------------------------------------------------------------------------


def test_evaluate_auth_enforced_when_api_key_set(monkeypatch):
    """When API_KEY is set, requests without X-API-Key must be 401."""
    monkeypatch.setenv("API_KEY", "secret-test-key")
    from api.config import get_settings

    get_settings.cache_clear()

    from api.main import create_app

    c = TestClient(create_app())
    r = c.post(
        "/api/evaluate",
        data={
            "campaign_name": "x",
            "agency": "x",
            "client": "x",
            "category": "Outdoor",
            "client_internationally_known": "true",
        },
        files={"image": ("x.jpg", b"fake", "image/jpeg")},
    )
    assert r.status_code == 401


# ----------------------------------------------------------------------------
# Static frontend mounted at /
# ----------------------------------------------------------------------------


def test_frontend_served_at_root(client):
    """The React bundle (frontend/dist) is served at /, falling back to mini_frontend."""
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    # Either branding is acceptable, depending on which bundle is mounted:
    #  - frontend/dist  → "Mrs Airma · The Cannes Oracle"
    #  - mini_frontend  → "Mme Airma · La Voyante de Cannes" (legacy fallback)
    assert "Airma" in r.text
