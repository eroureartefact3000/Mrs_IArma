"""Print & Publishing Lions judging criteria.

Pondération aligned with the Outdoor template (idea-led category with strong
single-frame requirement) per the Cannes Lions 2026 entry kit:
    35% Idea  /  10% Strategy  /  30% Execution  /  25% Impact

Tier-to-score mapping (canonical Cannes band, same as Outdoor / PR):
    Grand Prix : 90-100
    Gold       : 80-100
    Silver     : 65-80
    Bronze     : 50-65
"""
from typing import Literal


PRINT_CRITERIA: dict = {
    "category": "Print & Publishing",
    "definition": (
        "The Print & Publishing Lions celebrate creative work in print media — "
        "newspapers, magazines, publications, branded content, and in-store print. "
        "The work should demonstrate ideas that work without much explanatory copy, "
        "landing in a single page or spread. Per the entry kit, main criteria are: "
        "idea, execution, impact — with strategy as supporting context."
    ),
    "axes": [
        {
            "key": "idea",
            "name": "Idea",
            "weight": 0.35,
            "description": (
                "Originality and memorability of the creative idea. In Print, the idea "
                "must work in a single frame — it has to land from a headline plus a hero "
                "image, without long body copy."
            ),
            "signals": [
                "Uniqueness vs. category conventions",
                "Memorability — does it stick after a single exposure?",
                "Native to print (works in a single frame, not a film-shrunk-to-poster)",
                "Headline-and-image tension — copy and visual amplify each other",
                "Mnemonic power of the visual or copy device",
                "Cultural relevance / topicality",
            ],
        },
        {
            "key": "strategy",
            "name": "Strategy",
            "weight": 0.10,
            "description": (
                "WHY this idea, for this brand, in this context. Strategy answers two "
                "sub-questions, in order: (1) Who is the brand and is the idea coherent "
                "with its mission? (2) Are the context and insights real, verifiable, "
                "data-backed? Do NOT discuss orchestration or media choices here — those "
                "belong to Execution."
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
                "HOW the idea was delivered. Execution answers: are the means and media "
                "chosen relevant to the objective and the target? Covers craft quality "
                "(typography, photography, illustration, layout), publication placement, "
                "and multi-execution coherence."
            ),
            "signals": [
                "Craft quality (visual, typography, photography, illustration, print production)",
                "Publication / placement fit — right title for right message",
                "Multi-execution coherence (campaign of 3+ executions hangs together)",
                "Use of the printed page format (size, fold, paper stock when relevant)",
                "Target-channel fit (audience reached where they read)",
            ],
        },
        {
            "key": "impact",
            "name": "Impact & Results",
            "weight": 0.25,
            "description": (
                "Measurable impact on business, society, or culture. Combines reach, "
                "tangible business results, behaviour change, and cultural footprint. "
                "Print is less measurable than digital, so qualitative-but-credible "
                "impact (cultural conversation, award pickup, jury-quotable moments) "
                "carries weight too."
            ),
            "signals": [
                "Reach / circulation / share of voice",
                "Brand metric shifts (awareness, consideration, sentiment)",
                "Tangible business results (sales, visits, sign-ups)",
                "Cultural conversation lasting beyond the campaign window",
                "Behaviour or attitude change",
                "Disproportionate impact relative to budget",
            ],
        },
    ],
    "sub_categories_hint": {
        "A": "Press & Publications: Sectors (Consumer Goods, Healthcare, Automotive, Travel, Media, B2B, NFP/Gov)",
        "B": "Direct Print (Direct mail, branded content in print, in-store / point-of-sale print)",
        "C": "Innovation in Print (Standard sites, Ambient Print, Technology in Print)",
        "D": "Print Craft (Typography, Illustration, Photography, Art Direction, Copywriting)",
        "E": "Culture & Context (Local Brand, Challenger, Single-Market, Social Behaviour, Humour, Budget, Purpose, Disruption, Cultural Engagement)",
    },
}


Tier = Literal["Grand Prix", "Gold", "Silver", "Bronze", "Shortlist", "Loser"]


_PRINT_BANDS = {
    "Grand Prix": (90, 100),
    "Gold": (80, 100),
    "Silver": (65, 80),
    "Bronze": (50, 65),
}


def expected_score_range(tier: Tier) -> tuple[int, int] | None:
    """Per-tier expected score range. None for Shortlist/Loser (not prize tiers)."""
    return _PRINT_BANDS.get(tier)


def tier_consistency(tier: Tier, weighted_score: float) -> Literal["expected", "below", "above", "n/a"]:
    """Flag whether a weighted score falls in the band expected for its tier."""
    band = _PRINT_BANDS.get(tier)
    if band is None:
        return "n/a"
    low, high = band
    if weighted_score < low:
        return "below"
    if weighted_score > high:
        return "above"
    return "expected"
