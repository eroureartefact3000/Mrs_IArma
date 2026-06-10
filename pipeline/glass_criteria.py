"""Glass · The Lion for Change judging criteria.

Reward creative work that breaks down gender inequality or harmful gender
stereotypes. Impact dominant: did the work shift perceptions / behaviour?
    25% Idea  /  20% Strategy  /  15% Execution  /  40% Impact
"""
from typing import Literal


GLASS_CRITERIA: dict = {
    "category": "Glass (The Lion for Change)",
    "definition": (
        "The Glass Lion awards creative work that addresses gender inequality "
        "or harmful gender stereotypes (and intersectionally: race, sexuality, "
        "ability). The work must show genuine intent to drive change, not "
        "purpose-washing. Impact dominates."
    ),
    "axes": [
        {"key": "idea", "name": "Idea", "weight": 0.25,
         "description": "Originality of the change-driving concept.",
         "signals": ["Reframes a stereotype boldly", "Centres affected community's voice", "Mnemonic device with cultural travel"]},
        {"key": "strategy", "name": "Strategy", "weight": 0.20,
         "description": "WHO does this serve, WHY does the brand have authority, HOW is the stereotype addressed.",
         "signals": ["Specific stereotype / inequality named", "Affected community involvement (co-author, not subject)", "Brand authority to speak (no purpose-washing)", "Data-rooted insight"]},
        {"key": "execution", "name": "Execution", "weight": 0.15,
         "description": "Craft + orchestration, but lighter than impact.",
         "signals": ["Craft quality", "Channel choice + earned-media orchestration", "Multi-execution coherence"]},
        {"key": "impact", "name": "Change Impact", "weight": 0.40,
         "description": "Dominant. Documented attitudinal / behavioural / legislative shift, with affected community recognition.",
         "signals": ["Behaviour change (signed petitions, joined movements, changed practice)", "Attitude shift documented in surveys", "Legislative / policy change", "Industry / system-level adoption", "Cultural conversation among the affected community"]},
    ],
    "sub_categories_hint": {
        "A": "Gender Equality",
        "B": "Stereotype-Breaking",
        "C": "Intersectional (gender + race / sexuality / ability)",
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
