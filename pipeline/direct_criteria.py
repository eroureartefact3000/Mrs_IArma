"""Direct Lions judging criteria.

Pondération biased toward Impact since Direct is fundamentally measured by
audience response, per the Cannes Lions 2026 entry kit:
    25% Idea  /  15% Strategy  /  25% Execution  /  35% Impact

Tier-to-score mapping (canonical Cannes band):
    Grand Prix : 90-100
    Gold       : 80-100
    Silver     : 65-80
    Bronze     : 50-65
"""
from typing import Literal


DIRECT_CRITERIA: dict = {
    "category": "Direct",
    "definition": (
        "The Direct Lions celebrate creative work that drives a specific, measurable "
        "audience response — direct mail, ambient direct, direct-response broadcast, "
        "lead-generation campaigns, behavioural-change interventions. The defining "
        "characteristic: a clear call-to-action and a response that can be counted. "
        "Per the entry kit, Impact carries the dominant weight since Direct is "
        "judged on measurable response."
    ),
    "axes": [
        {
            "key": "idea",
            "name": "Idea",
            "weight": 0.25,
            "description": (
                "Originality of the creative mechanism. In Direct, the idea is usually "
                "a mechanism — something the audience interacts with — rather than a "
                "passive message. The most-memorable Direct work has a clever device "
                "that makes the response inevitable."
            ),
            "signals": [
                "Uniqueness of the mechanism vs. category conventions",
                "Mechanic that makes response feel inevitable or playful",
                "Mnemonic power — does the device stick?",
                "Translatability across markets",
                "Cultural relevance / topicality",
            ],
        },
        {
            "key": "strategy",
            "name": "Direct Strategy",
            "weight": 0.15,
            "description": (
                "WHO is being targeted and WHY this mechanism will move them. Audience "
                "selection, channel choice, response architecture (what action the "
                "audience takes and how it flows back to the brand). Do NOT discuss "
                "craft or production here."
            ),
            "signals": [
                "Clear audience identification — narrow target, not 'everyone'",
                "Channel choice fits where the target is reachable",
                "Response architecture is clean (action → measurement)",
                "Brand mission ↔ idea coherence",
                "Insight is sourced from real data (behavioural truth, not assumption)",
            ],
        },
        {
            "key": "execution",
            "name": "Execution",
            "weight": 0.25,
            "description": (
                "HOW the mechanism is built and delivered. Production quality, "
                "interaction design, channel craft (mail piece tactile quality, ambient "
                "install build, broadcast craft). The execution must make the response "
                "experience itself rewarding."
            ),
            "signals": [
                "Craft quality of the response-driving asset",
                "Channel-specific craft (tactile, spatial, audio, digital — fit-for-format)",
                "Interaction design — is the response easy and satisfying?",
                "Production finesse and material quality",
                "Multi-execution coherence when relevant",
            ],
        },
        {
            "key": "impact",
            "name": "Response & Business Impact",
            "weight": 0.35,
            "description": (
                "The dominant axis for Direct. Direct Lions are judged on measurable "
                "audience response — response rate, conversion, sign-ups, sales lift, "
                "behaviour change. Vanity reach metrics (impressions) are weaker than "
                "response metrics (people who actually did the thing)."
            ),
            "signals": [
                "Response rate / conversion rate (the primary Direct metric)",
                "Sign-ups, sales, donations, applications, calls — counted actions",
                "Behaviour or attitude change with documented before-and-after",
                "Disproportionate response relative to media spend",
                "Cost-per-acquisition or ROI evidence",
                "Cultural conversation as a multiplier (secondary, not primary)",
            ],
        },
    ],
    "sub_categories_hint": {
        "A": "Sectors (Consumer Goods, Healthcare, Automotive, Travel, Media, B2B, NFP/Gov) — direct-response work in each sector",
        "B": "Direct Techniques (Direct Mail, Ambient Direct, Direct Response Broadcast, Digital Direct, Use of Tech)",
        "C": "Excellence in Direct Craft (independent agencies)",
        "D": "Culture & Context (Local Brand, Challenger, Single-Market, Behaviour, Humour, Budget, Purpose, Disruption, Cultural Engagement)",
    },
}


Tier = Literal["Grand Prix", "Gold", "Silver", "Bronze", "Shortlist", "Loser"]


_DIRECT_BANDS = {
    "Grand Prix": (90, 100),
    "Gold": (80, 100),
    "Silver": (65, 80),
    "Bronze": (50, 65),
}


def expected_score_range(tier: Tier) -> tuple[int, int] | None:
    return _DIRECT_BANDS.get(tier)


def tier_consistency(tier: Tier, weighted_score: float) -> Literal["expected", "below", "above", "n/a"]:
    band = _DIRECT_BANDS.get(tier)
    if band is None:
        return "n/a"
    low, high = band
    if weighted_score < low:
        return "below"
    if weighted_score > high:
        return "above"
    return "expected"
