"""Industry Craft Lions judging criteria.

Pondération heavily craft-defined per the Cannes Lions 2026 entry kit:
    20% Idea  /  10% Strategy  /  55% Execution  /  15% Impact

Tier-to-score mapping (canonical Cannes band):
    Grand Prix : 90-100
    Gold       : 80-100
    Silver     : 65-80
    Bronze     : 50-65
"""
from typing import Literal


INDUSTRY_CRAFT_CRITERIA: dict = {
    "category": "Industry Craft",
    "definition": (
        "The Industry Craft Lions celebrate the craft disciplines that bring "
        "advertising ideas to life — illustration, typography, photography, "
        "art direction, copywriting, music, motion. The board IS the craft. "
        "Per the entry kit, Execution dominates by a wide margin; idea and "
        "strategy are subordinate to craft excellence."
    ),
    "axes": [
        {
            "key": "idea",
            "name": "Idea",
            "weight": 0.20,
            "description": (
                "Originality of the craft-led concept. The unifying creative thought "
                "that the craft expression brings to life."
            ),
            "signals": [
                "Uniqueness of the craft concept vs. category conventions",
                "Conceptual clarity — one strong creative thought driving the craft",
                "Cultural resonance / topicality",
                "Mnemonic power of the craft expression",
            ],
        },
        {
            "key": "strategy",
            "name": "Strategy",
            "weight": 0.10,
            "description": (
                "WHY this craft approach for this brand. Sanity-check axis: is the "
                "craft choice coherent with the brand's mission and the brief? Do "
                "NOT discuss craft itself here — that belongs to Execution."
            ),
            "signals": [
                "WHO IS THE BRAND? Brand mission and aesthetic territory",
                "Craft choice ↔ brand mission coherence",
                "Brief-to-craft fit (does this craft solve the stated problem?)",
            ],
        },
        {
            "key": "execution",
            "name": "Craft Execution",
            "weight": 0.55,
            "description": (
                "The dominant axis by a wide margin. Pure craft quality: illustration, "
                "typography, photography, art direction, copywriting, music, motion. "
                "Production finesse, technique mastery, attention to micro-detail. "
                "This is the entire point of the category."
            ),
            "signals": [
                "Technique mastery — illustration line quality, type construction, photographic light",
                "Production finesse and attention to micro-detail",
                "Materiality and tactile craft when relevant",
                "Composition and layout discipline",
                "Tonal control (colour, music, voice, motion)",
                "Multi-execution consistency without monotony",
                "Pushing the medium beyond the obvious",
            ],
        },
        {
            "key": "impact",
            "name": "Impact",
            "weight": 0.15,
            "description": (
                "Weighted lightly because Industry Craft is judged primarily on the "
                "craft itself. Industry recognition, craft-press pickup, peer-to-peer "
                "discourse, jury-quotable moments. Business outcomes carry less weight "
                "than they would in Direct or Media."
            ),
            "signals": [
                "Industry-press / craft-press pickup",
                "Cultural conversation about the craft technique",
                "Peer recognition (other craftspeople citing the work)",
                "Brand metric shifts when documented",
                "Adoption or imitation of the technique",
            ],
        },
    ],
    "sub_categories_hint": {
        "A": "Print & Publishing Craft (typography, illustration, photography, art direction in print)",
        "B": "Film Craft (already a separate category — Industry Craft picks up other moving-image craft)",
        "C": "Visual Craft (illustration, photography, CGI, art direction across media)",
        "D": "Writing (copywriting, dialogue, narrative craft)",
        "E": "Branded Content Craft (long-form, editorial, content-led craft)",
    },
}


Tier = Literal["Grand Prix", "Gold", "Silver", "Bronze", "Shortlist", "Loser"]


_BANDS = {
    "Grand Prix": (90, 100),
    "Gold": (80, 100),
    "Silver": (65, 80),
    "Bronze": (50, 65),
}


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
