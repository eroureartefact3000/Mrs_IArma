"""Creative Effectiveness Lions judging criteria.

The most impact-dominant category. Awards prove that creative work produced
business / behaviour / cultural change. Requires documented before-and-after.
    10% Idea  /  25% Strategy  /  10% Execution  /  55% Impact
"""
from typing import Literal


CREATIVE_EFFECTIVENESS_CRITERIA: dict = {
    "category": "Creative Effectiveness",
    "definition": (
        "The Creative Effectiveness Lions celebrate creative work proven to "
        "have produced measurable business, behavioural, or cultural change. "
        "Entries must include longitudinal data, control comparisons, and "
        "attribution evidence. Impact is the dominant criterion by a large "
        "margin; idea and execution are downstream evidence."
    ),
    "axes": [
        {"key": "idea", "name": "Idea (downstream)", "weight": 0.10,
         "description": "The creative idea, judged for its role in producing the documented outcome. Secondary to results.",
         "signals": ["Idea ↔ business outcome coherence", "Translatability across business contexts"]},
        {"key": "strategy", "name": "Strategy", "weight": 0.25,
         "description": "The strategic frame and the data structure of the entry. Was the business problem reframed? Was attribution clean?",
         "signals": ["Business problem reframe quality", "Audience reframe quality", "Insight quality (data-rooted)", "Attribution methodology clarity", "Pre/post-measurement design"]},
        {"key": "execution", "name": "Execution", "weight": 0.10,
         "description": "Light weight. Effectiveness doesn't reward craft, it rewards results.",
         "signals": ["Channel mix appropriate to the goal", "Real-world test design", "Multi-phase orchestration"]},
        {"key": "impact", "name": "Effectiveness Evidence", "weight": 0.55,
         "description": "DOMINANT. Documented business / behavioural / cultural change with longitudinal data and attribution.",
         "signals": ["Sales / revenue growth with absolute figures", "Behaviour shifts with documented before-and-after", "Brand-equity / consideration shifts measured in surveys", "ROI / cost-per-outcome documented", "Cultural footprint lasting beyond the campaign window", "Attribution: how do you know it was the creative?"]},
    ],
    "sub_categories_hint": {
        "A": "Sectors (Effectiveness work by sector)",
        "B": "Effectiveness Time-Frame (Short / Medium / Long-Term)",
        "C": "Long-Term Brand Building",
        "D": "Behaviour-Change Effectiveness",
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
