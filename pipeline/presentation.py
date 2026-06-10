"""Presentation layer — assemble the user-facing TierPrediction for the UI.

Translates the raw pipeline output into the Mrs Airma · The Cannes Oracle
domain language (oracle tone, English) used by the front-end mockups.

Responsibilities:
  - Map English tier names → display labels (e.g. "Grand Prix" → "GRAND PRIX LION")
  - Pick the tier-specific oracle verdict (4 outcomes covered)
  - Build the 3 structured presages (favorable/unfavorable) from the malus breakdown
  - Compute the confidence label from the tier probability distribution
  - Translate axis keys to display labels with the category's official weights
"""
from __future__ import annotations

from typing import Any

from .schema import (
    AxisDisplay,
    ConfidenceLabel,
    PredictedTier,
    Presage,
    TierPrediction,
)


# ----------------------------------------------------------------------------
# Tier → display label & oracle verdict
# ----------------------------------------------------------------------------

# Display label as shown in the hero of the result page.
TIER_LABEL: dict[str, str] = {
    "Grand Prix": "GRAND PRIX LION",
    "Gold": "GOLD LION",
    "Silver": "SILVER LION",
    "Bronze": "BRONZE LION",
    "No Medal": "NO LION",
}

# Tier-specific oracle verdict in italic on the result page.
# Variants per tier for slight variety across consultations. Indexed by hash %.
MYSTIC_VERDICTS: dict[str, list[str]] = {
    "Grand Prix": [
        "The stars align. Your campaign will carry the highest honour.",
        "Mrs Airma sees it clearly: your work brushes the Cannes Grail.",
        "A comet bursts open. The Grand Prix reaches out to you.",
    ],
    "Gold": [
        "The stars bow. Your campaign will carry gold.",
        "Mrs Airma smiles. Gold rises on the horizon.",
        "The golden lion roars in your favour.",
    ],
    "Silver": [
        "A promising spark. Silver opens its arms to you.",
        "The stars whisper a silver gleam.",
        "Mrs Airma senses the glimmer of silver.",
    ],
    "Bronze": [
        "The promise of a flicker. Still to be polished.",
        "Bronze stirs. Mrs Airma offers her encouragement.",
        "A glimmer of bronze appears. Keep at the craft.",
    ],
    "No Medal": [
        "The stars remain silent. Will you return next year?",
        "The veil stays opaque. Mrs Airma invites you to begin again.",
        "No lion awakens this time. Patience and craft.",
    ],
}


def _pick_verdict(tier: PredictedTier, board_id: str) -> str:
    """Deterministic verdict variant pick based on board id (no API call needed)."""
    variants = MYSTIC_VERDICTS.get(tier, MYSTIC_VERDICTS["No Medal"])
    idx = abs(hash(board_id)) % len(variants)
    return variants[idx]


# ----------------------------------------------------------------------------
# Axes — internal key → display label
# ----------------------------------------------------------------------------

AXIS_LABEL: dict[str, str] = {
    "idea": "Creative Idea",
    "strategy": "Strategy",
    "execution": "Execution",
    "impact": "Impact & Results",
}


def _build_axes(
    axis_scores: dict[str, int | float],
    criteria: dict[str, Any],
) -> list[AxisDisplay]:
    """Translate the LLM-judge axis scores into the UI-facing AxisDisplay list,
    preserving the order defined in the category's criteria so the UI shows the
    weighted axes consistently top to bottom.
    """
    out: list[AxisDisplay] = []
    for axis in criteria["axes"]:
        key = axis["key"]
        out.append(
            AxisDisplay(
                key=key,  # type: ignore[arg-type]
                label=AXIS_LABEL.get(key, key.capitalize()),
                score=int(round(axis_scores.get(key, 0))),
                weight=float(axis["weight"]),
            )
        )
    return out


# ----------------------------------------------------------------------------
# Presages — structured malus criteria in oracle flavour
# ----------------------------------------------------------------------------

# Title + detail templates for each presage. The detail is filled with the actual
# detected holding when network is favorable, or kept generic otherwise.
PRESAGE_AESTHETIC_FAV = (
    "Polished Board",
    "Readable composition, careful hierarchy.",
)
PRESAGE_AESTHETIC_UNFAV = (
    "Off-Standard Board",
    "Composition needs reworking.",
)
PRESAGE_CLIENT_FAV = (
    "International Client",
    "Brand recognised beyond its borders.",
)
PRESAGE_CLIENT_UNFAV = (
    "Confidential Client",
    "Local presence only.",
)
PRESAGE_NETWORK_FAV_TEMPLATE = (
    "Agency of the Inner Circle",
    "{holding} network. A favorable presage.",
)
PRESAGE_NETWORK_UNFAV = (
    "Agency Outside the Circle",
    "Outside Publicis, Havas, Omnicom, WPP, IPG or Dentsu.",
)


def _build_presages(malus: dict) -> list[Presage]:
    """Always returns exactly 3 presages in this order: aesthetic, client, network."""
    presages: list[Presage] = []

    # Aesthetic
    if malus.get("aesthetic_applied"):
        title, detail = PRESAGE_AESTHETIC_UNFAV
        presages.append(Presage(type="aesthetic", kind="unfavorable", title=title, detail=detail, malus_pct=10))
    else:
        title, detail = PRESAGE_AESTHETIC_FAV
        presages.append(Presage(type="aesthetic", kind="favorable", title=title, detail=detail, malus_pct=0))

    # Client international
    if malus.get("client_applied"):
        title, detail = PRESAGE_CLIENT_UNFAV
        presages.append(Presage(type="client", kind="unfavorable", title=title, detail=detail, malus_pct=20))
    else:
        title, detail = PRESAGE_CLIENT_FAV
        presages.append(Presage(type="client", kind="favorable", title=title, detail=detail, malus_pct=0))

    # Network
    if malus.get("network_applied"):
        title, detail = PRESAGE_NETWORK_UNFAV
        presages.append(Presage(type="network", kind="unfavorable", title=title, detail=detail, malus_pct=20))
    else:
        holding = malus.get("detected_holding") or "major"
        title, detail_template = PRESAGE_NETWORK_FAV_TEMPLATE
        detail = detail_template.format(holding=holding)
        presages.append(Presage(type="network", kind="favorable", title=title, detail=detail, malus_pct=0))

    return presages


# ----------------------------------------------------------------------------
# Confidence label — derived from the tier probability distribution
# ----------------------------------------------------------------------------


def _confidence_from_distribution(tier_probs: dict[str, float]) -> ConfidenceLabel:
    """Confidence based on the gap between the top-1 tier and the top-2 tier.

    A large gap (top-1 dominates) → high confidence.
    A small gap (top-1 and top-2 nearly tied) → low confidence.
    """
    sorted_probs = sorted(tier_probs.values(), reverse=True)
    if len(sorted_probs) < 2:
        return "low"
    gap = sorted_probs[0] - sorted_probs[1]
    if gap >= 0.20:
        return "high"
    if gap >= 0.08:
        return "medium"
    return "low"


# ----------------------------------------------------------------------------
# Headline score percent
# ----------------------------------------------------------------------------


def _headline_score_percent(final_weighted_score: float) -> int:
    """The big % shown on the result page.

    Uses the final weighted score (post-malus) clipped to 0-100. The mockups
    display values like '87%' for Gold or '34%' for No Lion, which align with
    the post-malus weighted score.
    """
    return max(0, min(100, int(round(final_weighted_score))))


# ----------------------------------------------------------------------------
# Public assembly
# ----------------------------------------------------------------------------


def build_tier_prediction(
    *,
    board_id: str,
    predicted_tier: PredictedTier,
    tier_probabilities: dict[str, float],
    final_weighted_score: float,
    axis_scores: dict[str, int | float],
    malus: dict,
    synthesis: str,
    criteria: dict[str, Any],
) -> TierPrediction:
    """Assemble the full TierPrediction object the front-end will consume.

    `criteria` carries the per-category axis ordering + weights (e.g. Outdoor's
    35/10/30/25). Pass the criteria dict returned by the registry for the
    user's category.
    """
    return TierPrediction(
        predicted_tier=predicted_tier,
        tier_label=TIER_LABEL.get(predicted_tier, predicted_tier),
        tier_probabilities=tier_probabilities,
        confidence=_confidence_from_distribution(tier_probabilities),
        score_percent=_headline_score_percent(final_weighted_score),
        mystic_verdict=_pick_verdict(predicted_tier, board_id),
        axes=_build_axes(axis_scores, criteria),
        presages=_build_presages(malus),
        synthesis=synthesis,
    )
