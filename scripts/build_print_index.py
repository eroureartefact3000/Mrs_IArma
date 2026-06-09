"""Build the vector index for the Print & Publishing 2024 winners.

Reads per-board extractions from `data_internal/extractions/print/` and per-winner
rationales from `data_internal/rationales/print/`, merges them, embeds via Voyage,
and writes:

    data/print_index.npy           — float32 matrix (n_winners × 1024)
    data/print_index_meta.jsonl    — one JSON line per board

Only boards with a rationale (= medal winners) are indexed.

Usage:
    uv run python scripts/build_print_index.py
"""
from __future__ import annotations

import json
from pathlib import Path
from time import perf_counter

import numpy as np

from pipeline.embeddings import DIM, embed_documents
from pipeline.search_doc import build_search_document

ROOT = Path(__file__).resolve().parent.parent
EXTRACTIONS_DIR = ROOT / "data_internal" / "extractions" / "print"
RATIONALES_DIR = ROOT / "data_internal" / "rationales" / "print"
DATA_DIR = ROOT / "data"
EMBEDDINGS_PATH = DATA_DIR / "print_index.npy"
META_PATH = DATA_DIR / "print_index_meta.jsonl"


def load_merged_records() -> list[dict]:
    records: list[dict] = []
    skipped_no_rationale = 0
    for ext_path in sorted(EXTRACTIONS_DIR.glob("*.json")):
        ext = json.loads(ext_path.read_text())
        slug = ext_path.stem
        rat_path = RATIONALES_DIR / f"{slug}.json"
        if not rat_path.exists():
            skipped_no_rationale += 1
            continue
        rat = json.loads(rat_path.read_text())
        ext["why_it_won"] = rat
        records.append(ext)
    print(f"Loaded {len(records)} winners (skipped {skipped_no_rationale} boards without rationale)")
    return records


def main() -> None:
    records = load_merged_records()
    assert records, "No Print winners found — aborting."

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
    print(f"\nEmbedded {len(embeddings)} docs in {elapsed:.1f}s — shape {matrix.shape}, dtype {matrix.dtype}")
    assert matrix.shape[1] == DIM, f"Expected dim {DIM}, got {matrix.shape[1]}"

    norms = np.linalg.norm(matrix, axis=1)
    print(f"Vector norms: min={norms.min():.4f}  max={norms.max():.4f}  mean={norms.mean():.4f}")

    DATA_DIR.mkdir(exist_ok=True)
    np.save(EMBEDDINGS_PATH, matrix)
    with META_PATH.open("w") as f:
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

    size_mb = EMBEDDINGS_PATH.stat().st_size / (1024 * 1024)
    print(f"\nSaved index:")
    print(f"  {EMBEDDINGS_PATH}  ({size_mb:.2f} MB)")
    print(f"  {META_PATH}")


if __name__ == "__main__":
    main()
