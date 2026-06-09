"""Social & Influencer Lions judging criteria.

Pondération balanced between idea/strategy/execution/impact reflecting that
social work is creative + audience-defined + craft + engagement:
    25% Idea  /  20% Strategy  /  20% Execution  /  35% Impact
"""
from typing import Literal


SOCIAL_CRITERIA: dict = {
    "category": "Social & Influencer",
    "definition": (
        "The Social & Influencer Lions celebrate creative work that uses social "
        "platforms and influencer partnerships to drive brand impact — community "
        "management, real-time response, influencer-led campaigns, social content "
        "series, creator partnerships. The work must be native to the platform "
        "and the format, not repurposed advertising."
    ),
    "axes": [
        {"key": "idea", "name": "Social Idea", "weight": 0.25,
         "description": "Originality of the social-native concept.",
         "signals": [
             "Platform-native creative (would only work on this platform)",
             "Format insight (Reels, TikTok, X-threads, Reddit, etc.)",
             "Cultural-moment exploitation",
             "Mnemonic device that travels in social conversation",
             "Translatability across creator voices",
         ]},
        {"key": "strategy", "name": "Strategy", "weight": 0.20,
         "description": "WHO is being reached and WHY this platform / creator. Audience-strategy axis.",
         "signals": [
             "WHO IS THE BRAND? Social authority",
             "Specific platform/audience targeting (not 'everyone')",
             "Creator selection logic (right voice for the brand)",
             "Brand-mission ↔ social-idea coherence",
             "Real cultural insight (not assumption)",
         ]},
        {"key": "execution", "name": "Execution", "weight": 0.20,
         "description": "HOW the social work was crafted and delivered.",
         "signals": [
             "Platform craft (right tone, right format, right beats per platform)",
             "Creator-content quality (when creators are involved)",
             "Real-time / responsive moments",
             "Multi-post / multi-creator orchestration",
             "Community-management craft",
         ]},
        {"key": "impact", "name": "Impact & Results", "weight": 0.35,
         "description": "**Dominant axis.** Social Lions are engagement-judged. Reach + engagement + behaviour shift + cultural conversation.",
         "signals": [
             "Engagement metrics (likes, shares, comments — beware of inflated platform reach numbers)",
             "Audience-participation actions (challenges, UGC, opt-in behaviour)",
             "Cultural conversation lasting beyond the campaign",
             "Brand metric shifts (consideration, sentiment, social-share-of-voice)",
             "Business results when documented (sales, sign-ups, traffic from social)",
             "Disproportionate impact relative to media spend",
         ]},
    ],
    "sub_categories_hint": {
        "A": "Social Content Marketing (organic content, community management)",
        "B": "Influencer Marketing (creator-led campaigns)",
        "C": "Real-Time Response (cultural-moment response work)",
        "D": "Innovative Use of Community (UGC, fandom activation)",
        "E": "Excellence in Social (Use of Platforms, Single-Market, Budget)",
        "F": "Culture & Context",
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
