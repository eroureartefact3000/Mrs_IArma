"""Entertainment Lions judging criteria.

Pondération aligned with brand-entertainment work, similar to Sport:
    30% Idea  /  10% Strategy  /  30% Execution  /  30% Impact
"""
from typing import Literal


ENTERTAINMENT_CRITERIA: dict = {
    "category": "Entertainment",
    "definition": (
        "The Entertainment Lions celebrate creative work that delivers brand "
        "messages through genuinely entertaining content — branded films, content "
        "series, podcasts, branded utility entertainment, gaming, live shows. The "
        "work must earn audience attention, not interrupt it. Distinct from "
        "Entertainment Lions for Music / Sport / Gaming which have dedicated lions."
    ),
    "axes": [
        {"key": "idea", "name": "Entertainment Idea", "weight": 0.30,
         "description": "Originality of the entertainment concept.",
         "signals": [
             "Stand-alone entertainment value (strip the brand — would people still watch?)",
             "Storytelling that earns attention",
             "Cultural relevance / topicality",
             "Mnemonic device or recurring franchise",
             "Translatability across audiences",
         ]},
        {"key": "strategy", "name": "Strategy", "weight": 0.10,
         "description": "WHY this content for this brand. Sanity check on authority and audience.",
         "signals": [
             "WHO IS THE BRAND? Entertainment authority",
             "Brand mission ↔ content theme coherence",
             "Audience fit",
             "Partnership / distribution logic",
         ]},
        {"key": "execution", "name": "Execution", "weight": 0.30,
         "description": "HOW the content was crafted and delivered.",
         "signals": [
             "Production craft (film, audio, live, interactive)",
             "Direction / talent quality",
             "Distribution strategy (right platforms for the audience)",
             "Multi-platform orchestration",
             "Audience-engagement loop",
         ]},
        {"key": "impact", "name": "Impact & Results", "weight": 0.30,
         "description": "Audience engagement + cultural conversation + brand outcomes.",
         "signals": [
             "Audience engagement (views, watch-time, social conversation, opt-in)",
             "Cultural conversation (press pickup, fan community building)",
             "Brand metric shifts (consideration, affinity, trust)",
             "Business results when documented",
             "Behaviour or attitude change",
             "Disproportionate impact vs. media spend",
         ]},
    ],
    "sub_categories_hint": {
        "A": "Branded Films, Series, and Audio (drama, doc, podcasts)",
        "B": "Audience Engagement & Distribution Strategy",
        "C": "Talent: Cultural Stars, Comedians, Creators",
        "D": "Excellence in Brand Entertainment (Single-Market, Tech, Budget)",
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
