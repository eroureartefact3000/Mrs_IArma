"""Film Lions judging criteria.

Film is a video-first category — the board is a CASE STUDY of the film, not
the film itself. Signal from the static board will be weaker than visual
categories. Pondération aligned with Idea + Execution heavy:
    35% Idea  /  10% Strategy  /  35% Execution  /  20% Impact
"""
from typing import Literal


FILM_CRITERIA: dict = {
    "category": "Film",
    "definition": (
        "The Film Lions celebrate creative work delivered through moving image — "
        "TV spots, online films, branded shorts, feature-length brand content. "
        "Boards in this category are case studies of the actual film work, often "
        "showing keyframes + tagline + objectives. The judging targets the film "
        "itself; the board is the jury's window into it."
    ),
    "axes": [
        {"key": "idea", "name": "Idea", "weight": 0.35,
         "description": "Originality of the film concept — the story or visual hook.",
         "signals": [
             "Story / narrative originality vs. category conventions",
             "Visual hook recognisable from keyframes",
             "Mnemonic power of the central film device",
             "Cultural relevance / topicality",
             "Translatability across markets",
         ]},
        {"key": "strategy", "name": "Strategy", "weight": 0.10,
         "description": "WHY this film for this brand. Sanity check on mission fit.",
         "signals": [
             "WHO IS THE BRAND? Mission + tone-of-voice authority",
             "Brand mission ↔ film concept coherence",
             "Audience fit (right film for right viewer)",
             "Insight rooted in real audience truth",
         ]},
        {"key": "execution", "name": "Execution", "weight": 0.35,
         "description": "HOW the film was crafted — cinematography, editing, sound, performance. Read from keyframes + tagline + production credits.",
         "signals": [
             "Cinematography craft inferable from stills",
             "Performance / casting quality",
             "Editing / pacing (when shown via storyboard sequence on the board)",
             "Sound design / music (when described or credited on the board)",
             "Multi-execution coherence when the campaign has multiple films",
             "Production-credit caliber (director, DOP, music) — proxy for craft when stills are limited",
         ]},
        {"key": "impact", "name": "Impact & Results", "weight": 0.20,
         "description": "Audience reach + cultural conversation + brand outcomes.",
         "signals": [
             "View counts / watch-time / completion rate",
             "Cultural conversation (press, social, fan discourse)",
             "Brand metric shifts (consideration, recall, affinity)",
             "Business results when documented",
             "Disproportionate impact relative to media spend",
         ]},
    ],
    "sub_categories_hint": {
        "A": "Film: Sectors (CG, Healthcare, Auto, Travel, Media, B2B, NFP/Gov)",
        "B": "Use of Channels (TV, Online, Cinema, Social-First, Branded Content)",
        "C": "Excellence in Film (Single-Market, Use of Tech, Budget)",
        "D": "Culture & Context (Local, Challenger, Behaviour, Humour, Budget, Purpose, Disruption)",
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
