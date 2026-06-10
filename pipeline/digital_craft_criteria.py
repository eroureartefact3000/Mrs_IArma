"""Digital Craft Lions judging criteria.

Craft-dominant category for digital experiences (websites, apps, AR/VR/XR,
interactive installations, motion design, UI animations).
    20% Idea  /  10% Strategy  /  55% Execution  /  15% Impact
"""
from typing import Literal


DIGITAL_CRAFT_CRITERIA: dict = {
    "category": "Digital Craft",
    "definition": (
        "The Digital Craft Lions celebrate the craft of digital experiences: "
        "websites, apps, interactive installations, AR/VR/XR, motion graphics "
        "and UI animation. The board IS the craft showcase; execution dominates."
    ),
    "axes": [
        {"key": "idea", "name": "Idea", "weight": 0.20,
         "description": "Originality of the digital concept. Secondary to craft in this category.",
         "signals": ["Uniqueness of the digital interaction concept", "Mnemonic power", "Cultural resonance", "Translatability across platforms"]},
        {"key": "strategy", "name": "Strategy", "weight": 0.10,
         "description": "Light sanity check: brand mission fit and audience fit.",
         "signals": ["WHO IS THE BRAND? Mission and territory", "Idea ↔ mission coherence", "Audience-platform fit"]},
        {"key": "execution", "name": "Craft Execution", "weight": 0.55,
         "description": "Dominant axis. Digital craft: motion design, micro-interactions, performance, accessibility, multi-device coherence.",
         "signals": ["Motion design quality (easing, timing, choreography)", "Micro-interactions and feedback", "Performance (load time, smoothness)", "Multi-device coherence", "Accessibility considerations", "Technical innovation (WebGL, AR, generative)"]},
        {"key": "impact", "name": "Impact", "weight": 0.15,
         "description": "Industry recognition, craft-press pickup, peer recognition. Business outcomes are secondary in this craft category.",
         "signals": ["Industry / craft press pickup", "Peer recognition", "User engagement metrics", "Brand metric shifts"]},
    ],
    "sub_categories_hint": {
        "A": "Digital Design (Websites, Apps, Digital Products)",
        "B": "Interactive Experiences (AR/VR/XR, Installations)",
        "C": "Motion & Animation",
        "D": "Use of Tech (WebGL, generative, AI)",
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
