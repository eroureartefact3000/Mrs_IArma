"""Extract the v3 schema on every board classified as PR.

Reads data/categories.jsonl, filters to category == "PR", runs the two-pass
extractor on each, writes results to data/pr_extractions.jsonl line-by-line so
the run is resumable if anything crashes.

Cost: ~$20 for 65 boards (~$0.30 per board).
Runtime: ~22 min sequential, ~6 min with 4 workers.

Usage:
    uv run python extract_all_pr.py             # sequential
    uv run python extract_all_pr.py --workers 4 # parallel
    uv run python extract_all_pr.py --summary   # just print stats from existing jsonl
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

from pipeline.extractor import (
    compute_impact_strength,
    extract_pass1,
    extract_pass2,
    flag_for_review,
)
from pipeline.schema import BoardAnalysis

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data_internal"
DATA_DIR.mkdir(exist_ok=True)
CATEGORIES_PATH = DATA_DIR / "categories.jsonl"
OUT_PATH = DATA_DIR / "pr_extractions.jsonl"


def slug(filename: str) -> str:
    return (
        Path(filename).stem.lower()
        .replace(" ", "-")
        .replace("–", "-")
        .replace("(", "")
        .replace(")", "")[:80]
    )


def load_pr_targets() -> list[dict]:
    targets: list[dict] = []
    with CATEGORIES_PATH.open() as f:
        for line in f:
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            if d.get("category") == "PR" and not d.get("error"):
                targets.append(d)
    return targets


def already_done() -> set[str]:
    if not OUT_PATH.exists():
        return set()
    done = set()
    with OUT_PATH.open() as f:
        for line in f:
            try:
                d = json.loads(line)
                done.add(d.get("file_path", ""))
            except json.JSONDecodeError:
                continue
    return done


def extract_one(target: dict) -> dict:
    """Run the full extraction on one PR board. Returns a BoardAnalysis dict or an error record."""
    rel_path = target["file_path"]
    path = ROOT / rel_path
    try:
        extracted = extract_pass1(path)
        inferred, visual = extract_pass2(path, extracted)
        impact = compute_impact_strength(extracted, inferred)
        flag, reasons = flag_for_review(extracted, inferred)
        analysis = BoardAnalysis(
            id=slug(target["filename"]),
            tier=target["tier"],
            category=target["category"],
            category_confidence=target.get("confidence", "high"),
            category_reasoning=target.get("reasoning"),
            file_path=rel_path,
            extracted=extracted,
            inferred=inferred,
            visual=visual,
            impact_strength=impact,
            review_flag=flag,
            review_reasons=reasons,
        )
        return analysis.model_dump()
    except Exception as e:  # noqa: BLE001
        return {
            "file_path": rel_path,
            "tier": target["tier"],
            "filename": target["filename"],
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

    ok = [r for r in records if not r.get("error")]
    errors = [r for r in records if r.get("error")]

    print(f"\nTotal records: {len(records)} ({len(ok)} ok, {len(errors)} errors)")

    if errors:
        print("\nErrors:")
        for e in errors[:10]:
            print(f"  - {e.get('filename', '?')[:60]}: {e.get('error', '?')[:100]}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more")

    if not ok:
        return

    # Distribution by tier
    print("\nBy tier:")
    by_tier = Counter(r["tier"] for r in ok)
    for t in ["Grand Prix", "Gold", "Silver", "Bronze"]:
        print(f"  {t:11s} {by_tier.get(t, 0):3d}")

    # Impact strength distribution
    print("\nImpact strength:")
    by_impact = Counter(r["impact_strength"] for r in ok)
    for k in ["strong", "moderate", "qualitative_only", "none"]:
        print(f"  {k:18s} {by_impact.get(k, 0):3d}")

    # Flag stats
    flagged = [r for r in ok if r["review_flag"]]
    print(f"\nFlagged for review: {len(flagged)} / {len(ok)}")
    for r in flagged[:5]:
        print(f"  ⚠️  [{r['tier']}] {r['id'][:50]}: {r['review_reasons']}")
    if len(flagged) > 5:
        print(f"  ... and {len(flagged) - 5} more")

    # One-liner concision
    print("\nOne-liner concision:")
    word_counts = []
    over_12 = 0
    for r in ok:
        ol = r["inferred"]["one_liner"] or ""
        words = len(ol.split())
        word_counts.append(words)
        if words > 12:
            over_12 += 1
    if word_counts:
        avg = sum(word_counts) / len(word_counts)
        print(f"  Avg words: {avg:.1f}, over 12 words: {over_12} / {len(word_counts)}")

    # Sample of creative mechanisms (top 15)
    mech_counter: Counter[str] = Counter()
    for r in ok:
        for m in r["inferred"]["creative_mechanisms"]:
            mech_counter[m] += 1
    print("\nTop creative mechanisms:")
    for m, n in mech_counter.most_common(15):
        print(f"  {n:3d}  {m}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--summary", action="store_true", help="just print stats from existing jsonl")
    args = parser.parse_args()

    if args.summary:
        print_summary()
        return

    targets = load_pr_targets()
    done = already_done()
    todo = [t for t in targets if t["file_path"] not in done]

    print(f"PR targets:   {len(targets)}")
    print(f"Already done: {len(done)}")
    print(f"To do:        {len(todo)}")

    if not todo:
        print_summary()
        return

    t0 = perf_counter()
    with OUT_PATH.open("a") as out_f:
        if args.workers <= 1:
            for t in tqdm(todo, desc="Extracting"):
                rec = extract_one(t)
                out_f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                out_f.flush()
        else:
            with ThreadPoolExecutor(max_workers=args.workers) as pool:
                futures = {pool.submit(extract_one, t): t for t in todo}
                for fut in tqdm(as_completed(futures), total=len(futures), desc="Extracting"):
                    rec = fut.result()
                    out_f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    out_f.flush()

    elapsed = perf_counter() - t0
    print(f"\nDone in {elapsed:.0f}s ({elapsed / max(len(todo), 1):.1f}s per board)")
    print_summary()


if __name__ == "__main__":
    main()
