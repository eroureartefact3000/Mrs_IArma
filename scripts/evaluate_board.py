"""CLI to evaluate a single board.

Usage:
    uv run python evaluate_board.py \\
        --image "path/to/board.jpg" \\
        --campaign "Phone Break" \\
        --agency "VML Prague" \\
        --client "KitKat" \\
        --client-international         # omit for not-international (-20%% malus)
        [--passes 3]                   # judge passes (default 3)
        [--k 5]                        # RAG top-K (default 5)
        [--output data/evaluation.json]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from pipeline.evaluate import evaluate_board
from pipeline.schema import UserMetadata


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--campaign", required=True)
    parser.add_argument("--agency", required=True)
    parser.add_argument("--client", required=True)
    parser.add_argument(
        "--client-international",
        dest="client_international",
        action="store_true",
        help="Set if the client is internationally known (no -20%% malus). Default: True (recommended for testing).",
    )
    parser.add_argument(
        "--client-not-international",
        dest="client_international",
        action="store_false",
        help="Set if the client is NOT internationally known (triggers -20%% malus).",
    )
    parser.set_defaults(client_international=True)
    parser.add_argument("--category", default="Outdoor")
    parser.add_argument("--passes", type=int, default=3)
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    if not args.image.exists():
        raise SystemExit(f"Image not found: {args.image}")

    metadata = UserMetadata(
        campaign_name=args.campaign,
        agency=args.agency,
        client=args.client,
        category=args.category,
        client_internationally_known=args.client_international,
    )

    print(f"=== Evaluating {args.image.name} ===")
    print(f"  campaign : {metadata.campaign_name}")
    print(f"  agency   : {metadata.agency}")
    print(f"  client   : {metadata.client} (international: {metadata.client_internationally_known})")
    print(f"  category : {metadata.category}")
    print(f"  passes   : {args.passes}   k_refs: {args.k}")

    evaluation = evaluate_board(
        image_path=args.image,
        user_metadata=metadata,
        k_references=args.k,
        n_passes=args.passes,
        verbose=True,
    )

    # ========== USER-FACING OUTPUT (Mrs Airma · The Cannes Oracle) ==========
    tp = evaluation.tier_prediction
    print("\n" + "=" * 70)
    print(f"  {tp.tier_label}      ·      {tp.score_percent}%")
    print(f"  (confidence: {tp.confidence})")
    print("=" * 70)
    print()
    print(f"  « {tp.mystic_verdict} »")
    print()
    print("─ DETAILED READING OF THE STARS ──────────────────────────────────────")
    for a in tp.axes:
        bar_len = int(round(a.score / 100 * 30))
        bar = "█" * bar_len + "·" * (30 - bar_len)
        print(f"  {a.label:<18s} (weight {int(a.weight*100):>2}%)   {bar}  {a.score:>3}/100")
    print()
    presage_section = "FAVORABLE PRESAGES DETECTED" if all(p.kind == "favorable" for p in tp.presages) else "PRESAGES DETECTED"
    print(f"─ {presage_section} ───────────────────────────────────────")
    for p in tp.presages:
        sign = "✓" if p.kind == "favorable" else "✗"
        suffix = f"  (−{p.malus_pct}%)" if p.malus_pct else ""
        print(f"  {sign} {p.title:<28s}  {p.detail}{suffix}")
    print()
    print("─ SYNTHESIS ──────────────────────────────────────────────────────────")
    print(f"  {tp.synthesis}")
    print()

    # ========== INTERNAL DEBUG (not shown to end-user) ==========
    print("─" * 70)
    print("INTERNAL DEBUG (not user-facing):")
    probs = evaluation.tier_probabilities
    print(f"  argmax tier   : {evaluation.predicted_tier}")
    print(f"  tier probs    : " + "  ".join(f"{t[:3]}={probs.get(t, 0):.2f}" for t in ["Grand Prix", "Gold", "Silver", "Bronze", "No Medal"]))
    print(f"  axis scores   : I={evaluation.analysis.why_it_won.idea.score} "
          f"S={evaluation.analysis.why_it_won.strategy.score} "
          f"E={evaluation.analysis.why_it_won.execution.score} "
          f"R={evaluation.analysis.why_it_won.impact.score}")
    print(f"  base→final    : {evaluation.base_weighted_score:.1f} × {evaluation.malus['multiplier']:.2f} = {evaluation.final_weighted_score:.1f}")
    for note in evaluation.malus.get("notes", []):
        print(f"    · {note}")

    if args.output:
        args.output.parent.mkdir(exist_ok=True, parents=True)
        args.output.write_text(json.dumps(evaluation.model_dump(), indent=2, ensure_ascii=False))
        print(f"\nSaved full evaluation → {args.output}")


if __name__ == "__main__":
    main()
