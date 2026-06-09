"""Category-generic RAG index builder.

Reads per-board extractions from `data_internal/extractions/<slug>/` and per-winner
rationales from `data_internal/rationales/<slug>/`, merges them, embeds via Voyage,
and writes:

    data/<slug>_index.npy           — float32 matrix (n_winners × 1024)
    data/<slug>_index_meta.jsonl

Only boards with a rationale (= medal winners) are indexed.

Usage:
    uv run python scripts/build_index.py --category Design
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from time import perf_counter

import numpy as np

from pipeline.embeddings import DIM, embed_documents
from pipeline.search_doc import build_search_document

# Import the category → slug map from inventory_boards to keep them in sync
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from inventory_boards import CATEGORY_SLUG  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"


def load_merged_records(slug: str) -> list[dict]:
    ext_dir = ROOT / "data_internal" / "extractions" / slug
    rat_dir = ROOT / "data_internal" / "rationales" / slug
    records: list[dict] = []
    skipped = 0
    for ext_path in sorted(ext_dir.glob("*.json")):
        ext = json.loads(ext_path.read_text())
        board_slug = ext_path.stem
        rat_path = rat_dir / f"{board_slug}.json"
        if not rat_path.exists():
            skipped += 1
            continue
        rat = json.loads(rat_path.read_text())
        ext["why_it_won"] = rat
        records.append(ext)
    print(f"Loaded {len(records)} winners (skipped {skipped} boards without rationale)")
    return records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--category", required=True, help="Registry key, e.g. 'Design'")
    args = parser.parse_args()

    if args.category not in CATEGORY_SLUG:
        raise SystemExit(f"Unknown category '{args.category}'. Known: {sorted(CATEGORY_SLUG.keys())}")
    cat_slug = CATEGORY_SLUG[args.category]

    embeddings_path = DATA_DIR / f"{cat_slug}_index.npy"
    meta_path = DATA_DIR / f"{cat_slug}_index_meta.jsonl"

    records = load_merged_records(cat_slug)
    assert records, f"No {args.category} winners found — aborting."

    docs = [build_search_document(r) for r in records]
    nonempty = sum(1 for d in docs if d)
    print(f"Built {nonempty}/{len(docs)} search documents (non-empty)")

    print("\nSample search document (row 0):")
    print("---")
    print(docs[0])
    print("---")

    t0 = perf_counter()
    embeddings = embed_documents(docs)
    elapsed = perf_counter() - t0
    matrix = np.asarray(embeddings, dtype=np.float32)
    print(f"\nEmbedded {len(embeddings)} docs in {elapsed:.1f}s — shape {matrix.shape}")
    assert matrix.shape[1] == DIM, f"Expected dim {DIM}, got {matrix.shape[1]}"

    DATA_DIR.mkdir(exist_ok=True)
    np.save(embeddings_path, matrix)
    with meta_path.open("w") as f:
        for i, r in enumerate(records):
            entry = {
                "row": i,
                "id": r["id"],
                "tier": r["tier"],
                "category": r["category"],
                "campaign": (r.get("extracted") or {}).get("campaign"),
                "brand": (r.get("extracted") or {}).get("brand"),
                "one_liner": (r.get("inferred") or {}).get("one_liner"),
                "weighted_score": r["why_it_won"]["weighted_score"],
                "search_doc": docs[i],
                "full_record": r,
            }
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    size_mb = embeddings_path.stat().st_size / (1024 * 1024)
    print(f"\nSaved index:")
    print(f"  {embeddings_path}  ({size_mb:.2f} MB)")
    print(f"  {meta_path}")


if __name__ == "__main__":
    main()
