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


def test_categories_returns_at_least_outdoor_enabled(client):
    r = client.get("/api/categories")
    assert r.status_code == 200
    cats = r.json()["categories"]
    assert len(cats) >= 20
    # Each category must carry the registry-driven shape
    for c in cats:
        assert {"key", "label", "family", "enabled"} <= set(c.keys())
    enabled = [c for c in cats if c["enabled"]]
    assert len(enabled) == 1, "MVP exposes only Outdoor as enabled"
    assert enabled[0]["key"] == "Outdoor"
    assert enabled[0]["family"] == "Classic"


# ----------------------------------------------------------------------------
# /api/evaluate — input validation (no LLM calls)
# ----------------------------------------------------------------------------


def test_evaluate_rejects_missing_fields(client):
    """Missing required form fields → 422."""
    r = client.post("/api/evaluate", files={"image": ("x.jpg", b"fake", "image/jpeg")})
    assert r.status_code == 422


def test_evaluate_rejects_disabled_category(client):
    """A category that isn't enabled in /api/categories must be rejected upstream."""
    r = client.post(
        "/api/evaluate",
        data={
            "campaign_name": "Test",
            "agency": "Test",
            "client": "Test",
            "category": "Film",  # not enabled in MVP
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
# Mini frontend mounted at /
# ----------------------------------------------------------------------------


def test_mini_frontend_served_at_root(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "Mme Airma" in r.text


def test_mini_frontend_static_assets(client):
    """style.css and app.js must be reachable."""
    assert client.get("/style.css").status_code == 200
    assert client.get("/app.js").status_code == 200
