"""Outdoor Lions judging criteria — cross-referenced with the project brief
and corrected by DA feedback (2026-05-19).

Entry kit (Cannes Lions 2026, p.16): "The main criteria considered during
judging will be the idea, the execution and the impact."

Adapted to our 4-axis framework (consistent with the brief), with Strategy
kept at low weight since Outdoor judges don't isolate it.

Mental model strictly enforced (per DA):
    Strategy = WHY  (brand mission alignment + insight veracity)
    Execution = HOW (orchestration + media-target fit)
"""
from typing import Literal


OUTDOOR_CRITERIA: dict = {
    "category": "Outdoor",
    "definition": (
        "The Outdoor Lions celebrate creativity experienced out of home. The work "
        "should demonstrate ideas that engage in the field. It should leverage public "
        "spaces to communicate a message or immerse consumers in a brand experience. "
        "Per the entry kit, main criteria are: idea, execution, impact."
    ),
    "axes": [
        {
            "key": "idea",
            "name": "Idea",
            "weight": 0.35,
            "description": (
                "Originality and memorability of the creative idea. In Outdoor, the "
                "idea must work without much explanatory text — it has to land in a "
                "glance from a public space."
            ),
            "signals": [
                "Uniqueness vs. category conventions",
                "Memorability — does it stick after a single exposure?",
                "Native to outdoor (not a film-shrunk-to-poster)",
                "Cultural relevance / topicality",
                "Mnemonic power of the visual or copy device",
            ],
        },
        {
            "key": "strategy",
            "name": "Strategy",
            "weight": 0.10,
            "description": (
                "WHY this idea, for this brand, in this context. Strategy answers two "
                "sub-questions, in order: (1) Who is the brand and is the idea "
                "coherent with its mission? (2) Are the context and insights real, "
                "verifiable, data-backed? Do NOT discuss orchestration or media "
                "choices here — those belong to Execution."
            ),
            "signals": [
                "WHO IS THE BRAND? Identify the brand's mission (especially for non-international brands)",
                "Idea ↔ brand mission coherence",
                "Insight is sourced from real data (studies, stats, cultural truth)",
                "Context (problem the campaign addresses) is real and verifiable",
            ],
        },
        {
            "key": "execution",
            "name": "Execution",
            "weight": 0.30,
            "description": (
                "HOW the idea was delivered. Execution answers: are the means and "
                "media chosen relevant to the objective and the target? Covers "
                "craft quality, placement, orchestration of phases, amplification "
                "layers, and target-channel fit. Do NOT discuss brand mission or "
                "insight veracity here — those belong to Strategy."
            ),
            "signals": [
                "Craft quality (visual, typography, photography, production)",
                "Placement / context fit — right space for right message",
                "Orchestration of phases (launch, amplification, sustain)",
                "Amplification layers (partnerships, social pickup, PR loop)",
                "Target-channel fit (audience reached where they are)",
                "Multi-execution coherence when applicable",
            ],
        },
        {
            "key": "impact",
            "name": "Impact & Results",
            "weight": 0.25,
            "description": (
                "Measurable impact on business, society, or culture. Combines reach, "
                "tangible business results, behaviour change, and cultural footprint."
            ),
            "signals": [
                "Reach / impressions / share of voice",
                "Brand metric shifts (awareness, consideration, sentiment)",
                "Tangible business results (sales, visits, sign-ups)",
                "Cultural conversation lasting beyond the campaign window",
                "Behaviour or attitude change",
                "Disproportionate impact relative to budget",
            ],
        },
    ],
    "sub_categories_hint": {
        "A": "Billboards: Sectors (Consumer Goods, Healthcare, Automotive, Travel, Media, B2B, NFP/Gov)",
        "B": "Posters: Sectors (same sector breakdown as Billboards)",
        "C": "Ambient & Experiential (Displays, Interactive/Dynamic Digital Screens, Special Build, Live Advertising & Events, Interactive/Immersive Experiences, Transit)",
        "D": "Innovation in Outdoor (Standard Sites, Ambient Outdoor, Technology)",
        "E": "Culture & Context (Local Brand, Challenger Brand, Single-Market, Social Behaviour, Humour, Budget, Purpose & Social Responsibility, Market Disruption, Cultural Engagement)",
    },
}


Tier = Literal[
    "Grand Prix", "Gold", "Silver", "Bronze", "Shortlist", "Loser"
]


# Brief: 80-100 Gold / 65-80 Silver / 50-65 Bronze / <50 nothing
# Grand Prix: top of Gold band (95-100 typically)
_TIER_BANDS = {
    "Grand Prix": (90, 100),
    "Gold": (80, 100),
    "Silver": (65, 80),
    "Bronze": (50, 65),
}


def expected_score_range(tier: Tier) -> tuple[int, int] | None:
    """Per-tier expected score range. None for Shortlist/Loser (not prize tiers)."""
    return _TIER_BANDS.get(tier)


def tier_consistency(tier: Tier, weighted_score: float) -> Literal["expected", "below", "above", "n/a"]:
    """For winners: check whether the score falls in the tier band.

    Shortlist and Loser do not have an official prize band, so we return 'n/a'.
    """
    band = _TIER_BANDS.get(tier)
    if band is None:
        return "n/a"
    low, high = band
    if weighted_score < low:
        return "below"
    if weighted_score > high:
        return "above"
    return "expected"
