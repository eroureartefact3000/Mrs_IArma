"""Extract the v3 schema on every Outdoor 2024 board (winners + shortlist + losers).

Walks `2024/OUTDOOR/{GRAND PRIX, GOLD, SILVER, BRONZE, SHORTLIST}/` plus the
Outdoor-flavoured boards in `2024/loser/`. Writes results to
`data/outdoor_2024_extractions.jsonl` line-by-line (resumable).

Cost estimate: ~$35-40 for ~120 boards. Runtime ~7-8 min with 4 workers.
"""
from __future__ import annotations

import argparse
import json
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
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)
OUT_PATH = DATA_DIR / "outdoor_2024_extractions.jsonl"

# Folder name -> canonical Tier value
FOLDER_TO_TIER = {
    "GRAND PRIX": "Grand Prix",
    "GOLD": "Gold",
    "SILVER": "Silver",
    "BRONZE": "Bronze",
    "SHORTLIST": "Shortlist",
}

SUPPORTED_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".avif", ".gif"}

# Manually-curated: which files in /loser are Outdoor in nature.
# KitKat Break Chair is clearly outdoor (installation/chair in public space).
# IKEA Supporting First Steps (INGO Hamburg) is most likely ambient/outdoor.
OUTDOOR_LOSERS = [
    "The KitKat Break Chair - VML Sydney.avif",
    "Supporting First Steps - IKEA - INGO Hamburg.png",
]


def slug(filename: str) -> str:
    stem = Path(filename).stem.lower()
    for ch in (" ", "–", "(", ")", "/", "_", ",", "."):
        stem = stem.replace(ch, "-")
    while "--" in stem:
        stem = stem.replace("--", "-")
    return stem.strip("-")[:80]


def list_targets() -> list[dict]:
    """Return a list of {tier, file_path, filename} for all Outdoor 2024 boards."""
    targets: list[dict] = []
    outdoor_dir = ROOT / "2024" / "OUTDOOR"
    for folder, tier in FOLDER_TO_TIER.items():
        tier_dir = outdoor_dir / folder
        if not tier_dir.exists():
            continue
        for p in sorted(tier_dir.iterdir()):
            if p.suffix.lower() in SUPPORTED_EXTS and not p.name.startswith("."):
                targets.append(
                    {
                        "tier": tier,
                        "file_path": str(p.relative_to(ROOT)),
                        "filename": p.name,
                    }
                )

    loser_dir = ROOT / "2024" / "loser"
    for name in OUTDOOR_LOSERS:
        p = loser_dir / name
        if p.exists():
            targets.append(
                {
                    "tier": "Loser",
                    "file_path": str(p.relative_to(ROOT)),
                    "filename": p.name,
                }
            )

    return targets


def already_done() -> set[str]:
    if not OUT_PATH.exists():
        return set()
    done: set[str] = set()
    with OUT_PATH.open() as f:
        for line in f:
            try:
                d = json.loads(line)
                done.add(d.get("file_path", ""))
            except json.JSONDecodeError:
                continue
    return done


def extract_one(target: dict) -> dict:
    rel_path = target["file_path"]
    path = ROOT / rel_path
    try:
        extracted = extract_pass1(path)
        inferred, visual = extract_pass2(path, extracted)
        impact = compute_impact_strength(extracted, inferred)
        flag, reasons = flag_for_review(extracted, inferred)
        analysis = BoardAnalysis(
            id=slug(target["filename"]),
            tier=target["tier"],  # type: ignore[arg-type]
            category="Outdoor",
            category_confidence="high",
            category_reasoning="Sourced from 2024/OUTDOOR folder (pre-classified by dataset).",
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
        print(f"No file at {OUT_PATH}")
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
        print("Errors:")
        for e in errors[:10]:
            print(f"  - {e.get('filename', '?')[:60]}: {e.get('error', '?')[:100]}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more")
    if not ok:
        return
    by_tier = Counter(r["tier"] for r in ok)
    print("\nBy tier:")
    for t in ["Grand Prix", "Gold", "Silver", "Bronze", "Shortlist", "Loser"]:
        if by_tier.get(t):
            print(f"  {t:11s} {by_tier[t]:3d}")
    by_impact = Counter(r["impact_strength"] for r in ok)
    print("\nImpact strength:")
    for k in ["strong", "moderate", "qualitative_only", "none"]:
        if by_impact.get(k):
            print(f"  {k:18s} {by_impact[k]:3d}")
    flagged = [r for r in ok if r["review_flag"]]
    print(f"\nFlagged for review: {len(flagged)} / {len(ok)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--limit", type=int, default=None, help="for smoke testing")
    args = parser.parse_args()

    if args.summary:
        print_summary()
        return

    targets = list_targets()
    done = already_done()
    todo = [t for t in targets if t["file_path"] not in done]
    if args.limit:
        todo = todo[: args.limit]

    print(f"Outdoor targets:  {len(targets)}")
    print(f"Already done:     {len(done)}")
    print(f"To do this run:   {len(todo)}")
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
