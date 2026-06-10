"""Audio & Radio Lions judging criteria.

Pondération aligned with audio-only work: idea + execution dominate; impact
matters but is often softer (radio audiences are harder to measure than digital).
    30% Idea  /  10% Strategy  /  35% Execution  /  25% Impact
"""
from typing import Literal


AUDIO_RADIO_CRITERIA: dict = {
    "category": "Audio & Radio",
    "definition": (
        "The Audio & Radio Lions celebrate creative work delivered through audio "
        "only — radio spots, podcasts, audio-led campaigns, sound-design-led "
        "branded content. The work must land without visual support: voice, "
        "music, sound design, and timing carry the entire idea."
    ),
    "axes": [
        {"key": "idea", "name": "Idea", "weight": 0.30,
         "description": "Originality of the audio concept. The single creative thought that makes the spot stick after one listen.",
         "signals": ["Mnemonic device (jingle, hook, signature sound)", "Cultural relevance", "Sonic surprise / format invention", "Translatability across markets"]},
        {"key": "strategy", "name": "Strategy", "weight": 0.10,
         "description": "WHY this audio approach for this brand. Brand-mission fit and audience insight.",
         "signals": ["WHO IS THE BRAND? Mission + audio territory", "Audience reachable via audio", "Insight rooted in real behavioural truth"]},
        {"key": "execution", "name": "Execution", "weight": 0.35,
         "description": "HOW the audio is crafted. Voiceover direction, sound design, music composition, timing, mix quality.",
         "signals": ["Voiceover craft", "Sound design quality", "Music composition / scoring", "Pacing and timing", "Format-native (radio break vs podcast vs ambient audio)"]},
        {"key": "impact", "name": "Impact & Results", "weight": 0.25,
         "description": "Audience reach + behaviour change + brand metric shifts. Audio impact is often softer than digital; cultural pickup and recall matter.",
         "signals": ["Reach / listenership", "Recall and recognition shifts", "Behaviour change", "Cultural conversation", "Business outcome when documented"]},
    ],
    "sub_categories_hint": {
        "A": "Sectors (radio spots by sector)",
        "B": "Excellence in Audio & Radio (Use of Audio Technology, Audio-Led Branded Content)",
        "C": "Innovation in Audio (Use of Music, Sound Design)",
        "D": "Culture & Context",
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
