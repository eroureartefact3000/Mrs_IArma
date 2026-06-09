"""Smoke tests for the category registry.

These tests don't hit external APIs. They verify the registry bootstraps
correctly, knows Outdoor is enabled, and raises clean errors for unknown /
not-enabled categories.
"""
from __future__ import annotations

import pytest


def test_registry_has_outdoor_enabled():
    from pipeline.category_registry import get_category

    cfg = get_category("Outdoor")
    assert cfg.enabled is True
    assert cfg.criteria is not None
    assert cfg.index_path is not None and cfg.index_path.exists()
    assert cfg.meta_path is not None and cfg.meta_path.exists()
    assert cfg.label == "Outdoor"
    assert cfg.family == "Classic"


def test_registry_lists_at_least_30_categories():
    from pipeline.category_registry import list_categories

    cats = list_categories()
    assert len(cats) >= 30
    keys = {c.key for c in cats}
    # Spot-check a few canonical categories
    for k in ["Outdoor", "PR", "Film", "Health & Wellness", "Innovation"]:
        assert k in keys


def test_registry_only_outdoor_is_enabled_in_mvp():
    """The MVP exposes Outdoor as the only enabled category."""
    from pipeline.category_registry import list_enabled_keys

    assert list_enabled_keys() == {"Outdoor"}


def test_unknown_category_raises_unknown():
    from pipeline.category_registry import UnknownCategory, get_category

    with pytest.raises(UnknownCategory):
        get_category("NotARealCategory")


def test_disabled_category_raises_not_enabled():
    """`PR` is registered as a placeholder but not enabled — require_enabled_category should reject it."""
    from pipeline.category_registry import (
        CategoryNotEnabled,
        require_enabled_category,
    )

    with pytest.raises(CategoryNotEnabled):
        require_enabled_category("PR")


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
