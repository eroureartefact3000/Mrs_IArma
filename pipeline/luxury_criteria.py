"""Luxury & Lifestyle Lions judging criteria.

Craft-led category for luxury and lifestyle brands. Execution matters as
much as idea; impact often qualitative (cultural resonance over hard metrics).
    25% Idea  /  15% Strategy  /  35% Execution  /  25% Impact
"""
from typing import Literal


LUXURY_CRITERIA: dict = {
    "category": "Luxury",
    "definition": (
        "The Luxury & Lifestyle Lions celebrate creative work for luxury and "
        "premium lifestyle brands: fashion, jewellery, watches, beauty, hotels, "
        "spirits, automotive luxury. Execution craft and cultural elegance "
        "carry equal weight to the idea. Impact tends to be qualitative."
    ),
    "axes": [
        {"key": "idea", "name": "Idea", "weight": 0.25,
         "description": "Originality fit for luxury sensibility. Restraint, surprise, cultural depth.",
         "signals": ["Tonal precision (luxury voice, not mass-market)", "Cultural resonance", "Brand-heritage tension (honour while modernising)", "Restraint as craft"]},
        {"key": "strategy", "name": "Strategy", "weight": 0.15,
         "description": "WHY this idea protects + extends brand equity.",
         "signals": ["WHO IS THE BRAND? Heritage and equity", "Audience precision (luxury consumer segments)", "Brand mission ↔ idea coherence"]},
        {"key": "execution", "name": "Execution", "weight": 0.35,
         "description": "HOW the work is crafted. Production quality, art direction, materiality, restraint.",
         "signals": ["Craft quality (production, photography, film, materials)", "Art direction discipline", "Talent / casting fit", "Tonal control", "Materiality when applicable"]},
        {"key": "impact", "name": "Impact", "weight": 0.25,
         "description": "Brand equity shifts, cultural conversation, prestige metrics.",
         "signals": ["Brand-equity / desirability shifts", "Cultural conversation (fashion / luxury press)", "Sales / clientele growth when relevant", "Heritage refresh metrics"]},
    ],
    "sub_categories_hint": {
        "A": "Luxury Sectors (Fashion, Jewellery, Watches, Beauty, Hotels, Auto, Spirits)",
        "B": "Excellence in Luxury Craft",
        "C": "Cultural Engagement in Luxury",
    },
}

Tier = Literal["Grand Prix", "Gold", "Silver", "Bronze", "Shortlist", "Loser"]
_BANDS = {"Grand Prix": (90, 100), "Gold": (80, 100), "Silver": (65, 80), "Bronze": (50, 65)}


def expected_score_range(tier: Tier) -> tuple[int, int] | None:
    return _BANDS.get(tier)


def tier_consistency(tier: Tier, weighted_score: float) -> Literal["expected", "below", "above", "n/a"]:
    band = _BANDS.get(tier)
    if band is None: return "n/a"
    low, high = band
    if weighted_score < low: return "below"
    if weighted_score > high: return "above"
    return "expected"
