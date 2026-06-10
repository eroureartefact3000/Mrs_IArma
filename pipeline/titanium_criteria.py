"""Titanium Lions judging criteria.

The most prestigious Cannes category. Rewards work that breaks new ground
and changes the industry. Distinct from any single sub-discipline.
    35% Idea  /  10% Strategy  /  30% Execution  /  25% Impact
"""
from typing import Literal


TITANIUM_CRITERIA: dict = {
    "category": "Titanium",
    "definition": (
        "The Titanium Lion rewards work that breaks new creative ground — "
        "campaigns that change the industry, redefine how brands behave, or "
        "create new creative formats. The bar is exceptional originality with "
        "documented influence on the discipline itself."
    ),
    "axes": [
        {"key": "idea", "name": "Idea", "weight": 0.35,
         "description": "The biggest weight. Industry-redefining originality.",
         "signals": ["Genuinely category-defining (rewrites the playbook)", "Cross-discipline ambition", "Cultural / industry conversation initiated", "Translatable approach beyond this brand"]},
        {"key": "strategy", "name": "Strategy", "weight": 0.10,
         "description": "Brand authority + audacity. Light weight because Titanium rewards risk.",
         "signals": ["WHO IS THE BRAND? Authority to take this risk", "Audacity of the move", "Brand-mission ↔ idea coherence"]},
        {"key": "execution", "name": "Execution", "weight": 0.30,
         "description": "Cross-discipline execution quality. The work must DELIVER on its ambition.",
         "signals": ["Cross-discipline orchestration", "Production quality across formats", "Scale of execution", "Multi-phase ambition", "Earned-media multiplier"]},
        {"key": "impact", "name": "Impact", "weight": 0.25,
         "description": "Industry / cultural / business impact. The work changed something.",
         "signals": ["Industry influence (other brands copying / responding)", "Cultural footprint", "Business outcome", "Award / press recognition across categories", "Long-term equity build"]},
    ],
    "sub_categories_hint": {
        "A": "Titanium (single sub-category — no further splits)",
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
