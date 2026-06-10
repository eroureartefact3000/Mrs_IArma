"""Entertainment Lions for Gaming judging criteria.

Gaming as a brand-entertainment platform: in-game integrations, branded games,
gaming-culture campaigns, streamer partnerships.
    30% Idea  /  10% Strategy  /  30% Execution  /  30% Impact
"""
from typing import Literal


ENT_GAMING_CRITERIA: dict = {
    "category": "Entertainment for Gaming",
    "definition": (
        "The Entertainment Lions for Gaming celebrate brand work in and around "
        "gaming: in-game integrations, branded games, gaming-culture activations, "
        "streamer partnerships. The work must respect gaming culture and earn "
        "the audience's attention, not interrupt the play experience."
    ),
    "axes": [
        {"key": "idea", "name": "Entertainment Idea", "weight": 0.30,
         "description": "Originality of the gaming concept. Gaming-native, respects player culture.",
         "signals": ["Native to gaming culture (not a brand pasting a logo into Fortnite)", "Gameplay-as-the-idea or platform-feature exploit", "Streamer / pro-player partnership rationale", "Cultural moment exploitation"]},
        {"key": "strategy", "name": "Strategy", "weight": 0.10,
         "description": "Light sanity check. Brand authority in gaming + audience fit.",
         "signals": ["WHO IS THE BRAND? Gaming authority / track record", "Audience-platform fit (casual vs hardcore gamers)", "Partnership / IP rights logic"]},
        {"key": "execution", "name": "Execution", "weight": 0.30,
         "description": "HOW the gaming work was crafted: build quality, integration depth, player experience.",
         "signals": ["Build quality (custom mod, branded skin, full game)", "Integration depth (deep mechanic vs cosmetic logo)", "Player experience polish", "Streamer / talent direction"]},
        {"key": "impact", "name": "Impact", "weight": 0.30,
         "description": "Player engagement + cultural conversation + brand metric shifts.",
         "signals": ["Player participation (downloads, time-played, server visits)", "Streamer-driven viewership", "Cultural conversation in gaming press / Discord", "Brand metric shifts among gamers", "Disproportionate impact vs spend"]},
    ],
    "sub_categories_hint": {
        "A": "Brand Storytelling using Gaming",
        "B": "In-Game Brand Integration",
        "C": "Branded Games (full custom games)",
        "D": "Streamer / Creator Partnerships",
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
