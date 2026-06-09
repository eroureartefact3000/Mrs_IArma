"""Smoke test: 1 evaluation per newly-wired category.

Goal: confirm the production pipeline doesn't crash on any of the 12 new
categories. Not a calibration measurement — just pipeline integrity.

For each category, runs evaluate_board on one Silver-tier winner with the
board's own id in exclude_ids, so retrieval doesn't self-match.

Output: data_internal/smoke_test_results.jsonl + pass/fail summary to stdout.

Cost: ~$18-25 (12 × ~$1.50-2). Runtime: ~12 min sequential.
"""
from __future__ import annotations

import json
from pathlib import Path
from time import perf_counter

from pipeline.evaluate import evaluate_board
from pipeline.schema import UserMetadata

ROOT = Path(__file__).resolve().parent.parent
PICKS_PATH = Path("/tmp/smoke_test_picks.json")
OUT_PATH = ROOT / "data_internal" / "smoke_test_results.jsonl"


def main() -> None:
    picks = json.loads(PICKS_PATH.read_text())
    print(f"Smoke testing {len(picks)} categories...")
    OUT_PATH.parent.mkdir(exist_ok=True)

    results = []
    t_total = perf_counter()
    for i, pick in enumerate(picks, 1):
        cat = pick["category"]
        slug = pick["slug"]
        img_path = ROOT / pick["file_path"]
        print(f"\n[{i}/{len(picks)}] {cat}")
        print(f"  board     : {slug}")
        print(f"  actual    : {pick['tier']}")

        if not img_path.exists():
            print(f"  ✗ FILE MISSING: {img_path}")
            results.append({"category": cat, "slug": slug, "status": "file_missing"})
            continue

        metadata = UserMetadata(
            campaign_name=pick["campaign"] or "Smoke Test",
            agency=pick["agency"] or "unknown",
            client=pick["client"] or "unknown",
            category=cat,
            client_internationally_known=True,  # default; doesn't matter for smoke
        )

        t0 = perf_counter()
        try:
            evaluation = evaluate_board(
                image_path=img_path,
                user_metadata=metadata,
                k_references=5,
                n_passes=3,
                verbose=False,
                exclude_ids={slug},
            )
            elapsed = perf_counter() - t0
            tp = evaluation.tier_prediction
            ok = {
                "category": cat,
                "slug": slug,
                "actual_tier": pick["tier"],
                "predicted_tier": evaluation.predicted_tier,
                "score_percent": tp.score_percent,
                "confidence": tp.confidence,
                "axis_scores": {
                    "idea": evaluation.analysis.why_it_won.idea.score,
                    "strategy": evaluation.analysis.why_it_won.strategy.score,
                    "execution": evaluation.analysis.why_it_won.execution.score,
                    "impact": evaluation.analysis.why_it_won.impact.score,
                },
                "elapsed_sec": round(elapsed, 1),
                "status": "ok",
            }
            results.append(ok)
            print(f"  ✓ predicted: {evaluation.predicted_tier} ({tp.score_percent}%, {tp.confidence}) in {elapsed:.1f}s")
        except Exception as e:
            elapsed = perf_counter() - t0
            err = {
                "category": cat,
                "slug": slug,
                "elapsed_sec": round(elapsed, 1),
                "status": "error",
                "error": repr(e),
            }
            results.append(err)
            print(f"  ✗ ERROR after {elapsed:.1f}s: {e!r}")

    elapsed = perf_counter() - t_total
    with OUT_PATH.open("w") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    n_ok = sum(1 for r in results if r["status"] == "ok")
    n_err = sum(1 for r in results if r["status"] == "error")
    n_missing = sum(1 for r in results if r["status"] == "file_missing")

    print(f"\n{'=' * 60}")
    print(f"SMOKE TEST DONE — {elapsed:.0f}s total")
    print(f"  ✓ ok        : {n_ok}/{len(picks)}")
    print(f"  ✗ error     : {n_err}")
    print(f"  ? missing   : {n_missing}")
    print(f"\nResults: {OUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
