"""Creative Commerce Lions judging criteria.

Commerce-driven: idea must produce a measurable sales / conversion outcome.
Impact weight is dominant.
    20% Idea  /  15% Strategy  /  25% Execution  /  40% Impact
"""
from typing import Literal


CREATIVE_COMMERCE_CRITERIA: dict = {
    "category": "Creative Commerce",
    "definition": (
        "The Creative Commerce Lions celebrate creative work that drives "
        "measurable commerce outcomes: sales, conversion, customer acquisition, "
        "marketplace and retail-led innovation. Impact dominates; ideas exist "
        "in service of commerce KPIs."
    ),
    "axes": [
        {"key": "idea", "name": "Idea", "weight": 0.20,
         "description": "Originality of the commerce mechanism. Idea is in service of conversion, not abstract.",
         "signals": ["Mechanism originality vs commerce conventions", "Mnemonic power", "Translatability"]},
        {"key": "strategy", "name": "Strategy", "weight": 0.15,
         "description": "WHO is being converted, WHY this commerce mechanic, HOW it ties to brand.",
         "signals": ["Audience identification (specific segment, not 'everyone')", "Brand mission ↔ mechanic coherence", "Channel/marketplace choice rationale", "Data-rooted insight"]},
        {"key": "execution", "name": "Execution", "weight": 0.25,
         "description": "HOW the commerce experience is crafted and orchestrated.",
         "signals": ["Conversion-flow craft (frictionless action → purchase)", "Channel-specific craft (retail / e-commerce / livestream / OOH-as-commerce)", "Multi-channel orchestration", "Customer-experience quality"]},
        {"key": "impact", "name": "Commerce Impact", "weight": 0.40,
         "description": "Dominant axis. Sales lift, conversion rate, customer acquisition, ROI, lifetime value.",
         "signals": ["Sales lift (absolute or % over baseline)", "Conversion rate", "New customer acquisition counts", "Average order value shifts", "Disproportionate impact relative to spend (ROI)", "Cultural / behavioural shift that drives sustained commerce"]},
    ],
    "sub_categories_hint": {
        "A": "Sectors (Commerce work by sector)",
        "B": "Use of Channels (E-commerce, Retail, Marketplace, Live Commerce)",
        "C": "Excellence in Commerce (Single-Market, Use of Tech, Budget)",
        "D": "Culture & Context",
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
