"""Pydantic models for the v3 board-extraction schema.

Two top-level blocks separate what is literally on the board (`extracted`) from
what the VLM had to infer (`inferred`). The `visual` block carries craft signals
that don't depend on text. Nothing in `extracted` is allowed to be invented.
"""
from typing import Literal

from pydantic import BaseModel, Field


class Extracted(BaseModel):
    campaign: str | None = None
    brand: str | None = None
    agencies: list[str] = Field(default_factory=list)
    tagline: str | None = None
    context: str | None = None
    insight: str | None = None
    idea: str | None = None
    execution: list[str] = Field(default_factory=list)
    metrics: list[str] = Field(default_factory=list)
    press_coverage: list[str] = Field(default_factory=list)


class Inferred(BaseModel):
    context: str | None = None
    insight: str | None = None
    idea: str | None = None
    one_liner: str | None = None
    creative_mechanisms: list[str] = Field(default_factory=list)
    qualitative_summary: str | None = None  # 1-2 sentence narrative of impact (used by RAG)


class Visual(BaseModel):
    style_description: str
    craft_quality: Literal["high", "medium", "low"]
    dominant_colors: list[str]


Tier = Literal["Grand Prix", "Gold", "Silver", "Bronze", "Shortlist", "Loser"]
WINNING_TIERS = {"Grand Prix", "Gold", "Silver", "Bronze"}
ImpactStrength = Literal["strong", "moderate", "qualitative_only", "none"]
TierConsistency = Literal["expected", "below", "above", "n/a"]


class AxisScore(BaseModel):
    score: int = Field(ge=0, le=100)
    rationale: str


class WhyItWon(BaseModel):
    idea: AxisScore
    strategy: AxisScore
    execution: AxisScore
    impact: AxisScore
    weighted_score: float
    verdict: str
    tier_consistency: TierConsistency


class BoardAnalysis(BaseModel):
    id: str
    tier: Tier
    category: str
    file_path: str
    extracted: Extracted
    inferred: Inferred
    visual: Visual
    review_flag: bool = False
    review_reasons: list[str] = Field(default_factory=list)
    why_it_won: WhyItWon | None = None


# ============================================================================
# Phase 2 — Evaluation of a new (uploaded) board
# ============================================================================


PredictedTier = Literal["Grand Prix", "Gold", "Silver", "Bronze", "No Medal"]


class UserMetadata(BaseModel):
    """Provided by the creative uploading their board."""
    campaign_name: str
    agency: str
    client: str
    category: str = "Outdoor"  # MVP only supports Outdoor; future: any Cannes family
    client_internationally_known: bool = True  # asked via the UI questionnaire


class Reference(BaseModel):
    """A past winner used as RAG calibration anchor in the evaluation prompt."""
    id: str
    campaign: str | None = None
    brand: str | None = None
    tier: Tier
    one_liner: str | None = None
    weighted_score: float
    similarity_score: float
    verdict: str | None = None


class TierProbabilities(BaseModel):
    """LLM-judged probability distribution across tiers. Sums to 1.0."""
    grand_prix: float = Field(ge=0.0, le=1.0, alias="Grand Prix")
    gold: float = Field(ge=0.0, le=1.0, alias="Gold")
    silver: float = Field(ge=0.0, le=1.0, alias="Silver")
    bronze: float = Field(ge=0.0, le=1.0, alias="Bronze")
    no_medal: float = Field(ge=0.0, le=1.0, alias="No Medal")

    model_config = {"populate_by_name": True}


ConfidenceLabel = Literal["high", "medium", "low"]


class MedalPrediction(BaseModel):
    """Binary medal-vs-no-medal prediction + confidence + diagnostic synthesis.

    Kept for internal use and debugging. The user-facing primary output is now
    `TierPrediction` (see below) which exposes the full 5-tier distribution
    with confidence label, mystic verdict, and structured présages.

    Note (2026-06-01): `improvement_tips` was removed because boards have
    already been submitted to the Cannes 2026 jury — forward-looking tips
    are not actionable at this stage. The synthesis is now a post-mortem
    diagnostic rather than an actionable note.
    """
    will_medal: bool  # True if P(medal) >= threshold
    medal_probability: float = Field(ge=0.0, le=1.0)  # P(medal) AFTER malus
    threshold: float = Field(ge=0.0, le=1.0)  # decision threshold used
    confidence: ConfidenceLabel  # high/medium/low based on distance to threshold
    synthesis: str  # 1-2 diagnostic sentences explaining the prediction


# ============================================================================
# Phase 4 — User-facing Tier Prediction (Mrs Airma · The Cannes Oracle)
# ============================================================================


AxisKey = Literal["idea", "strategy", "execution", "impact"]


class AxisDisplay(BaseModel):
    """A scored axis with display label and weight, for direct UI consumption.

    Distinct from `AxisScore` above, which is the judge-internal {score, rationale}
    structure used to build `WhyItWon`. This one is the user-facing presentation
    of an axis: display label + weight in the weighted total + final score.
    """
    key: AxisKey  # internal id ("idea" / "strategy" / "execution" / "impact")
    label: str  # display label (e.g. "Creative Idea")
    score: int = Field(ge=0, le=100)
    weight: float = Field(ge=0.0, le=1.0)  # weight in the weighted total (0.35, 0.10, etc.)


PresageKind = Literal["favorable", "unfavorable"]
PresageType = Literal["aesthetic", "client", "network"]


class Presage(BaseModel):
    """A structured presage (omen) corresponding to one of the 3 malus criteria.

    Each criterion produces a presage in either flavour:
      - favorable (no malus applied) — green check style
      - unfavorable (malus applied)  — red cross style
    """
    type: PresageType  # which malus criterion this presages
    kind: PresageKind  # favorable or unfavorable
    title: str  # short title (e.g. "Polished Board" / "Off-Standard Board")
    detail: str  # one-line detail (e.g. "Readable composition, careful hierarchy.")
    malus_pct: int = 0  # percentage points deducted if unfavorable (0 if favorable)


class TierPrediction(BaseModel):
    """Primary user-facing output. Aligns with the Mrs Airma design mockups."""
    predicted_tier: PredictedTier  # argmax of tier_probabilities → Grand Prix / Gold / Silver / Bronze / No Medal
    tier_label: str  # display label (e.g. "GOLD LION", "SILVER LION", "NO LION")
    tier_probabilities: dict[str, float]  # full distribution, sums to 1.0
    confidence: ConfidenceLabel  # high/medium/low — based on the gap between top-1 and top-2 tier
    score_percent: int = Field(ge=0, le=100)  # the headline % shown on the result page (e.g. "87%")
    mystic_verdict: str  # tier-specific oracle quote (e.g. "The stars align. Your campaign will carry gold.")
    axes: list[AxisDisplay]  # the 4 axes with display labels + weights + scores
    presages: list[Presage]  # exactly 3 presages, one per malus criterion
    synthesis: str  # 1-2 diagnostic sentences explaining the prediction (post-mortem, not actionable)


class BoardEvaluation(BaseModel):
    """End-to-end output of the evaluation pipeline.

    Primary user-facing output is `tier_prediction`. The legacy `medal_prediction`
    (binary) is kept for internal debugging and A/B comparison. All raw fields
    (axis scores, tier probabilities, references, pass details, malus) are
    retained for calibration & debug — not shown to the end user.
    """
    user_metadata: UserMetadata

    # PRIMARY user-facing output (Phase 4):
    tier_prediction: TierPrediction

    # Legacy / internal binary prediction (Phase 3.5):
    medal_prediction: MedalPrediction

    # Internal / debug fields (not shown to user):
    analysis: BoardAnalysis
    base_weighted_score: float
    final_weighted_score: float
    predicted_tier: PredictedTier
    tier_probabilities: dict[str, float] = Field(default_factory=dict)
    references: list[Reference]
    malus: dict
    pass_scores: list[dict] = Field(default_factory=list)
    pass_probs: list[dict] = Field(default_factory=list)
    pairwise: dict = Field(default_factory=dict)
    rigour_flags: list[str] = Field(default_factory=list)
