"""Entertainment Lions for Music judging criteria.

Music as brand-entertainment platform: branded musical content, artist
partnerships, music-led activations.
    30% Idea  /  10% Strategy  /  30% Execution  /  30% Impact
"""
from typing import Literal


ENT_MUSIC_CRITERIA: dict = {
    "category": "Entertainment for Music",
    "definition": (
        "The Entertainment Lions for Music celebrate brand work in and around "
        "music: artist partnerships, music videos, branded musical content, "
        "music-festival activations, songs and audio campaigns built around "
        "music culture. The work must respect music culture and earn audience "
        "attention rather than buy it."
    ),
    "axes": [
        {"key": "idea", "name": "Entertainment Idea", "weight": 0.30,
         "description": "Originality of the music concept. Music-native, respects artist and audience culture.",
         "signals": ["Music-native idea (not advertising with a sponsorship logo)", "Artist authenticity (genuine fit, not transactional)", "Cultural moment exploitation", "Genre / scene specificity"]},
        {"key": "strategy", "name": "Strategy", "weight": 0.10,
         "description": "Light sanity check. Brand authority in music + audience fit.",
         "signals": ["WHO IS THE BRAND? Music-marketing track record", "Artist / IP rights logic", "Audience-genre fit"]},
        {"key": "execution", "name": "Execution", "weight": 0.30,
         "description": "HOW the music work was crafted: production, performance, distribution.",
         "signals": ["Music production quality", "Performance / artist direction", "Music-video craft when applicable", "Multi-platform distribution"]},
        {"key": "impact", "name": "Impact", "weight": 0.30,
         "description": "Audience engagement + cultural conversation + chart/streaming impact + brand outcomes.",
         "signals": ["Streaming numbers / chart position", "Audience engagement (sing-along, dance trends, UGC)", "Cultural conversation in music press", "Brand metric shifts among music audience", "Disproportionate impact vs spend"]},
    ],
    "sub_categories_hint": {
        "A": "Branded Musical Content (music videos, songs)",
        "B": "Live Music Activations & Sponsorships",
        "C": "Artist & Talent Partnerships",
        "D": "Excellence in Brand Music (Single-Market, Use of Tech)",
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
