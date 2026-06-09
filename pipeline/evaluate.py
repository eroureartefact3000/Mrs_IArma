"""End-to-end evaluation pipeline for a new (uploaded) board.

evaluate_board(image_path, user_metadata, k_references=5, n_passes=3)
    1. Extract v3 (extract_pass1 + extract_pass2)
    2. Build search document → embed → RAG top-K from outdoor index
    3. Multi-pass judge with image + extraction + RAG references
    4. Compute malus (aesthetic + client + network)
    5. Final score = base × malus_multiplier → map to predicted tier
    6. Return a fully-populated BoardEvaluation
"""
from __future__ import annotations

import json
from pathlib import Path
from time import perf_counter
from typing import Any

from .category_registry import require_enabled_category
from .extractor import (
    extract_pass1,
    extract_pass2,
    flag_for_review,
)
from .judge import judge_board
from .malus import compute_malus
from .presentation import build_tier_prediction
from .schema import (
    AxisScore,
    BoardAnalysis,
    BoardEvaluation,
    ConfidenceLabel,
    MedalPrediction,
    PredictedTier,
    Reference,
    UserMetadata,
    WhyItWon,
)
from .search import search
from .search_doc import build_search_document


def _slug(filename: str) -> str:
    stem = Path(filename).stem.lower()
    for ch in (" ", "–", "(", ")", "/", "_", ",", "."):
        stem = stem.replace(ch, "-")
    while "--" in stem:
        stem = stem.replace("--", "-")
    return stem.strip("-")[:80]


def _score_to_tier(score: float) -> PredictedTier:
    """Map a 0-100 weighted score to a Cannes Lions tier per the project brief."""
    if score >= 90:
        return "Grand Prix"
    if score >= 80:
        return "Gold"
    if score >= 65:
        return "Silver"
    if score >= 50:
        return "Bronze"
    return "No Medal"


# Decision threshold for the binary medal/no-medal prediction.
# Empirically tuned via Phase 3 calibration sweep on 10 boards (2026-06-01):
#   - threshold 0.20 → 0.60 : binary accuracy plateaus at 70%
#   - threshold 0.65         : binary accuracy peaks at 80% (1 FP + 1 FN)
#   - threshold 0.70         : drops back to 70%
# 0.65 is the sweet spot. Adjustable per use case via evaluate_board(medal_threshold=...).
DEFAULT_MEDAL_THRESHOLD = 0.65


def _confidence_label(p_medal: float, threshold: float) -> ConfidenceLabel:
    """Confidence based on absolute distance to the decision threshold."""
    margin = abs(p_medal - threshold)
    if margin >= 0.25:
        return "high"
    if margin >= 0.10:
        return "medium"
    return "low"


def evaluate_board(
    image_path: Path,
    user_metadata: UserMetadata,
    *,
    k_references: int = 5,
    n_passes: int = 3,
    verbose: bool = True,
    exclude_ids: set[str] | None = None,
    medal_threshold: float = DEFAULT_MEDAL_THRESHOLD,
) -> BoardEvaluation:
    timing: dict[str, float] = {}

    # ------- Step 0: Resolve the category from the registry -------
    # Fail fast if the category isn't registered or isn't enabled. This catches
    # bad user input before we burn API calls on extraction.
    category_cfg = require_enabled_category(user_metadata.category)
    assert category_cfg.criteria is not None

    # ------- Step 1: Extraction v3 -------
    if verbose:
        print(f"\n[1/4] Extracting v3 from {image_path.name}...")
    t0 = perf_counter()
    extracted = extract_pass1(image_path)
    inferred, visual = extract_pass2(image_path, extracted)
    flag, reasons = flag_for_review(extracted, inferred)
    timing["extract"] = perf_counter() - t0
    if verbose:
        print(
            f"  → {timing['extract']:.1f}s  "
            f"campaign={extracted.campaign!r}  brand={extracted.brand!r}  "
            f"craft={visual.craft_quality}"
        )

    # ------- Step 2: RAG retrieval (winners + non-winners) -------
    # Calibration 2026-06-01: the LLM-judge was biased "everything is a medal"
    # when only seeing winner references (P(No Medal) too low). Adding 2 forced
    # non-winners (Shortlist/Loser) as contrast anchors gives the model concrete
    # examples of "what does not win".
    if verbose:
        print(f"\n[2/4] Retrieving top-{k_references} winners + 2 non-winners...")
    t0 = perf_counter()
    candidate_analysis_payload = {
        "extracted": extracted.model_dump(),
        "inferred": inferred.model_dump(),
        "visual": visual.model_dump(),
    }
    search_doc = build_search_document(candidate_analysis_payload)

    # 5 winner anchors (calibrate the top)
    winner_hits = search(
        search_doc,
        category=user_metadata.category,
        k=k_references,
        tier_filter={"Grand Prix", "Gold", "Silver", "Bronze"},
        exclude_ids=exclude_ids,
    )
    # 2 non-winner anchors (calibrate the bottom)
    non_winner_hits = search(
        search_doc,
        category=user_metadata.category,
        k=2,
        tier_filter={"Shortlist", "Loser"},
        exclude_ids=exclude_ids,
    )
    hits = winner_hits + non_winner_hits
    references = [
        Reference(
            id=h["id"],
            campaign=h.get("campaign"),
            brand=h.get("brand"),
            tier=h["tier"],
            one_liner=h.get("one_liner"),
            weighted_score=h["weighted_score"],
            similarity_score=h["score"],
            verdict=(h.get("full_record") or {}).get("why_it_won", {}).get("verdict"),
        )
        for h in hits
    ]
    timing["search"] = perf_counter() - t0
    if verbose:
        print(f"  → {timing['search']:.1f}s  retrieved {len(references)} references")
        for r in references:
            print(f"      {r.similarity_score:.3f}  [{r.tier:10s}]  {r.campaign}  | {r.one_liner}")

    # ------- Step 3: LLM-Judge (multi-pass) -------
    if verbose:
        print(f"\n[3/4] Running LLM-Judge ({n_passes}× parallel passes)...")
    t0 = perf_counter()
    judge_out = judge_board(
        image_path=image_path,
        extracted=extracted,
        inferred=inferred,
        visual=visual,
        references=references,
        n_passes=n_passes,
        criteria=category_cfg.criteria,
        category=user_metadata.category,
    )
    timing["judge"] = perf_counter() - t0
    if verbose:
        print(f"  → {timing['judge']:.1f}s")
        scores = judge_out["averaged_scores"]
        probs = judge_out["tier_probabilities"]
        print(
            f"      averaged axes: I={scores['idea']:.1f}  S={scores['strategy']:.1f}  "
            f"E={scores['execution']:.1f}  R={scores['impact']:.1f}  "
            f"→ weighted={judge_out['weighted_score']:.1f}"
        )
        print(f"      tier probs: " + "  ".join(f"{t[:3]}={probs[t]:.2f}" for t in ["Grand Prix", "Gold", "Silver", "Bronze", "No Medal"]))

    # ------- Step 4: Apply malus + tier prediction -------
    if verbose:
        print(f"\n[4/4] Applying malus + tier prediction...")
    malus = compute_malus(
        craft_quality=visual.craft_quality,
        agency_name=user_metadata.agency,
        client_internationally_known=user_metadata.client_internationally_known,
    )
    base_score = judge_out["weighted_score"]
    final_score = round(base_score * malus.multiplier, 1)

    # Apply malus to probabilities: deduction proportional to (1 - multiplier),
    # transferred down by one tier. With mult=0.80, 20% of GP/Gold/Silver mass
    # shifts one tier down, 20% of Bronze shifts to No Medal.
    raw_probs = dict(judge_out["tier_probabilities"])
    if malus.multiplier < 1.0:
        deduction_ratio = 1.0 - malus.multiplier
        shifted = {t: raw_probs[t] for t in raw_probs}
        for higher, lower in [
            ("Grand Prix", "Gold"),
            ("Gold", "Silver"),
            ("Silver", "Bronze"),
            ("Bronze", "No Medal"),
        ]:
            mass = shifted[higher] * deduction_ratio
            shifted[higher] -= mass
            shifted[lower] += mass
        final_probs = shifted
    else:
        final_probs = raw_probs

    # Renormalise just to be safe
    total = sum(final_probs.values())
    if total > 0:
        final_probs = {t: v / total for t, v in final_probs.items()}

    predicted_tier = max(final_probs.items(), key=lambda kv: kv[1])[0]
    medal_probability = 1.0 - final_probs.get("No Medal", 0.0)

    # Binary medal/no-medal prediction
    will_medal = medal_probability >= medal_threshold
    confidence = _confidence_label(medal_probability, medal_threshold)
    medal_prediction = MedalPrediction(
        will_medal=will_medal,
        medal_probability=medal_probability,
        threshold=medal_threshold,
        confidence=confidence,
        synthesis=judge_out.get("synthesis", ""),
    )

    # Primary user-facing prediction (Mrs Airma · The Cannes Oracle)
    tier_prediction = build_tier_prediction(
        board_id=_slug(image_path.name),
        predicted_tier=predicted_tier,  # type: ignore[arg-type]
        tier_probabilities=final_probs,
        final_weighted_score=final_score,
        axis_scores=judge_out["averaged_scores"],
        malus=malus.model_dump(),
        synthesis=judge_out.get("synthesis", ""),
        criteria=category_cfg.criteria,
    )

    if verbose:
        verdict_str = "WILL MEDAL" if will_medal else "NO MEDAL"
        print(f"  base_score={base_score:.1f}  ×  malus_mult={malus.multiplier:.2f}  →  final_score={final_score:.1f}")
        print(f"  P(medal) = {medal_probability:.2%}  (threshold={medal_threshold:.0%})")
        print(f"  → {verdict_str}  ({confidence} confidence)")
        print(f"  [debug] argmax tier={predicted_tier}")
        print(f"  [debug] Final probs: " + "  ".join(f"{t[:3]}={final_probs[t]:.2f}" for t in ["Grand Prix", "Gold", "Silver", "Bronze", "No Medal"]))
        print(f"  → tier_prediction: {tier_prediction.tier_label} ({tier_prediction.score_percent}%, conf={tier_prediction.confidence})")
        for note in malus.notes:
            print(f"     · {note}")

    # ------- Package the final BoardEvaluation -------
    scored_axes = judge_out["averaged_scores"]
    rationales = judge_out["rationales"]
    why = WhyItWon(
        idea=AxisScore(score=int(round(scored_axes["idea"])), rationale=rationales["idea"]),
        strategy=AxisScore(score=int(round(scored_axes["strategy"])), rationale=rationales["strategy"]),
        execution=AxisScore(score=int(round(scored_axes["execution"])), rationale=rationales["execution"]),
        impact=AxisScore(score=int(round(scored_axes["impact"])), rationale=rationales["impact"]),
        weighted_score=base_score,
        verdict=judge_out["verdict"],
        # No tier consistency check — the candidate has no ground-truth tier.
        tier_consistency="n/a",
    )

    analysis = BoardAnalysis(
        id=_slug(image_path.name),
        # No ground-truth tier — we store predicted_tier separately in BoardEvaluation.
        # Use "Loser" as a placeholder sentinel since Tier requires a value;
        # the real prediction lives in BoardEvaluation.predicted_tier.
        tier="Loser",
        category=user_metadata.category,
        file_path=str(image_path),
        extracted=extracted,
        inferred=inferred,
        visual=visual,
        review_flag=flag,
        review_reasons=reasons,
        why_it_won=why,
    )

    total_elapsed = sum(timing.values())
    if verbose:
        print(f"\n✅ Done in {total_elapsed:.1f}s total  ({timing})")

    return BoardEvaluation(
        user_metadata=user_metadata,
        tier_prediction=tier_prediction,
        medal_prediction=medal_prediction,
        analysis=analysis,
        tier_probabilities=final_probs,
        pairwise=judge_out.get("pairwise", {}),
        pass_probs=judge_out.get("pass_probs", []),
        base_weighted_score=base_score,
        final_weighted_score=final_score,
        predicted_tier=predicted_tier,
        references=references,
        malus=malus.model_dump(),
        pass_scores=judge_out["pass_scores"],
        rigour_flags=[],  # placeholder for future automated rigour checks
    )
