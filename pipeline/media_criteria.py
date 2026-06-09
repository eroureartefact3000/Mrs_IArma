"""Media Lions judging criteria.

Pondération heavily strategy + impact, per the Cannes Lions 2026 entry kit:
    20% Idea  /  35% Strategy  /  15% Execution  /  30% Impact

Tier-to-score mapping (canonical Cannes band):
    Grand Prix : 90-100
    Gold       : 80-100
    Silver     : 65-80
    Bronze     : 50-65
"""
from typing import Literal


MEDIA_CRITERIA: dict = {
    "category": "Media",
    "definition": (
        "The Media Lions celebrate creative use of media — innovative channel "
        "strategy, smart use of context, surprising placements, partnerships, "
        "media-as-product thinking. The work should demonstrate how a media "
        "choice itself becomes the creative idea. Per the entry kit, Strategy "
        "and Impact dominate; Idea is the channel insight; Execution is lighter "
        "than in Craft categories."
    ),
    "axes": [
        {
            "key": "idea",
            "name": "Media Idea",
            "weight": 0.20,
            "description": (
                "Originality of the media insight or channel-strategy concept. "
                "The 'aha' moment where the medium itself becomes the idea."
            ),
            "signals": [
                "Channel-as-creative-idea (the placement IS the message)",
                "Unique use of media context, format, or partnership",
                "Cultural-moment exploitation",
                "Mnemonic media device",
            ],
        },
        {
            "key": "strategy",
            "name": "Media Strategy",
            "weight": 0.35,
            "description": (
                "**The biggest weight.** Media Lions are fundamentally a strategy "
                "discipline. Audience identification, channel ecosystem choice, "
                "data-led targeting, partnership logic, media-mix architecture. "
                "Do NOT discuss execution craft here."
            ),
            "signals": [
                "Audience-data clarity — narrow, defensible targets",
                "Channel-ecosystem fit (right mix of paid/owned/earned)",
                "Partnership originality and rights leverage",
                "Data-led targeting with documented behavioural insight",
                "Media-architecture coherence (phases, sequencing, amplification)",
                "Brand mission ↔ media-strategy fit",
            ],
        },
        {
            "key": "execution",
            "name": "Execution",
            "weight": 0.15,
            "description": (
                "HOW the media plan was put into market. Placement craft, "
                "creative-message fit, real-time response, optimisation discipline. "
                "Light weight because Media Lions are strategy-first."
            ),
            "signals": [
                "Placement craft (right placement, right moment, right audience)",
                "Creative-message ↔ media-context fit",
                "Real-time / optimisation discipline",
                "Multi-channel coherence in execution",
            ],
        },
        {
            "key": "impact",
            "name": "Business & Cultural Impact",
            "weight": 0.30,
            "description": (
                "Measurable business and cultural impact. Reach + behaviour change "
                "+ business outcomes + cultural footprint. Media Lions reward "
                "disproportionate impact relative to spend (efficiency)."
            ),
            "signals": [
                "Business results (sales lift, share gain, conversion)",
                "Audience-behaviour shifts with documented before-and-after",
                "Cultural conversation beyond the campaign window",
                "Disproportionate impact-per-dollar (media efficiency)",
                "Brand metric shifts (awareness, consideration, sentiment)",
            ],
        },
    ],
    "sub_categories_hint": {
        "A": "Sectors (Consumer Goods, Healthcare, Automotive, Travel, Media, B2B, NFP/Gov)",
        "B": "Use of Channels (Audio, Mobile, OOH, Print, Screens, Digital, Branded Content)",
        "C": "Excellence in Media (Single-Market, Use of Data, Use of Real-Time Data, Partnerships)",
        "D": "Use of Technology / Innovation in Media",
        "E": "Culture & Context (Local, Challenger, Behaviour, Humour, Budget, Purpose, Disruption)",
    },
}


Tier = Literal["Grand Prix", "Gold", "Silver", "Bronze", "Shortlist", "Loser"]


_BANDS = {
    "Grand Prix": (90, 100), "Gold": (80, 100),
    "Silver": (65, 80), "Bronze": (50, 65),
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
