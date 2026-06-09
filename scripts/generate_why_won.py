"""Generate a 'why-it-won' rationale for every PR board already extracted.

Reads data/pr_extractions.jsonl, runs the rationale generator on each entry,
writes the enriched analyses to data/pr_with_rationale.jsonl. Resumable.

Cost: ~$15-20 for 65 boards (~$0.25 per call, text-only).
Runtime: ~10 min with 4 workers.

Usage:
    uv run python generate_why_won.py             # sequential
    uv run python generate_why_won.py --workers 4 # parallel
    uv run python generate_why_won.py --summary   # just analyse existing output
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from time import perf_counter

from tqdm import tqdm

from pipeline.pr_criteria import PR_CRITERIA, expected_score_range, tier_consistency
from pipeline.rationale import generate_why_it_won
from pipeline.schema import BoardAnalysis, Extracted, Inferred, Visual

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data_internal"
DATA_DIR.mkdir(exist_ok=True)
IN_PATH = DATA_DIR / "pr_extractions.jsonl"
OUT_PATH = DATA_DIR / "pr_with_rationale.jsonl"


def load_inputs() -> list[dict]:
    items: list[dict] = []
    with IN_PATH.open() as f:
        for line in f:
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            if d.get("error"):
                continue
            items.append(d)
    return items


def already_done() -> set[str]:
    if not OUT_PATH.exists():
        return set()
    done = set()
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
            criteria=PR_CRITERIA,
            expected_range_fn=lambda t: expected_score_range(t) if t in {"Grand Prix", "Gold", "Silver", "Bronze"} else None,  # type: ignore[arg-type]
            tier_consistency_fn=tier_consistency,
        )
        enriched = dict(record)
        enriched["why_it_won"] = why.model_dump()
        # Round-trip through BoardAnalysis to ensure schema-compliance.
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
        print(f"No file at {OUT_PATH}", file=sys.stderr)
        return

    records: list[dict] = []
    with OUT_PATH.open() as f:
        for line in f:
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    ok = [r for r in records if not r.get("error") and r.get("why_it_won")]
    errors = [r for r in records if r.get("error")]

    print(f"\nTotal: {len(records)} ({len(ok)} ok, {len(errors)} errors)")
    if errors:
        print("\nErrors:")
        for e in errors[:5]:
            print(f"  - {e.get('id', '?')[:60]}: {e.get('error', '?')[:100]}")
        if len(errors) > 5:
            print(f"  ... and {len(errors) - 5} more")

    if not ok:
        return

    # Tier consistency
    print("\n=== Tier consistency (how well scores match tier expectations) ===")
    consistency_by_tier: dict[str, Counter[str]] = {}
    for r in ok:
        t = r["tier"]
        c = r["why_it_won"]["tier_consistency"]
        consistency_by_tier.setdefault(t, Counter())[c] += 1
    for tier in ["Grand Prix", "Gold", "Silver", "Bronze"]:
        if tier not in consistency_by_tier:
            continue
        counts = consistency_by_tier[tier]
        total = sum(counts.values())
        line = f"  {tier:11s} (n={total}): "
        parts = []
        for status in ["expected", "below", "above"]:
            if counts[status]:
                parts.append(f"{status}={counts[status]}")
        print(line + "  ".join(parts))

    # Score distribution by tier
    print("\n=== Weighted score statistics by tier ===")
    scores_by_tier: dict[str, list[float]] = {}
    for r in ok:
        scores_by_tier.setdefault(r["tier"], []).append(r["why_it_won"]["weighted_score"])
    for tier in ["Grand Prix", "Gold", "Silver", "Bronze"]:
        ss = scores_by_tier.get(tier)
        if not ss:
            continue
        print(f"  {tier:11s}  min={min(ss):.1f}  mean={sum(ss) / len(ss):.1f}  max={max(ss):.1f}  (n={len(ss)})")

    # 3 sample verdicts (one per tier ideally)
    print("\n=== Sample verdicts ===")
    seen_tiers: set[str] = set()
    for r in ok:
        if r["tier"] in seen_tiers:
            continue
        seen_tiers.add(r["tier"])
        w = r["why_it_won"]
        print(f"\n  [{r['tier']:11s}] {r['id'][:60]}")
        print(f"    one_liner: {r['inferred']['one_liner']}")
        print(f"    scores: idea={w['idea']['score']}  strategy={w['strategy']['score']}  execution={w['execution']['score']}  impact={w['impact']['score']}  → {w['weighted_score']:.1f}  ({w['tier_consistency']})")
        print(f"    verdict: {w['verdict']}")
        if len(seen_tiers) == 4:
            break


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()

    if args.summary:
        print_summary()
        return

    inputs = load_inputs()
    done = already_done()
    todo = [r for r in inputs if r["id"] not in done]

    print(f"PR inputs:    {len(inputs)}")
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
