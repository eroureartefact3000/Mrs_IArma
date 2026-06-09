"""Pre-classify all winning boards in 2025/ into Cannes Lions categories.

Walks Grand Prix / Gold / Silver / Bronze, runs the classifier on each board,
and saves results to data/categories.jsonl line-by-line so we can resume on crash.

Cost: ~$7-12 for 358 boards (~$0.02-0.03 per call).
Runtime: ~30 min sequential. Use --workers N for parallelism.

Usage:
    uv run python classify_all.py             # sequential
    uv run python classify_all.py --workers 4 # 4 parallel workers
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

from pipeline.classifier import classify

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data_internal"
DATA_DIR.mkdir(exist_ok=True)
OUT_PATH = DATA_DIR / "categories.jsonl"

TIERS = ["Grand Prix", "Gold", "Silver", "Bronze"]
SUPPORTED_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".avif", ".gif"}


def list_boards() -> list[tuple[str, Path]]:
    boards: list[tuple[str, Path]] = []
    for tier in TIERS:
        tier_dir = ROOT / "2025" / tier
        if not tier_dir.exists():
            continue
        for p in sorted(tier_dir.iterdir()):
            if p.suffix.lower() in SUPPORTED_EXTS and not p.name.startswith("."):
                boards.append((tier, p))
    return boards


def already_done(out_path: Path) -> set[str]:
    if not out_path.exists():
        return set()
    done = set()
    with out_path.open() as f:
        for line in f:
            try:
                d = json.loads(line)
                done.add(d["file_path"])
            except json.JSONDecodeError:
                continue
    return done


def classify_one(tier: str, path: Path) -> dict:
    rel_path = str(path.relative_to(ROOT))
    try:
        cls = classify(path)
        return {
            "tier": tier,
            "file_path": rel_path,
            "filename": path.name,
            "category": cls.get("category"),
            "confidence": cls.get("confidence"),
            "reasoning": cls.get("reasoning"),
        }
    except Exception as e:  # noqa: BLE001
        return {
            "tier": tier,
            "file_path": rel_path,
            "filename": path.name,
            "category": None,
            "error": f"{type(e).__name__}: {e}",
        }


def print_distribution() -> None:
    counts: Counter[str] = Counter()
    errors = 0
    with OUT_PATH.open() as f:
        for line in f:
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            if d.get("error"):
                errors += 1
                continue
            counts[d.get("category", "?")] += 1

    print("\nCategory distribution:")
    for cat, n in counts.most_common():
        pct = 100 * n / max(sum(counts.values()), 1)
        marker = " ← PR" if cat == "PR" else ""
        print(f"  {n:4d}  ({pct:5.1f}%)  {cat}{marker}")
    if errors:
        print(f"  {errors:4d}  errors")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=1, help="parallel workers (default 1)")
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="just print the distribution from existing categories.jsonl",
    )
    args = parser.parse_args()

    if args.summary_only:
        if not OUT_PATH.exists():
            print(f"No file at {OUT_PATH}", file=sys.stderr)
            sys.exit(1)
        print_distribution()
        return

    all_boards = list_boards()
    done = already_done(OUT_PATH)
    todo = [(t, p) for (t, p) in all_boards if str(p.relative_to(ROOT)) not in done]

    print(f"Total boards: {len(all_boards)}")
    print(f"Already done: {len(done)}")
    print(f"To do      : {len(todo)}")
    if not todo:
        print_distribution()
        return

    t0 = perf_counter()
    with OUT_PATH.open("a") as out_f:
        if args.workers <= 1:
            for tier, path in tqdm(todo, desc="Classifying"):
                record = classify_one(tier, path)
                out_f.write(json.dumps(record, ensure_ascii=False) + "\n")
                out_f.flush()
        else:
            with ThreadPoolExecutor(max_workers=args.workers) as pool:
                futures = {pool.submit(classify_one, t, p): (t, p) for t, p in todo}
                for fut in tqdm(as_completed(futures), total=len(futures), desc="Classifying"):
                    record = fut.result()
                    out_f.write(json.dumps(record, ensure_ascii=False) + "\n")
                    out_f.flush()

    elapsed = perf_counter() - t0
    print(f"\nDone in {elapsed:.0f}s ({elapsed / max(len(todo), 1):.1f}s per board)")
    print_distribution()


if __name__ == "__main__":
    main()
