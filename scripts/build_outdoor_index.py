"""Build the vector index for the 117 Outdoor 2024 boards.

Reads data/outdoor_2024_with_rationale.jsonl, builds a search document per
board, embeds them via Voyage-3-large, and writes:

    data/outdoor_index.npy           — float32 matrix (n_boards × 1024)
    data/outdoor_index_meta.jsonl    — one JSON line per board (in matrix-row order)
                                       containing id, tier, campaign, one_liner,
                                       weighted_score, search_doc, full_record.

The full_record is kept inline so search.py can return the whole BoardAnalysis
without re-loading the rationale file.

Usage:
    uv run python build_outdoor_index.py
"""
from __future__ import annotations

import json
from pathlib import Path
from time import perf_counter

import numpy as np

from pipeline.embeddings import DIM, embed_documents
from pipeline.search_doc import build_search_document

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
IN_PATH = DATA_DIR / "outdoor_2024_with_rationale.jsonl"
EMBEDDINGS_PATH = DATA_DIR / "outdoor_index.npy"
META_PATH = DATA_DIR / "outdoor_index_meta.jsonl"


def load_records() -> list[dict]:
    records: list[dict] = []
    with IN_PATH.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("error") or not r.get("why_it_won"):
                continue
            records.append(r)
    return records


def main() -> None:
    records = load_records()
    print(f"Loaded {len(records)} records from {IN_PATH.name}")

    docs = [build_search_document(r) for r in records]
    nonempty = sum(1 for d in docs if d)
    print(f"Built {nonempty}/{len(docs)} search documents (non-empty)")

    print(f"\nSample search document (row 0):")
    print("---")
    print(docs[0])
    print("---")

    t0 = perf_counter()
    embeddings = embed_documents(docs)
    elapsed = perf_counter() - t0
    matrix = np.asarray(embeddings, dtype=np.float32)
    print(f"\nEmbedded {len(embeddings)} docs in {elapsed:.1f}s — shape {matrix.shape}, dtype {matrix.dtype}")
    assert matrix.shape[1] == DIM, f"Expected dim {DIM}, got {matrix.shape[1]}"

    # Quick sanity: unit-normalised?
    norms = np.linalg.norm(matrix, axis=1)
    print(f"Vector norms: min={norms.min():.4f}  max={norms.max():.4f}  mean={norms.mean():.4f}")

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
