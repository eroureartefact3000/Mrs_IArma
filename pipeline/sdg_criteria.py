"""Sustainable Development Goals Lions judging criteria.

Pondération aligned with purpose-led work: idea + impact dominate, per the
Cannes Lions 2026 entry kit:
    25% Idea  /  15% Strategy  /  20% Execution  /  40% Impact
"""
from typing import Literal


SDG_CRITERIA: dict = {
    "category": "Sustainable Development Goals",
    "definition": (
        "The Sustainable Development Goals Lions celebrate creative work that "
        "advances one or more of the UN's 17 SDGs — no poverty, zero hunger, "
        "good health, quality education, gender equality, clean water, climate "
        "action, etc. The work must demonstrate genuine progress toward an SDG, "
        "not just borrow purpose. Per the entry kit, Impact carries the dominant "
        "weight: did the work actually move a development metric?"
    ),
    "axes": [
        {"key": "idea", "name": "Idea", "weight": 0.25,
         "description": "Originality of the creative approach to the SDG.",
         "signals": [
             "Uniqueness vs. category-purpose conventions (avoid generic 'awareness' tropes)",
             "Cultural-conversation entry point",
             "Mnemonic device that drives recall of the SDG message",
             "Translatability across markets",
         ]},
        {"key": "strategy", "name": "Strategy", "weight": 0.15,
         "description": "WHO the work serves, WHAT SDG it advances, WHY this brand has authority.",
         "signals": [
             "Specific SDG named and targeted (not generic 'good cause')",
             "WHO IS THE BRAND? Authority to speak on the SDG",
             "Audience definition tied to the SDG outcome",
             "Insight rooted in real development data",
             "Brand mission ↔ SDG coherence",
         ]},
        {"key": "execution", "name": "Execution", "weight": 0.20,
         "description": "HOW the work was crafted and orchestrated. Purpose work demands earned-media discipline.",
         "signals": [
             "Craft quality (visual, copy, production)",
             "Earned-media orchestration (this work usually needs PR loop)",
             "Partnership coherence with NGOs / governments / multilaterals",
             "Multi-execution coherence",
         ]},
        {"key": "impact", "name": "Impact & Results", "weight": 0.40,
         "description": "**Dominant axis.** SDG Lions reward documented development outcomes.",
         "signals": [
             "Documented progress on a specific SDG metric (people fed, vaccinated, schooled, etc.)",
             "Policy / legislative change",
             "System-level impact (NGO / government / multilateral adoption)",
             "Behaviour change with documented before/after",
             "Cultural conversation lasting beyond the campaign window",
             "Disproportionate impact relative to budget",
         ]},
    ],
    "sub_categories_hint": {
        "A": "People (No Poverty, Zero Hunger, Good Health, Quality Education, Gender Equality)",
        "B": "Planet (Clean Water, Affordable Clean Energy, Climate Action, Life Below Water, Life on Land)",
        "C": "Prosperity (Decent Work, Industry & Innovation, Reduced Inequalities, Sustainable Cities)",
        "D": "Peace & Partnership (Peace Justice & Strong Institutions, Partnerships for the Goals)",
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
