"""Mrs IArma · Cannes Lions prediction engine.

Public API for backend integrators.

============================================================
Quick start (Python)
============================================================

    from pathlib import Path
    from pipeline import evaluate_board, UserMetadata

    result = evaluate_board(
        image_path=Path("board.jpg"),
        user_metadata=UserMetadata(
            campaign_name="Phone Break",
            agency="VML Prague",
            client="KitKat",
            category="Outdoor",
            client_internationally_known=True,
        ),
    )

    print(result.tier_prediction.tier_label)
    # "GRAND PRIX LION"

    print(result.tier_prediction.score_percent)
    # 89

    print(result.tier_prediction.synthesis)
    # "Foundational idea..."

============================================================
What this engine does
============================================================
Given a Cannes Lions board image + creative metadata (campaign, agency,
client, etc.), this engine predicts which tier the entry would win:
Grand Prix / Gold / Silver / Bronze / No Medal.

Pipeline (~45 s, ~$2 per evaluation):
    1. Extraction       — Claude Opus VLM extracts a structured v3 schema
                          from the board image
    2. RAG retrieval    — Voyage AI finds 7 closest past entries
                          (5 winners + 2 non-winners) from the per-category
                          2024 reference base
    3. Multi-pass judge — 3 parallel Claude Opus calls produce per-axis
                          scores + tier probability distribution
    4. Malus & presages — 3 deterministic adjustments based on craft,
                          client international status, agency network

Returns a `BoardEvaluation` with:
    - `tier_prediction` (primary user-facing output, oracle tone)
    - `medal_prediction` (internal binary medal/no-medal)
    - extraction details, references used, raw scores, malus breakdown

See `INTEGRATION.md` at repo root for the full integration guide.
============================================================
"""

# Primary high-level entry point — what the backend dev will call.
from .evaluate import evaluate_board, DEFAULT_MEDAL_THRESHOLD

# Public data models — what the backend dev will type against.
from .schema import (
    # Inputs
    UserMetadata,
    # Primary output
    BoardEvaluation,
    TierPrediction,
    AxisDisplay,
    Presage,
    # Internal but exposed for completeness
    MedalPrediction,
    BoardAnalysis,
    Reference,
    # Type aliases
    PredictedTier,
    ConfidenceLabel,
    Tier,
)

# Errors that the integrator may want to catch
from .search import IndexNotBuilt

__all__ = [
    # High-level
    "evaluate_board",
    "DEFAULT_MEDAL_THRESHOLD",
    # Inputs
    "UserMetadata",
    # Outputs
    "BoardEvaluation",
    "TierPrediction",
    "AxisDisplay",
    "Presage",
    "MedalPrediction",
    "BoardAnalysis",
    "Reference",
    # Type aliases
    "PredictedTier",
    "ConfidenceLabel",
    "Tier",
    # Errors
    "IndexNotBuilt",
]

__version__ = "0.1.0"
