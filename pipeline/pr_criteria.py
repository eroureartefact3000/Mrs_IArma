"""PR Lions judging criteria — cross-referenced with the project brief.

Pondération is the official Cannes Lions 2026 weighting (entry kit p.77):
    20% Idea  /  30% PR Strategy  /  20% PR Execution  /  30% Impact & Results

The 4 axes map to the brief's generic axes (Creative idea / Strategy / Execution /
Results) but use PR-specific signals from the entry kit.

Tier-to-score mapping (from the brief):
    Grand Prix : 90-100 (top end of Gold range)
    Gold       : 80-100
    Silver     : 65-80
    Bronze     : 50-65
"""
from typing import Literal


PR_CRITERIA: dict = {
    "category": "PR",
    "definition": (
        "PR Lions celebrate the craft of strategic and creative communication. "
        "The work should demonstrate how original thinking, transformative insight "
        "and a strategy rooted in earned media have influenced opinion and driven "
        "progress and change in business, society or culture. The work should have "
        "storytelling at its core and establish, protect and enhance the reputation "
        "and business of an organisation or brand."
    ),
    "axes": [
        {
            "key": "idea",
            "name": "Idea",
            "weight": 0.20,
            "description": (
                "Originality and memorability of the creative idea — the strategic angle, "
                "story hook, or creative mechanism that makes the work distinctive."
            ),
            "signals": [
                "Uniqueness vs. category conventions",
                "Mnemonic potential — does the idea stick?",
                "Strategic angle of the idea (newsworthy, conversation-starting)",
                "Original use of a PR technique (event, stunt, media relations, partnership)",
                "Translatability — would this work across markets?",
            ],
        },
        {
            "key": "strategy",
            "name": "PR Strategy",
            "weight": 0.30,
            "description": (
                "How rooted in earned-media thinking the strategy is. Quality of insight, "
                "audience targeting, channel choices, and strategic alignment with the "
                "brand or organisation's mission."
            ),
            "signals": [
                "Earned-media-first thinking (not paid-first)",
                "Clear audience identification and motivation",
                "Insight quality and data-grounded reasoning",
                "Strategic alignment with brand mission or organisation purpose",
                "Crisis prevention / reputation management angle when relevant",
                "Use of cultural or behavioural insight",
            ],
        },
        {
            "key": "execution",
            "name": "PR Execution",
            "weight": 0.20,
            "description": (
                "Quality and creativity of the implementation. Use of PR techniques "
                "(media relations, events, stunts, partnerships, real-time response, "
                "influencer marketing, internal communications, sponsorship)."
            ),
            "signals": [
                "Innovation in PR technique execution",
                "Storytelling craft and narrative discipline",
                "Earned (vs. paid/owned) media mix",
                "Real-time / responsive moments",
                "Influencer / creator / partnership integration",
                "Production quality and craft of the assets",
            ],
        },
        {
            "key": "impact",
            "name": "Impact & Results",
            "weight": 0.30,
            "description": (
                "Measurable impact on business, society, or culture. Combines tangible "
                "business results AND quality/quantity of earned media coverage. Also "
                "considers behaviour change, policy change, and lasting cultural impact."
            ),
            "signals": [
                "Tangible business results (revenue, sales, downloads, sign-ups)",
                "Quality of earned media (top-tier outlets, journalist quotes)",
                "Quantity of earned media (reach, impressions, share of voice)",
                "Behaviour or attitude change",
                "Legislative / policy change",
                "Cultural conversation lasting beyond the campaign window",
                "Disproportionate impact relative to budget",
            ],
        },
    ],
    "sub_categories_hint": {
        "A": "Sectors (Consumer Goods, Healthcare, Automotive, Travel, Media, B2B, NFP/Gov)",
        "B": "Social Engagement & Influencer Marketing",
        "C": "Insights & Measurement (Research, PR Effectiveness)",
        "D": "PR Techniques (Media Relations, Events/Stunts, Launch, Storytelling, Tech, Internal)",
        "E": "Excellence in PR Craft (independent agencies only; Corporate Image, Public Affairs, Crisis Comms, Internal Comms, Sponsorship)",
        "F": "Culture & Context (Local Brand, Challenger, Single-Market, Behaviour, Humour, Budget, Purpose, Disruption, Cultural Engagement)",
    },
}


Tier = Literal["Grand Prix", "Gold", "Silver", "Bronze", "Shortlist", "Loser"]


_PR_BANDS = {
    "Grand Prix": (90, 100),
    "Gold": (80, 100),
    "Silver": (65, 80),
    "Bronze": (50, 65),
}


def expected_score_range(tier: Tier) -> tuple[int, int] | None:
    """Per-tier expected score range. None for Shortlist/Loser (not prize tiers)."""
    return _PR_BANDS.get(tier)


def tier_consistency(tier: Tier, weighted_score: float) -> Literal["expected", "below", "above", "n/a"]:
    """Flag whether a weighted score falls in the band expected for its tier."""
    band = _PR_BANDS.get(tier)
    if band is None:
        return "n/a"
    low, high = band
    if weighted_score < low:
        return "below"
    if weighted_score > high:
        return "above"
    return "expected"
