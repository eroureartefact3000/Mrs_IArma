"""Category registry — single source of truth for which Cannes Lions categories
the engine supports, with their criteria, RAG index location, and metadata.

A category is added to the engine by registering one `CategoryConfig` here.
That config bundles:
  - the judging criteria (axes + weights + descriptions)
  - the path to the RAG index files
  - display metadata for the UI (English label, optional grouping)
  - the `enabled` flag (whether the category is actually wired up for evaluation)

Categories that don't have a registered config are visible in the API listing
as `enabled: false` placeholders — the front-end shows them as "coming soon".

To add a new category (e.g. PR):
    1. Create `pipeline/pr_criteria.py` with a `PR_CRITERIA` dict
    2. Build the RAG index → `data/pr_index.npy` + `data/pr_index_meta.jsonl`
    3. Register here with `register_category(CategoryConfig(...))`
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Repository root: pipeline/ is one level under repo root.
_REPO_ROOT = Path(__file__).resolve().parent.parent
_DATA_DIR = _REPO_ROOT / "data"


@dataclass(frozen=True)
class CategoryConfig:
    """Configuration for one Cannes Lions category."""

    # Stable internal key (matches user_metadata.category, e.g. "Outdoor", "PR").
    key: str

    # Display label shown in the UI dropdown. English only.
    label: str

    # Cannes Lions family grouping (Brand / Classic / Craft / Engagement /
    # Entertainment / Experience / Good / Health / Strategy / Titanium).
    # Used by the front-end to group categories in the dropdown.
    family: str

    # Whether the engine has a working pipeline for this category.
    # `False` = category is visible in the listing but rejected on evaluate (placeholder).
    enabled: bool = False

    # Judging criteria dict (see outdoor_criteria.py for the shape).
    # Required when `enabled=True`; ignored when `enabled=False`.
    criteria: dict[str, Any] | None = None

    # Path to the RAG index numpy matrix. Resolved against the data/ directory
    # at runtime. Required when `enabled=True`.
    index_path: Path | None = None

    # Path to the RAG index metadata JSONL.
    meta_path: Path | None = None

    # Optional: tier score bands per tier {tier: (min, max)}. Defaults are
    # defined inside each criteria module (e.g. outdoor_criteria.expected_score_range).
    tier_bands: dict[str, tuple[int, int]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.enabled:
            if self.criteria is None:
                raise ValueError(f"Category '{self.key}' is enabled but has no criteria.")
            if self.index_path is None or self.meta_path is None:
                raise ValueError(f"Category '{self.key}' is enabled but is missing an index path.")
            if not self.index_path.exists() or not self.meta_path.exists():
                raise ValueError(
                    f"Category '{self.key}' index files are missing on disk: "
                    f"{self.index_path}, {self.meta_path}"
                )


# ---------------------------------------------------------------------------
# Internal registry storage
# ---------------------------------------------------------------------------

_REGISTRY: dict[str, CategoryConfig] = {}


class UnknownCategory(KeyError):
    """Raised when looking up a category not registered."""


class CategoryNotEnabled(RuntimeError):
    """Raised when trying to evaluate against a registered-but-not-enabled category."""


def register_category(config: CategoryConfig) -> None:
    """Register a category configuration. Idempotent overwrite on same key."""
    _REGISTRY[config.key] = config


def get_category(key: str) -> CategoryConfig:
    """Return the registered config or raise `UnknownCategory`."""
    try:
        return _REGISTRY[key]
    except KeyError:
        raise UnknownCategory(
            f"Category '{key}' is not registered. "
            f"Known: {sorted(_REGISTRY.keys())}"
        ) from None


def require_enabled_category(key: str) -> CategoryConfig:
    """Return the config if registered AND enabled, else raise appropriately."""
    cfg = get_category(key)
    if not cfg.enabled:
        raise CategoryNotEnabled(
            f"Category '{key}' is registered but not enabled — "
            f"no RAG index / criteria wired up yet."
        )
    return cfg


def list_categories() -> list[CategoryConfig]:
    """Return all registered categories. UI-facing listing."""
    return list(_REGISTRY.values())


def list_enabled_keys() -> set[str]:
    """Return the set of category keys that are fully enabled (have a working index)."""
    return {c.key for c in _REGISTRY.values() if c.enabled}


# ---------------------------------------------------------------------------
# Bootstrap: register the known categories
# ---------------------------------------------------------------------------
# This module-level code runs at import time. Importing `pipeline` registers
# every category the engine knows about. New categories are added by extending
# this section.

def _bootstrap() -> None:
    """Register every category the engine knows about."""
    # --- Outdoor (fully wired) -----------------------------------------------
    from .outdoor_criteria import OUTDOOR_CRITERIA

    register_category(
        CategoryConfig(
            key="Outdoor",
            label="Outdoor",
            family="Classic",
            enabled=True,
            criteria=OUTDOOR_CRITERIA,
            index_path=_DATA_DIR / "outdoor_index.npy",
            meta_path=_DATA_DIR / "outdoor_index_meta.jsonl",
            tier_bands={
                "Grand Prix": (90, 100),
                "Gold": (80, 100),
                "Silver": (65, 80),
                "Bronze": (50, 65),
            },
        )
    )

    # --- PR (fully wired) ----------------------------------------------------
    from .pr_criteria import PR_CRITERIA

    register_category(
        CategoryConfig(
            key="PR",
            label="PR",
            family="Engagement",
            enabled=True,
            criteria=PR_CRITERIA,
            index_path=_DATA_DIR / "pr_index.npy",
            meta_path=_DATA_DIR / "pr_index_meta.jsonl",
            tier_bands={
                "Grand Prix": (90, 100),
                "Gold": (80, 100),
                "Silver": (65, 80),
                "Bronze": (50, 65),
            },
        )
    )

    # --- Print & Publishing (fully wired) ------------------------------------
    _print_index = _DATA_DIR / "print_index.npy"
    _print_meta = _DATA_DIR / "print_index_meta.jsonl"
    if _print_index.exists() and _print_meta.exists():
        from .print_criteria import PRINT_CRITERIA

        register_category(
            CategoryConfig(
                key="Print & Publishing",
                label="Print & Publishing",
                family="Classic",
                enabled=True,
                criteria=PRINT_CRITERIA,
                index_path=_print_index,
                meta_path=_print_meta,
                tier_bands={
                    "Grand Prix": (90, 100),
                    "Gold": (80, 100),
                    "Silver": (65, 80),
                    "Bronze": (50, 65),
                },
            )
        )

    # --- Design (fully wired) ------------------------------------------------
    _design_index = _DATA_DIR / "design_index.npy"
    _design_meta = _DATA_DIR / "design_index_meta.jsonl"
    if _design_index.exists() and _design_meta.exists():
        from .design_criteria import DESIGN_CRITERIA

        register_category(
            CategoryConfig(
                key="Design",
                label="Design",
                family="Craft",
                enabled=True,
                criteria=DESIGN_CRITERIA,
                index_path=_design_index,
                meta_path=_design_meta,
                tier_bands={
                    "Grand Prix": (90, 100),
                    "Gold": (80, 100),
                    "Silver": (65, 80),
                    "Bronze": (50, 65),
                },
            )
        )

    # --- Direct (fully wired) ------------------------------------------------
    _direct_index = _DATA_DIR / "direct_index.npy"
    _direct_meta = _DATA_DIR / "direct_index_meta.jsonl"
    if _direct_index.exists() and _direct_meta.exists():
        from .direct_criteria import DIRECT_CRITERIA

        register_category(
            CategoryConfig(
                key="Direct",
                label="Direct",
                family="Engagement",
                enabled=True,
                criteria=DIRECT_CRITERIA,
                index_path=_direct_index,
                meta_path=_direct_meta,
                tier_bands={
                    "Grand Prix": (90, 100),
                    "Gold": (80, 100),
                    "Silver": (65, 80),
                    "Bronze": (50, 65),
                },
            )
        )

    # --- Industry Craft (fully wired) ----------------------------------------
    _ic_index = _DATA_DIR / "industry_craft_index.npy"
    _ic_meta = _DATA_DIR / "industry_craft_index_meta.jsonl"
    if _ic_index.exists() and _ic_meta.exists():
        from .industry_craft_criteria import INDUSTRY_CRAFT_CRITERIA

        register_category(
            CategoryConfig(
                key="Industry Craft",
                label="Industry Craft",
                family="Craft",
                enabled=True,
                criteria=INDUSTRY_CRAFT_CRITERIA,
                index_path=_ic_index,
                meta_path=_ic_meta,
                tier_bands={
                    "Grand Prix": (90, 100),
                    "Gold": (80, 100),
                    "Silver": (65, 80),
                    "Bronze": (50, 65),
                },
            )
        )

    # --- Media (fully wired) -------------------------------------------------
    _media_index = _DATA_DIR / "media_index.npy"
    _media_meta = _DATA_DIR / "media_index_meta.jsonl"
    if _media_index.exists() and _media_meta.exists():
        from .media_criteria import MEDIA_CRITERIA

        register_category(
            CategoryConfig(
                key="Media",
                label="Media",
                family="Engagement",
                enabled=True,
                criteria=MEDIA_CRITERIA,
                index_path=_media_index,
                meta_path=_media_meta,
                tier_bands={
                    "Grand Prix": (90, 100),
                    "Gold": (80, 100),
                    "Silver": (65, 80),
                    "Bronze": (50, 65),
                },
            )
        )

    # --- Brand Experience & Activation (fully wired) -------------------------
    _bxa_index = _DATA_DIR / "bxa_index.npy"
    _bxa_meta = _DATA_DIR / "bxa_index_meta.jsonl"
    if _bxa_index.exists() and _bxa_meta.exists():
        from .bxa_criteria import BXA_CRITERIA

        register_category(
            CategoryConfig(
                key="Brand Experience & Activation",
                label="Brand Experience & Activation",
                family="Experience",
                enabled=True,
                criteria=BXA_CRITERIA,
                index_path=_bxa_index,
                meta_path=_bxa_meta,
                tier_bands={
                    "Grand Prix": (90, 100),
                    "Gold": (80, 100),
                    "Silver": (65, 80),
                    "Bronze": (50, 65),
                },
            )
        )

    # --- Health & Wellness (fully wired) -------------------------------------
    _health_index = _DATA_DIR / "health_index.npy"
    _health_meta = _DATA_DIR / "health_index_meta.jsonl"
    if _health_index.exists() and _health_meta.exists():
        from .health_criteria import HEALTH_CRITERIA

        register_category(
            CategoryConfig(
                key="Health & Wellness",
                label="Health & Wellness",
                family="Health",
                enabled=True,
                criteria=HEALTH_CRITERIA,
                index_path=_health_index,
                meta_path=_health_meta,
                tier_bands={
                    "Grand Prix": (90, 100),
                    "Gold": (80, 100),
                    "Silver": (65, 80),
                    "Bronze": (50, 65),
                },
            )
        )

    # --- Sustainable Development Goals (fully wired) -------------------------
    _sdg_index = _DATA_DIR / "sdg_index.npy"
    _sdg_meta = _DATA_DIR / "sdg_index_meta.jsonl"
    if _sdg_index.exists() and _sdg_meta.exists():
        from .sdg_criteria import SDG_CRITERIA

        register_category(
            CategoryConfig(
                key="Sustainable Development Goals",
                label="Sustainable Development Goals",
                family="Good",
                enabled=True,
                criteria=SDG_CRITERIA,
                index_path=_sdg_index,
                meta_path=_sdg_meta,
                tier_bands={
                    "Grand Prix": (90, 100),
                    "Gold": (80, 100),
                    "Silver": (65, 80),
                    "Bronze": (50, 65),
                },
            )
        )

    # --- Entertainment Lions for Sport (fully wired) -------------------------
    _ent_sport_index = _DATA_DIR / "ent_sport_index.npy"
    _ent_sport_meta = _DATA_DIR / "ent_sport_index_meta.jsonl"
    if _ent_sport_index.exists() and _ent_sport_meta.exists():
        from .ent_sport_criteria import ENT_SPORT_CRITERIA

        register_category(
            CategoryConfig(
                key="Entertainment Lions for Sport",
                label="Entertainment Lions for Sport",
                family="Entertainment",
                enabled=True,
                criteria=ENT_SPORT_CRITERIA,
                index_path=_ent_sport_index,
                meta_path=_ent_sport_meta,
                tier_bands={
                    "Grand Prix": (90, 100),
                    "Gold": (80, 100),
                    "Silver": (65, 80),
                    "Bronze": (50, 65),
                },
            )
        )

    # --- Entertainment (fully wired) -----------------------------------------
    _ent_index = _DATA_DIR / "entertainment_index.npy"
    _ent_meta = _DATA_DIR / "entertainment_index_meta.jsonl"
    if _ent_index.exists() and _ent_meta.exists():
        from .entertainment_criteria import ENTERTAINMENT_CRITERIA

        register_category(
            CategoryConfig(
                key="Entertainment",
                label="Entertainment",
                family="Entertainment",
                enabled=True,
                criteria=ENTERTAINMENT_CRITERIA,
                index_path=_ent_index,
                meta_path=_ent_meta,
                tier_bands={
                    "Grand Prix": (90, 100),
                    "Gold": (80, 100),
                    "Silver": (65, 80),
                    "Bronze": (50, 65),
                },
            )
        )

    # --- Social & Influencer (fully wired) -----------------------------------
    _social_index = _DATA_DIR / "social_index.npy"
    _social_meta = _DATA_DIR / "social_index_meta.jsonl"
    if _social_index.exists() and _social_meta.exists():
        from .social_criteria import SOCIAL_CRITERIA

        register_category(
            CategoryConfig(
                key="Social & Influencer",
                label="Social & Influencer",
                family="Engagement",
                enabled=True,
                criteria=SOCIAL_CRITERIA,
                index_path=_social_index,
                meta_path=_social_meta,
                tier_bands={
                    "Grand Prix": (90, 100),
                    "Gold": (80, 100),
                    "Silver": (65, 80),
                    "Bronze": (50, 65),
                },
            )
        )

    # --- Film (fully wired) --------------------------------------------------
    _film_index = _DATA_DIR / "film_index.npy"
    _film_meta = _DATA_DIR / "film_index_meta.jsonl"
    if _film_index.exists() and _film_meta.exists():
        from .film_criteria import FILM_CRITERIA

        register_category(
            CategoryConfig(
                key="Film",
                label="Film",
                family="Classic",
                enabled=True,
                criteria=FILM_CRITERIA,
                index_path=_film_index,
                meta_path=_film_meta,
                tier_bands={
                    "Grand Prix": (90, 100),
                    "Gold": (80, 100),
                    "Silver": (65, 80),
                    "Bronze": (50, 65),
                },
            )
        )

    # --- Creative Strategy (fully wired) -------------------------------------
    _cs_index = _DATA_DIR / "creative_strategy_index.npy"
    _cs_meta = _DATA_DIR / "creative_strategy_index_meta.jsonl"
    if _cs_index.exists() and _cs_meta.exists():
        from .creative_strategy_criteria import CREATIVE_STRATEGY_CRITERIA

        register_category(
            CategoryConfig(
                key="Creative Strategy",
                label="Creative Strategy",
                family="Strategy",
                enabled=True,
                criteria=CREATIVE_STRATEGY_CRITERIA,
                index_path=_cs_index,
                meta_path=_cs_meta,
                tier_bands={
                    "Grand Prix": (90, 100),
                    "Gold": (80, 100),
                    "Silver": (65, 80),
                    "Bronze": (50, 65),
                },
            )
        )

    # --- Placeholders for all the other Cannes Lions categories --------------
    # These are registered as `enabled=False`. They show up in the API listing
    # so the UI can render the dropdown with "coming soon" affordances, but
    # they reject any evaluation attempt.
    placeholders: list[tuple[str, str, str]] = [
        # (key, label, family)
        ("Creative Brand", "Creative Brand", "Brand"),
        ("Audio & Radio", "Audio & Radio", "Classic"),
        ("Film", "Film", "Classic"),
        ("Print & Publishing", "Print & Publishing", "Classic"),
        ("Design", "Design", "Craft"),
        ("Digital Craft", "Digital Craft", "Craft"),
        ("Film Craft", "Film Craft", "Craft"),
        ("Industry Craft", "Industry Craft", "Craft"),
        ("Creative B2B", "Creative B2B", "Engagement"),
        ("Creative Data", "Creative Data", "Engagement"),
        ("Direct", "Direct", "Engagement"),
        ("Media", "Media", "Engagement"),
        ("PR", "PR", "Engagement"),
        ("Social & Creator", "Social & Creator", "Engagement"),
        ("Entertainment", "Entertainment", "Entertainment"),
        ("Entertainment for Gaming", "Entertainment for Gaming", "Entertainment"),
        ("Entertainment for Music", "Entertainment for Music", "Entertainment"),
        ("Entertainment for Sport", "Entertainment for Sport", "Entertainment"),
        ("Brand Experience & Activation", "Brand Experience & Activation", "Experience"),
        ("Creative Business Transformation", "Creative Business Transformation", "Experience"),
        ("Creative Commerce", "Creative Commerce", "Experience"),
        ("Innovation", "Innovation", "Experience"),
        ("Luxury", "Luxury & Lifestyle", "Experience"),
        ("Glass (The Lion for Change)", "Glass · The Lion for Change", "Good"),
        ("Sustainable Development Goals", "Sustainable Development Goals", "Good"),
        ("Health & Wellness", "Health & Wellness", "Health"),
        ("Pharma", "Pharma", "Health"),
        ("Creative Effectiveness", "Creative Effectiveness", "Strategy"),
        ("Creative Strategy", "Creative Strategy", "Strategy"),
        ("Titanium", "Titanium", "Titanium"),
    ]
    for key, label, family in placeholders:
        if key in _REGISTRY:
            continue  # already registered as enabled above
        register_category(CategoryConfig(key=key, label=label, family=family, enabled=False))


_bootstrap()
