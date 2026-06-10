"""Category-generic inventory script.

Walks 2024/<CATEGORY_FOLDER>/{GRAND PRIX, GOLD, SILVER, BRONZE, SHORTLIST}/ and
produces:
  - data_internal/<category_key>_inventory.json
  - Console preview of subagent batching

Usage:
    uv run python scripts/inventory_boards.py --category Design [--batches 3]
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Map registry key → source folder under 2024/  (case-sensitive on disk).
# Note: "CREATIVE DATA " on disk has a trailing space.
CATEGORY_DIRS: dict[str, str] = {
    "Outdoor": "OUTDOOR",
    "PR": "PR",
    "Print & Publishing": "PRINT&PUBLISHING",
    "Design": "DESIGN",
    "Direct": "DIRECT",
    "Industry Craft": "INDUSTRY CRAFT",
    "Media": "MEDIA",
    "Brand Experience & Activation": "BRAND EXPERIENCE & ACTIVATION",
    "Health & Wellness": "HEALTH & WELLNESS",
    "Sustainable Development Goals": "SUSTAINABLE DEVELOPMENT GOALS",
    "Entertainment Lions for Sport": "ENTERTAINMENT LIONS FOR SPORT",
    "Entertainment": "ENTERTAINMENT",
    "Social & Influencer": "SOCIAL & INFLUENCER",
    "Film": "FILM",
    "Creative Strategy": "CREATIVE STRATEGY",
    # Wave 2 — remaining 15 categories
    "Audio & Radio": "AUDIO&RADIO",
    "Digital Craft": "DIGITAL CRAFT",
    "Film Craft": "FILM CRAFT",
    "Creative B2B": "CREATIVE B2B",
    "Creative Data": "CREATIVE DATA",
    "Creative Commerce": "CREATIVE COMMERCE",
    "Creative Effectiveness": "CREATIVE EFFECTIVENESS",
    "Entertainment for Gaming": "ENTERTAINMENT LIONS FOR GAMING",
    "Entertainment for Music": "ENTERTAINMENT LIONS FOR MUSIC",
    "Creative Business Transformation": "CREATIVE BUSINESS TRANSFORMATION",
    "Innovation": "INNOVATION",
    "Luxury": "LUXURY & LIFESTYLE",
    "Glass (The Lion for Change)": "GLASS - THE LION FOR CHANGE",
    "Pharma": "PHARMA",
    "Titanium": "TITANIUM",
}


# Map registry key → short slug used in file paths & registry
CATEGORY_SLUG: dict[str, str] = {
    "Outdoor": "outdoor",
    "PR": "pr",
    "Print & Publishing": "print",
    "Design": "design",
    "Direct": "direct",
    "Industry Craft": "industry_craft",
    "Media": "media",
    "Brand Experience & Activation": "bxa",
    "Health & Wellness": "health",
    "Sustainable Development Goals": "sdg",
    "Entertainment Lions for Sport": "ent_sport",
    "Entertainment": "entertainment",
    "Social & Influencer": "social",
    "Film": "film",
    "Creative Strategy": "creative_strategy",
    # Wave 2
    "Audio & Radio": "audio_radio",
    "Digital Craft": "digital_craft",
    "Film Craft": "film_craft",
    "Creative B2B": "creative_b2b",
    "Creative Data": "creative_data",
    "Creative Commerce": "creative_commerce",
    "Creative Effectiveness": "creative_effectiveness",
    "Entertainment for Gaming": "ent_gaming",
    "Entertainment for Music": "ent_music",
    "Creative Business Transformation": "creative_bt",
    "Innovation": "innovation",
    "Luxury": "luxury",
    "Glass (The Lion for Change)": "glass",
    "Pharma": "pharma",
    "Titanium": "titanium",
}


FOLDER_TO_TIER = {
    "GRAND PRIX": "Grand Prix",
    "GOLD": "Gold",
    "SILVER": "Silver",
    "BRONZE": "Bronze",
    "SHORTLIST": "Shortlist",
}
SUPPORTED_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".avif", ".gif"}
_TIER_RANK = {"Grand Prix": 5, "Gold": 4, "Silver": 3, "Bronze": 2, "Shortlist": 1}


def slug_of(filename: str) -> str:
    stem = Path(filename).stem.lower()
    for ch in (" ", "–", "(", ")", "/", "_", ",", ".", "'", "’", "&", "?"):
        stem = stem.replace(ch, "-")
    while "--" in stem:
        stem = stem.replace("--", "-")
    return stem.strip("-")[:80]


def collect_boards(category_dir: Path) -> list[dict]:
    boards: list[dict] = []
    for folder, tier in FOLDER_TO_TIER.items():
        tier_dir = category_dir / folder
        if not tier_dir.exists():
            continue
        for p in sorted(tier_dir.iterdir()):
            if p.suffix.lower() not in SUPPORTED_EXTS:
                continue
            if p.name.startswith("."):
                continue
            boards.append({
                "tier": tier,
                "filename": p.name,
                "slug": slug_of(p.name),
                "file_path": str(p.relative_to(ROOT)),
            })
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
    parser.add_argument("--category", required=True, help="Registry key, e.g. 'Design'")
    parser.add_argument("--batches", type=int, default=3)
    args = parser.parse_args()

    cat_key = args.category
    if cat_key not in CATEGORY_DIRS:
        raise SystemExit(f"Unknown category '{cat_key}'. Known: {sorted(CATEGORY_DIRS.keys())}")

    cat_dir = ROOT / "2024" / CATEGORY_DIRS[cat_key]
    if not cat_dir.exists():
        raise SystemExit(f"Source dir does not exist: {cat_dir}")

    cat_slug = CATEGORY_SLUG[cat_key]
    out_path = ROOT / "data_internal" / f"{cat_slug}_inventory.json"

    boards = collect_boards(cat_dir)
    print(f"Total {cat_key} boards: {len(boards)}")
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

    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "category": cat_key,
        "category_slug": cat_slug,
        "total": len(boards),
        "by_tier": dict(counts),
        "boards": boards,
        "batches": batches,
    }
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    print(f"\nWrote {out_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
