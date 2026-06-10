"""Innovation Lions judging criteria.

Reward technological / methodological breakthrough as the creative work.
    30% Idea  /  10% Strategy  /  30% Execution  /  30% Impact
"""
from typing import Literal


INNOVATION_CRITERIA: dict = {
    "category": "Innovation",
    "definition": (
        "The Innovation Lions celebrate breakthrough technology / method / "
        "platform creating new creative possibilities. The work must show "
        "a technological or methodological first, with the creative idea "
        "made possible by that innovation."
    ),
    "axes": [
        {"key": "idea", "name": "Innovation Idea", "weight": 0.30,
         "description": "Originality of the technical breakthrough.",
         "signals": ["Technical first (not just 'AI used here')", "Patent-worthy or genuinely novel approach", "Re-applicable across brands / industries"]},
        {"key": "strategy", "name": "Strategy", "weight": 0.10,
         "description": "Brand fit + audience relevance for the innovation.",
         "signals": ["WHO IS THE BRAND? Tech-innovation credibility", "Innovation ↔ brand mission coherence"]},
        {"key": "execution", "name": "Execution", "weight": 0.30,
         "description": "HOW the innovation was built and delivered. Engineering quality, deployment scale.",
         "signals": ["Engineering craft", "Deployment scale (proof-of-concept vs in-production)", "User experience quality", "Multi-platform / multi-region scale-up"]},
        {"key": "impact", "name": "Impact", "weight": 0.30,
         "description": "Documented user / business / industry impact + replicability.",
         "signals": ["User adoption / engagement", "Business outcome", "Industry recognition (patents, tech press, academic citation)", "Re-use by other brands / agencies"]},
    ],
    "sub_categories_hint": {
        "A": "Applied Innovation (real product / service)",
        "B": "Use of AI / Machine Learning",
        "C": "Use of Emerging Technology (XR, blockchain, quantum)",
        "D": "Industry Innovation (process / methodology)",
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
