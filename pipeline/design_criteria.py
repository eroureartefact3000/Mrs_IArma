"""Design Lions judging criteria.

Pondération biased toward Execution since Design is craft-defined per the
Cannes Lions 2026 entry kit:
    25% Idea  /  10% Strategy  /  45% Execution  /  20% Impact

Tier-to-score mapping (canonical Cannes band):
    Grand Prix : 90-100
    Gold       : 80-100
    Silver     : 65-80
    Bronze     : 50-65
"""
from typing import Literal


DESIGN_CRITERIA: dict = {
    "category": "Design",
    "definition": (
        "The Design Lions celebrate creative and effective design solutions across "
        "all media. The work should demonstrate excellence in craft, visual problem-"
        "solving, and aesthetic intelligence — from brand identity systems to "
        "packaging, environmental graphics, publication design, typography, and "
        "data visualisation. Per the entry kit, the dominant criterion is execution "
        "(craft); idea and impact carry secondary weight."
    ),
    "axes": [
        {
            "key": "idea",
            "name": "Idea",
            "weight": 0.25,
            "description": (
                "Originality of the design concept. The unifying creative thought "
                "that organises the design system or single artefact."
            ),
            "signals": [
                "Uniqueness vs. category conventions",
                "Conceptual clarity — one strong idea expressed visually",
                "Cultural resonance / topical relevance",
                "Translatability across applications (logo, packaging, signage, etc.)",
                "Mnemonic power of the visual or symbolic device",
            ],
        },
        {
            "key": "strategy",
            "name": "Strategy",
            "weight": 0.10,
            "description": (
                "WHY this design, for this brand, in this context. Sanity-check "
                "axis: is the design coherent with the brand's mission? Is the "
                "brief well-served by the visual language chosen? Do NOT discuss "
                "craft or production here — those belong to Execution."
            ),
            "signals": [
                "WHO IS THE BRAND? Identify the brand's mission and aesthetic territory",
                "Design ↔ brand mission coherence",
                "Audience fit (is the visual language right for the target?)",
                "Brief-to-solution fit (does the design actually solve the stated problem?)",
            ],
        },
        {
            "key": "execution",
            "name": "Execution",
            "weight": 0.45,
            "description": (
                "HOW the design is crafted. The dominant axis. Covers typography "
                "quality, illustration / photography / CGI craft, layout and "
                "composition, colour decisions, materiality (when applicable), "
                "system coherence across applications, and production finesse."
            ),
            "signals": [
                "Typography craft (typeface choice, kerning, hierarchy, custom letterforms)",
                "Visual craft (illustration, photography, CGI quality)",
                "Composition and layout discipline",
                "Colour palette intentionality",
                "Materiality and production craft (paper stock, finishes, fabrication when relevant)",
                "System coherence across applications (logo + packaging + signage hold together)",
                "Multi-execution consistency without monotony",
            ],
        },
        {
            "key": "impact",
            "name": "Impact & Results",
            "weight": 0.20,
            "description": (
                "Measurable impact on business, cultural recognition, or design "
                "discourse. Design is often less measurable than other categories, "
                "so qualitative-but-credible impact (cultural conversation, design "
                "press pickup, jury-quotable craft moments) carries weight."
            ),
            "signals": [
                "Brand metric shifts (recognition, recall, sentiment)",
                "Business results (sales, traffic, brand-equity lift)",
                "Design-press / design-awards pickup",
                "Cultural conversation lasting beyond the campaign window",
                "Adoption / extensibility of the design system over time",
            ],
        },
    ],
    "sub_categories_hint": {
        "A": "Brand Identity (creation or refresh — visual identity systems)",
        "B": "Packaging Design (consumer / luxury / craft / sustainable / structural)",
        "C": "Communication Design (publication, posters, editorial, art direction)",
        "D": "Spatial / Environmental Design (signage, wayfinding, retail, exhibition)",
        "E": "Digital & Interactive Design (UI/UX, digital products, motion graphics)",
        "F": "Design Craft (typography, illustration, art direction, copywriting)",
    },
}


Tier = Literal["Grand Prix", "Gold", "Silver", "Bronze", "Shortlist", "Loser"]


_DESIGN_BANDS = {
    "Grand Prix": (90, 100),
    "Gold": (80, 100),
    "Silver": (65, 80),
    "Bronze": (50, 65),
}


def expected_score_range(tier: Tier) -> tuple[int, int] | None:
    return _DESIGN_BANDS.get(tier)


def tier_consistency(tier: Tier, weighted_score: float) -> Literal["expected", "below", "above", "n/a"]:
    band = _DESIGN_BANDS.get(tier)
    if band is None:
        return "n/a"
    low, high = band
    if weighted_score < low:
        return "below"
    if weighted_score > high:
        return "above"
    return "expected"
