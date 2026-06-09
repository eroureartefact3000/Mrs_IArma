"""Creative Strategy Lions judging criteria.

Strategy-first category: the work being judged IS the strategic thinking that
unlocked the creative work, not the creative itself. Boards are typically
strategy case studies. Signal from the static board will be weaker than
visual categories. Pondération:
    20% Idea  /  50% Strategy  /  10% Execution  /  20% Impact
"""
from typing import Literal


CREATIVE_STRATEGY_CRITERIA: dict = {
    "category": "Creative Strategy",
    "definition": (
        "The Creative Strategy Lions celebrate the strategic thinking that "
        "unlocked creative work — the insight, audience definition, brand "
        "positioning, business reframe, or cultural framing that gave the "
        "creative its power. The board is a strategy case study; the creative "
        "execution is downstream evidence."
    ),
    "axes": [
        {"key": "idea", "name": "Creative Idea (downstream)", "weight": 0.20,
         "description": "The creative idea the strategy unlocked. Secondary in this category — judged for how well it expresses the strategic insight.",
         "signals": [
             "Idea ↔ strategic insight coherence",
             "Mnemonic / memorable expression of the strategy",
             "Translatability of the idea across markets",
         ]},
        {"key": "strategy", "name": "Creative Strategy", "weight": 0.50,
         "description": "**Dominant axis by far.** The strategic thinking itself: insight quality, audience reframe, business problem reframe, cultural framing.",
         "signals": [
             "WHO IS THE BRAND? Mission and business context",
             "Insight quality — original, data-rooted, behavioural truth",
             "Audience reframe (new way of seeing the target)",
             "Business problem reframe (turning a limitation into an asset)",
             "Cultural framing (riding a cultural insight defensibly)",
             "Strategy ↔ creative-idea coherence (does the work prove the strategy?)",
         ]},
        {"key": "execution", "name": "Execution", "weight": 0.10,
         "description": "HOW the strategy was brought to market. Light weight — Creative Strategy doesn't reward craft, it rewards thinking.",
         "signals": [
             "Strategic plan articulated clearly on the board",
             "Channel/format choices align with the strategy",
             "Multi-phase orchestration when relevant",
             "Real-world test or pilot evidence",
         ]},
        {"key": "impact", "name": "Impact & Results", "weight": 0.20,
         "description": "Did the strategy work? Business outcomes + behaviour change + cultural traction.",
         "signals": [
             "Business results tied directly to the strategic move (sales, share, growth)",
             "Behaviour or attitude change with documented before/after",
             "Cultural conversation validating the strategic insight",
             "Brand metric shifts (perception, consideration)",
             "Disproportionate impact relative to budget",
         ]},
    ],
    "sub_categories_hint": {
        "A": "Sectors (CG, Healthcare, Auto, Travel, Media, B2B, NFP/Gov)",
        "B": "Use of Insight",
        "C": "Reframing the Brief (audience reframe, business problem reframe)",
        "D": "Use of Data & Research as Strategic Lever",
        "E": "Culture & Context",
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
