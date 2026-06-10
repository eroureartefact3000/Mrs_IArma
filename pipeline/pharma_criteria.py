"""Pharma Lions judging criteria.

Regulated pharmaceutical creative work. Distinct from Health & Wellness:
deals with prescription products, healthcare professionals, regulated claims.
    20% Idea  /  25% Strategy  /  25% Execution  /  30% Impact
"""
from typing import Literal


PHARMA_CRITERIA: dict = {
    "category": "Pharma",
    "definition": (
        "The Pharma Lions celebrate creative work in regulated pharmaceutical "
        "communications: prescription drug awareness, disease education, "
        "healthcare-professional engagement, patient services. Constrained by "
        "regulations and the seriousness of the medical context. Strategy + "
        "Impact + Execution all carry weight; idea is in service of medical "
        "accuracy."
    ),
    "axes": [
        {"key": "idea", "name": "Idea", "weight": 0.20,
         "description": "Originality within the regulatory constraints. Empathy-led, never trivialising.",
         "signals": ["Uniqueness in a heavily regulated category", "Patient empathy at the centre", "Mnemonic that survives medical accuracy review", "Translatability across markets"]},
        {"key": "strategy", "name": "Strategy", "weight": 0.25,
         "description": "WHO is the audience (HCP / patient / payer), WHY this insight, HOW does it respect medical accuracy.",
         "signals": ["Audience precision (HCP vs patient vs payer)", "Insight rooted in real clinical or patient truth", "Brand mission ↔ medical credentials", "Regulatory compliance baked into the strategy"]},
        {"key": "execution", "name": "Execution", "weight": 0.25,
         "description": "HOW the work was crafted and delivered within regulatory constraints.",
         "signals": ["Craft quality respecting medical accuracy", "Channel choice (medical media, conferences, patient services)", "Multi-execution coherence", "Educational content quality when applicable"]},
        {"key": "impact", "name": "Impact", "weight": 0.30,
         "description": "Documented health behaviour change, HCP adoption, patient empowerment, business outcome.",
         "signals": ["Health-behaviour shifts (screening, adherence, awareness)", "HCP adoption / prescription metrics when documented", "Patient empowerment outcomes", "Business results (when allowable)", "Industry / regulatory recognition"]},
    ],
    "sub_categories_hint": {
        "A": "Patient-Facing (OTC, awareness, patient services)",
        "B": "HCP / Professional-Facing",
        "C": "Disease Awareness & Advocacy",
        "D": "Innovation in Pharma Communications",
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
