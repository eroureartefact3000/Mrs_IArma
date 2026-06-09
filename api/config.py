"""API configuration loaded from environment variables.

Single source of truth for runtime config. The integrating back-end can
swap any of these out without touching application code.
"""
from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the API service.

    Reads from environment variables (or `.env` file in dev). All defaults
    are sensible for local dev; production deployments should override
    explicitly via Secret Manager / equivalent.
    """

    # --- Provider keys (REQUIRED) ---
    anthropic_api_key: str = Field(..., description="Anthropic Claude API key")
    voyage_api_key: str = Field(..., description="Voyage AI embeddings API key")

    # --- Service identity ---
    environment: Literal["development", "staging", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # --- Auth (front → back) ---
    # If empty string, auth is DISABLED. Recommended only in local dev.
    api_key: str = Field(
        default="",
        description="Shared secret expected in X-API-Key header. Empty disables auth.",
    )

    # --- CORS ---
    # Comma-separated list of origins. "*" allows everything (dev only).
    allowed_origins: str = Field(
        default="*",
        description="Comma-separated allowed origins for CORS. Use a strict list in production.",
    )

    # --- Rate limiting (per IP) ---
    rate_limit_per_minute: int = Field(default=10, ge=0, description="0 disables rate limiting")
    rate_limit_per_hour: int = Field(default=60, ge=0)

    # --- Daily budget cap ---
    # If non-zero, the service refuses new evaluations after this many calls per day.
    # Useful for cost control on a public site. Reset at UTC midnight.
    daily_evaluation_cap: int = Field(
        default=0,
        ge=0,
        description="Max evaluations per UTC day across all IPs. 0 = unlimited.",
    )

    # --- Pipeline tuning ---
    judge_passes: int = Field(default=3, ge=1, le=5)
    rag_top_k: int = Field(default=5, ge=1, le=10)

    # --- Upload limits ---
    max_upload_mb: int = Field(default=25, ge=1, le=50)

    # --- Mini frontend ---
    serve_mini_frontend: bool = Field(default=True, description="Serve mini_frontend/ at /")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def allowed_origins_list(self) -> list[str]:
        if self.allowed_origins.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton. Reset via `get_settings.cache_clear()` in tests."""
    return Settings()
