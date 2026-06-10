"""Creative Data Lions judging criteria.

Data-driven creative work. Strategy + Impact dominant because the insight
and the result are what get judged.
    20% Idea  /  30% Strategy  /  15% Execution  /  35% Impact
"""
from typing import Literal


CREATIVE_DATA_CRITERIA: dict = {
    "category": "Creative Data",
    "definition": (
        "The Creative Data Lions celebrate creative work where data is the "
        "engine: data-led insight, personalisation, data visualisation as the "
        "creative idea, data-as-product, data-storytelling. Strategy and Impact "
        "carry the dominant weight."
    ),
    "axes": [
        {"key": "idea", "name": "Idea", "weight": 0.20,
         "description": "Originality of the data-driven idea. The creative spark that data unlocks.",
         "signals": ["Mnemonic data-led concept", "Surprising data insight made tangible", "Translatability across brands / markets"]},
        {"key": "strategy", "name": "Data Strategy", "weight": 0.30,
         "description": "The biggest weight alongside Impact. Insight quality, data sources, audience targeting, ethical data use.",
         "signals": ["Originality and veracity of the underlying data insight", "Proprietary vs publicly-available data", "Audience-targeting precision", "Ethical data sourcing", "Brand mission ↔ data approach coherence"]},
        {"key": "execution", "name": "Execution", "weight": 0.15,
         "description": "HOW data was activated. Lighter weight: the system matters less than the insight and the outcome.",
         "signals": ["Data-product craft (UI, dashboard, visualisation)", "Personalisation at scale", "Real-time / dynamic-data orchestration"]},
        {"key": "impact", "name": "Impact", "weight": 0.35,
         "description": "Dominant axis. Documented behaviour change, business outcome, cultural conversation tied to the data move.",
         "signals": ["Behaviour shift with documented before/after", "Business results tied to the data action", "Reach + engagement with the data insight", "Audience-segment performance metrics"]},
    ],
    "sub_categories_hint": {
        "A": "Use of Data",
        "B": "Data Storytelling & Visualisation",
        "C": "Personalisation",
        "D": "Use of Real-Time Data",
        "E": "Culture & Context",
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
