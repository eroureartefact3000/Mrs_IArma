"""Health & Wellness Lions judging criteria.

Pondération aligned with general-audience health communication (over-the-counter,
wellness, consumer-facing), per the Cannes Lions 2026 entry kit:
    25% Idea  /  20% Strategy  /  25% Execution  /  30% Impact
"""
from typing import Literal


HEALTH_CRITERIA: dict = {
    "category": "Health & Wellness",
    "definition": (
        "The Health & Wellness Lions celebrate creative work in consumer-facing "
        "health and wellness — over-the-counter products, healthcare services, "
        "wellbeing brands, behavioural-change campaigns aimed at general audiences. "
        "Distinguished from Pharma (which is regulated prescription work). The "
        "work should educate, motivate, or shift health behaviour with genuine "
        "human care."
    ),
    "axes": [
        {"key": "idea", "name": "Idea", "weight": 0.25,
         "description": "Originality of the creative idea in service of health.",
         "signals": [
             "Uniqueness vs. health-category conventions (avoid generic 'happy patient' tropes)",
             "Empathy-led — does the work feel human, not clinical?",
             "Mnemonic device that drives recall of the health message",
             "Cultural relevance to the target audience",
             "Translatability across markets",
         ]},
        {"key": "strategy", "name": "Strategy", "weight": 0.20,
         "description": "WHY this brand, this audience, this insight. Health work demands strong audience insight.",
         "signals": [
             "WHO IS THE BRAND? Health mission and credentials",
             "Audience definition — specific health context (condition, life stage, behaviour)",
             "Insight rooted in real behavioural / clinical truth (not stereotype)",
             "Brand mission ↔ idea coherence",
             "Cultural-sensitivity calibration when relevant",
         ]},
        {"key": "execution", "name": "Execution", "weight": 0.25,
         "description": "HOW the work was crafted and delivered. Health work requires careful tonality.",
         "signals": [
             "Craft quality (visual, copy, production)",
             "Tonality — neither saccharine nor scaremongering",
             "Channel choice — right place to reach health audience",
             "Multi-execution coherence",
             "Amplification layers (community partnerships, healthcare-pro endorsement, earned media)",
         ]},
        {"key": "impact", "name": "Impact & Results", "weight": 0.30,
         "description": "Health outcomes, behaviour change, business results. Health Lions reward documented behaviour shifts.",
         "signals": [
             "Health-behaviour change (testing rates, vaccination, screening, lifestyle)",
             "Reach into target health audience",
             "Brand metric shifts (consideration, trust, recall)",
             "Business results (sales, prescriptions, sign-ups)",
             "Policy / system-level impact (healthcare provider adoption, payer changes)",
             "Cultural conversation lasting beyond the campaign window",
         ]},
    ],
    "sub_categories_hint": {
        "A": "Consumer Products (OTC, supplements, personal care)",
        "B": "Health Services & Corporate Communications",
        "C": "Wellness & Treatment (mental, physical, lifestyle wellness)",
        "D": "Health Awareness & Advocacy",
        "E": "Use of Tech / Innovation in Health Communications",
        "F": "Culture & Context (Local, Challenger, Behaviour, Humour, Budget, Purpose, Disruption)",
    },
}

Tier = Literal["Grand Prix", "Gold", "Silver", "Bronze", "Shortlist", "Loser"]
_BANDS = {"Grand Prix": (90, 100), "Gold": (80, 100), "Silver": (65, 80), "Bronze": (50, 65)}


def expected_score_range(tier: Tier) -> tuple[int, int] | None:
    return _BANDS.get(tier)


def tier_consistency(tier: Tier, weighted_score: float) -> Literal["expected", "below", "above", "n/a"]:
    band = _BANDS.get(tier)
    if band is None:
        return "n/a"
    low, high = band
    if weighted_score < low:
        return "below"
    if weighted_score > high:
        return "above"
    return "expected"
