"""Creative Business Transformation Lions judging criteria.

Creative work that transforms how a business operates (new product, new
service, new business model, new internal culture).
    20% Idea  /  20% Strategy  /  25% Execution  /  35% Impact
"""
from typing import Literal


CREATIVE_BT_CRITERIA: dict = {
    "category": "Creative Business Transformation",
    "definition": (
        "The Creative Business Transformation Lions celebrate creative work "
        "that fundamentally changes how a business operates: new product or "
        "service, new business model, internal culture transformation, "
        "operational shift. Impact must show business / operational change, "
        "not just communication outcomes."
    ),
    "axes": [
        {"key": "idea", "name": "Idea", "weight": 0.20,
         "description": "Originality of the transformation thinking. Business model reframe.",
         "signals": ["Business-model originality", "Cross-functional ambition", "Translatability across industries"]},
        {"key": "strategy", "name": "Strategy", "weight": 0.20,
         "description": "WHY this transformation. Business diagnosis, opportunity identification, change-management approach.",
         "signals": ["Diagnosis of the business problem", "Opportunity sizing", "Change-management plan", "Stakeholder buy-in approach"]},
        {"key": "execution", "name": "Execution", "weight": 0.25,
         "description": "HOW the transformation was delivered: design, build, deploy, train, scale.",
         "signals": ["Product / service design quality", "Roll-out orchestration", "Internal adoption / training", "Multi-market scale-up when applicable"]},
        {"key": "impact", "name": "Business Impact", "weight": 0.35,
         "description": "Documented business / operational / cultural change.",
         "signals": ["Revenue / margin shift", "Operational efficiency gains", "New customer segments unlocked", "Internal culture / capability shifts", "Multi-year sustained change"]},
    ],
    "sub_categories_hint": {
        "A": "Brand Transformation",
        "B": "Business Model Transformation",
        "C": "Customer Experience Transformation",
        "D": "Internal / Cultural Transformation",
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
