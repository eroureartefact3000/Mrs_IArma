"""Entertainment Lions for Sport judging criteria.

Pondération aligned with brand-entertainment work: idea + execution dominate,
strategy lighter, impact tracks cultural conversation:
    30% Idea  /  10% Strategy  /  30% Execution  /  30% Impact
"""
from typing import Literal


ENT_SPORT_CRITERIA: dict = {
    "category": "Entertainment Lions for Sport",
    "definition": (
        "The Entertainment Lions for Sport celebrate creative work where sport "
        "is the brand-entertainment vehicle — sponsorship-led storytelling, "
        "athlete partnerships, branded content tied to sport, sport-as-platform "
        "for cultural moments. The work must be genuinely entertaining, not "
        "just sport-themed advertising."
    ),
    "axes": [
        {"key": "idea", "name": "Entertainment Idea", "weight": 0.30,
         "description": "Originality of the entertainment concept built around sport.",
         "signals": [
             "Sport-as-platform — not sport-as-backdrop",
             "Storytelling that earns audience attention (not interrupts it)",
             "Cultural-moment exploitation (specific match, athlete, season)",
             "Mnemonic device or recurring entertainment franchise",
             "Translatability across sport audiences",
         ]},
        {"key": "strategy", "name": "Strategy", "weight": 0.10,
         "description": "WHY this sport tie-in for this brand. Sanity check on authority and audience fit.",
         "signals": [
             "WHO IS THE BRAND? Sport-marketing authority",
             "Brand mission ↔ sport tie-in coherence",
             "Audience-fit (sport fans served, not exploited)",
             "Partnership rights logic (athlete / league / event)",
         ]},
        {"key": "execution", "name": "Execution", "weight": 0.30,
         "description": "HOW the entertainment was crafted and delivered.",
         "signals": [
             "Production craft (film, live, social, content)",
             "Athlete/talent direction quality",
             "Cultural-moment timing (right beat in the sport calendar)",
             "Multi-platform orchestration",
             "Earned-media loop from the content",
         ]},
        {"key": "impact", "name": "Impact & Results", "weight": 0.30,
         "description": "Audience engagement + cultural conversation + brand outcomes.",
         "signals": [
             "Audience engagement (views, watch-time, social conversation)",
             "Cultural conversation (sport press pickup, athlete-fan dialogue)",
             "Brand metric shifts (consideration, affinity)",
             "Business results when documented",
             "Behaviour or attitude change",
             "Disproportionate impact vs. media spend",
         ]},
    ],
    "sub_categories_hint": {
        "A": "Brand Storytelling using Sport (films, content series, sponsorship-led stories)",
        "B": "Audience Engagement & Distribution Strategy",
        "C": "Talent: Athletes, Coaches, Teams as platforms",
        "D": "Excellence in Sports Entertainment (Single-Market, Use of Tech, Budget)",
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
