"""Generate per-axis 'why-it-won' rationale for every Outdoor 2024 board.

Reads `data/outdoor_2024_extractions.jsonl`, runs the rationale generator using
the Outdoor criteria (35/10/30/25) + DA-corrected mental model (Strategy=WHY,
Execution=HOW), saves enriched results to `data/outdoor_2024_with_rationale.jsonl`.

Cost: ~$20-25 for ~120 boards. ~6 min with 4 workers.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from statistics import mean, stdev
from time import perf_counter

from tqdm import tqdm

from pipeline.outdoor_criteria import (
    OUTDOOR_CRITERIA,
    expected_score_range,
    tier_consistency,
)
from pipeline.rationale import generate_why_it_won
from pipeline.schema import BoardAnalysis, Extracted, Inferred, Visual

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
IN_PATH = DATA_DIR / "outdoor_2024_extractions.jsonl"
OUT_PATH = DATA_DIR / "outdoor_2024_with_rationale.jsonl"


def load_inputs() -> list[dict]:
    items: list[dict] = []
    with IN_PATH.open() as f:
        for line in f:
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not d.get("error"):
                items.append(d)
    return items


def already_done() -> set[str]:
    if not OUT_PATH.exists():
        return set()
    done: set[str] = set()
    with OUT_PATH.open() as f:
        for line in f:
            try:
                d = json.loads(line)
                if d.get("why_it_won"):
                    done.add(d["id"])
            except json.JSONDecodeError:
                continue
    return done


def process_one(record: dict) -> dict:
    try:
        extracted = Extracted(**record["extracted"])
        inferred = Inferred(**record["inferred"])
        visual = Visual(**record["visual"])
        why = generate_why_it_won(
            extracted=extracted,
            inferred=inferred,
            visual=visual,
            tier=record["tier"],
            criteria=OUTDOOR_CRITERIA,
            expected_range_fn=expected_score_range,
            tier_consistency_fn=tier_consistency,
        )
        enriched = dict(record)
        enriched["why_it_won"] = why.model_dump()
        # Round-trip through BoardAnalysis to validate.
        BoardAnalysis(**enriched)
        return enriched
    except Exception as e:  # noqa: BLE001
        return {
            "id": record.get("id"),
            "file_path": record.get("file_path"),
            "tier": record.get("tier"),
            "error": f"{type(e).__name__}: {e}",
        }


def print_summary() -> None:
    if not OUT_PATH.exists():
        print(f"No file at {OUT_PATH}")
        return
    records = [json.loads(line) for line in OUT_PATH.open() if line.strip()]
    ok = [r for r in records if not r.get("error") and r.get("why_it_won")]
    errors = [r for r in records if r.get("error")]
    print(f"\nTotal: {len(records)} ({len(ok)} ok, {len(errors)} errors)")
    if not ok:
        return

    # By tier — consistency and score stats
    print("\n=== Score statistics by tier ===")
    by_tier_scores: dict[str, list[float]] = {}
    for r in ok:
        by_tier_scores.setdefault(r["tier"], []).append(r["why_it_won"]["weighted_score"])
    for tier in ["Grand Prix", "Gold", "Silver", "Bronze", "Shortlist", "Loser"]:
        ss = by_tier_scores.get(tier)
        if not ss:
            continue
        stat_line = f"  {tier:11s}  n={len(ss):3d}  min={min(ss):.1f}  mean={mean(ss):.1f}  max={max(ss):.1f}"
        if len(ss) > 1:
            stat_line += f"  std={stdev(ss):.1f}"
        print(stat_line)

    # Spread by axis (intra-tier)
    print("\n=== Per-axis std-dev within each tier (discrimination check) ===")
    for tier in ["Gold", "Silver", "Bronze", "Shortlist"]:
        recs = [r for r in ok if r["tier"] == tier]
        if len(recs) < 3:
            continue
        line = f"  {tier:10s}  "
        for axis in ["idea", "strategy", "execution", "impact"]:
            scores = [r["why_it_won"][axis]["score"] for r in recs]
            line += f"{axis}={stdev(scores):4.1f}  "
        print(line)

    # Sample one verdict per tier
    print("\n=== Sample verdicts ===")
    seen: set[str] = set()
    for r in ok:
        if r["tier"] in seen:
            continue
        seen.add(r["tier"])
        w = r["why_it_won"]
        print(f"\n  [{r['tier']:11s}] {r['id'][:65]}")
        print(f"    one-liner: {r['inferred']['one_liner']}")
        print(
            f"    scores: I={w['idea']['score']}  S={w['strategy']['score']}  "
            f"E={w['execution']['score']}  R={w['impact']['score']}  → {w['weighted_score']:.1f}  ({w['tier_consistency']})"
        )
        print(f"    verdict: {w['verdict']}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    if args.summary:
        print_summary()
        return

    inputs = load_inputs()
    done = already_done()
    todo = [r for r in inputs if r["id"] not in done]
    if args.limit:
        todo = todo[: args.limit]

    print(f"Inputs:       {len(inputs)}")
    print(f"Already done: {len(done)}")
    print(f"To do:        {len(todo)}")
    if not todo:
        print_summary()
        return

    t0 = perf_counter()
    with OUT_PATH.open("a") as out_f:
        if args.workers <= 1:
            for r in tqdm(todo, desc="Rationale"):
                rec = process_one(r)
                out_f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                out_f.flush()
        else:
            with ThreadPoolExecutor(max_workers=args.workers) as pool:
                futures = {pool.submit(process_one, r): r for r in todo}
                for fut in tqdm(as_completed(futures), total=len(futures), desc="Rationale"):
                    rec = fut.result()
                    out_f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    out_f.flush()

    elapsed = perf_counter() - t0
    print(f"\nDone in {elapsed:.0f}s ({elapsed / max(len(todo), 1):.1f}s per board)")
    print_summary()


if __name__ == "__main__":
    main()
