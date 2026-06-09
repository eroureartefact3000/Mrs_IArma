"""Generate the dispatching inventory for the Print & Publishing pilot.

Walks 2024/PRINT&PUBLISHING/{GRAND PRIX, GOLD, SILVER, BRONZE, SHORTLIST}/ and
produces:
  - data_internal/print_inventory.json — a single source of truth for the boards
    with their canonical slug + tier + file_path
  - A console preview of how the boards will be batched across N subagents
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PRINT_DIR = ROOT / "2024" / "PRINT&PUBLISHING"
OUT_PATH = ROOT / "data_internal" / "print_inventory.json"

FOLDER_TO_TIER = {
    "GRAND PRIX": "Grand Prix",
    "GOLD": "Gold",
    "SILVER": "Silver",
    "BRONZE": "Bronze",
    "SHORTLIST": "Shortlist",
}

SUPPORTED_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".avif", ".gif"}


def slug_of(filename: str) -> str:
    stem = Path(filename).stem.lower()
    for ch in (" ", "–", "(", ")", "/", "_", ",", ".", "'", "’", "&", "?"):
        stem = stem.replace(ch, "-")
    while "--" in stem:
        stem = stem.replace("--", "-")
    return stem.strip("-")[:80]


def collect_boards() -> list[dict]:
    boards: list[dict] = []
    for folder, tier in FOLDER_TO_TIER.items():
        tier_dir = PRINT_DIR / folder
        if not tier_dir.exists():
            continue
        for p in sorted(tier_dir.iterdir()):
            if p.suffix.lower() not in SUPPORTED_EXTS:
                continue
            if p.name.startswith("."):
                continue
            boards.append(
                {
                    "tier": tier,
                    "filename": p.name,
                    "slug": slug_of(p.name),
                    "file_path": str(p.relative_to(ROOT)),
                }
            )
    return boards


def make_batches(boards: list[dict], n_batches: int) -> list[list[dict]]:
    tier_order = list(FOLDER_TO_TIER.values())
    by_tier_then_name = sorted(boards, key=lambda b: (tier_order.index(b["tier"]), b["filename"]))
    batches: list[list[dict]] = [[] for _ in range(n_batches)]
    for i, b in enumerate(by_tier_then_name):
        batches[i % n_batches].append(b)
    return batches


def check_duplicate_slugs(boards: list[dict]) -> list[tuple[str, list[dict]]]:
    by_slug: dict[str, list[dict]] = {}
    for b in boards:
        by_slug.setdefault(b["slug"], []).append(b)
    return [(s, bs) for s, bs in by_slug.items() if len(bs) > 1]


_TIER_RANK = {"Grand Prix": 5, "Gold": 4, "Silver": 3, "Bronze": 2, "Shortlist": 1}


def deduplicate_keep_highest_tier(boards: list[dict]) -> list[dict]:
    best_by_slug: dict[str, dict] = {}
    duplicate_map: dict[str, list[str]] = {}
    for b in boards:
        slug = b["slug"]
        existing = best_by_slug.get(slug)
        if existing is None:
            best_by_slug[slug] = b
            duplicate_map[slug] = [b["tier"]]
        else:
            duplicate_map[slug].append(b["tier"])
            if _TIER_RANK.get(b["tier"], 0) > _TIER_RANK.get(existing["tier"], 0):
                best_by_slug[slug] = b
    out: list[dict] = []
    for slug, b in best_by_slug.items():
        all_tiers = duplicate_map[slug]
        other_tiers = [t for t in all_tiers if t != b["tier"]]
        b = dict(b)
        if other_tiers:
            b["also_placed_at"] = sorted(set(other_tiers), key=lambda t: -_TIER_RANK.get(t, 0))
        out.append(b)
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batches", type=int, default=3, help="number of subagent batches to plan")
    args = parser.parse_args()

    boards = collect_boards()
    print(f"Total Print boards: {len(boards)}")
    print()
    counts = Counter(b["tier"] for b in boards)
    for t in FOLDER_TO_TIER.values():
        print(f"  {t:11s}: {counts.get(t, 0)}")

    dups = check_duplicate_slugs(boards)
    if dups:
        print(f"\n⚠️  {len(dups)} duplicate slugs detected.")
        boards = deduplicate_keep_highest_tier(boards)
        print(f"   After dedup: {len(boards)} boards.")
        counts = Counter(b["tier"] for b in boards)
        print("   New per-tier counts:")
        for t in FOLDER_TO_TIER.values():
            print(f"     {t:11s}: {counts.get(t, 0)}")
        for b in boards:
            if "also_placed_at" in b:
                others = ", ".join(b["also_placed_at"])
                print(f"     [{b['tier']:10s}] {b['slug'][:60]}  (also: {others})")
    else:
        print("\n✓ No duplicate slugs.")

    batches = make_batches(boards, args.batches)
    print(f"\nBatches (n={args.batches}):")
    for i, batch in enumerate(batches, start=1):
        tiers = Counter(b["tier"] for b in batch)
        tier_str = ", ".join(f"{t}={tiers[t]}" for t in FOLDER_TO_TIER.values() if tiers[t])
        print(f"  Batch {i}: {len(batch):3d} boards  ({tier_str})")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "total": len(boards),
        "by_tier": dict(counts),
        "boards": boards,
        "batches": batches,
    }
    OUT_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    print(f"\nWrote {OUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
