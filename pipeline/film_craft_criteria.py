"""Film Craft Lions judging criteria.

Craft-dominant for film: direction, cinematography, editing, sound design,
music, casting, production design, VFX. Boards are case studies of the film
work; signal will be weaker than for pure-visual categories.
    15% Idea  /  10% Strategy  /  60% Execution  /  15% Impact
"""
from typing import Literal


FILM_CRAFT_CRITERIA: dict = {
    "category": "Film Craft",
    "definition": (
        "The Film Craft Lions celebrate the craft disciplines that bring films "
        "to life: direction, cinematography, editing, sound design, music, "
        "casting, production design, VFX, animation. The judging targets the "
        "filmic craft; the board is the case study window."
    ),
    "axes": [
        {"key": "idea", "name": "Idea", "weight": 0.15,
         "description": "Originality of the creative thought driving the craft. Secondary in this craft-dominant category.",
         "signals": ["Conceptual clarity behind the craft choice", "Cultural resonance"]},
        {"key": "strategy", "name": "Strategy", "weight": 0.10,
         "description": "Light sanity check on brand-mission fit.",
         "signals": ["WHO IS THE BRAND? Mission + tone-of-voice", "Idea ↔ mission coherence"]},
        {"key": "execution", "name": "Craft Execution", "weight": 0.60,
         "description": "Dominant axis by a wide margin. Specific film-craft technique: cinematography, editing, sound design, music, casting, VFX, production design, animation.",
         "signals": ["Cinematography (lighting, lens choice, framing)", "Editing (pacing, rhythm, transitions)", "Sound design + music", "Performance / casting", "Production design + costume", "VFX or animation craft", "Director's signature visible"]},
        {"key": "impact", "name": "Impact", "weight": 0.15,
         "description": "Industry recognition (film-craft awards, critical pickup, peer citations). Business outcomes less central.",
         "signals": ["Film-press / craft-press pickup", "Peer-to-peer citations", "Awards beyond Cannes (Clio, D&AD, festival selections)", "Audience engagement"]},
    ],
    "sub_categories_hint": {
        "A": "Cinematography",
        "B": "Editing",
        "C": "Sound Design & Music",
        "D": "Direction",
        "E": "Production Design / Art Direction",
        "F": "VFX / Animation",
        "G": "Casting / Performance",
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
