"""Smoke tests for the category registry.

These tests don't hit external APIs. They verify the registry bootstraps
correctly with all 30 enabled Cannes Lions 2026 categories and raises clean
errors for unknown categories.
"""
from __future__ import annotations

import pytest


# A spot-check of canonical category keys that must be enabled in every build.
_ENABLED_SAMPLE = {
    "Outdoor",
    "PR",
    "Film",
    "Print & Publishing",
    "Health & Wellness",
    "Innovation",
    "Creative Strategy",
    "Titanium",
    "Design",
    "Glass (The Lion for Change)",
}


def test_registry_has_outdoor_enabled():
    from pipeline.category_registry import get_category

    cfg = get_category("Outdoor")
    assert cfg.enabled is True
    assert cfg.criteria is not None
    assert cfg.index_path is not None and cfg.index_path.exists()
    assert cfg.meta_path is not None and cfg.meta_path.exists()
    assert cfg.label == "Outdoor"
    assert cfg.family == "Classic"


def test_registry_has_thirty_enabled_categories():
    """All 30 Cannes Lions 2026 entry categories must be enabled."""
    from pipeline.category_registry import list_categories, list_enabled_keys

    cats = list_categories()
    assert len(cats) == 30
    enabled = list_enabled_keys()
    assert len(enabled) == 30
    # Every spot-checked category must be enabled
    missing = _ENABLED_SAMPLE - enabled
    assert not missing, f"expected enabled but missing: {missing}"


def test_unknown_category_raises_unknown():
    from pipeline.category_registry import UnknownCategory, get_category

    with pytest.raises(UnknownCategory):
        get_category("NotARealCategory")


def test_require_enabled_passes_for_each_registered_category():
    """`require_enabled_category` should pass for every entry in the registry."""
    from pipeline.category_registry import (
        list_enabled_keys,
        require_enabled_category,
    )

    for key in list_enabled_keys():
        cfg = require_enabled_category(key)
        assert cfg.enabled is True


def test_outdoor_passes_require_enabled():
    from pipeline.category_registry import require_enabled_category

    cfg = require_enabled_category("Outdoor")
    assert cfg.enabled is True


def test_tier_bands_match_brief():
    """Outdoor tier bands should match the brief's 90/80/65/50 thresholds."""
    from pipeline.category_registry import get_category

    cfg = get_category("Outdoor")
    assert cfg.tier_bands == {
        "Grand Prix": (90, 100),
        "Gold": (80, 100),
        "Silver": (65, 80),
        "Bronze": (50, 65),
    }
