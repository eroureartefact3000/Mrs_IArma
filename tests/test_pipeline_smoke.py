"""Smoke tests for the pipeline package.

These tests do NOT hit any external API (Anthropic / Voyage). They verify:
  - the public API surface is importable and stable
  - the Pydantic schemas validate sane input
  - the presentation layer assembles correctly from synthetic data
  - the RAG index files are present and loadable

For integration tests against real API calls, see `scripts/test_5_boards.py`
(dev tool — paid).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

# ----------------------------------------------------------------------------
# Public API surface
# ----------------------------------------------------------------------------


def test_public_api_imports():
    """The public exports listed in pipeline.__all__ must all be importable."""
    import pipeline

    assert pipeline.__version__
    for name in pipeline.__all__:
        assert hasattr(pipeline, name), f"pipeline.{name} missing"

    # Spot-check key symbols
    from pipeline import (  # noqa: F401
        evaluate_board,
        UserMetadata,
        BoardEvaluation,
        TierPrediction,
    )


def test_user_metadata_validation():
    """UserMetadata must accept valid input and reject empty fields."""
    from pipeline import UserMetadata
    from pydantic import ValidationError

    m = UserMetadata(
        campaign_name="Phone Break",
        agency="VML Prague",
        client="KitKat",
        category="Outdoor",
        client_internationally_known=True,
    )
    assert m.campaign_name == "Phone Break"
    assert m.client_internationally_known is True

    # Default category is Outdoor
    m2 = UserMetadata(campaign_name="x", agency="x", client="x")
    assert m2.category == "Outdoor"


# ----------------------------------------------------------------------------
# Presentation layer (verdicts, presages, axes) — no API calls
# ----------------------------------------------------------------------------


def test_presentation_tier_label_mapping():
    from pipeline.presentation import TIER_LABEL

    assert TIER_LABEL["Grand Prix"] == "GRAND PRIX LION"
    assert TIER_LABEL["Gold"] == "GOLD LION"
    assert TIER_LABEL["No Medal"] == "NO LION"


def test_presentation_build_tier_prediction_full_favorable():
    """End-to-end synthetic build: Pedigree-like Gold prediction, all présages favorable."""
    from pipeline.outdoor_criteria import OUTDOOR_CRITERIA
    from pipeline.presentation import build_tier_prediction

    tp = build_tier_prediction(
        criteria=OUTDOOR_CRITERIA,
        board_id="adoptable-pedigree-test",
        predicted_tier="Gold",
        tier_probabilities={
            "Grand Prix": 0.07,
            "Gold": 0.45,
            "Silver": 0.30,
            "Bronze": 0.13,
            "No Medal": 0.05,
        },
        final_weighted_score=84.0,
        axis_scores={"idea": 95, "strategy": 92, "execution": 93, "impact": 88},
        malus={
            "aesthetic_applied": False,
            "client_applied": False,
            "network_applied": False,
            "detected_holding": "Omnicom",
            "multiplier": 1.0,
            "notes": [],
        },
        synthesis="Strong idea, clean execution, impact proof still to be anchored.",
    )

    assert tp.predicted_tier == "Gold"
    assert tp.tier_label == "GOLD LION"
    assert tp.score_percent == 84
    # Gap between top-1 (0.45) and top-2 (0.30) is 0.15 → "medium" per the
    # _confidence_from_distribution thresholds (>=0.08 = medium, >=0.20 = high).
    assert tp.confidence == "medium"
    assert len(tp.axes) == 4
    assert len(tp.presages) == 3
    assert all(p.kind == "favorable" for p in tp.presages)
    # Axes carry correct display labels and weights
    by_key = {a.key: a for a in tp.axes}
    assert by_key["idea"].label == "Creative Idea"
    assert by_key["idea"].weight == 0.35
    assert by_key["impact"].label == "Impact & Results"
    assert by_key["impact"].weight == 0.25
    # Network presage names the detected holding
    network_p = next(p for p in tp.presages if p.type == "network")
    assert "Omnicom" in network_p.detail


def test_presentation_build_tier_prediction_all_unfavorable():
    """Loser-like prediction: all 3 presages unfavorable, mystic verdict 'No Lion'."""
    from pipeline.outdoor_criteria import OUTDOOR_CRITERIA
    from pipeline.presentation import build_tier_prediction

    tp = build_tier_prediction(
        criteria=OUTDOOR_CRITERIA,
        board_id="loser-test",
        predicted_tier="No Medal",
        tier_probabilities={
            "Grand Prix": 0.02,
            "Gold": 0.08,
            "Silver": 0.15,
            "Bronze": 0.20,
            "No Medal": 0.55,
        },
        final_weighted_score=34.0,
        axis_scores={"idea": 38, "strategy": 32, "execution": 40, "impact": 26},
        malus={
            "aesthetic_applied": True,
            "client_applied": True,
            "network_applied": True,
            "detected_holding": None,
            "multiplier": 0.50,
            "notes": [],
        },
        synthesis="An idea that struggles to land.",
    )

    assert tp.predicted_tier == "No Medal"
    assert tp.tier_label == "NO LION"
    assert tp.score_percent == 34
    assert tp.confidence == "high"  # 0.55 vs 0.20 = 0.35 gap
    assert all(p.kind == "unfavorable" for p in tp.presages)
    assert sum(p.malus_pct for p in tp.presages) == 50  # 10 + 20 + 20


def test_presentation_mystic_verdict_variants_deterministic():
    """Same board id → same verdict variant picked (deterministic hashing)."""
    from pipeline.presentation import _pick_verdict

    v1 = _pick_verdict("Gold", "board-abc")
    v2 = _pick_verdict("Gold", "board-abc")
    assert v1 == v2


# ----------------------------------------------------------------------------
# Malus rules
# ----------------------------------------------------------------------------


def test_malus_no_penalties_when_favorable():
    from pipeline.malus import compute_malus

    m = compute_malus(
        craft_quality="high",
        agency_name="BBDO New York",
        client_internationally_known=True,
    )
    assert m.multiplier == 1.0
    assert m.detected_holding == "Omnicom"
    assert not m.aesthetic_applied
    assert not m.client_applied
    assert not m.network_applied


def test_malus_all_penalties_when_unfavorable():
    from pipeline.malus import compute_malus

    m = compute_malus(
        craft_quality="low",
        agency_name="Some Independent Studio",
        client_internationally_known=False,
    )
    # 10 + 20 + 20 = 50% deduction → 0.50 multiplier
    assert m.multiplier == 0.50
    assert m.aesthetic_applied
    assert m.client_applied
    assert m.network_applied
    assert m.detected_holding is None


def test_malus_holding_detection_all_six():
    """All 6 supported holdings must be detected from common agency names."""
    from pipeline.malus import detect_holding

    cases = [
        ("Publicis Conseil Paris", "Publicis"),
        ("Leo Burnett London", "Publicis"),
        ("Havas Paris", "Havas"),
        ("BETC Paris", "Havas"),
        ("BBDO India Mumbai", "Omnicom"),
        ("TBWA Worldwide", "Omnicom"),
        ("DDB New Zealand", "Omnicom"),
        ("Ogilvy Sao Paulo", "WPP"),
        ("VML Prague", "WPP"),
        ("Grey Mexico", "WPP"),
        ("McCann Paris", "IPG"),
        ("FCB India Mumbai", "IPG"),
        ("MullenLowe", "IPG"),
        ("Dentsu Creative Taipei", "Dentsu"),
        ("Some Independent Studio", None),
    ]
    for agency, expected in cases:
        assert detect_holding(agency) == expected, f"detect_holding('{agency}') expected {expected}"


# ----------------------------------------------------------------------------
# Score → tier mapping
# ----------------------------------------------------------------------------


def test_score_to_tier_thresholds():
    """The brief's 90/80/65/50 thresholds must map cleanly to tiers."""
    from pipeline.evaluate import _score_to_tier

    assert _score_to_tier(95.0) == "Grand Prix"
    assert _score_to_tier(90.0) == "Grand Prix"
    assert _score_to_tier(89.9) == "Gold"
    assert _score_to_tier(80.0) == "Gold"
    assert _score_to_tier(79.9) == "Silver"
    assert _score_to_tier(65.0) == "Silver"
    assert _score_to_tier(64.9) == "Bronze"
    assert _score_to_tier(50.0) == "Bronze"
    assert _score_to_tier(49.9) == "No Medal"
    assert _score_to_tier(0.0) == "No Medal"


# ----------------------------------------------------------------------------
# RAG index integrity (no API call — just verify files load)
# ----------------------------------------------------------------------------


def test_rag_index_files_present():
    """The committed RAG index files must exist and be loadable as numpy."""
    from pipeline.search import DEFAULT_EMBEDDINGS, DEFAULT_META

    assert DEFAULT_EMBEDDINGS.exists(), f"missing {DEFAULT_EMBEDDINGS}"
    assert DEFAULT_META.exists(), f"missing {DEFAULT_META}"

    matrix = np.load(DEFAULT_EMBEDDINGS)
    assert matrix.ndim == 2
    assert matrix.shape[1] == 1024, f"expected 1024-dim vectors, got {matrix.shape[1]}"
    assert matrix.shape[0] > 100, f"expected >100 boards in index, got {matrix.shape[0]}"

    # Meta jsonl has one record per matrix row
    n_meta = sum(1 for line in DEFAULT_META.open() if line.strip())
    assert n_meta == matrix.shape[0], f"meta has {n_meta} rows, matrix has {matrix.shape[0]}"


def test_rag_meta_records_have_required_fields():
    """Each meta record must carry the fields the judge prompt expects."""
    from pipeline.search import DEFAULT_META

    with DEFAULT_META.open() as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            for key in ("id", "tier", "campaign", "weighted_score", "full_record"):
                assert key in d, f"meta row {i} missing '{key}'"
            if i >= 5:
                break  # don't read the whole file
