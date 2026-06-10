"""Creative B2B Lions judging criteria.

Business-to-business creative work. Strategy and Impact dominate because
B2B targets are narrow and outcomes are commercial.
    25% Idea  /  20% Strategy  /  20% Execution  /  35% Impact
"""
from typing import Literal


CREATIVE_B2B_CRITERIA: dict = {
    "category": "Creative B2B",
    "definition": (
        "The Creative B2B Lions celebrate creative work targeted at business "
        "decision-makers: enterprise tech, B2B services, industrial brands, "
        "B2B trade media. Audiences are narrower and outcomes are commercial. "
        "Strategy and Impact dominate."
    ),
    "axes": [
        {"key": "idea", "name": "Idea", "weight": 0.25,
         "description": "Originality of the B2B concept. Cuts through to a narrow, sophisticated audience.",
         "signals": ["Uniqueness vs B2B-category clichés (avoid generic 'business growth' tropes)", "Audience-savvy creativity", "Mnemonic for an expert decision-maker", "Translatability across industries"]},
        {"key": "strategy", "name": "Strategy", "weight": 0.20,
         "description": "WHO is the decision-maker, WHY this insight will move them, HOW it ties to business outcome.",
         "signals": ["Decision-maker identification (CIO, CFO, procurement, etc.)", "Insight rooted in real B2B-buyer behaviour", "Brand mission ↔ idea coherence", "Account-based-marketing rationale when applicable"]},
        {"key": "execution", "name": "Execution", "weight": 0.20,
         "description": "HOW the work was crafted and orchestrated to reach narrow B2B audiences.",
         "signals": ["Craft quality", "Channel choice fit for B2B audiences (LinkedIn, trade media, events, direct sales enablement)", "Multi-touchpoint orchestration", "Sales-enablement integration"]},
        {"key": "impact", "name": "Business Impact", "weight": 0.35,
         "description": "Dominant axis. Pipeline impact, qualified leads, deals closed, customer acquisition, ABM hit rate.",
         "signals": ["Pipeline / opportunity value generated", "Qualified leads count", "Deals closed / new customer accounts", "Customer-lifetime-value shifts", "Sales-cycle reduction", "Brand-among-target shifts"]},
    ],
    "sub_categories_hint": {
        "A": "Sectors (Tech, Industrial, Financial Services, Healthcare, etc.)",
        "B": "Account-Based Marketing",
        "C": "B2B Brand Strategy & Positioning",
        "D": "Use of Tech / Innovation in B2B",
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
